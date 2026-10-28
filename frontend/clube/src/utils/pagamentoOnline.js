// Pagamentos online (backend app/pagamentos): quando o fornecedor quer o cliente na página dele, a resposta
// traz { redirecionar: { url, metodo: 'GET'|'POST', campos, fornecedor } }. Com o simulado nunca acontece.
// Na volta, a página /pagamento/callback (PagamentoRegresso.vue) confirma no backend.

const CHAVE = 'pagamento_fornecedor'

// segue o redirecionamento, se houver → true (a página vai sair)
export function seguirPagamento (resposta) {
  const r = resposta?.redirecionar
  if (!r?.url) return false
  try { localStorage.setItem(CHAVE, r.fornecedor || '') } catch (e) { /* sem localStorage: o regresso traz o resto */ }
  if ((r.metodo || 'GET').toUpperCase() === 'POST') {
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = r.url
    Object.entries(r.campos || {}).forEach(([nome, valor]) => {
      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = nome
      input.value = valor
      form.appendChild(input)
    })
    document.body.appendChild(form)
    form.submit()
  } else {
    window.location.href = r.url
  }
  return true
}

export function fornecedorDoRegresso () {
  try {
    const f = localStorage.getItem(CHAVE)
    localStorage.removeItem(CHAVE)
    return f || ''
  } catch (e) {
    return ''
  }
}
