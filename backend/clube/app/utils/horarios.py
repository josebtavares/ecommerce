"""
Horário das lojas.

- Todas as horas são lidas no fuso da plataforma (ConfiguracaoPlataforma.fuso_horario,
  gerido pelo admin do site; por defeito Cabo Verde).
- Loja com horario_ativo=False → aberta 24h (o comportamento de sempre).
- Cada HorarioLoja é um intervalo num dia da semana; fecha <= abre → passa da meia-noite
  (00:00–00:00 = o dia inteiro).
- Loja fechada no checkout: fora_horario 'agendar' → a encomenda fica para a próxima abertura
  (Encomenda.agendada_para); 'bloquear' → não aceita.
"""
import math
import re
from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo, available_timezones

from django.utils import timezone

DIAS        = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
DIAS_MINUSC = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
MAX_INTERVALOS_DIA = 4
FUSO_PADRAO = 'Atlantic/Cape_Verde'
MAX_DIAS_ABERTURA = 8   # regra 'agendar': aceita encomendas para a reabertura até 8 dias depois
HORA_RE = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')


# ── Fuso ──────────────────────────────────────────────────────

def fuso_valido(nome):
    return isinstance(nome, str) and nome in available_timezones()


def fuso():
    from ..models import ConfiguracaoPlataforma
    nome = ConfiguracaoPlataforma.atual().fuso_horario
    try:
        return ZoneInfo(nome)
    except Exception:
        return ZoneInfo(FUSO_PADRAO)


def agora():
    return timezone.now().astimezone(fuso())


# ── Janelas de abertura ───────────────────────────────────────

def _intervalos(loja):
    # .all() aproveita o prefetch_related('horarios') das listagens
    return [(h.dia_semana, h.abre, h.fecha) for h in loja.horarios.all()]


def _excecoes(loja):
    # .all() aproveita o prefetch_related('excecoes')
    return list(loja.excecoes.all())


def excecao_do_dia(excecoes, dia):
    return next((e for e in excecoes if e.inicio <= dia <= e.fim), None)


def _intervalos_do_dia(loja, dia, semanal, excecoes):
    """[(abre, fecha)] de um dia: a exceção (feriado/férias) manda; sem horário = dia inteiro."""
    ex = excecao_do_dia(excecoes, dia)
    if ex is not None:
        return [(time.fromisoformat(i['abre']), time.fromisoformat(i['fecha'])) for i in ex.intervalos or []]
    if not loja.horario_ativo:
        return [(time(0), time(0))]
    return semanal.get(dia.weekday(), [])


def pausa_ativa(loja, ref=None):
    ref = ref or timezone.now()
    return bool(loja.pausa_ate and loja.pausa_ate > ref)


def janelas(loja, desde, dias=8, tz=None, encomendas=True):
    """
    Janelas de abertura concretas [(abre, fecha)] (datetimes no fuso da plataforma) do dia
    anterior a `desde` até `dias` dias depois — o dia anterior apanha os intervalos que passam
    da meia-noite. Janelas que se tocam/sobrepõem são juntas (ex.: 18:00–00:00 + 00:00–02:00).
    Conta com os dias especiais (ExcecaoHorario). Loja sem horário = aberta o dia todo.
    encomendas=True → as janelas em que se aceitam encomendas: menos a última meia hora (ou o
    que a loja definir em ultima_encomenda_min) e sem o tempo da pausa ("Fechar agora").
    """
    tz = tz or desde.tzinfo
    base = desde.date()
    semanal = {}
    for dia_semana, abre, fecha in _intervalos(loja):
        semanal.setdefault(dia_semana, []).append((abre, fecha))
    excecoes = _excecoes(loja)
    lista = []
    for d in range(-1, dias + 1):
        dia = base + timedelta(days=d)
        for abre, fecha in _intervalos_do_dia(loja, dia, semanal, excecoes):
            a = datetime.combine(dia, abre, tzinfo=tz)
            f = datetime.combine(dia, fecha, tzinfo=tz)
            if fecha <= abre:
                f = datetime.combine(dia + timedelta(days=1), fecha, tzinfo=tz)
            lista.append((a, f))
    lista.sort()
    juntas = []
    for a, f in lista:
        if juntas and a <= juntas[-1][1]:
            juntas[-1] = (juntas[-1][0], max(juntas[-1][1], f))
        else:
            juntas.append((a, f))
    if not encomendas:
        return juntas
    corte = timedelta(minutes=loja.ultima_encomenda_min or 0)
    if corte:
        juntas = [(a, f - corte) for a, f in juntas if f - corte > a]
    if pausa_ativa(loja, desde):
        p = loja.pausa_ate.astimezone(tz)
        juntas = [(max(a, p), f) for a, f in juntas if f > p]
    return juntas


