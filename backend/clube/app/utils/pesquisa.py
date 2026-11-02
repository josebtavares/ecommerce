"""
Barra de pesquisa da home e do cabeçalho (fase 1: sem serviços externos).

  normalizar(texto)            → minúsculas, sem acentos, só letras/números ("Café-Bar" → "cafe bar cafebar")
  indexar_produto/loja/servico(id) → (re)escreve a linha do índice (EntradaPesquisa) e o tsvector
  reindexar_tudo()             → refaz o índice todo (worker, de 6 em 6 horas, e se estiver vazio)
  pesquisar(q, ...)            → resultados agrupados: produtos, lojas, serviços, categorias (+ "querias dizer")

Como encontra:
  · texto em português com raízes (to_tsvector 'portuguese'): "camisas" encontra "camisa";
  · a última palavra é prefixo enquanto se escreve: "sapat" encontra "sapatilhas";
  · sem acentos dos dois lados: "cafe" encontra "Café";
  · erros de escrita no nome (pg_trgm, word_similarity): "camizola" encontra "Camisola";
  · sinónimos PT/BR/Crioulo (SINONIMOS): "celular" encontra "telemóvel".
Ordem: relevância do texto (nome > categoria/loja > descrição) + parecença do nome + começa pelo que se escreveu.
O que está à vista decide-se na pesquisa (produto activo de loja activa, serviço marcável), nunca no índice.
"""
import hashlib
import logging
import re
import unicodedata

from django.core.cache import cache
from django.db import transaction

log = logging.getLogger(__name__)

MAX_Q = 80
CACHE_S = 60
LIMITE_C = 2000          # descrição + atributos: chega para encontrar, não incha o índice
SIM_MINIMA = 0.45        # word_similarity para aceitar um erro de escrita no nome
SIM_SUGESTAO = 0.3
# híbrido (fase 2, utils/semantica.py): Reciprocal Rank Fusion das duas listas
RRF_K = 60
PESO_SEMANTICO = 0.8     # um pouco abaixo das palavras: o que tem a palavra pedida continua à frente
SEM_LIMITE = 60          # candidatos semânticos por tipo
# afinado com voyage-4-lite (2026-11-02): ruído ≤ 0,23 ('xyzq blorf'); relevante 0,29–0,64 ('tenho fome' → pratos 0,29,
# 'cortar o cabelo' → cortes 0,61). Fica o que passa o mínimo E está perto do melhor (corta a cauda de ruído).
SEM_MINIMO = 0.28
SEM_MARGEM = 0.15         # dentro do mesmo tipo
SEM_MARGEM_GLOBAL = 0.25  # face ao melhor de todos os tipos (um tipo fraco não traz ruído)
MAX_HIBRIDO = 300

# grupos de palavras equivalentes (já normalizadas, uma palavra cada)
SINONIMOS = [
    ['telemovel', 'telemoveis', 'celular', 'celulares', 'smartphone', 'smartphones', 'telefone'],
    ['sapatilha', 'sapatilhas', 'tenis', 'sneaker', 'sneakers'],
    ['tshirt', 'tshirts', 'camiseta', 'camisetas', 't-shirt'],
    ['camisola', 'camisolas', 'sweat', 'sweatshirt', 'hoodie', 'moletom', 'sueter'],
    ['casaco', 'casacos', 'jaqueta', 'blusao', 'blazer'],
    ['calcas', 'calca', 'jeans', 'ganga'],
    ['calcado', 'sapato', 'sapatos', 'calcados'],
    ['roupa', 'roupas', 'vestuario'],
    ['mala', 'malas', 'bolsa', 'bolsas'],
    ['frigorifico', 'geladeira'],
    ['portatil', 'laptop', 'notebook', 'computador'],
    ['auscultadores', 'auriculares', 'fones', 'headphones', 'headset'],
    ['ecra', 'tela', 'monitor'],
    ['rato', 'mouse'],
    ['relogio', 'relogios', 'smartwatch'],
    ['sumo', 'sumos', 'suco', 'sucos'],
    ['gelado', 'gelados', 'sorvete', 'sorvetes'],
    ['hamburguer', 'hamburger', 'burger', 'hamburgueres'],
    ['refrigerante', 'refrigerantes', 'refresco', 'refrescos', 'soda'],
    ['cerveja', 'cervejas', 'beer'],
    ['grogue', 'grog', 'aguardente'],
    ['frango', 'galinha'],
    ['comida', 'refeicao', 'refeicoes', 'almoco', 'jantar'],
    ['bolo', 'bolos', 'doce', 'doces', 'sobremesa'],
    ['perfume', 'perfumes', 'fragrancia', 'colonia'],
    ['maquilhagem', 'maquiagem', 'makeup', 'cosmetica', 'cosmeticos'],
    ['barbeiro', 'barbearia', 'barba'],
    ['cabeleireiro', 'cabeleireira', 'salao', 'cabelo'],
    ['unhas', 'manicure', 'pedicure', 'gelinho'],
    ['massagem', 'massagens', 'spa'],
    ['ginasio', 'academia', 'gym', 'fitness'],
    ['bicicleta', 'bicicletas', 'bike'],
    ['oculos', 'lentes'],
    ['fato', 'terno'],
    ['cueca', 'cuecas', 'calcinha', 'boxers'],
]
_SIN = {}
for _g in SINONIMOS:
    _g = [re.sub(r'[^a-z0-9]', '', w) for w in _g]
    for _w in _g:
        _SIN.setdefault(_w, set()).update(x for x in _g if x != _w)


