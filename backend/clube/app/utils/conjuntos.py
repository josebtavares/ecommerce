"""
Conjuntos (menus, packs, cabazes) — produtos feitos de outros produtos.

Um conjunto é um Produto (loja) ou ProdutoPOS com e_conjunto=True e uma lista de componentes
(ComponenteConjunto / ComponenteConjuntoPOS). Não tem stock próprio:
  - disponível = min(stock do componente // quantidade no conjunto) — None se nenhum controla stock
  - vender desconta o stock de cada componente; cancelar repõe-no (a partir do snapshot guardado
    no item, para não depender do que o conjunto tem hoje)

Mesmo módulo para a loja online e para o POS:
  - componentes da loja: Inventario ou VarianteProduto
  - componentes do POS:  ProdutoPOS.stock (se controlar_stock) ou VarianteProdutoPOS
Um componente da loja Bendi num conjunto do POS fica indisponível se a loja for suspensa ou
desligada do POS — o conjunto deixa de se vender até o dono substituir esse componente.
"""
from django.db.models import F

from ..models import Produto, Inventario, VarianteProduto, ComponenteConjunto
from .variantes import atualizar_total_inventario

MAX_COMPONENTES = 20
MAX_QUANTIDADE = 99


# ── Leitura ────────────────────────────────────────────────────

def _e_pos(produto):
    return produto.__class__.__name__ == 'ProdutoPOS'


class Comp:
    """Componente normalizado (loja ou POS) — o resto do módulo só lida com isto."""
    __slots__ = ('id', 'origem', 'produto', 'variante', 'quantidade')

    def __init__(self, id, origem, produto, variante, quantidade):
        self.id, self.origem, self.produto = id, origem, produto
        self.variante, self.quantidade = variante, quantidade

    @property
    def nome(self):
        return self.produto.nome + (f' ({self.variante.descricao()})' if self.variante else '')


def componentes_de(conjunto):
    """Lista de Comp, pela ordem definida pelo dono (usa o prefetch se existir)."""
    out = []
    for c in conjunto.componentes.all():
        if _e_pos(conjunto) and c.produto_pos_id:
            out.append(Comp(c.id, 'pos', c.produto_pos, c.variante_pos, c.quantidade))
        else:
            out.append(Comp(c.id, 'loja', c.produto, c.variante, c.quantidade))
    return out


def _loja_indisponivel_no_pos(produto_loja, pos):
    """Componente da loja Bendi dentro de um conjunto do POS: a loja ainda serve este POS?"""
    if pos is None:
        return None
    if pos.loja_vinculada_id != produto_loja.loja_id or pos.modo not in ('integrado', 'hibrido'):
        return 'a loja já não está ligada a este POS'
    if produto_loja.loja.estado == 'suspensa':
        return 'a loja foi suspensa pela plataforma'
    return None


def _problema(comp, pos=None):
    """Motivo pelo qual o componente impede a venda do conjunto (None = está bem)."""
    p = comp.produto
    if not p.ativo:
        return f'"{p.nome}" foi desactivado'
    if comp.origem == 'loja':
        motivo = _loja_indisponivel_no_pos(p, pos)
        if motivo:
            return f'"{p.nome}" é da loja Bendi e {motivo}'
    if p.stock_por_variante:
        if comp.variante is None:
            return f'falta escolher a variação de "{p.nome}"'
        if not comp.variante.ativo:
            return f'a variação {comp.variante.descricao()} de "{p.nome}" já não existe'
    return None


def _stock_comp(comp):
    """Stock actual do componente; None = não controla stock."""
    p = comp.produto
    if comp.variante is not None and p.stock_por_variante:
        return comp.variante.quantidade
    if comp.origem == 'pos':
        return p.stock if p.controlar_stock else None
    try:
        return p.inventario.quantidade
    except Inventario.DoesNotExist:
        return None


def disponibilidade(conjunto, pos=None):
    """
    {'disponivel': bool, 'quantidade': int|None, 'motivo': str|None, 'componente_id': id|None}
    quantidade = quantos conjuntos se podem vender agora (None = sem limite de stock).
    pos: o POS onde se vende (para os componentes da loja num conjunto do POS).
    """
    comps = componentes_de(conjunto)
    if not comps:
        return {'disponivel': False, 'quantidade': 0, 'motivo': 'o conjunto não tem produtos', 'componente_id': None}
    maximo = None
    for c in comps:
        motivo = _problema(c, pos)
        if motivo:
            return {'disponivel': False, 'quantidade': 0, 'motivo': motivo, 'componente_id': c.id}
        s = _stock_comp(c)
        if s is not None:
            cabe = max(s, 0) // c.quantidade
            maximo = cabe if maximo is None else min(maximo, cabe)
    return {'disponivel': maximo is None or maximo > 0, 'quantidade': maximo, 'motivo': None, 'componente_id': None}


