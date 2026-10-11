"""
Estado da otimização de vídeos de uma loja (backoffice) — ver app/utils/video.py.

GET  /app/loja/<loja_id>/videos/                 → vídeos ainda por otimizar ou com erro
POST /app/loja/<loja_id>/videos/reprocessar/     → { "modelo": "loja"|"produto", "id": <id> }
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, Produto, UtilizadorLoja
from ..utils import video

EM_CURSO = ('pendente', 'a_processar')


def _url(request, ficheiro):
    return request.build_absolute_uri(ficheiro.url) if ficheiro else None


def _item(request, modelo, obj, campo):
    return {
        'modelo':     modelo,
        'id':         obj.pk,
        'estado':     getattr(obj, f'{campo}_estado'),
        'url':        _url(request, getattr(obj, campo)),
        'poster_url': _url(request, getattr(obj, f'{campo}_poster')),
    }


def _pode(request, loja, permissao):
    return UtilizadorLoja.verificar_permissao(loja, request.user.utilizador, permissao)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def videos_estado(request, loja_id):
    """
    Lista os vídeos da loja em curso ou com erro. Com ?ids=1,2 devolve também esses
    produtos qualquer que seja o estado (para o backoffice saber quando ficaram prontos).
    """
    loja = get_object_or_404(Loja, id=loja_id)
    if not (_pode(request, loja, 'gerir_produtos') or _pode(request, loja, 'editar_loja')):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    ids = [int(i) for i in request.query_params.get('ids', '').split(',') if i.strip().isdigit()]
    produtos = Produto.objects.filter(loja=loja).filter(
        ficheiro_estado__in=EM_CURSO + ('erro',)
    ) | Produto.objects.filter(loja=loja, id__in=ids)

    return Response({
        'em_curso': (loja.banner_estado in EM_CURSO
                     or produtos.filter(ficheiro_estado__in=EM_CURSO).exists()),
        'banner':   _item(request, 'loja', loja, 'banner') if loja.banner_estado else None,
        'produtos': [_item(request, 'produto', p, 'ficheiro') for p in produtos.distinct()[:200]],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def videos_reprocessar(request, loja_id):
    loja   = get_object_or_404(Loja, id=loja_id)
    modelo = request.data.get('modelo')

    if modelo == 'loja':
        if not _pode(request, loja, 'editar_loja'):
            return Response({'detail': 'Sem permissão: editar_loja'}, status=status.HTTP_403_FORBIDDEN)
        obj, campo = loja, 'banner'
    elif modelo == 'produto':
        if not _pode(request, loja, 'gerir_produtos'):
            return Response({'detail': 'Sem permissão: gerir_produtos'}, status=status.HTTP_403_FORBIDDEN)
        obj, campo = get_object_or_404(Produto, id=request.data.get('id'), loja=loja), 'ficheiro'
    else:
        return Response({'detail': 'modelo inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    if getattr(obj, f'{campo}_estado') in EM_CURSO:
        return Response(_item(request, modelo, obj, campo))
    if not video.reprocessar(obj, campo):
        return Response({'detail': 'Este ficheiro não é um vídeo.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_item(request, modelo, obj, campo), status=status.HTTP_202_ACCEPTED)
