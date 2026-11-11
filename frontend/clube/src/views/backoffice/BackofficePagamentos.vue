<template>
  <!-- Backoffice → Pagamentos: os pagamentos com cartão (vinti4) da loja, pelo contrato dela com a SISP.
       O mesmo ecrã do Admin → Pagamentos → Cartão, só com o que é da loja (Views/lojaCartaoView.py).
       Tempo real: utils/tempo_real_listas.py origem 'cartao'. -->
  <div class="space-y-4" data-teste="backoffice-pagamentos">
    <div>
      <h2 class="text-lg font-bold text-zinc-100">Pagamentos com cartão</h2>
      <p class="text-xs text-zinc-500 mt-0.5">
        Cada pagamento com cartão (vinti4) feito na tua loja e o que a SISP respondeu. O dinheiro entra diretamente na
        conta do teu contrato com a SISP. Carrega aqui os ficheiros VBVT do teu Portal do Comerciante para confirmar
        que tudo bate certo.
      </p>
    </div>

    <div v-if="contrato && !contrato.estado" class="rounded-xl border border-zinc-700 bg-zinc-900 p-3 text-xs text-zinc-300" data-teste="pag-sem-contrato">
      A loja ainda não aceita cartão. Para aceitar, faz o pedido ou indica o teu contrato vinti4 em Configurações.
      <button v-if="podeAgir" type="button" @click="$emit('configurar')" class="ml-1 underline text-zinc-100">Abrir Configurações</button>
    </div>
    <div v-else-if="contrato && !contrato.portal" class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200" data-teste="pag-sem-portal">
      Falta o acesso ao Portal do Comerciante (Portal ID e password) em Configurações → Pagamento com cartão.
      Sem ele, um pagamento sem resposta da SISP fica "por confirmar" e não dá para usar "Perguntar à SISP".
      <button v-if="podeAgir" type="button" @click="$emit('configurar')" class="ml-1 underline text-amber-100">Abrir Configurações</button>
    </div>

    <PagamentosVinti4 ref="cartao" :base="`/app/loja/${lojaId}/cartao`" :vbvt-base="`/app/loja/${lojaId}/cartao/vbvt`"
                      :admin="false" :pode-agir="podeAgir" :nome-csv="`pagamentos-cartao-loja-${lojaId}`"
                      @carregado="contrato = $event.contrato || contrato" />
  </div>
</template>

<script>
import PagamentosVinti4 from '@/components/admin/PagamentosVinti4.vue'
import { verAdmin } from '@/services/api'
import { ouvirListas } from '@/utils/tempoRealEncomendas'

export default {
  name: 'BackofficePagamentos',
  components: { PagamentosVinti4 },
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['configurar'],
  data () { return { contrato: null } },
  computed: {
    podeAgir () { return !verAdmin(this.lojaId) },      // admin a ver o backoffice: só leitura
  },
  mounted () {
    this.parar = ouvirListas('cartao', () => this.$refs.cartao?.recarregar(), { lojaId: this.lojaId })
  },
  beforeUnmount () { this.parar?.() },
}
</script>
