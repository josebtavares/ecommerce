// composable/usePdfRelatorio.js
// Gera PDFs de relatórios usando jsPDF (sem dependências do servidor)
// Instalar: npm install jspdf

export function usePdfRelatorio() {

  // ── Cores e estilos ────────────────────────────────────
  const CORES = {
    fundo:       [15, 15, 15],      // zinc-950
    card:        [24, 24, 27],      // zinc-900
    borda:       [39, 39, 42],      // zinc-800
    texto:       [244, 244, 245],   // zinc-100
    textoSub:    [113, 113, 122],   // zinc-500
    vermelho:    [239, 68, 68],     // red-500
    verde:       [34, 197, 94],     // green-500
    amarelo:     [234, 179, 8],     // yellow-500
    azul:        [59, 130, 246],    // blue-500
    laranja:     [249, 115, 22],    // orange-500
  }

  function fmt(val) {
    return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
  }

  function fmtNum(n) {
    return new Intl.NumberFormat('pt-PT').format(n || 0)
  }

  function hoje() {
    return new Date().toLocaleDateString('pt-PT', {
      day: '2-digit', month: 'long', year: 'numeric'
    })
  }

  // ── Helpers de desenho ─────────────────────────────────
  function drawRect(doc, x, y, w, h, cor, raio = 3) {
    doc.setFillColor(...cor)
    doc.roundedRect(x, y, w, h, raio, raio, 'F')
  }

  function drawLine(doc, x1, y1, x2, y2, cor = CORES.borda, esp = 0.3) {
    doc.setDrawColor(...cor)
    doc.setLineWidth(esp)
    doc.line(x1, y1, x2, y2)
  }

  function drawText(doc, texto, x, y, opts = {}) {
    const { size = 9, cor = CORES.texto, bold = false, align = 'left' } = opts
    doc.setFontSize(size)
    doc.setTextColor(...cor)
    doc.setFont('helvetica', bold ? 'bold' : 'normal')
    doc.text(String(texto), x, y, { align })
  }

  function drawKpi(doc, x, y, w, h, label, valor, cor = CORES.vermelho) {
    drawRect(doc, x, y, w, h, CORES.card)
    doc.setDrawColor(...CORES.borda)
    doc.setLineWidth(0.3)
    doc.roundedRect(x, y, w, h, 3, 3, 'S')
    drawText(doc, label, x + 4, y + 8, { size: 7, cor: CORES.textoSub })
    drawText(doc, valor, x + 4, y + 18, { size: 13, cor, bold: true })
  }

  function drawBarChart(doc, x, y, w, h, dados, labelKey, valorKey, cor = CORES.vermelho) {
    if (!dados?.length) return
    const max = Math.max(...dados.map(d => d[valorKey]), 1)
    const barH = Math.max(4, (h - 4) / dados.length - 2)

    dados.forEach((item, i) => {
      const barY   = y + i * (barH + 2)
      const barW   = (item[valorKey] / max) * (w - 50)
      // fundo
      drawRect(doc, x + 45, barY, w - 50, barH, CORES.borda, 1)
      // barra
      drawRect(doc, x + 45, barY, Math.max(2, barW), barH, cor, 1)
      // label
      const nome = String(item[labelKey]).slice(0, 18)
      drawText(doc, nome, x + 44, barY + barH / 2 + 2, { size: 6.5, cor: CORES.textoSub, align: 'right' })
      // valor
      const valStr = typeof item[valorKey] === 'number' && item[valorKey] > 100
        ? fmt(item[valorKey])
        : fmtNum(item[valorKey])
      drawText(doc, valStr, x + w, barY + barH / 2 + 2, { size: 6.5, cor: CORES.texto, align: 'right' })
    })
  }

  function drawLineChart(doc, x, y, w, h, dados, label = 'Vendas') {
    if (!dados?.length) return
    const max = Math.max(...dados.map(d => d.total), 1)

    // área de fundo
    drawRect(doc, x, y, w, h, CORES.card)

    // grid lines
    for (let i = 1; i < 4; i++) {
      const gy = y + (h / 4) * i
      drawLine(doc, x + 2, gy, x + w - 2, gy, CORES.borda, 0.2)
    }

    // pontos e linha
    const pts = dados.map((d, i) => ({
      px: x + 2 + (i / (dados.length - 1 || 1)) * (w - 4),
      py: y + h - 4 - (d.total / max) * (h - 8),
    }))

    // fill area
    if (pts.length > 1) {
      doc.setFillColor(239, 68, 68, 0.1)
      const path = [
        [pts[0].px, y + h - 2],
        ...pts.map(p => [p.px, p.py]),
        [pts[pts.length - 1].px, y + h - 2],
      ]
      doc.setFillColor(60, 20, 20)
      doc.moveTo(path[0][0], path[0][1])
      path.slice(1).forEach(p => doc.lineTo(p[0], p[1]))
      doc.fill()
    }

    // linha
    doc.setDrawColor(...CORES.vermelho)
    doc.setLineWidth(0.7)
    pts.forEach((p, i) => {
      if (i === 0) doc.moveTo(p.px, p.py)
      else doc.lineTo(p.px, p.py)
    })
    doc.stroke()

    // pontos
    pts.forEach(p => {
      doc.setFillColor(...CORES.vermelho)
      doc.circle(p.px, p.py, 1, 'F')
    })

    // labels eixo X (primeiro, meio, último)
    const indices = [0, Math.floor(dados.length / 2), dados.length - 1]
    indices.forEach(i => {
      if (!dados[i]) return
      const d   = new Date(dados[i].dia)
      const lbl = `${d.getDate()}/${d.getMonth() + 1}`
      drawText(doc, lbl, pts[i].px, y + h + 4, { size: 6, cor: CORES.textoSub, align: 'center' })
    })
  }

  function drawSectionHeader(doc, titulo, x, y, pageW) {
    drawText(doc, titulo.toUpperCase(), x, y, { size: 7, cor: CORES.textoSub, bold: true })
    drawLine(doc, x, y + 2, pageW - x, y + 2, CORES.borda, 0.3)
    return y + 8
  }

  function drawCapa(doc, titulo, subtitulo, periodo, geradoPor = '') {
    const pw = doc.internal.pageSize.getWidth()
    const ph = doc.internal.pageSize.getHeight()

    // fundo
    doc.setFillColor(...CORES.fundo)
    doc.rect(0, 0, pw, ph, 'F')

    // barra vermelha topo
    doc.setFillColor(...CORES.vermelho)
    doc.rect(0, 0, pw, 2, 'F')

    // título
    drawText(doc, titulo, pw / 2, ph / 2 - 20, { size: 22, bold: true, align: 'center' })
    drawText(doc, subtitulo, pw / 2, ph / 2 - 8, { size: 11, cor: CORES.textoSub, align: 'center' })

    // período
    drawRect(doc, pw / 2 - 45, ph / 2 + 2, 90, 12, CORES.card, 4)
    drawText(doc, `Período: ${periodo}`, pw / 2, ph / 2 + 10, { size: 9, cor: CORES.vermelho, align: 'center', bold: true })

    // rodapé
    drawText(doc, `Gerado em ${hoje()}`, pw / 2, ph - 20, { size: 8, cor: CORES.textoSub, align: 'center' })
    if (geradoPor) {
      drawText(doc, `por ${geradoPor}`, pw / 2, ph - 14, { size: 7, cor: CORES.textoSub, align: 'center' })
    }

    // barra vermelha fundo
    doc.setFillColor(...CORES.vermelho)
    doc.rect(0, ph - 2, pw, 2, 'F')
  }

  function drawRodape(doc, pagina, total, nomeLoja = '') {
    const pw = doc.internal.pageSize.getWidth()
    const ph = doc.internal.pageSize.getHeight()
    drawLine(doc, 10, ph - 12, pw - 10, ph - 12, CORES.borda, 0.3)
    drawText(doc, nomeLoja, 10, ph - 6, { size: 6.5, cor: CORES.textoSub })
    drawText(doc, `Gerado em ${hoje()}`, pw / 2, ph - 6, { size: 6.5, cor: CORES.textoSub, align: 'center' })
    drawText(doc, `Página ${pagina} de ${total}`, pw - 10, ph - 6, { size: 6.5, cor: CORES.textoSub, align: 'right' })
  }

  // ══════════════════════════════════════════════════════════
  // PDF BACKOFFICE — relatório da loja
  // ══════════════════════════════════════════════════════════
  async function gerarPdfLoja(dados, nomeLoja, periodo) {
    const { default: jsPDF } = await import('jspdf')
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const pw  = doc.internal.pageSize.getWidth()
    const mg  = 12
    const cw  = pw - mg * 2

    // ── Página 1: capa ─────────────────────────────────────
    drawCapa(doc, nomeLoja, 'Relatório de Desempenho', periodo)

    // ── Página 2: KPIs + gráfico ───────────────────────────
    doc.addPage()
    doc.setFillColor(...CORES.fundo)
    doc.rect(0, 0, pw, doc.internal.pageSize.getHeight(), 'F')

    let y = mg

    // KPIs — linha 1
    y = drawSectionHeader(doc, 'Resumo do período', mg, y, pw)
    const kpiW = (cw - 6) / 4
    drawKpi(doc, mg,              y, kpiW, 26, 'Vendas',        fmt(dados.total_vendas),    CORES.vermelho)
    drawKpi(doc, mg + kpiW + 2,  y, kpiW, 26, 'Encomendas',    fmtNum(dados.total_encomendas), CORES.azul)
    drawKpi(doc, mg + (kpiW + 2) * 2, y, kpiW, 26, 'Concluídas', fmtNum(dados.enc_concluidas), CORES.verde)
    drawKpi(doc, mg + (kpiW + 2) * 3, y, kpiW, 26, 'Canceladas', fmtNum(dados.enc_canceladas), CORES.textoSub)
    y += 32

    // KPIs — linha 2
    const kpiW2 = (cw - 4) / 3
    drawKpi(doc, mg,              y, kpiW2, 26, 'Taxa conclusão', `${dados.taxa_conclusao}%`, CORES.verde)
    drawKpi(doc, mg + kpiW2 + 2, y, kpiW2, 26, 'Com. pendentes', fmt(dados.comissao_pendente), CORES.amarelo)
    drawKpi(doc, mg + (kpiW2 + 2) * 2, y, kpiW2, 26, 'Rating médio',
      dados.rating_medio ? `${dados.rating_medio.toFixed(1)} ★` : '—', CORES.amarelo)
    y += 34

    // Gráfico vendas
    y = drawSectionHeader(doc, 'Vendas por dia', mg, y, pw)
    if (dados.grafico_vendas?.length) {
      drawLineChart(doc, mg, y, cw, 45, dados.grafico_vendas)
      y += 55
    } else {
      drawText(doc, 'Sem vendas neste período', mg, y + 10, { cor: CORES.textoSub })
      y += 20
    }

    // ── Página 3: produtos + entregas + stock ──────────────
    doc.addPage()
    doc.setFillColor(...CORES.fundo)
    doc.rect(0, 0, pw, doc.internal.pageSize.getHeight(), 'F')
    y = mg

    // Top produtos
    y = drawSectionHeader(doc, 'Top produtos mais vendidos', mg, y, pw)
    if (dados.produtos_top?.length) {
      drawBarChart(doc, mg, y, cw, dados.produtos_top.length * 8 + 4, dados.produtos_top, 'nome', 'qty', CORES.vermelho)
      y += dados.produtos_top.length * 10 + 8
    } else {
      drawText(doc, 'Sem dados', mg, y + 6, { cor: CORES.textoSub })
      y += 14
    }

    // Entregas
    y = drawSectionHeader(doc, 'Resumo de entregas', mg, y, pw)
    const entW = (cw - 6) / 4
    drawKpi(doc, mg,              y, entW, 22, 'Total',    fmtNum(dados.entregas_periodo),   CORES.azul)
    drawKpi(doc, mg + entW + 2,  y, entW, 22, 'Entregues', fmtNum(dados.entregas_concluidas), CORES.verde)
    drawKpi(doc, mg + (entW+2)*2, y, entW, 22, 'Falhadas',  fmtNum(dados.entregas_falhadas),  CORES.vermelho)
    drawKpi(doc, mg + (entW+2)*3, y, entW, 22, 'Taxa',      `${dados.taxa_entrega}%`,         CORES.verde)
    y += 30

    // Stock em alerta
    if (dados.stock_baixo?.length) {
      y = drawSectionHeader(doc, 'Stock em alerta', mg, y, pw)
      dados.stock_baixo.forEach(s => {
        const cor = s.qty === 0 ? CORES.vermelho : CORES.amarelo
        drawRect(doc, mg, y, cw, 9, CORES.card, 2)
        drawText(doc, s.nome, mg + 3, y + 6.5, { size: 8, cor: CORES.texto })
        const label = s.qty === 0 ? 'Esgotado' : `${s.qty} un.`
        drawText(doc, label, pw - mg - 3, y + 6.5, { size: 8, cor, bold: true, align: 'right' })
        y += 11
      })
    }

    // Comissões
    y += 4
    y = drawSectionHeader(doc, 'Comissões', mg, y, pw)
    drawKpi(doc, mg,          y, (cw-4)/3, 22, 'No período',  fmt(dados.comissao_periodo),  CORES.laranja)
    drawKpi(doc, mg+(cw-4)/3+2, y, (cw-4)/3, 22, 'Pendentes', fmt(dados.comissao_pendente), CORES.amarelo)
    drawKpi(doc, mg+(cw-4)/3*2+4, y, (cw-4)/3, 22, 'Liquidadas', fmt(dados.comissao_liquidada), CORES.verde)

    // rodapés
    const totalPags = doc.getNumberOfPages()
    for (let i = 2; i <= totalPags; i++) {
      doc.setPage(i)
      drawRodape(doc, i - 1, totalPags - 1, nomeLoja)
    }

    doc.save(`relatorio_${nomeLoja.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`)
  }

  // ══════════════════════════════════════════════════════════
  // PDF ADMIN — relatório global
  // ══════════════════════════════════════════════════════════
  async function gerarPdfAdmin(dados, periodo, geradoPor = '') {
    const { default: jsPDF } = await import('jspdf')
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const pw  = doc.internal.pageSize.getWidth()
    const mg  = 12
    const cw  = pw - mg * 2

    // ── Capa ───────────────────────────────────────────────
    drawCapa(doc, 'Relatório Global', 'Painel de Administração', periodo, geradoPor)

    // ── Página 2: KPIs financeiros ─────────────────────────
    doc.addPage()
    doc.setFillColor(...CORES.fundo)
    doc.rect(0, 0, pw, doc.internal.pageSize.getHeight(), 'F')
    let y = mg

    y = drawSectionHeader(doc, 'Métricas financeiras', mg, y, pw)
    const kpiW = (cw - 6) / 4
    drawKpi(doc, mg,              y, kpiW, 26, 'GMV',               fmt(dados.gmv),                   CORES.vermelho)
    drawKpi(doc, mg + kpiW + 2,  y, kpiW, 26, 'Comissões geradas',  fmt(dados.comissoes_geradas),      CORES.laranja)
    drawKpi(doc, mg+(kpiW+2)*2,  y, kpiW, 26, 'Com. pendentes',     fmt(dados.comissoes_pendentes),    CORES.amarelo)
    drawKpi(doc, mg+(kpiW+2)*3,  y, kpiW, 26, 'Com. liquidadas',    fmt(dados.comissoes_liquidadas),   CORES.verde)
    y += 32

    y = drawSectionHeader(doc, 'Métricas operacionais', mg, y, pw)
    const kpiW2 = (cw - 6) / 4
    drawKpi(doc, mg,              y, kpiW2, 26, 'Encomendas',      fmtNum(dados.total_encomendas),    CORES.azul)
    drawKpi(doc, mg+kpiW2+2,     y, kpiW2, 26, 'Concluídas',      fmtNum(dados.enc_concluidas),      CORES.verde)
    drawKpi(doc, mg+(kpiW2+2)*2, y, kpiW2, 26, 'Taxa conclusão',   `${dados.taxa_conclusao}%`,        CORES.verde)
    drawKpi(doc, mg+(kpiW2+2)*3, y, kpiW2, 26, 'Canceladas',      fmtNum(dados.enc_canceladas),      CORES.textoSub)
    y += 34

    // Gráfico GMV
    y = drawSectionHeader(doc, 'GMV por dia', mg, y, pw)
    if (dados.grafico?.length) {
      drawLineChart(doc, mg, y, cw, 45, dados.grafico)
      y += 55
    } else {
      drawText(doc, 'Sem dados de vendas neste período', mg, y + 10, { cor: CORES.textoSub })
      y += 20
    }

    // Estados das encomendas
    y = drawSectionHeader(doc, 'Encomendas por estado', mg, y, pw)
    const estados = Object.entries(dados.por_estado || {})
    const colW    = (cw - (estados.length - 1) * 2) / estados.length
    const coresEstado = {
      pendente: CORES.amarelo, pago: CORES.azul, preparando: [168, 85, 247],
      enviado: [99, 102, 241], concluido: CORES.verde, cancelado: CORES.vermelho,
    }
    estados.forEach(([key, val], i) => {
      const ex = mg + i * (colW + 2)
      drawKpi(doc, ex, y, colW, 22, key, fmtNum(val), coresEstado[key] || CORES.textoSub)
    })
    y += 30

    // ── Página 3: top lojas + top produtos ─────────────────
    doc.addPage()
    doc.setFillColor(...CORES.fundo)
    doc.rect(0, 0, pw, doc.internal.pageSize.getHeight(), 'F')
    y = mg

    // Top lojas
    y = drawSectionHeader(doc, 'Top lojas por volume de vendas', mg, y, pw)
    if (dados.lojas_top?.length) {
      drawBarChart(doc, mg, y, cw, dados.lojas_top.length * 9, dados.lojas_top, 'nome', 'total', CORES.vermelho)
      y += dados.lojas_top.length * 11 + 8
    } else {
      drawText(doc, 'Sem dados', mg, y + 6, { cor: CORES.textoSub })
      y += 14
    }

    // Top produtos
    y = drawSectionHeader(doc, 'Top produtos mais vendidos', mg, y, pw)
    if (dados.produtos_top?.length) {
      drawBarChart(doc, mg, y, cw, dados.produtos_top.length * 9, dados.produtos_top, 'nome', 'qty', CORES.azul)
      y += dados.produtos_top.length * 11 + 8
    } else {
      drawText(doc, 'Sem dados', mg, y + 6, { cor: CORES.textoSub })
      y += 14
    }

    // Avaliações
    if (dados.rating_medio || dados.total_avaliacoes) {
      y = drawSectionHeader(doc, 'Avaliações', mg, y, pw)
      drawKpi(doc, mg,        y, (cw-4)/2, 22, 'Rating médio global',
        dados.rating_medio ? `${dados.rating_medio.toFixed(1)} ★` : '—', CORES.amarelo)
      drawKpi(doc, mg+(cw-4)/2+4, y, (cw-4)/2, 22, 'Total de avaliações',
        fmtNum(dados.total_avaliacoes), CORES.textoSub)
    }

    // rodapés
    const totalPags = doc.getNumberOfPages()
    for (let i = 2; i <= totalPags; i++) {
      doc.setPage(i)
      drawRodape(doc, i - 1, totalPags - 1, 'Administração da Plataforma')
    }

    doc.save(`relatorio_admin_${new Date().toISOString().split('T')[0]}.pdf`)
  }

  return { gerarPdfLoja, gerarPdfAdmin }
}