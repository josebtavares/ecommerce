"""
Pesquisa semântica (fase 2 da barra de pesquisa): "prenda para a mãe" encontra perfumes e flores mesmo sem
essas palavras. Junta-se à pesquisa por palavras (utils/pesquisa.py), nunca a substitui.

- Os vetores dos produtos/lojas/serviços (EntradaPesquisa.semantico) são calculados pelo worker, em lotes
  (atualizar_pendentes) — nunca durante o pedido de um cliente. Só se pede de novo quando o texto muda (hash).
- O vetor da pesquisa vem da API (Voyage, input_type=query) com prazo curto e fica em cache 30 dias.
- A procura é por produto interno numa matriz em memória (numpy), recarregada quando o worker muda vetores.
- Se a API falhar, demorar, ou passar o limite diário, devolve-se nada e fica só a pesquisa por palavras.
Sem VOYAGE_API_KEY tudo isto está desligado.
"""
import hashlib
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

log = logging.getLogger(__name__)

URL = 'https://api.voyageai.com/v1/embeddings'
PRAZO_CONSULTA_S = 1.2       # quanto espera o cliente (no total) pelo vetor da pesquisa
PRAZO_LOTE_S = 30
LOTE = 96                    # textos por pedido ao indexar
MAX_TEXTO = 1500             # caracteres de cada documento
MIN_LETRAS = 4               # pesquisas mais curtas são só por palavras (ainda a escrever)
LIMITE_DIA = 20000           # pedidos de vetores de pesquisa por dia (protege a conta)
CACHE_CONSULTA_S = 30 * 24 * 3600
PAUSA_ERRO_S = 60            # depois de um erro da API, não insiste durante este tempo
CHAVE_VERSAO = 'pesq:sem:versao'
CHAVE_PAUSA = 'pesq:sem:pausa'
ROTULO = {'produto': 'Produto', 'loja': 'Loja', 'servico': 'Serviço'}

_matrizes = {}               # tipo → (versão, ids np.array, matriz np.array)
_trinco = threading.Lock()
_executor = None


def _com_prazo(fn, prazo):
    """Corre fn numa thread e espera no máximo `prazo` segundos no total (ligação + TLS + resposta).
    Se passar, o cliente segue só com as palavras; a thread acaba sozinha (o urllib tem o seu timeout)."""
    global _executor
    from concurrent.futures import ThreadPoolExecutor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='voyage')
    return _executor.submit(fn).result(timeout=prazo)


def ativa():
    return bool(getattr(settings, 'VOYAGE_API_KEY', ''))


def _np():
    import numpy
    return numpy


# ── API ────────────────────────────────────────────────────────────────

