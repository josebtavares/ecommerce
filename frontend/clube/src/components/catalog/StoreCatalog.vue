<template>
  <div class="w-full">

    <!-- ═══ TABS POR CATEGORIA ═══ -->
    <div class="flex gap-2 overflow-x-auto pb-2 mb-5 scrollbar-hide">
      <button
        @click="selectCategoria(null)"
        :class="[
          'px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap flex-shrink-0',
          activeCategoria === null
            ? 'bg-red-600 text-white'
            : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
        ]">
        Todas
      </button>
      <button
        v-for="cat in categorias" :key="cat.value"
        @click="selectCategoria(cat.value)"
        :class="[
          'px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap flex-shrink-0 flex items-center gap-1.5',
          activeCategoria === cat.value
            ? 'bg-red-600 text-white'
            : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
        ]">
        <span>{{ cat.icon }}</span>
        {{ cat.label }}
      </button>
    </div>

    <!-- ═══ BARRA DE FILTROS ═══ -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 mb-6">
      <div class="flex flex-wrap gap-3">

        <!-- Pesquisa por nome -->
        <div class="relative flex-1 min-w-48">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input v-model="filters.q" @input="debouncedFetch"
            placeholder="Pesquisar loja..."
            class="w-full pl-9 pr-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Entrega -->
        <button @click="toggleFilter('entrega_ativa')"
          :class="[
            'px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-2',
            filters.entrega_ativa
              ? 'bg-green-600/20 border border-green-500/50 text-green-400'
              : 'bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-zinc-200'
          ]">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          Com entrega
        </button>

        <!-- Takeaway -->
        <button @click="toggleFilter('levantamento_ativo')"
          :class="[
            'px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-2',
            filters.levantamento_ativo
              ? 'bg-blue-600/20 border border-blue-500/50 text-blue-400'
              : 'bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-zinc-200'
          ]">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5" />
          </svg>
          Takeaway
        </button>

        <!-- Ordenar -->
        <select v-model="filters.ordem" @change="resetAndFetch"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 focus:outline-none focus:border-red-500 transition cursor-pointer">
          <option value="">Ordenar por</option>
          <option value="nome_asc">Nome A→Z</option>
          <option value="nome_desc">Nome Z→A</option>
          <option value="novidade">Mais recente</option>
        </select>

        <!-- Limpar filtros -->
        <button v-if="hasActiveFilters" @click="clearFilters"
          class="px-4 py-2 rounded-xl text-sm font-semibold text-red-400 hover:text-red-300
                 bg-red-500/10 hover:bg-red-500/20 transition-all flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Limpar
        </button>
      </div>
    </div>

    <!-- ═══ RESULTADOS ═══ -->
    <div class="flex items-center justify-between mb-4">
      <p class="text-sm text-zinc-500">
        <span v-if="!loading">{{ total }} loja{{ total !== 1 ? 's' : '' }}</span>
        <span v-else>A carregar...</span>
      </p>
    </div>

    <!-- Skeleton -->
    <div v-if="loading && lojas.length === 0"
         class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div v-for="n in 8" :key="n" class="bg-zinc-900 rounded-2xl animate-pulse" style="height:240px"></div>
    </div>

    <!-- Grid -->
    <div v-else-if="lojas.length"
         class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div
        v-for="loja in lojas" :key="loja.id"
        @click="$emit('store-click', loja)"
        class="group relative rounded-2xl overflow-hidden cursor-pointer bg-zinc-900 border border-zinc-800
               hover:border-red-500/40 transition-all hover:-translate-y-1 hover:shadow-xl"
        style="height:240px"
      >
        <!-- Banner / imagem de fundo -->
        <img
          :src="loja.banner_url || loja.logo_url || defaultImg"
          :alt="loja.nome"
          class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/50 to-transparent"></div>

        <!-- Logo -->
        <div class="absolute top-3 left-3">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-10 h-10 rounded-xl object-cover border-2 border-zinc-700 shadow-lg" />
          <div v-else class="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center border-2 border-zinc-700">
            <span class="text-sm font-bold text-zinc-400">{{ loja.nome.charAt(0) }}</span>
          </div>
        </div>

        <!-- Rating -->
        <div v-if="loja.rating_medio"
             class="absolute top-3 right-3 px-2 py-0.5 bg-zinc-900/80 backdrop-blur rounded-lg flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <span class="text-xs font-semibold text-white">{{ loja.rating_medio }}</span>
        </div>

        <!-- Info -->
        <div class="absolute bottom-0 left-0 right-0 p-4">
          <span class="inline-block px-2 py-0.5 bg-red-600/90 text-white text-[10px] font-bold rounded mb-1.5">
            {{ categoriaLabel(loja.categoria) }}
          </span>
          <h3 class="text-base font-bold text-white truncate group-hover:text-red-400 transition-colors">
            {{ loja.nome }}
          </h3>
          <p v-if="loja.localizacao" class="text-xs text-zinc-400 truncate mt-0.5 flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            </svg>
            {{ loja.localizacao }}
          </p>
          <div class="flex gap-1.5 mt-2">
            <span v-if="loja.entrega_ativa"
                  class="px-1.5 py-0.5 bg-green-600/20 text-green-400 text-[10px] rounded">
              Entrega
            </span>
            <span v-if="loja.levantamento_ativo"
                  class="px-1.5 py-0.5 bg-blue-600/20 text-blue-400 text-[10px] rounded">
              Takeaway
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading" class="text-center py-16 text-zinc-500">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <p>Nenhuma loja encontrada.</p>
      <button v-if="hasActiveFilters" @click="clearFilters" class="text-red-400 hover:text-red-300 text-sm mt-2">
        Limpar filtros →
      </button>
    </div>

    <!-- Sentinel scroll infinito -->
    <div ref="sentinel" class="h-4 mt-4"></div>

    <!-- Loading mais -->
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
  name: 'StoreCatalog',

  props: {
    endpoint: { type: String, default: '/app/loja/' },
    limit:    { type: Number, default: 16 },
  },

  emits: ['store-click'],

  data () {
    return {
      defaultImg: (process.env.VUE_APP_URL_BASE || 'http://localhost:8000') + '/media/lojas/default_banner.jpg',

      categorias: [
        { value: 'restaurante',  label: 'Restaurante',  icon: '🍔' },
        { value: 'moda',         label: 'Moda',         icon: '👗' },
        { value: 'tecnologia',   label: 'Tecnologia',   icon: '📱' },
        { value: 'supermercado', label: 'Supermercado', icon: '🛒' },
        { value: 'farmacia',     label: 'Farmácia',     icon: '💊' },
        { value: 'desporto',     label: 'Desporto',     icon: '⚽' },
        { value: 'casa',         label: 'Casa',         icon: '🏠' },
        { value: 'beleza',       label: 'Beleza',       icon: '💄' },
        { value: 'livraria',     label: 'Livraria',     icon: '📚' },
        { value: 'outros',       label: 'Outros',       icon: '🏪' },
      ],

      activeCategoria: null,

      lojas: [],
      total: 0,
      offset: 0,
      loading: false,
      loadingMore: false,
      reachedEnd: false,

      filters: {
        q: '',
        entrega_ativa: false,
        levantamento_ativo: false,
        ordem: '',
      },

      debounceTimer: null,
      observer: null,
    }
  },

  computed: {
    hasActiveFilters () {
      return this.filters.q ||
        this.filters.entrega_ativa ||
        this.filters.levantamento_ativo ||
        this.filters.ordem ||
        this.activeCategoria
    },
  },

  async mounted () {
    await this.resetAndFetch()
    this.setupObserver()
  },

  beforeUnmount () {
    this.observer?.disconnect()
    clearTimeout(this.debounceTimer)
  },

  methods: {
    categoriaLabel (val) {
      return this.categorias.find(c => c.value === val)?.label || val
    },

    selectCategoria (val) {
      this.activeCategoria = val
      this.resetAndFetch()
    },

    toggleFilter (key) {
      this.filters[key] = !this.filters[key]
      this.resetAndFetch()
    },

    clearFilters () {
      this.filters = { q: '', entrega_ativa: false, levantamento_ativo: false, ordem: '' }
      this.activeCategoria = null
      this.resetAndFetch()
    },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.resetAndFetch(), 350)
    },

    buildParams (offset = 0) {
        const p = { limit: this.limit, offset }
        if (this.activeCategoria)            p.categoria = this.activeCategoria
        if (this.filters.q)                  p.q = this.filters.q          // era 'search'
        if (this.filters.entrega_ativa)      p.entrega = 'true'            // era 'entrega_ativa=true'
        if (this.filters.levantamento_ativo) p.levantamento = 'true'       // era 'levantamento_ativo=true'
        if (this.filters.ordem === 'nome_asc')  p.ordering = 'nome'
        if (this.filters.ordem === 'nome_desc') p.ordering = '-nome'
        if (this.filters.ordem === 'novidade')  p.ordering = '-data_criacao'
        return p
    },

    async resetAndFetch () {
      this.reachedEnd = false
      this.offset = 0
      this.lojas = []
      this.loading = true
      try {
        const { data } = await api.get(this.endpoint, { params: this.buildParams(0) })
        this.lojas = data.results || data
        this.total = data.count ?? this.lojas.length
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
        const results = data.results || data
        this.lojas.push(...results)
        this.total = data.count ?? this.lojas.length
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