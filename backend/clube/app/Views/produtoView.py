from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Count
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
from ..utils.dinheiro import ler_valor
from ..utils.variantes import sincronizar_variantes, aplicar_grelha_do_pedido
from ..utils.tipos import tipos_para_loja, tipo_permitido
from ..utils import conjuntos as conj

# prefetch dos componentes dos conjuntos (evita uma query por componente nas listagens)
PREFETCH_CONJUNTO = ('componentes__produto__inventario', 'componentes__variante', 'componentes__produto__variantes',
                     'grupos__opcoes__produto__inventario', 'grupos__opcoes__variante', 'grupos__opcoes__produto__variantes')


def _quer_conjunto(dados, atual=False):
    """Campo e_conjunto do formulário (multipart → texto); sem o campo, mantém o actual."""
    if 'e_conjunto' not in dados:
        return atual
    return str(dados.get('e_conjunto')).lower() in ('1', 'true', 'on', 'sim')


def _aplicar_conjunto(produto, dados):
    """
    Liga/desliga o conjunto e guarda os componentes enviados (tudo-ou-nada com o resto do
    formulário: quem chama faz set_rollback se vier erro). Devolve a mensagem de erro ou None.
    """
    quer = _quer_conjunto(dados, produto.e_conjunto)
    linhas, erro = conj.ler_componentes(dados)
    if erro:
        return erro

    if not quer:
        if produto.e_conjunto:
            from ..models import Inventario
            produto.componentes.all().delete()
            produto.grupos.all().delete()
            produto.e_conjunto = False
            produto.save(update_fields=['e_conjunto'])
            # volta a ser um produto normal → passa a ter stock próprio (começa a 0)
            Inventario.objects.get_or_create(
                loja=produto.loja, produto=produto,
                defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco})
        return None

    if not produto.e_conjunto:
        usado = conj.conjuntos_que_usam(produto)
        if usado:
            return (f'"{produto.nome}" faz parte de {", ".join(usado)} — '
                    f'um produto dentro de um conjunto não pode ser ele próprio um conjunto.')
        if produto.stock_por_variante:
            return 'Este produto tem stock por variação — um conjunto não tem stock próprio. Cria um produto novo para o conjunto.'
        if linhas is None and 'grupos' not in dados:
            return 'Escolhe os produtos que fazem parte do conjunto.'
        produto.e_conjunto = True
        produto.save(update_fields=['e_conjunto'])

    return conj.aplicar_formulario(produto, dados, conj.resolver_loja(produto.loja))


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
    tipos = TipoProduto.objects.filter(ativo=True, loja__isnull=True, pos__isnull=True)
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
        Q(loja__isnull=True, pos__isnull=True, ativo=True) |  # globais: só activos
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
 
    # o produto passou a ter várias categorias (M2M) — o campo antigo `categoria` dava erro 500
    categorias = (
        Produto.objects
        .filter(ativo=True, loja__ativa=True, categorias__isnull=False)
        .values('categorias__nome')
        .annotate(total=Count('id', distinct=True))
        .filter(total__gte=min_produtos)
        .order_by('-total')  # mais populares primeiro
    )
    # limita o número de categorias devolvidas (default 20, max 50)
    limit = min(int(request.GET.get('limit', 20)), 50)
    categorias = categorias[:limit]

    return Response([
        {'categoria': c['categorias__nome'], 'total': c['total']}
        for c in categorias
    ])
    
def _gere_loja(request, loja_id):
    """O utilizador é staff da plataforma ou membro activo desta loja (backoffice)?"""
    u = request.user
    if not u.is_authenticated:
        return False
    if u.is_staff:
        return True
    return UtilizadorLoja.objects.filter(
        loja_id=loja_id, utilizador__user=u, ativo=True
    ).exists()


