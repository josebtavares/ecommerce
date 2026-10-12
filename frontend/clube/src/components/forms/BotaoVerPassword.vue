<template>
  <!-- vai dentro de um wrapper `relative`; o input precisa de padding à direita (pr-10) -->
  <button type="button" tabindex="-1"
          class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-colors"
          :class="isDark ? 'text-zinc-500 hover:text-zinc-200' : 'text-zinc-400 hover:text-zinc-700'"
          :aria-label="visivel ? 'Ocultar password' : 'Ver password'"
          :title="visivel ? 'Ocultar password' : 'Ver password'"
          @click="$emit('toggle')">
    <!-- olho -->
    <svg v-if="!visivel" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M2.04 12.32a1 1 0 010-.64C3.42 7.51 7.36 4.5 12 4.5c4.64 0 8.57 3 9.96 7.18.07.21.07.43 0 .64C20.58 16.49 16.64 19.5 12 19.5c-4.64 0-8.57-3-9.96-7.18z" />
      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
    <!-- olho riscado -->
    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.22A10.48 10.48 0 002.04 12.32a1 1 0 000 .64C3.42 16.49 7.36 19.5 12 19.5c1.86 0 3.6-.48 5.11-1.32M6.23 6.23A10.45 10.45 0 0112 4.5c4.64 0 8.57 3 9.96 7.18.07.21.07.43 0 .64a10.52 10.52 0 01-4.19 5.45M6.23 6.23L3 3m3.23 3.23l3.65 3.65m7.89 7.89L21 21m-3.23-3.23l-3.65-3.65m0 0a3 3 0 10-4.24-4.24m4.24 4.24L9.88 9.88" />
    </svg>
  </button>
</template>

<script>
export default {
  name: 'BotaoVerPassword',
  props: {
    visivel: { type: Boolean, default: false },
    isDark:  { type: Boolean, default: true },
  },
  emits: ['toggle'],
}
</script>
