"""
Catálogo público de uma loja: filtros que se adaptam aos produtos que a loja tem de facto.

- facetas(qs)          → atributos/valores (com contagens) dos produtos do queryset, para montar os campos
- filtrar_atributos()  → atributo_<nome>=<valor> exacto (texto ou lista), ciente das variações:
                         num produto com stock por variação, "cor=Preto + tamanho=M" só casa se essa
                         combinação existir (e, com em_stock, se tiver stock)
- filtrar_stock()      → "Em stock" a sério (inventário, variações e conjuntos)
- ordenar()            → preço/novidade/nome, com desempate estável para a paginação
"""
import re
import unicodedata

from django.db.models import BooleanField, Exists, OuterRef, Q
from django.db.models.expressions import RawSQL

MAX_VALORES = 40        # um atributo com mais valores distintos do que isto não vira lista (fica na pesquisa)
MAX_TEXTO = 60          # valores muito longos (descrições num atributo) também não
MAX_PEDIDOS = 12        # nº máximo de atributos filtrados de uma vez
ORDENS = {'preco': ('preco', '-id'), '-preco': ('-preco', '-id'), '-data_criacao': ('-data_criacao', '-id'),
          'data_criacao': ('data_criacao', 'id'), 'nome': ('nome', 'id'), '-nome': ('-nome', '-id')}


def _norm(v):
    return unicodedata.normalize('NFKD', str(v)).encode('ascii', 'ignore').decode().lower().strip()


def _lista(v):
    """Valor de um atributo → lista de textos (aceita texto, número, lista)."""
    if v is None or v == '' or isinstance(v, dict):
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if x not in (None, '') and not isinstance(x, (dict, list))]
    if isinstance(v, bool):
        return ['Sim' if v else 'Não']
    return [str(v).strip()]


def _chave_ordem(v):
    """Ordena tamanhos/números de forma natural: 'XS' < 'S' < … e '38' < '40' < '100'."""
    tamanhos = ['xxs', 'xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl', '3xl', '4xl']
    n = _norm(v)
    if n in tamanhos:
        return (0, tamanhos.index(n), '')
    m = re.match(r'^(\d+(?:[.,]\d+)?)', n)
    if m:
        return (1, float(m.group(1).replace(',', '.')), n)
    return (2, 0, n)


def facetas(qs):
    """
    → [{nome, variante, valores: [{valor, total}]}] pelos produtos de qs.
    Os valores vêm dos produtos (não das opções do tipo): só aparece o que existe na loja.
    Valores iguais com maiúsculas/acentos diferentes juntam-se (fica a grafia mais usada).
    """
    from .variantes import atributos_variante
    linhas = list(qs.select_related('tipo').only('id', 'atributos', 'tipo__atributos_schema', 'tipo__id'))
    total_produtos = len(linhas)
    ordem_schema, opcoes_schema, variante, contagem = [], {}, set(), {}
    for p in linhas:
        if p.tipo:
            for campo in p.tipo.atributos_schema or []:
                nome = campo.get('nome') if isinstance(campo, dict) else campo
                if nome and nome not in ordem_schema:
                    ordem_schema.append(nome)
                if isinstance(campo, dict) and campo.get('opcoes'):
                    opcoes_schema.setdefault(nome, [_norm(o) for o in campo['opcoes']])
            variante.update(atributos_variante(p))
        for nome, v in (p.atributos or {}).items():
            if not isinstance(nome, str) or '__' in nome or not nome.strip():
                continue
            vistos = set()
            for txt in _lista(v):
                k = _norm(txt)
                if not k or len(txt) > MAX_TEXTO or k in vistos:
                    continue
                vistos.add(k)
                g = contagem.setdefault(nome, {}).setdefault(k, {'total': 0, 'grafias': {}})
                g['total'] += 1
                g['grafias'][txt] = g['grafias'].get(txt, 0) + 1

    def posicao(nome):
        return (ordem_schema.index(nome), '') if nome in ordem_schema else (len(ordem_schema), _norm(nome))

    out = []
    for nome in sorted(contagem, key=posicao):
        grupos = contagem[nome]
        if len(grupos) > MAX_VALORES:
            continue
        # um único valor que todos os produtos têm não filtra nada
        if len(grupos) == 1 and next(iter(grupos.values()))['total'] >= total_produtos:
            continue
        opc = opcoes_schema.get(nome) or []

        def chave(k):   # primeiro pela ordem das opções do tipo, depois de forma natural
            return (0, opc.index(k), 0, '') if k in opc else (1, *_chave_ordem(k))
        valores = [{'valor': max(g['grafias'], key=lambda t: (g['grafias'][t], t)), 'total': g['total']}
                   for k, g in sorted(grupos.items(), key=lambda kv: chave(kv[0]))]
        out.append({'nome': nome, 'variante': nome in variante, 'valores': valores})
    return out


