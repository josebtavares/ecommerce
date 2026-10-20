// Formatação das células dos relatórios (os mesmos tipos que o backend: utils/relatorios_motor.py).
import { formatarDinheiro } from '@/utils/dinheiro'

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const p2 = (n) => String(n).padStart(2, '0')

export function formatarCelula (v, tipo) {
  if (v === null || v === undefined || v === '') return ''
  switch (tipo) {
    case 'dinheiro': return formatarDinheiro(v)
    case 'percent':  return `${Number(v).toLocaleString('pt-PT', { maximumFractionDigits: 2 })}%`
    case 'numero':   return Number(v).toLocaleString('pt-PT', { maximumFractionDigits: 1 })
    case 'id':       return String(v)          // nº de encomenda, fatura… sem separador de milhares
    case 'data': {
      const [a, m, d] = String(v).slice(0, 10).split('-')
      return `${d}/${m}/${a}`
    }
    case 'mes': {
      const [a, m] = String(v).split('-')
      return `${MESES[Number(m) - 1]}/${a}`
    }
    case 'datahora': {
      // a API manda a hora já no fuso da plataforma (2026-10-09T11:53:00-01:00): mostra-se tal como vem
      const [data, hora] = String(v).split('T')
      const [a, m, d] = data.split('-')
      return `${d}/${m}/${a} ${(hora || '').slice(0, 5)}`
    }
    default: return String(v)
  }
}

export const NUMERICOS = ['dinheiro', 'numero', 'percent', 'id']

export function nomeFicheiro (prefixo, rid, inicio, fim, formato) {
  const d = (s) => s.replaceAll('-', '')
  return `${prefixo}_${rid}_${d(inicio)}-${d(fim)}.${formato}`
}

export function agoraCurto (iso) {
  const t = new Date(iso)
  return `${p2(t.getDate())}/${p2(t.getMonth() + 1)}/${t.getFullYear()} ${p2(t.getHours())}:${p2(t.getMinutes())}`
}
