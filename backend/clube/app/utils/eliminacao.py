"""
Apagar uma conta = anonimizá-la (Perfil → "Apagar a minha conta", ou o Super Admin).

O que fica, sem ligação à pessoa:
- encomendas, pagamentos, reembolsos, faturas, marcações e vendas POS (registos financeiros e
  fiscais — a lei obriga a guardá-los; nunca se apagam);
- avaliações e mensagens do chat, com o autor "Utilizador eliminado" (as avaliações contam na nota);
- as lojas e os POS do dono, suspensos (MOTIVO_ELIMINADO): saem do site, o arquivo fiscal fica e o
  admin consulta-o em "Ver backoffice" (utils/ver_loja.py).

O que sai: nome, email, telefone, morada, foto, ligação ao Google, password, carrinhos, cartões
guardados, favoritos, notificações, galeria e os documentos legais das lojas (utils/documentos_loja.py);
deixa de ser membro de equipas de lojas.
Banido: o email fica bloqueado (só o hash — EmailBloqueado) para não abrir outra conta.

Pedido pela própria pessoa: 30 dias para mudar de ideias (DIAS_PARA_ELIMINAR). As sessões terminam
e as lojas ficam logo suspensas; entrar outra vez antes do fim cancela o pedido e repõe as lojas.
O worker (processar_videos) apaga as que chegaram ao fim; o admin apaga logo.

Não se apaga com coisas por resolver (pendentes): encomendas em curso, devoluções abertas,
marcações por fazer, contas do POS abertas — como cliente e nas lojas de que é dono.
"""
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

from .moderacao import MOTIVO_ELIMINADO

DIAS_PARA_ELIMINAR = 30
EM_CURSO = ('pago', 'preparando', 'enviado')
# por_reembolsar: aceite mas o dinheiro ainda não saiu (o pagamento online recusou) — também prende
DEVOLUCAO_ABERTA = ('pedido', 'proposta', 'em_disputa', 'aguarda_produto', 'a_devolver', 'por_reembolsar')
MARCACAO_ABERTA = ('pendente', 'confirmada')


def hash_email(email):
    return hashlib.sha256((email or '').strip().lower().encode()).hexdigest()


def email_bloqueado(email):
    from ..models import EmailBloqueado
    return bool(email) and EmailBloqueado.objects.filter(hash=hash_email(email)).exists()


def _plural(n, um, varios):
    return f'{n} {um if n == 1 else varios}'


def _marcacoes_por_devolver(**filtro):
    """Marcações pagas com a devolução recusada pelo pagamento online (marcacoes.reembolsar) — ainda por sair."""
    from django.db.models import F
    from ..servicos.models import Marcacao
    return (Marcacao.objects.filter(pago=True, reembolso_devido__gt=F('valor_reembolsado'), **filtro)
            .exclude(reembolso_erro='').count())


def pendentes(alvo):
    """O que impede apagar a conta agora (lista de frases; vazia = pode)."""
    from ..models import Encomenda, Reembolso, Loja
    from ..pos.models import ContaMesa
    from ..servicos.models import Marcacao
    agora = timezone.now()
    r = []
    if alvo.user.is_staff:
        r.append('É uma conta da equipa de administração — o Super Admin tem de lhe tirar o papel primeiro.')
    n = Encomenda.objects.filter(comprador=alvo, status__in=EM_CURSO).count()
    if n:
        r.append(f'Tens {_plural(n, "encomenda", "encomendas")} em curso — espera que cheguem.')
    n = Reembolso.objects.filter(comprador=alvo, estado__in=DEVOLUCAO_ABERTA).count()
    if n:
        r.append(f'Tens {_plural(n, "devolução aberta", "devoluções abertas")}.')
    n = Marcacao.objects.filter(cliente=alvo, estado__in=MARCACAO_ABERTA, inicio__gte=agora).count()
    if n:
        r.append(f'Tens {_plural(n, "marcação marcada", "marcações marcadas")} — cancela-as primeiro.')
    n = _marcacoes_por_devolver(cliente=alvo)
    if n:
        r.append(f'Tens {_plural(n, "devolução de marcação", "devoluções de marcações")} a processar — espera que termine.')
    for loja in Loja.objects.filter(dono=alvo).order_by('nome'):
        partes = []
        n = Encomenda.objects.filter(loja=loja, status__in=EM_CURSO).count()
        if n:
            partes.append(_plural(n, 'encomenda em curso', 'encomendas em curso'))
        n = Reembolso.objects.filter(loja=loja, estado__in=DEVOLUCAO_ABERTA).count()
        if n:
            partes.append(_plural(n, 'devolução aberta', 'devoluções abertas'))
        n = Marcacao.objects.filter(loja=loja, estado__in=MARCACAO_ABERTA, inicio__gte=agora).count()
        if n:
            partes.append(_plural(n, 'marcação por fazer', 'marcações por fazer'))
        n = _marcacoes_por_devolver(loja=loja)
        if n:
            partes.append(_plural(n, 'devolução de marcação por concluir', 'devoluções de marcações por concluir'))
        if partes:
            r.append(f'A loja {loja.nome} tem {", ".join(partes)}.')
    for conta in ContaMesa.objects.filter(pos__dono=alvo, status='aberta').values('pos__nome').distinct():
        r.append(f'O POS {conta["pos__nome"]} tem contas abertas.')
    return r


