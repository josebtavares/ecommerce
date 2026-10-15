from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..utils import home as H


@api_view(['GET'])
@permission_classes([AllowAny])
def home_publica(request):
    """GET /app/home/ — secções publicadas, já resolvidas (primeira página de cada slider)."""
    return Response(H.home(request))


@api_view(['GET'])
@permission_classes([AllowAny])
def home_seccao(request, seccao_id):
    """GET /app/home/seccao/<id>/?grupo=&offset=&limit= — páginas seguintes de um slider."""
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit = min(max(int(request.GET.get('limit', 10)), 1), 50)
    except ValueError:
        return Response({'detail': 'offset/limit inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
    s = H.seccao_publicada(seccao_id)
    pagina = H.pagina_seccao(s, request.GET.get('grupo') or None, offset, limit, request) if s else None
    if pagina is None:
        return Response({'detail': 'Secção não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(pagina)
