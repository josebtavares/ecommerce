from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..Views.notificacaoView import notificar

from ..models import (
    Utilizador, Loja, Produto, Encomenda,
    Pagamento, TipoProduto, UtilizadorLoja,
)
from ..Serializers.ProdutoSerializer import TipoProdutoSerializer
from ..utils.pagination import paginar


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════

def _exige_admin(request, permissao=None):
    """
    Verifica se o utilizador é staff e tem a permissão necessária.
    Se permissao=None, só verifica is_staff.
    """
    if not request.user.is_staff:
        return Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
    if permissao:
        try:
            util = request.user.utilizador
        except Exception:
            return Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
        if not util.pode_admin(permissao):
            return Response({'detail': f'Sem permissao: {permissao}'}, status=status.HTTP_403_FORBIDDEN)
    return None


# ══════════════════════════════════════════════════════════════
# ESTATÍSTICAS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):
    """GET /app/admin/stats/"""
    erro = _exige_admin(request, 'ver_stats')
    if erro: return erro

    total_utilizadores = Utilizador.objects.count()
    total_lojas        = Loja.objects.count()
    lojas_ativas       = Loja.objects.filter(ativa=True).count()
    lojas_pendentes    = Loja.objects.filter(ativa=False).count()
    total_produtos     = Produto.objects.filter(ativo=True).count()
    total_encomendas   = Encomenda.objects.count()
    total_vendas       = Pagamento.objects.filter(status='aprovado').aggregate(
                             total=Sum('valor')
                         )['total'] or 0
    utilizadores_verificados = Utilizador.objects.filter(verificado=True).count()

    # encomendas por estado
    encomendas_por_estado = dict(
        Encomenda.objects.values('status')
        .annotate(total=Count('id'))
        .values_list('status', 'total')
    )

    return Response({
        'utilizadores': {
            'total':      total_utilizadores,
            'verificados': utilizadores_verificados,
        },
        'lojas': {
            'total':    total_lojas,
            'ativas':   lojas_ativas,
            'pendentes': lojas_pendentes,
        },
        'produtos':   total_produtos,
        'encomendas': {
            'total':      total_encomendas,
            'por_estado': encomendas_por_estado,
        },
        'vendas_total': str(total_vendas),
    })


