<template>
  <!-- Concelho de Cabo Verde, agrupado por ilha (utils/geografia.js). v-model = código ('PR', 'SV'…) -->
  <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)" :class="classeCampo"
          aria-label="Concelho" data-teste="seletor-concelho">
    <option value="">Escolhe o concelho</option>
    <optgroup v-for="ilha in ilhas" :key="ilha.nome" :label="ilha.nome">
      <option v-for="c in ilha.concelhos" :key="c.codigo" :value="c.codigo">{{ c.nome }}</option>
    </optgroup>
  </select>
</template>

<script>
import { concelhosPorIlha } from '@/utils/geografia'

export default {
  name: 'SeletorConcelho',
  props: {
    modelValue:  { type: String, default: '' },
    classeCampo: { type: [String, Array, Object], default: '' },
  },
  emits: ['update:modelValue'],
  computed: {
    ilhas () { return concelhosPorIlha() },
  },
}
</script>
