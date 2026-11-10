<!-- FaturaEncomenda.vue — backoffice: a fatura de uma encomenda (FaturaVenda) + o comprovativo do pagamento.
     encomenda: detalhe (EncomendaSerializer). Emite 'atualizada' com a encomenda devolvida pelo backend. -->
<template>
  <FaturaVenda :documento="encomenda" :url="`/app/loja/${lojaId}/encomendas/${encomenda.id}/fatura/`"
    :cancelada="encomenda.status === 'cancelado'" teste="fatura-encomenda"
    dica="Emite a fatura no e-Fatura e regista-a aqui: o cliente vê-a na encomenda." @atualizada="d => $emit('atualizada', d)">
    <!-- comprovativo do pagamento: a Bendi gera-o e envia-o ao cliente; a fatura é da loja -->
    <template #acoes>
      <BotaoPdf v-if="pago" texto="Comprovativo de pagamento" titulo="Descarregar o comprovativo de pagamento (PDF)" teste="comprovativo-loja"
        @click="descarregarComprovativoEncomenda(encomenda.id)" />
    </template>
  </FaturaVenda>
</template>

<script>
import { descarregarComprovativoEncomenda } from '@/utils/documentos'
import FaturaVenda from './FaturaVenda.vue'
import BotaoPdf from '@/components/fiscal/BotaoPdf.vue'

export default {
  name: 'FaturaEncomenda',
  components: { BotaoPdf, FaturaVenda },
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
