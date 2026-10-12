import { reactive } from 'vue'

// Sessão da Bendi no site público (sem login obrigatório).
// Ver é livre; encomendar, carrinho e avaliar pedem conta — o servidor é que garante isso,
// isto só serve para a interface não tentar e para mostrar o convite a entrar.

export function estaAutenticado () {
  return !!localStorage.getItem('access_token')
}

// só caminhos internos (nunca "//site" ou "https://…") — evita redirecionar para fora do site
export function caminhoSeguro (s, alternativa = '/Home') {
  return typeof s === 'string' && s.startsWith('/') && !s.startsWith('//') && !s.startsWith('/\\')
    ? s
    : alternativa
}

export function caminhoAtual () {
  return window.location.pathname + window.location.search
}

// Modal "Entra ou cria conta" — um só, montado no App.vue (components/auth/PedirLogin.vue)
export const pedidoLogin = reactive({
  aberto: false,
  mensagem: '',
  seguinte: '/Home',
})

export function pedirLogin (mensagem = 'Entra ou cria conta para continuar.', seguinte = caminhoAtual()) {
  pedidoLogin.mensagem = mensagem
  pedidoLogin.seguinte = caminhoSeguro(seguinte)
  pedidoLogin.aberto = true
}

export function fecharPedidoLogin () {
  pedidoLogin.aberto = false
}
