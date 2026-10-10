"""
Stock por variação de produto — partilhado por:
  - app.Produto       (loja Bendi)   → variantes: app.VarianteProduto,     total no Inventario
  - pos.ProdutoPOS    (próprio POS)  → variantes: pos.VarianteProdutoPOS,  total em ProdutoPOS.stock

Um atributo gera variantes quando, no schema do TipoProduto, é do tipo "choices"
e tem "variante": true (ex.: tamanho, cor — mas não "picante").
As combinações possíveis de um produto são o produto cartesiano das opções que
o produto tem nesses atributos (produto.atributos).

O modo variante só fica activo num produto quando o dono guarda a grelha
(produto.stock_por_variante = True). Até lá o produto usa o stock total.
"""
import json
from decimal import Decimal, InvalidOperation
from itertools import product as produto_cartesiano

from django.db.models import Sum

from ..models import Inventario


def _e_produto_pos(produto):
    return produto._meta.model_name == 'produtopos'


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
    Garante que existe uma variante activa por combinação actual:
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
            v = produto.variantes.create(combinacao=combo, chave=chave)
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
    """Com stock por variação, o stock total do produto = soma das variantes activas."""
    if not produto.stock_por_variante:
        return
    total = produto.variantes.filter(ativo=True).aggregate(t=Sum('quantidade'))['t'] or 0

    if _e_produto_pos(produto):
        if produto.stock != total or not produto.controlar_stock:
            produto.stock = total
            produto.controlar_stock = True
            produto.save(update_fields=['stock', 'controlar_stock'])
        return

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
    A partir das opções escolhidas ({"tamanho": "M", "cor": "preto", "picante": "médio"})
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

    qs = produto.variantes.filter(chave=chave_de(combo), ativo=True)
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


def variantes_payload(produto):
    """Campos de variação para os payloads de produto (card, POS)."""
    activas = [v for v in produto.variantes.all() if v.ativo] if produto.stock_por_variante else []
    return {
        'atributos_variante':  atributos_variante(produto),
        'stock_por_variante':  produto.stock_por_variante,
        'variantes':           [serializar_variante(v, produto) for v in activas],
        'variantes_pendentes': not produto.stock_por_variante and tem_atributos_variante(produto),
    }


# ── Grelha (backoffice e POS) ────────────────────────────────

def _stock_total_simples(produto):
    if _e_produto_pos(produto):
        return produto.stock
    inv = getattr(produto, 'inventario', None)
    return inv.quantidade if inv else 0


def grelha_variantes(produto):
    """
    Estado da grelha — uma linha por combinação possível, com os valores
    guardados (se existirem). Não escreve na BD.
    """
    existentes = {v.chave: v for v in produto.variantes.all()}
    linhas = []
    for combo in combinacoes_produto(produto):
        chave = chave_de(combo)
        v = existentes.get(chave)
        if v:
            linha = serializar_variante(v, produto)
            linha['combinacao'] = combo
        else:
            linha = {
                'id': None, 'chave': chave, 'combinacao': combo, 'quantidade': 0,
                'preco': None, 'preco_efetivo': str(produto.preco), 'sku': '', 'disponivel': False,
            }
        linhas.append(linha)

    total_simples = _stock_total_simples(produto)
    return {
        'produto_id':         produto.id,
        'produto_nome':       produto.nome,
        'preco_produto':      str(produto.preco),
        'stock_por_variante': produto.stock_por_variante,
        'atributos_variante': [n for n in atributos_variante(produto) if any(n in l['combinacao'] for l in linhas)],
        'variantes':          linhas,
        'total':              sum(l['quantidade'] for l in linhas) if produto.stock_por_variante else total_simples,
        'stock_total_antigo': None if produto.stock_por_variante else total_simples,
    }


def _preco(valor):
    if valor in (None, ''):
        return None, None
    try:
        p = Decimal(str(valor)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None, 'Preço inválido.'
    if p < 0:
        return None, 'O preço não pode ser negativo.'
    return p, None


def guardar_grelha(produto, dados):
    """
    Aplica o PUT da grelha. dados:
      { variantes: [{ chave, quantidade, preco?, sku? }] } → guarda e ACTIVA o modo variante
      { stock_por_variante: false }                        → volta ao stock total (mantém a soma)
    Devolve (grelha, None) ou (None, mensagem_de_erro). Chamar dentro de transaction.atomic.
    """
    if dados.get('stock_por_variante') is False:
        produto.stock_por_variante = False
        produto.save(update_fields=['stock_por_variante'])
        return grelha_variantes(produto), None

    combos = {chave_de(c): c for c in combinacoes_produto(produto)}
    if not combos:
        return None, ('Este produto não tem atributos com stock por variação. '
                      'Marca um atributo de escolha como "variante" no tipo do produto.')

    entrada = dados.get('variantes')
    if not isinstance(entrada, list):
        return None, 'variantes deve ser uma lista.'

    valores = {}
    for linha in entrada:
        if not isinstance(linha, dict):
            return None, 'Linha inválida.'
        chave = linha.get('chave') or (chave_de(linha['combinacao']) if isinstance(linha.get('combinacao'), dict) else None)
        if chave not in combos:
            return None, f'Combinação desconhecida: {chave}'
        nome = ' · '.join(combos[chave].values())
        try:
            qtd = int(linha.get('quantidade', 0))
        except (TypeError, ValueError):
            qtd = -1
        if qtd < 0:
            return None, f'Quantidade inválida em {nome}.'
        preco, erro_preco = _preco(linha.get('preco'))
        if erro_preco:
            return None, f'{erro_preco} ({nome})'
        valores[chave] = {'quantidade': qtd, 'preco': preco, 'sku': str(linha.get('sku') or '').strip()[:100]}

    produto.stock_por_variante = True
    produto.save(update_fields=['stock_por_variante'])
    for v in sincronizar_variantes(produto):
        if v.chave in valores:
            d = valores[v.chave]
            v.quantidade, v.preco, v.sku = d['quantidade'], d['preco'], d['sku']
            v.save(update_fields=['quantidade', 'preco', 'sku', 'data_atualizacao'])
    atualizar_total_inventario(produto)
    produto.refresh_from_db()
    return grelha_variantes(produto), None


def aplicar_grelha_do_pedido(produto, dados):
    """
    Grelha enviada junto com o formulário do produto (criar/editar), num só pedido:
      stock_por_variante: "true"/"false"   (ausente → não mexe)
      variantes:          JSON [{ chave, quantidade, preco?, sku? }]
    Chamar depois de gravar o produto (tipo e atributos já actualizados), dentro
    da mesma transação. Devolve mensagem de erro (→ fazer rollback) ou None.
    """
    flag = dados.get('stock_por_variante')
    if flag is None or flag == '':
        return None
    ativo = flag if isinstance(flag, bool) else str(flag).lower() in ('true', '1')

    if not ativo:
        if produto.stock_por_variante:
            guardar_grelha(produto, {'stock_por_variante': False})
        return None

    raw = dados.get('variantes') or '[]'
    try:
        linhas = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return 'variantes: JSON inválido.'
    _, erro = guardar_grelha(produto, {'variantes': linhas})
    return erro
