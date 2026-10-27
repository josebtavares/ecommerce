"""
Conversa de uma marcação (como a dos reembolsos): o cliente fala com a loja e com o profissional
dessa marcação, com fotos (ex.: a ideia de uma tatuagem). A loja pode propor um preço novo; o
cliente aceita ou recusa. As fotos são privadas: só se vêem por um link assinado e o acesso volta
a ser verificado em cada pedido.
"""
from decimal import Decimal

from django.core import signing
from django.db import transaction
from django.utils import timezone

from ..models import UtilizadorLoja
from ..utils.dinheiro import formatar
from .models import FotoMarcacao, Marcacao, MensagemMarcacao, PropostaPreco

MAX_TEXTO = 2000
MAX_FOTOS = 10
SALT_FOTO = 'servicos.foto_marcacao'
VALIDADE_FOTO = 60 * 60 * 6


class ErroConversa(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def papel(u, m):
    """'cliente', 'loja' ou None. Loja = quem gere marcações, ou o profissional (com conta) desta marcação."""
    if not u:
        return None
    if m.cliente_id and m.cliente_id == u.id:
        return 'cliente'
    membro = UtilizadorLoja.objects.filter(loja_id=m.loja_id, utilizador=u, ativo=True).first()
    if not membro:
        return None
    if membro.pode('gerir_marcacoes'):
        return 'loja'
    prof = getattr(membro, 'profissional', None)
    if prof and prof.id == m.profissional_id:
        return 'loja'
    return None


def pode_conversar(m):
    """Só há conversa com clientes com conta (as marcações manuais por telefone não têm)."""
    return bool(m.cliente_id)


def nome_autor(u, papel_, m):
    if papel_ == 'cliente':
        return u.nome or u.user.username
    nome = u.nome or u.user.username
    return f'{nome} · {m.loja.nome}'[:100]


def _sistema(m, texto, proposta=None):
    return MensagemMarcacao.objects.create(marcacao=m, papel='sistema', texto=texto, proposta=proposta)


def preparar_fotos(ficheiros, ja_tem=0):
    from ..chat import imagens
    ficheiros = list(ficheiros or [])
    if not ficheiros:
        return []
    if not imagens.imagens_disponiveis():
        raise ErroConversa('O envio de fotos não está disponível de momento.')
    if ja_tem + len(ficheiros) > MAX_FOTOS:
        raise ErroConversa(f'Máximo de {MAX_FOTOS} fotos por marcação.')
    prontas = []
    for f in ficheiros:
        try:
            conteudo, _, _ = imagens.processar(f)
        except imagens.ImagemInvalida as e:
            raise ErroConversa(str(e))
        prontas.append(conteudo)
    return prontas


def escrever(m, u, papel_, texto, ficheiros=()):
    texto = (texto or '').strip()
    if not pode_conversar(m):
        raise ErroConversa('Esta marcação foi feita pela loja sem conta de cliente — não há conversa.')
    if not texto and not ficheiros:
        raise ErroConversa('Escreve uma mensagem.')
    if len(texto) > MAX_TEXTO:
        raise ErroConversa(f'A mensagem é demasiado longa (máximo {MAX_TEXTO} caracteres).')
    fotos = preparar_fotos(ficheiros, ja_tem=m.fotos.count())
    with transaction.atomic():
        msg = MensagemMarcacao.objects.create(marcacao=m, autor=u, autor_nome=nome_autor(u, papel_, m), papel=papel_, texto=texto)
        for conteudo in fotos:
            f = FotoMarcacao(marcacao=m, mensagem=msg, autor=u)
            f.ficheiro.save(conteudo.name, conteudo, save=True)
        agora = timezone.now()
        campo = 'lida_cliente_em' if papel_ == 'cliente' else 'lida_loja_em'
        Marcacao.objects.filter(pk=m.pk).update(**{campo: agora})
    _avisar_mensagem(m, papel_, u)
    return msg


def _avisar_mensagem(m, papel_, u):
    from ..Views.notificacaoView import notificar, notificar_staff
    texto = f'{m.servico_nome} a {m.inicio.astimezone(_tz()).strftime("%d/%m às %H:%M")}'
    if papel_ != 'cliente' and m.cliente_id:
        notificar(utilizador=m.cliente, tipo='marcacao_mensagem', titulo=f'Nova mensagem de {m.loja.nome}', mensagem=texto,
                  loja=m.loja, link=f'/minhas-marcacoes/{m.id}')
    if papel_ == 'cliente':
        link = f'/loja/{m.loja_id}/backoffice/servicos?marcacao={m.id}'
        notificar_staff(loja=m.loja, roles=['dono', 'gestor'], tipo='marcacao_mensagem',
                        titulo='Nova mensagem de um cliente', mensagem=texto, link=link)
        prof = m.profissional
        if prof.membro_id and prof.membro.ativo and prof.membro.role not in ('dono', 'gestor'):
            notificar(utilizador=prof.membro.utilizador, tipo='marcacao_mensagem', titulo='Nova mensagem de um cliente',
                      mensagem=texto, loja=m.loja, link=link)


def _tz():
    from ..utils.horarios import fuso
    return fuso()


def marcar_lida(m, papel_):
    campo = 'lida_cliente_em' if papel_ == 'cliente' else 'lida_loja_em'
    Marcacao.objects.filter(pk=m.pk).update(**{campo: timezone.now()})


def por_ler(m, papel_):
    lida = m.lida_cliente_em if papel_ == 'cliente' else m.lida_loja_em
    outros = m.mensagens.exclude(papel=papel_)
    if lida:
        outros = outros.filter(criada_em__gt=lida)
    return outros.count()


# ── propostas de preço ───────────────────────────────────────

@transaction.atomic
def propor(m, valor, motivo, por):
    m = Marcacao.objects.select_for_update().get(pk=m.pk)
    if m.estado not in Marcacao.ATIVOS:
        raise ErroConversa('Esta marcação já não está activa.')
    if not pode_conversar(m):
        raise ErroConversa('Marcação sem conta de cliente: muda o preço directamente ao concluir.')
    if valor == m.preco_indicado:
        raise ErroConversa('Esse já é o preço da marcação.')
    m.propostas.filter(estado='pendente').update(estado='anulada', respondida_em=timezone.now())
    p = PropostaPreco.objects.create(marcacao=m, valor=valor, valor_antes=m.preco_indicado, motivo=motivo[:300], criada_por=por[:100])
    _sistema(m, f'A loja propõe um preço novo: {formatar(valor)} (era {formatar(m.preco_indicado)}).'
             + (f' Motivo: {motivo}' if motivo else ''), proposta=p)
    from ..Views.notificacaoView import notificar
    notificar(utilizador=m.cliente, tipo='marcacao_proposta', titulo=f'{m.loja.nome} propõe um preço novo',
              mensagem=f'{m.servico_nome}: {formatar(valor)}. Aceita ou recusa na marcação.', loja=m.loja,
              link=f'/minhas-marcacoes/{m.id}')
    return p


@transaction.atomic
def responder(m, proposta_id, aceitar, u):
    m = Marcacao.objects.select_for_update().get(pk=m.pk)
    p = m.propostas.filter(pk=proposta_id).first()
    if not p or p.estado != 'pendente':
        raise ErroConversa('Esta proposta já não está à espera de resposta.')
    if m.estado not in Marcacao.ATIVOS:
        raise ErroConversa('Esta marcação já não está activa.')
    p.estado, p.respondida_em = ('aceite' if aceitar else 'recusada'), timezone.now()
    p.save(update_fields=['estado', 'respondida_em'])
    if aceitar:
        m.preco_indicado, m.tipo_preco = p.valor, 'fixo'        # passa a ser o preço combinado
        campos = ['preco_indicado', 'tipo_preco', 'data_atualizacao']
        if m.pago:
            # pagou antecipado: o que pagou a mais é devolvido; o que falta paga no local
            m.reembolso_devido = max(Decimal('0'), m.valor_pago - p.valor)
            campos.append('reembolso_devido')
        m.save(update_fields=campos)
        from .marcacoes import falta_pagar
        texto = f'O cliente aceitou o preço de {formatar(p.valor)}.'
        if m.pago and falta_pagar(m) > 0:
            texto += f' Falta pagar {formatar(falta_pagar(m))} no local.'
        elif m.pago and m.reembolso_devido > m.valor_reembolsado:
            texto += f' A loja devolve {formatar(m.reembolso_devido - m.valor_reembolsado)}.'
    else:
        texto = f'O cliente recusou o preço de {formatar(p.valor)}.'
    _sistema(m, texto)
    if aceitar:
        from .marcacoes import reembolsar
        reembolsar(m)
    from ..Views.notificacaoView import notificar_staff
    notificar_staff(loja=m.loja, roles=['dono', 'gestor'], tipo='marcacao_proposta',
                    titulo='Proposta de preço aceite' if aceitar else 'Proposta de preço recusada', mensagem=texto,
                    link=f'/loja/{m.loja_id}/backoffice/servicos?marcacao={m.id}')
    return m


# ── payloads ────────────────────────────────────────────────

def assinar_foto(foto_id, utilizador_id):
    return signing.dumps({'f': foto_id, 'u': utilizador_id}, salt=SALT_FOTO, compress=True)


def ler_assinatura_foto(token):
    try:
        d = signing.loads(token, salt=SALT_FOTO, max_age=VALIDADE_FOTO)
        return int(d['f']), int(d['u'])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None


def mensagens_payload(request, m, papel_):
    u = request.user.utilizador
    fotos = {}
    for f in m.fotos.order_by('id'):
        fotos.setdefault(f.mensagem_id, []).append(
            {'id': f.id, 'url': request.build_absolute_uri(f'/app/marcacoes/fotos/{f.id}/?t={assinar_foto(f.id, u.id)}')})
    tz = _tz()
    return [{'id': x.id, 'papel': x.papel, 'meu': x.papel == papel_ and x.autor_id == u.id,
             'autor': x.autor_nome or ('Bendi' if x.papel == 'sistema' else ''), 'texto': x.texto,
             'proposta_id': x.proposta_id, 'criada_em': x.criada_em.astimezone(tz).isoformat(), 'fotos': fotos.get(x.id, [])}
            for x in m.mensagens.all()]


def propostas_payload(m):
    tz = _tz()
    return [{'id': p.id, 'valor': str(p.valor), 'valor_antes': str(p.valor_antes), 'motivo': p.motivo, 'estado': p.estado,
             'estado_nome': p.get_estado_display(), 'criada_por': p.criada_por,
             'criada_em': p.data_criacao.astimezone(tz).isoformat()} for p in m.propostas.all()]
