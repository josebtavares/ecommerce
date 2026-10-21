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

CRITERIOS_SERVICOS = {
    'novos':         'Serviços novos',
    'mais_marcados': 'Mais marcados (últimos 30 dias)',
}

# tipo de secção → o que mostra
CONTEUDO = {
    'servicos': 'servicos',
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
        'id': s.id, 'tipo': s.tipo, 'ativa': s.ativa, 'titulo': s.titulo, 'subtitulo': s.subtitulo,
        'inicio': s.inicio.isoformat() if s.inicio else None,
        'fim': s.fim.isoformat() if s.fim else None,
        'fonte': s.fonte, 'criterio': s.criterio, 'parametros': s.parametros or {}, 'limite': s.limite,
        'itens': [{'loja_id': i.loja_id, 'produto_id': i.produto_id, 'imagem_id': i.imagem_id,
                   'titulo': i.titulo, 'texto': i.texto, 'link': i.link} for i in s.itens.all()],
    }


def publicar(user=None):
    """Copia o rascunho para uma nova publicação (as escondidas vão também, para Descartar/Restaurar as manter)."""
    from ..models import HomeSeccao, HomePublicacao
    seccoes = HomeSeccao.objects.prefetch_related('itens')
    pub = HomePublicacao.objects.create(dados=[_dados_seccao(s) for s in seccoes], publicado_por=user)
    limpar_imagens()
    return pub


def limpar_imagens():
    """Apaga as imagens carregadas há mais de 1 dia que nenhum rascunho nem publicação usa
    (o sinal post_delete põe o ficheiro na fila do worker de limpeza)."""
    from ..models import HomeImagem, HomeItem, HomePublicacao
    usadas = set(HomeItem.objects.exclude(imagem=None).values_list('imagem_id', flat=True))
    for dados in HomePublicacao.objects.values_list('dados', flat=True):
        for s in dados or []:
            usadas.update(i.get('imagem_id') for i in s.get('itens') or [] if i.get('imagem_id'))
    HomeImagem.objects.filter(criado_em__lt=timezone.now() - timedelta(days=1)).exclude(id__in=usadas).delete()


def publicada():
    """(id da publicação ou 'padrao', lista de secções)."""
    from ..models import HomePublicacao
    pub = HomePublicacao.objects.only('id', 'dados').first()
    if pub is None:
        return 'padrao', LAYOUT_PADRAO
    return pub.id, pub.dados


def _visivel(s, agora):
    from django.utils.dateparse import parse_datetime
    if not s.get('ativa', True):
        return False
    inicio = parse_datetime(s['inicio']) if s.get('inicio') else None
    fim = parse_datetime(s['fim']) if s.get('fim') else None
    return (inicio is None or inicio <= agora) and (fim is None or agora < fim)


# ── lojas ──────────────────────────────────────────────────────

def _lojas_base():
    from ..models import Loja
    return Loja.objects.filter(ativa=True)


def _abertas_primeiro(qs, ordem):
    """Fechadas no fim. Sem nenhuma fechada não há nada a ordenar — e o Case com lista vazia vira a constante 0,
    que com .values_list() sai como "ORDER BY 0" (o Postgres lê como posição de coluna e dá erro)."""
    from django.db.models import Case, When, IntegerField
    from .horarios import ids_fechadas
    fechadas = ids_fechadas()
    if not fechadas:
        return qs, ordem
    qs = qs.annotate(_fechada=Case(When(id__in=fechadas, then=1), default=0, output_field=IntegerField()))
    return qs, ['_fechada', *ordem]


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
        qs, ordem = _abertas_primeiro(qs, ordem)
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
    from django.db.models import Prefetch
    from ..models import Loja, AvaliacaoLoja
    from ..Serializers.LojaSerializer import LojaPublicSerializer
    avaliacoes = Prefetch('avaliacoes', queryset=AvaliacaoLoja.objects.only('id', 'loja_id', 'pontuacao', 'oculta'))
    lojas = {l.id: l for l in Loja.objects.filter(id__in=ids).prefetch_related('horarios', 'excecoes', avaliacoes)}
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
                        .prefetch_related('variantes', 'imagens', 'categorias', *PREFETCH_CONJUNTO)
    produtos = {p.id: p for p in qs}
    return ProdutoSerializer([produtos[i] for i in ids if i in produtos], many=True, context={'request': request}).data


