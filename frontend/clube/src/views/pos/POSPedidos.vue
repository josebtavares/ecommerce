<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">Pedidos Ativos</h2>
        <p class="text-gray-600">{{ pedidos.length }} pedidos em curso</p>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-sm text-gray-600">Atualizar automaticamente</span>
        <label class="relative inline-block w-12 h-6">
          <input v-model="autoRefresh" type="checkbox" class="sr-only peer" @change="toggleAutoRefresh">
          <div class="w-full h-full bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>
    </div>

    <!-- Filtros por Status -->
    <div class="bg-white p-4 rounded-lg shadow">
      <div class="flex space-x-4">
        <button
          v-for="filtro in filtrosStatus"
          :key="filtro.value"
          @click="statusFiltro = filtro.value"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition',
            statusFiltro === filtro.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          {{ filtro.label }} ({{ contarPorStatus(filtro.value) }})
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="text-gray-600 mt-2">A carregar pedidos...</p>
    </div>

    <!-- Lista de Pedidos -->
    <div v-else-if="pedidosFiltrados.length > 0" class="space-y-4">
      <div
        v-for="pedido in pedidosFiltrados"
        :key="pedido.id"
        class="bg-white rounded-lg shadow-md p-4 border-l-4"
        :class="getStatusColor(pedido.status)"
      >
        <!-- Header do Pedido -->
        <div class="flex justify-between items-start mb-3">
          <div>
            <h3 class="text-lg font-bold text-gray-800">{{ pedido.mesa.numero }}</h3>
            <p class="text-sm text-gray-600">Conta #{{ pedido.id }}</p>
          </div>
          <div class="text-right">
            <span :class="['px-3 py-1 rounded-full text-xs font-semibold', getStatusBadge(pedido.status)]">
              {{ getStatusLabel(pedido.status) }}
            </span>
            <p class="text-xs text-gray-500 mt-1">{{ formatTime(pedido.aberta_em) }}</p>
          </div>
        </div>

        <!-- Items do Pedido -->
        <div class="space-y-2 mb-3">
          <div
            v-for="item in pedido.items"
            :key="item.id"
            class="flex justify-between items-center p-2 bg-gray-50 rounded"
          >
            <div class="flex-1">
              <p class="font-semibold text-gray-800">{{ item.quantidade }}x {{ item.nome }}</p>
              <p v-if="item.observacoes" class="text-xs text-gray-600 italic">{{ item.observacoes }}</p>
              <span :class="['text-xs font-semibold', getItemStatusColor(item.status)]">
                {{ getItemStatusLabel(item.status) }}
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm font-bold text-gray-700">{{ item.preco_total }}€</span>
              <select
                v-model="item.status"
                @change="atualizarStatusItem(pedido.id, item.id, item.status)"
                class="text-xs border rounded px-2 py-1"
              >
                <option value="pendente">Pendente</option>
                <option value="preparando">A preparar</option>
                <option value="pronto">Pronto</option>
                <option value="entregue">Entregue</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Footer com Total -->
        <div class="flex justify-between items-center pt-3 border-t">
          <div class="text-sm text-gray-600">
            <span>{{ pedido.items.length }} item{{ pedido.items.length !== 1 ? 's' : '' }}</span>
            <span v-if="pedido.atendente_atual" class="ml-3">· Atendente: {{ pedido.atendente_atual.nome }}</span>
          </div>
          <div class="text-right">
            <p class="text-xs text-gray-500">Total</p>
            <p class="text-xl font-bold text-blue-600">{{ pedido.total }}€</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12 bg-white rounded-lg shadow">
      <div class="text-gray-400 text-4xl mb-2">🍽️</div>
      <p class="text-gray-600">Nenhum pedido ativo</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'POSPedidos',
  
  props: {
    posId: {
      type: Number,
      required: true
    }
  },
  
  data() {
    return {
      pedidos: [],
      loading: false,
      statusFiltro: 'todas',
      autoRefresh: false,
      refreshInterval: null,
      
      filtrosStatus: [
        { value: 'todas', label: 'Todas' },
        { value: 'aberta', label: 'Abertas' },
        { value: 'preparando', label: 'A preparar' },
        { value: 'pronto', label: 'Prontos' }
      ]
    }
  },
  
  computed: {
    pedidosFiltrados() {
      if (this.statusFiltro === 'todas') {
        return this.pedidos
      }
      
      if (this.statusFiltro === 'preparando' || this.statusFiltro === 'pronto') {
        return this.pedidos.filter(p => 
          p.items.some(item => item.status === this.statusFiltro)
        )
      }
      
      return this.pedidos.filter(p => p.status === this.statusFiltro)
    }
  },
  
  created() {
    this.carregarPedidos()
  },
  
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  
  methods: {
    async carregarPedidos() {
      this.loading = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/contas/ativas/`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        this.pedidos = response.data
        
      } catch (error) {
        console.error('Erro ao carregar pedidos:', error)
      } finally {
        this.loading = false
      }
    },
    
    toggleAutoRefresh() {
      if (this.autoRefresh) {
        this.refreshInterval = setInterval(() => {
          this.carregarPedidos()
        }, 10000) // Atualizar a cada 10 segundos
      } else {
        if (this.refreshInterval) {
          clearInterval(this.refreshInterval)
          this.refreshInterval = null
        }
      }
    },
    
    contarPorStatus(status) {
      if (status === 'todas') return this.pedidos.length
      if (status === 'preparando' || status === 'pronto') {
        return this.pedidos.filter(p => 
          p.items.some(item => item.status === status)
        ).length
      }
      return this.pedidos.filter(p => p.status === status).length
    },
    
    async atualizarStatusItem(contaId, itemId, novoStatus) {
      try {
        const token = localStorage.getItem('pos_access_token')
        await axios.patch(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/contas/${contaId}/items/${itemId}/`,
          { status: novoStatus },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        await this.carregarPedidos()
        
      } catch (error) {
        console.error('Erro ao atualizar status:', error)
        alert('Erro ao atualizar status do item')
      }
    },
    
    getStatusColor(status) {
      const colors = {
        'aberta': 'border-blue-500',
        'fechada': 'border-green-500',
        'cancelada': 'border-red-500'
      }
      return colors[status] || 'border-gray-300'
    },
    
    getStatusBadge(status) {
      const badges = {
        'aberta': 'bg-blue-100 text-blue-800',
        'fechada': 'bg-green-100 text-green-800',
        'cancelada': 'bg-red-100 text-red-800'
      }
      return badges[status] || 'bg-gray-100 text-gray-800'
    },
    
    getStatusLabel(status) {
      const labels = {
        'aberta': 'Aberta',
        'fechada': 'Fechada',
        'cancelada': 'Cancelada'
      }
      return labels[status] || status
    },
    
    getItemStatusColor(status) {
      const colors = {
        'pendente': 'text-gray-600',
        'preparando': 'text-orange-600',
        'pronto': 'text-green-600',
        'entregue': 'text-blue-600',
        'cancelado': 'text-red-600'
      }
      return colors[status] || 'text-gray-600'
    },
    
    getItemStatusLabel(status) {
      const labels = {
        'pendente': '⏳ Pendente',
        'preparando': '🔥 A preparar',
        'pronto': '✅ Pronto',
        'entregue': '🎉 Entregue',
        'cancelado': '❌ Cancelado'
      }
      return labels[status] || status
    },
    
    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const now = new Date()
      const diff = Math.floor((now - date) / 1000 / 60) // minutos
      
      if (diff < 1) return 'Agora mesmo'
      if (diff < 60) return `Há ${diff} min`
      
      const hours = Math.floor(diff / 60)
      return `Há ${hours}h ${diff % 60}min`
    }
  }
}
</script>