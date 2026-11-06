<!-- LandingLojas.vue — "Para lojas": uma faixa escura (nos dois temas) com as funcionalidades em mosaico. A primeira é o
     destaque (grande, com a imagem/vídeo da secção por fundo, se houver); as outras têm tamanhos diferentes conforme
     quantas são, para o mosaico ficar sempre completo. -->
<template>
  <section :id="s.tipo" class="landing-seccao relative overflow-hidden py-20 sm:py-28 px-5 sm:px-8 text-white"
           :data-teste="'landing-' + s.tipo" :class="[isDark ? 'bg-black' : 'bg-zinc-900', { visivel }]">
    <!-- luzes de fundo -->
    <span aria-hidden="true" class="pointer-events-none absolute -top-40 -left-32 w-[36rem] h-[36rem] rounded-full blur-3xl opacity-30"
          :class="isDark ? 'bg-red-700' : 'bg-orange-500'"></span>
    <span aria-hidden="true" class="pointer-events-none absolute -bottom-48 -right-24 w-[30rem] h-[30rem] rounded-full blur-3xl opacity-20"
          :class="isDark ? 'bg-rose-900' : 'bg-amber-400'"></span>
    <span aria-hidden="true" class="pointer-events-none absolute inset-0 grelha-pontos opacity-[0.07]"></span>

    <div class="relative max-w-7xl mx-auto">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
        <div class="max-w-2xl">
          <span v-if="s.nav" class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest bg-white/10 text-white/80">
            <font-awesome-icon :icon="['fas', 'store']" class="w-3 h-3" />{{ s.nav }}</span>
          <h2 class="mt-5 text-3xl sm:text-5xl font-extrabold tracking-tight leading-[1.1] whitespace-pre-line">{{ s.titulo }}</h2>
          <p v-if="s.subtitulo" class="mt-4 text-lg leading-relaxed text-white/70 whitespace-pre-line">{{ s.subtitulo }}</p>
        </div>
        <a v-if="s.botao" :href="s.botao.link" @click="clique($event, s.botao.link)" :data-teste="s.tipo + '-botao'"
           class="group self-start lg:self-auto flex-shrink-0 inline-flex items-center gap-3 px-6 py-3.5 rounded-2xl font-bold bg-white text-zinc-900 shadow-xl transition hover:-translate-y-0.5">
          {{ s.botao.texto }}
          <font-awesome-icon :icon="['fas', 'arrow-right']" class="w-4 h-4 transition group-hover:translate-x-1" :class="isDark ? 'text-red-600' : 'text-orange-500'" />
        </a>
      </div>

      <ul class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-6 lg:auto-rows-[minmax(10.5rem,auto)]">
        <li v-for="(c, n) in itens" :key="c.id" data-teste="cartao"
            class="peca group relative overflow-hidden rounded-3xl transition duration-300 hover:-translate-y-1"
            :class="[tamanho(n), n === 0 ? 'destaque' : 'border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] hover:border-white/25 backdrop-blur-sm']"
            :style="{ '--atraso': (n * 70) + 'ms' }">
          <!-- destaque: média da secção por fundo, ou um gradiente -->
          <template v-if="n === 0">
            <template v-if="s.media">
              <video v-if="s.media.tipo === 'video'" :src="s.media.url" :poster="s.media.poster || undefined" autoplay muted loop playsinline
                     class="absolute inset-0 w-full h-full object-cover transition duration-700 group-hover:scale-105" aria-hidden="true"></video>
              <img v-else :src="s.media.url" alt="" loading="lazy" class="absolute inset-0 w-full h-full object-cover transition duration-700 group-hover:scale-105" />
              <span class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-black/10"></span>
            </template>
            <span v-else class="absolute inset-0" :class="isDark ? 'bg-gradient-to-br from-red-600 via-red-800 to-zinc-900' : 'bg-gradient-to-br from-orange-500 via-orange-600 to-rose-700'"></span>
            <font-awesome-icon v-if="!s.media" :icon="['fas', icone(c.icone)]" aria-hidden="true"
                               class="absolute right-6 top-6 text-[9rem] sm:text-[12rem] text-white/10 transition duration-500 group-hover:rotate-6" />
            <div class="relative h-full min-h-[16rem] p-7 sm:p-9 flex flex-col justify-end">
              <span class="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
                <font-awesome-icon :icon="['fas', icone(c.icone)]" class="text-2xl" /></span>
              <h3 class="mt-5 text-2xl sm:text-3xl font-extrabold">{{ c.titulo }}</h3>
              <p v-if="c.texto" class="mt-2 max-w-md text-white/85 leading-relaxed whitespace-pre-line">{{ c.texto }}</p>
            </div>
          </template>

          <div v-else class="h-full p-5 sm:p-6 grid grid-cols-[auto_1fr] gap-x-4 content-start sm:flex sm:flex-col">
            <span class="row-span-2 w-11 h-11 rounded-xl flex items-center justify-center transition group-hover:scale-110"
                  :class="isDark ? 'bg-red-600/20 text-red-400' : 'bg-orange-500/20 text-orange-300'">
              <font-awesome-icon :icon="['fas', icone(c.icone)]" class="w-5 h-5" /></span>
            <h3 class="sm:mt-auto sm:pt-6 text-lg font-bold">{{ c.titulo }}</h3>
            <p v-if="c.texto" class="mt-1 text-sm leading-relaxed text-white/60 whitespace-pre-line">{{ c.texto }}</p>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script>
import { findIconDefinition } from '@fortawesome/fontawesome-svg-core'
import revelar from './revelar'

export default {
  name: 'LandingLojas',
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
  },
  emits: ['acao'],
  computed: {
    itens () { return this.s.itens || [] },
  },
  methods: {
    // colunas de cada peça (6 no computador, 2 no tablet), para nunca sobrar um buraco no mosaico
    tamanho (n) {
      const total = this.itens.length
      const ultimo = n === total - 1
      // tablet: o destaque ocupa a linha toda; o último fica largo se sobrar sozinho
      const sm = n === 0 || (ultimo && (total - 1) % 2 === 1) ? 'sm:col-span-2' : ''
      let lg
      if (total === 1) lg = 'lg:col-span-6'
      else if (total === 2) lg = 'lg:col-span-3'
      else if (n === 0) lg = 'lg:col-span-3 lg:row-span-2'
      else if (n <= 2) lg = 'lg:col-span-3'
      else {
        const resto = total - 3                         // depois do destaque e das duas ao lado: filas de 3
        const pos = n - 3
        const naUltimaFila = pos >= resto - (resto % 3)
        if (naUltimaFila && resto % 3 === 1) lg = 'lg:col-span-6'
        else if (naUltimaFila && resto % 3 === 2) lg = 'lg:col-span-3'
        else lg = 'lg:col-span-2'
      }
      return `${sm} ${lg}`
    },
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
.grelha-pontos { background-image: radial-gradient(circle, #fff 1px, transparent 1px); background-size: 22px 22px; }
/* entrada: animação (não transição), para o atraso de cada peça não atrasar o efeito do rato */
.peca { opacity: 0; }
.visivel .peca { opacity: 1; animation: entrar .6s ease backwards; animation-delay: var(--atraso); }
@keyframes entrar { from { opacity: 0; transform: translateY(1.25rem) scale(.98); } }
.destaque { box-shadow: 0 30px 60px -20px rgba(0, 0, 0, .6); }
@media (prefers-reduced-motion: reduce) { .peca { opacity: 1; animation: none; } }
</style>
