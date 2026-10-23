<template>
  <!-- Lista curta de marcações (avisos: ausência, horário novo, profissional com marcações futuras) -->
  <div class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 space-y-1.5" role="alert">
    <p class="text-xs font-semibold text-amber-200">{{ titulo }}</p>
    <p v-for="m in marcacoes" :key="m.id" class="text-xs text-amber-100/90">
      {{ rotuloDia(diaDe(m.inicio)) }} {{ hora(m.inicio) }} · {{ m.servico_nome }} · {{ m.cliente_nome || 'sem nome' }} · {{ m.profissional_nome }}
    </p>
  </div>
</template>

<script>
import { diaDe, hora, rotuloDia } from '@/utils/servicos'

export default {
  name: 'ListaMarcacoes',
  props: { marcacoes: { type: Array, required: true }, titulo: { type: String, default: '' } },
  methods: { diaDe, hora, rotuloDia },
}
</script>
