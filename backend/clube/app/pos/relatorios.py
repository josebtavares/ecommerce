"""
Painel e relatórios do POS (âmbito 'pos' do motor de relatórios: utils/relatorios_motor.py).

Regras de data (fuso da plataforma, como na loja):
  venda              → quando a conta é fechada (paga)            ContaMesa.fechada_em
  conta cancelada    → quando foi cancelada                       ContaMesa.cancelada_em
  artigo cancelado   → quando o artigo foi cancelado              ItemContaMesa.atualizado_em
  turno de caixa     → quando o turno abriu                       TurnoPOS.aberto_em

Valores de uma conta fechada: artigos (os não cancelados) + taxa de serviço + gorjeta − desconto = total pago.
Conta dividida: o total reparte-se pelos métodos de cada parte (PagamentoDividido); sem partes registadas,
fica como "Dividida (sem detalhe)".
"""
from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import ExtractHour

from ..utils import relatorios as rel
from ..utils import relatorios_motor as motor
from ..utils.horarios import fuso
from ..utils.relatorios import ZERO, d2
from ..utils.relatorios_motor import DIAS_AGREGADO, _col, _r, _somas, relatorio
from .models import ConfiguracaoPOS, ContaMesa, ItemContaMesa, Mesa, PagamentoDividido, ProdutoPOS, TurnoPOS, UtilizadorPOS
from .stock import custos_atuais

METODOS = {**dict(ContaMesa.METODO_PAGAMENTO_CHOICES), 'cartao': 'Cartão', 'dividida': 'Dividida (sem detalhe)'}
ORDEM_METODOS = ['dinheiro', 'cartao', 'mbway', 'transferencia', 'dividida']
SEM_REGISTO = 'Equipa (não registado)'     # contas abertas por membros antes de o POS guardar quem foi


# ── consultas base ───────────────────────────────────────────────────

def contas_vendidas(pos_id, periodo):
    """Contas fechadas (pagas) no período."""
    return ContaMesa.objects.filter(periodo.filtro('fechada_em'), pos_id=pos_id, status='fechada')


def itens_vendidos(pos_id, periodo):
    """Artigos (não cancelados) das contas fechadas no período."""
    return (ItemContaMesa.objects.filter(conta__pos_id=pos_id, conta__status='fechada', conta__fechada_em__gte=periodo.de,
                                         conta__fechada_em__lt=periodo.ate)
            .exclude(status='cancelado'))


def resumo_vendas(pos_id, periodo):
    a = contas_vendidas(pos_id, periodo).aggregate(
        total=Sum('total'), artigos=Sum('subtotal'), taxa=Sum('taxa_servico_valor'), gorjetas=Sum('gorjeta'),
        descontos=Sum('desconto_valor'), n=Count('id'))
    n = a['n'] or 0
    total = a['total'] or ZERO
    return {'total': total, 'contas': n, 'ticket_medio': total / n if n else ZERO, 'artigos': a['artigos'] or ZERO,
            'taxa_servico': a['taxa'] or ZERO, 'gorjetas': a['gorjetas'] or ZERO, 'descontos': a['descontos'] or ZERO}


def por_metodo(contas):
    """{metodo: (valor, nº de contas)} — as contas divididas repartidas pelas partes."""
    out = defaultdict(lambda: [ZERO, 0])
    for m, t, n in contas.exclude(metodo_pagamento='dividida').values_list('metodo_pagamento').annotate(t=Sum('total'), n=Count('id')):
        out[m or 'dividida'][0] += t or ZERO
        out[m or 'dividida'][1] += n
    divididas = dict(contas.filter(metodo_pagamento='dividida').values_list('id', 'total'))
    if divididas:
        partes = defaultdict(lambda: ZERO)
        contadas = set()
        for cid, m, v in PagamentoDividido.objects.filter(conta_id__in=divididas).values_list('conta_id', 'metodo', 'valor'):
            partes[cid, m] += v
        for (cid, m), v in partes.items():
            out[m][0] += v
            if (cid, m) not in contadas:
                out[m][1] += 1
                contadas.add((cid, m))
        for cid, total in divididas.items():
            resto = total - sum((v for (c, _), v in partes.items() if c == cid), ZERO)
            if resto:
                out['dividida'][0] += resto
                out['dividida'][1] += 1
    return dict(out)


def _custo_atual_item(it, custos):
    """Custo de uma unidade com os preços de custo de hoje (vendas anteriores ao registo do custo)."""
    if it.componentes:
        total = ZERO
        for c in it.componentes:
            custo = custos.get((c.get('origem') or 'loja', c.get('produto_id')))
            if custo is None:
                return None
            total += custo * int(c.get('quantidade') or 0)
        return total
    return custos.get(('pos', it.produto_pos_id) if it.produto_pos_id else ('loja', it.produto_id))


def custos_para(itens):
    """Os custos de hoje de todos os produtos (e componentes) destes itens, numa consulta por origem."""
    chaves = set()
    for it in itens:
        chaves.add(('pos', it.produto_pos_id) if it.produto_pos_id else ('loja', it.produto_id))
        for c in it.componentes or []:
            chaves.add((c.get('origem') or 'loja', c.get('produto_id')))
    return custos_atuais(chaves)


def custo_item(it, custos):
    return it.custo_unitario if it.custo_unitario is not None else _custo_atual_item(it, custos)


def nome_atendente(conta):
    if conta.atendente_id and not conta.membro_id:
        return f'{conta.atendente_nome or "Dono"} (dono)'
    return conta.atendente_nome or SEM_REGISTO


def chave_atendente(membro_id, atendente_id, nome):
    """Quem abriu a conta: um membro, o dono, ou (membro apagado / sem registo) só o nome guardado."""
    if membro_id:
        return ('m', membro_id), nome or SEM_REGISTO
    if atendente_id:
        return ('d', atendente_id), f'{nome or "Dono"} (dono)'
    return ('n', nome), nome or SEM_REGISTO


