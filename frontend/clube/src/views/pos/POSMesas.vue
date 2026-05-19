<template>
  <div class="space-y-4">
    <!-- Header com botão criar mesa -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">Mesas</h2>
        <p class="text-gray-600">{{ mesas.length }} mesas ativas</p>
      </div>
      <button
        @click="showCriarMesaModal = true"
        class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold transition"
      >
        + Nova Mesa
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white p-4 rounded-lg shadow">
      <div class="flex space-x-4">
        <button
          v-for="filtro in filtros"
          :key="filtro.value"
          @click="filtroAtivo = filtro.value"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition',
            filtroAtivo === filtro.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          {{ filtro.label }} ({{ contarMesas(filtro.value) }})
        </button>
      </div>
    </div>

    <!-- Grid de Mesas com Infinite Scroll -->
    <div
      ref="scrollContainer"
      @scroll="handleScroll"
      class="h-[calc(100vh-300px)] overflow-y-auto"
    >
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <MesaCard
          v-for="mesa in mesasFiltradas"
          :key="mesa.id"
          :mesa="mesa"
          @click="abrirMesa(mesa)"
          @editar="editarMesa(mesa)"
          @apagar="apagarMesa(mesa)"
        />
      </div>

      <!-- Loading indicator -->
      <div v-if="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="text-gray-600 mt-2">A carregar mais mesas...</p>
      </div>

      <!-- Fim dos dados -->
      <div v-if="!hasMore && mesas.length > 0" class="text-center py-8 text-gray-500">
        Todas as mesas carregadas
      </div>
    </div>

    <!-- Modal Criar Mesa -->
    <div v-if="showCriarMesaModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 class="text-xl font-bold mb-4">Nova Mesa</h3>
        <form @submit.prevent="criarMesa">
          <div class="mb-4">
            <label class="block text-gray-700 font-medium mb-2">Número/Nome</label>
            <input
              v-model="novaMesa.numero"
              type="text"
              placeholder="Ex: Mesa 5, Esplanada 2"
              required
              class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="mb-4">
            <label class="block text-gray-700 font-medium mb-2">Capacidade</label>
            <input
              v-model.number="novaMesa.capacidade"
              type="number"
              min="1"
              max="20"
              required
              class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="flex space-x-4">
            <button
              type="button"
              @click="showCriarMesaModal = false"
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Criar
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Conta -->
    <ContaModal
      v-if="mesaSelecionada"
      :mesa="mesaSelecionada"
      :pos-id="posId"
      @close="mesaSelecionada = null"
      @atualizar="carregarMesas"
    />
  </div>
</template>

<script>
import axios from 'axios'
import MesaCard from './components/MesaCard.vue'
import ContaModal from './components/ContaModal.vue'

export default {
  name: 'POSMesas',
  
  components: {
    MesaCard,
    ContaModal
  },
  
  props: {
    posId: {
      type: Number,
      required: true
    }
  },
  
  data() {
    return {
      mesas: [],
      offset: 0,
      limit: 20,
      loading: false,
      hasMore: true,
      filtroAtivo: 'todas',
      showCriarMesaModal: false,
      mesaSelecionada: null,
      
      novaMesa: {
        numero: '',
        capacidade: 4
      },
      
      filtros: [
        { value: 'todas', label: 'Todas' },
        { value: 'livre', label: 'Livres' },
        { value: 'ocupada', label: 'Ocupadas' },
        { value: 'reservada', label: 'Reservadas' }
      ]
    }
  },
  
  computed: {
    mesasFiltradas() {
      if (this.filtroAtivo === 'todas') {
        return this.mesas
      }
      return this.mesas.filter(m => m.status === this.filtroAtivo)
    }
  },
  
  created() {
    if (this.posId) {
      this.carregarMesas()
    }
  },
  
  watch: {
    posId(newId, oldId) {
      if (newId && newId !== oldId) {
        this.carregarMesas(true)
      }
    }
  },
  
  methods: {
    async carregarMesas(reset = false) {
      if (!this.posId) {
        return
      }
      if (this.loading) return
      
      if (reset) {
        this.mesas = []
        this.offset = 0
        this.hasMore = true
      }
      
      this.loading = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/mesas/`,
          {
            headers: { Authorization: `Bearer ${token}` },
            params: {
              offset: this.offset,
              limit: this.limit
            }
          }
        )
        
        const novasMesas = response.data.results || response.data
        
        if (novasMesas.length < this.limit) {
          this.hasMore = false
        }
        
        this.mesas.push(...novasMesas)
        this.offset += this.limit
        
      } catch (error) {
        console.error('Erro ao carregar mesas:', error)
        alert('Erro ao carregar mesas')
      } finally {
        this.loading = false
      }
    },
    
    handleScroll(event) {
      const { scrollTop, scrollHeight, clientHeight } = event.target
      
      // Carregar mais quando chegar a 80% do scroll
      if (scrollTop + clientHeight >= scrollHeight * 0.8 && this.hasMore && !this.loading) {
        this.carregarMesas()
      }
    },
    
    contarMesas(status) {
      if (status === 'todas') return this.mesas.length
      return this.mesas.filter(m => m.status === status).length
    },
    
    async criarMesa() {
      try {
        const token = localStorage.getItem('pos_access_token')
        await axios.post(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/mesas/criar/`,
          this.novaMesa,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        this.showCriarMesaModal = false
        this.novaMesa = { numero: '', capacidade: 4 }
        this.carregarMesas(true)
        
      } catch (error) {
        console.error('Erro ao criar mesa:', error)
        alert(error.response?.data?.detail || 'Erro ao criar mesa')
      }
    },
    
    abrirMesa(mesa) {
      this.mesaSelecionada = mesa
    },
    
    editarMesa(mesa) {
      // TODO: Implementar edição
      console.log('Editar mesa:', mesa)
    },
    
    async apagarMesa(mesa) {
      if (!confirm(`Apagar ${mesa.numero}?`)) return
      
      try {
        const token = localStorage.getItem('pos_access_token')
        await axios.delete(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/mesas/${mesa.id}/`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        this.carregarMesas(true)
        
      } catch (error) {
        console.error('Erro ao apagar mesa:', error)
        alert('Erro ao apagar mesa')
      }
    }
  }
}
</script>