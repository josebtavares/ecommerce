"""
Painel e relatórios do POS: o dono e os membros da equipa com a permissão "ver relatórios".
As faturas da subscrição só as vê o dono. As regras e as consultas estão em pos/relatorios.py.
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from ..models import RelatorioGerado
from ..utils import relatorios as rel
from ..utils import relatorios_motor as motor
from ..Views.relatorioView import _consultar, _exportar, _historico
from . import relatorios as rpos
from .permissions import IsPOSAuthenticated, POSAuthentication
from .views import _resolve_pos_request, _sem_permissao

SO_DONO = ('subscricoes',)


def _pos_com_permissao(request, pos_id):
    pos, membro, _ = _resolve_pos_request(request, pos_id)
    erro = _sem_permissao(membro, 'pode_ver_relatorios', 'Sem permissão para ver os relatórios.')
    return pos, membro, erro


def _excluidos(membro):
    return SO_DONO if membro else ()


def _autor(membro):
    return f'{membro.nome} (@{membro.username_pos})' if membro else None


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_painel(request, pos_id):
    """GET /api/pos/<id>/painel/?data_inicio&data_fim — o dashboard do POS."""
    pos, membro, erro = _pos_com_permissao(request, pos_id)
    if erro:
        return erro
    try:
        periodo = rel.ler_periodo(request, padrao_dias=30)
    except rel.PeriodoInvalido as e:
        return Response({'detail': str(e)}, status=400)
    return Response(rpos.painel(pos, periodo, dono=membro is None))


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_rel_catalogo(request, pos_id):
    """GET /api/pos/<id>/relatorios/catalogo/"""
    pos, membro, erro = _pos_com_permissao(request, pos_id)
    if erro:
        return erro
    return Response({'relatorios': motor.catalogo('pos', pos_id=pos.id, excluir=_excluidos(membro))})


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_rel_relatorio(request, pos_id, rid):
    """GET /api/pos/<id>/relatorios/r/<rid>/ — sempre só os dados deste POS."""
    pos, membro, erro = _pos_com_permissao(request, pos_id)
    if erro:
        return erro
    if rid in _excluidos(membro):
        return Response({'detail': 'Relatório não encontrado.'}, status=404)
    return _consultar(request, rid, 'pos', pos=pos)


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_rel_exportar(request, pos_id, rid):
    """GET /api/pos/<id>/relatorios/r/<rid>/exportar/?formato=csv|xlsx|pdf"""
    pos, membro, erro = _pos_com_permissao(request, pos_id)
    if erro:
        return erro
    if rid in _excluidos(membro):
        return Response({'detail': 'Relatório não encontrado.'}, status=404)
    return _exportar(request, rid, 'pos', pos=pos, autor=_autor(membro))


@api_view(['GET'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
def pos_rel_historico(request, pos_id):
    """GET /api/pos/<id>/relatorios/historico/ — as exportações deste POS (os membros não veem as da subscrição)."""
    pos, membro, erro = _pos_com_permissao(request, pos_id)
    if erro:
        return erro
    qs = RelatorioGerado.objects.filter(pos=pos)
    if membro:
        qs = qs.exclude(relatorio__in=SO_DONO)
    return Response(_historico(qs))
