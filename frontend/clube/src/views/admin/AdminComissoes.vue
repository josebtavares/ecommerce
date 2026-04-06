<template>
  <div class="space-y-5">

    <!-- Totais -->
    <div class="grid grid-cols-2 gap-4">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-xs text-zinc-500 mb-1">Total pendente</p>
        <p class="text-xl sm:text-2xl font-extrabold text-yellow-400">€{{ totalPendente }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-xs text-zinc-500 mb-1">Total liquidado</p>
        <p class="text-xl sm:text-2xl font-extrabold text-green-400">€{{ totalLiquidado }}</p>
      </div>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 items-center">
      <select v-model="filtroStatus" @change="fetchComissoes(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todas</option>
        <option value="pendente">Pendentes</option>
        <option value="liquidada">Liquidadas</option>
      </select>
      <p class="text-xs text-zinc-500 ml-auto">{{ totalCount }} comissões</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista -->
    <div v-else class="space-y-2">
      <div v-for="c in comissoes" :key="c.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">

        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <p class="text-sm font-semibold text-zinc-200">{{ c.loja_nome }}</p>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold',
                             c.status === 'pendente' ? 'bg-yellow-500/15 text-yellow-400' : 'bg-green-500/15 text-green-400']">
                {{ c.status }}
              </span>
            </div>
            <p class="text-xs text-zinc-500">
              Encomenda #{{ c.encomenda_id }} · €{{ c.valor_encomenda }} × {{ c.percentagem }}%
            </p>
            <p class="text-[10px] text-zinc-600 mt-0.5">{{ c.data_criacao }}</p>
            <p v-if="c.data_liquidacao" class="text-[10px] text-zinc-600">Liquidada em {{ c.data_liquidacao }}</p>
          </div>
          <div class="flex flex-col items-end gap-2 flex-shrink-0">
            <p class="text-base font-extrabold text-red-400">€{{ c.valor_comissao }}</p>
            <button v-if="c.status === 'pendente'"
              @click="liquidar(c)"
              class="px-3 py-1.5 rounded-lg bg-green-500/15 text-green-400 hover:bg-green-500/25 text-xs font-bold transition">
              Liquidar
            </button>
          </div>
        </div>
      </div>

      <div v-if="comissoes.length === 0"
           class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Nenhuma comissão encontrada.
      </div>
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">Página {{ page }} de {{ totalPages }}</p>
      <div class="flex gap-2">
        <button @click="fetchComissoes(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button @click="fetchComissoes(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'
export default {
  name: 'AdminComissoes',
  data () {
    return {
      loading: true, comissoes: [], totalCount: 0,
      page: 1, limit: 20, filtroStatus: '',
      totalPendente: '0.00', totalLiquidado: '0.00',
    }
  },
  computed: { totalPages () { return Math.ceil(this.totalCount / this.limit) } },
  async created () { await this.fetchComissoes() },
  methods: {
    async fetchComissoes (pagina = this.page) {
      this.page = pagina; this.loading = true
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.filtroStatus) params.status = this.filtroStatus
        const { data } = await api.get('/app/admin/comissoes/', { params })
        this.comissoes      = data.results || data
        this.totalCount     = data.count ?? this.comissoes.length
        this.totalPendente  = data.total_pendente  || '0.00'
        this.totalLiquidado = data.total_liquidado || '0.00'
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async liquidar (c) {
      if (!confirm(`Marcar comissão #${c.id} (€${c.valor_comissao}) como liquidada?`)) return
      try {
        await api.patch(`/app/admin/comissoes/${c.id}/liquidar/`)
        c.status = 'liquidada'
        await this.fetchComissoes(this.page)
      } catch (e) { console.error(e) }
    },
  },
}
</script>