def por_atendente(qs, prefixo='', **agregados):
    """{chave: {'nome', <agregados>}} — agrupa por quem abriu a conta."""
    campos = [f'{prefixo}membro_id', f'{prefixo}atendente_id', f'{prefixo}atendente_nome']
    out = {}
    for r in qs.values(*campos).annotate(**agregados).order_by():
        k, nome = chave_atendente(r.pop(campos[0]), r.pop(campos[1]), r.pop(campos[2]))
        x = out.setdefault(k, {'nome': nome, **{a: None for a in agregados}})
        for a, v in r.items():
            x[a] = v if x[a] is None else x[a] + (v or 0)
    return out


def resumo_turno(t, agora=None):
    """Situação de um turno: vendas em dinheiro (com as partes das divididas), esperado, contado e diferença."""
    from django.utils import timezone
    fim = t.fechado_em or agora or timezone.now()
    contas = ContaMesa.objects.filter(pos_id=t.pos_id, status='fechada', fechada_em__gte=t.aberto_em, fechada_em__lte=fim)
    a = contas.aggregate(v=Sum('total'), n=Count('id'))
    dinheiro = t.vendas_dinheiro(ate=fim)
    esperado = t.valor_abertura + dinheiro
    return {'id': t.id, 'operador': t.operador.nome if t.operador_id else '', 'aberto': t.aberto,
            'aberto_em': t.aberto_em, 'fechado_em': t.fechado_em, 'valor_abertura': t.valor_abertura,
            'vendas_dinheiro': dinheiro, 'esperado': esperado, 'contado': t.valor_fecho,
            'diferenca': (t.valor_fecho - esperado) if t.valor_fecho is not None and not t.aberto else None,
            'vendas_total': a['v'] or ZERO, 'contas': a['n'] or 0}


# ══════════════════════════════════════════════════════════════
# PAINEL (o dashboard do POS)
# ══════════════════════════════════════════════════════════════

def painel(pos, periodo, dono=False):
    p, ant = periodo, periodo.anterior()
    v, va = resumo_vendas(pos.id, p), resumo_vendas(pos.id, ant)
    contas = contas_vendidas(pos.id, p)

    # gráfico: vendas por dia/mês
    s = rel.serie(ContaMesa.objects.filter(pos_id=pos.id, status='fechada'), 'fechada_em', p, t=Sum('total'), n=Count('id'))
    grafico = rel.juntar_series(p, vendas=(s, 't'), contas=(s, 'n'))
    for linha in grafico:
        linha['contas'] = int(linha['contas'])

    # por hora do dia (no fuso da plataforma)
    horas = {h: (t, n) for h, t, n in contas.annotate(h=ExtractHour('fechada_em', tzinfo=fuso()))
             .values_list('h').annotate(t=Sum('total'), n=Count('id')).values_list('h', 't', 'n')}
    por_hora = [{'hora': h, 'vendas': float(horas.get(h, (0, 0))[0] or 0), 'contas': horas.get(h, (0, 0))[1]} for h in range(24)]

    met = por_metodo(contas)
    metodos = [{'metodo': m, 'nome': METODOS.get(m, m), 'valor': d2(met[m][0]), 'contas': met[m][1]}
               for m in sorted(met, key=lambda m: -met[m][0])]

    # produtos
    itens = list(itens_vendidos(pos.id, p).select_related('produto_pos', 'produto'))
    custos = custos_para(itens)
    prods, custo_total, valor_com_custo = {}, ZERO, ZERO
    for it in itens:
        k = ('pos', it.produto_pos_id) if it.produto_pos_id else ('loja', it.produto_id)
        nome = (it.produto_pos or it.produto).nome if (it.produto_pos_id or it.produto_id) else it.nome
        x = prods.setdefault(k, {'nome': nome, 'origem': k[0], 'unidades': 0, 'valor': ZERO})
        x['unidades'] += it.quantidade
        x['valor'] += it.preco_total
        c = custo_item(it, custos)
        if c is not None:
            custo_total += c * it.quantidade
            valor_com_custo += it.preco_total
    top = sorted(prods.values(), key=lambda x: (-x['valor'], x['nome']))[:8]
    unidades = sum(x['unidades'] for x in prods.values())

    # atendentes e mesas
    atend = [{'nome': x['nome'], 'contas': x['n'], 'total': d2(x['t'])}
             for x in por_atendente(contas, n=Count('id'), t=Sum('total')).values()]
    atend.sort(key=lambda x: (-Decimal(x['total']), x['nome']))
    mesas = [{'mesa': num, 'contas': n, 'total': d2(t), 'ticket_medio': d2(t / n if n else ZERO)} for num, n, t in
             contas.values_list('mesa__numero').annotate(n=Count('id'), t=Sum('total')).values_list('mesa__numero', 'n', 't')]
    mesas.sort(key=lambda x: -Decimal(x['total']))

    # cancelamentos (controlo)
    canc = ContaMesa.objects.filter(p.filtro('cancelada_em'), pos_id=pos.id, status='cancelada').aggregate(
        n=Count('id', distinct=True), v=Sum('items__preco_total'))
    itens_canc = ItemContaMesa.objects.filter(p.filtro('atualizado_em'), conta__pos_id=pos.id, status='cancelado').exclude(
        conta__status='cancelada').aggregate(n=Sum('quantidade'), v=Sum('preco_total'))

    # agora
    abertas = ContaMesa.objects.filter(pos_id=pos.id, status='aberta').aggregate(n=Count('id'), v=Sum('total'))
    turno = TurnoPOS.objects.filter(pos_id=pos.id, aberto=True).select_related('operador__user').first()
    ultimo = (TurnoPOS.objects.filter(pos_id=pos.id, aberto=False).select_related('operador__user')
              .order_by('-fechado_em').first())

    def turno_json(t):
        if not t:
            return None
        r = resumo_turno(t)
        return {k: (d2(x) if isinstance(x, Decimal) else x) for k, x in r.items()}

    return {
        'periodo': p.payload(), 'periodo_anterior': ant.payload(),
        'vendas': {
            'total': d2(v['total']), 'variacao': rel.variacao(v['total'], va['total']),
            'contas': v['contas'], 'contas_variacao': rel.variacao(v['contas'], va['contas']),
            'ticket_medio': d2(v['ticket_medio']), 'ticket_variacao': rel.variacao(v['ticket_medio'], va['ticket_medio']),
            'artigos': d2(v['artigos']), 'taxa_servico': d2(v['taxa_servico']), 'gorjetas': d2(v['gorjetas']),
            'descontos': d2(v['descontos']), 'unidades': unidades,
        },
        'margem': {
            'custo': d2(custo_total), 'margem': d2(valor_com_custo - custo_total) if valor_com_custo else None,
            'cobertura': round(float(valor_com_custo / v['artigos'] * 100), 1) if v['artigos'] else None,
        },
        'cancelamentos': {'contas': canc['n'] or 0, 'valor_contas': d2(canc['v']),
                          'artigos': itens_canc['n'] or 0, 'valor_artigos': d2(itens_canc['v'])},
        'grafico': grafico, 'por_hora': por_hora, 'por_metodo': metodos,
        'top_produtos': [{**x, 'valor': d2(x['valor'])} for x in top],
        'por_atendente': atend[:10], 'por_mesa': mesas[:10],
        'agora': {'contas_abertas': abertas['n'] or 0, 'valor_aberto': d2(abertas['v'])},
        'turno': turno_json(turno), 'ultimo_turno': turno_json(ultimo),
        'pode_gerir_turno': dono,
        'iva_definido': bool(pos.percentagem_iva),
    }


