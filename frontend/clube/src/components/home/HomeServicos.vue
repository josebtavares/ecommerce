<!-- HomeServicos.vue — secção "Serviços" da home (Admin → Página inicial): serviços com marcação online -->
<template>
  <div>
    <div class="flex items-center justify-between gap-3 mb-4">
      <div class="min-w-0">
        <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo || 'Serviços' }}</h2>
        <p v-if="subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ subtitulo }}</p>
      </div>
      <SetasSlider class="flex-shrink-0" :anterior="podeAnterior" :seguinte="podeSeguinte" :isDark="isDark"
        @anterior="mover(-1)" @seguinte="mover(1)" />
    </div>
    <div ref="fila" class="flex gap-3 overflow-x-auto pb-2 snap-x scroll-smooth" style="scrollbar-width: none"
         @scroll.passive="atualizarSetas">
      <ServicoCard v-for="s in servicos" :key="s.id" :s="s" :isDark="isDark" class="w-44 sm:w-52 flex-shrink-0 snap-start" />
    </div>
  </div>
</template>

<script>
import ServicoCard from '@/components/servicos/ServicoCard.vue'
import SetasSlider from '@/components/sliders/SetasSlider.vue'

export default {
  name: 'HomeServicos',
  components: { ServicoCard, SetasSlider },
  props: {
    servicos:  { type: Array,  default: () => [] },
    titulo:    { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark:    { type: Boolean, default: true },
  },
  data () { return { podeAnterior: false, podeSeguinte: false } },
  mounted () {
    this.atualizarSetas()
    window.addEventListener('resize', this.atualizarSetas)
  },
  beforeUnmount () { window.removeEventListener('resize', this.atualizarSetas) },
  watch: { servicos () { this.$nextTick(this.atualizarSetas) } },
  methods: {
    mover (d) { const f = this.$refs.fila; if (f) f.scrollBy({ left: d * f.clientWidth * 0.8 }) },
    atualizarSetas () {
      const f = this.$refs.fila
      if (!f) return
      this.podeAnterior = f.scrollLeft > 2
      this.podeSeguinte = f.scrollLeft + f.clientWidth < f.scrollWidth - 2
    },
  },
}
</script>