# ══════════════════════════════════════════════════════════════
# LOJAS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_loja_list(request):
    """
    GET /app/admin/lojas/?q=&ativa=&offset=0&limit=20
    """
    erro = _exige_admin(request, 'gerir_lojas')
    if erro: return erro

    qs = Loja.objects.select_related('dono__user').order_by('-data_criacao')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(categoria__icontains=q))

    ativa = request.GET.get('ativa')
    if ativa == 'true':
        qs = qs.filter(ativa=True)
    elif ativa == 'false':
        qs = qs.filter(ativa=False)

    categoria = request.GET.get('categoria')
    if categoria:
        qs = qs.filter(categoria__iexact=categoria)

    offset = int(request.GET.get('offset', 0))
    limit  = int(request.GET.get('limit', 20))
    total  = qs.count()
    lojas  = qs[offset:offset + limit]

    results = []
    for loja in lojas:
        results.append({
            'id':          loja.id,
            'nome':        loja.nome,
            'categoria':   loja.categoria,
            'localizacao': loja.localizacao,
            'ativa':       loja.ativa,
            'dono': {
                'id':       loja.dono.id,
                'username': loja.dono.user.username,
                'email':    loja.dono.user.email,
            },
            'logo_url':    request.build_absolute_uri(loja.logo.url) if loja.logo else None,
            'banner_url':  request.build_absolute_uri(loja.banner.url) if loja.banner else None,
            'data_criacao': loja.data_criacao.strftime('%d-%m-%Y %H:%M'),
            'total_produtos': loja.produtos.filter(ativo=True).count(),
            'total_encomendas': loja.encomendas.count(),
        })

    return Response({
        'count':       total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results':     results,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_loja_gerir(request, loja_id):
    """
    PATCH /app/admin/lojas/<loja_id>/
    Body: { ativa: true/false }
    Activa ou desactiva uma loja.
    """
    erro = _exige_admin(request, 'gerir_lojas')
    if erro: return erro

    loja = get_object_or_404(Loja, id=loja_id)

    if 'ativa' in request.data:
        loja.ativa = request.data['ativa']
        loja.save(update_fields=['ativa'])
        
    if 'ativa' in request.data:
        if request.data['ativa']:
            notificar(
                utilizador=loja.dono,
                tipo='loja_aprovada',
                titulo=f'A tua loja "{loja.nome}" foi aprovada!',
                mensagem='A tua loja já está visível no site. Podes começar a receber encomendas.',
                loja=loja,
                link=f'/loja/{loja.id}/backoffice',
            )
        else:
            notificar(
                utilizador=loja.dono,
                tipo='loja_rejeitada',
                titulo=f'A tua loja "{loja.nome}" foi desactivada.',
                mensagem='A tua loja foi desactivada pelo administrador. Contacta o suporte para mais informações.',
                loja=loja,
                link=f'/loja/{loja.id}/backoffice',
            )

    return Response({
        'id':    loja.id,
        'nome':  loja.nome,
        'ativa': loja.ativa,
    })


# ══════════════════════════════════════════════════════════════
# UTILIZADORES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_utilizador_list(request):
    """
    GET /app/admin/utilizadores/?q=&verificado=&status=&offset=0&limit=20
    """
    erro = _exige_admin(request, 'gerir_utilizadores')
    if erro: return erro

    qs = Utilizador.objects.select_related('user').order_by('-data_criacao')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)
        )

    verificado = request.GET.get('verificado')
    if verificado == 'true':
        qs = qs.filter(verificado=True)
    elif verificado == 'false':
        qs = qs.filter(verificado=False)

    stat = request.GET.get('status')
    if stat:
        qs = qs.filter(status=stat)

    offset = int(request.GET.get('offset', 0))
    limit  = int(request.GET.get('limit', 20))
    total  = qs.count()
    utils  = qs[offset:offset + limit]

    results = []
    for u in utils:
        foto_url = request.build_absolute_uri(u.foto.url) if u.foto else None
        results.append({
            'id':         u.id,
            'username':   u.user.username,
            'email':      u.user.email,
            'nome':       u.nome,
            'telefone':   u.telefone,
            'foto_url':   foto_url,
            'verificado': u.verificado,
            'status':     u.status,
            'is_staff':   u.user.is_staff,
            'role_admin': u.role_admin,
            'data_criacao': u.data_criacao.strftime('%d-%m-%Y %H:%M'),
            'total_lojas': u.lojas.count(),
        })

    return Response({
        'count':       total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results':     results,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_utilizador_gerir(request, utilizador_id):
    """
    PATCH /app/admin/utilizadores/<id>/
    Body: { verificado?, status?, is_staff?, role_admin? }
    """
    erro = _exige_admin(request, 'gerir_utilizadores')
    if erro: return erro

    utilizador = get_object_or_404(Utilizador, id=utilizador_id)

    # nao pode editar a si mesmo para evitar acidente
    if utilizador.user == request.user:
        return Response(
            {'detail': 'Nao podes editar a tua propria conta aqui.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'verificado' in request.data:
        utilizador.verificado = request.data['verificado']

    if 'status' in request.data:
        novo_status = request.data['status']
        if novo_status in ('ativo', 'banido', 'suspenso'):
            utilizador.status = novo_status

    if 'is_staff' in request.data:
        utilizador.user.is_staff = request.data['is_staff']
        if not request.data['is_staff']:
            utilizador.role_admin = None
        utilizador.user.save(update_fields=['is_staff'])

    if 'role_admin' in request.data:
        role = request.data['role_admin']
        roles_validas = [r[0] for r in Utilizador.ROLES_ADMIN]
        if role in roles_validas:
            utilizador.role_admin = role
            utilizador.user.is_staff = True
            utilizador.user.save(update_fields=['is_staff'])
        elif role is None or role == '':
            utilizador.role_admin = None

    utilizador.save()

    return Response({
        'id':         utilizador.id,
        'username':   utilizador.user.username,
        'verificado': utilizador.verificado,
        'status':     utilizador.status,
        'is_staff':   utilizador.user.is_staff,
        'role_admin': utilizador.role_admin,
    })


# ══════════════════════════════════════════════════════════════
# PRODUTOS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_produto_list(request):
    """
    GET /app/admin/produtos/?q=&loja_id=&tipo=&offset=0&limit=20
    """
    erro = _exige_admin(request, 'gerir_produtos')
    if erro: return erro

    from ..Serializers.ProdutoSerializer import ProdutoSerializer
    qs = Produto.objects.select_related('loja', 'tipo').order_by('-data_criacao')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))

    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    tipo = request.GET.get('tipo')
    if tipo:
        qs = qs.filter(tipo__nome__iexact=tipo)

    ativo = request.GET.get('ativo')
    if ativo == 'true':
        qs = qs.filter(ativo=True)
    elif ativo == 'false':
        qs = qs.filter(ativo=False)

    response, erro = paginar(request, qs, ProdutoSerializer)
    if erro: return erro
    return response


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_produto_gerir(request, produto_id):
    """
    PATCH /app/admin/produtos/<id>/
    Body: { ativo: true/false, destaque: true/false }
    """
    erro = _exige_admin(request, 'gerir_produtos')
    if erro: return erro

    produto = get_object_or_404(Produto, id=produto_id)

    if 'ativo' in request.data:
        produto.ativo = request.data['ativo']
    if 'destaque' in request.data:
        produto.destaque = request.data['destaque']

    produto.save()
    return Response({'id': produto.id, 'ativo': produto.ativo, 'destaque': produto.destaque})


# ══════════════════════════════════════════════════════════════
# ENCOMENDAS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_encomenda_list(request):
    """
    GET /app/admin/encomendas/?status=&loja_id=&offset=0&limit=20
    """
    erro = _exige_admin(request, 'gerir_encomendas')
    if erro: return erro

    from ..Serializers.InventarioCarrinhoEncomendaSerializer import EncomendaMiniSerializer
    qs = Encomenda.objects.select_related('loja', 'comprador__user').order_by('-data_criacao')

    stat = request.GET.get('status')
    if stat:
        qs = qs.filter(status=stat)

    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    response, erro = paginar(request, qs, EncomendaMiniSerializer)
    if erro: return erro
    return response


# ══════════════════════════════════════════════════════════════
# PAGAMENTOS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pagamento_list(request):
    """
    GET /app/admin/pagamentos/?status=&offset=0&limit=20
    """
    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro: return erro

    from ..Serializers.PagamentoSerializer import PagamentoSerializer
    qs = Pagamento.objects.select_related('encomenda__loja', 'encomenda__comprador__user', 'metodo').order_by('-data_criacao')

    stat = request.GET.get('status')
    if stat:
        qs = qs.filter(status=stat)

    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(encomenda__loja_id=loja_id)

    response, erro = paginar(request, qs, PagamentoSerializer)
    if erro: return erro
    return response


# ══════════════════════════════════════════════════════════════
# TIPOS DE PRODUTO GLOBAIS
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_tipos_list_criar(request):
    """
    GET  /app/admin/tipos/       → lista tipos globais
    POST /app/admin/tipos/       → cria tipo global
    """
    erro = _exige_admin(request, 'gerir_tipos_globais')
    if erro: return erro

    if request.method == 'GET':
        qs = TipoProduto.objects.filter(loja__isnull=True).order_by('nome')
        serializer = TipoProdutoSerializer(qs, many=True)
        return Response(serializer.data)

    serializer = TipoProdutoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tipo = serializer.save(loja=None)
    return Response(TipoProdutoSerializer(tipo).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_tipos_gerir(request, tipo_id):
    """
    PATCH  /app/admin/tipos/<id>/  → editar tipo global
    DELETE /app/admin/tipos/<id>/  → desactivar tipo global
    """
    erro = _exige_admin(request, 'gerir_tipos_globais')
    if erro: return erro

    tipo = get_object_or_404(TipoProduto, id=tipo_id, loja__isnull=True)

    if request.method == 'DELETE':
        tipo.ativo = False
        tipo.save(update_fields=['ativo'])
        return Response({'detail': 'Tipo desactivado.'})

    serializer = TipoProdutoSerializer(tipo, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# COMISSOES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_comissao_list(request):
    """
    GET /app/admin/comissoes/?status=&loja_id=&offset=0&limit=20
    """
    from ..models import Comissao
    from django.db.models import Sum

    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro: return erro

    qs = Comissao.objects.select_related('loja', 'encomenda').order_by('-data_criacao')

    stat = request.GET.get('status')
    if stat:
        qs = qs.filter(status=stat)

    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    # totais
    total_pendente  = Comissao.objects.filter(status='pendente').aggregate(t=Sum('valor_comissao'))['t'] or 0
    total_liquidado = Comissao.objects.filter(status='liquidada').aggregate(t=Sum('valor_comissao'))['t'] or 0

    offset = int(request.GET.get('offset', 0))
    limit  = int(request.GET.get('limit', 20))
    total  = qs.count()
    items  = qs[offset:offset + limit]

    results = []
    for c in items:
        results.append({
            'id':             c.id,
            'loja_id':        c.loja.id,
            'loja_nome':      c.loja.nome,
            'encomenda_id':   c.encomenda_id,
            'valor_encomenda': str(c.valor_encomenda),
            'percentagem':    str(c.percentagem),
            'valor_comissao': str(c.valor_comissao),
            'status':         c.status,
            'data_criacao':   c.data_criacao.strftime('%d-%m-%Y %H:%M'),
            'data_liquidacao': c.data_liquidacao.strftime('%d-%m-%Y %H:%M') if c.data_liquidacao else None,
        })

    return Response({
        'count':           total,
        'next_offset':     offset + limit if offset + limit < total else None,
        'total_pendente':  str(total_pendente),
        'total_liquidado': str(total_liquidado),
        'results':         results,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_comissao_liquidar(request, comissao_id):
    """
    PATCH /app/admin/comissoes/<id>/liquidar/
    Marca a comissao como liquidada.
    """
    from ..models import Comissao
    from django.utils.timezone import now

    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro: return erro

    comissao = get_object_or_404(Comissao, id=comissao_id)
    if comissao.status == 'liquidada':
        return Response({'detail': 'Comissao ja esta liquidada.'}, status=status.HTTP_400_BAD_REQUEST)

    comissao.status = 'liquidada'
    comissao.data_liquidacao = now()
    if request.data.get('notas'):
        comissao.notas = request.data['notas']
    comissao.save()

    return Response({'id': comissao.id, 'status': comissao.status, 'data_liquidacao': comissao.data_liquidacao})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_loja_comissao(request, loja_id):
    """
    GET /app/admin/lojas/<loja_id>/comissao/
    Ver e editar a percentagem de comissao de uma loja.
    """
    erro = _exige_admin(request, 'gerir_lojas')
    if erro: return erro

    loja = get_object_or_404(Loja, id=loja_id)

    if request.method == 'GET':
        return Response({
            'loja_id':             loja.id,
            'loja_nome':           loja.nome,
            'percentagem_comissao': str(loja.percentagem_comissao),
        })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_loja_comissao_update(request, loja_id):
    """
    PATCH /app/admin/lojas/<loja_id>/comissao/
    Actualiza a percentagem de comissao de uma loja.
    """
    erro = _exige_admin(request, 'gerir_lojas')
    if erro: return erro

    loja = get_object_or_404(Loja, id=loja_id)

    percentagem = request.data.get('percentagem_comissao')
    if percentagem is not None:
        try:
            p = float(percentagem)
            if not (0 <= p <= 100):
                raise ValueError
            loja.percentagem_comissao = p
            loja.save(update_fields=['percentagem_comissao'])
        except (ValueError, TypeError):
            return Response({'detail': 'Percentagem invalida (0-100).'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'loja_id':              loja.id,
        'percentagem_comissao': str(loja.percentagem_comissao),
    })
    
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_categoria_list_criar(request):
    """
    GET  /app/admin/categorias/  → lista todas (incluindo inactivas)
    POST /app/admin/categorias/  → cria nova
    """
    from ..models import Categoria
    erro = _exige_admin(request, 'gerir_lojas')
    if erro: return erro
 
    if request.method == 'GET':
        cats = Categoria.objects.all()
        return Response([
            {'id': c.id, 'nome': c.nome, 'icon': c.icon, 'ativo': c.ativo, 'ordem': c.ordem}
            for c in cats
        ])
 
    nome = request.data.get('nome', '').strip()
    if not nome:
        return Response({'detail': 'Nome obrigatorio.'}, status=status.HTTP_400_BAD_REQUEST)
 
    cat, criada = Categoria.objects.get_or_create(
        nome__iexact=nome,
        defaults={
            'nome':  nome,
            'icon':  request.data.get('icon', '🏪'),
            'ordem': int(request.data.get('ordem', 99)),
            'ativo': True,
        }
    )
    if not criada:
        return Response({'detail': 'Categoria ja existe.'}, status=status.HTTP_400_BAD_REQUEST)
 
    return Response(
        {'id': cat.id, 'nome': cat.nome, 'icon': cat.icon, 'ativo': cat.ativo, 'ordem': cat.ordem},
        status=status.HTTP_201_CREATED
    )
 
 
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_categoria_gerir(request, cat_id):
    """
    PATCH  /app/admin/categorias/<id>/  → editar
    DELETE /app/admin/categorias/<id>/  → desactivar
    """
    from ..models import Categoria
    erro = _exige_admin(request, 'gerir_lojas')
    if erro: return erro
 
    cat = get_object_or_404(Categoria, id=cat_id)
 
    if request.method == 'DELETE':
        cat.ativo = False
        cat.save(update_fields=['ativo'])
        return Response({'detail': 'Categoria desactivada.'})
 
    if 'nome'  in request.data: cat.nome  = request.data['nome']
    if 'icon'  in request.data: cat.icon  = request.data['icon']
    if 'ordem' in request.data: cat.ordem = request.data['ordem']
    if 'ativo' in request.data: cat.ativo = request.data['ativo']
    cat.save()
 
    return Response({'id': cat.id, 'nome': cat.nome, 'icon': cat.icon, 'ativo': cat.ativo, 'ordem': cat.ordem})