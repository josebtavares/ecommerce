"""
Ficheiros de media: substituídos, apagados e vídeos novos.

  • Ficheiro SUBSTITUÍDO (novo banner, logo, vídeo/imagem do produto…) → o anterior vai para a
    fila de limpeza (app/utils/limpeza.py) e o worker apaga-o em segundo plano.
  • Registo APAGADO (imagem adicional, item da galeria, produto/loja eliminados…) → os ficheiros
    dele vão para a mesma fila. Funciona também para apagamentos em cascata.
  • Ficheiro novo que é vídeo → agenda a otimização (app/utils/video.py).

Tudo depois do commit: se a transacção falhar, nada é apagado nem agendado.

Detecção da troca:
  post_init — guarda os nomes tal como vieram da BD (detecta trocas sem queries);
  pre_save  — se o campo parece ter mudado, lê o nome que está na BD (fonte de verdade:
              o worker grava com update() e o objeto em memória pode estar desactualizado);
  post_save — agenda a limpeza do anterior e a otimização do vídeo.

Os receivers estão ligados só aos modelos com ficheiros (com sender explícito), para não
desligar o "fast delete" do Django nos restantes modelos.
"""
from django.core.files import File
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_delete, post_init, post_save, pre_save

from .models import Galeria, Loja, Produto
from .utils import limpeza, video

# campos cujo ficheiro anterior é apagado quando é substituído
CAMPOS_FICHEIRO = {
    Loja:    ('logo', 'banner'),
    Produto: ('ficheiro',),
    Galeria: ('ficheiro',),
}
# campos com vídeo a otimizar
CAMPOS_VIDEO = {Loja: 'banner', Produto: 'ficheiro', Galeria: 'ficheiro'}


def _nome(valor):
    return getattr(valor, 'name', valor) or ''


def _campos_tocados(sender, instance, update_fields):
    for campo in CAMPOS_FICHEIRO.get(sender, ()):
        if update_fields is not None and campo not in update_fields:
            continue
        if campo not in instance.__dict__:          # campo adiado e não tocado
            continue
        yield campo


# ── Substituição ─────────────────────────────────────────────────────────────

def _guardar_ficheiros_iniciais(sender, instance, **kwargs):
    # lê o valor "cru" — não força a carga de campos adiados (.only()/.defer())
    instance._ficheiros_iniciais = {c: _nome(instance.__dict__.get(c)) for c in CAMPOS_FICHEIRO[sender]}


def _ler_ficheiros_anteriores(sender, instance, update_fields=None, raw=False, **kwargs):
    instance._ficheiros_anteriores = {}
    if raw or instance._state.adding or instance.pk is None:
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


def _ficheiro_substituido(sender, instance, created, update_fields=None, raw=False, **kwargs):
    if raw:
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
            limpeza.agendar_apagar_depois_do_commit(
                [anterior], f'substituido:{sender._meta.model_name}.{campo}')
        if CAMPOS_VIDEO.get(sender) == campo:
            transaction.on_commit(lambda c=campo: video.agendar(instance, c))

    instance._ficheiros_iniciais  = iniciais
    instance._ficheiros_anteriores = {}


for _modelo in CAMPOS_FICHEIRO:
    post_init.connect(_guardar_ficheiros_iniciais, sender=_modelo, weak=False)
    pre_save.connect(_ler_ficheiros_anteriores, sender=_modelo, weak=False)
    post_save.connect(_ficheiro_substituido, sender=_modelo, weak=False)


# ── Registo apagado ──────────────────────────────────────────────────────────

def _registo_apagado(sender, instance, **kwargs):
    nomes = [
        _nome(instance.__dict__.get(campo))
        for Modelo, campo in limpeza.campos_ficheiro() if Modelo is sender
    ]
    limpeza.agendar_apagar_depois_do_commit(nomes, f'apagado:{sender._meta.model_name}')


def ligar_limpeza_ao_apagar():
    """Chamado em AppConfig.ready(): todos os modelos com FileField/ImageField."""
    for Modelo in {m for m, _ in limpeza.campos_ficheiro()}:
        post_delete.connect(_registo_apagado, sender=Modelo, weak=False,
                            dispatch_uid=f'limpeza_apagado_{Modelo._meta.label}')
