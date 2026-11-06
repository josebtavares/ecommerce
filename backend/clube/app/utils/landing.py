"""
Landing page da Bende (/sobre): apresenta a plataforma a quem ainda não a conhece.

Uma página só, com secções fixas (TIPOS) que o admin (perm gerir_home) edita na própria página:
o rascunho (LandingRascunho, uma linha) só chega aos visitantes ao publicar (LandingPublicacao).
Sem publicação, os visitantes vêem PADRAO (textos de origem).

Formato de cada secção: {'tipo', 'ativa', 'nav', 'titulo', 'subtitulo', ...campos do tipo (CAMPOS)}.
Os textos são texto simples (o frontend nunca os mostra como HTML). Imagens e vídeos são HomeImagem
(o mesmo envio e a mesma conversão da home: R2 na produção, media no dev) e guardam-se pelo id.
"""
import re
import secrets
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.db import transaction

from . import home as H

CACHE_SEGUNDOS = 60
TIPOS = ('hero', 'clientes', 'lojas', 'planos', 'tutoriais', 'faq', 'contactos')
NOMES = {'hero': 'Topo (hero)', 'clientes': 'Para clientes', 'lojas': 'Para lojas', 'planos': 'Planos e preços',
         'tutoriais': 'Tutoriais', 'faq': 'Perguntas frequentes', 'contactos': 'Contactos'}
REDES = ('facebook', 'instagram', 'tiktok', 'youtube', 'linkedin', 'x')
TIPOS_PLANO = ('loja', 'pos', 'loja_pos', 'servicos')
RE_ICONE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
RE_YOUTUBE_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
RE_ANCORA = re.compile(r'^#[a-z0-9-]{1,40}$')
RE_ITEM_ID = re.compile(r'^[a-z0-9]{1,12}$')
MEDIAS = ('media', 'media_movel', 'media2')     # campos que guardam o id de uma HomeImagem

# ── campos de cada tipo: ('texto', máx) · ('bool',) · ('int', mín, máx) · ('botao',) · ('media',)
#    ('lista', máx itens, {campo: espec}) · ('escolhas', valores) · ('redes',) · ('email',) · ('youtube',)
_PASSO = {'icone': ('icone',), 'titulo': ('texto', 80), 'texto': ('texto', 300)}
CAMPOS = {
    'hero': {'botao': ('botao',), 'botao2': ('botao',), 'media': ('media',), 'media_movel': ('media',),
             'escurecer': ('int', 0, 80)},
    'clientes': {'passos': ('lista', 8, _PASSO), 'botao': ('botao',), 'media': ('media',), 'media2': ('media',)},
    'lojas': {'itens': ('lista', 12, _PASSO), 'botao': ('botao',), 'media': ('media',)},
    'planos': {'tipos': ('escolhas', TIPOS_PLANO), 'mostrar_comissao': ('bool',), 'comissao_titulo': ('texto', 80),
               'comissao_texto': ('texto', 300), 'nota': ('texto', 300), 'botao': ('botao',)},
    'tutoriais': {'videos': ('lista', 60, {'youtube': ('youtube',), 'titulo': ('texto', 120),
                                           'descricao': ('texto', 300), 'categoria': ('texto', 40)})},
    'faq': {'perguntas': ('lista', 40, {'pergunta': ('texto', 200), 'resposta': ('texto', 2000)})},
    'contactos': {'email': ('email',), 'telefone': ('texto', 40), 'whatsapp': ('texto', 40),
                  'morada': ('texto', 300), 'horario': ('texto', 120), 'redes': ('redes',),
                  'media': ('media',)},
}
COMUNS = {'ativa': ('bool',), 'nav': ('texto', 30), 'titulo': ('texto', 120), 'subtitulo': ('texto', 300)}
OBRIGATORIOS = {'youtube', 'pergunta'}      # itens sem estes campos não fazem sentido


def _b(texto, link):
    return {'texto': texto, 'link': link}


