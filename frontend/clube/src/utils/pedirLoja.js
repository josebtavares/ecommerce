// pedirLoja.js — GET /app/loja/<id>/ partilhado entre quem abre a página da loja ao mesmo tempo
// (views/loja/lojaPublica.vue escolhe o template; composables/useLojaData.js mostra a loja): um pedido em vez de dois.
// Cada um recebe a sua cópia (o template altera o objecto, ex.: rating_medio). Só vale uns segundos — recarregar
// a loja (loadAll) vai sempre à API.
// A resposta fica para os DOIS que a pedem ao abrir a loja (a página e o template) e depois sai; no máximo 60 s
// desde que chegou. Com rede lenta o template ainda está a descarregar quando a resposta chega e só a pede
// segundos depois — antes (5 s desde o envio) voltava a pedir a loja (teste de carga 2026-11-14).
import api from '@/services/api'

const VALIDADE_MS = 60000
const USOS = 2
const pedidos = new Map()

export function pedirLoja (id) {
  const chave = String(id)
  let e = pedidos.get(chave)
  if (!e || (e.t !== null && Date.now() - e.t > VALIDADE_MS)) {
    e = { p: null, t: null, usos: 0 }        // t = quando chegou a resposta (null = ainda em curso)
    const entrada = e
    entrada.p = api.get(`/app/loja/${id}/`).then(r => { entrada.t = Date.now(); return r.data })
    entrada.p.catch(() => { if (pedidos.get(chave) === entrada) pedidos.delete(chave) })
    pedidos.set(chave, entrada)
  }
  e.usos += 1
  if (e.usos >= USOS) pedidos.delete(chave)    // já serviu os dois: a próxima visita pede dados novos
  return e.p.then(d => JSON.parse(JSON.stringify(d)))
}
