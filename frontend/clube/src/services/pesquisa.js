// Barra de pesquisa (backend: utils/pesquisa.py, GET /app/pesquisa/).
//  · procurar(q, opcoes)  → resultados; cancela o pedido anterior ainda a correr e guarda os últimos 30 (60 s)
//  · recentes / guardarRecente / limparRecentes → pesquisas recentes, só neste browser
import api from '@/services/api'

const MEMORIA_MS = 60 * 1000
const memoria = new Map()            // chave → { quando, dados }
let emCurso = null

export const MIN_LETRAS = 2

export function normalizar (t) {
  return String(t || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

export async function procurar (q, { tipo = '', offset = 0, limit = 0, filtros = {}, ordem = '' } = {}) {
  const params = { q: q.trim() }
  if (tipo) params.tipo = tipo
  if (offset) params.offset = offset
  if (limit) params.limit = limit
  if (ordem) params.ordem = ordem
  for (const [k, v] of Object.entries(filtros)) if (v !== '' && v != null) params[k] = v
  const chave = JSON.stringify(params)
  const guardado = memoria.get(chave)
  if (guardado && Date.now() - guardado.quando < MEMORIA_MS) return guardado.dados
  if (!tipo && emCurso) emCurso.abort()        // a lista enquanto se escreve: só interessa a última
  const controlo = new AbortController()
  if (!tipo) emCurso = controlo
  const { data } = await api.get('/app/pesquisa/', { params, signal: controlo.signal })
  if (emCurso === controlo) emCurso = null
  memoria.set(chave, { quando: Date.now(), dados: data })
  if (memoria.size > 30) memoria.delete(memoria.keys().next().value)
  return data
}

export function foiCancelado (e) {
  return e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED'
}

// ── pesquisas recentes (localStorage pode falhar: janela privada, bloqueado) ──
const RECENTES = 'pesquisas_recentes'

export function recentes () {
  try { return JSON.parse(localStorage.getItem(RECENTES) || '[]').slice(0, 6) } catch { return [] }
}

export function guardarRecente (q) {
  q = String(q || '').trim()
  if (q.length < MIN_LETRAS) return
  try {
    const lista = [q, ...recentes().filter(x => normalizar(x) !== normalizar(q))].slice(0, 6)
    localStorage.setItem(RECENTES, JSON.stringify(lista))
  } catch { /* sem armazenamento: não guarda */ }
}

export function limparRecentes () {
  try { localStorage.removeItem(RECENTES) } catch { /* nada */ }
}

// destaca o que se escreveu: devolve pedaços [{ t, m }] (m = corresponde), sem acentos dos dois lados
export function destacar (texto, q) {
  texto = String(texto || '')
  const palavras = normalizar(q).split(/[^a-z0-9]+/).filter(p => p.length >= 2)
  if (!palavras.length) return [{ t: texto, m: false }]
  const base = normalizar(texto)
  const marca = new Array(texto.length).fill(false)
  // normalize NFKD mantém o comprimento em letras latinas comuns; se não, não destaca
  if (base.length !== texto.length) return [{ t: texto, m: false }]
  for (const p of palavras) {
    let i = base.indexOf(p)
    while (i !== -1) {
      if (i === 0 || /[^a-z0-9]/.test(base[i - 1])) for (let k = i; k < i + p.length; k++) marca[k] = true
      i = base.indexOf(p, i + 1)
    }
  }
  const out = []
  for (let i = 0; i < texto.length; i++) {
    if (out.length && out[out.length - 1].m === marca[i]) out[out.length - 1].t += texto[i]
    else out.push({ t: texto[i], m: marca[i] })
  }
  return out
}

// para onde vai cada resultado
export function destino (tipo, r) {
  if (tipo === 'loja') return `/loja/${r.id}`
  if (tipo === 'produto') return { path: `/loja/${r.loja.id}`, query: { produto: r.id } }
  if (tipo === 'servico') return { path: `/loja/${r.loja.id}`, query: { servico: r.id } }
  if (tipo === 'categoria') return { path: '/Home', query: { categoria: r.valor } }   // a home filtra o catálogo
  return { path: '/pesquisa', query: { q: r } }
}
