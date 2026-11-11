<!-- BarraGuardarSeccao.vue — o botão "Guardar" no fundo de cada secção das Configurações da loja.
     Cada secção guarda só os seus campos (sem um botão único no fim da página). -->
<template>
  <div class="mt-5 pt-4 border-t border-zinc-800 flex flex-wrap items-center justify-end gap-3" :data-teste="`guardar-${seccao}`">
    <p v-if="erro" class="mr-auto text-xs text-red-400" role="alert">{{ erro }}</p>
    <p v-else-if="guardado && !alterado" class="mr-auto text-xs text-green-500">Guardado ✓</p>
    <p v-else-if="alterado" class="mr-auto text-xs text-amber-400">Alterações por guardar</p>
    <button type="button" @click="$emit('guardar')" :disabled="!alterado || aGuardar"
      class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition">
      {{ aGuardar ? 'A guardar…' : 'Guardar' }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'BarraGuardarSeccao',
  props: {
    seccao:   { type: String, required: true },
    alterado: { type: Boolean, default: false },
    aGuardar: { type: Boolean, default: false },
    guardado: { type: Boolean, default: false },
    erro:     { type: String, default: '' },
  },
  emits: ['guardar'],
}
</script>
