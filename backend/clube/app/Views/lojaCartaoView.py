"""
Backoffice da loja → Pagamentos: os pagamentos com cartão (vinti4) da loja, com o contrato dela com a SISP.
O mesmo que o Admin → Pagamentos → Cartão (pagamentos/cartao_listas.py), só com o que é da loja: nunca as
mensalidades e comissões da Bendi nem as transacções de outras lojas. Permissão ver_pagamentos_cartao (só o dono).

  GET  /app/loja/<id>/cartao/?estado=&reconciliacao=&tipo=&de=&ate=&q=&limit=&offset=   lista + contagens + totais
  GET  /app/loja/<id>/cartao/csv/                     (os mesmos filtros)
  GET  /app/loja/<id>/cartao/<tx>/                    ficha, com as respostas da SISP
  POST /app/loja/<id>/cartao/<tx>/consultar/          pergunta já à API de estado (com o Portal da loja)
  GET  /app/loja/<id>/cartao/vbvt/?estado=            ficheiros VBVT do Merchant ID do contrato da loja
  POST /app/loja/<id>/cartao/vbvt/  multipart { ficheiro, forcar? }   (só o ficheiro do contrato da loja)
  GET  /app/loja/<id>/cartao/vbvt/<f>/
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import FicheiroVBVT, Loja, TransacaoVinti4
from ..pagamentos import cartao_listas
from .faturacaoView import _csv, _datas, _paginar
from .lojaView import _exige_permissao
from .pagamentosAdminView import _vbvt_item as _vbvt_admin

PERMISSAO = 'ver_pagamentos_cartao'


def _loja(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, PERMISSAO)
    return loja, erro


def _destino(loja):
    def caminho(tipo, oid):
        if tipo == 'enc':
            return f'/loja/{loja.id}/backoffice/encomendas/{oid}'
        if tipo == 'mar':
            return f'/loja/{loja.id}/backoffice/servicos'
        return ''
    return caminho


def _filtrado(request, loja):
    de, ate, erro = _datas(request)
    if erro:
        return None, None, erro
    qs = TransacaoVinti4.objects.select_related('loja', 'utilizador').filter(loja=loja)
    try:
        qs, base = cartao_listas.filtrar(qs, request.GET, de, ate)
    except cartao_listas.FiltroInvalido as e:
        return None, None, Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return qs, base, None


def _contrato(loja):
    from ..pagamentos.vbvt import mid_da_loja
    from ..utils import vinti4
    a = vinti4.adesao(loja)
    return {'estado': a.estado if a else '', 'merchant_id': bool(mid_da_loja(loja)),
            'portal': bool(a and a.portal_id and a.portal_password_cifrada)}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista(request, loja_id):
    loja, erro = _loja(request, loja_id)
    if erro:
        return erro
    qs, base, erro = _filtrado(request, loja)
    if erro:
        return erro
    pagina, total = _paginar(request, qs)
    return Response({'count': total, 'results': [cartao_listas.item(t) for t in pagina],
                     **cartao_listas.contagens(base), 'contrato': _contrato(loja)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def csv(request, loja_id):
    loja, erro = _loja(request, loja_id)
    if erro:
        return erro
    qs, _, erro = _filtrado(request, loja)
    if erro:
        return erro
    if qs.count() > cartao_listas.MAX_CSV:
        return Response({'detail': f'Mais de {cartao_listas.MAX_CSV} transações — escolhe um período mais curto.'},
                        status=status.HTTP_400_BAD_REQUEST)
    r = HttpResponse(_csv(cartao_listas.csv_linhas(qs)), content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="pagamentos-cartao-{loja.slug or loja.id}-{timezone.localdate()}.csv"'
    return r


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalhe(request, loja_id, tx_id):
    loja, erro = _loja(request, loja_id)
    if erro:
        return erro
    t = get_object_or_404(TransacaoVinti4.objects.select_related('loja', 'utilizador'), id=tx_id, loja=loja)
    return Response(cartao_listas.item(t, completo=True, destino_loja=_destino(loja)))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def consultar(request, loja_id, tx_id):
    from ..pagamentos import ErroPagamento, vinti4
    loja, erro = _loja(request, loja_id)
    if erro:
        return erro
    get_object_or_404(TransacaoVinti4, id=tx_id, loja=loja)
    if is_ratelimited(request, group='vinti4_consulta', key='user', rate='30/h', increment=True):
        return Response({'detail': 'Demasiadas perguntas à SISP seguidas. Aguarda um momento.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)
    try:
        tx, resultado, corpo = vinti4.consultar_agora(tx_id)
    except ErroPagamento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    tx = TransacaoVinti4.objects.select_related('loja', 'utilizador').get(id=tx.id)
    return Response({'resultado': resultado, 'resposta': corpo,
                     'transacao': cartao_listas.item(tx, completo=True, destino_loja=_destino(loja))})


def _vbvt_item(f, completo=False):
    d = _vbvt_admin(f, completo)
    if f.carregado_por_id and f.carregado_por.is_staff:      # a loja não vê as contas do admin
        d['carregado_por'] = 'Equipa Bendi'
    return d


def _ficheiros(loja):
    from ..pagamentos.vbvt import mid_da_loja
    mid = mid_da_loja(loja)
    return FicheiroVBVT.objects.filter(merchant_id=mid) if mid else FicheiroVBVT.objects.none()


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vbvt(request, loja_id):
    from ..pagamentos import vbvt as leitor
    loja, erro = _loja(request, loja_id)
    if erro:
        return erro
    if request.method == 'GET':
        qs = _ficheiros(loja).select_related('loja', 'carregado_por').order_by('-carregado_em')
        estado = request.GET.get('estado')
        if estado in ('aplicado', 'rejeitado'):
            qs = qs.filter(estado=estado)
        pagina, total = _paginar(request, qs)
        return Response({'count': total, 'results': [_vbvt_item(f) for f in pagina], 'contrato': _contrato(loja)})
    if is_ratelimited(request, group='vinti4_vbvt', key='user', rate='30/h', increment=True):
        return Response({'detail': 'Demasiados ficheiros seguidos. Aguarda um momento.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)
    ficheiro = request.FILES.get('ficheiro')
    if not ficheiro:
        return Response({'detail': 'Escolhe o ficheiro VBVT descarregado do Portal do Comerciante.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if ficheiro.size > leitor.TAMANHO_MAX:
        return Response({'detail': 'O ficheiro é demasiado grande (máximo 5 MB).'}, status=status.HTTP_400_BAD_REQUEST)
    if not leitor.mid_da_loja(loja):
        return Response({'detail': 'A loja ainda não tem o Merchant ID do contrato vinti4 (Configurações).'},
                        status=status.HTTP_400_BAD_REQUEST)
    forcar = str(request.data.get('forcar') or '').lower() in ('1', 'true', 'sim')
    try:
        f = leitor.processar(ficheiro.read(), nome=ficheiro.name, utilizador=request.user, forcar=forcar, loja=loja)
    except leitor.ErroVBVT as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_vbvt_item(f, completo=True), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vbvt_detalhe(request, loja_id, ficheiro_id):
    loja, erro = _loja(request, loja_id)
    if erro:
        return erro
    f = get_object_or_404(_ficheiros(loja).select_related('loja', 'carregado_por'), id=ficheiro_id)
    return Response(_vbvt_item(f, completo=True))
