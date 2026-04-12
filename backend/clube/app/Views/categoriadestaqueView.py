from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response

from ..models import CategoriaDestaque, Produto
from ..Serializers.CategoriaDestaqueSerializer import CategoriaDestaqueSerializer


# ══════════════════════════════════════════════════════════════
# PÚBLICO — home
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def categoria_destaque_list_publica(request):
    """
    GET /app/categorias-destaque/
    Devolve categorias activas ordenadas por `ordem`.
    Usado pelo home para construir os sliders.
    """
    categorias = CategoriaDestaque.objects.filter(ativo=True)
    serializer = CategoriaDestaqueSerializer(categorias, many=True)
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# ADMIN — gestão completa
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAdminUser])
def categoria_destaque_list_admin(request):
    categorias = CategoriaDestaque.objects.select_related('categoria').all()
    loja_id = request.GET.get('loja_id')
    if loja_id:
        categorias = categorias.filter(categoria__loja_id=loja_id)

    data = []
    for cat in categorias:
        data.append({
            'id':             cat.id,
            'nome':           cat.categoria.nome,
            'icone':          cat.icone or cat.categoria.icone or '📂',
            'ordem':          cat.ordem,
            'ativo':          cat.ativo,
            'loja_nome':      cat.categoria.loja.nome,
            'loja_id':        cat.categoria.loja.id,
            'categoria_id':   cat.categoria.id,
            'total_produtos': cat.categoria.produtos.filter(ativo=True).count(),
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def categoria_destaque_criar(request):
    """
    POST /app/admin/categorias-destaque/criar/
    Body: { nome, icone?, ordem? }
    """
    serializer = CategoriaDestaqueSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    cat = serializer.save()
    return Response(CategoriaDestaqueSerializer(cat).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def categoria_destaque_gerir(request, cat_id):
    """
    PATCH  /app/admin/categorias-destaque/<cat_id>/  → editar
    DELETE /app/admin/categorias-destaque/<cat_id>/  → eliminar definitivamente
    """
    cat = get_object_or_404(CategoriaDestaque, id=cat_id)

    if request.method == 'DELETE':
        cat.delete()
        return Response({'detail': 'Categoria eliminada.'})

    serializer = CategoriaDestaqueSerializer(cat, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def categoria_destaque_toggle(request, cat_id):
    """
    PATCH /app/admin/categorias-destaque/<cat_id>/toggle/
    Activa ou desactiva uma categoria.
    """
    cat = get_object_or_404(CategoriaDestaque, id=cat_id)
    cat.ativo = not cat.ativo
    cat.save(update_fields=['ativo'])
    return Response({'id': cat.id, 'ativo': cat.ativo})


# ══════════════════════════════════════════════════════════════
# PÚBLICO — sugestões para o backoffice da loja
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def categoria_sugestoes(request):
    """
    GET /app/produto/categorias/sugestoes/?loja_id=3
    Devolve categorias existentes na BD para sugestões ao criar produto.
    Combina: categorias destaque + categorias já usadas nesta loja.
    """
    loja_id = request.GET.get('loja_id')

    # categorias destaque (nome curado pelo admin)
    destaque = list(
        CategoriaDestaque.objects.filter(ativo=True).values_list('nome', flat=True)
    )

    # categorias já usadas na loja (se loja_id fornecido)
    da_loja = []
    if loja_id:
        da_loja = list(
            Produto.objects
            .filter(loja_id=loja_id, ativo=True)
            .exclude(categoria='').exclude(categoria__isnull=True)
            .values_list('categoria', flat=True)
            .distinct()
        )

    # merge sem duplicados, destaque primeiro
    todas = destaque.copy()
    for c in da_loja:
        if c not in todas:
            todas.append(c)

    return Response(todas)