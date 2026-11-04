"""
Dinheiro dos condutores (utils/acertos_condutor.py).

GET  /app/loja/<id>/entrega/dinheiro/                       condutor: o que tem consigo + os seus acertos;
                                                            loja (gerir_pagamentos): resumo por condutor + acertos
GET  /app/loja/<id>/entrega/dinheiro/<condutor_id>/         loja: entregas por acertar desse condutor + acertos dele
POST /app/loja/<id>/entrega/dinheiro/<condutor_id>/receber/ loja: {entregas: [ids], nota} → regista o acerto
POST /app/loja/<id>/entrega/dinheiro/acertos/<id>/anular/   loja: {motivo} → anula (fica o registo)
"""
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import AcertoCondutor, Condutor, Loja, UtilizadorLoja
from ..utils import acertos_condutor as A

PERM = 'gerir_pagamentos'


def _membro(request, loja):
    return UtilizadorLoja.obter_membro(loja, request.user.utilizador)


def _da_loja(request, loja):
    m = _membro(request, loja)
    if not m or not m.pode(PERM):
        return Response({'detail': f'Sem permissão: {PERM}'}, status=status.HTTP_403_FORBIDDEN)
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dinheiro(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    m = _membro(request, loja)
    if m and m.role == 'condutor':
        c = Condutor.objects.filter(loja=loja, utilizador=m.utilizador).first()
        if not c:
            return Response({'detail': 'Não és condutor desta loja.'}, status=status.HTTP_403_FORBIDDEN)
        entregas = A.lista_por_acertar(loja, c)
        total = sum((Decimal(e['valor']) for e in entregas), Decimal('0.00'))
        return Response({'condutor': True, 'por_acertar': str(total), 'n': len(entregas), 'entregas': entregas,
                         'acertos': A.historico(loja, c)})
    erro = _da_loja(request, loja)
    if erro:
        return erro
    return Response({'condutor': False, 'condutores': A.resumo(loja), 'acertos': A.historico(loja)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dinheiro_condutor(request, loja_id, condutor_id):
    loja = get_object_or_404(Loja, id=loja_id)
    erro = _da_loja(request, loja)
    if erro:
        return erro
    c = get_object_or_404(Condutor.objects.select_related('utilizador__user'), id=condutor_id, loja=loja)
    entregas = A.lista_por_acertar(loja, c)
    return Response({'condutor_id': c.id, 'nome': A.nome_condutor(c), 'ativo': c.ativo, 'entregas': entregas,
                     'por_acertar': str(sum((Decimal(e['valor']) for e in entregas), Decimal('0.00'))),
                     'acertos': A.historico(loja, c, n=10)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dinheiro_receber(request, loja_id, condutor_id):
    loja = get_object_or_404(Loja, id=loja_id)
    erro = _da_loja(request, loja)
    if erro:
        return erro
    c = get_object_or_404(Condutor.objects.select_related('utilizador__user'), id=condutor_id, loja=loja)
    entregas = request.data.get('entregas')
    if not isinstance(entregas, list):
        return Response({'detail': 'Escolhe as entregas.'}, status=status.HTTP_400_BAD_REQUEST)
    nota = request.data.get('nota') or ''
    if not isinstance(nota, str):
        return Response({'detail': 'Nota inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    acerto, erro = A.receber(loja, c, entregas, request.user, nota)
    if erro:
        return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)
    return Response(A.acerto_dados(acerto), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dinheiro_anular(request, loja_id, acerto_id):
    loja = get_object_or_404(Loja, id=loja_id)
    erro = _da_loja(request, loja)
    if erro:
        return erro
    a = get_object_or_404(AcertoCondutor, id=acerto_id, loja=loja)
    motivo = request.data.get('motivo')
    if not isinstance(motivo, str):
        return Response({'detail': 'Indica o motivo.'}, status=status.HTTP_400_BAD_REQUEST)
    erro = A.anular(a, request.user, motivo)
    if erro:
        return Response({'detail': erro}, status=status.HTTP_400_BAD_REQUEST)
    a.refresh_from_db()
    return Response(A.acerto_dados(a))