def _registar(alvo, acao, por=None, motivo='', afetados=None):
    from ..models import ModeracaoUtilizador
    return ModeracaoUtilizador.objects.create(utilizador=alvo, acao=acao, motivo=motivo[:500], feito_por=por,
                                              afetados=afetados or {})


def pedir(alvo):
    """A própria pessoa pede: fica marcada para daqui a 30 dias; lojas suspensas; sessões terminam."""
    from .moderacao import _suspender_do_dono
    from ..autenticacao import terminar_sessoes
    quando = timezone.now() + timedelta(days=DIAS_PARA_ELIMINAR)
    with transaction.atomic():
        afetados = _suspender_do_dono(alvo, MOTIVO_ELIMINADO)
        alvo.eliminar_em = quando
        alvo.save(update_fields=['eliminar_em', 'data_atualizacao'])
        _registar(alvo, 'pedir_eliminacao', afetados=afetados)
        email, nome = alvo.user.email, alvo.user.first_name or alvo.user.username
        transaction.on_commit(lambda: _avisar_pedido(email, nome, quando))
    terminar_sessoes(alvo.user)
    return quando


def cancelar(alvo, por=None):
    """Entrou outra vez dentro do prazo (ou o admin cancelou): a conta fica e as lojas voltam."""
    from ..models import Utilizador, ModeracaoUtilizador
    from .moderacao import _repor_do_dono
    with transaction.atomic():
        # condicional: dois logins ao mesmo tempo não cancelam duas vezes
        if not Utilizador.objects.filter(pk=alvo.pk, eliminar_em__isnull=False).update(eliminar_em=None):
            return False
        alvo.eliminar_em = None
        pedido = ModeracaoUtilizador.objects.filter(utilizador=alvo, acao='pedir_eliminacao').first()
        if pedido:
            _repor_do_dono(pedido)
        _registar(alvo, 'cancelar_eliminacao', por=por)
    return True


def cancelar_ao_entrar(utilizador):
    """Chamado nos logins (password certa): cancela um pedido de eliminação ainda no prazo."""
    if utilizador is None or not utilizador.eliminar_em or utilizador.status == 'eliminado':
        return False
    return cancelar(utilizador)


