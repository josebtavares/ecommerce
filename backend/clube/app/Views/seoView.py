from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import Loja, Produto
from ..utils import seo


def _produto_publico(id, loja_id=None):
    filtros = {'pk': id, 'ativo': True, 'loja__ativa': True}
    if loja_id is not None:
        filtros['loja_id'] = loja_id
    return Produto.objects.select_related('loja').filter(**filtros).first()


@api_view(['GET'])
@permission_classes([AllowAny])
def seo_pagina(request, id):
    """GET /app/seo/loja/<id>/[?produto=<id>] — dados para o HTML da página da loja (ou do produto nela)."""
    loja = get_object_or_404(Loja, pk=id, ativa=True)
    pid = request.query_params.get('produto', '')
    valido = pid.isascii() and pid.isdigit() and len(pid) < 12
    produto = _produto_publico(int(pid), loja.pk) if valido else None
    return Response(seo.dados_produto(produto) if produto else seo.dados_loja(loja))


@api_view(['GET'])
@permission_classes([AllowAny])
def seo_imagem(request, tipo, id):
    """GET /app/seo/imagem/<loja|produto>/<id>.jpg — imagem da partilha (o site serve-a em /og/…)."""
    if tipo == 'loja':
        foto = seo.foto_loja(get_object_or_404(Loja, pk=id, ativa=True))
    else:
        produto = _produto_publico(id)
        foto = seo.foto_produto(produto) if produto else None
    dados = seo.imagem_jpeg(foto) if foto else None
    if dados is None:
        return HttpResponse(status=404)
    resposta = HttpResponse(dados, content_type='image/jpeg')
    resposta['Cache-Control'] = 'public, max-age=604800'
    return resposta


@api_view(['GET'])
@permission_classes([AllowAny])
def seo_sitemap(request):
    """GET /app/seo/sitemap/ — lojas e produtos para o /sitemap.xml."""
    return Response(seo.lista_sitemap())
