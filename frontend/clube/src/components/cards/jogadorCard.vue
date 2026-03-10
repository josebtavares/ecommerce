<!-- PlayerCard.vue -->
<template>
  <div
    class="relative w-58 h-84 shrink-0 rounded-2xl overflow-hidden
           shadow-xl ring-1 ring-black/25 hover:scale-105 transition" @click="$emit('select', data)">

    <!-- imagem de fundo ------------------------------------------------>
    <img
      :src="data.foto"
      alt="foto do jogador"
      class="absolute inset-0 w-full h-full object-cover opacity-80" />

    <!-- gradiente escuro de baixo para cima -->
    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>

    <!-- conteúdo ------------------------------------------------------->
    <div class="relative z-10 h-full flex flex-col justify-end p-3 text-white">
      <h2 class="text-lg font-bold leading-5 break-words mb-1">
        {{ data.nome }}
      </h2>

      <div class="text-xs flex flex-wrap gap-x-2 gap-y-0.5">
        <span class="font-semibold">{{ data.posicao }}</span>
        <span>· #{{ data.numero }}</span>
        <span v-if="data.idade">· {{ data.idade }}&nbsp;anos</span>
        <span v-if="data.nacionalidade">· {{ data.nacionalidade }}</span>
      </div>
    </div>

    <!-- moldura decorativa (tipo Pokémon) ----------------------------->
    <div class="absolute inset-0 rounded-2xl pointer-events-none
                ring-4 ring-yellow-400/80"></div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  data: {
    type: Object,
    default: () => ({
      nome: 'Jogador',
      foto: '/placeholder.jpg',
      posicao: 'Médio',
      numero: 10,
      idade: 28,
      nacionalidade: 'BRA'
    })
  }
})
//emits
defineEmits(['select'])
</script>
