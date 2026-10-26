// directives/videoVisivel.js — v-video-visivel
// Substitui o `autoplay` dos vídeos decorativos (banners, cartões de produto):
//   • só reproduz enquanto o vídeo está no ecrã e pausa quando sai — evita ter
//     vários vídeos a descodificar ao mesmo tempo (a causa dos "stutters");
//   • com poster, não descarrega nada até ser preciso (preload="none");
//   • respeita "poupança de dados" e "reduzir movimento" (fica no poster — utils/media.js);
//   • escolhe a versão leve (utils/media.js): v-video-visivel="'cartao'" → 480p,
//     v-video-visivel="'destaque'" → 720p no telemóvel; se a versão faltar, volta ao original;
//   • ao desmontar, liberta o descodificador.
// Uso: <video v-video-visivel="'cartao'" :src="…" :poster="…" muted loop playsinline></video>

import { miniatura, poupar, videoCartao, videoDestaque } from '@/utils/media'

const VERSAO = { cartao: videoCartao, destaque: videoDestaque }

let observer = null

function tocar (video) {
  if (poupar() || document.hidden) return
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

// troca src/poster pelas versões leves (só quando o Vue mudou o src — senão já está tratado)
function escolherVersao (el, uso) {
  const original = el.getAttribute('src') || ''
  if (original !== el._versaoAtual) {
    el._original = original
    el._versaoAtual = (VERSAO[uso] || (u => u))(original)
    if (el._versaoAtual !== original) el.setAttribute('src', el._versaoAtual)
  }
  const poster = el.getAttribute('poster')
  if (uso === 'cartao' && poster && poster !== el._posterAtual) {
    el._posterAtual = miniatura(poster)
    if (el._posterAtual !== poster) el.setAttribute('poster', el._posterAtual)
  }
}

function voltarAoOriginal (e) {
  const el = e.currentTarget
  if (el._original && el.getAttribute('src') !== el._original) {
    el._versaoAtual = el._original
    el.setAttribute('src', el._original)
    if (el._videoVisivel) tocar(el)
  }
}

export default {
  created (el) {
    el.preload = 'none'        // antes do src (o Vue aplica os atributos depois deste hook): nada descarrega já
  },
  mounted (el, binding) {
    el.muted = true            // obrigatório para reproduzir sem interacção
    el.playsInline = true
    el.dataset.videoVisivel = ''
    escolherVersao(el, binding.value)
    el.addEventListener('error', voltarAoOriginal)
    prepararPreload(el)
    if (typeof IntersectionObserver === 'undefined') { tocar(el); return }
    getObserver().observe(el)
  },
  updated (el, binding) {
    escolherVersao(el, binding.value)
    prepararPreload(el)
  },
  beforeUnmount (el) {
    observer?.unobserve(el)
    el.removeEventListener('error', voltarAoOriginal)
    el.pause()
    el.removeAttribute('src')  // liberta memória/descodificador
    el.load()
  },
}
