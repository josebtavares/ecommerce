from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from ..Views.notificacaoView import notificar_staff, notificar_admins, notificar
from decimal import Decimal


from ..models import (
    OpcaoEntrega, Condutor, Entrega,
    AvaliacaoLoja, Loja, Encomenda, UtilizadorLoja,
)
from ..Serializers.EntregaAvaliacaoSerializer import (
    OpcaoEntregaSerializer,
    CondutorSerializer,
    EntregaSerializer,
    AvaliacaoLojaSerializer,
    AvaliacaoMiniSerializer,
)
from ..utils.pagination import paginar


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════

def _exige_permissao(request, loja, permissao):
    try:
        membro = UtilizadorLoja.objects.get(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        membro = None

    if not membro or not membro.pode(permissao):
        return None, Response(
            {'detail': f'Sem permissão: {permissao}'},
            status=status.HTTP_403_FORBIDDEN
        )
    return membro, None


# ══════════════════════════════════════════════════════════════
# OPÇÕES DE ENTREGA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def opcao_entrega_list(request, loja_id):
    """
    GET /app/loja/<loja_id>/entrega/opcoes/
    - Público (checkout): só lojas activas
    - Backoffice (dono): acede mesmo com loja inactiva
    """
    # tenta obter a loja sem filtro de ativa
    loja = get_object_or_404(Loja, id=loja_id)
 
    # se loja inactiva, só o dono/staff consegue ver
    if not loja.ativa:
        if not request.user.is_authenticated:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        membro = UtilizadorLoja.objects.filter(
            loja=loja,
            utilizador=request.user.utilizador,
            ativo=True
        ).first()
        if not membro and not request.user.is_staff:
            from rest_framework.exceptions import NotFound
            raise NotFound()
 
    opcoes = OpcaoEntrega.objects.filter(loja=loja, ativa=True)
    serializer = OpcaoEntregaSerializer(opcoes, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def opcao_entrega_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/entrega/opcoes/criar/
    Body: { nome, preco, tempo_estimado, area_cobertura }
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_opcoes_entrega')
    if erro:
        return erro

    serializer = OpcaoEntregaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    opcao = serializer.save(loja=loja)
    return Response(OpcaoEntregaSerializer(opcao).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def opcao_entrega_gerir(request, loja_id, opcao_id):
    """
    PATCH  /app/loja/<loja_id>/entrega/opcoes/<opcao_id>/  → editar
    DELETE /app/loja/<loja_id>/entrega/opcoes/<opcao_id>/  → desactivar
    """
    loja  = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_opcoes_entrega')
    if erro:
        return erro

    opcao = get_object_or_404(OpcaoEntrega, id=opcao_id, loja=loja)

    if request.method == 'DELETE':
        opcao.ativa = False
        opcao.save(update_fields=['ativa'])
        return Response({'detail': 'Opção de entrega desactivada.'})

    serializer = OpcaoEntregaSerializer(opcao, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# CONDUTORES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def condutor_list(request, loja_id):
    """GET /app/loja/<loja_id>/entrega/condutores/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    condutores = Condutor.objects.filter(loja=loja, ativo=True).select_related('utilizador__user')
    serializer = CondutorSerializer(condutores, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def condutor_adicionar(request, loja_id):
    """
    POST /app/loja/<loja_id>/entrega/condutores/adicionar/
    Body: { utilizador_id, tipo_veiculo }
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    serializer = CondutorSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    condutor = serializer.save(loja=loja)
    return Response(CondutorSerializer(condutor, context={'request': request}).data,
                    status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def condutor_remover(request, loja_id, condutor_id):
    """DELETE /app/loja/<loja_id>/entrega/condutores/<condutor_id>/remover/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    condutor = get_object_or_404(Condutor, id=condutor_id, loja=loja)
    condutor.ativo = False
    condutor.save(update_fields=['ativo'])
    return Response({'detail': 'Condutor removido.'})


# ══════════════════════════════════════════════════════════════
# ENTREGA
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def entrega_criar(request, loja_id, encomenda_id):
    """
    POST /app/loja/<loja_id>/encomendas/<encomenda_id>/entrega/criar/
    Body: { condutor_id?, opcao_entrega_id? }
 
    - Sem entrega existente    → cria nova
    - Entrega com status=falhou → reatribui + repõe atribuido + encomenda volta a enviado
    - Entrega noutro estado     → erro
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'atribuir_condutor')
    if erro:
        return erro
 
    encomenda = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)
 
    if encomenda.status not in ('pago', 'preparando', 'enviado'):
        return Response(
            {'detail': f'Não é possível criar/reatribuir entrega para encomenda: {encomenda.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    condutor = None
    if request.data.get('condutor_id'):
        condutor = get_object_or_404(Condutor, id=request.data['condutor_id'], loja=loja, ativo=True)
 
    opcao = None
    opcao_id = request.data.get('opcao_entrega_id')
    if opcao_id:
        opcao = get_object_or_404(OpcaoEntrega, id=opcao_id, loja=loja, ativa=True)
    elif hasattr(encomenda, 'opcao_entrega') and encomenda.opcao_entrega:
        opcao = encomenda.opcao_entrega
 
    # ── entrega já existe ─────────────────────────────────────
    if hasattr(encomenda, 'entrega'):
        entrega = encomenda.entrega
        if entrega.status == 'falhou':
            # reatribui — repõe para atribuido
            entrega.condutor = condutor
            entrega.status   = 'atribuido'
            if opcao:
                entrega.opcao_entrega = opcao
            entrega.save(update_fields=['condutor', 'status', 'opcao_entrega'])
 
            # encomenda volta a "enviado"
            encomenda.status = 'enviado'
            encomenda.save(update_fields=['status'])
 
            if condutor:
                from ..Views.notificacaoView import notificar
                notificar(
                    utilizador=condutor.utilizador,
                    tipo='entrega_atribuida',
                    titulo=f'Entrega reatribuída — Encomenda #{encomenda.id}',
                    mensagem=f'{loja.nome} · {encomenda.morada_entrega or "Levantamento"}.',
                    loja=loja,
                    link=f'/loja/{loja.id}/backoffice',
                )
            return Response(
                EntregaSerializer(entrega, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Esta encomenda já tem entrega atribuída.'},
                status=status.HTTP_400_BAD_REQUEST
            )
 
    # ── cria nova entrega ─────────────────────────────────────
    entrega = Entrega.objects.create(
        encomenda     = encomenda,
        condutor      = condutor,
        opcao_entrega = opcao,
        status        = 'atribuido',
    )
 
    if condutor:
        from ..Views.notificacaoView import notificar
        notificar(
            utilizador=condutor.utilizador,
            tipo='entrega_atribuida',
            titulo=f'Nova entrega atribuída — Encomenda #{encomenda.id}',
            mensagem=f'{loja.nome} · {encomenda.morada_entrega or "Levantamento"}.',
            loja=loja,
            link=f'/loja/{loja.id}/backoffice',
        )
 
    return Response(
        EntregaSerializer(entrega, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def entrega_get(request, loja_id, encomenda_id):
    """GET /app/loja/<loja_id>/encomendas/<encomenda_id>/entrega/"""
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    encomenda = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)
    entrega   = get_object_or_404(Entrega, encomenda=encomenda)
    serializer = EntregaSerializer(entrega, context={'request': request})
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def entrega_atualizar(request, loja_id, encomenda_id):
    """
    PATCH /app/loja/<loja_id>/encomendas/<encomenda_id>/entrega/atualizar/
    Body: { status?, condutor_id? }
 
    status=entregue  → encomenda passa a "concluido"
    status=falhou    → encomenda volta a "preparando" (para reatribuir)
    condutor_id      → reatribui condutor sem mudar status
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro
 
    encomenda = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)
    entrega   = get_object_or_404(Entrega, encomenda=encomenda)
 
    # reatribuir condutor
    if 'condutor_id' in request.data:
        condutor = get_object_or_404(Condutor, id=request.data['condutor_id'], loja=loja, ativo=True)
        entrega.condutor = condutor
        if entrega.status == 'falhou':
            entrega.status = 'atribuido'
            encomenda.status = 'enviado'
            encomenda.save(update_fields=['status'])
            
        entrega.save(update_fields=['condutor', 'status'])
 
        # notifica novo condutor
        notificar(
            utilizador=condutor.utilizador,
            tipo='entrega_atribuida',
            titulo=f'Entrega reatribuída — Encomenda #{encomenda.id}',
            mensagem=f'{loja.nome} · {encomenda.morada_entrega or "Levantamento"}.',
            loja=loja,
            link=f'/loja/{loja.id}/backoffice',
        )
 
        serializer = EntregaSerializer(entrega, context={'request': request})
        return Response(serializer.data)
 
    # actualizar status
    novo_status = request.data.get('status')
    if novo_status:
        serializer = EntregaSerializer(entrega, data={'status': novo_status}, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        entrega = serializer.save()
 
        if novo_status == 'entregue':
            # entrega concluída → encomenda concluída
            from django.utils.timezone import now
            entrega.data_entrega = now()
            entrega.save(update_fields=['data_entrega'])
            encomenda.status = 'concluido'
            encomenda.save(update_fields=['status'])
 
            notificar(
                    utilizador=encomenda.comprador,
                    tipo='encomenda_concluida',
                    titulo=f'Encomenda #{encomenda.id} entregue!',
                    mensagem='A tua encomenda foi entregue. Obrigado pela compra!',
                    loja=encomenda.loja,
                    link='/perfil',
                )
            # pagamento dinheiro pendente → aprova + regista comissão
            try:
                pagamento = encomenda.pagamento
                if pagamento.referencia_transacao == 'dinheiro' and pagamento.status == 'pendente':
                    pagamento.status = 'aprovado'
                    pagamento.save(update_fields=['status'])
                    from ..models import Comissao
                    Comissao.registar(encomenda)
            except Exception:
                pass
 
            _perc = loja.percentagem_comissao
            _com  = (encomenda.valor_total * _perc / 100).quantize(Decimal('0.01'))
            _liq  = encomenda.valor_total - _com
            notificar_staff(
                loja=loja,
                roles=['dono', 'gestor'],
                tipo='encomenda_concluida_loja',
                titulo=f'Encomenda #{encomenda.id} concluída ✓',
                mensagem=f'Receita: €{encomenda.valor_total} · Líquido: €{_liq}.',
                link=f'/loja/{loja.id}/backoffice',
            )
            try:
                if encomenda.pagamento.referencia_transacao == 'dinheiro':
                    notificar_admins(
                        tipo='comissao_recebida',
                        titulo=f'Comissão registada — {loja.nome}',
                        mensagem=f'Encomenda #{encomenda.id} · Comissão: €{_com}.',
                        loja=loja,
                        link='/admin',
                    )
            except Exception:
                pass
 
        elif novo_status == 'falhou':
            # entrega falhou → encomenda volta a "preparando" para reatribuição
            encomenda.status = 'preparando'
            encomenda.save(update_fields=['status'])
 
            notificar_staff(
                loja=loja,
                roles=['dono', 'gestor'],
                tipo='entrega_cancelada',
                titulo=f'Entrega falhou — Encomenda #{encomenda.id}',
                mensagem='A encomenda voltou ao estado "preparando". Podes atribuir outro condutor.',
                link=f'/loja/{loja.id}/backoffice',
            )
 
    serializer = EntregaSerializer(entrega, context={'request': request})
    return Response(serializer.data)


# ══════════════════════════════════════════════════════════════
# AVALIAÇÕES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def avaliacao_list_loja(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id, ativa=True)
    qs   = AvaliacaoLoja.objects.filter(loja=loja).order_by('-data_criacao')

    # por defeito filtra ocultas — staff pode pedir para ver todas
    incluir_ocultas = request.GET.get('incluir_ocultas') == 'true'
    if incluir_ocultas and request.user.is_authenticated:
        eh_staff = UtilizadorLoja.objects.filter(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        ).exists()
        if not eh_staff:
            incluir_ocultas = False

    if not incluir_ocultas:
        qs = qs.filter(oculta=False)

    pontuacao = request.GET.get('pontuacao')
    if pontuacao:
        qs = qs.filter(pontuacao=pontuacao)

    response, erro = paginar(request, qs, AvaliacaoMiniSerializer, limit_default=10)
    if erro:
        return erro
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def avaliacao_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/avaliacoes/criar/
    Body: { encomenda_id, pontuacao, comentario? }
    Só o comprador pode avaliar, só após encomenda concluída.
    """
    loja = get_object_or_404(Loja, id=loja_id, ativa=True)

    data = request.data.copy()
    data['loja'] = loja.id

    serializer = AvaliacaoLojaSerializer(
        data=data, context={'request': request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    avaliacao = serializer.save()
    estrelas = '⭐' * avaliacao.pontuacao
    notificar_staff(
        loja=loja,
        roles=['dono', 'gestor'],
        tipo='avaliacao_recebida',
        titulo=f'Nova avaliação {estrelas}',
        mensagem=avaliacao.comentario[:120] if avaliacao.comentario else f'{avaliacao.pontuacao} estrelas.',
        link=f'/loja/{loja.id}/backoffice',
    )
    return Response(
        AvaliacaoLojaSerializer(avaliacao, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def avaliacao_editar(request, loja_id, avaliacao_id):
    """
    PATCH /app/loja/<loja_id>/avaliacoes/<avaliacao_id>/editar/
    Só o autor pode editar.
    """
    avaliacao  = get_object_or_404(AvaliacaoLoja, id=avaliacao_id, loja_id=loja_id)
    utilizador = request.user.utilizador
 
    if avaliacao.utilizador != utilizador:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
 
    # só permite alterar pontuação e comentário
    data = {}
    if 'pontuacao' in request.data:
        data['pontuacao'] = request.data['pontuacao']
    if 'comentario' in request.data:
        data['comentario'] = request.data['comentario']
 
    serializer = AvaliacaoLojaSerializer(avaliacao, data=data, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    serializer.save()
    return Response(AvaliacaoMiniSerializer(avaliacao).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def avaliacao_ocultar(request, loja_id, avaliacao_id):
    """
    PATCH /app/loja/<loja_id>/avaliacoes/<avaliacao_id>/ocultar/
    Toggle oculta — só dono/gestor da loja pode ocultar.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'ver_loja')
    if erro:
        return erro
 
    avaliacao = get_object_or_404(AvaliacaoLoja, id=avaliacao_id, loja=loja)
    avaliacao.oculta = not avaliacao.oculta
    avaliacao.save(update_fields=['oculta'])
    return Response({'id': avaliacao.id, 'oculta': avaliacao.oculta})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def avaliacao_apagar(request, loja_id, avaliacao_id):
    """
    DELETE /app/loja/<loja_id>/avaliacoes/<avaliacao_id>/apagar/
    Só o autor pode apagar a sua avaliação.
    """
    avaliacao  = get_object_or_404(AvaliacaoLoja, id=avaliacao_id, loja_id=loja_id)
    utilizador = request.user.utilizador

    if avaliacao.utilizador != utilizador:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    avaliacao.delete()
    return Response({'detail': 'Avaliação apagada.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def entrega_list_loja(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    qs = Entrega.objects.filter(
        encomenda__loja=loja
    ).select_related(
        'condutor__utilizador__user',
        'opcao_entrega',
        'encomenda__comprador__user',
        'encomenda__comprador',
        'encomenda__pagamento__metodo',
        'encomenda__opcao_entrega',
    ).order_by('-data_criacao')

    status_filtro = request.GET.get('status')
    if status_filtro:
        qs = qs.filter(status=status_filtro)

    # condutor só vê as suas
    try:
        membro = UtilizadorLoja.objects.get(loja=loja, utilizador=request.user.utilizador, ativo=True)
        if membro.role == 'condutor':
            condutor = Condutor.objects.filter(loja=loja, utilizador=request.user.utilizador).first()
            if condutor:
                qs = qs.filter(condutor=condutor)
    except UtilizadorLoja.DoesNotExist:
        pass

    response, erro = paginar(request, qs, EntregaSerializer, limit_default=10)
    if erro:
        return erro
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pode_avaliar_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/avaliacoes/pode-avaliar/
    Devolve a próxima encomenda concluída ainda sem avaliação.
    Uma avaliação por encomenda — mas pode avaliar várias vezes se tiver várias encomendas.
    """
    utilizador = request.user.utilizador
    loja = get_object_or_404(Loja, id=loja_id)
 
    from ..models import Encomenda
 
    # encomendas concluídas desta loja ainda sem avaliação
    ja_avaliadas = AvaliacaoLoja.objects.filter(
        utilizador=utilizador, loja=loja
    ).values_list('encomenda_id', flat=True)
 
    proxima = Encomenda.objects.filter(
        comprador=utilizador,
        loja=loja,
        status='concluido'
    ).exclude(id__in=ja_avaliadas).first()
 
    total_encomendas  = Encomenda.objects.filter(comprador=utilizador, loja=loja, status='concluido').count()
    total_avaliacoes  = AvaliacaoLoja.objects.filter(utilizador=utilizador, loja=loja).count()
 
    return Response({
        'pode_avaliar':         proxima is not None,
        'encomenda_id':         proxima.id if proxima else None,
        'total_encomendas':     total_encomendas,
        'total_avaliacoes':     total_avaliacoes,
        'avaliacoes_restantes': max(0, total_encomendas - total_avaliacoes),
    })
 