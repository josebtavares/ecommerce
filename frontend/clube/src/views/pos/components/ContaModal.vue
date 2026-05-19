<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col">
      <!-- Header -->
      <div class="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-bold">{{ mesa.numero }}</h2>
          <p class="text-sm opacity-90">Capacidade: {{ mesa.capacidade }} pessoas</p>
        </div>
        <button @click="$emit('close')" class="text-white hover:bg-blue-700 rounded-lg p-2">
          <span class="text-2xl">×</span>
        </button>
      </div>

      <!-- Content -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Left: Produtos -->
        <div class="w-2/3 border-r overflow-y-auto p-4">
          <h3 class="text-lg font-bold mb-4">Adicionar Produtos</h3>
          
          <!-- Search -->
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Pesquisar produtos..."
            class="w-full px-4 py-2 border rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
            @input="pesquisarProdutos"
          />

          <!-- Produtos Grid com Infinite Scroll -->
          <div
            ref="produtosScroll"
            @scroll="handleProdutosScroll"
            class="h-[calc(100%-100px)] overflow-y-auto"
          >
            <div class="grid grid-cols-3 gap-4">
              <div
                v-for="produto in produtos"
                :key="produto.id"
                @click="adicionarProduto(produto)"
                class="border rounded-lg p-3 cursor-pointer hover:shadow-lg hover:border-blue-500 transition"
              >
                <img
                  v-if="produto.imagem_url"
                  :src="produto.imagem_url"
                  class="w-full h-32 object-cover rounded mb-2"
                />
                <div v-else class="w-full h-32 bg-gray-200 rounded mb-2 flex items-center justify-center">
                  <span class="text-gray-400">Sem imagem</span>
                </div>
                <h4 class="font-semibold text-sm mb-1">{{ produto.nome }}</h4>
                <p class="text-blue-600 font-bold">{{ produto.preco }}€</p>
                <p v-if="produto.stock" class="text-xs text-gray-500">Stock: {{ produto.stock }}</p>
              </div>
            </div>

            <!-- Loading -->
            <div v-if="loadingProdutos" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>

            <!-- No more products -->
            <div v-if="!hasMoreProdutos && produtos.length > 0" class="text-center py-4 text-gray-500">
              Todos os produtos carregados
            </div>
          </div>
        </div>

        <!-- Right: Conta -->
        <div class="w-1/3 flex flex-col">
          <!-- Items da Conta -->
          <div class="flex-1 overflow-y-auto p-4">
            <h3 class="text-lg font-bold mb-4">Pedido</h3>

            <div v-if="!conta || conta.items.length === 0" class="text-center text-gray-500 py-8">
              Nenhum item adicionado
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="item in conta.items"
                :key="item.id"
                class="bg-gray-50 rounded-lg p-3"
              >
                <div class="flex justify-between items-start mb-2">
                  <div class="flex-1">
                    <h4 class="font-semibold">{{ item.nome }}</h4>
                    <p class="text-sm text-gray-600">{{ item.preco_unitario }}€ × {{ item.quantidade }}</p>
                  </div>
                  <button
                    @click="removerItem(item)"
                    class="text-red-600 hover:bg-red-50 rounded p-1"
                  >
                    <span class="text-xl">×</span>
                  </button>
                </div>

                <!-- Quantidade Controls -->
                <div class="flex items-center space-x-2">
                  <button
                    @click="alterarQuantidade(item, -1)"
                    class="px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded"
                  >
                    -
                  </button>
                  <span class="font-semibold">{{ item.quantidade }}</span>
                  <button
                    @click="alterarQuantidade(item, 1)"
                    class="px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded"
                  >
                    +
                  </button>
                  <span class="ml-auto font-bold text-blue-600">{{ item.preco_total }}€</span>
                </div>

                <!-- Observações -->
                <input
                  v-model="item.observacoes"
                  type="text"
                  placeholder="Observações (ex: sem cebola)"
                  class="w-full mt-2 px-2 py-1 text-sm border rounded"
                  @blur="atualizarObservacoes(item)"
                />
              </div>
            </div>
          </div>

          <!-- Totais e Ações -->
          <div v-if="conta" class="border-t p-4 space-y-2">
            <div class="flex justify-between text-sm">
              <span>Subtotal:</span>
              <span class="font-semibold">{{ conta.subtotal }}€</span>
            </div>
            <div v-if="conta.taxa_servico_valor > 0" class="flex justify-between text-sm">
              <span>Taxa de serviço ({{ conta.taxa_servico_percentagem }}%):</span>
              <span class="font-semibold">{{ conta.taxa_servico_valor }}€</span>
            </div>
            <div class="flex justify-between text-lg font-bold border-t pt-2">
              <span>Total:</span>
              <span class="text-blue-600">{{ conta.total }}€</span>
            </div>

            <!-- Botões -->
            <div class="space-y-2 mt-4">
              <button
                @click="finalizarConta"
                :disabled="!conta || conta.items.length === 0"
                class="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Finalizar e Pagar
              </button>
              <button
                @click="$emit('close')"
                class="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 rounded-lg font-semibold"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Pagamento -->
    <PagamentoModal
      v-if="showPagamentoModal"
      :conta="conta"
      @close="showPagamentoModal = false"
      @pago="handlePagamentoConcluido"
    />
  </div>