def _urls_imagens(ids, request):
    from ..models import HomeImagem
    ids = [i for i in ids if i]
    if not ids:
        return {}
    return {im.id: request.build_absolute_uri(im.ficheiro.url) for im in HomeImagem.objects.filter(id__in=ids)}


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
        for cat in categorias_destaque(p):
            qs = produtos_auto('categoria_produto', {**p, 'categoria_id': cat.id})
            grupos.append((str(cat.id), cat.nome, '', lambda qs=qs: list(qs.values_list('id', flat=True)[:limite])))
    return grupos


def categorias_destaque(p):
    """Categorias de produto da secção (parametros.categoria_ids, pela ordem escolhida). Sem lista, usa as da
    antiga página Admin → Categorias em Destaque. Só de lojas activas."""
    from ..models import CategoriaLoja, CategoriaDestaque
    ids = [i for i in (p.get('categoria_ids') or []) if isinstance(i, int)]
    if ids:
        cats = {c.id: c for c in CategoriaLoja.objects.filter(id__in=ids, loja__ativa=True)}
        return [cats[i] for i in ids if i in cats]
    destaques = CategoriaDestaque.objects.filter(ativo=True, categoria__loja__ativa=True) \
                                         .select_related('categoria').order_by('ordem', 'id')
    return [d.categoria for d in destaques]


def _ids_simples(s, vistos=None):
    """Ids de uma secção de lojas ou produtos (não-grupo).
    parametros.sem_repetidos: o automático salta o que as secções de cima já mostram (vistos);
    parametros.minimo: com menos itens do que isto a secção esconde-se (um slider com 1 produto parece vazio)."""
    p = s.get('parametros') or {}
    if s['tipo'] == 'lojas':
        base, auto, campo = _lojas_base(), lojas_auto(s.get('criterio'), p), 'loja_id'
    else:
        base, auto, campo = _produtos_base(), produtos_auto(s.get('criterio'), p), 'produto_id'
    excluir = (vistos or {}).get(CONTEUDO[s['tipo']]) if p.get('sem_repetidos') else None
    if excluir:
        auto = auto.exclude(id__in=excluir)
    ids = _ids_seccao(s, base, auto, campo)
    minimo = _int(p.get('minimo'))
    return [] if minimo and len(ids) < minimo else ids


def _escolher_loja_destaque(s):
    """Loja do bloco "loja em destaque": a escolhida à mão; sem ela, uma das primeiras do critério,
    que muda todos os dias (a mesma durante o dia inteiro, para todos)."""
    p = s.get('parametros') or {}
    loja_id = _int(p.get('loja_id')) or next((i['loja_id'] for i in s.get('itens') or [] if i.get('loja_id')), None)
    if loja_id:
        return loja_id if _lojas_base().filter(id=loja_id).exists() else None
    if s.get('criterio') in CRITERIOS_LOJAS:
        candidatas = list(lojas_auto(s['criterio'], p).values_list('id', flat=True)[:7])
        if candidatas:
            return candidatas[timezone.localdate().toordinal() % len(candidatas)]
    return None


def _ids_loja_destaque(s, loja_id):
    manuais = [i for i in s.get('itens') or [] if i.get('produto_id')]
    sub = {**s, 'itens': manuais, 'fonte': 'misto' if manuais else 'auto', 'limite': min(_int(s.get('limite'), 8) or 8, 20)}
    base = _produtos_base().filter(loja_id=loja_id)
    auto = produtos_auto('loja', {'loja_id': loja_id}).order_by('-destaque', '-id')
    return _ids_seccao(sub, base, auto, 'produto_id')


def _mostrados(s, vistos):
    """Lojas e produtos que a secção mostra (ids completos, sem serializar) — para o sem_repetidos das de baixo.
    O hero não conta: é a montra do topo, as secções de baixo podem repetir as lojas dele."""
    tipo = s['tipo']
    out = {'lojas': [], 'produtos': []}
    if tipo in ('lojas', 'produtos'):
        out[CONTEUDO[tipo]] = _ids_simples(s, vistos)
    elif tipo in GRUPOS:
        out[CONTEUDO[tipo]] = [i for g in _grupos(s) for i in g[3]()]
    elif tipo == 'loja_destaque':
        loja_id = _escolher_loja_destaque(s)
        if loja_id:
            out = {'lojas': [loja_id], 'produtos': _ids_loja_destaque(s, loja_id)}
    return out


def _usa_sem_repetidos(seccoes):
    return any((s.get('parametros') or {}).get('sem_repetidos') for s in seccoes)