def pedidos_atributos(params):
    """atributo_<nome>=<valor> (repetido = "ou") → {nome: [valores]}; ignora nomes estranhos."""
    pedidos = {}
    for param in params.keys():
        if not param.startswith('atributo_'):
            continue
        nome = param[len('atributo_'):]
        if not nome or '__' in nome or len(nome) > 100:
            continue
        valores = [v.strip() for v in params.getlist(param) if v and v.strip()][:20]
        if valores:
            pedidos[nome] = [v[:200] for v in valores]
        if len(pedidos) >= MAX_PEDIDOS:
            break
    return pedidos


def _tem_valor(tabela):
    """SQL: o atributo (texto ou lista) tem algum dos valores pedidos (sem diferenciar maiúsculas)."""
    a = f'"{tabela}"."atributos" -> %s'
    return (f"EXISTS (SELECT 1 FROM jsonb_array_elements_text(CASE jsonb_typeof({a}) WHEN 'array' THEN {a} "
            f"ELSE jsonb_build_array({a}) END) AS e(v) WHERE lower(e.v) = ANY(%s))")


def _variante_casa(pedidos, em_stock):
    """Subquery: variação activa do produto com a combinação pedida (atributos que não são de variação passam)."""
    from ..models import VarianteProduto
    v = VarianteProduto.objects.filter(produto=OuterRef('pk'), ativo=True)
    if em_stock:
        v = v.filter(quantidade__gt=0)
    for nome, valores in pedidos.items():
        casa = Q()
        for val in valores:
            casa |= Q(**{f'combinacao__{nome}__iexact': val})
        v = v.filter(casa | ~Q(combinacao__has_key=nome))
    return Exists(v)


def filtrar_atributos(qs, pedidos, em_stock=False):
    from ..models import Produto
    if not pedidos:
        return qs
    tabela = Produto._meta.db_table
    for i, (nome, valores) in enumerate(pedidos.items()):
        sql = _tem_valor(tabela)
        qs = qs.annotate(**{f'_attr{i}': RawSQL(sql, (nome, nome, nome, [v.lower() for v in valores]),
                                                 output_field=BooleanField())}).filter(**{f'_attr{i}': True})
    # com stock por variação, a combinação tem de existir de facto (ex.: Preto + M)
    return qs.filter(Q(stock_por_variante=False) | _variante_casa(pedidos, em_stock))


def filtrar_stock(qs, pedidos=None):
    """Só o que se pode comprar agora. Conjuntos: pela disponibilidade dos componentes."""
    from ..models import VarianteProduto
    from . import conjuntos as conj
    if pedidos:   # filtrar_atributos(em_stock=True) já exigiu stock na combinação pedida
        com_variacao = Q(stock_por_variante=True)
    else:
        com_variacao = Q(stock_por_variante=True) & Q(Exists(
            VarianteProduto.objects.filter(produto=OuterRef('pk'), ativo=True, quantidade__gt=0)))
    simples = Q(stock_por_variante=False, e_conjunto=False) & (Q(inventario__isnull=True) | Q(inventario__quantidade__gt=0))
    conjuntos = Q(e_conjunto=True)
    qs = qs.filter(com_variacao | simples | conjuntos)
    esgotados = [p.id for p in qs.filter(e_conjunto=True)[:300] if not conj.disponibilidade(p)['disponivel']]
    return qs.exclude(id__in=esgotados) if esgotados else qs


def ordenar(qs, ordering, relevancia=None):
    """ordering conhecido → essa ordem; senão a relevância da pesquisa (se houver) ou os mais novos primeiro."""
    from django.db.models import Case, IntegerField, Value, When
    if ordering in ORDENS:
        return qs.order_by(*ORDENS[ordering])
    if relevancia:
        pos = Case(*[When(id=i, then=Value(n)) for n, i in enumerate(relevancia)],
                   default=Value(len(relevancia)), output_field=IntegerField())
        return qs.annotate(_rel=pos).order_by('_rel', '-id')
    return qs.order_by('-id')
