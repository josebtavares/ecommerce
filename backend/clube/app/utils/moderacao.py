"""
Suspender, banir e reactivar contas (Admin → Utilizadores).

- suspender: temporário, com data de fim opcional; o suporte e o superadmin podem.
- banir: permanente; só o superadmin bane e levanta. O email fica preso à conta (é único),
  por isso não dá para criar outra conta com ele, nem pelo Google.
- Cada acção fica em ModeracaoUtilizador (quem, quando, porquê), termina as sessões abertas
  e avisa o utilizador por email.

Não há tarefas agendadas: uma suspensão cujo fim já passou levanta-se quando a conta volta a
ser usada (conta_ativa, login) ou quando o admin abre a lista (levantar_expiradas).
"""
import logging
from datetime import datetime, time

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

ACOES = ('suspender', 'banir', 'levantar')


def fim_do_dia(dia):
    """A suspensão "até 05/11" dura o dia 5 inteiro, no fuso da plataforma."""
    from .horarios import fuso
    return datetime.combine(dia, time(23, 59, 59), tzinfo=fuso())


def data_curta(quando):
    from .horarios import fuso
    return timezone.localtime(quando, fuso()).strftime('%d/%m/%Y')


def levantar_expiradas(utilizadores=None):
    """Reactiva as suspensões cujo fim já passou e regista-o no histórico. Devolve quantas."""
    from ..models import Utilizador, ModeracaoUtilizador
    agora = timezone.now()
    qs = utilizadores if utilizadores is not None else Utilizador.objects.all()
    n = 0
    for u in qs.filter(status='suspenso', suspenso_ate__lte=agora).only('id', 'suspenso_ate'):
        with transaction.atomic():
            # condicional: dois pedidos ao mesmo tempo não registam duas vezes
            mudou = Utilizador.objects.filter(pk=u.pk, status='suspenso', suspenso_ate__lte=agora) \
                .update(status='ativo', suspenso_ate=None, motivo_estado='')
            if mudou:
                ModeracaoUtilizador.objects.create(utilizador_id=u.pk, acao='expirou', ate=u.suspenso_ate)
                n += 1
    return n


def mensagem_bloqueio(utilizador):
    """O que a pessoa vê ao tentar entrar (só depois de acertar na password)."""
    motivo = f' Motivo: {utilizador.motivo_estado}' if utilizador.motivo_estado else ''
    if utilizador.status == 'banido':
        return f'A tua conta foi banida.{motivo}'
    if utilizador.status == 'suspenso':
        ate = f' até {data_curta(utilizador.suspenso_ate)}' if utilizador.suspenso_ate else ''
        return f'A tua conta está suspensa{ate}.{motivo}'
    return 'A tua conta não está activa. Contacta o suporte.'


def pode_moderar(quem, alvo, acao):
    """Devolve a razão para recusar, ou None. `quem` é o Utilizador do admin."""
    if alvo.user_id == quem.user_id:
        return 'Não podes moderar a tua própria conta.'
    superadmin = quem.role_admin == 'superadmin'
    if alvo.user.is_staff and not superadmin:
        return 'Só o Super Admin pode moderar contas da equipa de administração.'
    if (acao == 'banir' or alvo.status == 'banido') and not superadmin:
        return 'Só o Super Admin pode banir ou levantar um ban.'
    return None


def moderar(alvo, acao, por, motivo='', ate=None):
    """Aplica a acção (já validada) e regista-a. `ate`: datetime ou None (só para suspender)."""
    from ..models import ModeracaoUtilizador
    from ..autenticacao import terminar_sessoes
    motivo = (motivo or '').strip()[:500]
    with transaction.atomic():
        if acao == 'suspender':
            alvo.status, alvo.suspenso_ate, alvo.motivo_estado = 'suspenso', ate, motivo
        elif acao == 'banir':
            alvo.status, alvo.suspenso_ate, alvo.motivo_estado = 'banido', None, motivo
        else:
            alvo.status, alvo.suspenso_ate, alvo.motivo_estado = 'ativo', None, ''
        alvo.save(update_fields=['status', 'suspenso_ate', 'motivo_estado', 'data_atualizacao'])
        registo = ModeracaoUtilizador.objects.create(
            utilizador=alvo, acao=acao, motivo=motivo, ate=ate if acao == 'suspender' else None, feito_por=por)
        transaction.on_commit(lambda: _avisar(alvo, acao, motivo, ate))
    if acao in ('suspender', 'banir'):
        terminar_sessoes(alvo.user)
    return registo


def _avisar(alvo, acao, motivo, ate):
    email = alvo.user.email
    if not email:
        return
    nome = alvo.user.first_name or alvo.user.username
    linha_motivo = f'\nMotivo: {motivo}\n' if motivo else ''
    suporte = getattr(settings, 'EMAIL_SUPORTE', '')
    contacto = ('Se achas que é um engano, responde a este email.' if suporte
                else 'Se achas que é um engano, contacta a equipa do Bende.')
    if acao == 'suspender':
        quando = f' até {data_curta(ate)}' if ate else ''
        assunto = 'A tua conta Bende foi suspensa'
        texto = (f'Olá {nome},\n\nA tua conta Bende foi suspensa{quando}.\n{linha_motivo}\n'
                 f'Enquanto estiver suspensa não consegues entrar no site nem no POS.'
                 + (' Volta a funcionar sozinha no fim da suspensão.' if ate else '') + f'\n\n{contacto}')
    elif acao == 'banir':
        assunto = 'A tua conta Bende foi banida'
        texto = (f'Olá {nome},\n\nA tua conta Bende foi banida e deixou de ter acesso ao site e ao POS.\n'
                 f'{linha_motivo}\n{contacto}')
    else:
        assunto = 'A tua conta Bende foi reactivada'
        texto = (f'Olá {nome},\n\nA tua conta Bende voltou a estar activa. Já podes entrar em '
                 f'{settings.FRONTEND_BASE_URL}/Login')
    try:
        EmailMessage(subject=assunto, body=texto + '\n\nBende', from_email=settings.DEFAULT_FROM_EMAIL,
                     to=[email], reply_to=[suporte] if suporte else None).send()
    except Exception:
        log.exception('moderação: falhou o email "%s"', assunto)
