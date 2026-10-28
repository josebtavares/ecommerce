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
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
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
    Subscricao,
)

try:
    from app.models import Inventario
except Exception:
    Inventario = None
    
from .stock import reservar_stock, repor_stock_item, cancelar_conta, custo_de_venda
from ..utils import conjuntos as conj
from ..utils import faturas_vendas
from ..utils.fiscal import validar_dados_fiscais, aplicar_dados_fiscais, dados_fiscais_payload, ao_ligar_loja, copiar_da_loja, _verdadeiro, fatura_resumo

# prefetch dos componentes dos conjuntos (menus) nas listagens do POS
PREFETCH_CONJUNTO_POS = ('componentes__produto_pos', 'componentes__variante_pos', 'componentes__produto__inventario',
                         'componentes__produto__loja', 'componentes__variante',
                         'grupos__opcoes__produto_pos', 'grupos__opcoes__variante_pos', 'grupos__opcoes__produto__inventario',
                         'grupos__opcoes__produto__loja', 'grupos__opcoes__variante',
                         'componentes__produto_pos__variantes', 'componentes__produto__variantes',
                         'grupos__opcoes__produto_pos__variantes', 'grupos__opcoes__produto__variantes')
PREFETCH_CONJUNTO_LOJA = ('componentes__produto__inventario', 'componentes__variante',
                          'grupos__opcoes__produto__inventario', 'grupos__opcoes__variante',
                          'componentes__produto__variantes', 'grupos__opcoes__produto__variantes')
from app.utils.auth import autenticar
from app.utils.dinheiro import ler_valor, formatar as formatar_dinheiro
from app.utils.google_auth import google_obter_utilizador
from app.utils.password import mensagem_password_fraca
from app.utils.contas import username_livre
from app.Views.utilizadorView import _build_user_payload
from app.utils.variantes import sincronizar_variantes, variantes_payload, aplicar_grelha_do_pedido
from app.utils.tipos import tipos_para_loja, tipos_para_pos, tipo_permitido
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
from rest_framework.exceptions import PermissionDenied

# lojas que um POS pode usar: aprovadas pela plataforma (uma loja fechada pelo dono continua a
# poder vender ao balcão; pendentes e suspensas não)
LOJAS_VINCULAVEIS = ('ativa', 'fechada')

 
 
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


def _resolve_pos_request(request, pos_id, require_owner=False, ativo=False, permitir_suspenso=False):
    """
    Retorna o POS acessível pelo request de conta principal ou membro de equipa.
    permitir_suspenso: o Histórico e as faturas das vendas já feitas continuam abertos num POS suspenso
    (a obrigação fiscal não pára com a suspensão; o que se bloqueia é vender).
    """
    membro = get_membro_from_request(request)

    if membro:
        query = ConfiguracaoPOS.objects.filter(id=pos_id)
        if ativo:
            query = query.filter(ativo=True)
        pos = get_object_or_404(query)
        if pos.id != membro.pos.id or require_owner:
            raise Http404()
        if not permitir_suspenso:
            _bloquear_se_suspenso(pos)
        return pos, membro, None

    utilizador = request.user.utilizador
    query = ConfiguracaoPOS.objects.filter(id=pos_id, dono=utilizador)
    if ativo:
        query = query.filter(ativo=True)
    pos = get_object_or_404(query)
    if not permitir_suspenso:
        _bloquear_se_suspenso(pos)
    return pos, None, utilizador


def _sem_permissao(membro, flag, msg):
    """Membro da equipa sem a permissão → 403 (a conta principal pode tudo). O frontend já escondia
    estes botões, mas o servidor não verificava: bastava chamar a API."""
    if membro and not getattr(membro, flag, False):
        return Response({'detail': msg}, status=status.HTTP_403_FORBIDDEN)
    return None


def _quem(membro, utilizador):
    """Nome de quem faz a operação (membro da equipa ou conta principal), guardado nos registos."""
    pessoa = membro or utilizador
    return pessoa.nome[:100] if pessoa else ''


def _cancelar_item(item, por, motivo=''):
    """Artigo cancelado/retirado: repõe o stock e fica na conta (não cobrado) com quem, quando e porquê."""
    repor_stock_item(item)
    item.status = 'cancelado'
    item.cancelado_em = timezone.now()
    item.cancelado_por = (por or '')[:100]
    item.motivo_cancelamento = (motivo or '')[:200]
    item.save(update_fields=['status', 'cancelado_em', 'cancelado_por', 'motivo_cancelamento', 'atualizado_em'])


def _loja_suspensa(pos):
    """
    Loja vinculada suspensa pela plataforma → os produtos dela não se vendem no POS (os
    próprios do POS sim). A ligação mantém-se: ao reactivar a loja, voltam sozinhos.
    Uma loja FECHADA pelo dono não conta — fechar a loja online não fecha o balcão.
    """
    return bool(pos.loja_vinculada_id) and pos.loja_vinculada.estado == 'suspensa'


def _bloquear_se_suspenso(pos):
    """POS suspenso pela plataforma não opera — 403 com o motivo."""
    if pos.suspenso:
        motivo = f' Motivo: {pos.suspenso_motivo}' if pos.suspenso_motivo else ''
        raise PermissionDenied(f'Este POS está suspenso pela plataforma.{motivo} Contacta o suporte.')


def _get_pos_for_request(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id, ativo=False)
    return pos, membro


def _set_stock_loja(produto, stock):
    if Inventario is None:
        return
    # com stock por variação o total é a soma das variantes — gerido no backoffice
    if getattr(produto, 'stock_por_variante', False):
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


def _opcoes_extra_texto(item):
    variante = item.variante_pos or item.variante
    ja_no_nome = set((variante.combinacao or {}).keys()) if variante else set()
    partes = []
    for k, v in (item.atributos or {}).items():
        if k in ja_no_nome or v in (None, '', []):
            continue
        partes.append(f'{k}: {", ".join(map(str, v)) if isinstance(v, list) else v}')
    return ' · '.join(partes)


