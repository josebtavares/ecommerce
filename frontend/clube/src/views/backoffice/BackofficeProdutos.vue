<template>
  <div class="space-y-5">

    <!-- ═══ TABS POR TIPO ═══ -->
    <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      <button @click="selectTipo(null)"
        :class="['px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap flex-shrink-0',
                 activeTipo === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        Todos
      </button>
      <button v-for="tipo in tipos" :key="tipo.id"
        @click="selectTipo(tipo)"
        :class="['px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap flex-shrink-0',
                 activeTipo?.id === tipo.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ tipo.nome }}
      </button>
    </div>

    <!-- ═══ HEADER — pesquisa + accoes ═══ -->
    <div class="flex items-center gap-3 flex-wrap">
      <div class="relative flex-1 min-w-48">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="pesquisa" @input="debouncedFetch" placeholder="Pesquisar produto..."
          class="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
      </div>
      <select v-model="limit" @change="fetchProdutos(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option :value="12">12 / pág.</option>
        <option :value="24">24 / pág.</option>
        <option :value="48">48 / pág.</option>
      </select>
      <p class="text-xs text-zinc-500">{{ totalCount }} produto{{ totalCount !== 1 ? 's' : '' }}</p>
      <button @click="abrirCriar"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition flex items-center gap-2 ml-auto">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Novo produto
      </button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <div v-for="n in limit" :key="n" class="bg-zinc-900 rounded-2xl h-56 animate-pulse"></div>
    </div>

    <!-- Grid -->
    <div v-else-if="produtos.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <div v-for="p in produtos" :key="p.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden group">
        <div class="relative h-40 overflow-hidden">
          <img v-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome"
               class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          <div v-else class="w-full h-full bg-zinc-800 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <div class="absolute top-2 left-2 flex gap-1">
            <span v-if="p.destaque" class="px-1.5 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded">⭐</span>
            <span v-if="!p.ativo" class="px-1.5 py-0.5 bg-zinc-900/80 text-zinc-400 text-[10px] font-bold rounded">Inactivo</span>
          </div>
          <!-- tipo badge -->
          <span v-if="p.tipo?.nome"
                class="absolute top-2 right-2 px-1.5 py-0.5 bg-black/60 text-zinc-300 text-[10px] rounded">
            {{ p.tipo.nome }}
          </span>
          <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-3">
            <button @click="abrirEditar(p)"
              class="w-9 h-9 rounded-xl bg-white/20 hover:bg-white/30 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click="eliminarProduto(p)"
              class="w-9 h-9 rounded-xl bg-red-600/60 hover:bg-red-600/80 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        <div class="p-3">
          <p class="text-sm font-semibold text-zinc-100 truncate">{{ p.nome }}</p>
          <!-- atributos badge -->
          <div v-if="p.atributos && Object.keys(p.atributos).length" class="flex flex-wrap gap-1 mt-1">
            <span v-for="(val, key) in slicedAtributos(p.atributos)" :key="key"
                  class="px-1.5 py-0.5 bg-zinc-800 text-zinc-500 text-[10px] rounded capitalize">
              {{ key }}: {{ val }}
            </span>
          </div>
          <div class="flex items-center justify-between mt-2">
            <span class="text-sm font-bold text-red-400">{{ formatPrice(p.preco) }}</span>
            <span class="text-xs text-zinc-600">{{ p.inventario?.quantidade ?? '—' }} un.</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading" class="text-center py-16 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto mb-3 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
      <p>{{ activeTipo ? `Sem produtos do tipo "${activeTipo.nome}".` : 'Nenhum produto encontrado.' }}</p>
      <button @click="abrirCriar" class="text-red-400 hover:text-red-300 mt-2">Criar o primeiro →</button>
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchProdutos(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchProdutos(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchProdutos(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Modal produto -->
    <BackofficeProdutoModal
      v-if="showModal"
      :loja-id="lojaId"
      :produto="produtoSelecionado"
      :tipo-inicial="activeTipo"
      @close="showModal = false"
      @saved="onSaved"
    />
  </div>
</template>

<script>
import api from '@/services/api'
import BackofficeProdutoModal from './BackofficeProdutoModal.vue'

export default {
  name: 'BackofficeProdutos',
  components: { BackofficeProdutoModal },
  props: { lojaId: [String, Number] },

  data () {
    return {
      // Tipos
      tipos: [],
      activeTipo: null,
      // Produtos
      loading: true,
      produtos: [],
      totalCount: 0,
      page: 1,
      limit: 12,
      pesquisa: '',
      // Modal
      showModal: false,
      produtoSelecionado: null,
      debounceTimer: null,
    }
  },

  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
  },

  async created () {
    await Promise.all([this.fetchTipos(), this.fetchProdutos()])
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },

    slicedAtributos (atributos) {
      return Object.fromEntries(Object.entries(atributos).slice(0, 2))
    },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchProdutos(1), 350)
    },

    // ── Tipos ────────────────────────────────────────────────
    async fetchTipos () {
      try {
        // busca os produtos da loja e extrai os tipos únicos que existem
        // assim só aparecem tabs dos tipos com produtos nesta loja
        const { data } = await api.get(`/app/loja/${this.lojaId}/produtos/`, {
          params: { limit: 200 }
        })
        const produtos = data.results || data
        const tiposMap = {}
        produtos.forEach(p => {
          if (p.tipo && !tiposMap[p.tipo.id]) {
            tiposMap[p.tipo.id] = p.tipo
          }
        })
        this.tipos = Object.values(tiposMap)
      } catch (e) { console.error(e) }
    },

    selectTipo (tipo) {
      this.activeTipo = tipo
      this.fetchProdutos(1)
    },

    // ── Produtos ─────────────────────────────────────────────
    async fetchProdutos (pagina = this.page) {
      this.page    = pagina
      this.loading = true
      try {
        const params = {
          limit:  this.limit,
          offset: (this.page - 1) * this.limit,
        }
        if (this.pesquisa)    params.q    = this.pesquisa
        if (this.activeTipo)  params.tipo = this.activeTipo.nome
        const { data } = await api.get(`/app/loja/${this.lojaId}/produtos/`, { params })
        this.produtos   = data.results || data
        this.totalCount = data.count   ?? this.produtos.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    abrirCriar ()   { this.produtoSelecionado = null; this.showModal = true },
    abrirEditar (p) { this.produtoSelecionado = p;    this.showModal = true },

    async eliminarProduto (p) {
      if (!confirm(`Eliminar "${p.nome}"?`)) return
      try {
        await api.delete(`/app/loja/${this.lojaId}/produtos/${p.id}/eliminar/`)
        await this.fetchProdutos()
      } catch (e) { console.error(e) }
    },

    onSaved () {
      this.showModal = false
      // refresh tipos + produtos (pode ter sido criado novo tipo)
      this.fetchTipos()
      this.fetchProdutos()
    },
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>