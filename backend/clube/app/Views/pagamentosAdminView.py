"""
Admin → Pagamentos (gerir_pagamentos): o estado do dinheiro, não a parte fiscal (essa é a Faturação).

Pagamentos dos clientes às lojas — encomendas e marcações pagas online, numa lista só:
  GET /app/admin/pagamentos/?origem=encomendas|marcacoes&estado=&metodo=&fornecedor=&loja_id=&de=&ate=&q=&limit=&offset=
  GET /app/admin/pagamentos/resumo/?loja_id=&de=&ate=      cartões: recebido, pendentes (transferências a expirar),
                                                           falhados, reembolsos por concluir
  GET /app/admin/pagamentos/abas/?q=&limit=&offset=&fixar= abas das lojas (contador = pagamentos pendentes)
  GET /app/admin/pagamentos.csv?…                          o que a lista mostra (todas as páginas)
Recebimentos da Bendi — mensalidades pagas e cobranças de comissões pagas (sem as ofertas/perdoadas):
  GET /app/admin/pagamentos/bende/?tipo=mensalidade|cobranca&de=&ate=&q=&limit=&offset=
  GET /app/admin/pagamentos/bende.csv?…

estado de uma linha: aprovado | pendente | falhado | reembolsado | reembolsado_parcial | cancelado (nunca pago:
encomenda cancelada / marcação cancelada ou expirada antes de pagar). Período (de/ate, AAAA-MM-DD): data do pedido
na lista; o cartão "Recebido" conta pela data em que o dinheiro entrou.
"""
import re
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import (Case, CharField, Count, DateTimeField, DecimalField, F, IntegerField, OuterRef, Q,
                              Subquery, Sum, Value, When)
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (CobrancaComissoes, Comissao, Encomenda, FaturaSubscricao, Loja, MetodoPagamento, Pagamento,
                      Reembolso)
from ..servicos.models import Marcacao
from ..utils import encomendas as enc_utils
from ..utils import fiscal
from .adminView import _exige_admin
from .faturacaoView import _csv, _datas, _paginar, _quando, abas_resposta

D = DecimalField(max_digits=12, decimal_places=2)
TXT = CharField()
ZERO = Value(Decimal('0'), output_field=D)

ESTADOS = {'aprovado': 'Pago', 'pendente': 'Pendente', 'falhado': 'Falhado', 'reembolsado': 'Reembolsado',
           'reembolsado_parcial': 'Reembolsado em parte', 'cancelado': 'Não pago'}
RECEBIDOS = ('aprovado', 'reembolsado', 'reembolsado_parcial')
METODOS = dict(MetodoPagamento.TIPOS) | {'online': 'Online (marcação)'}
COLUNAS = ('x_origem', 'x_id', 'x_ref', 'x_loja', 'x_loja_nome', 'x_cliente', 'x_valor', 'x_estado', 'x_metodo',
           'x_forn', 'x_referencia', 'x_criado', 'x_pago_em', 'x_reemb', 'x_comissao')
MAX_CSV = 5000


# ── as duas origens com as mesmas colunas ──────────────────────────

def _reembolsado_encomenda():
    """O que foi devolvido (ou é devido: por concluir) ao cliente — como utils/devolucoes.valor_reembolsado."""
    sub = (Reembolso.objects.filter(encomenda_id=OuterRef('encomenda_id'))
           .filter(Q(data_reembolso__isnull=False) | Q(estado='por_reembolsar')).exclude(metodo='abatido')
           .order_by().values('encomenda_id').annotate(t=Sum('valor_aprovado')).values('t')[:1])
    return Coalesce(Subquery(sub, output_field=D), ZERO, output_field=D)


