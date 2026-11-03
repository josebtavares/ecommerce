<!-- AvisoMudouPorFora.vue — tempo real (utils/tempoRealEncomendas.js): a encomenda/entrega que a pessoa tem em mãos
     (modal aberto, acção a meio) foi alterada por outra pessoa. Os dados não mudam por baixo dela: actualizam ao
     terminar. Fica por cima dos modais. -->
<template>
  <div v-if="visivel" role="status" aria-live="polite" data-teste="mudou-por-fora"
       class="fixed top-3 left-1/2 -translate-x-1/2 z-[70] w-[calc(100%-2rem)] max-w-md flex items-start gap-2 rounded-xl
              border border-amber-500/40 bg-zinc-900 px-3 py-2.5 text-xs text-amber-200 shadow-2xl">
    <font-awesome-icon :icon="['fas', 'rotate']" class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
    <span class="flex-1">{{ texto }}</span>
  </div>
</template>

<script>
export default {
  name: 'AvisoMudouPorFora',
  props: {
    visivel: { type: Boolean, default: false },
    texto: { type: String, default: 'Esta encomenda foi alterada por outra pessoa — os dados atualizam quando terminares.' },
  },
}
</script>
