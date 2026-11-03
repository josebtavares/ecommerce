// Tempo real pelo WebSocket das notificações: o sino (NotificacaoSino) recebe avisos só com ids e reencaminha-os
// como eventos do browser. Quem tem uma lista ou uma ficha aberta vai buscar o que mudou. Vários avisos seguidos
// juntam-se num só pedido; quando a ligação volta depois de cair, recarrega (pode ter perdido avisos); sem ligação,
// verifica de 20 em 20 s.
//   • encomendas e entregas (backend utils/tempo_real_encomendas.py): { id, loja_id }
//   • mensalidades, subscrições e faturas do Bende (utils/tempo_real_subscricoes.py): { tipo, id, loja_id, pos_id }
import { EVENTO_RELIGADO } from '@/composables/useTempoRealReembolsos'

export const EVENTO_ENCOMENDA = 'bendi:encomenda'
export const EVENTO_SUBSCRICAO = 'bendi:subscricao'
const SEM_LIGACAO_MS = 20000

// fn(aviso | null) — null quando é para recarregar tudo (avisos diferentes juntos, religou, sem ligação).
// semSocket: páginas sem o sino (POS) — verificam sempre de 20 em 20 s enquanto visíveis. Devolve a função para parar.
export function ouvirAvisos (evento, fn, { filtro = () => true, espera = 400, semSocket = false } = {}) {
  let temporizador = null
  let ultimo = null
  const agendar = (aviso) => {
    ultimo = temporizador && ultimo?.id !== aviso?.id ? null : aviso
    clearTimeout(temporizador)
    temporizador = setTimeout(() => { temporizador = null; fn(ultimo) }, espera)
  }
  const aoAviso = (e) => { const a = e.detail || {}; if (filtro(a)) agendar(a) }
  const aoReligar = () => agendar(null)
  window.addEventListener(evento, aoAviso)
  window.addEventListener(EVENTO_RELIGADO, aoReligar)
  const recurso = setInterval(() => {
    if ((semSocket || !window.bendiTempoReal) && document.visibilityState === 'visible') fn(null)
  }, SEM_LIGACAO_MS)
  return () => {
    clearTimeout(temporizador)
    clearInterval(recurso)
    window.removeEventListener(evento, aoAviso)
    window.removeEventListener(EVENTO_RELIGADO, aoReligar)
  }
}

export function ouvirEncomendas (fn, opcoes) { return ouvirAvisos(EVENTO_ENCOMENDA, fn, opcoes) }
export function ouvirSubscricoes (fn, opcoes) { return ouvirAvisos(EVENTO_SUBSCRICAO, fn, opcoes) }