def normalizar(texto, juntar=True):
    """'Café-Bar T-Shirt' → 'cafe bar t shirt cafebar tshirt' (as palavras com hífen também juntas)."""
    t = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode().lower()
    juntas = [re.sub(r'[^a-z0-9]', '', w) for w in re.findall(r'[a-z0-9]+(?:[-/.][a-z0-9]+)+', t)] if juntar else []
    t = re.sub(r'[^a-z0-9]+', ' ', t).strip()
    return ' '.join([t] + juntas) if juntas else t


def _valores(atributos):
    """Valores de um JSON de atributos (texto, números, listas) → texto."""
    if isinstance(atributos, dict):
        return ' '.join(_valores(v) for v in atributos.values())
    if isinstance(atributos, (list, tuple)):
        return ' '.join(_valores(v) for v in atributos)
    if isinstance(atributos, (str, int, float)) and not isinstance(atributos, bool):
        return str(atributos)
    return ''


def _guardar(tipo, objeto_id, loja_id, nome, a, b, c):
    from ..models import EntradaPesquisa
    a, b, c = normalizar(a), normalizar(b), normalizar(c)[:LIMITE_C]
    EntradaPesquisa.objects.update_or_create(
        tipo=tipo, objeto_id=objeto_id,
        defaults={'loja_id': loja_id, 'nome': nome[:200], 'nome_norm': normalizar(nome, juntar=False)[:200],
                  'texto_a': a, 'texto_b': b, 'texto_c': c})
    EntradaPesquisa.objects.filter(tipo=tipo, objeto_id=objeto_id).update(vetor=_vetor())


def _vetor():
    """Português (radicais: camisolas → camisol) + 'simple' (a palavra inteira), para as palavras cujo radical
    fica curto demais e colide com outras (comida e comando → 'com'; ver _consulta)."""
    from django.contrib.postgres.search import SearchVector
    v = None
    for config in ('portuguese', 'simple'):
        for campo, peso in (('texto_a', 'A'), ('texto_b', 'B'), ('texto_c', 'C')):
            x = SearchVector(campo, weight=peso, config=config)
            v = x if v is None else v + x
    return v


def _apagar(tipo, objeto_id):
    from ..models import EntradaPesquisa
    EntradaPesquisa.objects.filter(tipo=tipo, objeto_id=objeto_id).delete()


def _textos_produto(p):
    variantes = ' '.join(_valores(v.combinacao) for v in p.variantes.all())
    b = ' '.join([p.tipo.nome if p.tipo else ''] + [c.nome for c in p.categorias.all()] + [p.loja.nome, p.loja.categoria])
    c = ' '.join([p.descricao or '', _valores(p.atributos), variantes, p.sku or ''])
    return p.nome, b, c


