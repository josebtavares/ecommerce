// Stock por variação — lógica do card de compra (sem dependências de Vue).
// Uma variante: { id, combinacao: { tamanho: 'M', cor: 'preto' }, quantidade, preco_efetivo }

/** O produto usa stock por variação e tem variantes activas? */
export function usaVariantes (produto) {
  return !!(produto?.stock_por_variante && produto?.variantes?.length)
}

/** Atributos que definem a variante (ex.: ['tamanho', 'cor']), só os presentes nas variantes. */
export function atributosVariante (produto) {
  const presentes = new Set((produto?.variantes || []).flatMap(v => Object.keys(v.combinacao || {})))
  return (produto?.atributos_variante || []).filter(n => presentes.has(n))
}

/** Variante compatível com as escolhas dadas (ignora atributos não-variante, ex.: picante). */
function compativel (v, escolhas, nomes, ignorar = null) {
  return nomes.every(n => n === ignorar || !escolhas[n] || v.combinacao[n] === escolhas[n])
}

/**
 * Estado de uma opção, tendo em conta o que já está escolhido nos outros atributos:
 *   'disponivel'     — há stock para esta opção com as escolhas actuais
 *   'esgotada_combo' — há stock com outras escolhas (clicável: troca as escolhas em conflito)
 *   'esgotada'       — nenhuma combinação com esta opção tem stock
 *   'inexistente'    — o produto não tem esta opção
 */
export function estadoOpcao (produto, escolhas, nome, opcao) {
  const nomes = atributosVariante(produto)
  const comOpcao = (produto.variantes || []).filter(v => v.combinacao[nome] === opcao)
  if (!comOpcao.length) return 'inexistente'
  if (!comOpcao.some(v => v.quantidade > 0)) return 'esgotada'
  return comOpcao.some(v => v.quantidade > 0 && compativel(v, escolhas, nomes, nome))
    ? 'disponivel'
    : 'esgotada_combo'
}

/**
 * Escolher uma opção: mantém as outras escolhas compatíveis (com stock) e larga
 * as que entrariam em conflito — ex.: tinha M·preto, escolhe S, e S·preto está
 * esgotado → fica só S (o cliente escolhe a cor de novo).
 */
export function escolherOpcao (produto, escolhas, nome, opcao) {
  const nomes = atributosVariante(produto)
  const novas = { ...escolhas, [nome]: opcao }
  if (!nomes.includes(nome)) return novas
  const temStock = e => (produto.variantes || []).some(v => v.quantidade > 0 && compativel(v, e, nomes))
  if (temStock(novas)) return novas
  // larga as outras escolhas-variante, uma a uma, até haver stock
  for (const outro of nomes) {
    if (outro === nome || !novas[outro]) continue
    delete novas[outro]
    if (temStock(novas)) break
  }
  return novas
}

/** Variante exacta quando todos os atributos-variante estão escolhidos. */
export function varianteEscolhida (produto, escolhas) {
  const nomes = atributosVariante(produto)
  if (!nomes.length || nomes.some(n => !escolhas[n])) return null
  return (produto.variantes || []).find(v => nomes.every(n => v.combinacao[n] === escolhas[n])) || null
}

/** Atributos-variante ainda por escolher. */
export function variantesPorEscolher (produto, escolhas) {
  return atributosVariante(produto).filter(n => !escolhas[n])
}

/** Stock das combinações compatíveis com as escolhas (todas, se nada escolhido). */
export function stockCompativel (produto, escolhas) {
  const nomes = atributosVariante(produto)
  return (produto.variantes || [])
    .filter(v => compativel(v, escolhas, nomes))
    .reduce((s, v) => s + v.quantidade, 0)
}

/** { min, max } dos preços das combinações compatíveis com stock (para "desde X"). */
export function intervaloPreco (produto, escolhas) {
  const nomes = atributosVariante(produto)
  const precos = (produto.variantes || [])
    .filter(v => v.quantidade > 0 && compativel(v, escolhas, nomes))
    .map(v => Number(v.preco_efetivo))
  if (!precos.length) return null
  return { min: Math.min(...precos), max: Math.max(...precos) }
}
