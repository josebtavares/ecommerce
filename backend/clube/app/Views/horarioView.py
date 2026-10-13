"""
Horário das lojas (backoffice) e fuso horário da plataforma (admin do site).
A lógica está em utils/horarios.py.
"""
from zoneinfo import available_timezones

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, ConfiguracaoPlataforma
from ..utils import horarios
from .lojaView import _exige_permissao
from .adminView import _exige_admin


def _horario_loja(loja):
    return {
        'horario_ativo': loja.horario_ativo,
        'fora_horario':  loja.fora_horario,
        'dias':          horarios.semana(loja),
        'estado':        horarios.payload_publico(loja),
        'fuso':          ConfiguracaoPlataforma.atual().fuso_horario,
        'agora':         horarios.agora().strftime('%H:%M'),
    }


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def loja_horario(request, loja_id):
    """
    GET /app/loja/<loja_id>/horario/
    PUT /app/loja/<loja_id>/horario/
        { horario_ativo, fora_horario: 'agendar'|'bloquear',
          dias: [{dia: 0-6, intervalos: [{abre: 'HH:MM', fecha: 'HH:MM'}]}] }
    """
    loja = get_object_or_404(Loja.objects.select_for_update() if request.method == 'PUT' else Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'editar_loja')
    if erro:
        return erro
    if request.method == 'GET':
        return Response(_horario_loja(loja))

    dados = request.data
    ativo = dados.get('horario_ativo', loja.horario_ativo)
    if not isinstance(ativo, bool):
        return Response({'detail': 'horario_ativo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    fora = dados.get('fora_horario', loja.fora_horario)
    if fora not in dict(Loja.FORA_HORARIO):
        return Response({'detail': 'Escolhe o que acontece com a loja fechada.'}, status=status.HTTP_400_BAD_REQUEST)

    linhas = None
    if 'dias' in dados:
        linhas, msg = horarios.validar_dias(dados.get('dias'))
        if msg:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    tem_intervalos = bool(linhas) if linhas is not None else loja.horarios.exists()
    if ativo and not tem_intervalos:
        return Response({'detail': 'Abre pelo menos um dia antes de ligar o horário.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if linhas is not None:
        horarios.guardar(loja, linhas)
    loja.horario_ativo, loja.fora_horario = ativo, fora
    loja.save(update_fields=['horario_ativo', 'fora_horario', 'data_atualizacao'])
    return Response(_horario_loja(loja))


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_plataforma(request):
    """
    GET   /app/admin/plataforma/
    PATCH /app/admin/plataforma/   { fuso_horario: 'Atlantic/Cape_Verde' }
    """
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    cfg = ConfiguracaoPlataforma.atual()
    if request.method == 'PATCH':
        nome = request.data.get('fuso_horario')
        if not horarios.fuso_valido(nome):
            return Response({'detail': 'Fuso horário inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        cfg = ConfiguracaoPlataforma.objects.get_or_create(pk=1)[0]
        cfg.fuso_horario = nome
        cfg.save()
    hora = timezone.now().astimezone(horarios.fuso())
    return Response({
        'fuso_horario': cfg.fuso_horario,
        'hora_local':   hora.strftime('%d/%m/%Y %H:%M'),
        'utc_offset':   hora.strftime('%z'),
        'fusos':        sorted(available_timezones()),
    })