def vistos_antes(seccoes, alvo_id, agora=None):
    """O que as secções visíveis acima de alvo_id mostram (None se a secção não usa sem_repetidos)."""
    agora = agora or timezone.now()
    visiveis = [s for s in seccoes if s.get('tipo') in CONTEUDO and _visivel(s, agora)]
    alvo = next((s for s in visiveis if str(s.get('id')) == str(alvo_id)), None)
    if alvo is None or not (alvo.get('parametros') or {}).get('sem_repetidos'):
        return None
    vistos = {'lojas': set(), 'produtos': set()}
    for s in visiveis:
        if s is alvo:
            break
        for k, ids in _mostrados(s, vistos).items():
            vistos[k].update(ids)
    return vistos


def pagina_seccao(s, grupo, offset, limit, request, chave_cache=None, vistos=None):
    """Página seguinte de um slider (endpoint /app/home/seccao/<id>/). None se não existir.
    Com chave_cache, a lista de ids fica em cache (o endpoint é público e cada página repetia as contas)."""
    conteudo = CONTEUDO.get(s['tipo'])
    if conteudo not in ('lojas', 'produtos'):
        return None
    serializar = _serializar_lojas if conteudo == 'lojas' else _serializar_produtos
    ids = cache.get(chave_cache) if chave_cache else None
    if ids is None:
        if s['tipo'] in GRUPOS:
            g = next((g for g in _grupos(s) if g[0] == grupo), None)
            if g is None:
                return None   # grupo inexistente: não fica em cache (o nome vem do pedido)
            ids = g[3]()
        else:
            ids = _ids_simples(s, vistos)
        if chave_cache:
            cache.set(chave_cache, ids, CACHE_SEGUNDOS)
    return _pagina(ids, offset, limit, serializar, request)


def pagina_publica(seccao_id, grupo, offset, limit, request):
    """Página de um slider da home publicada (None se a secção/grupo não existir ou não estiver visível)."""
    pub_id, seccoes = publicada()
    agora = timezone.now()
    s = next((s for s in seccoes if str(s.get('id')) == str(seccao_id) and _visivel(s, agora)), None)
    if s is None:
        return None
    from hashlib import md5
    chave = f'home:v1:ids:{pub_id}:{s["id"]}:{md5((grupo or "").encode()).hexdigest()}'
    vistos = None
    if (s.get('parametros') or {}).get('sem_repetidos') and cache.get(chave) is None:
        vistos = vistos_antes(seccoes, s['id'], agora)
    return pagina_seccao(s, grupo, offset, limit, request, chave_cache=chave, vistos=vistos)


# ── secção completa (primeira página) ─────────────────────────

def _base(s):
    p = s.get('parametros') or {}
    return {'id': s['id'], 'tipo': s['tipo'], 'conteudo': CONTEUDO.get(s['tipo']), 'criterio': s.get('criterio') or '',
            'titulo': s.get('titulo') or '', 'subtitulo': s.get('subtitulo') or '',
            'parametros': {k: p[k] for k in ('estilo_titulo', 'ancora') if k in p}}


def resolver(s, request, vistos=None):
    tipo = s['tipo']
    out = _base(s)
    p = s.get('parametros') or {}

    if tipo == 'cabecalho':
        return out if out['titulo'] else None

    if tipo in ('lojas', 'produtos'):
        conteudo = CONTEUDO[tipo]
        tam = PAGINA_LOJAS if conteudo == 'lojas' else PAGINA_PRODUTOS
        pag = pagina_seccao(s, None, 0, tam, request, vistos=vistos)
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
                elif i.get('titulo') or i.get('imagem_id'):
                    slides.append({'tipo': 'banner', 'titulo': i.get('titulo') or '', 'texto': i.get('texto') or '',
                                   'link': i.get('link') or '', 'imagem_id': i.get('imagem_id')})
        slides = slides[:limite]
        if fonte in ('auto', 'misto') and len(slides) < limite:
            usadas = [x['id'] for x in slides if x['tipo'] == 'loja']
            extra = lojas_auto(s.get('criterio') or 'novas', p).exclude(id__in=usadas) \
                                                                 .values_list('id', flat=True)[:limite - len(slides)]
            slides += [{'tipo': 'loja', 'id': i, 'titulo': '', 'texto': ''} for i in extra]
        lojas = {l['id']: l for l in _serializar_lojas([x['id'] for x in slides if x['tipo'] == 'loja'], request)}
        prods = {x['id']: x for x in _serializar_produtos([x['id'] for x in slides if x['tipo'] == 'produto'], request)}
        imagens = _urls_imagens([x.get('imagem_id') for x in slides], request)
        for x in slides:
            if x['tipo'] == 'banner':
                x['imagem_url'] = imagens.get(x.pop('imagem_id', None))
            if x['tipo'] == 'loja':
                x['loja'] = lojas.get(x['id'])
            elif x['tipo'] == 'produto':
                x['produto'] = prods.get(x['id'])
        out['slides'] = [x for x in slides if (x['tipo'] == 'banner' and (x['titulo'] or x['imagem_url']))
                         or x.get('loja') or x.get('produto')]
        return out if out['slides'] else None

    if tipo == 'loja_destaque':
        loja_id = _escolher_loja_destaque(s)
        if not loja_id:
            return None
        out['loja'] = _serializar_lojas([loja_id], request)[0]
        out['produtos'] = _serializar_produtos(_ids_loja_destaque(s, loja_id), request)
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

    if tipo == 'servicos':
        out['servicos'] = servicos_auto(s.get('criterio') or 'novos', min(max(_int(s.get('limite'), 12), 1), LIMITE_MAX), request)
        return out if out['servicos'] else None

    if tipo == 'banner':
        itens = [i for i in s.get('itens') or [] if i.get('titulo') or i.get('imagem_id')]
        imagens = _urls_imagens([i.get('imagem_id') for i in itens], request)
        banners = [{'titulo': i.get('titulo') or '', 'texto': i.get('texto') or '', 'link': i.get('link') or '',
                    'imagem_url': imagens.get(i.get('imagem_id'))} for i in itens]
        out['banners'] = [b for b in banners if b['titulo'] or b['imagem_url']]
        return out if out['banners'] else None

    return None


