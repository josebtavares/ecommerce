// directives/videoVisivel.js — v-video-visivel
// Substitui o `autoplay` dos vídeos decorativos (banners, cartões de produto):
//   • só reproduz com pelo menos metade do vídeo no ecrã e pausa quando sai; no máximo
//     MAX_A_TOCAR ao mesmo tempo (os mais visíveis) — evita ter muitos vídeos a descarregar
//     e descodificar ao mesmo tempo (a causa dos "stutters");
//   • com poster, não descarrega nada até ser preciso (preload="none");
//   • respeita "poupança de dados" e "reduzir movimento" (fica no poster — utils/media.js);
//   • escolhe a versão leve (utils/media.js): v-video-visivel="'cartao'" → 480p,
//     v-video-visivel="'destaque'" → 720p no telemóvel; se a versão faltar, volta ao original;
//   • ao desmontar, liberta o descodificador.
// Uso: <video v-video-visivel="'cartao'" :src="…" :poster="…" muted loop playsinline></video>

import { miniatura, poupar, videoCartao, videoDestaque } from '@/utils/media'

const VERSAO = { cartao: videoCartao, destaque: videoDestaque }

const MAX_A_TOCAR = 4
let observer = null
const visiveis = new Map()     // vídeo → fracção visível (só os que têm pelo menos metade no ecrã)

function tocar (video) {
  if (poupar() || document.hidden) return
  const p = video.play()
  if (p && typeof p.catch === 'function') p.catch(() => {})   // autoplay bloqueado: fica no poster
}

// metade do vídeo no ecrã (ou, se for mais alto que o ecrã, metade da altura do ecrã ocupada por ele
// e pelo menos metade da largura — um slide encostado à borda fica com largura 0 e não conta)
function metadeNoEcra (e) {
  if (!e.isIntersecting) return false
  if (e.intersectionRatio >= 0.5) return true
  const r = e.intersectionRect
  return r.height >= window.innerHeight * 0.5 && r.width >= e.boundingClientRect.width * 0.5
}

// toca os MAX_A_TOCAR mais visíveis (em empate, os que já estavam no ecrã); os outros ficam pausados
function escolher () {
  if (document.hidden) return
  const ordem = [...visiveis.entries()].sort((a, b) => b[1] - a[1])
  ordem.forEach(([v], i) => {
    if (i < MAX_A_TOCAR) { if (v.paused) tocar(v) } else if (!v.paused) v.pause()
  })
}

function getObserver () {
  if (!observer) {
    observer = new IntersectionObserver(entradas => {
      for (const e of entradas) {
        if (metadeNoEcra(e)) visiveis.set(e.target, Math.round(e.intersectionRatio * 4) / 4)
        else {
          visiveis.delete(e.target)
          if (!e.target.paused) e.target.pause()
        }
      }
      escolher()
    }, { threshold: [0, 0.25, 0.5, 0.75, 1] })

    // separador em segundo plano: pausa tudo; ao voltar, retoma só os visíveis
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) document.querySelectorAll('video[data-video-visivel]').forEach(v => v.pause())
      else escolher()
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
    if (visiveis.has(el)) escolher()
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
    if (visiveis.delete(el)) escolher()
    el.removeEventListener('error', voltarAoOriginal)
    el.pause()
    el.removeAttribute('src')  // liberta memória/descodificador
    el.load()
  },
}
