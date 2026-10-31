// Chat — estado partilhado, API (/api/chat/) e um único WebSocket (/ws/chat/).
// Usado pelo balão flutuante (ChatFlutuante), pela página /mensagens e pelos atalhos
// "Perguntar à loja", "Falar sobre esta encomenda" e "Contactar suporte".
// O servidor aplica todas as regras; aqui só se mostra o que a API devolve.
import { reactive } from 'vue'
import api, { urlWebSocketComBilhete } from '@/services/api'
import { estaAutenticado, pedirLogin } from '@/services/sessao'

export const chat = reactive({
  pronto: false,
  aberto: false,               // janela flutuante
  caixas: [],                  // [{caixa_id, tipo, nome, foto, nao_lidas, restrita}]
  caixaId: null,               // caixa seleccionada na lista
  conversas: [],
  totalConversas: 0,
  conversa: null,              // conversa aberta
  mensagens: [],
  maisAntigas: false,
  aCarregar: false,
  aEnviar: false,
  erro: '',
  produtoPendente: null,       // cartão de produto a juntar à próxima mensagem
  aEscrever: {},               // conversa_id → { nome, ate }
  pesquisa: '',
  filtroTipo: '',
  filtroLoja: null,            // conversas de uma loja (ex.: equipa no backoffice)
  filtroEstado: '',            // suporte: aberta | fechada
  painelEmbutido: false,       // o backoffice/admin mostra o painel — o balão esconde-se
})

export const totalNaoLidas = () => chat.caixas.reduce((s, c) => s + (c.nao_lidas || 0), 0)

// ── API ──────────────────────────────────────────────────────────
export async function carregarCaixas () {
  if (!estaAutenticado()) return
  const { data } = await api.get('/api/chat/caixas/')
  chat.caixas = data
  if (!chat.caixaId || !data.some(c => c.caixa_id === chat.caixaId)) {
    chat.caixaId = data[0]?.caixa_id || null
  }
}

export async function carregarConversas () {
  if (!chat.caixaId) return
  const params = { caixa: chat.caixaId, limit: 50 }
  if (chat.pesquisa.trim()) params.q = chat.pesquisa.trim()
  if (chat.filtroTipo) params.tipo = chat.filtroTipo
  if (chat.filtroLoja) params.loja = chat.filtroLoja
  if (chat.filtroEstado) params.estado = chat.filtroEstado
  const { data } = await api.get('/api/chat/conversas/', { params })
  chat.conversas = data.results
  chat.totalConversas = data.count
}

export async function escolherCaixa (caixaId) {
  chat.caixaId = caixaId
  chat.conversa = null
  chat.mensagens = []
  chat.filtroTipo = ''
  await carregarConversas()
}

export async function abrirConversa (conversa) {
  chat.conversa = conversa
  chat.mensagens = []
  chat.maisAntigas = false
  chat.erro = ''
  await carregarMensagens()
  marcarLida()
}

export function fecharConversa () {
  chat.conversa = null
  chat.mensagens = []
  chat.produtoPendente = null
}

export async function carregarMensagens (antigas = false) {
  const c = chat.conversa
  if (!c) return
  chat.aCarregar = true
  try {
    const params = { caixa: c.caixa_id, limit: 40 }
    if (antigas && chat.mensagens.length) params.antes = chat.mensagens[0].id
    const { data } = await api.get(`/api/chat/conversas/${c.id}/mensagens/`, { params })
    if (chat.conversa?.id !== c.id) return
    chat.mensagens = antigas ? [...data.results, ...chat.mensagens] : data.results
    chat.maisAntigas = data.mais_antigas
  } finally {
    chat.aCarregar = false
  }
}

async function buscarNovas (conversaId) {
  const c = chat.conversa
  if (!c || c.id !== conversaId) return
  const ultima = chat.mensagens[chat.mensagens.length - 1]?.id || 0
  const { data } = await api.get(`/api/chat/conversas/${c.id}/mensagens/`, {
    params: { caixa: c.caixa_id, depois: ultima },
  })
  if (chat.conversa?.id !== c.id) return
  for (const m of data.results) {
    if (!chat.mensagens.some(x => x.id === m.id)) chat.mensagens.push(m)
  }
}

