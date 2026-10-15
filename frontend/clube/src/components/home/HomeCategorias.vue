<!-- HomeCategorias.vue — grelha de categorias de lojas (Admin → Página inicial); clicar filtra o catálogo -->
<template>
  <div>
    <div class="mb-4">
      <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo || 'Categorias' }}</h2>
      <p v-if="subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ subtitulo }}</p>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
      <button v-for="c in categorias" :key="c.valor" type="button" @click="$emit('escolher', c.valor)"
        class="group flex flex-col items-center justify-center gap-2 px-3 py-5 rounded-2xl border transition text-center"
        :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-red-500/50 hover:bg-zinc-800'
                       : 'bg-white border-stone-200 hover:border-red-400 hover:shadow-md'">
        <span class="w-12 h-12 rounded-2xl flex items-center justify-center text-red-500 transition group-hover:scale-110"
              :class="isDark ? 'bg-red-500/10' : 'bg-red-50'">
          <font-awesome-icon :icon="['fas', iconeCategoria(null, c.valor)]" class="w-5 h-5" />
        </span>
        <span class="text-sm font-semibold" :class="isDark ? 'text-zinc-100' : 'text-zinc-800'">{{ c.nome }}</span>
        <span class="text-[11px]" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ c.total }} {{ c.total === 1 ? 'loja' : 'lojas' }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { iconeCategoria } from '@/utils/icones'

export default {
  name: 'HomeCategorias',
  props: {
    categorias: { type: Array,  default: () => [] },
    titulo:     { type: String, default: '' },
    subtitulo:  { type: String, default: '' },
    isDark:     { type: Boolean, default: true },
  },
  emits: ['escolher'],
  methods: { iconeCategoria },
}
</script>
