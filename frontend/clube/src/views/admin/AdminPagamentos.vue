<template>
  <div class="space-y-5">

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 items-center">
      <select v-model="filtroLoja" @change="fetchPagamentos(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todas as lojas</option>
        <option v-for="l in lojas" :key="l.id" :value="l.id">{{ l.nome }}</option>
      </select>
      <select v-model="filtroStatus" @change="fetchPagamentos(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todos</option>
        <option value="pendente">Pendente</option>
        <option value="aprovado">Aprovado</option>
        <option value="falhado">Falhado</option>
        <option value="reembolsado">Reembolsado</option>
      </select>
      <p class="text-xs text-zinc-500 ml-auto">{{ totalCount }} pagamentos</p>
    </div>

    <!-- Abas por loja -->
    <div v-if="lojas.length > 0" class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      <button @click="filtroLoja = ''; fetchPagamentos(1)"
        :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === '' ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        Todas
      </button>
      <button v-for="l in lojas" :key="l.id"
        @click="filtroLoja = l.id; fetchPagamentos(1)"
        :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === l.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ l.nome }}
      </button>
    </div>

    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-2">
      <div v-for="pag in pagamentos" :key="pag.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">

        <button @click="toggleExpand(pag.id)"
          class="w-full flex items-center gap-4 px-4 py-3 text-left hover:bg-zinc-800/40 transition">
          <div class="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center text-lg flex-shrink-0">
            {{ metodIcon(pag.metodo_tipo) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="text-sm font-semibold text-zinc-200">{{ pag.loja_nome || `Encomenda #${pag.encomenda}` }}</p>
              <span class="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded capitalize">
                {{ pag.metodo_tipo || '—' }}
              </span>
            </div>
            <p class="text-xs text-zinc-500">{{ pag.comprador_username || '—' }} · {{ pag.data_criacao }}</p>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', statusColor(pag.status)]">
              {{ pag.status }}
            </span>
            <span class="text-sm font-bold text-red-400">{{ formatPrice(pag.valor) }}</span>
            <svg xmlns="http://www.w3.org/2000/svg"
                 :class="['h-4 w-4 text-zinc-600 transition-transform', expandedId === pag.id ? 'rotate-180' : '']"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        <div v-if="expandedId === pag.id" class="border-t border-zinc-800 px-4 py-4 space-y-4">
          <div class="grid grid-cols-3 gap-3">
            <div class="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p class="text-sm font-bold text-zinc-100">{{ formatPrice(pag.valor) }}</p>
              <p class="text-[10px] text-zinc-500 mt-0.5">Valor pago</p>
            </div>
            <div class="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p class="text-sm font-bold text-red-400">
                {{ pag.comissao_valor ? `- ${formatPrice(pag.comissao_valor)}` : '—' }}
              </p>
              <p class="text-[10px] text-zinc-500 mt-0.5">
                Comissão {{ pag.comissao_percentagem ? `(${pag.comissao_percentagem}%)` : '' }}
              </p>
            </div>
            <div class="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p class="text-sm font-bold text-green-400">{{ formatPrice(pag.receita_liquida || pag.valor) }}</p>
              <p class="text-[10px] text-zinc-500 mt-0.5">Receita loja</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div class="space-y-1.5">
              <div class="flex justify-between">
                <span class="text-zinc-500">Método</span>
                <span class="text-zinc-300 capitalize">{{ pag.metodo_tipo || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Loja</span>
                <span class="text-zinc-300">{{ pag.loja_nome || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Comprador</span>
                <span class="text-zinc-300">{{ pag.comprador_username || '—' }}</span>
              </div>
            </div>
            <div class="space-y-1.5">
              <div class="flex justify-between">
                <span class="text-zinc-500">Referência</span>
                <span class="text-zinc-400 truncate max-w-28">{{ pag.referencia_transacao || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Estado</span>
                <span :class="pag.status === 'aprovado' ? 'text-green-400 font-bold' : 'text-yellow-400'">
                  {{ pag.status }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Data</span>
                <span class="text-zinc-300">{{ pag.data_criacao }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="pagamentos.length === 0" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Nenhum pagamento encontrado.
      </div>
    </div>

    <!-- Paginacao -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchPagamentos(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchPagamentos(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchPagamentos(page + 1)" :disabled="page >= totalPages"
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
  name: 'AdminPagamentos',
  data () {
    return {
      loading: true, pagamentos: [], totalCount: 0,
      page: 1, limit: 10,
      filtroStatus: '', filtroLoja: '',
      lojas: [], expandedId: null,
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
    await Promise.all([this.fetchLojas(), this.fetchPagamentos()])
  },
  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },
    statusColor (s) {
      const map = { pendente: 'bg-yellow-500/15 text-yellow-400', aprovado: 'bg-green-500/15 text-green-400', falhado: 'bg-red-500/15 text-red-400', reembolsado: 'bg-blue-500/15 text-blue-400' }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },
    metodIcon (tipo) {
      const map = { dinheiro: '💵', mbway: '📱', cartao: '💳', paypal: '🅿️', stripe: '💳' }
      return map[tipo] || '💰'
    },
    toggleExpand (id) { this.expandedId = this.expandedId === id ? null : id },
    async fetchLojas () {
      try {
        const { data } = await api.get('/app/admin/lojas/', { params: { limit: 100 } })
        this.lojas = data.results || data
      } catch (e) { console.error(e) }
    },
    async fetchPagamentos (pagina = this.page) {
      this.page = pagina; this.loading = true; this.expandedId = null
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.filtroStatus) params.status = this.filtroStatus
        if (this.filtroLoja)   params.loja_id = this.filtroLoja
        const { data } = await api.get('/app/admin/pagamentos/', { params })
        this.pagamentos = data.results || data
        this.totalCount = data.count ?? this.pagamentos.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>