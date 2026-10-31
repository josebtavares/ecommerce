"""
Regras do chat — quem pode agir como que caixa, ver que conversa e falar com quem.
Todos os endpoints passam por aqui; a interface só esconde o que o servidor já recusa.

  Cliente → Loja ✓ (lojas activas)        Loja → Cliente  só com relação (encomenda ou conversa)
  Cliente → Suporte ✓                     Loja → Loja ✗   ·   Loja → Suporte ✓
  Cliente → Cliente ✗                     Suporte → qualquer um ✓
  Membro ↔ membro da mesma loja ✓ (grupo da equipa e conversas directas)

Caixa da loja: dono e gestor sempre; staff/contabilista se o dono ativar `pode_chat`;
condutor só as conversas das encomendas cuja entrega lhe está atribuída.
"""
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from app.models import Loja, UtilizadorLoja, Encomenda, Condutor
from .models import Caixa, Conversa, Participante, Bloqueio

LOJAS_COM_CHAT = ('ativa', 'fechada')   # suspensas/pendentes só falam com o suporte


class ErroChat(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


# ══════════════════════════════════════════════════════════════
# Quem pode agir como que caixa
# ══════════════════════════════════════════════════════════════

def membro_ativo(utilizador, loja_id):
    return UtilizadorLoja.obter_membro(loja_id, utilizador)


def atende_suporte(utilizador):
    return utilizador.is_active and utilizador.user.is_staff and utilizador.pode_admin('atender_suporte')


def pode_agir_como(utilizador, caixa):
    """Acesso completo à caixa (ler todas as conversas dela e responder)."""
    if caixa.tipo == Caixa.PESSOAL:
        return caixa.utilizador_id == utilizador.id
    if caixa.tipo == Caixa.LOJA:
        m = membro_ativo(utilizador, caixa.loja_id)
        return bool(m and m.atende_chat)
    return atende_suporte(utilizador)


def entregas_do_condutor(utilizador, loja_id):
    """Encomendas desta loja cuja entrega está atribuída a este utilizador (condutor activo)."""
    return Encomenda.objects.filter(
        loja_id=loja_id,
        entrega__condutor__utilizador=utilizador,
        entrega__condutor__ativo=True,
    )


def caixas_de(utilizador):
    """
    Caixas a que o utilizador tem acesso: [(caixa, restrita)].
    `restrita` = condutor: só vê as conversas das encomendas que lhe estão atribuídas.
    """
    caixas = [(Caixa.de_utilizador(utilizador), False)]
    vistas = set()
    for m in UtilizadorLoja.objects.filter(utilizador=utilizador, ativo=True).select_related('loja'):
        if m.atende_chat:
            caixas.append((Caixa.de_loja(m.loja), False))
            vistas.add(m.loja_id)
    for c in Condutor.objects.filter(utilizador=utilizador, ativo=True).select_related('loja'):
        if c.loja_id not in vistas:
            caixas.append((Caixa.de_loja(c.loja), True))
            vistas.add(c.loja_id)
    if atende_suporte(utilizador):
        caixas.append((Caixa.suporte(), False))
    return caixas


def acesso_caixa(utilizador, caixa):
    """None (sem acesso), 'total' ou 'condutor'."""
    if pode_agir_como(utilizador, caixa):
        return 'total'
    if caixa.tipo == Caixa.LOJA and Condutor.objects.filter(
            loja_id=caixa.loja_id, utilizador=utilizador, ativo=True).exists():
        return 'condutor'
    return None


# ══════════════════════════════════════════════════════════════
# Quem pode ver/escrever numa conversa
# ══════════════════════════════════════════════════════════════

def pode_usar(utilizador, conversa, caixa):
    """O utilizador pode ler e escrever nesta conversa como `caixa`?"""
    # grupo da equipa: qualquer membro activo da loja, com a sua caixa pessoal
    if conversa.tipo == Conversa.EQUIPA_GRUPO:
        return (caixa.tipo == Caixa.PESSOAL and caixa.utilizador_id == utilizador.id
                and membro_ativo(utilizador, conversa.loja_id) is not None)

    if not conversa.participantes.filter(caixa=caixa).exists():
        return False

    # conversa directa da equipa: os dois têm de continuar na loja
    if conversa.tipo == Conversa.EQUIPA_DIRETA:
        return (caixa.tipo == Caixa.PESSOAL and caixa.utilizador_id == utilizador.id
                and membro_ativo(utilizador, conversa.loja_id) is not None)

    acesso = acesso_caixa(utilizador, caixa)
    if acesso == 'total':
        return True
    if acesso == 'condutor':
        return bool(conversa.encomenda_id) and entregas_do_condutor(
            utilizador, caixa.loja_id).filter(id=conversa.encomenda_id).exists()
    return False


def conversas_visiveis(utilizador, caixa):
    """Conversas que o utilizador vê ao abrir esta caixa."""
    acesso = acesso_caixa(utilizador, caixa)
    if acesso is None:
        raise ErroChat('Sem acesso a esta caixa.', 403)
    qs = Conversa.objects.filter(participantes__caixa=caixa)
    if caixa.tipo == Caixa.PESSOAL:
        sincronizar_grupos(utilizador)
        lojas = UtilizadorLoja.objects.filter(utilizador=utilizador, ativo=True).values('loja_id')
        # só os grupos/directas das lojas onde ainda trabalha
        qs = qs.filter(~Q(tipo__in=(Conversa.EQUIPA_GRUPO, Conversa.EQUIPA_DIRETA)) | Q(loja_id__in=lojas))
    if acesso == 'condutor':
        qs = qs.filter(encomenda__in=entregas_do_condutor(utilizador, caixa.loja_id))
    return qs.distinct()


def sincronizar_grupos(utilizador):
    """Garante o grupo da equipa (e a participação) de cada loja onde o utilizador trabalha."""
    pessoal = Caixa.de_utilizador(utilizador)
    for loja_id in UtilizadorLoja.objects.filter(utilizador=utilizador, ativo=True).values_list('loja_id', flat=True):
        grupo = _obter_conversa(f'grp:{loja_id}', tipo=Conversa.EQUIPA_GRUPO, loja_id=loja_id, assunto='Equipa')
        Participante.objects.get_or_create(conversa=grupo, caixa=pessoal)


# ══════════════════════════════════════════════════════════════
# Iniciar conversa
# ══════════════════════════════════════════════════════════════

def bloqueado(a, b):
    """Há bloqueio entre as duas caixas, num sentido ou noutro."""
    return Bloqueio.objects.filter(Q(caixa=a, bloqueada=b) | Q(caixa=b, bloqueada=a)).exists()


def _obter_conversa(chave, **campos):
    conv = Conversa.objects.filter(chave=chave).first()
    if conv:
        return conv
    try:
        with transaction.atomic():
            return Conversa.objects.create(chave=chave, **campos)
    except IntegrityError:          # outro pedido criou-a ao mesmo tempo
        return Conversa.objects.get(chave=chave)


def _com_participantes(conversa, *caixas):
    for c in caixas:
        Participante.objects.get_or_create(conversa=conversa, caixa=c)
    return conversa


def _verificar_remetente(utilizador, origem):
    if not utilizador.is_active:
        raise ErroChat('A tua conta não está activa.', 403)
    if acesso_caixa(utilizador, origem) != 'total':
        raise ErroChat('Não podes falar em nome desta caixa.', 403)
    if origem.tipo == Caixa.LOJA and origem.loja.estado not in LOJAS_COM_CHAT:
        raise ErroChat('Esta loja só pode falar com o suporte.', 403)


def _verificar_bloqueio(a, b):
    if bloqueado(a, b):
        raise ErroChat('Não é possível falar com esta conta.', 403)


def iniciar(utilizador, origem, destino, destino_id=None, encomenda_id=None, loja_id=None):
    """
    Abre (ou devolve a existente) a conversa entre `origem` (uma caixa do utilizador) e o destino:
      destino='loja'         destino_id=<loja>          [encomenda_id]
      destino='utilizador'   destino_id=<utilizador>    [encomenda_id] [loja_id p/ equipa]
      destino='suporte'
      destino='equipa_grupo' loja_id=<loja>
    """
    from app.models import Utilizador

    # ── grupo da equipa ───────────────────────────────────────
    if destino == 'equipa_grupo':
        if origem.tipo != Caixa.PESSOAL or origem.utilizador_id != utilizador.id:
            raise ErroChat('O grupo da equipa usa a tua caixa pessoal.', 400)
        if not loja_id or membro_ativo(utilizador, loja_id) is None:
            raise ErroChat('Não pertences a esta loja.', 403)
        sincronizar_grupos(utilizador)
        return Conversa.objects.get(chave=f'grp:{loja_id}')

    # condutor: pela caixa da loja, só com o cliente de uma entrega que é dele
    if origem.tipo == Caixa.LOJA and acesso_caixa(utilizador, origem) == 'condutor':
        enc = entregas_do_condutor(utilizador, origem.loja_id).filter(id=encomenda_id).first() if encomenda_id else None
        if not enc or destino != 'utilizador' or str(destino_id) != str(enc.comprador_id):
            raise ErroChat('Só podes falar com o cliente das tuas entregas.', 403)
        if not utilizador.is_active or origem.loja.estado not in LOJAS_COM_CHAT:
            raise ErroChat('Não podes falar em nome desta caixa.', 403)
        caixa_cliente = Caixa.de_utilizador(enc.comprador)
        _verificar_bloqueio(origem, caixa_cliente)
        return _conversa_cliente_loja(caixa_cliente, origem, origem.loja, enc.comprador, enc.id)

    if origem.tipo == Caixa.SUPORTE:
        if not atende_suporte(utilizador):
            raise ErroChat('Sem permissão para o suporte.', 403)
    else:
        _verificar_remetente(utilizador, origem)

    # ── → Suporte Bendi ───────────────────────────────────────
    if destino == 'suporte':
        if origem.tipo == Caixa.SUPORTE:
            raise ErroChat('Destino inválido.', 400)
        sup = Caixa.suporte()
        conv = _obter_conversa(f'sup:{origem.id}', tipo=Conversa.SUPORTE, assunto='Suporte',
                               loja_id=origem.loja_id if origem.tipo == Caixa.LOJA else None)
        return _com_participantes(conv, origem, sup)

    # ── → Loja ────────────────────────────────────────────────
    if destino == 'loja':
        loja = Loja.objects.filter(id=destino_id).first()
        if not loja:
            raise ErroChat('Loja não encontrada.', 404)
        caixa_loja = Caixa.de_loja(loja)

        if origem.tipo == Caixa.SUPORTE:          # suporte → loja
            conv = _obter_conversa(f'sup:{caixa_loja.id}', tipo=Conversa.SUPORTE, assunto='Suporte', loja=loja)
            return _com_participantes(conv, caixa_loja, origem)

        if origem.tipo == Caixa.LOJA:
            raise ErroChat('As lojas não falam entre si.', 403)

        # cliente → loja. Fechada pelo dono: as encomendas em curso continuam, por isso quem lá comprou
        # ainda a pode contactar (antes só respondia a conversas que já existiam)
        if loja.estado not in LOJAS_COM_CHAT or (
                loja.estado != 'ativa' and not Encomenda.objects.filter(loja=loja, comprador=utilizador).exists()):
            raise ErroChat('Esta loja não está disponível.', 404)
        if membro_ativo(utilizador, loja.id):
            raise ErroChat('Pertences a esta loja — usa o chat da equipa.', 400)
        _verificar_bloqueio(origem, caixa_loja)
        return _conversa_cliente_loja(origem, caixa_loja, loja, utilizador, encomenda_id)

    # ── → Utilizador ──────────────────────────────────────────
    if destino == 'utilizador':
        alvo = Utilizador.objects.filter(id=destino_id).first()
        if not alvo or not alvo.is_active:
            raise ErroChat('Utilizador não encontrado.', 404)
        caixa_alvo = Caixa.de_utilizador(alvo)

        if origem.tipo == Caixa.SUPORTE:          # suporte → utilizador
            conv = _obter_conversa(f'sup:{caixa_alvo.id}', tipo=Conversa.SUPORTE, assunto='Suporte')
            return _com_participantes(conv, caixa_alvo, origem)

        if origem.tipo == Caixa.LOJA:             # loja → cliente: só com relação
            loja = origem.loja
            if membro_ativo(alvo, loja.id):
                raise ErroChat('Este utilizador é da equipa — usa o chat da equipa.', 400)
            relacao = (Encomenda.objects.filter(loja=loja, comprador=alvo).exists()
                       or Conversa.objects.filter(chave=f'cl:{caixa_alvo.id}:{loja.id}').exists())
            if not relacao:
                raise ErroChat('A loja só pode iniciar conversa com quem já comprou ou falou com ela.', 403)
            _verificar_bloqueio(origem, caixa_alvo)
            return _conversa_cliente_loja(caixa_alvo, origem, loja, alvo, encomenda_id)

        # pessoal → pessoal: só colegas da mesma loja (nunca cliente ↔ cliente)
        if alvo.id == utilizador.id:
            raise ErroChat('Destino inválido.', 400)
        comuns = set(UtilizadorLoja.objects.filter(utilizador=utilizador, ativo=True).values_list('loja_id', flat=True)) \
            & set(UtilizadorLoja.objects.filter(utilizador=alvo, ativo=True).values_list('loja_id', flat=True))
        if not comuns:
            raise ErroChat('Só podes falar com lojas, com o suporte ou com a tua equipa.', 403)
        if loja_id is None:
            loja_id = min(comuns)
        elif int(loja_id) not in comuns:
            raise ErroChat('Não trabalham os dois nesta loja.', 403)
        _verificar_bloqueio(origem, caixa_alvo)
        a, b = sorted((origem.id, caixa_alvo.id))
        conv = _obter_conversa(f'dir:{loja_id}:{a}:{b}', tipo=Conversa.EQUIPA_DIRETA, loja_id=loja_id)
        return _com_participantes(conv, origem, caixa_alvo)

    raise ErroChat('Destino inválido.', 400)


def _conversa_cliente_loja(caixa_cliente, caixa_loja, loja, cliente, encomenda_id):
    if encomenda_id:
        enc = Encomenda.objects.filter(id=encomenda_id, loja=loja, comprador=cliente).first()
        if not enc:
            raise ErroChat('Encomenda não encontrada.', 404)
        conv = _obter_conversa(f'enc:{enc.id}', tipo=Conversa.CLIENTE_LOJA, loja=loja, encomenda=enc,
                               assunto=f'Encomenda #{enc.id}')
    else:
        conv = _obter_conversa(f'cl:{caixa_cliente.id}:{loja.id}', tipo=Conversa.CLIENTE_LOJA, loja=loja)
    return _com_participantes(conv, caixa_cliente, caixa_loja)


# ══════════════════════════════════════════════════════════════
# Enviar
# ══════════════════════════════════════════════════════════════

def outras_caixas(conversa, caixa):
    return [p.caixa for p in conversa.participantes.select_related('caixa').exclude(caixa=caixa)]


def verificar_envio(utilizador, conversa, caixa):
    if not pode_usar(utilizador, conversa, caixa):
        raise ErroChat('Sem acesso a esta conversa.', 403)
    if not utilizador.is_active:
        raise ErroChat('A tua conta não está activa.', 403)
    if caixa.tipo == Caixa.LOJA and caixa.loja.estado not in LOJAS_COM_CHAT and conversa.tipo != Conversa.SUPORTE:
        raise ErroChat('Esta loja só pode falar com o suporte.', 403)
    # o cliente não escreve a uma loja suspensa/pendente (ela já não lhe pode responder — só ao suporte)
    if conversa.tipo == Conversa.CLIENTE_LOJA and caixa.tipo == Caixa.PESSOAL and conversa.loja             and conversa.loja.estado not in LOJAS_COM_CHAT:
        raise ErroChat('Esta loja não está disponível de momento. Para ajuda, fala com o suporte.', 403)
    if conversa.tipo != Conversa.EQUIPA_GRUPO:
        for outra in outras_caixas(conversa, caixa):
            _verificar_bloqueio(caixa, outra)


def registar_envio(conversa, caixa, mensagem):
    """Actualiza a conversa e marca como lida para quem enviou."""
    conversa.ultima_mensagem_em = mensagem.criada_em or timezone.now()
    campos = ['ultima_mensagem_em']
    if conversa.estado == Conversa.FECHADA:      # responder reabre o pedido de suporte
        conversa.estado = Conversa.ABERTA
        campos.append('estado')
    conversa.save(update_fields=campos)
    Participante.objects.update_or_create(conversa=conversa, caixa=caixa, defaults={'ultima_lida': mensagem.id})


def utilizador_ve_conversa(utilizador, conversa):
    """Por alguma das suas caixas (ou como membro, no grupo da equipa) o utilizador lê esta conversa?"""
    if conversa.tipo == Conversa.EQUIPA_GRUPO:
        return membro_ativo(utilizador, conversa.loja_id) is not None
    return any(pode_usar(utilizador, conversa, p.caixa)
               for p in conversa.participantes.select_related('caixa__loja', 'caixa__utilizador'))
