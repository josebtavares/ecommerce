"""
Relatórios das marcações (módulo de relatórios da loja e do admin — utils/relatorios_motor.py).
Contam pela data da marcação (o dia do serviço). Receita = preço das marcações concluídas
(o final, se a loja o registou), menos o que foi devolvido.
"""
from collections import defaultdict
from decimal import Decimal

from ..utils import relatorios_motor as motor
from ..utils.relatorios import ZERO
from ..utils.relatorios_motor import _col, _loja, _r, _somas, relatorio
from .models import Marcacao, Profissional


def _f_estado(ambito, loja_id, pos_id):
    if ambito == 'pos':
        return None
    return {'nome': 'estado', 'label': 'Estado', 'tipo': 'select', 'todos': 'Todos',
            'opcoes': motor._opcoes(Marcacao.ESTADOS)}


def _f_profissional(ambito, loja_id, pos_id):
    if ambito != 'loja':
        return None
    return {'nome': 'profissional', 'label': 'Profissional', 'tipo': 'select', 'todos': 'Todos',
            'opcoes': [{'valor': str(i), 'label': n} for i, n in
                       Profissional.objects.filter(loja_id=loja_id).order_by('ordem', 'nome').values_list('id', 'nome')]}


motor.FILTROS_EXTRA.update({'estado_marcacao': _f_estado, 'profissional_servicos': _f_profissional})


def _base(f):
    qs = _loja(f, Marcacao.objects.filter(f.periodo.filtro('inicio'))).exclude(estado='expirada')
    estado = f.escolha('estado', dict(Marcacao.ESTADOS))
    if estado:
        qs = qs.filter(estado=estado)
    prof = f.inteiro('profissional') if f.ambito == 'loja' else None
    if prof:
        qs = qs.filter(profissional_id=prof)
    return qs


def _receita(m):
    """O que a marcação rendeu à loja: só as concluídas (e o que ficou de uma falta paga sem devolução).
    Concluída: o preço — numa paga antecipada só se devolve o pago a mais (valor_pago − preço)."""
    if m.estado == 'concluida':
        return m.preco
    if m.estado in ('falta', 'cancelada') and m.pago:
        return m.valor_pago - m.valor_reembolsado
    return ZERO


@relatorio('servicos_marcacoes', 'Marcações — detalhe',
           'Cada marcação: dia, serviço, profissional, cliente, estado, preço, pago e devolvido.',
           filtros=['loja', 'estado_marcacao', 'profissional_servicos'], ambitos=('loja', 'admin'), grupo='Serviços')
def _detalhe(f):
    qs = _base(f).select_related('profissional', 'cliente__user', 'loja').order_by('inicio', 'id')
    linhas = []
    for m in qs[:motor.MAX_LINHAS]:
        linhas.append({'marcacao': m.id, 'inicio': m.inicio, 'loja': m.loja.nome, 'servico': m.servico_nome,
                       'profissional': m.profissional.nome,
                       'cliente': (m.cliente.nome if m.cliente_id else '') or m.cliente_nome,
                       'estado': m.get_estado_display(), 'pagamento': m.get_pagamento_display(),
                       'preco': m.preco, 'pago': m.valor_pago, 'devolvido': m.valor_reembolsado, 'receita': _receita(m)})
    n = len(linhas)
    contar = lambda e: sum(1 for l in linhas if l['estado'] == dict(Marcacao.ESTADOS)[e])
    concl, faltas = contar('concluida'), contar('falta')
    fechadas = concl + faltas
    colunas = [_col('marcacao', 'Marcação', 'id'), _col('inicio', 'Dia e hora', 'datahora')]
    if f.ambito == 'admin':
        colunas.append(_col('loja', 'Loja'))
    colunas += [_col('servico', 'Serviço'), _col('profissional', 'Profissional'), _col('cliente', 'Cliente'),
                _col('estado', 'Estado'), _col('pagamento', 'Pagamento'), _col('preco', 'Preço', 'dinheiro'),
                _col('pago', 'Pago antecipado', 'dinheiro'), _col('devolvido', 'Devolvido', 'dinheiro'),
                _col('receita', 'Receita', 'dinheiro')]
    return {
        'resumo': [_r('Marcações', n, 'numero'), _r('Concluídas', concl, 'numero'),
                   _r('Canceladas', contar('cancelada'), 'numero'), _r('Faltas', faltas, 'numero'),
                   _r('Taxa de faltas', round(faltas / fechadas * 100, 1) if fechadas else None, 'percent'),
                   _r('Receita', sum((l['receita'] for l in linhas), ZERO))],
        'colunas': colunas, 'linhas': linhas, 'totais': _somas(linhas, ['pago', 'devolvido', 'receita']),
        'notas': ['Pela data da marcação (o dia do serviço); as expiradas (não pagas a tempo) não contam. '
                  'Receita = preço das concluídas (o final, se foi registado) menos o devolvido; '
                  'numa falta ou cancelamento pago sem devolução, conta o que ficou. '
                  'Taxa de faltas = faltas ÷ (concluídas + faltas).'],
    }


