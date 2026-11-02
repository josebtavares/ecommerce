// Contagem de impressões e cliques dos anúncios da home (backend utils/publicidade_stats.py).
// Uma impressão e um clique por anúncio em cada visita (esta página carregada); o servidor ainda limita por visitante.
// Envia em lotes com sendBeacon (sobrevive a sair da página e não pede pré-verificação CORS: text/plain).
const URL_EVENTOS = `${process.env.VUE_APP_URL_BASE}/app/home/publicidade/eventos/`
const ESPERA_MS = 2000
const MAX_LOTE = 20

const fila = []
const contados = new Set()
let temporizador = null

function enviar () {
  clearTimeout(temporizador)
  temporizador = null
  while (fila.length) {
    const corpo = JSON.stringify({ eventos: fila.splice(0, MAX_LOTE) })
    let foi = false
    try { foi = !!navigator.sendBeacon?.(URL_EVENTOS, new Blob([corpo], { type: 'text/plain' })) } catch (e) { /* sem beacon */ }
    if (!foi) {
      fetch(URL_EVENTOS, { method: 'POST', body: corpo, headers: { 'Content-Type': 'text/plain' }, keepalive: true, credentials: 'omit' })
        .catch(() => {})
    }
  }
}

// já = true (cliques): manda logo, antes de a página mudar
export function contarAnuncio (chave, tipo, ja = false) {
  if (!chave || !['impressao', 'clique'].includes(tipo)) return
  const k = `${tipo}:${chave}`
  if (contados.has(k)) return
  contados.add(k)
  fila.push({ chave, tipo })
  if (ja) enviar()
  else if (!temporizador) temporizador = setTimeout(enviar, ESPERA_MS)
}

if (typeof window !== 'undefined') {
  window.addEventListener('pagehide', enviar)
  document.addEventListener('visibilitychange', () => { if (document.hidden) enviar() })
}