def _quando(dt, ref):
    """'hoje às 14:00', 'amanhã às 08:00', 'sexta às 08:00', 'dia 24/12 às 08:00'."""
    hora = dt.strftime('%H:%M')
    dias = (dt.date() - ref.date()).days
    if dias == 0:
        return f'hoje às {hora}'
    if dias == 1:
        return f'amanhã às {hora}'
    if dias < 7:
        return f'{DIAS_MINUSC[dt.weekday()]} às {hora}'
    return f'dia {dt:%d/%m} às {hora}'


def estado(loja, quando=None):
    """
    {'ativo', 'aberta', 'fecha_em', 'abre_em', 'texto', 'pausa'} — datetimes no fuso da plataforma.
    'aberta' = aceita encomendas agora (conta com a pausa e a hora da última encomenda).
    'ativo'  = mostrar o selo: loja com horário, ou fechada agora (pausa / dia especial).
    Loja sem horário e sem pausa nem dia especial → sempre aberta, sem selo (como antes).
    """
    tz = fuso()
    ref = (quando or timezone.now()).astimezone(tz)
    pausa = pausa_ativa(loja, ref)
    if not loja.horario_ativo and not pausa and not _excecoes(loja):
        return {'ativo': False, 'aberta': True, 'fecha_em': None, 'abre_em': None, 'texto': '', 'pausa': False}
    js = janelas(loja, ref, tz=tz)
    corte = bool(loja.ultima_encomenda_min)
    for a, f in js:
        if a <= ref < f:
            if not loja.horario_ativo:      # 24h com um dia especial noutra altura → sem selo
                return {'ativo': False, 'aberta': True, 'fecha_em': None, 'abre_em': None, 'texto': '', 'pausa': False}
            verbo = 'encomendas até' if corte else 'fecha'
            texto = (f'Aberta · {verbo} {_quando(f, ref)}' if f.date() != ref.date()
                     else f'Aberta · {verbo} às {f:%H:%M}')
            return {'ativo': True, 'aberta': True, 'fecha_em': f, 'abre_em': None, 'texto': texto, 'pausa': False}
    prox = next((a for a, _ in js if a > ref), None)
    if prox is None:
        # férias/dias especiais longos: procura a reabertura mais à frente (só nestes casos, que são raros)
        prox = next((a for a, _ in janelas(loja, ref, dias=MAX_DIAS_EXCECAO + 8, tz=tz) if a > ref), None)
    if pausa and prox and prox == loja.pausa_ate.astimezone(tz):
        texto = f'Fechada · reabre às {prox:%H:%M}' if prox.date() == ref.date() else f'Fechada · reabre {_quando(prox, ref)}'
    else:
        texto = f'Fechada · abre {_quando(prox, ref)}' if prox else 'Fechada'
    return {'ativo': True, 'aberta': False, 'fecha_em': None, 'abre_em': prox, 'texto': texto, 'pausa': pausa}


def quando_texto(dt, quando=None):
    """Texto de uma data agendada ('amanhã às 08:00') no fuso da plataforma."""
    if dt is None:
        return ''
    tz = fuso()
    return _quando(dt.astimezone(tz), (quando or timezone.now()).astimezone(tz))