def _agrupado(f, chave, nome, extra=None):
    """extra: {chave: (nome, {campo: valor})} — colunas a mais (e linhas só com elas)."""
    vazio = {'marcacoes': 0, 'concluidas': 0, 'canceladas': 0, 'faltas': 0, 'minutos': 0, 'receita': ZERO}
    grupos = defaultdict(lambda: dict(vazio))
    nomes = {}
    for m in _base(f).select_related('profissional')[:motor.MAX_LINHAS]:
        k = chave(m)
        nomes[k] = nome(m)
        g = grupos[k]
        g['marcacoes'] += 1
        if m.estado == 'concluida':
            g['concluidas'] += 1
            g['minutos'] += m.duracao_min
        elif m.estado == 'cancelada':
            g['canceladas'] += 1
        elif m.estado == 'falta':
            g['faltas'] += 1
        g['receita'] += _receita(m)
    for k, (n, campos) in (extra or {}).items():
        nomes.setdefault(k, n)
        grupos[k].update(campos)
    linhas = []
    for k, g in grupos.items():
        fechadas = g['concluidas'] + g['faltas']
        linhas.append({'nome': nomes[k], **g, 'horas': round(g['minutos'] / 60, 1),
                       'taxa_faltas': round(g['faltas'] / fechadas * 100, 1) if fechadas else None,
                       'ticket': (g['receita'] / g['concluidas']).quantize(Decimal('0.01')) if g['concluidas'] else None})
    linhas.sort(key=lambda l: (-l['receita'], l['nome']))
    for l in linhas:
        l.pop('minutos')
    return linhas


def _colunas_agrupado(rotulo):
    return [_col('nome', rotulo), _col('marcacoes', 'Marcações', 'numero'), _col('concluidas', 'Concluídas', 'numero'),
            _col('canceladas', 'Canceladas', 'numero'), _col('faltas', 'Faltas', 'numero'),
            _col('taxa_faltas', 'Taxa de faltas', 'percent'), _col('horas', 'Horas de serviço', 'numero'),
            _col('receita', 'Receita', 'dinheiro'), _col('ticket', 'Valor médio', 'dinheiro')]


@relatorio('servicos_profissionais', 'Marcações por profissional',
           'Por profissional: marcações, concluídas, faltas, horas de serviço e receita.',
           filtros=['estado_marcacao'], ambitos=('loja',), grupo='Serviços')
def _por_profissional(f):
    linhas = _agrupado(f, lambda m: m.profissional_id, lambda m: m.profissional.nome)
    return {'resumo': [_r('Profissionais', len(linhas), 'numero'), _r('Receita', sum((l['receita'] for l in linhas), ZERO))],
            'colunas': _colunas_agrupado('Profissional'), 'linhas': linhas,
            'totais': _somas(linhas, ['marcacoes', 'concluidas', 'canceladas', 'faltas', 'horas', 'receita']),
            'notas': ['Pela data da marcação. Uma marcação passada a outro profissional conta para quem a tem agora.']}


@relatorio('servicos_servicos', 'Marcações por serviço',
           'Por serviço: marcações, concluídas, faltas e receita.',
           filtros=['loja', 'profissional_servicos'], ambitos=('loja', 'admin'), grupo='Serviços')
def _por_servico(f):
    admin = f.ambito == 'admin'
    # cada serviço feito dentro de um pacote concluído (a receita fica no pacote)
    em_pacotes = {}
    for m in _base(f).filter(estado='concluida').exclude(componentes=[]).select_related('loja')[:motor.MAX_LINHAS]:
        for c in m.componentes:
            k = (m.loja_id, c['id']) if admin else c['id']
            n, campos = em_pacotes.get(k, (f"{c['nome']} · {m.loja.nome}" if admin else c['nome'], {'em_pacotes': 0}))
            campos['em_pacotes'] += 1
            em_pacotes[k] = (n, campos)
    if admin:
        linhas = _agrupado(f, lambda m: (m.loja_id, m.servico_id), lambda m: f'{m.servico_nome} · {m.loja.nome}', em_pacotes)
    else:
        linhas = _agrupado(f, lambda m: m.servico_id, lambda m: m.servico_nome, em_pacotes)
    for l in linhas:
        l.setdefault('em_pacotes', 0)
    colunas = _colunas_agrupado('Serviço')
    colunas.insert(3, _col('em_pacotes', 'Feitos em pacotes', 'numero'))
    return {'resumo': [_r('Serviços', len(linhas), 'numero'), _r('Receita', sum((l['receita'] for l in linhas), ZERO))],
            'colunas': colunas, 'linhas': linhas,
            'totais': _somas(linhas, ['marcacoes', 'concluidas', 'em_pacotes', 'canceladas', 'faltas', 'horas', 'receita']),
            'notas': ['Pela data da marcação; o nome é o que o serviço tinha quando foi marcado.',
                      'Feitos em pacotes = quantas vezes o serviço foi feito dentro de um pacote concluído '
                      '(a receita conta no pacote).']}
