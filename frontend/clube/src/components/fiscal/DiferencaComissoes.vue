<!-- DiferencaComissoes.vue — um mês de comissões: créditos à loja (reembolsos depois de a comissão estar liquidada)
     e diferença para a fatura do Bende já registada (reembolsos depois da fatura → nota de crédito).
     item: { creditos, liquido, valor_faturado, diferenca } do backend (faturacaoView.resumo_comissoes).
     admin: texto para quem emite a fatura (Bende) ou para a loja. -->
<template>
  <p v-if="item.diferenca" class="w-full rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-200"
     data-teste="comissoes-diferenca" role="status">
    <template v-if="admin">
      A fatura registada cobre {{ dinheiro(item.valor_faturado) }}, mas depois houve reembolsos e o mês vale agora
      {{ dinheiro(item.liquido) }}. Emite uma nota de crédito de {{ dinheiro(item.diferenca) }} no e-Fatura (ou substitui a fatura).
    </template>
    <template v-else>
      Depois da fatura houve reembolsos: o mês passou de {{ dinheiro(item.valor_faturado) }} para {{ dinheiro(item.liquido) }}.
      O Bende acerta a diferença ({{ dinheiro(item.diferenca) }}) com uma nota de crédito.
    </template>
  </p>
  <p v-else-if="Number(item.creditos)" class="w-full text-[11px] text-zinc-500" data-teste="comissoes-creditos">
    Créditos à loja (reembolsos): −{{ dinheiro(item.creditos) }} · líquido {{ dinheiro(item.liquido) }}
  </p>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'

export default {
  name: 'DiferencaComissoes',
  props: {
    item:  { type: Object, required: true },
    admin: { type: Boolean, default: false },
  },
  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
  },
}
</script>