# ══════════════════════════════════════════════════════════════
# FILTROS DO POS
# ══════════════════════════════════════════════════════════════

def _so_pos(fn):
    def f(ambito, loja_id, pos_id):
        return fn(pos_id) if ambito == 'pos' and pos_id else None
    return f


def _opcoes(pares):
    return [{'valor': str(v), 'label': str(l)} for v, l in pares]


motor.FILTROS_EXTRA.update({
    'metodo_pos': _so_pos(lambda pid: {
        'nome': 'metodo', 'label': 'Método', 'tipo': 'select', 'todos': 'Todos',
        'opcoes': _opcoes([(m, METODOS[m].replace(' (sem detalhe)', '')) for m in ORDEM_METODOS])}),
    'atendente': _so_pos(lambda pid: {
        'nome': 'atendente', 'label': 'Atendente', 'tipo': 'select', 'todos': 'Todos',
        'opcoes': [{'valor': 'dono', 'label': 'Dono (conta principal)'}] + _opcoes(
            UtilizadorPOS.objects.filter(pos_id=pid).order_by('nome').values_list('id', 'nome'))
            + ([{'valor': 'sem', 'label': SEM_REGISTO}] if ContaMesa.objects.filter(
                pos_id=pid, membro__isnull=True, atendente__isnull=True).exists() else [])}),
    'mesa': _so_pos(lambda pid: {
        'nome': 'mesa', 'label': 'Mesa', 'tipo': 'select', 'todos': 'Todas',
        'opcoes': _opcoes(Mesa.objects.filter(pos_id=pid).order_by('numero').values_list('id', 'numero'))}),
    'estado_conta': _so_pos(lambda pid: {
        'nome': 'estado', 'label': 'Contas', 'tipo': 'select',
        'opcoes': _opcoes([('fechadas', 'fechadas (vendas)'), ('canceladas', 'canceladas'), ('todas', 'fechadas e canceladas')])}),
    'agrupar_produtos_pos': _so_pos(lambda pid: {
        'nome': 'agrupar', 'label': 'Agrupar por', 'tipo': 'select',
        'opcoes': _opcoes([('produto', 'produto'), ('variante', 'produto e variante'), ('categoria', 'categoria')])}),
    'origem_produto': _so_pos(lambda pid: None if ConfiguracaoPOS.objects.filter(id=pid, modo='standalone').exists()
                              and not ItemContaMesa.objects.filter(conta__pos_id=pid, produto__isnull=False).exists() else {
        'nome': 'origem', 'label': 'Origem', 'tipo': 'select', 'todos': 'POS e loja',
        'opcoes': _opcoes([('pos', 'produtos do POS'), ('loja', 'produtos da loja')])}),
    'categoria_pos': _so_pos(lambda pid: {
        'nome': 'categoria', 'label': 'Categoria', 'tipo': 'select', 'todos': 'Todas',
        'opcoes': _opcoes((c, c) for c in ProdutoPOS.objects.filter(pos_id=pid).order_by('categoria')
                          .values_list('categoria', flat=True).distinct())}),
    'tipo_cancelamento': _so_pos(lambda pid: {
        'nome': 'tipo', 'label': 'Tipo', 'tipo': 'select', 'todos': 'Todos',
        'opcoes': _opcoes([('conta', 'contas canceladas'), ('artigo', 'artigos cancelados'), ('desconto', 'descontos')])}),
})


def _atendente(f, qs, prefixo=''):
    a = (f.params.get('atendente') or '').strip()
    if not a:
        return qs
    if a == 'dono':
        return qs.filter(**{f'{prefixo}atendente__isnull': False, f'{prefixo}membro__isnull': True})
    if a == 'sem':
        return qs.filter(**{f'{prefixo}atendente__isnull': True, f'{prefixo}membro__isnull': True})
    m = f.inteiro('atendente')
    if not UtilizadorPOS.objects.filter(id=m, pos_id=f.pos_id).exists():
        raise motor.FiltroInvalido('Valor inválido para "atendente".')
    return qs.filter(**{f'{prefixo}membro_id': m})


def _col_periodo(p):
    return _col('periodo', 'Mês' if p.granularidade == 'mes' else 'Dia', 'mes' if p.granularidade == 'mes' else 'data')


# ══════════════════════════════════════════════════════════════
# VENDAS POR DIA / MÊS
# ══════════════════════════════════════════════════════════════

@relatorio('pos_vendas', 'Vendas por dia / mês',
           'Contas fechadas, artigos, taxa de serviço, gorjetas, descontos, total e ticket médio, por dia ou por mês.',
           filtros=['agrupar_tempo'], max_dias=DIAS_AGREGADO, ambitos=('pos',))
