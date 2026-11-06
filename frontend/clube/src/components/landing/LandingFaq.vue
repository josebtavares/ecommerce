<!-- LandingFaq.vue — perguntas frequentes: cada uma abre ao clicar (<details>, funciona também com o teclado). -->
<template>
  <section id="faq" class="landing-seccao py-20 sm:py-24 px-5 sm:px-8" data-teste="landing-faq"
           :class="alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : ''">
    <div class="max-w-3xl mx-auto">
      <LandingTitulo :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />
      <div class="mt-10 space-y-3">
        <details v-for="p in s.perguntas || []" :key="p.id" class="group rounded-2xl border" data-teste="faq-item"
                 :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
          <summary class="flex items-center justify-between gap-4 cursor-pointer list-none px-5 py-4 font-semibold"
                   :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
            <span>{{ p.pergunta }}</span>
            <font-awesome-icon :icon="['fas', 'plus']" class="w-4 h-4 flex-shrink-0 transition-transform group-open:rotate-45"
                               :class="isDark ? 'text-red-400' : 'text-orange-500'" />
          </summary>
          <p class="px-5 pb-5 -mt-1 text-sm leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ p.resposta }}</p>
        </details>
      </div>
    </div>
  </section>
</template>

<script>
import LandingTitulo from './LandingTitulo.vue'

export default {
  name: 'LandingFaq',
  components: { LandingTitulo },
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
}
</script>

<style scoped>
summary::-webkit-details-marker { display: none; }
</style>
