"""
Views/Endpoints do Sistema POS
Gestão de autenticação, configuração, mesas, contas, produtos híbridos e operações POS.
"""
import json
from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    ConfiguracaoPOS,
    Mesa,
    ContaMesa,
    ItemContaMesa,
    PagamentoDividido,
    TurnoPOS,
    ProdutoPOS,
)

from app.models import (
    Loja,
    Produto,
    Utilizador,
    UtilizadorLoja,
    TipoProduto,
    CategoriaLoja,
)

try:
    from app.models import Inventario
except Exception:
    Inventario = None


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _str_to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ['true', '1', 'yes', 'sim', 'on']


def _build_absolute_url(request, file_field):
    if not file_field:
        return None

    try:
        url = file_field.url
    except Exception:
        return None

    return request.build_absolute_uri(url) if request else url


def _getlist(data, key):
    if hasattr(data, 'getlist'):
        return data.getlist(key)

    value = data.get(key)
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _get_stock_loja(produto):
    """
    O modelo Produto da Bendi não tem stock.
    O stock normalmente vem do Inventario.
    """
    if Inventario is None:
        return None

    try:
        inv = Inventario.objects.filter(produto=produto, loja=produto.loja).first()
        if inv:
            return inv.quantidade
    except Exception:
        pass

    return None


def _set_stock_loja(produto, stock):
    if Inventario is None:
        return

    try:
        inv, _ = Inventario.objects.get_or_create(
            loja=produto.loja,
            produto=produto,
            defaults={
                'quantidade': 0,
                'preco_custo': 0,
                'preco_venda': produto.preco,
            }
        )
        inv.quantidade = int(stock or 0)
        inv.preco_venda = produto.preco
        inv.save(update_fields=['quantidade', 'preco_venda'])
    except Exception:
        pass


def _categorias_loja_payload(produto):
    try:
        return [
            {
                'id': cat.id,
                'nome': cat.nome
            }
            for cat in produto.categorias.all()
        ]
    except Exception:
        return []


def _categoria_loja_texto(produto):
    cats = _categorias_loja_payload(produto)
    if cats:
        return cats[0]['nome']
    return 'Sem categoria'


def _aplicar_categorias_loja(produto, request):
    """
    Aplica categorias no Produto da Bendi.
    Aceita:
    - categoria_ids
    - novas_categorias
    - categoria simples
    """
    categoria_ids_raw = _getlist(request.data, 'categoria_ids')

    if categoria_ids_raw:
        ids = [int(x) for x in categoria_ids_raw if str(x).isdigit()]
        cats = CategoriaLoja.objects.filter(id__in=ids, loja=produto.loja)
        produto.categorias.set(cats)

    novas_categorias = _getlist(request.data, 'novas_categorias')

    categoria_simples = (request.data.get('categoria') or '').strip()
    if categoria_simples:
        novas_categorias.append(categoria_simples)

    for nome in novas_categorias:
        nome = str(nome).lower().strip()
        if nome:
            cat, _ = CategoriaLoja.objects.get_or_create(
                loja=produto.loja,
                nome=nome,
                defaults={'ativo': True}
            )
            produto.categorias.add(cat)


def _produto_pos_payload(produto, request=None):
    return {
        'uid': f'pos-{produto.id}',
        'id': produto.id,
        'origem': 'pos',
        'nome': produto.nome,
        'descricao': produto.descricao,
        'preco': str(produto.preco),
        'categoria': produto.categoria or 'Sem categoria',
        'categorias': [
            {
                'id': None,
                'nome': produto.categoria or 'Sem categoria'
            }
        ],
        'tipo': None,
        'tipo_id': None,
        'imagem_url': _build_absolute_url(request, produto.imagem),
        'stock': produto.stock,
        'controlar_stock': produto.controlar_stock,
        'ativo': produto.ativo,
        'disponivel_pos': produto.disponivel_pos,
        'disponivel': produto.disponivel,
        'loja': None,
        'pos_id': produto.pos_id,
        'criado_em': produto.criado_em,
        'atualizado_em': produto.atualizado_em,
    }


