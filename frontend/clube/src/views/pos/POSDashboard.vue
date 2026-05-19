<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Header -->
    <header class="bg-white shadow-md">
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <!-- Logo e Nome do POS -->
        <div class="flex items-center space-x-4">
          <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-xl">P</span>
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-800">{{ posNome }}</h1>
            <p class="text-sm text-gray-500">{{ posCodigo }}</p>
          </div>
        </div>

        <!-- User Menu -->
        <div class="flex items-center space-x-4">
          <!-- Notificações -->
          <button class="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span v-if="pedidosPendentes > 0" class="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {{ pedidosPendentes }}
            </span>
          </button>

          <!-- User -->
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <span class="text-gray-700 font-semibold">{{ userInitial }}</span>
            </div>
            <span class="text-gray-700 font-medium">{{ userName }}</span>
          </div>

          <!-- Logout -->
          <button @click="logout" class="p-2 text-red-600 hover:bg-red-50 rounded-lg">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="bg-white border-b">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-4 px-2 border-b-2 font-medium text-sm transition',
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <span class="mr-2">{{ tab.icon }}</span>
            {{ tab.label }}
          </button>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto p-4">
      <component :is="currentTabComponent" :pos-id="posId" />
    </main>
  </div>
</template>

<script>
import POSMesas from './POSMesas.vue'
import POSPedidos from './POSPedidos.vue'
import POSHistorico from './POSHistorico.vue'

import POSProdutos from './POSProdutos.vue'  // ADICIONAR
import axios from 'axios'

export default {
  name: 'POSDashboard',
  
  components: {
    POSMesas,
    POSPedidos,
    POSHistorico,
  
    POSProdutos  // ADICIONAR
  },
  
  data() {
    return {
      activeTab: 'mesas',
      posId: null,
      posNome: '',
      posCodigo: '',
      userName: '',
      userInitial: '',
      pedidosPendentes: 0,
      
      tabs: [
        { id: 'mesas', label: 'Mesas', icon: '📊' },
        { id: 'pedidos', label: 'Pedidos', icon: '🛒' },
        { id: 'produtos', label: 'Produtos', icon: '📦' },  // ADICIONAR
        { id: 'historico', label: 'Histórico', icon: '📜' },
        { id: 'caixa', label: 'Caixa', icon: '💰' }
      ]
    }
  },
  
  computed: {
    currentTabComponent() {
      const componentMap = {
        'mesas': 'POSMesas',
        'pedidos': 'POSPedidos',
        'produtos': 'POSProdutos',  // ADICIONAR
        'historico': 'POSHistorico',
        'caixa': 'POSCaixa'
      }
      return componentMap[this.activeTab]
    }
  },
  
  async created() {
    this.loadUserData()
    await this.loadPOSData()
  },
  
  methods: {
    loadUserData() {
      const user = JSON.parse(localStorage.getItem('pos_user') || '{}')
      this.userName = user.nome || user.first_name || 'Utilizador'
      this.userInitial = this.userName.charAt(0).toUpperCase()
    },
    
    async loadPOSData() {
      try {
        // Carregar POS existentes do localStorage (guardados durante login)
        const posExistentes = JSON.parse(localStorage.getItem('pos_existentes') || '[]')
        
        // TODO: Por agora, assumir primeiro POS
        // Futuramente, permitir seleção se utilizador tiver múltiplos POS
        if (posExistentes && posExistentes.length > 0) {
          const primeiroPos = posExistentes[0]
          this.posId = primeiroPos.id
          this.posNome = primeiroPos.nome
          this.posCodigo = primeiroPos.codigo_pos
          
          // Guardar seleção atual
          localStorage.setItem('pos_selected', JSON.stringify(primeiroPos))
        } else {
          // Sem POS - redirecionar para criar
          alert('Nenhum POS encontrado. Vamos criar um!')
          // TODO: Redirecionar para tela de criação de POS
        }
        
      } catch (error) {
        console.error('Erro ao carregar POS:', error)
      }
    },
    
    logout() {
      if (confirm('Tem a certeza que quer sair?')) {
        localStorage.removeItem('pos_access_token')
        localStorage.removeItem('pos_refresh_token')
        localStorage.removeItem('pos_user')
        localStorage.removeItem('pos_selected')
        this.$router.push('/pos/login')
      }
    }
  }
}
</script>