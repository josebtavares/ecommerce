from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Produto, VarianteProduto, UtilizadorLoja
from ..utils.variantes import (
    atributos_variante, combinacoes_produto, chave_de,
    sincronizar_variantes, atualizar_total_inventario, serializar_variante,
)


def _exige_inventario(request, loja_id):
    membro = UtilizadorLoja.objects.filter(
        loja_id=loja_id, utilizador=request.user.utilizador, ativo=True
    ).first()
    if not membro or not membro.pode('gerir_inventario'):
        return Response({'detail': 'Sem permissão: gerir_inventario'}, status=status.HTTP_403_FORBIDDEN)
    return None


def _grelha(produto):
    """
    Estado da grelha para o backoffice — uma linha por combinação possível,
    com os valores guardados (se existirem). Não escreve na BD.
    """
    existentes = {v.chave: v for v in produto.variantes.all()}
    linhas = []
    for combo in combinacoes_produto(produto):
        chave = chave_de(combo)
        v = existentes.get(chave)
        if v:
            linha = serializar_variante(v, produto)
            linha['combinacao'] = combo
        else:
            linha = {
                'id': None, 'chave': chave, 'combinacao': combo, 'quantidade': 0,
                'preco': None, 'preco_efetivo': str(produto.preco), 'sku': '', 'disponivel': False,
            }
        linhas.append(linha)

    total_inventario = getattr(getattr(produto, 'inventario', None), 'quantidade', 0)
    return {
        'produto_id':         produto.id,
        'produto_nome':       produto.nome,
        'preco_produto':      str(produto.preco),
        'stock_por_variante': produto.stock_por_variante,
        'atributos_variante': [n for n in atributos_variante(produto) if any(n in l['combinacao'] for l in linhas)],
        'variantes':          linhas,
        'total':              sum(l['quantidade'] for l in linhas) if produto.stock_por_variante else total_inventario,
        'stock_total_antigo': None if produto.stock_por_variante else total_inventario,
    }


def _preco(valor):
    if valor in (None, ''):
        return None, None
    try:
        p = Decimal(str(valor)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None, 'Preço inválido.'
    if p < 0:
        return None, 'O preço não pode ser negativo.'
    return p, None


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
        return Response(_grelha(produto))

    # ── desactivar ────────────────────────────────────────────
    if request.data.get('stock_por_variante') is False:
        produto.stock_por_variante = False
        produto.save(update_fields=['stock_por_variante'])
        return Response(_grelha(produto))

    # ── guardar grelha ────────────────────────────────────────
    combos = {chave_de(c): c for c in combinacoes_produto(produto)}
    if not combos:
        return Response(
            {'detail': 'Este produto não tem atributos com stock por variação. '
                       'Marca um atributo de escolha como "variante" no tipo do produto.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    entrada = request.data.get('variantes')
    if not isinstance(entrada, list):
        return Response({'detail': 'variantes deve ser uma lista.'}, status=status.HTTP_400_BAD_REQUEST)

    valores = {}
    for linha in entrada:
        if not isinstance(linha, dict):
            return Response({'detail': 'Linha inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        chave = linha.get('chave') or (chave_de(linha['combinacao']) if isinstance(linha.get('combinacao'), dict) else None)
        if chave not in combos:
            return Response({'detail': f'Combinação desconhecida: {chave}'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            qtd = int(linha.get('quantidade', 0))
        except (TypeError, ValueError):
            qtd = -1
        if qtd < 0:
            return Response({'detail': f'Quantidade inválida em {" · ".join(combos[chave].values())}.'},
                            status=status.HTTP_400_BAD_REQUEST)
        preco, erro_preco = _preco(linha.get('preco'))
        if erro_preco:
            return Response({'detail': f'{erro_preco} ({" · ".join(combos[chave].values())})'},
                            status=status.HTTP_400_BAD_REQUEST)
        valores[chave] = {'quantidade': qtd, 'preco': preco, 'sku': str(linha.get('sku') or '').strip()[:100]}

    produto.stock_por_variante = True
    produto.save(update_fields=['stock_por_variante'])
    for v in sincronizar_variantes(produto):
        if v.chave in valores:
            dados = valores[v.chave]
            v.quantidade, v.preco, v.sku = dados['quantidade'], dados['preco'], dados['sku']
            v.save(update_fields=['quantidade', 'preco', 'sku', 'data_atualizacao'])
    atualizar_total_inventario(produto)

    produto.refresh_from_db()
    return Response(_grelha(produto))


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
