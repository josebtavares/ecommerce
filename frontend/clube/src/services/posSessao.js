import { POS_ACCESS, POS_REFRESH } from '@/services/api'

// Sessão da conta principal (dono) do POS — usada pelo login, registo e login com Google
export function guardarSessaoPrincipalPOS (data) {
  const lojas = Array.isArray(data.lojas) ? data.lojas : []
  const posExistentes = Array.isArray(data.pos_existentes) ? data.pos_existentes : []
  const selectedPOS = posExistentes.length > 0 ? posExistentes[0] : null

  const precisaOnboarding = Boolean(
    data.precisa_onboarding || posExistentes.length === 0
  )

  // Sessão do POS — chaves próprias: a sessão Bendi (access_token/user) não é tocada
  localStorage.setItem(POS_ACCESS, data.access_token)
  localStorage.setItem(POS_REFRESH, data.refresh_token)
  localStorage.setItem('tipo_sessao', 'principal')

  // User POS
  localStorage.setItem('pos_user', JSON.stringify(data.user || null))

  // Dados do POS
  localStorage.setItem('pos_lojas', JSON.stringify(lojas))
  localStorage.setItem('pos_existentes', JSON.stringify(posExistentes))
  localStorage.setItem('pos_tem_lojas', data.tem_lojas ? 'true' : 'false')
  localStorage.setItem('pos_precisa_onboarding', precisaOnboarding ? 'true' : 'false')

  localStorage.setItem(
    'pos_onboarding_data',
    JSON.stringify({
      tem_lojas: Boolean(data.tem_lojas),
      lojas,
      pos_existentes: posExistentes,
      precisa_onboarding: precisaOnboarding,
      mensagem: data.mensagem || ''
    })
  )

  if (data.permissoes) {
    localStorage.setItem('pos_permissoes', JSON.stringify(data.permissoes))
  } else {
    localStorage.removeItem('pos_permissoes')
  }

  // Se já existe POS, selecionar o primeiro automaticamente
  if (selectedPOS) {
    localStorage.setItem('pos_selected', JSON.stringify(selectedPOS))
    localStorage.setItem('pos_id', String(selectedPOS.id))
    localStorage.setItem('pos_precisa_onboarding', 'false')
  } else {
    localStorage.removeItem('pos_selected')
    localStorage.removeItem('pos_id')
  }

  // Limpar dados de sessão de membro anterior
  localStorage.removeItem('pos_membro')
  localStorage.removeItem('pos_membro_pos')
  localStorage.removeItem('pos_membro_permissoes')
}

// para onde ir depois de entrar no POS
export function destinoPOS (data) {
  const posExistentes = Array.isArray(data.pos_existentes) ? data.pos_existentes : []
  return data.precisa_onboarding && posExistentes.length === 0
    ? '/pos/dashboard?onboarding=1'
    : '/pos/dashboard'
}
