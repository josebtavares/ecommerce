"""
Borda HTTP (ASGI, à frente do Django) — o que aguenta muitos visitantes ao mesmo tempo.

1. Cache das respostas públicas (só visitantes sem sessão, só GET de leitura, ROTAS abaixo): fica no Redis e é servida
   daqui, sem entrar no Django — sem thread, sem base de dados (~1 ms). A chave leva versões que o backend sobe quando
   alguma coisa da loja muda (app/utils/cache_publico.py: sinais dos modelos) — o visitante vê a mudança logo; a
   validade (CACHE_PUBLICO_S, 60 s) só cobre o que muda sem passar pelos modelos (ex.: "aberta agora").
2. Limite de pedidos em simultâneo por processo (MAX_PEDIDOS). O Django corre cada pedido numa thread própria; sem
   limite, com muitos pedidos as threads esgotam-se ("can't start new thread") e os pedidos rebentam com 500. Aqui os
   que excedem esperam na fila (sem thread — é só o event loop) até ESPERA_FILA_S; depois recebem 503 "ocupado".
   /health/ não espera na fila.
Variáveis: CACHE_PUBLICO=0 desliga a cache; MAX_PEDIDOS; ESPERA_FILA_S; CACHE_PUBLICO_S.
"""
import asyncio
import hashlib
import json
import logging
import os
import re
from urllib.parse import parse_qsl, urlencode

log = logging.getLogger(__name__)

MAX_PEDIDOS = int(os.environ.get('MAX_PEDIDOS', '32'))
ESPERA_FILA_S = float(os.environ.get('ESPERA_FILA_S', '20'))
TTL = int(os.environ.get('CACHE_PUBLICO_S', '60'))
LIGADA = os.environ.get('CACHE_PUBLICO', '1') == '1'
MAX_CORPO = 2 * 1024 * 1024
PREFIXO = 'borda:'

# (padrão do caminho, âmbito): 'loja' → versão da loja (grupo 1 = id); 'catalogo' → muda com qualquer loja;
# 'global' → só configuração da plataforma. Todas levam também a versão global.
ROTAS = [
    (re.compile(r'^/app/plataforma/publica/$'), 'global'),
    (re.compile(r'^/app/home/$'), 'catalogo'),
    (re.compile(r'^/app/home/seccao/\d+/$'), 'catalogo'),
    (re.compile(r'^/app/loja/$'), 'catalogo'),
    (re.compile(r'^/app/loja/endereco/[a-z0-9-]{1,60}/$'), 'catalogo'),
    (re.compile(r'^/app/loja/(\d+)/$'), 'loja'),
    (re.compile(r'^/app/loja/(\d+)/(?:entrega/opcoes|pagamento/metodos|produtos/tipos|produtos/filtros|categorias'
                r'|avaliacoes)/$'), 'loja'),
    (re.compile(r'^/app/lojas/(\d+)/servicos/publico/$'), 'loja'),
    (re.compile(r'^/app/produto/$'), 'produtos'),      # com ?loja_id= → versão dessa loja
    (re.compile(r'^/app/produto/\d+/$'), 'catalogo'),
]

_redis = None


def _cliente():
    global _redis
    if _redis is None:
        import redis.asyncio as aioredis
        from django.conf import settings
        _redis = aioredis.from_url(settings.CACHES['default']['LOCATION'], socket_timeout=0.5,
                                   socket_connect_timeout=0.5)
    return _redis


def _cabecalho(scope, nome):
    for k, v in scope.get('headers') or ():
        if k == nome:
            return v
    return None


