"""
Home pública montada pelo admin.

O admin edita o rascunho (HomeSeccao / HomeItem) e publica: publicar() guarda uma cópia em
HomePublicacao.dados, que é o que a home lê. Sem publicação, usa-se LAYOUT_PADRAO (a home antiga).

Cada secção resolve-se aqui, sempre só com conteúdo válido (lojas activas, produtos activos
dessas lojas): uma loja escolhida à mão que entretanto foi suspensa desaparece sozinha.
Secções sem conteúdo não são devolvidas.
"""
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, Max, Q, Sum
from django.utils import timezone

PAGINA_LOJAS = 8
PAGINA_PRODUTOS = 10
LIMITE_MAX = 100
CACHE_SEGUNDOS = 60
VENDIDAS = ('pago', 'preparando', 'enviado', 'concluido')

CRITERIOS_LOJAS = {
    'novas':          'Lojas novas',
    'populares':      'Populares (avaliação)',
    'mais_vendidas':  'Mais vendidas',
    'mais_favoritas': 'Mais favoritas',
    'abertas':        'Abertas agora',
    'todas':          'Todas (mais recentes primeiro)',
}
CRITERIOS_PRODUTOS = {
    'novos':             'Produtos novos',
    'mais_vendidos':     'Mais vendidos',
    'destaque_donos':    'Destaques das lojas',
    'tipo':              'De um tipo',
    'loja':              'De uma loja',
    'categoria_produto': 'De uma categoria em destaque',
}

# tipo de secção → o que mostra
CONTEUDO = {
    'hero': 'hero', 'lojas': 'lojas', 'produtos': 'produtos', 'loja_destaque': 'loja_destaque',
    'categorias': 'categorias', 'banner': 'banners', 'cabecalho': 'cabecalho',
    'lojas_por_categoria': 'lojas', 'produtos_por_tipo': 'produtos', 'produtos_categorias_destaque': 'produtos',
}
GRUPOS = ('lojas_por_categoria', 'produtos_por_tipo', 'produtos_categorias_destaque')

# a home antiga, tal e qual
LAYOUT_PADRAO = [
    {'id': 'p-hero', 'tipo': 'hero', 'fonte': 'auto', 'criterio': 'novas', 'limite': 5},
    {'id': 'p-categorias', 'tipo': 'lojas_por_categoria', 'fonte': 'auto', 'limite': 50},
    {'id': 'p-produtos', 'tipo': 'cabecalho', 'titulo': 'Produtos', 'subtitulo': 'Descobre produtos de todas as lojas',
     'parametros': {'ancora': 'produtos'}},
    {'id': 'p-destaques', 'tipo': 'produtos', 'titulo': 'Em Destaque', 'fonte': 'auto', 'criterio': 'destaque_donos', 'limite': 50},
    {'id': 'p-tipos', 'tipo': 'produtos_por_tipo', 'fonte': 'auto', 'limite': 50},
    {'id': 'p-cat-destaque', 'tipo': 'produtos_categorias_destaque', 'fonte': 'auto', 'limite': 50,
     'titulo': 'Por categoria', 'parametros': {'estilo_titulo': 'divisor'}},
]

ROTULOS_CATEGORIA = {
    'restaurante': 'Restaurantes', 'moda': 'Moda', 'tecnologia': 'Tecnologia', 'supermercado': 'Supermercado',
    'farmacia': 'Farmácia', 'desporto': 'Desporto', 'beleza': 'Beleza', 'livraria': 'Livraria',
    'casa': 'Casa e Jardim', 'outros': 'Outros',
}


def rotulo_categoria(valor):
    return ROTULOS_CATEGORIA.get(valor) or (valor[:1].upper() + valor[1:])


def _int(v, padrao=None):
    if isinstance(v, bool):
        return padrao
    try:
        return int(v)
    except (TypeError, ValueError):
        return padrao


# ── publicação ─────────────────────────────────────────────────

def _dados_seccao(s):
    return {
        'id': s.id, 'tipo': s.tipo, 'titulo': s.titulo, 'subtitulo': s.subtitulo,
        'inicio': s.inicio.isoformat() if s.inicio else None,
        'fim': s.fim.isoformat() if s.fim else None,
        'fonte': s.fonte, 'criterio': s.criterio, 'parametros': s.parametros or {}, 'limite': s.limite,
        'itens': [{'loja_id': i.loja_id, 'produto_id': i.produto_id,
                   'titulo': i.titulo, 'texto': i.texto, 'link': i.link} for i in s.itens.all()],
    }