def servicos_auto(criterio, limite, request):
    from django.db.models import Count, Q
    from ..servicos.cobranca import servicos_publicos
    from ..servicos.views_cliente import servico_card
    qs = servicos_publicos()
    if criterio == 'mais_marcados':
        desde = timezone.now() - timedelta(days=30)
        qs = qs.annotate(n=Count('marcacoes', filter=Q(marcacoes__data_criacao__gte=desde) & ~Q(marcacoes__estado='expirada'),
                                 distinct=True)).order_by('-n', '-data_criacao')
    else:
        qs = qs.order_by('-data_criacao', 'id')
    return [servico_card(request, s) for s in qs[:limite]]


def categorias_lojas():
    """Categorias das lojas activas (menu lateral da home)."""
    vistas = []
    for c in _lojas_base().exclude(categoria='').order_by('-data_criacao').values_list('categoria', flat=True):
        v = c.strip().lower()
        if v and v not in vistas:
            vistas.append(v)
    return [{'valor': v, 'nome': rotulo_categoria(v)} for v in vistas]


def montar(seccoes, request, pub_id):
    """Resolve as secções (só as que estão dentro das datas e têm conteúdo)."""
    agora = timezone.now()
    visiveis = [s for s in seccoes if s.get('tipo') in CONTEUDO and _visivel(s, agora)]
    # só se alguma secção pede "sem repetidos" vale a pena contar o que as de cima mostram
    vistos = {'lojas': set(), 'produtos': set()} if _usa_sem_repetidos(visiveis) else None
    resolvidas = []
    for s in visiveis:
        r = resolver(s, request, vistos)
        if r and vistos is not None:
            for k, ids in _mostrados(s, vistos).items():
                vistos[k].update(ids)
        if r:
            resolvidas.append(r)
    return {'publicacao': pub_id, 'seccoes': resolvidas, 'categorias_lojas': categorias_lojas()}


def home(request):
    """Payload completo da home (cache curta por publicação e por origem do pedido)."""
    pub_id, seccoes = publicada()
    chave = f'home:v1:{pub_id}:{request.build_absolute_uri("/")}'
    dados = cache.get(chave)
    if dados is None:
        dados = montar(seccoes, request, pub_id)
        cache.set(chave, dados, CACHE_SEGUNDOS)
    return dados


def seccao_publicada(seccao_id):
    _, seccoes = publicada()
    agora = timezone.now()
    return next((s for s in seccoes if str(s.get('id')) == str(seccao_id) and _visivel(s, agora)), None)


# ══════════════════════════════════════════════════════════════
# RASCUNHO (admin)
# ══════════════════════════════════════════════════════════════

