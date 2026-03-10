from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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
    Lista opções de entrega activas da loja (público).
    """
    loja    = get_object_or_404(Loja, id=loja_id, ativa=True)
    opcoes  = OpcaoEntrega.objects.filter(loja=loja, ativa=True)
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
    Cria a entrega para uma encomenda paga.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'atribuir_condutor')
    if erro:
        return erro

    encomenda = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)

    if encomenda.status not in ('pago', 'preparando'):
        return Response(
            {'detail': f'Não é possível criar entrega para encomenda: {encomenda.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if hasattr(encomenda, 'entrega'):
        return Response(
            {'detail': 'Esta encomenda já tem entrega atribuída.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    condutor     = None
    opcao        = None

    if request.data.get('condutor_id'):
        condutor = get_object_or_404(Condutor, id=request.data['condutor_id'], loja=loja, ativo=True)

    if request.data.get('opcao_entrega_id'):
        opcao = get_object_or_404(OpcaoEntrega, id=request.data['opcao_entrega_id'], loja=loja, ativa=True)

    entrega = Entrega.objects.create(
        encomenda     = encomenda,
        condutor      = condutor,
        opcao_entrega = opcao,
        status        = 'atribuido',
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
    Atualiza status ou reatribui condutor.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    encomenda = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)
    entrega   = get_object_or_404(Entrega, encomenda=encomenda)

    # reatribuir condutor
    if 'condutor_id' in request.data:
        condutor = get_object_or_404(
            Condutor, id=request.data['condutor_id'], loja=loja, ativo=True
        )
        entrega.condutor = condutor

    serializer = EntregaSerializer(entrega, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    entrega = serializer.save()

    # se entrega concluída → actualiza encomenda
    if entrega.status == 'entregue':
        from django.utils.timezone import now
        entrega.data_entrega = now()
        entrega.save(update_fields=['data_entrega'])
        encomenda.status = 'concluido'
        encomenda.save(update_fields=['status'])

    return Response(EntregaSerializer(entrega, context={'request': request}).data)


# ══════════════════════════════════════════════════════════════
# AVALIAÇÕES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def avaliacao_list_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/avaliacoes/?offset=0&limit=10
    Lista pública de avaliações de uma loja com paginação.
    """
    loja = get_object_or_404(Loja, id=loja_id, ativa=True)
    qs   = AvaliacaoLoja.objects.filter(loja=loja).order_by('-data_criacao')

    # filtro por pontuação
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
    return Response(
        AvaliacaoLojaSerializer(avaliacao, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


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