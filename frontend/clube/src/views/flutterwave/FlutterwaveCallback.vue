<template>
  <div class="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
    <div class="max-w-sm w-full text-center">

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
        <button @click="irParaSucesso"
          class="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold transition">
          Ver encomenda
        </button>
      </div>

      <!-- Erro -->
      <div v-else-if="estado === 'erro'">
        <div class="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h1 class="text-2xl font-extrabold text-white mb-2">Pagamento falhado</h1>
        <p class="text-zinc-400 text-sm mb-2">{{ mensagemErro }}</p>
        <button @click="$router.push({ name: 'Home' })"
          class="w-full py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold transition">
          Voltar ao início
        </button>
      </div>

    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'FlutterwaveCallback',

  data () {
    return {
      estado:        'loading',
      mensagemErro:  '',
      encomendaId:   null,
    }
  },

  async created () {
    // Ler parâmetros da URL que o Flutterwave envia
    const params        = new URLSearchParams(window.location.search)
    const status        = params.get('status')
    const transactionId = params.get('transaction_id')
    const txRef         = params.get('tx_ref') || localStorage.getItem('flw_tx_ref')

    this.encomendaId = localStorage.getItem('flw_encomenda_id')

    // Flutterwave cancelou ou falhou
    if (status === 'cancelled') {
      this.mensagemErro = 'Pagamento cancelado.'
      this.estado = 'erro'
      return
    }

    if (!transactionId || !txRef) {
      this.mensagemErro = 'Dados de pagamento em falta.'
      this.estado = 'erro'
      return
    }

    try {
      // verificar pagamento no backend
      await api.post('/app/pagamento/flutterwave/verificar/', {
        transaction_id: transactionId,
        tx_ref:         txRef,
      })

      // limpar localStorage
      localStorage.removeItem('flw_tx_ref')
      localStorage.removeItem('flw_encomenda_id')

      // limpar carrinho
      window.dispatchEvent(new CustomEvent('carrinho-limpo', {
        detail: { lojaId: null }
      }))

      this.estado = 'sucesso'

    } catch (e) {
      this.mensagemErro = e.response?.data?.detail || 'Erro ao verificar o pagamento.'
      this.estado = 'erro'
    }
  },

  methods: {
    irParaSucesso () {
      if (this.encomendaId) {
        this.$router.push({ name: 'EncomendaSucesso', params: { id: this.encomendaId } })
      } else {
        this.$router.push({ name: 'Home' })
      }
    }
  }
}
</script>