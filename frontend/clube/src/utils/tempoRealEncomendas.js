// Tempo real das encomendas e entregas (backend utils/tempo_real_encomendas.py): o sino (NotificacaoSino) recebe
// pelo WebSocket das notificações um aviso só com ids ({ id, loja_id }) e reencaminha-o como evento do browser.
// Quem tem uma lista ou uma ficha aberta vai buscar o que mudou. Vários avisos seguidos juntam-se num só pedido;
// quando a ligação volta depois de cair, recarrega (pode ter perdido avisos); sem ligação, verifica de 20 em 20 s.
import { EVENTO_RELIGADO } from '@/composables/useTempoRealReembolsos'

export const EVENTO_ENCOMENDA = 'bendi:encomenda'
const SEM_LIGACAO_MS = 20000

// fn(aviso | null) — null quando é para recarregar tudo (religou / sem ligação). Devolve a função para parar.
export function ouvirEncomendas (fn, { filtro = () => true, espera = 400 } = {}) {
  let temporizador = null
  let ultimo = null
  const agendar = (aviso) => {
    // avisos de encomendas diferentes no mesmo intervalo: recarrega tudo uma vez
    ultimo = temporizador && ultimo?.id !== aviso?.id ? null : aviso
    clearTimeout(temporizador)
    temporizador = setTimeout(() => { temporizador = null; fn(ultimo) }, espera)
  }
  const aoAviso = (e) => { const a = e.detail || {}; if (filtro(a)) agendar(a) }
  const aoReligar = () => agendar(null)
  window.addEventListener(EVENTO_ENCOMENDA, aoAviso)
  window.addEventListener(EVENTO_RELIGADO, aoReligar)
  const recurso = setInterval(() => {
    if (!window.bendiTempoReal && document.visibilityState === 'visible') fn(null)
  }, SEM_LIGACAO_MS)
  return () => {
    clearTimeout(temporizador)
    clearInterval(recurso)
    window.removeEventListener(EVENTO_ENCOMENDA, aoAviso)
    window.removeEventListener(EVENTO_RELIGADO, aoReligar)
  }
}