def _pos_vendas(f):
    p = motor._periodo_agrupado(f)
    s = rel.serie(ContaMesa.objects.filter(pos_id=f.pos_id, status='fechada'), 'fechada_em', p,
                  n=Count('id'), artigos=Sum('subtotal'), taxa=Sum('taxa_servico_valor'), gorjetas=Sum('gorjeta'),
                  descontos=Sum('desconto_valor'), total=Sum('total'))
    linhas = []
    for b in p.baldes():
        x = s.get(b) or {}
        n = x.get('n') or 0
        total = x.get('total') or ZERO
        linhas.append({'periodo': b.isoformat(), 'contas': n, 'artigos': x.get('artigos') or ZERO,
                       'taxa_servico': x.get('taxa') or ZERO, 'gorjetas': x.get('gorjetas') or ZERO,
                       'descontos': x.get('descontos') or ZERO, 'total': total, 'ticket_medio': total / n if n else None})
    tot = _somas(linhas, ['contas', 'artigos', 'taxa_servico', 'gorjetas', 'descontos', 'total'])
    n = int(tot['contas'])
    tot['ticket_medio'] = tot['total'] / n if n else None
    return {
        'resumo': [_r('Vendas', tot['total']), _r('Contas fechadas', n, 'numero'), _r('Ticket médio', tot['ticket_medio']),
                   _r('Artigos', tot['artigos']), _r('Taxa de serviço', tot['taxa_servico']), _r('Gorjetas', tot['gorjetas']),
                   _r('Descontos', tot['descontos'])],
        'colunas': [_col_periodo(p), _col('contas', 'Contas', 'numero'), _col('artigos', 'Artigos', 'dinheiro'),
                    _col('taxa_servico', 'Taxa de serviço', 'dinheiro'), _col('gorjetas', 'Gorjetas', 'dinheiro'),
                    _col('descontos', 'Descontos', 'dinheiro'), _col('total', 'Total', 'dinheiro'),
                    _col('ticket_medio', 'Ticket médio', 'dinheiro')],
        'linhas': linhas, 'totais': tot,
        'notas': [NOTA_VENDAS],
    }


NOTA_VENDAS = ('Vendas pela hora em que a conta foi fechada (paga). Total = artigos (sem os cancelados) + taxa de serviço '
               '+ gorjeta − desconto. As contas canceladas não contam (têm o seu relatório).')


# ══════════════════════════════════════════════════════════════
# CONTAS (DETALHE)
# ══════════════════════════════════════════════════════════════

@relatorio('pos_contas', 'Contas — detalhe',
           'Uma linha por conta: mesa, atendente, método de pagamento, valores e NIF do cliente.',
           filtros=['estado_conta', 'metodo_pos', 'atendente', 'mesa'], ambitos=('pos',))
def _pos_contas(f):
    p = f.periodo
    estado = f.escolha('estado', ('fechadas', 'canceladas', 'todas'), 'fechadas')
    fechadas = Q(status='fechada') & p.filtro('fechada_em')
    canceladas = Q(status='cancelada') & p.filtro('cancelada_em')
    cond = {'fechadas': fechadas, 'canceladas': canceladas, 'todas': fechadas | canceladas}[estado]
    qs = ContaMesa.objects.filter(cond, pos_id=f.pos_id).select_related('mesa')
    metodo = f.escolha('metodo', ORDEM_METODOS)
    if metodo:
        qs = qs.filter(metodo_pagamento=metodo)
    mesa = f.inteiro('mesa')
    if mesa:
        qs = qs.filter(mesa_id=mesa)
    qs = _atendente(f, qs)
    qs = qs.annotate(unidades=Sum('items__quantidade', filter=~Q(items__status='cancelado')),
                     valor_cancelado=Sum('items__preco_total', filter=Q(items__status='cancelado')))
    linhas = []
    for c in qs.order_by(F('fechada_em').asc(nulls_last=True), 'cancelada_em', 'id')[:motor.MAX_LINHAS]:
        cancelada = c.status == 'cancelada'
        linhas.append({
            'conta': c.id, 'aberta': c.criada_em, 'fechada': c.cancelada_em if cancelada else c.fechada_em,
            'mesa': c.mesa.numero if c.mesa_id else '', 'atendente': nome_atendente(c),
            'estado': 'Cancelada' if cancelada else 'Fechada',
            'metodo': '' if cancelada else METODOS.get(c.metodo_pagamento, c.metodo_pagamento or '').replace(' (sem detalhe)', ''),
            'unidades': 0 if cancelada else (c.unidades or 0),
            'artigos': ZERO if cancelada else c.subtotal, 'taxa_servico': ZERO if cancelada else c.taxa_servico_valor,
            'gorjeta': ZERO if cancelada else c.gorjeta, 'desconto': ZERO if cancelada else c.desconto_valor,
            'total': ZERO if cancelada else c.total, 'cancelado': c.valor_cancelado or ZERO,
            'nif': c.nif_cliente, 'motivo': c.motivo_cancelamento if cancelada else '',
        })
    tot = _somas(linhas, ['unidades', 'artigos', 'taxa_servico', 'gorjeta', 'desconto', 'total', 'cancelado'])
    n_fech = sum(1 for l in linhas if l['estado'] == 'Fechada')
    colunas = [_col('conta', 'Conta', 'id'), _col('aberta', 'Aberta em', 'datahora'),
               _col('fechada', 'Fechada em' if estado == 'fechadas' else 'Fechada / cancelada em', 'datahora'),
               _col('mesa', 'Mesa'), _col('atendente', 'Atendente')]
    if estado != 'fechadas':
        colunas.append(_col('estado', 'Estado'))
    colunas += [_col('metodo', 'Método'), _col('unidades', 'Unidades', 'numero'), _col('artigos', 'Artigos', 'dinheiro'),
                _col('taxa_servico', 'Taxa serviço', 'dinheiro'), _col('gorjeta', 'Gorjeta', 'dinheiro'),
                _col('desconto', 'Desconto', 'dinheiro'), _col('total', 'Total', 'dinheiro'),
                _col('cancelado', 'Artigos cancelados', 'dinheiro'), _col('nif', 'NIF cliente')]
    if estado != 'fechadas':
        colunas.append(_col('motivo', 'Motivo do cancelamento'))
    return {
        'resumo': [_r('Total', tot['total']), _r('Contas fechadas', n_fech, 'numero'),
                   _r('Ticket médio', tot['total'] / n_fech if n_fech else None),
                   _r('Contas canceladas', len(linhas) - n_fech, 'numero'), _r('Artigos cancelados', tot['cancelado']),
                   _r('Com NIF do cliente', sum(1 for l in linhas if l['nif']), 'numero')],
        'colunas': colunas, 'linhas': linhas, 'totais': tot,
        'notas': [NOTA_VENDAS + ' Uma conta cancelada aparece pela data do cancelamento, com total zero; '
                  '"Artigos cancelados" é o valor dos artigos que não foram cobrados.'],
    }


