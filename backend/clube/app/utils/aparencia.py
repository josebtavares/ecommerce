"""
Aparência do site, mudada em Admin → Definições sem deploy: o fundo do login, o fundo do registo e o logótipo.

• Fundos: imagem ou vídeo, guardados como HomeImagem (a mesma otimização da publicidade da home:
  fotos → WebP 1920 px + 600 px no upload; vídeos → MP4 1080p + 720p (telemóveis) + poster, pelo worker).
  Um vídeo novo fica em <campo>_novo até o worker acabar; até lá o site continua com o anterior.
  O "Recuperar senha" usa o fundo do login; o registo usa o do login se não tiver um próprio.
• Logótipo: duas versões (fundos claros = o principal; fundos escuros = tema escuro). Convertido para WebP
  640 px com a transparência. Do logo principal geram-se os ícones (separador do browser 32 px, ecrã inicial
  do telemóvel 180 px, emails 192 px), em PNG.
• Os ficheiros vão para o storage do site: pasta media na dev, Cloudflare R2 na produção.

Vazio = o original (os ficheiros que vêm com o frontend). O frontend lê tudo em GET /app/plataforma/aparencia/.
"""
import io
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

FUNDOS = ('login', 'registo')
LOGOS = {'claro': 'logo', 'escuro': 'logo_escuro'}
LADO_LOGO = 640
ICONES = {'32': 32, '180': 180, '192': 192}
LOGO_MAX_MB = 5
VIDEO_MAX_MB = 40
VIDEO_MAX_S = 60


def _url(nome, request=None):
    if not nome:
        return None
    url = default_storage.url(nome)
    return request.build_absolute_uri(url) if request is not None and url.startswith('/') else url


def _media(im, request=None):
    if im is None or not im.ficheiro:
        return None
    return {'id': im.id, 'tipo': im.tipo, 'url': _url(im.ficheiro.name, request),
            'poster': _url(im.ficheiro_poster.name, request) if im.ficheiro_poster else None,
            'estado': (im.ficheiro_estado or 'pendente') if im.tipo == 'video' else 'pronto'}


def promover(cfg=None):
    """Vídeo novo já otimizado → passa a ser o fundo em uso. Corre ao ler (o pedido seguinte ao fim do worker)."""
    from ..models import ConfiguracaoPlataforma
    cfg = cfg or ConfiguracaoPlataforma.atual()
    prontos = [f for f in FUNDOS if getattr(cfg, f'fundo_{f}_novo_id')
               and getattr(cfg, f'fundo_{f}_novo').ficheiro_estado == 'pronto']
    if not prontos:
        return cfg
    with transaction.atomic():
        cfg = ConfiguracaoPlataforma.objects.select_for_update().get(pk=1)
        for f in prontos:
            novo = getattr(cfg, f'fundo_{f}_novo')
            if novo is not None and novo.ficheiro_estado == 'pronto':
                setattr(cfg, f'fundo_{f}', novo)
                setattr(cfg, f'fundo_{f}_novo', None)
        cfg.save()
    return cfg


def publico(request=None):
    """O que o site mostra (null = o original)."""
    cfg = promover()
    login = _media(cfg.fundo_login, request)
    return {
        'fundo_login': login,
        'fundo_registo': _media(cfg.fundo_registo, request) or login,
        'logo': _url(cfg.logo.name, request) if cfg.logo else None,
        'logo_escuro': _url(cfg.logo_escuro.name, request) if cfg.logo_escuro else None,
        'icones': {k: _url(v, request) for k, v in (cfg.icones or {}).items() if v} or None,
    }


def admin(request=None):
    """O que o editor mostra: o que está em uso e o vídeo que ainda está a ser otimizado (ou falhou)."""
    cfg = promover()
    d = publico(request)
    for f in FUNDOS:
        d[f'fundo_{f}_proprio'] = bool(getattr(cfg, f'fundo_{f}_id'))
        d[f'fundo_{f}_novo'] = _media(getattr(cfg, f'fundo_{f}_novo'), request)
    d['fundo_registo_igual'] = not cfg.fundo_registo_id and not cfg.fundo_registo_novo_id
    d['limites'] = {'video_mb': VIDEO_MAX_MB, 'video_s': VIDEO_MAX_S, 'logo_mb': LOGO_MAX_MB}
    return d


def icones_em_uso():
    """Nomes dos ícones gerados (não estão num FileField: a limpeza pergunta aqui antes de apagar)."""
    from ..models import ConfiguracaoPlataforma
    cfg = ConfiguracaoPlataforma.objects.filter(pk=1).only('icones').first()
    return {v for v in ((cfg.icones or {}).values() if cfg else ()) if v}


def usadas():
    """Ids de HomeImagem usados pelos fundos (a limpeza da home não os apaga)."""
    from ..models import ConfiguracaoPlataforma
    cfg = ConfiguracaoPlataforma.objects.filter(pk=1).first()
    if cfg is None:
        return set()
    return {i for i in (cfg.fundo_login_id, cfg.fundo_login_novo_id, cfg.fundo_registo_id, cfg.fundo_registo_novo_id) if i}


