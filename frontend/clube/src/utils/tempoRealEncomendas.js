// Tempo real pelo WebSocket das notificações: o sino (NotificacaoSino) recebe avisos só com ids e reencaminha-os
// como eventos do browser. Quem tem uma lista ou uma ficha aberta vai buscar o que mudou. Vários avisos seguidos
// juntam-se num só pedido; quando a ligação volta depois de cair, recarrega (pode ter perdido avisos); sem ligação,
// verifica de 20 em 20 s.
//   • encomendas e entregas (backend utils/tempo_real_encomendas.py): { id, loja_id }
//   • mensalidades, subscrições e faturas do Bende (utils/tempo_real_subscricoes.py): { tipo, id, loja_id, pos_id }
//   • faturas das vendas e vendas que passam a faturáveis (utils/tempo_real_faturacao.py): { origem, id, loja_id, pos_id }
//     (as comissões, créditos e cobranças de comissões vão pelas subscrições: { tipo: comissao|credito_comissao|cobranca_comissoes })
//   • números da plataforma — Dashboard e Relatórios do admin (utils/tempo_real_painel.py): { origem }
import { EVENTO_RELIGADO } from '@/composables/useTempoRealReembolsos'

export const EVENTO_ENCOMENDA = 'bendi:encomenda'
export const EVENTO_SUBSCRICAO = 'bendi:subscricao'
export const EVENTO_FATURACAO = 'bendi:faturacao'
export const EVENTO_PAINEL = 'bendi:painel'
const SEM_LIGACAO_MS = 20000

// fn(aviso | null) — null quando é para recarregar tudo (avisos diferentes juntos, religou, sem ligação).
// semSocket: páginas sem o sino (POS) — verificam sempre de 20 em 20 s enquanto visíveis.
// maximo: com avisos sem parar (muitas vendas), recarrega pelo menos a cada `maximo` ms. Devolve a função para parar.
export function ouvirAvisos (evento, fn, { filtro = () => true, espera = 400, maximo = 0, semSocket = false } = {}) {
  let temporizador = null
  let ultimo = null
  let primeiro = 0
  const agendar = (aviso) => {
    ultimo = temporizador && ultimo?.id !== aviso?.id ? null : aviso
    if (!temporizador) primeiro = Date.now()
    else if (maximo && Date.now() - primeiro >= maximo - espera) return     // não adia mais: já vai recarregar
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
export function ouvirFaturacao (fn, opcoes) { return ouvirAvisos(EVENTO_FATURACAO, fn, opcoes) }
export function ouvirPainel (fn, opcoes) { return ouvirAvisos(EVENTO_PAINEL, fn, { espera: 1500, maximo: 6000, ...opcoes }) }