def preco_componentes(conjunto):
    """Soma dos preços dos componentes vendidos em separado (para mostrar a poupança)."""
    total = 0
    for c in componentes_de(conjunto):
        preco = c.variante.preco_efetivo if c.variante is not None else c.produto.preco
        total += preco * c.quantidade
    return total


# ── Venda: bloquear, validar e descontar ─────────────────────────

def _chave_e_lock(comp):
    """
    Bloqueia (select_for_update) a linha de stock do componente.
    Devolve (chave, linha) — chave identifica o stock para somar pedidos de vários itens
    (o mesmo produto pode estar sozinho no carrinho e dentro de um menu); None = sem controlo.
    """
    from ..pos.models import ProdutoPOS, VarianteProdutoPOS
    p = comp.produto
    if comp.variante is not None and p.stock_por_variante:
        if comp.origem == 'pos':
            v = VarianteProdutoPOS.objects.select_for_update().get(pk=comp.variante.pk)
            return ('vp', v.id), v
        v = VarianteProduto.objects.select_for_update().get(pk=comp.variante.pk)
        return ('v', v.id), v
    if comp.origem == 'pos':
        pp = ProdutoPOS.objects.select_for_update().get(pk=p.pk)
        return (('pp', pp.id), pp) if pp.controlar_stock else (None, None)
    inv = Inventario.objects.select_for_update().filter(produto_id=p.pk).first()
    return (('i', inv.id), inv) if inv else (None, None)


def stock_da_linha(linha):
    return linha.stock if hasattr(linha, 'controlar_stock') else linha.quantidade


def bloquear(conjunto, pos=None):
    """
    Valida e bloqueia o stock dos componentes de um conjunto que se vai vender.
    Devolve (linhas, erro). linhas: [{'comp', 'chave', 'linha', 'por_unidade'}]
    """
    comps = componentes_de(conjunto)
    if not comps:
        return None, f'"{conjunto.nome}" não tem produtos — não pode ser vendido.'
    linhas = []
    for c in comps:
        motivo = _problema(c, pos)
        if motivo:
            return None, f'"{conjunto.nome}" está indisponível: {motivo}.'
        chave, linha = _chave_e_lock(c)
        linhas.append({'comp': c, 'chave': chave, 'linha': linha, 'por_unidade': c.quantidade})
    return linhas, None


def msg_sem_stock(conjunto, comp, disponivel):
    if disponivel <= 0:
        return f'"{conjunto.nome}" está esgotado: não há "{comp.nome}".'
    return f'Stock insuficiente para "{conjunto.nome}": "{comp.nome}" só tem {disponivel}.'


def descontar_chave(chave, quantidade):
    """Desconta `quantidade` do stock identificado pela chave (F() — sem perder outras escritas)."""
    from ..pos.models import ProdutoPOS, VarianteProdutoPOS
    tipo, pk = chave
    if tipo == 'v':
        VarianteProduto.objects.filter(pk=pk).update(quantidade=F('quantidade') - quantidade)
        atualizar_total_inventario(Produto.objects.get(variantes__pk=pk))
    elif tipo == 'i':
        Inventario.objects.filter(pk=pk).update(quantidade=F('quantidade') - quantidade)
    elif tipo == 'vp':
        VarianteProdutoPOS.objects.filter(pk=pk).update(quantidade=F('quantidade') - quantidade)
        atualizar_total_inventario(ProdutoPOS.objects.get(variantes__pk=pk))
    elif tipo == 'pp':
        ProdutoPOS.objects.filter(pk=pk).update(stock=F('stock') - quantidade)


def snapshot(linhas):
    """O que o conjunto levava — guardado no item da encomenda/conta."""
    return [{
        'origem': l['comp'].origem,
        'produto_id': l['comp'].produto.id,
        'variante_id': l['comp'].variante.id if l['comp'].variante is not None else None,
        'nome': l['comp'].nome,
        'quantidade': l['por_unidade'],
    } for l in linhas]


