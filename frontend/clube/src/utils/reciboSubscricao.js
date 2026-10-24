import { formatarDinheiro } from '@/utils/dinheiro'
// Comprovativo de pagamento (ou nota de cobrança) de uma mensalidade da subscrição, em PDF, gerado no browser (jsPDF).
// Não é uma fatura: as faturas legais saem do e-Fatura (ver utils/fiscal.js).
// Fundo branco para poder ser impresso. Dados vêm de fatura_payload (utils/subscricoes.py).

const euros = v => formatarDinheiro(Number(v) || 0)
const data = s => (s ? new Date(s.length === 10 ? s + 'T12:00:00' : s).toLocaleDateString('pt-PT') : '—')

export async function gerarReciboSubscricao (f) {
  const { default: jsPDF } = await import('jspdf')
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pw = doc.internal.pageSize.getWidth()
  const mg = 20
  const paga = f.estado === 'paga'
  const titulo = paga ? 'Comprovativo de pagamento' : f.estado === 'anulada' ? 'Nota de cobrança anulada' : 'Nota de cobrança'

  // cabeçalho
  doc.setFillColor(220, 38, 38)
  doc.rect(0, 0, pw, 4, 'F')
  doc.setTextColor(24, 24, 27)
  doc.setFont('helvetica', 'bold'); doc.setFontSize(22)
  doc.text('Bendi', mg, 24)
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(113, 113, 122)
  doc.text(f.pos_id ? 'Subscrição do POS na plataforma' : 'Subscrição da loja na plataforma', mg, 30)
  doc.setFont('helvetica', 'bold'); doc.setFontSize(16); doc.setTextColor(24, 24, 27)
  doc.text(`${titulo} nº ${f.id}`, pw - mg, 24, { align: 'right' })
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(113, 113, 122)
  doc.text(`Emitido a ${data(new Date().toISOString())}`, pw - mg, 30, { align: 'right' })

  // linhas
  let y = 48
  const linha = (rotulo, valor, destaque = false) => {
    doc.setDrawColor(228, 228, 231); doc.line(mg, y + 3, pw - mg, y + 3)
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(113, 113, 122)
    doc.text(rotulo, mg, y)
    doc.setFont('helvetica', destaque ? 'bold' : 'normal'); doc.setFontSize(destaque ? 13 : 11); doc.setTextColor(24, 24, 27)
    doc.text(String(valor), pw - mg, y, { align: 'right', maxWidth: pw - mg * 2 - 50 })
    y += 11
  }
  linha(f.pos_id ? 'POS' : 'Loja', f.loja_nome || '—')
  linha('Descrição', f.descricao)
  linha('Período', `${data(f.periodo_inicio)} a ${data(f.periodo_fim)}`)
  if (paga) {
    linha('Pago a', data(f.paga_em))
    linha('Método', f.metodo_nome || '—')
  } else {
    linha('Vencimento', data(f.vencimento))
    linha('Estado', f.estado_nome)
  }
  if (f.notas) linha('Notas', f.notas)
  y += 4
  linha(paga ? 'Total pago' : 'Total', euros(f.valor), true)

  // rodapé
  doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(161, 161, 170)
  const rodape = paga
    ? (f.pos_id ? 'Comprovativo do pagamento da mensalidade do POS.' : 'Comprovativo do pagamento da mensalidade. As lojas em subscrição não pagam comissão sobre as vendas.')
    : 'Documento informativo do valor a pagar.'
  doc.text(rodape, mg, 275, { maxWidth: pw - mg * 2 })
  doc.setFont('helvetica', 'bold')
  doc.text('Documento interno — não substitui fatura.', mg, 280)
  doc.setFont('helvetica', 'normal')
  if (f.metodo === 'simulado') doc.text('Pagamento simulado (ambiente de testes).', mg, 285)

  doc.save(`${paga ? 'comprovativo' : 'nota-cobranca'}-subscricao-${f.id}.pdf`)
}
