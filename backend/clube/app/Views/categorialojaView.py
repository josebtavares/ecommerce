from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response

from ..models import CategoriaLoja, CategoriaDestaque, Produto, Loja, UtilizadorLoja
from ..Serializers.CategoriaLojaSerializer import (
    CategoriaLojaSerializer,
    CategoriaLojaMiniSerializer,
    CategoriaDestaqueSerializer,
)


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════

def _verificar_membro(request, loja):
    try:
        return UtilizadorLoja.objects.get(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        return None


# ══════════════════════════════════════════════════════════════
# PÚBLICO — página da loja
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def categoria_loja_list_publica(request, loja_id):
    """
    GET /app/loja/<loja_id>/categorias/
    Devolve categorias activas da loja para a página pública.
    """
    loja = get_object_or_404(Loja, id=loja_id, ativa=True)
    cats = CategoriaLoja.objects.filter(loja=loja, ativo=True)
    return Response(CategoriaLojaSerializer(cats, many=True).data)


# ══════════════════════════════════════════════════════════════
# BACKOFFICE DA LOJA — gestão de categorias
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def categoria_loja_list_backoffice(request, loja_id):
    """
    GET /app/loja/<loja_id>/categorias/gerir/
    Lista todas as categorias (activas e inactivas) para o backoffice.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _verificar_membro(request, loja)
    if not membro or not membro.pode('gerir_produtos'):
        return Response({'detail': 'Sem permissão.'}, status=403)

    cats = CategoriaLoja.objects.filter(loja=loja)
    return Response(CategoriaLojaSerializer(cats, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def categoria_loja_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/categorias/criar/
    Body: { nome, icone?, ordem? }
    Se já existir com o mesmo nome (inactiva) → reactiva.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _verificar_membro(request, loja)
    if not membro or not membro.pode('gerir_produtos'):
        return Response({'detail': 'Sem permissão.'}, status=403)

    nome = (request.data.get('nome') or '').lower().strip()
    if not nome:
        return Response({'nome': 'O nome é obrigatório.'}, status=400)

    existente = CategoriaLoja.objects.filter(loja=loja, nome=nome).first()
    if existente:
        if existente.ativo:
            return Response({'id': existente.id, 'nome': existente.nome,
                             'icone': existente.icone, 'ativo': existente.ativo,
                             'ordem': existente.ordem, 'total_produtos': existente.produtos.filter(ativo=True).count()})
        else:
            existente.ativo = True
            existente.icone = request.data.get('icone', existente.icone)
            existente.save(update_fields=['ativo', 'icone'])
            return Response(CategoriaLojaSerializer(existente).data, status=200)

    serializer = CategoriaLojaSerializer(data={**request.data, 'nome': nome})
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    cat = serializer.save(loja=loja)
    return Response(CategoriaLojaSerializer(cat).data, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def categoria_loja_gerir(request, loja_id, cat_id):
    """
    PATCH  /app/loja/<loja_id>/categorias/<cat_id>/  → editar
    DELETE /app/loja/<loja_id>/categorias/<cat_id>/  → eliminar definitivamente
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _verificar_membro(request, loja)
    if not membro or not membro.pode('gerir_produtos'):
        return Response({'detail': 'Sem permissão.'}, status=403)

    cat = get_object_or_404(CategoriaLoja, id=cat_id, loja=loja)

    if request.method == 'DELETE':
        cat.delete()
        return Response({'detail': 'Categoria eliminada.'})

    serializer = CategoriaLojaSerializer(cat, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def categoria_loja_toggle(request, loja_id, cat_id):
    """
    PATCH /app/loja/<loja_id>/categorias/<cat_id>/toggle/
    Activa ou desactiva a categoria na página da loja.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _verificar_membro(request, loja)
    if not membro or not membro.pode('gerir_produtos'):
        return Response({'detail': 'Sem permissão.'}, status=403)

    cat = get_object_or_404(CategoriaLoja, id=cat_id, loja=loja)
    cat.ativo = not cat.ativo
    cat.save(update_fields=['ativo'])
    return Response({'id': cat.id, 'ativo': cat.ativo})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def categoria_loja_adicionar_produto(request, loja_id, cat_id):
    """
    POST /app/loja/<loja_id>/categorias/<cat_id>/produtos/
    Body: { produto_ids: [1, 2, 3] }
    Substitui completamente os produtos da categoria (set, não add).
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _verificar_membro(request, loja)
    if not membro or not membro.pode('gerir_produtos'):
        return Response({'detail': 'Sem permissão.'}, status=403)

    cat = get_object_or_404(CategoriaLoja, id=cat_id, loja=loja)
    ids = request.data.get('produto_ids', [])
    # usa set() em vez de add() — remove os que não estão na lista
    produtos = Produto.objects.filter(id__in=ids, loja=loja)
    cat.produtos.set(produtos)
    return Response({
        'detail': f'{produtos.count()} produto(s) na categoria.',
        'total': cat.produtos.filter(ativo=True).count()
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def categoria_loja_remover_produto(request, loja_id, cat_id, produto_id):
    """
    DELETE /app/loja/<loja_id>/categorias/<cat_id>/produtos/<produto_id>/
    Remove um produto da categoria.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro = _verificar_membro(request, loja)
    if not membro or not membro.pode('gerir_produtos'):
        return Response({'detail': 'Sem permissão.'}, status=403)

    cat    = get_object_or_404(CategoriaLoja, id=cat_id, loja=loja)
    produto = get_object_or_404(Produto, id=produto_id, loja=loja)
    cat.produtos.remove(produto)
    return Response({'detail': 'Produto removido da categoria.'})


# ══════════════════════════════════════════════════════════════
# ADMIN — categorias destaque (home)
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAdminUser])
def categoria_destaque_list_admin(request):
    """
    GET /app/admin/categorias-destaque/
    Lista destaques agrupados por loja.
    ?loja_id=X para filtrar.
    """
    qs = CategoriaDestaque.objects.select_related('categoria__loja').all()
    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(categoria__loja_id=loja_id)
    return Response(CategoriaDestaqueSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def categoria_destaque_lojas_admin(request):
    """
    GET /app/admin/categorias-destaque/lojas/
    Lista lojas que têm categorias, para as abas do admin.
    """
    lojas = Loja.objects.filter(
        categorias__isnull=False, ativa=True
    ).distinct().values('id', 'nome')
    return Response(list(lojas))


@api_view(['GET'])
@permission_classes([IsAdminUser])
def categoria_destaque_disponiveis(request):
    """
    GET /app/admin/categorias-destaque/disponiveis/?loja_id=X
    Lista categorias de uma loja que ainda não estão em destaque.
    """
    loja_id = request.GET.get('loja_id')
    if not loja_id:
        return Response([])

    ja_em_destaque = CategoriaDestaque.objects.values_list('categoria_id', flat=True)
    cats = CategoriaLoja.objects.filter(
        loja_id=loja_id, ativo=True
    ).exclude(id__in=ja_em_destaque)
    return Response(CategoriaLojaSerializer(cats, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def categoria_destaque_criar(request):
    """
    POST /app/admin/categorias-destaque/criar/
    Body: { categoria_loja_id, icone?, ordem? }
    """
    serializer = CategoriaDestaqueSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    destaque = serializer.save()
    return Response(CategoriaDestaqueSerializer(destaque).data, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def categoria_destaque_gerir(request, destaque_id):
    """
    PATCH  /app/admin/categorias-destaque/<destaque_id>/  → editar icone/ordem
    DELETE /app/admin/categorias-destaque/<destaque_id>/  → remover do home
    """
    destaque = get_object_or_404(CategoriaDestaque, id=destaque_id)

    if request.method == 'DELETE':
        destaque.delete()
        return Response({'detail': 'Removido do destaque.'})

    serializer = CategoriaDestaqueSerializer(destaque, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def categoria_destaque_toggle(request, destaque_id):
    """PATCH /app/admin/categorias-destaque/<destaque_id>/toggle/"""
    destaque = get_object_or_404(CategoriaDestaque, id=destaque_id)
    destaque.ativo = not destaque.ativo
    destaque.save(update_fields=['ativo'])
    return Response({'id': destaque.id, 'ativo': destaque.ativo})


# ══════════════════════════════════════════════════════════════
# PÚBLICO — home
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def categoria_destaque_list_publica(request):
    """
    GET /app/categorias-destaque/
    Devolve categorias em destaque para o home.
    """
    destaques = CategoriaDestaque.objects.filter(
        ativo=True
    ).select_related('categoria__loja')
    return Response([
        {
            'id':         d.id,
            'nome':       d.categoria.nome,
            'icone':      d.icone_display,
            'ordem':      d.ordem,
            'loja_id':    d.categoria.loja.id,
            'loja_nome':  d.categoria.loja.nome,
            'categoria_id': d.categoria.id,
        }
        for d in destaques
    ])