def _qs_encomendas():
    comissao = Comissao.objects.filter(encomenda_id=OuterRef('encomenda_id')).values('valor_comissao')[:1]  # sem as anuladas
    return Pagamento.objects.annotate(
        x_origem=Value('encomenda', output_field=TXT), x_id=F('id'), x_ref=F('encomenda_id'),
        x_loja=F('encomenda__loja_id'), x_loja_nome=F('encomenda__loja__nome'),
        x_cliente=Coalesce(F('encomenda__comprador__user__username'), Value('', output_field=TXT), output_field=TXT),
        x_valor=F('valor'),
        x_estado=Case(When(status='pendente', encomenda__status='cancelado', then=Value('cancelado')),
                      default=F('status'), output_field=TXT),
        x_metodo=Coalesce(F('metodo__tipo'), Value('', output_field=TXT), output_field=TXT),
        x_forn=F('fornecedor'), x_referencia=F('referencia_transacao'),
        x_criado=F('data_criacao'), x_pago_em=F('data_pagamento'),
        x_reemb=_reembolsado_encomenda(),
        x_comissao=Coalesce(Subquery(comissao, output_field=D), ZERO, output_field=D),
    )


def _qs_marcacoes():
    """Só as de pagamento antecipado (online, pela Bendi); as pagas no local não passam por cá."""
    return Marcacao.objects.filter(pagamento='antecipado').annotate(
        x_origem=Value('marcacao', output_field=TXT), x_id=F('id'), x_ref=F('id'),
        x_loja=F('loja_id'), x_loja_nome=F('loja__nome'),
        x_cliente=Coalesce(F('cliente__user__username'), F('cliente_nome'), output_field=TXT),
        x_valor=Case(When(pago=True, then=F('valor_pago')), default=Coalesce(F('preco_final'), F('preco_indicado')),
                     output_field=D),
        x_estado=Case(
            When(pago=True, valor_pago__gt=0, valor_reembolsado__gte=F('valor_pago'), then=Value('reembolsado')),
            When(pago=True, valor_reembolsado__gt=0, then=Value('reembolsado_parcial')),
            When(pago=True, then=Value('aprovado')),
            When(estado__in=('cancelada', 'expirada', 'falta', 'concluida'), then=Value('cancelado')),
            default=Value('pendente'), output_field=TXT),
        x_metodo=Value('online', output_field=TXT),
        x_forn=F('pagamento_fornecedor'), x_referencia=F('pagamento_referencia'),
        x_criado=F('data_criacao'), x_pago_em=F('pago_em'),
        x_reemb=F('valor_reembolsado'), x_comissao=ZERO,
    )


def _filtrar(request, qs, origem, com_periodo=True, com_estado=True):
    g = request.GET
    loja = g.get('loja_id')
    if loja and loja.isdigit():
        qs = qs.filter(x_loja=int(loja))
    if com_estado and g.get('estado') in ESTADOS:
        qs = qs.filter(x_estado=g['estado'])
    if g.get('metodo'):
        qs = qs.filter(x_metodo=g['metodo'])
    if g.get('fornecedor'):           # 'nenhum' = sem fornecedor (dinheiro, transferência)
        qs = qs.filter(x_forn='' if g['fornecedor'] == 'nenhum' else g['fornecedor'])
    if com_periodo:
        de, ate, _ = _datas(request)
        if de:
            qs = qs.filter(x_criado__date__gte=de)
        if ate:
            qs = qs.filter(x_criado__date__lte=ate)
    q = (g.get('q') or '').strip()
    if q:
        m = re.fullmatch(r'([EeMm])-?\s*(\d+)', q)
        if m:
            qs = qs.filter(x_ref=int(m.group(2))) if m.group(1).upper() == ('E' if origem == 'encomenda' else 'M') else qs.none()
        elif q.isdigit():
            qs = qs.filter(Q(x_ref=int(q)) | Q(x_referencia__icontains=q))
        else:
            qs = qs.filter(Q(x_loja_nome__icontains=q) | Q(x_cliente__icontains=q) | Q(x_referencia__icontains=q))
    return qs


def _base(request, **kw):
    origem = request.GET.get('origem')
    partes = []
    if origem in (None, '', 'encomendas'):
        partes.append(_filtrar(request, _qs_encomendas(), 'encomenda', **kw))
    if origem in (None, '', 'marcacoes'):
        partes.append(_filtrar(request, _qs_marcacoes(), 'marcacao', **kw))
    return partes


