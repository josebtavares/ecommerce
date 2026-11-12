<!-- LandingBackoffice.vue — "Backoffice": mostra o painel da loja por dentro, um módulo de cada vez.
     À esquerda a lista dos módulos (no telemóvel, botões que deslizam); à direita uma janela de browser com a captura
     de ecrã do módulo escolhido e, por baixo, o texto e os pontos fortes (uma linha = um ponto).
     Sem captura, a janela mostra um esboço do backoffice com o ícone do módulo. Os módulos mudam sozinhos
     até o visitante escolher um (e param com o rato por cima ou com "reduzir movimento"). -->
<template>
  <section :id="s.tipo" class="landing-seccao relative overflow-hidden px-5 sm:px-8 py-20 sm:py-28" :data-teste="'landing-' + s.tipo"
           :class="[{ visivel }, isDark ? 'bg-zinc-900' : 'bg-slate-50']">
    <span aria-hidden="true" class="absolute -right-40 top-24 w-[34rem] h-[34rem] rounded-full blur-3xl"
          :class="isDark ? 'bg-red-600/10' : 'bg-orange-200/40'"></span>

    <div class="relative max-w-6xl mx-auto">
      <LandingCabecalho :etiqueta="s.nav" :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" centro />

      <div v-if="modulos.length" class="mt-12 sm:mt-16 grid gap-8 lg:grid-cols-[17rem_1fr] lg:gap-12 items-start"
           @mouseenter="pausa = true" @mouseleave="pausa = false">
        <!-- módulos -->
        <div class="lista -mx-5 px-5 sm:mx-0 sm:px-0 flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-1 lg:pb-0"
             role="tablist" aria-label="Módulos do backoffice" data-teste="backoffice-modulos" @keydown="teclado">
          <button v-for="(m, n) in modulos" :key="m.id || n" type="button" role="tab" :id="'bo-tab-' + n"
                  :aria-selected="n === atual" :aria-controls="'bo-painel'" :tabindex="n === atual ? 0 : -1"
                  :data-teste="'backoffice-modulo-' + n" @click="escolher(n)" :style="{ '--atraso': (n * 60) + 'ms' }"
                  class="modulo relative flex-shrink-0 flex items-center gap-3 text-left rounded-xl px-3.5 py-2.5 lg:py-3 transition"
                  :class="n === atual
                    ? (isDark ? 'bg-zinc-800 text-white ring-1 ring-zinc-700 shadow-lg shadow-black/30' : 'bg-white text-slate-900 shadow-lg shadow-slate-900/10 ring-1 ring-slate-200')
                    : (isDark ? 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60' : 'text-slate-500 hover:text-slate-900 hover:bg-white/70')">
            <span class="w-9 h-9 flex-shrink-0 rounded-lg flex items-center justify-center transition"
                  :class="n === atual ? (isDark ? 'bg-red-600 text-white' : 'bg-orange-500 text-white') : (isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-slate-200/70 text-slate-500')">
              <font-awesome-icon :icon="['fas', icone(m.icone)]" class="text-sm" />
            </span>
            <span class="titulo-landing text-sm font-semibold whitespace-nowrap lg:whitespace-normal">{{ m.titulo }}</span>
            <!-- barra do tempo até ao módulo seguinte -->
            <span v-if="n === atual && automatico" aria-hidden="true" :key="'b' + volta"
                  class="progresso hidden lg:block absolute left-3.5 right-3.5 bottom-1 h-0.5 rounded origin-left"
                  :class="[isDark ? 'bg-red-500/70' : 'bg-orange-400/80', pausa ? 'parado' : '']"
                  :style="{ animationDuration: INTERVALO + 'ms' }"></span>
          </button>
        </div>

        <!-- janela + texto -->
        <div id="bo-painel" role="tabpanel" :aria-labelledby="'bo-tab-' + atual" class="janela-bloco min-w-0">
          <div class="rounded-2xl overflow-hidden shadow-2xl ring-1"
               :class="isDark ? 'bg-zinc-950 ring-zinc-700 shadow-black/50' : 'bg-white ring-slate-200 shadow-slate-900/15'">
            <div class="flex items-center gap-2 px-4 py-2.5 border-b" :class="isDark ? 'border-zinc-800 bg-zinc-900' : 'border-slate-200 bg-slate-100'">
              <span class="w-3 h-3 rounded-full bg-red-400"></span>
              <span class="w-3 h-3 rounded-full bg-amber-400"></span>
              <span class="w-3 h-3 rounded-full bg-green-400"></span>
              <span class="ml-3 flex-1 max-w-sm truncate rounded-md px-3 py-1 text-[11px]"
                    :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-white text-slate-500'">
                <font-awesome-icon :icon="['fas', 'lock']" class="mr-1.5 text-[9px] text-green-500" />e-bendi.cv/backoffice
              </span>
            </div>
            <div class="relative aspect-[16/10]" data-teste="backoffice-ecra">
              <transition name="troca" mode="out-in">
                <div :key="atual" class="absolute inset-0">
                  <LandingFoto v-if="modulo.media" :media="modulo.media" class="object-top" />
                  <!-- esboço do backoffice quando ainda não há captura -->
                  <div v-else class="w-full h-full flex" aria-hidden="true" data-teste="backoffice-esboco">
                    <div class="w-1/5 hidden sm:flex flex-col gap-2 p-3" :class="isDark ? 'bg-zinc-900' : 'bg-slate-50'">
                      <span class="h-6 w-2/3 rounded mb-2" :class="isDark ? 'bg-red-600/60' : 'bg-orange-400/70'"></span>
                      <span v-for="i in 7" :key="i" class="h-3 rounded" :class="[isDark ? 'bg-zinc-800' : 'bg-slate-200', i === (atual % 7) + 1 ? (isDark ? '!bg-red-500/50' : '!bg-orange-300') : '']"></span>
                    </div>
                    <div class="flex-1 p-4 sm:p-6 flex flex-col gap-3">
                      <div class="flex items-center gap-3">
                        <span class="w-10 h-10 rounded-xl flex items-center justify-center" :class="isDark ? 'bg-red-600 text-white' : 'bg-orange-500 text-white'">
                          <font-awesome-icon :icon="['fas', icone(modulo.icone)]" />
                        </span>
                        <span class="h-4 w-40 rounded" :class="isDark ? 'bg-zinc-700' : 'bg-slate-300'"></span>
                      </div>
                      <div class="grid grid-cols-3 gap-3">
                        <span v-for="i in 3" :key="i" class="h-14 sm:h-20 rounded-xl" :class="isDark ? 'bg-zinc-800' : 'bg-slate-100'"></span>
                      </div>
                      <div class="flex-1 rounded-xl flex items-end gap-2 p-3" :class="isDark ? 'bg-zinc-900' : 'bg-slate-50'">
                        <span v-for="(h, i) in BARRAS" :key="i" class="flex-1 rounded-t" :style="{ height: h + '%' }"
                              :class="isDark ? 'bg-red-500/40' : 'bg-orange-300/80'"></span>
                      </div>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </div>

          <transition name="troca" mode="out-in">
            <div :key="atual" class="mt-8 grid gap-6 md:grid-cols-[1fr_auto] md:gap-10" data-teste="backoffice-texto">
              <div>
                <h3 class="titulo-landing text-2xl font-bold" :class="isDark ? 'text-white' : 'text-slate-900'">{{ modulo.titulo }}</h3>
                <p v-if="modulo.texto" class="mt-2 leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-slate-500'">{{ modulo.texto }}</p>
              </div>
              <ul v-if="pontos.length" class="space-y-2 md:min-w-[16rem]" data-teste="backoffice-pontos">
                <li v-for="(p, i) in pontos" :key="i" class="flex items-start gap-2.5 text-sm" :class="isDark ? 'text-zinc-300' : 'text-slate-700'">
                  <font-awesome-icon :icon="['fas', 'circle-check']" class="mt-0.5 flex-shrink-0" :class="isDark ? 'text-red-400' : 'text-orange-500'" />
                  <span>{{ p }}</span>
                </li>
              </ul>
            </div>
          </transition>
        </div>
      </div>

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

const INTERVALO = 7000
const BARRAS = [35, 55, 40, 70, 50, 85, 60, 75]

export default {
  name: 'LandingBackoffice',
  components: { LandingCabecalho, LandingFoto },
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
  },
  emits: ['acao'],
  data () {
    return { atual: 0, automatico: true, pausa: false, volta: 0, INTERVALO, BARRAS }
  },
  computed: {
    modulos () { return this.s.modulos || [] },
    modulo () { return this.modulos[this.atual] || this.modulos[0] || {} },
    pontos () { return (this.modulo.pontos || '').split('\n').map(p => p.trim()).filter(Boolean) },
  },
  watch: {
    modulos () { if (this.atual >= this.modulos.length) this.atual = 0 },
    visivel (v) { if (v) this.arrancar() },
  },
  mounted () {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) this.automatico = false
  },
  beforeUnmount () { clearInterval(this.relogio) },
  methods: {
    icone (nome) { return nome && findIconDefinition({ prefix: 'fas', iconName: nome }) ? nome : 'circle-check' },
    arrancar () {
      if (!this.automatico || this.relogio) return
      // conta o tempo aos bocados para a pausa (rato por cima, separador escondido) não saltar módulos
      let passado = 0
      this.relogio = setInterval(() => {
        if (this.pausa || document.hidden || this.modulos.length < 2) return
        passado += 250
        if (passado >= INTERVALO) { passado = 0; this.atual = (this.atual + 1) % this.modulos.length; this.volta++ }
      }, 250)
    },
    escolher (n) {
      this.atual = n
      this.automatico = false
      clearInterval(this.relogio)
      this.relogio = null
      // no telemóvel, o botão escolhido fica à vista
      this.$nextTick(() => document.getElementById('bo-tab-' + n)?.scrollIntoView?.({ block: 'nearest', inline: 'center', behavior: 'smooth' }))
    },
    teclado (e) {
      const passo = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
      if (!passo) return
      e.preventDefault()
      const n = (this.atual + passo + this.modulos.length) % this.modulos.length
      this.escolher(n)
      document.getElementById('bo-tab-' + n)?.focus()
    },
    clique (e, link) {
      if (e.ctrlKey || e.metaKey || e.shiftKey) return
      e.preventDefault()
      this.$emit('acao', link)
    },
  },
}
</script>

<style scoped>
.lista { scrollbar-width: none; }
.lista::-webkit-scrollbar { display: none; }
.modulo, .janela-bloco { opacity: 0; }
.visivel .modulo { opacity: 1; animation: subir .6s ease backwards; animation-delay: var(--atraso); }
.visivel .janela-bloco { opacity: 1; animation: subir .8s ease backwards; animation-delay: .2s; }
@keyframes subir { from { opacity: 0; transform: translateY(1.5rem); } }
.progresso { animation: encher linear forwards; }
.progresso.parado { animation-play-state: paused; }
@keyframes encher { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.troca-enter-active, .troca-leave-active { transition: opacity .25s ease, transform .25s ease; }
.troca-enter-from { opacity: 0; transform: translateY(.5rem); }
.troca-leave-to { opacity: 0; }
:deep(img), :deep(video) { object-position: top; }
@media (prefers-reduced-motion: reduce) {
  .modulo, .janela-bloco { opacity: 1; animation: none !important; }
  .troca-enter-active, .troca-leave-active { transition: none; }
}
</style>
