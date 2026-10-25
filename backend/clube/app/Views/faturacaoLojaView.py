"""
Faturação no backoffice da loja (permissão gerir_faturacao: dono, gestor, contabilista) — a ficha do admin, só
desta loja: as vendas das três origens (loja online, marcações, contas do POS vendidas em nome da loja) com o
comprovativo do Bende (só o que foi pago no Bende) e a fatura que a loja emitiu no e-Fatura.

  GET  /app/loja/<id>/faturacao/resumo/?de=&ate=              dados fiscais + totais por origem no período
                                                               (+ por faturar de sempre)
  GET  /app/loja/<id>/faturacao/vendas/?origem=loja|marcacoes|pos&de&ate&estado&q&min&max&limit&offset
  GET  /app/loja/<id>/faturacao/vendas.csv?origem=&de=&ate=&estado=&q=&min=&max=   o que a lista mostra, em CSV
  GET  /app/loja/<id>/faturacao/exportar/?de=&ate=            ZIP do arquivo fiscal (CSVs + comprovativos + faturas)
  GET  /app/loja/<id>/faturacao/pesquisa/?q=&limit=&offset=   qualquer documento desta loja (E-/M-/V-/S-/C-, nº de
                                                               fatura em vigor ou anulada, cliente, NIF do cliente)
  GET  /app/loja/<id>/faturacao/historico/?ref=               as faturas registadas num documento (em vigor e anuladas)
  POST/DELETE /app/loja/<id>/faturacao/contas/<conta_id>/fatura/   fatura de uma conta do POS vendida em nome da loja
As faturas das encomendas e das marcações registam-se nos endpoints de sempre (também com gerir_faturacao).
"""
from datetime import date

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import HistoricoFatura, Loja, UtilizadorLoja
from ..pos.models import ContaMesa
from ..utils import fiscal
from ..utils import faturas_vendas as fv
from . import faturacaoView as fat

# na pesquisa da loja não entram outras lojas/POS (só os documentos)
TIPOS_PESQUISA = ('venda', 'anulada', 'mensalidade', 'comissoes')


def _acesso(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    membro = UtilizadorLoja.objects.filter(loja=loja, utilizador=request.user.utilizador, ativo=True).first()
    if not membro or not membro.pode('gerir_faturacao'):
        return None, Response({'detail': 'Sem permissão: gerir_faturacao'}, status=status.HTTP_403_FORBIDDEN)
    return loja, None


def _origem(request):
    origem = request.GET.get('origem') or 'loja'
    if origem not in fv.ORIGENS:
        return None, Response({'detail': 'Origem inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    return origem, None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumo(request, loja_id):
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    de, ate, erro = fat._datas(request)
    if erro:
        return erro
    origens = fat._origens(loja, 'loja', de, ate)
    totais = {k: sum(o[k] for o in origens) for k in ('vendas', 'faturadas', 'por_faturar', 'anuladas')}
    totais['valor'] = str(sum(fat.Decimal(o['valor']) for o in origens))
    # por faturar de sempre (o aviso no topo não depende do período escolhido)
    sempre = {o: fv.vendas(o, loja=loja).filter(fv.q_por_faturar(o)).count() for o in fv.ORIGENS}
    return Response({'loja': {'id': loja.id, 'nome': loja.nome, **fiscal.dados_fiscais_payload(loja)},
                     'origens': origens, 'totais': totais,
                     'por_faturar_sempre': {'total': sum(sempre.values()), 'origens': sempre}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendas(request, loja_id):
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    origem, erro = _origem(request)
    if erro:
        return erro
    return fat._lista_vendas(request, origem, loja=loja)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendas_csv(request, loja_id):
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    origem, erro = _origem(request)
    if erro:
        return erro
    qs, erro = fat.vendas_filtradas(request, origem, loja=loja)
    if erro:
        return erro
    if qs.count() > fat.MAX_VENDAS_ZIP * 5:
        return Response({'detail': 'Demasiadas vendas para um CSV — escolhe um período mais curto.'},
                        status=status.HTTP_400_BAD_REQUEST)
    de, ate, _ = fat._datas(request)
    qs = fv.com_relacoes(origem, qs).order_by(fv.CAMPO_DATA[origem], 'id')
    r = HttpResponse(fat._csv(fat._linhas_vendas(loja, qs, de, ate, request, origem)), content_type='text/csv; charset=utf-8')
    nome = {'loja': 'vendas', 'marcacoes': 'marcacoes', 'pos': 'vendas-pos'}[origem]
    r['Content-Disposition'] = f'attachment; filename="{nome}-{loja.id}-{de or "inicio"}-{ate or date.today()}.csv"'
    return r


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exportar(request, loja_id):
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    de, ate, erro = fat._datas(request)
    if erro:
        return erro
    return fat.arquivo_zip(request, loja, 'loja', de, ate)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pesquisa(request, loja_id):
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'count': 0, 'results': []})
    res = [r for r in fat.pesquisa_documentos(request, q, loja_id=loja.id) if r['tipo'] in TIPOS_PESQUISA]
    pagina, total = fat._paginar(request, res)
    return Response({'count': total, 'results': pagina})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historico(request, loja_id):
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    ref = (request.GET.get('ref') or '').strip().upper()
    qs = HistoricoFatura.objects.filter(Q(loja=loja) | Q(pos__loja_vinculada=loja), referencia=ref)
    return Response({'referencia': ref, 'itens': fiscal.historico_payload(qs, request)})


@api_view(['POST', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([IsAuthenticated])
def conta_fatura(request, loja_id, conta_id):
    """Conta do POS vendida em nome da loja (ContaMesa.loja). O POS também a pode faturar no Histórico dele."""
    loja, erro = _acesso(request, loja_id)
    if erro:
        return erro
    conta = get_object_or_404(ContaMesa, id=conta_id, loja=loja)
    _, _, erro = fv.pedido(request, conta, 'pos', request.user)
    if erro:
        return erro
    conta = fv.com_relacoes('pos', fv.base('pos').filter(pk=conta.pk)).get()
    return Response(fv.linha('pos', conta, request, fv.anuladas_por('pos', [conta.id]).get(conta.id, 0)))
