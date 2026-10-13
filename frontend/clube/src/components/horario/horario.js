// Horário das lojas — textos partilhados (loja pública, checkout, backoffice).

// "08:00–12:00 · 14:00–22:00", "Aberto 24h" ou "Fechado"
export function horasDoDia (dia) {
  const ints = dia?.intervalos || []
  if (!ints.length) return 'Fechado'
  if (ints.length === 1 && ints[0].abre === '00:00' && ints[0].fecha === '00:00') return 'Aberto 24h'
  return ints.map(i => `${i.abre}–${i.fecha}`).join(' · ')
}

// "amanhã às 08:00" a partir de "Fechada · abre amanhã às 08:00"
export function quandoAbre (horario) {
  const t = horario?.texto || ''
  const i = t.indexOf('abre ')
  return i >= 0 ? t.slice(i + 5) : ''
}
