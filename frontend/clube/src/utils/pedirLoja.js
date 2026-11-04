// pedirLoja.js — GET /app/loja/<id>/ partilhado entre quem abre a página da loja ao mesmo tempo
// (views/loja/lojaPublica.vue escolhe o template; composables/useLojaData.js mostra a loja): um pedido em vez de dois.
// Cada um recebe a sua cópia (o template altera o objecto, ex.: rating_medio). Só vale uns segundos — recarregar
// a loja (loadAll) vai sempre à API.
import api from '@/services/api'

const VALIDADE_MS = 5000
const pedidos = new Map()

export function pedirLoja (id) {
  const chave = String(id)
  const e = pedidos.get(chave)
  if (!e || Date.now() - e.t > VALIDADE_MS) {
    const p = api.get(`/app/loja/${id}/`).then(r => r.data)
    p.catch(() => pedidos.delete(chave))
    pedidos.set(chave, { p, t: Date.now() })
  }
  return pedidos.get(chave).p.then(d => JSON.parse(JSON.stringify(d)))
}
