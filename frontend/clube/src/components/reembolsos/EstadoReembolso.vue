<template>
  <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase whitespace-nowrap', corEstado(estado)]">
    {{ labelEstado(estado, valor) }}
  </span>
</template>

<script setup>
import { corEstado, labelEstado } from '@/utils/reembolsos'

defineProps({
  estado: { type: String, required: true },
  valor:  { type: [String, Number], default: undefined },   // valor aprovado (0 → "Cancelamento aceite")
})
</script>
