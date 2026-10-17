// Dinheiro da plataforma: escudo cabo-verdiano no formato tradicional (1250 → "1.250$00").
// Todos os valores vêm da API já em CVE — aqui só se formata.
export const MOEDA = 'CVE'

export function formatarDinheiro (v) {
  const n = Number(v) || 0
  const centavos = Math.round(Math.abs(n) * 100)
  const inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  const dec = String(centavos % 100).padStart(2, '0')
  return `${n < 0 && centavos ? '-' : ''}${inteiro}$${dec}`
}