def _produto_loja_payload(produto, request=None):
    ficheiro = getattr(produto, 'ficheiro', None)
    stock = _get_stock_loja(produto)

    ativo = getattr(produto, 'ativo', True)
    disponivel_pos = getattr(produto, 'disponivel_pos', True)

    return {
        'uid': f'loja-{produto.id}',
        'id': produto.id,
        'origem': 'loja',
        'nome': produto.nome,
        'descricao': produto.descricao,
        'preco': str(produto.preco),
        'sku': getattr(produto, 'sku', ''),
        'categoria': _categoria_loja_texto(produto),
        'categorias': _categorias_loja_payload(produto),
        'tipo': {
            'id': produto.tipo.id,
            'nome': produto.tipo.nome,
        } if produto.tipo else None,
        'tipo_id': produto.tipo_id,
        'atributos': produto.atributos or {},
        'imagem_url': _build_absolute_url(request, ficheiro),
        'stock': stock,
        'controlar_stock': stock is not None,
        'ativo': ativo,
        'disponivel_pos': disponivel_pos,
        'disponivel': bool(ativo and disponivel_pos and (stock is None or stock > 0)),
        'loja': {
            'id': produto.loja.id,
            'nome': produto.loja.nome,
        },
        'loja_id': produto.loja_id,
        'data_criacao': produto.data_criacao,
    }


def _pos_response(pos):
    return {
        'id': pos.id,
        'codigo_pos': pos.codigo_pos,
        'nome': pos.nome,
        'modo': pos.modo,
        'taxa_servico_ativa': pos.taxa_servico_ativa,
        'taxa_servico_percentagem': str(pos.taxa_servico_percentagem),
        'loja_vinculada': {
            'id': pos.loja_vinculada.id,
            'nome': pos.loja_vinculada.nome,
            'logo_url': pos.loja_vinculada.logo.url if pos.loja_vinculada and pos.loja_vinculada.logo else None,
        } if pos.loja_vinculada else None,
        'efatura_ativo': pos.efatura_ativo,
        'criado_em': pos.criado_em,
    }


