<!-- FaturaEncomenda.vue — backoffice: a fatura de uma encomenda (FaturaVenda) + o comprovativo do pagamento.
     encomenda: detalhe (EncomendaSerializer). Emite 'atualizada' com a encomenda devolvida pelo backend. -->
<template>
  <FaturaVenda :documento="encomenda" :url="`/app/loja/${lojaId}/encomendas/${encomenda.id}/fatura/`"
    :cancelada="encomenda.status === 'cancelado'" teste="fatura-encomenda"
    dica="Emite a fatura no e-Fatura e regista-a aqui: o cliente vê-a na encomenda." @atualizada="d => $emit('atualizada', d)">
    <!-- comprovativo do pagamento: o Bende gera-o e envia-o ao cliente; a fatura é da loja -->
    <template #acoes>
      <button v-if="pago" type="button" @click="descarregarComprovativoEncomenda(encomenda.id)" data-teste="comprovativo-loja"
        class="text-[11px] text-zinc-400 hover:text-zinc-200 underline">Comprovativo de pagamento</button>
    </template>
  </FaturaVenda>
</template>

<script>
import { descarregarComprovativoEncomenda } from '@/utils/documentos'
import FaturaVenda from './FaturaVenda.vue'

export default {
  name: 'FaturaEncomenda',
  components: { FaturaVenda },
  props: {
    encomenda: { type: Object, required: true },
    lojaId:    { type: [String, Number], required: true },
  },
  emits: ['atualizada'],
  computed: {
    pago () { return ['aprovado', 'reembolsado', 'reembolsado_parcial'].includes(this.encomenda.pagamento_status) },
  },
  methods: { descarregarComprovativoEncomenda },
}
</script>
