<template>
  <div class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-lg w-full max-w-md p-6">
      <h2 class="text-2xl font-bold mb-4">Finalizar Pagamento</h2>

      <!-- Total -->
      <div class="bg-blue-50 rounded-lg p-4 mb-6">
        <div class="flex justify-between items-center">
          <span class="text-lg">Total a pagar:</span>
          <span class="text-3xl font-bold text-blue-600">{{ conta.total }}€</span>
        </div>
      </div>

      <!-- Métodos de Pagamento -->
      <div class="space-y-3 mb-6">
        <button
          v-for="metodo in metodosPagamento"
          :key="metodo.value"
          @click="metodoSelecionado = metodo.value"
          :class="[
            'w-full p-4 border-2 rounded-lg text-left transition',
            metodoSelecionado === metodo.value
              ? 'border-blue-600 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          ]"
        >
          <div class="flex justify-between items-center">
            <div>
              <div class="font-semibold">{{ metodo.label }}</div>
              <div class="text-sm text-gray-600">{{ metodo.descricao }}</div>
            </div>
            <div v-if="metodoSelecionado === metodo.value" class="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
              <span class="text-white text-sm">✓</span>
            </div>
          </div>
        </button>
      </div>

      <!-- NIF (opcional) -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          NIF do cliente (opcional)
        </label>
        <input
          v-model="nifCliente"
          type="text"
          placeholder="000000000"
          maxlength="9"
          class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Botões -->
      <div class="flex space-x-3">
        <button
          @click="$emit('close')"
          class="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 font-semibold"
        >
          Cancelar
        </button>
        <button
          @click="confirmarPagamento"
          :disabled="!metodoSelecionado || processando"
          class="flex-1 px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ processando ? 'Processando...' : 'Confirmar Pagamento' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'PagamentoModal',
  
  props: {
    conta: {
      type: Object,
      required: true
    }
  },
  
  data() {
    return {
      metodoSelecionado: null,
      nifCliente: '',
      processando: false,
      
      metodosPagamento: [
        { value: 'dinheiro', label: 'Dinheiro', descricao: 'Pagamento em numerário' },
        { value: 'cartao', label: 'Cartão', descricao: 'Débito ou crédito' },
        { value: 'mbway', label: 'MBWay', descricao: 'Pagamento via MBWay' },
        { value: 'transferencia', label: 'Transferência', descricao: 'Transferência bancária' }
      ]
    }
  },
  
  methods: {
    async confirmarPagamento() {
      if (!this.metodoSelecionado) return
      
      this.processando = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const posId = this.conta.pos
        
        await axios.post(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${posId}/contas/${this.conta.id}/fechar/`,
          {
            metodo_pagamento: this.metodoSelecionado,
            nif_cliente: this.nifCliente || ''
          },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        alert('✅ Pagamento confirmado com sucesso!')
        this.$emit('pago')
        
      } catch (error) {
        console.error('Erro ao processar pagamento:', error)
        alert(error.response?.data?.detail || 'Erro ao processar pagamento')
      } finally {
        this.processando = false
      }
    }
  }
}
</script>