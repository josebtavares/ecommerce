"""
Estatísticas da secção Publicidade da home — Admin → Estatísticas → Publicidade, e a linha de resumo de cada anúncio
no editor da Página inicial.

• Impressão: o anúncio esteve mesmo à vista (≥ 50% dentro do ecrã, separador visível — o browser decide,
  components/home/HomePublicidade.vue). Clique: abriu o link do anúncio.
• Cada visitante conta no máximo uma impressão e um clique por anúncio a cada JANELA_S. O IP só entra (resumido
  com a SECRET_KEY) numa chave temporária da cache; na base de dados ficam apenas totais por anúncio e por dia.
• Só se aceitam chaves de anúncios da home publicada (nada de lixo inventado) e não se contam robôs.
"""
import csv
import hashlib
import io
import re
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.utils import timezone

JANELA_S = 30 * 60
# além do "mesmo visitante" (IP + browser), um tecto por IP e por anúncio na mesma janela: trocar de user-agent
# não inflaciona os números; 20 chega para muita gente atrás do mesmo IP (redes móveis, escritórios)
MAX_POR_IP = 20
MAX_EVENTOS = 20
CAMPOS = {'impressao': 'impressoes', 'clique': 'cliques'}
CHAVE_VALIDAS = 'pub:chaves:v1'
CACHE_VALIDAS_S = 60
ROBOS = re.compile(r'bot|crawl|spider|slurp|facebookexternalhit|whatsapp|telegram|preview|headless|lighthouse|python|curl|wget',
                   re.I)
ESTADOS = {'ativo': 'Activo', 'agendado': 'Agendado', 'terminado': 'Terminado', 'escondido': 'Secção escondida',
           'removido': 'Já não está na home'}


def _ctr(cliques, impressoes):
    return round(100 * cliques / impressoes, 1) if impressoes else None


# ── registo (público) ─────────────────────────────────────────

def chaves_publicadas():
    v = cache.get(CHAVE_VALIDAS)
    if v is None:
        from . import home as H
        _, dados = H.publicada()
        v = sorted({i['chave'] for s in dados or [] if s.get('tipo') == 'publicidade'
                    for i in s.get('itens') or [] if i.get('chave')})
        cache.set(CHAVE_VALIDAS, v, CACHE_VALIDAS_S)
    return set(v)


def esquecer_chaves():
    cache.delete(CHAVE_VALIDAS)


def _somar(chave, dia, campo):
    from ..models import AnuncioEstatistica
    if AnuncioEstatistica.objects.filter(chave=chave, dia=dia).update(**{campo: F(campo) + 1}):
        return
    try:
        with transaction.atomic():
            AnuncioEstatistica.objects.create(chave=chave, dia=dia, **{campo: 1})
    except IntegrityError:          # outro pedido criou a linha ao mesmo tempo
        AnuncioEstatistica.objects.filter(chave=chave, dia=dia).update(**{campo: F(campo) + 1})


def registar(eventos, ip, user_agent):
    """eventos = [{chave, tipo: 'impressao'|'clique'}] → quantos contaram."""
    if not isinstance(eventos, list) or not user_agent or ROBOS.search(user_agent):
        return 0
    validas = chaves_publicadas()
    if not validas:
        return 0
    quem = hashlib.sha256(f'{ip}|{user_agent}|{settings.SECRET_KEY}'.encode()).hexdigest()[:20]
    rede = hashlib.sha256(f'{ip}|{settings.SECRET_KEY}'.encode()).hexdigest()[:20]
    dia = timezone.localdate()
    contados = 0
    for e in eventos[:MAX_EVENTOS]:
        if not isinstance(e, dict):
            continue
        chave, tipo = e.get('chave'), e.get('tipo')
        if tipo not in CAMPOS or not isinstance(chave, str) or chave not in validas:
            continue
        if not cache.add(f'pub:ev:{tipo}:{chave}:{quem}', 1, JANELA_S):
            continue                # já contou há pouco (recarregar a página não infla os números)
        k_ip = f'pub:ip:{tipo}:{chave}:{rede}'
        cache.add(k_ip, 0, JANELA_S)
        if cache.incr(k_ip) > MAX_POR_IP:
            continue
        _somar(chave, dia, CAMPOS[tipo])
        contados += 1
    return contados


