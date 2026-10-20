<template>
  <div class="rel-claro space-y-5">
    <div class="flex flex-col gap-1">
      <h2 class="text-2xl font-black text-slate-950">Relatórios</h2>
      <p class="text-sm font-semibold text-slate-500">
        Relatórios detalhados para a contabilidade, com exportação em Excel, PDF e CSV.
      </p>
    </div>
    <ModuloRelatorios :base="`/api/pos/${posId}/relatorios`" :prefixo="`pos-${posId}`" />
  </div>
</template>

<script setup>
// Relatórios do POS: o mesmo módulo da backoffice e do admin (catálogo, filtros, exportações), com o tema claro do POS.
import '@/assets/relatorios-claro.css'
import ModuloRelatorios from '@/components/relatorios/ModuloRelatorios.vue'

defineProps({
  posId: { type: [Number, String], required: true },
})
</script>
