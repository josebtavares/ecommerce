// utils/fontes.js — esperar pelas fontes web antes de mostrar uma página
// Cada template da loja importa as suas fontes do Google Fonts (@import no CSS do template, display=swap).
// Se a fonte chega depois do primeiro desenho, o texto muda de largura e a página "salta"
// (ex.: no TechStore o 2.º botão do topo passava para a linha de baixo). Quem chama espera por elas
// em paralelo com os dados — no máximo `limite` ms; numa rede lenta mostra com a fonte de recurso.

// só os caracteres latinos (é o subconjunto que a página usa — não descarrega cirílico/grego/…)
const TEXTO = 'Aaçãé'

export function esperarFontes (limite = 1000) {
  if (typeof document === 'undefined' || !document.fonts?.load) return Promise.resolve()
  const pedidos = new Set()
  document.fonts.forEach(f => {
    if (f.status === 'loaded') return
    // pesos variáveis vêm como "400 900": basta um deles para o ficheiro descarregar
    const peso = String(f.weight || '400').split(' ')[0]
    pedidos.add(`${f.style || 'normal'} ${peso} 16px "${f.family.replace(/"/g, '')}"`)
  })
  if (!pedidos.size) return Promise.resolve()
  const todas = Promise.all([...pedidos].map(p => document.fonts.load(p, TEXTO).catch(() => null)))
  return Promise.race([todas, new Promise(resolve => setTimeout(resolve, limite))])
}
