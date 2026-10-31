"""
Pré-visualização dos links (WhatsApp, Facebook) e SEO das páginas públicas.

O site é uma SPA: quem lê os links não corre JavaScript. O servidor do frontend
(frontend/clube/scripts/servidor.js) pede aqui os dados de cada página e escreve-os no HTML.

  dados_loja / dados_produto   título, descrição, imagem e dados estruturados da página
  imagem_jpeg                  a imagem da partilha: JPEG 1200×630 (as fotos do site são WebP)
  lista_sitemap                o que o Google deve indexar

Só usa o que já é público na página da loja. As lojas de demonstração partilham-se na mesma,
mas não são indexadas (`indexar` falso e fora do sitemap).
"""
import hashlib
import io
import re

from django.core.cache import cache
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .dinheiro import formatar

LARGURA, ALTURA = 1200, 630
QUALIDADE = 82
MAX_DESCRICAO = 180
CACHE_IMAGEM = 24 * 3600
_FOTO = re.compile(r'\.(jpe?g|png|gif|webp)$', re.I)


def _texto(valor, limite=MAX_DESCRICAO):
    """Uma linha só, cortada numa palavra."""
    texto = ' '.join(str(valor or '').split())
    if len(texto) <= limite:
        return texto
    return texto[:limite - 1].rsplit(' ', 1)[0].rstrip(' ,.;:-') + '…'


def _foto(*ficheiros):
    """O primeiro ficheiro que é uma foto (o banner e o ficheiro do produto podem ser vídeos)."""
    for f in ficheiros:
        if f and _FOTO.search(f.name):
            return f
    return None


def foto_loja(loja):
    return _foto(loja.banner, loja.banner_poster, loja.logo)


def foto_produto(produto):
    extras = [i.ficheiro for i in produto.imagens.all()[:3]]
    return _foto(produto.ficheiro, produto.ficheiro_poster, *extras)


def _url_imagem(tipo, obj, foto):
    if not foto:
        return None
    versao = hashlib.sha1(foto.name.encode()).hexdigest()[:10]
    return f'/og/{tipo}/{obj.pk}.jpg?v={versao}'


def _preco_produto(produto):
    """Preço como na página: o mais baixo das variações activas ("desde"). Devolve (preço, desde)."""
    precos = []
    if produto.stock_por_variante:
        precos = [v.preco_efetivo for v in produto.variantes.filter(ativo=True)]
    if not precos:
        return produto.preco, False
    return min(precos), min(precos) != max(precos)


def dados_loja(loja):
    onde = f' em {loja.localizacao}' if loja.localizacao else ''
    descricao = _texto(loja.descricao) or _texto(f'{loja.categoria}{onde}. Vê os produtos e encomenda online na Bende.')
    estruturados = {
        '@context': 'https://schema.org', '@type': 'Store', 'name': loja.nome, 'description': descricao,
    }
    if loja.localizacao:
        estruturados['address'] = loja.localizacao
    return {
        'tipo': 'loja', 'titulo': f'{loja.nome} — Bende', 'descricao': descricao, 'nome': loja.nome,
        'caminho': f'/loja/{loja.pk}', 'imagem': _url_imagem('loja', loja, foto_loja(loja)),
        'indexar': not loja.demo, 'estruturados': estruturados,
    }


def dados_produto(produto):
    loja = produto.loja
    preco, desde = _preco_produto(produto)
    rotulo = f'{"desde " if desde else ""}{formatar(preco)}'
    resumo = _texto(produto.descricao)
    descricao = _texto(f'{rotulo} · {loja.nome}' + (f'. {resumo}' if resumo else ''))
    return {
        'tipo': 'produto', 'titulo': f'{produto.nome} — {loja.nome}', 'descricao': descricao, 'nome': produto.nome,
        'caminho': f'/loja/{loja.pk}?produto={produto.pk}',
        'imagem': _url_imagem('produto', produto, foto_produto(produto)), 'indexar': not loja.demo,
        'estruturados': {
            '@context': 'https://schema.org', '@type': 'Product', 'name': produto.nome,
            'description': resumo or descricao,
            'brand': {'@type': 'Brand', 'name': loja.nome},
            'offers': {'@type': 'Offer', 'priceCurrency': 'CVE', 'price': f'{preco:.2f}',
                       'seller': {'@type': 'Organization', 'name': loja.nome}},
        },
    }


def _gerar_jpeg(foto):
    """A foto inteira, centrada sobre uma cópia desfocada dela (como no cartão do produto)."""
    with foto.open('rb') as f:
        img = ImageOps.exif_transpose(Image.open(f)).convert('RGBA')
    branco = Image.new('RGBA', img.size, (255, 255, 255, 255))
    rgb = Image.alpha_composite(branco, img).convert('RGB')

    pequena = ImageOps.fit(rgb, (LARGURA // 4, ALTURA // 4)).filter(ImageFilter.GaussianBlur(8))
    tela = ImageEnhance.Brightness(pequena.resize((LARGURA, ALTURA), Image.Resampling.BILINEAR)).enhance(0.8)
    principal = ImageOps.contain(rgb, (LARGURA, ALTURA), Image.Resampling.LANCZOS)
    tela.paste(principal, ((LARGURA - principal.width) // 2, (ALTURA - principal.height) // 2))

    saida = io.BytesIO()
    tela.save(saida, 'JPEG', quality=QUALIDADE, optimize=True, progressive=True)
    return saida.getvalue()


def imagem_jpeg(foto):
    """JPEG da partilha (bytes), ou None se o ficheiro faltar ou não abrir."""
    chave = 'seo:jpeg:' + hashlib.sha1(foto.name.encode()).hexdigest()
    dados = cache.get(chave)
    if dados is None:
        try:
            dados = _gerar_jpeg(foto)
        except (OSError, ValueError, Image.DecompressionBombError):
            return None
        cache.set(chave, dados, CACHE_IMAGEM)
    return dados


def lista_sitemap():
    from ..models import Loja, Produto
    lojas = Loja.objects.filter(ativa=True, demo=False)
    produtos = Produto.objects.filter(ativo=True, loja__in=lojas).values_list('pk', 'loja_id')
    return {
        'lojas': [{'id': pk, 'atualizado': d.date().isoformat()}
                  for pk, d in lojas.values_list('pk', 'data_atualizacao')],
        'produtos': [{'id': pk, 'loja': loja} for pk, loja in produtos[:45000]],
    }