def anonimizar(alvo, por=None, motivo=''):
    """Apaga os dados pessoais da conta (ver o topo). Não verifica pendentes — quem chama verifica."""
    from ..models import (Utilizador, UtilizadorLoja, Carrinho, CartaoGuardado, Favorito, Notificacao,
                          Galeria, Condutor, Loja, EmailBloqueado)
    from ..pos.models import ConfiguracaoPOS
    from .moderacao import _suspender_do_dono
    from ..autenticacao import terminar_sessoes
    user = alvo.user
    email, nome = user.email, user.first_name or user.username
    foto = alvo.foto.name if alvo.foto else ''
    with transaction.atomic():
        alvo = Utilizador.objects.select_for_update().select_related('user').get(pk=alvo.pk)
        if alvo.status == 'eliminado':
            return False
        if alvo.status == 'banido' and email:
            EmailBloqueado.objects.get_or_create(hash=hash_email(email))
        # lojas e POS ainda não suspensos por causa da conta (o pedido já os suspendeu)
        from .moderacao import MOTIVOS_DONO
        if Loja.objects.filter(dono=alvo).exclude(estado='suspensa', estado_motivo__in=MOTIVOS_DONO).exists() \
                or ConfiguracaoPOS.objects.filter(dono=alvo).exclude(suspenso=True, suspenso_motivo__in=MOTIVOS_DONO).exists():
            _suspender_do_dono(alvo, MOTIVO_ELIMINADO)
        else:
            Loja.objects.filter(dono=alvo, estado='suspensa', estado_motivo__in=MOTIVOS_DONO) \
                .update(estado_motivo=MOTIVO_ELIMINADO)
            ConfiguracaoPOS.objects.filter(dono=alvo, suspenso=True, suspenso_motivo__in=MOTIVOS_DONO) \
                .update(suspenso_motivo=MOTIVO_ELIMINADO)

        for M in (Carrinho, CartaoGuardado, Favorito, Notificacao, Galeria):
            M.objects.filter(utilizador=alvo).delete()
        # documentos legais das lojas (identificação do titular…): saem com a conta, os ficheiros também
        from .documentos_loja import apagar_da_conta
        apagar_da_conta(alvo)
        UtilizadorLoja.objects.filter(utilizador=alvo).update(ativo=False)
        Condutor.objects.filter(utilizador=alvo).update(ativo=False)

        user.username = f'eliminado-{alvo.pk}'
        user.first_name, user.last_name, user.email = 'Utilizador', 'eliminado', ''
        user.is_active = user.is_staff = user.is_superuser = False
        user.set_unusable_password()
        user.save()
        alvo.telefone = alvo.morada = alvo.motivo_estado = ''
        alvo.foto = 'utilizadores/default.png'
        alvo.google_id = None
        alvo.verificado = False
        alvo.role_admin = None
        alvo.status, alvo.suspenso_ate, alvo.eliminar_em = 'eliminado', None, None
        alvo.save()
        _registar(alvo, 'eliminar', por=por, motivo=motivo)
        transaction.on_commit(lambda: _avisar_eliminada(email, nome))
        if foto and foto != 'utilizadores/default.png':
            transaction.on_commit(lambda: _apagar_foto(foto))
    terminar_sessoes(user)
    return True


def eliminar_vencidas():
    """Worker: apaga as contas cujo prazo de 30 dias acabou. As que entretanto ficaram com coisas
    por resolver esperam (voltam a ser vistas no minuto seguinte). Devolve quantas apagou."""
    from ..models import Utilizador
    n = 0
    for u in Utilizador.objects.select_related('user').filter(eliminar_em__lte=timezone.now()).exclude(status='eliminado'):
        if pendentes(u):
            continue
        try:
            n += bool(anonimizar(u, motivo='Pedido pela própria pessoa (30 dias)'))
        except Exception:
            log.exception('eliminação: falhou a conta %s', u.pk)
    return n


def _apagar_foto(nome):
    from django.core.files.storage import default_storage
    try:
        default_storage.delete(nome)
    except Exception:
        log.warning('eliminação: não apagou a foto %s', nome)


def _enviar(email, assunto, texto):
    if not email:
        return
    suporte = getattr(settings, 'EMAIL_SUPORTE', '')
    try:
        EmailMessage(subject=assunto, body=texto + '\n\nBende', from_email=settings.DEFAULT_FROM_EMAIL,
                     to=[email], reply_to=[suporte] if suporte else None).send()
    except Exception:
        log.exception('eliminação: falhou o email "%s"', assunto)


def _avisar_pedido(email, nome, quando):
    from .moderacao import data_curta
    _enviar(email, 'Pedido para apagar a tua conta Bende',
            f'Olá {nome},\n\nRecebemos o teu pedido para apagar a conta Bende. Vai ser apagada a '
            f'{data_curta(quando)}.\n\nMudaste de ideias? Entra na tua conta antes dessa data e o pedido é '
            f'cancelado: {settings.FRONTEND_BASE_URL}/Login\n\nAs encomendas, faturas e pagamentos ficam '
            f'guardados sem o teu nome, como a lei obriga.')


def _avisar_eliminada(email, nome):
    _enviar(email, 'A tua conta Bende foi apagada',
            f'Olá {nome},\n\nA tua conta Bende foi apagada: o nome, email, telefone, morada e foto já não '
            f'estão guardados. As encomendas, faturas e pagamentos ficam sem o teu nome, como a lei obriga, '
            f'e as tuas avaliações e mensagens aparecem como "Utilizador eliminado".')
