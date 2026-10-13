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
import re
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo, available_timezones

from django.utils import timezone

DIAS        = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
DIAS_MINUSC = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
MAX_INTERVALOS_DIA = 4
FUSO_PADRAO = 'Atlantic/Cape_Verde'
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


def janelas(loja, desde, dias=8, tz=None):
    """
    Janelas de abertura concretas [(abre, fecha)] (datetimes no fuso da plataforma) do dia
    anterior a `desde` até `dias` dias depois — o dia anterior apanha os intervalos que passam
    da meia-noite. Janelas que se tocam/sobrepõem são juntas (ex.: 18:00–00:00 + 00:00–02:00).
    """
    tz = tz or desde.tzinfo
    base = desde.date()
    lista = []
    ints = _intervalos(loja)
    for d in range(-1, dias + 1):
        dia = base + timedelta(days=d)
        for dia_semana, abre, fecha in ints:
            if dia_semana != dia.weekday():
                continue
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
    {'ativo', 'aberta', 'fecha_em', 'abre_em', 'texto'} — datetimes no fuso da plataforma.
    Loja sem horário → sempre aberta.
    """
    if not loja.horario_ativo:
        return {'ativo': False, 'aberta': True, 'fecha_em': None, 'abre_em': None, 'texto': ''}
    tz = fuso()
    ref = (quando or timezone.now()).astimezone(tz)
    js = janelas(loja, ref, tz=tz)
    for a, f in js:
        if a <= ref < f:
            return {'ativo': True, 'aberta': True, 'fecha_em': f, 'abre_em': None,
                    'texto': f'Aberta · fecha {_quando(f, ref)}' if f.date() != ref.date()
                             else f'Aberta · fecha às {f:%H:%M}'}
    prox = next((a for a, _ in js if a > ref), None)
    return {'ativo': True, 'aberta': False, 'fecha_em': None, 'abre_em': prox,
            'texto': f'Fechada · abre {_quando(prox, ref)}' if prox else 'Fechada'}


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


def payload_publico(loja, quando=None):
    """O que a loja pública, os cards e o checkout precisam."""
    e = estado(loja, quando)
    if not e['ativo']:
        return {'ativo': False, 'aberta': True}
    return {
        'ativo':        True,
        'aberta':       e['aberta'],
        'texto':        e['texto'],
        'abre_em':      e['abre_em'].isoformat() if e['abre_em'] else None,
        'fecha_em':     e['fecha_em'].isoformat() if e['fecha_em'] else None,
        'fora_horario': loja.fora_horario,
        'hoje':         (quando or timezone.now()).astimezone(fuso()).weekday(),
        'semana':       semana(loja),
    }


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
