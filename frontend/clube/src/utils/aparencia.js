// utils/aparencia.js — fundos do login/registo e logótipo do site, mudados em Admin → Definições → Aparência
// (backend: app/utils/aparencia.py · GET /app/plataforma/aparencia/). Sem nada definido fica o original
// (os ficheiros que vêm com o frontend). A última resposta fica guardada no browser: na visita seguinte o logo
// certo aparece logo, sem piscar o antigo; o pedido actualiza-a em segundo plano.
import { reactive } from 'vue'
import api from '@/services/api'
import { mediaUrl } from '@/services/media'
import { videoDestaque } from '@/utils/media'
import logoClaroOriginal from '@/assets/img/login/logo_final_640.webp'
import logoEscuroOriginal from '@/assets/img/login/logo_final_640_light.webp'
import posterRegistoOriginal from '@/assets/img/register/register_fundo3.png'

const CHAVE = 'bendi:aparencia'

// o que o site mostra sem nada escolhido (o editor do admin usa-os na pré-visualização)
export const ORIGINAL = {
  logo: logoClaroOriginal,
  logo_escuro: logoEscuroOriginal,
  fundo: () => ({ tipo: 'video', url: mediaUrl('videos/fundo-login.mp4'), poster: null }),
}

function lerGuardada () {
  try { return JSON.parse(localStorage.getItem(CHAVE)) || null } catch { return null }
}

export const aparencia = reactive({ dados: lerGuardada() })

let pedido = null

/** Lê a aparência do servidor (uma vez por carregamento da página; forcar=true depois de a mudar no admin). */
export function carregarAparencia (forcar = false) {
  if (pedido && !forcar) return pedido
  pedido = api.get('/app/plataforma/aparencia/').then(({ data }) => {
    aparencia.dados = data
    try { localStorage.setItem(CHAVE, JSON.stringify(data)) } catch { /* sem armazenamento: só nesta visita */ }
    aplicarIcones()
    return data
  }).catch(() => { pedido = null; return aparencia.dados })
  return pedido
}

/** Logótipo para o tema: escuro=true → a versão para fundos escuros. Se só houver uma versão nova, serve para os dois. */
export function logoPara (escuro) {
  const d = aparencia.dados || {}
  if (escuro) return d.logo_escuro || d.logo || logoEscuroOriginal
  return d.logo || d.logo_escuro || logoClaroOriginal
}

/** Fundo do login / registo / recuperar senha: { tipo: 'imagem'|'video', url, poster }. */
export function fundoPara (qual) {
  const d = aparencia.dados || {}
  const m = qual === 'registo' ? d.fundo_registo : d.fundo_login
  if (m && m.url) {
    return m.tipo === 'video'
      ? { tipo: 'video', url: videoDestaque(m.url), poster: m.poster || null }
      : { tipo: 'imagem', url: m.url, poster: null }
  }
  return { tipo: 'video', url: mediaUrl('videos/fundo-login.mp4'),
           poster: qual === 'registo' ? posterRegistoOriginal : null }
}

/** Ícone do separador e do ecrã inicial do telemóvel gerados do logo novo (index.html traz os originais). */
export function aplicarIcones () {
  const ic = aparencia.dados?.icones
  if (!ic || typeof document === 'undefined') return
  document.querySelectorAll('link[rel="icon"]').forEach(l => {
    const tam = l.getAttribute('sizes')
    const novo = tam === '192x192' ? ic['192'] : ic['32']
    if (novo) {
      l.href = novo
      l.type = 'image/png'
    }
  })
  const apple = document.querySelector('link[rel="apple-touch-icon"]')
  if (apple && ic['180']) apple.href = ic['180']
}
