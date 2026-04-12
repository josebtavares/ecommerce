<!-- TemplateTechStore — stub funcional, usa TemplateClassico como base -->
<!-- Personaliza o template visual aqui mantendo a mesma estrutura -->
<template>
  <TemplateClassico :tema="tema" />
</template>

<script>
import TemplateClassico from './TemplateClassico.vue'
export default {
  name: 'TemplateTechStore',
  components: { TemplateClassico },
  props: { tema: { type: Object, default: () => ({}) } }
}
</script>
