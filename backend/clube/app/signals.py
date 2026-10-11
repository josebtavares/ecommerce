"""
Ficheiros de media substituídos e vídeos novos.

  • Quando um ficheiro é SUBSTITUÍDO (novo banner, logo, vídeo/imagem do produto…), o anterior
    é apagado do storage — sem isto ficavam órfãos para sempre (disco na dev, R2 na prod).
  • Quando o ficheiro novo é um vídeo, agenda a otimização (app/utils/video.py). O poster do
    ficheiro anterior é apagado em video.agendar().

Funciona com qualquer view/admin/shell que grave o modelo, sem ter de chamar nada à mão.
  post_init — guarda os nomes tal como vieram da BD (para detectar trocas sem queries);
  pre_save  — se o campo parece ter mudado, lê o nome que está na BD (fonte de verdade:
              o worker grava com update() e o objeto em memória pode estar desactualizado);
  post_save — apaga o anterior e agenda o vídeo depois do commit (rollback = nada apagado).

O worker de vídeo grava com QuerySet.update() — não passa por aqui — e apaga ele próprio o
original que converteu.
"""
import logging

from django.core.files import File
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_init, post_save, pre_save
from django.dispatch import receiver

from .models import Galeria, Loja, Produto
from .utils import video

log = logging.getLogger(__name__)

# campos cujo ficheiro anterior é apagado quando é substituído
CAMPOS_FICHEIRO = {
    Loja:    ('logo', 'banner'),
    Produto: ('ficheiro',),
    Galeria: ('ficheiro',),
}
# campos com vídeo a otimizar
CAMPOS_VIDEO = {Loja: 'banner', Produto: 'ficheiro', Galeria: 'ficheiro'}

# onde procurar antes de apagar (nenhum outro registo pode estar a usar o ficheiro)
_REFERENCIAS = (
    (Loja,    ('logo', 'banner', 'banner_poster')),
    (Produto, ('ficheiro', 'ficheiro_poster')),
    (Galeria, ('ficheiro', 'ficheiro_poster')),
)


def _nome(valor):
    return getattr(valor, 'name', valor) or ''


def _em_uso(nome):
    return any(
        Modelo.objects.filter(**{campo: nome}).exists()
        for Modelo, campos in _REFERENCIAS for campo in campos
    )


def _apagar_anterior(storage, nome):
    if not nome or _em_uso(nome):
        return
    try:
        storage.delete(nome)
    except Exception as e:   # um órfão não deve estragar o pedido
        log.warning('[media] não consegui apagar %s: %s', nome, e)


def _campos_tocados(sender, instance, update_fields):
    for campo in CAMPOS_FICHEIRO.get(sender, ()):
        if update_fields is not None and campo not in update_fields:
            continue
        if campo not in instance.__dict__:          # campo adiado e não tocado
            continue
        yield campo


@receiver(post_init)
def _guardar_ficheiros_iniciais(sender, instance, **kwargs):
    campos = CAMPOS_FICHEIRO.get(sender)
    if not campos:
        return
    # lê o valor "cru" — não força a carga de campos adiados (.only()/.defer())
    instance._ficheiros_iniciais = {c: _nome(instance.__dict__.get(c)) for c in campos}


@receiver(pre_save)
def _ler_ficheiros_anteriores(sender, instance, update_fields=None, raw=False, **kwargs):
    if sender not in CAMPOS_FICHEIRO or raw:
        return
    instance._ficheiros_anteriores = {}
    if instance._state.adding or instance.pk is None:
        return
    iniciais = getattr(instance, '_ficheiros_iniciais', {})
    for campo in _campos_tocados(sender, instance, update_fields):
        valor = instance.__dict__.get(campo)
        if isinstance(valor, FieldFile):
            upload_novo = not valor._committed       # atribuído mas ainda não gravado
        else:
            upload_novo = isinstance(valor, File)    # File/UploadedFile cru
        if upload_novo or _nome(valor) != iniciais.get(campo, ''):
            instance._ficheiros_anteriores[campo] = (
                sender.objects.filter(pk=instance.pk).values_list(campo, flat=True).first() or ''
            )


@receiver(post_save)
def _ficheiro_substituido(sender, instance, created, update_fields=None, raw=False, **kwargs):
    if sender not in CAMPOS_FICHEIRO or raw:
        return
    anteriores = getattr(instance, '_ficheiros_anteriores', {})
    iniciais   = getattr(instance, '_ficheiros_iniciais', {})

    for campo in _campos_tocados(sender, instance, update_fields):
        atual = _nome(instance.__dict__.get(campo))
        iniciais[campo] = atual
        if created:
            mudou, anterior = bool(atual), ''
        elif campo in anteriores:
            anterior = anteriores[campo]
            mudou    = anterior != atual
        else:
            continue

        if not mudou:
            continue
        if anterior:
            storage = sender._meta.get_field(campo).storage
            transaction.on_commit(lambda s=storage, n=anterior: _apagar_anterior(s, n))
        if CAMPOS_VIDEO.get(sender) == campo:
            transaction.on_commit(lambda c=campo: video.agendar(instance, c))

    instance._ficheiros_iniciais  = iniciais
    instance._ficheiros_anteriores = {}
