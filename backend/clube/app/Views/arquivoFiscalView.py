"""
Arquivos fiscais preparados em segundo plano (utils/arquivo_fiscal.py): lista e descarga (link de 5 minutos).

Admin (gerir_faturacao):
  GET  /app/admin/faturacao/bende/arquivo/?de=AAAA-MM&ate=AAAA-MM      ZIP do Bende (na hora, ou 202 = fila) — faturacaoView
  GET  /app/admin/faturacao/arquivos/?alvo=bende|loja|pos&id=          lista
  POST /app/admin/faturacao/arquivos/<aid>/descarregar/
Loja (gerir_faturacao):
  GET  /app/loja/<id>/faturacao/arquivos/            POST /app/loja/<id>/faturacao/arquivos/<aid>/descarregar/
POS (quem vê a faturação; a equipa só os seus, sem os documentos do Bende):
  GET  /app/pos/<id>/faturacao/arquivos/             POST /app/pos/<id>/faturacao/arquivos/<aid>/descarregar/
Dev (sem R2):
  GET  /app/faturacao/arquivos/ficheiro/<token>/
"""
from django.core import signing
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import ArquivoFiscal
from ..utils import arquivo_fiscal as af
from ..utils import backups
from .adminView import _exige_admin
from .faturacaoLojaView import _acesso as _acesso_loja

VALIDADE_LINK = 300
SALT_LINK = 'arquivo-fiscal-ficheiro'


def _descarregar(request, qs, aid):
    a = qs.filter(pk=aid).first()
    if not a:
        return Response({'detail': 'Arquivo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if a.estado != 'ok' or not a.chave:
        return Response({'detail': 'Este arquivo já não está disponível.'}, status=status.HTTP_410_GONE)
    arm = backups.armazenamento()
    if not arm.existe(a.chave):
        a.estado = 'expirada'
        a.save(update_fields=['estado'])
        return Response({'detail': 'O ficheiro já não existe. Pede o arquivo outra vez.'}, status=status.HTTP_410_GONE)
    url = arm.url(a.chave, VALIDADE_LINK)
    if url is None:     # dev: o próprio servidor entrega o ficheiro
        url = request.build_absolute_uri(f'/app/faturacao/arquivos/ficheiro/{signing.dumps({"id": a.id}, salt=SALT_LINK)}/')
    ArquivoFiscal.objects.filter(pk=a.pk).update(descargas=a.descargas + 1)
    return Response({'url': url, 'expira_em_s': VALIDADE_LINK, 'nome': af.nome_ficheiro(a)})


# ── admin ──────────────────────────────────────────────────────────

def _qs_admin(request):
    alvo = request.GET.get('alvo') or 'bende'
    if alvo == 'bende':
        return ArquivoFiscal.objects.filter(alvo='bende')
    if alvo not in ('loja', 'pos'):
        return None
    try:
        i = int(request.GET.get('id') or 0)
    except ValueError:
        return None
    return ArquivoFiscal.objects.filter(**{'alvo': alvo, f'{alvo}_id': i}).select_related('loja', 'pos')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_arquivos(request):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    qs = _qs_admin(request)
    if qs is None:
        return Response({'detail': 'Alvo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    return af.lista(request, qs, admin=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_arquivo_descarregar(request, aid):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    return _descarregar(request, ArquivoFiscal.objects.all(), aid)


# ── loja ───────────────────────────────────────────────────────────

def _qs_loja(loja):
    return ArquivoFiscal.objects.filter(alvo='loja', loja=loja)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_arquivos(request, loja_id):
    loja, erro = _acesso_loja(request, loja_id)
    if erro:
        return erro
    return af.lista(request, _qs_loja(loja))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_arquivo_descarregar(request, loja_id, aid):
    loja, erro = _acesso_loja(request, loja_id)
    if erro:
        return erro
    return _descarregar(request, _qs_loja(loja), aid)


# ── POS ────────────────────────────────────────────────────────────

def _qs_pos(pos, membro):
    qs = ArquivoFiscal.objects.filter(alvo='pos', pos=pos)
    return qs.filter(com_bende=False) if membro is not None else qs


def pos_arquivos(request, pos_id):
    from ..pos.views_faturacao import _acesso
    pos, membro, erro = _acesso(request, pos_id)
    if erro:
        return erro
    return af.lista(request, _qs_pos(pos, membro))


def pos_arquivo_descarregar(request, pos_id, aid):
    from ..pos.views_faturacao import _acesso
    pos, membro, erro = _acesso(request, pos_id)
    if erro:
        return erro
    return _descarregar(request, _qs_pos(pos, membro), aid)


# ── dev ────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def arquivo_ficheiro(request, token):
    """Só para o armazenamento em disco (dev); no R2 o link vai direto ao bucket."""
    try:
        dados = signing.loads(token, salt=SALT_LINK, max_age=VALIDADE_LINK)
    except signing.BadSignature:
        raise Http404
    a = ArquivoFiscal.objects.filter(pk=dados.get('id'), estado='ok').first()
    caminho = backups.armazenamento().caminho(a.chave) if a else None
    if not caminho or not caminho.exists():
        raise Http404
    return FileResponse(open(caminho, 'rb'), as_attachment=True, filename=af.nome_ficheiro(a),
                        content_type='application/zip')