MAX_SECCOES = 40
MAX_ITENS = 50
TIPOS_COM_ITENS = {
    'hero':          ('loja', 'produto', 'banner'),
    'lojas':         ('loja',),
    'produtos':      ('produto',),
    'loja_destaque': ('produto',),
    'banner':        ('banner',),
}
CRITERIOS_POR_TIPO = {
    'hero': CRITERIOS_LOJAS, 'lojas': CRITERIOS_LOJAS, 'produtos': CRITERIOS_PRODUTOS,
    'loja_destaque': CRITERIOS_LOJAS,   # sem loja escolhida: uma das primeiras deste critério, muda todos os dias
    'servicos': CRITERIOS_SERVICOS,     # só automático
}
# parâmetro → (tipo, mínimo, máximo) ; str/lista: máximo = comprimento
PARAMETROS = {
    'categoria':        ('str', 0, 100),
    'categoria_loja':   ('str', 0, 100),
    'dias':             ('int', 1, 365),
    'min_avaliacoes':   ('int', 1, 100),
    'abertas_primeiro': ('bool', 0, 0),
    'tipo_id':          ('int', 1, None),
    'loja_id':          ('int', 1, None),
    'categoria_id':     ('int', 1, None),
    'ancora':           ('str', 0, 30),
    'estilo_titulo':    ('str', 0, 10),
    'categorias':       ('lista', 0, 30),
    'categoria_ids':    ('ids', 0, 30),
    'sem_repetidos':    ('bool', 0, 0),
    'minimo':           ('int', 1, 20),
}
LIMITE_PADRAO = {'hero': 5, 'loja_destaque': 8}


def limite_padrao(tipo):
    return LIMITE_PADRAO.get(tipo, 50 if tipo in GRUPOS else 12)


def _normalizar(s):
    """Forma comparável de uma secção (sem id), para saber se o rascunho difere do publicado."""
    return {
        'tipo': s.get('tipo'), 'ativa': s.get('ativa', True) is not False,
        'titulo': s.get('titulo') or '', 'subtitulo': s.get('subtitulo') or '',
        'inicio': s.get('inicio'), 'fim': s.get('fim'), 'fonte': s.get('fonte') or 'auto',
        'criterio': s.get('criterio') or '', 'parametros': s.get('parametros') or {},
        'limite': s.get('limite') or limite_padrao(s.get('tipo')),
        'itens': [{'loja_id': i.get('loja_id'), 'produto_id': i.get('produto_id'), 'imagem_id': i.get('imagem_id'),
                   'titulo': i.get('titulo') or '', 'texto': i.get('texto') or '', 'link': i.get('link') or ''}
                  for i in s.get('itens') or []],
    }


def rascunho_dados():
    from ..models import HomeSeccao
    return [_dados_seccao(s) for s in HomeSeccao.objects.prefetch_related('itens')]


def carregar_rascunho(seccoes):
    """Substitui o rascunho por estas secções (itens de lojas/produtos que já não existem são ignorados)."""
    from django.db import transaction
    from django.utils.dateparse import parse_datetime
    from ..models import HomeSeccao, HomeItem, HomeImagem, Loja, Produto
    with transaction.atomic():
        _trancar_rascunho()
        HomeSeccao.objects.all().delete()
        todos = [i for s in seccoes for i in s.get('itens') or []]
        lojas = set(Loja.objects.filter(id__in=[i['loja_id'] for i in todos if i.get('loja_id')])
                    .values_list('id', flat=True))
        prods = set(Produto.objects.filter(id__in=[i['produto_id'] for i in todos if i.get('produto_id')])
                    .values_list('id', flat=True))
        imagens = set(HomeImagem.objects.filter(id__in=[i['imagem_id'] for i in todos if i.get('imagem_id')])
                      .values_list('id', flat=True))
        for ordem, s in enumerate(seccoes):
            n = _normalizar(s)
            sec = HomeSeccao.objects.create(
                tipo=n['tipo'], titulo=n['titulo'], subtitulo=n['subtitulo'], ordem=ordem, ativa=n['ativa'],
                inicio=parse_datetime(n['inicio']) if n['inicio'] else None,
                fim=parse_datetime(n['fim']) if n['fim'] else None,
                fonte=n['fonte'], criterio=n['criterio'], parametros=n['parametros'], limite=n['limite'])
            itens = []
            for o, i in enumerate(n['itens']):
                if (i['loja_id'] and i['loja_id'] not in lojas) or (i['produto_id'] and i['produto_id'] not in prods):
                    continue
                itens.append(HomeItem(seccao=sec, ordem=o, loja_id=i['loja_id'], produto_id=i['produto_id'],
                                      imagem_id=i['imagem_id'] if i['imagem_id'] in imagens else None,
                                      titulo=i['titulo'], texto=i['texto'], link=i['link']))
            HomeItem.objects.bulk_create(itens)


