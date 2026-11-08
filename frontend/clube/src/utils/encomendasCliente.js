// Encomendas do cliente: separadores e estado (página /encomendas, ficha /encomendas/<id>).
// Os separadores batem com GRUPOS_CLIENTE do backend (Views/inventariocarrinhoencomendaView.py).
export const SEPARADORES = [
  { k: '',           n: 'Todas' },
  { k: 'em_curso',   n: 'Em curso' },
  { k: 'concluidas', n: 'Concluídas' },
  { k: 'canceladas', n: 'Canceladas' },
]

const NOMES = {
  pendente: 'Por pagar', pago: 'Paga', preparando: 'Em preparação', enviado: 'Enviada',
  concluido: 'Concluída', cancelado: 'Cancelada',
}

// transferência ainda não confirmada pela loja: não está paga, mesmo com o estado 'pago'
export function nomeEstado (enc) {
  if (enc.prazo_transferencia) return 'A aguardar transferência'
  return NOMES[enc.status] || enc.status
}

export function corEstado (enc) {
  if (enc.prazo_transferencia) return 'bg-amber-500/15 text-amber-500'
  return {
    pendente:   'bg-yellow-500/15 text-yellow-500',
    pago:       'bg-blue-500/15 text-blue-400',
    preparando: 'bg-purple-500/15 text-purple-400',
    enviado:    'bg-indigo-500/15 text-indigo-400',
    concluido:  'bg-green-500/15 text-green-500',
    cancelado:  'bg-red-500/15 text-red-400',
  }[enc.status] || 'bg-zinc-500/15 text-zinc-400'
}

export function dataCurta (d) {
  return d ? new Date(d).toLocaleDateString('pt-PT') : ''
}
