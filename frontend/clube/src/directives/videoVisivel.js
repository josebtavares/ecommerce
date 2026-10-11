// directives/videoVisivel.js — v-video-visivel
// Substitui o `autoplay` dos vídeos decorativos (banners, cartões de produto):
//   • só reproduz enquanto o vídeo está no ecrã e pausa quando sai — evita ter
//     vários vídeos a descodificar ao mesmo tempo (a causa dos "stutters");
//   • com poster, não descarrega nada até ser preciso (preload="none");
//   • respeita "reduzir movimento" do sistema (fica no poster);
//   • ao desmontar, liberta o descodificador.
// Uso: <video v-video-visivel :src="…" :poster="…" muted loop playsinline></video>

const reduzirMovimento = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

let observer = null

function tocar (video) {
  if (reduzirMovimento() || document.hidden) return
  const p = video.play()
  if (p && typeof p.catch === 'function') p.catch(() => {})   // autoplay bloqueado: fica no poster
}

function getObserver () {
  if (!observer) {
    observer = new IntersectionObserver(entradas => {
      for (const e of entradas) {
        e.target._videoVisivel = e.isIntersecting
        if (e.isIntersecting) tocar(e.target)
        else if (!e.target.paused) e.target.pause()
      }
    }, { rootMargin: '150px 0px', threshold: 0.1 })

    // separador em segundo plano: pausa tudo; ao voltar, retoma só os visíveis
    document.addEventListener('visibilitychange', () => {
      document.querySelectorAll('video[data-video-visivel]').forEach(v => {
        if (document.hidden) v.pause()
        else if (v._videoVisivel) tocar(v)
      })
    })
  }
  return observer
}

function prepararPreload (el) {
  el.preload = el.getAttribute('poster') ? 'none' : 'metadata'
}

export default {
  mounted (el) {
    el.muted = true            // obrigatório para reproduzir sem interacção
    el.playsInline = true
    el.dataset.videoVisivel = ''
    prepararPreload(el)
    if (typeof IntersectionObserver === 'undefined') { tocar(el); return }
    getObserver().observe(el)
  },
  updated (el) {
    prepararPreload(el)
  },
  beforeUnmount (el) {
    observer?.unobserve(el)
    el.pause()
    el.removeAttribute('src')  // liberta memória/descodificador
    el.load()
  },
}
