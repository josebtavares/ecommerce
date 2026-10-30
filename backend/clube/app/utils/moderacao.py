"""
Suspender, banir e reactivar contas (Admin → Utilizadores).

- suspender: temporário, com data de fim opcional; o suporte e o superadmin podem.
- banir: permanente; só o superadmin bane e levanta. O email fica preso à conta (é único),
  por isso não dá para criar outra conta com ele, nem pelo Google.
- Cada acção fica em ModeracaoUtilizador (quem, quando, porquê), termina as sessões abertas
  e avisa o utilizador por email.
- banir suspende as lojas e os POS do dono (motivo MOTIVO_BAN; o motivo do ban não aparece na
  loja, que os gestores vêem). O registo do ban guarda como estavam; sair do ban repõe-nos.
  As encomendas pagas continuam a ser tratadas pelos gestores; as por pagar são canceladas.
- suspender só suspende as lojas e os POS se o admin o pedir (incluir_lojas; motivo
  MOTIVO_SUSPENSO) — ex.: o problema é a loja, ou o dono é o único a tratar das encomendas.
  Sem isso a loja continua a vender. No fim da suspensão (também a automática) voltam como estavam.

Não há tarefas agendadas: uma suspensão cujo fim já passou levanta-se quando a conta volta a
ser usada (conta_ativa, login) ou quando o admin abre a lista (levantar_expiradas).
"""
import logging
from datetime import datetime, time

from django.conf import settings
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

ACOES = ('suspender', 'banir', 'levantar')
MOTIVO_BAN = 'Conta do dono banida'
MOTIVO_SUSPENSO = 'Conta do dono suspensa'
MOTIVO_ELIMINADO = 'Conta do dono eliminada'      # utils/eliminacao.py
MOTIVOS_DONO = (MOTIVO_BAN, MOTIVO_SUSPENSO, MOTIVO_ELIMINADO)


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
                _repor_ultimo(u)
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


def dono_banido(dono_id):
    from ..models import Utilizador
    return Utilizador.objects.filter(pk=dono_id, status='banido').exists()


def recusa_reativar(dono_id, motivo):
    """Razão para o admin não reactivar uma loja/POS por causa da conta do dono, ou None."""
    if dono_banido(dono_id):
        return 'O dono está banido — levanta o ban em Utilizadores e volta ao estado em que estava.'
    if motivo == MOTIVO_ELIMINADO:
        return 'O dono apagou a conta (ou pediu para a apagar) — a loja não pode voltar a abrir.'
    if motivo == MOTIVO_SUSPENSO:
        return ('Foi suspensa com a conta do dono — reactiva a conta em Utilizadores e volta ao estado '
                'em que estava.')
    return None


def _suspender_do_dono(alvo, motivo_loja=MOTIVO_BAN):
    """Suspende as lojas e os POS do dono. Devolve como estavam (para os repor)."""
    from ..models import Loja
    from ..pos.models import ConfiguracaoPOS
    lojas, pos = [], []
    for loja in Loja.objects.filter(dono=alvo).order_by('id'):
        lojas.append({'id': loja.id, 'nome': loja.nome, 'estado': loja.estado, 'motivo': loja.estado_motivo})
        # também as já suspensas (ex.: falta de pagamento): com o motivo do ban, pagar não as reabre
        loja.mudar_estado('suspensa', motivo_loja)
    for p in ConfiguracaoPOS.objects.select_for_update().filter(dono=alvo).order_by('id'):
        pos.append({'id': p.id, 'nome': p.nome, 'suspenso': p.suspenso, 'motivo': p.suspenso_motivo})
        p.suspenso, p.suspenso_motivo = True, motivo_loja
        p.suspenso_em = p.suspenso_em or timezone.now()
        p.save(update_fields=['suspenso', 'suspenso_motivo', 'suspenso_em', 'atualizado_em'])
    return {'lojas': lojas, 'pos': pos}


def _repor_ultimo(alvo):
    """A conta sai do ban/suspensão: repõe o que o último ban/suspensão suspendeu (se suspendeu)."""
    from ..models import ModeracaoUtilizador
    ultimo = ModeracaoUtilizador.objects.filter(utilizador_id=alvo.pk, acao__in=('banir', 'suspender')).first()
    if ultimo and ultimo.afetados:
        _repor_do_dono(ultimo)