# ══════════════════════════════════════════════════════════════
# VENDAS POR PRODUTO
# ══════════════════════════════════════════════════════════════

@relatorio('pos_produtos', 'Vendas por produto',
           'Unidades e valor vendidos por produto (sozinhos e dentro de menus), custo e margem.',
           filtros=['agrupar_produtos_pos', 'origem_produto', 'categoria_pos', 'pesquisa_produto'],
           max_dias=DIAS_AGREGADO, ambitos=('pos',))
def _pos_produtos(f):
    from ..models import Produto
    p = f.periodo
    agrupar = f.escolha('agrupar', ('produto', 'variante', 'categoria'), 'produto')
    origem = f.escolha('origem', ('pos', 'loja'))
    categoria = f.texto('categoria', 100)
    q = f.texto('q').lower()
    itens = list(itens_vendidos(f.pos_id, p).select_related('produto_pos', 'produto'))
    custos = custos_para(itens)
    mostra_origem = any(it.produto_id for it in itens)

    # nomes e categorias de todos os produtos que aparecem (vendidos sozinhos ou dentro de menus)
    ids = {'pos': set(), 'loja': set()}
    for it in itens:
        ids['pos' if it.produto_pos_id else 'loja'].add(it.produto_pos_id or it.produto_id)
        for c in it.componentes or []:
            ids[c.get('origem') or 'loja'].add(c.get('produto_id'))
    info = {('pos', i): (n, cat or 'Sem categoria') for i, n, cat in
            ProdutoPOS.objects.filter(id__in=ids['pos']).values_list('id', 'nome', 'categoria')}
    cats_loja = {}
    for pid, nome in Produto.categorias.through.objects.filter(produto_id__in=ids['loja']).values_list('produto_id', 'categorialoja__nome'):
        cats_loja.setdefault(pid, []).append(nome)
    info.update({('loja', i): (n, ', '.join(sorted(cats_loja.get(i, []))) or 'Sem categoria') for i, n in
                 Produto.objects.filter(id__in=ids['loja']).values_list('id', 'nome')})

    def aceita(k):
        if origem and k[0] != origem:
            return False
        nome, cat = info.get(k, ('', 'Sem categoria'))
        if categoria and cat != categoria:
            return False
        return not q or q in nome.lower()

    linhas = {}

    def linha(k, nome_variante=''):
        nome, cat = info.get(k, ('Produto apagado', 'Sem categoria'))
        if agrupar == 'categoria':
            chave, rotulo = ('cat', cat), cat
        elif agrupar == 'variante':
            chave, rotulo = (k, nome_variante), nome
        else:
            chave, rotulo = k, nome
        if chave not in linhas:
            linhas[chave] = {'produto': rotulo, 'variante': nome_variante, 'origem': 'POS' if k[0] == 'pos' else 'Loja',
                             'categoria': cat, 'unidades': 0, 'em_menus': 0, 'valor': ZERO, 'custo': ZERO, '_sem_custo': False}
        return linhas[chave]

    for it in itens:
        k = ('pos', it.produto_pos_id) if it.produto_pos_id else ('loja', it.produto_id)
        if aceita(k):
            var = ', '.join(str(v) for v in (it.atributos or {}).values()) if agrupar == 'variante' else ''
            l = linha(k, var)
            l['unidades'] += it.quantidade
            l['valor'] += it.preco_total
            c = custo_item(it, custos)
            if c is None:
                l['_sem_custo'] = True
            else:
                l['custo'] += c * it.quantidade
        for c in it.componentes or []:
            ck = (c.get('origem') or 'loja', c.get('produto_id'))
            n = int(c.get('quantidade') or 0) * it.quantidade
            if n and ck[1] and aceita(ck):
                linha(ck)['em_menus'] += n

    out = []
    for l in linhas.values():
        sem = l.pop('_sem_custo')
        tem_custo = not sem and l['unidades'] > 0
        l['custo'] = l['custo'] if tem_custo else None
        l['margem'] = l['valor'] - l['custo'] if tem_custo else None
        l['margem_pct'] = round(l['margem'] / l['valor'] * 100, 1) if tem_custo and l['valor'] else None
        out.append(l)
    out.sort(key=lambda l: (-l['valor'], -l['unidades'] - l['em_menus'], l['produto']))
    tot = _somas(out, ['unidades', 'em_menus', 'valor'])
    com = [l for l in out if l['margem'] is not None]
    tot['custo'] = sum((l['custo'] for l in com), ZERO) if com else None
    tot['margem'] = sum((l['margem'] for l in com), ZERO) if com else None
    valor_com = sum((l['valor'] for l in com), ZERO)
    tot['margem_pct'] = round(tot['margem'] / valor_com * 100, 1) if com and valor_com else None
    sem_custo = sum(1 for l in out if l['margem'] is None and l['unidades'])

    colunas = [_col('produto', 'Categoria' if agrupar == 'categoria' else 'Produto')]
    if agrupar == 'variante':
        colunas.append(_col('variante', 'Variante'))
    if agrupar != 'categoria':
        if mostra_origem:
            colunas.append(_col('origem', 'Origem'))
        colunas.append(_col('categoria', 'Categoria'))
    colunas += [_col('unidades', 'Unidades', 'numero'), _col('em_menus', 'Em menus', 'numero'),
                _col('valor', 'Vendido', 'dinheiro'), _col('custo', 'Custo', 'dinheiro'),
                _col('margem', 'Margem', 'dinheiro'), _col('margem_pct', 'Margem %', 'percent')]
    notas = ['Artigos das contas fechadas no período (os cancelados não contam). "Vendido" = valor dos artigos vendidos '
             'sozinhos; as unidades que saíram dentro de menus contam em "Em menus" (o valor fica no menu). '
             'Sem taxa de serviço, gorjetas nem descontos da conta. Custo = o preço de custo guardado em cada venda '
             '(nas vendas antigas, o custo de hoje); num menu, a soma do custo dos componentes.']
    if sem_custo:
        notas.insert(0, f'{sem_custo} linha(s) sem preço de custo: preenche-o nos Produtos para a margem ficar completa.')
    return {
        'resumo': [_r('Vendido', tot['valor']), _r('Unidades', int(tot['unidades']), 'numero'),
                   _r('Unidades em menus', int(tot['em_menus']), 'numero'), _r('Custo (produtos com custo)', tot['custo']),
                   _r('Margem (produtos com custo)', tot['margem']), _r('Margem %', tot['margem_pct'], 'percent')],
        'colunas': colunas, 'linhas': out, 'totais': tot, 'notas': notas,
    }


