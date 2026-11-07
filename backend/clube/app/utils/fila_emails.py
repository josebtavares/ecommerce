"""
Fila de emails: os pedidos só gravam o email (enfileirar), na mesma transacção da acção — se a acção for desfeita,
o email também. O worker (processar_videos → thread própria) envia-os de poucos em poucos segundos:

- prioridades: 1 essencial (conta, segurança, pagamentos e faturas), 2 importante (encomendas, marcações...),
  3 informativo. Perto do limite do Resend, os menos importantes esperam para deixar lugar aos essenciais
  (RESERVA: a prioridade 3 só usa até 70% do limite, a 2 até 90%, a 1 tudo);
- limite: EMAIL_LIMITE_DIA (últimas 24 h) e EMAIL_LIMITE_MES (mês do calendário), por omissão os do plano
  gratuito do Resend (100 / 3000). Ao mudar de plano basta mudar as variáveis;
- falhas: novas tentativas ao fim de 1, 5, 15, 60, 180 min; depois fica "falhou" e os admins são avisados;
- não repete: `chave` única (ex.: o mesmo comprovativo não sai duas vezes);
- privacidade: os anexos apagam-se depois do envio e o registo ao fim de RETENCAO_DIAS.

Os emails internos dos backups (utils/backups.py, backup_media.py, repor_backup.py) não passam aqui: têm de sair
mesmo durante a manutenção, quando a fila está parada.
"""
import logging
import os
import time
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

log = logging.getLogger(__name__)

ESSENCIAL, IMPORTANTE, INFORMATIVO = 1, 2, 3
RESERVA = {ESSENCIAL: 1.0, IMPORTANTE: 0.9, INFORMATIVO: 0.7}
ESPERAS_MIN = (1, 5, 15, 60, 180)          # entre tentativas; depois disto → 'falhou'
ESPERA_LIMITE = timedelta(minutes=10)       # sem lugar no limite: volta a ver daqui a 10 min
PRESO = timedelta(minutes=10)               # 'a_enviar' há mais do que isto = o worker caiu a meio
RETENCAO_DIAS = 30
LOTE = 10
PAUSA_ENTRE = 0.6                           # o Resend aceita 2 pedidos por segundo
AVISO_USO = 0.8                             # avisa os admins quando o dia passa de 80%


def limite_dia():
    return _int_env('EMAIL_LIMITE_DIA', 100)


def limite_mes():
    return _int_env('EMAIL_LIMITE_MES', 3000)


def _int_env(nome, padrao):
    try:
        return max(1, int(os.environ.get(nome, padrao)))
    except (TypeError, ValueError):
        return padrao


# ══════════════════════════════════════════════════════════════
# ENFILEIRAR (nos pedidos)
# ══════════════════════════════════════════════════════════════

def enfileirar(para, assunto, texto, *, tipo, prioridade=IMPORTANTE, botao=None, anexos=(), utilizador=None,
               chave=None, validade=None):
    """Grava o email para o worker enviar. `para`: um email. `botao`: (rótulo, url). `anexos`: [(nome, bytes, mime)].
    `chave`: se já houver um email com ela, não grava outro (devolve None). `validade`: timedelta — depois disto
    já não vale a pena enviar. Devolve o EmailEnviado (ou None se não havia destinatário / era repetido)."""
    from ..models import EmailAnexo, EmailEnviado
    para = (para or '').strip()
    if not para:
        return None
    dados = dict(tipo=tipo[:40], prioridade=prioridade, para=para[:254], utilizador=utilizador,
                 assunto=assunto[:300], texto=texto, chave=chave[:120] if chave else None,
                 botao_texto=(botao[0] if botao else '')[:80], botao_url=(botao[1] if botao else '')[:1000],
                 expira_em=timezone.now() + validade if validade else None)
    try:
        with transaction.atomic():          # savepoint: um repetido não estraga a transacção de quem chama
            e = EmailEnviado.objects.create(**dados)
            for nome, conteudo, mime in anexos:
                EmailAnexo.objects.create(email=e, nome=nome[:200], mime=mime[:100], conteudo=conteudo)
    except IntegrityError:
        if chave and EmailEnviado.objects.filter(chave=dados['chave']).exists():
            return None
        raise
    return e


