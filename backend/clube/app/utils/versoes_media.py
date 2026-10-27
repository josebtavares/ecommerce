"""
Versões mais leves dos ficheiros públicos (fotos e vídeos), com nomes derivados do principal.

  fotos   <pasta>/<20 hex>.webp   (máx. 1600 px; banners 1920)  → <pasta>/<20 hex>__600.webp   (cartões e listas)
  vídeos  <pasta>/<20 hex>.mp4    (1080p)         → __720.mp4 (telemóveis), __480.mp4 (cartões)
  posters posters/…/<20 hex>.webp (1280 px)       → __600.webp

Só os ficheiros com este nome (feitos pela plataforma) têm versões; o frontend deriva os nomes da mesma
maneira (src/utils/media.js). As versões não estão em nenhum FileField: a limpeza (utils/limpeza.py) e o
varrimento de órfãos tratam-nas como parte do ficheiro principal.

As fotos são convertidas no upload (uploads.py → converter_imagem); os vídeos e posters pelo worker
(utils/video.py); as que já existiam pelo comando manage.py otimizar_media.
"""
import io
import re
import uuid

from PIL import Image, ImageFilter, ImageOps

LADO_FOTO = 1600
# banners que ocupam a largura toda do ecrã: 1600 px ficava mole num monitor grande
LADO_POR_CAMPO = {('loja', 'banner'): 1920, ('homeimagem', 'ficheiro'): 1920}
LADO_MINIATURA = 600
# WebP 90/85: quase indistinguível do original nas fotos de comida/produtos (com 82/78 via-se perda nos detalhes)
QUALIDADE = 90
QUALIDADE_MINIATURA = 85
MAX_PIXEIS = 250_000_000          # acima disto é quase de certeza uma "bomba" de descompressão
MAX_PIXEIS_SEM_REDUCAO = 50_000_000   # PNG/WebP/GIF (não se descodificam reduzidos): ~200 MB em RGBA

PRINCIPAL = re.compile(r'^(?P<base>(?:.*/)?[0-9a-f]{20})\.(?P<ext>webp|mp4)$')
VARIANTE = re.compile(r'^(?P<base>(?:.*/)?[0-9a-f]{20})__(?:600|480|720)\.(?P<ext>webp|mp4)$')
SUFIXOS = {'webp': ('__600',), 'mp4': ('__720', '__480')}


class ImagemInvalida(Exception):
    pass


def nome_novo(ext):
    return f'{uuid.uuid4().hex[:20]}.{ext}'


def variantes(nome):
    """Nomes das versões de um ficheiro principal (vazio se não for um nome da plataforma)."""
    m = PRINCIPAL.match(nome or '')
    if not m:
        return []
    return [f"{m.group('base')}{s}.{m.group('ext')}" for s in SUFIXOS[m.group('ext')]]


def principal_de(nome):
    """Se `nome` for uma versão, devolve o ficheiro principal; senão None."""
    m = VARIANTE.match(nome or '')
    return f"{m.group('base')}.{m.group('ext')}" if m else None


def variante(nome, sufixo):
    m = PRINCIPAL.match(nome or '')
    return f"{m.group('base')}{sufixo}.{m.group('ext')}" if m else None


# ── fotos ──────────────────────────────────────────────────────────

def _abrir(ficheiro, lado=LADO_FOTO):
    Image.MAX_IMAGE_PIXELS = MAX_PIXEIS
    try:
        ficheiro.seek(0)
    except Exception:
        pass
    try:
        img = Image.open(ficheiro)
        # só o JPEG descodifica já reduzido; os outros ocupam 4 bytes por píxel (+ cópias) —
        # um PNG de 15000×15000 com poucos MB pedia vários GB de RAM ao servidor
        if img.format != 'JPEG' and img.width * img.height > MAX_PIXEIS_SEM_REDUCAO:
            raise Image.DecompressionBombError('demasiados píxeis')
        img.draft('RGB', (lado * 2, lado * 2))     # JPEG: descodifica já reduzido (poupa RAM)
        img.load()
    except Image.DecompressionBombError:
        raise ImagemInvalida('A imagem é demasiado grande (em píxeis) para ser processada.')
    except Exception:
        raise ImagemInvalida('O ficheiro não é uma imagem válida ou está danificado.')
    img = ImageOps.exif_transpose(img)                       # fotos de telemóvel "deitadas"
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'A' in img.getbands() or img.mode == 'P' else 'RGB')
    return img


def _webp(img, lado, qualidade):
    copia = img.copy()
    copia.thumbnail((lado, lado), Image.LANCZOS)             # nunca aumenta
    if max(img.size) > max(copia.size) * 1.5:
        # reduzir muito amacia os contornos: um toque de nitidez devolve o detalhe
        copia = copia.filter(ImageFilter.UnsharpMask(radius=0.8, percent=50, threshold=2))
    saida = io.BytesIO()
    copia.save(saida, 'WEBP', quality=qualidade, method=6)   # sem EXIF (localização, modelo do telemóvel)
    return saida.getvalue()


def lado_de(modelo, campo):
    return LADO_POR_CAMPO.get((modelo, campo), LADO_FOTO)


def _ja_otimizada(ficheiro, img, lado):
    """WebP que já cabe no tamanho e não traz metadados: fica tal e qual (comprimir outra vez só piorava
    a qualidade e muitas vezes até aumentava o ficheiro)."""
    try:
        ficheiro.seek(0)
        original = Image.open(ficheiro)
        if (original.format != 'WEBP' or max(original.size) > lado or original.info.get('exif')
                or original.info.get('xmp') or getattr(original, 'is_animated', False)):
            return None
        ficheiro.seek(0)
        dados = ficheiro.read()
        # nada colado depois da imagem: o tamanho no cabeçalho RIFF tem de bater com o ficheiro
        if dados[:4] != b'RIFF' or dados[8:12] != b'WEBP' or int.from_bytes(dados[4:8], 'little') + 8 != len(dados):
            return None
        return dados
    except Exception:
        return None


def converter_imagem(ficheiro, lado=LADO_FOTO):
    """→ (bytes da foto com no máximo `lado` px, bytes da miniatura 600 px), ambas WebP sem metadados."""
    img = _abrir(ficheiro, lado)
    foto = _ja_otimizada(ficheiro, img, lado) or _webp(img, lado, QUALIDADE)
    if max(img.size) <= LADO_MINIATURA:
        return foto, foto           # foto pequena: a "miniatura" seria a mesma foto com menos qualidade
    return foto, _webp(img, LADO_MINIATURA, QUALIDADE_MINIATURA)


def animada(ficheiro):
    """GIF/WebP animados ficam como estão (converter perdia a animação)."""
    try:
        ficheiro.seek(0)
        img = Image.open(ficheiro)
        r = getattr(img, 'is_animated', False)
        ficheiro.seek(0)
        return r
    except Exception:
        return False