def indexar_produto(produto_id):
    from ..models import Produto
    p = (Produto.objects.select_related('loja', 'tipo').prefetch_related('categorias', 'variantes')
         .filter(pk=produto_id).first())
    if not p:
        return _apagar('produto', produto_id)
    _guardar('produto', p.id, p.loja_id, p.nome, *_textos_produto(p))


def indexar_loja(loja_id, com_conteudo=False):
    """com_conteudo: o nome/categoria da loja mudou — também está no texto dos produtos e serviços dela."""
    from ..models import Loja
    l = Loja.objects.filter(pk=loja_id).first()
    if not l:
        return
    _guardar('loja', l.id, l.id, l.nome, l.nome, f'{l.categoria} {l.localizacao}', l.descricao or '')
    if com_conteudo:
        for pid in l.produtos.values_list('id', flat=True):
            indexar_produto(pid)
        for sid in l.servicos.values_list('id', flat=True):
            indexar_servico(sid)


def indexar_servico(servico_id):
    from ..servicos.models import Servico
    s = Servico.objects.select_related('loja').filter(pk=servico_id).first()
    if not s:
        return _apagar('servico', servico_id)
    inclui = ' '.join(c.servico.nome for c in s.componentes.select_related('servico')) if s.e_pacote else ''
    _guardar('servico', s.id, s.loja_id, s.nome, s.nome, f'{s.categoria} {s.loja.nome} {s.loja.categoria}',
             f'{s.descricao or ""} {inclui}')


def reindexar_tudo():
    """Refaz o índice (apaga o que já não existe). → nº de linhas."""
    from ..models import EntradaPesquisa, Loja, Produto
    from ..servicos.models import Servico
    vistos = {'produto': set(), 'loja': set(), 'servico': set()}
    linhas = []
    for l in Loja.objects.all():
        linhas.append(('loja', l.id, l.id, l.nome, l.nome, f'{l.categoria} {l.localizacao}', l.descricao or ''))
    for p in Produto.objects.select_related('loja', 'tipo').prefetch_related('categorias', 'variantes').iterator(chunk_size=500):
        linhas.append(('produto', p.id, p.loja_id, p.nome, *_textos_produto(p)))
    for s in Servico.objects.select_related('loja').prefetch_related('componentes__servico'):
        inclui = ' '.join(c.servico.nome for c in s.componentes.all()) if s.e_pacote else ''
        linhas.append(('servico', s.id, s.loja_id, s.nome, s.nome, f'{s.categoria} {s.loja.nome} {s.loja.categoria}',
                       f'{s.descricao or ""} {inclui}'))
    objs = []
    for tipo, oid, loja_id, nome, a, b, c in linhas:
        vistos[tipo].add(oid)
        objs.append(EntradaPesquisa(tipo=tipo, objeto_id=oid, loja_id=loja_id, nome=nome[:200],
                                    nome_norm=normalizar(nome, juntar=False)[:200],
                                    texto_a=normalizar(a), texto_b=normalizar(b), texto_c=normalizar(c)[:LIMITE_C]))
    with transaction.atomic():
        EntradaPesquisa.objects.bulk_create(
            objs, batch_size=500, update_conflicts=True, unique_fields=['tipo', 'objeto_id'],
            update_fields=['loja', 'nome', 'nome_norm', 'texto_a', 'texto_b', 'texto_c', 'atualizado_em'])
        for tipo, ids in vistos.items():
            EntradaPesquisa.objects.filter(tipo=tipo).exclude(objeto_id__in=ids).delete()
        EntradaPesquisa.objects.update(vetor=_vetor())
    return len(objs)


# ── manter o índice em dia (sinais) ──────────────────────────────────

def _depois(fn, *args):
    """Depois de a gravação ficar feita; um erro aqui nunca estraga a gravação (o worker refaz tudo de 6 em 6 h)."""
    def correr():
        try:
            fn(*args)
        except Exception:
            log.exception('pesquisa: indexar falhou %s%s', fn.__name__, args)
    transaction.on_commit(correr)