PADRAO = [
    {'tipo': 'hero', 'ativa': True, 'nav': '',
     'titulo': 'Tudo o que precisas, nas lojas de Cabo Verde',
     'subtitulo': 'Compra nas lojas da tua ilha, marca serviços e recebe em casa. Para quem vende, a Bende junta '
                  'loja online, POS, entregas e faturação num só lugar.',
     'botao': _b('Ir à loja Bende', '/Home'), 'botao2': _b('Criar conta', '#criar-conta'),
     'media': None, 'media_movel': None, 'escurecer': 45},
    {'tipo': 'clientes', 'ativa': True, 'nav': 'Para clientes',
     'titulo': 'Comprar na Bende é simples',
     'subtitulo': 'Do produto à tua porta, em poucos passos.',
     'passos': [
         {'icone': 'store', 'titulo': 'Descobre lojas', 'texto': 'Lojas, restaurantes e serviços perto de ti, '
                                                                  'com horários, avaliações e preços claros.'},
         {'icone': 'cart-shopping', 'titulo': 'Encomenda', 'texto': 'Junta ao carrinho e paga online, por '
                                                                     'transferência ou na entrega.'},
         {'icone': 'truck-fast', 'titulo': 'Recebe', 'texto': 'Acompanha a entrega em tempo real ou levanta '
                                                              'na loja.'},
         {'icone': 'calendar-check', 'titulo': 'Marca serviços', 'texto': 'Cabeleireiro, estética, reparações: '
                                                                          'escolhe o dia e a hora.'},
     ],
     'botao': _b('Explorar lojas', '/Home'), 'media': None, 'media2': None},
    {'tipo': 'lojas', 'ativa': True, 'nav': 'Para lojas',
     'titulo': 'Vende mais com a Bende',
     'subtitulo': 'Tudo o que a tua loja precisa para vender online e ao balcão.',
     'itens': [
         {'icone': 'shop', 'titulo': 'Loja online', 'texto': 'A tua loja com endereço próprio, catálogo, '
                                                             'variantes e stock.'},
         {'icone': 'cash-register', 'titulo': 'POS', 'texto': 'Vende ao balcão com caixa, mesas e contas '
                                                              'divididas.'},
         {'icone': 'motorcycle', 'titulo': 'Entregas', 'texto': 'Os teus condutores, com prova de entrega e '
                                                                'resumo do dia.'},
         {'icone': 'file-invoice', 'titulo': 'Faturação', 'texto': 'Faturas e-Fatura e relatórios prontos '
                                                                   'para a contabilidade.'},
         {'icone': 'calendar-days', 'titulo': 'Marcações', 'texto': 'Agenda de serviços com profissionais e '
                                                                    'pacotes.'},
         {'icone': 'chart-line', 'titulo': 'Relatórios', 'texto': 'Vendas, produtos e clientes num painel '
                                                                  'simples.'},
     ],
     'botao': _b('Criar a minha loja', '/loja/criar'), 'media': None},
    {'tipo': 'planos', 'ativa': True, 'nav': 'Planos',
     'titulo': 'Planos e preços',
     'subtitulo': 'Começa sem mensalidade e muda quando quiseres.',
     'tipos': ['loja', 'pos', 'loja_pos', 'servicos'],
     'mostrar_comissao': True, 'comissao_titulo': 'Comissão por venda',
     'comissao_texto': 'Sem mensalidade: só pagas uma pequena percentagem quando vendes online.',
     'nota': 'Preços em escudos (CVE).', 'botao': _b('Criar a minha loja', '/loja/criar')},
    {'tipo': 'tutoriais', 'ativa': True, 'nav': 'Tutoriais',
     'titulo': 'Tutoriais', 'subtitulo': 'Aprende a usar a Bende em poucos minutos.', 'videos': []},
    {'tipo': 'faq', 'ativa': True, 'nav': 'Perguntas',
     'titulo': 'Perguntas frequentes', 'subtitulo': '',
     'perguntas': [
         {'pergunta': 'Preciso de conta para comprar?',
          'resposta': 'Sim. A conta é gratuita e serve para comprar, marcar serviços e acompanhar as encomendas.'},
         {'pergunta': 'Como abro a minha loja?',
          'resposta': 'Cria uma conta, carrega em "Criar a minha loja" e preenche os dados. A equipa da Bende '
                      'revê a loja antes de ela aparecer.'},
         {'pergunta': 'Quanto custa vender na Bende?',
          'resposta': 'Podes pagar uma comissão por venda ou escolher um plano mensal. Vê os valores na secção '
                      'Planos e preços.'},
     ]},
    {'tipo': 'contactos', 'ativa': True, 'nav': 'Contactos',
     'titulo': 'Fala connosco', 'subtitulo': 'Estamos aqui para ajudar clientes e lojas.',
     'email': '', 'telefone': '', 'whatsapp': '', 'morada': '', 'horario': '', 'redes': {}, 'media': None},
]
for _s in PADRAO:      # ids estáveis dos itens de origem (o editor usa-os como chave)
    for _k in ('passos', 'itens', 'videos', 'perguntas'):
        for _n, _i in enumerate(_s.get(_k) or []):
            _i['id'] = f'p{_n + 1}'