def publicar(user=None):
    """Copia o rascunho (só as secções activas) para uma nova publicação."""
    from ..models import HomeSeccao, HomePublicacao
    seccoes = HomeSeccao.objects.filter(ativa=True).prefetch_related('itens')
    pub = HomePublicacao.objects.create(dados=[_dados_seccao(s) for s in seccoes], publicado_por=user)
    return pub


def publicada():
    """(id da publicação ou 'padrao', lista de secções)."""
    from ..models import HomePublicacao
    pub = HomePublicacao.objects.only('id', 'dados').first()
    if pub is None:
        return 'padrao', LAYOUT_PADRAO
    return pub.id, pub.dados


def _visivel(s, agora):
    from django.utils.dateparse import parse_datetime
    inicio = parse_datetime(s['inicio']) if s.get('inicio') else None
    fim = parse_datetime(s['fim']) if s.get('fim') else None
    return (inicio is None or inicio <= agora) and (fim is None or agora < fim)


# ── lojas ──────────────────────────────────────────────────────

def _lojas_base():
    from ..models import Loja
    return Loja.objects.filter(ativa=True)


def _abertas_primeiro(qs):
    from django.db.models import Case, When, IntegerField
    from .horarios import ids_fechadas
    return qs.annotate(_fechada=Case(When(id__in=ids_fechadas(), then=1), default=0, output_field=IntegerField()))


def lojas_auto(criterio, p):
    qs = _lojas_base()
    if p.get('categoria'):
        qs = qs.filter(categoria__iexact=p['categoria'])
    agora = timezone.now()
    dias = _int(p.get('dias'))
    ordem = ['-data_criacao', '-id']
    abertas = criterio in ('novas', 'todas', '', None)
    if criterio == 'novas':
        if dias and dias > 0:
            qs = qs.filter(data_criacao__gte=agora - timedelta(days=dias))
    elif criterio == 'populares':
        minimo = max(_int(p.get('min_avaliacoes'), 3), 1)
        filtro = Q(avaliacoes__oculta=False)
        qs = qs.annotate(_n=Count('avaliacoes', filter=filtro), _m=Avg('avaliacoes__pontuacao', filter=filtro)) \
               .filter(_n__gte=minimo)
        ordem = ['-_m', '-_n', '-id']
    elif criterio == 'mais_vendidas':
        desde = agora - timedelta(days=dias if dias and dias > 0 else 30)
        qs = qs.annotate(_v=Count('encomendas', filter=Q(encomendas__status__in=VENDIDAS,
                                                          encomendas__data_criacao__gte=desde))).filter(_v__gt=0)
        ordem = ['-_v', '-id']
    elif criterio == 'mais_favoritas':
        qs = qs.annotate(_f=Count('favoritada_por')).filter(_f__gt=0)
        ordem = ['-_f', '-id']
    elif criterio == 'abertas':
        from .horarios import ids_fechadas
        qs = qs.exclude(id__in=ids_fechadas())
    if p.get('abertas_primeiro', abertas):
        qs = _abertas_primeiro(qs)
        ordem = ['_fechada', *ordem]
    return qs.order_by(*ordem)


def _ids_validos(qs, ids):
    """Mantém a ordem dos ids pedidos, só os que existem no queryset."""
    validos = set(qs.filter(id__in=ids).values_list('id', flat=True))
    return [i for i in ids if i in validos]


def _ids_seccao(s, base_qs, auto_qs, campo):
    """Ids finais (manual / auto / misto), sem repetidos, até ao limite."""
    limite = min(max(_int(s.get('limite'), 12), 1), LIMITE_MAX)
    fonte = s.get('fonte') or 'auto'
    manuais = []
    if fonte in ('manual', 'misto'):
        pedidos = [i[campo] for i in s.get('itens') or [] if i.get(campo)]
        manuais = _ids_validos(base_qs, list(dict.fromkeys(pedidos)))
    ids = manuais[:limite]
    if fonte in ('auto', 'misto') and len(ids) < limite and auto_qs is not None:
        extra = auto_qs.exclude(id__in=ids).values_list('id', flat=True)[:limite - len(ids)]
        ids += list(extra)
    return ids


