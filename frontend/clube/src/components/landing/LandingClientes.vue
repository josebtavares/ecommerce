<!-- LandingClientes.vue — "Para clientes": colagem de duas fotos à esquerda (a pequena por cima da grande, com o selo
     dos passos), e à direita o letreiro, o título, o texto, os passos e os botões. Sem fotos, blocos com as cores da
     Bende ocupam o lugar delas. -->
<template>
  <section :id="s.tipo" class="landing-seccao py-20 sm:py-28 px-5 sm:px-8 overflow-hidden" :data-teste="'landing-' + s.tipo"
           :class="[alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : '', { visivel }]">
    <div class="max-w-6xl mx-auto grid lg:grid-cols-2 gap-14 lg:gap-20 items-center">
      <!-- colagem -->
      <div class="colagem relative mx-auto w-full max-w-lg lg:max-w-none aspect-[1/1] sm:aspect-[6/5]">
        <span aria-hidden="true" class="absolute -left-6 top-10 w-[70%] h-[80%] rounded-[3rem] -rotate-6"
              :class="isDark ? 'bg-red-600/10' : 'bg-orange-100/70'"></span>
        <div class="foto-grande absolute right-0 top-0 w-[78%] h-[80%] rounded-2xl overflow-hidden shadow-2xl"
             :class="isDark ? 'shadow-black/50' : 'shadow-slate-900/15'">
          <LandingFoto v-if="s.media" :media="s.media" />
          <div v-else class="w-full h-full flex items-center justify-center"
               :class="isDark ? 'bg-gradient-to-br from-zinc-800 to-zinc-900' : 'bg-gradient-to-br from-orange-100 to-rose-100'">
            <font-awesome-icon :icon="['fas', 'bag-shopping']" class="text-[8rem] sm:text-[10rem]" :class="isDark ? 'text-zinc-700' : 'text-orange-300'" />
          </div>
        </div>
        <div class="foto-pequena absolute left-0 bottom-0 w-[50%] h-[42%] rounded-2xl overflow-hidden shadow-2xl border-[6px] sm:border-8"
             :class="isDark ? 'border-zinc-950 shadow-black/60' : 'border-white shadow-slate-900/20'">
          <LandingFoto v-if="s.media2" :media="s.media2" />
          <div v-else class="w-full h-full flex items-center justify-center"
               :class="isDark ? 'bg-gradient-to-br from-red-600 to-red-800' : 'bg-gradient-to-br from-orange-500 to-rose-500'">
            <font-awesome-icon :icon="['fas', 'truck-fast']" class="text-5xl sm:text-6xl text-white/90" />
          </div>
        </div>
        <!-- selo -->
        <div v-if="passos.length" class="selo absolute right-[6%] bottom-[14%] w-28 h-28 sm:w-32 sm:h-32 flex flex-col items-center justify-center text-white shadow-xl"
             :class="isDark ? 'bg-red-600' : 'bg-orange-500'">
          <span class="titulo-landing text-4xl sm:text-5xl font-bold leading-none">{{ passos.length }}</span>
          <span class="mt-1 text-[0.7rem] font-semibold uppercase tracking-widest text-white/85">passos</span>
        </div>
      </div>

      <!-- texto -->
      <div>
        <LandingCabecalho :etiqueta="s.nav" :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />

        <ol class="mt-9 space-y-6">
          <li v-for="(c, n) in passos" :key="c.id" data-teste="cartao" class="passo flex gap-5" :style="{ '--atraso': (n * 110) + 'ms' }">
            <span class="relative flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center"
                  :class="isDark ? 'bg-red-600/15 text-red-400' : 'bg-orange-50 text-orange-500'">
              <font-awesome-icon :icon="['fas', icone(c.icone)]" class="text-xl" />
              <span class="absolute -top-2 -right-2 w-6 h-6 rounded-full text-[0.65rem] font-bold flex items-center justify-center"
                    :class="isDark ? 'bg-zinc-100 text-zinc-900' : 'bg-slate-900 text-white'">{{ n + 1 }}</span>
            </span>
            <div class="min-w-0">
              <h3 class="titulo-landing text-lg font-semibold" :class="isDark ? 'text-zinc-100' : 'text-slate-900'">{{ c.titulo }}</h3>
              <p v-if="c.texto" class="mt-1 leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-slate-500'">{{ c.texto }}</p>
            </div>
          </li>
        </ol>

        <div v-if="s.botao || temTutoriais" class="mt-10 flex flex-wrap items-center gap-6">
          <a v-if="s.botao" :href="s.botao.link" @click="clique($event, s.botao.link)" :data-teste="s.tipo + '-botao'"
             class="inline-flex items-center px-8 py-4 rounded-full font-semibold text-white shadow-lg transition hover:-translate-y-0.5"
             :class="isDark ? 'bg-red-600 shadow-red-900/30' : 'bg-orange-500 shadow-orange-500/30'">{{ s.botao.texto }}</a>
          <span v-if="s.botao && temTutoriais" class="hidden sm:block w-px h-8" :class="isDark ? 'bg-zinc-700' : 'bg-slate-200'"></span>
          <a v-if="temTutoriais" href="#tutoriais" @click="clique($event, '#tutoriais')" data-teste="clientes-tutoriais"
             class="group inline-flex items-center gap-4 font-medium" :class="isDark ? 'text-zinc-200' : 'text-slate-800'">
            <span class="w-14 h-14 rounded-full flex items-center justify-center transition group-hover:scale-110"
                  :class="isDark ? 'bg-zinc-800 text-white' : 'bg-slate-100 text-slate-900'">
              <font-awesome-icon :icon="['fas', 'play']" class="text-base ml-0.5" /></span>
            Ver os tutoriais
          </a>
        </div>
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
  name: 'LandingClientes',
  components: { LandingCabecalho, LandingFoto },
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
    temTutoriais: { type: Boolean, default: false },   // a secção de tutoriais está na página → botão "Ver os tutoriais"
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
.selo { border-radius: 1.25rem 1.25rem 1.25rem 0.25rem; }
/* entrada: as fotos deslizam de lados opostos, os passos aparecem um a um */
.foto-grande, .foto-pequena, .selo, .passo { opacity: 0; }
.visivel .foto-grande { opacity: 1; animation: daDireita .8s ease backwards; }
.visivel .foto-pequena { opacity: 1; animation: deBaixo .8s .15s ease backwards; }
.visivel .selo { opacity: 1; animation: aparecer .6s .45s ease backwards; }
.visivel .passo { opacity: 1; animation: daDireita .6s ease backwards; animation-delay: calc(var(--atraso) + 200ms); }
@keyframes daDireita { from { opacity: 0; transform: translateX(1.5rem); } }
@keyframes deBaixo { from { opacity: 0; transform: translateY(1.5rem); } }
@keyframes aparecer { from { opacity: 0; transform: scale(.8); } }
@media (prefers-reduced-motion: reduce) { .foto-grande, .foto-pequena, .selo, .passo { opacity: 1; animation: none !important; } }
</style>