def ligar_sinais():
    from django.db.models.signals import m2m_changed, post_delete, post_save
    from ..models import CategoriaLoja, Loja, Produto, VarianteProduto
    from ..servicos.models import Servico

    def produto(sender, instance, **kw):
        _depois(indexar_produto, instance.pk)

    def produto_apagado(sender, instance, **kw):
        _depois(_apagar, 'produto', instance.pk)

    def categorias(sender, instance, action, **kw):
        if action in ('post_add', 'post_remove', 'post_clear') and isinstance(instance, Produto):
            _depois(indexar_produto, instance.pk)

    def categoria_loja(sender, instance, **kw):
        for pid in instance.produtos.values_list('id', flat=True):
            _depois(indexar_produto, pid)

    def variante(sender, instance, **kw):
        _depois(indexar_produto, instance.produto_id)

    def loja(sender, instance, created=False, update_fields=None, **kw):
        if update_fields and not set(update_fields) & {'nome', 'categoria', 'localizacao', 'descricao'}:
            return
        from ..models import EntradaPesquisa
        antes = EntradaPesquisa.objects.filter(tipo='loja', objeto_id=instance.pk).values_list('texto_a', 'texto_b').first()
        mudou = not antes or antes != (normalizar(instance.nome), normalizar(f'{instance.categoria} {instance.localizacao}'))
        _depois(indexar_loja, instance.pk, bool(antes) and mudou)

    def servico(sender, instance, **kw):
        _depois(indexar_servico, instance.pk)

    def servico_apagado(sender, instance, **kw):
        _depois(_apagar, 'servico', instance.pk)

    post_save.connect(produto, sender=Produto, dispatch_uid='pesquisa_produto')
    post_delete.connect(produto_apagado, sender=Produto, dispatch_uid='pesquisa_produto_del')
    m2m_changed.connect(categorias, sender=Produto.categorias.through, dispatch_uid='pesquisa_categorias')
    post_save.connect(categoria_loja, sender=CategoriaLoja, dispatch_uid='pesquisa_categoria_loja')
    post_save.connect(variante, sender=VarianteProduto, dispatch_uid='pesquisa_variante')
    post_save.connect(loja, sender=Loja, dispatch_uid='pesquisa_loja')
    post_save.connect(servico, sender=Servico, dispatch_uid='pesquisa_servico')
    post_delete.connect(servico_apagado, sender=Servico, dispatch_uid='pesquisa_servico_del')


# ── pesquisar ────────────────────────────────────────────────────────

_RADICAIS = {}


def _radical_curto(palavra):
    """O radical em português tem ≤ 3 letras (ex.: comida → com)? Então procura-se a palavra inteira."""
    r = _RADICAIS.get(palavra)
    if r is None:
        from django.db import connection
        with connection.cursor() as c:
            c.execute("SELECT ts_lexize('portuguese_stem', %s)", [palavra])
            lex = (c.fetchone() or [None])[0] or []
        r = bool(lex) and len(lex[0]) <= 3 and len(palavra) > len(lex[0]) + 1
        if len(_RADICAIS) > 5000:
            _RADICAIS.clear()
        _RADICAIS[palavra] = r
    return r


def _consulta(tokens, juntar='&'):
    """SearchQuery das palavras (e sinónimos); a última é prefixo. Radicais curtos vão pela palavra inteira."""
    from django.contrib.postgres.search import SearchQuery
    grupos = None
    for i, t in enumerate(tokens):
        ultima = i == len(tokens) - 1
        grupo = None
        for a in [t] + sorted(_SIN.get(t, ())):
            termo = f'{a}:*' if (ultima and a == t) else a
            q = SearchQuery(termo, search_type='raw', config='simple' if _radical_curto(a) else 'portuguese')
            grupo = q if grupo is None else grupo | q
        grupos = grupo if grupos is None else (grupos & grupo if juntar == '&' else grupos | grupo)
    return grupos


def _tsquery(tokens, juntar='&'):
    """Só [a-z0-9] chega aqui (sem sintaxe do to_tsquery para partir). A última palavra é prefixo."""
    grupos = []
    for i, t in enumerate(tokens):
        ultima = i == len(tokens) - 1
        alts = [t] + sorted(_SIN.get(t, ()))
        grupos.append('(' + ' | '.join(f'{a}:*' if (ultima and a == t) else a for a in alts) + ')')
    return f' {juntar} '.join(grupos)


def _tokens(qn):
    return [t for t in re.sub(r'[^a-z0-9 ]', ' ', qn).split() if t][:8]


