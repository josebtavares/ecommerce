<template>
  <div class="fixed inset-0 z-50 flex items-end justify-center bg-black/55 p-0 backdrop-blur-sm sm:items-center sm:p-4">
    <div class="flex h-[96vh] w-full max-w-7xl flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:h-[90vh] sm:rounded-[2rem]">
      <!-- Header -->
      <header class="border-b border-slate-200 bg-white px-4 py-4 sm:px-6">
        <div class="flex items-center justify-between gap-4">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-2xl font-black text-slate-950">
                {{ mesa.numero }}
              </h2>

              <span
                :class="[
                  'rounded-full px-3 py-1 text-xs font-black uppercase tracking-wide',
                  mesa.status === 'ocupada'
                    ? 'bg-blue-50 text-blue-700'
                    : 'bg-emerald-50 text-emerald-700'
                ]"
              >
                {{ mesa.status || 'livre' }}
              </span>
            </div>

            <p class="mt-1 text-sm font-semibold text-slate-500">
              Capacidade: {{ mesa.capacidade }} pessoas
            </p>
          </div>

          <button
            type="button"
            @click="$emit('close')"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </div>

        <div class="mt-4 flex gap-2 lg:hidden">
          <button
            type="button"
            @click="activePanel = 'produtos'"
            :class="[
              'flex-1 rounded-2xl border px-4 py-3 text-sm font-black transition',
              activePanel === 'produtos'
                ? 'border-slate-950 bg-slate-950 text-white'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
            ]"
          >
            Produtos
          </button>

          <button
            type="button"
            @click="activePanel = 'pedido'"
            :class="[
              'flex-1 rounded-2xl border px-4 py-3 text-sm font-black transition',
              activePanel === 'pedido'
                ? 'border-slate-950 bg-slate-950 text-white'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
            ]"
          >
            Pedido
          </button>
        </div>
      </header>

      <!-- Error -->
      <div
        v-if="error"
        class="mx-4 mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700 sm:mx-6"
      >
        {{ error }}
      </div>

      <!-- Body -->
      <div class="grid min-h-0 flex-1 grid-cols-1 overflow-hidden lg:grid-cols-[1fr_420px]">
        <!-- Produtos -->
        <section :class="['min-h-0 border-b border-slate-200 p-4 lg:border-b-0 lg:border-r lg:p-6', activePanel === 'produtos' ? 'block' : 'hidden lg:block']">
          <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 class="text-xl font-black text-slate-950">Adicionar produtos</h3>
              <p class="text-sm font-semibold text-slate-500">
                {{ produtosFiltrados.length }} produtos disponíveis
              </p>
            </div>

            <button
              type="button"
              @click="carregarProdutos"
              :disabled="loadingProdutos"
              class="h-10 rounded-2xl bg-slate-100 px-4 text-sm font-black text-slate-700 transition hover:bg-slate-200 disabled:opacity-60"
            >
              Atualizar
            </button>
          </div>

          <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-[1fr_160px]">
            <input
              v-model.trim="searchQuery"
              type="text"
              placeholder="Pesquisar produtos..."
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />

            <select
              v-model="origemFiltro"
              class="h-12 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            >
              <option value="">Todos</option>
              <option value="pos">POS</option>
              <option value="loja">Loja</option>
            </select>
          </div>

          <div v-if="categoriasDisponiveis.length" class="mb-4 flex flex-wrap gap-2">
            <button
              type="button"
              @click="categoriaFiltro = ''"
              :class="[
                'rounded-2xl px-3 py-2 text-xs font-black transition',
                !categoriaFiltro
                  ? 'bg-slate-950 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              ]"
            >
              Todas
            </button>

            <button
              v-for="categoria in categoriasDisponiveis"
              :key="categoria"
              type="button"
              @click="categoriaFiltro = categoria"
              :class="[
                'rounded-2xl px-3 py-2 text-xs font-black transition',
                categoriaFiltro === categoria
                  ? 'bg-slate-950 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              ]"
            >
              {{ categoria }}
            </button>
          </div>

          <div
            v-if="loadingProdutos && produtos.length === 0"
            class="grid grid-cols-2 gap-3 overflow-y-auto pr-1 sm:grid-cols-3 xl:grid-cols-4"
          >
            <div
              v-for="i in 8"
              :key="i"
              class="h-48 animate-pulse rounded-[1.5rem] bg-slate-100"
            ></div>
          </div>

          <div
            v-else-if="produtosFiltrados.length === 0"
            class="flex h-full min-h-[280px] flex-col items-center justify-center rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
          >
            <div class="flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">
              📦
            </div>

            <h4 class="mt-4 text-lg font-black text-slate-950">
              Nenhum produto disponível
            </h4>

            <p class="mt-2 max-w-sm text-sm leading-6 text-slate-500">
              Cria produtos próprios no POS ou liga o POS a uma loja Bendi.
            </p>
          </div>

          <div
            v-else
            class="grid max-h-[calc(100vh-370px)] grid-cols-2 gap-3 overflow-y-auto pr-1 sm:grid-cols-3 lg:max-h-[calc(90vh-240px)] xl:grid-cols-4"
          >
            <button
              v-for="produto in produtosFiltrados"
              :key="produto.uid || `${produto.origem}-${produto.id}`"
              type="button"
              :disabled="addingProdutoUid === produtoUid(produto) || produto.disponivel === false"
              @click="adicionarProduto(produto)"
              class="group overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
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

                <span
                  :class="[
                    'absolute left-2 top-2 rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-white',
                    produto.origem === 'pos' ? 'bg-purple-600' : 'bg-blue-600'
                  ]"
                >
                  {{ produto.origem === 'pos' ? 'POS' : 'Loja' }}
                </span>
              </div>

              <div class="p-3">
                <p class="line-clamp-2 min-h-[40px] text-sm font-black text-slate-950">
                  {{ produto.nome }}
                </p>

                <p class="mt-1 truncate text-xs font-semibold text-slate-500">
                  {{ produto.categoria || 'Sem categoria' }}
                </p>

                <div class="mt-3 flex items-center justify-between gap-2">
                  <span class="text-base font-black text-slate-950">
                    {{ money(produto.preco) }}
                  </span>

                  <span
                    v-if="produto.stock !== null && produto.stock !== undefined"
                    class="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-black text-slate-500"
                  >
                    Stock: {{ produto.stock }}
                  </span>
                </div>
              </div>
            </button>
          </div>
        </section>

        <!-- Conta -->
        <aside :class="['flex min-h-0 flex-col bg-slate-50', activePanel === 'pedido' ? 'block' : 'hidden lg:flex']">
          <div class="border-b border-slate-200 bg-white p-4">
            <div class="flex items-center justify-between gap-3">
              <div>
                <h3 class="text-xl font-black text-slate-950">Pedido</h3>
                <p class="text-sm font-semibold text-slate-500">
                  Conta #{{ conta?.id || '—' }}
                </p>
              </div>

              <div
                v-if="loadingConta"
                class="h-7 w-7 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"
              ></div>
            </div>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto p-4">
            <div
              v-if="!conta"
              class="flex h-full min-h-[220px] flex-col items-center justify-center text-center"
            >
              <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
              <p class="mt-4 text-sm font-bold text-slate-500">
                A preparar conta...
              </p>
            </div>

            <div
              v-else-if="items.length === 0"
              class="flex h-full min-h-[220px] flex-col items-center justify-center rounded-[2rem] border border-dashed border-slate-300 bg-white p-8 text-center"
            >
              <div class="flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-3xl">
                🛒
              </div>

              <h4 class="mt-4 text-lg font-black text-slate-950">
                Pedido vazio
              </h4>

              <p class="mt-2 text-sm leading-6 text-slate-500">
                Seleciona produtos à esquerda para adicionar ao pedido.
              </p>
            </div>

            <div v-else class="space-y-3">
              <article
                v-for="item in items"
                :key="item.id"
                class="rounded-[1.25rem] border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      <h4 class="truncate text-sm font-black text-slate-950">
                        {{ item.nome }}
                      </h4>

                      <span
                        :class="[
                          'rounded-full px-2 py-0.5 text-[10px] font-black uppercase',
                          item.origem === 'pos'
                            ? 'bg-purple-100 text-purple-700'
                            : 'bg-blue-100 text-blue-700'
                        ]"
                      >
                        {{ item.origem === 'pos' ? 'POS' : 'Loja' }}
                      </span>
                    </div>

                    <p class="mt-1 text-xs font-semibold text-slate-500">
                      {{ money(item.preco_unitario) }} × {{ item.quantidade }}
                    </p>
                  </div>

                  <button
                    type="button"
                    @click="removerItem(item)"
                    class="rounded-xl p-2 text-red-500 transition hover:bg-red-50 hover:text-red-700"
                    title="Remover item"
                  >
                    ×
                  </button>
                </div>

                <div class="mt-3 flex items-center justify-between gap-3">
                  <span class="text-lg font-black text-slate-950">
                    {{ money(item.preco_total) }}
                  </span>

                  <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-500">
                    {{ item.status || 'pendente' }}
                  </span>
                </div>

                <p
                  v-if="item.observacoes"
                  class="mt-3 rounded-2xl bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700"
                >
                  Obs: {{ item.observacoes }}
                </p>
              </article>
            </div>
          </div>

          <!-- Totais -->
          <footer v-if="conta" class="border-t border-slate-200 bg-white p-4">
            <div class="space-y-2">
              <div class="flex justify-between text-sm font-bold text-slate-500">
                <span>Subtotal</span>
                <span>{{ money(conta.subtotal) }}</span>
              </div>

              <div
                v-if="Number(conta.taxa_servico_valor) > 0"
                class="flex justify-between text-sm font-bold text-slate-500"
              >
                <span>Taxa de serviço ({{ conta.taxa_servico_percentagem }}%)</span>
                <span>{{ money(conta.taxa_servico_valor) }}</span>
              </div>

              <div class="flex justify-between border-t border-slate-200 pt-3 text-xl font-black text-slate-950">
                <span>Total</span>
                <span>{{ money(conta.total) }}</span>
              </div>
            </div>

            <div class="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              <button
                type="button"
                @click="$emit('close')"
                class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
              >
                Fechar
              </button>

              <button
                type="button"
                @click="finalizarConta"
                :disabled="items.length === 0"
                class="h-12 rounded-2xl bg-emerald-600 text-sm font-black text-white shadow-lg shadow-emerald-600/20 transition hover:-translate-y-0.5 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                Finalizar e pagar
              </button>
            </div>
          </footer>
        </aside>
      </div>
    </div>

    <PagamentoModal
      v-if="showPagamentoModal"
      :conta="conta"
      :pos-id="posId"
      @close="showPagamentoModal = false"
      @pago="handlePagamentoConcluido"
    />
  </div>
