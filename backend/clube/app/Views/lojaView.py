import re

from django.db import transaction
from django.db.models import Q, Sum, Count, Avg, Case, When, IntegerField
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils.timezone import now, make_aware
from django.utils.dateparse import parse_date
from datetime import timedelta, datetime, date

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..Views.notificacaoView import notificar_admins, notificar, notificar_staff
from ..models import Loja, UtilizadorLoja, Utilizador, User
from ..Serializers.LojaSerializer import (
    LojaSerializer,
    LojaPublicSerializer,
    LojaMiniSerializer,
    UtilizadorLojaSerializer,
)
from ..utils.pagination import paginar, periodo_dias
from ..utils.password import mensagem_password_fraca
from ..utils.contas import USERNAME_RE, username_em_uso, email_em_uso


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _get_membro(request, loja):
    try:
        return UtilizadorLoja.objects.get(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        return None


def _exige_permissao(request, loja, permissao):
    membro = _get_membro(request, loja)
    if not membro or not membro.pode(permissao):
        return None, Response(
            {'detail': f'Sem permissão: {permissao}'},
            status=status.HTTP_403_FORBIDDEN
        )
    return membro, None


# ══════════════════════════════════════════════════════════════
# LOJA — LEITURA PÚBLICA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def loja_list(request):
    """
    GET /app/loja/?q=pizza&categoria=comida&offset=0&limit=20
                  &entrega=true&localizacao=lisboa
    """
    # estado aberta/fechada nos cards
    qs = Loja.objects.filter(ativa=True).prefetch_related('horarios', 'excecoes')

    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))

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

    # as abertas primeiro (o estado vem de utils/horarios.py, com cache de 1 minuto), depois a ordem pedida
    from ..utils.horarios import ids_fechadas
    qs = qs.annotate(fechada_agora=Case(When(id__in=ids_fechadas(), then=1), default=0, output_field=IntegerField()))
    ordering = request.GET.get('ordering')
    qs = qs.order_by("fechada_agora", ordering if ordering in ['nome', '-nome', '-data_criacao'] else '-data_criacao')

    response, erro = paginar(request, qs, LojaPublicSerializer, limit_default=5)
    if erro:
        return erro
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def loja_get(request, id):
    loja = get_object_or_404(Loja, id=id)
    
    # loja não activa (pendente/fechada/suspensa) — só o dono/staff pode ver
    if not loja.ativa:
        membro = None
        if request.user.is_authenticated:
            membro = UtilizadorLoja.objects.filter(
                loja=loja, utilizador=request.user.utilizador, ativo=True
            ).first()
        if not membro and not (request.user.is_authenticated and request.user.is_staff):
            if loja.estado == 'fechada':
                # o visitante percebe que a loja existe mas está fechada (não é um link partido)
                return Response({'detail': 'Esta loja está temporariamente fechada.',
                                 'estado': 'fechada', 'nome': loja.nome}, status=404)
            return Response({'detail': 'Loja não encontrada.'}, status=404)
    
    return Response(LojaPublicSerializer(loja, context={'request': request}).data)