# ══════════════════════════════════════════════════════════════
# PAGAMENTOS POR MÉTODO (FECHO DIÁRIO)
# ══════════════════════════════════════════════════════════════

@relatorio('pos_pagamentos', 'Pagamentos por método',
           'Quanto entrou em dinheiro, cartão, MBWay e transferência, por dia ou por mês (o fecho diário).',
           filtros=['agrupar_tempo'], max_dias=DIAS_AGREGADO, ambitos=('pos',), grupo='Caixa')
def _pos_pagamentos(f):
    from datetime import datetime
    from django.db.models.functions import TruncDate, TruncMonth
    p = motor._periodo_agrupado(f)
    trunc = TruncDate if p.granularidade == 'dia' else TruncMonth
    contas = contas_vendidas(f.pos_id, p).annotate(_b=trunc('fechada_em', tzinfo=fuso()))
    por_balde = defaultdict(lambda: defaultdict(lambda: ZERO))

    def balde(b):
        return b.date() if isinstance(b, datetime) else b
    for b, m, t in contas.exclude(metodo_pagamento='dividida').values_list('_b', 'metodo_pagamento').annotate(t=Sum('total')).values_list('_b', 'metodo_pagamento', 't'):
        por_balde[balde(b)][m or 'dividida'] += t or ZERO
    divididas = {cid: (balde(b), t) for cid, b, t in contas.filter(metodo_pagamento='dividida').values_list('id', '_b', 'total')}
    pagos = defaultdict(lambda: ZERO)
    for cid, m, v in PagamentoDividido.objects.filter(conta_id__in=divididas).values_list('conta_id', 'metodo', 'valor'):
        por_balde[divididas[cid][0]][m] += v
        pagos[cid] += v
    for cid, (b, t) in divididas.items():
        if t - pagos[cid]:
            por_balde[b]['dividida'] += t - pagos[cid]
    usados = [m for m in ORDEM_METODOS if any(por_balde[b].get(m) for b in list(por_balde))] or ['dinheiro']
    n_contas = dict((balde(b), n) for b, n in contas.values_list('_b').annotate(n=Count('id')).values_list('_b', 'n'))
    linhas = []
    for b in p.baldes():
        x = por_balde.get(b) or {}
        linha = {'periodo': b.isoformat(), 'contas': n_contas.get(b, 0)}
        for m in usados:
            linha[m] = x.get(m, ZERO)
        linha['total'] = sum((x.get(m, ZERO) for m in usados), ZERO)
        linhas.append(linha)
    tot = _somas(linhas, ['contas', 'total'] + usados)
    return {
        'resumo': [_r('Total recebido', tot['total'])] + [_r(METODOS[m], tot[m]) for m in usados]
                  + [_r('Contas fechadas', int(tot['contas']), 'numero')],
        'colunas': [_col_periodo(p), _col('contas', 'Contas', 'numero')]
                   + [_col(m, METODOS[m], 'dinheiro') for m in usados] + [_col('total', 'Total', 'dinheiro')],
        'linhas': linhas, 'totais': tot,
        'notas': ['Pela hora em que a conta foi fechada. Uma conta dividida reparte-se pelos métodos de cada parte; '
                  'sem as partes registadas aparece como "Dividida (sem detalhe)". Só aparecem os métodos usados no período.'],
    }


# ══════════════════════════════════════════════════════════════
# TURNOS DE CAIXA
# ══════════════════════════════════════════════════════════════

@relatorio('pos_turnos', 'Turnos de caixa',
           'Cada turno: quem abriu, fundo de caixa, vendas em dinheiro, o esperado, o contado e a diferença.',
           ambitos=('pos',), grupo='Caixa')
