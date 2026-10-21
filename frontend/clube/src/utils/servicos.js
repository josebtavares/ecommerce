// Serviços e marcações — datas e horas. O servidor manda ISO com o fuso de Cabo Verde
// ("2026-11-02T10:00:00-01:00"): lemos a hora do texto, sem passar pelo fuso do browser.

export const DIAS_CURTOS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
export const DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

export const hora = (iso) => (iso || '').slice(11, 16)
export const diaDe = (iso) => (iso || '').slice(0, 10)
export const minutosDe = (iso) => { const h = hora(iso); return Number(h.slice(0, 2)) * 60 + Number(h.slice(3, 5)) }

// 'AAAA-MM-DD' ± n dias (meio-dia: sem saltos de hora de verão)
export function somarDias (dia, n) {
  const d = new Date(dia + 'T12:00:00')
  d.setDate(d.getDate() + n)
  return d.toISOString().slice(0, 10)
}

// 0 = segunda … 6 = domingo (como no servidor)
export const diaSemana = (dia) => (new Date(dia + 'T12:00:00').getDay() + 6) % 7

export function rotuloDia (dia, comAno = false) {
  const [a, m, d] = dia.split('-')
  return `${DIAS_CURTOS[diaSemana(dia)]}, ${d}/${m}${comAno ? '/' + a : ''}`
}

// hoje em Cabo Verde (UTC−1, sem hora de verão)
export function hojeCV () {
  const d = new Date(Date.now() - 60 * 60 * 1000)
  return d.toISOString().slice(0, 10)
}

export const ESTADOS_MARCACAO = {
  pendente:   { nome: 'Pendente',   cor: 'bg-amber-500/15 border-amber-500/40 text-amber-200', ponto: 'bg-amber-400' },
  confirmada: { nome: 'Confirmada', cor: 'bg-sky-500/15 border-sky-500/40 text-sky-100',       ponto: 'bg-sky-400' },
  concluida:  { nome: 'Concluída',  cor: 'bg-green-500/15 border-green-500/40 text-green-100', ponto: 'bg-green-400' },
  cancelada:  { nome: 'Cancelada',  cor: 'bg-zinc-800/60 border-zinc-700 text-zinc-500 line-through', ponto: 'bg-zinc-500' },
  falta:      { nome: 'Falta',      cor: 'bg-red-500/10 border-red-500/30 text-red-300',       ponto: 'bg-red-400' },
  expirada:   { nome: 'Expirada',   cor: 'bg-zinc-800/60 border-zinc-700 text-zinc-500',       ponto: 'bg-zinc-600' },
}

export function duracaoTexto (min) {
  const h = Math.floor(min / 60), m = min % 60
  return h ? `${h} h${m ? ' ' + m + ' min' : ''}` : `${m} min`
}

export const CAMPO = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500'
