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
         'comissao_sisp': str(t.comissao_sisp) if t.comissao_sisp is not None else '', 'tipo_cartao': t.tipo_cartao,
         'valor_estornado': str(t.valor_estornado)}
    if completo:          # o caminho no site pede uma consulta por linha: só na ficha
        d['destino'] = destino_loja(lido[0], lido[1]) if (destino_loja and lido) else destino(t.referencia)[1]
        d['respostas'] = t.respostas
        d['reembolsos'] = reembolsos(t, lido, loja=destino_loja is not None) if lido else []
    return d


def reembolsos(t, lido, loja=False):
    """
    O dinheiro desta transacção que volta (ou vai voltar) ao cliente — para a ficha mostrar o pedido de reembolso e
    o estado dele, com o caminho para o tratar (Devoluções no backoffice da loja ou no admin):
    • encomenda: os pedidos de reembolso dela (o de um pagamento tardio/a dobrar é o desta transacção);
    • marcação: o reembolso guardado na própria marcação (cancelamento, preço mais baixo, pagamento tardio).
    Só de transacções pagas (as outras não cobraram nada).
    """
    if t.estado != 'paga':
        return []
    from ..utils.dinheiro import formatar
    tipo, oid = lido[0], lido[1]
    if tipo == 'enc':
        from ..utils.devolucoes import reembolsos_da_transacao
        qs = reembolsos_da_transacao(t, oid).order_by('id')
        return [{'id': r.id, 'titulo': f'Pedido de reembolso #{r.id} · {r.get_motivo_display()}',
                 'estado': r.estado, 'estado_nome': r.get_estado_display(),
                 'valor': formatar(r.valor_aprovado if r.valor_aprovado is not None else r.valor_pedido),
                 'referencia': r.referencia if r.metodo == 'manual' and r.referencia != 'dinheiro' else '', 'em': _quando(r.data_reembolso),
                 'como': r.get_devolvido_como_display() if r.devolvido_como else '',
                 'confirmado_sisp': _quando(r.confirmado_sisp_em),
                 'link': f'/loja/{r.loja_id}/backoffice/devolucoes/{r.id}' if loja else f'/admin/devolucoes/{r.id}'}
                for r in qs]
    if tipo == 'mar':
        from ..servicos.marcacoes import por_reembolsar
        from ..servicos.models import Marcacao
        m = Marcacao.objects.filter(pk=oid).first()
        if not m or not m.reembolso_devido:
            return []
        falta = por_reembolsar(m)
        devolvido = m.valor_reembolsado >= m.reembolso_devido
        estado = 'reembolsado' if devolvido else 'por_reembolsar' if falta else 'pedido'
        nomes = {'reembolsado': 'Devolvido', 'por_reembolsar': 'Estorno por fazer' if m.pagamento_fornecedor == 'vinti4'
                 else 'Reembolso por concluir', 'pedido': 'A devolver'}
        return [{'id': m.id, 'titulo': f'Reembolso da marcação #{m.id}', 'estado': estado, 'estado_nome': nomes[estado],
                 'valor': formatar(m.reembolso_devido), 'referencia': '', 'em': _quando(m.reembolsado_em) if devolvido else '',
                 'como': '', 'confirmado_sisp': '',
                 'link': f'/loja/{m.loja_id}/backoffice/servicos' if loja else '/admin/devolucoes?grupo=por_concluir'}]
    return []


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
