<!-- LandingTitulo.vue — título e subtítulo de uma secção da landing page. -->
<template>
  <div class="max-w-3xl" :class="centro ? 'mx-auto text-center' : ''">
    <h2 class="text-3xl sm:text-4xl font-extrabold tracking-tight whitespace-pre-line" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ titulo }}</h2>
    <p v-if="subtitulo" class="mt-3 text-base sm:text-lg leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ subtitulo }}</p>
  </div>
</template>

<script>
export default {
  name: 'LandingTitulo',
  props: {
    titulo: { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark: { type: Boolean, default: false },
    centro: { type: Boolean, default: true },
  },
}
</script>
