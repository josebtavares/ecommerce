// Tempo real do POS: uma ligação ws/pos/ por página do POS (o POSDashboard liga e desliga). O servidor
// (backend utils/tempo_real_pos.py) manda avisos só com ids — { tipo, id, ... } — e cada aba vai buscar o que mudou:
//   • mesa {id}            — aberta, fechada, em limpeza, criada/removida
//   • conta {id, mesa_id, status} — itens, cozinha, pagamento, desconto, cobrada, cancelada
//   • turno {id}           — caixa aberta/fechada, movimentos
//   • produto {id}         — produto/stock/variantes/menus (também os da loja ligada)
//   • equipa {id}          — membro criado, mudado (permissões, papel), desactivado
//   • pos {id}             — definições do POS, suspensão
//   • faturacao / subscricao {id} — faturas das vendas, mensalidades
// Sem ligação (a ligar, rede, servidor sem Redis) cada aba verifica sozinha de 20 em 20 s; quando volta a ligar
// recarrega (pode ter perdido avisos).
import api, { urlWebSocket, verAdminPOS } from '@/services/api'
import { ouvirAvisos } from '@/utils/tempoRealEncomendas'

export const EVENTO_POS = 'bendi:pos'
export const EVENTO_POS_RELIGADO = 'bendi:pos-religado'
export const EVENTO_POS_SEM_ACESSO = 'bendi:pos-sem-acesso'

let ws = null
let posLigado = null      // POS desta ligação
let parado = true
let jaLigou = false
let tentativas = 0
let temporizador = null
let ping = null
let aLigar = false

function marcar (ligado) { window.bendiTempoRealPOS = ligado }

async function bilhete (posId) {
  // o admin a ver tem um token só de leitura: pede o bilhete com GET
  const pedido = verAdminPOS() ? api.get : api.post
  const { data } = await pedido(`/api/pos/${posId}/ws/bilhete/`)
  return data.bilhete
}

async function abrir () {
  if (parado || aLigar || (ws && ws.readyState <= WebSocket.OPEN)) return
  const posId = posLigado
  aLigar = true
  let url = null
  try {
    url = urlWebSocket(`pos/?bilhete=${encodeURIComponent(await bilhete(posId))}`)
  } catch {
    url = null          // sem bilhete (rede, sessão a renovar): tenta mais tarde
  } finally {
    aLigar = false
  }
  if (parado || posId !== posLigado) return
  if (!url) { religarMaisTarde(); return }
  const socket = new WebSocket(url)
  ws = socket

  socket.onopen = () => {
    marcar(true)
    if (jaLigou) window.dispatchEvent(new CustomEvent(EVENTO_POS_RELIGADO))
    jaLigou = true
    tentativas = 0
    clearInterval(ping)
    ping = setInterval(() => { if (socket.readyState === WebSocket.OPEN) socket.send('ping') }, 45000)
  }

  socket.onmessage = (e) => {
    if (e.data === 'pong') return
    try {
      const msg = JSON.parse(e.data)
      if (msg.type === 'avisos') {
        for (const aviso of msg.avisos || []) window.dispatchEvent(new CustomEvent(EVENTO_POS, { detail: aviso }))
      } else if (msg.type === 'sem_acesso') {
        window.dispatchEvent(new CustomEvent(EVENTO_POS_SEM_ACESSO))
      }
    } catch { /* silencioso */ }
  }

  socket.onclose = (e) => {
    if (ws === socket) { ws = null; marcar(false) }
    clearInterval(ping)
    if (parado || e.code === 1000) return
    // 4003: este membro deixou de ter acesso (desactivado/removido) — a página termina a sessão
    if (e.code === 4003) { window.dispatchEvent(new CustomEvent(EVENTO_POS_SEM_ACESSO)); return }
    religarMaisTarde()
  }
  socket.onerror = () => { socket.close() }
}

function religarMaisTarde () {
  const espera = Math.min(1000 * 2 ** tentativas, 30000)
  tentativas = Math.min(tentativas + 1, 6)
  clearTimeout(temporizador)
  temporizador = setTimeout(abrir, espera)
}

// liga ao POS (troca de POS → fecha a anterior)
export function ligarPOS (posId) {
  if (!posId) return
  if (posLigado !== posId) desligarPOS()
  posLigado = posId
  parado = false
  abrir()
}

export function desligarPOS () {
  parado = true
  posLigado = null
  jaLigou = false
  tentativas = 0
  clearTimeout(temporizador)
  clearInterval(ping)
  marcar(false)
  if (ws) { const s = ws; ws = null; s.close(1000) }
}

// voltou a aparecer o separador / a rede: se caiu, tenta já
export function acordarPOS () {
  if (!parado && !ws) { tentativas = 0; clearTimeout(temporizador); abrir() }
}

// fn(aviso | null) quando chega um aviso de um dos `tipos` (null = recarregar tudo). Devolve a função para parar.
export function ouvirPOS (tipos, fn, { filtro = () => true, ...opcoes } = {}) {
  const lista = Array.isArray(tipos) ? tipos : [tipos]
  return ouvirAvisos(EVENTO_POS, fn, {
    ...opcoes,
    filtro: (a) => lista.includes(a.tipo) && filtro(a),
    ligado: () => Boolean(window.bendiTempoRealPOS),
    religado: EVENTO_POS_RELIGADO,
  })
}
