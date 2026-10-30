<template>
  <div class="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
    <div class="max-w-md w-full text-center">

      <!-- Ícone de sucesso -->
      <div class="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <h1 class="text-3xl font-extrabold text-white mb-2">Encomenda confirmada!</h1>
      <p class="text-zinc-400 mb-8">O teu pedido foi recebido e está a ser processado.</p>

      <!-- Detalhes da encomenda -->
      <div v-if="encomenda" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 text-left mb-8 space-y-3">
        <div class="flex justify-between text-sm">
          <span class="text-zinc-500">Encomenda</span>
          <span class="text-zinc-200 font-semibold">#{{ encomenda.id }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-zinc-500">Loja</span>
          <span class="text-zinc-200">{{ encomenda.loja_nome }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-zinc-500">Tipo</span>
          <span class="text-zinc-200 capitalize">{{ encomenda.tipo_entrega === 'entrega' ? 'Entrega ao domicílio' : 'Takeaway' }}</span>
        </div>
        <!-- feita com a loja fechada -->
        <div v-if="encomenda.agendada_texto && encomenda.agendamento_origem === 'cliente'"
             class="text-sm rounded-xl bg-sky-500/10 border border-sky-500/30 px-3 py-2.5 text-sky-200">
          Agendada para <b>{{ encomenda.agendada_texto }}</b>.
        </div>
        <div v-else-if="encomenda.agendada_texto" class="text-sm rounded-xl bg-amber-500/10 border border-amber-500/30 px-3 py-2.5 text-amber-200">
          A loja estava fechada — a tua encomenda vai ser preparada a partir de <b>{{ encomenda.agendada_texto }}</b>.
        </div>
        <div class="flex justify-between text-sm border-t border-zinc-800 pt-3">
          <span class="text-zinc-400 font-semibold">Total</span>
          <span class="text-red-400 font-bold">{{ formatPrice(encomenda.valor_total) }}</span>
        </div>
        <div class="flex justify-between items-center text-sm">
          <span class="text-zinc-500">Estado</span>
          <span v-if="encomenda.transferencia" class="px-2 py-0.5 bg-amber-500/15 text-amber-300 text-xs font-bold rounded-full uppercase">
            Aguarda transferência
          </span>
          <span v-else class="px-2 py-0.5 bg-blue-500/15 text-blue-400 text-xs font-bold rounded-full uppercase">
            {{ encomenda.status }}
          </span>
        </div>
      </div>

      <!-- por transferência: para onde transferir (também por email) -->
      <DadosTransferencia v-if="encomenda?.transferencia" :dados="encomenda.transferencia" class="mb-8" />

      <!-- comprovativo do pagamento online (contrato SISP, cl.3): também segue por email, em PDF -->
      <div v-if="encomenda?.comprovativo" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 text-left mb-8 space-y-2"
           data-teste="comprovativo-pagamento">
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider pb-1">Comprovativo de pagamento</p>
        <div v-for="[r, v] in linhasComprovativo" :key="r" class="flex justify-between gap-4 text-sm">
          <span class="text-zinc-500 flex-shrink-0">{{ r }}</span>
          <span class="text-zinc-200 text-right break-all">{{ v }}</span>
        </div>
        <button type="button" @click="descarregarComprovativoEncomenda(encomenda.id)" data-teste="comprovativo-pdf"
          class="mt-2 text-xs font-semibold text-red-400 hover:text-red-300 underline">Descarregar em PDF</button>
      </div>

      <div class="flex gap-3">
        <button @click="$router.push({ name: 'Home' })"
          class="flex-1 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold transition">
          Voltar ao início
        </button>
        <button @click="$router.push('/perfil')"
          class="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-semibold transition">
          Ver encomendas
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { temaPainel } from '@/utils/tema'
import { descarregarComprovativoEncomenda } from '@/utils/documentos'
import DadosTransferencia from '@/components/loja/DadosTransferencia.vue'

export default {
  name: 'EncomendaSucesso',
  mixins: [temaPainel],
  components: { DadosTransferencia },
  data () {
    return { encomenda: null }
  },
  async created () {
    try {
      const { data } = await api.get(`/app/encomenda/${this.$route.params.id}/`)
      this.encomenda = data
    } catch (e) { console.error(e) }
  },
  computed: {
    linhasComprovativo () {
      const c = this.encomenda.comprovativo
      return [
        ['Loja', c.comerciante + (c.comerciante_nif ? ` · NIF ${c.comerciante_nif}` : '')],
        ['Valor', `${this.formatPrice(c.valor)} (${c.moeda})`],
        ['Data', c.data], ['Método', c.metodo], ['Processado por', c.processado_por],
        ['Referência', c.referencia || '—'], ['Estado', c.estado],
      ]
    },
  },
  methods: {
    descarregarComprovativoEncomenda,
    formatPrice (val) {
      return formatarDinheiro(val || 0)
    }
  }
}
</script>