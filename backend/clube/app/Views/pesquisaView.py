"""
GET /app/pesquisa/?q=camisola                       → lista enquanto se escreve (produtos, lojas, serviços, categorias)
GET /app/pesquisa/?q=camisola&tipo=produto&offset=0&limit=24
       &preco_min=&preco_max=&categoria=&localizacao=&ordem=preco|-preco   → página de resultados
Pública, com cache de 60 s por pesquisa e limite por IP (utils/pesquisa.py).

POST /app/pesquisa/registo/  {id, sessao, q, origem, resultados, clique?}  → 204 (estatísticas, utils/pesquisa_stats.py)
GET  /app/admin/pesquisas/?dias=7|30|90                                     → Admin → Pesquisas (ver_stats)
"""
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..utils import pesquisa as P
from ..utils import pesquisa_stats
from ..utils.dinheiro import ler_valor

TIPOS = {'produtos': 'produto', 'produto': 'produto', 'lojas': 'loja', 'loja': 'loja',
         'servicos': 'servico', 'servico': 'servico'}


def _int(v, padrao, minimo, maximo):
    try:
        return min(max(int(v), minimo), maximo)
    except (TypeError, ValueError):
        return padrao


@api_view(['GET'])
@permission_classes([AllowAny])
def pesquisa(request):
    if is_ratelimited(request=request, group='pesquisa', key='ip', rate='120/m', method='GET', increment=True):
        return Response({'detail': 'Demasiadas pesquisas seguidas. Espera um pouco.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    g = request.GET
    tipo_raw = g.get('tipo') or ''
    tipo = TIPOS.get(tipo_raw)
    if tipo_raw and not tipo:
        return Response({'detail': 'tipo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    filtros = {}
    for campo in ('preco_min', 'preco_max'):
        if g.get(campo) not in (None, ''):
            valor, erro = ler_valor(g.get(campo), obrigatorio=False)
            if erro:
                return Response({'detail': f'{campo} inválido.'}, status=status.HTTP_400_BAD_REQUEST)
            filtros[campo] = valor
    for campo in ('categoria', 'localizacao'):
        if (g.get(campo) or '').strip():
            filtros[campo] = g.get(campo).strip()[:80]
    ordem = g.get('ordem') if g.get('ordem') in ('preco', '-preco') else ''
    if tipo:
        dados = P.pesquisar(g.get('q'), request, tipo=tipo, limite=_int(g.get('limit'), 24, 1, 48),
                            offset=_int(g.get('offset'), 0, 0, 10000), filtros=filtros, ordem=ordem)
    else:
        dados = P.pesquisar(g.get('q'), request, limite=_int(g.get('limit'), 5, 1, 8), filtros=filtros)
    return Response(dados)


@api_view(['POST'])
@permission_classes([AllowAny])
def pesquisa_registo(request):
    """O browser conta uma pesquisa (sem utilizador nem IP guardados). Responde sempre 204 — é só estatística."""
    if is_ratelimited(request=request, group='pesquisa-registo', key='ip', rate='60/m', method='POST', increment=True):
        return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)
    pesquisa_stats.registar(request.data)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pesquisas(request):
    from .adminView import _exige_admin
    erro = _exige_admin(request, 'ver_stats')
    if erro:
        return erro
    return Response(pesquisa_stats.estatisticas(_int(request.GET.get('dias'), 30, 1, 365)))
