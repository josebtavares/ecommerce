// Favoritos — produtos e lojas guardados (o coração nos cards).
// Um só pedido por sessão traz os ids (para marcar todos os corações); guardar/retirar é
// imediato no ecrã e volta atrás se o servidor recusar. Visitante → convite a entrar, e o
// coração que tocou fica guardado depois de entrar.
import { reactive } from 'vue'
import api from '@/services/api'
import { estaAutenticado, pedirLogin } from '@/services/sessao'

const PENDENTE = 'favorito_pendente'

export const favoritos = reactive({
  produtos: new Set(),
  lojas: new Set(),
  carregado: false,
  versao: 0,          // muda a cada alteração — a lista do perfil recarrega
})

let aCarregar = null

function conjunto (tipo) {
  return tipo === 'loja' ? favoritos.lojas : favoritos.produtos
}

export function eFavorito (tipo, id) {
  return estaAutenticado() && conjunto(tipo).has(Number(id))
}

export function garantirFavoritos () {
  if (!estaAutenticado()) {
    if (favoritos.carregado) { favoritos.produtos.clear(); favoritos.lojas.clear(); favoritos.carregado = false }
    return Promise.resolve()
  }
  if (favoritos.carregado) return Promise.resolve()
  if (!aCarregar) {
    aCarregar = api.get('/app/favoritos/ids/')
      .then(({ data }) => {
        favoritos.produtos = new Set(data.produtos)
        favoritos.lojas = new Set(data.lojas)
        favoritos.carregado = true
        return aplicarPendente()
      })
      .catch(() => {})
      .finally(() => { aCarregar = null })
  }
  return aCarregar
}

async function aplicarPendente () {
  let p = null
  try { p = JSON.parse(sessionStorage.getItem(PENDENTE) || 'null') } catch { p = null }
  sessionStorage.removeItem(PENDENTE)
  if (p && (p.tipo === 'produto' || p.tipo === 'loja') && !eFavorito(p.tipo, p.id)) {
    await alternarFavorito(p.tipo, p.id)
  }
}

export async function alternarFavorito (tipo, id) {
  id = Number(id)
  if (!estaAutenticado()) {
    sessionStorage.setItem(PENDENTE, JSON.stringify({ tipo, id }))
    pedirLogin(tipo === 'loja'
      ? 'Entra ou cria conta para guardares esta loja nos favoritos.'
      : 'Entra ou cria conta para guardares este produto nos favoritos.')
    return false
  }
  const c = conjunto(tipo)
  const tinha = c.has(id)
  // imediato no ecrã; volta atrás se o servidor recusar
  if (tinha) c.delete(id); else c.add(id)
  try {
    if (tinha) await api.delete(`/app/favoritos/${tipo}/${id}/`)
    else await api.post('/app/favoritos/', tipo === 'loja' ? { loja_id: id } : { produto_id: id })
    favoritos.versao++
    return true
  } catch (e) {
    if (tinha) c.add(id); else c.delete(id)
    return false
  }
}
