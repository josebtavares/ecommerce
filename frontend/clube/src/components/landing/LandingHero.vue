<!-- LandingHero.vue — topo da landing page: vídeo ou imagem a ocupar o ecrã (versão própria no telemóvel, se houver),
     véu escuro para o texto se ler, título, subtítulo e até dois botões. Sem media: fundo com as cores da marca.
     Vídeo: 720p no telemóvel; com "poupança de dados" / "reduzir movimento" fica só o poster. -->
<template>
  <section id="hero" class="relative min-h-[100svh] flex items-center overflow-hidden" data-teste="landing-hero"
           :class="media ? 'bg-black' : (isDark ? 'bg-zinc-950' : 'bg-orange-50')">
    <template v-if="media">
      <video v-if="media.tipo === 'video' && !pouparDados" :key="fonteVideo" ref="video" :src="fonteVideo" :poster="media.poster || undefined"
             autoplay muted loop playsinline preload="auto" aria-hidden="true" data-teste="hero-video"
             class="absolute inset-0 w-full h-full object-cover" @error="aoErroVideo"></video>
      <img v-else :src="media.tipo === 'video' ? media.poster : media.url" alt="" aria-hidden="true" data-teste="hero-imagem"
           fetchpriority="high" class="absolute inset-0 w-full h-full object-cover" />
      <div class="absolute inset-0" :style="{ background: `rgba(0,0,0,${(s.escurecer ?? 45) / 100})` }"></div>
      <div class="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black/50 to-transparent"></div>
    </template>
    <div v-else class="absolute inset-0 pointer-events-none" aria-hidden="true">
      <div class="absolute -top-40 -right-40 w-[38rem] h-[38rem] rounded-full blur-3xl opacity-40"
           :class="isDark ? 'bg-red-700' : 'bg-orange-300'"></div>
      <div class="absolute -bottom-48 -left-32 w-[32rem] h-[32rem] rounded-full blur-3xl opacity-30"
           :class="isDark ? 'bg-red-900' : 'bg-amber-200'"></div>
    </div>

    <div class="relative z-10 w-full max-w-7xl mx-auto px-5 sm:px-8 pt-28 pb-20">
      <div class="max-w-3xl">
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.08] tracking-tight whitespace-pre-line"
            :class="media ? 'text-white drop-shadow' : (isDark ? 'text-white' : 'text-zinc-900')" data-teste="hero-titulo">{{ s.titulo }}</h1>
        <p v-if="s.subtitulo" class="mt-5 text-base sm:text-xl leading-relaxed max-w-2xl whitespace-pre-line"
           :class="media ? 'text-white/90' : (isDark ? 'text-zinc-300' : 'text-zinc-600')">{{ s.subtitulo }}</p>
        <div v-if="s.botao || s.botao2" class="mt-9 flex flex-wrap gap-3">
          <a v-if="s.botao" :href="s.botao.link" @click="clique($event, s.botao.link)" data-teste="hero-botao"
             class="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl text-base font-bold text-white shadow-lg transition hover:opacity-90 active:scale-[0.98]"
             :class="isDark ? 'bg-red-600' : 'bg-orange-500'">
            {{ s.botao.texto }} <font-awesome-icon :icon="['fas', 'arrow-right']" class="w-4 h-4" />
          </a>
          <a v-if="s.botao2" :href="s.botao2.link" @click="clique($event, s.botao2.link)" data-teste="hero-botao2"
             class="inline-flex items-center px-6 py-3.5 rounded-2xl text-base font-semibold border transition"
             :class="media ? 'border-white/50 text-white hover:bg-white/10'
                           : (isDark ? 'border-zinc-700 text-zinc-100 hover:bg-zinc-900' : 'border-zinc-300 text-zinc-800 hover:bg-white')">
            {{ s.botao2.texto }}
          </a>
        </div>
      </div>
    </div>

    <a v-if="seguinte" :href="'#' + seguinte" @click.prevent="$emit('acao', '#' + seguinte)" aria-label="Ver mais"
       class="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 w-10 h-10 rounded-full flex items-center justify-center animate-bounce"
       :class="media ? 'text-white/80' : (isDark ? 'text-zinc-500' : 'text-zinc-400')">
      <font-awesome-icon :icon="['fas', 'chevron-down']" class="w-5 h-5" />
    </a>
  </section>
</template>

<script>
import { ecraPequeno, poupar, videoMovel } from '@/utils/media'

export default {
  name: 'LandingHero',
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    seguinte: { type: String, default: '' },        // secção seguinte (seta para baixo)
  },
  emits: ['acao'],
  data () { return { movel: ecraPequeno(), pouparDados: poupar(), tentativa: 0 } },
  computed: {
    media () { return (this.movel && this.s.media_movel) || this.s.media || null },
    fonteVideo () {
      const url = this.media?.url
      if (!url) return ''
      // 720p no telemóvel; se a versão ainda não existir (vídeo acabado de converter) usa o original
      return this.movel && this.tentativa === 0 ? videoMovel(url) : url
    },
  },
  mounted () {
    this.aoMudar = () => { this.movel = ecraPequeno() }
    window.addEventListener('resize', this.aoMudar, { passive: true })
  },
  beforeUnmount () { window.removeEventListener('resize', this.aoMudar) },
  methods: {
    aoErroVideo () {
      if (this.tentativa === 0 && this.fonteVideo !== this.media.url) {
        this.tentativa = 1
        this.$nextTick(() => this.$refs.video?.play?.().catch(() => {}))
      }
    },
    clique (e, link) {
      if (e.ctrlKey || e.metaKey || e.shiftKey) return
      e.preventDefault()
      this.$emit('acao', link)
    },
  },
}
</script>
