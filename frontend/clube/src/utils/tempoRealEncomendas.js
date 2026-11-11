// Tempo real pelo WebSocket das notificações: o sino (NotificacaoSino) recebe avisos só com ids e reencaminha-os
// como eventos do browser. Quem tem uma lista ou uma ficha aberta vai buscar o que mudou. Vários avisos seguidos
// juntam-se num só pedido; quando a ligação volta depois de cair, recarrega (pode ter perdido avisos); sem ligação,
// verifica de 20 em 20 s.
//   • encomendas e entregas (backend utils/tempo_real_encomendas.py): { id, loja_id }
//   • mensalidades, subscrições e faturas da Bendi (utils/tempo_real_subscricoes.py): { tipo, id, loja_id, pos_id }
//   • faturas das vendas e vendas que passam a faturáveis (utils/tempo_real_faturacao.py): { origem, id, loja_id, pos_id }
//     (as comissões, créditos e cobranças de comissões vão pelas subscrições: { tipo: comissao|credito_comissao|cobranca_comissoes })
//   • números da plataforma — Dashboard e Relatórios do admin (utils/tempo_real_painel.py): { origem }
//   • listas — Produtos/Inventário da loja e Lojas, Produtos, Catálogo, Encomendas, Utilizadores, POS, Denúncias do admin
//     (utils/tempo_real_listas.py): { origem, loja_id }
import { EVENTO_RELIGADO } from '@/composables/useTempoRealReembolsos'

export const EVENTO_ENCOMENDA = 'bendi:encomenda'
export const EVENTO_SUBSCRICAO = 'bendi:subscricao'
export const EVENTO_FATURACAO = 'bendi:faturacao'
export const EVENTO_PAINEL = 'bendi:painel'
export const EVENTO_LISTA = 'bendi:lista'
const SEM_LIGACAO_MS = 20000

// fn(aviso | null) — null quando é para recarregar tudo (avisos diferentes juntos, religou, sem ligação).
// semSocket: páginas sem o sino (POS) — verificam sempre de 20 em 20 s enquanto visíveis.
// maximo: com avisos sem parar (muitas vendas), recarrega pelo menos a cada `maximo` ms. Devolve a função para parar.
// ligado / religado: outra ligação que não a do sino (o POS tem a sua — utils/tempoRealPOS.js).
export function ouvirAvisos (evento, fn, { filtro = () => true, espera = 400, maximo = 0, semSocket = false,
                                         ligado = () => window.bendiTempoReal, religado = EVENTO_RELIGADO } = {}) {
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
  window.addEventListener(religado, aoReligar)
  const recurso = setInterval(() => {
    if ((semSocket || !ligado()) && document.visibilityState === 'visible') fn(null)
  }, SEM_LIGACAO_MS)
  return () => {
    clearTimeout(temporizador)
    clearInterval(recurso)
    window.removeEventListener(evento, aoAviso)
    window.removeEventListener(religado, aoReligar)
  }
}

export function ouvirEncomendas (fn, opcoes) { return ouvirAvisos(EVENTO_ENCOMENDA, fn, opcoes) }
export function ouvirSubscricoes (fn, opcoes) { return ouvirAvisos(EVENTO_SUBSCRICAO, fn, opcoes) }
export function ouvirFaturacao (fn, opcoes) { return ouvirAvisos(EVENTO_FATURACAO, fn, opcoes) }
// origens: uma ou várias ('produto', 'inventario', 'loja', 'utilizador', 'pos', 'encomenda', 'denuncia', 'cartao');
// lojaId: só os avisos dessa loja. Com muitos avisos seguidos (vendas), recarrega no máximo de 5 em 5 s.
export function ouvirListas (origens, fn, { lojaId = null, ...opcoes } = {}) {
  const lista = [].concat(origens)
  const filtro = a => lista.includes(a.origem) && (lojaId == null || String(a.loja_id) === String(lojaId))
  return ouvirAvisos(EVENTO_LISTA, fn, { espera: 800, maximo: 5000, filtro, ...opcoes })
}
export function ouvirPainel (fn, opcoes) { return ouvirAvisos(EVENTO_PAINEL, fn, { espera: 1500, maximo: 6000, ...opcoes }) }
