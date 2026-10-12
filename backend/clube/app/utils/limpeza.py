"""
Limpeza do storage em segundo plano (disco na dev, Cloudflare R2 na prod — mesmo código).

  agendar_apagar(nomes)   → põe ficheiros na fila (FicheiroParaApagar); chamado depois do commit
                            quando um ficheiro é substituído ou o registo dono é apagado.
  processar_lote()        → o worker (manage.py processar_videos) apaga-os aos poucos.

Regra de ouro: um ficheiro só é apagado se NENHUM registo o usar no momento de apagar
(_em_uso percorre todos os FileField/ImageField dos modelos) e se não for um ficheiro
"de sistema" (defaults dos modelos, ex.: utilizadores/default.png).
"""
import logging

from django.apps import apps
from django.core.files.storage import default_storage
from django.db import models, transaction

log = logging.getLogger(__name__)

MAX_TENTATIVAS = 5

# ficheiros usados pelo código (não pela BD) — nunca apagar
PROTEGIDOS_EXTRA = {
    'utilizadores/default.png',
    'lojas/default_banner.jpg',
}

# pastas com recursos do site carregados à mão no storage e referidos pelo frontend
# por URL directo (ex.: videos/background.mp4 do login) — nunca apagar
PASTAS_PROTEGIDAS = ('videos/', 'chat_privado/')   # chat_privado: imagens do chat (armazenamento privado)

_cache = {}


def campos_ficheiro():
    """[(Modelo, nome_do_campo)] de todos os FileField/ImageField dos modelos do projecto."""
    if 'campos' not in _cache:
        lista = []
        for Modelo in apps.get_models():
            if Modelo._meta.app_label not in ('app', 'pos'):
                continue
            for f in Modelo._meta.get_fields():
                if isinstance(f, models.FileField):
                    lista.append((Modelo, f.name))
        _cache['campos'] = lista
    return _cache['campos']


def protegidos():
    if 'protegidos' not in _cache:
        nomes = set(PROTEGIDOS_EXTRA)
        for Modelo, campo in campos_ficheiro():
            default = Modelo._meta.get_field(campo).default
            if isinstance(default, str) and default:
                nomes.add(default)
        _cache['protegidos'] = nomes
    return _cache['protegidos']


def protegido(nome):
    return nome in protegidos() or nome.startswith(PASTAS_PROTEGIDAS)


def em_uso(nome):
    return any(Modelo.objects.filter(**{campo: nome}).exists() for Modelo, campo in campos_ficheiro())


def agendar_apagar(nomes, origem=''):
    """Põe ficheiros na fila de limpeza (ignora vazios e protegidos)."""
    nomes = {n for n in nomes if n and not protegido(n)}
    if not nomes:
        return
    FicheiroParaApagar = apps.get_model('app', 'FicheiroParaApagar')
    FicheiroParaApagar.objects.bulk_create(
        [FicheiroParaApagar(nome=n, origem=origem[:60]) for n in nomes]
    )


def agendar_apagar_depois_do_commit(nomes, origem=''):
    """Como agendar_apagar, mas só se a transacção actual for confirmada."""
    nomes = list(nomes)
    transaction.on_commit(lambda: agendar_apagar(nomes, origem))


def processar_lote(tamanho=50):
    """
    Apaga até `tamanho` ficheiros da fila. Devolve quantos saíram da fila (os que falham ficam
    para depois, com tentativas+1 — não contam, para o worker não ficar em ciclo se o storage
    estiver em baixo).
    """
    tratados = 0
    FicheiroParaApagar = apps.get_model('app', 'FicheiroParaApagar')
    with transaction.atomic():
        itens = list(
            FicheiroParaApagar.objects.select_for_update(skip_locked=True)
            .filter(tentativas__lt=MAX_TENTATIVAS).order_by('criado_em')[:tamanho]
        )
        for item in itens:
            if protegido(item.nome) or em_uso(item.nome):
                item.delete()               # voltou a ser usado — não se apaga
                tratados += 1
                continue
            try:
                default_storage.delete(item.nome)   # não existir já não é erro
                item.delete()
                tratados += 1
            except Exception as e:
                item.tentativas += 1
                item.erro = str(e)[-1000:]
                item.save(update_fields=['tentativas', 'erro'])
                log.warning('[limpeza] não consegui apagar %s: %s', item.nome, e)
    return tratados
