// Textos-base das políticas da loja (criação da loja). O dono pode mudá-los à vontade — aqui e depois
// em Configurações → Políticas. Seguem as regras da plataforma (backend utils/devolucoes.py):
// problema com o artigo → 48 h depois da entrega; mudança de ideias → prazo_devolucao_dias (0 = não aceita).

const PRAZO_PROBLEMA_H = 48

export const PRAZOS_DEVOLUCAO = [
  { dias: 0, label: 'Não aceito' },
  { dias: 7, label: '7 dias' },
  { dias: 14, label: '14 dias' },
  { dias: 30, label: '30 dias' },
]

export function politicaDevolucaoBase (dias) {
  const problema = `Se o artigo chegar com defeito, errado ou em falta, avisa-nos nas ${PRAZO_PROBLEMA_H} horas seguintes à ` +
    'entrega, na página da encomenda: trocamos o artigo ou devolvemos o dinheiro.'
  if (!dias) {
    return 'Não aceitamos devoluções por mudança de ideias.\n\n' + problema
  }
  return `Podes devolver os artigos até ${dias} dias depois de os receberes, mesmo que tenhas mudado de ideias, ` +
    'desde que estejam sem uso e na embalagem original. Nesse caso, o envio de volta é por tua conta.\n\n' +
    problema + '\n\n' +
    'O reembolso é feito pelo mesmo meio de pagamento, depois de recebermos o produto.'
}

export function politicaEntregasBase () {
  return 'Entregamos nas zonas e pelos preços indicados no checkout. O tempo de entrega é uma estimativa e conta a ' +
    'partir da confirmação da encomenda (e do pagamento, quando é antecipado).\n\n' +
    'Se não estiveres na morada, contactamos-te para combinar outra entrega. Nos envios por transportadora ' +
    'indicamos o código de rastreio sempre que existir.'
}
