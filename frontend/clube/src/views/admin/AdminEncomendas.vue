<template>
  <div class="space-y-5">

    <!-- Filtro por loja -->
    <div class="flex flex-wrap gap-3 items-center">
      <select v-model="filtroLoja" @change="fetchEncomendas(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todas as lojas</option>
        <option v-for="l in lojas" :key="l.id" :value="l.id">{{ l.nome }}</option>
      </select>
      <select v-model="filtroStatus" @change="fetchEncomendas(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todos os estados</option>
        <option value="pendente">Pendente</option>
        <option value="pago">Pago</option>
        <option value="preparando">Preparando</option>
        <option value="enviado">Enviado</option>
        <option value="concluido">Concluido</option>
        <option value="cancelado">Cancelado</option>
      </select>
      <p class="text-xs text-zinc-500 ml-auto">{{ totalCount }} encomendas</p>
    </div>

    <!-- Abas por loja -->
    <div v-if="lojas.length > 0" class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      <button @click="filtroLoja = ''; fetchEncomendas(1)"
        :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === '' ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        Todas
      </button>
      <button v-for="l in lojas" :key="l.id"
        @click="filtroLoja = l.id; fetchEncomendas(1)"
        :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === l.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ l.nome }}
      </button>
    </div>

    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-2">
      <div v-for="enc in encomendas" :key="enc.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">

        <button @click="toggleExpand(enc.id)"
          class="w-full flex items-center gap-4 px-4 py-3 text-left hover:bg-zinc-800/40 transition">
          <div class="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center text-xs font-bold text-zinc-400 flex-shrink-0">
            #{{ enc.id }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="text-sm font-semibold text-zinc-200">{{ enc.loja_nome }}</p>
              <span v-if="enc.metodo_pagamento"
                    class="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">
                {{ enc.metodo_pagamento === 'dinheiro' ? '💵' : enc.metodo_pagamento === 'mbway' ? '📱' : '💳' }}
                {{ enc.metodo_pagamento }}
              </span>
              <span class="text-[10px] text-zinc-500">
                {{ enc.tipo_entrega === 'entrega' ? '🚚' : '🏪' }} {{ enc.tipo_entrega }}
              </span>
            </div>
            <p class="text-xs text-zinc-500">{{ enc.data_criacao }} · {{ enc.comprador_username }}</p>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', statusColor(enc.status)]">
              {{ enc.status }}
            </span>
            <span class="text-sm font-bold text-red-400">{{ formatPrice(enc.valor_total) }}</span>
            <svg xmlns="http://www.w3.org/2000/svg"
                 :class="['h-4 w-4 text-zinc-600 transition-transform', expandedId === enc.id ? 'rotate-180' : '']"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        <div v-if="expandedId === enc.id" class="border-t border-zinc-800 px-4 py-4 space-y-4">
          <div class="grid grid-cols-3 gap-3">
            <div class="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p class="text-sm font-bold text-zinc-100">{{ formatPrice(enc.valor_total) }}</p>
              <p class="text-[10px] text-zinc-500 mt-0.5">Valor total</p>
            </div>
            <div class="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p class="text-sm font-bold text-red-400">
                {{ enc.comissao_valor ? `- ${formatPrice(enc.comissao_valor)}` : '—' }}
              </p>
              <p class="text-[10px] text-zinc-500 mt-0.5">
                Comissão {{ enc.comissao_percentagem ? `(${enc.comissao_percentagem}%)` : '' }}
              </p>
            </div>
            <div class="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p class="text-sm font-bold text-green-400">{{ formatPrice(enc.receita_liquida || enc.valor_total) }}</p>
              <p class="text-[10px] text-zinc-500 mt-0.5">Receita loja</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div class="space-y-1.5">
              <div class="flex justify-between">
                <span class="text-zinc-500">Comprador</span>
                <span class="text-zinc-300">{{ enc.comprador_username }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Loja</span>
                <span class="text-zinc-300">{{ enc.loja_nome }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Entrega</span>
                <span class="text-zinc-300 capitalize">{{ enc.tipo_entrega }}</span>
              </div>
            </div>
            <div class="space-y-1.5">
              <div class="flex justify-between">
                <span class="text-zinc-500">Pagamento</span>
                <span class="text-zinc-300 capitalize">{{ enc.metodo_pagamento || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Estado pag.</span>
                <span :class="enc.pagamento_status === 'aprovado' ? 'text-green-400' : 'text-yellow-400'">
                  {{ enc.pagamento_status || '—' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Data</span>
                <span class="text-zinc-300">{{ enc.data_criacao }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="encomendas.length === 0" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Nenhuma encomenda encontrada.
      </div>
    </div>

    <!-- Paginacao -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchEncomendas(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchEncomendas(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchEncomendas(page + 1)" :disabled="page >= totalPages"
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
  name: 'AdminEncomendas',
  data () {
    return {
      loading: true, encomendas: [], totalCount: 0,
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
    await Promise.all([this.fetchLojas(), this.fetchEncomendas()])
  },
  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },
    statusColor (s) {
      const map = { pendente: 'bg-yellow-500/15 text-yellow-400', pago: 'bg-blue-500/15 text-blue-400', preparando: 'bg-purple-500/15 text-purple-400', enviado: 'bg-indigo-500/15 text-indigo-400', concluido: 'bg-green-500/15 text-green-400', cancelado: 'bg-red-500/15 text-red-400' }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },
    toggleExpand (id) { this.expandedId = this.expandedId === id ? null : id },
    async fetchLojas () {
      try {
        const { data } = await api.get('/app/admin/lojas/', { params: { limit: 100 } })
        this.lojas = data.results || data
      } catch (e) { console.error(e) }
    },
    async fetchEncomendas (pagina = this.page) {
      this.page = pagina; this.loading = true; this.expandedId = null
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.filtroStatus) params.status = this.filtroStatus
        if (this.filtroLoja)   params.loja_id = this.filtroLoja
        const { data } = await api.get('/app/admin/encomendas/', { params })
        this.encomendas = data.results || data
        this.totalCount = data.count ?? this.encomendas.length
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