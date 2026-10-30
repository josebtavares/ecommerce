"""
Pagamento com cartão (vinti4) — a adesão de cada loja à SISP (utils/vinti4.py).

  GET  /app/loja/<loja_id>/vinti4/       → { adesao, requisitos, ficha, pode_pedir, pede_password, simulado }   (dono)
  POST /app/loja/<loja_id>/vinti4/       { acao: 'pedir' }                                                       (dono)
  PUT  /app/loja/<loja_id>/vinti4/       { pos_id, merchant_id, chave, password } → por_validar                  (dono)
  GET  /app/admin/lojas/<loja_id>/vinti4/                                                                       (gerir_pagamentos)
  POST /app/admin/lojas/<loja_id>/vinti4/ { acao: teste|ativar|suspender|recusar, motivo? }                     (gerir_pagamentos)
"""
from django.shortcuts import get_object_or_404
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja
from ..pagamentos import cobra_a_serio
from ..utils import vinti4
from .adminView import _exige_admin
from .lojaView import _exige_permissao


def _dono(request, loja):
    _, erro = _exige_permissao(request, loja, 'gerir_dados_bancarios')
    if erro:
        return erro
    from ..utils.ver_loja import a_ver
    if a_ver(loja.id, request.user.utilizador):
        return Response({'detail': 'O contrato vinti4 vê-se no Admin → Lojas.'}, status=status.HTTP_403_FORBIDDEN)
    return None


def _lista_loja(request, loja):
    reqs = vinti4.requisitos(loja)
    a = vinti4.adesao(loja)
    return {'adesao': vinti4.payload(a), 'requisitos': reqs, 'ficha': vinti4.ficha(loja),
            'pode_pedir': not a and all(r['ok'] for r in reqs),
            'pede_password': request.user.has_usable_password(), 'simulado': not cobra_a_serio()}


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def loja_vinti4(request, loja_id):
    loja = get_object_or_404(Loja.objects.select_related('dono__user'), id=loja_id)
    erro = _dono(request, loja)
    if erro:
        return erro
    if request.method == 'GET':
        return Response(_lista_loja(request, loja))
    if is_ratelimited(request, group='vinti4', key='user', rate='20/h', increment=True):
        return Response({'detail': 'Demasiados pedidos seguidos. Aguarda um momento.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    try:
        if request.method == 'POST':
            if request.data.get('acao') != 'pedir':
                return Response({'detail': 'Acção inválida.'}, status=status.HTTP_400_BAD_REQUEST)
            vinti4.pedir(loja)
        else:
            if request.user.has_usable_password():
                from .utilizadorView import _password_errada
                erro_password = _password_errada(request, request.data.get('password'))
                if erro_password:
                    return Response({'password': erro_password}, status=status.HTTP_400_BAD_REQUEST)
            _, erros = vinti4.guardar_credenciais(request, loja, request.data.get('pos_id'),
                                                  request.data.get('merchant_id'), request.data.get('chave'))
            if erros:
                return Response(erros, status=status.HTTP_400_BAD_REQUEST)
    except vinti4.ErroVinti4 as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_lista_loja(request, loja))


def _lista_admin(loja):
    return {'adesao': vinti4.payload(vinti4.adesao(loja), admin=True), 'requisitos': vinti4.requisitos(loja),
            'simulado': not cobra_a_serio()}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_loja_vinti4(request, loja_id):
    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro:
        return erro
    loja = get_object_or_404(Loja.objects.select_related('dono__user'), id=loja_id)
    if request.method == 'POST':
        try:
            vinti4.decidir(request, loja, request.data.get('acao'), request.data.get('motivo', ''))
        except vinti4.ErroVinti4 as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_lista_admin(loja))
