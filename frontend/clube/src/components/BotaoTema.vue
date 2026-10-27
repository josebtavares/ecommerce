<template>
  <!-- alternar claro/escuro nas páginas escritas em escuro (ver utils/tema.js) -->
  <button type="button" @click="$emit('alternar')" :title="isDark ? 'Tema claro' : 'Tema escuro'"
    class="w-9 h-9 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 flex items-center justify-center transition flex-shrink-0">
    <i :class="['fas text-sm', isDark ? 'fa-sun' : 'fa-moon']"></i>
  </button>
</template>

<script>
export default {
  name: 'BotaoTema',
  props: { isDark: { type: Boolean, default: false } },
  emits: ['alternar'],
}
</script>
