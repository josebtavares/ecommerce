// Datas dos dashboards e relatórios. Sempre a data local (toISOString passaria para UTC e, à noite,
// em Cabo Verde (UTC−1) já seria o dia seguinte).
export function dataISO (d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function intervaloAtalho (id, hoje = new Date()) {
  const a = hoje.getFullYear(), m = hoje.getMonth(), d = hoje.getDate()
  const r = (i, f) => ({ inicio: dataISO(i), fim: dataISO(f) })
  switch (id) {
    case 'hoje':        return r(hoje, hoje)
    case '7d':          return r(new Date(a, m, d - 6), hoje)
    case '30d':         return r(new Date(a, m, d - 29), hoje)
    case 'mes_passado': return r(new Date(a, m - 1, 1), new Date(a, m, 0))
    case 'ano':         return r(new Date(a, 0, 1), hoje)
    case '12m':         return r(new Date(a, m - 11, 1), hoje)
    case 'ano_passado': return r(new Date(a - 1, 0, 1), new Date(a - 1, 11, 31))
    default:            return r(new Date(a, m, 1), hoje)             // 'mes'
  }
}

// "2026-10-05" → "5/10"; com granularidade 'mes' → "out 2026"
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
export function rotuloBalde (iso, granularidade = 'dia') {
  if (!iso) return ''
  const [a, m, d] = iso.split('-').map(Number)
  return granularidade === 'mes' ? `${MESES[m - 1]} ${a}` : `${d}/${m}`
}

export function dataCurta (iso) {
  if (!iso) return ''
  const [a, m, d] = iso.split('-')
  return `${d}/${m}/${a}`
}