def _visiveis(tipo):
    """Ids à vista agora (cache 60 s): o índice só tem texto."""
    chave = f'pesq:visiveis:{tipo}'
    ids = cache.get(chave)
    if ids is None:
        if tipo == 'produto':
            from ..models import Produto
            ids = set(Produto.objects.filter(ativo=True, loja__ativa=True).values_list('id', flat=True))
        elif tipo == 'loja':
            from ..models import Loja
            ids = set(Loja.objects.filter(ativa=True).values_list('id', flat=True))
        else:
            from ..servicos.cobranca import servicos_publicos
            ids = set(servicos_publicos().values_list('id', flat=True))
        cache.set(chave, ids, CACHE_S)
    return ids


def _base(tipo, qn, tokens, juntar, visiveis=True):
    from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramWordSimilarity
    from django.db.models import Case, F, FloatField, Q, Value, When
    from ..models import EntradaPesquisa
    consulta = _consulta(tokens, juntar)
    qs = EntradaPesquisa.objects.filter(tipo=tipo)
    if visiveis:
        qs = qs.filter(objeto_id__in=_visiveis(tipo))
    qs = qs.annotate(
        rel=SearchRank(F('vetor'), consulta, weights=[0.1, 0.25, 0.5, 1.0], normalization=32),
        sim=TrigramWordSimilarity(Value(qn), 'nome_norm'),
        comeca=Case(When(nome_norm__startswith=qn, then=Value(0.4)), default=Value(0.0), output_field=FloatField()),
    )
    cond = Q(vetor=consulta)
    if len(qn) >= 4:
        cond |= Q(sim__gte=SIM_MINIMA)
    return qs.filter(cond).annotate(pontos=F('rel') * 3 + F('sim') + F('comeca'))


def ids_produtos(q, loja_id=None, limite=300):
    """Ids dos produtos que casam com q (erros de escrita, sinónimos, atributos…), do mais relevante para o
    menos. Sem filtro de visibilidade: quem chama já tem o queryset certo (ex.: o catálogo da loja)."""
    qn = normalizar(q, juntar=False)
    tokens = _tokens(normalizar(re.sub(r'(?<=[^\W_])[-/.](?=[^\W_])', '', q), juntar=False))
    if len(qn.replace(' ', '')) < 2 or not tokens:
        return []

    def procurar(juntar):
        qs = _base('produto', qn, tokens, juntar, visiveis=False)
        return qs.filter(loja_id=loja_id) if loja_id else qs
    qs = procurar('&')
    if len(tokens) > 1 and not qs.exists():
        qs = procurar('|')
    return list(qs.order_by('-pontos', 'objeto_id').values_list('objeto_id', flat=True)[:limite])


def _procurar(tipo, qn, tokens, filtros, ordem):
    """→ queryset de EntradaPesquisa ordenado; se pedir todas as palavras dá pouco, aceita qualquer delas."""
    qs = _filtrar(tipo, _base(tipo, qn, tokens, '&'), filtros)
    if len(tokens) > 1 and not qs.exists():
        qs = _filtrar(tipo, _base(tipo, qn, tokens, '|'), filtros)
    return _ordenar(tipo, qs, ordem)


def _candidatos_semanticos(vetor):
    """{tipo: [(id, semelhança)]} já com os limiares (mínimo, margem no tipo e margem global)."""
    from . import semantica
    if vetor is None:
        return {}
    por_tipo = {t: semantica.semelhantes(t, vetor, _visiveis(t), limite=SEM_LIMITE, minimo=SEM_MINIMO, margem=SEM_MARGEM)
                for t in TIPOS}
    melhor = max((r[0][1] for r in por_tipo.values() if r), default=0)
    return {t: [(i, v) for i, v in r if v >= melhor - SEM_MARGEM_GLOBAL] for t, r in por_tipo.items()}


