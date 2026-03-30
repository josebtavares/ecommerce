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
        <div class="flex justify-between text-sm border-t border-zinc-800 pt-3">
          <span class="text-zinc-400 font-semibold">Total</span>
          <span class="text-red-400 font-bold">{{ formatPrice(encomenda.valor_total) }}</span>
        </div>
        <div class="flex justify-between items-center text-sm">
          <span class="text-zinc-500">Estado</span>
          <span class="px-2 py-0.5 bg-blue-500/15 text-blue-400 text-xs font-bold rounded-full uppercase">
            {{ encomenda.status }}
          </span>
        </div>
      </div>

      <div class="flex gap-3">
        <button @click="$router.push({ name: 'Home' })"
          class="flex-1 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold transition">
          Voltar ao início
        </button>
        <button @click="$router.push({ name: 'Home' })"
          class="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-semibold transition">
          Ver encomendas
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'EncomendaSucesso',
  data () {
    return { encomenda: null }
  },
  async created () {
    try {
      const { data } = await api.get(`/app/encomenda/${this.$route.params.id}/`)
      this.encomenda = data
    } catch (e) { console.error(e) }
  },
  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    }
  }
}
</script>