// Documentos em PDF gerados no servidor (backend app/utils/documentos.py) e ficheiros de faturas registadas
import api from '@/services/api'

export async function descarregarPdf (url, nome, params = {}) {
  const r = await api.get(url, { responseType: 'blob', params })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(r.data)
  a.download = nome
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 10000)
}

// comprovativo de uma mensalidade paga (loja, POS ou admin)
export function descarregarComprovativoSubscricao (f) {
  return descarregarPdf(`/app/subscricao/faturas/${f.id}/comprovativo/`, `comprovativo-subscricao-${f.id}.pdf`)
}

export function descarregarComprovativoEncomenda (id) {
  return descarregarPdf(`/app/encomenda/${id}/comprovativo/`, `comprovativo-encomenda-${id}.pdf`)
}

// em dev os ficheiros vêm como /media/…; em produção já são URLs completos (R2)
export function urlFicheiro (u) {
  if (!u) return ''
  return /^https?:/.test(u) ? u : `${process.env.VUE_APP_URL_BASE || ''}${u}`
}
