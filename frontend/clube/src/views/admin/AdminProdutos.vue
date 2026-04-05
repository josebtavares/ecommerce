<template>
  <div class="space-y-5">

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 items-center">
      <div class="relative flex-1 min-w-48">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="q" @input="debouncedFetch" placeholder="Pesquisar produto..."
          class="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
      </div>
      <select v-model="filtroAtivo" @change="fetchProdutos(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todos</option>
        <option value="true">Activos</option>
        <option value="false">Inactivos</option>
      </select>
      <p class="text-xs text-zinc-500 ml-auto">{{ totalCount }} produtos</p>
    </div>

    <!-- Abas por loja -->
    <div v-if="lojas.length > 0" class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      <button @click="filtroLoja = ''; fetchProdutos(1)"
        :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === '' ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        Todas
      </button>
      <button v-for="l in lojas" :key="l.id"
        @click="filtroLoja = l.id; fetchProdutos(1)"
        :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === l.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ l.nome }}
      </button>
    </div>

    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      <div v-for="n in 8" :key="n" class="h-48 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <div v-for="p in produtos" :key="p.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden group">
        <div class="relative h-36 overflow-hidden">
          <img v-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full bg-zinc-800 flex items-center justify-center text-zinc-600 text-2xl">📦</div>
          <div v-if="!p.ativo" class="absolute inset-0 bg-black/60 flex items-center justify-center">
            <span class="text-xs font-bold text-zinc-300">Inactivo</span>
          </div>
          <span v-if="p.destaque" class="absolute top-2 right-2 text-xs">⭐</span>
        </div>
        <div class="p-3">
          <p class="text-xs font-semibold text-zinc-200 truncate">{{ p.nome }}</p>
          <p class="text-xs text-zinc-500 truncate">{{ p.loja?.nome }}</p>
          <div class="flex items-center justify-between mt-2">
            <span class="text-xs font-bold text-red-400">€{{ p.preco }}</span>
            <div class="flex gap-1">
              <button @click="toggleAtivo(p)"
                :class="['px-2 py-0.5 rounded text-[10px] font-bold transition',
                         p.ativo ? 'bg-red-500/15 text-red-400 hover:bg-red-500/25' : 'bg-green-500/15 text-green-400 hover:bg-green-500/25']">
                {{ p.ativo ? 'Desactivar.' : 'Activar' }}
              </button>
              <button @click="toggleDestaque(p)"
                :class="['px-2 py-0.5 rounded text-[10px] font-bold transition',
                         p.destaque ? 'bg-yellow-500/15 text-yellow-400' : 'bg-zinc-800 text-zinc-500']">
                ⭐
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="produtos.length === 0 && !loading"
           class="col-span-full text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Nenhum produto encontrado.
      </div>
    </div>

    <!-- Paginacao -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchProdutos(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchProdutos(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchProdutos(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
export default {
  name: 'AdminProdutos',
  data () {
    return {
      loading: true, produtos: [], totalCount: 0,
      page: 1, limit: 20,
      q: '', filtroAtivo: '', filtroLoja: '',
      lojas: [], debounceTimer: null,
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
    await Promise.all([this.fetchLojas(), this.fetchProdutos()])
  },
  methods: {
    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchProdutos(1), 350)
    },
    async fetchLojas () {
      try {
        const { data } = await api.get('/app/admin/lojas/', { params: { limit: 100 } })
        this.lojas = data.results || data
      } catch (e) { console.error(e) }
    },
    async fetchProdutos (pagina = this.page) {
      this.page = pagina; this.loading = true
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.q) params.q = this.q
        if (this.filtroAtivo !== '') params.ativo = this.filtroAtivo
        if (this.filtroLoja) params.loja_id = this.filtroLoja
        const { data } = await api.get('/app/admin/produtos/', { params })
        this.produtos   = data.results || data
        this.totalCount = data.count ?? this.produtos.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async toggleAtivo (p) {
      try { const { data } = await api.patch(`/app/admin/produtos/${p.id}/`, { ativo: !p.ativo }); p.ativo = data.ativo } catch (e) { console.error(e) }
    },
    async toggleDestaque (p) {
      try { const { data } = await api.patch(`/app/admin/produtos/${p.id}/`, { destaque: !p.destaque }); p.destaque = data.destaque } catch (e) { console.error(e) }
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>