<template>
  <div class="space-y-5">

    <!-- ══ SUMÁRIO DE TOTAIS ══ -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Pendente</p>
        <p class="text-xl font-extrabold text-yellow-400">€{{ totalPendente }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Liquidado</p>
        <p class="text-xl font-extrabold text-green-400">€{{ totalLiquidado }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Total comissões</p>
        <p class="text-xl font-extrabold text-zinc-100">{{ totalCount }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Nesta página</p>
        <p class="text-xl font-extrabold text-zinc-400">{{ comissoes.length }}</p>
      </div>
    </div>

    <!-- ══ ABAS DE LOJAS ══ -->
    <div v-if="lojas.length > 0"
         class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      <button @click="selectLoja(null)"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === null
                   ? 'bg-red-600 text-white'
                   : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        Todas as lojas
      </button>
      <button v-for="loja in lojas" :key="loja.id"
        @click="selectLoja(loja.id)"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === loja.id
                   ? 'bg-red-600 text-white'
                   : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        {{ loja.nome }}
        <span v-if="loja.pendente" class="ml-1.5 px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-[9px] font-bold">
          €{{ loja.pendente }}
        </span>
      </button>
    </div>

    <!-- ══ FILTROS ══ -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 space-y-3">
      <div class="flex flex-wrap gap-3">

        <!-- Status -->
        <div class="flex gap-1">
          <button v-for="s in statusOpcoes" :key="s.value"
            @click="filtroStatus = s.value; fetchComissoes(1)"
            :class="['px-3 py-2 rounded-xl text-xs font-semibold transition border',
                     filtroStatus === s.value
                       ? s.activeClass
                       : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:text-zinc-200']">
            {{ s.label }}
          </button>
        </div>

        <!-- Data início -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-zinc-500 whitespace-nowrap">De</label>
          <input v-model="filtroDataInicio" @change="fetchComissoes(1)" type="date"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200
                   focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Data fim -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-zinc-500 whitespace-nowrap">Até</label>
          <input v-model="filtroDataFim" @change="fetchComissoes(1)" type="date"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200
                   focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Atalhos de datas -->
        <div class="flex gap-1 flex-wrap">
          <button v-for="atalho in atalhosData" :key="atalho.label"
            @click="aplicarAtalho(atalho)"
            class="px-2.5 py-1.5 rounded-lg text-[10px] font-semibold transition border border-zinc-700
                   text-zinc-500 hover:text-zinc-200 hover:border-zinc-500">
            {{ atalho.label }}
          </button>
        </div>

        <!-- Mínimo de comissão -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-zinc-500 whitespace-nowrap">Mín. €</label>
          <input v-model="filtroMin" @input="debouncedFetch" type="number" min="0" step="0.01" placeholder="0.00"
            class="w-24 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200
                   focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Ordenação -->
        <select v-model="filtroOrdem" @change="fetchComissoes(1)"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-300
                 focus:outline-none focus:border-red-500 transition cursor-pointer">
          <option value="-data_criacao">Criação mais recente</option>
          <option value="data_criacao">Criação mais antiga</option>
          <option value="-data_liquidacao">Liquidação mais recente</option>
          <option value="data_liquidacao">Liquidação mais antiga</option>
          <option value="-valor_comissao">Maior comissão</option>
          <option value="valor_comissao">Menor comissão</option>
        </select>

        <!-- Itens por página -->
        <select v-model="limit" @change="fetchComissoes(1)"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-300
                 focus:outline-none focus:border-red-500 transition cursor-pointer">
          <option :value="15">15 / pág.</option>
          <option :value="20">20 / pág.</option>
          <option :value="50">50 / pág.</option>
        </select>

        <!-- Limpar filtros -->
        <button v-if="temFiltrosActivos" @click="limparFiltros"
          class="px-3 py-2 rounded-xl text-xs font-semibold text-red-400 hover:text-red-300
                 bg-red-500/10 hover:bg-red-500/20 transition flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Limpar
        </button>
      </div>

      <!-- Indicador de filtros activos -->
      <div v-if="temFiltrosActivos" class="flex flex-wrap gap-2">
        <span v-if="filtroLoja"
              class="flex items-center gap-1 px-2 py-0.5 bg-red-600/15 text-red-400 text-[10px] rounded-lg border border-red-500/30">
          {{ lojaLabel(filtroLoja) }}
          <button @click="selectLoja(null)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroStatus && filtroStatus !== ''"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          {{ statusOpcoes.find(s => s.value === filtroStatus)?.label }}
          <button @click="filtroStatus = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroDataInicio"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          De {{ filtroDataInicio }}
          <button @click="filtroDataInicio = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroDataFim"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          Até {{ filtroDataFim }}
          <button @click="filtroDataFim = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroMin"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          Mín. €{{ filtroMin }}
          <button @click="filtroMin = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
      </div>
    </div>

    <!-- Resultado -->
    <div class="flex items-center justify-between text-xs text-zinc-500">
      <span>{{ totalCount }} comissão{{ totalCount !== 1 ? 'ões' : '' }} encontrada{{ totalCount !== 1 ? 's' : '' }}</span>
      <span v-if="totalCount > 0">Página {{ page }} de {{ totalPages }}</span>
    </div>

    <!-- ══ LOADING ══ -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in limit" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
    </div>

    <!-- ══ LISTA ══ -->
    <div v-else-if="comissoes.length" class="space-y-2">
      <div v-for="c in comissoes" :key="c.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 hover:border-zinc-700 transition">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <p class="text-sm font-semibold text-zinc-200 truncate">{{ c.loja_nome }}</p>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold',
                             c.status === 'pendente' ? 'bg-yellow-500/15 text-yellow-400' : 'bg-green-500/15 text-green-400']">
                {{ c.status }}
              </span>
            </div>
            <p class="text-xs text-zinc-500">
              Encomenda #{{ c.encomenda_id }}
              <span class="mx-1 text-zinc-700">·</span>
              Valor €{{ c.valor_encomenda }}
              <span class="mx-1 text-zinc-700">·</span>
              Taxa {{ c.percentagem }}%
            </p>
            <p class="text-[10px] text-zinc-600 mt-0.5">{{ formatarData(c.data_criacao) }}</p>
            <p v-if="c.data_liquidacao" class="text-[10px] text-green-600 mt-0.5">
              ✓ Liquidada em {{ formatarData(c.data_liquidacao) }}
            </p>
          </div>
          <div class="flex flex-col items-end gap-2 flex-shrink-0">
            <p class="text-lg font-extrabold text-red-400">€{{ c.valor_comissao }}</p>
            <button v-if="c.status === 'pendente'"
              @click="liquidar(c)" :disabled="liquidandoId === c.id"
              class="px-3 py-1.5 rounded-lg bg-green-500/15 text-green-400 hover:bg-green-500/25
                     text-xs font-bold transition disabled:opacity-50 flex items-center gap-1">
              <svg v-if="liquidandoId === c.id" class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              {{ liquidandoId === c.id ? '...' : 'Liquidar' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading"
         class="text-center py-14 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto mb-3 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
      Nenhuma comissão encontrada.
      <br/>
      <button v-if="temFiltrosActivos" @click="limparFiltros" class="text-red-400 hover:text-red-300 mt-2 text-xs">
        Limpar filtros →
      </button>
    </div>

    <!-- ══ PAGINAÇÃO ══ -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-1.5">
        <button @click="fetchComissoes(1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30 text-xs text-zinc-400">
          «
        </button>
        <button @click="fetchComissoes(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchComissoes(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchComissoes(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button @click="fetchComissoes(totalPages)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30 text-xs text-zinc-400">
          »
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
      loading: true,
      comissoes: [],
      totalCount: 0,
      page: 1,
      limit: 20,           // 20 por defeito

      // filtros
      filtroStatus:     '',
      filtroLoja:       null,
      filtroDataInicio: '',
      filtroDataFim:    '',
      filtroMin:        '',
      filtroOrdem:      '-data_criacao',

      // totais
      totalPendente:  '0.00',
      totalLiquidado: '0.00',

      // lojas para as abas
      lojas: [],

      // estado
      liquidandoId: null,
      debounceTimer: null,

      statusOpcoes: [
        { value: '',         label: 'Todas',     activeClass: 'bg-zinc-700 border-zinc-600 text-zinc-200' },
        { value: 'pendente', label: 'Pendentes', activeClass: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400' },
        { value: 'liquidada',label: 'Liquidadas',activeClass: 'bg-green-500/20 border-green-500/50 text-green-400' },
      ],

      atalhosData: [
        { label: 'Hoje',       dias: 0  },
        { label: 'Esta semana',dias: 7  },
        { label: 'Este mês',   dias: 30 },
        { label: '3 meses',    dias: 90 },
      ],
    }
  },

  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },

    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },

    temFiltrosActivos () {
      return this.filtroLoja || this.filtroStatus ||
             this.filtroDataInicio || this.filtroDataFim || this.filtroMin
    },
  },

  async created () {
    await Promise.all([this.fetchLojas(), this.fetchComissoes()])
  },

  methods: {
    async fetchComissoes (pagina = this.page) {
      this.page = pagina
      this.loading = true
      try {
        const params = {
          offset:   (this.page - 1) * this.limit,
          limit:    this.limit,
          ordering: this.filtroOrdem,
        }
        if (this.filtroStatus)     params.status       = this.filtroStatus
        if (this.filtroLoja)       params.loja_id      = this.filtroLoja
        if (this.filtroDataInicio) params.data_inicio  = this.filtroDataInicio
        if (this.filtroDataFim)    params.data_fim     = this.filtroDataFim
        if (this.filtroMin)        params.valor_min    = this.filtroMin

        const { data } = await api.get('/app/admin/comissoes/', { params })
        this.comissoes      = data.results || data
        this.totalCount     = data.count           ?? this.comissoes.length
        this.totalPendente  = data.total_pendente  || '0.00'
        this.totalLiquidado = data.total_liquidado || '0.00'
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async fetchLojas () {
      try {
        // Busca sumário de comissões por loja para mostrar pendentes nas abas
        const { data } = await api.get('/app/admin/comissoes/por-loja/')
        this.lojas = data
      } catch (e) {
        // fallback: sem abas se o endpoint não existir ainda
        this.lojas = []
      }
    },

    selectLoja (id) {
      this.filtroLoja = id
      this.fetchComissoes(1)
    },

    lojaLabel (id) {
      return this.lojas.find(l => l.id === id)?.nome || `Loja #${id}`
    },

    aplicarAtalho (atalho) {
      const hoje = new Date()
      const inicio = new Date()
      if (atalho.dias === 0) {
        // hoje
        this.filtroDataInicio = this.formatarDateInput(hoje)
        this.filtroDataFim    = this.formatarDateInput(hoje)
      } else {
        inicio.setDate(hoje.getDate() - atalho.dias)
        this.filtroDataInicio = this.formatarDateInput(inicio)
        this.filtroDataFim    = this.formatarDateInput(hoje)
      }
      this.fetchComissoes(1)
    },

    formatarDateInput (d) {
      return d.toISOString().split('T')[0]
    },

    formatarData (str) {
      if (!str) return ''
      return new Date(str).toLocaleDateString('pt-PT', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      })
    },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchComissoes(1), 400)
    },

    limparFiltros () {
      this.filtroStatus     = ''
      this.filtroLoja       = null
      this.filtroDataInicio = ''
      this.filtroDataFim    = ''
      this.filtroMin        = ''
      this.filtroOrdem      = '-data_criacao'
      this.fetchComissoes(1)
    },

    async liquidar (c) {
      if (!confirm(`Marcar comissão #${c.id} (€${c.valor_comissao}) como liquidada?`)) return
      this.liquidandoId = c.id
      try {
        await api.patch(`/app/admin/comissoes/${c.id}/liquidar/`)
        await this.fetchComissoes(this.page)
      } catch (e) { console.error(e) }
      finally { this.liquidandoId = null }
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>