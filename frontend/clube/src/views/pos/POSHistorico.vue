<template>
  <div class="space-y-4">
    <!-- Header com Filtros -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">Histórico</h2>
        <p class="text-gray-600">{{ totalCount }} contas registadas</p>
      </div>
    </div>

    <!-- Filtros -->
    <div class="bg-white p-4 rounded-lg shadow space-y-3">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Data Início -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Data Início</label>
          <input
            v-model="filtros.dataInicio"
            type="date"
            @change="carregarHistorico(true)"
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Data Fim -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Data Fim</label>
          <input
            v-model="filtros.dataFim"
            type="date"
            @change="carregarHistorico(true)"
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Método Pagamento -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Método Pagamento</label>
          <select
            v-model="filtros.metodoPagamento"
            @change="carregarHistorico(true)"
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos</option>
            <option value="dinheiro">Dinheiro</option>
            <option value="cartao">Cartão</option>
            <option value="mbway">MBWay</option>
            <option value="transferencia">Transferência</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="text-gray-600 mt-2">A carregar histórico...</p>
    </div>

    <!-- Tabela de Histórico -->
    <div v-else-if="historico.length > 0" class="bg-white rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Data/Hora</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Mesa</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Items</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Pagamento</th>
              <th class="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Total</th>
              <th class="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="conta in historico" :key="conta.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-sm text-gray-800">
                {{ formatDateTime(conta.fechada_em) }}
              </td>
              <td class="px-4 py-3 text-sm font-medium text-gray-800">
                {{ conta.mesa.numero }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">
                {{ conta.items.length }} item{{ conta.items.length !== 1 ? 's' : '' }}
              </td>
              <td class="px-4 py-3">
                <span :class="['px-2 py-1 rounded text-xs font-semibold', getMetodoBadge(conta.metodo_pagamento)]">
                  {{ getMetodoLabel(conta.metodo_pagamento) }}
                </span>
              </td>
              <td class="px-4 py-3 text-right text-sm font-bold text-blue-600">
                {{ conta.total }}€
              </td>
              <td class="px-4 py-3 text-center">
                <button
                  @click="verDetalhes(conta)"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Ver detalhes
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginação -->
      <div class="px-4 py-3 bg-gray-50 border-t flex justify-between items-center">
        <p class="text-sm text-gray-600">
          Mostrando {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
        </p>
        <div class="flex space-x-2">
          <button
            @click="carregarHistorico(false, page - 1)"
            :disabled="page <= 1"
            class="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Anterior
          </button>
          <button
            @click="carregarHistorico(false, page + 1)"
            :disabled="page >= totalPages"
            class="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Próxima
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12 bg-white rounded-lg shadow">
      <div class="text-gray-400 text-4xl mb-2">📜</div>
      <p class="text-gray-600">Nenhum registo encontrado</p>
    </div>

    <!-- Modal Detalhes -->
    <div v-if="contaSelecionada" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h3 class="text-xl font-bold">Conta #{{ contaSelecionada.id }}</h3>
              <p class="text-sm text-gray-600">{{ contaSelecionada.mesa.numero }}</p>
            </div>
            <button @click="contaSelecionada = null" class="text-gray-400 hover:text-gray-600">
              <span class="text-2xl">×</span>
            </button>
          </div>

          <!-- Items -->
          <div class="space-y-2 mb-4">
            <h4 class="font-semibold text-gray-700">Items:</h4>
            <div v-for="item in contaSelecionada.items" :key="item.id" class="flex justify-between p-2 bg-gray-50 rounded">
              <div>
                <p class="font-medium">{{ item.quantidade }}x {{ item.nome }}</p>
                <p v-if="item.observacoes" class="text-xs text-gray-600 italic">{{ item.observacoes }}</p>
              </div>
              <span class="font-bold">{{ item.preco_total }}€</span>
            </div>
          </div>

          <!-- Totais -->
          <div class="border-t pt-4 space-y-2">
            <div class="flex justify-between text-sm">
              <span>Subtotal:</span>
              <span class="font-semibold">{{ contaSelecionada.subtotal }}€</span>
            </div>
            <div v-if="contaSelecionada.taxa_servico_valor > 0" class="flex justify-between text-sm">
              <span>Taxa de serviço:</span>
              <span class="font-semibold">{{ contaSelecionada.taxa_servico_valor }}€</span>
            </div>
            <div class="flex justify-between text-lg font-bold border-t pt-2">
              <span>Total:</span>
              <span class="text-blue-600">{{ contaSelecionada.total }}€</span>
            </div>
          </div>

          <!-- Info Pagamento -->
          <div class="mt-4 p-3 bg-blue-50 rounded">
            <p class="text-sm"><strong>Método:</strong> {{ getMetodoLabel(contaSelecionada.metodo_pagamento) }}</p>
            <p class="text-sm"><strong>Data:</strong> {{ formatDateTime(contaSelecionada.fechada_em) }}</p>
            <p v-if="contaSelecionada.nif_cliente" class="text-sm"><strong>NIF:</strong> {{ contaSelecionada.nif_cliente }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'POSHistorico',
  
  props: {
    posId: {
      type: Number,
      required: true
    }
  },
  
  data() {
    return {
      historico: [],
      loading: false,
      page: 1,
      limit: 20,
      totalCount: 0,
      contaSelecionada: null,
      
      filtros: {
        dataInicio: '',
        dataFim: '',
        metodoPagamento: ''
      }
    }
  },
  
  computed: {
    totalPages() {
      return Math.ceil(this.totalCount / this.limit)
    }
  },
  
  created() {
    // Definir data início como há 30 dias
    const hoje = new Date()
    const ha30Dias = new Date(hoje.setDate(hoje.getDate() - 30))
    this.filtros.dataInicio = ha30Dias.toISOString().split('T')[0]
    this.filtros.dataFim = new Date().toISOString().split('T')[0]
    
    this.carregarHistorico()
  },
  
  methods: {
    async carregarHistorico(reset = false, novaPagina = this.page) {
      if (reset) {
        this.page = 1
        novaPagina = 1
      } else {
        this.page = novaPagina
      }
      
      this.loading = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const params = {
          offset: (this.page - 1) * this.limit,
          limit: this.limit
        }
        
        if (this.filtros.dataInicio) params.data_inicio = this.filtros.dataInicio
        if (this.filtros.dataFim) params.data_fim = this.filtros.dataFim
        if (this.filtros.metodoPagamento) params.metodo = this.filtros.metodoPagamento
        
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/historico/`,
          {
            headers: { Authorization: `Bearer ${token}` },
            params
          }
        )
        
        this.historico = response.data.results || response.data
        this.totalCount = response.data.count || this.historico.length
        
      } catch (error) {
        console.error('Erro ao carregar histórico:', error)
      } finally {
        this.loading = false
      }
    },
    
    verDetalhes(conta) {
      this.contaSelecionada = conta
    },
    
    getMetodoBadge(metodo) {
      const badges = {
        'dinheiro': 'bg-green-100 text-green-800',
        'cartao': 'bg-blue-100 text-blue-800',
        'mbway': 'bg-purple-100 text-purple-800',
        'transferencia': 'bg-orange-100 text-orange-800'
      }
      return badges[metodo] || 'bg-gray-100 text-gray-800'
    },
    
    getMetodoLabel(metodo) {
      const labels = {
        'dinheiro': 'Dinheiro',
        'cartao': 'Cartão',
        'mbway': 'MBWay',
        'transferencia': 'Transferência'
      }
      return labels[metodo] || metodo
    },
    
    formatDateTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('pt-PT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>