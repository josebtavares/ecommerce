<!-- HomeServicos.vue — secção "Serviços" da home (Admin → Página inicial): serviços com marcação online -->
<template>
  <div>
    <div class="mb-4">
      <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo || 'Serviços' }}</h2>
      <p v-if="subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ subtitulo }}</p>
    </div>
    <div class="flex gap-3 overflow-x-auto pb-2 snap-x">
      <ServicoCard v-for="s in servicos" :key="s.id" :s="s" :isDark="isDark" class="w-44 sm:w-52 flex-shrink-0 snap-start" />
    </div>
  </div>
</template>

<script>
import ServicoCard from '@/components/servicos/ServicoCard.vue'

export default {
  name: 'HomeServicos',
  components: { ServicoCard },
  props: {
    servicos:  { type: Array,  default: () => [] },
    titulo:    { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark:    { type: Boolean, default: true },
  },
}
</script>
