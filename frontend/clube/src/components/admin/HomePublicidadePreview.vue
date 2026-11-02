<!-- HomePublicidadePreview.vue — Admin → Página inicial → secção Publicidade: o carrossel tal como fica na home,
     numa moldura de computador (desenhado a 1270 px, a largura real num ecrã 1366, e reduzido para caber) ou de
     telemóvel (358 px, a largura real num ecrã 390). Usa o próprio HomePublicidade (modo forçado, sem links). -->
<template>
  <div data-teste="pub-previa">
    <div class="flex items-center justify-between gap-2 mb-2 flex-wrap">
      <p class="text-xs text-zinc-400 font-medium">Pré-visualização (antes de guardar)</p>
      <div class="flex gap-1">
        <button v-for="m in MODOS" :key="m.v" type="button" @click="modo = m.v" :data-teste="'pub-previa-' + m.v"
          :class="['px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center gap-1.5',
                   modo === m.v ? 'border-red-500/60 text-red-300 bg-red-500/10' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500']">
          <font-awesome-icon :icon="['fas', m.icone]" /> {{ m.n }}
        </button>
      </div>
    </div>

    <!-- cores originais: no tema claro do Admin a paleta é trocada (tema-claro.css) e o anúncio deixava de ser igual à home -->
    <div class="pub-cores-originais rounded-2xl border border-zinc-800 bg-zinc-950 p-3 sm:p-4">
      <p v-if="!anuncios.length" class="text-xs text-zinc-500 py-10 text-center">
        {{ vazio || 'Sem anúncios com imagem ou vídeo activos agora: a secção não aparece na home.' }}
      </p>

      <!-- computador: desenha à largura real e reduz -->
      <div v-else-if="modo === 'computador'" ref="moldura" class="w-full overflow-hidden"
           :style="{ height: altura ? altura * escala + 'px' : 'auto' }">
        <div ref="interior" :style="{ width: LARGURA_PC + 'px', transform: `scale(${escala})`, transformOrigin: 'top left' }">
          <HomePublicidade modo="computador" :anuncios="anuncios" :proporcao="proporcao" :intervalo="intervalo"
                           :titulo="titulo" :subtitulo="subtitulo" :isDark="true" />
        </div>
      </div>

      <!-- telemóvel: largura real dentro de um "telefone" -->
      <div v-else class="mx-auto rounded-[2rem] border-4 border-zinc-800 bg-zinc-950 px-4 py-6" :style="{ width: LARGURA_TEL + 40 + 'px', maxWidth: '100%' }">
        <HomePublicidade modo="telemovel" :anuncios="anuncios" :proporcao="proporcao" :intervalo="intervalo"
                         :titulo="titulo" :subtitulo="subtitulo" :isDark="true" />
      </div>

      <p v-if="anuncios.length" class="text-[10px] text-zinc-600 mt-2">
        {{ modo === 'computador' ? 'Computador' : 'Telemóvel' }}: proporção {{ formato(proporcao[modo]) }}
        {{ fixa[modo] ? '(fixada por ti)' : '(automática, a mais comum entre os anúncios)' }}.
        <template v-if="modo === 'computador'"> Em ecrãs baixos a altura fica limitada a 70% do ecrã (o anúncio continua inteiro).</template>
      </p>
    </div>
  </div>
</template>

<script>
import HomePublicidade from '@/components/home/HomePublicidade.vue'

const LARGURA_PC = 1270
const LARGURA_TEL = 358

export function formatoProporcao (r) {
  if (!r) return '—'
  const conhecidas = { '21:9': 21 / 9, '3:1': 3, '2:1': 2, '16:9': 16 / 9, '4:3': 4 / 3, '1:1': 1, '4:5': 0.8, '9:16': 9 / 16, '3:2': 1.5 }
  const k = Object.keys(conhecidas).find(n => Math.abs(conhecidas[n] - r) < 0.02)
  return k || `${r.toFixed(2).replace('.', ',')}:1`
}

export default {
  name: 'HomePublicidadePreview',
  components: { HomePublicidade },
  props: {
    anuncios:  { type: Array, default: () => [] },
    proporcao: { type: Object, required: true },
    fixa:      { type: Object, default: () => ({}) },
    intervalo: { type: Number, default: 6 },
    titulo:    { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    vazio:     { type: String, default: '' },
  },
  data () {
    return {
      LARGURA_PC, LARGURA_TEL,
      MODOS: [{ v: 'computador', n: 'Computador', icone: 'desktop' }, { v: 'telemovel', n: 'Telemóvel', icone: 'mobile-screen' }],
      modo: 'computador',
      escala: 0.5,
      altura: 0,
    }
  },
  mounted () {
    this.ro = new ResizeObserver(() => this.medir())
    this.$watch(() => [this.modo, this.anuncios.length], () => { this.$nextTick(() => this.observar()) }, { immediate: true })
  },
  beforeUnmount () { this.ro?.disconnect() },
  methods: {
    formato: formatoProporcao,
    observar () {
      this.ro.disconnect()
      if (this.$refs.moldura) this.ro.observe(this.$refs.moldura)
      if (this.$refs.interior) this.ro.observe(this.$refs.interior)
      this.medir()
    },
    medir () {
      const m = this.$refs.moldura
      const i = this.$refs.interior
      if (!m || !i) return
      this.escala = Math.min(1, m.clientWidth / LARGURA_PC)
      this.altura = i.offsetHeight
    },
  },
}
</script>

<style scoped>
.pub-cores-originais {
  --color-zinc-50: oklch(98.5% 0 0);
  --color-zinc-100: oklch(96.7% 0.001 286.375);
  --color-zinc-200: oklch(92% 0.004 286.32);
  --color-zinc-300: oklch(87.1% 0.006 286.286);
  --color-zinc-400: oklch(70.5% 0.015 286.067);
  --color-zinc-500: oklch(55.2% 0.016 285.938);
  --color-zinc-600: oklch(44.2% 0.017 285.786);
  --color-zinc-700: oklch(37% 0.013 285.805);
  --color-zinc-800: oklch(27.4% 0.006 286.033);
  --color-zinc-900: oklch(21% 0.006 285.885);
  --color-zinc-950: oklch(14.1% 0.005 285.823);
  --color-white: #fff;
  color-scheme: dark;
}
/* o tema-claro.css volta a escurecer o "branco" dentro de fundos zinc (html.tema-claro [class~="bg-zinc-900"]);
   aqui dentro o branco é branco (mais específico: classe + atributo + atributo) */
.pub-cores-originais[class~="bg-zinc-950"],
.pub-cores-originais :deep([class~="bg-zinc-950"]),
.pub-cores-originais :deep([class~="bg-zinc-900"]),
.pub-cores-originais :deep([class~="bg-zinc-800"]) {
  --color-white: #fff;
}
</style>
