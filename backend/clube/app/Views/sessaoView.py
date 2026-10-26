"""
Fim de sessão e bilhetes do WebSocket.

POST /api/token/logout/  — sair a sério: o refresh fica na lista negra (não renova mais) e o access
                           que vier no cabeçalho deixa de valer já, em vez de durar até expirar (30 min).
                           Sem autenticação obrigatória: quem sai com o access já expirado também tem
                           de conseguir invalidar o refresh.
POST /api/ws/bilhete/    — bilhete de uso único (60 s) para abrir o WebSocket. Antes o próprio JWT ia
                           no endereço (?token=...) e ficava gravado nos logs do servidor e do proxy.
"""
import secrets

from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from ..autenticacao import terminar_access

BILHETE_WS_SEGUNDOS = 60


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def terminar_sessao(request):
    refresh = request.data.get('refresh') if isinstance(request.data, dict) else None
    if refresh:
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            pass        # já expirado ou já na lista negra: a sessão já não renova
    cabecalho = request.META.get('HTTP_AUTHORIZATION', '')
    if cabecalho.startswith('Bearer '):
        try:
            terminar_access(AccessToken(cabecalho[7:]))
        except TokenError:
            pass        # expirado: já não vale
    return Response(status=status.HTTP_205_RESET_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bilhete_ws(request):
    bilhete = secrets.token_urlsafe(32)
    cache.set(f'ws_bilhete:{bilhete}', request.user.pk, BILHETE_WS_SEGUNDOS)
    return Response({'bilhete': bilhete})