# ── nomes e estados ───────────────────────────────────────────

def guardar_nomes(dados):
    """Ao publicar: lembra como é cada anúncio publicado (para as estatísticas, mesmo depois de sair da home)."""
    from ..models import AnuncioInfo
    agora = timezone.now()
    for s in dados or []:
        if s.get('tipo') != 'publicidade':
            continue
        for i in s.get('itens') or []:
            if not i.get('chave'):
                continue
            info, criado = AnuncioInfo.objects.get_or_create(chave=i['chave'], defaults={'publicado_em': agora})
            info.titulo = (i.get('titulo') or '')[:120]
            info.anunciante = (i.get('anunciante') or '')[:80]
            info.link = (i.get('link') or '')[:300]
            info.imagem_id = i.get('imagem_id') or None
            info.save()


def _estados():
    """chave → estado na home publicada agora."""
    from django.utils.dateparse import parse_datetime
    from . import home as H
    agora = timezone.now()
    _, dados = H.publicada()
    out = {}
    for s in dados or []:
        if s.get('tipo') != 'publicidade':
            continue
        visivel = H._visivel(s, agora)
        for i in s.get('itens') or []:
            if not i.get('chave'):
                continue
            inicio = parse_datetime(i['inicio']) if i.get('inicio') else None
            fim = parse_datetime(i['fim']) if i.get('fim') else None
            if fim and fim <= agora:
                e = 'terminado'
            elif not visivel:
                e = 'escondido'
            elif inicio and inicio > agora:
                e = 'agendado'
            else:
                e = 'ativo'
            out.setdefault(i['chave'], e)
    return out


def _miniatura(im, request):
    if im is None:
        return None
    f = im.ficheiro_poster if im.tipo == 'video' else im.ficheiro
    if not f:
        return None
    return request.build_absolute_uri(f.url) if request else f.url


# ── Admin ─────────────────────────────────────────────────────

def _periodo(dias):
    hoje = timezone.localdate()
    return hoje - timedelta(days=dias - 1), hoje