def _serializar_lojas(ids, request):
    from ..models import Loja
    from ..Serializers.LojaSerializer import LojaPublicSerializer
    lojas = {l.id: l for l in Loja.objects.filter(id__in=ids).prefetch_related('horarios', 'excecoes')}
    return LojaPublicSerializer([lojas[i] for i in ids if i in lojas], many=True, context={'request': request}).data


# ── produtos ───────────────────────────────────────────────────

def _produtos_base():
    from ..models import Produto
    return Produto.objects.filter(ativo=True, loja__ativa=True)


def produtos_auto(criterio, p):
    qs = _produtos_base()
    if p.get('categoria_loja'):
        qs = qs.filter(loja__categoria__iexact=p['categoria_loja'])
    agora = timezone.now()
    dias = _int(p.get('dias'))
    ordem = ['-id']
    if criterio == 'novos':
        if dias and dias > 0:
            qs = qs.filter(data_criacao__gte=agora - timedelta(days=dias))
    elif criterio == 'mais_vendidos':
        desde = agora - timedelta(days=dias if dias and dias > 0 else 30)
        filtro = Q(itemencomenda__encomenda__status__in=VENDIDAS, itemencomenda__encomenda__data_criacao__gte=desde)
        qs = qs.annotate(_v=Sum('itemencomenda__quantidade', filter=filtro)).filter(_v__gt=0)
        ordem = ['-_v', '-id']
    elif criterio == 'destaque_donos':
        qs = qs.filter(destaque=True)
    elif criterio == 'tipo':
        qs = qs.filter(tipo_id=_int(p.get('tipo_id'), 0))
    elif criterio == 'loja':
        qs = qs.filter(loja_id=_int(p.get('loja_id'), 0))
    elif criterio == 'categoria_produto':
        qs = qs.filter(categorias__id=_int(p.get('categoria_id'), 0))
    return qs.order_by(*ordem)


def _serializar_produtos(ids, request):
    from ..models import Produto
    from ..Serializers.ProdutoSerializer import ProdutoSerializer
    from ..Views.produtoView import PREFETCH_CONJUNTO
    qs = Produto.objects.filter(id__in=ids).select_related('loja', 'tipo', 'inventario') \
                        .prefetch_related('variantes', *PREFETCH_CONJUNTO)
    produtos = {p.id: p for p in qs}
    return ProdutoSerializer([produtos[i] for i in ids if i in produtos], many=True, context={'request': request}).data


# ── páginas (sliders) ──────────────────────────────────────────

def _pagina(ids, offset, limit, serializar, request):
    fatia = ids[offset:offset + limit]
    return {
        'count': len(ids),
        'next_offset': offset + limit if offset + limit < len(ids) else None,
        'results': serializar(fatia, request) if fatia else [],
    }


def _grupos(s):
    """Sub-secções de uma secção de grupo: [(chave, titulo, icone, params, ids_fn)]."""
    tipo = s['tipo']
    limite = min(max(_int(s.get('limite'), 50), 1), LIMITE_MAX)
    p = s.get('parametros') or {}
    grupos = []
    if tipo == 'lojas_por_categoria':
        cats = (_lojas_base().exclude(categoria='').values('categoria')
                .annotate(_ultima=Max('data_criacao')).order_by('-_ultima'))
        vistas = []
        for c in cats:
            valor = c['categoria'].strip().lower()
            if valor and valor not in vistas:
                vistas.append(valor)
        for valor in vistas:
            qs = lojas_auto('todas', {**p, 'categoria': valor})
            grupos.append((valor, rotulo_categoria(valor), valor,
                           lambda qs=qs: list(qs.values_list('id', flat=True)[:limite])))
    elif tipo == 'produtos_por_tipo':
        from ..models import TipoProduto
        for t in TipoProduto.objects.filter(ativo=True, loja__isnull=True, pos__isnull=True).order_by('nome'):
            qs = produtos_auto('tipo', {**p, 'tipo_id': t.id})
            grupos.append((str(t.id), t.nome, '', lambda qs=qs: list(qs.values_list('id', flat=True)[:limite])))
    elif tipo == 'produtos_categorias_destaque':
        from ..models import CategoriaDestaque
        destaques = CategoriaDestaque.objects.filter(ativo=True, categoria__loja__ativa=True) \
                                             .select_related('categoria').order_by('ordem', 'id')
        for d in destaques:
            qs = produtos_auto('categoria_produto', {**p, 'categoria_id': d.categoria_id})
            grupos.append((str(d.categoria_id), d.categoria.nome, '',
                           lambda qs=qs: list(qs.values_list('id', flat=True)[:limite])))
    return grupos


