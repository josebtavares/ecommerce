"""
Invalidação da cache pública da borda (clube/borda.py).

A chave de cada resposta guardada leva versões no Redis:
  borda:v:global      — configuração da plataforma (rodapé, home, categorias, planos): invalida tudo;
  borda:v:catalogo    — sobe com qualquer mudança de qualquer loja (home, lista de lojas, produto avulso);
  borda:v:loja:<id>   — sobe quando algo DESSA loja muda (página da loja, produtos dela, categorias, entregas…).
Os sinais post_save/post_delete dos modelos abaixo sobem as versões depois do commit, por isso o visitante vê a
mudança no pedido seguinte. O que muda com .update() (sem sinais) fica no máximo CACHE_PUBLICO_S (60 s).
"""
import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save

log = logging.getLogger(__name__)
PREFIXO = 'borda:v:'

# modelos de uma loja: (app, nome) → como chegar à loja a partir da instância
DA_LOJA = {
    ('app', 'Loja'): 'pk',
    ('app', 'LojaEnderecoAntigo'): 'loja_id', ('app', 'TipoProduto'): 'loja_id', ('app', 'Produto'): 'loja_id',
    ('app', 'Inventario'): 'loja_id', ('app', 'OpcaoEntrega'): 'loja_id', ('app', 'HorarioLoja'): 'loja_id',
    ('app', 'ExcecaoHorario'): 'loja_id', ('app', 'MetodoPagamento'): 'loja_id', ('app', 'AvaliacaoLoja'): 'loja_id',
    ('app', 'CategoriaLoja'): 'loja_id', ('app', 'DocumentoLoja'): 'loja_id', ('app', 'DadosBancarios'): 'loja_id',
    ('app', 'AdesaoVinti4'): 'loja_id', ('app', 'Subscricao'): 'loja_id',
    ('app', 'ProdutoImagem'): 'produto', ('app', 'VarianteProduto'): 'produto',
    ('app', 'ComponenteConjunto'): 'produto', ('app', 'OpcaoEscolha'): 'produto', ('app', 'GrupoEscolha'): 'conjunto',
    ('app', 'CategoriaDestaque'): 'categoria',
    ('servicos', 'ConfigServicos'): 'loja_id', ('servicos', 'Profissional'): 'loja_id',
    ('servicos', 'Servico'): 'loja_id', ('servicos', 'ComponentePacote'): 'servico',
    ('servicos', 'ServicoImagem'): 'servico', ('servicos', 'HorarioProfissional'): 'profissional',
    ('servicos', 'AusenciaProfissional'): 'profissional',
}
# da plataforma: invalidam tudo
GLOBAIS = {('app', 'ConfiguracaoPlataforma'), ('app', 'PaginaInstitucional'), ('app', 'HomeSeccao'),
           ('app', 'HomeImagem'), ('app', 'HomeItem'), ('app', 'HomePublicacao'), ('app', 'LojaTemplate'),
           ('app', 'PlanoSubscricao'), ('app', 'Categoria')}


def _redis():
    from django_redis import get_redis_connection
    return get_redis_connection('default')


def invalidar(loja_id=None, tudo=False):
    """Sobe as versões depois do commit (fora de transacção: já)."""
    def subir():
        try:
            p = _redis().pipeline()
            if tudo:
                p.incr(PREFIXO + 'global')
            p.incr(PREFIXO + 'catalogo')
            if loja_id:
                p.incr(f'{PREFIXO}loja:{loja_id}')
            p.execute()
        except Exception as e:   # sem Redis não há cache a invalidar
            log.warning('cache pública: não invalidou (%s)', e)
    transaction.on_commit(subir)


def invalidar_stock(produto_id=None, variante_id=None, inventario_id=None):
    """O stock muda com .update(F(...)) (sem sinais): invalida a loja do produto."""
    from ..models import Produto, Inventario, VarianteProduto
    if produto_id:
        loja = Produto.objects.filter(pk=produto_id).values_list('loja_id', flat=True).first()
    elif variante_id:
        loja = VarianteProduto.objects.filter(pk=variante_id).values_list('produto__loja_id', flat=True).first()
    elif inventario_id:
        loja = Inventario.objects.filter(pk=inventario_id).values_list('produto__loja_id', flat=True).first()
    else:
        return
    if loja:
        invalidar(loja_id=loja)


def _loja_de(instancia, via):
    if via == 'pk':
        return instancia.pk
    if via == 'loja_id':
        return getattr(instancia, 'loja_id', None)
    rel = getattr(instancia, f'{via}_id', None)
    if rel is None:
        return None
    modelo = instancia._meta.get_field(via).related_model
    campo = 'loja_id'
    return modelo.objects.filter(pk=rel).values_list(campo, flat=True).first()


def _ao_mudar(sender, instance, **kw):
    if kw.get('raw'):
        return
    chave = (sender._meta.app_label, sender.__name__)
    if chave in GLOBAIS:
        return invalidar(tudo=True)
    via = DA_LOJA.get(chave)
    if via is None:
        return
    try:
        loja = _loja_de(instance, via)
    except Exception:
        loja = None
    # sem loja conhecida (ex.: o pai já foi apagado): invalida tudo, por segurança
    invalidar(loja_id=loja, tudo=loja is None)


def ligar():
    from django.apps import apps
    for app_label, nome in list(DA_LOJA) + list(GLOBAIS):
        modelo = apps.get_model(app_label, nome)
        post_save.connect(_ao_mudar, sender=modelo, dispatch_uid=f'cache_publico_s_{app_label}_{nome}')
        post_delete.connect(_ao_mudar, sender=modelo, dispatch_uid=f'cache_publico_d_{app_label}_{nome}')
