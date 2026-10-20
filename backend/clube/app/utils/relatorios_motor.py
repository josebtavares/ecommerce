"""
Motor dos relatórios (admin e, com a loja fixa, o módulo Relatórios da backoffice).

Cada relatório recebe os filtros e devolve um dicionário:
  resumo  → [{label, valor, tipo}]          cartões no topo; 1.ª folha do Excel; topo do PDF
  colunas → [{chave, label, tipo}]          tipo: texto | dinheiro | numero | data | datahora | percent
  linhas  → [dict]                          todas (o ecrã pagina; as exportações levam tudo)
  totais  → {chave: valor}                  linha de totais (só as colunas que somam)
  notas   → [str]                           as regras usadas (vão para o Excel e o PDF)

As regras de data (o que conta em que dia) estão em utils/relatorios.py.
"""
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Count, F, Q, Sum

from . import relatorios as rel
from .relatorios import ZERO

MAX_LINHAS = 50000
DIAS_DETALHE = 366          # relatórios linha a linha: até 1 ano por pedido
DIAS_AGREGADO = 3660        # relatórios agregados (por mês, por loja, por produto): até 10 anos

RELATORIOS = {}


@dataclass
class Relatorio:
    id: str
    titulo: str
    descricao: str
    gerar: callable
    filtros: list = field(default_factory=list)      # nomes (ver FILTROS)
    max_dias: int = DIAS_DETALHE
    ambitos: tuple = ('admin',)                       # 'admin' e/ou 'loja'
    grupo: str = 'Vendas'


def relatorio(id, titulo, descricao, filtros=(), max_dias=DIAS_DETALHE, ambitos=('admin',), grupo='Vendas'):
    def reg(fn):
        RELATORIOS[id] = Relatorio(id, titulo, descricao, fn, list(filtros), max_dias, ambitos, grupo)
        return fn
    return reg


class FiltroInvalido(ValueError):
    pass


@dataclass
class Filtros:
    periodo: rel.Periodo
    params: dict
    loja_id: int = None          # fixa no módulo da loja; escolhida no admin
    ambito: str = 'admin'

    def escolha(self, nome, opcoes, padrao=''):
        v = (self.params.get(nome) or '').strip()
        if not v:
            return padrao
        if v not in opcoes:
            raise FiltroInvalido(f'Valor inválido para "{nome}".')
        return v

    def inteiro(self, nome):
        v = (self.params.get(nome) or '').strip()
        if not v:
            return None
        try:
            return int(v)
        except ValueError:
            raise FiltroInvalido(f'Valor inválido para "{nome}".')

    def texto(self, nome, maximo=80):
        return (self.params.get(nome) or '').strip()[:maximo]


# ── definições dos filtros (o ecrã desenha-os a partir daqui) ────────

def _opcoes(choices):
    return [{'valor': v, 'label': str(l)} for v, l in choices]


