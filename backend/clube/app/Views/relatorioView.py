"""
Relatórios: catálogo, consulta (com as linhas paginadas para o ecrã) e exportação (CSV, Excel, PDF).
As regras e as consultas estão em utils/relatorios_motor.py; os ficheiros em utils/relatorios_export.py.
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_ratelimit.core import is_ratelimited
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, RelatorioGerado
from ..utils import relatorios as rel
from ..utils import relatorios_export as exp
from ..utils import relatorios_motor as motor
from .adminView import _exige_admin


def _consultar(request, rid, ambito, loja=None):
    try:
        r, p, res = motor.executar(rid, request, ambito, loja.id if loja else None)
    except KeyError:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)
    except (rel.PeriodoInvalido, motor.FiltroInvalido) as e:
        return Response({'detail': str(e)}, status=400)
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit = min(max(int(request.GET.get('limit', 50)), 1), 500)
    except ValueError:
        offset, limit = 0, 50
    cols = res['colunas']
    tipos = {c['chave']: c['tipo'] for c in cols}
    linhas = [{k: exp.json_valor(v, tipos.get(k, 'texto')) for k, v in l.items()} for l in res['linhas'][offset:offset + limit]]
    return Response({
        'relatorio': {'id': r.id, 'titulo': res['titulo'], 'descricao': r.descricoes.get(ambito, r.descricao), 'sem_periodo': r.sem_periodo},
        'periodo': p.payload(),
        'resumo': [{**i, 'valor': exp.json_valor(i['valor'], i['tipo'])} for i in res['resumo']],
        'colunas': cols,
        'linhas': linhas,
        'total_linhas': len(res['linhas']),
        'offset': offset, 'limit': limit,
        'totais': {k: exp.json_valor(v, tipos.get(k, 'numero')) for k, v in res['totais'].items()},
        'notas': res['notas'],
        'truncado': res['truncado'],
        'filtros_aplicados': res['filtros_aplicados'],
    })


def _exportar(request, rid, ambito, loja=None):
    formato = request.GET.get('formato', '')
    if formato not in exp.FORMATOS:
        return Response({'detail': 'Formato inválido (csv, xlsx ou pdf).'}, status=400)
    if is_ratelimited(request=request, group='relatorios_exportar', key='user', rate='60/h', method=request.method, increment=True):
        return Response({'detail': 'Demasiadas exportações. Tenta daqui a pouco.'}, status=429)
    try:
        r, p, res = motor.executar(rid, request, ambito, loja.id if loja else None)
    except KeyError:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)
    except (rel.PeriodoInvalido, motor.FiltroInvalido) as e:
        return Response({'detail': str(e)}, status=400)
    ut = request.user.utilizador
    meta = {
        'emissor': loja.nome if loja else 'Bendi',
        'nif': (loja.efatura_nif if loja else '') or '',
        'titulo': res['titulo'], 'inicio': p.inicio, 'fim': p.fim, 'sem_periodo': r.sem_periodo,
        'filtros': res['filtros_aplicados'], 'gerado_em': timezone.now(), 'gerado_por': ut.nome,
    }
    gerar, tipo, ext = exp.FORMATOS[formato]
    conteudo = gerar(meta, res)
    filtros = {k: v for k, v in request.GET.items() if k not in ('formato', 'offset', 'limit')}
    RelatorioGerado.objects.create(utilizador=ut, loja=loja, relatorio=r.id, formato=formato, inicio=p.inicio, fim=p.fim,
                                   filtros=filtros, linhas=len(res['linhas']))
    nome = f'{"bendi" if not loja else "loja-" + str(loja.id)}_{r.id}_{p.inicio:%Y%m%d}-{p.fim:%Y%m%d}.{ext}'
    resp = HttpResponse(conteudo, content_type=tipo)
    resp['Content-Disposition'] = f'attachment; filename="{nome}"'
    resp['Cache-Control'] = 'no-store'
    return resp


def _historico(qs):
    return [{'id': x.id, 'relatorio': x.relatorio,
             'titulo': motor.RELATORIOS[x.relatorio].titulo if x.relatorio in motor.RELATORIOS else x.relatorio,
             'formato': x.formato, 'inicio': x.inicio, 'fim': x.fim, 'linhas': x.linhas, 'filtros': x.filtros,
             'sem_periodo': motor.RELATORIOS[x.relatorio].sem_periodo if x.relatorio in motor.RELATORIOS else False,
             'por': x.utilizador.nome if x.utilizador_id else '', 'data': x.data_criacao}
            for x in qs.select_related('utilizador__user')[:30]]


# ── admin ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_catalogo(request):
    """GET /app/admin/relatorios/catalogo/ — os relatórios e os filtros de cada um."""
    erro = _exige_admin(request, 'ver_relatorios')
    if erro: return erro
    return Response({'relatorios': motor.catalogo('admin')})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_relatorio(request, rid):
    """GET /app/admin/relatorios/r/<id>/?data_inicio&data_fim&<filtros>&offset&limit"""
    erro = _exige_admin(request, 'ver_relatorios')
    if erro: return erro
    return _consultar(request, rid, 'admin')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_exportar(request, rid):
    """GET /app/admin/relatorios/r/<id>/exportar/?formato=csv|xlsx|pdf&<os mesmos filtros>"""
    erro = _exige_admin(request, 'ver_relatorios')
    if erro: return erro
    return _exportar(request, rid, 'admin')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_historico(request):
    """GET /app/admin/relatorios/historico/ — as últimas exportações (de todos os admins e lojas)."""
    erro = _exige_admin(request, 'ver_relatorios')
    if erro: return erro
    qs = RelatorioGerado.objects.all()
    if request.GET.get('meus') == '1':
        qs = qs.filter(utilizador=request.user.utilizador)
    return Response(_historico(qs.filter(loja__isnull=True)))


# ── loja (permissão ver_relatorios: dono, gestor, contabilista) ─────

def _loja_com_permissao(request, loja_id):
    from .lojaView import _exige_permissao
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'ver_relatorios')
    return loja, erro


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_catalogo(request, loja_id):
    """GET /app/loja/<id>/relatorios/catalogo/"""
    loja, erro = _loja_com_permissao(request, loja_id)
    if erro: return erro
    return Response({'relatorios': motor.catalogo('loja', loja.id)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_relatorio(request, loja_id, rid):
    """GET /app/loja/<id>/relatorios/r/<rid>/ — sempre só os dados desta loja."""
    loja, erro = _loja_com_permissao(request, loja_id)
    if erro: return erro
    return _consultar(request, rid, 'loja', loja)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_exportar(request, loja_id, rid):
    """GET /app/loja/<id>/relatorios/r/<rid>/exportar/?formato=csv|xlsx|pdf"""
    loja, erro = _loja_com_permissao(request, loja_id)
    if erro: return erro
    return _exportar(request, rid, 'loja', loja)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_historico(request, loja_id):
    """GET /app/loja/<id>/relatorios/historico/ — as exportações desta loja."""
    loja, erro = _loja_com_permissao(request, loja_id)
    if erro: return erro
    return Response(_historico(RelatorioGerado.objects.filter(loja=loja)))