def _padrao(tipo):
    import copy
    return copy.deepcopy(next(s for s in PADRAO if s['tipo'] == tipo))


def normalizar(dados):
    """Lista guardada → as 7 secções, cada tipo uma vez (as que faltarem entram com o texto de origem)."""
    vistos, out = set(), []
    for s in dados or []:
        t = s.get('tipo') if isinstance(s, dict) else None
        if t in TIPOS and t not in vistos:
            vistos.add(t)
            base = _padrao(t)
            base.update({k: v for k, v in s.items() if k in COMUNS or k in CAMPOS[t]})
            out.append(base)
    out += [_padrao(t) for t in TIPOS if t not in vistos]
    return out


# ══════════════════════════════════════════════════════════════
# VALIDAÇÃO
# ══════════════════════════════════════════════════════════════

class Invalido(ValueError):
    pass


def link_valido(link):
    """'/caminho', http(s)://…, ou uma âncora da página ('#planos', '#entrar', '#criar-conta')."""
    return bool(RE_ANCORA.match(link)) or H._link_valido(link)


def youtube_id(texto):
    """Link do YouTube (watch, youtu.be, shorts, embed, live) ou o próprio id → id de 11 caracteres, ou None."""
    texto = (texto or '').strip()
    if RE_YOUTUBE_ID.match(texto):
        return texto
    if not re.match(r'^https?://', texto, re.I):
        texto = 'https://' + texto
    try:
        u = urlparse(texto)
    except ValueError:
        return None
    host = (u.hostname or '').lower()
    if host.startswith('www.'):
        host = host[4:]
    cand = None
    if host == 'youtu.be':
        cand = u.path.strip('/').split('/')[0]
    elif host in ('youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtube-nocookie.com'):
        if u.path == '/watch':
            cand = (parse_qs(u.query).get('v') or [''])[0]
        else:
            partes = u.path.strip('/').split('/')
            if len(partes) >= 2 and partes[0] in ('embed', 'shorts', 'live', 'v'):
                cand = partes[1]
    return cand if cand and RE_YOUTUBE_ID.match(cand) else None


def _texto(v, maximo, nome):
    if v is None:
        v = ''
    if not isinstance(v, str):
        raise Invalido(f'{nome}: tem de ser texto.')
    v = v.replace('\r\n', '\n').strip()
    if any(ord(c) < 32 and c not in '\n\t' for c in v):
        raise Invalido(f'{nome}: tem caracteres inválidos.')
    if len(v) > maximo:
        raise Invalido(f'{nome}: no máximo {maximo} caracteres (tem {len(v)}).')
    return v