def definicoes_filtros(nomes, ambito='admin', loja_id=None):
    from ..models import (Encomenda, FaturaSubscricao, Loja, MetodoPagamento, PlanoSubscricao, Reembolso,
                          Comissao, CategoriaLoja, TipoProduto)
    out = []
    for n in nomes:
        if n == 'loja':
            if ambito != 'admin':
                continue
            out.append({'nome': 'loja_id', 'label': 'Loja', 'tipo': 'select', 'todos': 'Todas as lojas',
                        'opcoes': [{'valor': str(i), 'label': nome} for i, nome in
                                   Loja.objects.exclude(estado='pendente').order_by('nome').values_list('id', 'nome')]})
        elif n == 'base_encomendas':
            out.append({'nome': 'base', 'label': 'Contar pela data', 'tipo': 'select',
                        'opcoes': _opcoes([('criadas', 'em que foi feita'), ('concluidas', 'de conclusão')])})
        elif n == 'estado_encomenda':
            out.append({'nome': 'estado', 'label': 'Estado', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes(Encomenda.STATUS)})
        elif n == 'metodo':
            out.append({'nome': 'metodo', 'label': 'Método', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes(MetodoPagamento.TIPOS)})
        elif n == 'entrega':
            out.append({'nome': 'entrega', 'label': 'Entrega', 'tipo': 'select', 'todos': 'Todas',
                        'opcoes': _opcoes(Encomenda.TIPO_ENTREGA)})
        elif n == 'base_faturas':
            out.append({'nome': 'base', 'label': 'Contar pela data', 'tipo': 'select',
                        'opcoes': _opcoes([('emitidas', 'de emissão'), ('pagas', 'de pagamento'),
                                           ('vencimento', 'de vencimento')])})
        elif n == 'estado_fatura':
            out.append({'nome': 'estado', 'label': 'Estado', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes([('pendente', 'Por pagar'), ('em_atraso', 'Em atraso'), ('paga', 'Paga'),
                                           ('anulada', 'Anulada')])})
        elif n == 'alvo':
            out.append({'nome': 'alvo', 'label': 'Cliente', 'tipo': 'select', 'todos': 'Lojas e POS',
                        'opcoes': _opcoes([('loja', 'Só lojas'), ('pos', 'Só POS')])})
        elif n == 'plano':
            out.append({'nome': 'plano', 'label': 'Plano', 'tipo': 'select', 'todos': 'Todos os planos',
                        'opcoes': [{'valor': str(p.id), 'label': f'{p.nome} ({p.get_tipo_display()})'}
                                   for p in PlanoSubscricao.objects.order_by('tipo', 'ordem', 'preco')]})
        elif n == 'metodo_fatura':
            out.append({'nome': 'metodo', 'label': 'Pago com', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes(FaturaSubscricao.METODOS)})
        elif n == 'base_comissoes':
            out.append({'nome': 'base', 'label': 'Contar pela data', 'tipo': 'select',
                        'opcoes': _opcoes([('geradas', 'em que foi gerada'), ('liquidadas', 'de liquidação')])})
        elif n == 'estado_comissao':
            out.append({'nome': 'estado', 'label': 'Estado', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes(Comissao.STATUS)})
        elif n == 'modelo':
            out.append({'nome': 'modelo', 'label': 'Modelo', 'tipo': 'select', 'todos': 'Comissão e subscrição',
                        'opcoes': _opcoes(Loja.MODELOS_COBRANCA)})
        elif n == 'base_reembolsos':
            out.append({'nome': 'base', 'label': 'Contar pela data', 'tipo': 'select',
                        'opcoes': _opcoes([('feitos', 'do reembolso'), ('pedidos', 'do pedido')])})
        elif n == 'estado_reembolso':
            out.append({'nome': 'estado', 'label': 'Estado', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes(Reembolso.ESTADOS)})
        elif n == 'motivo':
            out.append({'nome': 'motivo', 'label': 'Motivo', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': _opcoes(Reembolso.MOTIVOS)})
        elif n == 'agrupar_tempo':
            out.append({'nome': 'agrupar', 'label': 'Agrupar por', 'tipo': 'select',
                        'opcoes': _opcoes([('auto', 'automático'), ('dia', 'dia'), ('mes', 'mês')])})
        elif n == 'agrupar_produtos':
            ops = [('produto', 'produto'), ('variante', 'produto e variante'),
                   ('categoria', 'categoria da loja' if ambito == 'loja' else 'categoria (loja)'), ('tipo', 'tipo de produto')]
            out.append({'nome': 'agrupar', 'label': 'Agrupar por', 'tipo': 'select', 'opcoes': _opcoes(ops)})
        elif n == 'tipo_produto':
            tipos = TipoProduto.objects.filter(Q(loja__isnull=True) | Q(loja_id=loja_id)) if loja_id else \
                TipoProduto.objects.filter(loja__isnull=True)
            out.append({'nome': 'tipo', 'label': 'Tipo de produto', 'tipo': 'select', 'todos': 'Todos',
                        'opcoes': [{'valor': str(i), 'label': n} for i, n in tipos.order_by('nome').values_list('id', 'nome')]})
        elif n == 'categoria_loja':
            if ambito != 'loja':
                continue
            out.append({'nome': 'categoria', 'label': 'Categoria', 'tipo': 'select', 'todos': 'Todas',
                        'opcoes': [{'valor': str(i), 'label': n} for i, n in
                                   CategoriaLoja.objects.filter(loja_id=loja_id).order_by('ordem', 'nome').values_list('id', 'nome')]})
        elif n == 'pesquisa_produto':
            out.append({'nome': 'q', 'label': 'Produto', 'tipo': 'texto', 'placeholder': 'Nome do produto'})
    return out


# ── utilitários ──────────────────────────────────────────────────────

def _nome(user):
    if not user:
        return ''
    return user.get_full_name() or user.username


def _col(chave, label, tipo='texto'):
    return {'chave': chave, 'label': label, 'tipo': tipo}


def _r(label, valor, tipo='dinheiro'):
    return {'label': label, 'valor': valor, 'tipo': tipo}


def _somas(linhas, chaves):
    return {k: sum((Decimal(str(l.get(k) or 0)) for l in linhas), ZERO) for k in chaves}


def _loja(f, qs, campo='loja_id'):
    """Aplica a loja (fixa no módulo da loja; escolhida no filtro do admin)."""
    loja_id = f.loja_id or (f.inteiro('loja_id') if f.ambito == 'admin' else None)
    return qs.filter(**{campo: loja_id}) if loja_id else qs


def _loja_id(f):
    return f.loja_id or (f.inteiro('loja_id') if f.ambito == 'admin' else None)


def _metodo_label():
    from ..models import MetodoPagamento
    return dict(MetodoPagamento.TIPOS)


# ══════════════════════════════════════════════════════════════
# RECEITA DA PLATAFORMA
# ══════════════════════════════════════════════════════════════

@relatorio('receita', 'Receita da plataforma',
           'Comissões geradas, subscrições pagas e créditos devolvidos às lojas, por dia ou por mês.',
           filtros=['loja', 'agrupar_tempo'], max_dias=DIAS_AGREGADO, grupo='Plataforma')
def _receita(f):
    from ..models import Comissao, CreditoComissao, FaturaSubscricao
    p = f.periodo
    agrupar = f.escolha('agrupar', ('auto', 'dia', 'mes'), 'auto')
    if agrupar != 'auto':
        p = _PeriodoFixo(p.inicio, p.fim, agrupar)
    com = _loja(f, Comissao.objects.all())
    fat = _loja(f, FaturaSubscricao.objects.filter(estado='paga').exclude(metodo='oferta'))
    cred = _loja(f, CreditoComissao.objects.all())
    c = rel.serie(com, 'data_criacao', p, t=Sum('valor_comissao'), n=Count('id'))
    fl = rel.serie(fat.filter(loja__isnull=False), 'paga_em', p, t=Sum('valor'))
    fp = rel.serie(fat.filter(pos__isnull=False), 'paga_em', p, t=Sum('valor'))
    cr = rel.serie(cred, 'data_criacao', p, t=Sum('valor'))
    linhas = []
    for b in p.baldes():
        lc = Decimal((c.get(b) or {}).get('t') or 0)
        l1 = Decimal((fl.get(b) or {}).get('t') or 0)
        l2 = Decimal((fp.get(b) or {}).get('t') or 0)
        lr = Decimal((cr.get(b) or {}).get('t') or 0)
        linhas.append({'periodo': b.isoformat(), 'comissoes': lc, 'encomendas': (c.get(b) or {}).get('n') or 0,
                       'subscricoes_lojas': l1, 'subscricoes_pos': l2, 'creditos': lr, 'total': lc + l1 + l2 - lr})
    tot = _somas(linhas, ['comissoes', 'encomendas', 'subscricoes_lojas', 'subscricoes_pos', 'creditos', 'total'])
    return {
        'resumo': [_r('Receita total', tot['total']), _r('Comissões', tot['comissoes']),
                   _r('Subscrições de lojas', tot['subscricoes_lojas']), _r('Subscrições de POS', tot['subscricoes_pos']),
                   _r('Créditos devolvidos', tot['creditos'])],
        'colunas': [_col('periodo', 'Mês' if p.granularidade == 'mes' else 'Dia', 'mes' if p.granularidade == 'mes' else 'data'),
                    _col('encomendas', 'Encomendas c/ comissão', 'numero'), _col('comissoes', 'Comissões', 'dinheiro'),
                    _col('subscricoes_lojas', 'Subscrições lojas', 'dinheiro'), _col('subscricoes_pos', 'Subscrições POS', 'dinheiro'),
                    _col('creditos', 'Créditos', 'dinheiro'), _col('total', 'Receita', 'dinheiro')],
        'linhas': linhas, 'totais': tot,
        'notas': ['Comissões pela data em que foram geradas; subscrições pela data de pagamento (ofertas não contam); '
                  'créditos de comissão (reembolsos de encomendas com a comissão já liquidada) pela data em que foram criados.'],
    }


class _PeriodoFixo(rel.Periodo):
    """Um Periodo com a granularidade escolhida pelo utilizador em vez da automática."""
    def __init__(self, inicio, fim, granularidade):
        super().__init__(inicio, fim)
        self._g = granularidade

    @property
    def granularidade(self):
        return self._g


# ══════════════════════════════════════════════════════════════
# SUBSCRIÇÕES (FATURAS)
# ══════════════════════════════════════════════════════════════

@relatorio('subscricoes', 'Subscrições — faturas',
           'Todas as faturas de subscrição de lojas e POS: emitidas, pagas, em atraso e anuladas.',
           filtros=['base_faturas', 'estado_fatura', 'alvo', 'plano', 'metodo_fatura', 'loja'], grupo='Plataforma')
def _subscricoes(f):
    from ..models import FaturaSubscricao, Subscricao
    from .subscricoes import hoje, nome_alvo
    p = f.periodo
    base = f.escolha('base', ('emitidas', 'pagas', 'vencimento'), 'emitidas')
    qs = FaturaSubscricao.objects.select_related('loja', 'pos', 'plano')
    if base == 'emitidas':
        qs = qs.filter(p.filtro('data_criacao'))
    elif base == 'pagas':
        qs = qs.filter(p.filtro('paga_em'), estado='paga')
    else:
        qs = qs.filter(vencimento__gte=p.inicio, vencimento__lte=p.fim)
    d = hoje()
    estado = f.escolha('estado', ('pendente', 'em_atraso', 'paga', 'anulada'))
    if estado == 'em_atraso':
        qs = qs.filter(estado='pendente', vencimento__lt=d)
    elif estado == 'pendente':
        qs = qs.filter(estado='pendente', vencimento__gte=d)
    elif estado:
        qs = qs.filter(estado=estado)
    alvo = f.escolha('alvo', ('loja', 'pos'))
    if alvo == 'loja':
        qs = qs.filter(loja__isnull=False)
    elif alvo == 'pos':
        qs = qs.filter(pos__isnull=False)
    plano = f.inteiro('plano')
    if plano:
        qs = qs.filter(plano_id=plano)
    metodo = f.escolha('metodo', dict(FaturaSubscricao.METODOS))
    if metodo:
        qs = qs.filter(metodo=metodo)
    qs = _loja(f, qs)
    metodos = dict(FaturaSubscricao.METODOS)

    def estado_de(x):
        if x.estado == 'pendente':
            return 'Em atraso' if x.vencimento < d else 'Por pagar'
        return x.get_estado_display()
    linhas = [{
        'fatura': x.id, 'cliente': nome_alvo(x.alvo), 'tipo': 'Loja' if x.loja_id else 'POS',
        'plano': x.plano.nome if x.plano_id else '', 'periodo_inicio': x.periodo_inicio, 'periodo_fim': x.periodo_fim,
        'emitida': x.data_criacao, 'vencimento': x.vencimento, 'estado': estado_de(x), 'paga_em': x.paga_em,
        'metodo': metodos.get(x.metodo, '') if x.estado == 'paga' else '', 'referencia': x.referencia, 'valor': x.valor,
    } for x in qs.order_by(F('paga_em').asc(nulls_last=True) if base == 'pagas' else 'data_criacao', 'id')[:MAX_LINHAS]]

    def soma(cond):
        return sum((l['valor'] for l in linhas if cond(l)), ZERO)
    pagas = soma(lambda l: l['estado'] == 'Paga' and l['metodo'] != metodos['oferta'])
    resumo = [_r('Faturas', len(linhas), 'numero'), _r('Valor faturado', soma(lambda l: l['estado'] != 'Anulada')),
              _r('Pago', pagas), _r('Por pagar', soma(lambda l: l['estado'] == 'Por pagar')),
              _r('Em atraso', soma(lambda l: l['estado'] == 'Em atraso')),
              _r('Ofertas da plataforma', soma(lambda l: l['metodo'] == metodos['oferta'])),
              _r('Anuladas', soma(lambda l: l['estado'] == 'Anulada'))]
    if not _loja_id(f):
        hoje_ = rel.subscricoes_hoje()
        novas = Subscricao.objects.filter(p.filtro('data_criacao')).count()
        resumo += [_r('Receita mensal recorrente (hoje)', Decimal(hoje_['mrr'])), _r('Subscrições novas no período', novas, 'numero')]
    return {
        'resumo': resumo,
        'colunas': [_col('fatura', 'Fatura', 'numero'), _col('cliente', 'Cliente'), _col('tipo', 'Tipo'), _col('plano', 'Plano'),
                    _col('periodo_inicio', 'Período de', 'data'), _col('periodo_fim', 'até', 'data'),
                    _col('emitida', 'Emitida', 'data'), _col('vencimento', 'Vencimento', 'data'), _col('estado', 'Estado'),
                    _col('paga_em', 'Paga em', 'data'), _col('metodo', 'Método'), _col('referencia', 'Referência'),
                    _col('valor', 'Valor', 'dinheiro')],
        'linhas': linhas, 'totais': {'valor': soma(lambda l: l['estado'] != 'Anulada')},
        'notas': ['"Até" é exclusivo: o primeiro dia do período seguinte. O total não inclui faturas anuladas. '
                  'As ofertas da plataforma aparecem como pagas mas não são receita.'],
    }


# ══════════════════════════════════════════════════════════════
# COMISSÕES E CRÉDITOS
# ══════════════════════════════════════════════════════════════

@relatorio('comissoes', 'Comissões',
           'Comissão de cada encomenda: valor, percentagem, se já foi liquidada e créditos por reembolsos.',
           filtros=['base_comissoes', 'estado_comissao', 'loja'], grupo='Plataforma', ambitos=('admin', 'loja'))
def _comissoes(f):
    from ..models import Comissao, CreditoComissao
    p = f.periodo
    base = f.escolha('base', ('geradas', 'liquidadas'), 'geradas')
    qs = Comissao.objects.select_related('loja', 'encomenda').annotate(cred=Sum('creditos__valor'))
    qs = qs.filter(p.filtro('data_criacao')) if base == 'geradas' else qs.filter(p.filtro('data_liquidacao'), status='liquidada')
    estado = f.escolha('estado', dict(Comissao.STATUS))
    if estado:
        qs = qs.filter(status=estado)
    qs = _loja(f, qs)
    linhas = [{
        'comissao': c.id, 'encomenda': c.encomenda_id, 'loja': c.loja.nome, 'gerada': c.data_criacao,
        'valor_encomenda': c.valor_encomenda, 'percentagem': c.percentagem, 'valor': c.valor_comissao,
        'estado': c.get_status_display(), 'liquidada_em': c.data_liquidacao, 'creditos': c.cred or ZERO,
    } for c in qs.order_by('data_criacao', 'id')[:MAX_LINHAS]]
    tot = _somas(linhas, ['valor_encomenda', 'valor', 'creditos'])
    cred = _loja(f, CreditoComissao.objects.all())
    cred_periodo = cred.filter(p.filtro('data_criacao')).aggregate(t=Sum('valor'))['t'] or ZERO
    pend = sum((l['valor'] for l in linhas if l['estado'] == dict(Comissao.STATUS)['pendente']), ZERO)
    return {
        'resumo': [_r('Comissões', tot['valor']), _r('Encomendas', len(linhas), 'numero'),
                   _r('Valor das encomendas', tot['valor_encomenda']), _r('Por liquidar', pend),
                   _r('Créditos criados no período', cred_periodo),
                   _r('Créditos por descontar (hoje)', cred.filter(estado='pendente').aggregate(t=Sum('valor'))['t'] or ZERO)],
        'colunas': [_col('comissao', 'Comissão', 'numero'), _col('encomenda', 'Encomenda', 'numero'), _col('loja', 'Loja'),
                    _col('gerada', 'Gerada', 'data'), _col('valor_encomenda', 'Valor da encomenda', 'dinheiro'),
                    _col('percentagem', '%', 'percent'), _col('valor', 'Comissão', 'dinheiro'), _col('estado', 'Estado'),
                    _col('liquidada_em', 'Liquidada em', 'data'), _col('creditos', 'Créditos', 'dinheiro')],
        'linhas': linhas, 'totais': tot,
        'notas': ['Uma comissão ainda por liquidar já vem recalculada se a encomenda teve reembolsos. '
                  'Se já estava liquidada, o reembolso cria um crédito a descontar na liquidação seguinte (coluna Créditos).'],
    }


# ══════════════════════════════════════════════════════════════
# VENDAS POR LOJA
# ══════════════════════════════════════════════════════════════

@relatorio('vendas_lojas', 'Vendas por loja',
           'Por loja: encomendas concluídas, vendas brutas, ajustes, devoluções, líquido e o que rendeu à Bendi.',
           filtros=['modelo', 'loja'], max_dias=DIAS_AGREGADO)
def _vendas_lojas(f):
    from ..models import Comissao, FaturaSubscricao, Loja
    p = f.periodo
    v = {x['loja_id']: x for x in rel.encomendas_vendidas(p).values('loja_id')
         .annotate(n=Count('id'), brutas=Sum('valor_total'), ajustes=Sum('ajuste'))}
    dv = dict(rel.devolucoes(p).values_list('loja_id').annotate(t=Sum('valor_aprovado')))
    com = dict(Comissao.objects.filter(p.filtro('data_criacao')).values_list('loja_id').annotate(t=Sum('valor_comissao')))
    sub = dict(FaturaSubscricao.objects.filter(p.filtro('paga_em'), estado='paga', loja__isnull=False)
               .exclude(metodo='oferta').values_list('loja_id').annotate(t=Sum('valor')))
    lojas = Loja.objects.filter(id__in=set(v) | set(dv) | set(com) | set(sub))
    modelo = f.escolha('modelo', dict(Loja.MODELOS_COBRANCA))
    if modelo:
        lojas = lojas.filter(modelo_cobranca=modelo)
    lojas = _loja(f, lojas, 'id')
    linhas = []
    for l in lojas.order_by('nome'):
        x = v.get(l.id) or {}
        brutas, aj, de = x.get('brutas') or ZERO, x.get('ajustes') or ZERO, dv.get(l.id) or ZERO
        n = x.get('n') or 0
        c, s = com.get(l.id) or ZERO, sub.get(l.id) or ZERO
        linhas.append({'loja': l.nome, 'modelo': l.get_modelo_cobranca_display(), 'encomendas': n, 'brutas': brutas,
                       'ajustes': aj, 'devolucoes': de, 'liquidas': brutas - aj - de,
                       'ticket_medio': (brutas - aj) / n if n else ZERO, 'comissoes': c, 'subscricoes': s, 'receita_bendi': c + s})
    linhas.sort(key=lambda l: -l['liquidas'])
    tot = _somas(linhas, ['encomendas', 'brutas', 'ajustes', 'devolucoes', 'liquidas', 'comissoes', 'subscricoes', 'receita_bendi'])
    return {
        'resumo': [_r('Vendas líquidas', tot['liquidas']), _r('Vendas brutas', tot['brutas']), _r('Ajustes', tot['ajustes']),
                   _r('Devoluções', tot['devolucoes']), _r('Encomendas concluídas', int(tot['encomendas']), 'numero'),
                   _r('Lojas com movimento', len(linhas), 'numero'), _r('Receita da Bendi', tot['receita_bendi'])],
        'colunas': [_col('loja', 'Loja'), _col('modelo', 'Modelo'), _col('encomendas', 'Encomendas', 'numero'),
                    _col('brutas', 'Brutas', 'dinheiro'), _col('ajustes', 'Ajustes', 'dinheiro'),
                    _col('devolucoes', 'Devoluções', 'dinheiro'), _col('liquidas', 'Líquidas', 'dinheiro'),
                    _col('ticket_medio', 'Ticket médio', 'dinheiro'), _col('comissoes', 'Comissões', 'dinheiro'),
                    _col('subscricoes', 'Subscrições', 'dinheiro'), _col('receita_bendi', 'Receita Bendi', 'dinheiro')],
        'linhas': linhas, 'totais': tot, 'notas': [NOTA_VENDAS],
    }


NOTA_VENDAS = ('Vendas pela data de conclusão (entregue / levantada). Ajustes = reembolsos feitos antes da conclusão '
               '(ex.: artigo esgotado). Devoluções = reembolsos de encomendas já concluídas, no período em que foram feitos. '
               'Líquidas = brutas − ajustes − devoluções.')


# ══════════════════════════════════════════════════════════════
# VENDAS POR PRODUTO
# ══════════════════════════════════════════════════════════════

@relatorio('vendas_produtos', 'Vendas por produto',
           'Unidades e valor vendidos por produto (sozinhos e dentro de menus), unidades devolvidas e margem.',
           filtros=['agrupar_produtos', 'tipo_produto', 'categoria_loja', 'pesquisa_produto', 'loja'],
           max_dias=DIAS_AGREGADO, ambitos=('admin', 'loja'))
def _vendas_produtos(f):
    from ..models import Inventario, ItemEncomenda, ItemReembolso, Produto
    p = f.periodo
    agrupar = f.escolha('agrupar', ('produto', 'variante', 'categoria', 'tipo'), 'produto')
    itens = (ItemEncomenda.objects.filter(encomenda__status='concluido', encomenda__data_conclusao__gte=p.de,
                                          encomenda__data_conclusao__lt=p.ate)
             .select_related('encomenda__loja', 'produto__tipo', 'variante'))
    itens = _loja(f, itens, 'encomenda__loja_id')
    tipo = f.inteiro('tipo')
    categoria = f.inteiro('categoria') if f.ambito == 'loja' else None
    q = f.texto('q')
    # os filtros de produto aplicam-se às linhas finais (um produto pode vir dentro de um menu)
    produtos_ok = None
    if tipo or categoria or q:
        pq = Produto.objects.all()
        if tipo:
            pq = pq.filter(tipo_id=tipo)
        if categoria:
            pq = pq.filter(categorias__id=categoria)
        if q:
            pq = pq.filter(nome__icontains=q)
        produtos_ok = set(_loja(f, pq).values_list('id', flat=True))

    # devolvido: devoluções de encomendas concluídas (reembolsos depois da conclusão, pela data do reembolso).
    # O valor de cada artigo segue o que foi aprovado (a loja pode ter aprovado menos do que o pedido);
    # a taxa de entrega devolvida não é de nenhum produto.
    dev = {}
    its = (ItemReembolso.objects.filter(reembolso__data_reembolso__gte=p.de, reembolso__data_reembolso__lt=p.ate,
                                        reembolso__encomenda__status='concluido',
                                        reembolso__data_reembolso__gt=F('reembolso__encomenda__data_conclusao'))
           .select_related('reembolso', 'item'))
    for it in _loja(f, its, 'reembolso__loja_id'):
        r = it.reembolso
        base = r.valor_pedido - r.valor_entrega
        aprovado = r.valor_aprovado or ZERO           # o aprovado cobre primeiro os artigos, depois a entrega
        fator = min(max(aprovado / base, ZERO), Decimal('1')) if base > 0 else ZERO
        k = (it.item.produto_id, it.item.variante_id)
        q0, v0 = dev.get(k, (0, ZERO))
        dev[k] = (q0 + it.quantidade, v0 + (it.valor * fator).quantize(Decimal('0.01')))

    linhas = {}
    custos = dict(Inventario.objects.values_list('produto_id', 'preco_custo'))

    def chave_de(pid, vid, prod):
        if agrupar == 'variante':
            return (pid, vid)
        if agrupar == 'tipo':
            return ('tipo', prod.tipo_id if prod else None)
        if agrupar == 'categoria':
            if pid not in cache_cats:
                cache_cats[pid] = ', '.join(sorted(prod.categorias.values_list('nome', flat=True))) if prod else ''
            return ('cat', cache_cats[pid] or 'Sem categoria')
        return (pid, None)

    cache_prod = {}
    cache_cats = {}

    def prod_de(pid):
        if pid not in cache_prod:
            cache_prod[pid] = Produto.objects.select_related('tipo', 'loja').filter(id=pid).first()
        return cache_prod[pid]

    def linha(chave, pid, vid, prod, nome_variante=''):
        if chave not in linhas:
            if agrupar == 'tipo':
                nome = (prod.tipo.nome if prod and prod.tipo_id else 'Sem tipo')
            elif agrupar == 'categoria':
                nome = chave[1]
            else:
                nome = prod.nome if prod else 'Produto apagado'
            linhas[chave] = {'produto': nome, 'variante': nome_variante, 'loja': prod.loja.nome if prod and agrupar in ('produto', 'variante') else '',
                             'tipo': (prod.tipo.nome if prod and prod.tipo_id else '') if agrupar in ('produto', 'variante') else '',
                             'unidades': 0, 'em_conjuntos': 0, 'valor': ZERO, 'custo': ZERO, 'devolvidas': 0,
                             'valor_devolvido': ZERO, '_sem_custo': False}
        return linhas[chave]

    for it in itens[:MAX_LINHAS * 4]:
        pid, vid = it.produto_id, it.variante_id
        if pid and (produtos_ok is None or pid in produtos_ok):
            prod = it.produto
            cache_prod.setdefault(pid, prod)
            nome_var = ', '.join(f'{v}' for v in (it.atributos or {}).values()) if agrupar == 'variante' else ''
            l = linha(chave_de(pid, vid, prod), pid, vid, prod, nome_var)
            l['unidades'] += it.quantidade
            l['valor'] += it.preco * it.quantidade
            custo = custos.get(pid)
            if custo:
                l['custo'] += custo * it.quantidade
            else:
                l['_sem_custo'] = True
        for c in it.componentes or []:
            cpid = c.get('produto_id')
            n = int(c.get('quantidade') or 0) * it.quantidade
            if not cpid or not n or (c.get('origem') or 'loja') != 'loja' or (produtos_ok is not None and cpid not in produtos_ok):
                continue
            prod = prod_de(cpid)
            l = linha(chave_de(cpid, c.get('variante_id'), prod), cpid, c.get('variante_id'), prod)
            l['em_conjuntos'] += n
    for (pid, vid), (qd, vd) in dev.items():
        if not pid or (produtos_ok is not None and pid not in produtos_ok):
            continue
        prod = prod_de(pid)
        l = linha(chave_de(pid, vid, prod), pid, vid, prod)
        l['devolvidas'] += qd
        l['valor_devolvido'] += vd

    out = []
    for l in linhas.values():
        sem = l.pop('_sem_custo')
        l['liquido'] = l['valor'] - l['valor_devolvido']
        l['margem'] = (l['valor'] - l['custo']) if l['custo'] and not sem else None
        out.append(l)
    out.sort(key=lambda l: (-l['unidades'] - l['em_conjuntos'], l['produto']))
    tot = _somas(out, ['unidades', 'em_conjuntos', 'valor', 'devolvidas', 'valor_devolvido', 'liquido'])
    com_custo = [l['margem'] for l in out if l['margem'] is not None]
    tot['margem'] = sum(com_custo, ZERO) if com_custo else None
    colunas = [_col('produto', {'tipo': 'Tipo de produto', 'categoria': 'Categoria'}.get(agrupar, 'Produto'))]
    if agrupar == 'variante':
        colunas.append(_col('variante', 'Variante'))
    if agrupar in ('produto', 'variante'):
        if f.ambito == 'admin':
            colunas.append(_col('loja', 'Loja'))
        colunas.append(_col('tipo', 'Tipo'))
    colunas += [_col('unidades', 'Unidades', 'numero'), _col('em_conjuntos', 'Em menus', 'numero'),
                _col('valor', 'Vendido', 'dinheiro'), _col('devolvidas', 'Devolvidas', 'numero'),
                _col('valor_devolvido', 'Devolvido', 'dinheiro'), _col('liquido', 'Líquido', 'dinheiro'),
                _col('margem', 'Margem', 'dinheiro')]
    return {
        'resumo': [_r('Vendido', tot['valor']), _r('Unidades', int(tot['unidades']), 'numero'),
                   _r('Unidades em menus', int(tot['em_conjuntos']), 'numero'), _r('Devolvido', tot['valor_devolvido']),
                   _r('Líquido', tot['liquido']), _r('Margem (produtos com custo)', tot['margem'])],
        'colunas': colunas, 'linhas': out, 'totais': tot,
        'notas': ['Encomendas concluídas no período (data de conclusão). "Vendido" = preço × unidades vendidas sozinhas; '
                  'as unidades que saíram dentro de menus/conjuntos contam em "Em menus" (o valor fica no menu). '
                  'Os valores são só dos artigos (sem taxas de entrega). '
                  'Devoluções pela data do reembolso. Margem = vendido − preço de custo atual do inventário '
                  '(vazia quando o produto não tem custo).'],
    }


# ══════════════════════════════════════════════════════════════
# ENCOMENDAS (DETALHE)
# ══════════════════════════════════════════════════════════════

@relatorio('encomendas', 'Encomendas — detalhe',
           'Uma linha por encomenda: datas, cliente, estado, pagamento, valores, reembolsos e comissão.',
           filtros=['base_encomendas', 'estado_encomenda', 'metodo', 'entrega', 'loja'], ambitos=('admin', 'loja'))
def _encomendas(f):
    from django.db.models import DecimalField, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce
    from ..models import Encomenda, Reembolso
    p = f.periodo
    base = f.escolha('base', ('criadas', 'concluidas'), 'criadas')
    qs = Encomenda.objects.select_related('loja', 'comprador__user', 'pagamento__metodo', 'comissao')
    qs = qs.filter(p.filtro('data_criacao')) if base == 'criadas' else qs.filter(p.filtro('data_conclusao'), status='concluido')
    estado = f.escolha('estado', dict(Encomenda.STATUS))
    if estado:
        qs = qs.filter(status=estado)
    metodo = f.escolha('metodo', _metodo_label())
    if metodo:
        qs = qs.filter(pagamento__metodo__tipo=metodo)
    entrega = f.escolha('entrega', dict(Encomenda.TIPO_ENTREGA))
    if entrega:
        qs = qs.filter(tipo_entrega=entrega)
    qs = _loja(f, qs)
    dec = DecimalField(max_digits=12, decimal_places=2)
    reemb = (Reembolso.objects.filter(encomenda=OuterRef('pk'), data_reembolso__isnull=False)
             .values('encomenda').annotate(t=Sum('valor_aprovado')).values('t'))
    qs = qs.annotate(reembolsado=Coalesce(Subquery(reemb, output_field=dec), Value(ZERO), output_field=dec))
    metodos = _metodo_label()
    pag_estados = {'pendente': 'Por pagar', 'aprovado': 'Pago', 'falhado': 'Falhou', 'reembolsado': 'Reembolsado',
                   'reembolsado_parcial': 'Reembolsado em parte'}
    linhas = []
    for e in qs.order_by('data_criacao', 'id')[:MAX_LINHAS]:
        pg = getattr(e, 'pagamento', None) if hasattr(e, 'pagamento') else None
        com = getattr(e, 'comissao', None) if hasattr(e, 'comissao') else None
        linhas.append({
            'encomenda': e.id, 'criada': e.data_criacao, 'concluida': e.data_conclusao, 'loja': e.loja.nome,
            'cliente': _nome(e.comprador.user), 'estado': e.get_status_display(), 'entrega': e.get_tipo_entrega_display(),
            'metodo': metodos.get(pg.metodo.tipo, '') if pg and pg.metodo_id else '',
            'pagamento': pag_estados.get(pg.status, pg.status) if pg else 'Sem pagamento',
            'pago_em': pg.data_pagamento if pg else None,
            'total': e.valor_total, 'reembolsado': e.reembolsado,
            'liquido': ZERO if e.status == 'cancelado' else e.valor_total - e.reembolsado,
            'comissao': com.valor_comissao if com else ZERO,
        })
    tot = _somas(linhas, ['total', 'reembolsado', 'liquido', 'comissao'])
    concl = [l for l in linhas if l['concluida'] and l['estado'] == dict(Encomenda.STATUS)['concluido']]
    colunas = [_col('encomenda', 'Encomenda', 'numero'), _col('criada', 'Feita em', 'datahora'),
               _col('concluida', 'Concluída em', 'datahora')]
    if f.ambito == 'admin' and not _loja_id(f):
        colunas.append(_col('loja', 'Loja'))
    colunas += [_col('cliente', 'Cliente'), _col('estado', 'Estado'), _col('entrega', 'Entrega'), _col('metodo', 'Método'),
                _col('pagamento', 'Pagamento'), _col('pago_em', 'Pago em', 'datahora'), _col('total', 'Total', 'dinheiro'),
                _col('reembolsado', 'Reembolsado', 'dinheiro'), _col('liquido', 'Líquido', 'dinheiro'),
                _col('comissao', 'Comissão', 'dinheiro')]
    return {
        'resumo': [_r('Encomendas', len(linhas), 'numero'), _r('Valor total', tot['total']), _r('Reembolsado', tot['reembolsado']),
                   _r('Líquido (sem canceladas)', tot['liquido']), _r('Concluídas', len(concl), 'numero'),
                   _r('Canceladas', sum(1 for l in linhas if l['estado'] == dict(Encomenda.STATUS)['cancelado']), 'numero'),
                   _r('Comissões', tot['comissao'])],
        'colunas': colunas, 'linhas': linhas, 'totais': tot,
        'notas': ['"Reembolsado" inclui todos os reembolsos já feitos da encomenda, em qualquer data '
                  '(também os descontos antes de pagar). Uma encomenda cancelada tem líquido zero.'],
    }


# ══════════════════════════════════════════════════════════════
# REEMBOLSOS
# ══════════════════════════════════════════════════════════════

@relatorio('reembolsos', 'Reembolsos e devoluções',
           'Todos os pedidos de reembolso: motivo, estado, quem decidiu, método e valores.',
           filtros=['base_reembolsos', 'estado_reembolso', 'motivo', 'loja'], ambitos=('admin', 'loja'))
def _reembolsos(f):
    from ..models import Reembolso
    p = f.periodo
    base = f.escolha('base', ('feitos', 'pedidos'), 'feitos')
    qs = Reembolso.objects.select_related('loja', 'comprador__user')
    qs = qs.filter(p.filtro('data_reembolso')) if base == 'feitos' else qs.filter(p.filtro('data_criacao'))
    estado = f.escolha('estado', dict(Reembolso.ESTADOS))
    if estado:
        qs = qs.filter(estado=estado)
    motivo = f.escolha('motivo', dict(Reembolso.MOTIVOS))
    if motivo:
        qs = qs.filter(motivo=motivo)
    qs = _loja(f, qs)
    metodos = dict(Reembolso.METODOS)

    def decidiu(r):
        if r.decisao_admin:
            return 'Bendi'
        if r.origem == 'sistema':
            return 'Automático'
        return 'Loja' if r.resposta_loja or r.origem == 'loja' else ''
    linhas = [{
        'reembolso': r.id, 'pedido_em': r.data_criacao, 'reembolsado_em': r.data_reembolso, 'encomenda': r.encomenda_id,
        'loja': r.loja.nome, 'cliente': _nome(r.comprador.user), 'tipo': 'Cancelamento' if r.tipo == 'cancelamento' else 'Devolução',
        'motivo': r.get_motivo_display(), 'estado': r.get_estado_display(), 'decidiu': decidiu(r),
        'metodo': metodos.get(r.metodo, ''), 'valor_pedido': r.valor_pedido, 'valor_aprovado': r.valor_aprovado or ZERO,
        '_horas': ((r.data_resposta_loja - r.data_criacao).total_seconds() / 3600) if r.data_resposta_loja else None,
        '_abatido': r.metodo == 'abatido',
    } for r in qs.order_by('data_criacao', 'id')[:MAX_LINHAS]]
    feitos = [l for l in linhas if l['reembolsado_em']]
    horas = [l['_horas'] for l in linhas if l['_horas'] is not None]
    devolvido = sum((l['valor_aprovado'] for l in feitos if not l['_abatido']), ZERO)
    por_motivo = {}
    for l in feitos:
        por_motivo[l['motivo']] = por_motivo.get(l['motivo'], ZERO) + l['valor_aprovado']
    for l in linhas:
        l.pop('_horas'); l.pop('_abatido')
    resumo = [_r('Pedidos', len(linhas), 'numero'), _r('Reembolsados', len(feitos), 'numero'),
              _r('Dinheiro devolvido', devolvido),
              _r('Descontado antes de pagar', sum((l['valor_aprovado'] for l in feitos), ZERO) - devolvido),
              _r('Decididos pela Bendi', sum(1 for l in linhas if l['decidiu'] == 'Bendi'), 'numero'),
              _r('Resposta média da loja (horas)', round(sum(horas) / len(horas), 1) if horas else None, 'numero')]
    resumo += [_r(f'Motivo: {m}', v) for m, v in sorted(por_motivo.items(), key=lambda x: -x[1])[:5]]
    colunas = [_col('reembolso', 'Pedido', 'numero'), _col('pedido_em', 'Pedido em', 'datahora'),
               _col('reembolsado_em', 'Reembolsado em', 'datahora'), _col('encomenda', 'Encomenda', 'numero')]
    if f.ambito == 'admin' and not _loja_id(f):
        colunas.append(_col('loja', 'Loja'))
    colunas += [_col('cliente', 'Cliente'), _col('tipo', 'Tipo'), _col('motivo', 'Motivo'), _col('estado', 'Estado'),
                _col('decidiu', 'Decidido por'), _col('metodo', 'Método'), _col('valor_pedido', 'Pedido', 'dinheiro'),
                _col('valor_aprovado', 'Aprovado', 'dinheiro')]
    return {
        'resumo': resumo, 'colunas': colunas, 'linhas': linhas,
        'totais': _somas(linhas, ['valor_pedido', 'valor_aprovado']),
        'notas': ['"Descontado antes de pagar" = artigos retirados de encomendas a pagar em dinheiro na entrega '
                  '(o cliente pagou menos; não houve dinheiro devolvido).'],
    }


# ══════════════════════════════════════════════════════════════
# RECEBIMENTOS (PAGAMENTOS)
# ══════════════════════════════════════════════════════════════

@relatorio('pagamentos', 'Recebimentos',
           'Pagamentos recebidos pela data do pagamento, por método, e o dinheiro ainda por receber.',
           filtros=['metodo', 'loja'], ambitos=('admin', 'loja'))
def _pagamentos(f):
    from ..models import Pagamento
    p = f.periodo
    qs = Pagamento.objects.filter(p.filtro('data_pagamento')).select_related('encomenda__loja', 'encomenda__comprador__user', 'metodo')
    metodo = f.escolha('metodo', _metodo_label())
    if metodo:
        qs = qs.filter(metodo__tipo=metodo)
    qs = _loja(f, qs, 'encomenda__loja_id')
    metodos = _metodo_label()
    estados = dict(Pagamento.STATUS)
    linhas = [{
        'pagamento': x.id, 'recebido_em': x.data_pagamento, 'encomenda': x.encomenda_id, 'loja': x.encomenda.loja.nome,
        'cliente': _nome(x.encomenda.comprador.user), 'metodo': metodos.get(x.metodo.tipo, '') if x.metodo_id else '',
        'estado': estados.get(x.status, x.status), 'referencia': x.referencia_transacao if x.referencia_transacao != 'dinheiro' else '',
        'valor': x.valor,
    } for x in qs.order_by('data_pagamento', 'id')[:MAX_LINHAS]]
    por_metodo = {}
    for l in linhas:
        por_metodo[l['metodo'] or 'Outro'] = por_metodo.get(l['metodo'] or 'Outro', ZERO) + l['valor']
    # por receber hoje: dinheiro na entrega de encomendas ainda em curso
    pend = _loja(f, Pagamento.objects.filter(status='pendente', referencia_transacao='dinheiro')
                 .exclude(encomenda__status__in=['cancelado', 'concluido']), 'encomenda__loja_id').aggregate(t=Sum('valor'), n=Count('id'))
    tot = _somas(linhas, ['valor'])
    colunas = [_col('pagamento', 'Pagamento', 'numero'), _col('recebido_em', 'Recebido em', 'datahora'),
               _col('encomenda', 'Encomenda', 'numero')]
    if f.ambito == 'admin' and not _loja_id(f):
        colunas.append(_col('loja', 'Loja'))
    colunas += [_col('cliente', 'Cliente'), _col('metodo', 'Método'), _col('estado', 'Estado hoje'),
                _col('referencia', 'Referência'), _col('valor', 'Valor', 'dinheiro')]
    return {
        'resumo': [_r('Recebido', tot['valor']), _r('Pagamentos', len(linhas), 'numero')]
                  + [_r(m, v) for m, v in sorted(por_metodo.items(), key=lambda x: -x[1])]
                  + [_r('Dinheiro por receber (encomendas em curso)', pend['t'] or ZERO)],
        'colunas': colunas, 'linhas': linhas, 'totais': tot,
        'notas': ['Cartão: conta no momento do pagamento. Dinheiro na entrega: conta quando a encomenda é entregue. '
                  '"Estado hoje" mostra se o pagamento foi depois reembolsado (os reembolsos têm o seu relatório).'],
    }


# ══════════════════════════════════════════════════════════════
# EXECUÇÃO
# ══════════════════════════════════════════════════════════════

def catalogo(ambito='admin', loja_id=None):
    return [{'id': r.id, 'titulo': r.titulo, 'descricao': r.descricao, 'grupo': r.grupo, 'max_dias': r.max_dias,
             'filtros': definicoes_filtros(r.filtros, ambito, loja_id)}
            for r in RELATORIOS.values() if ambito in r.ambitos]


def executar(rid, request, ambito='admin', loja_id=None):
    """(relatorio, periodo, resultado). Levanta KeyError (não existe) ou rel.PeriodoInvalido / FiltroInvalido."""
    r = RELATORIOS[rid]
    if ambito not in r.ambitos:
        raise KeyError(rid)
    periodo = rel.ler_periodo(request, maximo=r.max_dias)
    f = Filtros(periodo, request.GET, loja_id=loja_id, ambito=ambito)
    res = r.gerar(f)
    res['truncado'] = len(res['linhas']) >= MAX_LINHAS
    res['filtros_aplicados'] = filtros_legiveis(r, request.GET, ambito, loja_id)
    return r, periodo, res


def filtros_legiveis(r, params, ambito, loja_id):
    """[(label, valor escolhido)] — para o cabeçalho das exportações."""
    out = []
    for d in definicoes_filtros(r.filtros, ambito, loja_id):
        v = (params.get(d['nome']) or '').strip()
        if not v:
            if d.get('todos'):
                continue
            v = d['opcoes'][0]['valor'] if d.get('opcoes') else ''
            if not v:
                continue
        if d['tipo'] == 'texto':
            out.append((d['label'], v))
        else:
            out.append((d['label'], next((o['label'] for o in d['opcoes'] if o['valor'] == v), v)))
    return out