def semana(loja):
    """[{dia, nome, intervalos: [{abre, fecha}]}] — segunda a domingo."""
    dias = [{'dia': i, 'nome': DIAS[i], 'intervalos': []} for i in range(7)]
    for dia_semana, abre, fecha in sorted(_intervalos(loja)):
        dias[dia_semana]['intervalos'].append({'abre': abre.strftime('%H:%M'), 'fecha': fecha.strftime('%H:%M')})
    return dias


def _texto_excecao(e):
    datas = f'{e.inicio:%d/%m}' if e.inicio == e.fim else f'{e.inicio:%d/%m} a {e.fim:%d/%m}'
    horas = ' · '.join(f'{i["abre"]}–{i["fecha"]}' for i in e.intervalos) if e.intervalos else 'Fechado'
    return f'{datas}: {horas}'


def excecoes_proximas(loja, quando=None, dias=30, maximo=5):
    """Dias especiais de hoje a `dias` dias — para o cliente ver no horário da loja."""
    hoje = (quando or timezone.now()).astimezone(fuso()).date()
    ate = hoje + timedelta(days=dias)
    lista = [e for e in _excecoes(loja) if e.fim >= hoje and e.inicio <= ate][:maximo]
    return [{'inicio': e.inicio.isoformat(), 'fim': e.fim.isoformat(), 'texto': _texto_excecao(e),
             'mensagem': e.mensagem, 'fechado': not e.intervalos} for e in lista]


def payload_publico(loja, quando=None):
    """O que a loja pública, os cards e o checkout precisam."""
    e = estado(loja, quando)
    if not e['ativo']:
        return {'ativo': False, 'aberta': True}
    ref = (quando or timezone.now()).astimezone(fuso())
    ex_hoje = excecao_do_dia(_excecoes(loja), ref.date())
    return {
        'ativo':        True,
        'aberta':       e['aberta'],
        'texto':        e['texto'],
        'abre_em':      e['abre_em'].isoformat() if e['abre_em'] else None,
        'fecha_em':     e['fecha_em'].isoformat() if e['fecha_em'] else None,
        'fora_horario': loja.fora_horario,
        'hoje':         ref.weekday(),
        'semana':       semana(loja) if loja.horario_ativo else [],
        'pausa':        e['pausa'],
        'ultima_encomenda': loja.ultima_encomenda_min,
        'aviso':        ex_hoje.mensagem if ex_hoje and ex_hoje.mensagem else '',   # ex.: "Férias — voltamos dia 16"
        'excecoes':     excecoes_proximas(loja, quando),
    }


# ── Agendamento pelo cliente (dia e hora para receber/levantar) ──

INTERVALOS_AGENDAMENTO = (15, 30, 60, 120)
MAX_DIAS_AGENDAMENTO = 60
MAX_ANTECEDENCIA = 24 * 60
DIAS_CURTOS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


def vagas(loja, quando=None):
    """
    Horas que o cliente pode escolher: dentro do horário (ou o dia todo, se a loja não tem
    horário), a partir de agora + antecedência, até `agendamento_dias` dias (hoje incluído),
    de `agendamento_intervalo` em `agendamento_intervalo` minutos (08:00, 08:30, …).
    Devolve [(date, [datetime, …])] por dia, só os dias com horas livres.
    """
    tz = fuso()
    ref = (quando or timezone.now()).astimezone(tz)
    passo = loja.agendamento_intervalo if loja.agendamento_intervalo in INTERVALOS_AGENDAMENTO else 30
    dias = max(1, min(loja.agendamento_dias or 1, MAX_DIAS_AGENDAMENTO))
    inicio = ref + timedelta(minutes=min(loja.agendamento_antecedencia or 0, MAX_ANTECEDENCIA))
    ultimo_dia = ref.date() + timedelta(days=dias - 1)

    # horário (ou o dia todo), dias especiais, pausa e hora da última encomenda
    js = janelas(loja, ref, dias=dias + 1, tz=tz)

    por_dia = {}
    for a, f in js:
        t = max(a, inicio)
        # alinha ao relógio do dia (08:00, 08:30…), nunca antes da abertura
        meia_noite = datetime.combine(t.date(), time(0), tzinfo=tz)
        segundos = (t - meia_noite).total_seconds()
        t = meia_noite + timedelta(minutes=math.ceil(segundos / 60 / passo) * passo)
        while t < f and t.date() <= ultimo_dia:
            por_dia.setdefault(t.date(), set()).add(t)
            t += timedelta(minutes=passo)
    return [(d, sorted(por_dia[d])) for d in sorted(por_dia)]