def _pos_turnos(f):
    from django.utils import timezone
    agora = timezone.now()
    turnos = TurnoPOS.objects.filter(f.periodo.filtro('aberto_em'), pos_id=f.pos_id).select_related('operador__user')
    linhas = []
    for t in turnos.order_by('aberto_em', 'id')[:motor.MAX_LINHAS]:
        r = resumo_turno(t, agora)
        linhas.append({'turno': t.id, 'operador': r['operador'], 'estado': 'Aberto' if t.aberto else 'Fechado',
                       'aberto_em': t.aberto_em, 'fechado_em': t.fechado_em, 'contas': r['contas'],
                       'vendas_total': r['vendas_total'], 'abertura': t.valor_abertura, 'vendas_dinheiro': r['vendas_dinheiro'],
                       'esperado': r['esperado'], 'contado': r['contado'], 'diferenca': r['diferenca']})
    tot = _somas(linhas, ['contas', 'vendas_total', 'vendas_dinheiro'])
    fechados = [l for l in linhas if l['diferenca'] is not None]
    tot['diferenca'] = sum((l['diferenca'] for l in fechados), ZERO) if fechados else None
    return {
        'resumo': [_r('Turnos', len(linhas), 'numero'), _r('Vendas nos turnos', tot['vendas_total']),
                   _r('Vendas em dinheiro', tot['vendas_dinheiro']), _r('Diferença acumulada', tot['diferenca']),
                   _r('Turnos com falta', sum(1 for l in fechados if l['diferenca'] < 0), 'numero'),
                   _r('Turnos com sobra', sum(1 for l in fechados if l['diferenca'] > 0), 'numero')],
        'colunas': [_col('turno', 'Turno', 'id'), _col('operador', 'Operador'), _col('estado', 'Estado'),
                    _col('aberto_em', 'Aberto em', 'datahora'), _col('fechado_em', 'Fechado em', 'datahora'),
                    _col('contas', 'Contas', 'numero'), _col('vendas_total', 'Vendas (todos os métodos)', 'dinheiro'),
                    _col('abertura', 'Fundo de caixa', 'dinheiro'), _col('vendas_dinheiro', 'Vendas em dinheiro', 'dinheiro'),
                    _col('esperado', 'Esperado', 'dinheiro'), _col('contado', 'Contado', 'dinheiro'),
                    _col('diferenca', 'Diferença', 'dinheiro')],
        'linhas': linhas, 'totais': tot,
        'notas': ['Pela data em que o turno abriu. Esperado = fundo de caixa + vendas em dinheiro do turno (incluindo a parte '
                  'em dinheiro das contas divididas). Diferença = contado − esperado (negativa = falta dinheiro). '
                  'Num turno ainda aberto, as vendas são até agora.'],
    }


# ══════════════════════════════════════════════════════════════
# VENDAS POR ATENDENTE
# ══════════════════════════════════════════════════════════════

@relatorio('pos_atendentes', 'Vendas por atendente',
           'Por membro da equipa: contas fechadas, vendas, ticket médio, gorjetas e cancelamentos.',
           filtros=['atendente'], max_dias=DIAS_AGREGADO, ambitos=('pos',), grupo='Equipa')
def _pos_atendentes(f):
    p = f.periodo
    vend = por_atendente(_atendente(f, contas_vendidas(f.pos_id, p)), n=Count('id'), t=Sum('total'), g=Sum('gorjeta'))
    uni = por_atendente(_atendente(f, itens_vendidos(f.pos_id, p), 'conta__'), 'conta__', u=Sum('quantidade'))
    cc = por_atendente(_atendente(f, ContaMesa.objects.filter(p.filtro('cancelada_em'), pos_id=f.pos_id, status='cancelada')),
                       n=Count('id'))
    ic = por_atendente(_atendente(f, ItemContaMesa.objects.filter(p.filtro('atualizado_em'), conta__pos_id=f.pos_id,
                                                                  status='cancelado').exclude(conta__status='cancelada'), 'conta__'),
                       'conta__', n=Sum('quantidade'), v=Sum('preco_total'))
    linhas = []
    for k in set(vend) | set(cc) | set(ic):
        v, u, c, i = vend.get(k, {}), uni.get(k, {}), cc.get(k, {}), ic.get(k, {})
        nome = (v or c or i)['nome']
        n, t = v.get('n') or 0, v.get('t') or ZERO
        linhas.append({'atendente': nome, 'contas': n, 'total': t, 'ticket_medio': t / n if n else None,
                       'unidades': u.get('u') or 0, 'gorjetas': v.get('g') or ZERO, 'contas_canceladas': c.get('n') or 0,
                       'artigos_cancelados': i.get('n') or 0, 'valor_cancelado': i.get('v') or ZERO})
    linhas.sort(key=lambda l: (-l['total'], l['atendente']))
    tot = _somas(linhas, ['contas', 'total', 'unidades', 'gorjetas', 'contas_canceladas', 'artigos_cancelados', 'valor_cancelado'])
    n = int(tot['contas'])
    tot['ticket_medio'] = tot['total'] / n if n else None
    return {
        'resumo': [_r('Vendas', tot['total']), _r('Contas fechadas', n, 'numero'), _r('Ticket médio', tot['ticket_medio']),
                   _r('Gorjetas', tot['gorjetas']), _r('Contas canceladas', int(tot['contas_canceladas']), 'numero'),
                   _r('Artigos cancelados', tot['valor_cancelado'])],
        'colunas': [_col('atendente', 'Atendente'), _col('contas', 'Contas', 'numero'), _col('total', 'Vendas', 'dinheiro'),
                    _col('ticket_medio', 'Ticket médio', 'dinheiro'), _col('unidades', 'Unidades', 'numero'),
                    _col('gorjetas', 'Gorjetas', 'dinheiro'), _col('contas_canceladas', 'Contas canceladas', 'numero'),
                    _col('artigos_cancelados', 'Artigos cancelados', 'numero'),
                    _col('valor_cancelado', 'Valor cancelado', 'dinheiro')],
        'linhas': linhas, 'totais': tot,
        'notas': ['O atendente é quem abriu a conta (o dono ou um membro da equipa). '
                  f'"{SEM_REGISTO}": contas abertas por membros antes de o POS registar quem as abriu. '
                  'Vendas pela hora do fecho; cancelamentos pela hora do cancelamento.'],
    }


# ══════════════════════════════════════════════════════════════
# CANCELAMENTOS E DESCONTOS (CONTROLO)
# ══════════════════════════════════════════════════════════════

@relatorio('pos_cancelamentos', 'Cancelamentos e descontos',
           'Contas canceladas, artigos cancelados e descontos dados, com o atendente e o motivo — para controlo interno.',
           filtros=['tipo_cancelamento', 'atendente'], ambitos=('pos',), grupo='Equipa')
