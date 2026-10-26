"""
Exportar os dados de uma loja (ZIP com CSV; utils/exportacao_loja.py). Pede o dono no backoffice ou o
admin (permissão exportar_lojas); o worker prepara o ficheiro e avisa por notificação.

  GET  /app/loja/<id>/exportacoes/?limit=&offset=          lista (só o dono)
  POST /app/loja/<id>/exportacoes/            {imagens}   pedir uma nova
  POST /app/loja/<id>/exportacoes/<eid>/descarregar/      link de 5 minutos
  (o mesmo em /app/admin/lojas/<id>/exportacoes/...)
  GET  /app/exportacoes/ficheiro/<token>/                 só na dev (sem R2): entrega o ficheiro do link assinado
"""
from django.core import signing
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import ExportacaoLoja, Loja
from ..utils import backups
from ..utils import exportacao_loja as exl
from .adminView import _exige_admin
from .faturacaoView import _paginar

VALIDADE_LINK = 300
SALT_LINK = 'exportacao-ficheiro'


def _e_dono(request, loja):
    u = getattr(request.user, 'utilizador', None)
    return u is not None and loja.dono_id == u.id


def _item(e, admin):
    if e.pelo_admin and not admin:
        por = 'Equipa Bende'
    else:
        por = (e.pedido_por.get_full_name() or e.pedido_por.username) if e.pedido_por else ''
    return {
        'id': e.id, 'estado': e.estado, 'estado_label': e.get_estado_display(), 'com_imagens': e.com_imagens,
        'pedido_por': por, 'pelo_admin': e.pelo_admin, 'criado_em': e.criado_em, 'concluido_em': e.concluido_em,
        'tamanho': e.tamanho, 'expira_em': e.expira_em, 'descargas': e.descargas,
        'avisos': len([a for a in e.avisos.splitlines() if a.strip()]),
        'erro': e.erro[-300:] if e.estado == 'erro' else '',
        'disponivel': e.estado == 'ok',
    }


def _lista(request, loja, admin):
    qs = ExportacaoLoja.objects.filter(loja=loja).select_related('pedido_por')
    pagina, total = _paginar(request, qs, 10)
    return Response({
        'count': total, 'results': [_item(e, admin) for e in pagina],
        'em_curso': qs.filter(estado__in=('pendente', 'a_correr')).exists(),
        'dias_validade': exl.DIAS_VALIDADE,
    })


def _pedir(request, loja, admin):
    try:
        e = exl.pedir(loja, request.user, com_imagens=bool(request.data.get('imagens')), pelo_admin=admin)
    except exl.ExportacaoEmCurso as x:
        return Response({'detail': str(x)}, status=status.HTTP_409_CONFLICT)
    except exl.LimiteExportacoes as x:
        return Response({'detail': str(x)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    return Response(_item(e, admin), status=status.HTTP_201_CREATED)


def _descarregar(request, loja, exportacao_id):
    e = ExportacaoLoja.objects.filter(pk=exportacao_id, loja=loja).first()
    if not e:
        return Response({'detail': 'Exportação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    if e.estado != 'ok' or not e.chave:
        return Response({'detail': 'Esta exportação já não está disponível.'}, status=status.HTTP_410_GONE)
    arm = backups.armazenamento()
    if not arm.existe(e.chave):
        e.estado = 'expirada'
        e.save(update_fields=['estado'])
        return Response({'detail': 'O ficheiro já não existe. Pede uma nova exportação.'}, status=status.HTTP_410_GONE)
    url = arm.url(e.chave, VALIDADE_LINK)
    if url is None:     # dev: o próprio servidor entrega o ficheiro
        url = request.build_absolute_uri(f'/app/exportacoes/ficheiro/{signing.dumps({"id": e.id}, salt=SALT_LINK)}/')
    e.descargas += 1
    e.ultima_descarga_em = timezone.now()
    e.save(update_fields=['descargas', 'ultima_descarga_em'])
    return Response({'url': url, 'expira_em_s': VALIDADE_LINK, 'nome': e.chave.rsplit('/', 1)[-1]})


# ── backoffice (só o dono) ─────────────────────────────────────────

def _loja_do_dono(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    if not _e_dono(request, loja):
        return None, Response({'detail': 'Só o dono da loja pode exportar os dados.'}, status=status.HTTP_403_FORBIDDEN)
    return loja, None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def loja_exportacoes(request, loja_id):
    loja, erro = _loja_do_dono(request, loja_id)
    if erro:
        return erro
    return _pedir(request, loja, False) if request.method == 'POST' else _lista(request, loja, False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_exportacao_descarregar(request, loja_id, exportacao_id):
    loja, erro = _loja_do_dono(request, loja_id)
    if erro:
        return erro
    return _descarregar(request, loja, exportacao_id)


# ── admin ──────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_loja_exportacoes(request, loja_id):
    erro = _exige_admin(request, 'exportar_lojas')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    return _pedir(request, loja, True) if request.method == 'POST' else _lista(request, loja, True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_loja_exportacao_descarregar(request, loja_id, exportacao_id):
    erro = _exige_admin(request, 'exportar_lojas')
    if erro:
        return erro
    return _descarregar(request, get_object_or_404(Loja, id=loja_id), exportacao_id)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def exportacao_ficheiro(request, token):
    """Só para o armazenamento em disco (dev); no R2 o link vai direto ao bucket."""
    try:
        dados = signing.loads(token, salt=SALT_LINK, max_age=VALIDADE_LINK)
    except signing.BadSignature:
        raise Http404
    e = ExportacaoLoja.objects.filter(pk=dados.get('id'), estado='ok').first()
    caminho = backups.armazenamento().caminho(e.chave) if e else None
    if not caminho or not caminho.exists():
        raise Http404
    return FileResponse(open(caminho, 'rb'), as_attachment=True, filename=caminho.name, content_type='application/zip')
