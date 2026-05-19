<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-black text-slate-950">Produtos POS</h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          Gere produtos próprios do POS e produtos da loja Bendi.
        </p>
      </div>

      <button
        type="button"
        @click="abrirModalCriar"
        class="inline-flex h-11 items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        + Novo produto
      </button>
    </div>

    <!-- Info modo -->
    <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-sm font-black text-slate-950">
            Modo atual: {{ modoLabel }}
          </p>
          <p class="mt-1 text-xs font-semibold text-slate-500">
            <span v-if="modo === 'standalone'">
              Este POS usa apenas produtos próprios.
            </span>
            <span v-else-if="modo === 'integrado'">
              Este POS usa apenas produtos da loja Bendi vinculada.
            </span>
            <span v-else-if="modo === 'hibrido'">
              Este POS usa produtos próprios e produtos da loja Bendi.
            </span>
            <span v-else>
              A carregar configuração do POS...
            </span>
          </p>
        </div>

        <div
          v-if="lojaVinculada"
          class="rounded-2xl bg-blue-50 px-4 py-2 text-sm font-black text-blue-700"
        >
          Loja: {{ lojaVinculada.nome }}
        </div>

        <div
          v-else
          class="rounded-2xl bg-amber-50 px-4 py-2 text-sm font-black text-amber-700"
        >
          Sem loja vinculada
        </div>
      </div>
    </section>

    <!-- Alertas -->
    <div
      v-if="error"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
    >
      {{ error }}
    </div>

    <div
      v-if="success"
      class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
    >
      {{ success }}
    </div>

    <!-- Filtros -->
    <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-[1fr_180px_180px_180px]">
        <input
          v-model.trim="searchQuery"
          type="text"
          placeholder="Pesquisar por nome, categoria ou descrição..."
          class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        />

        <select
          v-model="origemFiltro"
          class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        >
          <option value="">Todas origens</option>
          <option value="pos">Produtos POS</option>
          <option value="loja">Loja Bendi</option>
        </select>

        <select
          v-model="categoriaFiltro"
          class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        >
          <option value="">Todas categorias</option>
          <option v-for="cat in categorias" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>

        <select
          v-model="ativoFiltro"
          class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        >
          <option value="">Todos</option>
          <option value="true">Ativos</option>
          <option value="false">Inativos</option>
        </select>
      </div>
    </section>

    <!-- Loading -->
    <div
      v-if="loading && produtos.length === 0"
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5"
    >
      <div
        v-for="i in 10"
        :key="i"
        class="h-64 animate-pulse rounded-[1.5rem] bg-slate-100"
      ></div>
    </div>

    <!-- Empty -->
    <section
      v-else-if="produtosFiltrados.length === 0"
      class="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-10 text-center"
    >
      <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">
        📦
      </div>

      <h3 class="mt-5 text-xl font-black text-slate-950">
        Nenhum produto encontrado
      </h3>

      <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
        Cria produtos próprios do POS ou liga o POS a uma loja Bendi para importar o catálogo.
      </p>

      <button
        type="button"
        @click="abrirModalCriar"
        class="mt-6 inline-flex h-11 items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        Criar produto
      </button>
    </section>

    <!-- Grid -->
    <section
      v-else
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5"
    >
      <article
        v-for="produto in produtosFiltrados"
        :key="produto.uid || `${produto.origem}-${produto.id}`"
        class="group overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl"
      >
        <div class="relative aspect-square bg-slate-100">
          <img
            v-if="produto.imagem_url"
            :src="produto.imagem_url"
            :alt="produto.nome"
            class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
          />

          <div
            v-else
            class="flex h-full w-full items-center justify-center text-4xl text-slate-300"
          >
            📦
          </div>

          <div class="absolute left-2 top-2 flex flex-wrap gap-1">
            <span
              :class="[
                'rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide',
                produto.origem === 'pos'
                  ? 'bg-purple-600 text-white'
                  : 'bg-blue-600 text-white'
              ]"
            >
              {{ produto.origem === 'pos' ? 'POS' : 'Loja' }}
            </span>

            <span
              v-if="produto.disponivel === false"
              class="rounded-full bg-amber-500 px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-white"
            >
              Indisp.
            </span>
          </div>

          <div
            :class="[
              'absolute right-2 top-2 rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide',
              produtoAtivo(produto)
                ? 'bg-emerald-500 text-white'
                : 'bg-red-500 text-white'
            ]"
          >
            {{ produtoAtivo(produto) ? 'Ativo' : 'Inativo' }}
          </div>
        </div>

        <div class="p-4">
          <h3 class="line-clamp-2 min-h-[40px] text-sm font-black text-slate-950">
            {{ produto.nome }}
          </h3>

          <p class="mt-1 truncate text-xs font-semibold text-slate-500">
            {{ produto.categoria || 'Sem categoria' }}
          </p>

          <div class="mt-3 flex items-center justify-between gap-2">
            <span class="text-lg font-black text-slate-950">
              {{ money(produto.preco) }}
            </span>

            <span class="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-black text-slate-500">
              Stock: {{ produto.stock ?? '—' }}
            </span>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-2">
            <button
              type="button"
              @click="editarProduto(produto)"
              class="h-9 rounded-xl bg-slate-100 text-xs font-black text-slate-700 transition hover:bg-slate-200"
            >
              Editar
            </button>

            <button
              type="button"
              @click="toggleAtivo(produto)"
              :class="[
                'h-9 rounded-xl text-xs font-black transition',
                produtoAtivo(produto)
                  ? 'bg-red-50 text-red-700 hover:bg-red-100'
                  : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
              ]"
            >
              {{ produtoAtivo(produto) ? 'Desativar' : 'Ativar' }}
            </button>
          </div>
        </div>
      </article>
    </section>

    <!-- Modal Criar/Editar Produto -->
    <div
      v-if="showProdutoModal"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharModal"
    >
      <div class="max-h-[95vh] w-full max-w-2xl overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-white p-5">
          <div>
            <h3 class="text-xl font-black text-slate-950">
              {{ produtoEditando ? 'Editar produto' : 'Novo produto' }}
            </h3>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              {{ produtoEditando ? 'Atualiza os dados do produto.' : 'Escolhe se o produto será próprio do POS ou da loja Bendi.' }}
            </p>
          </div>

          <button
            type="button"
            @click="fecharModal"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </header>

        <form class="max-h-[calc(95vh-88px)] space-y-4 overflow-y-auto p-5" @submit.prevent="salvarProduto">
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Origem do produto
            </label>

            <select
              v-model="formProduto.origem"
              :disabled="!!produtoEditando"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10 disabled:cursor-not-allowed disabled:opacity-70"
            >
              <option
                v-if="podeCriarProdutoPOS"
                value="pos"
              >
                Produto próprio do POS
              </option>

              <option
                v-if="podeCriarProdutoLoja"
                value="loja"
              >
                Produto da loja Bendi
              </option>
            </select>

            <p class="mt-2 text-xs font-semibold text-slate-400">
              Em modo standalone só podes criar produtos próprios do POS. Em híbrido podes criar nos dois lados.
            </p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Nome *
            </label>

            <input
              v-model.trim="formProduto.nome"
              type="text"
              required
              placeholder="Ex: Café expresso"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Descrição
            </label>

            <textarea
              v-model.trim="formProduto.descricao"
              rows="3"
              placeholder="Descrição do produto..."
              class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            ></textarea>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">
                Preço *
              </label>

              <input
                v-model.number="formProduto.preco"
                type="number"
                step="0.01"
                min="0"
                required
                placeholder="0.00"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
            </div>

            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">
                Categoria
              </label>

              <input
                v-model.trim="formProduto.categoria"
                type="text"
                list="categorias-list"
                placeholder="Ex: Bebidas"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />

              <datalist id="categorias-list">
                <option v-for="cat in categorias" :key="cat" :value="cat" />
              </datalist>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50 px-4">
              <input
                v-model="formProduto.controlar_stock"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 text-slate-950 focus:ring-slate-950"
              />
              <span class="ml-2 text-sm font-black text-slate-700">
                Controlar stock
              </span>
            </label>

            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">
                Stock
              </label>

              <input
                v-model.number="formProduto.stock"
                type="number"
                min="0"
                placeholder="0"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
            </div>
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Imagem/Ficheiro
            </label>

            <input
              type="file"
              accept="image/*,video/*"
              @change="handleImagemUpload"
              class="block w-full cursor-pointer rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 file:mr-4 file:rounded-xl file:border-0 file:bg-slate-950 file:px-4 file:py-2 file:text-sm file:font-black file:text-white hover:file:bg-slate-800"
            />

            <div v-if="imagemPreview" class="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
              <img
                v-if="isImagePreview"
                :src="imagemPreview"
                class="h-44 w-full object-cover"
              />

              <div
                v-else
                class="flex h-24 items-center justify-center text-sm font-bold text-slate-500"
              >
                Ficheiro selecionado
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50 px-4">
              <input
                v-model="formProduto.ativo"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 text-slate-950 focus:ring-slate-950"
              />
              <span class="ml-2 text-sm font-black text-slate-700">
                Produto ativo
              </span>
            </label>

            <label class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50 px-4">
              <input
                v-model="formProduto.disponivel_pos"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 text-slate-950 focus:ring-slate-950"
              />
              <span class="ml-2 text-sm font-black text-slate-700">
                Disponível no POS
              </span>
            </label>
          </div>

          <div class="grid grid-cols-2 gap-3 pt-4">
            <button
              type="button"
              @click="fecharModal"
              class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
            >
              Cancelar
            </button>

            <button
              type="submit"
              :disabled="salvando || !formProduto.origem"
              class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span v-if="!salvando">
                {{ produtoEditando ? 'Atualizar' : 'Criar' }}
              </span>

              <span v-else class="flex items-center gap-2">
                <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                A guardar...
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/api'

