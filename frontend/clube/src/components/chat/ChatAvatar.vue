<template>
  <!-- foto em círculo; sem foto, as iniciais numa cor estável por nome -->
  <div class="relative flex-shrink-0 rounded-full overflow-hidden flex items-center justify-center font-bold text-white select-none"
       :style="{ width: tamanho + 'px', height: tamanho + 'px', fontSize: Math.round(tamanho * 0.38) + 'px', background: foto && !falhou ? 'transparent' : cor }">
    <img v-if="foto && !falhou" :src="foto" :alt="nome" class="w-full h-full object-cover" @error="falhou = true" />
    <span v-else-if="tipo === 'suporte'" aria-hidden="true">B</span>
    <span v-else>{{ iniciais }}</span>
  </div>
</template>

<script>
const CORES = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6', '#3b82f6', '#8b5cf6', '#ec4899']

export default {
  name: 'ChatAvatar',
  props: {
    nome:    { type: String, default: '' },
    foto:    { type: String, default: null },
    tipo:    { type: String, default: '' },
    tamanho: { type: Number, default: 40 },
  },
  data () {
    return { falhou: false }
  },
  computed: {
    iniciais () {
      const partes = (this.nome || '?').trim().split(/\s+/)
      return ((partes[0]?.[0] || '?') + (partes.length > 1 ? partes[partes.length - 1][0] : '')).toUpperCase()
    },
    cor () {
      if (this.tipo === 'suporte') return '#dc2626'
      let h = 0
      for (const ch of this.nome || '') h = (h * 31 + ch.charCodeAt(0)) >>> 0
      return CORES[h % CORES.length]
    },
  },
  watch: {
    foto () { this.falhou = false },
  },
}
</script>
