// utils/media.js — versões leves das fotos e vídeos (backend: app/utils/versoes_media.py)
//
// Os ficheiros feitos pela plataforma têm um nome de 20 caracteres hexadecimais; as versões ficam ao lado:
//   foto   …/<hex>.webp  (1600 px)  → …/<hex>__600.webp
//   vídeo  …/<hex>.mp4   (1080p)    → …/<hex>__720.mp4 (telemóveis), …/<hex>__480.mp4 (cartões)
// Outros nomes (ficheiros antigos, imagens externas) ficam como estão.

const PRINCIPAL = /^(.*\/[0-9a-f]{20})\.(webp|mp4)(\?.*)?$/

function versao (url, sufixo, ext) {
  const m = PRINCIPAL.exec(url || '')
  if (!m || m[2] !== ext) return url
  return `${m[1]}${sufixo}.${m[2]}${m[3] || ''}`
}

// foto para cartões, listas e miniaturas (600 px)
export const miniatura = url => versao(url, '__600', 'webp')

// vídeo de cartão/carrossel (480p)
export const videoCartao = url => versao(url, '__480', 'mp4')

export const ecraPequeno = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(max-width: 767px)').matches

// vídeo em destaque (topo da home, página da loja/produto): 720p no telemóvel, 1080p no computador
export const videoDestaque = url => (ecraPequeno() ? versao(url, '__720', 'mp4') : url)

// "Poupança de dados" do telemóvel/browser ou "Reduzir movimento" do sistema: os vídeos ficam no poster
export function poupar () {
  if (typeof window === 'undefined') return false
  if (navigator.connection?.saveData) return true
  return !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}
