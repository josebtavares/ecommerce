import api from '@/services/api'

// Confirmação do email (backend: utils/confirmar_email.py). O estado vive no `user` do localStorage
// (email_confirmado); quem o muda avisa com o evento EVENTO para o aviso do App.vue se actualizar.

export const EVENTO = 'bende:utilizador'

export function utilizadorGuardado () {
  try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null }
}

// só as contas que o backend diz estarem por confirmar (as antigas sem o campo não contam)
export function emailPorConfirmar () {
  return !!localStorage.getItem('access_token') && utilizadorGuardado()?.email_confirmado === false
}

export function atualizarGuardado (campos) {
  const u = utilizadorGuardado()
  if (!u) return
  localStorage.setItem('user', JSON.stringify({ ...u, ...campos }))
  window.dispatchEvent(new CustomEvent(EVENTO))
}

// o backend respondeu 403 codigo email_por_confirmar (encomendar, marcar, criar loja)
export function porConfirmar (erro) {
  if (erro?.response?.data?.codigo !== 'email_por_confirmar') return false
  atualizarGuardado({ email_confirmado: false })
  return true
}

// a conta como está no servidor: o `user` guardado é uma cópia do login e o admin pode ter mudado
// a conta entretanto (verificar, dar acesso…) ou o link do email ter sido aberto noutro browser
export async function atualizarDoServidor () {
  const { data } = await api.get('/app/utilizador/me/')
  // outra conta: saiu e entrou entretanto, ou o admin a ver um backoffice em modo de leitura
  if (data.id === utilizadorGuardado()?.id) atualizarGuardado(data)
  return data.email_confirmado
}

// uma vez por visita (App.vue; o router espera por ela nas páginas com meta.contaAtual)
let leitura = null
export function lerConta () {
  if (!leitura) leitura = atualizarDoServidor().catch(() => {})
  return leitura
}

// sem deixar a página presa se o servidor demorar
export function esperarConta (limite = 3000) {
  return Promise.race([lerConta(), new Promise(resolve => setTimeout(resolve, limite))])
}

export function reenviarLink () {
  return api.post('/app/utilizador/confirmar_email/reenviar/')
}

export function confirmarLink (token) {
  return api.post('/app/utilizador/confirmar_email/', { token })
}
