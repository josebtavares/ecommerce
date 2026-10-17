"""
Imagens do chat: privadas, normalizadas e sem metadados.

• Armazenamento próprio, nunca o /media/ público nem o bucket R2 público:
    - dev  → pasta `privado/` (fora do MEDIA_ROOT, não é servida directamente)
    - prod → bucket R2 SEM acesso público (R2_BUCKET_PRIVADO); sem ele, o envio de imagens fica desligado
  No R2 o acesso público é por bucket inteiro — por isso não basta uma "pasta privada" no bucket actual.
• Só se abrem por /api/chat/anexos/<id>/?t=<assinatura> (link assinado, gerado para quem participa).
• Redimensionadas (1600px), convertidas para WebP e sem EXIF (as fotos de telemóvel trazem o GPS).
"""
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.core import signing
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

TAMANHO_MAX = 10 * 1024 * 1024        # 10 MB (o ficheiro original)
PIXEIS_MAX = 40_000_000               # protege contra "bombas" de descompressão
LADO_MAX = 1600
FORMATOS = ('JPEG', 'PNG', 'WEBP', 'GIF')
VALIDADE_LINK = 60 * 60               # 1 hora
SALT = 'chat-anexo'


def _usa_s3():
    # Django 5.1+ só lê STORAGES (o DEFAULT_FILE_STORAGE antigo é ignorado)
    backend = getattr(settings, 'STORAGES', {}).get('default', {}).get('BACKEND', '')
    return 'S3Boto3Storage' in backend


def armazenamento_privado():
    """Storage das imagens do chat (callable do FileField — avaliado ao arrancar)."""
    bucket = os.environ.get('R2_BUCKET_PRIVADO')
    if bucket:
        from storages.backends.s3boto3 import S3Boto3Storage
        # sem custom_domain: os links são assinados e temporários, servidos pelo endpoint do R2
        return S3Boto3Storage(bucket_name=bucket, custom_domain=None, default_acl=None,
                              querystring_auth=True, querystring_expire=300, file_overwrite=False)
    return FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'privado'), base_url=None)


def imagens_disponiveis():
    """Na prod só com o bucket privado configurado (nunca cair no disco do contentor)."""
    return bool(os.environ.get('R2_BUCKET_PRIVADO')) or not _usa_s3()


class ImagemInvalida(Exception):
    pass


def processar(ficheiro):
    """→ (ContentFile .webp, largura, altura). Lança ImagemInvalida com a mensagem para o utilizador."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    if ficheiro.size > TAMANHO_MAX:
        raise ImagemInvalida('A imagem tem mais de 10 MB.')
    try:
        img = Image.open(ficheiro)
        formato = img.format
        if formato not in FORMATOS:
            raise ImagemInvalida('Formato não suportado (usa JPG, PNG, WebP ou GIF).')
        if img.width * img.height > PIXEIS_MAX:
            raise ImagemInvalida('A imagem é demasiado grande.')
        img.verify()                      # ficheiro corrompido / disfarçado
        ficheiro.seek(0)
        img = Image.open(ficheiro)
        img.load()
    except ImagemInvalida:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ImagemInvalida('Ficheiro de imagem inválido.')

    img = ImageOps.exif_transpose(img)    # respeita a rotação da câmara antes de largar o EXIF
    tem_alfa = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
    img = img.convert('RGBA' if tem_alfa else 'RGB')
    img.thumbnail((LADO_MAX, LADO_MAX))

    saida = BytesIO()
    img.save(saida, 'WEBP', quality=80, method=4)   # sem exif= → sai sem metadados
    return ContentFile(saida.getvalue(), name=f'{uuid.uuid4().hex}.webp'), img.width, img.height


# ── links assinados ──────────────────────────────────────────────

def assinar(mensagem_id, utilizador_id):
    return signing.dumps({'m': mensagem_id, 'u': utilizador_id}, salt=SALT, compress=True)


def ler_assinatura(token):
    """→ (mensagem_id, utilizador_id) ou None se inválida/expirada."""
    try:
        dados = signing.loads(token, salt=SALT, max_age=VALIDADE_LINK)
        return int(dados['m']), int(dados['u'])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None