def estatisticas(dias=30, anunciante='', request=None):
    from ..models import AnuncioEstatistica, AnuncioInfo
    desde, hoje = _periodo(dias)
    estados = _estados()
    infos = {i.chave: i for i in AnuncioInfo.objects.select_related('imagem')}
    anunciante = (anunciante or '').strip()

    linhas = AnuncioEstatistica.objects.filter(dia__gte=desde, dia__lte=hoje)
    chaves = set(estados) | set(linhas.values_list('chave', flat=True).distinct())
    if anunciante:
        chaves = {c for c in chaves if c in infos and infos[c].anunciante.lower() == anunciante.lower()}
    linhas = linhas.filter(chave__in=chaves)

    por_anuncio = {l['chave']: l for l in linhas.values('chave').annotate(i=Sum('impressoes'), c=Sum('cliques'))}
    por_dia = {l['dia']: l for l in linhas.values('dia').annotate(i=Sum('impressoes'), c=Sum('cliques'))}
    serie = []
    d = desde
    while d <= hoje:
        l = por_dia.get(d) or {}
        serie.append({'dia': d.isoformat(), 'impressoes': l.get('i') or 0, 'cliques': l.get('c') or 0})
        d += timedelta(days=1)

    anuncios = []
    for c in chaves:
        info = infos.get(c)
        t = por_anuncio.get(c) or {}
        imp, cli = t.get('i') or 0, t.get('c') or 0
        anuncios.append({
            'chave': c, 'titulo': info.titulo if info else '', 'anunciante': info.anunciante if info else '',
            'link': info.link if info else '', 'miniatura': _miniatura(info.imagem if info else None, request),
            'estado': estados.get(c, 'removido'), 'impressoes': imp, 'cliques': cli, 'ctr': _ctr(cli, imp),
        })
    ordem_estado = {'ativo': 0, 'agendado': 1, 'escondido': 2, 'terminado': 3, 'removido': 4}
    anuncios.sort(key=lambda a: (-a['impressoes'], ordem_estado[a['estado']], a['titulo'].lower()))

    imp = sum(a['impressoes'] for a in anuncios)
    cli = sum(a['cliques'] for a in anuncios)
    com_dados = set(AnuncioEstatistica.objects.values_list('chave', flat=True).distinct())
    anunciantes = sorted({i.anunciante for i in infos.values() if i.anunciante and (i.chave in com_dados or i.chave in estados)},
                         key=str.lower)
    return {
        'desde': desde.isoformat(), 'ate': hoje.isoformat(), 'anunciante': anunciante,
        'resumo': {'impressoes': imp, 'cliques': cli, 'ctr': _ctr(cli, imp),
                   'anuncios': len(anuncios), 'ativos': sum(a['estado'] == 'ativo' for a in anuncios)},
        'por_dia': serie, 'anuncios': anuncios, 'anunciantes': anunciantes, 'estados': ESTADOS,
        'janela_min': JANELA_S // 60,
    }


def _celula(v):
    """texto escrito no Admin: no Excel, '=…', '+…', '-…' e '@…' seriam fórmulas."""
    v = str(v or '')
    return "'" + v if v[:1] in ('=', '+', '-', '@', chr(9), chr(13)) else v


def csv_periodo(dias=30, anunciante=''):
    """Uma linha por anúncio e por dia com dados (para mandar ao anunciante). ';' e BOM para o Excel em PT."""
    from ..models import AnuncioEstatistica, AnuncioInfo
    desde, hoje = _periodo(dias)
    infos = {i.chave: i for i in AnuncioInfo.objects.all()}
    qs = AnuncioEstatistica.objects.filter(dia__gte=desde, dia__lte=hoje).order_by('dia', 'chave')
    anunciante = (anunciante or '').strip().lower()
    buf = io.StringIO()
    buf.write('﻿')
    w = csv.writer(buf, delimiter=';')
    w.writerow(['Dia', 'Anunciante', 'Anúncio', 'Link', 'Impressões', 'Cliques', 'CTR (%)'])
    for l in qs:
        info = infos.get(l.chave)
        if anunciante and (not info or info.anunciante.lower() != anunciante):
            continue
        ctr = _ctr(l.cliques, l.impressoes)
        w.writerow([l.dia.strftime('%d/%m/%Y'), _celula(info.anunciante if info else ''), _celula((info.titulo if info else '') or l.chave),
                    _celula(info.link if info else ''), l.impressoes, l.cliques, '' if ctr is None else str(ctr).replace('.', ',')])
    return buf.getvalue(), f'publicidade_{desde:%Y%m%d}_{hoje:%Y%m%d}.csv'


def resumo_chaves(chaves, dias=30):
    """{chave: {impressoes, cliques, ctr}} dos últimos `dias` — para o editor da Página inicial."""
    from ..models import AnuncioEstatistica
    chaves = [c for c in chaves if c]
    if not chaves:
        return {}
    desde, hoje = _periodo(dias)
    out = {}
    for l in (AnuncioEstatistica.objects.filter(chave__in=chaves, dia__gte=desde, dia__lte=hoje)
              .values('chave').annotate(i=Sum('impressoes'), c=Sum('cliques'))):
        out[l['chave']] = {'impressoes': l['i'], 'cliques': l['c'], 'ctr': _ctr(l['c'], l['i'])}
    return out