def _pedir(textos, tipo_entrada, prazo):
    """→ lista de vetores float32 normalizados (mesma ordem). Erros sobem (quem chama decide)."""
    np = _np()
    corpo = json.dumps({'input': textos, 'model': settings.VOYAGE_MODELO, 'input_type': tipo_entrada,
                        'output_dimension': settings.VOYAGE_DIMENSOES}).encode()
    pedido = urllib.request.Request(URL, data=corpo, method='POST', headers={
        'Authorization': f'Bearer {settings.VOYAGE_API_KEY}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(pedido, timeout=prazo) as r:
        dados = json.loads(r.read())
    linhas = sorted(dados['data'], key=lambda d: d.get('index', 0))
    if len(linhas) != len(textos):
        raise ValueError(f'a API devolveu {len(linhas)} vetores para {len(textos)} textos')
    out = []
    for d in linhas:
        v = np.asarray(d['embedding'], dtype=np.float32)
        n = float(np.linalg.norm(v))
        out.append(v / n if n else v)
    return out


def _em_pausa():
    return bool(cache.get(CHAVE_PAUSA))


def _pausar(motivo):
    cache.set(CHAVE_PAUSA, 1, PAUSA_ERRO_S)
    log.warning('semântica: pausa %ss (%s)', PAUSA_ERRO_S, motivo)


# ── documentos (worker) ────────────────────────────────────────────────

def texto_documento(e):
    """O que se envia para o vetor de uma EntradaPesquisa (texto já normalizado do índice)."""
    partes = [f'{ROTULO.get(e.tipo, e.tipo)}: {e.nome}.']
    if e.texto_b:
        partes.append(e.texto_b + '.')
    if e.texto_c:
        partes.append(e.texto_c)
    return ' '.join(partes)[:MAX_TEXTO]


def _hash(texto):
    return hashlib.sha1(f'{settings.VOYAGE_MODELO}|{settings.VOYAGE_DIMENSOES}|{texto}'.encode()).hexdigest()


def atualizar_pendentes(maximo=2000):
    """
    Worker: calcula os vetores que faltam ou cujo texto mudou. → nº de vetores pedidos à API.
    Entradas tocadas pelo índice depois do último vetor são revistas; se o texto é igual só se marca a data.
    """
    from django.db.models import F, Q
    from ..models import EntradaPesquisa
    if not ativa() or _em_pausa():
        return 0
    qs = (EntradaPesquisa.objects.filter(Q(semantico__isnull=True) | Q(semantico_em__isnull=True)
                                         | Q(semantico_em__lt=F('atualizado_em')))
          .only('id', 'tipo', 'nome', 'texto_b', 'texto_c', 'semantico_hash').order_by('id')[:maximo])
    agora = timezone.now()
    iguais, novos = [], []
    for e in qs:
        t = texto_documento(e)
        h = _hash(t)
        if h == e.semantico_hash and e.semantico_hash:
            iguais.append(e.id)
        else:
            novos.append((e.id, t, h))
    if iguais:
        EntradaPesquisa.objects.filter(id__in=iguais).update(semantico_em=agora)
    pedidos = 0
    for i in range(0, len(novos), LOTE):
        lote = novos[i:i + LOTE]
        try:
            vetores = _pedir([t for _, t, _ in lote], 'document', PRAZO_LOTE_S)
        except Exception as e:
            _pausar(f'lote: {_erro(e)}')
            break
        for (eid, _, h), v in zip(lote, vetores):
            EntradaPesquisa.objects.filter(id=eid).update(semantico=v.tobytes(), semantico_hash=h, semantico_em=agora)
        pedidos += len(lote)
    if pedidos:
        _nova_versao()
    return pedidos


def _erro(e):
    if isinstance(e, urllib.error.HTTPError):
        return f'HTTP {e.code}'
    return type(e).__name__


def _nova_versao():
    try:
        cache.incr(CHAVE_VERSAO)
    except ValueError:
        cache.set(CHAVE_VERSAO, 1, None)


# ── consulta ───────────────────────────────────────────────────────────

def vetor_consulta(qn):
    """Vetor da pesquisa (cache 30 dias). None se não deve/consegue (curta, pausa, limite, erro, prazo)."""
    np = _np()
    if not ativa() or len(qn.replace(' ', '')) < MIN_LETRAS:
        return None
    if not re.search(r'[aeiou]', qn):      # 'xyzqwv', 'sdfgh': não são palavras (e o modelo ainda inventa)
        return None
    chave = 'pesq:semq:' + _hash(qn)
    guardado = cache.get(chave)
    if guardado is not None:
        return np.frombuffer(guardado, dtype=np.float32)
    if _em_pausa():
        return None
    dia = 'pesq:sem:dia:' + timezone.localdate().isoformat()
    if cache.get_or_set(dia, 0, 2 * 24 * 3600) >= LIMITE_DIA:
        return None
    try:
        cache.incr(dia)
    except ValueError:
        pass
    t0 = time.monotonic()
    def pedir():
        v = _pedir([qn], 'query', 3)
        cache.set(chave, v[0].tobytes(), CACHE_CONSULTA_S)   # mesmo que chegue tarde, fica para a próxima
        return v[0]
    try:
        return _com_prazo(pedir, PRAZO_CONSULTA_S)
    except Exception as e:
        from concurrent.futures import TimeoutError as Prazo
        if isinstance(e, Prazo):
            log.info('semântica: vetor da pesquisa demorou > %ss (segue só com palavras)', PRAZO_CONSULTA_S)
        else:
            _pausar(f'consulta: {_erro(e)} em {time.monotonic() - t0:.2f}s')
        return None


def _matriz(tipo):
    """(ids, matriz) dos vetores deste tipo, em memória; recarrega quando o worker muda algum."""
    np = _np()
    from ..models import EntradaPesquisa
    versao = cache.get(CHAVE_VERSAO, 0)
    atual = _matrizes.get(tipo)
    if atual and atual[0] == versao:
        return atual[1], atual[2]
    with _trinco:
        atual = _matrizes.get(tipo)
        if atual and atual[0] == versao:
            return atual[1], atual[2]
        linhas = list(EntradaPesquisa.objects.filter(tipo=tipo, semantico__isnull=False)
                      .values_list('objeto_id', 'semantico'))
        dim = settings.VOYAGE_DIMENSOES
        linhas = [(i, b) for i, b in linhas if b is not None and len(b) == dim * 4]
        ids = np.array([i for i, _ in linhas], dtype=np.int64)
        m = (np.frombuffer(b''.join(bytes(b) for _, b in linhas), dtype=np.float32).reshape(len(linhas), dim)
             if linhas else np.zeros((0, dim), dtype=np.float32))
        _matrizes[tipo] = (versao, ids, m)
        return ids, m


def semelhantes(tipo, vetor, visiveis, limite=60, minimo=0.0, margem=None):
    """→ [(objeto_id, semelhança)] dos mais parecidos, só entre os `visiveis`, acima de `minimo`
    e (com `margem`) a menos de `margem` do melhor."""
    np = _np()
    if vetor is None:
        return []
    ids, m = _matriz(tipo)
    if not len(ids):
        return []
    s = m @ vetor
    if visiveis is not None:
        s = np.where(np.isin(ids, np.fromiter(visiveis, dtype=np.int64)), s, -1.0)
    n = min(limite, len(ids))
    topo = np.argpartition(-s, n - 1)[:n]
    topo = topo[np.argsort(-s[topo])]
    if margem is not None and len(topo):
        minimo = max(minimo, float(s[topo[0]]) - margem)
    return [(int(ids[i]), float(s[i])) for i in topo if s[i] >= minimo]


# ── reordenação (rerank) ───────────────────────────────────────────────
# As semelhanças dos vetores ficam todas entre ~0,28 e ~0,67: quando a loja não tem o que se pede ("perfume"),
# os vizinhos mais próximos passam os limiares e entra ruído (Fanta). O reranker lê a pesquisa e cada candidato
# juntos e dá uma nota de relevância que separa muito melhor (calibrado em seg/calibrar_rr.py, 2026-11-02).

URL_RERANK = 'https://api.voyageai.com/v1/rerank'
PRAZO_RERANK_S = 1.0
RERANK_TEXTO = 400            # caracteres de cada candidato
LIMITE_DIA_RERANK = 20000
CACHE_RERANK_S = 7 * 24 * 3600
CHAVE_PAUSA_RERANK = 'pesq:rr:pausa'
INSTRUCAO = ('Instrução: o cliente de uma loja online em Cabo Verde pesquisou isto. '
             'Este produto, loja ou serviço é o que ele procura? Pesquisa: ')


def _pedir_rerank(q, documentos, prazo):
    """→ notas (mesma ordem dos documentos). Erros sobem."""
    corpo = json.dumps({'query': INSTRUCAO + q, 'documents': documentos, 'model': settings.VOYAGE_RERANK}).encode()
    pedido = urllib.request.Request(URL_RERANK, data=corpo, method='POST', headers={
        'Authorization': f'Bearer {settings.VOYAGE_API_KEY}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(pedido, timeout=prazo) as r:
        dados = json.loads(r.read())
    notas = [None] * len(documentos)
    for d in dados['data']:
        notas[d['index']] = float(d['relevance_score'])
    if any(n is None for n in notas):
        raise ValueError('o reranker não devolveu nota para todos os documentos')
    return notas


def reordenar(qn, entradas, prazo=None):
    """
    entradas: EntradaPesquisa (tipo, objeto_id, nome, texto_b, texto_c, semantico_hash).
    → notas de relevância na mesma ordem, ou None (desligado, pausa, limite, erro ou prazo) — quem chama
    usa então a ordem dos vetores, com um corte mais apertado.
    """
    if not ativa() or not getattr(settings, 'VOYAGE_RERANK', '') or not entradas:
        return None
    chave = 'pesq:rr:' + hashlib.sha1('|'.join(
        [settings.VOYAGE_RERANK, INSTRUCAO, qn] + [f'{e.tipo}:{e.objeto_id}:{e.semantico_hash}' for e in entradas]
    ).encode()).hexdigest()
    guardado = cache.get(chave)
    if guardado is not None:
        return guardado
    if cache.get(CHAVE_PAUSA_RERANK):
        return None
    dia = 'pesq:rr:dia:' + timezone.localdate().isoformat()
    if cache.get_or_set(dia, 0, 2 * 24 * 3600) >= LIMITE_DIA_RERANK:
        return None
    try:
        cache.incr(dia)
    except ValueError:
        pass
    documentos = [texto_documento(e)[:RERANK_TEXTO] for e in entradas]
    t0 = time.monotonic()

    def pedir():
        notas = _pedir_rerank(qn, documentos, 3)
        cache.set(chave, notas, CACHE_RERANK_S)      # mesmo que chegue tarde, fica para a próxima
        return notas
    try:
        return _com_prazo(pedir, min(prazo or PRAZO_RERANK_S, PRAZO_RERANK_S))
    except Exception as e:
        from concurrent.futures import TimeoutError as Prazo
        if isinstance(e, Prazo):
            log.info('rerank: passou o prazo (segue com a ordem dos vetores)')
        else:
            cache.set(CHAVE_PAUSA_RERANK, 1, PAUSA_ERRO_S)
            log.warning('rerank: pausa %ss (%s em %.2fs)', PAUSA_ERRO_S, _erro(e), time.monotonic() - t0)
        return None


def estado():
    """Para o admin/diagnóstico: quantos vetores existem e se a API está em pausa."""
    from ..models import EntradaPesquisa
    return {'ativa': ativa(), 'modelo': settings.VOYAGE_MODELO, 'pausa': _em_pausa(),
            'com_vetor': EntradaPesquisa.objects.filter(semantico__isnull=False).count(),
            'total': EntradaPesquisa.objects.count()}
