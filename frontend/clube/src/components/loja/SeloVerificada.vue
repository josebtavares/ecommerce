<!-- SeloVerificada.vue — selo "Loja verificada" (documentos aprovados pela Bende — utils/documentos_loja.py).
     Só aparece com loja.verificada === true, o que a API só devolve quando o admin liga o selo para o público
     (Definições da plataforma). Herda a cor do sítio onde está (hero dos templates, cards, rodapé). -->
<template>
  <span v-if="loja && loja.verificada === true" class="selo-verificada" :class="{ 'selo-verificada--icone': icone }"
        title="A Bende verificou os documentos desta loja" data-teste="selo-verificada">
    <font-awesome-icon :icon="['fas', 'circle-check']" />
    <span v-if="!icone">Loja verificada</span>
  </span>
</template>

<script>
export default {
  name: 'SeloVerificada',
  props: {
    loja:  { type: Object, default: null },
    icone: { type: Boolean, default: false },   // só o ícone (cards pequenos)
  },
}
</script>

<style scoped>
.selo-verificada {
  display: inline-flex; align-items: center; gap: .3em;
  font-size: .75rem; font-weight: 600; line-height: 1.2; letter-spacing: normal; text-transform: none;
  padding: .2em .65em; border-radius: 999px; vertical-align: middle;
  border: 1px solid color-mix(in srgb, currentColor 35%, transparent);
  background: color-mix(in srgb, currentColor 10%, transparent);
}
.selo-verificada svg { color: #22c55e; }
.selo-verificada--icone { padding: 0; border: 0; background: none; font-size: .9em; }
</style>
