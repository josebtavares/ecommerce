from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from ..Views.notificacaoView import notificar_admins,notificar

from django.db.models import Sum, Count, Avg, Q
from django.utils.timezone import now
from datetime import timedelta


from ..models import Loja, LojaTemplate, UtilizadorLoja, Utilizador
from ..Serializers.LojaSerializer import (
    LojaSerializer,
    LojaPublicSerializer,
    LojaMiniSerializer,
    LojaTemplateSerializer,
    UtilizadorLojaSerializer,
)
from ..utils.pagination import paginar


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _get_membro(request, loja):
    """Devolve o UtilizadorLoja activo ou None."""
    try:
        return UtilizadorLoja.objects.get(
            loja=loja,
            utilizador=request.user.utilizador,
            ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        return None


def _exige_permissao(request, loja, permissao):
    """
    Devolve (membro, None) se OK.
    Devolve (None, Response 403) se sem permissão.
    """
    membro = _get_membro(request, loja)
    if not membro or not membro.pode(permissao):
        return None, Response(
            {'detail': f'Sem permissão: {permissao}'},
            status=status.HTTP_403_FORBIDDEN
        )
    return membro, None


# ══════════════════════════════════════════════════════════════
# TEMPLATES  (público)
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def template_list(request):
    """GET /app/loja/templates/"""
    templates = LojaTemplate.objects.filter(ativo=True)
    serializer = LojaTemplateSerializer(templates, many=True, context={'request': request})
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# LOJA — LEITURA PÚBLICA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def loja_list(request):
    """
    GET /app/loja/?q=pizza&categoria=comida&offset=0&limit=20
                  &entrega=true&localizacao=lisboa
    Lista pública de lojas activas com pesquisa e filtros.
    """
    qs = Loja.objects.select_related('template').filter(ativa=True)

    # pesquisa de texto
    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))

    # filtros
    categoria = request.GET.get('categoria')
    if categoria:
        qs = qs.filter(categoria__iexact=categoria)

    localizacao = request.GET.get('localizacao')
    if localizacao:
        qs = qs.filter(localizacao__icontains=localizacao)

    if request.GET.get('entrega') == 'true':
        qs = qs.filter(entrega_ativa=True)

    if request.GET.get('levantamento') == 'true':
        qs = qs.filter(levantamento_ativo=True)
        
    ordering = request.GET.get('ordering')
    if ordering in ['nome', '-nome', '-data_criacao']:
        qs = qs.order_by(ordering)

    response, erro = paginar(request, qs, LojaPublicSerializer, limit_default=5)
    if erro:
        return erro
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def loja_get(request, id):
    """GET /app/loja/<id>/  — página pública da loja"""
    loja = get_object_or_404(Loja, id=id, ativa=True)
    serializer = LojaPublicSerializer(loja, context={'request': request})
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# LOJA — CRIAR  (qualquer utilizador autenticado)
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def loja_create(request):
    """
    POST /app/loja/criar/
    Só utilizadores verificados podem criar lojas.
    Loja criada com ativa=False — aguarda aprovação do admin.
    """
    utilizador = request.user.utilizador
 
    # verifica se o utilizador está verificado
    if not utilizador.verificado:
        return Response(
            {'detail': 'A tua conta precisa de estar verificada para criar uma loja.'},
            status=status.HTTP_403_FORBIDDEN
        )
 
    serializer = LojaSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    loja = serializer.save(
        dono   = utilizador,
        ativa  = False,          # pendente de aprovação pelo admin
        logo   = request.FILES.get('logo'),
        banner = request.FILES.get('banner'),
    )
    
    notificar_admins(
        tipo='loja_pendente',
        titulo=f'Nova loja pendente: {loja.nome}',
        mensagem=f'{utilizador.nome} criou a loja "{loja.nome}" ({loja.categoria}). Aguarda aprovação.',
        loja=loja,
        link='/admin',
    )
 
    # regista o criador como dono no staff
    UtilizadorLoja.objects.create(
        loja=loja,
        utilizador=utilizador,
        role='dono',
        ativo=True,
    )
 
    # cria métodos de pagamento seleccionados
    metodos = request.data.getlist('metodos_pagamento')
    if metodos:
        from ..models import MetodoPagamento
        for tipo in metodos:
            MetodoPagamento.objects.get_or_create(loja=loja, tipo=tipo, defaults={'ativo': True})
 
    # cria opções de entrega (enviadas como JSON string)
    import json
    opcoes_raw = request.data.get('opcoes_entrega')
    if opcoes_raw:
        try:
            opcoes = json.loads(opcoes_raw)
            from ..models import OpcaoEntrega
            for op in opcoes:
                if op.get('nome'):
                    OpcaoEntrega.objects.create(
                        loja           = loja,
                        nome           = op['nome'],
                        preco          = op.get('preco', 0),
                        tempo_estimado = op.get('tempo_estimado', ''),
                        ativa          = True,
                    )
        except (json.JSONDecodeError, TypeError):
            pass
 
    return Response(
        LojaSerializer(loja, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


# ══════════════════════════════════════════════════════════════
# LOJA — BACKOFFICE  (requer permissão)
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_backoffice(request, id):
    """
    GET /app/loja/<id>/backoffice/
    Dados completos da loja para o painel de gestão.
    Inclui minha_role para o frontend saber o que mostrar.
    """
    loja = get_object_or_404(Loja, id=id)
    _, erro = _exige_permissao(request, loja, 'ver_loja')
    if erro:
        return erro

    serializer = LojaSerializer(loja, context={'request': request})
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def loja_update(request, id):
    """PUT/PATCH /app/loja/<id>/editar/"""
    loja = get_object_or_404(Loja, id=id)
    _, erro = _exige_permissao(request, loja, 'editar_loja')
    if erro:
        return erro

    serializer = LojaSerializer(
        loja, data=request.data, partial=True,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    loja = serializer.save(
        logo  =request.FILES.get('logo',   loja.logo),
        banner=request.FILES.get('banner', loja.banner),
    )
    return Response(LojaSerializer(loja, context={'request': request}).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def loja_delete(request, id):
    """DELETE /app/loja/<id>/eliminar/ — só o dono pode apagar"""
    loja = get_object_or_404(Loja, id=id)
    _, erro = _exige_permissao(request, loja, 'apagar_loja')
    if erro:
        return erro

    loja.ativa = False
    loja.save(update_fields=['ativa'])
    return Response({'detail': 'Loja desactivada.'}, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# LOJAS DO UTILIZADOR AUTENTICADO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def minhas_lojas(request):
    """
    GET /app/loja/minhas/
    Devolve todas as lojas onde o utilizador tem algum role
    (dono, gestor, staff, etc.).
    """
    utilizador = request.user.utilizador
    lojas = Loja.objects.filter(
        staff__utilizador=utilizador,
        staff__ativo=True,
    ).select_related('template').distinct()

    serializer = LojaSerializer(lojas, many=True, context={'request': request})
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# GESTÃO DE STAFF
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_list(request, loja_id):
    """GET /app/loja/<loja_id>/staff/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro

    # só mostra membros activos
    staff = UtilizadorLoja.objects.filter(
        loja=loja, ativo=True
    ).select_related('utilizador__user')
    serializer = UtilizadorLojaSerializer(staff, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_add(request, loja_id):
    """
    POST /app/loja/<loja_id>/staff/adicionar/
    Body: { utilizador_id, role }
    Se role=condutor → cria também registo Condutor.
    Se o utilizador já existiu no staff (ativo=False), reactiva-o.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro
 
    if request.data.get('role') == 'dono':
        return Response(
            {'detail': 'Não é possível atribuir o role de dono desta forma.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    utilizador_id = request.data.get('utilizador_id')
    novo_role     = request.data.get('role', 'staff')
 
    existente = UtilizadorLoja.objects.filter(
        loja=loja, utilizador_id=utilizador_id
    ).first()
 
    if existente:
        if existente.ativo:
            return Response(
                {'detail': 'Este utilizador já faz parte do staff.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            existente.role  = novo_role
            existente.ativo = True
            existente.save(update_fields=['role', 'ativo'])
            # se mudou para condutor, garante registo Condutor activo
            if novo_role == 'condutor':
                _sincronizar_condutor(loja, existente.utilizador, request.data.get('tipo_veiculo', ''))
                _notificar_novo_staff(existente.utilizador, loja, novo_role)
            return Response(
                UtilizadorLojaSerializer(existente, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
 
    serializer = UtilizadorLojaSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    membro = serializer.save(loja=loja)
 
    # se role=condutor → cria registo Condutor
    if novo_role == 'condutor':
        _sincronizar_condutor(loja, membro.utilizador, request.data.get('tipo_veiculo', ''))
 
    _notificar_novo_staff(membro.utilizador, loja, novo_role)
 
    return Response(
        UtilizadorLojaSerializer(membro, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )
    
def _sincronizar_condutor(loja, utilizador, tipo_veiculo=''):
    """Cria ou reactiva o registo Condutor quando role=condutor."""
    from ..models import Condutor
    condutor, criado = Condutor.objects.get_or_create(
        loja=loja,
        utilizador=utilizador,
        defaults={'tipo_veiculo': tipo_veiculo, 'ativo': True}
    )
    if not criado:
        # reactiva se estava inactivo
        condutor.ativo = True
        if tipo_veiculo:
            condutor.tipo_veiculo = tipo_veiculo
        condutor.save(update_fields=['ativo', 'tipo_veiculo'])
    return condutor
 
 
def _notificar_novo_staff(utilizador, loja, role):
    try:
        from ..Views.notificacaoView import notificar
        notificar(
            utilizador=utilizador,
            tipo='novo_staff',
            titulo=f'Foste adicionado à loja "{loja.nome}"',
            mensagem=f'Tens o papel de {role} na loja {loja.nome}.',
            loja=loja,
            link=f'/loja/{loja.id}/backoffice',
        )
    except Exception:
        pass


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def staff_update_role(request, loja_id, membro_id):
    """
    PATCH /app/loja/<loja_id>/staff/<membro_id>/
    Body: { role }
    - role muda para 'condutor'      → cria/reactiva Condutor
    - role muda de 'condutor' para X → desactiva Condutor
    """
    loja    = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro
 
    membro = get_object_or_404(UtilizadorLoja, id=membro_id, loja=loja, ativo=True)
 
    if membro.role == 'dono':
        return Response(
            {'detail': 'Não é possível alterar o role do dono.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    role_anterior = membro.role
    novo_role     = request.data.get('role', role_anterior)
 
    serializer = UtilizadorLojaSerializer(membro, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    serializer.save()
 
    # sincroniza registo Condutor se o role mudou de/para 'condutor'
    if role_anterior != novo_role:
        from ..models import Condutor
        if novo_role == 'condutor':
            # cria ou reactiva
            _sincronizar_condutor(loja, membro.utilizador, request.data.get('tipo_veiculo', ''))
        elif role_anterior == 'condutor':
            # desactiva
            Condutor.objects.filter(loja=loja, utilizador=membro.utilizador).update(ativo=False)
 
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def staff_remove(request, loja_id, membro_id):
    """DELETE /app/loja/<loja_id>/staff/<membro_id>/remover/"""
    loja   = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro
 
    membro = get_object_or_404(UtilizadorLoja, id=membro_id, loja=loja, ativo=True)
 
    if membro.role == 'dono':
        return Response(
            {'detail': 'Não é possível remover o dono da loja.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    membro.ativo = False
    membro.save(update_fields=['ativo'])
 
    # se era condutor → desactiva também o registo Condutor
    if membro.role == 'condutor':
        from ..models import Condutor
        Condutor.objects.filter(loja=loja, utilizador=membro.utilizador).update(ativo=False)
 
    return Response({'detail': 'Membro removido do staff.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def categoria_list(request):
    """GET /app/categorias/ — lista pública de categorias activas"""
    from ..models import Categoria
    cats = Categoria.objects.filter(ativo=True)
    return Response([
        {'id': c.id, 'nome': c.nome, 'icon': c.icon, 'ordem': c.ordem}
        for c in cats
    ])
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_dashboard(request, loja_id):
    """
    GET /app/loja/<loja_id>/dashboard/
    Métricas do backoffice da loja.
    Query params: periodo=7|30|90 (dias, default=30)
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'ver_loja')
    if erro:
        return erro
 
    periodo = int(request.GET.get('periodo', 30))
    inicio  = now() - timedelta(days=periodo)
    inicio_anterior = inicio - timedelta(days=periodo)
 
    from ..models import Encomenda, ItemEncomenda, Comissao, AvaliacaoLoja, Inventario
 
    enc_qs      = Encomenda.objects.filter(loja=loja)
    enc_periodo = enc_qs.filter(data_criacao__gte=inicio)
    enc_ant     = enc_qs.filter(data_criacao__gte=inicio_anterior, data_criacao__lt=inicio)
 
    # ── KPIs principais ──────────────────────────────────────
    total_vendas    = enc_periodo.filter(status='concluido').aggregate(v=Sum('valor_total'))['v'] or 0
    total_vendas_ant= enc_ant.filter(status='concluido').aggregate(v=Sum('valor_total'))['v'] or 0
    total_enc       = enc_periodo.count()
    total_enc_ant   = enc_ant.count()
    enc_concluidas  = enc_periodo.filter(status='concluido').count()
    enc_canceladas  = enc_periodo.filter(status='cancelado').count()
 
    def variacao(actual, anterior):
        if not anterior:
            return None
        return round(((actual - anterior) / anterior) * 100, 1)
 
    # ── Encomendas por estado ─────────────────────────────────
    por_estado = {}
    for s in ['pendente','pago','preparando','enviado','concluido','cancelado']:
        por_estado[s] = enc_qs.filter(status=s).count()
 
    # ── Vendas por dia (últimos N dias) ───────────────────────
    from django.db.models.functions import TruncDate
    vendas_por_dia = (
        enc_qs.filter(data_criacao__gte=inicio, status='concluido')
        .annotate(dia=TruncDate('data_criacao'))
        .values('dia')
        .annotate(total=Sum('valor_total'), count=Count('id'))
        .order_by('dia')
    )
    grafico_vendas = [
        {'dia': str(v['dia']), 'total': float(v['total']), 'count': v['count']}
        for v in vendas_por_dia
    ]
 
    # ── Produtos mais vendidos ────────────────────────────────
    top_produtos = (
        ItemEncomenda.objects
        .filter(encomenda__loja=loja, encomenda__data_criacao__gte=inicio)
        .values('produto__id', 'produto__nome')
        .annotate(total_qty=Sum('quantidade'), total_val=Sum('preco'))
        .order_by('-total_qty')[:5]
    )
    produtos_top = [
        {
            'id':    p['produto__id'],
            'nome':  p['produto__nome'],
            'qty':   p['total_qty'],
            'valor': float(p['total_val'] or 0),
        }
        for p in top_produtos
    ]
 
    # ── Comissões ─────────────────────────────────────────────
    com_qs = Comissao.objects.filter(loja=loja)
    comissao_pendente  = com_qs.filter(status='pendente').aggregate(v=Sum('valor_comissao'))['v'] or 0
    comissao_liquidada = com_qs.filter(status='liquidada').aggregate(v=Sum('valor_comissao'))['v'] or 0
 
    # ── Avaliações ────────────────────────────────────────────
    av_qs       = AvaliacaoLoja.objects.filter(loja=loja)
    rating_med  = av_qs.aggregate(m=Avg('pontuacao'))['m']
    total_aval  = av_qs.count()
    aval_rec    = av_qs.filter(data_criacao__gte=inicio).count()
 
    # ── Stock em alerta ───────────────────────────────────────
    stock_alerta = (
        Inventario.objects.filter(loja=loja, quantidade__lte=5)
        .select_related('produto')
        .values('produto__id', 'produto__nome', 'quantidade')[:10]
    )
    stock_baixo = [
        {'id': s['produto__id'], 'nome': s['produto__nome'], 'qty': s['quantidade']}
        for s in stock_alerta
    ]
 
    return Response({
        'periodo':            periodo,
        # KPIs
        'total_vendas':       float(total_vendas),
        'variacao_vendas':    variacao(total_vendas, total_vendas_ant),
        'total_encomendas':   total_enc,
        'variacao_enc':       variacao(total_enc, total_enc_ant),
        'enc_concluidas':     enc_concluidas,
        'enc_canceladas':     enc_canceladas,
        'taxa_conclusao':     round(enc_concluidas / total_enc * 100, 1) if total_enc else 0,
        # Distribuição
        'por_estado':         por_estado,
        'grafico_vendas':     grafico_vendas,
        'produtos_top':       produtos_top,
        # Financeiro
        'comissao_pendente':  float(comissao_pendente),
        'comissao_liquidada': float(comissao_liquidada),
        # Avaliações
        'rating_medio':       round(float(rating_med), 2) if rating_med else None,
        'total_avaliacoes':   total_aval,
        'avaliacoes_recentes':aval_rec,
        # Stock
        'stock_baixo':        stock_baixo,
        'stock_alerta_count': len(stock_baixo),
    })
    
