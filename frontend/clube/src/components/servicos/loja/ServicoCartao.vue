<template>
  <!-- Cartão de um serviço na página da loja (slider e catálogo) -->
  <button type="button" @click="$emit('abrir', s)" :data-teste="`servico-${s.id}`"
    class="group text-left flex flex-col rounded-2xl border overflow-hidden transition"
    :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-gray-200 hover:border-gray-400 hover:shadow-md'">
    <div class="relative aspect-[4/3] w-full overflow-hidden flex items-center justify-center" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'">
      <span v-if="s.e_pacote" class="absolute top-2 left-2 z-[1] px-2 py-0.5 rounded-md text-white text-[10px] font-bold uppercase" :style="{ backgroundColor: cor }">Pacote</span>
      <img v-if="s.imagens.length" :src="s.imagens[0]" alt="" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" />
      <font-awesome-icon v-else :icon="['fas', 'calendar-check']" class="text-3xl" :style="{ color: cor }" />
    </div>
    <div class="p-3 flex-1 flex flex-col w-full">
      <p class="font-semibold text-sm leading-tight line-clamp-2">{{ s.nome }}</p>
      <p class="text-xs mt-1" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ duracaoTexto(s.duracao_min) }}</p>
      <p v-if="s.e_pacote" class="text-[11px] mt-0.5 line-clamp-1" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ s.componentes.map(c => c.nome).join(' + ') }}</p>
      <div class="flex items-center justify-between gap-2 mt-auto pt-2">
        <span class="text-sm font-bold" :style="{ color: cor }">{{ s.preco_texto }}</span>
        <span class="text-[11px] font-bold px-2.5 py-1 rounded-lg text-white" :style="{ backgroundColor: cor }">Marcar</span>
      </div>
    </div>
  </button>
</template>

<script>
import { duracaoTexto } from '@/utils/servicos'

export default {
  name: 'ServicoCartao',
  props: { s: { type: Object, required: true }, isDark: { type: Boolean, default: true }, cor: { type: String, default: '#dc2626' } },
  emits: ['abrir'],
  methods: { duracaoTexto },
}
</script>
