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
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from .serializers import ContaMesaSerializer, ItemContaMesaSerializer, MesaSerializer

from .models import (
    ConfiguracaoPOS,
    Mesa,
    ContaMesa,
    ItemContaMesa,
    PagamentoDividido,
    TurnoPOS,
    ProdutoPOS,
    UtilizadorPOS,
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
    
from .permissions import (
    POSAuthentication,
    IsPOSAuthenticated,
    IsContaPrincipal,
    is_membro,
    get_membro_from_request,
)

from rest_framework.decorators import authentication_classes

# ── Rate limiting ──────────────────────────────────────────────────
from django_ratelimit.core import is_ratelimited
from functools import wraps
from django.http import Http404

 
 
def pos_ratelimit(key='ip', rate='10/m', method='POST'):
    """
    Decorator de rate limiting compatível com DRF.
    Devolve Response 429 em vez de HttpResponse Django.
 
    Limites aplicados:
      pos_login        → 10/min por IP, 5/min por email
      pos_membro_login → 15/min por IP
      pos_register     → 5/hora por IP
    """
    def decorator(func):
        @wraps(func)
        def wrapped(request, *args, **kwargs):
            limited = is_ratelimited(
                request=request,
                group=f'pos_{func.__name__}',
                key=key,
                rate=rate,
                method=method,
                increment=True,
            )
            if limited:
                return Response(
                    {'detail': 'Demasiadas tentativas. Aguarda um momento antes de tentar novamente.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            return func(request, *args, **kwargs)
        return wrapped
    return decorator
 


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
    if Inventario is None:
        return None
    try:
        inv = Inventario.objects.filter(produto=produto, loja=produto.loja).first()
        if inv:
            return inv.quantidade
    except Exception:
        pass
    return None


def _resolve_pos_request(request, pos_id, require_owner=False, ativo=False):
    """Retorna o POS acessível pelo request de conta principal ou membro de equipa."""
    membro = get_membro_from_request(request)

    if membro:
        query = ConfiguracaoPOS.objects.filter(id=pos_id)
        if ativo:
            query = query.filter(ativo=True)
        pos = get_object_or_404(query)
        if pos.id != membro.pos.id or require_owner:
            raise Http404()
        return pos, membro, None

    utilizador = request.user.utilizador
    query = ConfiguracaoPOS.objects.filter(id=pos_id, dono=utilizador)
    if ativo:
        query = query.filter(ativo=True)
    pos = get_object_or_404(query)
    return pos, None, utilizador


def _get_pos_for_request(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id, ativo=False)
    return pos, membro


def _set_stock_loja(produto, stock):
    if Inventario is None:
        return
    try:
        inv, _ = Inventario.objects.get_or_create(
            loja=produto.loja,
            produto=produto,
            defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco}
        )
        inv.quantidade = int(stock or 0)
        inv.preco_venda = produto.preco
        inv.save(update_fields=['quantidade', 'preco_venda'])
    except Exception:
        pass


def _categorias_loja_payload(produto):
    try:
        return [{'id': cat.id, 'nome': cat.nome} for cat in produto.categorias.all()]
    except Exception:
        return []


def _categoria_loja_texto(produto):
    cats = _categorias_loja_payload(produto)
    return cats[0]['nome'] if cats else 'Sem categoria'


def _aplicar_categorias_loja(produto, request):
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
                loja=produto.loja, nome=nome, defaults={'ativo': True}
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
        'categorias': [{'id': None, 'nome': produto.categoria or 'Sem categoria'}],
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
        'tipo': {'id': produto.tipo.id, 'nome': produto.tipo.nome} if produto.tipo else None,
        'tipo_id': produto.tipo_id,
        'atributos': produto.atributos or {},
        'imagem_url': _build_absolute_url(request, ficheiro),
        'stock': stock,
        'controlar_stock': stock is not None,
        'ativo': ativo,
        'disponivel_pos': disponivel_pos,
        'disponivel': bool(ativo and disponivel_pos and (stock is None or stock > 0)),
        'loja': {'id': produto.loja.id, 'nome': produto.loja.nome},
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
    if loja.dono_id == utilizador.id:
        return True
    try:
        return UtilizadorLoja.verificar_permissao(loja, utilizador, 'gerir_produtos')
    except Exception:
        return False


def _conta_payload(conta, request=None):
    items = ItemContaMesa.objects.filter(conta=conta).select_related('produto', 'produto_pos')
    return {
        'id': conta.id,
        'mesa': {'id': conta.mesa.id, 'numero': conta.mesa.numero},
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
                'status': item.status,
            }
            for item in items
        ],
        'criada_em': conta.criada_em,
        'fechada_em': conta.fechada_em,
    }


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — CONTA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
@pos_ratelimit(key='ip', rate='10/m')
@pos_ratelimit(key='post:email', rate='5/m')
def pos_login(request):
    """
    Login de conta principal (dono do POS).
    Credenciais: email + password
    """
    email    = (request.data.get('email') or '').strip()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'detail': 'Email e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        django_user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        django_user = None

    if not django_user:
        return Response(
            {'detail': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = authenticate(
        request,
        username=django_user.username,
        password=password
    )

    if not user:
        return Response({'detail': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        utilizador = user.utilizador
    except Exception:
        return Response({'detail': 'Perfil não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    pos_list = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True)
    lojas    = Loja.objects.filter(dono=utilizador, ativa=True)
    refresh  = RefreshToken.for_user(user)

    return Response({
        'tipo_sessao': 'principal',
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': utilizador.id,
            'nome': utilizador.nome,
            'email': user.email,
        },
        'tem_lojas': lojas.exists(),
        'lojas': [
            {'id': l.id, 'nome': l.nome, 'logo_url': l.logo.url if l.logo else None}
            for l in lojas
        ],
        'pos_existentes': [
            {
                'id': p.id,
                'codigo_pos': p.codigo_pos,
                'nome': p.nome,
                'modo': p.modo,
                'loja_vinculada': {
                    'id': p.loja_vinculada.id,
                    'nome': p.loja_vinculada.nome,
                } if p.loja_vinculada else None,
            }
            for p in pos_list
        ],
        'precisa_onboarding': not pos_list.exists(),
    })


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — MEMBRO DE EQUIPA
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
@pos_ratelimit(key='ip', rate='15/m') 
def pos_membro_login(request):
    """
    Login de membro de equipa.
    Credenciais: username_pos + password
    JWT com claims customizados (sem User Django).
    """
    username = (request.data.get('username') or '').strip().lower()
    password = request.data.get('password', '')
    pos_id   = request.data.get('pos_id')

    if not username or not password:
        return Response(
            {'detail': 'Username e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    membros = UtilizadorPOS.objects.filter(
        username_pos__iexact=username,
        ativo=True
    ).select_related('pos')

    if not membros.exists():
        return Response({'detail': 'Utilizador não encontrado'}, status=status.HTTP_401_UNAUTHORIZED)

    if pos_id:
        membros = membros.filter(pos_id=pos_id)
        if not membros.exists():
            return Response(
                {'detail': 'Utilizador não encontrado neste POS'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    # Username em vários POS → pedir escolha
    if membros.count() > 1 and not pos_id:
        return Response(
            {
                'detail': 'Username existe em mais de um POS. Escolhe qual.',
                'escolher_pos': True,
                'pos_disponiveis': [
                    {
                        'pos_id': m.pos.id,
                        'pos_nome': m.pos.nome,
                        'codigo_pos': m.pos.codigo_pos,
                    }
                    for m in membros
                ]
            },
            status=status.HTTP_200_OK
        )

    membro = membros.first()

    if not membro.check_password(password):
        return Response({'detail': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    # JWT com claims customizados (sem User Django)
    access  = AccessToken()
    refresh = RefreshToken()

    claims = {
        'tipo_sessao':  'membro',
        'membro_id':    membro.id,
        'pos_id':       membro.pos.id,
        'pos_nome':     membro.pos.nome,
        'papel':        membro.papel,
        'nome':         membro.nome,
        'username_pos': membro.username_pos,
    }

    for key, val in claims.items():
        access[key]  = val
        refresh[key] = val

    return Response({
        'tipo_sessao': 'membro',
        'access_token': str(access),
        'refresh_token': str(refresh),
        'membro': {
            'id':           membro.id,
            'nome':         membro.nome,
            'username_pos': membro.username_pos,
            'papel':        membro.papel,
            'papel_display':membro.get_papel_display(),
        },
        'pos': {
            'id':          membro.pos.id,
            'nome':        membro.pos.nome,
            'codigo_pos':  membro.pos.codigo_pos,
            'modo':        membro.pos.modo,
            'loja_vinculada': {
                'id': membro.pos.loja_vinculada.id,
                'nome': membro.pos.loja_vinculada.nome,
            } if membro.pos.loja_vinculada else None,
        },
        'permissoes': {
            'pode_abrir_mesas':         membro.pode_abrir_mesas,
            'pode_fechar_contas':       membro.pode_fechar_contas,
            'pode_cancelar_items':      membro.pode_cancelar_items,
            'pode_dar_descontos':       membro.pode_dar_descontos,
            'pode_gerir_produtos':      membro.pode_gerir_produtos,
            'pode_gerir_mesas':         membro.pode_gerir_mesas,
            'pode_gerir_utilizadores':  membro.pode_gerir_utilizadores,
            'pode_ver_relatorios':      membro.pode_ver_relatorios,
            'pode_abrir_fechar_turno':  membro.pode_abrir_fechar_turno,
            'pode_ver_pedidos':         membro.pode_ver_pedidos,
            'pode_atualizar_status_items': membro.pode_atualizar_status_items,
        },
    })


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — REGISTO
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
@pos_ratelimit(key='ip', rate='5/h')
def pos_register(request):
    """Registo de conta principal."""
    first_name = request.data.get('first_name', '').strip()
    last_name  = request.data.get('last_name', '').strip()
    email      = request.data.get('email', '').strip()
    password   = request.data.get('password', '')

    if not all([first_name, last_name, email, password]):
        return Response(
            {'detail': 'Todos os campos são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 6:
        return Response(
            {'detail': 'Password deve ter no mínimo 6 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Email já existe → tentar login
    try:
        existing_user = User.objects.get(email__iexact=email)
        user = authenticate(request, username=existing_user.username, password=password)

        if not user:
            return Response(
                {'detail': 'Email já registado com password diferente. Usa Login.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        utilizador     = user.utilizador
        refresh        = RefreshToken.for_user(user)
        pos_existentes = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True)
        lojas          = Loja.objects.filter(dono=utilizador, ativa=True)

        return Response({
            'tipo_sessao': 'principal',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {'id': utilizador.id, 'nome': utilizador.nome, 'email': user.email},
            'tem_lojas': lojas.exists(),
            'lojas': [{'id': l.id, 'nome': l.nome} for l in lojas],
            'pos_existentes': [
                {'id': p.id, 'codigo_pos': p.codigo_pos, 'nome': p.nome, 'modo': p.modo}
                for p in pos_existentes
            ],
            'precisa_onboarding': not pos_existentes.exists(),
            'mensagem': 'Login com conta existente',
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        pass

    # Criar nova conta
    base = email.split('@')[0]
    username = base
    i = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{i}"
        i += 1

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name,
            )
            utilizador = Utilizador.objects.create(user=user, status='ativo', verificado=False)
            refresh    = RefreshToken.for_user(user)

            return Response({
                'tipo_sessao': 'principal',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {'id': utilizador.id, 'nome': utilizador.nome, 'email': user.email},
                'tem_lojas': False,
                'lojas': [],
                'pos_existentes': [],
                'precisa_onboarding': True,
                'mensagem': 'Conta criada com sucesso',
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'detail': f'Erro ao criar conta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO POS
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_criar(request):
    utilizador = request.user.utilizador
    nome    = request.data.get('nome', 'POS Principal')
    loja_id = request.data.get('loja_id')
    modo    = request.data.get('modo', 'standalone')

    if modo not in ['standalone', 'integrado', 'hibrido']:
        modo = 'standalone'

    config = ConfiguracaoPOS.objects.create(nome=nome, dono=utilizador, modo='standalone')

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
    modo    = request.data.get('modo', 'integrado')

    if not loja_id:
        return Response({'detail': 'loja_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if modo not in ['integrado', 'hibrido']:
        modo = 'integrado'

    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)


    loja = Loja.objects.filter(
        Q(id=loja_id) & (
            Q(dono=utilizador) |
            Q(staff__utilizador=utilizador, staff__ativo=True)
        )
    ).distinct().first()

    if not loja:
        return Response(
            {'detail': 'Loja não encontrada ou sem permissão.'},
            status=status.HTTP_404_NOT_FOUND
        )

    pos.conectar_loja(loja, modo=modo)
    loja.pos_ativo = True
    loja.save(update_fields=['pos_ativo'])

    return Response({'detail': f'POS conectado à loja {loja.nome}', 'pos': _pos_response(pos)})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_desconectar_loja(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    pos.desconectar_loja()
    return Response({'detail': 'POS desconectado da loja', 'pos': _pos_response(pos)})


# ═══════════════════════════════════════════════════════════════════
# PRODUTOS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_produtos(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id, ativo=True)

    gestao = request.GET.get('gestao') in ['1', 'true', 'True']
    origem = request.GET.get('origem', 'todos')
    q      = request.GET.get('q', '').strip()
    data   = []

    if origem not in ['todos', 'pos', 'loja']:
        origem = 'todos'

    if pos.modo in ['standalone', 'hibrido'] and origem in ['todos', 'pos']:
        qs_pos = ProdutoPOS.objects.filter(pos=pos)
        if not gestao:
            qs_pos = qs_pos.filter(ativo=True, disponivel_pos=True)
        if q:
            qs_pos = qs_pos.filter(
                Q(nome__icontains=q) | Q(descricao__icontains=q) | Q(categoria__icontains=q)
            )
        data.extend([_produto_pos_payload(p, request) for p in qs_pos])

    if pos.modo in ['integrado', 'hibrido'] and pos.loja_vinculada and origem in ['todos', 'loja']:
        qs_loja = Produto.objects.filter(loja=pos.loja_vinculada)
        if not gestao:
            qs_loja = qs_loja.filter(ativo=True, disponivel_pos=True)
        if q:
            qs_loja = qs_loja.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))
        data.extend([_produto_loja_payload(p, request) for p in qs_loja])

    return Response({
        'results': data,
        'count': len(data),
        'modo': pos.modo,
        'origem': origem,
        'loja_vinculada': {
            'id': pos.loja_vinculada.id, 'nome': pos.loja_vinculada.nome
        } if pos.loja_vinculada else None
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def produto_criar(request, pos_id):
    pos, membro, utilizador = _resolve_pos_request(request, pos_id, ativo=True)

    # Membros precisam de permissão explícita
    if membro and not membro.pode_gerir_produtos:
        return Response(
            {'detail': 'Sem permissão para gerir produtos.'},
            status=status.HTTP_403_FORBIDDEN
        )

    origem         = request.data.get('origem') or ('loja' if pos.modo == 'integrado' else 'pos')
    nome           = (request.data.get('nome') or '').strip()
    descricao      = request.data.get('descricao', '')
    categoria      = (request.data.get('categoria') or 'Sem categoria').strip() or 'Sem categoria'
    preco          = request.data.get('preco')
    imagem         = request.FILES.get('imagem') or request.FILES.get('ficheiro')
    ativo          = _str_to_bool(request.data.get('ativo'), True)
    disponivel_pos = _str_to_bool(request.data.get('disponivel_pos'), True)
    controlar_stock = _str_to_bool(request.data.get('controlar_stock'), False)
    stock          = int(request.data.get('stock', 0) or 0)

    if not nome or preco is None:
        return Response({'detail': 'Nome e preço são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    if origem == 'pos':
        if pos.modo not in ['standalone', 'hibrido']:
            return Response({'detail': 'Este POS não permite produtos próprios.'}, status=status.HTTP_400_BAD_REQUEST)

        produto = ProdutoPOS.objects.create(
            pos=pos, nome=nome, descricao=descricao, categoria=categoria,
            preco=Decimal(str(preco)), imagem=imagem, controlar_stock=controlar_stock,
            stock=stock, ativo=ativo, disponivel_pos=disponivel_pos
        )
        return Response(_produto_pos_payload(produto, request), status=status.HTTP_201_CREATED)

    if origem == 'loja':
        # Membros não podem criar produtos na loja Bendi —
        # isso afecta o catálogo público online, responsabilidade do dono
        if membro:
            return Response(
                {'detail': 'Membros só podem criar produtos próprios do POS, não da loja Bendi.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'POS precisa estar integrado ou híbrido.'}, status=status.HTTP_400_BAD_REQUEST)

        loja = pos.loja_vinculada
        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response({'detail': 'Sem permissão para gerir produtos desta loja.'}, status=status.HTTP_403_FORBIDDEN)

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
                return Response({'atributos': f'Campos obrigatórios em falta: {em_falta}'}, status=status.HTTP_400_BAD_REQUEST)

        produto = Produto.objects.create(
            loja=loja, tipo=tipo, nome=nome, descricao=descricao,
            preco=Decimal(str(preco)), sku=request.data.get('sku', ''),
            ficheiro=imagem, atributos=atributos or {},
            destaque=_str_to_bool(request.data.get('destaque'), False),
            ativo=ativo, disponivel_pos=disponivel_pos,
        )
        _aplicar_categorias_loja(produto, request)
        _set_stock_loja(produto, stock)
        return Response(_produto_loja_payload(produto, request), status=status.HTTP_201_CREATED)

    return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([POSAuthentication])   # ← substituir IsAuthenticated
@permission_classes([IsPOSAuthenticated])       # ← substituir IsAuthenticated
@transaction.atomic
def produto_atualizar(request, pos_id, produto_id):
    # ← substituir as duas primeiras linhas por isto:
    pos, membro, utilizador = _resolve_pos_request(request, pos_id, ativo=True)

    # Membros precisam de permissão explícita
    if membro and not membro.pode_gerir_produtos:
        return Response(
            {'detail': 'Sem permissão para gerir produtos.'},
            status=status.HTTP_403_FORBIDDEN
        )

    origem = request.data.get('origem') or request.GET.get('origem') or 'pos'

    if origem == 'pos':
        produto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos)
        if pos.modo not in ['standalone', 'hibrido']:
            return Response({'detail': 'Este POS não permite produtos próprios.'}, status=status.HTTP_400_BAD_REQUEST)

        for campo, attr in [('nome','nome'),('descricao','descricao'),('categoria','categoria'),('preco',None),
                             ('controlar_stock',None),('stock',None),('ativo',None),('disponivel_pos',None)]:
            if campo not in request.data:
                continue
            if campo == 'categoria':
                produto.categoria = request.data['categoria'] or 'Sem categoria'
            elif campo == 'preco':
                produto.preco = Decimal(str(request.data['preco']))
            elif campo in ('controlar_stock', 'ativo', 'disponivel_pos'):
                setattr(produto, campo, _str_to_bool(request.data.get(campo), getattr(produto, campo)))
            elif campo == 'stock':
                produto.stock = int(request.data.get('stock') or 0)
            else:
                setattr(produto, campo, request.data[campo])

        imagem = request.FILES.get('imagem') or request.FILES.get('ficheiro')
        if imagem:
            produto.imagem = imagem
        produto.save()
        return Response(_produto_pos_payload(produto, request))

    if origem == 'loja':
        # Membros não gerem produtos da loja Bendi directamente
        if membro:
            return Response(
                {'detail': 'Membros não podem gerir produtos da loja Bendi.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja.'}, status=status.HTTP_400_BAD_REQUEST)

        loja = pos.loja_vinculada
        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response({'detail': 'Sem permissão para gerir produtos desta loja.'}, status=status.HTTP_403_FORBIDDEN)

        produto = get_object_or_404(Produto, id=produto_id, loja=loja)

        for campo in ('nome', 'descricao', 'sku'):
            if campo in request.data:
                setattr(produto, campo, request.data[campo])
        if 'preco' in request.data:
            produto.preco = Decimal(str(request.data['preco']))
        for campo in ('ativo', 'disponivel_pos', 'destaque'):
            if campo in request.data:
                setattr(produto, campo, _str_to_bool(request.data.get(campo), getattr(produto, campo)))
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
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def produto_apagar(request, pos_id, produto_id):
    pos, membro, utilizador = _resolve_pos_request(request, pos_id, ativo=True)
    if membro and not membro.pode_gerir_produtos:
        return Response({'detail': 'Sem permissão.'}, status=403)
    origem = request.GET.get('origem') or request.data.get('origem') or 'pos'

    if origem == 'pos':
        produto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos)
        produto.ativo = False
        produto.save(update_fields=['ativo'])
        return Response({'detail': 'Produto POS desativado.', 'produto': _produto_pos_payload(produto, request)})

    if origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja.'}, status=status.HTTP_400_BAD_REQUEST)
        loja = pos.loja_vinculada
        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response({'detail': 'Sem permissão para gerir produtos desta loja.'}, status=status.HTTP_403_FORBIDDEN)
        produto = get_object_or_404(Produto, id=produto_id, loja=loja)
        produto.ativo = False
        produto.save(update_fields=['ativo'])
        return Response({'detail': 'Produto da loja desativado.', 'produto': _produto_loja_payload(produto, request)})

    return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
# MESAS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def mesas_listar(request, pos_id):
    pos, membro = _get_pos_for_request(request, pos_id)
    mesas = Mesa.objects.filter(pos=pos, ativa=True).order_by('numero')

    return Response([
        {
            'id': m.id,
            'numero': m.numero,
            'capacidade': m.capacidade,
            'status': m.status,
            'atendente_atual': {'id': m.atendente_atual.id, 'nome': m.atendente_atual.nome} if m.atendente_atual else None,
            'aberta_em': m.aberta_em,
            'tem_conta_aberta': ContaMesa.objects.filter(mesa=m, status='aberta').exists(),
        }
        for m in mesas
    ])


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def mesa_criar(request, pos_id):
    pos, membro = _get_pos_for_request(request, pos_id)
    if membro and not membro.pode_gerir_mesas:
        return Response({'detail': 'Sem permissão para criar mesas.'}, status=status.HTTP_403_FORBIDDEN)

    numero     = request.data.get('numero')
    capacidade = request.data.get('capacidade', 4)

    if not numero:
        return Response({'detail': 'Número da mesa é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
    if Mesa.objects.filter(pos=pos, numero=numero).exists():
        return Response({'detail': 'Já existe uma mesa com este número'}, status=status.HTTP_400_BAD_REQUEST)

    mesa = Mesa.objects.create(pos=pos, numero=numero, capacidade=capacidade)
    return Response({'id': mesa.id, 'numero': mesa.numero, 'capacidade': mesa.capacidade, 'status': mesa.status}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def mesa_abrir(request, pos_id, mesa_id):
    pos, membro = _get_pos_for_request(request, pos_id)
    if membro and not membro.pode_abrir_mesas:
        return Response({'detail': 'Sem permissão para abrir mesas.'}, status=status.HTTP_403_FORBIDDEN)

    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)

    conta_existente = ContaMesa.objects.filter(mesa=mesa, status='aberta').first()
    if conta_existente:
        return Response({
            'detail': 'Mesa já tem conta aberta',
            'mesa': MesaSerializer(mesa, context={'request': request}).data,
            'conta_id': conta_existente.id,
            'conta': ContaMesaSerializer(conta_existente, context={'request': request}).data,
        })

    if mesa.status == 'livre':
        mesa.abrir(None if membro else request.user.utilizador)

    conta = ContaMesa.objects.create(
        pos=pos,
        mesa=mesa,
        atendente=None if membro else request.user.utilizador,
        taxa_servico_percentagem=pos.taxa_servico_percentagem if pos.taxa_servico_ativa else Decimal('0.00')
    )

    return Response({
        'detail': 'Mesa aberta com sucesso',
        'mesa': MesaSerializer(mesa, context={'request': request}).data,
        'conta_id': conta.id,
    })


@api_view(['DELETE'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def mesa_apagar(request, pos_id, mesa_id):
    pos, membro = _get_pos_for_request(request, pos_id)
    if membro and not membro.pode_gerir_mesas:
        return Response({'detail': 'Sem permissão para apagar mesas.'}, status=status.HTTP_403_FORBIDDEN)

    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)

    if ContaMesa.objects.filter(mesa=mesa, status='aberta').exists():
        return Response({'detail': 'Não é possível apagar mesa com conta aberta'}, status=status.HTTP_400_BAD_REQUEST)

    mesa.delete()
    return Response({'detail': 'Mesa apagada com sucesso'})


# ═══════════════════════════════════════════════════════════════════
# CONTAS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def conta_criar(request, pos_id, mesa_id):
    pos, membro, utilizador = _resolve_pos_request(request, pos_id)
    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)
    conta_aberta = ContaMesa.objects.filter(mesa=mesa, status='aberta').first()

    if request.method == 'GET':
        if not conta_aberta:
            return Response({'detail': 'Esta mesa não tem conta aberta'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_conta_payload(conta_aberta, request))

    if conta_aberta:
        return Response(_conta_payload(conta_aberta, request), status=status.HTTP_200_OK)

    conta = ContaMesa.objects.create(
        pos=pos, mesa=mesa, atendente=utilizador,
        taxa_servico_percentagem=pos.taxa_servico_percentagem if pos.taxa_servico_ativa else Decimal('0.00')
    )
    mesa.abrir(utilizador)
    return Response(_conta_payload(conta, request), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def conta_detalhe(request, pos_id, conta_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    return Response(_conta_payload(conta, request))


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def conta_adicionar_item(request, pos_id, conta_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    produto_id  = request.data.get('produto_id')
    origem      = request.data.get('origem', 'loja')
    quantidade  = int(request.data.get('quantidade', 1) or 1)
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
            conta=conta, produto=None, produto_pos=produto,
            nome=produto.nome, quantidade=quantidade, preco_unitario=produto.preco, observacoes=observacoes
        )
        if produto.controlar_stock:
            produto.stock = max(produto.stock - quantidade, 0)
            produto.save(update_fields=['stock'])

    elif origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja'}, status=status.HTTP_400_BAD_REQUEST)
        produto = get_object_or_404(Produto, id=produto_id, loja=pos.loja_vinculada, ativo=True, disponivel_pos=True)
        item = ItemContaMesa.objects.create(
            conta=conta, produto=produto, produto_pos=None,
            nome=produto.nome, quantidade=quantidade, preco_unitario=produto.preco, observacoes=observacoes
        )
    else:
        return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'detail': 'Item adicionado',
        'item': {
            'id': item.id, 'produto_id': item.produto_ref_id, 'origem': item.origem,
            'nome': item.nome, 'quantidade': item.quantidade, 'preco_total': str(item.preco_total),
        },
        'conta': {'subtotal': str(conta.subtotal), 'total': str(conta.total)},
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def conta_remover_item(request, pos_id, conta_id, item_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    item  = get_object_or_404(ItemContaMesa, id=item_id, conta=conta)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    if item.produto_pos and item.produto_pos.controlar_stock:
        item.produto_pos.stock += item.quantidade
        item.produto_pos.save(update_fields=['stock'])

    item.delete()
    conta.calcular_totais()
    return Response({'detail': 'Item removido', 'conta': {'subtotal': str(conta.subtotal), 'total': str(conta.total)}})


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def conta_fechar(request, pos_id, conta_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    metodo_pagamento = request.data.get('metodo_pagamento')
    nif_cliente      = request.data.get('nif_cliente', '')

    if not metodo_pagamento:
        return Response({'detail': 'metodo_pagamento é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if nif_cliente:
        conta.nif_cliente = nif_cliente
        conta.save(update_fields=['nif_cliente'])

    conta.fechar(metodo_pagamento)
    return Response({
        'detail': 'Conta fechada com sucesso',
        'conta': {'id': conta.id, 'total': str(conta.total), 'metodo_pagamento': conta.metodo_pagamento, 'fechada_em': conta.fechada_em}
    })


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def contas_ativas(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    contas = ContaMesa.objects.filter(pos=pos, status='aberta').select_related('mesa', 'atendente').prefetch_related('items').order_by('-criada_em')
    return Response([_conta_payload(c, request) for c in contas])


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_historico(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)

    contas = ContaMesa.objects.filter(pos=pos, status='fechada').select_related('mesa', 'atendente').prefetch_related('items')

    data_inicio = request.query_params.get('data_inicio')
    data_fim    = request.query_params.get('data_fim')
    metodo      = request.query_params.get('metodo')

    if data_inicio:
        contas = contas.filter(fechada_em__gte=data_inicio)
    if data_fim:
        from datetime import datetime, time as dt_time
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        contas = contas.filter(fechada_em__lte=datetime.combine(data_fim_obj, dt_time(23, 59, 59)))
    if metodo:
        contas = contas.filter(metodo_pagamento=metodo)

    contas = contas.order_by('-fechada_em')
    offset = int(request.query_params.get('offset', 0))
    limit  = int(request.query_params.get('limit', 20))
    total  = contas.count()

    return Response({'count': total, 'results': [_conta_payload(c, request) for c in contas[offset:offset + limit]]})


@api_view(['PATCH'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def item_status_atualizar(request, pos_id, conta_id, item_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    conta       = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    item        = get_object_or_404(ItemContaMesa, id=item_id, conta=conta)
    novo_status = request.data.get('status')

    if novo_status not in ['pendente', 'preparando', 'pronto', 'entregue', 'cancelado']:
        return Response({'detail': 'Status inválido'}, status=status.HTTP_400_BAD_REQUEST)

    item.status = novo_status
    item.save(update_fields=['status', 'atualizado_em'])

    return Response({
        'detail': 'Status atualizado',
        'item': {
            'id': item.id, 'produto_id': item.produto_ref_id, 'origem': item.origem,
            'nome': item.nome, 'quantidade': item.quantidade,
            'preco_unitario': str(item.preco_unitario), 'preco_total': str(item.preco_total),
            'observacoes': item.observacoes, 'status': item.status,
        }
    })


# ═══════════════════════════════════════════════════════════════════
# TURNOS
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def turno_abrir(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    if TurnoPOS.objects.filter(pos=pos, aberto=True).exists():
        return Response({'detail': 'Já existe um turno aberto'}, status=status.HTTP_400_BAD_REQUEST)

    valor_abertura = request.data.get('valor_abertura')
    if valor_abertura is None:
        return Response({'detail': 'valor_abertura é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    turno = TurnoPOS.objects.create(pos=pos, operador=utilizador, valor_abertura=Decimal(str(valor_abertura)))
    return Response({'id': turno.id, 'valor_abertura': str(turno.valor_abertura), 'aberto_em': turno.aberto_em}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def turno_fechar(request, pos_id, turno_id):
    utilizador = request.user.utilizador
    pos   = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    turno = get_object_or_404(TurnoPOS, id=turno_id, pos=pos)

    if not turno.aberto:
        return Response({'detail': 'Turno já está fechado'}, status=status.HTTP_400_BAD_REQUEST)

    valor_fecho = request.data.get('valor_fecho')
    if valor_fecho is None:
        return Response({'detail': 'valor_fecho é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    turno.fechar_turno(Decimal(str(valor_fecho)))
    return Response({
        'id': turno.id, 'valor_abertura': str(turno.valor_abertura),
        'valor_fecho': str(turno.valor_fecho), 'diferenca': str(turno.diferenca), 'fechado_em': turno.fechado_em,
    })


# ═══════════════════════════════════════════════════════════════════
# EQUIPA POS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pos_equipa(request, pos_id):
    """
    GET  → listar membros da equipa
    POST → criar novo membro (nome + username_pos + password? + papel)
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)

    # ── GET ──────────────────────────────────────────────────────────
    if request.method == 'GET':
        membros = UtilizadorPOS.objects.filter(pos=pos).order_by('nome')
        return Response([m.to_dict() for m in membros])

    # ── POST ─────────────────────────────────────────────────────────
    nome     = request.data.get('nome', '').strip()
    username = (request.data.get('username_pos') or '').strip().lower()
    password = request.data.get('password', '').strip()
    papel    = request.data.get('papel', 'empregado')

    if not nome:
        return Response({'detail': 'Nome é obrigatório'}, status=400)
    if not username:
        return Response({'detail': 'Username é obrigatório'}, status=400)
    if len(username) < 3:
        return Response({'detail': 'Username deve ter pelo menos 3 caracteres'}, status=400)
    if not username.replace('_', '').replace('.', '').isalnum():
        return Response({'detail': 'Username só pode conter letras, números, _ e .'}, status=400)
    if papel not in ['gerente', 'empregado', 'cozinha', 'caixa']:
        return Response({'detail': 'Papel inválido'}, status=400)
    if UtilizadorPOS.objects.filter(pos=pos, username_pos__iexact=username).exists():
        return Response({'detail': f'Username "{username}" já existe neste POS'}, status=400)

    password_final = password or User.objects.make_random_password(length=10)

    membro = UtilizadorPOS(pos=pos, nome=nome, username_pos=username, papel=papel)
    membro.set_password(password_final)
    membro.save()

    resp = membro.to_dict()
    if not password:
        resp['password_gerada'] = password_final
        resp['aviso'] = 'Anota esta password — não será mostrada novamente.'
    else:
        resp['aviso'] = 'Membro criado. Passa as credenciais ao colaborador.'

    return Response(resp, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def pos_equipa_membro(request, pos_id, membro_id):
    """
    GET    → detalhe do membro
    PATCH  → editar (nome, username, papel, permissões, password, ativo)
    DELETE → remover membro
    """
    utilizador = request.user.utilizador
    pos    = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)
    membro = get_object_or_404(UtilizadorPOS, id=membro_id, pos=pos)

    if request.method == 'GET':
        return Response(membro.to_dict())

    if request.method == 'PATCH':
        if 'nome' in request.data:
            membro.nome = request.data['nome'].strip()

        if 'username_pos' in request.data:
            novo_username = request.data['username_pos'].strip().lower()
            if (novo_username != membro.username_pos and
                UtilizadorPOS.objects.filter(pos=pos, username_pos__iexact=novo_username).exclude(id=membro.id).exists()):
                return Response({'detail': f'Username "{novo_username}" já existe neste POS'}, status=400)
            membro.username_pos = novo_username

        if 'papel' in request.data:
            membro.papel = request.data['papel']
            membro.aplicar_permissoes_padrao()

        for perm in [
            'pode_abrir_mesas', 'pode_fechar_contas', 'pode_cancelar_items',
            'pode_dar_descontos', 'pode_gerir_produtos', 'pode_gerir_mesas',
            'pode_gerir_utilizadores', 'pode_ver_relatorios', 'pode_abrir_fechar_turno',
            'pode_ver_pedidos', 'pode_atualizar_status_items',
        ]:
            if perm in request.data:
                setattr(membro, perm, bool(request.data[perm]))

        if 'password' in request.data and request.data['password']:
            membro.set_password(request.data['password'])

        if 'ativo' in request.data:
            membro.ativo = bool(request.data['ativo'])

        membro.save()
        return Response(membro.to_dict())

    if request.method == 'DELETE':
        membro.delete()
        return Response({'detail': 'Membro removido.'}, status=204)
    
    
# views.py — adicionar esta função
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pos_verificar_username(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador, ativo=True)
    username = (request.GET.get('username') or '').strip().lower()
    if not username:
        return Response({'disponivel': False, 'sugestoes': []})
    existe = UtilizadorPOS.objects.filter(pos=pos, username_pos__iexact=username).exists()
    if not existe:
        return Response({'disponivel': True, 'sugestoes': []})
    existentes = set(UtilizadorPOS.objects.filter(pos=pos).values_list('username_pos', flat=True))
    sugestoes = []
    for candidato in [f'{username}2', f'{username}3', f'{username}_{pos.id}', f'{username[0:8]}_{len(username)}']:
        if candidato not in existentes and len(sugestoes) < 3:
            sugestoes.append(candidato)
    return Response({'disponivel': False, 'sugestoes': sugestoes})