def layout_padrao_editavel():
    """O layout original, com a lista actual de categorias em destaque escrita na secção
    (a página antiga Admin → Categorias em Destaque passa a ser editada aqui)."""
    from ..models import CategoriaDestaque
    ids = list(CategoriaDestaque.objects.filter(ativo=True, categoria__isnull=False)
               .order_by('ordem', 'id').values_list('categoria_id', flat=True))
    out = []
    for s in LAYOUT_PADRAO:
        s = {**s, 'parametros': dict(s.get('parametros') or {})}
        if s['tipo'] == 'produtos_categorias_destaque' and ids:
            s['parametros']['categoria_ids'] = list(dict.fromkeys(ids))
        out.append(s)
    return out


def _trancar_rascunho():
    """Tranca até ao fim da transacção: dois pedidos ao mesmo tempo não criam o rascunho duas vezes."""
    from django.db import connection
    if connection.vendor == 'postgresql':
        with connection.cursor() as c:
            c.execute('SELECT pg_advisory_xact_lock(%s)', [774411])


def garantir_rascunho():
    """Na primeira visita ao admin (ainda nada publicado), o rascunho começa igual ao layout original.
    Depois da primeira publicação, um rascunho vazio é escolha do admin (apagou tudo) e fica vazio."""
    from django.db import transaction
    from ..models import HomeSeccao, HomePublicacao
    if HomeSeccao.objects.exists() or HomePublicacao.objects.exists():
        return
    with transaction.atomic():
        _trancar_rascunho()
        if not HomeSeccao.objects.exists() and not HomePublicacao.objects.exists():
            carregar_rascunho(layout_padrao_editavel())


def tem_alteracoes():
    pub_id, publicadas = publicada()
    if pub_id == 'padrao':
        publicadas = layout_padrao_editavel()
    return [_normalizar(s) for s in rascunho_dados()] != [_normalizar(s) for s in publicadas]


def avisos_seccao(s):
    """Problemas que o admin deve ver (lojas/produtos escolhidos que não aparecem, datas…)."""
    from ..models import Loja, Produto
    avisos = []
    itens = list(s.itens.all())
    lojas = [i.loja_id for i in itens if i.loja_id]
    prods = [i.produto_id for i in itens if i.produto_id]
    if lojas:
        for l in Loja.objects.filter(id__in=lojas, ativa=False):
            avisos.append(f'A loja "{l.nome}" não está activa ({l.estado}) e não aparece.')
    if prods:
        for p in Produto.objects.filter(id__in=prods).filter(Q(ativo=False) | Q(loja__ativa=False)):
            avisos.append(f'O produto "{p.nome}" não está visível (inactivo ou loja não activa) e não aparece.')
    agora = timezone.now()
    if s.fim and s.fim <= agora:
        avisos.append('As datas já terminaram: a secção não aparece.')
    elif s.inicio and s.inicio > agora:
        avisos.append('Só aparece a partir da data de início.')
    if s.fonte == 'manual' and s.tipo in ('hero', 'lojas', 'produtos', 'banner') and not itens:
        avisos.append('Sem itens escolhidos: a secção não aparece.')
    if s.tipo == 'cabecalho' and not s.titulo:
        avisos.append('Cabeçalho sem título: não aparece.')
    if s.tipo == 'loja_destaque':
        lid = (s.parametros or {}).get('loja_id')
        loja = Loja.objects.filter(id=lid).first() if lid else None
        if loja is None and s.criterio in CRITERIOS_LOJAS:
            if not lojas_auto(s.criterio, s.parametros or {}).exists():
                avisos.append('Nenhuma loja cumpre o critério agora: a secção não aparece.')
        elif loja is None:
            avisos.append('Escolhe a loja em destaque.')
        elif not loja.ativa:
            avisos.append(f'A loja "{loja.nome}" não está activa ({loja.estado}): a secção não aparece.')
    return avisos


def _link_valido(link):
    if not link:
        return True
    # "\" e caracteres de controlo/espaços: os browsers tratam "/\site" como "//site" (outro domínio)
    if '\\' in link or any(c.isspace() or ord(c) < 32 for c in link):
        return False
    if link.startswith('/') and not link.startswith('//'):
        return True
    from urllib.parse import urlparse
    u = urlparse(link)
    return u.scheme in ('http', 'https') and bool(u.netloc)


