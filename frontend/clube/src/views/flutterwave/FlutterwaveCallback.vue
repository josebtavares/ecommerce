<template>
  <div class="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
    <div class="max-w-sm w-full text-center" data-teste="pagamento-regresso">

      <!-- Loading -->
      <div v-if="estado === 'loading'">
        <svg class="animate-spin h-12 w-12 text-red-500 mx-auto mb-4" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
          <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
        </svg>
        <p class="text-zinc-400 text-sm">A verificar o pagamento…</p>
      </div>

      <!-- Sucesso -->
      <div v-else-if="estado === 'sucesso'">
        <div class="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 class="text-2xl font-extrabold text-white mb-2">Pagamento confirmado!</h1>
        <p class="text-zinc-400 text-sm mb-6">O teu pagamento foi processado com sucesso.</p>
        <button @click="continuar"
          class="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold transition">
          {{ textoBotao }}
        </button>
      </div>

      <!-- Erro / reembolso -->
      <div v-else>
        <div class="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h1 class="text-2xl font-extrabold text-white mb-2">{{ estado === 'reembolso' ? 'Pagamento não aceite' : 'Pagamento falhado' }}</h1>
        <p class="text-zinc-400 text-sm mb-6">{{ mensagemErro }}</p>
        <button @click="continuar"
          class="w-full py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold transition">
          {{ destino ? textoBotao : 'Voltar ao início' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { temaPainel } from '@/utils/tema'
import { fornecedorDoRegresso } from '@/utils/pagamentoOnline'

// regresso do cliente depois de pagar na página do fornecedor (pagamentos.servico confirma junto dele)
export default {
  name: 'PagamentoRegresso',
  mixins: [temaPainel],

  data () {
    return {
      estado:       'loading',
      mensagemErro: '',
      tipo:         '',
      destino:      '',
    }
  },

  computed: {
    textoBotao () {
      return { encomenda: 'Ver encomenda', marcacao: 'Ver marcação', fatura: 'Ver subscrição' }[this.tipo] || 'Continuar'
    },
  },

  async created () {
    const dados = Object.fromEntries(new URLSearchParams(window.location.search))
    // o Flutterwave volta com ?transaction_id=&tx_ref=; os outros dizem-se no localStorage
    dados.fornecedor = fornecedorDoRegresso() || (dados.tx_ref ? 'flutterwave' : '')
    try {
      const { data } = await api.post('/app/pagamento/regresso/', dados)
      this.tipo = data.tipo
      this.destino = data.destino
      if (data.tipo === 'encomenda') {
        window.dispatchEvent(new CustomEvent('carrinho-limpo', { detail: { lojaId: null } }))
      }
      this.estado = 'sucesso'
    } catch (e) {
      const d = e.response?.data || {}
      this.tipo = d.tipo || ''
      this.destino = d.destino || ''
      this.mensagemErro = d.detail || 'Erro ao verificar o pagamento.'
      this.estado = d.codigo === 'reembolso' ? 'reembolso' : 'erro'
    }
  },

  methods: {
    continuar () {
      this.$router.push(this.destino || { name: 'Home' })
    },
  },
}
</script>