export default {
  name: 'POSProdutos',

  props: {
    posId: {
      type: [Number, String],
      required: true
    }
  },

  data() {
    return {
      produtos: [],
      loading: false,
      searchQuery: '',
      categoriaFiltro: '',
      origemFiltro: '',
      ativoFiltro: '',

      modo: '',
      lojaVinculada: null,

      showProdutoModal: false,
      produtoEditando: null,
      salvando: false,
      imagemPreview: null,
      isImagePreview: true,

      error: '',
      success: '',

      formProduto: {
        origem: 'pos',
        nome: '',
        descricao: '',
        preco: 0,
        categoria: '',
        controlar_stock: false,
        stock: 0,
        ativo: true,
        disponivel_pos: true,
        imagem: null
      }
    }
  },

  computed: {
    modoLabel() {
      const labels = {
        standalone: 'Standalone',
        integrado: 'Integrado',
        hibrido: 'Híbrido'
      }

      return labels[this.modo] || '—'
    },

    podeCriarProdutoPOS() {
      return this.modo === 'standalone' || this.modo === 'hibrido'
    },

    podeCriarProdutoLoja() {
      return (this.modo === 'integrado' || this.modo === 'hibrido') && !!this.lojaVinculada
    },

    categorias() {
      const categoriasProdutos = this.produtos
        .map((produto) => produto.categoria)
        .filter(Boolean)

      return [...new Set(categoriasProdutos)]
    },

    produtosFiltrados() {
      const query = this.searchQuery.toLowerCase().trim()

      return this.produtos.filter((produto) => {
        const matchesSearch =
          !query ||
          String(produto.nome || '').toLowerCase().includes(query) ||
          String(produto.descricao || '').toLowerCase().includes(query) ||
          String(produto.categoria || '').toLowerCase().includes(query)

        const matchesCategoria =
          !this.categoriaFiltro || produto.categoria === this.categoriaFiltro

        const matchesOrigem =
          !this.origemFiltro || produto.origem === this.origemFiltro

        const ativoProduto = this.produtoAtivo(produto)

        const matchesAtivo =
          this.ativoFiltro === '' || String(ativoProduto) === this.ativoFiltro

        return matchesSearch && matchesCategoria && matchesOrigem && matchesAtivo
      })
    }
  },

  created() {
    this.carregarProdutos()
  },

  watch: {
    posId(newId, oldId) {
      if (newId && newId !== oldId) {
        this.carregarProdutos()
      }
    }
  },

  methods: {
    async carregarProdutos() {
      if (!this.posId || this.loading) return

      this.loading = true
      this.error = ''

      try {
        const { data } = await api.get(`/api/pos/${this.posId}/produtos/?gestao=1`)

        this.modo = data.modo || ''
        this.lojaVinculada = data.loja_vinculada || null

        this.produtos = Array.isArray(data.results)
          ? data.results.map(this.normalizarProduto)
          : Array.isArray(data)
            ? data.map(this.normalizarProduto)
            : []
      } catch (error) {
        console.error('Erro ao carregar produtos:', error)
        this.error = error.response?.data?.detail || 'Erro ao carregar produtos.'
      } finally {
        this.loading = false
      }
    },

    abrirModalCriar() {
      this.clearMessages()
      this.produtoEditando = null
      this.resetForm()

      if (this.podeCriarProdutoPOS) {
        this.formProduto.origem = 'pos'
      } else if (this.podeCriarProdutoLoja) {
        this.formProduto.origem = 'loja'
      } else {
        this.formProduto.origem = ''
      }

      this.showProdutoModal = true
    },

    editarProduto(produto) {
      this.clearMessages()
      this.produtoEditando = produto
      this.showProdutoModal = true

      this.formProduto = {
        origem: produto.origem || 'pos',
        nome: produto.nome || '',
        descricao: produto.descricao || '',
        preco: Number(produto.preco || 0),
        categoria: produto.categoria || '',
        controlar_stock: Boolean(produto.controlar_stock),
        stock: Number(produto.stock || 0),
        ativo: this.produtoAtivo(produto),
        disponivel_pos: produto.disponivel_pos ?? true,
        imagem: null
      }

      this.imagemPreview = produto.imagem_url || null
      this.isImagePreview = true
    },

    async toggleAtivo(produto) {
      this.clearMessages()

      try {
        const formData = new FormData()
        formData.append('origem', produto.origem)
        formData.append('ativo', String(!this.produtoAtivo(produto)))

        await api.patch(
          `/api/pos/${this.posId}/produtos/${produto.id}/`,
          formData
        )

        this.success = 'Produto atualizado com sucesso.'
        await this.carregarProdutos()
      } catch (error) {
        console.error('Erro ao atualizar produto:', error)
        this.error = error.response?.data?.detail || 'Erro ao atualizar produto.'
      }
    },

    handleImagemUpload(event) {
      const file = event.target.files?.[0]

      if (!file) return

      this.formProduto.imagem = file
      this.isImagePreview = file.type.startsWith('image/')

      if (this.isImagePreview) {
        const reader = new FileReader()
        reader.onload = (e) => {
          this.imagemPreview = e.target.result
        }
        reader.readAsDataURL(file)
      } else {
        this.imagemPreview = 'file'
      }
    },

    async salvarProduto() {
      this.clearMessages()

      const validationError = this.validarForm()
      if (validationError) {
        this.error = validationError
        return
      }

      this.salvando = true

      try {
        const formData = new FormData()

        formData.append('origem', this.formProduto.origem)
        formData.append('nome', this.formProduto.nome.trim())
        formData.append('descricao', this.formProduto.descricao || '')
        formData.append('preco', String(this.formProduto.preco))
        formData.append('categoria', this.formProduto.categoria || 'Sem categoria')
        formData.append('controlar_stock', String(Boolean(this.formProduto.controlar_stock)))
        formData.append('stock', String(Number(this.formProduto.stock || 0)))
        formData.append('ativo', String(Boolean(this.formProduto.ativo)))
        formData.append('disponivel_pos', String(Boolean(this.formProduto.disponivel_pos)))

        // Para produtos da loja Bendi, a backend também aceita "categoria" e cria CategoriaLoja.
        if (this.formProduto.origem === 'loja' && this.formProduto.categoria) {
          formData.append('novas_categorias', this.formProduto.categoria.trim())
        }

        if (this.formProduto.imagem) {
          // Backend aceita ambos; para loja Bendi usa ficheiro, para POS usa imagem.
          formData.append('imagem', this.formProduto.imagem)
          formData.append('ficheiro', this.formProduto.imagem)
        }

        if (this.produtoEditando) {
          await api.patch(
            `/api/pos/${this.posId}/produtos/${this.produtoEditando.id}/`,
            formData
          )
          this.success = 'Produto atualizado com sucesso.'
        } else {
          await api.post(`/api/pos/${this.posId}/produtos/criar/`, formData)
          this.success = 'Produto criado com sucesso.'
        }

        this.fecharModal()
        await this.carregarProdutos()
      } catch (error) {
        console.error('Erro ao salvar produto:', error)
        this.error = error.response?.data?.detail || this.formatBackendError(error.response?.data) || 'Erro ao salvar produto.'
      } finally {
        this.salvando = false
      }
    },

    fecharModal() {
      this.showProdutoModal = false
      this.produtoEditando = null
      this.resetForm()
    },

    resetForm() {
      this.imagemPreview = null
      this.isImagePreview = true

      this.formProduto = {
        origem: 'pos',
        nome: '',
        descricao: '',
        preco: 0,
        categoria: '',
        controlar_stock: false,
        stock: 0,
        ativo: true,
        disponivel_pos: true,
        imagem: null
      }
    },

    validarForm() {
      if (!this.formProduto.origem) {
        return 'Escolhe a origem do produto.'
      }

      if (this.formProduto.origem === 'pos' && !this.podeCriarProdutoPOS && !this.produtoEditando) {
        return 'Este POS não permite criar produtos próprios.'
      }

      if (this.formProduto.origem === 'loja' && !this.podeCriarProdutoLoja && !this.produtoEditando) {
        return 'Este POS não permite criar produtos da loja.'
      }

      if (!this.formProduto.nome.trim()) {
        return 'O nome do produto é obrigatório.'
      }

      if (Number(this.formProduto.preco) < 0) {
        return 'O preço não pode ser negativo.'
      }

      if (Number(this.formProduto.stock) < 0) {
        return 'O stock não pode ser negativo.'
      }

      return null
    },

    normalizarProduto(produto) {
      const categoria =
        produto.categoria ||
        produto.categorias?.[0]?.nome ||
        produto.tipo?.nome ||
        'Sem categoria'

      return {
        ...produto,
        uid: produto.uid || `${produto.origem}-${produto.id}`,
        categoria,
        imagem_url: produto.imagem_url || produto.ficheiro_url || null,
        ativo: produto.ativo ?? true,
        disponivel_pos: produto.disponivel_pos ?? true,
        stock: produto.stock ?? 0,
        origem: produto.origem || 'pos'
      }
    },

    produtoAtivo(produto) {
      return produto.ativo ?? true
    },

    money(value) {
      const number = Number(value || 0)

      return new Intl.NumberFormat('pt-PT', {
        style: 'currency',
        currency: 'EUR'
      }).format(number)
    },

    formatBackendError(data) {
      if (!data || typeof data !== 'object') return ''

      const firstKey = Object.keys(data)[0]
      const value = data[firstKey]

      if (Array.isArray(value)) return `${firstKey}: ${value.join(', ')}`
      if (typeof value === 'string') return `${firstKey}: ${value}`

      return ''
    },

    clearMessages() {
      this.error = ''
      this.success = ''
    }
  }
}
</script>