def _uniao(partes):
    qs = [p.order_by().values(*COLUNAS) for p in partes]     # sem a ordenação do modelo: o Postgres não aceita ORDER BY dentro do UNION
    return qs[0].union(*qs[1:], all=True) if len(qs) > 1 else qs[0]


def _prazos(linhas):
    """Transferências por confirmar: até quando (72 h) — só as da página."""
    ids = [l['x_ref'] for l in linhas if l['x_origem'] == 'encomenda' and l['x_estado'] == 'pendente' and l['x_metodo'] == 'transferencia']
    if not ids:
        return {}
    encs = Encomenda.objects.filter(id__in=ids).select_related('pagamento__metodo')
    return {e.id: enc_utils.prazo_transferencia(e) for e in encs}


def _item(l, prazos):
    enc = l['x_origem'] == 'encomenda'
    valor, reemb, com = l['x_valor'] or Decimal('0'), l['x_reemb'] or Decimal('0'), l['x_comissao'] or Decimal('0')
    recebido = l['x_estado'] in RECEBIDOS
    prazo = prazos.get(l['x_ref']) if enc else None
    return {
        'origem': l['x_origem'], 'id': l['x_id'], 'referencia_doc': f"{'E' if enc else 'M'}-{l['x_ref']}", 'doc_id': l['x_ref'],
        'loja': {'id': l['x_loja'], 'nome': l['x_loja_nome']}, 'cliente': l['x_cliente'] or '',
        'valor': str(valor), 'estado': l['x_estado'], 'estado_label': ESTADOS.get(l['x_estado'], l['x_estado']),
        'metodo': l['x_metodo'], 'metodo_label': METODOS.get(l['x_metodo'], l['x_metodo'] or '—'),
        'fornecedor': l['x_forn'] or '', 'referencia': l['x_referencia'] or '',
        'criado_em': l['x_criado'], 'pago_em': l['x_pago_em'],
        'reembolsado': str(reemb), 'comissao': str(com) if enc else None,
        'receita_loja': str(valor - reemb - com) if recebido else None,
        'prazo': prazo, 'prazo_perto': bool(prazo and prazo - timezone.now() < timedelta(hours=enc_utils.LEMBRAR_TRANSFERENCIA_H)),
    }