# ══════════════════════════════════════════════════════════════
# LOJA — CRIAR
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def loja_create(request):
    """POST /app/loja/criar/"""
    utilizador = request.user.utilizador

    if not utilizador.verificado:
        return Response(
            {'detail': 'A tua conta precisa de estar verificada para criar uma loja.'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = LojaSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # como a plataforma vai ganhar com a loja: comissão (por defeito) ou subscrição com um plano
    from ..utils.subscricoes import plano_ativo
    modelo = request.data.get('modelo_cobranca') or 'comissao'
    plano = None
    if modelo not in ('comissao', 'subscricao'):
        return Response({'modelo_cobranca': 'Escolhe comissão ou subscrição.'}, status=status.HTTP_400_BAD_REQUEST)
    if modelo == 'subscricao':
        plano = plano_ativo(request.data.get('plano_id'))
        if not plano:
            return Response({'plano_id': 'Escolhe um dos planos de subscrição.'}, status=status.HTTP_400_BAD_REQUEST)

    loja = serializer.save(
        dono   = utilizador,
        estado = 'pendente',       # aguarda aprovação da plataforma (ativa=False por consequência)
        logo   = request.FILES.get('logo'),
        banner = request.FILES.get('banner'),
        modelo_cobranca = modelo,
    )
    if plano:
        from ..utils import subscricoes
        subscricoes.criar_para_loja_nova(loja, plano)     # arranca quando o admin aprovar a loja

    notificar_admins(
        tipo='loja_pendente',
        titulo=f'Nova loja pendente: {loja.nome}',
        mensagem=f'{utilizador.nome} criou a loja "{loja.nome}" ({loja.categoria}). Aguarda aprovação.',
        loja=loja,
        link='/admin',
    )

    UtilizadorLoja.objects.create(loja=loja, utilizador=utilizador, role='dono', ativo=True)

    metodos = request.data.getlist('metodos_pagamento')
    if metodos:
        from ..models import MetodoPagamento
        for tipo in metodos:
            MetodoPagamento.objects.get_or_create(loja=loja, tipo=tipo, defaults={'ativo': True})

    import json
    opcoes_raw = request.data.get('opcoes_entrega')
    if opcoes_raw:
        try:
            opcoes = json.loads(opcoes_raw)
            from ..models import OpcaoEntrega
            for op in opcoes:
                if op.get('nome'):
                    OpcaoEntrega.objects.create(
                        loja=loja, nome=op['nome'],
                        preco=op.get('preco', 0),
                        tempo_estimado=op.get('tempo_estimado', ''),
                        ativa=True,
                    )
        except (json.JSONDecodeError, TypeError):
            pass

    return Response(
        LojaSerializer(loja, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


# ══════════════════════════════════════════════════════════════
# LOJA — BACKOFFICE
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_backoffice(request, id):
    """GET /app/loja/<id>/backoffice/"""
    loja = get_object_or_404(Loja, id=id)
    _, erro = _exige_permissao(request, loja, 'ver_loja')
    if erro:
        return erro
    return Response(LojaSerializer(loja, context={'request': request}).data)


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

    serializer = LojaSerializer(loja, data=request.data, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    loja = serializer.save(
        logo  =request.FILES.get('logo',   loja.logo),
        banner=request.FILES.get('banner', loja.banner),
    )
    return Response(LojaSerializer(loja, context={'request': request}).data)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def loja_fechar(request, id):
    """
    GET  /app/loja/<id>/fechar/        → { encomendas_pendentes } (aviso antes de fechar)
    POST /app/loja/<id>/fechar/        (DELETE /app/loja/<id>/eliminar/ — compatibilidade)
    O dono fecha a loja: deixa de aparecer no site e de receber encomendas. Nada é apagado;
    as encomendas pagas continuam a ser geridas no backoffice e as ainda por pagar são
    canceladas (já não podem ser pagas). Pode reabrir quando quiser.
    """
    loja = get_object_or_404(Loja, id=id)
    _, erro = _exige_permissao(request, loja, 'apagar_loja')
    if erro:
        return erro
    if request.method == 'GET':
        return Response({'encomendas_pendentes': loja.encomendas.filter(status='pendente').count()})
    if loja.estado != 'ativa':
        return Response({'detail': f'Só uma loja activa pode ser fechada (estado actual: {loja.get_estado_display()}).'},
                        status=status.HTTP_400_BAD_REQUEST)

    canceladas = loja.mudar_estado('fechada', (request.data.get('motivo') or '')[:300])
    notificar_admins(
        tipo='loja_fechada',
        titulo=f'Loja fechada pelo dono: {loja.nome}',
        mensagem=loja.estado_motivo or 'O dono fechou a loja.',
        loja=loja,
        link='/admin',
    )
    return Response({**LojaSerializer(loja, context={'request': request}).data,
                     'encomendas_canceladas': canceladas})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_reabrir(request, id):
    """
    POST /app/loja/<id>/reabrir/
    Só reabre uma loja que o próprio dono fechou (uma loja suspensa só o admin reactiva).
    """
    loja = get_object_or_404(Loja, id=id)
    _, erro = _exige_permissao(request, loja, 'apagar_loja')
    if erro:
        return erro
    if loja.estado != 'fechada':
        return Response({'detail': f'Só uma loja fechada pelo dono pode ser reaberta (estado actual: {loja.get_estado_display()}).'},
                        status=status.HTTP_400_BAD_REQUEST)
    # fechar a loja não serve para fugir à suspensão por falta de pagamento
    from ..models import Subscricao
    if loja.modelo_cobranca == 'subscricao' and Subscricao.objects.filter(loja=loja, estado='suspensa').exists():
        return Response({'detail': 'A subscrição está por pagar — paga a fatura em atraso (Backoffice → Subscrição) e depois reabre a loja.'},
                        status=status.HTTP_400_BAD_REQUEST)

    loja.mudar_estado('ativa')
    return Response(LojaSerializer(loja, context={'request': request}).data)


# ══════════════════════════════════════════════════════════════
# APARÊNCIA — template + cores
# ══════════════════════════════════════════════════════════════

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def loja_aparencia(request, loja_id):
    """
    PATCH /app/loja/<loja_id>/aparencia/
    Body: { template_id, cor_primaria, cor_secundaria, dark_mode }
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'editar_loja')
    if erro:
        return erro

    dados = {}
    for campo in ('cor_primaria', 'cor_secundaria'):
        if campo in request.data:
            valor = str(request.data[campo] or '').strip()
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', valor):
                return Response({'detail': f'{campo}: cor inválida (usa o formato #RRGGBB).'},
                                status=status.HTTP_400_BAD_REQUEST)
            dados[campo] = valor.lower()

    if 'template_id' in request.data:
        valor = str(request.data['template_id'] or '').strip()
        if not re.fullmatch(r'[a-z0-9_]{1,50}', valor):
            return Response({'detail': 'template_id inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        dados['template_id'] = valor

    if 'dark_mode' in request.data:
        valor = request.data['dark_mode']
        dados['dark_mode'] = valor if isinstance(valor, bool) else str(valor).lower() in ('true', '1')

    alterados = list(dados)
    for campo, valor in dados.items():
        setattr(loja, campo, valor)

    if alterados:
        loja.save(update_fields=alterados)

    return Response({
        'template_id':    loja.template_id,
        'cor_primaria':   loja.cor_primaria,
        'cor_secundaria': loja.cor_secundaria,
        'dark_mode':      loja.dark_mode,
    })


# ══════════════════════════════════════════════════════════════
# LOJAS DO UTILIZADOR
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def minhas_lojas(request):
    """GET /app/loja/minhas/"""
    utilizador = request.user.utilizador
    lojas = Loja.objects.filter(
        staff__utilizador=utilizador, staff__ativo=True
    ).distinct()
    return Response(LojaSerializer(lojas, many=True, context={'request': request}).data)


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
    staff = UtilizadorLoja.objects.filter(loja=loja, ativo=True).select_related('utilizador__user')
    return Response(UtilizadorLojaSerializer(staff, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_add(request, loja_id):
    """POST /app/loja/<loja_id>/staff/adicionar/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro

    if request.data.get('role') == 'dono':
        return Response({'detail': 'Não é possível atribuir o role de dono desta forma.'}, status=400)

    utilizador_id = request.data.get('utilizador_id')
    novo_role     = request.data.get('role', 'staff')

    existente = UtilizadorLoja.objects.filter(loja=loja, utilizador_id=utilizador_id).first()
    if existente:
        if existente.ativo:
            return Response({'detail': 'Este utilizador já faz parte do staff.'}, status=400)
        existente.role  = novo_role
        existente.ativo = True
        existente.save(update_fields=['role', 'ativo'])
        if novo_role == 'condutor':
            _sincronizar_condutor(loja, existente.utilizador, request.data.get('tipo_veiculo', ''))
        _notificar_novo_staff(existente.utilizador, loja, novo_role)
        return Response(UtilizadorLojaSerializer(existente, context={'request': request}).data)

    serializer = UtilizadorLojaSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    membro = serializer.save(loja=loja)
    if novo_role == 'condutor':
        _sincronizar_condutor(loja, membro.utilizador, request.data.get('tipo_veiculo', ''))
    _notificar_novo_staff(membro.utilizador, loja, novo_role)

    return Response(
        UtilizadorLojaSerializer(membro, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


def _sincronizar_condutor(loja, utilizador, tipo_veiculo=''):
    from ..models import Condutor
    condutor, criado = Condutor.objects.get_or_create(
        loja=loja, utilizador=utilizador,
        defaults={'tipo_veiculo': tipo_veiculo, 'ativo': True}
    )
    if not criado:
        condutor.ativo = True
        if tipo_veiculo:
            condutor.tipo_veiculo = tipo_veiculo
        condutor.save(update_fields=['ativo', 'tipo_veiculo'])
    return condutor


def _notificar_novo_staff(utilizador, loja, role):
    try:
        notificar(
            utilizador=utilizador, tipo='novo_staff',
            titulo=f'Foste adicionado à loja "{loja.nome}"',
            mensagem=f'Tens o papel de {role} na loja {loja.nome}.',
            loja=loja, link=f'/loja/{loja.id}/backoffice',
        )
    except Exception:
        pass


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def staff_update_role(request, loja_id, membro_id):
    """PATCH /app/loja/<loja_id>/staff/<membro_id>/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro

    membro = get_object_or_404(UtilizadorLoja, id=membro_id, loja=loja, ativo=True)

    if membro.role == 'dono':
        return Response({'detail': 'Não é possível alterar o role do dono.'}, status=400)

    role_anterior = membro.role
    novo_role     = request.data.get('role', role_anterior)

    if role_anterior == 'condutor' and novo_role != 'condutor':
        from ..models import Condutor, Entrega
        condutor = Condutor.objects.filter(loja=loja, utilizador=membro.utilizador).first()
        if condutor:
            entregas_activas = Entrega.objects.filter(
                condutor=condutor, status__in=['atribuido', 'a_caminho']
            ).select_related('encomenda')

            if entregas_activas.exists() and not request.data.get('forcar', False):
                return Response({
                    'detail': f'Este condutor tem {entregas_activas.count()} entrega(s) activa(s). Envia "forcar": true para confirmar.',
                    'entregas_activas': entregas_activas.count(),
                    'requer_confirmacao': True,
                }, status=status.HTTP_409_CONFLICT)

            for entrega in entregas_activas:
                entrega.status = 'falhou'
                entrega.save(update_fields=['status'])
                entrega.encomenda.status = 'preparando'
                entrega.encomenda.save(update_fields=['status'])

            condutor.ativo = False
            condutor.save(update_fields=['ativo'])

    serializer = UtilizadorLojaSerializer(membro, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()

    if novo_role == 'condutor' and role_anterior != 'condutor':
        _sincronizar_condutor(loja, membro.utilizador, request.data.get('tipo_veiculo', ''))

    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def staff_remove(request, loja_id, membro_id):
    """DELETE /app/loja/<loja_id>/staff/<membro_id>/remover/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro

    membro = get_object_or_404(UtilizadorLoja, id=membro_id, loja=loja, ativo=True)
    if membro.role == 'dono':
        return Response({'detail': 'Não é possível remover o dono da loja.'}, status=400)

    if membro.role == 'condutor':
        from ..models import Condutor, Entrega
        condutor = Condutor.objects.filter(loja=loja, utilizador=membro.utilizador).first()
        if condutor:
            entregas_activas = Entrega.objects.filter(
                condutor=condutor, status__in=['atribuido', 'a_caminho']
            ).select_related('encomenda')

            if entregas_activas.exists() and not request.data.get('forcar', False):
                return Response({
                    'detail': f'Este condutor tem {entregas_activas.count()} entrega(s) activa(s). Envia "forcar": true para confirmar.',
                    'entregas_activas': entregas_activas.count(),
                    'requer_confirmacao': True,
                }, status=status.HTTP_409_CONFLICT)

            for entrega in entregas_activas:
                entrega.status = 'falhou'
                entrega.save(update_fields=['status'])
                entrega.encomenda.status = 'preparando'
                entrega.encomenda.save(update_fields=['status'])

            condutor.ativo = False
            condutor.save(update_fields=['ativo'])

    membro.ativo = False
    membro.save(update_fields=['ativo'])
    return Response({'detail': 'Membro removido do staff.'})


# ══════════════════════════════════════════════════════════════
# CATEGORIAS DE LOJA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def categoria_list(request):
    """GET /app/categorias/"""
    from ..models import Categoria
    cats = Categoria.objects.filter(ativo=True)
    return Response([
        {'id': c.id, 'nome': c.nome, 'icon': c.icon, 'ordem': c.ordem}
        for c in cats
    ])


# ══════════════════════════════════════════════════════════════
# PAGAMENTO PÚBLICO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def metodos_pagamento_publico(request, loja_id):
    """GET /app/loja/<loja_id>/pagamento/metodos/"""
    from ..models import MetodoPagamento
    loja = get_object_or_404(Loja, id=loja_id)
    metodos = MetodoPagamento.objects.filter(loja=loja, ativo=True)
    return Response([{'id': m.id, 'tipo': m.tipo, 'ativo': m.ativo} for m in metodos])


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_dashboard(request, loja_id):
    """
    GET /app/loja/<loja_id>/dashboard/
    ?periodo=7|30|90  ou  ?data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD
    """
    from ..models import Encomenda, ItemEncomenda, Comissao, AvaliacaoLoja, Inventario, Entrega

    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'ver_loja')
    if erro:
        return erro

    hoje = date.today()
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str    = request.GET.get('data_fim')

    if data_inicio_str and data_fim_str:
        try:
            inicio = make_aware(datetime.combine(parse_date(data_inicio_str), datetime.min.time()))
            fim    = make_aware(datetime.combine(parse_date(data_fim_str),    datetime.max.time()))
        except Exception:
            return Response({'detail': 'Datas inválidas. Use YYYY-MM-DD.'}, status=400)
        periodo = None
    else:
        periodo = periodo_dias(request)
        inicio  = now() - timedelta(days=periodo)
        fim     = now()
        data_inicio_str = str(hoje - timedelta(days=periodo))
        data_fim_str    = str(hoje)

    duracao          = fim - inicio
    inicio_anterior  = inicio - duracao
    fim_anterior     = inicio

    from ..models import Reembolso
    from ..utils.devolucoes import anotar_liquido, resumo_reembolsos
    # vendas = encomendas concluídas menos o que foi reembolsado delas
    enc_qs      = anotar_liquido(Encomenda.objects.filter(loja=loja))
    enc_periodo = enc_qs.filter(data_criacao__range=(inicio, fim))
    enc_ant     = enc_qs.filter(data_criacao__range=(inicio_anterior, fim_anterior))

    def variacao(actual, anterior):
        if not anterior: return None
        return round(((actual - anterior) / anterior) * 100, 1)

    total_vendas     = enc_periodo.filter(status='concluido').aggregate(v=Sum('liquido'))['v'] or 0
    total_vendas_ant = enc_ant.filter(status='concluido').aggregate(v=Sum('liquido'))['v'] or 0
    vendas_brutas    = enc_periodo.filter(status='concluido').aggregate(v=Sum('valor_total'))['v'] or 0
    # reembolsos feitos no período (inclui cancelamentos de encomendas pagas)
    reemb_qs   = Reembolso.objects.filter(loja=loja)
    reembolsos = resumo_reembolsos(reemb_qs.filter(data_reembolso__range=(inicio, fim)))
    total_enc        = enc_periodo.count()
    total_enc_ant    = enc_ant.count()
    enc_concluidas   = enc_periodo.filter(status='concluido').count()
    enc_canceladas   = enc_periodo.filter(status='cancelado').count()

    por_estado = {
        s: enc_qs.filter(status=s).count()
        for s in ['pendente', 'pago', 'preparando', 'enviado', 'concluido', 'cancelado']
    }

    vendas_por_dia = (
        enc_qs.filter(data_criacao__range=(inicio, fim), status='concluido')
        .annotate(dia=TruncDate('data_criacao'))
        .values('dia')
        .annotate(total=Sum('liquido'), count=Count('id'))
        .order_by('dia')
    )
    grafico_vendas = [
        {'dia': str(v['dia']), 'total': float(v['total']), 'count': v['count']}
        for v in vendas_por_dia
    ]

    # unidades vendidas sozinhas + dentro de menus/conjuntos (encomendas canceladas não contam)
    from ..utils.conjuntos import vendas_por_produto
    itens = (ItemEncomenda.objects
             .filter(encomenda__loja=loja, encomenda__data_criacao__range=(inicio, fim))
             .exclude(encomenda__status='cancelado')
             .values_list('produto__id', 'produto__nome', 'quantidade', 'preco', 'componentes'))
    produtos_top = [
        {'id': p['id'], 'nome': p['nome'], 'qty': p['qty'], 'valor': round(p['valor'], 2),
         'qty_direto': p['qty_direto'], 'qty_conjuntos': p['qty_conjuntos']}
        for p in vendas_por_produto(('loja', pid, nome, q, preco, comps) for pid, nome, q, preco, comps in itens)[:5]
    ]

    com_qs = Comissao.objects.filter(loja=loja)
    comissao_pendente  = com_qs.filter(status='pendente').aggregate(v=Sum('valor_comissao'))['v'] or 0
    comissao_liquidada = com_qs.filter(status='liquidada').aggregate(v=Sum('valor_comissao'))['v'] or 0
    comissao_periodo   = com_qs.filter(data_criacao__range=(inicio, fim)).aggregate(v=Sum('valor_comissao'))['v'] or 0

    av_qs      = AvaliacaoLoja.objects.filter(loja=loja)
    rating_med = av_qs.aggregate(m=Avg('pontuacao'))['m']

    stock_alerta = (
        Inventario.objects.filter(loja=loja, quantidade__lte=5, produto__e_conjunto=False)
        .select_related('produto')
        .values('produto__id', 'produto__nome', 'quantidade')[:10]
    )
    stock_baixo = [
        {'id': s['produto__id'], 'nome': s['produto__nome'], 'qty': s['quantidade']}
        for s in stock_alerta
    ]

    ent_qs      = Entrega.objects.filter(encomenda__loja=loja)
    ent_periodo = ent_qs.filter(data_criacao__range=(inicio, fim))
    entregas_por_status = {
        s: ent_qs.filter(status=s).count()
        for s in ['atribuido', 'a_caminho', 'entregue', 'falhou']
    }
    entregas_periodo    = ent_periodo.count()
    entregas_concluidas = ent_periodo.filter(status='entregue').count()
    entregas_falhadas   = ent_periodo.filter(status='falhou').count()
    taxa_entrega        = round(entregas_concluidas / entregas_periodo * 100, 1) if entregas_periodo else 0

    return Response({
        'periodo':              periodo,
        'data_inicio':          data_inicio_str,
        'data_fim':             data_fim_str,
        'total_vendas':         float(total_vendas),          # líquido de reembolsos
        'vendas_brutas':        float(vendas_brutas),
        'variacao_vendas':      variacao(total_vendas, total_vendas_ant),
        'reembolsos_periodo':   reembolsos['total'],
        'reembolsos_count':     reembolsos['count'],
        'reembolsos_por_responder': reemb_qs.filter(estado='pedido').count(),
        'credito_comissao':     float(loja.creditos_comissao.filter(estado='pendente')
                                      .aggregate(v=Sum('valor'))['v'] or 0),
        'total_encomendas':     total_enc,
        'variacao_enc':         variacao(total_enc, total_enc_ant),
        'enc_concluidas':       enc_concluidas,
        'enc_canceladas':       enc_canceladas,
        'taxa_conclusao':       round(enc_concluidas / total_enc * 100, 1) if total_enc else 0,
        'por_estado':           por_estado,
        'grafico_vendas':       grafico_vendas,
        'produtos_top':         produtos_top,
        'comissao_pendente':    float(comissao_pendente),
        'comissao_liquidada':   float(comissao_liquidada),
        'comissao_periodo':     float(comissao_periodo),
        'rating_medio':         round(float(rating_med), 2) if rating_med else None,
        'total_avaliacoes':     av_qs.count(),
        'avaliacoes_recentes':  av_qs.filter(data_criacao__range=(inicio, fim)).count(),
        'stock_baixo':          stock_baixo,
        'stock_alerta_count':   len(stock_baixo),
        'entregas_por_status':  entregas_por_status,
        'entregas_periodo':     entregas_periodo,
        'entregas_concluidas':  entregas_concluidas,
        'entregas_falhadas':    entregas_falhadas,
        'taxa_entrega':         taxa_entrega,
    })
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@transaction.atomic
def staff_criar_utilizador(request, loja_id):
    """
    POST /app/loja/<loja_id>/staff/criar-utilizador/
    Body (multipart ou JSON): { username, email, password, role,
                                first_name?, last_name?, telefone?, morada?, foto?, tipo_veiculo? }
    Cria utilizador novo + adiciona à loja com role especificado
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro

    # Validar dados do utilizador
    username = str(request.data.get('username', '')).strip()
    email = str(request.data.get('email', '')).strip()
    password = str(request.data.get('password', ''))
    role = request.data.get('role', 'staff')

    if not username or not email or not password:
        return Response({'detail': 'Username, email e password são obrigatórios.'}, status=400)

    roles_validos = [r for r, _ in UtilizadorLoja.ROLES if r != 'dono']
    if role not in roles_validos:
        return Response({'detail': 'Role inválido.'}, status=400)

    msg_password = mensagem_password_fraca(password)
    if msg_password:
        return Response({'detail': msg_password}, status=400)

    foto = request.FILES.get('foto')
    if foto:
        if foto.size > 5 * 1024 * 1024:
            return Response({'detail': 'A foto não pode ter mais de 5 MB.'}, status=400)
        if not (foto.content_type or '').startswith('image/'):
            return Response({'detail': 'A foto tem de ser uma imagem.'}, status=400)

    if not USERNAME_RE.match(username):
        return Response({'detail': 'O username só pode ter letras, números e @ . + - _ (3 a 150 caracteres).'}, status=400)

    if username_em_uso(username):
        return Response({'detail': 'Username já existe.'}, status=400)

    if email_em_uso(email):
        return Response({'detail': 'Email já está registado.'}, status=400)

    # Criar User Django
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=request.data.get('first_name', ''),
        last_name=request.data.get('last_name', '')
    )

    # Criar Utilizador
    utilizador = Utilizador.objects.create(
        user=user,
        telefone=request.data.get('telefone', ''),
        morada=request.data.get('morada', ''),
        verificado=False  # criado por gestor → não verificado
    )
    if foto:
        utilizador.foto = foto
        utilizador.save(update_fields=['foto'])

    # Adicionar à loja com role
    membro = UtilizadorLoja.objects.create(
        loja=loja,
        utilizador=utilizador,
        role=role,
        ativo=True
    )

    if role == 'condutor':
        _sincronizar_condutor(loja, utilizador, request.data.get('tipo_veiculo', ''))

    _notificar_novo_staff(utilizador, loja, role)

    return Response(
        UtilizadorLojaSerializer(membro, context={'request': request}).data,
        status=201
    )