def _ambito(scope):
    """None → não vai à cache; senão (chaves das versões, parte fixa da chave)."""
    if scope.get('method') != 'GET' or _cabecalho(scope, b'authorization') is not None:
        return None
    caminho = scope.get('path') or ''
    for padrao, ambito in ROTAS:
        m = padrao.match(caminho)
        if m:
            break
    else:
        return None
    aceita = (_cabecalho(scope, b'accept') or b'').lower()
    if b'text/html' in aceita:      # a página navegável do DRF não vai à cache
        return None
    query = sorted(parse_qsl((scope.get('query_string') or b'').decode('latin-1'), keep_blank_values=True))
    versoes = [PREFIXO + 'v:global']
    if ambito == 'loja':
        versoes.append(f'{PREFIXO}v:loja:{m.group(1)}')
    elif ambito == 'produtos':
        loja = dict(query).get('loja_id', '')
        versoes.append(f'{PREFIXO}v:loja:{loja}' if loja.isdigit() else PREFIXO + 'v:catalogo')
    elif ambito == 'catalogo':
        versoes.append(PREFIXO + 'v:catalogo')
    origem = (_cabecalho(scope, b'origin') or b'').decode('latin-1')
    host = (_cabecalho(scope, b'host') or b'').decode('latin-1')
    fixa = '|'.join([host, origem, caminho, urlencode(query)])
    return versoes, fixa


async def _enviar(send, estado, cabecalhos, corpo):
    await send({'type': 'http.response.start', 'status': estado, 'headers': cabecalhos})
    await send({'type': 'http.response.body', 'body': corpo, 'more_body': False})


class Borda:
    def __init__(self, app):
        self.app = app
        self.vagas = None   # o semáforo nasce no event loop do processo

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('path') == '/health/':
            return await self.app(scope, receive, send)
        chave = None
        if LIGADA:
            ambito = _ambito(scope)
            if ambito:
                try:
                    r = _cliente()
                    versoes, fixa = ambito
                    vs = await r.mget(versoes)
                    texto = '|'.join((v or b'0').decode() for v in vs) + '|' + fixa
                    chave = PREFIXO + 'r:' + hashlib.sha1(texto.encode()).hexdigest()
                    guardado = await r.get(chave)
                    if guardado:
                        d = json.loads(guardado)
                        cab = [(k.encode('latin-1'), v.encode('latin-1')) for k, v in d['h']]
                        corpo = d['b'].encode('latin-1')
                        cab += [(b'content-length', str(len(corpo)).encode()), (b'x-cache', b'HIT')]
                        return await _enviar(send, d['s'], cab, corpo)
                except Exception as e:   # Redis em baixo: segue para o Django, sem cache
                    log.warning('borda: cache indisponível (%s)', e)
                    chave = None
        if self.vagas is None:
            self.vagas = asyncio.Semaphore(MAX_PEDIDOS)
        try:
            await asyncio.wait_for(self.vagas.acquire(), ESPERA_FILA_S)
        except asyncio.TimeoutError:
            corpo = json.dumps({'detail': 'O servidor está muito ocupado. Tenta outra vez daqui a pouco.'}).encode()
            return await _enviar(send, 503, [(b'content-type', b'application/json'), (b'retry-after', b'5')], corpo)
        try:
            if chave is None:
                return await self.app(scope, receive, send)
            return await self.app(scope, receive, self._guardar(send, chave))
        finally:
            self.vagas.release()

    def _guardar(self, send, chave):
        estado = {'s': None, 'h': None, 'b': [], 'n': 0, 'ok': True}

        async def enviar(msg):
            await send(msg)
            if msg['type'] == 'http.response.start':
                estado['s'] = msg['status']
                estado['h'] = [(k.decode('latin-1'), v.decode('latin-1')) for k, v in msg.get('headers') or ()]
                if msg['status'] != 200 or any(k.lower() in ('set-cookie', 'cache-control') for k, _ in estado['h']):
                    estado['ok'] = False
            elif msg['type'] == 'http.response.body' and estado['ok']:
                corpo = msg.get('body') or b''
                estado['n'] += len(corpo)
                if estado['n'] > MAX_CORPO:
                    estado['ok'] = False
                    return
                estado['b'].append(corpo)
                if not msg.get('more_body'):
                    cab = [(k, v) for k, v in estado['h'] if k.lower() not in ('date', 'content-length', 'x-cache')]
                    d = {'s': 200, 'h': cab, 'b': b''.join(estado['b']).decode('latin-1')}
                    try:
                        await _cliente().set(chave, json.dumps(d), ex=TTL)
                    except Exception as e:
                        log.warning('borda: não guardou na cache (%s)', e)
        return enviar
