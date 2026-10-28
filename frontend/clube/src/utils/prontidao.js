// Produto "completo" para a loja poder ser publicada — igual a backend app/utils/prontidao.py.
export const DESCRICAO_MIN = 20

// { temFoto, descricao, preco } → ['foto', 'descrição', 'preço'] (vazio = completo)
export function faltas ({ temFoto, descricao, preco }) {
  const f = []
  if (!temFoto) f.push('foto')
  if ((descricao || '').trim().length < DESCRICAO_MIN) f.push('descrição')
  if (!(Number(preco) > 0)) f.push('preço')
  return f
}

// produto como vem da API (ProdutoSerializer)
export function faltasProduto (p) {
  return faltas({ temFoto: !!(p.ficheiro_url || p.imagens?.length), descricao: p.descricao, preco: p.preco })
}