def _so_lojas_visiveis(request, qs, loja_id=None):
    """
    Listagens públicas: só produtos de lojas activas (pendentes, fechadas e suspensas não
    aparecem na home nem nas pesquisas). Quem gere a loja pedida continua a ver os produtos
    dela — o backoffice usa estes endpoints mesmo com a loja fechada.
    """
    if loja_id and str(loja_id).isdigit() and _gere_loja(request, loja_id):
        return qs
    return qs.filter(loja__ativa=True)


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
    qs = Produto.objects.select_related('loja', 'tipo', 'inventario').prefetch_related('variantes', *PREFETCH_CONJUNTO).filter(ativo=True)

    # ── 1) filtro por loja ────────────────────────────────────
    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    qs = _so_lojas_visiveis(request, qs, loja_id)

    # ── 2) filtro por tipo de produto ─────────────────────────
    tipo = request.GET.get('tipo')
    if tipo:
        qs = qs.filter(tipo__nome__iexact=tipo)

    tipo_id = request.GET.get('tipo_id')
    if tipo_id and tipo_id.isdigit():
        qs = qs.filter(tipo_id=tipo_id)

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
    # (NaN/Infinity/negativos eram aceites pelo float() e rebentavam a query com erro 500)
    for campo, lookup in (('preco_min', 'preco__gte'), ('preco_max', 'preco__lte')):
        valor, erro_preco = ler_valor(request.GET.get(campo), obrigatorio=False)
        if erro_preco:
            return Response({'detail': 'preco_min / preco_max inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
        if valor is not None:
            qs = qs.filter(**{lookup: valor})

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

    # ordem estável — sem ela o offset pode repetir/saltar produtos entre páginas
    qs = qs.order_by('-id')

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
    if not produto.loja.ativa and not _gere_loja(request, produto.loja_id):
        return Response({'detail': 'Produto não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
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

    qs = Produto.objects.select_related('tipo', 'inventario').prefetch_related('variantes', *PREFETCH_CONJUNTO).filter(loja_id=loja_id)

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
        tipo = tipo_permitido(tipos_para_loja(loja), tipo_id)
        if not tipo:
            return Response({'tipo_id': 'Tipo inválido para esta loja.'}, status=status.HTTP_400_BAD_REQUEST)
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
 
    # conjunto (menu, pack): sem inventário nem grelha próprios — o stock é o dos componentes
    if _quer_conjunto(request.data):
        erro_conj = _aplicar_conjunto(produto, request.data)
        if erro_conj:
            transaction.set_rollback(True)
            return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
        _gerir_imagens(produto, request)
        return Response(ProdutoSerializer(produto, context={'request': request}).data, status=status.HTTP_201_CREATED)

    from ..models import Inventario
    Inventario.objects.get_or_create(
        loja=loja, produto=produto,
        defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco}
    )

    # ── NOVO: processar imagens adicionais ─────────────────────
    _gerir_imagens(produto, request)

    # grelha de stock por variação enviada com o formulário (tudo-ou-nada)
    erro_grelha = aplicar_grelha_do_pedido(produto, request.data)
    if erro_grelha:
        transaction.set_rollback(True)
        return Response({'detail': erro_grelha}, status=status.HTTP_400_BAD_REQUEST)

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
    aviso = conj.aviso_desactivar(produto, request.data, request.GET)
    if aviso:
        return Response(aviso, status=status.HTTP_409_CONFLICT)
 
    # DEPOIS — sem copy(), sem erro:
    atributos_raw = request.data.get('atributos')
    atributos_parsed = None
    if atributos_raw:
        try:
            atributos_parsed = json.loads(atributos_raw) if isinstance(atributos_raw, str) else atributos_raw
        except json.JSONDecodeError:
            return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    campos = {}
    for field in ['nome', 'preco', 'sku', 'descricao', 'destaque', 'ativo', 'tipo_id']:
        if field in request.data:
            campos[field] = request.data[field]
    if campos.get('tipo_id') and tipo_permitido(tipos_para_loja(produto.loja), campos['tipo_id']) is False:
        return Response({'tipo_id': 'Tipo inválido para esta loja.'}, status=status.HTTP_400_BAD_REQUEST)
    if atributos_parsed is not None:
        campos['atributos'] = atributos_parsed

    serializer = ProdutoSerializer(produto, data=campos, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    produto = serializer.save()
    loja = produto.loja

    # opções/tipo mudaram → grelha de variantes acompanha (novas a 0, removidas desactivadas)
    if produto.stock_por_variante and ('atributos' in campos or 'tipo_id' in campos):
        sincronizar_variantes(produto)

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

    # conjunto: liga/desliga e componentes (tudo-ou-nada com o resto do formulário)
    erro_conj = _aplicar_conjunto(produto, request.data)
    if erro_conj:
        transaction.set_rollback(True)
        return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)

    # grelha de stock por variação enviada com o formulário (tudo-ou-nada) — conjuntos não têm
    erro_grelha = None if produto.e_conjunto else aplicar_grelha_do_pedido(produto, request.data)
    if erro_grelha:
        transaction.set_rollback(True)
        return Response({'detail': erro_grelha}, status=status.HTTP_400_BAD_REQUEST)
    produto.refresh_from_db()

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
    # faz parte de conjuntos → avisa primeiro (esses conjuntos deixam de se vender);
    # o backoffice repete o pedido com ?confirmar=1 depois de o dono confirmar
    usado = conj.conjuntos_que_usam(produto)
    if usado and request.GET.get('confirmar') != '1':
        return Response({
            'detail': f'"{produto.nome}" faz parte de {", ".join(usado)}. '
                      f'Se o desactivares, esses conjuntos ficam indisponíveis até o retirares deles.',
            'conjuntos': usado,
            'precisa_confirmar': True,
        }, status=status.HTTP_409_CONFLICT)
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
def produto_tipos_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/produtos/tipos/
    Tipos com produtos activos nesta loja, com a contagem de cada um,
    e o total de produtos activos. Usado pelas templates da página pública
    para montar as secções "Por tipo" sem descarregar os produtos.
    """
    qs = _so_lojas_visiveis(request, Produto.objects.filter(loja_id=loja_id, ativo=True), loja_id)
    tipos = (
        qs.filter(tipo__isnull=False)
        .values('tipo_id', 'tipo__nome')
        .annotate(total_produtos=Count('id'))
        .order_by('tipo__nome')
    )
    return Response({
        'total': qs.count(),
        'destaques': qs.filter(destaque=True).count(),
        'tipos': [
            {'id': t['tipo_id'], 'nome': t['tipo__nome'], 'total_produtos': t['total_produtos']}
            for t in tipos
        ],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def produto_categorias_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/produtos/categorias/
    Devolve as categorias distintas dos produtos activos desta loja.
    Usado na página pública da loja para construir os sliders e abas.
    """
    qs = _so_lojas_visiveis(request, Produto.objects.filter(loja_id=loja_id, ativo=True), loja_id)
    categorias = (
        qs.filter(categorias__isnull=False)
        .values_list('categorias__nome', flat=True)
        .distinct()
        .order_by('categorias__nome')
    )
    return Response(list(categorias))