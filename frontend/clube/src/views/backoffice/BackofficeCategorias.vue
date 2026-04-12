<template>
  <div class="space-y-5 max-w-3xl">

    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Categorias da loja</h2>
        <p class="text-xs text-zinc-500 mt-0.5">
          Agrupa os teus produtos em categorias. Um produto pode pertencer a várias.
        </p>
      </div>
      <button @click="abrirCriar"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nova categoria
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista -->
    <div v-else-if="categorias.length > 0" class="space-y-2">
      <div v-for="cat in categorias" :key="cat.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4 group">
        <span class="text-2xl flex-shrink-0">{{ cat.icone }}</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="text-sm font-bold text-zinc-200 capitalize">{{ cat.nome }}</p>
            <span v-if="!cat.ativo" class="px-1.5 py-0.5 bg-zinc-700 text-zinc-500 text-[10px] rounded">Oculta</span>
          </div>
          <p class="text-xs text-zinc-500 mt-0.5">
            {{ cat.total_produtos }} produto{{ cat.total_produtos !== 1 ? 's' : '' }}
          </p>
        </div>
        <div class="flex items-center gap-2 sm:opacity-100 group-hover:opacity-100 transition">
          <button @click="abrirGerirProdutos(cat)"
            class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
            Produtos
          </button>
          <button @click="toggleAtivo(cat)"
            :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                     cat.ativo
                       ? 'bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500'
                       : 'bg-green-500/10 hover:bg-green-500/20 text-green-500']">
            {{ cat.ativo ? 'Ocultar' : 'Mostrar' }}
          </button>
          <button @click="abrirEditar(cat)"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button @click="eliminar(cat)"
            class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading"
         class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800 border-dashed">
      Ainda não criaste nenhuma categoria.
      <button @click="abrirCriar" class="text-red-400 hover:text-red-300 ml-1">Criar agora →</button>
    </div>

    <!-- ═══ MODAL CRIAR/EDITAR ═══ -->
    <div v-if="showModal"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="fecharModal">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm shadow-2xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <h3 class="text-base font-bold text-zinc-100">{{ editando ? 'Editar categoria' : 'Nova categoria' }}</h3>
          <button @click="fecharModal"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Nome *</label>
            <input v-model="form.nome" type="text" placeholder="ex: homem, verão, promoção..."
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Ícone (emoji)</label>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center text-xl flex-shrink-0">
                {{ form.icone || '📂' }}
              </div>
              <input v-model="form.icone" type="text" maxlength="4" placeholder="📂"
                class="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition" />
            </div>
          </div>
          <div v-if="erroModal" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">
            {{ erroModal }}
          </div>
          <div class="flex gap-3 pt-2 border-t border-zinc-800">
            <button @click="fecharModal"
              class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
              Cancelar
            </button>
            <button @click="guardar" :disabled="loadingSave || !form.nome.trim()"
              :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition',
                       !form.nome.trim() || loadingSave
                         ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                         : 'bg-red-600 hover:bg-red-500 text-white']">
              {{ editando ? 'Guardar' : 'Criar' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ MODAL GERIR PRODUTOS (mini-catálogo) ═══ -->
    <div v-if="categoriaGerindo"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="fecharGerirProdutos">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-2xl h-[85vh] flex flex-col shadow-2xl">

        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800 flex-shrink-0">
          <div>
            <h3 class="text-base font-bold text-zinc-100 capitalize">
              {{ categoriaGerindo.icone }} {{ categoriaGerindo.nome }}
            </h3>
            <p class="text-xs text-zinc-500 mt-0.5">
              {{ produtosSeleccionados.size }} seleccionado{{ produtosSeleccionados.size !== 1 ? 's' : '' }}
              <span v-if="alteracoesPendentes" class="text-yellow-500 ml-2">· alterações por guardar</span>
            </p>
          </div>
          <button @click="fecharGerirProdutos"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Filtros -->
        <div class="px-4 py-3 border-b border-zinc-800 flex-shrink-0 space-y-2">
          <!-- Tabs por tipo -->
          <div class="flex gap-2 overflow-x-auto scrollbar-hide">
            <button @click="tipoFiltro = null; resetProdutos()"
              :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                       tipoFiltro === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
              Todos
            </button>
            <button v-for="tipo in tiposDisponiveis" :key="tipo.id"
              @click="tipoFiltro = tipo; resetProdutos()"
              :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0 capitalize',
                       tipoFiltro?.id === tipo.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
              {{ tipo.nome }}
            </button>
          </div>
          <!-- Pesquisa + toggle -->
          <div class="flex gap-2">
            <div class="relative flex-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input v-model="pesquisaProdutos" @input="debouncedSearch" placeholder="Pesquisar produto..."
                class="w-full pl-9 pr-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100
                       placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
            </div>
            <!-- Toggle mostrar só seleccionados -->
            <button @click="apenasSeleccionados = !apenasSeleccionados"
              :class="['px-3 py-1.5 rounded-xl text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                       apenasSeleccionados
                         ? 'bg-red-600/20 border border-red-500/50 text-red-400'
                         : 'bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-zinc-200']">
              {{ apenasSeleccionados ? `✓ ${produtosSeleccionados.size} sel.` : 'Ver seleccionados' }}
            </button>
          </div>
        </div>

        <!-- Lista de produtos -->
        <div class="flex-1 overflow-y-auto p-3 space-y-1.5" @scroll.passive="onScroll">
          <div v-if="loadingProdutos && produtosModal.length === 0"
               class="space-y-2 p-2">
            <div v-for="n in 6" :key="n" class="h-14 bg-zinc-800 rounded-xl animate-pulse"></div>
          </div>

          <template v-else>
            <div v-for="p in produtosParaMostrar" :key="p.id"
                 @click="toggleProduto(p.id)"
                 :class="['flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition select-none',
                          produtosSeleccionados.has(p.id)
                            ? 'bg-red-600/15 border border-red-500/30'
                            : 'bg-zinc-800/50 border border-transparent hover:border-zinc-700']">
              <!-- Thumbnail -->
              <div class="w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 bg-zinc-700">
                <img v-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome"
                     class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-zinc-500 text-xs">📦</div>
              </div>
              <!-- Info -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-zinc-200 truncate">{{ p.nome }}</p>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-xs text-red-400 font-bold">{{ formatPrice(p.preco) }}</span>
                  <span v-if="p.tipo?.nome" class="text-[10px] text-zinc-500 capitalize">{{ p.tipo.nome }}</span>
                  <!-- Categorias actuais do produto (excluindo a que estamos a gerir) -->
                  <span v-for="cat in (p.categorias || []).filter(c => c.id !== categoriaGerindo.id)"
                        :key="cat.id"
                        class="text-[10px] px-1.5 py-0.5 bg-zinc-700 text-zinc-400 rounded capitalize">
                    {{ cat.nome }}
                  </span>
                </div>
              </div>
              <!-- Checkbox -->
              <div :class="['w-5 h-5 rounded-md border-2 flex-shrink-0 flex items-center justify-center transition',
                            produtosSeleccionados.has(p.id)
                              ? 'bg-red-600 border-red-500'
                              : 'border-zinc-600 bg-zinc-800']">
                <svg v-if="produtosSeleccionados.has(p.id)" xmlns="http://www.w3.org/2000/svg"
                     class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </template>

          <!-- Load more sentinel -->
          <div v-if="!apenasSeleccionados" ref="sentinel" class="h-4"></div>
          <div v-if="loadingMore" class="flex justify-center py-4">
            <svg class="animate-spin h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" class="opacity-75"/>
            </svg>
          </div>

          <div v-if="!loadingProdutos && produtosParaMostrar.length === 0"
               class="text-center py-8 text-zinc-500 text-sm">
            {{ apenasSeleccionados ? 'Nenhum produto seleccionado.' : 'Sem produtos encontrados.' }}
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-zinc-800 flex items-center justify-between flex-shrink-0">
          <button @click="fecharGerirProdutos"
            class="px-4 py-2 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="guardarProdutosDaCategoria" :disabled="loadingSaveProdutos"
            :class="['px-6 py-2 rounded-xl text-sm font-bold transition flex items-center gap-2',
                     loadingSaveProdutos
                       ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                       : 'bg-red-600 hover:bg-red-500 text-white']">
            <svg v-if="loadingSaveProdutos" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" class="opacity-75"/>
            </svg>
            Guardar ({{ produtosSeleccionados.size }})
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

