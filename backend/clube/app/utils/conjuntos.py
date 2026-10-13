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

from ..models import Produto, Inventario, VarianteProduto, ComponenteConjunto, GrupoEscolha, OpcaoEscolha
from .variantes import atualizar_total_inventario

MAX_COMPONENTES = 20
MAX_QUANTIDADE = 99


# ── Leitura ────────────────────────────────────────────────────

def _e_pos(produto):
    return produto.__class__.__name__ == 'ProdutoPOS'


class Comp:
    """
    Componente normalizado (loja ou POS) — o resto do módulo só lida com isto.
    Fixo (sempre vem no conjunto) ou opção escolhida pelo cliente (grupo, extra, opcao_id).
    """
    __slots__ = ('id', 'origem', 'produto', 'variante', 'quantidade', 'grupo', 'extra', 'opcao_id')

    def __init__(self, id, origem, produto, variante, quantidade, grupo=None, extra=0, opcao_id=None):
        self.id, self.origem, self.produto = id, origem, produto
        self.variante, self.quantidade = variante, quantidade
        self.grupo, self.extra, self.opcao_id = grupo, extra, opcao_id

    @property
    def nome(self):
        return self.produto.nome + (f' ({self.variante.descricao()})' if self.variante else '')


def componentes_de(conjunto):
    """Componentes fixos (Comp), pela ordem definida pelo dono (usa o prefetch se existir)."""
    out = []
    for c in conjunto.componentes.all():
        if _e_pos(conjunto) and c.produto_pos_id:
            out.append(Comp(c.id, 'pos', c.produto_pos, c.variante_pos, c.quantidade))
        else:
            out.append(Comp(c.id, 'loja', c.produto, c.variante, c.quantidade))
    return out


def _comp_opcao(o, grupo, pos_conjunto):
    if pos_conjunto and o.produto_pos_id:
        return Comp(o.id, 'pos', o.produto_pos, o.variante_pos, o.quantidade, grupo.nome, o.preco_extra, o.id)
    return Comp(o.id, 'loja', o.produto, o.variante, o.quantidade, grupo.nome, o.preco_extra, o.id)


def grupos_de(conjunto):
    """[(grupo, [Comp de cada opção])] — escolhas do cliente, pela ordem do dono."""
    pos_conjunto = _e_pos(conjunto)
    return [(g, [_comp_opcao(o, g, pos_conjunto) for o in g.opcoes.all()]) for g in conjunto.grupos.all()]


def normalizar_escolhas(escolhas):
    """{"<grupo_id>": [opcao_id, ...]} com chaves texto e listas ordenadas sem repetidos."""
    if not isinstance(escolhas, dict):
        return {}
    out = {}
    for k, v in escolhas.items():
        ids = v if isinstance(v, list) else [v]
        ids = sorted({i for i in (_int(x) for x in ids) if i})
        if ids and _int(k):
            out[str(_int(k))] = ids
    return out


def validar_escolhas(conjunto, escolhas, pos=None):
    """
    Confere as escolhas do cliente com os grupos do conjunto.
    Devolve ([Comp das opções escolhidas], erro).
    """
    escolhas = normalizar_escolhas(escolhas)
    grupos = grupos_de(conjunto)
    ids_grupos = {str(g.id) for g, _ in grupos}
    if set(escolhas) - ids_grupos:
        return None, 'As opções escolhidas já não existem neste menu — volta a escolher.'
    out = []
    for g, opcoes in grupos:
        pedidas = escolhas.get(str(g.id), [])
        if len(pedidas) < g.minimo:
            falta = 'uma opção' if g.minimo == 1 else f'{g.minimo} opções'
            return None, f'Escolhe {falta} em "{g.nome}".'
        if len(pedidas) > g.maximo:
            return None, f'Em "{g.nome}" só podes escolher {g.maximo}.'
        por_id = {c.opcao_id: c for c in opcoes}
        for oid in pedidas:
            c = por_id.get(oid)
            if c is None:
                return None, f'Uma opção de "{g.nome}" já não existe — volta a escolher.'
            motivo = _problema(c, pos)
            if motivo:
                return None, f'"{c.nome}" não está disponível em "{g.nome}": {motivo}.'
            out.append(c)
    return out, None


