from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..models import Produto, TipoProduto, Loja, UtilizadorLoja
from ..Serializers.ProdutoSerializer import ProdutoSerializer, TipoProdutoSerializer
from ..utils.pagination import paginar


# ══════════════════════════════════════════════════════════════
# TIPO DE PRODUTO  (gerido pela plataforma)
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def tipo_produto_list(request):
    """
    GET /app/produto/tipos/
    Devolve tipos globais (loja=null) activos.
    Usado no home para os sliders dinâmicos por tipo.
    """
    tipos = TipoProduto.objects.filter(ativo=True, loja__isnull=True)
    serializer = TipoProdutoSerializer(tipos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tipo_produto_list_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/tipos/
    Lista tipos globais + tipos privados desta loja.
    Usado no backoffice para popular o select ao criar produto.
    """
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    from django.db.models import Q
    tipos = TipoProduto.objects.filter(ativo=True).filter(
        Q(loja__isnull=True) | Q(loja_id=loja_id)
    ).order_by('loja', 'nome')
 
    serializer = TipoProdutoSerializer(tipos, many=True)
    return Response(serializer.data)
 
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tipo_produto_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/tipos/criar/
    Body: { nome, descricao?, atributos_schema }
    Cria um tipo privado desta loja.
    """
    _, loja, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    # valida nome único para esta loja
    nome = (request.data.get('nome') or '').lower().strip()
    if TipoProduto.objects.filter(loja=loja, nome=nome).exists():
        return Response(
            {'nome': 'Já tens um tipo com este nome.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    serializer = TipoProdutoSerializer(data={**request.data, 'nome': nome})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    tipo = serializer.save(loja=loja)
    return Response(TipoProdutoSerializer(tipo).data, status=status.HTTP_201_CREATED)
 
 
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tipo_produto_gerir(request, loja_id, tipo_id):
    """
    PATCH  /app/loja/<loja_id>/tipos/<tipo_id>/  → editar
    DELETE /app/loja/<loja_id>/tipos/<tipo_id>/  → desactivar
    Só pode gerir tipos da sua loja — não pode tocar nos globais.
    """
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    # só tipos da loja (loja=X), nunca globais (loja=null)
    tipo = get_object_or_404(TipoProduto, id=tipo_id, loja_id=loja_id)
 
    if request.method == 'DELETE':
        tipo.ativo = False
        tipo.save(update_fields=['ativo'])
        return Response({'detail': 'Tipo removido.'})
 
    serializer = TipoProdutoSerializer(tipo, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    serializer.save()
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# PRODUTO — LEITURA PÚBLICA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def produto_list_pagination(request):
    """
    GET /app/produto/?q=nike&tipo=calcado&offset=0&limit=20
                      &preco_min=10&preco_max=200
                      &loja_id=3
                      &atributo_cor=preto        ← qualquer atributo JSON!
                      &atributo_tamanho=42
                      &atributo_marca=Nike
                      &atributo_ingredientes=frango
                      &atributo_volume=500ml

    Funciona para QUALQUER tipo de produto e QUALQUER atributo
    sem precisar de mudar o código — basta passar atributo_<chave>=<valor>.
    """
    qs = Produto.objects.select_related('loja', 'tipo').filter(ativo=True)

    # ── 1) filtro por loja ────────────────────────────────────
    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    # ── 2) filtro por tipo de produto ─────────────────────────
    tipo = request.GET.get('tipo')
    if tipo:
        qs = qs.filter(tipo__nome__iexact=tipo)

    # ── 3) pesquisa de texto livre (nome + descrição) ─────────
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(nome__icontains=q) | Q(descricao__icontains=q)
        )

    # ── 4) filtros de preço ───────────────────────────────────
    try:
        if 'preco_min' in request.GET:
            qs = qs.filter(preco__gte=float(request.GET['preco_min']))
        if 'preco_max' in request.GET:
            qs = qs.filter(preco__lte=float(request.GET['preco_max']))
    except ValueError:
        return Response(
            {'detail': 'preco_min / preco_max inválidos.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── 5) filtros dinâmicos por atributos JSON ───────────────
    #
    #  Qualquer parâmetro que comece por "atributo_" é tratado
    #  como filtro dentro do JSONField `atributos`.
    #
    #  Exemplos:
    #    atributo_cor=preto       → atributos__cor__iexact=preto
    #    atributo_tamanho=42      → atributos__tamanho__iexact=42
    #    atributo_marca=Nike      → atributos__marca__iexact=Nike
    #    atributo_volume=500ml    → atributos__volume__iexact=500ml
    #    atributo_alergenos=gluten→ atributos__alergenos__icontains=gluten
    #
    for param, valor in request.GET.items():
        if param.startswith('atributo_') and valor:
            chave = param[len('atributo_'):]   # remove o prefixo
            qs = qs.filter(**{f'atributos__{chave}__icontains': valor})

    # ── 6) destaque ───────────────────────────────────────────
    if request.GET.get('destaque') == 'true':
        qs = qs.filter(destaque=True)

    response, erro = paginar(request, qs, ProdutoSerializer, limit_default=20)
    if erro:
        return erro
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def produto_get(request, id):
    """
    GET /app/produto/<id>/
    """
    produto = get_object_or_404(Produto, id=id, ativo=True)
    serializer = ProdutoSerializer(produto, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# PRODUTO — BACKOFFICE DA LOJA (requer permissão)
# ══════════════════════════════════════════════════════════════

def _verificar_permissao_loja(request, loja_id, permissao):
    """Helper: verifica se o utilizador tem permissão na loja."""
    loja = get_object_or_404(Loja, id=loja_id)
    utilizador = request.user.utilizador
    if not UtilizadorLoja.verificar_permissao(loja, utilizador, permissao):
        return None, loja, Response(
            {'detail': f'Sem permissão: {permissao}'},
            status=status.HTTP_403_FORBIDDEN
        )
    return utilizador, loja, None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def produto_list_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/produtos/?q=camisa&tipo=roupa&atributo_cor=azul
    Lista produtos da loja para o backoffice (inclui inactivos).
    """
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro

    qs = Produto.objects.select_related('tipo').filter(loja_id=loja_id)

    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))

    tipo = request.GET.get('tipo')
    if tipo:
        qs = qs.filter(tipo__nome__iexact=tipo)

    # filtros dinâmicos por atributos JSON
    for param, valor in request.GET.items():
        if param.startswith('atributo_') and valor:
            chave = param[len('atributo_'):]
            qs = qs.filter(**{f'atributos__{chave}__icontains': valor})

    response, erro = paginar(request, qs, ProdutoSerializer, limit_default=20)
    if erro:
        return erro
    return response


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def produto_create(request, loja_id):
    """
    POST /app/loja/<loja_id>/produtos/criar/
    Body (multipart):
      nome, preco, descricao, sku, categoria,
      tipo_id, atributos (JSON string),
      destaque, ficheiro (opcional)
    """
    _, loja, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro

    import json
    # atributos vem como JSON string no FormData
    atributos_raw = request.data.get('atributos', '{}')
    try:
        atributos = json.loads(atributos_raw) if isinstance(atributos_raw, str) else atributos_raw
    except json.JSONDecodeError:
        return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    # valida atributos contra o schema do tipo
    tipo_id = request.data.get('tipo_id')
    if tipo_id:
        tipo = get_object_or_404(TipoProduto, id=tipo_id, ativo=True)
        em_falta = tipo.validar_atributos(atributos)
        if em_falta:
            return Response(
                {'atributos': f'Campos obrigatórios em falta: {em_falta}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    data = request.data.copy()
    data['loja']      = loja.id
    data['atributos'] = atributos

    serializer = ProdutoSerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    produto = serializer.save(
        loja=loja,
        atributos=atributos,
        ficheiro=request.FILES.get('ficheiro')
    )
 
    # cria inventário automaticamente com quantidade=0
    from ..models import Inventario
    Inventario.objects.get_or_create(
        loja=loja,
        produto=produto,
        defaults={
            'quantidade':   0,
            'preco_custo':  0,
            'preco_venda':  produto.preco,
        }
    )
 
    return Response(
        ProdutoSerializer(produto, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def produto_update(request, loja_id, id):
    """
    PUT/PATCH /app/loja/<loja_id>/produtos/<id>/editar/
    """
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro

    produto = get_object_or_404(Produto, id=id, loja_id=loja_id)

    import json
    data = request.data.copy()

    # atributos vem como JSON string no FormData
    if 'atributos' in data:
        try:
            data['atributos'] = json.loads(data['atributos']) if isinstance(data['atributos'], str) else data['atributos']
        except json.JSONDecodeError:
            return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ProdutoSerializer(produto, data=data, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    produto = serializer.save()

    # ficheiro novo (opcional)
    if 'ficheiro' in request.FILES:
        produto.ficheiro = request.FILES['ficheiro']
        produto.save(update_fields=['ficheiro'])

    return Response(
        ProdutoSerializer(produto, context={'request': request}).data,
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def produto_delete(request, loja_id, id):
    """
    DELETE /app/loja/<loja_id>/produtos/<id>/eliminar/
    Soft delete — marca como inactivo.
    """
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro

    produto = get_object_or_404(Produto, id=id, loja_id=loja_id)
    produto.ativo = False
    produto.save(update_fields=['ativo'])
    return Response({'detail': 'Produto desactivado.'}, status=status.HTTP_200_OK)