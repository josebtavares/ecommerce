"""
Validação de TODOS os uploads públicos (imagens/vídeos de lojas, produtos, POS, perfil).

Os validadores dos campos (FileExtensionValidator) só correm em full_clean/serializers, e várias
views gravam o ficheiro directamente (ProdutoImagem.objects.create, produto.ficheiro = …,
serializer.save(logo=…)). Resultado: dava para pôr um .html ou .svg no bucket público com o
domínio da plataforma (página de phishing / script). Aqui a verificação corre no pre_save de
cada modelo, antes de o FileField enviar o ficheiro para o storage — vale para todos os caminhos.

Fotos no storage público: convertidas aqui mesmo (utils/versoes_media.py) — rodadas pela orientação da
câmara, sem metadados (localização…), WebP com no máximo 1600 px e uma miniatura de 600 px gravada ao lado
depois do save. Nunca se rejeita uma foto por ter muitos píxeis; só pelo peso (MAX_IMAGEM_MB) ou se não for
uma imagem. GIF/WebP animados e os campos com storage próprio (privado: comprovativos, reembolsos) ficam como estão.

O chat tem o seu próprio tratamento (app/chat/imagens.py: re-codifica em WebP, bucket privado).
"""
import os

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import FileField, ImageField
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_save, pre_save

from .utils import versoes_media

IMAGENS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'avif'}
VIDEOS = {'mp4', 'webm', 'mov', 'mkv'}
# só nos campos que o pedem explicitamente (FileExtensionValidator(['pdf']) — ex.: Encomenda.fatura_pdf)
DOCUMENTOS = {'pdf'}
MAX_IMAGEM_MB = 20      # antes de converter (as fotos de telemóveis de 50–200 MP chegam aos 20 MB)
MAX_VIDEO_MB = 200


def _novo(valor):
    """Ficheiro acabado de atribuir (ainda não gravado no storage)?"""
    if isinstance(valor, FieldFile):
        return bool(valor.name) and not valor._committed
    return isinstance(valor, File)


def validar_ficheiro(campo, ficheiro):
    ext = os.path.splitext(ficheiro.name or '')[1].lower().lstrip('.')
    aceites = IMAGENS if isinstance(campo, ImageField) else IMAGENS | VIDEOS
    # se o campo tem uma lista própria (p.ex. o banner, mais curta; a fatura, só PDF), essa manda
    for v in campo.validators:
        if getattr(v, 'allowed_extensions', None):
            aceites = (aceites | DOCUMENTOS) & {e.lower() for e in v.allowed_extensions}
    if ext not in aceites:
        raise ValidationError(f'Tipo de ficheiro não permitido (.{ext or "?"}). Aceites: '
                              + ', '.join(sorted(aceites)) + '.')
    tamanho = getattr(ficheiro, 'size', 0) or 0
    limite = MAX_VIDEO_MB if ext in VIDEOS else MAX_IMAGEM_MB
    if tamanho > limite * 1024 * 1024:
        raise ValidationError(f'O ficheiro tem mais de {limite} MB.')


def _antes_de_gravar(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw:
        return
    for campo in sender._meta.concrete_fields:
        if not isinstance(campo, FileField):
            continue
        if update_fields is not None and campo.name not in update_fields:
            continue
        valor = instance.__dict__.get(campo.attname)
        if _novo(valor):
            validar_ficheiro(campo, valor)
            _otimizar(instance, campo, valor)


def _otimizar(instance, campo, valor):
    """Foto nova no storage público → WebP 1600 px (substitui o valor) + miniatura para depois do save."""
    ext = os.path.splitext(valor.name or '')[1].lower().lstrip('.')
    if ext not in IMAGENS or ext == 'gif' or campo.storage is not default_storage:
        return
    if versoes_media.animada(valor):
        return
    try:
        foto, miniatura = versoes_media.converter_imagem(
            valor, versoes_media.lado_de(instance._meta.model_name, campo.name))
    except versoes_media.ImagemInvalida as e:
        raise ValidationError(str(e))
    setattr(instance, campo.attname, ContentFile(foto, name=versoes_media.nome_novo('webp')))
    instance.__dict__.setdefault('_miniaturas_por_gravar', {})[campo.attname] = miniatura


def _depois_de_gravar(sender, instance, raw=False, **kwargs):
    for attname, miniatura in instance.__dict__.pop('_miniaturas_por_gravar', {}).items():
        nome = versoes_media.variante(getattr(instance, attname).name, '__600')
        if nome:
            default_storage.save(nome, ContentFile(miniatura))


def ligar():
    """Chamado em AppConfig.ready()."""
    from django.apps import apps
    for modelo in apps.get_models():
        if modelo._meta.app_label not in ('app', 'pos', 'servicos'):
            continue
        if any(isinstance(c, FileField) for c in modelo._meta.concrete_fields):
            pre_save.connect(_antes_de_gravar, sender=modelo, weak=False,
                             dispatch_uid=f'uploads_{modelo._meta.label}')
            post_save.connect(_depois_de_gravar, sender=modelo, weak=False,
                              dispatch_uid=f'uploads_depois_{modelo._meta.label}')