def _valor(espec, v, nome, medias):
    tipo = espec[0]
    if tipo == 'texto':
        return _texto(v, espec[1], nome)
    if tipo == 'bool':
        if not isinstance(v, bool):
            raise Invalido(f'{nome}: tem de ser verdadeiro ou falso.')
        return v
    if tipo == 'int':
        if not isinstance(v, int) or isinstance(v, bool) or not espec[1] <= v <= espec[2]:
            raise Invalido(f'{nome}: número entre {espec[1]} e {espec[2]}.')
        return v
    if tipo == 'icone':
        v = _texto(v, 40, nome)
        if v and not RE_ICONE.match(v):
            raise Invalido(f'{nome}: ícone inválido.')
        return v
    if tipo == 'email':
        v = _texto(v, 254, nome)
        if v:
            from django.core.exceptions import ValidationError
            from django.core.validators import validate_email
            try:
                validate_email(v)       # sem aspas, "<", ">" nem espaços (vai num link mailto:)
            except ValidationError:
                raise Invalido(f'{nome}: email inválido.')
        return v
    if tipo == 'youtube':
        vid = youtube_id(v if isinstance(v, str) else '')
        if not vid:
            raise Invalido(f'{nome}: link do YouTube inválido.')
        return vid
    if tipo == 'botao':
        if v is None:
            return None
        if not isinstance(v, dict):
            raise Invalido(f'{nome}: botão inválido.')
        texto = _texto(v.get('texto'), 40, f'{nome} (texto)')
        link = _texto(v.get('link'), 300, f'{nome} (link)')
        if not texto and not link:
            return None
        if not texto or not link:
            raise Invalido(f'{nome}: o botão precisa de texto e de link.')
        if not link_valido(link):
            raise Invalido(f'{nome}: link inválido (usa /caminho, https://… ou #secção).')
        return {'texto': texto, 'link': link}
    if tipo == 'media':
        if v in (None, ''):
            return None
        if isinstance(v, dict):
            v = v.get('id')
        if not isinstance(v, int) or isinstance(v, bool):
            raise Invalido(f'{nome}: imagem/vídeo inválido.')
        medias.add(v)
        return v
    if tipo == 'escolhas':
        if not isinstance(v, list) or any(x not in espec[1] for x in v):
            raise Invalido(f'{nome}: escolha inválida.')
        return [x for x in espec[1] if x in v]          # sem repetidos, na ordem de sempre
    if tipo == 'redes':
        if v is None:
            return {}
        if not isinstance(v, dict) or any(k not in REDES for k in v):
            raise Invalido(f'{nome}: redes sociais inválidas.')
        out = {}
        for k in REDES:
            url = _texto(v.get(k), 300, f'{nome} ({k})')
            if url:
                u = urlparse(url)
                if u.scheme != 'https' or not u.netloc or not H._link_valido(url):
                    raise Invalido(f'{nome} ({k}): tem de ser um link https://.')
                out[k] = url
        return out
    if tipo == 'lista':
        if not isinstance(v, list):
            raise Invalido(f'{nome}: lista inválida.')
        if len(v) > espec[1]:
            raise Invalido(f'{nome}: no máximo {espec[1]}.')
        out, ids = [], set()
        for n, item in enumerate(v, 1):
            if not isinstance(item, dict):
                raise Invalido(f'{nome} {n}: inválido.')
            limpo = {c: _valor(e, item.get(c), f'{nome} {n} · {c}', medias) for c, e in espec[2].items()}
            for c in OBRIGATORIOS & espec[2].keys():
                if not limpo.get(c):
                    raise Invalido(f'{nome} {n}: falta {c}.')
            iid = item.get('id')
            if not (isinstance(iid, str) and RE_ITEM_ID.match(iid)) or iid in ids:
                iid = secrets.token_hex(4)
            ids.add(iid)
            out.append({'id': iid, **limpo})
        return out
    raise Invalido(f'{nome}: campo desconhecido.')


def validar_seccao(tipo, alteracoes, atual):
    """Aplica `alteracoes` (só os campos enviados) à secção `atual` → secção nova. Erro → Invalido.
    Devolve também os ids das imagens/vídeos referidos (para confirmar que existem)."""
    if not isinstance(alteracoes, dict):
        raise Invalido('Dados inválidos.')
    campos = {**COMUNS, **CAMPOS[tipo]}
    desconhecidos = set(alteracoes) - set(campos) - {'tipo'}
    if desconhecidos:
        raise Invalido(f'Campos desconhecidos: {", ".join(sorted(desconhecidos))}.')
    nova, medias = dict(atual), set()
    for c, v in alteracoes.items():
        if c != 'tipo':
            nova[c] = _valor(campos[c], v, c, medias)
    for c in MEDIAS:
        if nova.get(c):
            medias.add(nova[c])
    if medias:
        from ..models import HomeImagem
        existem = set(HomeImagem.objects.filter(id__in=medias).values_list('id', flat=True))
        if medias - existem:
            raise Invalido('Imagem ou vídeo não encontrado (volta a carregá-lo).')
    return nova


# ══════════════════════════════════════════════════════════════
# RASCUNHO E PUBLICAÇÃO
# ══════════════════════════════════════════════════════════════

def publicada():
    """(id da publicação ou 'padrao', secções)."""
    from ..models import LandingPublicacao
    pub = LandingPublicacao.objects.only('id', 'dados').first()
    if pub is None:
        return 'padrao', normalizar(PADRAO)
    return pub.id, normalizar(pub.dados)