# ══════════════════════════════════════════════════════════════
# ENVIAR (no worker)
# ══════════════════════════════════════════════════════════════

def uso(agora=None):
    from ..models import EmailEnviado
    agora = agora or timezone.now()
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    enviados = EmailEnviado.objects.filter(enviado_em__isnull=False)
    return {'dia': enviados.filter(enviado_em__gte=agora - timedelta(hours=24)).count(),
            'mes': enviados.filter(enviado_em__gte=inicio_mes).count(),
            'limite_dia': limite_dia(), 'limite_mes': limite_mes()}


def _ha_lugar(prioridade, u):
    f = RESERVA.get(prioridade, RESERVA[INFORMATIVO])
    return u['dia'] < u['limite_dia'] * f and u['mes'] < u['limite_mes'] * f


def _mensagem(e):
    from .email_html import criar
    msg = criar(e.para, e.assunto, e.texto, botao=(e.botao_texto, e.botao_url) if e.botao_texto else None)
    for a in e.anexos.all():
        msg.attach(a.nome, bytes(a.conteudo), a.mime)
    return msg


def _tirar_da_fila(agora):
    """Reserva até LOTE emails prontos (skip_locked: dois workers nunca pegam no mesmo)."""
    from ..models import EmailEnviado
    with transaction.atomic():
        ids = list(EmailEnviado.objects.select_for_update(skip_locked=True)
                   .filter(estado='pendente', proxima_tentativa__lte=agora)
                   .order_by('prioridade', 'criado_em').values_list('id', flat=True)[:LOTE])
        if ids:
            EmailEnviado.objects.filter(id__in=ids).update(estado='a_enviar', proxima_tentativa=agora)
    return ids


def processar(agora=None, pausa=PAUSA_ENTRE):
    """Uma volta da fila. Devolve {'enviados', 'falhas', 'adiados', 'expirados'}."""
    from ..models import EmailEnviado
    agora = agora or timezone.now()
    r = {'enviados': 0, 'falhas': 0, 'adiados': 0, 'expirados': 0}
    # o worker caiu a meio de um envio: volta à fila
    EmailEnviado.objects.filter(estado='a_enviar', proxima_tentativa__lt=agora - PRESO).update(estado='pendente')
    r['expirados'] = EmailEnviado.objects.filter(estado='pendente', expira_em__lt=agora).update(
        estado='cancelado', erro='Fora de prazo: já não fazia sentido enviar.')
    ids = _tirar_da_fila(agora)
    if not ids:
        return r
    u = uso(agora)
    adiados = []
    for e in EmailEnviado.objects.filter(id__in=ids).order_by('prioridade', 'criado_em'):
        if not _ha_lugar(e.prioridade, u):
            adiados.append(e.id)
            continue
        try:
            _mensagem(e).send()
        except Exception as erro:
            e.tentativas += 1
            e.erro = str(erro)[:1000]
            if e.tentativas > len(ESPERAS_MIN):
                e.estado = 'falhou'
                _avisar_falha(e)
            else:
                e.estado = 'pendente'
                e.proxima_tentativa = timezone.now() + timedelta(minutes=ESPERAS_MIN[e.tentativas - 1])
            e.save(update_fields=['tentativas', 'erro', 'estado', 'proxima_tentativa'])
            log.warning('fila de emails: falhou "%s" (%s, tentativa %s)', e.tipo, e.id, e.tentativas)
            r['falhas'] += 1
        else:
            e.estado, e.enviado_em, e.adiado_limite, e.erro = 'enviado', timezone.now(), False, ''
            e.save(update_fields=['estado', 'enviado_em', 'adiado_limite', 'erro'])
            e.anexos.all().delete()            # os PDFs já seguiram: não ficam guardados aqui
            u['dia'] += 1; u['mes'] += 1
            r['enviados'] += 1
            if pausa:
                time.sleep(pausa)
    if adiados:
        EmailEnviado.objects.filter(id__in=adiados).update(
            estado='pendente', adiado_limite=True, proxima_tentativa=agora + ESPERA_LIMITE)
        r['adiados'] = len(adiados)
    _avisar_uso(u, bool(adiados))
    return r