def _validar_parametros(p):
    from ..models import Loja, TipoProduto, CategoriaLoja
    if not isinstance(p, dict):
        return None, 'Parâmetros inválidos.'
    limpos = {}
    for k, v in p.items():
        if k not in PARAMETROS:
            return None, f'Parâmetro desconhecido: {k}.'
        t, mn, mx = PARAMETROS[k]
        if v is None or v == '':
            continue
        if t == 'int':
            n = _int(v)
            if n is None or n < mn or (mx is not None and n > mx):
                return None, f'Valor inválido em {k}.'
            limpos[k] = n
        elif t == 'bool':
            if not isinstance(v, bool):
                return None, f'Valor inválido em {k}.'
            limpos[k] = v
        elif t == 'str':
            if not isinstance(v, str) or len(v) > mx:
                return None, f'Valor inválido em {k}.'
            limpos[k] = v.strip().lower() if k in ('categoria', 'categoria_loja') else v.strip()
        elif t == 'ids':
            if not isinstance(v, list) or len(v) > mx or \
                    not all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in v):
                return None, f'Valor inválido em {k}.'
            limpos[k] = list(dict.fromkeys(v))
        else:
            if not isinstance(v, list) or len(v) > mx or not all(isinstance(x, str) and len(x) <= 100 for x in v):
                return None, f'Valor inválido em {k}.'
            limpos[k] = list(dict.fromkeys(x.strip().lower() for x in v if x.strip()))
    if limpos.get('estilo_titulo') not in (None, 'titulo', 'divisor'):
        return None, 'Estilo do título inválido.'
    if 'ancora' in limpos and not all(c.isalnum() or c in '-_' for c in limpos['ancora']):
        return None, 'A âncora só pode ter letras, números, - e _.'
    if 'tipo_id' in limpos and not TipoProduto.objects.filter(id=limpos['tipo_id'], loja__isnull=True,
                                                              pos__isnull=True).exists():
        return None, 'Esse tipo de produto não existe.'
    if 'loja_id' in limpos and not Loja.objects.filter(id=limpos['loja_id']).exists():
        return None, 'Essa loja não existe.'
    if 'categoria_id' in limpos and not CategoriaLoja.objects.filter(id=limpos['categoria_id']).exists():
        return None, 'Essa categoria não existe.'
    if limpos.get('categoria_ids') and \
            CategoriaLoja.objects.filter(id__in=limpos['categoria_ids']).count() != len(limpos['categoria_ids']):
        return None, 'Uma das categorias escolhidas não existe.'
    return limpos, None


def _validar_itens(lista, tipo, params):
    from ..models import Loja, Produto, HomeImagem
    if not isinstance(lista, list) or len(lista) > MAX_ITENS:
        return None, f'Itens inválidos (máximo {MAX_ITENS}).'
    aceites = TIPOS_COM_ITENS.get(tipo, ())
    itens = []
    for i in lista:
        if not isinstance(i, dict):
            return None, 'Item inválido.'
        loja_id, produto_id, imagem_id = _int(i.get('loja_id')), _int(i.get('produto_id')), _int(i.get('imagem_id'))
        titulo, texto, link = (i.get('titulo') or ''), (i.get('texto') or ''), (i.get('link') or '')
        if not all(isinstance(x, str) for x in (titulo, texto, link)):
            return None, 'Item inválido.'
        if len(titulo) > 120 or len(texto) > 300 or len(link) > 300:
            return None, 'Texto do item demasiado longo.'
        if loja_id and produto_id:
            return None, 'Cada item é uma loja, um produto ou um banner.'
        genero = 'loja' if loja_id else 'produto' if produto_id else 'banner'
        if genero not in aceites:
            return None, f'Esta secção não aceita itens do tipo {genero}.'
        if genero == 'banner' and not titulo.strip() and not imagem_id:
            return None, 'O banner precisa de um título ou de uma imagem.'
        if imagem_id and genero != 'banner':
            return None, 'Só os banners têm imagem própria.'
        if not _link_valido(link.strip()):
            return None, 'Link inválido: usa um caminho do site (ex.: /loja/12) ou um endereço http(s).'
        itens.append({'loja_id': loja_id, 'produto_id': produto_id, 'imagem_id': imagem_id,
                      'titulo': titulo.strip(), 'texto': texto.strip(), 'link': link.strip()})
    lojas = {x['loja_id'] for x in itens if x['loja_id']}
    prods = {x['produto_id'] for x in itens if x['produto_id']}
    if lojas and Loja.objects.filter(id__in=lojas).count() != len(lojas):
        return None, 'Uma das lojas escolhidas não existe.'
    if prods and Produto.objects.filter(id__in=prods).count() != len(prods):
        return None, 'Um dos produtos escolhidos não existe.'
    imagens = {x['imagem_id'] for x in itens if x['imagem_id']}
    if imagens and HomeImagem.objects.filter(id__in=imagens).count() != len(imagens):
        return None, 'Uma das imagens já não existe: carrega-a de novo.'
    if tipo == 'loja_destaque' and prods and \
            Produto.objects.filter(id__in=prods).exclude(loja_id=params.get('loja_id')).exists():
        return None, 'Os produtos têm de ser da loja em destaque.'
    return itens, None


