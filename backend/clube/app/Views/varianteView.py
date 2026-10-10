from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Produto, VarianteProduto, UtilizadorLoja
from ..utils.variantes import (
    grelha_variantes, guardar_grelha, atualizar_total_inventario, serializar_variante,
)


def _exige_inventario(request, loja_id):
    membro = UtilizadorLoja.objects.filter(
        loja_id=loja_id, utilizador=request.user.utilizador, ativo=True
    ).first()
    if not membro or not membro.pode('gerir_inventario'):
        return Response({'detail': 'Sem permissão: gerir_inventario'}, status=status.HTTP_403_FORBIDDEN)
    return None


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def produto_variantes(request, loja_id, id):
    """
    GET /app/loja/<loja_id>/produtos/<id>/variantes/
        → grelha: todas as combinações possíveis com quantidade/preço/sku

    PUT /app/loja/<loja_id>/produtos/<id>/variantes/
        Body: { variantes: [{ chave, quantidade, preco?, sku? }, ...] }
              → guarda a grelha e ACTIVA o stock por variação
        Body: { stock_por_variante: false }
              → volta ao stock total (o total fica com a soma actual)
    """
    erro = _exige_inventario(request, loja_id)
    if erro:
        return erro
    produto = get_object_or_404(Produto.objects.select_related('tipo'), id=id, loja_id=loja_id)

    if request.method == 'GET':
        return Response(grelha_variantes(produto))

    grelha, erro = guardar_grelha(produto, request.data)
    if erro:
        return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)
    return Response(grelha)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def variante_ajustar_stock(request, loja_id, id, variante_id):
    """
    PATCH /app/loja/<loja_id>/produtos/<id>/variantes/<variante_id>/ajustar/
    Body: { ajuste: +5 | -2 }
    """
    erro = _exige_inventario(request, loja_id)
    if erro:
        return erro
    v = get_object_or_404(
        VarianteProduto.objects.select_for_update().select_related('produto'),
        id=variante_id, produto_id=id, produto__loja_id=loja_id, ativo=True,
    )
    try:
        ajuste = int(request.data.get('ajuste', 0))
    except (TypeError, ValueError):
        return Response({'detail': 'ajuste deve ser um número inteiro.'}, status=status.HTTP_400_BAD_REQUEST)

    nova = v.quantidade + ajuste
    if nova < 0:
        return Response({'detail': f'Stock insuficiente. Actual: {v.quantidade}'}, status=status.HTTP_400_BAD_REQUEST)
    v.quantidade = nova
    v.save(update_fields=['quantidade', 'data_atualizacao'])
    atualizar_total_inventario(v.produto)
    return Response(serializar_variante(v))
