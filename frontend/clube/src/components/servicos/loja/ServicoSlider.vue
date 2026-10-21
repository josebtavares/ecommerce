<template>
  <!-- Fila horizontal de serviços (como o ProductSlider) -->
  <div class="mb-8" data-teste="servico-slider">
    <div class="flex items-center justify-between mb-3 gap-3">
      <h3 class="font-bold text-lg truncate" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo }}
        <span class="text-xs font-normal" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">({{ servicos.length }})</span></h3>
      <div v-if="servicos.length > 2" class="hidden sm:flex gap-1.5">
        <button v-for="d in [-1, 1]" :key="d" type="button" @click="mover(d)" :aria-label="d < 0 ? 'Anteriores' : 'Seguintes'"
          class="w-8 h-8 rounded-full border flex items-center justify-center text-sm"
          :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800' : 'bg-white border-gray-200 text-zinc-600 hover:bg-gray-50'">
          {{ d < 0 ? '‹' : '›' }}</button>
      </div>
    </div>
    <div ref="fila" class="flex gap-3 overflow-x-auto pb-2 snap-x scroll-smooth" style="scrollbar-width: none">
      <ServicoCartao v-for="s in servicos" :key="s.id" :s="s" :isDark="isDark" :cor="cor"
        class="w-44 sm:w-52 flex-shrink-0 snap-start" @abrir="$emit('abrir', $event)" />
    </div>
  </div>
</template>

<script>
import ServicoCartao from './ServicoCartao.vue'

export default {
  name: 'ServicoSlider',
  components: { ServicoCartao },
  props: {
    titulo: { type: String, default: 'Serviços' },
    servicos: { type: Array, default: () => [] },
    isDark: { type: Boolean, default: true },
    cor: { type: String, default: '#dc2626' },
  },
  emits: ['abrir'],
  methods: {
    mover (d) { const f = this.$refs.fila; if (f) f.scrollBy({ left: d * f.clientWidth * 0.8 }) },
  },
}
</script>
