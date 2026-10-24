"""
Subscrição do POS (utils/subscricoes_pos.py) — só a conta principal (o dono) a vê e paga;
os membros da equipa não. Funciona mesmo com o POS suspenso (é por aqui que se paga).
  GET   /api/pos/planos/                                   planos de POS (criação do POS)
  GET   /api/pos/<pos_id>/subscricao/                      estado, últimas faturas, planos, aviso
  GET   /api/pos/<pos_id>/subscricao/faturas/?estado&q&de&ate&limit&offset   todas as mensalidades, paginadas
  PATCH /api/pos/<pos_id>/subscricao/   { auto_renovar }
  POST  /api/pos/<pos_id>/subscricao/plano/   { plano_id }  escolher / mudar de plano
  POST  /api/pos/<pos_id>/subscricao/faturas/<fid>/pagar/  pagamento (simulado)
  POST  /api/pos/<pos_id>/subscricao/loja/   { acao }       plano Loja + POS da loja ligada
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


def _loja_ligada(pos):
    """A loja ligada (do mesmo dono) e o seu plano — para passar para Loja + POS ou sair dele."""
    loja = subs_pos.loja_do_dono(pos)
    if not loja:
        return None
    sl = Subscricao.objects.select_related('plano', 'plano_seguinte').filter(loja=loja).first()
    em_sub = loja.modelo_cobranca == 'subscricao' and sl and sl.estado not in ('aguarda', 'cancelada')
    pedido = sl.plano if sl and sl.estado == 'aguarda' and loja.modelo_cobranca == 'comissao' else None
    livre = subs.proxima_troca(loja)
    return {
        'loja_id': loja.id, 'loja_nome': loja.nome, 'modelo': loja.modelo_cobranca,
        'plano': subs.plano_payload(sl.plano) if em_sub else None,
        'plano_seguinte': subs.plano_payload(sl.plano_seguinte) if em_sub and sl.plano_seguinte_id else None,
        # pedido de mudança de comissão para subscrição à espera da 1.ª fatura (paga-se no backoffice)
        'pedido': subs.plano_payload(pedido) if pedido else None,
        'troca_livre_em': livre.isoformat() if livre and loja.modelo_cobranca == 'comissao' else None,
        'planos_combo': [subs.plano_payload(p) for p in subs.planos_ativos(('loja_pos',))],
        'planos_loja': [subs.plano_payload(p) for p in subs.planos_ativos(('loja',))],
    }


def _resumo(pos):
    sub = subs_pos.garantir(pos)
    with transaction.atomic():
        cob = subs_pos.sincronizar(Subscricao.objects.select_for_update().get(pk=sub.pk))
    sub.refresh_from_db()
    pos.refresh_from_db()
    # a lista completa (paginada, com pesquisa) é /api/pos/<id>/subscricao/faturas/; aqui só as últimas
    faturas = list(sub.faturas.select_related('plano', 'pos')[:10])
    pendentes = list(sub.faturas.filter(estado='pendente'))
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
        'loja': _loja_ligada(pos),
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


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_subscricao_faturas(request, pos_id):
    """GET /api/pos/<pos_id>/subscricao/faturas/?estado=&q=&de=&ate=&limit=&offset= — todas as mensalidades do POS."""
    from ..Views.subscricaoView import pagina_cobrancas
    pos, erro = _pos_do_dono(request, pos_id)
    if erro:
        return erro
    return pagina_cobrancas(request, FaturaSubscricao.objects.filter(pos=pos), limite=10)


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


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_subscricao_loja(request, pos_id):
    """
    POST /api/pos/<pos_id>/subscricao/loja/   (o dono do POS, que é também o dono da loja ligada)
      { acao: 'combo', plano_id }                      → a loja passa para um plano Loja + POS
      { acao: 'separar', plano_id, plano_pos_id? }     → a loja volta a um plano só de loja (na renovação)
    """
    pos, erro = _pos_do_dono(request, pos_id)
    if erro:
        return erro
    acao = request.data.get('acao')
    subs_pos.garantir(pos)
    try:
        if acao == 'combo':
            plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('loja_pos',))
            if not plano:
                return _erro('Escolhe um dos planos Loja + POS.')
            subs_pos.passar_para_combo(pos, plano)
        elif acao == 'separar':
            plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('loja',))
            if not plano:
                return _erro('Escolhe o plano da loja.')
            plano_pos = None
            if request.data.get('plano_pos_id') not in (None, ''):
                plano_pos = subs.plano_ativo(request.data.get('plano_pos_id'), tipos=('pos',))
                if not plano_pos:
                    return _erro('Escolhe um dos planos de POS.')
            subs_pos.sair_do_combo(pos, plano, plano_pos)
        else:
            return _erro('Acção inválida.')
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(_resumo(pos))
