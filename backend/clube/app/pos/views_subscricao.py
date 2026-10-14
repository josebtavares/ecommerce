"""
Subscrição do POS (utils/subscricoes_pos.py) — só a conta principal (o dono) a vê e paga;
os membros da equipa não. Funciona mesmo com o POS suspenso (é por aqui que se paga).
  GET   /api/pos/planos/                                   planos de POS (criação do POS)
  GET   /api/pos/<pos_id>/subscricao/                      estado, faturas, planos, aviso
  PATCH /api/pos/<pos_id>/subscricao/   { auto_renovar }
  POST  /api/pos/<pos_id>/subscricao/plano/   { plano_id }  escolher / mudar de plano
  POST  /api/pos/<pos_id>/subscricao/faturas/<fid>/pagar/  pagamento (simulado)
"""
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from rest_framework.response import Response

from app.models import ConfiguracaoPlataforma, FaturaSubscricao, Subscricao
from ..utils import subscricoes as subs
from ..utils import subscricoes_pos as subs_pos
from .models import ConfiguracaoPOS
from .permissions import IsPOSAuthenticated, POSAuthentication, get_membro_from_request


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detail': msg}, status=codigo)


def _pos_do_dono(request, pos_id):
    """(pos, None) ou (None, resposta de erro). Membros da equipa não gerem a subscrição."""
    if get_membro_from_request(request):
        return None, _erro('Só o dono do POS gere a subscrição.', status.HTTP_403_FORBIDDEN)
    utilizador = getattr(request.user, 'utilizador', None)
    if not utilizador:
        return None, _erro('Sem permissão.', status.HTTP_403_FORBIDDEN)
    return get_object_or_404(ConfiguracaoPOS, id=pos_id, dono=utilizador), None


def _dias_teste():
    return ConfiguracaoPlataforma.atual().subscricao_dias_teste


def _resumo(pos):
    sub = subs_pos.garantir(pos)
    with transaction.atomic():
        cob = subs_pos.sincronizar(Subscricao.objects.select_for_update().get(pk=sub.pk))
    sub.refresh_from_db()
    pos.refresh_from_db()
    faturas = list(sub.faturas.select_related('plano', 'pos')[:24])
    pendentes = [f for f in faturas if f.estado == 'pendente']
    return {
        'pos_id': pos.id,
        'aviso': subs_pos.aviso_pos(sub, pendentes, cob=cob),
        'subscricao': subs.subscricao_payload(sub),
        'sem_plano': not sub.plano_id,
        # incluído no plano Loja + POS da loja ligada: não paga o POS à parte
        'cobertura': {'loja_id': cob.loja_id, 'loja_nome': cob.loja.nome, 'estado': cob.estado,
                      'plano': subs.plano_payload(subs.plano_em_curso(cob) or cob.plano)} if cob else None,
        'faturas': [subs.fatura_payload(f) for f in faturas],
        'por_pagar': str(sum((f.valor for f in pendentes), Decimal('0'))),
        'planos': [subs.plano_payload(p) for p in subs.planos_ativos(('pos',))],
        'suspenso': pos.suspenso,
    }


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def planos_pos(request):
    utilizador = getattr(request.user, 'utilizador', None)
    # lojas do dono com o plano Loja + POS: um POS ligado a elas não precisa de plano
    incluido = []
    if utilizador and not get_membro_from_request(request):
        incluido = [s.loja_id for s in Subscricao.objects.select_related('loja', 'plano')
                    .filter(loja__dono=utilizador) if subs_pos.loja_cobre_pos(s)]
    return Response({'dias_teste': _dias_teste(),
                     'planos': [subs.plano_payload(p) for p in subs.planos_ativos(('pos',))],
                     'lojas_com_pos_incluido': incluido})


@api_view(['GET', 'PATCH'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_subscricao(request, pos_id):
    pos, erro = _pos_do_dono(request, pos_id)
    if erro:
        return erro
    if request.method == 'PATCH':
        valor = request.data.get('auto_renovar')
        if not isinstance(valor, bool):
            return _erro('auto_renovar inválido.')
        sub = subs_pos.garantir(pos)
        sub.auto_renovar = valor
        sub.save(update_fields=['auto_renovar', 'data_atualizacao'])
    return Response(_resumo(pos))


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_subscricao_plano(request, pos_id):
    pos, erro = _pos_do_dono(request, pos_id)
    if erro:
        return erro
    plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('pos',))
    if not plano:
        return _erro('Escolhe um dos planos de POS.')
    subs_pos.garantir(pos)
    try:
        subs_pos.escolher_plano(pos, plano)
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(_resumo(pos))


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_fatura_pagar(request, pos_id, fatura_id):
    pos, erro = _pos_do_dono(request, pos_id)
    if erro:
        return erro
    fatura = get_object_or_404(FaturaSubscricao, id=fatura_id, pos=pos)
    try:
        subs.pagar(fatura, 'simulado', referencia=f'SIM-{fatura.id}')
    except subs.ErroFatura as e:
        return _erro(str(e))
    pos.refresh_from_db()           # pagar pode ter levantado a suspensão
    return Response(_resumo(pos))
