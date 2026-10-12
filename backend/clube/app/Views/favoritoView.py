"""
Favoritos — produtos e lojas guardados pelo utilizador (o coração nos cards).

GET    /app/favoritos/ids/                    → { produtos: [ids], lojas: [ids] }  (marcar os corações)
GET    /app/favoritos/?tipo=produto|loja      → lista paginada para o perfil
POST   /app/favoritos/   { produto_id | loja_id }
DELETE /app/favoritos/produto/<id>/  ·  /app/favoritos/loja/<id>/

Só se guardam produtos e lojas visíveis ao público (não se descobrem lojas suspensas/pendentes
por aqui). Os que deixam de estar disponíveis continuam na lista, marcados como indisponíveis.
"""
from django.shortcuts import get_object_or_404
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Favorito, Produto, Loja

VIDEO = ('.mp4', '.webm', '.mov', '.mkv', '.avi', '.m4v')


def _url(request, ficheiro):
    try:
        return request.build_absolute_uri(ficheiro.url) if ficheiro else None
    except Exception:
        return None


def _e_video(ficheiro):
    return bool(ficheiro) and ficheiro.name.lower().endswith(VIDEO)


def _imagem_produto(request, p):
    if p.ficheiro_poster:
        return _url(request, p.ficheiro_poster)
    if p.ficheiro and not _e_video(p.ficheiro):
        return _url(request, p.ficheiro)
    return None


def _imagem_loja(request, loja):
    if loja.banner_poster:
        return _url(request, loja.banner_poster)
    if loja.banner and not _e_video(loja.banner):
        return _url(request, loja.banner)
    return None


def produto_visivel(p):
    return p.ativo and p.loja.ativa


def loja_visivel(loja):
    return loja.ativa


def _payload(request, f):
    if f.produto_id:
        p = f.produto
        return {
            'id': f.id, 'tipo': 'produto', 'criado_em': f.criado_em.isoformat(),
            'disponivel': produto_visivel(p),
            'produto': {'id': p.id, 'nome': p.nome, 'preco': str(p.preco), 'imagem': _imagem_produto(request, p)},
            'loja': {'id': p.loja_id, 'nome': p.loja.nome},
        }
    loja = f.loja
    return {
        'id': f.id, 'tipo': 'loja', 'criado_em': f.criado_em.isoformat(),
        'disponivel': loja_visivel(loja),
        'loja': {'id': loja.id, 'nome': loja.nome, 'categoria': loja.categoria,
                 'logo': _url(request, loja.logo), 'imagem': _imagem_loja(request, loja)},
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favoritos_ids(request):
    """Ids dos favoritos — um só pedido por página para marcar os corações."""
    qs = Favorito.objects.filter(utilizador=request.user.utilizador)
    return Response({
        'produtos': list(qs.filter(produto__isnull=False).values_list('produto_id', flat=True)),
        'lojas': list(qs.filter(loja__isnull=False).values_list('loja_id', flat=True)),
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def favoritos(request):
    u = request.user.utilizador

    if request.method == 'POST':
        if is_ratelimited(request=request, group='favoritos', key='user', rate='120/m', method='POST', increment=True):
            return Response({'detail': 'Demasiados pedidos. Aguarda um momento.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        produto_id, loja_id = request.data.get('produto_id'), request.data.get('loja_id')
        if bool(produto_id) == bool(loja_id):
            return Response({'detail': 'Indica um produto ou uma loja.'}, status=status.HTTP_400_BAD_REQUEST)
        if produto_id:
            p = Produto.objects.select_related('loja').filter(id=produto_id).first()
            # o mesmo 404 para "não existe" e "não é público" — não se distingue uma loja suspensa
            if not p or not produto_visivel(p):
                return Response({'detail': 'Produto não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
            f, criado = Favorito.objects.get_or_create(utilizador=u, produto=p)
        else:
            loja = Loja.objects.filter(id=loja_id).first()
            if not loja or not loja_visivel(loja):
                return Response({'detail': 'Loja não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
            f, criado = Favorito.objects.get_or_create(utilizador=u, loja=loja)
        return Response(_payload(request, f), status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)

    tipo = request.query_params.get('tipo')
    qs = Favorito.objects.filter(utilizador=u).select_related('produto__loja', 'loja')
    if tipo == 'produto':
        qs = qs.filter(produto__isnull=False)
    elif tipo == 'loja':
        qs = qs.filter(loja__isnull=False)
    try:
        offset = max(int(request.query_params.get('offset', 0)), 0)
        limit = min(max(int(request.query_params.get('limit', 20)), 1), 50)
    except ValueError:
        return Response({'detail': 'offset/limit inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
    total = qs.count()
    return Response({
        'count': total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results': [_payload(request, f) for f in qs[offset:offset + limit]],
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def favorito_remover(request, tipo, alvo_id):
    """Retirar dos favoritos (idempotente: retirar o que não está guardado também dá 204)."""
    if tipo not in ('produto', 'loja'):
        return Response({'detail': 'Tipo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    Favorito.objects.filter(utilizador=request.user.utilizador, **{f'{tipo}_id': alvo_id}).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