def limpar(agora=None):
    """Apaga o registo antigo (enviados, falhados e cancelados há mais de RETENCAO_DIAS)."""
    from ..models import EmailEnviado
    agora = agora or timezone.now()
    return EmailEnviado.objects.filter(estado__in=('enviado', 'falhou', 'cancelado'),
                                       criado_em__lt=agora - timedelta(days=RETENCAO_DIAS)).delete()[0]


# ══════════════════════════════════════════════════════════════
# AVISOS AOS ADMINS (no sino; nunca por email — não gastam o limite)
# ══════════════════════════════════════════════════════════════

def _admins(titulo, mensagem):
    from ..Views.notificacaoView import notificar_admins
    notificar_admins(tipo='emails', titulo=titulo, mensagem=mensagem, link='/admin/plataforma')


def _avisar_falha(e):
    _admins('Um email não foi enviado',
            f'"{e.assunto}" para {e.para} falhou {e.tentativas} vezes: {e.erro[:200]}. '
            f'Podes voltar a tentar em Admin → Definições → Emails.')


def _avisar_uso(u, houve_adiados):
    """Uma vez por dia: quando o dia passa de 80% do limite, ou quando há emails à espera de lugar."""
    from django.core.cache import cache
    hoje = timezone.localdate().isoformat()
    if houve_adiados and cache.add(f'emails:aviso_adiados:{hoje}', 1, 60 * 60 * 26):
        _admins('Limite de emails atingido',
                f'Já foram enviados {u["dia"]} emails nas últimas 24 h (limite {u["limite_dia"]}) e {u["mes"]} este mês '
                f'(limite {u["limite_mes"]}). Os menos importantes ficam à espera; os essenciais continuam a sair. '
                f'Para enviar mais, muda o plano do Resend e as variáveis EMAIL_LIMITE_DIA / EMAIL_LIMITE_MES.')
    elif (u['dia'] >= u['limite_dia'] * AVISO_USO and not cache.get(f'emails:aviso_adiados:{hoje}')
          and cache.add(f'emails:aviso_uso:{hoje}', 1, 60 * 60 * 26)):
        _admins('Emails perto do limite',
                f'{u["dia"]} de {u["limite_dia"]} emails nas últimas 24 h ({u["mes"]} de {u["limite_mes"]} este mês).')


# ══════════════════════════════════════════════════════════════
# ADMIN (Admin → Definições → Emails)
# ══════════════════════════════════════════════════════════════

def resumo():
    from ..models import EmailEnviado
    from django.db.models import Count
    estados = dict(EmailEnviado.objects.values('estado').annotate(n=Count('id')).values_list('estado', 'n'))
    problemas = EmailEnviado.objects.filter(estado__in=('falhou',)).order_by('-criado_em')[:30]
    adiados = EmailEnviado.objects.filter(estado='pendente', adiado_limite=True).count()
    return {
        'uso': uso(), 'pendentes': estados.get('pendente', 0) + estados.get('a_enviar', 0), 'adiados': adiados,
        'falhados': estados.get('falhou', 0), 'enviados_registo': estados.get('enviado', 0),
        'retencao_dias': RETENCAO_DIAS,
        'falhas': [{'id': e.id, 'tipo': e.tipo, 'para': e.para, 'assunto': e.assunto, 'erro': e.erro[:300],
                    'tentativas': e.tentativas, 'criado_em': e.criado_em.isoformat()} for e in problemas],
    }


def tentar_outra_vez(ids=None):
    """Falhados (todos ou os `ids`) → de volta à fila, com as tentativas a zero."""
    from ..models import EmailEnviado
    qs = EmailEnviado.objects.filter(estado='falhou')
    if ids is not None:
        qs = qs.filter(id__in=ids)
    return qs.update(estado='pendente', tentativas=0, proxima_tentativa=timezone.now(), erro='')
