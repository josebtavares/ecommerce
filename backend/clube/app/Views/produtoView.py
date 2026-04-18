from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
import json

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..models import Produto, TipoProduto, Loja, UtilizadorLoja,ProdutoImagem
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

    tipos = TipoProduto.objects.filter(
        Q(loja__isnull=True, ativo=True) |  # globais: só activos
        Q(loja_id=loja_id)                  # da loja: activos E inactivos
    ).order_by('loja', 'nome')

    return Response(TipoProdutoSerializer(tipos, many=True).data)
 
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tipo_produto_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/tipos/criar/
    Body: { nome, descricao?, atributos_schema }
 
    Se já existir um tipo com o mesmo nome (mesmo inactivo),
    reactiva-o em vez de devolver erro.
    """
    _, loja, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    nome = (request.data.get('nome') or '').lower().strip()
    if not nome:
        return Response({'nome': 'O nome é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
 
    # verifica se já existe (activo ou inactivo)
    existente = TipoProduto.objects.filter(loja=loja, nome=nome).first()
 
    if existente:
        if existente.ativo:
            # activo — não pode duplicar
            return Response(
                {'nome': f'Já tens um tipo activo com o nome "{nome}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # inactivo — reactiva e actualiza com os novos dados
            existente.ativo       = True
            existente.descricao   = request.data.get('descricao', existente.descricao)
            existente.atributos_schema = request.data.get('atributos_schema', existente.atributos_schema)
            existente.save(update_fields=['ativo', 'descricao', 'atributos_schema'])
            return Response(
                TipoProdutoSerializer(existente).data,
                status=status.HTTP_200_OK   # 200 porque reactivou, não criou
            )
 
    # não existe — cria normalmente
    serializer = TipoProdutoSerializer(data={**request.data, 'nome': nome})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    tipo = serializer.save(loja=loja)
    return Response(TipoProdutoSerializer(tipo).data, status=status.HTTP_201_CREATED)
 
 
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tipo_produto_gerir(request, loja_id, tipo_id):
    """
    PATCH  /app/loja/<loja_id>/tipos/<tipo_id>/         → editar
    DELETE /app/loja/<loja_id>/tipos/<tipo_id>/         → desactivar (soft delete)
    DELETE /app/loja/<loja_id>/tipos/<tipo_id>/?hard=1  → eliminar definitivamente
    """
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    tipo = get_object_or_404(TipoProduto, id=tipo_id, loja_id=loja_id)
 
    if request.method == 'DELETE':
        hard = request.GET.get('hard') == '1'
        if hard:
            # verifica se há produtos activos a usar este tipo
            produtos_ativos = tipo.produtos.filter(ativo=True).count()
            if produtos_ativos > 0:
                return Response(
                    {
                        'detail': f'Este tipo tem {produtos_ativos} produto(s) activo(s). '
                                  f'Desactiva ou remove os produtos primeiro.',
                        'produtos_ativos': produtos_ativos,
                    },
                    status=status.HTTP_409_CONFLICT
                )
            tipo.delete()
            return Response({'detail': 'Tipo eliminado definitivamente.'})
        else:
            # soft delete — mantém histórico
            tipo.ativo = False
            tipo.save(update_fields=['ativo'])
            return Response({'detail': 'Tipo desactivado.'})
 
    # PATCH — editar
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
def produto_categorias_plataforma(request):
    """
    GET /app/produto/categorias/
    Devolve categorias distintas de todos os produtos activos.
    Usado no home para sliders dinâmicos por categoria.
    Suporta ?min_produtos=3 para filtrar categorias com poucos produtos.
    """
    min_produtos = int(request.GET.get('min_produtos', 1))
 
    from django.db.models import Count
 
    categorias = (
        Produto.objects
        .filter(ativo=True)
        .exclude(categoria='')
        .exclude(categoria__isnull=True)
        .values('categoria')
        .annotate(total=Count('id'))
        .filter(total__gte=min_produtos)
        .order_by('-total')  # mais populares primeiro
    )
    # limita o número de categorias devolvidas (default 20, max 50)
    limit = min(int(request.GET.get('limit', 20)), 50)
    categorias = categorias[:limit]
 
    return Response([
        {'categoria': c['categoria'], 'total': c['total']}
        for c in categorias
    ])
    
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
        
    tipo = request.GET.get('tipo')
    if tipo:
        qs = qs.filter(tipo__nome__iexact=tipo)
 
    # ── filtro por categoria do produto ───────────────────────
    categoria_id = request.GET.get('categoria_id')
    if categoria_id:
        qs = qs.filter(categorias__id=categoria_id)
 
    categoria_nome = request.GET.get('categoria')
    if categoria_nome:
        qs = qs.filter(categorias__nome__iexact=categoria_nome)

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
    loja = get_object_or_404(Loja, id=loja_id)
    utilizador = request.user.utilizador
    if not UtilizadorLoja.verificar_permissao(loja, utilizador, permissao):
        return None, loja, Response({'detail': f'Sem permissão: {permissao}'}, status=status.HTTP_403_FORBIDDEN)
    return utilizador, loja, None
 
 
def _gerir_imagens(produto, request):
    """
    Processa imagens adicionais enviadas no multipart request:
      imagens_novas[0], imagens_novas[1], ...  → ficheiros a adicionar
      imagens_eliminar                         → JSON array de IDs a remover
      imagens_reordenar                        → JSON array [{id, ordem}]
    """
    # 1. Eliminar imagens marcadas
    ids_eliminar_raw = request.data.get('imagens_eliminar')
    if ids_eliminar_raw:
        try:
            ids = json.loads(ids_eliminar_raw) if isinstance(ids_eliminar_raw, str) else ids_eliminar_raw
            ProdutoImagem.objects.filter(produto=produto, id__in=ids).delete()
        except Exception:
            pass
 
    # 2. Adicionar novas imagens
    i = 0
    while f'imagens_novas[{i}]' in request.FILES:
        ficheiro = request.FILES[f'imagens_novas[{i}]']
        ordem    = int(request.data.get(f'imagens_ordem_nova[{i}]', i))
        legenda  = request.data.get(f'imagens_legenda[{i}]', '')
        ProdutoImagem.objects.create(produto=produto, ficheiro=ficheiro, ordem=ordem, legenda=legenda)
        i += 1
 
    # 3. Reordenar imagens existentes
    ordem_raw = request.data.get('imagens_reordenar')
    if ordem_raw:
        try:
            ordens = json.loads(ordem_raw) if isinstance(ordem_raw, str) else ordem_raw
            for item in ordens:
                ProdutoImagem.objects.filter(produto=produto, id=item['id']).update(ordem=item['ordem'])
        except Exception:
            pass


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
    _, loja, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    atributos_raw = request.data.get('atributos', '{}')
    try:
        atributos = json.loads(atributos_raw) if isinstance(atributos_raw, str) else atributos_raw
    except json.JSONDecodeError:
        return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)
 
    tipo_id = request.data.get('tipo_id')
    if tipo_id:
        tipo = get_object_or_404(TipoProduto, id=tipo_id, ativo=True)
        em_falta = tipo.validar_atributos(atributos)
        if em_falta:
            return Response({'atributos': f'Campos obrigatórios em falta: {em_falta}'}, status=status.HTTP_400_BAD_REQUEST)
 
    data = request.data.copy()
    data['loja']      = loja.id
    data['atributos'] = atributos
 
    serializer = ProdutoSerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    produto = serializer.save(loja=loja, atributos=atributos, ficheiro=request.FILES.get('ficheiro'))
 
    categoria_ids_raw = request.data.getlist('categoria_ids')
    if categoria_ids_raw:
        from ..models import CategoriaLoja
        cats = CategoriaLoja.objects.filter(id__in=[int(x) for x in categoria_ids_raw if x.isdigit()], loja=loja)
        produto.categorias.set(cats)
 
    novas_categorias_raw = request.data.getlist('novas_categorias')
    for nome in novas_categorias_raw:
        nome = nome.lower().strip()
        if nome:
            from ..models import CategoriaLoja
            cat, _ = CategoriaLoja.objects.get_or_create(loja=loja, nome=nome, defaults={'ativo': True})
            produto.categorias.add(cat)
 
    from ..models import Inventario
    Inventario.objects.get_or_create(
        loja=loja, produto=produto,
        defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco}
    )
 
    # ── NOVO: processar imagens adicionais ─────────────────────
    _gerir_imagens(produto, request)
 
    return Response(ProdutoSerializer(produto, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def produto_update(request, loja_id, id):
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
 
    produto = get_object_or_404(Produto, id=id, loja_id=loja_id)
 
    data = request.data.copy()
    if 'atributos' in data:
        try:
            data['atributos'] = json.loads(data['atributos']) if isinstance(data['atributos'], str) else data['atributos']
        except json.JSONDecodeError:
            return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)
 
    serializer = ProdutoSerializer(produto, data=data, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    produto = serializer.save()
    loja = produto.loja
 
    categoria_ids_raw = request.data.getlist('categoria_ids')
    if categoria_ids_raw:
        from ..models import CategoriaLoja
        cats = CategoriaLoja.objects.filter(id__in=[int(x) for x in categoria_ids_raw if x.isdigit()], loja=loja)
        produto.categorias.set(cats)
 
    novas_categorias_raw = request.data.getlist('novas_categorias')
    for nome in novas_categorias_raw:
        nome = nome.lower().strip()
        if nome:
            from ..models import CategoriaLoja
            cat, _ = CategoriaLoja.objects.get_or_create(loja=loja, nome=nome, defaults={'ativo': True})
            produto.categorias.add(cat)
 
    if 'ficheiro' in request.FILES:
        produto.ficheiro = request.FILES['ficheiro']
        produto.save(update_fields=['ficheiro'])
 
    # ── NOVO: processar imagens adicionais ─────────────────────
    _gerir_imagens(produto, request)
 
    return Response(ProdutoSerializer(produto, context={'request': request}).data)


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

# ── NOVO: eliminar imagem individual ───────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def produto_imagem_delete(request, loja_id, id, img_id):
    _, _, erro = _verificar_permissao_loja(request, loja_id, 'gerir_produtos')
    if erro:
        return erro
    produto = get_object_or_404(Produto, id=id, loja_id=loja_id)
    imagem  = get_object_or_404(ProdutoImagem, id=img_id, produto=produto)
    imagem.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def produto_categorias_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/produtos/categorias/
    Devolve as categorias distintas dos produtos activos desta loja.
    Usado na página pública da loja para construir os sliders e abas.
    """
    categorias = (
        Produto.objects
        .filter(loja_id=loja_id, ativo=True)
        .exclude(categoria='')
        .exclude(categoria__isnull=True)
        .values_list('categoria', flat=True)
        .distinct()
        .order_by('categoria')
    )
    return Response(list(categorias))