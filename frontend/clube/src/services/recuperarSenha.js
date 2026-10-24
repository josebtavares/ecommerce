import api from '@/services/api'
import { passwordValida } from '@/utils/password'

// Recuperar password — usado pela Bendi (views/RecuperarSenha.vue) e pelo POS (views/pos/POSRecuperarSenha.vue).
// `destino` 'pos' faz o link do email abrir /pos/recuperar_senha em vez de /recuperar_senha.

export function pedirLinkRecuperacao (email, destino = 'bendi') {
  return api.post('/app/utilizador/recuperar_senha/', { email, destino })
}

export function definirPasswordNova (uid, token, password) {
  return api.post('/app/utilizador/recuperar_senha/confirmar/', { uid, token, new_password: password })
}

// mensagem do backend: {detail} ou {campo: [erros]}
export function mensagemErroRecuperacao (err, padrao) {
  const d = err.response?.data
  if (err.response?.status === 429) return d?.detail || 'Demasiados pedidos. Tenta novamente mais tarde.'
  if (d?.detail) return d.detail
  const primeiro = d && typeof d === 'object' ? Object.values(d)[0] : null
  return (Array.isArray(primeiro) ? primeiro[0] : primeiro) || padrao
}

// erro a mostrar antes de enviar a password nova, ou '' se estiver tudo bem
export function erroPasswordNova (password, confirmacao) {
  if (!passwordValida(password)) return 'A password não cumpre todos os requisitos de segurança.'
  if (password !== confirmacao) return 'As passwords não coincidem.'
  return ''
}
