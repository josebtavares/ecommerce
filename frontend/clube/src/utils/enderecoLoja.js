// Endereço público das lojas: /loja/<slug> (ex.: /loja/bom-sabor). Backend: utils/endereco_loja.py.
// /loja/<id> e os endereços antigos continuam a funcionar: o router (router.js) resolve-os e troca o endereço.
// O backoffice continua em /loja/<id>/backoffice.
import api from '@/services/api'

const resolvidos = new Map()   // 'bom-sabor' | '7' | endereço antigo → { id, slug }
const NUMERO = /^\d+$/

// /loja/<slug> (ou /loja/<id> se o objecto não trouxer o slug — o router corrige o endereço depois)
export function caminhoLoja (loja, query) {
  const ref = loja && typeof loja === 'object' ? (loja.slug || loja.id) : loja
  const path = `/loja/${ref}`
  return query && Object.keys(query).length ? { path, query } : path
}

// href absoluto/relativo com query em texto (para <a href> e partilhas)
export function hrefLoja (loja, query) {
  const c = caminhoLoja(loja)
  const q = new URLSearchParams(Object.entries(query || {}).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString()
  return q ? `${c}?${q}` : c
}

// id numérico da loja a partir do parâmetro da rota (já resolvido pelo router); null se não existe
export function idDaLoja (ref) {
  const r = String(ref ?? '')
  if (NUMERO.test(r)) return r
  return resolvidos.get(r.toLowerCase())?.id?.toString() ?? null
}

// pede ao backend { id, slug } (com cache); null se a loja não existe ou não é visível
export async function resolverLoja (ref) {
  const r = String(ref ?? '').toLowerCase()
  if (!r) return null
  if (resolvidos.has(r)) return resolvidos.get(r)
  try {
    const { data } = await api.get(`/app/loja/endereco/${encodeURIComponent(r)}/`)
    const v = { id: data.id, slug: data.slug }
    resolvidos.set(r, v)
    resolvidos.set(data.slug, v)
    return v
  } catch {
    return null
  }
}

// o dono mudou o endereço: esquece o que estava em cache
export function esquecerLoja (...refs) {
  for (const r of refs) if (r !== undefined && r !== null) resolvidos.delete(String(r).toLowerCase())
}
