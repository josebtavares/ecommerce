<!-- LandingApp.vue — "Baixa a app": uma faixa com as cores da Bende e, por cima, um cartão claro com o título, as
     vantagens da app e os botões das lojas (Google Play sempre; App Store só com link). À direita, um telemóvel com a
     imagem da secção (uma captura da app) ou um ecrã com o logo. Sem link do Google Play → botão "Em breve".
     Começa escondida (utils/landing.py): o admin liga-a no editor quando a app estiver publicada. -->
<template>
  <section id="app" class="landing-seccao relative overflow-hidden px-5 sm:px-8 py-16 sm:py-24" data-teste="landing-app"
           :class="[visivel ? 'visivel' : '', isDark ? 'bg-gradient-to-br from-red-700 via-red-800 to-zinc-950' : 'bg-gradient-to-br from-orange-400 via-orange-500 to-rose-500']">
    <span aria-hidden="true" class="absolute inset-0 pontos opacity-15"></span>
    <span aria-hidden="true" class="absolute -right-24 -top-24 w-96 h-96 rounded-full border-[3rem] border-white/10"></span>
    <span aria-hidden="true" class="absolute -left-20 -bottom-28 w-80 h-80 rounded-full bg-white/10"></span>

    <div class="cartao relative max-w-6xl mx-auto rounded-[2rem] shadow-2xl grid lg:grid-cols-[7fr_5fr] items-center gap-10 lg:gap-6 px-6 sm:px-12 lg:px-16 py-12 sm:py-16"
         :class="isDark ? 'bg-zinc-900 shadow-black/40' : 'bg-white shadow-orange-900/20'">
      <div class="texto">
        <LandingCabecalho :etiqueta="s.nav" :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />

        <ul v-if="(s.itens || []).length" class="mt-8 grid gap-5 sm:grid-cols-2" data-teste="app-itens">
          <li v-for="(it, n) in s.itens" :key="it.id || n" class="vantagem flex items-start gap-3" :style="{ '--atraso': (n * 90) + 'ms' }">
            <span class="w-11 h-11 flex-shrink-0 rounded-xl flex items-center justify-center"
                  :class="isDark ? 'bg-red-500/15 text-red-400' : 'bg-orange-100 text-orange-600'">
              <font-awesome-icon :icon="['fas', icone(it.icone)]" class="text-lg" />
            </span>
            <span class="min-w-0">
              <span class="titulo-landing block font-semibold" :class="isDark ? 'text-zinc-100' : 'text-slate-900'">{{ it.titulo }}</span>
              <span v-if="it.texto" class="block mt-0.5 text-sm leading-relaxed" :class="isDark ? 'text-zinc-400' : 'text-slate-500'">{{ it.texto }}</span>
            </span>
          </li>
        </ul>

        <div class="mt-10 flex flex-wrap gap-3">
          <component :is="s.play_store ? 'a' : 'span'" :href="s.play_store || undefined" :target="s.play_store ? '_blank' : undefined"
                     :rel="s.play_store ? 'noopener' : undefined" data-teste="app-play"
                     :aria-disabled="s.play_store ? undefined : 'true'"
                     class="loja inline-flex items-center gap-3 pl-4 pr-6 py-2.5 rounded-xl border transition"
                     :class="s.play_store ? 'bg-black text-white border-black hover:-translate-y-0.5 hover:shadow-lg' : (isDark ? 'bg-zinc-800 text-zinc-400 border-zinc-700 cursor-default' : 'bg-slate-100 text-slate-500 border-slate-200 cursor-default')">
            <i class="fa-brands fa-google-play text-2xl" aria-hidden="true"></i>
            <span class="text-left leading-tight">
              <span class="block text-[10px] font-semibold uppercase tracking-wider opacity-80">{{ s.play_store ? 'Disponível no' : 'Em breve no' }}</span>
              <span class="block text-lg font-semibold -mt-0.5">Google Play</span>
            </span>
          </component>
          <a v-if="s.app_store" :href="s.app_store" target="_blank" rel="noopener" data-teste="app-apple"
             class="loja inline-flex items-center gap-3 pl-4 pr-6 py-2.5 rounded-xl border bg-black text-white border-black transition hover:-translate-y-0.5 hover:shadow-lg">
            <i class="fa-brands fa-apple text-3xl" aria-hidden="true"></i>
            <span class="text-left leading-tight">
              <span class="block text-[10px] font-semibold uppercase tracking-wider opacity-80">Descarregar na</span>
              <span class="block text-lg font-semibold -mt-0.5">App Store</span>
            </span>
          </a>
        </div>
      </div>

      <!-- telemóvel -->
      <div class="telemovel relative flex justify-center lg:-my-28">
        <span aria-hidden="true" class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 sm:w-80 sm:h-80 rounded-full"
              :class="isDark ? 'bg-red-500/15' : 'bg-orange-100'"></span>
        <div class="relative w-60 sm:w-64 aspect-[9/19] rounded-[2.6rem] p-2.5 shadow-2xl rotate-[4deg]"
             :class="isDark ? 'bg-black ring-2 ring-zinc-600' : 'bg-zinc-900 ring-1 ring-black/10'">
          <span aria-hidden="true" class="absolute top-4 left-1/2 -translate-x-1/2 w-20 h-5 rounded-full bg-black z-10"></span>
          <div class="w-full h-full rounded-[2.1rem] overflow-hidden" data-teste="app-ecra">
            <LandingFoto v-if="s.media" :media="s.media" />
            <div v-else class="w-full h-full flex flex-col"
                 :class="isDark ? 'bg-gradient-to-b from-red-600 to-zinc-950' : 'bg-gradient-to-b from-orange-400 to-rose-500'">
              <div class="flex-1 flex items-center justify-center">
                <img :src="logo" alt="Bende" class="w-28 h-28 object-contain drop-shadow-lg" />
              </div>
              <div class="px-4 pb-8 space-y-2" aria-hidden="true">
                <span class="block h-10 rounded-xl bg-white/20"></span>
                <span class="block h-10 rounded-xl bg-white/15"></span>
                <span class="block h-10 w-2/3 rounded-xl bg-white/10"></span>
              </div>
            </div>
          </div>
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
import logo from '@/assets/img/login/logo_final_640_light.webp'

export default {
  name: 'LandingApp',
  components: { LandingCabecalho, LandingFoto },
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
  },
  data () { return { logo } },
  methods: {
    icone (i) { return i && findIconDefinition({ prefix: 'fas', iconName: i }) ? i : 'circle-check' },
  },
}
</script>

<style scoped>
.pontos { background-image: radial-gradient(circle, #fff 1.5px, transparent 1.5px); background-size: 26px 26px; }
.cartao, .telemovel, .vantagem { opacity: 0; }
.visivel .cartao { opacity: 1; animation: subir .7s ease backwards; }
.visivel .telemovel { opacity: 1; animation: telemovel 1s ease backwards; animation-delay: .25s; }
.visivel .vantagem { opacity: 1; animation: subir .6s ease backwards; animation-delay: calc(var(--atraso) + 350ms); }
@keyframes subir { from { opacity: 0; transform: translateY(1.25rem); } }
@keyframes telemovel { from { opacity: 0; transform: translateY(3rem) rotate(-4deg); } }
@media (prefers-reduced-motion: reduce) { .cartao, .telemovel, .vantagem { opacity: 1; animation: none !important; } }
</style>
