"""
Admin → Catálogo: qualidade do catálogo das lojas (utils/qualidade.py). Permissão gerir_lojas.

  GET  /app/admin/qualidade/?estado=ativa|pendente&demo=0       → { resumo, lojas }
  GET  /app/admin/qualidade/lojas/<loja_id>/                     → loja + produtos com problemas
  POST /app/admin/qualidade/lojas/<loja_id>/avisar/              → notifica o dono (uma vez por dia)
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja
from ..utils import qualidade
from ..utils.horarios import fuso
from .adminView import _exige_admin


def _data(d):
    return d.astimezone(fuso()).strftime('%d/%m/%Y %H:%M') if d else None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_qualidade(request):
    erro = _exige_admin(request, 'gerir_lojas')
    if erro:
        return erro
    return Response(qualidade.analisar(estado=request.GET.get('estado'), incluir_demo=request.GET.get('demo') != '0'))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_qualidade_loja(request, loja_id):
    erro = _exige_admin(request, 'gerir_lojas')
    if erro:
        return erro
    loja = get_object_or_404(Loja.objects.select_related('dono__user'), id=loja_id)
    return Response({**qualidade.analisar_loja(loja, com_produtos=True), 'ultimo_aviso': _data(qualidade.ultimo_aviso(loja))})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_qualidade_avisar(request, loja_id):
    erro = _exige_admin(request, 'gerir_lojas')
    if erro:
        return erro
    loja = get_object_or_404(Loja.objects.select_related('dono__user'), id=loja_id)
    if loja.estado not in ('ativa', 'pendente'):
        return Response({'detail': 'Só lojas activas ou pendentes.'}, status=status.HTTP_400_BAD_REQUEST)
    enviado, quando = qualidade.avisar(loja)
    if not enviado and quando:
        return Response({'detail': f'A loja já foi avisada em {_data(quando)} — volta a avisar amanhã.',
                         'ultimo_aviso': _data(quando)}, status=status.HTTP_409_CONFLICT)
    if not enviado:
        return Response({'detail': 'Esta loja não tem nada a rever.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Loja avisada.', 'ultimo_aviso': _data(quando)})
