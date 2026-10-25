// Períodos das abas Faturação (loja e POS): datas AAAA-MM-DD no dia de Cabo Verde
import { hojeCV } from '@/utils/servicos'

export const PERIODOS = [
  { v: 'mes', t: 'Este mês' }, { v: 'mes_passado', t: 'Mês passado' }, { v: 'tres_meses', t: 'Últimos 3 meses' },
  { v: 'ano', t: 'Este ano' }, { v: 'ano_passado', t: 'Ano passado' }, { v: 'todas', t: 'Todas as datas' },
  { v: 'personalizado', t: 'Personalizado…' },
]

const iso = d => d.toISOString().slice(0, 10)

// [de, ate] do período ('todas' → ['', ''])
export function intervalo (p) {
  const h = new Date(hojeCV() + 'T12:00:00Z')
  const a = h.getUTCFullYear(), m = h.getUTCMonth()
  const dia = (y, mm, d) => iso(new Date(Date.UTC(y, mm, d)))
  return {
    mes: [dia(a, m, 1), iso(h)],
    mes_passado: [dia(a, m - 1, 1), dia(a, m, 0)],
    tres_meses: [dia(a, m - 2, 1), iso(h)],
    ano: [dia(a, 0, 1), iso(h)],
    ano_passado: [dia(a - 1, 0, 1), dia(a - 1, 11, 31)],
    todas: ['', ''],
  }[p]
}

export function textoPeriodo (de, ate) {
  const f = s => s.split('-').reverse().join('/')
  if (de && ate) return `${f(de)} a ${f(ate)}`
  if (de) return `desde ${f(de)}`
  if (ate) return `até ${f(ate)}`
  return 'Desde sempre'
}
