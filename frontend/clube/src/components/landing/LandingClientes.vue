<!-- LandingClientes.vue — "Para clientes": um percurso. À esquerda o título (fica parado ao deslizar, no computador) e o
     botão; à direita os passos numa linha do tempo, que vão aparecendo um a um. -->
<template>
  <section :id="s.tipo" class="landing-seccao relative overflow-hidden py-20 sm:py-28 px-5 sm:px-8" :data-teste="'landing-' + s.tipo"
           :class="[alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : '', { visivel }]">

    <div class="relative max-w-6xl mx-auto grid lg:grid-cols-[5fr_7fr] gap-12 lg:gap-20">
      <div class="lg:sticky lg:top-28 self-start">
        <span v-if="s.nav" class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest"
              :class="isDark ? 'bg-red-600/15 text-red-400' : 'bg-orange-100 text-orange-700'">
          <font-awesome-icon :icon="['fas', 'bag-shopping']" class="w-3 h-3" />{{ s.nav }}</span>
        <h2 class="mt-5 text-3xl sm:text-5xl font-extrabold tracking-tight leading-[1.1] whitespace-pre-line"
            :class="isDark ? 'text-white' : 'text-zinc-900'">{{ s.titulo }}</h2>
        <p v-if="s.subtitulo" class="mt-4 text-lg leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ s.subtitulo }}</p>
        <a v-if="s.botao" :href="s.botao.link" @click="clique($event, s.botao.link)" :data-teste="s.tipo + '-botao'"
           class="group mt-8 inline-flex items-center gap-3 pl-6 pr-2 py-2 rounded-full font-bold text-white shadow-lg transition hover:shadow-xl"
           :class="isDark ? 'bg-red-600 shadow-red-900/30' : 'bg-orange-500 shadow-orange-500/30'">
          {{ s.botao.texto }}
          <span class="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center transition group-hover:translate-x-1">
            <font-awesome-icon :icon="['fas', 'arrow-right']" class="w-4 h-4" /></span>
        </a>
      </div>

      <ol class="relative">
        <!-- a linha que liga os passos -->
        <span aria-hidden="true" class="absolute left-7 top-7 bottom-7 w-px"
              :class="isDark ? 'bg-gradient-to-b from-red-500 via-zinc-700 to-transparent' : 'bg-gradient-to-b from-orange-400 via-stone-300 to-transparent'"></span>
        <li v-for="(c, n) in passos" :key="c.id" data-teste="cartao" class="passo group relative flex gap-6 pb-10 last:pb-0"
            :style="{ transitionDelay: (n * 120) + 'ms' }">
          <span class="relative z-10 flex-shrink-0 w-14 h-14 rounded-full flex items-center justify-center text-lg font-black border-2 transition-colors"
                :class="isDark ? 'bg-zinc-950 border-red-500 text-red-400 group-hover:bg-red-600 group-hover:text-white'
                               : 'bg-white border-orange-400 text-orange-600 group-hover:bg-orange-500 group-hover:text-white'">
            {{ String(n + 1).padStart(2, '0') }}</span>
          <div class="pt-2 min-w-0">
            <h3 class="flex items-center gap-2.5 text-xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
              <font-awesome-icon :icon="['fas', icone(c.icone)]" class="w-5 h-5" :class="isDark ? 'text-red-400' : 'text-orange-500'" />
              {{ c.titulo }}</h3>
            <p v-if="c.texto" class="mt-2 max-w-xl leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ c.texto }}</p>
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>

<script>
import { findIconDefinition } from '@fortawesome/fontawesome-svg-core'
import revelar from './revelar'

export default {
  name: 'LandingClientes',
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
  emits: ['acao'],
  computed: {
    passos () { return this.s.passos || [] },
  },
  methods: {
    // ícone que não exista no Font Awesome → um genérico (o admin escreve o nome)
    icone (nome) { return nome && findIconDefinition({ prefix: 'fas', iconName: nome }) ? nome : 'circle-check' },
    clique (e, link) {
      if (e.ctrlKey || e.metaKey || e.shiftKey) return
      e.preventDefault()
      this.$emit('acao', link)
    },
  },
}
</script>

<style scoped>
.passo { opacity: 0; transform: translateX(1.5rem); transition: opacity .6s ease, transform .6s ease; }
.visivel .passo { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) { .passo { opacity: 1; transform: none; transition: none; } }
</style>