def _rotulo_dia(d, ref):
    dias = (d - ref.date()).days
    if dias == 0:
        return 'Hoje'
    if dias == 1:
        return 'Amanhã'
    return f'{DIAS_CURTOS[d.weekday()]} {d:%d/%m}'


def vagas_payload(loja, quando=None):
    ref = (quando or timezone.now()).astimezone(fuso())
    return [{'data': d.isoformat(), 'nome': DIAS[d.weekday()], 'rotulo': _rotulo_dia(d, ref),
             'horas': [t.strftime('%H:%M') for t in ts]} for d, ts in vagas(loja, quando)]


def validar_vaga(loja, texto, quando=None):
    """'2026-10-14T13:30' (hora local da plataforma) → (datetime, None) ou (None, mensagem)."""
    try:
        dt = datetime.fromisoformat(str(texto).strip())
    except (TypeError, ValueError):
        return None, 'Data/hora de agendamento inválida.'
    tz = fuso()
    dt = dt.astimezone(tz) if dt.tzinfo else dt.replace(tzinfo=tz)
    for d, ts in vagas(loja, quando):
        if d == dt.date():
            if any(t == dt for t in ts):
                return next(t for t in ts if t == dt), None
            break
    return None, 'Essa hora já não está disponível — escolhe outra.'


def agendamento_publico(loja):
    if not loja.agendamento_ativo:
        return {'ativo': False}
    return {'ativo': True, 'intervalo': loja.agendamento_intervalo, 'dias': loja.agendamento_dias,
            'antecedencia': loja.agendamento_antecedencia}


def texto_agendada(dt):
    """'Quarta 14/10 às 13:30' (no fuso da plataforma)."""
    if not dt:
        return ''
    d = dt.astimezone(fuso())
    return f'{DIAS[d.weekday()]} {d:%d/%m} às {d:%H:%M}'


def agendadas_fora(loja, quando=None, maximo=50):
    """
    Encomendas por entregar agendadas para uma hora em que a loja, com o horário actual, está fechada
    (ex.: o dono marcou feriado num dia que já tinha encomendas). Não se mudam sozinhas — o backoffice
    avisa para a loja falar com os clientes.
    """
    from ..models import Encomenda
    tz = fuso()
    ref = (quando or timezone.now()).astimezone(tz)
    qs = (Encomenda.objects.filter(loja=loja, agendada_para__gte=ref)
          .exclude(status__in=['enviado', 'concluido', 'cancelado'])
          .select_related('comprador__user').order_by('agendada_para'))
    lista = list(qs[:500])
    if not lista:
        return []
    dias = (lista[-1].agendada_para.astimezone(tz).date() - ref.date()).days + 1
    js = janelas(loja, ref, dias=dias, tz=tz, encomendas=False)
    fora = [e for e in lista if not any(a <= e.agendada_para < f for a, f in js)]
    return [{'id': e.id, 'quando': texto_agendada(e.agendada_para), 'status': e.status,
             'cliente': e.comprador.nome or e.comprador.user.username} for e in fora[:maximo]]


# ── Gravar (backoffice) ───────────────────────────────────────