export async function enviar (texto, imagem = null) {
  const c = chat.conversa
  if (!c || chat.aEnviar) return false
  chat.aEnviar = true
  chat.erro = ''
  try {
    let corpo = { caixa: c.caixa_id, texto }
    if (chat.produtoPendente) corpo.produto_id = chat.produtoPendente.id
    if (imagem) {
      const fd = new FormData()
      Object.entries(corpo).forEach(([k, v]) => fd.append(k, v))
      fd.append('imagem', imagem)
      corpo = fd
    }
    const { data } = await api.post(`/api/chat/conversas/${c.id}/mensagens/`, corpo)
    if (!chat.mensagens.some(x => x.id === data.id)) chat.mensagens.push(data)
    chat.produtoPendente = null
    actualizarNaLista(c.id, data)
    return true
  } catch (e) {
    chat.erro = e.response?.data?.detail || 'Não foi possível enviar.'
    return false
  } finally {
    chat.aEnviar = false
  }
}

export async function marcarLida () {
  const c = chat.conversa
  if (!c || !chat.mensagens.length) return
  try {
    await api.post(`/api/chat/conversas/${c.id}/lida/`, { caixa: c.caixa_id })
    const item = chat.conversas.find(x => x.id === c.id)
    if (item) item.nao_lidas = 0
    carregarCaixas()
  } catch { /* silencioso */ }
}

export async function apagarMensagem (m) {
  await api.post(`/api/chat/mensagens/${m.id}/apagar/`)
  Object.assign(m, { apagada: true, texto: '', anexo: null, produto: null })
}

export async function denunciar (motivo, mensagemId = null) {
  const c = chat.conversa
  await api.post('/api/chat/denuncias/', { caixa: c.caixa_id, conversa_id: c.id, mensagem_id: mensagemId, motivo })
}

export async function bloquear (sim) {
  const c = chat.conversa
  await api.post(`/api/chat/conversas/${c.id}/bloquear/`, { caixa: c.caixa_id, bloquear: sim })
}

export async function mudarEstado (estado) {
  const c = chat.conversa
  const { data } = await api.post(`/api/chat/conversas/${c.id}/estado/`, { caixa: c.caixa_id, estado })
  c.estado = data.estado
}

export async function pesquisarContactos (q, tipo = '') {
  if (!chat.caixaId || q.trim().length < 2) return []
  const { data } = await api.get('/api/chat/contactos/', { params: { caixa: chat.caixaId, q, tipo } })
  return data.results
}

function actualizarNaLista (conversaId, mensagem) {
  const i = chat.conversas.findIndex(x => x.id === conversaId)
  if (i < 0) return
  const item = chat.conversas[i]
  item.ultima_mensagem = mensagem
  item.ultima_mensagem_em = mensagem.criada_em
  chat.conversas.splice(i, 1)
  chat.conversas.unshift(item)
}

// ── Abrir conversa a partir de outros sítios do site ─────────────
async function abrirComDestino (corpo, mensagemLogin) {
  if (!estaAutenticado()) {
    pedirLogin(mensagemLogin)
    return false
  }
  if (!chat.pronto) await iniciarChat()
  const pessoal = chat.caixas.find(c => c.tipo === 'pessoal')
  if (!pessoal) return false
  try {
    const { data } = await api.post('/api/chat/conversas/', { caixa: pessoal.caixa_id, ...corpo })
    chat.caixaId = pessoal.caixa_id
    await carregarConversas()
    chat.aberto = true
    await abrirConversa(data)
    return true
  } catch (e) {
    chat.aberto = true
    chat.erro = e.response?.data?.detail || 'Não foi possível abrir a conversa.'
    return false
  }
}

export async function contactarLoja (lojaId, { produto = null, encomendaId = null } = {}) {
  const ok = await abrirComDestino(
    { destino: 'loja', destino_id: lojaId, encomenda_id: encomendaId },
    'Entra ou cria conta para falares com a loja.',
  )
  if (ok && produto) chat.produtoPendente = produto
  return ok
}

// condutor (ou quem atende a loja): a conversa da encomenda com o cliente, pela caixa da loja
export async function contactarCliente (lojaId, compradorId, encomendaId) {
  if (!chat.pronto) await iniciarChat()
  const caixa = chat.caixas.find(c => c.tipo === 'loja' && String(c.loja_id) === String(lojaId))
  chat.aberto = true
  if (!caixa) {
    chat.erro = 'Não tens acesso às mensagens desta loja.'
    return false
  }
  try {
    const { data } = await api.post('/api/chat/conversas/', {
      caixa: caixa.caixa_id, destino: 'utilizador', destino_id: compradorId, encomenda_id: encomendaId,
    })
    chat.caixaId = caixa.caixa_id
    await carregarConversas()
    await abrirConversa(data)
    return true
  } catch (e) {
    chat.erro = e.response?.data?.detail || 'Não foi possível abrir a conversa.'
    return false
  }
}