def _repor_do_dono(registo):
    """Sai do ban (ou da suspensão com lojas): cada loja/POS suspensa volta a como estava. Os que o admin já
    mudou entretanto ficam como estão. A subscrição manda no fim: paga durante o ban → volta
    activa; ficou por pagar durante o ban → fica suspensa por falta de pagamento."""
    from ..models import Loja, Subscricao
    from ..pos.models import ConfiguracaoPOS
    from .subscricoes import MOTIVO_SUSPENSAO
    por_pagar = f'{MOTIVO_SUSPENSAO}.'
    for a in registo.afetados.get('lojas', []):
        loja = Loja.objects.filter(pk=a['id'], estado='suspensa', estado_motivo__in=MOTIVOS_DONO).first()
        if not loja:
            continue
        estado, motivo = a['estado'], a['motivo']
        sub_suspensa = Subscricao.objects.filter(loja=loja, estado='suspensa').exists()
        if estado == 'suspensa' and motivo.startswith(MOTIVO_SUSPENSAO) and not sub_suspensa:
            estado, motivo = 'ativa', ''
        elif estado == 'ativa' and sub_suspensa:
            estado, motivo = 'suspensa', por_pagar
        loja.mudar_estado(estado, motivo)
    for a in registo.afetados.get('pos', []):
        p = ConfiguracaoPOS.objects.select_for_update().filter(pk=a['id'], suspenso=True, suspenso_motivo__in=MOTIVOS_DONO).first()
        if not p:
            continue
        suspenso, motivo = a['suspenso'], a['motivo']
        sub_suspensa = Subscricao.objects.filter(pos=p, estado='suspensa').exists()
        if suspenso and motivo.startswith(MOTIVO_SUSPENSAO) and not sub_suspensa:
            suspenso = False
        elif not suspenso and sub_suspensa:
            suspenso, motivo = True, por_pagar
        p.suspenso, p.suspenso_motivo = suspenso, (motivo if suspenso else '')
        if not suspenso:
            p.suspenso_em = None
        p.save(update_fields=['suspenso', 'suspenso_motivo', 'suspenso_em', 'atualizado_em'])


def pode_moderar(quem, alvo, acao):
    """Devolve a razão para recusar, ou None. `quem` é o Utilizador do admin."""
    if alvo.user_id == quem.user_id:
        return 'Não podes moderar a tua própria conta.'
    if alvo.status == 'eliminado':
        return 'Esta conta foi apagada.'
    superadmin = quem.role_admin == 'superadmin'
    if alvo.user.is_staff and not superadmin:
        return 'Só o Super Admin pode moderar contas da equipa de administração.'
    if (acao == 'banir' or alvo.status == 'banido') and not superadmin:
        return 'Só o Super Admin pode banir ou levantar um ban.'
    if acao == 'banir' and alvo.status == 'banido':
        return 'A conta já está banida.'
    return None


def moderar(alvo, acao, por, motivo='', ate=None, incluir_lojas=False):
    """Aplica a acção (já validada) e regista-a. `ate`: datetime ou None (só para suspender).
    incluir_lojas: suspender também as lojas e os POS (o ban suspende-os sempre)."""
    from ..models import ModeracaoUtilizador, Utilizador
    from ..autenticacao import terminar_sessoes
    motivo = (motivo or '').strip()[:500]
    with transaction.atomic():
        # dois pedidos ao mesmo tempo (ex.: banir duas vezes): o segundo via o estado antigo e
        # registava as lojas já suspensas pelo ban como "estado anterior" — nunca mais voltavam
        atual = Utilizador.objects.select_for_update().only('status').get(pk=alvo.pk)
        if atual.status != alvo.status:
            raise ValueError('A conta mudou entretanto. Abre-a outra vez.')
        afetados = {}
        if alvo.status in ('banido', 'suspenso'):
            # sai do estado anterior: o que ele suspendeu volta como estava (o novo volta a suspender)
            _repor_ultimo(alvo)
        if acao == 'banir':
            afetados = _suspender_do_dono(alvo)
        elif acao == 'suspender' and incluir_lojas:
            afetados = _suspender_do_dono(alvo, MOTIVO_SUSPENSO)
        if acao == 'suspender':
            alvo.status, alvo.suspenso_ate, alvo.motivo_estado = 'suspenso', ate, motivo
        elif acao == 'banir':
            alvo.status, alvo.suspenso_ate, alvo.motivo_estado = 'banido', None, motivo
        else:
            alvo.status, alvo.suspenso_ate, alvo.motivo_estado = 'ativo', None, ''
        alvo.save(update_fields=['status', 'suspenso_ate', 'motivo_estado', 'data_atualizacao'])
        registo = ModeracaoUtilizador.objects.create(
            utilizador=alvo, acao=acao, motivo=motivo, ate=ate if acao == 'suspender' else None, feito_por=por,
            afetados=afetados)
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
    from .email_html import criar
    try:
        criar(email, assunto, texto).send()
    except Exception:
        log.exception('moderação: falhou o email "%s"', assunto)
