import api from '@/services/api'

// Login com Google — Bendi e POS usam o mesmo redirect (/auth/google/callback).
// O `state` leva o destino e um valor aleatório: o callback só aceita o state que este
// separador gerou (protege contra CSRF no login) e sabe para onde voltar.
const CHAVE = 'google_oauth_state'

export async function iniciarLoginGoogle (destino = 'bendi') {
  const aleatorio = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('')
  const state = `${destino}.${aleatorio}`
  sessionStorage.setItem(CHAVE, state)

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
