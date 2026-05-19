<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">Produtos POS</h2>
        <p class="text-gray-600">Gestão de produtos para o sistema POS</p>
      </div>
      <button
        @click="showCriarProdutoModal = true"
        class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold transition"
      >
        + Novo Produto
      </button>
    </div>

    <!-- Search e Filtros -->
    <div class="bg-white p-4 rounded-lg shadow">
      <div class="flex space-x-4">
        <!-- Search -->
        <div class="flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Pesquisar produtos..."
            class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            @input="pesquisarProdutos"
          />
        </div>

        <!-- Filtro Categoria -->
        <select
          v-model="categoriaFiltro"
          @change="carregarProdutos(true)"
          class="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas categorias</option>
          <option v-for="cat in categorias" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>

        <!-- Filtro Ativo -->
        <select
          v-model="ativoFiltro"
          @change="carregarProdutos(true)"
          class="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos</option>
          <option value="true">Ativos</option>
          <option value="false">Inativos</option>
        </select>
      </div>
    </div>

    <!-- Grid de Produtos com Infinite Scroll -->
    <div
      ref="scrollContainer"
      @scroll="handleScroll"
      class="h-[calc(100vh-320px)] overflow-y-auto bg-white rounded-lg shadow p-4"
    >
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <div
          v-for="produto in produtos"
          :key="produto.id"
          class="border rounded-lg overflow-hidden hover:shadow-lg transition"
        >
          <!-- Imagem -->
          <div class="relative h-48 bg-gray-100">
            <img
              v-if="produto.imagem_url"
              :src="produto.imagem_url"
              :alt="produto.nome"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              Sem imagem
            </div>

            <!-- Badge Status -->
            <div
              :class="[
                'absolute top-2 right-2 px-2 py-1 rounded text-xs font-semibold',
                produto.ativo ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
              ]"
            >
              {{ produto.ativo ? 'Ativo' : 'Inativo' }}
            </div>
          </div>

          <!-- Info -->
          <div class="p-3">
            <h3 class="font-semibold text-sm mb-1 truncate">{{ produto.nome }}</h3>
            <p class="text-xs text-gray-600 mb-2">{{ produto.categoria }}</p>
            <div class="flex justify-between items-center mb-3">
              <span class="text-lg font-bold text-blue-600">{{ produto.preco }}€</span>
              <span v-if="produto.stock !== undefined" class="text-xs text-gray-500">
                Stock: {{ produto.stock }}
              </span>
            </div>

            <!-- Ações -->
            <div class="flex space-x-2">
              <button
                @click="editarProduto(produto)"
                class="flex-1 px-3 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-xs font-medium transition"
              >
                Editar
              </button>
              <button
                @click="toggleAtivo(produto)"
                :class="[
                  'flex-1 px-3 py-1 rounded text-xs font-medium transition',
                  produto.ativo
                    ? 'bg-red-50 hover:bg-red-100 text-red-700'
                    : 'bg-green-50 hover:bg-green-100 text-green-700'
                ]"
              >
                {{ produto.ativo ? 'Desativar' : 'Ativar' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="text-gray-600 mt-2">A carregar produtos...</p>
      </div>

      <!-- Fim -->
      <div v-if="!hasMore && produtos.length > 0" class="text-center py-8 text-gray-500">
        Todos os produtos carregados ({{ produtos.length }} total)
      </div>

      <!-- Empty -->
      <div v-if="!loading && produtos.length === 0" class="text-center py-12">
        <div class="text-gray-400 text-lg mb-2">Nenhum produto encontrado</div>
        <button
          @click="showCriarProdutoModal = true"
          class="text-blue-600 hover:text-blue-700 font-medium"
        >
          Criar primeiro produto
        </button>
      </div>
    </div>

    <!-- Modal Criar/Editar Produto -->
    <div v-if="showCriarProdutoModal || produtoEditando" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
          <h3 class="text-xl font-bold">
            {{ produtoEditando ? 'Editar Produto' : 'Novo Produto' }}
          </h3>
          <button @click="fecharModal" class="text-gray-400 hover:text-gray-600">
            <span class="text-2xl">×</span>
          </button>
        </div>

        <form @submit.prevent="salvarProduto" class="p-6 space-y-4">
          <!-- Nome -->
          <div>
            <label class="block text-gray-700 font-medium mb-2">Nome *</label>
            <input
              v-model="formProduto.nome"
              type="text"
              required
              placeholder="Ex: Café Expresso"
              class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <!-- Descrição -->
          <div>
            <label class="block text-gray-700 font-medium mb-2">Descrição</label>
            <textarea
              v-model="formProduto.descricao"
              rows="3"
              placeholder="Descrição do produto..."
              class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          <!-- Preço e Categoria -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-700 font-medium mb-2">Preço (€) *</label>
              <input
                v-model.number="formProduto.preco"
                type="number"
                step="0.01"
                min="0"
                required
                placeholder="0.00"
                class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-gray-700 font-medium mb-2">Categoria *</label>
              <input
                v-model="formProduto.categoria"
                type="text"
                required
                placeholder="Ex: Bebidas"
                list="categorias-list"
                class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <datalist id="categorias-list">
                <option v-for="cat in categorias" :key="cat" :value="cat" />
              </datalist>
            </div>
          </div>

          <!-- Stock -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex items-center">
              <input
                v-model="formProduto.controlar_stock"
                type="checkbox"
                id="controlar-stock"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label for="controlar-stock" class="ml-2 text-gray-700 font-medium">
                Controlar stock
              </label>
            </div>

            <div v-if="formProduto.controlar_stock">
              <label class="block text-gray-700 font-medium mb-2">Quantidade</label>
              <input
                v-model.number="formProduto.stock"
                type="number"
                min="0"
                placeholder="0"
                class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <!-- Imagem -->
          <div>
            <label class="block text-gray-700 font-medium mb-2">Imagem</label>
            <input
              type="file"
              accept="image/*"
              @change="handleImagemUpload"
              class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <div v-if="imagemPreview" class="mt-2">
              <img :src="imagemPreview" class="h-32 object-cover rounded" />
            </div>
          </div>

          <!-- Ativo -->
          <div class="flex items-center">
            <input
              v-model="formProduto.ativo"
              type="checkbox"
              id="produto-ativo"
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label for="produto-ativo" class="ml-2 text-gray-700 font-medium">
              Produto ativo (visível no POS)
            </label>
          </div>

          <!-- Botões -->
          <div class="flex space-x-4 pt-4">
            <button
              type="button"
              @click="fecharModal"
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-semibold"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="salvando"
              class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50"
            >
              {{ salvando ? 'Salvando...' : (produtoEditando ? 'Atualizar' : 'Criar') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'POSProdutos',
  
  props: {
    posId: {
      type: Number,
      required: true
    }
  },
  
  data() {
    return {
      produtos: [],
      categorias: ['Bebidas', 'Comidas', 'Sobremesas', 'Entradas', 'Pratos Principais'],
      offset: 0,
      limit: 20,
      loading: false,
      hasMore: true,
      searchQuery: '',
      categoriaFiltro: '',
      ativoFiltro: '',
      searchTimeout: null,
      
      showCriarProdutoModal: false,
      produtoEditando: null,
      salvando: false,
      imagemPreview: null,
      
      formProduto: {
        nome: '',
        descricao: '',
        preco: 0,
        categoria: '',
        controlar_stock: false,
        stock: 0,
        ativo: true,
        imagem: null
      }
    }
  },
  
  created() {
    this.carregarProdutos()
  },
  
  methods: {
    async carregarProdutos(reset = false) {
      if (this.loading) return
      
      if (reset) {
        this.produtos = []
        this.offset = 0
        this.hasMore = true
      }
      
      this.loading = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const params = {
          offset: this.offset,
          limit: this.limit
        }
        
        if (this.searchQuery) params.search = this.searchQuery
        if (this.categoriaFiltro) params.categoria = this.categoriaFiltro
        if (this.ativoFiltro) params.ativo = this.ativoFiltro
        
        const response = await axios.get(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/produtos/`,
          {
            headers: { Authorization: `Bearer ${token}` },
            params
          }
        )
        
        const novosProdutos = response.data.results || response.data
        
        if (novosProdutos.length < this.limit) {
          this.hasMore = false
        }
        
        this.produtos.push(...novosProdutos)
        this.offset += this.limit
        
      } catch (error) {
        console.error('Erro ao carregar produtos:', error)
      } finally {
        this.loading = false
      }
    },
    
    handleScroll(event) {
      const { scrollTop, scrollHeight, clientHeight } = event.target
      
      if (scrollTop + clientHeight >= scrollHeight * 0.8 && this.hasMore && !this.loading) {
        this.carregarProdutos()
      }
    },
    
    pesquisarProdutos() {
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.carregarProdutos(true)
      }, 500)
    },
    
    editarProduto(produto) {
      this.produtoEditando = produto
      this.formProduto = {
        nome: produto.nome,
        descricao: produto.descricao || '',
        preco: parseFloat(produto.preco),
        categoria: produto.categoria,
        controlar_stock: produto.controlar_stock || false,
        stock: produto.stock || 0,
        ativo: produto.ativo,
        imagem: null
      }
      
      if (produto.imagem_url) {
        this.imagemPreview = produto.imagem_url
      }
    },
    
    async toggleAtivo(produto) {
      try {
        const token = localStorage.getItem('pos_access_token')
        await axios.patch(
          `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/produtos/${produto.id}/`,
          { ativo: !produto.ativo },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        
        produto.ativo = !produto.ativo
        
      } catch (error) {
        console.error('Erro ao atualizar produto:', error)
        alert('Erro ao atualizar produto')
      }
    },
    
    handleImagemUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.formProduto.imagem = file
        
        // Preview
        const reader = new FileReader()
        reader.onload = (e) => {
          this.imagemPreview = e.target.result
        }
        reader.readAsDataURL(file)
      }
    },
    
    async salvarProduto() {
      this.salvando = true
      
      try {
        const token = localStorage.getItem('pos_access_token')
        const formData = new FormData()
        
        formData.append('nome', this.formProduto.nome)
        formData.append('descricao', this.formProduto.descricao)
        formData.append('preco', this.formProduto.preco)
        formData.append('categoria', this.formProduto.categoria)
        formData.append('controlar_stock', this.formProduto.controlar_stock)
        formData.append('stock', this.formProduto.stock)
        formData.append('ativo', this.formProduto.ativo)
        
        if (this.formProduto.imagem) {
          formData.append('imagem', this.formProduto.imagem)
        }
        
        if (this.produtoEditando) {
          // Editar
          await axios.put(
            `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/produtos/${this.produtoEditando.id}/`,
            formData,
            {
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'multipart/form-data'
              }
            }
          )
        } else {
          // Criar
          await axios.post(
            `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/produtos/criar/`,
            formData,
            {
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'multipart/form-data'
              }
            }
          )
        }
        
        this.fecharModal()
        this.carregarProdutos(true)
        
      } catch (error) {
        console.error('Erro ao salvar produto:', error)
        alert(error.response?.data?.detail || 'Erro ao salvar produto')
      } finally {
        this.salvando = false
      }
    },
    
    fecharModal() {
      this.showCriarProdutoModal = false
      this.produtoEditando = null
      this.imagemPreview = null
      this.formProduto = {
        nome: '',
        descricao: '',
        preco: 0,
        categoria: '',
        controlar_stock: false,
        stock: 0,
        ativo: true,
        imagem: null
      }
    }
  }
}
</script>