"""
POST /app/home/publicidade/eventos/   {eventos: [{chave, tipo: impressao|clique}]}  → 204 (público; sendBeacon)
GET  /app/admin/estatisticas/publicidade/?dias=7|30|90&anunciante=   → Admin → Estatísticas → Publicidade (ver_stats)
GET  /app/admin/estatisticas/publicidade/csv/?dias=&anunciante=       → CSV por anúncio e por dia (ver_stats)
Regras em utils/publicidade_stats.py.
"""
import json

from django.http import HttpResponse
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..utils import publicidade_stats as PS


class _JSONOuTexto(JSONParser):
    """o navigator.sendBeacon manda text/plain (assim não há pedido CORS de pré-verificação)."""
    media_type = 'text/plain'


def _dias(v):
    try:
        return min(max(int(v), 1), 365)
    except (TypeError, ValueError):
        return 30


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@parser_classes([JSONParser, _JSONOuTexto])
def eventos(request):
    if is_ratelimited(request=request, group='pub-eventos', key='ip', rate='60/m', method='POST', increment=True):
        return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)
    try:
        dados = request.data if isinstance(request.data, dict) else json.loads(request.data or '{}')
    except (ValueError, TypeError):
        dados = {}
    PS.registar(dados.get('eventos') if isinstance(dados, dict) else None,
                request.META.get('REMOTE_ADDR') or '', request.META.get('HTTP_USER_AGENT') or '')
    return Response(status=status.HTTP_204_NO_CONTENT)


def _ver_stats(request):
    from .adminView import _exige_admin
    return _exige_admin(request, 'ver_stats')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_estatisticas(request):
    erro = _ver_stats(request)
    if erro:
        return erro
    return Response(PS.estatisticas(_dias(request.GET.get('dias')), request.GET.get('anunciante') or '', request))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_estatisticas_csv(request):
    erro = _ver_stats(request)
    if erro:
        return erro
    texto, nome = PS.csv_periodo(_dias(request.GET.get('dias')), request.GET.get('anunciante') or '')
    r = HttpResponse(texto, content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="{nome}"'
    return r