def _ids_simples(s):
    """Ids de uma secção de lojas ou produtos (não-grupo)."""
    p = s.get('parametros') or {}
    if s['tipo'] == 'lojas':
        return _ids_seccao(s, _lojas_base(), lojas_auto(s.get('criterio'), p), 'loja_id')
    return _ids_seccao(s, _produtos_base(), produtos_auto(s.get('criterio'), p), 'produto_id')


def pagina_seccao(s, grupo, offset, limit, request):
    """Página seguinte de um slider (endpoint /app/home/seccao/<id>/). None se não existir."""
    conteudo = CONTEUDO.get(s['tipo'])
    if conteudo not in ('lojas', 'produtos'):
        return None
    serializar = _serializar_lojas if conteudo == 'lojas' else _serializar_produtos
    if s['tipo'] in GRUPOS:
        g = next((g for g in _grupos(s) if g[0] == grupo), None)
        if g is None:
            return None
        return _pagina(g[3](), offset, limit, serializar, request)
    return _pagina(_ids_simples(s), offset, limit, serializar, request)


# ── secção completa (primeira página) ─────────────────────────

def _base(s):
    p = s.get('parametros') or {}
    return {'id': s['id'], 'tipo': s['tipo'], 'conteudo': CONTEUDO.get(s['tipo']), 'criterio': s.get('criterio') or '',
            'titulo': s.get('titulo') or '', 'subtitulo': s.get('subtitulo') or '',
            'parametros': {k: p[k] for k in ('estilo_titulo', 'ancora') if k in p}}


