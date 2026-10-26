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
const lista = (...v) => [...new Set(v.filter(Boolean))].join(' ')

const politica = [
  "default-src 'self'",
  "script-src 'self'",
  // Vue, Swiper e FullCalendar mexem em estilos inline
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' data: https://fonts.gstatic.com",
  // fotos e vídeos das lojas: do armazenamento, da API e pré-visualizações locais (blob:)
  `img-src ${lista("'self'", 'data:', 'blob:', api, media, 'https:')}`,
  `media-src ${lista("'self'", 'blob:', api, media, 'https:')}`,
  `connect-src ${lista("'self'", api, ws, media)}`,
  "frame-src 'self'",
  "frame-ancestors 'self'",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join('; ')

const ficheiro = path.join(raiz, 'dist', 'serve.json')
const config = JSON.parse(fs.readFileSync(ficheiro, 'utf8'))
const todos = config.headers.find(h => h.source === '**')
const csp = todos.headers.find(h => h.key === 'Content-Security-Policy')
csp.value = politica
fs.writeFileSync(ficheiro, JSON.stringify(config, null, 2) + '\n')
console.log('CSP:', politica)
