from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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
    Cria a loja e atribui automaticamente o criador como 'dono'.
    """
    utilizador = request.user.utilizador

    serializer = LojaSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    loja = serializer.save(
        dono=utilizador,
        logo=request.FILES.get('logo'),
        banner=request.FILES.get('banner'),
    )

    # regista o criador como dono no staff
    UtilizadorLoja.objects.create(
        loja=loja,
        utilizador=utilizador,
        role='dono',
        ativo=True,
    )

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
            # reactiva o registo existente com o novo role
            existente.role  = novo_role
            existente.ativo = True
            existente.save(update_fields=['role', 'ativo'])
            return Response(
                UtilizadorLojaSerializer(existente, context={'request': request}).data,
                status=status.HTTP_200_OK
            )

    # utilizador nunca esteve no staff — cria novo registo
    serializer = UtilizadorLojaSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    membro = serializer.save(loja=loja)
    return Response(
        UtilizadorLojaSerializer(membro, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def staff_update_role(request, loja_id, membro_id):
    """
    PATCH /app/loja/<loja_id>/staff/<membro_id>/
    Body: { role }
    """
    loja   = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_staff')
    if erro:
        return erro

    membro = get_object_or_404(UtilizadorLoja, id=membro_id, loja=loja, ativo=True)

    if membro.role == 'dono':
        return Response(
            {'detail': 'Não é possível alterar o role do dono.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UtilizadorLojaSerializer(membro, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
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
    return Response({'detail': 'Membro removido do staff.'})