def rascunho(trancar=False):
    """A linha do rascunho (criada a partir do publicado na 1.ª vez). trancar=True → select_for_update."""
    from ..models import LandingRascunho
    qs = LandingRascunho.objects.select_for_update() if trancar else LandingRascunho.objects
    r = qs.filter(pk=1).first()
    if r is None:
        _, dados = publicada()
        LandingRascunho.objects.get_or_create(pk=1, defaults={'dados': dados})
        r = qs.get(pk=1)
    r.dados = normalizar(r.dados)
    return r


class Desactualizado(Exception):
    pass


def _gravar(r, dados, user):
    r.dados = dados
    r.versao += 1
    r.atualizado_por = user if getattr(user, 'is_authenticated', False) else None
    r.save(update_fields=['dados', 'versao', 'atualizado_por', 'atualizado_em'])
    return r


def _versao_ok(r, versao):
    if versao is not None and versao != r.versao:
        raise Desactualizado()


def editar_seccao(tipo, alteracoes, user, versao=None):
    with transaction.atomic():
        r = rascunho(trancar=True)
        _versao_ok(r, versao)
        dados = [validar_seccao(tipo, alteracoes, s) if s['tipo'] == tipo else s for s in r.dados]
        return _gravar(r, dados, user)


def ordenar(ordem, user, versao=None):
    if not isinstance(ordem, list) or sorted(ordem) != sorted(TIPOS):
        raise Invalido('A ordem tem de ter cada secção uma vez.')
    with transaction.atomic():
        r = rascunho(trancar=True)
        _versao_ok(r, versao)
        por_tipo = {s['tipo']: s for s in r.dados}
        return _gravar(r, [por_tipo[t] for t in ordem], user)


def carregar(dados, user):
    """Substitui o rascunho (descartar = o publicado, restaurar = uma publicação antiga, padrão = textos de origem)."""
    with transaction.atomic():
        return _gravar(rascunho(trancar=True), normalizar(dados), user)


def publicar(user, versao=None):
    from ..models import LandingPublicacao
    with transaction.atomic():
        r = rascunho(trancar=True)
        _versao_ok(r, versao)
        pub = LandingPublicacao.objects.create(dados=r.dados, publicado_por=user)
    H.limpar_imagens()
    return pub


def tem_alteracoes(r=None):
    r = r or rascunho()
    return r.dados != publicada()[1]


def medias_usadas():
    """Ids de HomeImagem usados pelo rascunho ou por alguma publicação (H.limpar_imagens não os apaga)."""
    from ..models import LandingPublicacao, LandingRascunho
    usadas = set()
    listas = list(LandingRascunho.objects.values_list('dados', flat=True))
    listas += list(LandingPublicacao.objects.values_list('dados', flat=True))
    for dados in listas:
        for s in dados or []:
            if isinstance(s, dict):
                usadas.update(v for k, v in s.items() if k in MEDIAS and isinstance(v, int))
    return usadas


# ══════════════════════════════════════════════════════════════
# PÁGINA PÚBLICA
# ══════════════════════════════════════════════════════════════

def miniatura_youtube(vid):
    return f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'


def _planos(tipos):
    from ..models import PlanoSubscricao
    nomes = dict(PlanoSubscricao.TIPOS)
    period = dict(PlanoSubscricao.PERIODICIDADES)
    planos = PlanoSubscricao.objects.filter(ativo=True, tipo__in=tipos)
    return [{'id': p.id, 'nome': p.nome, 'tipo': p.tipo, 'tipo_nome': nomes.get(p.tipo, p.tipo),
             'periodicidade': p.periodicidade, 'periodicidade_nome': period.get(p.periodicidade, ''),
             'meses': p.meses, 'preco': str(p.preco), 'descricao': p.descricao,
             'limite_marcacoes_mes': p.limite_marcacoes_mes, 'limite_profissionais': p.limite_profissionais}
            for p in planos]


def _comissao_padrao():
    from ..models import Loja
    return str(Loja._meta.get_field('percentagem_comissao').default)


