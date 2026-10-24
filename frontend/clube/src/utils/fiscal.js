// Dados fiscais de quem vende (loja/POS) — as mesmas regras do backend (app/utils/fiscal.py)

export const REGIMES = [
  { valor: 'particular', titulo: 'Como particular', texto: 'Vendas ocasionais de bens próprios.' },
  { valor: 'atividade',  titulo: 'Com atividade declarada', texto: 'Empresário em nome individual ou empresa.' },
]

export const EMISSOR_PUBLICO_URL = 'https://efatura.cv'

// a fatura só se regista numa venda que aconteceu (backend: ESTADOS_FATURAVEIS)
export const ESTADOS_FATURAVEIS = ['pago', 'preparando', 'enviado', 'concluido']

export function nifLimpo (nif = '') {
  return String(nif).replace(/\D/g, '')
}

export function dadosFiscaisValidos (d = {}) {
  return nifLimpo(d.nif).length === 9 && REGIMES.some(r => r.valor === d.regime_fiscal) && !!d.declaracao_fiscal
}

// corpo para o backend (JSON ou FormData)
export function corpoDadosFiscais (d) {
  return { nif: nifLimpo(d.nif), regime_fiscal: d.regime_fiscal, declaracao_fiscal: d.declaracao_fiscal ? 'true' : 'false' }
}