def _verificar_permissao_loja_produtos(loja, utilizador):
    """
    Se o projeto tiver UtilizadorLoja permissões, usa-as.
    Se o dono da loja for o utilizador, permite.
    """
    if loja.dono_id == utilizador.id:
        return True

    try:
        return UtilizadorLoja.verificar_permissao(loja, utilizador, 'gerir_produtos')
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def pos_login(request):
    email = (request.data.get('email') or '').strip()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'detail': 'Email e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=email, password=password)

    if not user:
        try:
            django_user = User.objects.get(email__iexact=email)
            user = authenticate(request, username=django_user.username, password=password)
        except User.DoesNotExist:
            user = None

    if not user:
        return Response({'detail': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        utilizador = user.utilizador
    except Utilizador.DoesNotExist:
        return Response({'detail': 'Perfil de utilizador não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not utilizador.is_active:
        return Response({'detail': 'Conta desactivada'}, status=status.HTTP_403_FORBIDDEN)

    lojas_do_utilizador = Loja.objects.filter(dono=utilizador, ativa=True)
    pos_existentes = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True)

    if not pos_existentes.exists():
        ConfiguracaoPOS.objects.create(
            nome='POS Principal',
            dono=utilizador,
            modo='standalone'
        )
        pos_existentes = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True)

    refresh = RefreshToken.for_user(user)

    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': utilizador.id,
            'nome': utilizador.nome,
            'email': user.email,
            'username': user.username,
        },
        'tem_lojas': lojas_do_utilizador.exists(),
        'lojas': [
            {
                'id': l.id,
                'nome': l.nome,
                'logo_url': l.logo.url if l.logo else None,
                'pos_ativo': l.pos_ativo
            }
            for l in lojas_do_utilizador
        ],
        'pos_existentes': [
            {
                'id': p.id,
                'codigo_pos': p.codigo_pos,
                'nome': p.nome,
                'modo': p.modo,
                'loja_vinculada': {
                    'id': p.loja_vinculada.id,
                    'nome': p.loja_vinculada.nome
                } if p.loja_vinculada else None
            }
            for p in pos_existentes
        ]
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def pos_register(request):
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not all([first_name, last_name, email, password]):
        return Response({'detail': 'Todos os campos são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({'detail': 'Password deve ter no mínimo 6 caracteres'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        existing_user = User.objects.get(email__iexact=email)
        user = authenticate(request, username=existing_user.username, password=password)

        if not user:
            return Response(
                {'detail': 'Email já registado com password diferente. Use a opção "Login".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        utilizador = user.utilizador
        refresh = RefreshToken.for_user(user)

        pos_existentes = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True)
        if not pos_existentes.exists():
            ConfiguracaoPOS.objects.create(nome='POS Principal', dono=utilizador, modo='standalone')
            pos_existentes = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': utilizador.id,
                'nome': utilizador.nome,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
            },
            'pos_existentes': [
                {
                    'id': p.id,
                    'codigo_pos': p.codigo_pos,
                    'nome': p.nome,
                    'modo': p.modo,
                    'loja_vinculada': {
                        'id': p.loja_vinculada.id,
                        'nome': p.loja_vinculada.nome
                    } if p.loja_vinculada else None
                }
                for p in pos_existentes
            ],
            'mensagem': 'Login bem-sucedido com conta existente'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        pass

    base_username = email.split('@')[0]
    username = base_username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            utilizador = Utilizador.objects.create(
                user=user,
                status='ativo',
                verificado=False
            )

            pos = ConfiguracaoPOS.objects.create(
                nome='POS Principal',
                dono=utilizador,
                modo='standalone'
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': utilizador.id,
                    'nome': utilizador.nome,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'username': user.username,
                },
                'pos': {
                    'id': pos.id,
                    'codigo_pos': pos.codigo_pos,
                    'nome': pos.nome,
                    'modo': pos.modo,
                    'loja_vinculada': None
                },
                'mensagem': 'Conta criada com sucesso'
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'detail': f'Erro ao criar utilizador: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO POS
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_criar(request):
    utilizador = request.user.utilizador
    nome = request.data.get('nome', 'POS Principal')
    loja_id = request.data.get('loja_id')
    modo = request.data.get('modo', 'standalone')

    if modo not in ['standalone', 'integrado', 'hibrido']:
        modo = 'standalone'

    config = ConfiguracaoPOS.objects.create(
        nome=nome,
        dono=utilizador,
        modo='standalone'
    )

    if loja_id:
        loja = get_object_or_404(Loja, id=loja_id, dono=utilizador)
        config.conectar_loja(loja, modo='hibrido' if modo == 'hibrido' else 'integrado')
    else:
        config.modo = 'standalone'
        config.save(update_fields=['modo'])

    return Response(_pos_response(config), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def pos_detalhe(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    if request.method == 'PATCH':
        if 'nome' in request.data:
            pos.nome = request.data['nome']

        if 'modo' in request.data:
            modo = request.data['modo']
            if modo not in ['standalone', 'integrado', 'hibrido']:
                return Response({'detail': 'Modo inválido'}, status=status.HTTP_400_BAD_REQUEST)

            if modo in ['integrado', 'hibrido'] and not pos.loja_vinculada:
                return Response(
                    {'detail': 'Para usar modo integrado ou híbrido, conecta primeiro uma loja.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            pos.modo = modo

        pos.save()
        return Response(_pos_response(pos))

    return Response(_pos_response(pos))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_conectar_loja(request, pos_id):
    utilizador = request.user.utilizador
    loja_id = request.data.get('loja_id')
    modo = request.data.get('modo', 'integrado')

    if not loja_id:
        return Response({'detail': 'loja_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if modo not in ['integrado', 'hibrido']:
        modo = 'integrado'

    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    loja = get_object_or_404(Loja, id=loja_id, dono=utilizador)

    pos.conectar_loja(loja, modo=modo)

    loja.pos_ativo = True
    loja.save(update_fields=['pos_ativo'])

    return Response({
        'detail': f'POS conectado à loja {loja.nome}',
        'pos': _pos_response(pos)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_desconectar_loja(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    pos.desconectar_loja()

    return Response({
        'detail': 'POS desconectado da loja',
        'pos': _pos_response(pos)
    })


# ═══════════════════════════════════════════════════════════════════
# PRODUTOS HÍBRIDOS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pos_produtos(request, pos_id):
    """
    GET /api/pos/<pos_id>/produtos/

    Query params:
    - gestao=1      → inclui inativos
    - origem=pos    → só produtos POS
    - origem=loja   → só produtos loja
    - origem=todos  → ambos
    - q=texto
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)

    gestao = request.GET.get('gestao') in ['1', 'true', 'True']
    origem = request.GET.get('origem', 'todos')
    q = request.GET.get('q', '').strip()

    data = []

    if origem not in ['todos', 'pos', 'loja']:
        origem = 'todos'

    # Produtos próprios do POS
    if pos.modo in ['standalone', 'hibrido'] and origem in ['todos', 'pos']:
        qs_pos = ProdutoPOS.objects.filter(pos=pos)

        if not gestao:
            qs_pos = qs_pos.filter(ativo=True, disponivel_pos=True)

        if q:
            qs_pos = qs_pos.filter(
                Q(nome__icontains=q) |
                Q(descricao__icontains=q) |
                Q(categoria__icontains=q)
            )

        data.extend([_produto_pos_payload(produto, request) for produto in qs_pos])

    # Produtos da loja Bendi
    if pos.modo in ['integrado', 'hibrido'] and pos.loja_vinculada and origem in ['todos', 'loja']:
        qs_loja = Produto.objects.filter(loja=pos.loja_vinculada)

        if not gestao:
            qs_loja = qs_loja.filter(ativo=True, disponivel_pos=True)

        if q:
            qs_loja = qs_loja.filter(
                Q(nome__icontains=q) |
                Q(descricao__icontains=q)
            )

        data.extend([_produto_loja_payload(produto, request) for produto in qs_loja])

    return Response({
        'results': data,
        'count': len(data),
        'modo': pos.modo,
        'origem': origem,
        'loja_vinculada': {
            'id': pos.loja_vinculada.id,
            'nome': pos.loja_vinculada.nome,
        } if pos.loja_vinculada else None
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def produto_criar(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)

    origem = request.data.get('origem') or ('loja' if pos.modo == 'integrado' else 'pos')

    nome = (request.data.get('nome') or '').strip()
    descricao = request.data.get('descricao', '')
    categoria = (request.data.get('categoria') or 'Sem categoria').strip() or 'Sem categoria'
    preco = request.data.get('preco')
    imagem = request.FILES.get('imagem') or request.FILES.get('ficheiro')
    ativo = _str_to_bool(request.data.get('ativo'), True)
    disponivel_pos = _str_to_bool(request.data.get('disponivel_pos'), True)
    controlar_stock = _str_to_bool(request.data.get('controlar_stock'), False)
    stock = int(request.data.get('stock', 0) or 0)

    if not nome or preco is None:
        return Response({'detail': 'Nome e preço são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    if origem == 'pos':
        if pos.modo not in ['standalone', 'hibrido']:
            return Response(
                {'detail': 'Este POS não permite produtos próprios. Usa modo standalone ou híbrido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        produto = ProdutoPOS.objects.create(
            pos=pos,
            nome=nome,
            descricao=descricao,
            categoria=categoria,
            preco=Decimal(str(preco)),
            imagem=imagem,
            controlar_stock=controlar_stock,
            stock=stock,
            ativo=ativo,
            disponivel_pos=disponivel_pos
        )

        return Response(_produto_pos_payload(produto, request), status=status.HTTP_201_CREATED)

    if origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response(
                {'detail': 'Para criar produto da loja, o POS precisa estar integrado ou híbrido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        loja = pos.loja_vinculada

        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response(
                {'detail': 'Sem permissão para gerir produtos desta loja.'},
                status=status.HTTP_403_FORBIDDEN
            )

        atributos_raw = request.data.get('atributos', '{}')
        try:
            atributos = json.loads(atributos_raw) if isinstance(atributos_raw, str) else atributos_raw
        except json.JSONDecodeError:
            return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        tipo = None
        tipo_id = request.data.get('tipo_id')
        if tipo_id:
            tipo = get_object_or_404(TipoProduto, id=tipo_id, ativo=True)
            em_falta = tipo.validar_atributos(atributos)
            if em_falta:
                return Response(
                    {'atributos': f'Campos obrigatórios em falta: {em_falta}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        produto = Produto.objects.create(
            loja=loja,
            tipo=tipo,
            nome=nome,
            descricao=descricao,
            preco=Decimal(str(preco)),
            sku=request.data.get('sku', ''),
            ficheiro=imagem,
            atributos=atributos or {},
            destaque=_str_to_bool(request.data.get('destaque'), False),
            ativo=ativo,
            disponivel_pos=disponivel_pos,
        )

        _aplicar_categorias_loja(produto, request)
        _set_stock_loja(produto, stock)

        return Response(_produto_loja_payload(produto, request), status=status.HTTP_201_CREATED)

    return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def produto_atualizar(request, pos_id, produto_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)

    origem = request.data.get('origem') or request.GET.get('origem') or 'pos'

    if origem == 'pos':
        produto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos)

        if pos.modo not in ['standalone', 'hibrido']:
            return Response(
                {'detail': 'Este POS não permite produtos próprios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'nome' in request.data:
            produto.nome = request.data['nome']
        if 'descricao' in request.data:
            produto.descricao = request.data['descricao']
        if 'categoria' in request.data:
            produto.categoria = request.data['categoria'] or 'Sem categoria'
        if 'preco' in request.data:
            produto.preco = Decimal(str(request.data['preco']))
        if 'controlar_stock' in request.data:
            produto.controlar_stock = _str_to_bool(request.data.get('controlar_stock'), produto.controlar_stock)
        if 'stock' in request.data:
            produto.stock = int(request.data.get('stock') or 0)
        if 'ativo' in request.data:
            produto.ativo = _str_to_bool(request.data.get('ativo'), produto.ativo)
        if 'disponivel_pos' in request.data:
            produto.disponivel_pos = _str_to_bool(request.data.get('disponivel_pos'), produto.disponivel_pos)

        imagem = request.FILES.get('imagem') or request.FILES.get('ficheiro')
        if imagem:
            produto.imagem = imagem

        produto.save()
        return Response(_produto_pos_payload(produto, request))

    if origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response(
                {'detail': 'Este POS não está ligado a uma loja.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        loja = pos.loja_vinculada

        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response(
                {'detail': 'Sem permissão para gerir produtos desta loja.'},
                status=status.HTTP_403_FORBIDDEN
            )

        produto = get_object_or_404(Produto, id=produto_id, loja=loja)

        if 'nome' in request.data:
            produto.nome = request.data['nome']
        if 'descricao' in request.data:
            produto.descricao = request.data['descricao']
        if 'preco' in request.data:
            produto.preco = Decimal(str(request.data['preco']))
        if 'sku' in request.data:
            produto.sku = request.data['sku']
        if 'ativo' in request.data:
            produto.ativo = _str_to_bool(request.data.get('ativo'), produto.ativo)
        if 'disponivel_pos' in request.data:
            produto.disponivel_pos = _str_to_bool(request.data.get('disponivel_pos'), produto.disponivel_pos)
        if 'destaque' in request.data:
            produto.destaque = _str_to_bool(request.data.get('destaque'), produto.destaque)

        if 'tipo_id' in request.data:
            tipo_id = request.data.get('tipo_id')
            produto.tipo = get_object_or_404(TipoProduto, id=tipo_id, ativo=True) if tipo_id else None

        if 'atributos' in request.data:
            try:
                produto.atributos = json.loads(request.data['atributos']) if isinstance(request.data['atributos'], str) else request.data['atributos']
            except json.JSONDecodeError:
                return Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        imagem = request.FILES.get('imagem') or request.FILES.get('ficheiro')
        if imagem:
            produto.ficheiro = imagem

        produto.save()
        _aplicar_categorias_loja(produto, request)

        if 'stock' in request.data:
            _set_stock_loja(produto, int(request.data.get('stock') or 0))

        return Response(_produto_loja_payload(produto, request))

    return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def produto_apagar(request, pos_id, produto_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)

    origem = request.GET.get('origem') or request.data.get('origem') or 'pos'

    if origem == 'pos':
        produto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos)
        produto.ativo = False
        produto.save(update_fields=['ativo'])
        return Response({
            'detail': 'Produto POS desativado com sucesso.',
            'produto': _produto_pos_payload(produto, request)
        })

    if origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja.'}, status=status.HTTP_400_BAD_REQUEST)

        loja = pos.loja_vinculada

        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response({'detail': 'Sem permissão para gerir produtos desta loja.'}, status=status.HTTP_403_FORBIDDEN)

        produto = get_object_or_404(Produto, id=produto_id, loja=loja)
        produto.ativo = False
        produto.save(update_fields=['ativo'])

        return Response({
            'detail': 'Produto da loja desativado com sucesso.',
            'produto': _produto_loja_payload(produto, request)
        })

    return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
# MESAS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mesas_listar(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    mesas = Mesa.objects.filter(pos=pos, ativa=True).order_by('numero')

    data = [
        {
            'id': m.id,
            'numero': m.numero,
            'capacidade': m.capacidade,
            'status': m.status,
            'atendente_atual': {
                'id': m.atendente_atual.id,
                'nome': m.atendente_atual.nome
            } if m.atendente_atual else None,
            'aberta_em': m.aberta_em,
            'tem_conta_aberta': ContaMesa.objects.filter(mesa=m, status='aberta').exists()
        }
        for m in mesas
    ]

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mesa_criar(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    numero = request.data.get('numero')
    capacidade = request.data.get('capacidade', 4)

    if not numero:
        return Response({'detail': 'Número da mesa é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if Mesa.objects.filter(pos=pos, numero=numero).exists():
        return Response({'detail': 'Já existe uma mesa com este número'}, status=status.HTTP_400_BAD_REQUEST)

    mesa = Mesa.objects.create(pos=pos, numero=numero, capacidade=capacidade)

    return Response({
        'id': mesa.id,
        'numero': mesa.numero,
        'capacidade': mesa.capacidade,
        'status': mesa.status
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mesa_abrir(request, pos_id, mesa_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)

    if mesa.status != 'livre':
        return Response({'detail': f'Mesa está {mesa.status}, não pode ser aberta'}, status=status.HTTP_400_BAD_REQUEST)

    mesa.abrir(utilizador)

    return Response({
        'detail': 'Mesa aberta',
        'mesa': {
            'id': mesa.id,
            'numero': mesa.numero,
            'status': mesa.status
        }
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def mesa_apagar(request, pos_id, mesa_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)

    if ContaMesa.objects.filter(mesa=mesa, status='aberta').exists():
        return Response({'detail': 'Não é possível apagar mesa com conta aberta'}, status=status.HTTP_400_BAD_REQUEST)

    mesa.delete()
    return Response({'detail': 'Mesa apagada com sucesso'})


# ═══════════════════════════════════════════════════════════════════
# CONTAS
# ═══════════════════════════════════════════════════════════════════

def _conta_payload(conta, request=None):
    items = ItemContaMesa.objects.filter(conta=conta).select_related('produto', 'produto_pos')

    return {
        'id': conta.id,
        'mesa': {
            'id': conta.mesa.id,
            'numero': conta.mesa.numero
        },
        'atendente': {
            'id': conta.atendente.id,
            'nome': conta.atendente.nome
        } if conta.atendente else None,
        'status': conta.status,
        'subtotal': str(conta.subtotal),
        'taxa_servico_percentagem': str(conta.taxa_servico_percentagem),
        'taxa_servico_valor': str(conta.taxa_servico_valor),
        'gorjeta': str(conta.gorjeta),
        'desconto_valor': str(conta.desconto_valor),
        'total': str(conta.total),
        'items': [
            {
                'id': item.id,
                'produto_id': item.produto_ref_id,
                'origem': item.origem,
                'nome': item.nome,
                'quantidade': item.quantidade,
                'preco_unitario': str(item.preco_unitario),
                'preco_total': str(item.preco_total),
                'observacoes': item.observacoes,
                'status': item.status
            }
            for item in items
        ],
        'criada_em': conta.criada_em,
        'fechada_em': conta.fechada_em
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conta_criar(request, pos_id, mesa_id):
    """
    GET  → devolve conta aberta da mesa.
    POST → cria conta se não existir.
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)

    conta_aberta = ContaMesa.objects.filter(mesa=mesa, status='aberta').first()

    if request.method == 'GET':
        if not conta_aberta:
            return Response({'detail': 'Esta mesa não tem conta aberta'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_conta_payload(conta_aberta, request))

    if conta_aberta:
        return Response(_conta_payload(conta_aberta, request), status=status.HTTP_200_OK)

    conta = ContaMesa.objects.create(
        pos=pos,
        mesa=mesa,
        atendente=utilizador,
        taxa_servico_percentagem=pos.taxa_servico_percentagem if pos.taxa_servico_ativa else Decimal('0.00')
    )

    mesa.abrir(utilizador)

    return Response(_conta_payload(conta, request), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conta_detalhe(request, pos_id, conta_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)

    return Response(_conta_payload(conta, request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conta_adicionar_item(request, pos_id, conta_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    produto_id = request.data.get('produto_id')
    origem = request.data.get('origem', 'loja')
    quantidade = int(request.data.get('quantidade', 1) or 1)
    observacoes = request.data.get('observacoes', '')

    if not produto_id:
        return Response({'detail': 'produto_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if origem == 'pos':
        produto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos, ativo=True)

        if not produto.disponivel:
            return Response({'detail': 'Produto POS indisponível'}, status=status.HTTP_400_BAD_REQUEST)

        if produto.controlar_stock and produto.stock < quantidade:
            return Response({'detail': 'Stock insuficiente'}, status=status.HTTP_400_BAD_REQUEST)

        item = ItemContaMesa.objects.create(
            conta=conta,
            produto=None,
            produto_pos=produto,
            nome=produto.nome,
            quantidade=quantidade,
            preco_unitario=produto.preco,
            observacoes=observacoes
        )

        if produto.controlar_stock:
            produto.stock = max(produto.stock - quantidade, 0)
            produto.save(update_fields=['stock'])

    elif origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja'}, status=status.HTTP_400_BAD_REQUEST)

        produto = get_object_or_404(
            Produto,
            id=produto_id,
            loja=pos.loja_vinculada,
            ativo=True,
            disponivel_pos=True
        )

        item = ItemContaMesa.objects.create(
            conta=conta,
            produto=produto,
            produto_pos=None,
            nome=produto.nome,
            quantidade=quantidade,
            preco_unitario=produto.preco,
            observacoes=observacoes
        )

    else:
        return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'detail': 'Item adicionado',
        'item': {
            'id': item.id,
            'produto_id': item.produto_ref_id,
            'origem': item.origem,
            'nome': item.nome,
            'quantidade': item.quantidade,
            'preco_total': str(item.preco_total)
        },
        'conta': {
            'subtotal': str(conta.subtotal),
            'total': str(conta.total)
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def conta_remover_item(request, pos_id, conta_id, item_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    item = get_object_or_404(ItemContaMesa, id=item_id, conta=conta)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    if item.produto_pos and item.produto_pos.controlar_stock:
        produto = item.produto_pos
        produto.stock += item.quantidade
        produto.save(update_fields=['stock'])

    item.delete()
    conta.calcular_totais()

    return Response({
        'detail': 'Item removido',
        'conta': {
            'subtotal': str(conta.subtotal),
            'total': str(conta.total)
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conta_fechar(request, pos_id, conta_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    metodo_pagamento = request.data.get('metodo_pagamento')
    nif_cliente = request.data.get('nif_cliente', '')

    if not metodo_pagamento:
        return Response({'detail': 'metodo_pagamento é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if nif_cliente:
        conta.nif_cliente = nif_cliente
        conta.save(update_fields=['nif_cliente'])

    conta.fechar(metodo_pagamento)

    return Response({
        'detail': 'Conta fechada com sucesso',
        'conta': {
            'id': conta.id,
            'total': str(conta.total),
            'metodo_pagamento': conta.metodo_pagamento,
            'fechada_em': conta.fechada_em
        }
    })


# ═══════════════════════════════════════════════════════════════════
# TURNOS
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def turno_abrir(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    if TurnoPOS.objects.filter(pos=pos, aberto=True).exists():
        return Response({'detail': 'Já existe um turno aberto'}, status=status.HTTP_400_BAD_REQUEST)

    valor_abertura = request.data.get('valor_abertura')
    if valor_abertura is None:
        return Response({'detail': 'valor_abertura é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    turno = TurnoPOS.objects.create(
        pos=pos,
        operador=utilizador,
        valor_abertura=Decimal(str(valor_abertura))
    )

    return Response({
        'id': turno.id,
        'valor_abertura': str(turno.valor_abertura),
        'aberto_em': turno.aberto_em
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def turno_fechar(request, pos_id, turno_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    turno = get_object_or_404(TurnoPOS, id=turno_id, pos=pos)

    if not turno.aberto:
        return Response({'detail': 'Turno já está fechado'}, status=status.HTTP_400_BAD_REQUEST)

    valor_fecho = request.data.get('valor_fecho')
    if valor_fecho is None:
        return Response({'detail': 'valor_fecho é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    turno.fechar_turno(Decimal(str(valor_fecho)))

    return Response({
        'id': turno.id,
        'valor_abertura': str(turno.valor_abertura),
        'valor_fecho': str(turno.valor_fecho),
        'diferenca': str(turno.diferenca),
        'fechado_em': turno.fechado_em
    })
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contas_ativas(request, pos_id):
    """
    Lista contas abertas do POS.
    Usado no separador Pedidos.
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    contas = ContaMesa.objects.filter(
        pos=pos,
        status='aberta'
    ).select_related('mesa', 'atendente').order_by('-criada_em')

    return Response([
        _conta_payload(conta, request)
        for conta in contas
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pos_historico(request, pos_id):
    """
    Lista contas fechadas do POS.
    Usado no separador Histórico.
    Suporta:
    ?data_inicio=YYYY-MM-DD
    ?data_fim=YYYY-MM-DD
    ?metodo=dinheiro|cartao|mbway|transferencia|dividida
    ?offset=0
    ?limit=20
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    qs = ContaMesa.objects.filter(
        pos=pos,
        status='fechada'
    ).select_related('mesa', 'atendente').order_by('-fechada_em')

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    metodo = request.GET.get('metodo')

    if data_inicio:
        qs = qs.filter(fechada_em__date__gte=data_inicio)

    if data_fim:
        qs = qs.filter(fechada_em__date__lte=data_fim)

    if metodo:
        qs = qs.filter(metodo_pagamento=metodo)

    try:
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
    except ValueError:
        offset = 0
        limit = 20

    limit = min(max(limit, 1), 100)

    total = qs.count()
    qs = qs[offset:offset + limit]

    return Response({
        'count': total,
        'results': [
            _conta_payload(conta, request)
            for conta in qs
        ]
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def item_status_atualizar(request, pos_id, conta_id, item_id):
    """
    Atualiza o status de um item da conta.
    Usado no separador Pedidos.
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    item = get_object_or_404(ItemContaMesa, id=item_id, conta=conta)

    novo_status = request.data.get('status')

    status_validos = [
        'pendente',
        'preparando',
        'pronto',
        'entregue',
        'cancelado'
    ]

    if novo_status not in status_validos:
        return Response(
            {'detail': 'Status inválido.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    item.status = novo_status
    item.save(update_fields=['status', 'atualizado_em'])

    return Response({
        'detail': 'Status atualizado.',
        'item': {
            'id': item.id,
            'status': item.status
        }
    })