// Tempo real dos pedidos de reembolso: o sino (NotificacaoSino) recebe pelo WebSocket das notificações um
// aviso só com ids ({ id, encomenda_id, loja_id }) e reencaminha-o como evento do browser. Quem está a ver
// um pedido ou uma lista vai buscar o que mudou. Vários avisos seguidos (uma acção com vários passos)
// juntam-se num só pedido. Quando a ligação volta depois de cair, recarrega (pode ter perdido avisos).
import { onMounted, onBeforeUnmount } from 'vue'

export const EVENTO_REEMBOLSO = 'bendi:reembolso'
export const EVENTO_RELIGADO = 'bendi:tempo-real-religado'
const SEM_LIGACAO_MS = 20000

// o sino marca aqui se o WebSocket está aberto; sem ligação (rede, proxy que bloqueia WebSockets, servidor a
// reiniciar) as páginas abertas verificam de 20 em 20 s — com ligação não fazem nada a mais
export function marcarLigacao (aberta) { window.bendiTempoReal = !!aberta }

export function useTempoRealReembolsos (aoMudar, filtro = () => true, espera = 300) {
  let temporizador = null
  const agendar = () => {
    clearTimeout(temporizador)
    temporizador = setTimeout(aoMudar, espera)
  }
  const aoAviso = (e) => { if (filtro(e.detail || {})) agendar() }

  let recurso = null
  onMounted(() => {
    window.addEventListener(EVENTO_REEMBOLSO, aoAviso)
    window.addEventListener(EVENTO_RELIGADO, agendar)
    recurso = setInterval(() => {
      if (!window.bendiTempoReal && document.visibilityState === 'visible') aoMudar()
    }, SEM_LIGACAO_MS)
  })
  onBeforeUnmount(() => {
    clearTimeout(temporizador)
    clearInterval(recurso)
    window.removeEventListener(EVENTO_REEMBOLSO, aoAviso)
    window.removeEventListener(EVENTO_RELIGADO, agendar)
  })
}