const LIMIT = 20

export default {
  name: 'BackofficeCategorias',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: false,
      loadingSave: false,
      loadingSaveProdutos: false,
      categorias: [],
      showModal: false,
      editando: null,
      erroModal: '',
      form: { nome: '', icone: '📂' },

      // Modal gerir produtos
      categoriaGerindo: null,
      produtosModal: [],          // produtos carregados (paginação)
      produtosSeleccionados: new Set(), // IDs seleccionados
      seleccionadosOriginal: new Set(), // IDs originais (para detectar alterações)
      tiposDisponiveis: [],
      tipoFiltro: null,
      pesquisaProdutos: '',
      apenasSeleccionados: false,
      loadingProdutos: false,
      loadingMore: false,
      offsetProdutos: 0,
      reachedEnd: false,
      debounceTimer: null,
      observer: null,
    }
  },

  computed: {
    produtosParaMostrar () {
      if (this.apenasSeleccionados) {
        return this.produtosModal.filter(p => this.produtosSeleccionados.has(p.id))
      }
      return this.produtosModal
    },
    alteracoesPendentes () {
      if (this.produtosSeleccionados.size !== this.seleccionadosOriginal.size) return true
      for (const id of this.produtosSeleccionados) {
        if (!this.seleccionadosOriginal.has(id)) return true
      }
      return false
    },
  },

  async created () {
    await this.fetchCategorias()
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },

    // ── Categorias ─────────────────────────────────────────
    async fetchCategorias () {
      this.loading = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/categorias/gerir/`)
        this.categorias = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    abrirCriar () {
      this.editando = null; this.erroModal = ''
      this.form = { nome: '', icone: '📂' }; this.showModal = true
    },
    abrirEditar (cat) {
      this.editando = cat; this.erroModal = ''
      this.form = { nome: cat.nome, icone: cat.icone }; this.showModal = true
    },
    fecharModal () { this.showModal = false; this.editando = null; this.erroModal = '' },

    async guardar () {
      if (!this.form.nome.trim()) return
      this.loadingSave = true; this.erroModal = ''
      try {
        if (this.editando) {
          await api.patch(`/app/loja/${this.lojaId}/categorias/${this.editando.id}/`, this.form)
        } else {
          await api.post(`/app/loja/${this.lojaId}/categorias/criar/`, this.form)
        }
        this.fecharModal()
        await this.fetchCategorias()
      } catch (e) {
        this.erroModal = e.response?.data?.nome || e.response?.data?.detail || 'Erro ao guardar.'
      } finally { this.loadingSave = false }
    },

    async toggleAtivo (cat) {
      try {
        const { data } = await api.patch(`/app/loja/${this.lojaId}/categorias/${cat.id}/toggle/`)
        cat.ativo = data.ativo
      } catch (e) { console.error(e) }
    },

    async eliminar (cat) {
      if (!confirm(`Eliminar a categoria "${cat.nome}"?\nOs produtos não são afectados.`)) return
      try {
        await api.delete(`/app/loja/${this.lojaId}/categorias/${cat.id}/`)
        await this.fetchCategorias()
      } catch (e) { console.error(e) }
    },

    // ── Modal gerir produtos ────────────────────────────────
    async abrirGerirProdutos (cat) {
      this.categoriaGerindo = cat
      this.produtosModal = []
      this.tipoFiltro = null
      this.pesquisaProdutos = ''
      this.apenasSeleccionados = false
      this.offsetProdutos = 0
      this.reachedEnd = false
      this.produtosSeleccionados = new Set()
      this.seleccionadosOriginal = new Set()

      // carrega em paralelo: todos os tipos + produtos desta categoria (para saber quais já estão)
      this.loadingProdutos = true
      try {
          const [prodLojaRes, catProdRes] = await Promise.all([
            api.get('/app/produto/', { params: { loja_id: this.lojaId, limit: 200 } }),
            api.get('/app/produto/', { params: { loja_id: this.lojaId, categoria_id: cat.id, limit: 500 } }),
          ])
        const tiposMap = {}
        ;(prodLojaRes.data.results || prodLojaRes.data).forEach(p => {
          if (p.tipo && !tiposMap[p.tipo.id]) tiposMap[p.tipo.id] = p.tipo
        })
        this.tiposDisponiveis = Object.values(tiposMap)
        const ids = new Set((catProdRes.data.results || catProdRes.data).map(p => p.id))
        this.produtosSeleccionados = new Set(ids)
        this.seleccionadosOriginal = new Set(ids)
      } catch (e) { console.error(e) }
      finally { this.loadingProdutos = false }

      await this.fetchProdutosModal(0)
      this.$nextTick(() => this.setupModalObserver())
    },

    fecharGerirProdutos () {
      if (this.alteracoesPendentes && !confirm('Tens alterações por guardar. Sair mesmo assim?')) return
      this.categoriaGerindo = null
      this.observer?.disconnect()
      this.observer = null
    },

    buildProdutosParams (offset) {
      const p = { loja_id: this.lojaId, limit: LIMIT, offset }
      if (this.tipoFiltro) p.tipo = this.tipoFiltro.nome
      if (this.pesquisaProdutos) p.q = this.pesquisaProdutos
      return p
    },

    async fetchProdutosModal (offset) {
      if (offset === 0) { this.loadingProdutos = true; this.produtosModal = [] }
      else { this.loadingMore = true }
      try {
        const { data } = await api.get('/app/produto/', { params: this.buildProdutosParams(offset) })
        const novos = data.results || data
        if (offset === 0) {
          this.produtosModal = novos
        } else {
          // evita duplicados
          const existentes = new Set(this.produtosModal.map(p => p.id))
          this.produtosModal.push(...novos.filter(p => !existentes.has(p.id)))
        }
        this.offsetProdutos = offset + novos.length
        this.reachedEnd = novos.length < LIMIT || !data.next_offset
      } catch (e) { console.error(e) }
      finally { this.loadingProdutos = false; this.loadingMore = false }
    },

    resetProdutos () {
      this.reachedEnd = false
      this.fetchProdutosModal(0)
    },

    debouncedSearch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.resetProdutos(), 350)
    },

    toggleProduto (id) {
      const novo = new Set(this.produtosSeleccionados)
      if (novo.has(id)) { novo.delete(id) } else { novo.add(id) }
      this.produtosSeleccionados = novo
    },

    async guardarProdutosDaCategoria () {
      if (!this.categoriaGerindo) return
      this.loadingSaveProdutos = true
      try {
        await api.post(
          `/app/loja/${this.lojaId}/categorias/${this.categoriaGerindo.id}/produtos/`,
          { produto_ids: [...this.produtosSeleccionados] }
        )
        // actualiza contador na lista
        const cat = this.categorias.find(c => c.id === this.categoriaGerindo.id)
        if (cat) cat.total_produtos = this.produtosSeleccionados.size
        // actualiza original para reflectir estado guardado
        this.seleccionadosOriginal = new Set(this.produtosSeleccionados)
        this.categoriaGerindo = null
        this.observer?.disconnect()
      } catch (e) { console.error(e) }
      finally { this.loadingSaveProdutos = false }
    },

    // ── Infinite scroll do modal ────────────────────────────
    setupModalObserver () {
      this.observer?.disconnect()
      if (!this.$refs.sentinel) return
      this.observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting && !this.reachedEnd && !this.loadingMore && !this.loadingProdutos && !this.apenasSeleccionados) {
          this.fetchProdutosModal(this.offsetProdutos)
        }
      }, { rootMargin: '150px' })
      this.observer.observe(this.$refs.sentinel)
    },
  },

  beforeUnmount () {
    this.observer?.disconnect()
    clearTimeout(this.debounceTimer)
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>