def _min(hhmm):
    h, m = hhmm.split(':')
    return int(h) * 60 + int(m)


def validar_dias(dias):
    """
    dias = [{dia: 0-6, intervalos: [{abre: 'HH:MM', fecha: 'HH:MM'}]}]
    Devolve ([(dia, time abre, time fecha)], None) ou (None, mensagem).
    """
    if not isinstance(dias, list):
        return None, 'Formato do horário inválido.'
    linhas, vistos = [], set()
    por_dia = {}
    for d in dias:
        if not isinstance(d, dict):
            return None, 'Formato do horário inválido.'
        try:
            dia = int(d.get('dia'))
        except (TypeError, ValueError):
            return None, 'Dia da semana inválido.'
        if dia < 0 or dia > 6 or dia in vistos:
            return None, 'Dia da semana inválido.'
        vistos.add(dia)
        ints = d.get('intervalos') or []
        if not isinstance(ints, list):
            return None, 'Formato do horário inválido.'
        if len(ints) > MAX_INTERVALOS_DIA:
            return None, f'{DIAS[dia]}: no máximo {MAX_INTERVALOS_DIA} intervalos por dia.'
        segs = []
        for i in ints:
            abre, fecha = str((i or {}).get('abre', '')), str((i or {}).get('fecha', ''))
            if not HORA_RE.match(abre) or not HORA_RE.match(fecha):
                return None, f'{DIAS[dia]}: hora inválida (usa HH:MM).'
            a, f = _min(abre), _min(fecha)
            if a == f and not (a == 0 and f == 0):
                return None, f'{DIAS[dia]}: a hora de fecho tem de ser diferente da de abertura.'
            fim = f if f > a else f + 1440          # passa da meia-noite (00:00–00:00 = dia inteiro)
            segs.append((a, fim, abre, fecha))
        segs.sort()
        for (a1, f1, ab1, fe1), (a2, f2, ab2, fe2) in zip(segs, segs[1:]):
            if a2 < f1:
                return None, f'{DIAS[dia]}: os intervalos {ab1}–{fe1} e {ab2}–{fe2} sobrepõem-se.'
        if any(f > 1440 for _, f, _, _ in segs[:-1]):
            return None, f'{DIAS[dia]}: só o último intervalo do dia pode passar da meia-noite.'
        por_dia[dia] = segs
        for a, f, abre, fecha in segs:
            linhas.append((dia, time(a // 60, a % 60), time(_min(fecha) // 60, _min(fecha) % 60)))

    # o intervalo que passa da meia-noite não pode entrar no horário do dia seguinte
    for dia, segs in por_dia.items():
        if segs and segs[-1][1] > 1440:
            seguinte = por_dia.get((dia + 1) % 7) or []
            if seguinte and seguinte[0][0] < segs[-1][1] - 1440:
                return None, (f'{DIAS[dia]}: o intervalo {segs[-1][2]}–{segs[-1][3]} entra no horário de '
                              f'{DIAS[(dia + 1) % 7].lower()}.')
    return linhas, None


def guardar(loja, linhas):
    from ..models import HorarioLoja
    loja.horarios.all().delete()
    HorarioLoja.objects.bulk_create([HorarioLoja(loja=loja, dia_semana=d, abre=a, fecha=f) for d, a, f in linhas])


# ── Dias especiais (feriados, férias, horário diferente) ─────────

MAX_EXCECOES = 30
MAX_DIAS_EXCECAO = 92


def validar_excecoes(lista, quando=None):
    """
    [{inicio: 'AAAA-MM-DD', fim, intervalos: [{abre, fecha}] (vazio = fechado), mensagem}]
    Devolve ([dict limpo], None) ou (None, mensagem). As que já acabaram são ignoradas.
    """
    if not isinstance(lista, list):
        return None, 'Formato dos dias especiais inválido.'
    if len(lista) > MAX_EXCECOES:
        return None, f'No máximo {MAX_EXCECOES} dias especiais.'
    hoje = (quando or timezone.now()).astimezone(fuso()).date()
    limpas = []
    for e in lista:
        if not isinstance(e, dict):
            return None, 'Formato dos dias especiais inválido.'
        try:
            inicio = date.fromisoformat(str(e.get('inicio')))
            fim = date.fromisoformat(str(e.get('fim') or e.get('inicio')))
        except ValueError:
            return None, 'Dia especial: data inválida.'
        if fim < inicio:
            return None, f'Dia especial {inicio:%d/%m}: a data de fim é antes da de início.'
        if (fim - inicio).days >= MAX_DIAS_EXCECAO:
            return None, f'Dia especial {inicio:%d/%m}: no máximo {MAX_DIAS_EXCECAO} dias seguidos.'
        if fim < hoje:
            continue
        ints = e.get('intervalos') or []
        linhas, msg = validar_dias([{'dia': 0, 'intervalos': ints}])
        if msg:
            return None, f'Dia especial {inicio:%d/%m}: ' + msg.split(': ', 1)[-1]
        mensagem = str(e.get('mensagem') or '').strip()
        if len(mensagem) > 120:
            return None, f'Dia especial {inicio:%d/%m}: mensagem com mais de 120 caracteres.'
        limpas.append({'inicio': inicio, 'fim': fim, 'mensagem': mensagem,
                       'intervalos': [{'abre': f'{a:%H:%M}', 'fecha': f'{f:%H:%M}'} for _, a, f in linhas]})
    limpas.sort(key=lambda x: x['inicio'])
    for x, y in zip(limpas, limpas[1:]):
        if y['inicio'] <= x['fim']:
            return None, f'Os dias especiais {x["inicio"]:%d/%m} e {y["inicio"]:%d/%m} sobrepõem-se.'
    return limpas, None


def guardar_excecoes(loja, limpas):
    from ..models import ExcecaoHorario
    loja.excecoes.all().delete()
    ExcecaoHorario.objects.bulk_create([ExcecaoHorario(loja=loja, **x) for x in limpas])


def excecoes_backoffice(loja, quando=None):
    hoje = (quando or timezone.now()).astimezone(fuso()).date()
    return [{'inicio': e.inicio.isoformat(), 'fim': e.fim.isoformat(), 'intervalos': e.intervalos,
             'mensagem': e.mensagem} for e in loja.excecoes.all() if e.fim >= hoje]


# ── "Fechar agora" (pausa) ───────────────────────────────────────

PAUSAS_MINUTOS = (15, 30, 60, 120, 240)


def pausar(loja, minutos=None, ate_fechar=False, quando=None):
    """Fecha a loja para encomendas por `minutos` ou até ao fim do horário de agora. → (ok, msg)."""
    ref = (quando or timezone.now()).astimezone(fuso())
    e = estado(loja, ref)
    if not e['aberta']:
        return False, 'A loja já está fechada.'
    if ate_fechar:
        if not loja.horario_ativo or not e['fecha_em']:
            return False, 'Esta loja não tem horário — escolhe por quanto tempo fecha.'
        ate = e['fecha_em']
    else:
        if minutos not in PAUSAS_MINUTOS:
            return False, 'Escolhe 15 min, 30 min, 1 hora, 2 horas ou 4 horas.'
        ate = ref + timedelta(minutes=minutos)
    loja.pausa_ate = ate
    loja.save(update_fields=['pausa_ate', 'data_atualizacao'])
    limpar_cache_fechadas()
    return True, ''


def reabrir(loja):
    loja.pausa_ate = None
    loja.save(update_fields=['pausa_ate', 'data_atualizacao'])
    limpar_cache_fechadas()


# ── Lojas abertas primeiro (listagens) ────────────────────────────

CACHE_FECHADAS = 'lojas_fechadas_ids'


def limpar_cache_fechadas():
    from django.core.cache import cache
    cache.delete(CACHE_FECHADAS)


def ids_fechadas():
    """Ids das lojas activas fechadas agora (cache de 1 minuto — o horário muda à hora certa)."""
    from django.core.cache import cache
    from django.db.models import Q
    from ..models import Loja
    ids = cache.get(CACHE_FECHADAS)
    if ids is None:
        hoje = agora().date()
        candidatas = (Loja.objects.filter(ativa=True)
                      .filter(Q(horario_ativo=True) | Q(pausa_ate__gt=timezone.now()) | Q(excecoes__fim__gte=hoje))
                      .distinct().prefetch_related('horarios', 'excecoes'))
        ids = [l.id for l in candidatas if not estado(l)['aberta']]
        cache.set(CACHE_FECHADAS, ids, 60)
    return ids


# ── Aviso das encomendas agendadas para hoje (worker) ─────────────

def avisar_agendadas(quando=None):
    """
    Uma vez por dia e por loja, à hora de abrir (08:00 nas lojas sem horário), avisa a equipa
    (dono/gestor/staff) de quantas encomendas estão agendadas para hoje, e cada condutor das
    entregas que tem atribuídas. Chamado pelo worker (processar_videos) a cada minuto.
    Devolve o número de lojas avisadas.
    """
    from ..models import Loja, Encomenda, Entrega
    from ..Views.notificacaoView import notificar, notificar_staff
    tz = fuso()
    ref = (quando or timezone.now()).astimezone(tz)
    hoje = ref.date()
    de = datetime.combine(hoje, time(0), tzinfo=tz)
    ate = de + timedelta(days=1)
    # só as que há para preparar: por pagar ('pendente'), canceladas e concluídas não contam
    hoje_qs = (Encomenda.objects.filter(agendada_para__gte=de, agendada_para__lt=ate)
               .exclude(status__in=['pendente', 'cancelado', 'concluido']))
    lojas = (Loja.objects.filter(id__in=hoje_qs.values('loja'), ativa=True)
             .exclude(aviso_agendadas_data=hoje).prefetch_related('horarios', 'excecoes'))
    avisadas = 0
    for loja in lojas:
        js = [a for a, _ in janelas(loja, ref, dias=0, tz=tz, encomendas=False) if a.date() == hoje]
        abre = min(js) if (js and loja.horario_ativo) else datetime.combine(hoje, time(8), tzinfo=tz)
        if ref < abre:
            continue
        do_dia = hoje_qs.filter(loja=loja)
        n = do_dia.count()
        link = f'/loja/{loja.id}/backoffice'
        titulo = f'{n} encomenda{"s" if n != 1 else ""} agendada{"s" if n != 1 else ""} para hoje'
        notificar_staff(loja=loja, roles=['dono', 'gestor'], tipo='agendadas_hoje', titulo=titulo,
                        mensagem='Vê-as em Entregas → Calendário.', link=link)
        # o staff não tem o calendário (Entregas é do dono/gestor/condutor) — vê-as nas Encomendas
        notificar_staff(loja=loja, roles=['staff'], tipo='agendadas_hoje', titulo=titulo,
                        mensagem='Vê-as em Encomendas → Agendadas.', link=link)
        por_condutor = {}
        for en in Entrega.objects.filter(encomenda__in=do_dia, condutor__isnull=False).select_related('condutor__utilizador'):
            por_condutor.setdefault(en.condutor.utilizador, 0)
            por_condutor[en.condutor.utilizador] += 1
        for ut, k in por_condutor.items():
            notificar(utilizador=ut, tipo='agendadas_hoje', titulo=f'Tens {k} entrega{"s" if k != 1 else ""} para hoje',
                      mensagem=f'{loja.nome} · vê-as em Entregas → Calendário.', loja=loja, link=link)
        loja.aviso_agendadas_data = hoje
        loja.save(update_fields=['aviso_agendadas_data'])
        avisadas += 1
    return avisadas
