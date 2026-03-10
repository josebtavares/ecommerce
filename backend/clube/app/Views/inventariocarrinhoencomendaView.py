from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    Inventario, Produto,
    Carrinho, ItemCarrinho,
    Encomenda, ItemEncomenda,
    Loja, UtilizadorLoja,
)
from ..Serializers.InventarioCarrinhoEncomendaSerializer import (
    InventarioSerializer,
    CarrinhoSerializer,
    ItemCarrinhoSerializer,
    EncomendaSerializer,
    EncomendaMiniSerializer,
    AtualizarStatusEncomendaSerializer,
)
from ..utils.pagination import paginar


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════

def _exige_permissao(request, loja, permissao):
    try:
        membro = UtilizadorLoja.objects.get(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        membro = None

    if not membro or not membro.pode(permissao):
        return None, Response(
            {'detail': f'Sem permissão: {permissao}'},
            status=status.HTTP_403_FORBIDDEN
        )
    return membro, None


# ══════════════════════════════════════════════════════════════
# INVENTÁRIO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventario_list(request, loja_id):
    """
    GET /app/loja/<loja_id>/inventario/?q=camisa&offset=0&limit=20
    Lista o inventário da loja com pesquisa e paginação.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_inventario')
    if erro:
        return erro

    qs = Inventario.objects.select_related('produto').filter(loja=loja)

    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(produto__nome__icontains=q) | Q(produto__sku__icontains=q)
        )

    # filtro por stock baixo
    if request.GET.get('stock_baixo') == 'true':
        qs = qs.filter(quantidade__lte=5)

    response, erro = paginar(request, qs, InventarioSerializer)
    if erro:
        return erro
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def inventario_criar_ou_atualizar(request, loja_id):
    """
    POST /app/loja/<loja_id>/inventario/
    Body: { produto_id, quantidade, preco_custo, preco_venda }
    Cria ou actualiza o inventário de um produto.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_inventario')
    if erro:
        return erro

    produto = get_object_or_404(Produto, id=request.data.get('produto_id'), loja=loja)

    inventario, criado = Inventario.objects.get_or_create(
        loja=loja, produto=produto,
        defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco}
    )

    serializer = InventarioSerializer(inventario, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def inventario_ajustar_stock(request, loja_id, produto_id):
    """
    PATCH /app/loja/<loja_id>/inventario/<produto_id>/ajustar/
    Body: { ajuste: 10 }  →  adiciona 10 ao stock
          { ajuste: -3 }  →  remove 3 do stock
    Útil para ajustes rápidos sem ter de enviar o total.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_inventario')
    if erro:
        return erro

    inventario = get_object_or_404(Inventario, loja=loja, produto_id=produto_id)

    try:
        ajuste = int(request.data.get('ajuste', 0))
    except ValueError:
        return Response({'detail': 'ajuste deve ser um número inteiro.'}, status=400)

    nova_qty = inventario.quantidade + ajuste
    if nova_qty < 0:
        return Response(
            {'detail': f'Stock insuficiente. Actual: {inventario.quantidade}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    inventario.quantidade = nova_qty
    inventario.save(update_fields=['quantidade', 'data_atualizacao'])

    return Response(InventarioSerializer(inventario).data)


# ══════════════════════════════════════════════════════════════
# CARRINHO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carrinho_get(request, loja_id):
    """
    GET /app/loja/<loja_id>/carrinho/
    Devolve o carrinho activo do utilizador para esta loja.
    Cria automaticamente se não existir.
    """
    loja       = get_object_or_404(Loja, id=loja_id, ativa=True)
    utilizador = request.user.utilizador

    carrinho, _ = Carrinho.objects.get_or_create(
        utilizador=utilizador, loja=loja
    )

    serializer = CarrinhoSerializer(carrinho, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def carrinho_adicionar(request, loja_id):
    """
    POST /app/loja/<loja_id>/carrinho/adicionar/
    Body: { produto_id, quantidade }
    Adiciona ou actualiza a quantidade de um item no carrinho.
    """
    loja       = get_object_or_404(Loja, id=loja_id, ativa=True)
    utilizador = request.user.utilizador

    # garante que o produto pertence à loja
    produto_id = request.data.get('produto_id')
    produto    = get_object_or_404(Produto, id=produto_id, loja=loja, ativo=True)

    carrinho, _ = Carrinho.objects.get_or_create(
        utilizador=utilizador, loja=loja
    )

    quantidade = int(request.data.get('quantidade', 1))

    item, criado = ItemCarrinho.objects.get_or_create(
        carrinho=carrinho, produto=produto,
        defaults={'quantidade': 0}
    )

    # valida stock
    try:
        stock = produto.inventario.quantidade
        if item.quantidade + quantidade > stock:
            return Response(
                {'detail': f'Stock insuficiente. Disponível: {stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Inventario.DoesNotExist:
        pass

    item.quantidade += quantidade
    item.save()

    return Response(
        CarrinhoSerializer(carrinho, context={'request': request}).data,
        status=status.HTTP_200_OK
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def carrinho_atualizar_item(request, loja_id, item_id):
    """
    PATCH /app/loja/<loja_id>/carrinho/item/<item_id>/
    Body: { quantidade: 3 }
    Actualiza a quantidade de um item. quantidade=0 remove o item.
    """
    utilizador = request.user.utilizador
    item       = get_object_or_404(
        ItemCarrinho,
        id=item_id,
        carrinho__utilizador=utilizador,
        carrinho__loja_id=loja_id
    )

    quantidade = int(request.data.get('quantidade', 1))

    if quantidade <= 0:
        item.delete()
        return Response({'detail': 'Item removido do carrinho.'})

    # valida stock
    try:
        stock = item.produto.inventario.quantidade
        if quantidade > stock:
            return Response(
                {'detail': f'Stock insuficiente. Disponível: {stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Inventario.DoesNotExist:
        pass

    item.quantidade = quantidade
    item.save()

    return Response(
        CarrinhoSerializer(item.carrinho, context={'request': request}).data
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def carrinho_limpar(request, loja_id):
    """DELETE /app/loja/<loja_id>/carrinho/limpar/"""
    utilizador = request.user.utilizador
    carrinho   = get_object_or_404(Carrinho, utilizador=utilizador, loja_id=loja_id)
    carrinho.itens.all().delete()
    return Response({'detail': 'Carrinho limpo.'})


# ══════════════════════════════════════════════════════════════
# ENCOMENDA
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def encomenda_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/encomenda/criar/
    Body: { tipo_entrega, morada_entrega?, notas? }
    Converte o carrinho activo numa encomenda.
    """
    loja       = get_object_or_404(Loja, id=loja_id, ativa=True)
    utilizador = request.user.utilizador

    # busca o carrinho activo
    carrinho = get_object_or_404(Carrinho, utilizador=utilizador, loja=loja)

    itens = carrinho.itens.select_related('produto__inventario').all()
    if not itens.exists():
        return Response(
            {'detail': 'O carrinho está vazio.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # valida e cria a encomenda
    serializer = EncomendaSerializer(
        data=request.data,
        context={'request': request, 'loja': loja}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # calcula o total
    valor_total = sum(
        item.produto.preco * item.quantidade for item in itens
    )

    encomenda = Encomenda.objects.create(
        comprador    = utilizador,
        loja         = loja,
        valor_total  = valor_total,
        tipo_entrega = serializer.validated_data.get('tipo_entrega', 'levantamento'),
        morada_entrega = serializer.validated_data.get('morada_entrega', ''),
        notas        = serializer.validated_data.get('notas', ''),
        status       = 'pendente',
    )

    # cria os itens da encomenda e desconta o stock
    for item in itens:
        ItemEncomenda.objects.create(
            encomenda  = encomenda,
            produto    = item.produto,
            quantidade = item.quantidade,
            preco      = item.produto.preco,  # snapshot do preço actual
        )
        # desconta stock se existir inventário
        try:
            inv = item.produto.inventario
            inv.quantidade -= item.quantidade
            inv.save(update_fields=['quantidade', 'data_atualizacao'])
        except Inventario.DoesNotExist:
            pass

    # limpa o carrinho após encomenda criada
    itens.delete()

    return Response(
        EncomendaSerializer(encomenda, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_list_comprador(request):
    """
    GET /app/encomenda/?status=pendente&offset=0&limit=10
    Encomendas do utilizador autenticado (comprador).
    """
    utilizador = request.user.utilizador
    qs = Encomenda.objects.filter(comprador=utilizador).order_by('-data_criacao')

    s = request.GET.get('status')
    if s:
        qs = qs.filter(status=s)

    response, erro = paginar(request, qs, EncomendaMiniSerializer)
    if erro:
        return erro
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_get(request, id):
    """
    GET /app/encomenda/<id>/
    Detalhe de uma encomenda — só o comprador ou staff da loja podem ver.
    """
    encomenda  = get_object_or_404(Encomenda, id=id)
    utilizador = request.user.utilizador

    eh_comprador = encomenda.comprador == utilizador
    eh_staff     = UtilizadorLoja.objects.filter(
        loja=encomenda.loja, utilizador=utilizador, ativo=True
    ).exists()

    if not eh_comprador and not eh_staff:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = EncomendaSerializer(encomenda, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_list_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/encomendas/?status=pendente&offset=0&limit=20
    Backoffice — lista encomendas da loja.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return erro

    qs = Encomenda.objects.filter(loja=loja).order_by('-data_criacao')

    s = request.GET.get('status')
    if s:
        qs = qs.filter(status=s)

    response, erro = paginar(request, qs, EncomendaMiniSerializer)
    if erro:
        return erro
    return response


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def encomenda_atualizar_status(request, loja_id, id):
    """
    PATCH /app/loja/<loja_id>/encomendas/<id>/status/
    Body: { status: 'preparando' }
    Backoffice — actualiza o status da encomenda com validação de transições.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return erro

    encomenda  = get_object_or_404(Encomenda, id=id, loja=loja)
    serializer = AtualizarStatusEncomendaSerializer(
        encomenda, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(
        EncomendaSerializer(encomenda, context={'request': request}).data
    )