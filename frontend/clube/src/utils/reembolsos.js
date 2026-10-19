// Pedidos de reembolso (ver backend utils/devolucoes.py) — textos e cores partilhados pelo cliente,
// pelo backoffice da loja e pelo admin.

export const ESTADOS = {
  pedido:          { label: 'A aguardar a loja',        cor: 'amber'  },
  proposta:        { label: 'A loja propôs outro valor', cor: 'sky'    },
  em_disputa:      { label: 'Em análise pela Bendi',    cor: 'purple' },
  aguarda_produto: { label: 'A aguardar o produto',     cor: 'indigo' },
  a_devolver:      { label: 'A devolver em mão',        cor: 'amber'  },
  reembolsado:     { label: 'Reembolsado',              cor: 'green'  },
  recusado:        { label: 'Recusado',                 cor: 'red'    },
  cancelado:       { label: 'Desistiu',                 cor: 'zinc'   },
}

export const ATIVOS = ['pedido', 'proposta', 'em_disputa', 'aguarda_produto', 'a_devolver']

// classes completas (o Tailwind só gera as que aparecem escritas por inteiro)
const CORES = {
  amber:  'bg-amber-500/15 text-amber-500',
  sky:    'bg-sky-500/15 text-sky-500',
  purple: 'bg-purple-500/15 text-purple-400',
  indigo: 'bg-indigo-500/15 text-indigo-400',
  green:  'bg-green-500/15 text-green-500',
  red:    'bg-red-500/15 text-red-500',
  zinc:   'bg-zinc-500/15 text-zinc-400',
}

export function corEstado (estado) {
  return CORES[ESTADOS[estado]?.cor] || CORES.zinc
}

export function labelEstado (estado, valorAprovado, metodo) {
  // artigo esgotado numa encomenda ainda por pagar: não houve dinheiro devolvido, baixou o valor a pagar
  if (estado === 'reembolsado' && metodo === 'abatido') return 'Descontado'
  // cancelamento aceite sem nada pago (dinheiro na entrega) não é um "reembolso"
  if (estado === 'reembolsado' && valorAprovado !== undefined && Number(valorAprovado) === 0) return 'Cancelamento aceite'
  return ESTADOS[estado]?.label || estado
}

export const MOTIVOS = {
  defeito:      { label: 'Produto com defeito ou danificado', ajuda: 'Chegou partido, estragado ou não funciona.' },
  errado:       { label: 'Produto errado',                    ajuda: 'Recebeste outro produto, tamanho ou cor.' },
  em_falta:     { label: 'Faltou algo',                       ajuda: 'A encomenda chegou incompleta.' },
  nao_chegou:   { label: 'A encomenda não chegou',            ajuda: 'Está marcada como entregue mas não a recebeste.' },
  esgotado:     { label: 'Artigo esgotado',                   ajuda: 'A loja não tinha o artigo e reembolsou-o antes de enviar.' },
  mudei_ideias: { label: 'Mudei de ideias',                   ajuda: 'Devolves o produto à loja. O envio de volta é por tua conta e a taxa de entrega não é reembolsada.' },
}
export const MOTIVOS_PROBLEMA = ['defeito', 'errado', 'em_falta', 'nao_chegou']

export function dataHora (iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}