def _ler_atributos(request, chave='atributos'):
    """Lê atributos (JSON em string no multipart, ou dict). Devolve (dict, None) ou (None, Response)."""
    raw = request.data.get(chave)
    if raw in (None, ''):
        return {}, None
    try:
        valor = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return None, Response({'atributos': 'JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(valor, dict):
        return None, Response({'atributos': 'Os atributos devem ser um objecto.'}, status=status.HTTP_400_BAD_REQUEST)
    return valor, None


def _tipo_payload(tipo):
    if not tipo:
        return None
    return {
        'id': tipo.id, 'nome': tipo.nome,
        'atributos_schema': tipo.atributos_schema or [],
        'is_global': tipo.is_global,
    }


def _conjunto_payload(produto, request, pos):
    """Campos de conjunto (menu) para o POS — disponibilidade vista a partir deste POS."""
    if not produto.e_conjunto:
        return {'e_conjunto': False, 'componentes': [], 'conjunto': None, 'grupos': []}
    d = conj.disponibilidade(produto, pos)
    return {
        'e_conjunto': True,
        # sem stock próprio: quantos menus se podem vender com o stock dos componentes
        'stock': d['quantidade'],
        'controlar_stock': d['quantidade'] is not None,
        'disponivel': bool(produto.ativo and produto.disponivel_pos and d['disponivel']),
        'componentes': conj.componentes_payload(produto, request, pos),
        'grupos': conj.grupos_payload(produto, request, pos),
        'conjunto': {'disponivel': d['disponivel'], 'quantidade': d['quantidade'], 'motivo': d['motivo'],
                     'componente_id': d['componente_id'],
                     'preco_componentes': str(conj.preco_componentes(produto))},
    }


def _produto_pos_payload(produto, request=None, pos=None):
    return {
        'uid': f'pos-{produto.id}',
        'id': produto.id,
        'origem': 'pos',
        'nome': produto.nome,
        'descricao': produto.descricao,
        'preco': str(produto.preco),
        'preco_custo': str(produto.preco_custo) if produto.preco_custo is not None else None,
        'categoria': produto.categoria or 'Sem categoria',
        'categorias': [{'id': None, 'nome': produto.categoria or 'Sem categoria'}],
        'tipo': _tipo_payload(produto.tipo),
        'tipo_id': produto.tipo_id,
        'atributos': produto.atributos or {},
        **variantes_payload(produto),
        'imagem_url': _build_absolute_url(request, produto.imagem),
        'stock': produto.stock,
        'controlar_stock': produto.controlar_stock,
        'ativo': produto.ativo,
        'disponivel_pos': produto.disponivel_pos,
        'disponivel': produto.disponivel,
        'loja': None,
        'pos_id': produto.pos_id,
        **_conjunto_payload(produto, request, pos or produto.pos),
        'criado_em': produto.criado_em,
        'atualizado_em': produto.atualizado_em,
    }


def _produto_loja_payload(produto, request=None, pos=None):
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
        'tipo': _tipo_payload(produto.tipo),
        'tipo_id': produto.tipo_id,
        'atributos': produto.atributos or {},
        **variantes_payload(produto),
        'imagem_url': _build_absolute_url(request, ficheiro),
        'stock': stock,
        'controlar_stock': stock is not None,
        'ativo': ativo,
        'disponivel_pos': disponivel_pos,
        'disponivel': bool(ativo and disponivel_pos and (stock is None or stock > 0)),
        'loja': {'id': produto.loja.id, 'nome': produto.loja.nome},
        'loja_id': produto.loja_id,
        'data_criacao': produto.data_criacao,
        **_conjunto_payload(produto, request, pos),
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
            'estado': pos.loja_vinculada.estado,
        } if pos.loja_vinculada else None,
        'loja_suspensa': _loja_suspensa(pos),
        'efatura_ativo': pos.efatura_ativo,
        'percentagem_iva': str(pos.percentagem_iva),
        'suspenso': pos.suspenso,
        'suspenso_motivo': pos.suspenso_motivo,
        'criado_em': pos.criado_em,
        'fiscal': dados_fiscais_payload(pos, detalhe=True),     # só vai para o dono (todos os usos são do dono)
    }


def _verificar_permissao_loja_produtos(loja, utilizador):
    if loja.dono_id == utilizador.id:
        return True
    try:
        return UtilizadorLoja.verificar_permissao(loja, utilizador, 'gerir_produtos')
    except Exception:
        return False


