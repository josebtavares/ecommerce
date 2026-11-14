// Sentry no browser: erros do site (Vue, JavaScript, promessas rejeitadas). Só liga com VUE_APP_SENTRY_DSN no build.
// Backend: clube/sentry.py. Privacidade:
// - sem dados pessoais por defeito (sendDefaultPii false), sem Session Replay;
// - endereços: os valores do ?query= são escondidos (tokens de "recuperar senha", "confirmar email", regresso do Google
//   e do pagamento…), excepto uns poucos inofensivos (produto, categoria…);
// - emails escondidos nas mensagens e nos breadcrumbs;
// - sem cabeçalhos de rastreio nos pedidos à API (tracePropagationTargets vazio): o CORS da API não os aceita.
import * as Sentry from '@sentry/vue'

const SEGUROS = new Set(['produto', 'categoria', 'perfil', 'servico', 'pagina', 'aba', 'tipo', 'estado', 'periodo'])
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g

export function limparUrl (url) {
  if (typeof url !== 'string' || !url.includes('?')) return url
  try {
    const u = new URL(url, 'http://x')
    for (const k of [...u.searchParams.keys()]) {
      if (!SEGUROS.has(k)) u.searchParams.set(k, '[Filtered]')
    }
    const resto = u.search + (u.hash ? '#[Filtered]' : '')
    const base = url.split('?')[0]
    return base + resto
  } catch {
    return url.split('?')[0]
  }
}

export function semEmails (texto) {
  return typeof texto === 'string' ? texto.replace(EMAIL, '[email]') : texto
}

export function limparEvento (evento) {
  if (evento.request?.url) evento.request.url = limparUrl(evento.request.url)
  if (evento.request) { delete evento.request.cookies; delete evento.request.query_string }
  if (evento.request?.headers) {
    for (const h of Object.keys(evento.request.headers)) {
      if (/^(authorization|cookie|referer)$/i.test(h)) delete evento.request.headers[h]
    }
  }
  if (evento.message) evento.message = semEmails(evento.message)
  for (const ex of evento.exception?.values || []) ex.value = semEmails(ex.value)
  if (evento.transaction) evento.transaction = limparUrl(evento.transaction)
  // medições de desempenho: pedidos à API, carregamentos (o endereço vai na descrição e nos dados)
  for (const sp of evento.spans || []) {
    if (sp.description) sp.description = semEmails(limparUrl(sp.description))
    for (const k of Object.keys(sp.data || {})) {
      if (typeof sp.data[k] === 'string' && /url|http\.query|target/i.test(k)) sp.data[k] = limparUrl(sp.data[k])
    }
  }
  delete evento.user
  return evento
}

export function limparBreadcrumb (b) {
  if (b.data) {
    for (const k of ['url', 'from', 'to']) if (b.data[k]) b.data[k] = limparUrl(b.data[k])
    delete b.data.request_body_size
  }
  if (b.message) b.message = semEmails(limparUrl(b.message))
  return b
}

let ligado = false
export const sentryLigado = () => ligado

export function iniciarSentry (app, router) {
  const dsn = (process.env.VUE_APP_SENTRY_DSN || '').trim()
  if (!dsn) return false
  ligado = true
  Sentry.init({
    app,
    dsn,
    environment: process.env.VUE_APP_SENTRY_AMBIENTE || process.env.NODE_ENV,
    release: process.env.VUE_APP_VERSAO || undefined,
    sendDefaultPii: false,
    integrations: [Sentry.browserTracingIntegration({ router })],
    tracesSampleRate: Number(process.env.VUE_APP_SENTRY_TRACES || 0.05),
    tracePropagationTargets: [],
    // 'static': as transacções passam pelo beforeSendTransaction (limparEvento); no modo 'stream' (o defeito
    // da versão 11) era ignorado e os endereços das medições iam sem limpeza
    traceLifecycle: 'static',
    beforeSend: limparEvento,
    beforeSendTransaction: limparEvento,
    beforeBreadcrumb: limparBreadcrumb,
    // barulho que não é nosso: extensões do browser e avisos inofensivos do browser
    denyUrls: [/^chrome-extension:\/\//i, /^moz-extension:\/\//i, /^safari-(web-)?extension:\/\//i],
    ignoreErrors: ['ResizeObserver loop limit exceeded', 'ResizeObserver loop completed with undelivered notifications'],
  })
  return true
}

// para o botão de teste do painel admin (Definições)
export function testarSentry () {
  return Sentry.captureMessage('Teste do Sentry pedido no painel admin (browser)', 'error')
}