</template>

<script>
import axios from 'axios'
import PagamentoModal from './PagamentoModal.vue'

export default {
  name: 'ContaModal',
  
  components: {
    PagamentoModal
  },
  
  props: {
    mesa: {
      type: Object,
      required: true
    },
    posId: {
      type: Number,
      required: true
    }
  },
  
  data() {
    return {
      conta: null,
      produtos: [],
      searchQuery: '',
      offsetProdutos: 0,
      limitProdutos: 15,
      loadingProdutos: false,
      hasMoreProdutos: true,
      searchTimeout: null,
      showPagamentoModal: false
    }
  },
  
  created() {
    this.carregarContaMesa()
    this.carregarProdutos()
  },
  
  methods: {
    async carregarContaMesa() {
      try {
        const token = localStorage.getItem('pos_access_token')
        
        // Verificar se mesa já tem conta aberta
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/mesas/${this.mesa.id}/conta/`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        this.conta = response.data
        
      } catch (error) {
        if (error.response?.status === 404) {
          // Criar nova conta
          await this.criarConta()
        } else {
          console.error('Erro ao carregar conta:', error)
        }
      }
    },
    
    async criarConta() {
      try {
        const token = localStorage.getItem('pos_access_token')
        const response = await axios.post(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/mesas/${this.mesa.id}/conta/`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        this.conta = response.data
        
      } catch (error) {
        console.error('Erro ao criar conta:', error)
        alert('Erro ao criar conta')
      }
    },
    
    async carregarProdutos(reset = false) {
      if (this.loadingProdutos) return
      
      if (reset) {
        this.produtos = []
        this.offsetProdutos = 0
        this.hasMoreProdutos = true
      }
      
      this.loadingProdutos = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/produtos/`,
          {
            headers: { Authorization: `Bearer ${token}` },
            params: {
              offset: this.offsetProdutos,
              limit: this.limitProdutos,
              search: this.searchQuery || undefined
            }
          }
        )
        
        const novosProdutos = response.data.results || response.data
        
        if (novosProdutos.length < this.limitProdutos) {
          this.hasMoreProdutos = false
        }
        
        this.produtos.push(...novosProdutos)
        this.offsetProdutos += this.limitProdutos
        
      } catch (error) {
        console.error('Erro ao carregar produtos:', error)
      } finally {
        this.loadingProdutos = false
      }
    },
    
    handleProdutosScroll(event) {
      const { scrollTop, scrollHeight, clientHeight } = event.target
      
      if (scrollTop + clientHeight >= scrollHeight * 0.8 && this.hasMoreProdutos && !this.loadingProdutos) {
        this.carregarProdutos()
      }
    },
    
    pesquisarProdutos() {
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.carregarProdutos(true)
      }, 500)
    },
    
    async adicionarProduto(produto) {
      try {
        const token = localStorage.getItem('pos_access_token')
        await axios.post(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/contas/${this.conta.id}/items/`,
          {
            produto_id: produto.id,
            quantidade: 1,
            observacoes: ''
          },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        // Recarregar conta
        await this.recarregarConta()
        
      } catch (error) {
        console.error('Erro ao adicionar produto:', error)
        alert(error.response?.data?.detail || 'Erro ao adicionar produto')
      }
    },
    
    async removerItem(item) {
      if (!confirm('Remover item da conta?')) return
      
      try {
        const token = localStorage.getItem('pos_access_token')
        await axios.delete(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/contas/${this.conta.id}/items/${item.id}/`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        await this.recarregarConta()
        
      } catch (error) {
        console.error('Erro ao remover item:', error)
        alert('Erro ao remover item')
      }
    },
    
    async alterarQuantidade(item, delta) {
      const novaQuantidade = item.quantidade + delta
      
      if (novaQuantidade <= 0) {
        this.removerItem(item)
        return
      }
      
      // TODO: Implementar endpoint de update quantidade
      item.quantidade = novaQuantidade
      await this.recarregarConta()
    },
    
    async atualizarObservacoes(item) {
      // TODO: Implementar endpoint de update observações
      console.log('Atualizar observações:', item.observacoes)
    },
    
    async recarregarConta() {
      try {
        const token = localStorage.getItem('pos_access_token')
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/contas/${this.conta.id}/`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        this.conta = response.data
        
      } catch (error) {
        console.error('Erro ao recarregar conta:', error)
      }
    },
    
    finalizarConta() {
      this.showPagamentoModal = true
    },
    
    handlePagamentoConcluido() {
      this.showPagamentoModal = false
      this.$emit('atualizar')
      this.$emit('close')
    }
  }
}
</script>