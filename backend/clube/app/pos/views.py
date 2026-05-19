"""
Views/Endpoints do Sistema POS
Gestão de autenticação, configuração, mesas, contas e operações POS
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.db.models import Sum, Q
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from .models import (
    ConfiguracaoPOS,
    Mesa,
    ContaMesa,
    ItemContaMesa,
    PagamentoDividido,
    TurnoPOS
)
from app.models import Loja, Produto, Utilizador


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def pos_login(request):
    """
    Login no POS com detecção automática de lojas
    Body: { email, password }
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'detail': 'Email e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Autenticar utilizador
    user = authenticate(username=email, password=password)
    if not user:
        return Response(
            {'detail': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        utilizador = user.utilizador
    except:
        return Response(
            {'detail': 'Utilizador não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verificar lojas do utilizador
    lojas_do_utilizador = Loja.objects.filter(
        dono=utilizador,
        ativa=True
    )
    
    # Verificar POS existentes
    pos_existentes = ConfiguracaoPOS.objects.filter(
        dono=utilizador,
        ativo=True
    )
    
    # Gerar tokens JWT
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': utilizador.id,
            'nome': utilizador.nome,
            'email': user.email,
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
    """
    Registo de novo utilizador (igual ao e-commerce)
    Body: { nome, email, password }
    """
    from django.contrib.auth.models import User
    from django.db import transaction
    
    nome = request.data.get('nome', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    
    if not all([nome, email, password]):
        return Response(
            {'detail': 'Todos os campos são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar se email já existe
    if User.objects.filter(email__iexact=email).exists():
        return Response(
            {'detail': 'Email já registado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar se username já existe
    username = email.split('@')[0]
    if User.objects.filter(username=username).exists():
        # Gerar username único
        i = 1
        while User.objects.filter(username=f"{username}{i}").exists():
            i += 1
        username = f"{username}{i}"
    
    try:
        with transaction.atomic():
            # Criar User do Django
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nome.split()[0] if nome else '',
                last_name=' '.join(nome.split()[1:]) if len(nome.split()) > 1 else ''
            )
            
            # Criar perfil Utilizador
            utilizador = Utilizador.objects.create(
                user=user,
                status='ativo',
                verificado=False
            )
            
            # Gerar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': utilizador.id,
                    'nome': utilizador.nome,  # usa a property
                    'email': user.email,
                    'username': user.username,
                }
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
    """
    Criar novo POS
    Body: { nome, loja_id? }
    Se loja_id fornecido → modo integrado
    Se não → modo standalone
    """
    utilizador = request.user.utilizador
    nome = request.data.get('nome', 'POS Principal')
    loja_id = request.data.get('loja_id')
    
    # Criar configuração POS
    config = ConfiguracaoPOS.objects.create(
        nome=nome,
        dono=utilizador,
        modo='standalone'
    )
    
    # Se loja_id fornecido, conectar
    if loja_id:
        loja = get_object_or_404(Loja, id=loja_id, dono=utilizador)
        config.conectar_loja(loja)
    
    return Response({
        'id': config.id,
        'codigo_pos': config.codigo_pos,
        'nome': config.nome,
        'modo': config.modo,
        'loja_vinculada': {
            'id': config.loja_vinculada.id,
            'nome': config.loja_vinculada.nome
        } if config.loja_vinculada else None
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pos_detalhe(request, pos_id):
    """
    Obter detalhes de um POS
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    
    return Response({
        'id': pos.id,
        'codigo_pos': pos.codigo_pos,
        'nome': pos.nome,
        'modo': pos.modo,
        'taxa_servico_ativa': pos.taxa_servico_ativa,
        'taxa_servico_percentagem': pos.taxa_servico_percentagem,
        'loja_vinculada': {
            'id': pos.loja_vinculada.id,
            'nome': pos.loja_vinculada.nome,
            'logo_url': pos.loja_vinculada.logo.url if pos.loja_vinculada.logo else None
        } if pos.loja_vinculada else None,
        'efatura_ativo': pos.efatura_ativo,
        'criado_em': pos.criado_em
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_conectar_loja(request, pos_id):
    """
    Conectar POS standalone a uma loja
    Body: { loja_id }
    """
    utilizador = request.user.utilizador
    loja_id = request.data.get('loja_id')
    
    if not loja_id:
        return Response(
            {'detail': 'loja_id é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    loja = get_object_or_404(Loja, id=loja_id, dono=utilizador)
    
    pos.conectar_loja(loja)
    
    return Response({
        'detail': f'POS conectado à loja {loja.nome}',
        'pos': {
            'id': pos.id,
            'modo': pos.modo,
            'loja_vinculada': {
                'id': loja.id,
                'nome': loja.nome
            }
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pos_desconectar_loja(request, pos_id):
    """
    Desconectar POS da loja (volta ao standalone)
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    
    pos.desconectar_loja()
    
    return Response({
        'detail': 'POS desconectado da loja',
        'pos': {
            'id': pos.id,
            'modo': pos.modo,
            'loja_vinculada': None
        }
    })


# ═══════════════════════════════════════════════════════════════════
# PRODUTOS (CATÁLOGO UNIFICADO)
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pos_produtos(request, pos_id):
    """
    Lista produtos disponíveis no POS
    Se modo integrado → produtos da loja
    Se standalone → produtos da loja (mesmo assim, mas filtra por disponivel_pos)
    
    Retorna no formato compatível com ProductCatalog
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    
    if pos.modo == 'integrado' and pos.loja_vinculada:
        # Usa produtos da loja online
        produtos = Produto.objects.filter(
            loja=pos.loja_vinculada,
            ativo=True,
            disponivel_pos=True
        ).select_related('categoria')
        
    else:
        # Standalone ou sem loja vinculada
        # Retorna produtos de todas as lojas do dono (ou criar campo pos_owner)
        produtos = Produto.objects.filter(
            loja__dono=utilizador,
            ativo=True,
            disponivel_pos=True
        ).select_related('categoria', 'loja')
    
    # Formato unificado para ProductCatalog
    data = [
        {
            'id': p.id,
            'nome': p.nome,
            'descricao': p.descricao,
            'preco': str(p.preco),
            'categoria': p.categoria.nome if p.categoria else 'Sem categoria',
            'imagem_url': p.imagem.url if p.imagem else None,
            'stock': p.stock,
            'disponivel': p.stock > 0 if hasattr(p, 'stock') else True
        }
        for p in produtos
    ]
    
    return Response(data)


# ═══════════════════════════════════════════════════════════════════
# MESAS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mesas_listar(request, pos_id):
    """
    Lista todas as mesas do POS
    """
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
            'tem_conta_aberta': ContaMesa.objects.filter(
                mesa=m,
                status='aberta'
            ).exists()
        }
        for m in mesas
    ]
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mesa_criar(request, pos_id):
    """
    Criar nova mesa
    Body: { numero, capacidade }
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    
    numero = request.data.get('numero')
    capacidade = request.data.get('capacidade', 4)
    
    if not numero:
        return Response(
            {'detail': 'Número da mesa é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar duplicação
    if Mesa.objects.filter(pos=pos, numero=numero).exists():
        return Response(
            {'detail': 'Já existe uma mesa com este número'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    mesa = Mesa.objects.create(
        pos=pos,
        numero=numero,
        capacidade=capacidade
    )
    
    return Response({
        'id': mesa.id,
        'numero': mesa.numero,
        'capacidade': mesa.capacidade,
        'status': mesa.status
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mesa_abrir(request, pos_id, mesa_id):
    """
    Abrir mesa (marcar como ocupada)
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)
    
    if mesa.status != 'livre':
        return Response(
            {'detail': f'Mesa está {mesa.status}, não pode ser aberta'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    mesa.abrir(utilizador)
    
    return Response({
        'detail': 'Mesa aberta',
        'mesa': {
            'id': mesa.id,
            'numero': mesa.numero,
            'status': mesa.status
        }
    })


# ═══════════════════════════════════════════════════════════════════
# CONTAS
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conta_criar(request, pos_id, mesa_id):
    """
    Criar nova conta para uma mesa
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    mesa = get_object_or_404(Mesa, id=mesa_id, pos=pos)
    
    # Verificar se já tem conta aberta
    if ContaMesa.objects.filter(mesa=mesa, status='aberta').exists():
        return Response(
            {'detail': 'Esta mesa já tem uma conta aberta'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Criar conta
    conta = ContaMesa.objects.create(
        pos=pos,
        mesa=mesa,
        atendente=utilizador,
        taxa_servico_percentagem=pos.taxa_servico_percentagem if pos.taxa_servico_ativa else Decimal('0.00')
    )
    
    # Abrir mesa
    mesa.abrir(utilizador)
    
    return Response({
        'id': conta.id,
        'mesa': {
            'id': mesa.id,
            'numero': mesa.numero
        },
        'status': conta.status,
        'subtotal': str(conta.subtotal),
        'total': str(conta.total),
        'items': []
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conta_detalhe(request, pos_id, conta_id):
    """
    Obter detalhes de uma conta
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    
    items = ItemContaMesa.objects.filter(conta=conta).select_related('produto')
    
    return Response({
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
                'produto_id': item.produto.id,
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
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conta_adicionar_item(request, pos_id, conta_id):
    """
    Adicionar item à conta
    Body: { produto_id, quantidade, observacoes? }
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    
    if conta.status != 'aberta':
        return Response(
            {'detail': 'Conta já está fechada/cancelada'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    produto_id = request.data.get('produto_id')
    quantidade = request.data.get('quantidade', 1)
    observacoes = request.data.get('observacoes', '')
    
    if not produto_id:
        return Response(
            {'detail': 'produto_id é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    produto = get_object_or_404(Produto, id=produto_id)
    
    # Criar item
    item = ItemContaMesa.objects.create(
        conta=conta,
        produto=produto,
        nome=produto.nome,
        quantidade=quantidade,
        preco_unitario=produto.preco,
        observacoes=observacoes
    )
    
    # Calcular totais é feito automaticamente no save()
    
    return Response({
        'detail': 'Item adicionado',
        'item': {
            'id': item.id,
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
    """
    Remover item da conta
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    item = get_object_or_404(ItemContaMesa, id=item_id, conta=conta)
    
    if conta.status != 'aberta':
        return Response(
            {'detail': 'Conta já está fechada/cancelada'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    """
    Fechar conta (processar pagamento)
    Body: { metodo_pagamento, nif_cliente? }
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    conta = get_object_or_404(ContaMesa, id=conta_id, pos=pos)
    
    if conta.status != 'aberta':
        return Response(
            {'detail': 'Conta já está fechada/cancelada'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    metodo_pagamento = request.data.get('metodo_pagamento')
    nif_cliente = request.data.get('nif_cliente', '')
    
    if not metodo_pagamento:
        return Response(
            {'detail': 'metodo_pagamento é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Atualizar NIF se fornecido
    if nif_cliente:
        conta.nif_cliente = nif_cliente
        conta.save(update_fields=['nif_cliente'])
    
    # Fechar conta
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
    """
    Abrir novo turno
    Body: { valor_abertura }
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    
    # Verificar se já tem turno aberto
    if TurnoPOS.objects.filter(pos=pos, aberto=True).exists():
        return Response(
            {'detail': 'Já existe um turno aberto'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    valor_abertura = request.data.get('valor_abertura')
    if valor_abertura is None:
        return Response(
            {'detail': 'valor_abertura é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    """
    Fechar turno
    Body: { valor_fecho }
    """
    utilizador = request.user.utilizador
    pos = get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador)
    turno = get_object_or_404(TurnoPOS, id=turno_id, pos=pos)
    
    if not turno.aberto:
        return Response(
            {'detail': 'Turno já está fechado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    valor_fecho = request.data.get('valor_fecho')
    if valor_fecho is None:
        return Response(
            {'detail': 'valor_fecho é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    turno.fechar_turno(Decimal(str(valor_fecho)))
    
    return Response({
        'id': turno.id,
        'valor_abertura': str(turno.valor_abertura),
        'valor_fecho': str(turno.valor_fecho),
        'diferenca': str(turno.diferenca),
        'fechado_em': turno.fechado_em
    })