def reservar(conjunto, quantidade, pos=None):
    """
    Venda isolada de um conjunto (POS): valida, desconta e devolve (snapshot, erro).
    Tudo-ou-nada: chamar dentro de transaction.atomic.
    """
    linhas, erro = bloquear(conjunto, pos)
    if erro:
        return None, erro
    for l in linhas:
        if l['chave'] is None:
            continue
        precisa = l['por_unidade'] * quantidade
        disponivel = stock_da_linha(l['linha'])
        if precisa > disponivel:
            return None, msg_sem_stock(conjunto, l['comp'], disponivel // l['por_unidade'])
    for l in linhas:
        if l['chave'] is not None:
            descontar_chave(l['chave'], l['por_unidade'] * quantidade)
    return snapshot(linhas), None


def repor(componentes, quantidade):
    """Devolve ao stock o que um item de conjunto tinha descontado (a partir do snapshot)."""
    from ..pos.models import ProdutoPOS, VarianteProdutoPOS
    for c in componentes or []:
        q = int(c.get('quantidade') or 0) * quantidade
        if q <= 0:
            continue
        if c.get('origem') == 'pos':
            if c.get('variante_id'):
                VarianteProdutoPOS.objects.filter(pk=c['variante_id']).update(quantidade=F('quantidade') + q)
                pp = ProdutoPOS.objects.filter(variantes__pk=c['variante_id']).first()
                if pp:
                    atualizar_total_inventario(pp)
            else:
                ProdutoPOS.objects.filter(pk=c['produto_id'], controlar_stock=True).update(stock=F('stock') + q)
        else:
            if c.get('variante_id'):
                VarianteProduto.objects.filter(pk=c['variante_id']).update(quantidade=F('quantidade') + q)
                p = Produto.objects.filter(variantes__pk=c['variante_id']).first()
                if p:
                    atualizar_total_inventario(p)
            else:
                Inventario.objects.filter(produto_id=c['produto_id']).update(quantidade=F('quantidade') + q)


# ── Guardar os componentes (backoffice da loja / POS) ─────────────

def ler_componentes(dados):
    """Lê o campo 'componentes' (JSON) do pedido — lista de dicts; None se não veio."""
    import json
    bruto = dados.get('componentes') if hasattr(dados, 'get') else None
    if bruto is None:
        return None, None
    if isinstance(bruto, str):
        try:
            bruto = json.loads(bruto or '[]')
        except (TypeError, ValueError):
            return None, 'Lista de produtos do conjunto inválida.'
    if not isinstance(bruto, list):
        return None, 'Lista de produtos do conjunto inválida.'
    return bruto, None


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def validar_linhas(linhas, conjunto, resolver):
    """
    Valida a lista enviada pelo dono e devolve ([(produto, variante, quantidade, origem)], erro).
    resolver(origem, produto_id, variante_id) → (produto, variante, erro) — define que produtos
    são permitidos (mesma loja / mesmo POS / loja ligada ao POS).
    """
    if not linhas:
        return None, 'Um conjunto precisa de pelo menos um produto.'
    if len(linhas) > MAX_COMPONENTES:
        return None, f'Um conjunto pode ter no máximo {MAX_COMPONENTES} produtos.'
    vistos, out = set(), []
    for l in linhas:
        if not isinstance(l, dict):
            return None, 'Lista de produtos do conjunto inválida.'
        origem = l.get('origem') or 'loja'
        pid, vid = _int(l.get('produto_id')), _int(l.get('variante_id'))
        qtd = 1 if l.get('quantidade') in (None, '') else _int(l.get('quantidade'))
        if not pid:
            return None, 'Produto do conjunto inválido.'
        if qtd is None or not 1 <= qtd <= MAX_QUANTIDADE:
            return None, f'A quantidade de cada produto tem de estar entre 1 e {MAX_QUANTIDADE}.'
        produto, variante, erro = resolver(origem, pid, vid)
        if erro:
            return None, erro
        if conjunto is not None and _e_pos(produto) == _e_pos(conjunto) and produto.pk == conjunto.pk:
            return None, 'Um conjunto não se pode conter a si próprio.'
        if produto.e_conjunto:
            return None, f'"{produto.nome}" já é um conjunto — não se pode pôr um conjunto dentro de outro.'
        if produto.stock_por_variante:
            if variante is None:
                return None, f'Escolhe a variação de "{produto.nome}" que entra no conjunto.'
            if not variante.ativo:
                return None, f'A variação escolhida de "{produto.nome}" já não existe.'
        else:
            variante = None
        chave = (origem, produto.pk, variante.pk if variante else None)
        if chave in vistos:
            return None, f'"{produto.nome}" aparece repetido — aumenta a quantidade em vez de o repetir.'
        vistos.add(chave)
        out.append((produto, variante, qtd, origem))
    return out, None


def resolver_loja(loja):
    """Componentes de um conjunto da loja: produtos activos ou inactivos da MESMA loja."""
    def _r(origem, pid, vid):
        if origem != 'loja':
            return None, None, 'Um conjunto da loja só pode ter produtos da própria loja.'
        p = Produto.objects.filter(pk=pid, loja=loja).first()
        if not p:
            return None, None, 'Produto do conjunto não encontrado nesta loja.'
        v = VarianteProduto.objects.filter(pk=vid, produto=p).first() if vid else None
        if vid and not v:
            return None, None, f'Variação de "{p.nome}" não encontrada.'
        return p, v, None
    return _r


def guardar_componentes_loja(conjunto, linhas_validas):
    ComponenteConjunto.objects.filter(conjunto=conjunto).delete()
    ComponenteConjunto.objects.bulk_create([
        ComponenteConjunto(conjunto=conjunto, produto=p, variante=v, quantidade=q, ordem=i)
        for i, (p, v, q, _) in enumerate(linhas_validas)
    ])


def conjuntos_que_usam(produto):
    """Nomes dos conjuntos (loja e POS) que têm este produto — para avisar antes de o retirar."""
    from ..pos.models import ComponenteConjuntoPOS
    if _e_pos(produto):
        qs = ComponenteConjuntoPOS.objects.filter(produto_pos=produto)
        return sorted({c.conjunto.nome for c in qs.select_related('conjunto')})
    nomes = {c.conjunto.nome for c in ComponenteConjunto.objects.filter(produto=produto).select_related('conjunto')}
    nomes |= {c.conjunto.nome for c in ComponenteConjuntoPOS.objects.filter(produto=produto).select_related('conjunto')}
    return sorted(nomes)


# ── Payload (montra / backoffice / POS) ───────────────────────────

def componentes_payload(conjunto, request=None, pos=None):
    out = []
    for c in componentes_de(conjunto):
        p = c.produto
        if c.origem == 'pos':
            imagem = p.imagem.url if p.imagem else None
        else:
            f = getattr(p, 'ficheiro_poster', None) or None
            imagem = f.url if f else (p.ficheiro.url if p.ficheiro and not str(p.ficheiro.name).lower().endswith(
                ('.mp4', '.webm', '.mov', '.mkv')) else None)
        if imagem and request is not None and imagem.startswith('/'):
            imagem = request.build_absolute_uri(imagem)
        out.append({
            'id': c.id,
            'origem': c.origem,
            'produto_id': p.id,
            'variante_id': c.variante.id if c.variante is not None else None,
            'nome': p.nome,
            'variante': c.variante.descricao() if c.variante is not None else '',
            'quantidade': c.quantidade,
            'preco': str(c.variante.preco_efetivo if c.variante is not None else p.preco),
            'imagem': imagem,
            'problema': _problema(c, pos),
        })
    return out


# ── POS ───────────────────────────────────────────────────────────

def resolver_pos(pos):
    """
    Componentes de um conjunto do POS: produtos do próprio POS e, num POS híbrido com a loja
    ligada e activa, produtos dessa loja Bendi.
    """
    from ..pos.models import ProdutoPOS, VarianteProdutoPOS

    def _r(origem, pid, vid):
        if origem == 'pos':
            p = ProdutoPOS.objects.filter(pk=pid, pos=pos).first()
            if not p:
                return None, None, 'Produto do conjunto não encontrado neste POS.'
            v = VarianteProdutoPOS.objects.filter(pk=vid, produto=p).first() if vid else None
            if vid and not v:
                return None, None, f'Variação de "{p.nome}" não encontrada.'
            return p, v, None
        if origem == 'loja':
            if pos.modo != 'hibrido' or not pos.loja_vinculada_id:
                return None, None, 'Só um POS híbrido pode juntar produtos da loja Bendi num conjunto.'
            if pos.loja_vinculada.estado == 'suspensa':
                return None, None, 'A loja Bendi ligada está suspensa — os produtos dela não podem entrar em conjuntos.'
            return resolver_loja(pos.loja_vinculada)('loja', pid, vid)
        return None, None, 'Origem inválida para um produto do conjunto.'
    return _r


def guardar_componentes_pos(conjunto, linhas_validas):
    from ..pos.models import ComponenteConjuntoPOS
    ComponenteConjuntoPOS.objects.filter(conjunto=conjunto).delete()
    objs = []
    for i, (p, v, q, origem) in enumerate(linhas_validas):
        if origem == 'pos':
            objs.append(ComponenteConjuntoPOS(conjunto=conjunto, produto_pos=p, variante_pos=v, quantidade=q, ordem=i))
        else:
            objs.append(ComponenteConjuntoPOS(conjunto=conjunto, produto=p, variante=v, quantidade=q, ordem=i))
    ComponenteConjuntoPOS.objects.bulk_create(objs)