def validar(dados, atual=None):
    """Valida os campos de uma secção (criar: atual=None; editar: só os campos enviados).
    Devolve (campos, itens|None, erro)."""
    from django.utils.dateparse import parse_datetime
    from ..models import HomeSeccao
    if not isinstance(dados, dict):
        return None, None, 'Pedido inválido.'
    campos = {}
    tipo = atual.tipo if atual else dados.get('tipo')
    if tipo not in dict(HomeSeccao.TIPOS):
        return None, None, 'Tipo de secção inválido.'
    if atual is None:
        campos['tipo'] = tipo
    elif 'tipo' in dados and dados['tipo'] != atual.tipo:
        return None, None, 'O tipo de uma secção não se muda: cria uma nova.'
    for k, maximo in (('titulo', 120), ('subtitulo', 200)):
        if k in dados:
            v = dados[k] if dados[k] is not None else ''
            if not isinstance(v, str) or len(v.strip()) > maximo:
                return None, None, f'{k.capitalize()} inválido (máximo {maximo} caracteres).'
            campos[k] = v.strip()
    if 'ativa' in dados:
        if not isinstance(dados['ativa'], bool):
            return None, None, 'Campo "ativa" inválido.'
        campos['ativa'] = dados['ativa']
    for k in ('inicio', 'fim'):
        if k in dados:
            v = dados[k]
            if v is None or v == '':
                campos[k] = None
                continue
            d = parse_datetime(v) if isinstance(v, str) else None
            if d is None:
                return None, None, f'Data de {k} inválida.'
            campos[k] = timezone.make_aware(d) if timezone.is_naive(d) else d
    inicio = campos.get('inicio', atual.inicio if atual else None)
    fim = campos.get('fim', atual.fim if atual else None)
    if inicio and fim and fim <= inicio:
        return None, None, 'A data de fim tem de ser depois do início.'
    if 'fonte' in dados:
        if dados['fonte'] not in dict(HomeSeccao.FONTES):
            return None, None, 'Fonte inválida.'
        campos['fonte'] = dados['fonte']
    fonte = campos.get('fonte', atual.fonte if atual else 'auto')
    if 'criterio' in dados:
        crit = dados['criterio'] or ''
        if not isinstance(crit, str):
            return None, None, 'Critério inválido.'
        validos = CRITERIOS_POR_TIPO.get(tipo)
        if crit and (validos is None or crit not in validos):
            return None, None, 'Critério inválido para este tipo de secção.'
        campos['criterio'] = crit
    if 'limite' in dados:
        lim = _int(dados['limite'])
        maximo = 20 if tipo in ('hero', 'loja_destaque') else LIMITE_MAX
        if lim is None or not 1 <= lim <= maximo:
            return None, None, f'O limite tem de estar entre 1 e {maximo}.'
        campos['limite'] = lim
    elif atual is None:
        campos['limite'] = limite_padrao(tipo)
    if 'parametros' in dados:
        limpos, erro = _validar_parametros(dados['parametros'] or {})
        if erro:
            return None, None, erro
        campos['parametros'] = limpos
    crit = campos.get('criterio', atual.criterio if atual else '')
    params = campos.get('parametros', atual.parametros if atual else {}) or {}
    # a loja em destaque pode ser criada sem loja nem critério (o admin escolhe a seguir; avisos_seccao avisa)
    if tipo == 'servicos' and fonte != 'auto':
        return None, None, 'A secção de serviços é sempre automática.'
    if fonte in ('auto', 'misto') and tipo in CRITERIOS_POR_TIPO and tipo != 'loja_destaque':
        if not crit:
            return None, None, 'Escolhe o critério automático.'
        precisa = {'tipo': 'tipo_id', 'loja': 'loja_id', 'categoria_produto': 'categoria_id'}.get(crit)
        if precisa and not params.get(precisa):
            return None, None, 'Falta escolher o valor do critério.'
    itens = None
    if 'itens' in dados:
        itens, erro = _validar_itens(dados['itens'] or [], tipo, params)
        if erro:
            return None, None, erro
    return campos, itens, None
