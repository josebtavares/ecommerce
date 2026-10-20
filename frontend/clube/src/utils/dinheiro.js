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

// Valor escrito por uma pessoa → centavos (inteiro); vazio → 0; inválido → NaN.
// Aceita "1250", "1250,5", "1250.50", "1.250", "1.250,00" e "1.250$00" (o ponto com 3 dígitos é de milhares).
export function lerCentavos (texto) {
  const t = String(texto ?? '').trim().replace(/\s/g, '').replace(/\$/g, ',')
  if (!t) return 0
  const milhares = /^\d{1,3}(\.\d{3})+(,\d*)?$/.test(t)
  const normal = t.includes(',') || milhares ? t.replace(/\./g, '').replace(',', '.') : t
  if (!/^\d+(\.\d{0,2})?$/.test(normal)) return NaN
  return Math.round(Number(normal) * 100)
}
