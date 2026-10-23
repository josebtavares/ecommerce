"""
Dashboards e relatórios: o período pedido e os números (vendas, receita da plataforma, subscrições…).

Regras de data — cada valor conta sempre pela mesma data, em todos os ecrãs e exportações:
  vendas            → data de conclusão da encomenda (entregue / levantada)
  recebimentos      → data do pagamento (cartão: logo; dinheiro: na entrega)
  reembolsos        → data do reembolso (o dinheiro aplicado)
  faturas           → pagas pela data de pagamento; emitidas pela data de criação
  comissões         → geradas pela data de registo; liquidadas pela data de liquidação
  créditos comissão → pela data de criação (o reembolso que os gerou)

Vendas líquidas = vendas brutas − ajustes − devoluções:
  ajustes    → reembolsos aplicados até à conclusão (artigo esgotado, desconto antes de pagar)
  devoluções → reembolsos de encomendas já concluídas, no período em que são feitos
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncDate, TruncMonth

from .horarios import fuso

MAX_DIAS = 3660                 # dashboards: até 10 anos (só totais)
ZERO = Decimal('0')
_DEC = DecimalField(max_digits=14, decimal_places=2)


def d2(v):
    """Decimal → str com 2 casas ("0.00"), o formato do dinheiro na API."""
    return str((v or ZERO).quantize(Decimal('0.01')))


def variacao(actual, anterior):
    if not anterior:
        return None
    return round(float((Decimal(actual) - Decimal(anterior)) / Decimal(anterior) * 100), 1)


@dataclass
class Periodo:
    inicio: date            # inclusive
    fim: date               # inclusive

    @property
    def de(self):
        return datetime.combine(self.inicio, time(0), tzinfo=fuso())

    @property
    def ate(self):          # exclusivo: o primeiro instante a seguir ao período
        return datetime.combine(self.fim + timedelta(days=1), time(0), tzinfo=fuso())

    @property
    def dias(self):
        return (self.fim - self.inicio).days + 1

    @property
    def granularidade(self):
        return 'dia' if self.dias <= 62 else 'mes'

    def anterior(self):
        """O período do mesmo tamanho imediatamente antes (para as variações)."""
        fim = self.inicio - timedelta(days=1)
        return Periodo(fim - timedelta(days=self.dias - 1), fim)

    def filtro(self, campo):
        """Q para `campo` (DateTimeField) dentro do período."""
        return Q(**{f'{campo}__gte': self.de, f'{campo}__lt': self.ate})

    def baldes(self):
        """Os dias (ou os 1.º de cada mês) do período, para as séries terem todos os pontos."""
        if self.granularidade == 'dia':
            return [self.inicio + timedelta(days=i) for i in range(self.dias)]
        out, d = [], self.inicio.replace(day=1)
        while d <= self.fim:
            out.append(d)
            d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        return out

    def payload(self):
        return {'inicio': self.inicio.isoformat(), 'fim': self.fim.isoformat(),
                'dias': self.dias, 'granularidade': self.granularidade}


class PeriodoInvalido(ValueError):
    pass


def ler_periodo(request, padrao_dias=30, maximo=MAX_DIAS):
    """
    ?data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD  (ou ?periodo=N → os últimos N dias, hoje incluído).
    Datas no fuso da plataforma. Lixo → PeriodoInvalido (a view responde 400).
    """
    from .horarios import agora
    hoje = agora().date()
    di, df = request.GET.get('data_inicio'), request.GET.get('data_fim')
    if di or df:
        try:
            inicio = date.fromisoformat(di or '')
            fim = date.fromisoformat(df or '')
        except ValueError:
            raise PeriodoInvalido('Datas inválidas. Usa AAAA-MM-DD.')
        if fim < inicio:
            raise PeriodoInvalido('A data final é anterior à inicial.')
    else:
        try:
            n = min(max(int(request.GET.get('periodo', padrao_dias)), 1), maximo)
        except (TypeError, ValueError):
            n = padrao_dias
        fim, inicio = hoje, hoje - timedelta(days=n - 1)
    if (fim - inicio).days + 1 > maximo:
        raise PeriodoInvalido(f'O período não pode ter mais de {maximo} dias.')
    return Periodo(inicio, fim)


def serie(qs, campo, periodo, **agregados):
    """
    {balde: {nome: valor}} de `qs` agrupado por dia/mês de `campo` (no fuso da plataforma).
    Os baldes sem linhas não aparecem — `juntar_series` preenche-os com zero.
    """
    trunc = TruncDate if periodo.granularidade == 'dia' else TruncMonth
    linhas = (qs.filter(periodo.filtro(campo)).annotate(_b=trunc(campo, tzinfo=fuso()))
              .values('_b').annotate(**agregados).order_by())
    out = {}
    for r in linhas:
        b = r.pop('_b')
        out[b.date() if isinstance(b, datetime) else b] = r
    return out


def juntar_series(periodo, **series):
    """[{dia, <nome>: float…}] com todos os baldes do período; series = {nome: (mapa, chave)}."""
    out = []
    for b in periodo.baldes():
        linha = {'dia': b.isoformat()}
        for nome, (mapa, chave) in series.items():
            linha[nome] = float((mapa.get(b) or {}).get(chave) or 0)
        out.append(linha)
    return out


# ── vendas ───────────────────────────────────────────────────────────

def _reembolsado_ate_conclusao():
    """Subquery: o que já foi reembolsado de cada encomenda até ela ser concluída (ajustes)."""
    from ..models import Reembolso
    sub = (Reembolso.objects.filter(encomenda=OuterRef('pk'), data_reembolso__isnull=False,
                                    data_reembolso__lte=OuterRef('data_conclusao'))
           .values('encomenda').annotate(t=Sum('valor_aprovado')).values('t'))
    return Coalesce(Subquery(sub, output_field=_DEC), Value(ZERO), output_field=_DEC)


def encomendas_vendidas(periodo, encomendas=None):
    """Encomendas concluídas no período, com `ajuste` (reembolsado até à conclusão) e `venda` (total − ajuste)."""
    from ..models import Encomenda
    qs = encomendas if encomendas is not None else Encomenda.objects.all()
    return (qs.filter(status='concluido').filter(periodo.filtro('data_conclusao'))
            .annotate(ajuste=_reembolsado_ate_conclusao())
            .annotate(venda=F('valor_total') - F('ajuste')))


def devolucoes(periodo, loja_id=None):
    """Reembolsos feitos no período de encomendas que já estavam concluídas (devoluções de vendas)."""
    from ..models import Reembolso
    qs = (Reembolso.objects.filter(periodo.filtro('data_reembolso'), encomenda__status='concluido',
                                   data_reembolso__gt=F('encomenda__data_conclusao')))
    return qs.filter(loja_id=loja_id) if loja_id else qs


def resumo_vendas(periodo, loja_id=None):
    from ..models import Encomenda
    base = Encomenda.objects.filter(loja_id=loja_id) if loja_id else None
    v = encomendas_vendidas(periodo, base).aggregate(brutas=Sum('valor_total'), ajustes=Sum('ajuste'), n=Count('id'))
    dev = devolucoes(periodo, loja_id).aggregate(t=Sum('valor_aprovado'), n=Count('id'))
    brutas, ajustes, devol = v['brutas'] or ZERO, v['ajustes'] or ZERO, dev['t'] or ZERO
    liquidas = brutas - ajustes - devol
    n = v['n'] or 0
    return {'brutas': brutas, 'ajustes': ajustes, 'devolucoes': devol, 'devolucoes_count': dev['n'] or 0,
            'liquidas': liquidas, 'encomendas': n, 'ticket_medio': (brutas - ajustes) / n if n else ZERO}


def serie_vendas(periodo, loja_id=None):
    """Por dia/mês: vendas (pela conclusão, já sem ajustes) menos as devoluções (pela data do reembolso)."""
    from ..models import Encomenda
    base = Encomenda.objects.filter(loja_id=loja_id) if loja_id else None
    v = serie(encomendas_vendidas(periodo, base), 'data_conclusao', periodo, t=Sum('venda'), n=Count('id'))
    d = serie(devolucoes(periodo, loja_id), 'data_reembolso', periodo, t=Sum('valor_aprovado'))
    out = juntar_series(periodo, vendas=(v, 't'), count=(v, 'n'), devolucoes=(d, 't'))
    for linha in out:
        linha['total'] = round(linha['vendas'] - linha['devolucoes'], 2)
        linha['count'] = int(linha['count'])
    return out


# ── recebimentos e reembolsos ────────────────────────────────────────

def recebimentos(periodo, loja_id=None):
    """Pagamentos recebidos no período (pela data do pagamento), por método."""
    from ..models import MetodoPagamento, Pagamento
    qs = Pagamento.objects.filter(periodo.filtro('data_pagamento'))
    if loja_id:
        qs = qs.filter(encomenda__loja_id=loja_id)
    nomes = {**dict(MetodoPagamento.TIPOS), 'outro': 'Outro'}
    linhas = (qs.annotate(tipo=Coalesce('metodo__tipo', Value('outro')))
              .values('tipo').annotate(v=Sum('valor'), n=Count('id')).order_by('-v'))
    por_metodo = [{'metodo': x['tipo'], 'nome': nomes.get(x['tipo'], x['tipo']), 'valor': d2(x['v']), 'count': x['n']}
                  for x in linhas]
    total = sum((x['v'] or ZERO for x in linhas), ZERO)
    return {'total': d2(total), 'count': sum(x['n'] for x in linhas), 'por_metodo': por_metodo}


def reembolsos(periodo, loja_id=None):
    """Dinheiro devolvido no período (descontos antes de pagar — 'abatido' — não saem da caixa)."""
    from ..models import Reembolso
    qs = Reembolso.objects.filter(periodo.filtro('data_reembolso'), valor_aprovado__gt=0)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    a = qs.exclude(metodo='abatido').aggregate(t=Sum('valor_aprovado'), n=Count('id'))
    return {'total': d2(a['t']), 'count': a['n'] or 0,
            'descontados': d2(qs.filter(metodo='abatido').aggregate(t=Sum('valor_aprovado'))['t'])}


# ── receita da plataforma ────────────────────────────────────────────

def receita_plataforma(periodo, loja_id=None):
    """Comissões geradas + subscrições pagas (sem ofertas) − créditos de comissão devolvidos às lojas."""
    from ..models import Comissao, CreditoComissao, FaturaSubscricao
    com = Comissao.objects.filter(periodo.filtro('data_criacao'))
    fat = FaturaSubscricao.objects.filter(periodo.filtro('paga_em'), estado='paga').exclude(metodo='oferta')
    cred = CreditoComissao.objects.filter(periodo.filtro('data_criacao'))
    if loja_id:
        com, fat, cred = com.filter(loja_id=loja_id), fat.filter(loja_id=loja_id), cred.filter(loja_id=loja_id)
    c = com.aggregate(t=Sum('valor_comissao'), n=Count('id'))['t'] or ZERO
    f = fat.aggregate(l=Sum('valor', filter=Q(loja__isnull=False)), p=Sum('valor', filter=Q(pos__isnull=False)),
                      n=Count('id'))
    cr = cred.aggregate(t=Sum('valor'))['t'] or ZERO
    sub = (f['l'] or ZERO) + (f['p'] or ZERO)
    return {'comissoes': c, 'subscricoes': sub, 'subscricoes_lojas': f['l'] or ZERO,
            'subscricoes_pos': f['p'] or ZERO, 'faturas_pagas': f['n'], 'creditos': cr, 'total': c + sub - cr}


def serie_receita(periodo):
    from ..models import Comissao, CreditoComissao, FaturaSubscricao
    c = serie(Comissao.objects.all(), 'data_criacao', periodo, t=Sum('valor_comissao'))
    f = serie(FaturaSubscricao.objects.filter(estado='paga').exclude(metodo='oferta'), 'paga_em', periodo,
              t=Sum('valor'))
    cr = serie(CreditoComissao.objects.all(), 'data_criacao', periodo, t=Sum('valor'))
    out = juntar_series(periodo, comissoes=(c, 't'), subscricoes=(f, 't'), creditos=(cr, 't'))
    for linha in out:
        linha['total'] = round(linha['comissoes'] + linha['subscricoes'] - linha['creditos'], 2)
    return out


# ── subscrições ──────────────────────────────────────────────────────

def subscricoes_hoje():
    """
    A fotografia de hoje: receita mensal recorrente (MRR), lojas por modelo, estados, POS, faturas em atraso.
    MRR = soma de preço ÷ meses das subscrições pagas a correr (em dia ou em atraso; o teste ainda não paga).
    """
    from ..models import FaturaSubscricao, Loja, Subscricao
    from .subscricoes import _resumo_pos, hoje
    a_contar = (Subscricao.objects.filter(plano__isnull=False, coberta_por__isnull=True)
                .filter(Q(loja__modelo_cobranca='subscricao') | Q(pos__isnull=False) | Q(loja_servicos__isnull=False)))
    mrr = ZERO
    mrr_lojas = ZERO
    for preco, meses, loja_id, serv_id, estado in a_contar.values_list('preco', 'meses', 'loja_id', 'loja_servicos_id', 'estado'):
        if estado in ('ativa', 'em_atraso') and meses:
            mrr += preco / meses
            if loja_id or serv_id:               # a subscrição de Serviços também é de uma loja
                mrr_lojas += preco / meses
    lojas = Loja.objects.exclude(estado='pendente')
    d = hoje()
    pend = FaturaSubscricao.objects.filter(estado='pendente')
    atraso = pend.filter(vencimento__lt=d).aggregate(v=Sum('valor'), n=Count('id'))
    proximos = pend.filter(vencimento__gte=d, vencimento__lt=d + timedelta(days=30)).aggregate(v=Sum('valor'), n=Count('id'))
    return {
        'mrr': d2(mrr), 'mrr_lojas': d2(mrr_lojas), 'mrr_pos': d2(mrr - mrr_lojas),
        'lojas': {'comissao': lojas.filter(modelo_cobranca='comissao').count(),
                  'subscricao': lojas.filter(modelo_cobranca='subscricao').count()},
        'por_estado': dict(a_contar.filter(loja__isnull=False).values_list('estado').annotate(n=Count('id'))),
        'pos': _resumo_pos(),
        'em_atraso': {'valor': d2(atraso['v']), 'faturas': atraso['n']},
        'proximos_30d': {'valor': d2(proximos['v']), 'faturas': proximos['n']},
    }