export function contactarSuporte () {
  return abrirComDestino({ destino: 'suporte' }, 'Entra ou cria conta para falares com o suporte.')
}

export async function iniciarConversaCom (contacto) {
  // a partir da pesquisa de contactos da caixa seleccionada
  const corpo = contacto.tipo === 'loja'
    ? { destino: 'loja', destino_id: contacto.id }
    : { destino: 'utilizador', destino_id: contacto.id }
  const { data } = await api.post('/api/chat/conversas/', { caixa: chat.caixaId, ...corpo })
  await carregarConversas()
  await abrirConversa(data)
}

// ── Tempo real ───────────────────────────────────────────────────
let ws = null
let tentativas = 0
let temporizador = null
let ultimoEscrever = 0
let desligado = false
let refrescar = null


// sem WebSocket (rede, proxy…), o chat aberto vai buscar novidades de 10 em 10 s
let sondagem = null
function sondarSemWs () {
  if (sondagem) return
  sondagem = setInterval(async () => {
    if (ws && ws.readyState === WebSocket.OPEN) { clearInterval(sondagem); sondagem = null; return }
    if (!chat.aberto && window.location.pathname !== '/mensagens') return
    if (chat.conversa) await buscarNovas(chat.conversa.id).catch(() => {})
    refrescarListas()
  }, 10000)
}

function refrescarListas () {
  clearTimeout(refrescar)
  refrescar = setTimeout(() => {
    carregarCaixas().catch(() => {})
    carregarConversas().catch(() => {})
  }, 300)
}

async function aoEvento (ev) {
  switch (ev.tipo) {
    case 'mensagem_nova':
      if (chat.conversa?.id === ev.conversa_id) {
        await buscarNovas(ev.conversa_id)
        if (chat.aberto || window.location.pathname === '/mensagens') marcarLida()
      }
      refrescarListas()
      break
    case 'lida':
      if (chat.conversa?.id === ev.conversa_id && ev.caixa_id !== chat.conversa.caixa_id) {
        chat.mensagens.forEach(m => { if (m.minha && m.id <= ev.ultima_lida) m.lida = true })
      }
      refrescarListas()
      break
    case 'a_escrever':
      chat.aEscrever = { ...chat.aEscrever, [ev.conversa_id]: { nome: ev.nome, ate: Date.now() + 3500 } }
      break
    case 'mensagem_apagada': {
      const m = chat.mensagens.find(x => x.id === ev.mensagem_id)
      if (m) Object.assign(m, { apagada: true, texto: '', anexo: null, produto: null })
      refrescarListas()
      break
    }
    case 'conversa_atualizada':
      refrescarListas()
      break
  }
}

let aLigar = false
async function ligarWs () {
  if (desligado || !estaAutenticado() || aLigar) return
  if (ws && ws.readyState <= WebSocket.OPEN) return
  aLigar = true
  const url = await urlWebSocketComBilhete('chat/').finally(() => { aLigar = false })
  if (desligado || (ws && ws.readyState <= WebSocket.OPEN)) return
  const socket = new WebSocket(url)
  ws = socket
  socket.onopen = () => { tentativas = 0 }
  socket.onmessage = (e) => {
    try { aoEvento(JSON.parse(e.data)) } catch { /* silencioso */ }
  }
  socket.onclose = (e) => {
    if (ws === socket) ws = null
    if (desligado || e.code === 1000) return
    sondarSemWs()
    // token expirado chega como 1006: o pedido HTTP renova-o (interceptor) antes de religar
    const atraso = Math.min(1000 * 2 ** tentativas, 30000)
    tentativas = Math.min(tentativas + 1, 6)
    clearTimeout(temporizador)
    temporizador = setTimeout(async () => {
      await carregarCaixas().catch(() => {})
      ligarWs()
    }, atraso)
  }
  socket.onerror = () => socket.close()
}

export function avisarAEscrever () {
  const c = chat.conversa
  if (!c || !ws || ws.readyState !== WebSocket.OPEN) return
  if (Date.now() - ultimoEscrever < 2500) return
  ultimoEscrever = Date.now()
  ws.send(JSON.stringify({ tipo: 'a_escrever', conversa_id: c.id, caixa_id: c.caixa_id }))
}

export async function iniciarChat () {
  if (!estaAutenticado()) return
  desligado = false
  await carregarCaixas().catch(() => {})
  chat.pronto = true
  ligarWs()
}

export function pararChat () {
  desligado = true
  clearTimeout(temporizador)
  clearInterval(sondagem)
  sondagem = null
  if (ws) ws.close(1000)
  ws = null
}