def _contactos(s):
    """Os campos vazios usam os contactos da plataforma (Admin → Plataforma), os do rodapé."""
    from ..models import ConfiguracaoPlataforma
    cfg = ConfiguracaoPlataforma.atual()
    return {'email': s.get('email') or cfg.contacto_email, 'telefone': s.get('telefone') or cfg.contacto_telefone,
            'whatsapp': s.get('whatsapp') or cfg.contacto_whatsapp, 'morada': s.get('morada') or cfg.contacto_morada,
            'horario': s.get('horario') or cfg.contacto_horario, 'redes': s.get('redes') or {}}


def resolver(seccoes, request, todas=False):
    """Secções guardadas → o que a página mostra. todas=False (visitantes): só activas e com conteúdo.
    todas=True (editor): todas, com 'vazia' a dizer quais os visitantes não vêem."""
    from ..models import HomeImagem
    ids = {s.get(k) for s in seccoes for k in MEDIAS if s.get(k)}
    imagens = HomeImagem.objects.in_bulk(ids) if ids else {}
    out = []
    for s in seccoes:
        r = {k: v for k, v in s.items() if k not in MEDIAS}
        for k in MEDIAS:
            if k in s:
                r[k] = H._media(imagens.get(s[k]), request) if s[k] else None
        t = s['tipo']
        if t == 'planos':
            r['planos'] = _planos(s.get('tipos') or [])
            r['comissao_percentagem'] = _comissao_padrao()
            vazia = not r['planos'] and not s.get('mostrar_comissao')
        elif t == 'tutoriais':
            r['videos'] = [{**v, 'miniatura': miniatura_youtube(v['youtube'])} for v in s.get('videos') or []]
            vazia = not r['videos']
        elif t == 'faq':
            vazia = not s.get('perguntas')
        elif t == 'contactos':
            r.update(_contactos(s))
            vazia = not any(r[k] for k in ('email', 'telefone', 'whatsapp', 'morada')) and not r['redes']
        elif t == 'clientes':
            vazia = not s.get('passos')
        elif t == 'lojas':
            vazia = not s.get('itens')
        else:
            vazia = False
        if todas:
            out.append({**r, 'vazia': vazia or not s.get('ativa')})
        elif s.get('ativa') and not vazia:
            out.append(r)
    return out


def pagina(request):
    """Payload público (cache curta por publicação e origem do pedido)."""
    pub_id, seccoes = publicada()
    chave = f'landing:v1:{pub_id}:{request.build_absolute_uri("/")}'
    dados = cache.get(chave)
    if dados is None:
        dados = {'publicacao': pub_id, 'seccoes': resolver(seccoes, request)}
        cache.set(chave, dados, CACHE_SEGUNDOS)
    return dados


# ══════════════════════════════════════════════════════════════
# YOUTUBE (editor): título e autor de um link, pelo oEmbed público (sem chave)
# ══════════════════════════════════════════════════════════════

class YoutubeErro(Exception):
    pass


def info_youtube(texto):
    """{'youtube', 'titulo', 'autor', 'miniatura'} — YoutubeErro com a mensagem para o admin.
    Sem resposta do YouTube (rede), devolve só o id e 'aviso' (o vídeo pode ser gravado na mesma)."""
    import json
    import urllib.error
    import urllib.request
    from urllib.parse import quote
    vid = youtube_id(texto)
    if not vid:
        raise YoutubeErro('Link do YouTube inválido.')
    chave = f'landing:yt:{vid}'
    guardado = cache.get(chave)
    if guardado:
        return guardado
    url = 'https://www.youtube.com/oembed?format=json&url=' + quote(f'https://www.youtube.com/watch?v={vid}', safe='')
    base = {'youtube': vid, 'titulo': '', 'autor': '', 'miniatura': miniatura_youtube(vid)}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Bende/1.0'}), timeout=6) as r:
            d = json.loads(r.read(200_000))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise YoutubeErro('Este vídeo não deixa ser mostrado noutros sites (privado ou com incorporação '
                              'desligada no YouTube).')
        if e.code in (400, 404):
            raise YoutubeErro('Vídeo não encontrado no YouTube.')
        return {**base, 'aviso': 'O YouTube não respondeu; confirma o título à mão.'}
    except Exception:
        return {**base, 'aviso': 'O YouTube não respondeu; confirma o título à mão.'}
    info = {**base, 'titulo': str(d.get('title') or '')[:120], 'autor': str(d.get('author_name') or '')[:80]}
    cache.set(chave, info, 6 * 3600)
    return info
