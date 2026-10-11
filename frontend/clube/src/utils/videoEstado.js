// utils/videoEstado.js — acompanha a otimização de vídeos no backoffice
// (backend: app/utils/video.py · GET/POST /app/loja/<id>/videos/…)
//
// Estados de <campo>_estado: '' (não é vídeo) | pendente | a_processar | pronto | erro
import api from '@/services/api'

export const emCurso = estado => estado === 'pendente' || estado === 'a_processar'

export function eVideo (url) {
  return /\.(mp4|webm|mov|mkv|m4v|avi)(\?|#|$)/i.test(url || '')
}

/**
 * Consulta o estado dos vídeos da loja de x em x segundos enquanto houver algum em curso.
 *   const vigia = criarVigia(lojaId, data => { … })
 *   vigia.vigiar([idsDeProdutosEmCurso], bannerEmCurso)   ·   vigia.parar()
 * `aoAtualizar` recebe { em_curso, banner, produtos: [{ modelo, id, estado, url, poster_url }] }.
 */
export function criarVigia (lojaId, aoAtualizar, intervalo = 5000) {
  let timer = null
  let ids   = []

  async function verificar () {
    try {
      const { data } = await api.get(`/app/loja/${lojaId}/videos/`, { params: { ids: ids.join(',') } })
      aoAtualizar(data)
      if (!data.em_curso) parar()
    } catch (e) { /* tenta no próximo ciclo */ }
  }

  function vigiar (idsProdutos = [], banner = false) {
    ids = idsProdutos
    if (!ids.length && !banner) { parar(); return }
    if (!timer) timer = setInterval(verificar, intervalo)
  }

  function parar () {
    clearInterval(timer)
    timer = null
  }

  return { vigiar, parar, verificar }
}

/** Volta a pôr na fila um vídeo que falhou. modelo: 'loja' | 'produto' */
export async function reprocessarVideo (lojaId, modelo, id) {
  const { data } = await api.post(`/app/loja/${lojaId}/videos/reprocessar/`, { modelo, id })
  return data
}
