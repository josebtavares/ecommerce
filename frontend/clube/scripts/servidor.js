// Servidor do site em produção (substitui o `npx serve`; os ficheiros continuam a ser servidos pelo
// serve-handler, o mesmo código, com os headers do dist/serve.json).
// O que acrescenta: o HTML de cada página leva o título, a descrição e a imagem certos (scripts/seo.js),
// para os links terem pré-visualização e o Google ver as lojas; /sitemap.xml; imagens de partilha em /og/.
// Os dados guardam-se em memória e renovam-se em segundo plano, para a página nunca ficar à espera;
// se a API falhar ou demorar, sai o index.html normal — o site funciona na mesma.
const fs = require('fs')
const http = require('http')
const path = require('path')
const compression = require('compression')
const serveHandler = require('serve-handler')
const { injetar, paginaFixa, sitemap } = require('./seo')

const DIST = path.join(__dirname, '..', 'dist')
const API = (process.env.VUE_APP_URL_BASE || 'http://localhost:8000').replace(/\/$/, '')
const SITE = (process.env.SITE_URL || 'https://bende.store').replace(/\/$/, '')
const PORTA = process.env.PORT || 3000
const ESPERA_API = 1500
const VALIDADE = 5 * 60 * 1000
const VALIDADE_404 = 60 * 1000
const VALIDADE_SITEMAP = 60 * 60 * 1000
const MAX_CACHE = 2000

const config = JSON.parse(fs.readFileSync(path.join(DIST, 'serve.json'), 'utf8'))
const indexHtml = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8')
const headersBase = config.headers.find(h => h.source === '**').headers
const opcoesFicheiros = { ...config, public: DIST, directoryListing: false,
                          rewrites: [{ source: '**', destination: '/index.html' }] }

const cache = new Map()    // chave → { valor, ate }
const aPedir = new Map()   // chave → promessa (o mesmo pedido não sai duas vezes)

// valor → guarda-o; null → erro passageiro (não guarda: fica o anterior, ou o index.html normal)
function renovar (chave, pedir) {
  if (aPedir.has(chave)) return aPedir.get(chave)
  const pedido = pedir().catch(() => null).then(r => {
    aPedir.delete(chave)
    if (r) {
      cache.delete(chave)
      if (cache.size >= MAX_CACHE) cache.delete(cache.keys().next().value)
      cache.set(chave, { valor: r.valor, ate: Date.now() + r.validade })
    }
    return r ? r.valor : (cache.get(chave)?.valor ?? null)
  })
  aPedir.set(chave, pedido)
  return pedido
}

function guardado (chave, pedir) {
  const e = cache.get(chave)
  if (!e) return renovar(chave, pedir)
  if (Date.now() > e.ate) renovar(chave, pedir)   // serve o que tem e renova em segundo plano
  return Promise.resolve(e.valor)
}

const api = (caminho, ms = ESPERA_API) => fetch(API + caminho, { signal: AbortSignal.timeout(ms) })

function dadosLoja (loja, produto) {
  const q = produto ? `?produto=${produto}` : ''
  return guardado(`loja:${loja}:${produto}`, async () => {
    const r = await api(`/app/seo/loja/${loja}/${q}`)
    if (r.status === 404) return { valor: { naoExiste: true }, validade: VALIDADE_404 }
    return r.ok ? { valor: await r.json(), validade: VALIDADE } : null
  })
}

function enviarHtml (res, html, estado = 200) {
  for (const { key, value } of headersBase) res.setHeader(key, value)
  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  res.setHeader('Cache-Control', 'no-cache')
  res.statusCode = estado
  res.end(html)
}

async function paginaLoja (req, res, url, loja) {
  const pid = url.searchParams.get('produto') || ''
  const produto = /^\d{1,11}$/.test(pid) ? pid : ''
  const dados = await dadosLoja(loja, produto)
  if (!dados) return enviarHtml(res, indexHtml)
  if (dados.naoExiste) {   // a app mostra "loja não encontrada"/"fechada"; o Google não a guarda
    return enviarHtml(res, injetar(indexHtml, SITE, { ...paginaFixa('/sem-pagina'), caminho: url.pathname }), 404)
  }
  enviarHtml(res, injetar(indexHtml, SITE, dados))
}

// a imagem vem da API; a Cloudflare guarda-a pelo Cache-Control (a versão vai no ?v=)
async function imagemPartilha (res, tipo, id, soCabecalhos) {
  const r = await api(`/app/seo/imagem/${tipo}/${id}.jpg`, 8000)
  if (!r.ok) { res.statusCode = r.status === 404 ? 404 : 502; return res.end() }
  res.setHeader('Content-Type', 'image/jpeg')
  res.setHeader('Cache-Control', r.headers.get('cache-control') || 'public, max-age=3600')
  res.end(soCabecalhos ? undefined : Buffer.from(await r.arrayBuffer()))
}

async function mapaDoSite (res) {
  const xml = await guardado('sitemap', async () => {
    const r = await api('/app/seo/sitemap/', 8000)
    return r.ok ? { valor: sitemap(SITE, await r.json()), validade: VALIDADE_SITEMAP } : null
  })
  if (!xml) { res.statusCode = 503; return res.end() }
  res.setHeader('Content-Type', 'application/xml; charset=utf-8')
  res.setHeader('Cache-Control', 'public, max-age=3600')
  res.end(xml)
}

async function atender (req, res) {
  if (req.method === 'GET' || req.method === 'HEAD') {
    const url = new URL(req.url, 'http://x')
    const c = url.pathname
    const og = c.match(/^\/og\/(loja|produto)\/(\d{1,12})\.jpg$/)
    if (og) return imagemPartilha(res, og[1], og[2], req.method === 'HEAD')
    if (c === '/sitemap.xml') return mapaDoSite(res)
    const loja = c.match(/^\/loja\/(\d{1,11})\/?$/i)
    if (loja) return paginaLoja(req, res, url, loja[1])
    if (!path.extname(c)) return enviarHtml(res, injetar(indexHtml, SITE, paginaFixa(c)))
  }
  return serveHandler(req, res, opcoesFicheiros)
}

const comprimir = compression()
http.createServer((req, res) => {
  comprimir(req, res, () => atender(req, res).catch(e => {
    console.error('servidor:', req.url, e.message)
    if (!res.headersSent) { res.statusCode = 500; res.end() }
  }))
}).listen(PORTA, () => console.log(`Bende a servir ${DIST} na porta ${PORTA} (API ${API})`))