def _pos_cancelamentos(f):
    p = f.periodo
    tipo = f.escolha('tipo', ('conta', 'artigo', 'desconto'))
    linhas = []
    if tipo in ('', 'conta'):
        qs = _atendente(f, ContaMesa.objects.filter(p.filtro('cancelada_em'), pos_id=f.pos_id, status='cancelada')
                        .select_related('mesa').annotate(v=Sum('items__preco_total'), u=Sum('items__quantidade')))
        for c in qs[:motor.MAX_LINHAS]:
            linhas.append({'quando': c.cancelada_em, 'tipo': 'Conta cancelada', 'conta': c.id,
                           'mesa': c.mesa.numero if c.mesa_id else '', 'atendente': nome_atendente(c),
                           'descricao': f'{c.u or 0} artigo(s)', 'motivo': c.motivo_cancelamento, 'valor': c.v or ZERO})
    if tipo in ('', 'artigo'):
        qs = _atendente(f, ItemContaMesa.objects.filter(p.filtro('atualizado_em'), conta__pos_id=f.pos_id, status='cancelado')
                        .exclude(conta__status='cancelada').select_related('conta__mesa'), 'conta__')
        for it in qs[:motor.MAX_LINHAS]:
            linhas.append({'quando': it.atualizado_em, 'tipo': 'Artigo cancelado', 'conta': it.conta_id,
                           'mesa': it.conta.mesa.numero if it.conta.mesa_id else '', 'atendente': nome_atendente(it.conta),
                           'descricao': f'{it.quantidade}× {it.nome}', 'motivo': '', 'valor': it.preco_total})
    if tipo in ('', 'desconto'):
        qs = _atendente(f, contas_vendidas(f.pos_id, p).filter(desconto_valor__gt=0).select_related('mesa'))
        for c in qs[:motor.MAX_LINHAS]:
            linhas.append({'quando': c.fechada_em, 'tipo': 'Desconto', 'conta': c.id, 'mesa': c.mesa.numero if c.mesa_id else '',
                           'atendente': nome_atendente(c), 'descricao': f'conta de {d2(c.subtotal + c.taxa_servico_valor + c.gorjeta)}',
                           'motivo': '', 'valor': c.desconto_valor})
    linhas.sort(key=lambda l: (l['quando'], l['conta']))

    def soma(t):
        return sum((l['valor'] for l in linhas if l['tipo'] == t), ZERO)
    return {
        'resumo': [_r('Contas canceladas', sum(1 for l in linhas if l['tipo'] == 'Conta cancelada'), 'numero'),
                   _r('Valor das contas canceladas', soma('Conta cancelada')),
                   _r('Artigos cancelados', soma('Artigo cancelado')),
                   _r('Descontos', soma('Desconto'))],
        'colunas': [_col('quando', 'Quando', 'datahora'), _col('tipo', 'Tipo'), _col('conta', 'Conta', 'id'), _col('mesa', 'Mesa'),
                    _col('atendente', 'Atendente da conta'), _col('descricao', 'Descrição'), _col('motivo', 'Motivo'),
                    _col('valor', 'Valor', 'dinheiro')],
        'linhas': linhas, 'totais': _somas(linhas, ['valor']),
        'notas': ['Artigos cancelados: os que ficaram na conta marcados como cancelados (não foram cobrados). '
                  'Os artigos retirados de uma conta ainda aberta antes de serem pedidos não ficam registados. '
                  'O atendente é quem abriu a conta.'],
    }


# ══════════════════════════════════════════════════════════════
# MAPA DE IVA
# ══════════════════════════════════════════════════════════════

@relatorio('pos_iva', 'Mapa de IVA',
           'Vendas separadas em base tributável e IVA, à taxa definida nas configurações do POS.',
           filtros=['agrupar_tempo'], max_dias=DIAS_AGREGADO, ambitos=('pos',), grupo='Plataforma')
def _pos_iva(f):
    taxa = ConfiguracaoPOS.objects.values_list('percentagem_iva', flat=True).get(id=f.pos_id) or ZERO
    res = _pos_vendas(f)
    fator = 1 + taxa / 100
    linhas = []
    for l in res['linhas']:
        tributavel = l['total'] - l['gorjetas']
        base = (tributavel / fator).quantize(Decimal('0.01'))
        linhas.append({'periodo': l['periodo'], 'contas': l['contas'], 'vendas': l['total'], 'gorjetas': l['gorjetas'],
                       'tributavel': tributavel, 'taxa': taxa, 'base': base, 'iva': tributavel - base})
    tot = _somas(linhas, ['contas', 'vendas', 'gorjetas', 'tributavel', 'base', 'iva'])
    notas = ['Os preços do POS incluem IVA: base = (vendas − gorjetas) ÷ (1 + taxa); IVA = (vendas − gorjetas) − base. '
             'A taxa de serviço entra na base; as gorjetas não. Mapa de apoio: o apuramento oficial é feito pelo '
             'contabilista com as faturas certificadas.']
    if not taxa:
        notas.insert(0, 'O POS não tem taxa de IVA definida (0%). Define-a nas configurações do POS para este mapa fazer sentido.')
    return {
        'resumo': [_r('Vendas (com IVA)', tot['vendas']), _r('Base tributável', tot['base']),
                   _r(f'IVA ({taxa.normalize():f}%)'.replace('.', ','), tot['iva']), _r('Gorjetas (fora do IVA)', tot['gorjetas']),
                   _r('Contas fechadas', int(tot['contas']), 'numero')],
        'colunas': [res['colunas'][0], _col('contas', 'Contas', 'numero'), _col('vendas', 'Vendas', 'dinheiro'),
                    _col('gorjetas', 'Gorjetas', 'dinheiro'), _col('tributavel', 'Tributável', 'dinheiro'),
                    _col('taxa', 'Taxa', 'percent'), _col('base', 'Base tributável', 'dinheiro'), _col('iva', 'IVA', 'dinheiro')],
        'linhas': linhas, 'totais': tot, 'notas': notas,
    }
