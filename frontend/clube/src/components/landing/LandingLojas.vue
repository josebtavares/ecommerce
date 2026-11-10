<!-- LandingLojas.vue — "Para lojas": faixa no topo (a foto/vídeo da secção escurecida, ou um cinzento suave) com o
     letreiro e o título ao centro; os cartões brancos das funcionalidades começam dentro da faixa e saem dela.
     Ao passar o rato, o cartão ganha a cor da Bendi. Por baixo, o botão. -->
<template>
  <section :id="s.tipo" class="landing-seccao" :data-teste="'landing-' + s.tipo" :class="{ visivel }">
    <div class="faixa relative overflow-hidden px-5 sm:px-8 pt-20 sm:pt-28 pb-44 sm:pb-52"
         :class="s.media ? 'bg-black' : (isDark ? 'bg-zinc-900' : 'bg-slate-100')">
      <template v-if="s.media">
        <div class="absolute inset-0"><LandingFoto :media="s.media" /></div>
        <span class="absolute inset-0 bg-slate-950/70"></span>
      </template>
      <div class="relative">
        <LandingCabecalho :etiqueta="s.nav" :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" :claro="!!s.media" centro />
      </div>
    </div>

    <div class="px-5 sm:px-8 pb-20 sm:pb-28" :class="isDark ? 'bg-zinc-950' : 'bg-white'">
      <ul class="relative -mt-32 sm:-mt-36 max-w-6xl mx-auto grid gap-6 sm:grid-cols-2" :class="colunas">
        <li v-for="(c, n) in itens" :key="c.id" data-teste="cartao" :style="{ '--atraso': (n * 80) + 'ms' }"
            class="cartao group relative overflow-hidden px-7 py-10 text-center shadow-xl transition duration-300 hover:-translate-y-2"
            :class="isDark ? 'bg-zinc-900 shadow-black/40 ring-1 ring-zinc-800 hover:bg-red-600' : 'bg-white shadow-slate-900/10 hover:bg-orange-500'">
          <span aria-hidden="true" class="absolute top-0 inset-x-0 h-1 origin-left scale-x-0 transition duration-300 group-hover:scale-x-100 bg-white/60"></span>
          <span class="mx-auto w-20 h-20 rounded-full flex items-center justify-center transition duration-300 group-hover:bg-white/20 group-hover:text-white"
                :class="isDark ? 'bg-red-600/10 text-red-400' : 'bg-orange-50 text-orange-500'">
            <font-awesome-icon :icon="['fas', icone(c.icone)]" class="text-3xl transition duration-300 group-hover:scale-110" />
          </span>
          <h3 class="titulo-landing mt-6 text-lg font-semibold transition-colors group-hover:text-white"
              :class="isDark ? 'text-zinc-100' : 'text-slate-900'">{{ c.titulo }}</h3>
          <p v-if="c.texto" class="mt-2 text-sm leading-relaxed whitespace-pre-line transition-colors group-hover:text-white/85"
             :class="isDark ? 'text-zinc-400' : 'text-slate-500'">{{ c.texto }}</p>
        </li>
      </ul>

      <div v-if="s.botao" class="mt-14 text-center">
        <a :href="s.botao.link" @click="clique($event, s.botao.link)" :data-teste="s.tipo + '-botao'"
           class="inline-flex items-center gap-3 px-9 py-4 rounded-full font-semibold text-white shadow-lg transition hover:-translate-y-0.5"
           :class="isDark ? 'bg-red-600 shadow-red-900/30' : 'bg-orange-500 shadow-orange-500/30'">
          {{ s.botao.texto }} <font-awesome-icon :icon="['fas', 'arrow-right']" class="text-sm" />
        </a>
      </div>
    </div>
  </section>
</template>

<script>
import { findIconDefinition } from '@fortawesome/fontawesome-svg-core'
import revelar from './revelar'
import LandingCabecalho from './LandingCabecalho.vue'
import LandingFoto from './LandingFoto.vue'

export default {
  name: 'LandingLojas',
  components: { LandingCabecalho, LandingFoto },
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
  },
  emits: ['acao'],
  computed: {
    itens () { return this.s.itens || [] },
    // 4 por fila quando a conta bate certo (4, 8, 12), senão 3 — filas sempre cheias sempre que possível
    colunas () { return this.itens.length % 4 === 0 && this.itens.length % 3 !== 0 ? 'lg:grid-cols-4' : 'lg:grid-cols-3' },
  },
  methods: {
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
.cartao { border-radius: 0.5rem; opacity: 0; }
.visivel .cartao { opacity: 1; animation: subir .7s ease backwards; animation-delay: var(--atraso); }
@keyframes subir { from { opacity: 0; transform: translateY(2rem); } }
@media (prefers-reduced-motion: reduce) { .cartao { opacity: 1; animation: none !important; } }
</style>
