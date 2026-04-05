<template>
  <div class="space-y-6">

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
      <div v-for="kpi in kpis" :key="kpi.label"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-zinc-500 uppercase tracking-wider">{{ kpi.label }}</span>
          <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', kpi.bg]">
            <component :is="kpi.iconComp" class="h-4 w-4" :class="kpi.color" />
          </div>
        </div>
        <div v-if="loading" class="h-7 w-24 bg-zinc-800 rounded animate-pulse"></div>
        <p v-else class="text-2xl font-extrabold text-zinc-100">{{ kpi.value }}</p>
        <p class="text-xs text-zinc-600 mt-1">{{ kpi.sub }}</p>
      </div>
    </div>

    <!-- Encomendas recentes + Por status -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Encomendas recentes -->
      <div class="lg:col-span-2 bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Encomendas recentes</h2>
        <div v-if="loading" class="space-y-3">
          <div v-for="n in 4" :key="n" class="h-12 bg-zinc-800 rounded-xl animate-pulse"></div>
        </div>
        <div v-else-if="encomendas.length === 0" class="text-center py-8 text-zinc-600 text-sm">
          Sem encomendas ainda.
        </div>
        <div v-else class="space-y-2">
          <div v-for="enc in encomendas" :key="enc.id"
               class="flex items-center justify-between p-3 bg-zinc-800/50 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-700 flex items-center justify-center text-xs font-bold text-zinc-400">
                #{{ enc.id }}
              </div>
              <div>
                <p class="text-sm font-medium text-zinc-200">{{ enc.comprador_username }}</p>
                <p class="text-xs text-zinc-500">{{ formatDate(enc.data_criacao) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', statusColor(enc.status)]">
                {{ enc.status }}
              </span>
              <span class="text-sm font-bold text-red-400">{{ formatPrice(enc.valor_total) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Por status -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Por estado</h2>
        <div v-if="loading" class="space-y-3">
          <div v-for="n in 5" :key="n" class="h-8 bg-zinc-800 rounded-lg animate-pulse"></div>
        </div>
        <div v-else class="space-y-2">
          <div v-for="s in statusStats" :key="s.status"
               class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-800/50">
            <div class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full', s.dot]"></span>
              <span class="text-sm text-zinc-300 capitalize">{{ s.status }}</span>
            </div>
            <span class="text-sm font-bold text-zinc-200">{{ s.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { h } from 'vue'
import api from '@/services/api'

const IconBag     = { render: () => h('svg', { xmlns:'http://www.w3.org/2000/svg', fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z' })]) }
const IconMoney   = { render: () => h('svg', { xmlns:'http://www.w3.org/2000/svg', fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })]) }
const IconBox     = { render: () => h('svg', { xmlns:'http://www.w3.org/2000/svg', fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' })]) }
const IconPending = { render: () => h('svg', { xmlns:'http://www.w3.org/2000/svg', fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })]) }

export default {
  name: 'BackofficeDashboard',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: true,
      encomendas: [],
      stats: { total: 0, receita: 0, comissoes: 0, liquida: 0, produtos: 0, pendentes: 0 },
    }
  },

  computed: {
    kpis () {
      return [
        { label: 'Total encomendas', value: this.stats.total,                        sub: 'Todas as encomendas',        bg: 'bg-blue-500/10',   color: 'text-blue-400',   iconComp: IconBag     },
        { label: 'Receita bruta',    value: this.formatPrice(this.stats.receita),     sub: 'Valor total das encomendas', bg: 'bg-green-500/10',  color: 'text-green-400',  iconComp: IconMoney   },
        { label: 'Comissoes pagas',  value: this.formatPrice(this.stats.comissoes),   sub: 'Descontado pela plataforma', bg: 'bg-red-500/10',    color: 'text-red-400',    iconComp: IconPending },
        { label: 'Receita liquida',  value: this.formatPrice(this.stats.liquida),     sub: 'O que fica para ti',         bg: 'bg-emerald-500/10',color: 'text-emerald-400',iconComp: IconMoney   },
        { label: 'Produtos activos', value: this.stats.produtos,                      sub: 'No catalogo',                bg: 'bg-purple-500/10', color: 'text-purple-400', iconComp: IconBox     },
        { label: 'Pendentes',        value: this.stats.pendentes,                     sub: 'A aguardar',                 bg: 'bg-yellow-500/10', color: 'text-yellow-400', iconComp: IconPending },
      ]
    },
    statusStats () {
      const statusList = ['pendente', 'pago', 'preparando', 'enviado', 'concluido', 'cancelado']
      const dots = { pendente: 'bg-yellow-400', pago: 'bg-blue-400', preparando: 'bg-purple-400', enviado: 'bg-indigo-400', concluido: 'bg-green-400', cancelado: 'bg-red-400' }
      return statusList.map(s => ({
        status: s,
        dot: dots[s] || 'bg-zinc-400',
        count: this.encomendas.filter(e => e.status === s).length,
      }))
    },
  },

  async created () {
    await this.fetchData()
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },
    formatDate (d) {
      return new Date(d).toLocaleDateString('pt-PT')
    },
    statusColor (s) {
      const map = { pendente: 'bg-yellow-500/15 text-yellow-400', pago: 'bg-blue-500/15 text-blue-400', preparando: 'bg-purple-500/15 text-purple-400', enviado: 'bg-indigo-500/15 text-indigo-400', concluido: 'bg-green-500/15 text-green-400', cancelado: 'bg-red-500/15 text-red-400' }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },

    async fetchData () {
      this.loading = true
      try {
        const [enc, prod] = await Promise.all([
          api.get(`/app/loja/${this.lojaId}/encomendas/?limit=100`),
          api.get(`/app/loja/${this.lojaId}/produtos/?limit=1`),
        ])
        const todasEncomendas = enc.data.results || enc.data
        this.encomendas = todasEncomendas.slice(0, 8)
        const encPagas = todasEncomendas.filter(e => ['pago','preparando','enviado','concluido'].includes(e.status))
        const receita   = encPagas.reduce((s, e) => s + parseFloat(e.valor_total || 0), 0)
        const comissoes = encPagas.reduce((s, e) => s + parseFloat(e.comissao_valor || 0), 0)
        const liquida   = encPagas.reduce((s, e) => s + parseFloat(e.receita_liquida || e.valor_total || 0), 0)
        this.stats = {
          total:     todasEncomendas.length,
          receita,
          comissoes,
          liquida,
          produtos:  prod.data.count ?? 0,
          pendentes: todasEncomendas.filter(e => e.status === 'pendente').length,
        }
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
  }
}
</script>