</template>

<script>
import api from '@/services/api'
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
      type: [Number, String],
      required: true
    }
  },

  data() {
    return {
      conta: null,
      produtos: [],
      searchQuery: '',
      origemFiltro: '',
      categoriaFiltro: '',
      loadingConta: false,
      loadingProdutos: false,
      addingProdutoUid: null,
      showPagamentoModal: false,
      activePanel: 'produtos',
      error: ''
    }
  },

  computed: {
    categoriasDisponiveis() {
      const categoriasSet = new Set()
      this.produtos.forEach((produto) => {
        if (produto.categoria && produto.categoria !== 'Sem categoria') {
          categoriasSet.add(produto.categoria)
        }
      })
      return Array.from(categoriasSet).sort((a, b) => a.localeCompare(b, 'pt', { sensitivity: 'base' }))
    },
    items() {
      return Array.isArray(this.conta?.items) ? this.conta.items : []
    },

    produtosFiltrados() {
      const query = this.searchQuery.toLowerCase().trim()

      return this.produtos
        .filter((produto) => {
          const matchesSearch =
            !query ||
            String(produto.nome || '').toLowerCase().includes(query) ||
            String(produto.descricao || '').toLowerCase().includes(query) ||
            String(produto.categoria || '').toLowerCase().includes(query)

          const matchesOrigem =
            !this.origemFiltro || produto.origem === this.origemFiltro

          const matchesCategoria =
            !this.categoriaFiltro || produto.categoria === this.categoriaFiltro

          return matchesSearch && matchesOrigem && matchesCategoria
        })
        .sort((a, b) => {
          const catA = a.categoria || 'Sem categoria'
          const catB = b.categoria || 'Sem categoria'

          if (catA === catB) {
            return String(a.nome || '').localeCompare(String(b.nome || ''), 'pt', { sensitivity: 'base' })
          }

          if (catA === 'Sem categoria') return 1
          if (catB === 'Sem categoria') return -1

          return catA.localeCompare(catB, 'pt', { sensitivity: 'base' })
        })
    }
  },

  async created() {
    await Promise.all([
      this.iniciarConta(),
      this.carregarProdutos()
    ])
  },

  methods: {
    async iniciarConta() {
      this.loadingConta = true
      this.error = ''

      try {
        // Com o backend novo, POST devolve a conta existente se já estiver aberta.
        const { data } = await api.post(`/api/pos/${this.posId}/mesas/${this.mesa.id}/conta/`, {})
        this.conta = this.normalizeConta(data)
      } catch (error) {
        console.error('Erro ao iniciar conta:', error)
        this.error = error.response?.data?.detail || 'Erro ao iniciar conta.'
      } finally {
        this.loadingConta = false
      }
    },

    async carregarConta(contaId) {
      const { data } = await api.get(`/api/pos/${this.posId}/contas/${contaId}/`)
      this.conta = this.normalizeConta(data)
    },

    async recarregarConta() {
      if (!this.conta?.id) return
      await this.carregarConta(this.conta.id)
    },

    async carregarProdutos() {
      if (this.loadingProdutos) return

      this.loadingProdutos = true

      try {
        const { data } = await api.get(`/api/pos/${this.posId}/produtos/`)

        this.produtos = Array.isArray(data.results)
          ? data.results.map(this.normalizarProduto)
          : Array.isArray(data)
            ? data.map(this.normalizarProduto)
            : []
      } catch (error) {
        console.error('Erro ao carregar produtos:', error)
        this.error = error.response?.data?.detail || 'Erro ao carregar produtos.'
      } finally {
        this.loadingProdutos = false
      }
    },

    async adicionarProduto(produto) {
      if (!this.conta?.id) {
        this.error = 'A conta ainda não está pronta.'
        return
      }

      if (produto.disponivel === false) {
        this.error = 'Este produto não está disponível.'
        return
      }

      this.addingProdutoUid = this.produtoUid(produto)
      this.error = ''

      try {
        await api.post(`/api/pos/${this.posId}/contas/${this.conta.id}/items/`, {
          produto_id: produto.id,
          origem: produto.origem,
          quantidade: 1,
          observacoes: ''
        })

        await this.recarregarConta()
        await this.carregarProdutos()
      } catch (error) {
        console.error('Erro ao adicionar produto:', error)
        this.error = error.response?.data?.detail || 'Erro ao adicionar produto.'
      } finally {
        this.addingProdutoUid = null
      }
    },

    async removerItem(item) {
      if (!confirm(`Remover ${item.nome} do pedido?`)) return

      this.error = ''

      try {
        await api.delete(`/api/pos/${this.posId}/contas/${this.conta.id}/items/${item.id}/`)

        await this.recarregarConta()
        await this.carregarProdutos()
      } catch (error) {
        console.error('Erro ao remover item:', error)
        this.error = error.response?.data?.detail || 'Erro ao remover item.'
      }
    },

    finalizarConta() {
      if (!this.conta || this.items.length === 0) return
      this.showPagamentoModal = true
    },

    handlePagamentoConcluido() {
      this.showPagamentoModal = false
      this.$emit('atualizar')
      this.$emit('close')
    },

    normalizeConta(conta) {
      return {
        ...conta,
        items: Array.isArray(conta.items) ? conta.items : []
      }
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
        disponivel: produto.disponivel ?? true,
        stock: produto.stock ?? 0,
        origem: produto.origem || 'pos'
      }
    },

    produtoUid(produto) {
      return produto.uid || `${produto.origem}-${produto.id}`
    },

    money(value) {
      const number = Number(value || 0)

      return new Intl.NumberFormat('pt-PT', {
        style: 'currency',
        currency: 'EUR'
      }).format(number)
    }
  }
}
</script>