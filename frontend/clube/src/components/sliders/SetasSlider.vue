<!-- SetasSlider.vue — botões ‹ › dos sliders horizontais (produtos, lojas, serviços) -->
<template>
  <div class="flex items-center gap-1.5">
    <button type="button" class="seta-slider" :class="[cores, !anterior ? 'opacity-40 cursor-not-allowed pointer-events-none' : '']"
      :disabled="!anterior" aria-label="Scroll left" @click="$emit('anterior')">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <button type="button" class="seta-slider" :class="[cores, !seguinte ? 'opacity-40 cursor-not-allowed pointer-events-none' : '']"
      :disabled="!seguinte" aria-label="Scroll right" @click="$emit('seguinte')">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'SetasSlider',
  props: {
    anterior: { type: Boolean, default: false },   // pode andar para a esquerda
    seguinte: { type: Boolean, default: false },   // pode andar para a direita
    isDark:   { type: Boolean, default: true },
  },
  emits: ['anterior', 'seguinte'],
  computed: {
    cores () {
      return this.isDark
        ? 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800 hover:text-white hover:border-zinc-700'
        : 'bg-white border-gray-200 text-zinc-600 hover:bg-gray-50 hover:text-zinc-900 hover:border-gray-300 shadow-sm'
    },
  },
}
</script>

<style scoped>
.seta-slider {
  width: 34px;
  height: 34px;
  border-width: 1px;
  border-style: solid;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease, opacity 180ms ease, transform 180ms ease;
}
.seta-slider:hover { transform: translateY(-1px); }
.seta-slider:active { transform: translateY(0); }
@media (max-width: 520px) {
  .seta-slider { width: 32px; height: 32px; }
}
</style>