def resolver(s, request):
    tipo = s['tipo']
    out = _base(s)
    p = s.get('parametros') or {}

    if tipo == 'cabecalho':
        return out if out['titulo'] else None

    if tipo in ('lojas', 'produtos'):
        conteudo = CONTEUDO[tipo]
        tam = PAGINA_LOJAS if conteudo == 'lojas' else PAGINA_PRODUTOS
        pag = pagina_seccao(s, None, 0, tam, request)
        if not pag['results']:
            return None
        out['pagina'] = pag
        return out

    if tipo in GRUPOS:
        conteudo = CONTEUDO[tipo]
        tam = PAGINA_LOJAS if conteudo == 'lojas' else PAGINA_PRODUTOS
        serializar = _serializar_lojas if conteudo == 'lojas' else _serializar_produtos
        out['grupos'] = []
        for chave, titulo, icone, ids_fn in _grupos(s):
            pag = _pagina(ids_fn(), 0, tam, serializar, request)
            if pag['results']:
                out['grupos'].append({'chave': chave, 'titulo': titulo, 'icone': icone, 'pagina': pag})
        return out if out['grupos'] else None

    if tipo == 'hero':
        slides = []
        limite = min(max(_int(s.get('limite'), 5), 1), 20)
        fonte = s.get('fonte') or 'auto'
        if fonte in ('manual', 'misto'):
            lojas_ok = set(_lojas_base().filter(id__in=[i['loja_id'] for i in s.get('itens') or [] if i.get('loja_id')])
                           .values_list('id', flat=True))
            prods_ok = set(_produtos_base().filter(id__in=[i['produto_id'] for i in s.get('itens') or [] if i.get('produto_id')])
                           .values_list('id', flat=True))
            for i in s.get('itens') or []:
                if i.get('loja_id'):
                    if i['loja_id'] in lojas_ok:
                        slides.append({'tipo': 'loja', 'id': i['loja_id'], 'titulo': i.get('titulo') or '', 'texto': i.get('texto') or ''})
                elif i.get('produto_id'):
                    if i['produto_id'] in prods_ok:
                        slides.append({'tipo': 'produto', 'id': i['produto_id'], 'titulo': i.get('titulo') or '', 'texto': i.get('texto') or ''})
                elif i.get('titulo'):
                    slides.append({'tipo': 'banner', 'titulo': i['titulo'], 'texto': i.get('texto') or '', 'link': i.get('link') or ''})
        slides = slides[:limite]
        if fonte in ('auto', 'misto') and len(slides) < limite:
            usadas = [x['id'] for x in slides if x['tipo'] == 'loja']
            extra = lojas_auto(s.get('criterio') or 'novas', p).exclude(id__in=usadas) \
                                                                 .values_list('id', flat=True)[:limite - len(slides)]
            slides += [{'tipo': 'loja', 'id': i, 'titulo': '', 'texto': ''} for i in extra]
        lojas = {l['id']: l for l in _serializar_lojas([x['id'] for x in slides if x['tipo'] == 'loja'], request)}
        prods = {x['id']: x for x in _serializar_produtos([x['id'] for x in slides if x['tipo'] == 'produto'], request)}
        for x in slides:
            if x['tipo'] == 'loja':
                x['loja'] = lojas.get(x['id'])
            elif x['tipo'] == 'produto':
                x['produto'] = prods.get(x['id'])
        out['slides'] = [x for x in slides if x['tipo'] == 'banner' or x.get('loja') or x.get('produto')]
        return out if out['slides'] else None

    if tipo == 'loja_destaque':
        loja_id = _int(p.get('loja_id')) or next((i['loja_id'] for i in s.get('itens') or [] if i.get('loja_id')), None)
        if not loja_id or not _lojas_base().filter(id=loja_id).exists():
            return None
        out['loja'] = _serializar_lojas([loja_id], request)[0]
        manuais = [i for i in s.get('itens') or [] if i.get('produto_id')]
        sub = {**s, 'itens': manuais, 'fonte': 'misto' if manuais else 'auto', 'limite': min(_int(s.get('limite'), 8) or 8, 20)}
        base = _produtos_base().filter(loja_id=loja_id)
        auto = produtos_auto('loja', {'loja_id': loja_id}).order_by('-destaque', '-id')
        out['produtos'] = _serializar_produtos(_ids_seccao(sub, base, auto, 'produto_id'), request)
        return out

    if tipo == 'categorias':
        contagem = {}
        for c in _lojas_base().exclude(categoria='').values_list('categoria', flat=True):
            v = c.strip().lower()
            contagem[v] = contagem.get(v, 0) + 1
        escolhidas = [str(c).strip().lower() for c in p.get('categorias') or []]
        ordem = [c for c in escolhidas if c in contagem] if escolhidas else sorted(contagem, key=lambda c: -contagem[c])
        out['categorias'] = [{'valor': c, 'nome': rotulo_categoria(c), 'total': contagem[c]} for c in ordem]
        return out if out['categorias'] else None

    if tipo == 'banner':
        out['banners'] = [{'titulo': i.get('titulo') or '', 'texto': i.get('texto') or '', 'link': i.get('link') or ''}
                          for i in s.get('itens') or [] if i.get('titulo')]
        return out if out['banners'] else None

    return None


def categorias_lojas():
    """Categorias das lojas activas (menu lateral da home)."""
    vistas = []
    for c in _lojas_base().exclude(categoria='').order_by('-data_criacao').values_list('categoria', flat=True):
        v = c.strip().lower()
        if v and v not in vistas:
            vistas.append(v)
    return [{'valor': v, 'nome': rotulo_categoria(v)} for v in vistas]


def home(request):
    """Payload completo da home (cache curta por publicação e por origem do pedido)."""
    pub_id, seccoes = publicada()
    chave = f'home:v1:{pub_id}:{request.build_absolute_uri("/")}'
    dados = cache.get(chave)
    if dados is None:
        agora = timezone.now()
        resolvidas = []
        for s in seccoes:
            if s.get('tipo') in CONTEUDO and _visivel(s, agora):
                r = resolver(s, request)
                if r:
                    resolvidas.append(r)
        dados = {'publicacao': pub_id, 'seccoes': resolvidas, 'categorias_lojas': categorias_lojas()}
        cache.set(chave, dados, CACHE_SEGUNDOS)
    return dados


def seccao_publicada(seccao_id):
    _, seccoes = publicada()
    agora = timezone.now()
    return next((s for s in seccoes if str(s.get('id')) == str(seccao_id) and _visivel(s, agora)), None)
