"""
Faturação no POS (dono e membros com pode_ver_relatorios — os mesmos do Histórico; também num POS suspenso).
O arquivo fiscal segue o NIF: as contas vendidas com o NIF de uma loja ligada são do arquivo dessa loja (ContaMesa.loja),
as outras do POS. Aqui aparecem todas as contas do POS, com o arquivo de cada uma; as de uma loja a que o POS já não
está ligado ficam só de leitura (faturam-se na Faturação da loja). O CSV é a lista; o ZIP é só o arquivo do POS.

  GET /api/pos/<id>/faturacao/resumo/?de=&ate=     dados fiscais + totais (todas, por arquivo) + por faturar de sempre
  GET /api/pos/<id>/faturacao/vendas/?arquivo=pos|loja-<id>&de&ate&estado&q&min&max&limit&offset
  GET /api/pos/<id>/faturacao/vendas.csv?…         o que a lista mostra, em CSV
  GET /api/pos/<id>/faturacao/exportar/?de=&ate=   ZIP do arquivo fiscal do POS (CSVs + faturas + documentos do Bende)
  GET /api/pos/<id>/faturacao/pesquisa/?q=&limit=&offset=
  GET /api/pos/<id>/faturacao/historico/?ref=
As faturas registam-se em /api/pos/<id>/contas/<conta_id>/fatura/ (views.conta_fatura).
"""
from datetime import date

from django.db.models import Count, Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from app.models import HistoricoFatura
from app.utils import fiscal
from app.utils import faturas_vendas as fv
from app.Views import faturacaoView as fat
from .permissions import IsPOSAuthenticated, POSAuthentication
from .views import _resolve_pos_request, _sem_permissao

TIPOS_PESQUISA = ('venda', 'anulada', 'mensalidade')


def _acesso(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id, permitir_suspenso=True)
    return pos, _sem_permissao(membro, 'pode_ver_relatorios', 'Sem permissão para ver a faturação.')


def _totais(qs, pos):
    """Por faturar: só as que o POS fatura (as de uma loja a que já não está ligado são da Faturação dela)."""
    t = qs.aggregate(vendas=Count('id'), faturadas=Count('id', filter=Q(fatura_registada_em__isnull=False)),
                     por_faturar=Count('id', filter=fv.q_por_faturar('pos') & fv.q_pos_fatura(pos)))
    t['anuladas'] = HistoricoFatura.objects.filter(tipo='venda_pos', anulada_em__isnull=False,
                                                   conta_id__in=qs.values('id')).count()
    t['valor'] = str(fv.valor('pos', qs))
    return t


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def resumo(request, pos_id):
    pos, erro = _acesso(request, pos_id)
    if erro:
        return erro
    de, ate, erro = fat._datas(request)
    if erro:
        return erro
    qs = fv.vendas('pos', pos=pos, de=de, ate=ate, todas_do_pos=True)
    arquivos = [{'chave': 'pos', 'tipo': 'pos', 'nome': 'Este POS', 'so_leitura': False,
                 **_totais(qs.filter(loja__isnull=True), pos)}]
    # as lojas com cujo NIF o POS vendeu (todas as datas, para o separador não desaparecer com o período)
    lojas = (fv.vendas('pos', pos=pos, todas_do_pos=True).filter(loja__isnull=False)
             .values_list('loja_id', 'loja__nome').distinct().order_by('loja__nome'))
    for loja_id, nome in lojas:
        arquivos.append({'chave': f'loja-{loja_id}', 'tipo': 'loja', 'nome': nome, 'loja_id': loja_id,
                         'so_leitura': loja_id != pos.loja_vinculada_id, **_totais(qs.filter(loja_id=loja_id), pos)})
    # por faturar de sempre — só as que o POS pode faturar (as de uma loja antiga faturam-se lá)
    sempre = fv.vendas('pos', pos=pos, todas_do_pos=True).filter(fv.q_pos_fatura(pos), fv.q_por_faturar('pos')).count()
    loja = pos.loja_vinculada
    return Response({
        'pos': {'id': pos.id, 'nome': pos.nome, **fiscal.dados_fiscais_payload(pos),
                'loja': {'id': loja.id, 'nome': loja.nome} if loja else None,
                'loja_do_arquivo': pos.loja_do_arquivo_id},
        'totais': _totais(qs, pos), 'arquivos': arquivos, 'por_faturar_sempre': sempre,
    })


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def vendas(request, pos_id):
    pos, erro = _acesso(request, pos_id)
    if erro:
        return erro
    return fat._lista_vendas(request, 'pos', pos=pos, todas_do_pos=True)


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def vendas_csv(request, pos_id):
    pos, erro = _acesso(request, pos_id)
    if erro:
        return erro
    qs, erro = fat.vendas_filtradas(request, 'pos', pos=pos, todas_do_pos=True)
    if erro:
        return erro
    if qs.count() > fat.MAX_VENDAS_ZIP * 5:
        return Response({'detail': 'Demasiadas vendas para um CSV — escolhe um período mais curto.'},
                        status=status.HTTP_400_BAD_REQUEST)
    de, ate, _ = fat._datas(request)
    qs = fv.com_relacoes('pos', qs).order_by('fechada_em', 'id')
    r = HttpResponse(fat._csv(fat._linhas_vendas(pos, qs, de, ate, request, 'pos')), content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="vendas-pos-{pos.id}-{de or "inicio"}-{ate or date.today()}.csv"'
    return r


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def exportar(request, pos_id):
    pos, erro = _acesso(request, pos_id)
    if erro:
        return erro
    de, ate, erro = fat._datas(request)
    if erro:
        return erro
    return fat.arquivo_zip(request, pos, 'pos', de, ate)


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pesquisa(request, pos_id):
    pos, erro = _acesso(request, pos_id)
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'count': 0, 'results': []})
    res = [r for r in fat.pesquisa_documentos(request, q, pos_id=pos.id) if r['tipo'] in TIPOS_PESQUISA]
    pagina, total = fat._paginar(request, res)
    return Response({'count': total, 'results': pagina})


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def historico(request, pos_id):
    pos, erro = _acesso(request, pos_id)
    if erro:
        return erro
    ref = (request.GET.get('ref') or '').strip().upper()
    qs = HistoricoFatura.objects.filter(pos=pos, referencia=ref)
    return Response({'referencia': ref, 'itens': fiscal.historico_payload(qs, request)})