def definir_fundo(qual, im):
    """im = HomeImagem acabada de carregar (ou None = repor o original / no registo: igual ao do login)."""
    from ..models import ConfiguracaoPlataforma
    with transaction.atomic():
        cfg = ConfiguracaoPlataforma.objects.select_for_update().get_or_create(pk=1)[0]
        if im is None:
            setattr(cfg, f'fundo_{qual}', None)
            setattr(cfg, f'fundo_{qual}_novo', None)
        elif im.tipo == 'video' and im.ficheiro_estado != 'pronto':
            setattr(cfg, f'fundo_{qual}_novo', im)          # o anterior continua até o worker acabar
        else:
            setattr(cfg, f'fundo_{qual}', im)
            setattr(cfg, f'fundo_{qual}_novo', None)
        cfg.save()


# ── logótipo ───────────────────────────────────────────────────────

def _abrir_logo(ficheiro):
    from PIL import Image
    from . import versoes_media
    img = versoes_media._abrir(ficheiro, LADO_LOGO * 2)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    caixa = img.getbbox()                 # tira a margem transparente à volta (o ícone fica maior)
    if caixa and img.getchannel('A').getextrema()[0] < 255:
        img = img.crop(caixa)
    return img


def _webp_logo(img):
    from PIL import Image
    copia = img.copy()
    copia.thumbnail((LADO_LOGO, LADO_LOGO), Image.LANCZOS)
    saida = io.BytesIO()
    copia.save(saida, 'WEBP', quality=92, method=6)       # com a transparência
    return saida.getvalue()


def _icone(img, lado, fundo, margem, redondo=False):
    """PNG quadrado com o logo centrado; fundo None = transparente."""
    from PIL import Image, ImageDraw
    tela = Image.new('RGBA', (lado, lado), fundo or (0, 0, 0, 0))
    util = max(1, round(lado * (1 - 2 * margem)))
    copia = img.copy()
    copia.thumbnail((util, util), Image.LANCZOS)
    tela.alpha_composite(copia, ((lado - copia.width) // 2, (lado - copia.height) // 2))
    if redondo:                            # como o ícone original dos emails: quadrado branco com cantos redondos
        mascara = Image.new('L', (lado, lado), 0)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, lado - 1, lado - 1), radius=round(lado * 0.2), fill=255)
        tela.putalpha(Image.composite(tela.getchannel('A'), mascara, mascara))
    saida = io.BytesIO()
    tela.save(saida, 'PNG', optimize=True)
    return saida.getvalue()


def icones_de(img):
    """{'32': bytes, '180': bytes, '192': bytes} — 32 transparente (separador), 180 fundo branco (iPhone/Android),
    192 branco com cantos redondos (emails, ecrã inicial)."""
    return {'32': _icone(img, 32, None, 0.0),
            '180': _icone(img, 180, (255, 255, 255, 255), 0.12),
            '192': _icone(img, 192, (255, 255, 255, 255), 0.14, redondo=True)}


class LogoInvalido(Exception):
    pass


def definir_logo(tema, ficheiro):
    """Grava o logo (WebP 640 px com transparência) e, no principal, os ícones. ficheiro None = repor o original."""
    from ..models import ConfiguracaoPlataforma
    from . import limpeza, versoes_media
    campo = LOGOS[tema]
    novos_icones = None
    if ficheiro is not None:
        try:
            img = _abrir_logo(ficheiro)
        except versoes_media.ImagemInvalida as e:
            raise LogoInvalido(str(e))
        if min(img.size) < 16:
            raise LogoInvalido('O logótipo é demasiado pequeno.')
        dados = _webp_logo(img)
        if campo == 'logo':
            novos_icones = icones_de(img)
    with transaction.atomic():
        cfg = ConfiguracaoPlataforma.objects.select_for_update().get_or_create(pk=1)[0]
        antigos = [getattr(cfg, campo).name] if getattr(cfg, campo) else []
        if campo == 'logo':
            antigos += [v for v in (cfg.icones or {}).values() if v]
        if ficheiro is None:
            setattr(cfg, campo, '')
            if campo == 'logo':
                cfg.icones = {}
        else:
            # uploads.py dá-lhe o nome da plataforma (<20 hex>.webp) e grava a versão __600 ao lado
            base = f'site/{uuid.uuid4().hex[:12]}'
            setattr(cfg, campo, ContentFile(dados, name='logo.webp'))
            if novos_icones:
                cfg.icones = {k: default_storage.save(f'{base}-icone-{k}.png', ContentFile(v))
                              for k, v in novos_icones.items()}
        cfg.save()
        if antigos:
            limpeza.agendar_apagar_depois_do_commit(antigos, 'aparencia:logo')
    return cfg