def preco_com_escolhas(conjunto, escolhas):
    """Preço do conjunto + extras das opções escolhidas (opções inválidas não contam)."""
    escolhas = normalizar_escolhas(escolhas)
    total = conjunto.preco
    for g, opcoes in grupos_de(conjunto):
        pedidas = set(escolhas.get(str(g.id), []))
        total += sum((c.extra for c in opcoes if c.opcao_id in pedidas), 0)
    return total


def texto_escolhas(conjunto, escolhas):
    """"Bebida: Fanta (33cl) +0,50 € · Extras: Queijo" — para o carrinho."""
    escolhas = normalizar_escolhas(escolhas)
    partes = []
    for g, opcoes in grupos_de(conjunto):
        pedidas = set(escolhas.get(str(g.id), []))
        nomes = [c.nome + (f' +{c.extra:.2f} €'.replace('.', ',') if c.extra else '')
                 for c in opcoes if c.opcao_id in pedidas]
        if nomes:
            partes.append(f'{g.nome}: {", ".join(nomes)}')
    return ' · '.join(partes)


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
    grupos = grupos_de(conjunto)
    if not comps and not grupos:
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
    # escolhas obrigatórias: tem de haver opções vendáveis suficientes. A quantidade é uma
    # estimativa (cada cliente escolhe opções diferentes); a venda valida o stock exacto.
    for g, opcoes in grupos:
        if g.minimo == 0:
            continue
        boas = [c for c in opcoes if _problema(c, pos) is None]
        stocks = [_stock_comp(c) for c in boas]
        com_stock = [s for s, c in zip(stocks, boas) if s is None or s >= c.quantidade]
        if len(com_stock) < g.minimo:
            motivo = (f'não há opções disponíveis em "{g.nome}"' if not boas
                      else f'as opções de "{g.nome}" estão esgotadas')
            return {'disponivel': False, 'quantidade': 0, 'motivo': motivo if not boas else None,
                    'componente_id': None}
        if any(s is None for s in com_stock):
            continue
        cabe = sum(max(s, 0) // c.quantidade for s, c in zip(stocks, boas) if s is not None) // g.minimo
        maximo = cabe if maximo is None else min(maximo, cabe)
    return {'disponivel': maximo is None or maximo > 0, 'quantidade': maximo, 'motivo': None, 'componente_id': None}


def opcao_disponivel(comp, pos=None):
    """Para mostrar ao cliente: a opção pode ser escolhida agora?"""
    if _problema(comp, pos):
        return False
    s = _stock_comp(comp)
    return s is None or s >= comp.quantidade


def _preco_separado(c):
    return (c.variante.preco_efetivo if c.variante is not None else c.produto.preco) * c.quantidade


def preco_componentes(conjunto):
    """
    Quanto custaria em separado (para mostrar a poupança): componentes fixos + as opções mais
    baratas de cada escolha obrigatória — comparável com o preço base do conjunto.
    """
    total = sum((_preco_separado(c) for c in componentes_de(conjunto)), 0)
    for g, opcoes in grupos_de(conjunto):
        if g.minimo:
            total += sum(sorted(_preco_separado(c) for c in opcoes)[:g.minimo])
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


def bloquear(conjunto, pos=None, escolhas=None):
    """
    Valida e bloqueia o stock dos componentes de um conjunto que se vai vender — os fixos e
    as opções que o cliente escolheu. Devolve (linhas, erro).
    linhas: [{'comp', 'chave', 'linha', 'por_unidade'}]
    """
    comps = componentes_de(conjunto)
    escolhidas, erro = validar_escolhas(conjunto, escolhas or {}, pos)
    if erro:
        return None, erro
    comps += escolhidas
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
    """O que o conjunto levava — guardado no item da encomenda/conta (com as escolhas)."""
    out = []
    for l in linhas:
        c = l['comp']
        s = {
            'origem': c.origem,
            'produto_id': c.produto.id,
            'variante_id': c.variante.id if c.variante is not None else None,
            'nome': c.nome,
            'quantidade': l['por_unidade'],
        }
        if c.grupo:
            s['grupo'] = c.grupo
            s['extra'] = str(c.extra)
        out.append(s)
    return out


def reservar(conjunto, quantidade, pos=None, escolhas=None):
    """
    Venda isolada de um conjunto (POS): valida, desconta e devolve (snapshot, erro).
    O mesmo stock pode vir duas vezes (fixo e escolhido) — soma-se antes de comparar.
    Tudo-ou-nada: chamar dentro de transaction.atomic.
    """
    linhas, erro = bloquear(conjunto, pos, escolhas)
    if erro:
        return None, erro
    pedido = {}
    for l in linhas:
        if l['chave'] is None:
            continue
        ja = pedido.get(l['chave'], 0)
        pedido[l['chave']] = ja + l['por_unidade'] * quantidade
        disponivel = stock_da_linha(l['linha'])
        if pedido[l['chave']] > disponivel:
            return None, msg_sem_stock(conjunto, l['comp'], max(disponivel - ja, 0) // l['por_unidade'])
    for chave, total in pedido.items():
        descontar_chave(chave, total)
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


def validar_linhas(linhas, conjunto, resolver, vazio_ok=False):
    """
    Valida a lista enviada pelo dono e devolve ([(produto, variante, quantidade, origem)], erro).
    resolver(origem, produto_id, variante_id) → (produto, variante, erro) — define que produtos
    são permitidos (mesma loja / mesmo POS / loja ligada ao POS).
    """
    if not linhas:
        # sem produtos fixos só se o conjunto tiver escolhas (ex.: "escolhe 2 bebidas")
        return ([], None) if vazio_ok else (None, 'Um conjunto precisa de pelo menos um produto.')
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
    from ..pos.models import ComponenteConjuntoPOS, OpcaoEscolhaPOS
    if _e_pos(produto):
        qs = ComponenteConjuntoPOS.objects.filter(produto_pos=produto)
        nomes = {c.conjunto.nome for c in qs.select_related('conjunto')}
        nomes |= {o.grupo.conjunto.nome for o in OpcaoEscolhaPOS.objects.filter(produto_pos=produto).select_related('grupo__conjunto')}
        return sorted(nomes)
    nomes = {c.conjunto.nome for c in ComponenteConjunto.objects.filter(produto=produto).select_related('conjunto')}
    nomes |= {c.conjunto.nome for c in ComponenteConjuntoPOS.objects.filter(produto=produto).select_related('conjunto')}
    nomes |= {o.grupo.conjunto.nome for o in OpcaoEscolha.objects.filter(produto=produto).select_related('grupo__conjunto')}
    nomes |= {o.grupo.conjunto.nome for o in OpcaoEscolhaPOS.objects.filter(produto=produto).select_related('grupo__conjunto')}
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


def aviso_desactivar(produto, dados, query):
    """
    O pedido desactiva (ativo=false) um produto que está dentro de conjuntos, sem confirmar?
    Devolve o corpo da resposta 409 (o frontend pergunta e repete com ?confirmar=1) ou None.
    """
    if 'ativo' not in dados or not produto.ativo:
        return None
    if str(dados.get('ativo')).lower() not in ('false', '0', 'off', 'nao', 'não'):
        return None
    if query.get('confirmar') == '1':
        return None
    usado = conjuntos_que_usam(produto)
    if not usado:
        return None
    return {
        'detail': f'"{produto.nome}" faz parte de {", ".join(usado)}. '
                  f'Se o desactivares, esses conjuntos ficam indisponíveis até o retirares deles.',
        'conjuntos': usado,
        'precisa_confirmar': True,
    }


# ── Escolhas do cliente (grupos de opções) ────────────────────────

MAX_GRUPOS = 10
MAX_OPCOES = 30


def ler_grupos(dados):
    """Campo 'grupos' (JSON) do formulário — lista de dicts; None se não veio."""
    import json
    bruto = dados.get('grupos') if hasattr(dados, 'get') else None
    if bruto is None:
        return None, None
    if isinstance(bruto, str):
        try:
            bruto = json.loads(bruto or '[]')
        except (TypeError, ValueError):
            return None, 'Lista de escolhas inválida.'
    if not isinstance(bruto, list):
        return None, 'Lista de escolhas inválida.'
    return bruto, None


def _decimal(v):
    from decimal import Decimal, InvalidOperation
    try:
        d = Decimal(str(v if v not in (None, '') else 0)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None
    return d if d >= 0 else None


def validar_grupos(grupos, conjunto, resolver):
    """
    Valida as escolhas enviadas pelo dono. Devolve ([{id, nome, minimo, maximo, opcoes}], erro),
    opcoes = [{id, produto, variante, quantidade, extra, origem}].
    """
    if len(grupos) > MAX_GRUPOS:
        return None, f'Um conjunto pode ter no máximo {MAX_GRUPOS} escolhas.'
    out = []
    for g in grupos:
        if not isinstance(g, dict):
            return None, 'Lista de escolhas inválida.'
        nome = str(g.get('nome') or '').strip()[:60]
        if not nome:
            return None, 'Dá um nome a cada escolha (ex.: "Bebida").'
        minimo, maximo = _int(g.get('minimo')), _int(g.get('maximo'))
        if minimo is None or maximo is None or minimo < 0 or maximo < 1 or minimo > maximo:
            return None, f'Em "{nome}", o mínimo e o máximo de opções não fazem sentido.'
        opcoes = g.get('opcoes') or []
        if not isinstance(opcoes, list) or not opcoes:
            return None, f'Adiciona opções a "{nome}".'
        if len(opcoes) > MAX_OPCOES:
            return None, f'"{nome}" pode ter no máximo {MAX_OPCOES} opções.'
        if maximo > len(opcoes):
            return None, f'Em "{nome}" o cliente não pode escolher {maximo} — só há {len(opcoes)} opções.'
        linhas, erro = validar_linhas(opcoes, conjunto, resolver)
        if erro:
            return None, f'{nome}: {erro}'
        extras = []
        for o in opcoes:
            e = _decimal(o.get('preco_extra'))
            if e is None or e > 9999:
                return None, f'Em "{nome}", o custo extra de cada opção tem de ser 0 ou mais.'
            extras.append(e)
        out.append({
            'id': _int(g.get('id')), 'nome': nome, 'minimo': minimo, 'maximo': maximo,
            'opcoes': [{'id': _int(o.get('id')), 'produto': p, 'variante': v, 'quantidade': q,
                        'extra': e, 'origem': origem}
                       for o, (p, v, q, origem), e in zip(opcoes, linhas, extras)],
        })
    return out, None


def guardar_grupos(conjunto, grupos_validos):
    """
    Grava as escolhas mantendo os ids das que já existiam (o carrinho guarda escolhas por id:
    editar o preço de uma opção não estraga os carrinhos). O que sai da lista é apagado.
    """
    from ..pos.models import GrupoEscolhaPOS, OpcaoEscolhaPOS
    e_pos = _e_pos(conjunto)
    MG, MO = (GrupoEscolhaPOS, OpcaoEscolhaPOS) if e_pos else (GrupoEscolha, OpcaoEscolha)
    existentes = {g.id: g for g in MG.objects.filter(conjunto=conjunto)}
    manter = set()
    for i, g in enumerate(grupos_validos):
        grupo = existentes.get(g['id']) or MG(conjunto=conjunto)
        grupo.nome, grupo.minimo, grupo.maximo, grupo.ordem = g['nome'], g['minimo'], g['maximo'], i
        grupo.save()
        manter.add(grupo.id)
        opc_exist = {o.id: o for o in MO.objects.filter(grupo=grupo)}
        manter_o = set()
        for j, o in enumerate(g['opcoes']):
            op = opc_exist.get(o['id']) or MO(grupo=grupo)
            op.quantidade, op.preco_extra, op.ordem = o['quantidade'], o['extra'], j
            if e_pos and o['origem'] == 'pos':
                op.produto_pos, op.variante_pos, op.produto, op.variante = o['produto'], o['variante'], None, None
            elif e_pos:
                op.produto, op.variante, op.produto_pos, op.variante_pos = o['produto'], o['variante'], None, None
            else:
                op.produto, op.variante = o['produto'], o['variante']
            op.save()
            manter_o.add(op.id)
        MO.objects.filter(grupo=grupo).exclude(id__in=manter_o).delete()
    MG.objects.filter(conjunto=conjunto).exclude(id__in=manter).delete()


def _imagem(c, request=None):
    p = c.produto
    if c.origem == 'pos':
        imagem = p.imagem.url if p.imagem else None
    else:
        f = getattr(p, 'ficheiro_poster', None) or None
        imagem = f.url if f else (p.ficheiro.url if p.ficheiro and not str(p.ficheiro.name).lower().endswith(
            ('.mp4', '.webm', '.mov', '.mkv')) else None)
    if imagem and request is not None and imagem.startswith('/'):
        imagem = request.build_absolute_uri(imagem)
    return imagem


def grupos_payload(conjunto, request=None, pos=None):
    out = []
    for g, opcoes in grupos_de(conjunto):
        out.append({
            'id': g.id, 'nome': g.nome, 'minimo': g.minimo, 'maximo': g.maximo,
            'opcoes': [{
                'id': c.opcao_id,
                'origem': c.origem,
                'produto_id': c.produto.id,
                'variante_id': c.variante.id if c.variante is not None else None,
                'nome': c.produto.nome,
                'variante': c.variante.descricao() if c.variante is not None else '',
                'quantidade': c.quantidade,
                'preco': str(c.variante.preco_efetivo if c.variante is not None else c.produto.preco),
                'preco_extra': str(c.extra),
                'imagem': _imagem(c, request),
                'disponivel': opcao_disponivel(c, pos),
                'problema': _problema(c, pos),
            } for c in opcoes],
        })
    return out


def aplicar_formulario(conjunto, dados, resolver):
    """
    Grava os produtos fixos ('componentes') e as escolhas ('grupos') enviados no formulário de
    um conjunto já marcado como tal. Devolve a mensagem de erro ou None (quem chama faz rollback).
    Um conjunto precisa de produtos fixos, de escolhas, ou dos dois.
    """
    linhas, erro = ler_componentes(dados)
    if erro:
        return erro
    grupos, erro = ler_grupos(dados)
    if erro:
        return erro
    vai_ter_grupos = bool(grupos) if grupos is not None else conjunto.grupos.exists()
    vai_ter_fixos = bool(linhas) if linhas is not None else conjunto.componentes.exists()
    if not vai_ter_grupos and not vai_ter_fixos:
        return 'Adiciona produtos ou escolhas ao conjunto.'
    if linhas is not None:
        validas, erro = validar_linhas(linhas, conjunto, resolver, vazio_ok=vai_ter_grupos)
        if erro:
            return erro
        (guardar_componentes_pos if _e_pos(conjunto) else guardar_componentes_loja)(conjunto, validas)
    if grupos is not None:
        validos, erro = validar_grupos(grupos, conjunto, resolver)
        if erro:
            return erro
        guardar_grupos(conjunto, validos)
    return None


def maximo_com_escolhas(conjunto, escolhas, pos=None):
    """
    Quantos conjuntos com ESTAS escolhas cabem no stock (o mesmo produto fixo e escolhido soma).
    Devolve (quantidade|None, erro) — None = sem limite.
    """
    escolhidas, erro = validar_escolhas(conjunto, escolhas, pos)
    if erro:
        return 0, erro
    comps = componentes_de(conjunto) + escolhidas
    for c in comps:
        motivo = _problema(c, pos)
        if motivo:
            return 0, f'"{conjunto.nome}" está indisponível: {motivo}.'
    pedido = {}
    for c in comps:
        s = _stock_comp(c)
        if s is None:
            continue
        k = (c.origem, c.produto.id, c.variante.id if c.variante is not None else None)
        stock, qtd = pedido.get(k, (s, 0))
        pedido[k] = (stock, qtd + c.quantidade)
    if not pedido:
        return None, None
    return min(max(s, 0) // q for s, q in pedido.values()), None
