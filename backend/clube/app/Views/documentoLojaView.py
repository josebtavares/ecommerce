"""
Documentos legais da loja (utils/documentos_loja.py).

Loja (só o dono — gerir_documentos):
  GET    /app/loja/<loja_id>/documentos/                → { documentos, tipos, resumo, consultas_bende }
  POST   /app/loja/<loja_id>/documentos/                multipart { tipo, ficheiro, descricao?, validade? }
  DELETE /app/loja/<loja_id>/documentos/<id>/
  POST   /app/loja/<loja_id>/documentos/<id>/abrir/     → { url } (link de 2 minutos)
Admin (verificar_documentos):
  GET    /app/admin/lojas/<loja_id>/documentos/         → { documentos, resumo, registo }
  PATCH  /app/admin/lojas/<loja_id>/documentos/         { obrigatorios: bool }
  POST   /app/admin/documentos/<id>/                    { acao: aprovar | rejeitar, motivo?, validade? }
  POST   /app/admin/documentos/<id>/abrir/              → { url } (fica registado)
Ficheiro:
  GET    /app/documentos/<id>/ficheiro/?t=              link assinado; o acesso volta a ser verificado
"""
from datetime import date

from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import DocumentoLoja, Loja, Utilizador
from ..utils import documentos_loja as docs
from .adminView import _exige_admin
from .lojaView import _exige_permissao


def _limitado(request, grupo, taxa):
    return is_ratelimited(request=request, group=f'documentos_{grupo}', key='user', rate=taxa,
                          method=request.method, increment=True)


def _demasiados():
    return Response({'detail': 'Demasiados pedidos seguidos. Aguarda um momento.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS)


def _data(valor):
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        raise docs.ErroDocumento('Data de validade inválida.')


def _url(request, d):
    token = docs.assinar(d.id, request.user.utilizador.id)
    return request.build_absolute_uri(f'/app/documentos/{d.id}/ficheiro/?t={token}')


def _dono(request, loja):
    """(None, erro) se não for o dono; o admin a ver o backoffice (só leitura) usa o Admin → Lojas."""
    _, erro = _exige_permissao(request, loja, 'gerir_documentos')
    if erro:
        return erro
    from ..utils.ver_loja import a_ver
    if a_ver(loja.id, request.user.utilizador):
        return Response({'detail': 'Os documentos vêem-se no Admin → Lojas (a consulta fica registada).'},
                        status=status.HTTP_403_FORBIDDEN)
    return None


def _lista_loja(loja):
    return {
        'documentos': [docs.payload(d) for d in loja.documentos.all()],
        'tipos': [{'valor': v, 'nome': n} for v, n in DocumentoLoja.TIPOS],
        'resumo': docs.resumo(loja),
        'consultas_bende': docs.acessos(loja, so_bende=True, n=10),
        'disponivel': docs.disponivel(),
    }


# ══════════════════════════════════════════════════════════════
# LOJA
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def loja_documentos(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    erro = _dono(request, loja)
    if erro:
        return erro
    if request.method == 'GET':
        return Response(_lista_loja(loja))
    if _limitado(request, 'enviar', '20/h'):
        return _demasiados()
    try:
        d = docs.enviar(request, loja, request.data.get('tipo'), request.FILES.get('ficheiro'),
                        descricao=request.data.get('descricao', ''), validade=_data(request.data.get('validade')))
    except docs.ErroDocumento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({**_lista_loja(loja), 'novo': d.id}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def loja_documento(request, loja_id, id):
    loja = get_object_or_404(Loja, id=loja_id)
    erro = _dono(request, loja)
    if erro:
        return erro
    docs.apagar(request, get_object_or_404(DocumentoLoja, id=id, loja=loja))
    return Response(_lista_loja(loja))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_documento_abrir(request, loja_id, id):
    loja = get_object_or_404(Loja, id=loja_id)
    erro = _dono(request, loja)
    if erro:
        return erro
    if _limitado(request, 'abrir', '60/h'):
        return _demasiados()
    d = get_object_or_404(DocumentoLoja, id=id, loja=loja)
    docs.registar(request, loja, 'ver', d)
    return Response({'url': _url(request, d)})


# ══════════════════════════════════════════════════════════════
# ADMIN
# ══════════════════════════════════════════════════════════════

def _lista_admin(loja):
    return {
        'documentos': [docs.payload(d, admin=True) for d in loja.documentos.select_related('enviado_por', 'revisto_por')],
        'resumo': docs.resumo(loja),
        'registo': docs.acessos(loja, n=30),
    }


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_loja_documentos(request, loja_id):
    erro = _exige_admin(request, 'verificar_documentos')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    if request.method == 'PATCH':
        if 'obrigatorios' not in request.data:
            return Response({'detail': 'Nada para mudar.'}, status=status.HTTP_400_BAD_REQUEST)
        docs.mudar_obrigatorios(request, loja, request.data['obrigatorios'] in (True, 'true', '1', 1))
    return Response(_lista_admin(loja))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_documento(request, id):
    erro = _exige_admin(request, 'verificar_documentos')
    if erro:
        return erro
    d = get_object_or_404(DocumentoLoja.objects.select_related('loja'), id=id)
    try:
        d, substituidos = docs.decidir(request, d, request.data.get('acao'), motivo=request.data.get('motivo', ''),
                                       validade=_data(request.data.get('validade')))
    except docs.ErroDocumento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({**_lista_admin(d.loja), 'substituidos': substituidos})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_documento_abrir(request, id):
    erro = _exige_admin(request, 'verificar_documentos')
    if erro:
        return erro
    if _limitado(request, 'abrir_admin', '120/h'):
        return _demasiados()
    d = get_object_or_404(DocumentoLoja.objects.select_related('loja'), id=id)
    docs.registar(request, d.loja, 'ver', d, pela_bende=True)
    return Response({'url': _url(request, d)})


# ══════════════════════════════════════════════════════════════
# FICHEIRO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([])          # abre-se num separador novo — a autorização vem na assinatura
@permission_classes([AllowAny])
def ficheiro(request, id):
    lido = docs.ler_assinatura(request.query_params.get('t', ''))
    if not lido or lido[0] != id:
        return Response({'detail': 'Link inválido ou expirado — volta a abrir o documento.'}, status=403)
    d = DocumentoLoja.objects.select_related('loja').filter(id=id).first()
    u = Utilizador.objects.filter(id=lido[1]).select_related('user').first()
    if not d or not docs.pode_abrir(u, d):
        return Response({'detail': 'Documento não encontrado.'}, status=404)
    tipo = 'application/pdf' if d.formato == 'pdf' else 'image/jpeg'
    nome = f'{d.tipo}-{d.loja_id}-{d.id}.{d.formato}'
    armazenamento = d.ficheiro.storage
    if hasattr(armazenamento, 'bucket_name'):
        # R2 privado: link temporário assinado pelo próprio R2 (outro domínio — nada corre no nosso)
        resp = HttpResponseRedirect(armazenamento.url(d.ficheiro.name, parameters={
            'ResponseContentType': tipo, 'ResponseContentDisposition': f'inline; filename="{nome}"'}))
    else:
        resp = FileResponse(armazenamento.open(d.ficheiro.name, 'rb'), content_type=tipo)
        resp['Content-Disposition'] = f'inline; filename="{nome}"'
    resp['Cache-Control'] = 'private, no-store'
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Referrer-Policy'] = 'no-referrer'
    return resp
