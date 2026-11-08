<template>
  <!-- um pedido de reembolso/cancelamento do cliente: o mesmo na página /perfil/reembolsos e no separador do perfil -->
  <button type="button" :data-teste="`reembolso-${r.id}`"
    class="w-full text-left rounded-2xl border p-4 flex items-center gap-3 transition"
    :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-gray-200 hover:border-gray-300'">
    <div class="flex-1 min-w-0">
      <p class="text-xs text-zinc-500">
        Encomenda #{{ r.encomenda_id }} · {{ r.loja_nome }} · {{ dataHora(r.data_criacao) }}
      </p>
      <p class="text-sm font-semibold truncate">{{ r.tipo === 'cancelamento' && r.motivo !== 'esgotado' ? 'Cancelamento' : r.motivo_label }}</p>
    </div>
    <div class="text-right flex-shrink-0 space-y-1">
      <EstadoReembolso :estado="r.estado" :valor="r.valor_aprovado ?? undefined" :metodo="r.metodo" />
      <p class="text-sm font-bold">{{ formatarDinheiro(r.valor_aprovado ?? r.valor_pedido) }}</p>
    </div>
  </button>
</template>

<script setup>
import { formatarDinheiro } from '@/utils/dinheiro'
import { dataHora } from '@/utils/reembolsos'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'

defineProps({ r: { type: Object, required: true }, isDark: { type: Boolean, default: true } })
</script>