def _hibrido(tipo, qn, tokens, filtros, ordem, vetor, candidatos=None):
    """
    → (ids ordenados, total). Sem vetor: só palavras (contagem exacta, paginação na base).
    Com vetor: junta as palavras (até MAX_HIBRIDO) com os mais parecidos em significado (RRF); os semânticos
    passam pelos mesmos filtros e pela mesma visibilidade.
    """
    from ..models import EntradaPesquisa
    qs = _procurar(tipo, qn, tokens, filtros, ordem)
    if vetor is None:
        return qs, None
    lex = list(qs.values_list('objeto_id', flat=True)[:MAX_HIBRIDO])
    sem = (candidatos if candidatos is not None else _candidatos_semanticos(vetor)).get(tipo, [])
    if sem and filtros:
        ok = set(_filtrar(tipo, EntradaPesquisa.objects.filter(tipo=tipo, objeto_id__in=[i for i, _ in sem]), filtros)
                 .values_list('objeto_id', flat=True))
        sem = [(i, v) for i, v in sem if i in ok]
    pontos = {}
    for r, i in enumerate(lex):
        pontos[i] = pontos.get(i, 0) + 1 / (RRF_K + r)
    for r, (i, _) in enumerate(sem):
        pontos[i] = pontos.get(i, 0) + PESO_SEMANTICO / (RRF_K + r)
    ids = sorted(pontos, key=lambda i: (-pontos[i], i))
    if tipo == 'produto' and ordem in ('preco', '-preco') and ids:
        from ..models import Produto
        ids = list(Produto.objects.filter(id__in=ids).order_by(ordem, 'id').values_list('id', flat=True))
    return ids, len(ids)


def _filtrar(tipo, qs, f):
    from django.db.models import Exists, OuterRef
    if tipo == 'produto' and (f.get('preco_min') is not None or f.get('preco_max') is not None):
        from ..models import Produto
        p = Produto.objects.filter(pk=OuterRef('objeto_id'))
        if f.get('preco_min') is not None:
            p = p.filter(preco__gte=f['preco_min'])
        if f.get('preco_max') is not None:
            p = p.filter(preco__lte=f['preco_max'])
        qs = qs.filter(Exists(p))
    if f.get('categoria'):
        qs = qs.filter(loja__categoria__iexact=f['categoria'])
    if f.get('localizacao'):
        qs = qs.filter(loja__localizacao__icontains=f['localizacao'])
    return qs


def _ordenar(tipo, qs, ordem):
    if tipo == 'produto' and ordem in ('preco', '-preco'):
        from django.db.models import OuterRef, Subquery
        from ..models import Produto
        qs = qs.annotate(preco=Subquery(Produto.objects.filter(pk=OuterRef('objeto_id')).values('preco')[:1]))
        return qs.order_by(ordem, '-pontos', 'id')
    return qs.order_by('-pontos', 'nome_norm', 'id')


# ── o que se devolve de cada um ──────────────────────────────────────

def _url(request, f):
    try:
        return request.build_absolute_uri(f.url) if f else None
    except Exception:
        return None


def _produtos(ids, request):
    from ..models import Produto
    por_id = {p.id: p for p in Produto.objects.filter(id__in=ids).select_related('loja', 'inventario')}
    out = []
    for i in ids:
        p = por_id.get(i)
        if not p:
            continue
        inv = getattr(p, 'inventario', None) if not p.e_conjunto else None
        out.append({'id': p.id, 'nome': p.nome, 'preco': str(p.preco),
                    'imagem': _url(request, p.ficheiro_poster) or (_url(request, p.ficheiro) if p.ficheiro_estado != 'processando' else None),
                    'video': bool(p.ficheiro and re.search(r'\.(mp4|webm|mov|mkv)$', p.ficheiro.name or '', re.I)),
                    'esgotado': bool(inv is not None and inv.quantidade <= 0),
                    'loja': {'id': p.loja_id, 'nome': p.loja.nome}})
    return out


def _lojas(ids, request):
    from ..models import Loja
    from .home import rotulo_categoria
    por_id = Loja.objects.in_bulk(ids)
    return [{'id': l.id, 'nome': l.nome, 'logo': _url(request, l.logo), 'categoria': rotulo_categoria(l.categoria),
             'localizacao': l.localizacao} for l in (por_id.get(i) for i in ids) if l]


def _servicos(ids, request):
    from ..servicos.models import Servico
    from ..servicos.views_cliente import servico_card
    por_id = {s.id: s for s in Servico.objects.filter(id__in=ids).select_related('loja').prefetch_related('imagens')}
    return [servico_card(request, por_id[i]) for i in ids if i in por_id]


