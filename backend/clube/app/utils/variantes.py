"""
Stock por variação de produto.

Um atributo gera variantes quando, no schema do TipoProduto, é do tipo "choices"
e tem "variante": true (ex.: tamanho, cor — mas não "picante").
As combinações possíveis de um produto são o produto cartesiano das opções que
o produto tem nesses atributos (produto.atributos).

O modo variante só fica activo num produto quando o dono guarda a grelha
(produto.stock_por_variante = True). Até lá o produto usa o Inventario total.
"""
from itertools import product as produto_cartesiano

from django.db.models import Sum

from ..models import Inventario, VarianteProduto


# ── Atributos e combinações ───────────────────────────────────

def atributos_variante(produto):
    """Nomes dos atributos-variante do tipo do produto, pela ordem do schema."""
    if not produto.tipo:
        return []
    nomes = []
    for campo in produto.tipo.atributos_schema or []:
        if isinstance(campo, dict) and campo.get('variante') and campo.get('tipo') == 'choices':
            nomes.append(campo['nome'])
    return nomes


def _valores(atributos, nome):
    v = (atributos or {}).get(nome)
    if v is None:
        return []
    lista = v if isinstance(v, list) else [v]
    vistos, out = set(), []
    for x in lista:
        s = str(x).strip()
        if s and s not in vistos:
            vistos.add(s)
            out.append(s)
    return out


def chave_de(combinacao):
    """{"tamanho": "M", "cor": "preto"} → "cor=preto|tamanho=M" (ordenada)."""
    return '|'.join(f'{k}={combinacao[k]}' for k in sorted(combinacao))


def combinacoes_produto(produto):
    """
    Lista de combinações possíveis [{"cor": "preto", "tamanho": "M"}, ...].
    Atributos-variante sem opções no produto são ignorados.
    """
    nomes = [n for n in atributos_variante(produto) if _valores(produto.atributos, n)]
    if not nomes:
        return []
    listas = [_valores(produto.atributos, n) for n in nomes]
    return [dict(zip(nomes, valores)) for valores in produto_cartesiano(*listas)]


def tem_atributos_variante(produto):
    return bool(combinacoes_produto(produto))


# ── Sincronização ────────────────────────────────────────────

def sincronizar_variantes(produto):
    """
    Garante que existe uma VarianteProduto activa por combinação actual:
      - cria as que faltam (quantidade 0)
      - reactiva as que voltaram a existir (mantém a quantidade antiga)
      - desactiva as que deixaram de existir
    Devolve a lista de variantes activas, pela ordem das combinações.
    Se o produto deixou de ter atributos-variante, desliga o modo variante.
    """
    combos = combinacoes_produto(produto)
    existentes = {v.chave: v for v in produto.variantes.all()}
    chaves_actuais = []
    activas = []

    for combo in combos:
        chave = chave_de(combo)
        chaves_actuais.append(chave)
        v = existentes.get(chave)
        if v is None:
            v = VarianteProduto.objects.create(produto=produto, combinacao=combo, chave=chave)
        elif not v.ativo or v.combinacao != combo:
            v.ativo = True
            v.combinacao = combo
            v.save(update_fields=['ativo', 'combinacao', 'data_atualizacao'])
        activas.append(v)

    produto.variantes.filter(ativo=True).exclude(chave__in=chaves_actuais).update(ativo=False)

    if not combos and produto.stock_por_variante:
        produto.stock_por_variante = False
        produto.save(update_fields=['stock_por_variante'])

    atualizar_total_inventario(produto)
    return activas


def atualizar_total_inventario(produto):
    """Com stock por variação, o Inventario do produto = soma das variantes activas."""
    if not produto.stock_por_variante:
        return
    total = produto.variantes.filter(ativo=True).aggregate(t=Sum('quantidade'))['t'] or 0
    inv, _ = Inventario.objects.get_or_create(
        loja=produto.loja, produto=produto,
        defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco},
    )
    if inv.quantidade != total:
        inv.quantidade = total
        inv.save(update_fields=['quantidade', 'data_atualizacao'])


# ── Resolução da variante escolhida pelo comprador ───────────

def resolver_variante(produto, atributos_escolhidos, lock=False):
    """
    A partir das opções escolhidas no card ({"tamanho": "M", "cor": "preto", "picante": "médio"})
    devolve (variante, None) ou (None, mensagem_de_erro).
    Para produtos sem stock por variação devolve (None, None).
    """
    if not produto.stock_por_variante:
        return None, None

    nomes = [n for n in atributos_variante(produto) if _valores(produto.atributos, n)]
    escolhidos = atributos_escolhidos or {}
    combo, em_falta = {}, []
    for n in nomes:
        v = escolhidos.get(n)
        if isinstance(v, list):
            v = v[0] if len(v) == 1 else None
        if v is None or not str(v).strip():
            em_falta.append(n)
        else:
            combo[n] = str(v).strip()

    if em_falta:
        return None, f'Escolhe {", ".join(em_falta)} de "{produto.nome}".'

    qs = VarianteProduto.objects.filter(produto=produto, chave=chave_de(combo), ativo=True)
    if lock:
        qs = qs.select_for_update()
    variante = qs.first()
    if not variante:
        return None, f'A combinação {" · ".join(combo.values())} de "{produto.nome}" não está disponível.'
    return variante, None


def serializar_variante(v, produto=None):
    produto = produto or v.produto
    return {
        'id':         v.id,
        'chave':      v.chave,
        'combinacao': v.combinacao,
        'quantidade': v.quantidade,
        'preco':      str(v.preco) if v.preco is not None else None,
        'preco_efetivo': str(v.preco if v.preco is not None else produto.preco),
        'sku':        v.sku,
        'disponivel': v.quantidade > 0,
    }
