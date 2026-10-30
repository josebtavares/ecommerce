// Depois do build: escreve a Content-Security-Policy completa no dist/serve.json (headers do `serve`).
// Os endereços da API, do WebSocket e das imagens vêm do ambiente do build (VUE_APP_*), por isso a
// mesma regra serve a dev e a prod. Scripts só do próprio site: um script injectado (XSS) não corre
// e não consegue levar os tokens que estão no localStorage para outro sítio.
const fs = require('fs')
const path = require('path')

// os mesmos .env que o vue-cli lê no build; as variáveis do ambiente (Railway) ganham sempre
const raiz = path.join(__dirname, '..')
for (const f of ['.env.production.local', '.env.local', '.env.production', '.env']) {
  require('dotenv').config({ path: path.join(raiz, f), override: false })
}

const origem = (url) => { try { return new URL(url).origin } catch { return null } }
const api = origem(process.env.VUE_APP_URL_BASE)
const media = origem(process.env.VUE_APP_MEDIA_URL)
// o WebSocket é sempre o servidor da API (services/api.js urlWebSocket)
const ws = api && api.replace(/^http/, 'ws')
// páginas de pagamento que recebem um formulário POST (utils/pagamentoOnline.js — ex.: SISP/vinti4):
// VUE_APP_PAGAMENTOS_FORM="https://a.exemplo https://b.exemplo" (vazio = só o próprio site, como até aqui)
const pagamentos = (process.env.VUE_APP_PAGAMENTOS_FORM || '').split(/[\s,]+/).map(origem)
const lista = (...v) => [...new Set(v.filter(Boolean))].join(' ')
// "não sou um robô" (components/forms/Turnstile.vue): só com a chave definida
const turnstile = process.env.VUE_APP_TURNSTILE_SITE_KEY ? 'https://challenges.cloudflare.com' : null

const politica = [
  "default-src 'self'",
  `script-src ${lista("'self'", turnstile)}`,
  // Vue, Swiper e FullCalendar mexem em estilos inline
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' data: https://fonts.gstatic.com",
  // fotos e vídeos das lojas: do armazenamento, da API e pré-visualizações locais (blob:)
  `img-src ${lista("'self'", 'data:', 'blob:', api, media, 'https:')}`,
  `media-src ${lista("'self'", 'blob:', api, media, 'https:')}`,
  `connect-src ${lista("'self'", api, ws, media, turnstile)}`,
  `frame-src ${lista("'self'", turnstile)}`,
  "frame-ancestors 'self'",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  `form-action ${lista("'self'", ...pagamentos)}`,
].join('; ')

const ficheiro = path.join(raiz, 'dist', 'serve.json')
const config = JSON.parse(fs.readFileSync(ficheiro, 'utf8'))
const todos = config.headers.find(h => h.source === '**')
const csp = todos.headers.find(h => h.key === 'Content-Security-Policy')
csp.value = politica
fs.writeFileSync(ficheiro, JSON.stringify(config, null, 2) + '\n')
console.log('CSP:', politica)
