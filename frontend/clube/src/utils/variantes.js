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

/**
 * Atributos de escolha do tipo do produto, só com as opções que o produto tem
 * (ex.: tamanho: [pequeno, grande], gelo: [sim, não]). Usado no POS.
 */
export function opcoesDoProduto (produto) {
  const valores = produto?.atributos || {}
  return (produto?.tipo?.atributos_schema || [])
    .filter(a => typeof a === 'object' && a.tipo === 'choices')
    .map(a => {
      const tem = valores[a.nome]
      const lista = Array.isArray(tem) ? tem : (tem ? [tem] : [])
      return { ...a, opcoes: (a.opcoes || []).filter(o => lista.includes(o)) }
    })
    .filter(a => a.opcoes.length)
}

/** O produto precisa que se escolham opções antes de ir para a conta? */
export function precisaEscolha (produto) {
  return opcoesDoProduto(produto).length > 0
}

// ── Grelha no formulário do produto (antes de gravar) ─────────────────────
// Mesma regra do backend (app/utils/variantes.py → combinacoes_produto/chave_de).

/** "cor=preto|tamanho=M" — chaves ordenadas, igual ao backend. */
export function chaveDe (combinacao) {
  return Object.keys(combinacao).sort().map(k => `${k}=${combinacao[k]}`).join('|')
}

/** Nomes dos atributos-variante (📦) de um schema de tipo, pela ordem do schema. */
export function atributosVarianteSchema (schema) {
  return (schema || [])
    .filter(a => typeof a === 'object' && a.tipo === 'choices' && a.variante)
    .map(a => a.nome)
}

/**
 * Combinações possíveis a partir do schema do tipo e das opções seleccionadas
 * no formulário: [{ chave, combinacao }]. Atributos 📦 sem opções são ignorados.
 */
export function combinacoesDe (schema, atributos) {
  const valores = n => {
    const v = (atributos || {})[n]
    const lista = Array.isArray(v) ? v : (v ? [v] : [])
    return [...new Set(lista.map(x => String(x).trim()).filter(Boolean))]
  }
  const nomes = atributosVarianteSchema(schema).filter(n => valores(n).length)
  if (!nomes.length) return []
  let combos = [{}]
  for (const n of nomes) {
    combos = combos.flatMap(c => valores(n).map(v => ({ ...c, [n]: v })))
  }
  return combos.map(combinacao => ({ chave: chaveDe(combinacao), combinacao }))
}

/** Reconstrói as linhas da grelha para novas combinações, mantendo os valores já escritos. */
export function mesclarLinhas (combos, linhasAnteriores) {
  const antes = Object.fromEntries((linhasAnteriores || []).map(l => [l.chave, l]))
  return combos.map(({ chave, combinacao }) => ({
    chave, combinacao,
    quantidade: antes[chave]?.quantidade ?? 0,
    preco:      antes[chave]?.preco ?? '',
    sku:        antes[chave]?.sku ?? '',
  }))
}

/** Linhas da grelha → formato do backend (campo "variantes" do formulário do produto). */
export function linhasParaPayload (linhas) {
  return (linhas || []).map(l => ({
    chave: l.chave,
    quantidade: Number(l.quantidade) || 0,
    preco: l.preco === '' || l.preco === null || l.preco === undefined ? null : String(l.preco),
    sku: String(l.sku || '').trim(),
  }))
}

/** Todas as quantidades são inteiros ≥ 0? */
export function grelhaValida (linhas) {
  return (linhas || []).every(l => l.quantidade !== '' && Number.isInteger(Number(l.quantidade)) && Number(l.quantidade) >= 0)
}

/** Linhas iniciais a partir das variantes guardadas de um produto (payload da API). */
export function linhasDoProduto (produto) {
  return (produto?.variantes || []).map(v => ({
    chave: v.chave, combinacao: v.combinacao,
    quantidade: v.quantidade ?? 0, preco: v.preco ?? '', sku: v.sku || '',
  }))
}
