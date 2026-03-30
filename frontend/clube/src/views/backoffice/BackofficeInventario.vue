<template>
  <div class="space-y-5">

    <!-- Header -->
    <div class="flex items-center gap-3">
      <div class="relative flex-1 max-w-xs">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="pesquisa" @input="debouncedFetch" placeholder="Pesquisar produto..."
          class="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
      </div>

      <!-- Por página -->
      <select v-model="limit" @change="fetchInventario(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300
               focus:outline-none focus:border-red-500 transition">
        <option :value="10">10 / pág.</option>
        <option :value="20">20 / pág.</option>
        <option :value="50">50 / pág.</option>
      </select>

      <button @click="filtroStockBaixo = !filtroStockBaixo; fetchInventario(1)"
        :class="['px-3 py-2 rounded-xl text-xs font-semibold transition border',
                 filtroStockBaixo
                   ? 'bg-red-600/20 border-red-500/50 text-red-400'
                   : 'bg-zinc-900 border-zinc-700 text-zinc-400 hover:text-zinc-200']">
        ⚠️ Stock baixo
      </button>
    </div>

    <!-- Info -->
    <p class="text-xs text-zinc-600">
      {{ totalCount }} produto{{ totalCount !== 1 ? 's' : '' }} no inventário
    </p>

    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in limit" :key="n" class="h-14 bg-zinc-900 rounded-xl animate-pulse"></div>
    </div>

    <!-- Tabela -->
    <div v-else-if="inventario.length"
         class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-zinc-800">
            <th class="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider">Produto</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-zinc-500 uppercase tracking-wider">Stock</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-zinc-500 uppercase tracking-wider hidden sm:table-cell">Custo</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-zinc-500 uppercase tracking-wider hidden sm:table-cell">Venda</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-zinc-500 uppercase tracking-wider">Ajustar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-800/50">
          <tr v-for="inv in inventario" :key="inv.id" class="hover:bg-zinc-800/30 transition">
            <td class="px-4 py-3">
              <p class="text-sm font-medium text-zinc-200">{{ inv.produto_nome }}</p>
              <p class="text-xs text-zinc-600">{{ inv.produto_sku }}</p>
            </td>
            <td class="px-4 py-3 text-center">
              <span :class="[
                'px-2 py-0.5 rounded-full text-xs font-bold',
                inv.quantidade === 0      ? 'bg-red-500/15 text-red-400' :
                inv.quantidade <= 5       ? 'bg-orange-500/15 text-orange-400' :
                inv.quantidade <= 20      ? 'bg-yellow-500/15 text-yellow-400' :
                                            'bg-green-500/15 text-green-400'
              ]">{{ inv.quantidade }} un.</span>
            </td>
            <td class="px-4 py-3 text-center text-sm text-zinc-500 hidden sm:table-cell">
              {{ formatPrice(inv.preco_custo) }}
            </td>
            <td class="px-4 py-3 text-center text-sm font-medium text-zinc-200 hidden sm:table-cell">
              {{ formatPrice(inv.preco_venda) }}
            </td>
            <td class="px-4 py-3 text-center">
              <button @click="abrirAjuste(inv)"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-300 transition">
                Ajustar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      Sem inventário registado.
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
      <p class="text-xs text-zinc-500">
        Página {{ page }} de {{ totalPages }}
        · {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchInventario(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30 disabled:cursor-not-allowed">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p"
          @click="fetchInventario(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchInventario(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30 disabled:cursor-not-allowed">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Modal ajuste -->
    <div v-if="modalAjuste"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="modalAjuste = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 shadow-2xl">
        <h3 class="text-base font-bold text-zinc-100 mb-1">Ajustar stock</h3>
        <p class="text-xs text-zinc-500 mb-5">{{ modalAjuste.produto_nome }}</p>
        <div class="space-y-4">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Ajuste de quantidade</label>
            <input v-model.number="ajusteValor" type="number" placeholder="+10 ou -5"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
            <p class="text-xs text-zinc-600 mt-1">
              Actual: {{ modalAjuste.quantidade }} → após: {{ modalAjuste.quantidade + (ajusteValor || 0) }}
            </p>
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Preço de custo</label>
            <input v-model.number="ajustePrecoC" type="number" step="0.01"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Preço de venda</label>
            <input v-model.number="ajustePrecoV" type="number" step="0.01"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="modalAjuste = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="guardarAjuste" :disabled="loadingAjuste"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     loadingAjuste ? 'bg-red-700 opacity-70 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
            <span v-if="loadingAjuste" class="flex items-center gap-1">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              A guardar…
            </span>
            <span v-else>Guardar</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'BackofficeInventario',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: true,
      inventario: [],
      totalCount: 0,
      page: 1,
      limit: 20,
      pesquisa: '',
      filtroStockBaixo: false,
      debounceTimer: null,
      modalAjuste: null,
      ajusteValor: 0,
      ajustePrecoC: 0,
      ajustePrecoV: 0,
      loadingAjuste: false,
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

  async created () { await this.fetchInventario() },

  methods: {
    formatPrice (val) { return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0) },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchInventario(1), 350)
    },

    async fetchInventario (pagina = this.page) {
      this.page    = pagina
      this.loading = true
      try {
        const params = {
          limit:  this.limit,
          offset: (this.page - 1) * this.limit,
        }
        if (this.pesquisa)       params.q          = this.pesquisa
        if (this.filtroStockBaixo) params.stock_baixo = 'true'
        const { data } = await api.get(`/app/loja/${this.lojaId}/inventario/`, { params })
        this.inventario = data.results || data
        this.totalCount = data.count   ?? this.inventario.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    abrirAjuste (inv) {
      this.modalAjuste  = inv
      this.ajusteValor  = 0
      this.ajustePrecoC = parseFloat(inv.preco_custo)
      this.ajustePrecoV = parseFloat(inv.preco_venda)
    },

    async guardarAjuste () {
      this.loadingAjuste = true
      try {
        await api.post(`/app/loja/${this.lojaId}/inventario/`, {
          produto_id:  this.modalAjuste.produto,
          quantidade:  this.modalAjuste.quantidade + (this.ajusteValor || 0),
          preco_custo: this.ajustePrecoC,
          preco_venda: this.ajustePrecoV,
        })
        this.modalAjuste = null
        await this.fetchInventario()
      } catch (e) { console.error(e) }
      finally { this.loadingAjuste = false }
    },
  }
}
</script>