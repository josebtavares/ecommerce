"""
Pagamentos com cartão (vinti4): a lista, os filtros, os totais, a ficha e o CSV — iguais no Admin → Pagamentos →
Cartão (todas as transacções) e no backoffice da loja → Pagamentos (só as dela). As vistas só escolhem o conjunto
de partida (Views/pagamentosAdminView.py e Views/lojaCartaoView.py).

Filtros (?): estado, reconciliacao=falta|feita, tipo=encomenda|marcacao|fatura|comissoes, de, ate (AAAA-MM-DD,
pela data em que o cliente foi à SISP), q (merchantRef, referência, descrição, cliente; no admin também a loja).
"""
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

PREFIXOS = {'encomenda': 'enc-', 'marcacao': 'mar-', 'fatura': 'fat-', 'comissoes': 'com-'}
TIPOS = {'encomenda': 'Encomenda', 'marcacao': 'Marcação', 'fatura': 'Mensalidade', 'comissoes': 'Comissões'}
MAX_CSV = 5000


def _quando(dt):
    return f'{timezone.localtime(dt):%d/%m/%Y %H:%M}' if dt else ''


class FiltroInvalido(ValueError):
    pass


def filtrar(qs, params, de=None, ate=None, admin=False):
    """→ (qs filtrado, qs sem os filtros de estado — para as contagens dos botões de estado não mudarem)."""
    from ..models import TransacaoVinti4
    tipo = params.get('tipo')
    if tipo:
        if tipo not in PREFIXOS:
            raise FiltroInvalido('Tipo inválido.')
        qs = qs.filter(referencia__startswith=PREFIXOS[tipo])
    if de:
        qs = qs.filter(criada_em__date__gte=de)
    if ate:
        qs = qs.filter(criada_em__date__lte=ate)
    if de and ate and de > ate:
        raise FiltroInvalido('A data inicial é depois da final.')
    q = str(params.get('q') or '').strip()[:60]
    if q:
        cond = (Q(ref__icontains=q) | Q(referencia__icontains=q) | Q(descricao__icontains=q)
                | Q(utilizador__username__icontains=q) | Q(utilizador__email__icontains=q)
                | Q(utilizador__first_name__icontains=q) | Q(utilizador__last_name__icontains=q) | Q(pan__icontains=q))
        if admin:
            cond |= Q(loja__nome__icontains=q)
        qs = qs.filter(cond)
    base = qs
    estado = params.get('estado')
    if estado:
        if estado not in dict(TransacaoVinti4.ESTADOS):
            raise FiltroInvalido('Estado inválido.')
        qs = qs.filter(estado=estado)
    rec = params.get('reconciliacao')
    if rec == 'falta':          # pagas cá que nenhum ficheiro VBVT confirmou ainda
        qs = qs.filter(estado='paga', reconciliada_em__isnull=True)
    elif rec == 'feita':
        qs = qs.filter(reconciliada_em__isnull=False)
    elif rec:
        raise FiltroInvalido('Filtro de reconciliação inválido.')
    return qs.order_by('-criada_em', '-id'), base


def contagens(base):
    """Botões de estado + os números do topo (sobre o período e a pesquisa, sem o filtro de estado)."""
    from ..models import TransacaoVinti4
    por_estado = dict(base.order_by().values_list('estado').annotate(n=Count('id')))
    pagas = base.filter(estado='paga')
    s = pagas.aggregate(n=Count('id'), valor=Sum('valor'), comissoes=Sum('comissao_sisp'))
    est = pagas.filter(estornada_em__isnull=False).aggregate(n=Count('id'), valor=Sum('valor'))
    valor, comissoes, estornado = (s['valor'] or Decimal('0')), (s['comissoes'] or Decimal('0')), (est['valor'] or Decimal('0'))
    return {
        'estados': [{'valor': k, 'nome': v, 'n': por_estado.get(k, 0)} for k, v in TransacaoVinti4.ESTADOS],
        'totais': {
            'pagas': s['n'], 'valor_pago': str(valor),
            'estornos': est['n'], 'valor_estornado': str(estornado),
            'comissoes_sisp': str(comissoes),
            # o que deve chegar ao banco: pago − estornado − comissões da SISP (só as que um VBVT já trouxe)
            'liquido': str(valor - estornado - comissoes),
            'por_reconciliar': pagas.filter(reconciliada_em__isnull=True).count(),
            'por_confirmar': por_estado.get('por_confirmar', 0),
        },
    }


def item(t, completo=False, destino_loja=None):
    """Uma transacção para o ecrã. destino_loja(tipo, id) → caminho no backoffice (na loja) em vez do do site."""
    from .servico import TIPOS as TIPOS_REF, destino, ler_referencia
    lido = ler_referencia(t.referencia)
    tipo = TIPOS_REF.get(lido[0], '') if lido else ''
    d = {'id': t.id, 'ref': t.ref, 'referencia': t.referencia, 'tipo': tipo, 'tipo_nome': TIPOS.get(tipo, ''),
         'loja': {'id': t.loja_id, 'nome': t.loja.nome} if t.loja_id else None,
         'pos_id': t.pos_id, 'pagador': (t.utilizador.get_full_name() or t.utilizador.username) if t.utilizador_id else '',
         'valor': str(t.valor), 'montante': t.montante, 'descricao': t.descricao,
         'estado': t.estado, 'estado_nome': t.get_estado_display(), 'transacao': t.transacao if t.tid else '',
         'pan': t.pan, 'erro_codigo': t.erro_codigo, 'erro': t.erro, 'mensagem': t.mensagem,
         'dcc': t.dcc, 'confirmada_por': t.confirmada_por, 'efeito': t.efeito, 'consultas': t.consultas,
         'criada_em': _quando(t.criada_em), 'terminada_em': _quando(t.terminada_em),
         'reconciliada_em': _quando(t.reconciliada_em), 'estornada_em': _quando(t.estornada_em),
         'comissao_sisp': str(t.comissao_sisp) if t.comissao_sisp is not None else '', 'tipo_cartao': t.tipo_cartao}
    if completo:          # o caminho no site pede uma consulta por linha: só na ficha
        d['destino'] = destino_loja(lido[0], lido[1]) if (destino_loja and lido) else destino(t.referencia)[1]
        d['respostas'] = t.respostas
    return d


def csv_linhas(qs, admin=False):
    cab = ['Data', 'merchantRef', 'Referência', 'Tipo'] + (['Loja'] if admin else []) + [
        'Cliente', 'Estado', 'Valor (CVE)', 'Cobrado (CVE)', 'Cartão', 'Nº da transação', 'Confirmada por',
        'Reconciliada (VBVT)', 'Comissão SISP (CVE)', 'Estornada', 'Mensagem']
    out = [cab]
    for t in qs.select_related('loja', 'utilizador')[:MAX_CSV]:
        d = item(t)
        out.append([d['criada_em'], d['ref'], d['referencia'], d['tipo_nome']] + (
            [d['loja']['nome'] if d['loja'] else 'Bendi'] if admin else []) + [
            d['pagador'], d['estado_nome'], d['valor'].replace('.', ','), d['montante'], d['pan'], d['transacao'],
            d['confirmada_por'], d['reconciliada_em'], d['comissao_sisp'].replace('.', ','), d['estornada_em'],
            d['mensagem'] or d['erro']])
    return out
