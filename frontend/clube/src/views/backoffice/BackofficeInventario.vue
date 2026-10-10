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
          <template v-for="inv in inventario" :key="inv.id">
          <tr class="hover:bg-zinc-800/30 transition">
            <td class="px-4 py-3">
              <p class="text-sm font-medium text-zinc-200">{{ inv.produto_nome }}</p>
              <p class="text-xs text-zinc-600">{{ inv.produto_sku }}</p>
              <!-- resumo das variações -->
              <button v-if="inv.stock_por_variante" type="button" @click="toggleVariantes(inv)"
                class="mt-1 inline-flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-200 transition">
                📦 {{ inv.variantes.length }} variações
                <span v-if="esgotadas(inv)" class="text-red-400">· {{ esgotadas(inv) }} esgotada{{ esgotadas(inv) > 1 ? 's' : '' }}</span>
                <span v-else-if="emBaixo(inv)" class="text-amber-400">· {{ emBaixo(inv) }} em baixo</span>
                <span class="transition-transform" :class="aberto === inv.id && 'rotate-180'">▾</span>
              </button>
              <button v-else-if="inv.variantes_pendentes" type="button" @click="toggleVariantes(inv)"
                class="mt-1 inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-500/10 text-[10px] font-semibold text-amber-300 hover:bg-amber-500/20 transition">
                ⚠️ Definir stock por variação
              </button>
            </td>
            <td class="px-4 py-3 text-center">
              <span :class="[
                'px-2 py-0.5 rounded-full text-xs font-bold',
                inv.quantidade === 0      ? 'bg-red-500/15 text-red-400' :
                inv.quantidade <= 5       ? 'bg-orange-500/15 text-orange-400' :
                inv.quantidade <= 20      ? 'bg-yellow-500/15 text-yellow-400' :
                                            'bg-green-500/15 text-green-400'
              ]">{{ inv.quantidade }} un.</span>
              <p v-if="inv.stock_por_variante" class="text-[10px] text-zinc-600 mt-1">total</p>
            </td>
            <td class="px-4 py-3 text-center text-sm text-zinc-500 hidden sm:table-cell">
              {{ formatPrice(inv.preco_custo) }}
            </td>
            <td class="px-4 py-3 text-center text-sm font-medium text-zinc-200 hidden sm:table-cell">
              {{ formatPrice(inv.preco_venda) }}
            </td>
            <td class="px-4 py-3 text-center">
              <div class="flex items-center justify-center gap-1.5 flex-wrap">
                <button v-if="inv.stock_por_variante || inv.variantes_pendentes" @click="toggleVariantes(inv)"
                  :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition',
                           aberto === inv.id ? 'bg-amber-500/20 text-amber-200' : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300']">
                  Variações
                </button>
                <button @click="abrirAjuste(inv)"
                  class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-300 transition">
                  {{ inv.stock_por_variante ? 'Preços' : 'Ajustar' }}
                </button>
              </div>
            </td>
          </tr>
          <!-- grelha de variações (expandida) -->
          <tr v-if="aberto === inv.id" class="bg-zinc-950/40">
            <td colspan="5" class="px-4 py-4">
              <VariantesStockEditor :lojaId="lojaId" :produtoId="inv.produto" @guardado="onVariantesGuardadas" />
            </td>
          </tr>
          </template>
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
        <h3 class="text-base font-bold text-zinc-100 mb-1">{{ modalAjuste.stock_por_variante ? 'Preços' : 'Ajustar stock' }}</h3>
        <p class="text-xs text-zinc-500 mb-5">{{ modalAjuste.produto_nome }}</p>
        <div class="space-y-4">
          <p v-if="modalAjuste.stock_por_variante"
             class="text-xs text-amber-200/90 bg-amber-500/5 border border-amber-500/30 rounded-xl px-3 py-2 leading-relaxed">
            Este produto usa stock por variação ({{ modalAjuste.quantidade }} un. no total).
            Ajusta as quantidades em <b>Variações</b>.
          </p>
          <div v-else>
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
        <p v-if="erroAjuste" class="mt-3 text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2">{{ erroAjuste }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import VariantesStockEditor from '@/components/inventario/VariantesStockEditor.vue'

export default {
  name: 'BackofficeInventario',
  components: { VariantesStockEditor },
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
      erroAjuste: '',
      aberto: null,   // id da linha com a grelha de variações aberta
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

    async fetchInventario (pagina = this.page, silencioso = false) {
      this.page    = pagina
      if (!silencioso) this.loading = true
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
      this.erroAjuste   = ''
      this.ajusteValor  = 0
      this.ajustePrecoC = parseFloat(inv.preco_custo)
      this.ajustePrecoV = parseFloat(inv.preco_venda)
    },

    async guardarAjuste () {
      this.loadingAjuste = true
      this.erroAjuste = ''
      try {
        const body = {
          produto_id:  this.modalAjuste.produto,
          preco_custo: this.ajustePrecoC,
          preco_venda: this.ajustePrecoV,
        }
        // com stock por variação a quantidade é gerida por variação (o backend rejeita o total)
        if (!this.modalAjuste.stock_por_variante) {
          body.quantidade = this.modalAjuste.quantidade + (this.ajusteValor || 0)
        }
        await api.post(`/app/loja/${this.lojaId}/inventario/`, body)
        this.modalAjuste = null
        await this.fetchInventario()
      } catch (e) {
        const d = e.response?.data
        this.erroAjuste = d?.detail || (d && Object.values(d).flat()[0]) || 'Erro ao guardar.'
      } finally { this.loadingAjuste = false }
    },

    // ── Variações ───────────────────────────────────────────
    toggleVariantes (inv) {
      this.aberto = this.aberto === inv.id ? null : inv.id
    },

    esgotadas (inv) { return inv.variantes.filter(v => v.quantidade === 0).length },
    emBaixo (inv)   { return inv.variantes.filter(v => v.quantidade > 0 && v.quantidade <= 5).length },

    // actualiza a linha (total, resumo) sem fechar a grelha
    async onVariantesGuardadas () {
      await this.fetchInventario(this.page, true)
    },
  }
}
</script>