<template>
  <div class="w-full">

    <!-- ═══ ABAS PRINCIPAIS: Tipos ═══ -->
    <div class="flex gap-2 overflow-x-auto pb-2 mb-3 scrollbar-hide">
      <button
        @click="selectTipo(null)"
        :class="[
          'px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap flex-shrink-0',
          activeTipo === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
        ]">
        Todos
      </button>
      <button
        v-for="tipo in tipos" :key="tipo.id"
        @click="selectTipo(tipo)"
        :class="[
          'px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap flex-shrink-0 capitalize',
          activeTipo?.id === tipo.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
        ]">
        {{ tipo.nome }}
      </button>
    </div>

    <!-- ═══ SUB-ABAS: Categorias do tipo seleccionado ═══ -->
    <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1"
                leave-active-class="transition duration-150" leave-to-class="opacity-0">
      <div v-if="activeTipo && categoriasDoTipo.length > 0"
           class="flex gap-2 overflow-x-auto pb-2 mb-3 scrollbar-hide pl-2 border-l-2 border-red-600/40">
        <button
          @click="selectCategoria(null)"
          :class="[
            'px-3 py-1.5 rounded-full text-xs font-semibold transition-all whitespace-nowrap flex-shrink-0',
            activeCategoria === null ? 'bg-red-600/80 text-white' : 'bg-zinc-800/80 text-zinc-400 hover:text-zinc-200'
          ]">
          Todas
        </button>
        <button
          v-for="cat in categoriasDoTipo" :key="cat"
          @click="selectCategoria(cat)"
          :class="[
            'px-3 py-1.5 rounded-full text-xs font-semibold transition-all whitespace-nowrap flex-shrink-0 capitalize',
            activeCategoria === cat ? 'bg-red-600/80 text-white' : 'bg-zinc-800/80 text-zinc-400 hover:text-zinc-200'
          ]">
          {{ cat }}
        </button>
      </div>
    </transition>

    <!-- ═══ BARRA DE FILTROS ═══ -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 mb-6">
      <div class="flex flex-wrap gap-3">

        <div class="relative flex-1 min-w-48">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input v-model="filters.q" @input="debouncedFetch"
            placeholder="Pesquisar produto..."
            class="w-full pl-9 pr-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
        </div>

        <div class="relative w-28">
          <span class="text-zinc-500 text-xs absolute left-3 top-1/2 -translate-y-1/2">€</span>
          <input v-model="filters.preco_min" @input="debouncedFetch" type="number" min="0" placeholder="Mín"
            class="w-full pl-7 pr-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
        </div>

        <div class="relative w-28">
          <span class="text-zinc-500 text-xs absolute left-3 top-1/2 -translate-y-1/2">€</span>
          <input v-model="filters.preco_max" @input="debouncedFetch" type="number" min="0" placeholder="Máx"
            class="w-full pl-7 pr-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
        </div>

        <select v-model="filters.ordem" @change="resetAndFetch"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 focus:outline-none focus:border-red-500 transition cursor-pointer">
          <option value="">Ordenar por</option>
          <option value="preco_asc">Preço ↑</option>
          <option value="preco_desc">Preço ↓</option>
          <option value="novidade">Mais recente</option>
        </select>

        <button @click="toggleStock"
          :class="[
            'px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-2',
            filters.stock_disponivel
              ? 'bg-green-600/20 border border-green-500/50 text-green-400'
              : 'bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-zinc-200'
          ]">
          <div :class="['w-2 h-2 rounded-full', filters.stock_disponivel ? 'bg-green-400' : 'bg-zinc-600']"></div>
          Em stock
        </button>

        <button v-if="hasActiveFilters" @click="clearFilters"
          class="px-4 py-2 rounded-xl text-sm font-semibold text-red-400 hover:text-red-300
                 bg-red-500/10 hover:bg-red-500/20 transition-all flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Limpar
        </button>
      </div>

      <!-- Atributos dinâmicos do tipo seleccionado -->
      <div v-if="activeTipo && atributosFiltravelis.length" class="flex flex-wrap gap-3 mt-3 pt-3 border-t border-zinc-800">
        <div v-for="attr in atributosFiltravelis" :key="attr.nome" class="relative">
          <select v-if="attr.tipo === 'choices'"
            v-model="filters.atributos[attr.nome]"
            @change="debouncedFetch"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   focus:outline-none focus:border-red-500 transition w-36">
            <option value="">{{ capitalize(attr.nome) }}</option>
            <option v-for="op in attr.opcoes" :key="op" :value="op">{{ op }}</option>
          </select>
          <input v-else
            v-model="filters.atributos[attr.nome]"
            @input="debouncedFetch"
            :placeholder="capitalize(attr.nome)"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition w-36"
          />
        </div>
      </div>
    </div>

    <!-- Indicador de filtros activos -->
    <div v-if="activeTipo || activeCategoria" class="flex items-center gap-2 mb-4 text-xs text-zinc-500">
      <span>A mostrar:</span>
      <span v-if="activeTipo" class="px-2 py-0.5 bg-red-600/20 text-red-400 rounded-full capitalize">
        {{ activeTipo.nome }}
      </span>
      <span v-if="activeCategoria" class="px-2 py-0.5 bg-zinc-700 text-zinc-300 rounded-full capitalize">
        {{ activeCategoria }}
      </span>
      <button @click="selectTipo(null)" class="text-zinc-600 hover:text-zinc-400 transition ml-1">
        × limpar
      </button>
    </div>

    <!-- Resultados -->
    <div class="flex items-center justify-between mb-4">
      <p class="text-sm text-zinc-500">
        <span v-if="!loading">{{ total }} produto{{ total !== 1 ? 's' : '' }}</span>
        <span v-else>A carregar...</span>
      </p>
    </div>

    <!-- Skeleton -->
    <div v-if="loading && produtos.length === 0"
         class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <div v-for="n in 10" :key="n" class="bg-zinc-900 rounded-2xl animate-pulse" style="height:230px"></div>
    </div>

    <!-- Grid -->
    <div v-else-if="produtos.length"
         class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <div
        v-for="produto in produtos" :key="produto.id"
        @click="$emit('product-click', produto)"
        class="group bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800
               hover:border-red-500/40 transition-all cursor-pointer hover:-translate-y-1 hover:shadow-xl"
      >
        <div class="relative h-40 overflow-hidden">
          <img :src="produto.ficheiro_url || defaultImg" :alt="produto.nome"
               class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          <span v-if="produto.destaque"
                class="absolute top-2 right-2 px-1.5 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded">⭐</span>
          <!-- Badge categoria quando não há filtro de categoria -->
          <span v-if="produto.categoria && !activeCategoria"
                class="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 text-zinc-300 text-[10px] rounded-full capitalize backdrop-blur-sm">
            {{ produto.categoria }}
          </span>
          <div v-if="produto.stock && produto.stock.quantidade === 0"
               class="absolute inset-0 bg-black/60 flex items-center justify-center text-xs font-bold text-zinc-300">
            Sem stock
          </div>
        </div>
        <div class="p-3">
          <p class="text-sm font-semibold text-zinc-100 truncate group-hover:text-red-400 transition-colors">
            {{ produto.nome }}
          </p>
          <div v-if="produto.atributos && Object.keys(produto.atributos).length" class="flex flex-wrap gap-1 mt-1">
            <span v-for="(val, key) in slicedAtributos(produto.atributos)" :key="key"
                  class="px-1.5 py-0.5 bg-zinc-800 text-zinc-500 text-[10px] rounded">{{ val }}</span>
          </div>
          <div class="flex items-center justify-between mt-2">
            <span class="text-sm font-bold text-red-400">{{ formatPrice(produto.preco) }}</span>
            <span v-if="produto.stock" class="text-[10px] text-zinc-600">{{ produto.stock.quantidade }} un.</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading" class="text-center py-16 text-zinc-500">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
      <p>Nenhum produto encontrado.</p>
      <button v-if="hasActiveFilters || activeTipo || activeCategoria" @click="resetAll"
              class="text-red-400 hover:text-red-300 text-sm mt-2">
        Limpar todos os filtros →
      </button>
    </div>

    <div ref="sentinel" class="h-4 mt-4"></div>

    <div v-if="loadingMore" class="flex justify-center py-6">
      <svg class="animate-spin h-6 w-6 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'ProductCatalog',

  props: {
    lojaId:   { type: [Number, String], default: null },
    endpoint: { type: String, default: '/app/produto/' },
    limit:    { type: Number, default: 20 },
  },

  emits: ['product-click'],

  data () {
    return {
      defaultImg: (process.env.VUE_APP_URL_BASE || 'http://localhost:8000') + '/media/produtos/default.jpg',
      // Tipos
      tipos: [],
      activeTipo: null,
      // Categorias
      todasCategorias: [],   // todas as categorias da loja
      categoriasDoTipo: [],  // categorias filtradas do tipo activo
      activeCategoria: null,
      // Produtos
      produtos: [],
      total: 0,
      offset: 0,
      loading: false,
      loadingMore: false,
      reachedEnd: false,
      // Filtros
      filters: {
        q: '',
        preco_min: '',
        preco_max: '',
        ordem: '',
        stock_disponivel: false,
        atributos: {},
      },
      debounceTimer: null,
      observer: null,
    }
  },

  computed: {
    atributosFiltravelis () {
      if (!this.activeTipo?.atributos_schema?.length) return []
      return this.activeTipo.atributos_schema
        .map(a => typeof a === 'string' ? { nome: a, tipo: 'texto', opcoes: [] } : a)
        .filter(a => a.nome)
    },

    hasActiveFilters () {
      return this.filters.q ||
        this.filters.preco_min ||
        this.filters.preco_max ||
        this.filters.ordem ||
        this.filters.stock_disponivel ||
        Object.values(this.filters.atributos).some(v => v)
    },
  },

  async mounted () {
    await Promise.all([this.fetchTipos(), this.fetchTodasCategorias()])
    await this.resetAndFetch()
    this.setupObserver()
  },

  beforeUnmount () {
    this.observer?.disconnect()
    clearTimeout(this.debounceTimer)
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },

    capitalize (str) {
      if (!str) return ''
      const s = typeof str === 'object' ? (str.nome || '') : String(str)
      return s.charAt(0).toUpperCase() + s.slice(1)
    },

    slicedAtributos (atributos) {
      return Object.fromEntries(Object.entries(atributos).slice(0, 2))
    },

    // ── Tipos ──────────────────────────────────────────────
    async fetchTipos () {
      try {
        const params = { limit: 100 }
        if (this.lojaId) params.loja_id = this.lojaId
        const { data } = await api.get(this.endpoint, { params })
        const produtos = data.results || data
        const map = {}
        produtos.forEach(p => { if (p.tipo && !map[p.tipo.id]) map[p.tipo.id] = p.tipo })
        this.tipos = Object.values(map)
      } catch (e) { console.error(e) }
    },

    // ── Categorias ─────────────────────────────────────────
    async fetchTodasCategorias () {
      if (!this.lojaId) return
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/produtos/categorias/`)
        this.todasCategorias = data
      } catch (e) { console.error(e) }
    },

    async fetchCategoriasDoTipo (tipo) {
      // busca categorias existentes nos produtos deste tipo
      try {
        const params = { limit: 200 }
        if (this.lojaId) params.loja_id = this.lojaId
        if (tipo) params.tipo = tipo.nome
        const { data } = await api.get(this.endpoint, { params })
        const produtos = data.results || data
        const cats = [...new Set(
          produtos.map(p => p.categoria).filter(Boolean)
        )].sort()
        this.categoriasDoTipo = cats
      } catch (e) { console.error(e) }
    },

    // ── Selecção ───────────────────────────────────────────
    async selectTipo (tipo) {
      this.activeTipo = tipo
      this.activeCategoria = null
      this.categoriasDoTipo = []
      if (tipo) {
        await this.fetchCategoriasDoTipo(tipo)
      }
      // reset atributos
      if (tipo?.atributos_schema) {
        const atributos = {}
        tipo.atributos_schema.forEach(a => {
          const nome = typeof a === 'string' ? a : a.nome
          if (nome) atributos[nome] = ''
        })
        this.filters.atributos = atributos
      } else {
        this.filters.atributos = {}
      }
      this.resetAndFetch()
    },

    selectCategoria (cat) {
      this.activeCategoria = cat
      this.resetAndFetch()
    },

    resetAll () {
      this.activeTipo = null
      this.activeCategoria = null
      this.categoriasDoTipo = []
      this.filters = { q: '', preco_min: '', preco_max: '', ordem: '', stock_disponivel: false, atributos: {} }
      this.resetAndFetch()
    },

    // ── Filtros ────────────────────────────────────────────
    toggleStock () {
      this.filters.stock_disponivel = !this.filters.stock_disponivel
      this.resetAndFetch()
    },

    clearFilters () {
      const atributos = {}
      if (this.activeTipo?.atributos_schema) {
        this.activeTipo.atributos_schema.forEach(a => {
          const nome = typeof a === 'string' ? a : a.nome
          if (nome) atributos[nome] = ''
        })
      }
      this.filters = { q: '', preco_min: '', preco_max: '', ordem: '', stock_disponivel: false, atributos }
      this.resetAndFetch()
    },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.resetAndFetch(), 350)
    },

    // ── Fetch ──────────────────────────────────────────────
    buildParams (offset = 0) {
      const p = { limit: this.limit, offset }
      if (this.lojaId)                   p.loja_id = this.lojaId
      if (this.activeTipo)               p.tipo = this.activeTipo.nome
      if (this.activeCategoria)          p.categoria = this.activeCategoria
      if (this.filters.q)                p.q = this.filters.q
      if (this.filters.preco_min)        p.preco_min = this.filters.preco_min
      if (this.filters.preco_max)        p.preco_max = this.filters.preco_max
      if (this.filters.stock_disponivel) p.stock_disponivel = true
      if (this.filters.ordem === 'preco_asc')  p.ordering = 'preco'
      if (this.filters.ordem === 'preco_desc') p.ordering = '-preco'
      if (this.filters.ordem === 'novidade')   p.ordering = '-data_criacao'
      Object.entries(this.filters.atributos).forEach(([k, v]) => {
        if (v) p[`atributo_${k}`] = v
      })
      return p
    },

    async resetAndFetch () {
      this.reachedEnd = false
      this.offset = 0
      this.produtos = []
      this.loading = true
      try {
        const { data } = await api.get(this.endpoint, { params: this.buildParams(0) })
        this.produtos = data.results || data
        this.total = data.count ?? this.produtos.length
        this.offset = data.next_offset ?? null
        this.reachedEnd = !this.offset
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async fetchMore () {
      if (this.reachedEnd || this.loadingMore || this.loading) return
      this.loadingMore = true
      try {
        const { data } = await api.get(this.endpoint, { params: this.buildParams(this.offset) })
        this.produtos.push(...(data.results || data))
        this.total = data.count ?? this.produtos.length
        this.offset = data.next_offset ?? null
        this.reachedEnd = !this.offset
      } catch (e) { console.error(e) }
      finally { this.loadingMore = false }
    },

    setupObserver () {
      this.observer = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) this.fetchMore() },
        { rootMargin: '300px' }
      )
      if (this.$refs.sentinel) this.observer.observe(this.$refs.sentinel)
    },
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>