def _conta_payload(conta, request=None):
    items = ItemContaMesa.objects.filter(conta=conta).select_related('produto', 'produto_pos', 'variante', 'variante_pos')
    return {
        'id': conta.id,
        'mesa': {'id': conta.mesa.id, 'numero': conta.mesa.numero},
        'atendente': {
            'id': conta.atendente.id,
            'nome': conta.atendente.nome
        } if conta.atendente else ({'id': None, 'nome': conta.atendente_nome} if conta.atendente_nome else None),
        'status': conta.status,
        'subtotal': str(conta.subtotal),
        'taxa_servico_percentagem': str(conta.taxa_servico_percentagem),
        'taxa_servico_valor': str(conta.taxa_servico_valor),
        'gorjeta': str(conta.gorjeta),
        'desconto_valor': str(conta.desconto_valor),
        'desconto_motivo': conta.desconto_motivo,
        'desconto_por': conta.desconto_por,
        'total': str(conta.total),
        'metodo_pagamento': conta.metodo_pagamento,
        'partes': [{'pessoa': p.pessoa_numero, 'valor': str(p.valor), 'metodo': p.metodo}
                   for p in conta.pagamentos_divididos.all()] if conta.metodo_pagamento == 'dividida' else [],
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
                'atributos': item.atributos or {},
                # opções que não são a variação (já no nome), ex.: "gelo: não" — útil para a cozinha
                'opcoes_texto': _opcoes_extra_texto(item),
                # menu: o que leva (para a cozinha e para a conta)
                'componentes': item.componentes or [],
                'cancelado_em': item.cancelado_em,
                'cancelado_por': item.cancelado_por,
                'motivo_cancelamento': item.motivo_cancelamento,
            }
            for item in items
        ],
        'criada_em': conta.criada_em,
        'fechada_em': conta.fechada_em,
        'fechada_por': conta.fechada_por,
        # fatura que o POS emitiu no e-Fatura e registou aqui (Histórico); faturável = fechada com total > 0
        'nif_cliente': conta.nif_cliente,
        'referencia': f'V-{conta.id}',
        'fatura': fatura_resumo(conta, request),
        'faturavel': conta.status == 'fechada' and conta.total > 0,
        'arquivo': faturas_vendas.arquivo_conta(conta),
    }


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — CONTA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def _sessao_principal(utilizador, request):
    """Resposta de sessão da conta principal (dono) — login, registo e Google."""
    pos_list = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True).select_related('loja_vinculada')
    lojas    = Loja.objects.filter(dono=utilizador, estado__in=LOJAS_VINCULAVEIS)
    refresh  = RefreshToken.for_user(utilizador.user)

    return {
        'tipo_sessao': 'principal',
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        # mesmo formato do login da Bendi — o frontend guarda isto em localStorage('user'),
        # partilhado com a loja/admin (role_admin, is_staff…); um formato reduzido estragava a sessão Bendi
        'user': {**_build_user_payload(utilizador, request), 'nome': utilizador.nome},
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
    }


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

    user, erro, codigo = autenticar(request, email, password)
    if erro:
        return Response({'detail': erro}, status=codigo)

    try:
        utilizador = user.utilizador
    except Exception:
        return Response({'detail': 'Perfil não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # conta suspensa/banida: antes entrava e só os pedidos seguintes falhavam
    from app.autenticacao import conta_ativa
    if not conta_ativa(user):
        from app.utils.moderacao import mensagem_bloqueio
        return Response({'detail': mensagem_bloqueio(utilizador), 'code': 'conta_inativa'}, status=status.HTTP_403_FORBIDDEN)
    utilizador.refresh_from_db(fields=['status', 'suspenso_ate', 'motivo_estado'])
    return Response(_sessao_principal(utilizador, request))


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@pos_ratelimit(key='ip', rate='10/m')
def pos_login_google(request):
    """
    Login/registo da conta principal com Google — o mesmo fluxo da Bendi
    (utils/google_auth), mas devolve a sessão do POS. Body: { code }
    """
    utilizador, criado, erro = google_obter_utilizador(request.data.get('code'))
    if erro:
        return erro
    return Response({**_sessao_principal(utilizador, request), 'criado': criado})


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

    # limite por username (além do por IP): trava adivinhar a password de um empregado a partir de vários IPs
    if is_ratelimited(request=request, group='pos_membro_username', key=lambda g, r: username,
                      rate='20/h', method='POST', increment=True):
        return Response({'detail': 'Demasiadas tentativas. Aguarda um momento antes de tentar novamente.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)

    membros = UtilizadorPOS.objects.filter(username_pos__iexact=username, ativo=True).select_related('pos')
    if pos_id:
        membros = membros.filter(pos_id=pos_id)

    # a password é verificada ANTES de dizer seja o que for: antes respondia "Utilizador não encontrado"
    # (dava para descobrir usernames) e listava os POS de um username sem password
    candidatos = [m for m in membros if m.check_password(password)]
    if not candidatos:
        return Response({'detail': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    # o mesmo username (e password) em vários POS → pedir escolha
    if len(candidatos) > 1:
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
                    for m in candidatos
                ]
            },
            status=status.HTTP_200_OK
        )

    membro = candidatos[0]

    if membro.pos.suspenso:
        return Response({'detail': 'Este POS está suspenso pela plataforma. Fala com o responsável do POS.'},
                        status=status.HTTP_403_FORBIDDEN)

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

    # Email já existe → tentar login
    try:
        existing_user = User.objects.get(email__iexact=email)
        user = authenticate(request, username=existing_user.username, password=password)

        if not user:
            return Response(
                {'detail': 'Email já registado com password diferente. Usa Login.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            **_sessao_principal(user.utilizador, request),
            'mensagem': 'Login com conta existente',
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        pass

    # conta nova: as mesmas regras de password do registo da Bendi (utils/password.py)
    msg = mensagem_password_fraca(password)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

    # Criar nova conta
    username = username_livre(email.split('@')[0])

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name,
            )
            utilizador = Utilizador.objects.create(user=user, status='ativo', verificado=False)

            return Response({
                **_sessao_principal(utilizador, request),
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pos_meus(request):
    """
    GET /api/pos/meus/
    POS da conta autenticada (fonte de verdade para o dashboard — não depende
    do que o login do POS guardou no browser). Inclui as lojas para o onboarding.
    """
    try:
        utilizador = request.user.utilizador
    except Exception:
        return Response({'detail': 'Sessão de membro não tem POS próprios.'}, status=status.HTTP_403_FORBIDDEN)
    pos_list = ConfiguracaoPOS.objects.filter(dono=utilizador, ativo=True).select_related('loja_vinculada').order_by('criado_em')
    lojas = Loja.objects.filter(dono=utilizador, estado__in=LOJAS_VINCULAVEIS)
    return Response({
        'pos': [_pos_response(p) for p in pos_list],
        'lojas': [{'id': l.id, 'nome': l.nome, 'categoria': l.categoria} for l in lojas],
        'user': {'id': utilizador.id, 'nome': utilizador.nome, 'email': request.user.email,
                 'username': request.user.username},
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_criar(request):
    utilizador = request.user.utilizador
    nome    = request.data.get('nome', 'POS Principal')
    loja_id = request.data.get('loja_id')
    modo    = request.data.get('modo', 'standalone')

    if modo not in ['standalone', 'integrado', 'hibrido']:
        modo = 'standalone'

    # o plano do POS (subscrição) — obrigatório quando há planos de POS; sem planos, escolhe depois.
    # Ligado a uma loja com o plano Loja + POS, não precisa: está incluído no plano da loja.
    from ..utils import subscricoes as subs
    from ..utils import subscricoes_pos as subs_pos
    loja = None
    if loja_id:
        loja = get_object_or_404(Loja, id=loja_id, dono=utilizador, estado__in=LOJAS_VINCULAVEIS)
    sub_loja = Subscricao.objects.select_related('loja', 'plano').filter(loja=loja).first() if loja else None
    incluido = subs_pos.loja_cobre_pos(sub_loja)
    plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('pos',))      # opcional se incluído
    if subs.planos_ativos(('pos',)) and not incluido and not plano:
        return Response({'detail': 'Escolhe um plano para o POS.'}, status=status.HTTP_400_BAD_REQUEST)

    # dados fiscais obrigatórios; ligado a uma loja que já os tem, pode usar os da loja
    fiscais, erros = validar_dados_fiscais(request.data)
    da_loja = bool(erros and loja and loja.nif and loja.regime_fiscal and loja.dados_fiscais_aceites_em
                   and not request.data.get('nif'))
    if da_loja:
        fiscais, erros = None, {}
    if erros:
        return Response({'detail': next(iter(erros.values())), 'erros': erros}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # uma conta, um POS (a equipa entra nesse POS com os seus logins)
        Utilizador.objects.select_for_update().get(pk=utilizador.pk)
        if ConfiguracaoPOS.objects.filter(dono=utilizador).exists():
            return Response({'detail': 'Esta conta já tem um POS.'}, status=status.HTTP_400_BAD_REQUEST)
        config = ConfiguracaoPOS.objects.create(nome=nome, dono=utilizador, modo='standalone')
        if fiscais:
            aplicar_dados_fiscais(config, fiscais, request.user)
        if loja:
            config.conectar_loja(loja, modo='hibrido' if modo == 'hibrido' else 'integrado')
            ao_ligar_loja(config, request.user)      # sem NIF próprio (ou o mesmo) → segue a loja
        subs_pos.criar_para_pos_novo(config, plano)

    return Response(_pos_response(config), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def pos_detalhe(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)

    # GET continua a funcionar num POS suspenso (o dashboard mostra o aviso); alterar não
    if request.method == 'PATCH':
        _bloquear_se_suspenso(pos)
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

        if 'percentagem_iva' in request.data:
            iva, erro = ler_valor(request.data['percentagem_iva'], 'A taxa de IVA')
            if erro or iva > 100:
                return Response({'detail': erro or 'A taxa de IVA vai de 0 a 100%.'}, status=status.HTTP_400_BAD_REQUEST)
            pos.percentagem_iva = iva

        pos.save()
        return Response(_pos_response(pos))

    return Response(_pos_response(pos))


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def pos_dados_fiscais(request, pos_id):
    """PATCH /api/pos/<pos_id>/fiscal/  Body: { nif, regime_fiscal, declaracao_fiscal } — só o dono.
    Ligado a uma loja: { da_loja: true } passa a usar os dados dela; gravar dados próprios deixa de os seguir."""
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=request.user.utilizador)
    if _verdadeiro(request.data.get('da_loja')):
        if not pos.loja_vinculada_id:
            return Response({'detail': 'O POS não está ligado a nenhuma loja.'}, status=status.HTTP_400_BAD_REQUEST)
        pos.fiscal_da_loja = True
        pos.save(update_fields=['fiscal_da_loja'])
        copiar_da_loja(pos, request.user)
        return Response(_pos_response(pos))
    fiscais, erros = validar_dados_fiscais(request.data)
    if erros:
        return Response({'detail': next(iter(erros.values())), 'erros': erros}, status=status.HTTP_400_BAD_REQUEST)
    if pos.fiscal_da_loja:
        pos.fiscal_da_loja = False
        pos.save(update_fields=['fiscal_da_loja'])
    aplicar_dados_fiscais(pos, fiscais, request.user)
    return Response(_pos_response(pos))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_conectar_loja(request, pos_id):
    utilizador = request.user.utilizador
    loja_id = request.data.get('loja_id')
    modo    = request.data.get('modo', 'integrado')

    if not loja_id:
        return Response({'detail': 'loja_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    # standalone é sem loja (desconectar-loja); antes caía em silêncio para integrado
    if modo not in ['integrado', 'hibrido']:
        return Response({'detail': 'Com loja, o modo é integrado ou híbrido. Para standalone, desliga a loja.'},
                        status=status.HTTP_400_BAD_REQUEST)

    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    _bloquear_se_suspenso(pos)


    # só o dono, como ao criar o POS com loja — um membro do staff (até condutor ou
    # contabilista) não pode ligar o POS dele à loja e vender/mexer no stock dela
    loja = Loja.objects.filter(
        id=loja_id, estado__in=LOJAS_VINCULAVEIS, dono=utilizador
    ).first()

    if not loja:
        return Response(
            {'detail': 'Loja não encontrada ou sem permissão.'},
            status=status.HTTP_404_NOT_FOUND
        )

    pos.conectar_loja(loja, modo=modo)
    ao_ligar_loja(pos, request.user)
    from ..utils.subscricoes_pos import sincronizar_pos
    sincronizar_pos(pos)          # a loja tem o plano Loja + POS → o POS passa a estar incluído
    loja.pos_ativo = True
    loja.save(update_fields=['pos_ativo'])

    return Response({'detail': f'POS conectado à loja {loja.nome}', 'pos': _pos_response(pos)})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_desconectar_loja(request, pos_id):
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    _bloquear_se_suspenso(pos)
    pos.desconectar_loja()
    from ..utils.subscricoes_pos import sincronizar_pos
    sincronizar_pos(pos)          # saiu do plano Loja + POS da loja → 30 dias até ao seu plano
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
        qs_pos = ProdutoPOS.objects.select_related('tipo').prefetch_related('variantes', *PREFETCH_CONJUNTO_POS).filter(pos=pos)
        if not gestao:
            qs_pos = qs_pos.filter(ativo=True, disponivel_pos=True)
        if q:
            qs_pos = qs_pos.filter(
                Q(nome__icontains=q) | Q(descricao__icontains=q) | Q(categoria__icontains=q)
            )
        data.extend([_produto_pos_payload(p, request, pos) for p in qs_pos])

    # loja suspensa: os produtos dela saem da venda (na gestão continuam, como no backoffice)
    loja_suspensa = _loja_suspensa(pos)
    if (pos.modo in ['integrado', 'hibrido'] and pos.loja_vinculada and origem in ['todos', 'loja']
            and (gestao or not loja_suspensa)):
        qs_loja = (Produto.objects.select_related('tipo', 'loja', 'inventario')
                   .prefetch_related('variantes', 'categorias', *PREFETCH_CONJUNTO_LOJA).filter(loja=pos.loja_vinculada))
        if not gestao:
            qs_loja = qs_loja.filter(ativo=True, disponivel_pos=True)
        if q:
            qs_loja = qs_loja.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))
        data.extend([_produto_loja_payload(p, request, pos) for p in qs_loja])

    return Response({
        'results': data,
        'count': len(data),
        'modo': pos.modo,
        'origem': origem,
        'loja_vinculada': {
            'id': pos.loja_vinculada.id, 'nome': pos.loja_vinculada.nome
        } if pos.loja_vinculada else None,
        'loja_suspensa': loja_suspensa,
    })


def _aplicar_conjunto_pos(produto, dados, pos):
    """
    Conjunto (menu) do POS: liga/desliga e guarda os componentes (produtos do POS e, num POS
    híbrido, da loja Bendi). Devolve a mensagem de erro ou None (quem chama faz o rollback).
    """
    from ..Views.produtoView import _quer_conjunto
    quer = _quer_conjunto(dados, produto.e_conjunto)
    linhas, erro = conj.ler_componentes(dados)
    if erro:
        return erro
    if not quer:
        if produto.e_conjunto:
            produto.componentes.all().delete()
            produto.grupos.all().delete()
            produto.e_conjunto = False
            produto.save(update_fields=['e_conjunto'])
        return None
    if not produto.e_conjunto:
        usado = conj.conjuntos_que_usam(produto)
        if usado:
            return (f'"{produto.nome}" faz parte de {", ".join(usado)} — '
                    f'um produto dentro de um conjunto não pode ser ele próprio um conjunto.')
        if produto.stock_por_variante:
            return 'Este produto tem stock por variação — um conjunto não tem stock próprio. Cria um produto novo para o menu.'
        if linhas is None and 'grupos' not in dados:
            return 'Escolhe os produtos que fazem parte do menu.'
        # sem stock próprio: o stock é o dos componentes
        produto.e_conjunto, produto.controlar_stock, produto.stock = True, False, 0
        produto.save(update_fields=['e_conjunto', 'controlar_stock', 'stock'])
    erro = conj.aplicar_formulario(produto, dados, conj.resolver_pos(pos))
    if erro:
        return erro
    if produto.controlar_stock or produto.stock:
        # um formulário antigo pode ter mandado stock — o menu continua sem stock próprio
        produto.controlar_stock, produto.stock = False, 0
        produto.save(update_fields=['controlar_stock', 'stock'])
    return None


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
    preco, erro_preco = ler_valor(preco, 'O preço')
    if erro_preco:
        return Response({'detail': erro_preco}, status=status.HTTP_400_BAD_REQUEST)
    preco_custo, erro_custo = ler_valor(request.data.get('preco_custo'), 'O preço de custo', obrigatorio=False)
    if erro_custo:
        return Response({'detail': erro_custo}, status=status.HTTP_400_BAD_REQUEST)

    atributos, erro_attr = _ler_atributos(request)
    if erro_attr:
        return erro_attr

    if origem == 'pos':
        if pos.modo not in ['standalone', 'hibrido']:
            return Response({'detail': 'Este POS não permite produtos próprios.'}, status=status.HTTP_400_BAD_REQUEST)

        # produtos próprios do POS: tipos globais + tipos do POS
        tipo = tipo_permitido(tipos_para_pos(pos), request.data.get('tipo_id'))
        if tipo is False:
            return Response({'tipo_id': 'Tipo inválido para este POS.'}, status=status.HTTP_400_BAD_REQUEST)
        if tipo:
            em_falta = tipo.validar_atributos(atributos)
            if em_falta:
                return Response({'atributos': f'Campos obrigatórios em falta: {em_falta}'}, status=status.HTTP_400_BAD_REQUEST)

        produto = ProdutoPOS.objects.create(
            pos=pos, nome=nome, descricao=descricao, categoria=categoria,
            preco=preco, preco_custo=preco_custo, imagem=imagem, controlar_stock=controlar_stock,
            stock=stock, ativo=ativo, disponivel_pos=disponivel_pos,
            tipo=tipo or None, atributos=atributos,
        )
        erro_conj = _aplicar_conjunto_pos(produto, request.data, pos)
        if erro_conj:
            transaction.set_rollback(True)
            return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
        # grelha de stock por variação enviada com o formulário (tudo-ou-nada)
        erro_grelha = None if produto.e_conjunto else aplicar_grelha_do_pedido(produto, request.data)
        if erro_grelha:
            transaction.set_rollback(True)
            return Response({'detail': erro_grelha}, status=status.HTTP_400_BAD_REQUEST)
        produto.refresh_from_db()
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

        # produtos da loja: tipos globais + tipos da loja (os tipos do POS não entram no catálogo)
        tipo = tipo_permitido(tipos_para_loja(loja), request.data.get('tipo_id'))
        if tipo is False:
            return Response({'tipo_id': 'Tipo inválido para esta loja.'}, status=status.HTTP_400_BAD_REQUEST)
        if tipo:
            em_falta = tipo.validar_atributos(atributos)
            if em_falta:
                return Response({'atributos': f'Campos obrigatórios em falta: {em_falta}'}, status=status.HTTP_400_BAD_REQUEST)

        produto = Produto.objects.create(
            loja=loja, tipo=tipo, nome=nome, descricao=descricao,
            preco=preco, sku=request.data.get('sku', ''),
            ficheiro=imagem, atributos=atributos or {},
            destaque=_str_to_bool(request.data.get('destaque'), False),
            ativo=ativo, disponivel_pos=disponivel_pos,
        )
        _aplicar_categorias_loja(produto, request)
        from ..Views.produtoView import _aplicar_conjunto, _quer_conjunto
        if _quer_conjunto(request.data):
            erro_conj = _aplicar_conjunto(produto, request.data)
            if erro_conj:
                transaction.set_rollback(True)
                return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
        else:
            _set_stock_loja(produto, stock)
        # grelha de stock por variação enviada com o formulário (tudo-ou-nada)
        erro_grelha = None if produto.e_conjunto else aplicar_grelha_do_pedido(produto, request.data)
        if erro_grelha:
            transaction.set_rollback(True)
            return Response({'detail': erro_grelha}, status=status.HTTP_400_BAD_REQUEST)
        produto.refresh_from_db()
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
        aviso = conj.aviso_desactivar(produto, request.data, request.GET)
        if aviso:
            return Response(aviso, status=status.HTTP_409_CONFLICT)

        if 'preco_custo' in request.data:
            produto.preco_custo, erro_custo = ler_valor(request.data['preco_custo'], 'O preço de custo', obrigatorio=False)
            if erro_custo:
                return Response({'detail': erro_custo}, status=status.HTTP_400_BAD_REQUEST)
        for campo, attr in [('nome','nome'),('descricao','descricao'),('categoria','categoria'),('preco',None),
                             ('controlar_stock',None),('stock',None),('ativo',None),('disponivel_pos',None)]:
            if campo not in request.data:
                continue
            if campo == 'categoria':
                produto.categoria = request.data['categoria'] or 'Sem categoria'
            elif campo == 'preco':
                produto.preco, erro_preco = ler_valor(request.data['preco'], 'O preço')
                if erro_preco:
                    return Response({'detail': erro_preco}, status=status.HTTP_400_BAD_REQUEST)
            elif campo in ('controlar_stock', 'ativo', 'disponivel_pos'):
                setattr(produto, campo, _str_to_bool(request.data.get(campo), getattr(produto, campo)))
            elif campo == 'stock':
                # com stock por variação o total é a soma das variações
                if not produto.stock_por_variante:
                    produto.stock = int(request.data.get('stock') or 0)
            else:
                setattr(produto, campo, request.data[campo])

        variantes_mudaram = False
        if 'tipo_id' in request.data:
            tipo = tipo_permitido(tipos_para_pos(pos), request.data.get('tipo_id'))
            if tipo is False:
                return Response({'tipo_id': 'Tipo inválido para este POS.'}, status=status.HTTP_400_BAD_REQUEST)
            variantes_mudaram = (tipo.id if tipo else None) != produto.tipo_id
            produto.tipo = tipo or None
        if 'atributos' in request.data:
            atributos, erro_attr = _ler_atributos(request)
            if erro_attr:
                return erro_attr
            variantes_mudaram = variantes_mudaram or atributos != (produto.atributos or {})
            produto.atributos = atributos

        imagem = request.FILES.get('imagem') or request.FILES.get('ficheiro')
        if imagem:
            produto.imagem = imagem
        produto.save()
        if produto.stock_por_variante and variantes_mudaram:
            sincronizar_variantes(produto)
        erro_conj = _aplicar_conjunto_pos(produto, request.data, pos)
        if erro_conj:
            transaction.set_rollback(True)
            return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
        # grelha de stock por variação enviada com o formulário (tudo-ou-nada)
        erro_grelha = None if produto.e_conjunto else aplicar_grelha_do_pedido(produto, request.data)
        if erro_grelha:
            transaction.set_rollback(True)
            return Response({'detail': erro_grelha}, status=status.HTTP_400_BAD_REQUEST)
        produto.refresh_from_db()
        return Response(_produto_pos_payload(produto, request, pos))

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
        aviso = conj.aviso_desactivar(produto, request.data, request.GET)
        if aviso:
            return Response(aviso, status=status.HTTP_409_CONFLICT)

        for campo in ('nome', 'descricao', 'sku'):
            if campo in request.data:
                setattr(produto, campo, request.data[campo])
        if 'preco' in request.data:
            produto.preco, erro_preco = ler_valor(request.data['preco'], 'O preço')
            if erro_preco:
                return Response({'detail': erro_preco}, status=status.HTTP_400_BAD_REQUEST)
        for campo in ('ativo', 'disponivel_pos', 'destaque'):
            if campo in request.data:
                setattr(produto, campo, _str_to_bool(request.data.get(campo), getattr(produto, campo)))
        variantes_mudaram = False
        if 'tipo_id' in request.data:
            tipo = tipo_permitido(tipos_para_loja(loja), request.data.get('tipo_id'))
            if tipo is False:
                return Response({'tipo_id': 'Tipo inválido para esta loja.'}, status=status.HTTP_400_BAD_REQUEST)
            variantes_mudaram = (tipo.id if tipo else None) != produto.tipo_id
            produto.tipo = tipo or None
        if 'atributos' in request.data:
            atributos, erro_attr = _ler_atributos(request)
            if erro_attr:
                return erro_attr
            variantes_mudaram = variantes_mudaram or atributos != (produto.atributos or {})
            produto.atributos = atributos

        imagem = request.FILES.get('imagem') or request.FILES.get('ficheiro')
        if imagem:
            produto.ficheiro = imagem
        produto.save()
        _aplicar_categorias_loja(produto, request)
        if produto.stock_por_variante and variantes_mudaram:
            sincronizar_variantes(produto)
        from ..Views.produtoView import _aplicar_conjunto
        erro_conj = _aplicar_conjunto(produto, request.data)
        if erro_conj:
            transaction.set_rollback(True)
            return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
        if 'stock' in request.data and not produto.e_conjunto:
            _set_stock_loja(produto, int(request.data.get('stock') or 0))
        # grelha de stock por variação enviada com o formulário (tudo-ou-nada)
        erro_grelha = None if produto.e_conjunto else aplicar_grelha_do_pedido(produto, request.data)
        if erro_grelha:
            transaction.set_rollback(True)
            return Response({'detail': erro_grelha}, status=status.HTTP_400_BAD_REQUEST)
        produto.refresh_from_db()
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
        # faz parte de menus → avisa primeiro; o POS repete com ?confirmar=1
        usado = conj.conjuntos_que_usam(produto)
        if usado and request.GET.get('confirmar') != '1':
            return Response({
                'detail': f'"{produto.nome}" faz parte de {", ".join(usado)}. '
                          f'Se o desactivares, esses menus ficam indisponíveis até o retirares deles.',
                'conjuntos': usado, 'precisa_confirmar': True,
            }, status=status.HTTP_409_CONFLICT)
        produto.ativo = False
        produto.save(update_fields=['ativo'])
        return Response({'detail': 'Produto POS desativado.', 'produto': _produto_pos_payload(produto, request, pos)})

    if origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja.'}, status=status.HTTP_400_BAD_REQUEST)
        loja = pos.loja_vinculada
        if not _verificar_permissao_loja_produtos(loja, utilizador):
            return Response({'detail': 'Sem permissão para gerir produtos desta loja.'}, status=status.HTTP_403_FORBIDDEN)
        produto = get_object_or_404(Produto, id=produto_id, loja=loja)
        usado = conj.conjuntos_que_usam(produto)
        if usado and request.GET.get('confirmar') != '1':
            return Response({
                'detail': f'"{produto.nome}" faz parte de {", ".join(usado)}. '
                          f'Se o desactivares, esses conjuntos ficam indisponíveis até o retirares deles.',
                'conjuntos': usado, 'precisa_confirmar': True,
            }, status=status.HTTP_409_CONFLICT)
        produto.ativo = False
        produto.save(update_fields=['ativo'])
        return Response({'detail': 'Produto da loja desativado.', 'produto': _produto_loja_payload(produto, request, pos)})

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
    existente = Mesa.objects.filter(pos=pos, numero=numero).first()
    if existente and existente.ativa:
        return Response({'detail': 'Já existe uma mesa com este número'}, status=status.HTTP_400_BAD_REQUEST)

    if existente:
        # mesa removida antes (desactivada para manter o histórico de contas) → volta a usar-se
        existente.ativa      = True
        existente.capacidade = capacidade
        existente.save(update_fields=['ativa', 'capacidade'])
        mesa = existente
    else:
        mesa = Mesa.objects.create(pos=pos, numero=numero, capacidade=capacidade)
    return Response({'id': mesa.id, 'numero': mesa.numero, 'capacidade': mesa.capacidade, 'status': mesa.status}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def mesa_abrir(request, pos_id, mesa_id):
    pos, membro = _get_pos_for_request(request, pos_id)
    if membro and not membro.pode_abrir_mesas:
        return Response({'detail': 'Sem permissão para abrir mesas.'}, status=status.HTTP_403_FORBIDDEN)

    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos, ativa=True)   # mesas removidas não abrem

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
        membro=membro, atendente_nome=(membro or request.user.utilizador).nome[:100],
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

    # mesa com histórico de contas (vendas) → só desactiva: as contas são registos financeiros
    if ContaMesa.objects.filter(mesa=mesa).exists():
        mesa.ativa = False
        mesa.save(update_fields=['ativa'])
        return Response({'detail': 'Mesa removida (o histórico de contas foi mantido)'})

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

    erro = _sem_permissao(membro, 'pode_abrir_mesas', 'Sem permissão para abrir mesas.')
    if erro:
        return erro
    if conta_aberta:
        return Response(_conta_payload(conta_aberta, request), status=status.HTTP_200_OK)

    conta = ContaMesa.objects.create(
        pos=pos, mesa=mesa, atendente=utilizador,
        membro=membro, atendente_nome=(membro or utilizador).nome[:100],
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
@transaction.atomic
def conta_adicionar_item(request, pos_id, conta_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    produto_id  = request.data.get('produto_id')
    origem      = request.data.get('origem', 'loja')
    observacoes = request.data.get('observacoes', '')
    try:
        quantidade = int(request.data.get('quantidade', 1) or 1)
    except (TypeError, ValueError):
        quantidade = 0
    if quantidade < 1:
        return Response({'detail': 'Quantidade inválida.'}, status=status.HTTP_400_BAD_REQUEST)

    if not produto_id:
        return Response({'detail': 'produto_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    # menu: opções escolhidas {grupo_id: [opcao_id]} (JSON ou objecto)
    escolhas = request.data.get('escolhas') or {}
    if isinstance(escolhas, str):
        try:
            escolhas = json.loads(escolhas)
        except (TypeError, ValueError):
            escolhas = {}

    atributos, erro_attr = _ler_atributos(request)
    if erro_attr:
        return erro_attr

    if origem == 'pos':
        produto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos, ativo=True)
        if not produto.ativo or not produto.disponivel_pos:
            return Response({'detail': 'Produto POS indisponível'}, status=status.HTTP_400_BAD_REQUEST)
    elif origem == 'loja':
        if pos.modo not in ['integrado', 'hibrido'] or not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja'}, status=status.HTTP_400_BAD_REQUEST)
        if _loja_suspensa(pos):
            return Response({'detail': f'Os produtos da loja "{pos.loja_vinculada.nome}" estão indisponíveis: '
                                       f'a loja foi suspensa pela plataforma.'},
                            status=status.HTTP_400_BAD_REQUEST)
        produto = get_object_or_404(Produto, id=produto_id, loja=pos.loja_vinculada, ativo=True, disponivel_pos=True)
    else:
        return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)

    # reserva o stock (POS ou Bendi, com ou sem variação) — tudo-ou-nada
    info, erro_stock = reservar_stock(produto, quantidade, atributos, pos=pos, escolhas=escolhas)
    if erro_stock:
        return Response({'detail': erro_stock}, status=status.HTTP_400_BAD_REQUEST)

    item = ItemContaMesa.objects.create(
        conta=conta,
        produto=produto if origem == 'loja' else None,
        produto_pos=produto if origem == 'pos' else None,
        variante=info['variante'], variante_pos=info['variante_pos'],
        atributos=atributos,
        componentes=info.get('componentes') or [],
        nome=info['nome'][:200], quantidade=quantidade,
        preco_unitario=info['preco_unitario'], observacoes=observacoes,
        custo_unitario=custo_de_venda(produto, info.get('componentes')),
    )

    return Response({
        'detail': 'Item adicionado',
        'item': {
            'id': item.id, 'produto_id': item.produto_ref_id, 'origem': item.origem,
            'nome': item.nome, 'quantidade': item.quantidade, 'preco_total': str(item.preco_total),
            'atributos': item.atributos,
        },
        'conta': {'subtotal': str(conta.subtotal), 'total': str(conta.total)},
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def conta_remover_item(request, pos_id, conta_id, item_id):
    """
    DELETE /api/pos/<pos_id>/contas/<conta_id>/items/<item_id>/   Body/query: { motivo? }
    Retira o artigo da conta: repõe o stock e deixa-o marcado como cancelado (antes era apagado sem rasto).
    """
    pos, membro, utilizador = _resolve_pos_request(request, pos_id)
    erro = _sem_permissao(membro, 'pode_cancelar_items', 'Sem permissão para remover items.')
    if erro:
        return erro
    conta = get_object_or_404(ContaMesa.objects.select_for_update(), id=conta_id, pos=pos)
    item  = get_object_or_404(ItemContaMesa.objects.select_for_update(), id=item_id, conta=conta)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)
    if item.status == 'cancelado':
        return Response({'detail': 'Este artigo já está cancelado.'}, status=status.HTTP_400_BAD_REQUEST)

    motivo = str(request.data.get('motivo') or request.query_params.get('motivo') or '').strip()
    _cancelar_item(item, _quem(membro, utilizador), motivo)
    conta.calcular_totais()
    return Response({'detail': 'Item removido', 'conta': {'subtotal': str(conta.subtotal), 'total': str(conta.total)}})


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def conta_fechar(request, pos_id, conta_id):
    """
    POST /api/pos/<pos_id>/contas/<conta_id>/fechar/
    Body: { metodo_pagamento, nif_cliente?, gorjeta?, desconto_valor?, desconto_motivo?,
            partes?: [{valor, metodo}] (obrigatório com metodo_pagamento "dividida") }
    Total = artigos + taxa de serviço + gorjeta − desconto; numa conta dividida as partes somam o total.
    """
    pos, membro, utilizador = _resolve_pos_request(request, pos_id)
    erro = _sem_permissao(membro, 'pode_fechar_contas', 'Sem permissão para fechar contas.')
    if erro:
        return erro
    # bloqueada: dois "fechar" ao mesmo tempo (duplo clique, dois terminais) não a fecham duas vezes
    conta = get_object_or_404(ContaMesa.objects.select_for_update(), id=conta_id, pos=pos)

    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    def recusar(msg):
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

    metodo_pagamento = request.data.get('metodo_pagamento')
    nif_cliente      = str(request.data.get('nif_cliente') or '').strip()[:20]

    if not metodo_pagamento:
        return recusar('metodo_pagamento é obrigatório')
    if metodo_pagamento not in dict(ContaMesa.METODO_PAGAMENTO_CHOICES):
        return recusar('Método de pagamento inválido.')
    if not conta.items.exclude(status='cancelado').exists():
        return recusar('A conta não tem artigos para cobrar.')

    gorjeta, erro = ler_valor(request.data.get('gorjeta'), 'A gorjeta', obrigatorio=False)
    if erro:
        return recusar(erro)
    desconto, erro = ler_valor(request.data.get('desconto_valor'), 'O desconto', obrigatorio=False)
    if erro:
        return recusar(erro)
    desconto = desconto or Decimal('0.00')
    if desconto and membro and not membro.pode_dar_descontos:
        return Response({'detail': 'Sem permissão para dar descontos.'}, status=status.HTTP_403_FORBIDDEN)

    quem = _quem(membro, utilizador)
    conta.calcular_totais()   # artigos e taxa de serviço actuais
    if desconto > conta.subtotal + conta.taxa_servico_valor:
        return recusar('O desconto não pode ser maior do que a conta (artigos + taxa de serviço).')
    conta.gorjeta = gorjeta or Decimal('0.00')
    conta.desconto_valor = desconto
    conta.desconto_motivo = str(request.data.get('desconto_motivo') or '').strip()[:200] if desconto else ''
    conta.desconto_por = quem if desconto else ''
    if nif_cliente:
        conta.nif_cliente = nif_cliente
    conta.save(update_fields=['gorjeta', 'desconto_valor', 'desconto_motivo', 'desconto_por', 'nif_cliente'])
    conta.calcular_totais()

    partes = []
    if metodo_pagamento == 'dividida':
        bruto = request.data.get('partes')
        if not isinstance(bruto, list) or not 2 <= len(bruto) <= 20:
            return recusar('Numa conta dividida indica entre 2 e 20 partes.')
        metodos = set(dict(ContaMesa.METODO_PAGAMENTO_CHOICES)) - {'dividida'}
        for n, parte in enumerate(bruto, 1):
            if not isinstance(parte, dict):
                return recusar('Partes inválidas.')
            valor, erro = ler_valor(parte.get('valor'), f'O valor da parte {n}')
            if erro:
                return recusar(erro)
            if valor <= 0:
                return recusar(f'A parte {n} tem de ter um valor maior do que zero.')
            if parte.get('metodo') not in metodos:
                return recusar(f'Escolhe o método de pagamento da parte {n}.')
            partes.append((n, valor, parte['metodo']))
        soma = sum((v for _, v, _ in partes), Decimal('0.00'))
        if soma != conta.total:
            return recusar(f'As partes somam {formatar_dinheiro(soma)} mas a conta é de {formatar_dinheiro(conta.total)}.')

    agora = timezone.now()
    for n, valor, metodo in partes:
        PagamentoDividido.objects.create(conta=conta, pessoa_numero=n, valor=valor, metodo=metodo, pago=True, pago_em=agora)
    if partes:
        conta.dividida_em = len(partes)
        conta.save(update_fields=['dividida_em'])

    conta.fechar(metodo_pagamento, por=quem)
    return Response({
        'detail': 'Conta fechada com sucesso',
        'conta': {'id': conta.id, 'total': str(conta.total), 'metodo_pagamento': conta.metodo_pagamento,
                  'fechada_em': conta.fechada_em, 'gorjeta': str(conta.gorjeta), 'desconto_valor': str(conta.desconto_valor),
                  'partes': [{'pessoa': n, 'valor': str(v), 'metodo': m} for n, v, m in partes]}
    })


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def conta_cancelar(request, pos_id, conta_id):
    """
    POST /api/pos/<pos_id>/contas/<conta_id>/cancelar/   Body: { motivo? }
    Cancela a conta inteira: repõe o stock de todos os itens e liberta a mesa.
    """
    pos, membro, utilizador = _resolve_pos_request(request, pos_id)
    if membro and not membro.pode_cancelar_items:
        return Response({'detail': 'Sem permissão para cancelar.'}, status=status.HTTP_403_FORBIDDEN)

    conta = get_object_or_404(ContaMesa.objects.select_for_update(), id=conta_id, pos=pos)
    if conta.status != 'aberta':
        return Response({'detail': 'Conta já está fechada/cancelada'}, status=status.HTTP_400_BAD_REQUEST)

    motivo = str(request.data.get('motivo') or '').strip()[:300]
    cancelar_conta(conta, motivo, por=_quem(membro, utilizador))   # repõe o stock, cancela os itens e liberta a mesa
    return Response({'detail': 'Conta cancelada. Stock reposto.', 'conta': {'id': conta.id, 'status': conta.status}})


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
    pos, membro, _ = _resolve_pos_request(request, pos_id, permitir_suspenso=True)
    erro = _sem_permissao(membro, 'pode_ver_relatorios', 'Sem permissão para ver o histórico.')
    if erro:
        return erro

    contas = ContaMesa.objects.filter(pos=pos, status='fechada').select_related('mesa', 'atendente', 'loja', 'pos').prefetch_related('items')

    data_inicio = request.query_params.get('data_inicio')
    data_fim    = request.query_params.get('data_fim')
    metodo      = request.query_params.get('metodo')

    # dias inteiros no fuso da plataforma (antes: hora do servidor, e o dia final perdia o último segundo)
    from datetime import date, datetime, time as dt_time, timedelta
    from app.utils.horarios import fuso
    try:
        if data_inicio:
            contas = contas.filter(fechada_em__gte=datetime.combine(date.fromisoformat(data_inicio), dt_time(0), tzinfo=fuso()))
        if data_fim:
            fim = date.fromisoformat(data_fim) + timedelta(days=1)
            contas = contas.filter(fechada_em__lt=datetime.combine(fim, dt_time(0), tzinfo=fuso()))
    except ValueError:
        return Response({'detail': 'Datas inválidas. Usa AAAA-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
    if metodo:
        contas = contas.filter(metodo_pagamento=metodo)
    fatura = request.query_params.get('fatura')
    if fatura == 'por_faturar':
        contas = contas.filter(id__in=faturas_vendas.base('pos').filter(faturas_vendas.q_por_faturar('pos'), faturas_vendas.q_pos_fatura(pos),
                                                                         pos=pos).values('id'))
    elif fatura == 'faturada':
        contas = contas.filter(fatura_registada_em__isnull=False)

    contas = contas.order_by('-fechada_em')
    try:
        offset = max(int(request.query_params.get('offset', 0)), 0)
        limit  = min(max(int(request.query_params.get('limit', 20)), 1), 100)
    except ValueError:
        offset, limit = 0, 20
    total  = contas.count()

    # contas fechadas sem fatura (todas, sem os filtros) — o aviso no topo do Histórico; só as que o POS fatura
    # (as de uma loja a que já não está ligado faturam-se na Faturação dessa loja)
    por_faturar = faturas_vendas.base('pos').filter(faturas_vendas.q_por_faturar('pos'), faturas_vendas.q_pos_fatura(pos), pos=pos).count()
    return Response({'count': total, 'por_faturar': por_faturar,
                     'results': [_conta_payload(c, request) for c in contas[offset:offset + limit]]})


@api_view(['POST', 'DELETE'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def conta_fatura(request, pos_id, conta_id):
    """
    POST   /api/pos/<pos_id>/contas/<conta_id>/fatura/   multipart: numero, pdf (opcional), motivo (ao substituir)
    DELETE /api/pos/<pos_id>/contas/<conta_id>/fatura/   {motivo} — anula (o registo e o PDF ficam no histórico)
    O POS emite a fatura no e-Fatura e regista-a na conta fechada. Quem vê o histórico (gerente) pode registar.
    Também num POS suspenso (são vendas já feitas).
    """
    pos, membro, utilizador = _resolve_pos_request(request, pos_id, permitir_suspenso=True)
    erro = _sem_permissao(membro, 'pode_ver_relatorios', 'Sem permissão para registar faturas.')
    if erro:
        return erro
    conta = get_object_or_404(ContaMesa.objects.select_related('loja', 'pos'), id=conta_id, pos=pos)
    if faturas_vendas.arquivo_conta(conta)['so_leitura']:
        return Response({'detail': f'Esta venda é do arquivo fiscal da loja {conta.loja.nome} (o POS estava ligado a ela '
                                   f'e vendia com o NIF dela): a fatura regista-se na Faturação da loja.'},
                        status=status.HTTP_403_FORBIDDEN)
    # o arquivo guarda o utilizador da conta principal; um membro da equipa fica sem utilizador (não tem User)
    _, _, erro = faturas_vendas.pedido(request, conta, 'pos', utilizador.user if utilizador else None)
    if erro:
        return erro
    conta = ContaMesa.objects.select_related('mesa', 'atendente', 'loja', 'pos').get(pk=conta.pk)
    return Response(_conta_payload(conta, request))


@api_view(['PATCH'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def item_status_atualizar(request, pos_id, conta_id, item_id):
    pos, membro, utilizador = _resolve_pos_request(request, pos_id)
    conta       = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    item        = get_object_or_404(ItemContaMesa.objects.select_for_update(), id=item_id, conta=conta)
    novo_status = request.data.get('status')

    if novo_status not in ['pendente', 'preparando', 'pronto', 'entregue', 'cancelado']:
        return Response({'detail': 'Status inválido'}, status=status.HTTP_400_BAD_REQUEST)
    erro = (_sem_permissao(membro, 'pode_cancelar_items', 'Sem permissão para cancelar items.')
            if novo_status == 'cancelado' else
            _sem_permissao(membro, 'pode_atualizar_status_items', 'Sem permissão para atualizar o estado dos items.'))
    if erro:
        return erro
    # conta já paga: a cozinha continua a mudar o estado, mas cancelar mexia no total e no stock
    if novo_status == 'cancelado' and conta.status != 'aberta':
        return Response({'detail': 'A conta já está fechada — não se cancelam items.'}, status=status.HTTP_400_BAD_REQUEST)

    if item.status == 'cancelado' and novo_status != 'cancelado':
        # o stock já foi devolvido; reactivar exigiria nova reserva → adicionar o item de novo
        return Response({'detail': 'Item cancelado não pode ser reactivado. Adiciona-o de novo.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if novo_status == 'cancelado':
        if item.status != 'cancelado':
            motivo = str(request.data.get('motivo') or '').strip()
            _cancelar_item(item, _quem(membro, utilizador), motivo)
    else:
        item.status = novo_status
        item.save(update_fields=['status', 'atualizado_em'])
    conta.calcular_totais()   # item cancelado deixa de contar no total

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

def _pos_turno(request, pos_id):
    """Turnos: a conta principal ou um membro com a permissão "Abrir/Fechar turno"."""
    pos, membro, utilizador = _resolve_pos_request(request, pos_id)
    erro = _sem_permissao(membro, 'pode_abrir_fechar_turno', 'Sem permissão para abrir e fechar a caixa.')
    return pos, membro, utilizador, erro


def _turno_json(turno, ver_esperado):
    from .relatorios import resumo_turno
    r = {k: (str(v) if isinstance(v, Decimal) else v) for k, v in resumo_turno(turno).items()}
    if not ver_esperado and turno.aberto:
        # fecho "às cegas": quem não vê os relatórios conta o dinheiro sem saber quanto devia estar
        for k in ('vendas_dinheiro', 'esperado', 'vendas_total', 'contas'):
            r[k] = None
    return r


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def turno_atual(request, pos_id):
    """GET /api/pos/<pos_id>/turnos/atual/ — caixa aberta (ou o último turno fechado) e se quem pede a pode gerir."""
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    pode_gerir = not membro or membro.pode_abrir_fechar_turno
    ver_esperado = not membro or membro.pode_ver_relatorios
    if not pode_gerir and not ver_esperado:
        return Response({'detail': 'Sem permissão para ver a caixa.'}, status=status.HTTP_403_FORBIDDEN)
    aberto = TurnoPOS.objects.filter(pos=pos, aberto=True).select_related('operador__user').first()
    ultimo = (TurnoPOS.objects.filter(pos=pos, aberto=False).select_related('operador__user')
              .order_by('-fechado_em').first())
    return Response({
        'turno': _turno_json(aberto, ver_esperado) if aberto else None,
        'ultimo_turno': _turno_json(ultimo, ver_esperado) if ultimo else None,
        'pode_gerir': pode_gerir, 'ver_esperado': ver_esperado,
    })


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def turno_abrir(request, pos_id):
    pos, membro, utilizador, erro = _pos_turno(request, pos_id)
    if erro:
        return erro
    # bloqueia o POS: dois "abrir caixa" ao mesmo tempo não abrem dois turnos
    ConfiguracaoPOS.objects.select_for_update().filter(id=pos.id).first()
    if TurnoPOS.objects.filter(pos=pos, aberto=True).exists():
        return Response({'detail': 'Já existe um turno aberto'}, status=status.HTTP_400_BAD_REQUEST)

    valor_abertura, erro = ler_valor(request.data.get('valor_abertura'), 'O valor de abertura')
    if erro:
        return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)

    # operador = a conta principal (o turno é dela); o membro que abriu fica em "membro" e no nome
    turno = TurnoPOS.objects.create(pos=pos, operador=utilizador or pos.dono, membro=membro,
                                    operador_nome=_quem(membro, utilizador), valor_abertura=valor_abertura)
    return Response({'id': turno.id, 'valor_abertura': str(turno.valor_abertura), 'aberto_em': turno.aberto_em,
                     'operador': turno.operador_nome}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def turno_fechar(request, pos_id, turno_id):
    pos, membro, utilizador, erro = _pos_turno(request, pos_id)
    if erro:
        return erro
    turno = get_object_or_404(TurnoPOS.objects.select_for_update(), id=turno_id, pos=pos)

    if not turno.aberto:
        return Response({'detail': 'Turno já está fechado'}, status=status.HTTP_400_BAD_REQUEST)

    valor_fecho, erro = ler_valor(request.data.get('valor_fecho'), 'O valor contado')
    if erro:
        return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)

    turno.fechar_turno(valor_fecho, por=_quem(membro, utilizador))
    return Response({
        'id': turno.id, 'valor_abertura': str(turno.valor_abertura),
        'valor_fecho': str(turno.valor_fecho), 'diferenca': str(turno.diferenca), 'fechado_em': turno.fechado_em,
        'fechado_por': turno.fechado_por,
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