def _exige(request):
    return _exige_admin(request, 'gerir_pagamentos')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista(request):
    erro = _exige(request)
    if erro:
        return erro
    _, _, erro = _datas(request)
    if erro:
        return erro
    partes = _base(request)
    total = sum(p.count() for p in partes)
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit = min(max(int(request.GET.get('limit', 20)), 1), 100)
    except ValueError:
        return Response({'detail': 'Paginação inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    linhas = list(_uniao(partes).order_by('-x_criado', '-x_ref')[offset:offset + limit])
    prazos = _prazos(linhas)
    return Response({'count': total, 'results': [_item(l, prazos) for l in linhas],
                     'fornecedores': sorted({f for f in Pagamento.objects.values_list('fornecedor', flat=True).distinct() if f} |
                                            {f for f in Marcacao.objects.values_list('pagamento_fornecedor', flat=True).distinct() if f})})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumo(request):
    erro = _exige(request)
    if erro:
        return erro
    de, ate, erro = _datas(request)
    if erro:
        return erro
    loja = request.GET.get('loja_id')
    loja = int(loja) if loja and loja.isdigit() else None

    def soma(partes):
        n, v = 0, Decimal('0')
        for p in partes:
            r = p.aggregate(n=Count('x_id'), v=Sum('x_valor'))
            n, v = n + r['n'], v + (r['v'] or 0)
        return {'n': n, 'valor': str(v)}

    def partes(**filtro):
        out = []
        for qs in (_qs_encomendas(), _qs_marcacoes()):
            if loja:
                qs = qs.filter(x_loja=loja)
            out.append(qs.filter(**filtro))
        return out

    periodo_pago = {**({'x_pago_em__date__gte': de} if de else {}), **({'x_pago_em__date__lte': ate} if ate else {})}
    periodo_criado = {**({'x_criado__date__gte': de} if de else {}), **({'x_criado__date__lte': ate} if ate else {})}
    recebido = soma(partes(x_estado__in=RECEBIDOS, **periodo_pago))

    # devolvido no período (encomendas: reembolsos feitos; marcações: devolvido)
    rq = Reembolso.objects.filter(data_reembolso__isnull=False).exclude(metodo='abatido')
    mq = Marcacao.objects.filter(pagamento='antecipado', valor_reembolsado__gt=0, reembolsado_em__isnull=False)
    if loja:
        rq, mq = rq.filter(loja_id=loja), mq.filter(loja_id=loja)
    if de:
        rq, mq = rq.filter(data_reembolso__date__gte=de), mq.filter(reembolsado_em__date__gte=de)
    if ate:
        rq, mq = rq.filter(data_reembolso__date__lte=ate), mq.filter(reembolsado_em__date__lte=ate)
    devolvido = (rq.aggregate(t=Sum('valor_aprovado'))['t'] or 0) + (mq.aggregate(t=Sum('valor_reembolsado'))['t'] or 0)

    pend = partes(x_estado='pendente')
    transf = [pend[0].filter(x_metodo='transferencia')]
    dinheiro = [pend[0].filter(x_metodo='dinheiro')]
    online = [pend[0].exclude(x_metodo__in=('transferencia', 'dinheiro')), pend[1]]
    perto = 0
    agora = timezone.now()
    for e in (Encomenda.objects.filter(pagamento__in=transf[0].values('id')).select_related('pagamento__metodo')):
        p = enc_utils.prazo_transferencia(e)
        if p and p - agora < timedelta(hours=enc_utils.LEMBRAR_TRANSFERENCIA_H):
            perto += 1

    rpc = Reembolso.objects.filter(estado='por_reembolsar')
    mpc = Marcacao.objects.filter(pago=True, reembolso_devido__gt=F('valor_reembolsado')).exclude(reembolso_erro='')
    if loja:
        rpc, mpc = rpc.filter(loja_id=loja), mpc.filter(loja_id=loja)
    return Response({
        'recebido': recebido, 'devolvido': str(devolvido),
        'pendentes': {**soma(pend), 'transferencias': {**soma(transf), 'perto_do_prazo': perto},
                      'dinheiro': soma(dinheiro), 'online': soma(online)},
        'falhados': soma(partes(x_estado='falhado', **periodo_criado)),
        'reembolsos_por_concluir': rpc.count() + mpc.count(),
        'incertos': rpc.filter(reembolso_incerto=True).count() + mpc.filter(reembolso_incerto=True).count(),
        'prazo_transferencia_h': enc_utils.PRAZO_TRANSFERENCIA_H,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def abas(request):
    """Abas das lojas: contador = pagamentos pendentes (encomendas + marcações); alerta = transferência perto do prazo."""
    erro = _exige(request)
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    pend = {}
    for qs in (_qs_encomendas(), _qs_marcacoes()):
        for loja_id, n in qs.filter(x_estado='pendente').order_by().values_list('x_loja').annotate(n=Count('x_id')):
            pend[loja_id] = pend.get(loja_id, 0) + n
    # lojas ainda por aprovar só aparecem se tiverem pagamentos pendentes (senão o contador não batia certo)
    lojas = Loja.objects.filter(~Q(estado='pendente') | Q(id__in=list(pend)))
    if q:
        lojas = lojas.filter(Q(nome__icontains=q) | Q(nif__icontains=q))
    itens = [{'tipo': 'loja', 'id': i, 'nome': nome, 'contador': pend.get(i, 0)} for i, nome in lojas.values_list('id', 'nome')]
    return abas_resposta(request, itens)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_csv(request):
    erro = _exige(request)
    if erro:
        return erro
    _, _, erro = _datas(request)
    if erro:
        return erro
    partes = _base(request)
    if sum(p.count() for p in partes) > MAX_CSV:
        return Response({'detail': f'Mais de {MAX_CSV} pagamentos — escolhe um período mais curto ou uma loja.'},
                        status=status.HTTP_400_BAD_REQUEST)
    linhas = list(_uniao(partes).order_by('-x_criado', '-x_ref'))
    prazos = _prazos(linhas)
    v = lambda x: '' if x is None else str(x).replace('.', ',')
    out = [['Documento', 'Loja', 'Cliente', 'Estado', 'Método', 'Fornecedor', 'Referência da transação', 'Pedido em',
            'Pago em', 'Valor (CVE)', 'Reembolsado (CVE)', 'Comissão (CVE)', 'Receita da loja (CVE)', 'Prazo da transferência']]
    for l in linhas:
        i = _item(l, prazos)
        out.append([i['referencia_doc'], i['loja']['nome'], i['cliente'], i['estado_label'], i['metodo_label'], i['fornecedor'],
                    i['referencia'], _quando(i['criado_em']), _quando(i['pago_em']), v(i['valor']), v(i['reembolsado']),
                    v(i['comissao']), v(i['receita_loja']), _quando(i['prazo'])])
    r = HttpResponse(_csv(out), content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="pagamentos-{timezone.localdate()}.csv"'
    return r


# ── Recebimentos da Bendi ──────────────────────────────────────────

def _bende_partes(request):
    g = request.GET
    de, ate, _ = _datas(request)
    q = (g.get('q') or '').strip()
    subs = (FaturaSubscricao.objects.filter(estado='paga', valor__gt=0).exclude(metodo='oferta')
            .annotate(x_tipo=Value('mensalidade', output_field=TXT), x_id=F('id'),
                      x_nome=Coalesce(F('loja__nome'), F('pos__nome'), output_field=TXT),
                      x_alvo=Case(When(loja__isnull=False, then=Value('loja')), default=Value('pos'), output_field=TXT),
                      x_alvo_id=Coalesce(F('loja_id'), F('pos_id'), output_field=IntegerField()),
                      x_valor=F('valor'), x_metodo=F('metodo'), x_pago_em=F('paga_em')))
    cobs = (CobrancaComissoes.objects.filter(estado='paga', valor__gt=0).exclude(metodo='oferta')
            .annotate(x_tipo=Value('cobranca', output_field=TXT), x_id=F('id'), x_nome=F('loja__nome'),
                      x_alvo=Value('loja', output_field=TXT), x_alvo_id=F('loja_id'),
                      x_valor=F('valor'), x_metodo=F('metodo'), x_pago_em=F('paga_em')))
    partes = []
    for tipo, qs in (('mensalidade', subs), ('cobranca', cobs)):
        if g.get('tipo') and g['tipo'] != tipo:
            continue
        if de:
            qs = qs.filter(x_pago_em__date__gte=de)
        if ate:
            qs = qs.filter(x_pago_em__date__lte=ate)
        if q:
            m = re.fullmatch(r'(S|CC)-?\s*(\d+)', q, re.I)
            if m:
                qs = qs.filter(x_id=int(m.group(2))) if (m.group(1).upper() == 'S') == (tipo == 'mensalidade') else qs.none()
            else:
                qs = qs.filter(x_nome__icontains=q)
        partes.append(qs)
    return partes


COLS_BENDE = ('x_tipo', 'x_id', 'x_nome', 'x_alvo', 'x_alvo_id', 'x_valor', 'x_metodo', 'x_pago_em')


def _bende_linhas(partes, fatia=None):
    qs = [p.order_by().values(*COLS_BENDE) for p in partes]
    if not qs:
        return []
    u = (qs[0].union(*qs[1:], all=True) if len(qs) > 1 else qs[0]).order_by('-x_pago_em', '-x_id')
    linhas = list(u[fatia] if fatia else u)
    subs = {f.id: f for f in FaturaSubscricao.objects.filter(id__in=[l['x_id'] for l in linhas if l['x_tipo'] == 'mensalidade'])
            .select_related('loja', 'pos', 'plano')}
    cobs = {c.id: c for c in CobrancaComissoes.objects.filter(id__in=[l['x_id'] for l in linhas if l['x_tipo'] == 'cobranca'])}
    metodos = dict(FaturaSubscricao.METODOS) | dict(CobrancaComissoes.METODOS)
    out = []
    for l in linhas:
        mens = l['x_tipo'] == 'mensalidade'
        obj = subs.get(l['x_id']) if mens else cobs.get(l['x_id'])
        out.append({
            'tipo': l['x_tipo'], 'id': l['x_id'], 'referencia': f"{'S' if mens else 'CC'}-{l['x_id']}",
            'nome': l['x_nome'] or '', 'alvo': l['x_alvo'], 'alvo_id': l['x_alvo_id'],
            'descricao': (obj.descricao if mens else f'Comissões até {obj.mes:%m/%Y}') if obj else '',
            'valor': str(l['x_valor']), 'metodo': l['x_metodo'], 'metodo_label': metodos.get(l['x_metodo'], l['x_metodo'] or '—'),
            'pago_em': l['x_pago_em'],
            'fatura': fiscal.fatura_resumo(obj) if mens and obj else None,
        })
    return out


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bende(request):
    erro = _exige(request)
    if erro:
        return erro
    _, _, erro = _datas(request)
    if erro:
        return erro
    partes = _bende_partes(request)
    tot = {'mensalidade': [0, Decimal('0')], 'cobranca': [0, Decimal('0')]}
    for p in partes:
        for tipo, n, v in p.order_by().values_list('x_tipo').annotate(n=Count('x_id'), v=Sum('x_valor')):
            tot[tipo][0] += n
            tot[tipo][1] += v or 0
    total = tot['mensalidade'][0] + tot['cobranca'][0]
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit = min(max(int(request.GET.get('limit', 20)), 1), 100)
    except ValueError:
        return Response({'detail': 'Paginação inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'count': total, 'results': _bende_linhas(partes, slice(offset, offset + limit)),
                     'totais': {'valor': str(tot['mensalidade'][1] + tot['cobranca'][1]),
                                'mensalidades': {'n': tot['mensalidade'][0], 'valor': str(tot['mensalidade'][1])},
                                'cobrancas': {'n': tot['cobranca'][0], 'valor': str(tot['cobranca'][1])}}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bende_csv(request):
    erro = _exige(request)
    if erro:
        return erro
    _, _, erro = _datas(request)
    if erro:
        return erro
    linhas = _bende_linhas(_bende_partes(request))
    if len(linhas) > MAX_CSV:
        return Response({'detail': f'Mais de {MAX_CSV} recebimentos — escolhe um período mais curto.'},
                        status=status.HTTP_400_BAD_REQUEST)
    out = [['Documento', 'Tipo', 'Loja/POS', 'Descrição', 'Pago em', 'Método', 'Valor (CVE)', 'Fatura da Bendi nº']]
    for i in linhas:
        out.append([i['referencia'], 'Mensalidade' if i['tipo'] == 'mensalidade' else 'Cobrança de comissões', i['nome'],
                    i['descricao'], _quando(i['pago_em']), i['metodo_label'], i['valor'].replace('.', ','),
                    (i['fatura'] or {}).get('numero', '')])
    r = HttpResponse(_csv(out), content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="recebimentos-bende-{timezone.localdate()}.csv"'
    return r


# ── Cartão (vinti4): cada ida à página da SISP, com o que a SISP respondeu (pagamentos/cartao_listas.py) ──
#   GET /app/admin/pagamentos/vinti4/?estado=&reconciliacao=&tipo=&credenciais=bendi|lojas&loja_id=&de=&ate=&q=&limit=&offset=
#   GET /app/admin/pagamentos/vinti4/csv/   (os mesmos filtros)
#   GET /app/admin/pagamentos/vinti4/<id>/      (com as respostas guardadas)

def _v4_item(t, completo=False):
    from ..pagamentos import cartao_listas
    return cartao_listas.item(t, completo=completo)


def _v4_filtrado(request):
    """→ (qs, base, erro)"""
    from ..models import TransacaoVinti4
    from ..pagamentos import cartao_listas
    de, ate, erro = _datas(request)
    if erro:
        return None, None, erro
    qs = TransacaoVinti4.objects.select_related('loja', 'utilizador')
    cred = request.GET.get('credenciais')
    if cred == 'bendi':
        qs = qs.filter(loja__isnull=True)
    elif cred == 'lojas':
        qs = qs.filter(loja__isnull=False)
    loja_id = request.GET.get('loja_id')
    if loja_id:
        if not str(loja_id).isdigit():
            return None, None, Response({'detail': 'Loja inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(loja_id=int(loja_id))
    try:
        qs, base = cartao_listas.filtrar(qs, request.GET, de, ate, admin=True)
    except cartao_listas.FiltroInvalido as e:
        return None, None, Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return qs, base, None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vinti4_lista(request):
    from ..pagamentos import cartao_listas
    erro = _exige(request)
    if erro:
        return erro
    qs, base, erro = _v4_filtrado(request)
    if erro:
        return erro
    from ..models import TransacaoVinti4
    pagina, total = _paginar(request, qs)
    lojas = (TransacaoVinti4.objects.filter(loja__isnull=False).order_by('loja__nome')
             .values_list('loja_id', 'loja__nome').distinct())        # para o filtro "Loja"
    from ..pagamentos import vinti4
    return Response({'count': total, 'results': [_v4_item(t) for t in pagina], **cartao_listas.contagens(base),
                     'lojas': [{'id': i, 'nome': n} for i, n in lojas],
                     'ambiente': vinti4.ambiente(), 'ligado': vinti4.em_uso()})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vinti4_csv(request):
    from ..pagamentos import cartao_listas
    erro = _exige(request)
    if erro:
        return erro
    qs, _, erro = _v4_filtrado(request)
    if erro:
        return erro
    if qs.count() > cartao_listas.MAX_CSV:
        return Response({'detail': f'Mais de {cartao_listas.MAX_CSV} transações — escolhe um período mais curto.'},
                        status=status.HTTP_400_BAD_REQUEST)
    r = HttpResponse(_csv(cartao_listas.csv_linhas(qs, admin=True)), content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="cartao-vinti4-{timezone.localdate()}.csv"'
    return r


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vinti4_detalhe(request, tx_id):
    from django.shortcuts import get_object_or_404
    from ..models import TransacaoVinti4
    erro = _exige(request)
    if erro:
        return erro
    t = get_object_or_404(TransacaoVinti4.objects.select_related('loja', 'utilizador'), id=tx_id)
    return Response(_v4_item(t, completo=True))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vinti4_consultar(request, tx_id):
    """POST /app/admin/pagamentos/vinti4/<id>/consultar/ — pergunta já à API de estado da SISP (Plan Test 39–41)."""
    from django.shortcuts import get_object_or_404
    from ..models import TransacaoVinti4
    from ..pagamentos import ErroPagamento
    from ..pagamentos import vinti4
    erro = _exige(request)
    if erro:
        return erro
    get_object_or_404(TransacaoVinti4, id=tx_id)
    try:
        tx, resultado, corpo = vinti4.consultar_agora(tx_id)
    except ErroPagamento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    tx = TransacaoVinti4.objects.select_related('loja', 'utilizador').get(id=tx.id)
    return Response({'resultado': resultado, 'resposta': corpo, 'transacao': _v4_item(tx, completo=True)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vinti4_resolver(request, tx_id):
    """POST /app/admin/pagamentos/vinti4/<id>/resolver/ {resultado: paga|nao_paga, nota} — fecha à mão um pagamento
    sem resposta da SISP, depois de ver no Portal do Comerciante (quando a API de estado não responde)."""
    from django.shortcuts import get_object_or_404
    from ..models import TransacaoVinti4
    from ..pagamentos import ErroPagamento
    from ..pagamentos import vinti4
    erro = _exige(request)
    if erro:
        return erro
    get_object_or_404(TransacaoVinti4, id=tx_id)
    try:
        tx = vinti4.resolver_a_mao(tx_id, request.data.get('resultado'), request.data.get('nota'), request.user)
    except ErroPagamento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    tx = TransacaoVinti4.objects.select_related('loja', 'utilizador').get(id=tx.id)
    return Response({'transacao': _v4_item(tx, completo=True)})


# ── ficheiros de reconciliação VBVT (pagamentos/vbvt.py) ──

def _vbvt_item(f, completo=False):
    from ..pagamentos import vbvt
    d = {'id': f.id, 'nome': f.nome, 'merchant_id': f.merchant_id, 'dono': f.loja.nome if f.loja_id else 'Bendi',
         'data': f.data.isoformat() if f.data else '', 'sequencia': f.sequencia,
         'data_anterior': f.data_anterior.isoformat() if f.data_anterior else '', 'sequencia_anterior': f.sequencia_anterior,
         'estado': f.estado, 'estado_nome': f.get_estado_display(), 'forcado': f.forcado,
         'n_erros': len(f.erros), 'n_avisos': len(f.avisos), 'resumo': f.resumo,
         'carregado_por': f.carregado_por.username if f.carregado_por_id else '', 'carregado_em': _quando(f.carregado_em)}
    if completo:
        d.update(erros=f.erros, avisos=f.avisos, linhas=f.linhas, relatorio=vbvt.relatorio(f),
                 resultados=vbvt.RESULTADOS, problemas=list(vbvt.PROBLEMAS))
    return d


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vbvt(request):
    """GET  /app/admin/pagamentos/vbvt/  → ficheiros carregados (mais recentes primeiro)
       POST /app/admin/pagamentos/vbvt/  multipart { ficheiro, forcar? } → processa (aplicado ou rejeitado)"""
    from ..models import FicheiroVBVT
    from ..pagamentos import vbvt as leitor
    erro = _exige(request)
    if erro:
        return erro
    if request.method == 'GET':
        qs = FicheiroVBVT.objects.select_related('loja', 'carregado_por').order_by('-carregado_em')
        dono = request.GET.get('dono')                  # bendi | <loja_id>
        if dono == 'bendi':
            qs = qs.filter(loja__isnull=True)
        elif dono and str(dono).isdigit():
            from ..pagamentos.vbvt import mid_da_loja
            loja = Loja.objects.filter(id=int(dono)).first()
            qs = qs.filter(merchant_id=mid_da_loja(loja)) if loja and mid_da_loja(loja) else qs.none()
        estado = request.GET.get('estado')
        if estado in ('aplicado', 'rejeitado'):
            qs = qs.filter(estado=estado)
        pagina, total = _paginar(request, qs)
        return Response({'count': total, 'results': [_vbvt_item(f) for f in pagina],
                         'merchant_id_bendi': bool(settings.VINTI4_MERCHANT_ID.strip())})
    ficheiro = request.FILES.get('ficheiro')
    if not ficheiro:
        return Response({'detail': 'Escolhe o ficheiro VBVT descarregado do Portal do Comerciante.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if ficheiro.size > leitor.TAMANHO_MAX:
        return Response({'detail': 'O ficheiro é demasiado grande (máximo 5 MB).'}, status=status.HTTP_400_BAD_REQUEST)
    forcar = str(request.data.get('forcar') or '').lower() in ('1', 'true', 'sim')
    try:
        f = leitor.processar(ficheiro.read(), nome=ficheiro.name, utilizador=request.user, forcar=forcar)
    except leitor.ErroVBVT as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_vbvt_item(f, completo=True), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vbvt_detalhe(request, ficheiro_id):
    from django.shortcuts import get_object_or_404
    from ..models import FicheiroVBVT
    erro = _exige(request)
    if erro:
        return erro
    f = get_object_or_404(FicheiroVBVT.objects.select_related('loja', 'carregado_por'), id=ficheiro_id)
    return Response(_vbvt_item(f, completo=True))
