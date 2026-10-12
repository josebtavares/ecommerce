import api from '@/services/api'

// Login com Google — Bendi e POS usam o mesmo redirect (/auth/google/callback).
// O `state` leva o destino e um valor aleatório: o callback só aceita o state que este
// separador gerou (protege contra CSRF no login) e sabe para onde voltar.
const CHAVE = 'google_oauth_state'
const CHAVE_SEGUINTE = 'google_oauth_seguinte'

// lê (e apaga) a página para onde voltar — o chamador valida com caminhoSeguro()
export function seguinteGoogle () {
  const s = sessionStorage.getItem(CHAVE_SEGUINTE) || ''
  sessionStorage.removeItem(CHAVE_SEGUINTE)
  return s
}

// `seguinte`: página para onde voltar depois de entrar (ex.: a loja onde se ia encomendar)
export async function iniciarLoginGoogle (destino = 'bendi', seguinte = '') {
  const aleatorio = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('')
  const state = `${destino}.${aleatorio}`
  sessionStorage.setItem(CHAVE, state)
  if (seguinte) sessionStorage.setItem(CHAVE_SEGUINTE, seguinte)
  else sessionStorage.removeItem(CHAVE_SEGUINTE)

  const { data } = await api.get('/app/utilizador/google/', { params: { state } })
  window.location.href = data.url
}

// devolve o destino ('bendi' | 'pos') se o state for o que este separador gerou; senão null
export function validarStateGoogle (stateRecebido) {
  const esperado = sessionStorage.getItem(CHAVE)
  sessionStorage.removeItem(CHAVE)
  if (!esperado || esperado !== stateRecebido) return null
  return esperado.split('.')[0]
}
