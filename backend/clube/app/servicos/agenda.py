"""
Agenda dos profissionais: quando trabalham, o que está ocupado e as horas livres.

Horário de um profissional num dia (no fuso da plataforma, Cabo Verde):
  - os seus blocos semanais (HorarioProfissional); sem blocos = o horário da loja;
  - um dia especial da loja (ExcecaoHorario: feriado, férias) manda sempre — fechado, ou só
    dentro dos intervalos desse dia;
  - loja sem horário e profissional sem blocos = sem horas (a loja tem de definir o horário).
Livre = horário − ausências − marcações activas (pendente/confirmada, [inicio, ocupado_ate)).
A base de dados recusa sobreposições de qualquer forma (restrição de exclusão); isto só serve
para mostrar as horas e dar mensagens claras.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

from ..utils.horarios import excecao_do_dia, fuso
from .models import AusenciaProfissional, Marcacao

PASSO_MIN = 15          # as horas propostas começam de 15 em 15 minutos


def _dt(dia, h, tz):
    return datetime.combine(dia, h, tzinfo=tz)


def _intervalos_loja(loja, dia, tz, excecoes):
    """[(a, f)] do horário normal da loja num dia (sem horário = nenhum)."""
    if not loja.horario_ativo:
        return []
    out = []
    for h in loja.horarios.all():
        if h.dia_semana != dia.weekday():
            continue
        a = _dt(dia, h.abre, tz)
        f = _dt(dia + timedelta(days=1) if h.fecha <= h.abre else dia, h.fecha, tz)
        out.append((a, f))
    return out


def _cortar(lista, limites):
    """Intersecção de dois conjuntos de intervalos."""
    out = []
    for a, f in lista:
        for la, lf in limites:
            ia, if_ = max(a, la), min(f, lf)
            if if_ > ia:
                out.append((ia, if_))
    return sorted(out)


def _tirar(lista, ocupados):
    """lista − ocupados."""
    out = []
    for a, f in lista:
        partes = [(a, f)]
        for oa, of in ocupados:
            novas = []
            for pa, pf in partes:
                if of <= pa or oa >= pf:
                    novas.append((pa, pf))
                    continue
                if oa > pa:
                    novas.append((pa, oa))
                if of < pf:
                    novas.append((of, pf))
            partes = novas
        out.extend(partes)
    return sorted(out)


def horario_do_dia(prof, dia, tz=None, excecoes=None):
    """Blocos [(a, f)] em que o profissional trabalha neste dia."""
    tz = tz or fuso()
    loja = prof.loja
    excecoes = excecoes if excecoes is not None else list(loja.excecoes.all())
    blocos = [(_dt(dia, h.inicio, tz), _dt(dia, h.fim, tz)) for h in prof.horarios.all() if h.dia_semana == dia.weekday()]
    proprio = any(True for _ in prof.horarios.all())
    ex = excecao_do_dia(excecoes, dia)
    if ex is not None:
        especiais = []
        for i in ex.intervalos or []:
            a, f = time.fromisoformat(i['abre']), time.fromisoformat(i['fecha'])
            especiais.append((_dt(dia, a, tz), _dt(dia + timedelta(days=1) if f <= a else dia, f, tz)))
        return _cortar(blocos, especiais) if proprio else sorted(especiais)
    return sorted(blocos) if proprio else _intervalos_loja(loja, dia, tz, excecoes)


def ocupados(prof, de, ate, excluir=None):
    """Ausências e marcações activas que tocam [de, ate)."""
    aus = [(x.inicio, x.fim) for x in AusenciaProfissional.objects.filter(profissional=prof, inicio__lt=ate, fim__gt=de)]
    mq = Marcacao.objects.filter(profissional=prof, estado__in=Marcacao.ATIVOS, inicio__lt=ate, ocupado_ate__gt=de)
    if excluir:
        mq = mq.exclude(pk=excluir)
    return aus + list(mq.values_list('inicio', 'ocupado_ate'))


def livre_do_dia(prof, dia, tz=None, excecoes=None, excluir=None):
    tz = tz or fuso()
    blocos = horario_do_dia(prof, dia, tz, excecoes)
    if not blocos:
        return []
    return _tirar(blocos, ocupados(prof, blocos[0][0], blocos[-1][1], excluir))


def horas_livres(servico, dia, profissionais, desde=None, excluir=None):
    """
    Horas de início livres para o serviço neste dia: [{'inicio': dt, 'profissionais': [ids]}].
    `desde` = não propor antes disto (agora + antecedência, para os clientes).
    """
    tz = fuso()
    precisa = timedelta(minutes=servico.duracao_min + servico.intervalo_min)
    passo = timedelta(minutes=PASSO_MIN)
    por_hora = {}
    excecoes = list(servico.loja.excecoes.all())
    for prof in profissionais:
        for a, f in livre_do_dia(prof, dia, tz, excecoes, excluir):
            # começa no primeiro múltiplo de 15 min a partir de a
            a, f = a.astimezone(tz), f.astimezone(tz)
            t = a.replace(second=0, microsecond=0)
            if t < a:
                t += timedelta(minutes=1)
            t += timedelta(minutes=-(t.hour * 60 + t.minute) % PASSO_MIN)
            while t + precisa <= f:
                if desde is None or t >= desde:
                    if t.date() == dia:
                        por_hora.setdefault(t, []).append(prof.id)
                t += passo
    return [{'inicio': t, 'profissionais': ids} for t, ids in sorted(por_hora.items())]


class Indisponivel(Exception):
    pass


def verificar(prof, inicio, ocupado_ate, ignorar_horario=False, excluir=None):
    """Levanta Indisponivel com a razão, ou não faz nada."""
    tz = fuso()
    local = inicio.astimezone(tz)
    if not ignorar_horario:
        blocos = horario_do_dia(prof, local.date(), tz)
        # um bloco do dia anterior que passa da meia-noite também conta
        blocos += [b for b in horario_do_dia(prof, local.date() - timedelta(days=1), tz) if b[1] > local]
        if not any(a <= inicio and ocupado_ate <= f for a, f in blocos):
            raise Indisponivel(f'{prof.nome} não trabalha a essa hora.')
    for a, f in ocupados(prof, inicio, ocupado_ate, excluir):
        if a < ocupado_ate and f > inicio:
            raise Indisponivel(f'{prof.nome} já está ocupado(a) a essa hora.')


def fora_do_horario(loja, maximo=100):
    """Marcações futuras activas que já não cabem no horário do profissional (para avisar a loja)."""
    from .marcacoes import marcacao_payload
    out = []
    qs = (Marcacao.objects.filter(loja=loja, estado__in=Marcacao.ATIVOS, inicio__gte=timezone.now())
          .select_related('profissional__loja', 'cliente__user').order_by('inicio'))
    for m in qs[:500]:
        try:
            verificar(m.profissional, m.inicio, m.ocupado_ate, excluir=m.pk)
        except Indisponivel:
            out.append(marcacao_payload(m))
            if len(out) >= maximo:
                break
    return out


def agora_mais(minutos):
    return timezone.now() + timedelta(minutes=minutos)
