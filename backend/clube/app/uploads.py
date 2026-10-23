"""
Validação de TODOS os uploads públicos (imagens/vídeos de lojas, produtos, POS, perfil).

Os validadores dos campos (FileExtensionValidator) só correm em full_clean/serializers, e várias
views gravam o ficheiro directamente (ProdutoImagem.objects.create, produto.ficheiro = …,
serializer.save(logo=…)). Resultado: dava para pôr um .html ou .svg no bucket público com o
domínio da plataforma (página de phishing / script). Aqui a verificação corre no pre_save de
cada modelo, antes de o FileField enviar o ficheiro para o storage — vale para todos os caminhos.

O chat tem o seu próprio tratamento (app/chat/imagens.py: re-codifica em WebP, bucket privado).
"""
import os

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import FileField, ImageField
from django.db.models.fields.files import FieldFile
from django.db.models.signals import pre_save

IMAGENS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'avif'}
VIDEOS = {'mp4', 'webm', 'mov', 'mkv'}
MAX_IMAGEM_MB = 10
MAX_VIDEO_MB = 200


def _novo(valor):
    """Ficheiro acabado de atribuir (ainda não gravado no storage)?"""
    if isinstance(valor, FieldFile):
        return bool(valor.name) and not valor._committed
    return isinstance(valor, File)


def validar_ficheiro(campo, ficheiro):
    ext = os.path.splitext(ficheiro.name or '')[1].lower().lstrip('.')
    aceites = IMAGENS if isinstance(campo, ImageField) else IMAGENS | VIDEOS
    # se o campo tem uma lista própria mais curta (p.ex. o banner), essa manda
    for v in campo.validators:
        if getattr(v, 'allowed_extensions', None):
            aceites = aceites & {e.lower() for e in v.allowed_extensions}
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


def ligar():
    """Chamado em AppConfig.ready()."""
    from django.apps import apps
    for modelo in apps.get_models():
        if modelo._meta.app_label not in ('app', 'pos', 'servicos'):
            continue
        if any(isinstance(c, FileField) for c in modelo._meta.concrete_fields):
            pre_save.connect(_antes_de_gravar, sender=modelo, weak=False,
                             dispatch_uid=f'uploads_{modelo._meta.label}')
