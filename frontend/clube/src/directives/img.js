// directives/img.js — v-img
// Para as <img> de conteúdo (fotos de lojas, produtos, serviços):
//   • loading="lazy" + decoding="async", postos antes do src (hook created): só descarrega perto do ecrã;
//   • cartões e listas pedem a miniatura no próprio template: <img v-img :src="$miniatura(url)">
//     (utils/media.js — 600 px); se a miniatura não existir, volta sozinha à foto original.
// Imagens que aparecem logo no topo da página (a maior do ecrã inicial) não devem levar v-img.

function voltarAoOriginal (e) {
  const el = e.currentTarget
  const src = el.getAttribute('src') || ''
  if (src.includes('__600.')) el.setAttribute('src', src.replace('__600.', '.'))
}

export default {
  created (el) {
    el.loading = 'lazy'
    el.decoding = 'async'
  },
  mounted (el) {
    el.addEventListener('error', voltarAoOriginal)
  },
  beforeUnmount (el) {
    el.removeEventListener('error', voltarAoOriginal)
  },
}