HIDRATAR = {'produto': _produtos, 'loja': _lojas, 'servico': _servicos}
TIPOS = ('produto', 'loja', 'servico')


def _categorias(qn, tokens):
    """Categorias de lojas (as do menu da home) que começam por alguma palavra pesquisada (ou sinónimo)."""
    from .home import categorias_lojas
    palavras = set(tokens) | {s for t in tokens for s in _SIN.get(t, ())}
    out = []
    for c in categorias_lojas():
        nome = normalizar(c['nome'], juntar=False)
        if qn in nome or any(w.startswith(t) for w in nome.split() for t in palavras if len(t) >= 3):
            out.append(c)
    return out[:4]


def _sugestao(qn):
    """Nenhum resultado: o nome mais parecido (à vista) → "Querias dizer …?"."""
    from django.contrib.postgres.search import TrigramWordSimilarity
    from django.db.models import Q, Value
    from ..models import EntradaPesquisa
    q = Q()
    for t in TIPOS:
        q |= Q(tipo=t, objeto_id__in=_visiveis(t))
    e = (EntradaPesquisa.objects.filter(q).annotate(sim=TrigramWordSimilarity(Value(qn), 'nome_norm'))
         .filter(sim__gte=SIM_SUGESTAO).order_by('-sim', 'id').values_list('nome', flat=True).first())
    return e


def pesquisar(q, request, tipo=None, limite=5, offset=0, filtros=None, ordem=''):
    """
    tipo=None → resumo para a lista enquanto se escreve: `limite` de cada (produtos, lojas, serviços) + categorias.
    tipo='produto'|'loja'|'servico' → só esse, paginado (página de resultados), com `total`.
    """
    q = (q or '').strip()[:MAX_Q]
    qn = normalizar(q, juntar=False)
    # 't-shirt' pesquisa-se como 'tshirt' (o índice tem as duas formas)
    tokens = _tokens(normalizar(re.sub(r'(?<=[^\W_])[-/.](?=[^\W_])', '', q), juntar=False))
    filtros = filtros or {}
    vazio = {'q': q, 'produtos': [], 'lojas': [], 'servicos': [], 'categorias': [], 'sugestao': None}
    if len(qn.replace(' ', '')) < 2 or not tokens:
        return vazio

    chave = '|'.join(map(str, [qn, tokens, tipo, limite, offset, ordem, sorted(filtros.items()),
                               request.build_absolute_uri('/')]))
    chave = 'pesq:v2:' + hashlib.sha1(chave.encode()).hexdigest()
    dados = cache.get(chave)
    if dados is not None:
        return dados

    from . import semantica
    vetor = semantica.vetor_consulta(qn)
    if tipo:
        res, total = _hibrido(tipo, qn, tokens, filtros, ordem, vetor, _candidatos_semanticos(vetor))
        if total is None:
            total = res.count()
            ids = list(res.values_list('objeto_id', flat=True)[offset:offset + limite])
        else:
            ids = res[offset:offset + limite]
        dados = {'q': q, 'tipo': tipo, 'total': total, 'resultados': HIDRATAR[tipo](ids, request),
                 'seguinte': offset + limite if offset + limite < total else None}
        if not total and not offset:
            dados['sugestao'] = _sugestao(qn)
    else:
        dados = dict(vazio)
        totais = {}
        candidatos = _candidatos_semanticos(vetor)
        for t in TIPOS:
            res, n = _hibrido(t, qn, tokens, filtros, '', vetor, candidatos)
            ids = list(res.values_list('objeto_id', flat=True)[:limite + 1]) if n is None else res[:limite + 1]
            totais[t] = len(ids)
            dados[{'produto': 'produtos', 'loja': 'lojas', 'servico': 'servicos'}[t]] = HIDRATAR[t](ids[:limite], request)
        dados['mais'] = {t: totais[t] > limite for t in TIPOS}
        dados['categorias'] = _categorias(qn, tokens)
        if not any(totais.values()) and not dados['categorias']:
            dados['sugestao'] = _sugestao(qn)
    cache.set(chave, dados, CACHE_S)
    return dados
