// Listas com "Ver mais" (encomendas, marcações e reembolsos do cliente): o tempo real recarrega o que já está
// mostrado. O servidor dá no máximo 100 de cada vez (utils/pagination.py MAX_LIMIT), por isso com mais de 100
// abertas vai buscar por partes — a lista nunca encolhe por causa de um aviso.
import api from '@/services/api'

const MAX = 100

// GET url com params + offset/limit até ter `quantos` (pelo menos `minimo`). Devolve { results, count }.
export async function recarregarMostradas (url, params, quantos, minimo = 20) {
  const alvo = Math.max(quantos, minimo)
  const results = []
  let count = 0
  for (let offset = 0; offset < alvo; offset += MAX) {
    const { data } = await api.get(url, { params: { ...params, offset, limit: Math.min(MAX, alvo - offset) } })
    const pagina = data.results || []
    results.push(...pagina)
    count = data.count ?? results.length
    if (data.next_offset == null || !pagina.length) break
  }
  const vistos = new Set()
  return { results: results.filter(x => !vistos.has(x.id) && vistos.add(x.id)), count }
}
