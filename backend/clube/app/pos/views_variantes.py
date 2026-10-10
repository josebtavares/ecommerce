"""
POS — tipos de produto e stock por variação.

Tipos disponíveis:
  ?para=pos  → produtos próprios do POS: globais + tipos do POS (editáveis aqui)
  ?para=loja → produtos da loja ligada:   globais + tipos da loja (só leitura no POS)
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from app.models import Produto, TipoProduto
from app.Serializers.ProdutoSerializer import TipoProdutoSerializer
from app.utils.tipos import tipos_para_loja, tipos_para_pos
from app.utils.variantes import grelha_variantes, guardar_grelha

from .models import ProdutoPOS
from .permissions import POSAuthentication, IsPOSAuthenticated
from .views import _resolve_pos_request, _verificar_permissao_loja_produtos


def _pode_gerir_produtos(membro):
    return membro is None or membro.pode_gerir_produtos


def _tipo_payload(tipo, pos):
    data = TipoProdutoSerializer(tipo).data
    data['origem'] = 'global' if tipo.is_global else ('pos' if tipo.pos_id == pos.id else 'loja')
    data['editavel'] = tipo.pos_id == pos.id
    return data


# ══════════════════════════════════════════════════════════════
# TIPOS
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_tipos(request, pos_id):
    """
    GET  /api/pos/<pos_id>/tipos/?para=pos|loja
    POST /api/pos/<pos_id>/tipos/   Body: { nome, descricao?, atributos_schema }  → tipo próprio do POS
    """
    pos, membro, _ = _resolve_pos_request(request, pos_id, ativo=True)

    if request.method == 'GET':
        para = request.GET.get('para', 'pos')
        if para == 'loja':
            if not pos.loja_vinculada:
                return Response([])
            qs = tipos_para_loja(pos.loja_vinculada)
        else:
            qs = tipos_para_pos(pos)
        return Response([_tipo_payload(t, pos) for t in qs.order_by('nome')])

    if not _pode_gerir_produtos(membro):
        return Response({'detail': 'Sem permissão para gerir produtos.'}, status=status.HTTP_403_FORBIDDEN)
    if pos.modo not in ['standalone', 'hibrido']:
        return Response({'detail': 'Os tipos do POS servem os produtos próprios — este POS não os tem.'},
                        status=status.HTTP_400_BAD_REQUEST)

    nome = str(request.data.get('nome') or '').lower().strip()
    if TipoProduto.objects.filter(pos=pos, nome=nome).exists():
        return Response({'nome': 'Já existe um tipo com este nome neste POS.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TipoProdutoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tipo = serializer.save(pos=pos, loja=None)
    return Response(_tipo_payload(tipo, pos), status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_tipo_gerir(request, pos_id, tipo_id):
    """
    PATCH  /api/pos/<pos_id>/tipos/<tipo_id>/   → editar tipo próprio do POS
    DELETE /api/pos/<pos_id>/tipos/<tipo_id>/   → desactivar (os produtos mantêm-no)
    """
    pos, membro, _ = _resolve_pos_request(request, pos_id, ativo=True)
    if not _pode_gerir_produtos(membro):
        return Response({'detail': 'Sem permissão para gerir produtos.'}, status=status.HTTP_403_FORBIDDEN)

    # só os tipos do próprio POS são editáveis aqui (globais → admin; da loja → backoffice)
    tipo = get_object_or_404(TipoProduto, id=tipo_id, pos=pos)

    if request.method == 'DELETE':
        tipo.ativo = False
        tipo.save(update_fields=['ativo'])
        return Response({'detail': 'Tipo desactivado.'})

    if 'nome' in request.data:
        nome = str(request.data.get('nome') or '').lower().strip()
        if TipoProduto.objects.filter(pos=pos, nome=nome).exclude(id=tipo.id).exists():
            return Response({'nome': 'Já existe um tipo com este nome neste POS.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TipoProdutoSerializer(tipo, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tipo = serializer.save()
    return Response(_tipo_payload(tipo, pos))


# ══════════════════════════════════════════════════════════════
# GRELHA DE VARIAÇÕES (produto do POS ou da loja ligada)
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'PUT'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def pos_produto_variantes(request, pos_id, produto_id):
    """
    GET/PUT /api/pos/<pos_id>/produtos/<produto_id>/variantes/?origem=pos|loja
    Mesmo contrato do backoffice (/app/loja/<loja>/produtos/<id>/variantes/).
    """
    pos, membro, utilizador = _resolve_pos_request(request, pos_id, ativo=True)
    origem = request.GET.get('origem') or request.data.get('origem') or 'pos'

    if origem == 'pos':
        if not _pode_gerir_produtos(membro):
            return Response({'detail': 'Sem permissão para gerir produtos.'}, status=status.HTTP_403_FORBIDDEN)
        produto = get_object_or_404(ProdutoPOS.objects.select_related('tipo'), id=produto_id, pos=pos)
    elif origem == 'loja':
        # o stock da loja é partilhado com as vendas online → só o dono/gestores da loja
        if membro:
            return Response({'detail': 'Membros não podem gerir o stock da loja Bendi.'},
                            status=status.HTTP_403_FORBIDDEN)
        if not pos.loja_vinculada:
            return Response({'detail': 'Este POS não está ligado a uma loja.'}, status=status.HTTP_400_BAD_REQUEST)
        if not _verificar_permissao_loja_produtos(pos.loja_vinculada, utilizador):
            return Response({'detail': 'Sem permissão para gerir produtos desta loja.'}, status=status.HTTP_403_FORBIDDEN)
        produto = get_object_or_404(Produto.objects.select_related('tipo'), id=produto_id, loja=pos.loja_vinculada)
    else:
        return Response({'detail': 'Origem inválida. Usa "pos" ou "loja".'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        return Response(grelha_variantes(produto))

    grelha, erro = guardar_grelha(produto, request.data)
    if erro:
        return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)
    return Response(grelha)
