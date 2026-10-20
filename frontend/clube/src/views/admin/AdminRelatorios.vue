<template>
  <!-- Relatórios da plataforma: catálogo, filtros, resumo, linhas e exportação (CSV, Excel, PDF) -->
  <ModuloRelatorios base="/app/admin/relatorios" prefixo="bendi" />
</template>

<script>
import ModuloRelatorios from '@/components/relatorios/ModuloRelatorios.vue'

export default {
  name: 'AdminRelatorios',
  components: { ModuloRelatorios },
}
</script>
