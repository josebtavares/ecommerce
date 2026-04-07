<template>
  <div class="space-y-6">

    <!-- Filtros de período ───────────────────────────────── -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
      <div class="flex flex-wrap gap-3 items-end">

        <!-- Atalhos rápidos -->
        <div class="flex gap-1 flex-wrap">
          <button v-for="a in atalhos" :key="a.label"
            @click="aplicarAtalho(a)"
            :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                     atalhoActivo === a.label
                       ? 'bg-red-600 text-white'
                       : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
            {{ a.label }}
          </button>
        </div>

        <!-- Datas personalizadas -->
        <div class="flex items-center gap-2 flex-wrap">
          <div class="flex flex-col gap-1">
            <label class="text-[10px] text-zinc-500 uppercase tracking-wider">De</label>
            <input type="date" v-model="dataInicio"
              class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm
                     text-zinc-200 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-[10px] text-zinc-500 uppercase tracking-wider">Até</label>
            <input type="date" v-model="dataFim"
              class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm
                     text-zinc-200 focus:outline-none focus:border-red-500 transition" />
          </div>
          <button @click="aplicarDatas"
            :disabled="loading"
            class="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-bold
                   rounded-xl transition disabled:opacity-50 self-end flex items-center gap-2">
            <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" class="opacity-75"/>
            </svg>
            Aplicar
          </button>

          <!-- Exportar PDF -->
          <button v-if="dados" @click="exportarPdf" :disabled="loadingPdf"
            class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-semibold
                   rounded-xl transition self-end flex items-center gap-2 disabled:opacity-50">
            <svg v-if="loadingPdf" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" class="opacity-75"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {{ loadingPdf ? 'A gerar...' : 'PDF' }}
          </button>
        </div>
      </div>

      <!-- Período activo -->
      <p v-if="dados" class="text-xs text-zinc-600 mt-3">
        De <span class="text-zinc-400">{{ dataInicio }}</span>
        até <span class="text-zinc-400">{{ dataFim }}</span>
      </p>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-4">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="n in 4" :key="n" class="h-24 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 h-52 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
        <div class="h-52 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
      </div>
    </div>

    <template v-else-if="dados">

      <!-- KPIs vendas ──────────────────────────────────────── -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="kpi in kpis" :key="kpi.label"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">{{ kpi.label }}</p>
          <p class="text-xl sm:text-2xl font-extrabold" :class="kpi.color">{{ kpi.valor }}</p>
          <div v-if="kpi.variacao !== null && kpi.variacao !== undefined"
               :class="['flex items-center gap-1 mt-1 text-xs font-semibold',
                        kpi.variacao >= 0 ? 'text-green-400' : 'text-red-400']">
            <span>{{ kpi.variacao >= 0 ? '↑' : '↓' }}</span>
            <span>{{ Math.abs(kpi.variacao) }}% vs período anterior</span>
          </div>
          <p v-else class="text-xs text-zinc-600 mt-1">{{ kpi.sub || '' }}</p>
        </div>
      </div>

      <!-- Gráfico + Por estado ──────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <div class="lg:col-span-2 bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Vendas no período
          </h3>
          <div v-if="!dados.grafico_vendas.length"
               class="flex items-center justify-center h-40 text-zinc-600 text-sm">
            Sem vendas concluídas neste período
          </div>
          <div v-else class="relative h-40">
            <svg class="w-full h-full" :viewBox="`0 0 ${svgW} ${svgH}`" preserveAspectRatio="none">
              <line v-for="i in 4" :key="i"
                :x1="0" :y1="svgH / 4 * i" :x2="svgW" :y2="svgH / 4 * i"
                stroke="#27272a" stroke-width="1" />
              <path :d="areaPath" fill="rgba(239,68,68,0.1)" />
              <path :d="linePath" fill="none" stroke="#ef4444" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round" />
              <circle v-for="(pt, i) in chartPoints" :key="i"
                :cx="pt.x" :cy="pt.y" r="3" fill="#ef4444" />
            </svg>
            <div class="flex justify-between mt-2 text-[10px] text-zinc-600">
              <span>{{ fmtDia(dados.grafico_vendas[0]?.dia) }}</span>
              <span>{{ fmtDia(dados.grafico_vendas[Math.floor(dados.grafico_vendas.length/2)]?.dia) }}</span>
              <span>{{ fmtDia(dados.grafico_vendas[dados.grafico_vendas.length-1]?.dia) }}</span>
            </div>
          </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Por estado</h3>
          <div class="space-y-2.5">
            <div v-for="(val, key) in dados.por_estado" :key="key"
                 class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full flex-shrink-0"
                     :style="{ background: estadoCor(key) }"></div>
                <span class="text-xs text-zinc-400 capitalize">{{ key }}</span>
              </div>
              <span class="text-xs font-bold text-zinc-200">{{ val }}</span>
            </div>
          </div>
          <div class="mt-4 flex justify-center">
            <svg viewBox="0 0 80 80" class="w-20 h-20">
              <circle v-for="(seg, i) in donutSegments" :key="i"
                cx="40" cy="40" r="30" fill="none"
                :stroke="seg.cor" stroke-width="10"
                :stroke-dasharray="`${seg.dash} ${188.5 - seg.dash}`"
                :stroke-dashoffset="seg.offset"
                transform="rotate(-90 40 40)" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Entregas ─────────────────────────────────────────── -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
          Entregas
        </h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div class="text-center p-3 bg-zinc-800/60 rounded-xl">
            <p class="text-2xl font-extrabold text-zinc-100">{{ dados.entregas_periodo }}</p>
            <p class="text-xs text-zinc-500 mt-1">no período</p>
          </div>
          <div class="text-center p-3 bg-zinc-800/60 rounded-xl">
            <p class="text-2xl font-extrabold text-green-400">{{ dados.entregas_concluidas }}</p>
            <p class="text-xs text-zinc-500 mt-1">entregues</p>
          </div>
          <div class="text-center p-3 bg-zinc-800/60 rounded-xl">
            <p class="text-2xl font-extrabold text-red-400">{{ dados.entregas_falhadas }}</p>
            <p class="text-xs text-zinc-500 mt-1">falhadas</p>
          </div>
          <div class="text-center p-3 bg-zinc-800/60 rounded-xl">
            <p class="text-2xl font-extrabold text-blue-400">{{ dados.taxa_entrega }}%</p>
            <p class="text-xs text-zinc-500 mt-1">taxa sucesso</p>
          </div>
        </div>

        <!-- Estado actual das entregas -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div v-for="(val, key) in dados.entregas_por_status" :key="key"
               class="flex items-center justify-between px-3 py-2 bg-zinc-800/40 rounded-lg">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0"
                   :style="{ background: entregaCor(key) }"></div>
              <span class="text-xs text-zinc-400 capitalize">{{ entregaLabel(key) }}</span>
            </div>
            <span class="text-xs font-bold text-zinc-200">{{ val }}</span>
          </div>
        </div>
      </div>

      <!-- Top produtos + Stock ──────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Produtos mais vendidos
          </h3>
          <div v-if="!dados.produtos_top.length"
               class="text-center py-6 text-zinc-600 text-sm">Sem vendas neste período</div>
          <div v-else class="space-y-3">
            <div v-for="(p, i) in dados.produtos_top" :key="p.id"
                 class="flex items-center gap-3">
              <span class="text-xs font-bold text-zinc-600 w-4 flex-shrink-0">{{ i + 1 }}</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-zinc-200 truncate">{{ p.nome }}</p>
                <div class="mt-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div class="h-full bg-red-500 rounded-full"
                       :style="{ width: barWidth(p.qty) + '%' }"></div>
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <p class="text-xs font-bold text-zinc-200">{{ p.qty }} un.</p>
                <p class="text-[10px] text-zinc-500">{{ fmt(p.valor) }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            Stock em alerta
            <span v-if="dados.stock_alerta_count > 0"
                  class="px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 text-[10px] rounded font-bold">
              {{ dados.stock_alerta_count }}
            </span>
          </h3>
          <div v-if="!dados.stock_baixo.length"
               class="flex flex-col items-center justify-center py-6 text-zinc-600 text-sm">
            <span class="text-2xl mb-2">✓</span>
            Todo o stock está OK
          </div>
          <div v-else class="space-y-2">
            <div v-for="s in dados.stock_baixo" :key="s.id"
                 class="flex items-center justify-between px-3 py-2 bg-yellow-500/5
                        border border-yellow-500/20 rounded-xl">
              <p class="text-sm text-zinc-300 truncate flex-1 min-w-0">{{ s.nome }}</p>
              <span :class="['text-xs font-bold px-2 py-0.5 rounded ml-2 flex-shrink-0',
                             s.qty === 0 ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400']">
                {{ s.qty === 0 ? 'Esgotado' : `${s.qty} un.` }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Encomendas recentes ───────────────────────────────── -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
          Encomendas recentes
        </h3>
        <div v-if="!encomendas.length"
             class="text-center py-6 text-zinc-600 text-sm">Sem encomendas ainda.</div>
        <div v-else class="space-y-2">
          <div v-for="enc in encomendas" :key="enc.id"
               class="flex items-center justify-between p-3 bg-zinc-800/50 rounded-xl flex-wrap gap-2">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-700 flex items-center justify-center
                          text-xs font-bold text-zinc-400 flex-shrink-0">
                #{{ enc.id }}
              </div>
              <div>
                <p class="text-sm font-medium text-zinc-200">{{ enc.comprador_username }}</p>
                <p class="text-xs text-zinc-500">{{ fmtData(enc.data_criacao) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
              <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase',
                             statusColor(enc.status)]">{{ enc.status }}</span>
              <span class="text-sm font-bold text-red-400">{{ fmt(enc.valor_total) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Financeiro + Avaliações ───────────────────────────── -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Comissões no período</p>
          <p class="text-xl font-extrabold text-orange-400">{{ fmt(dados.comissao_periodo) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Comissões pendentes</p>
          <p class="text-xl font-extrabold text-yellow-400">{{ fmt(dados.comissao_pendente) }}</p>
          <p class="text-xs text-zinc-600 mt-1">a liquidar</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Comissões liquidadas</p>
          <p class="text-xl font-extrabold text-green-400">{{ fmt(dados.comissao_liquidada) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Rating médio</p>
          <div class="flex items-baseline gap-1 mt-1">
            <p class="text-xl font-extrabold text-yellow-400">
              {{ dados.rating_medio ? dados.rating_medio.toFixed(1) : '—' }}
            </p>
            <span class="text-yellow-400">★</span>
          </div>
          <p class="text-xs text-zinc-600 mt-1">
            {{ dados.total_avaliacoes }} total · {{ dados.avaliacoes_recentes }} novas
          </p>
        </div>
      </div>

    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { usePdfRelatorio } from '@/composables/usePdfRelatorio'

export default {
  name: 'BackofficeDashboard',
  props: { lojaId: [String, Number] },

  data () {
    const hoje = new Date()
    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
    return {
      loading:      true,
      dados:        null,
      encomendas:   [],
      dataInicio:   this.fmtDate(inicioMes),
      dataFim:      this.fmtDate(hoje),
      atalhoActivo: 'Este mês',
      svgW: 400,
      svgH: 140,
      loadingPdf:   false,
      atalhos: [
        { label: 'Hoje',        dias: 0           },
        { label: 'Últimos 7d',  dias: 7           },
        { label: 'Últimos 30d', dias: 30          },
        { label: 'Este mês',    mesActual: true   },
        { label: 'Este ano',    anoActual: true   },
      ],
    }
  },

  computed: {
    kpis () {
      if (!this.dados) return []
      const d = this.dados
      return [
        { label: 'Vendas',         valor: this.fmt(d.total_vendas), color: 'text-red-400',   variacao: d.variacao_vendas },
        { label: 'Encomendas',     valor: d.total_encomendas,       color: 'text-blue-400',  variacao: d.variacao_enc    },
        { label: 'Taxa conclusão', valor: `${d.taxa_conclusao}%`,   color: 'text-green-400', sub: `${d.enc_concluidas} concluídas` },
        { label: 'Canceladas',     valor: d.enc_canceladas,         color: 'text-zinc-400',  sub: 'neste período' },
      ]
    },

    chartPoints () {
      const g = this.dados?.grafico_vendas || []
      if (!g.length) return []
      const max = Math.max(...g.map(d => d.total), 1)
      return g.map((d, i) => ({
        x: (i / (g.length - 1 || 1)) * this.svgW,
        y: this.svgH - (d.total / max) * this.svgH * 0.85,
      }))
    },

    linePath () {
      const pts = this.chartPoints
      if (!pts.length) return ''
      return pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
    },

    areaPath () {
      const pts = this.chartPoints
      if (!pts.length) return ''
      const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
      return `${line} L${this.svgW},${this.svgH} L0,${this.svgH} Z`
    },

    donutSegments () {
      if (!this.dados) return []
      const estados = this.dados.por_estado
      const total   = Object.values(estados).reduce((s, v) => s + v, 0) || 1
      const cores   = {
        pendente: '#eab308', pago: '#3b82f6', preparando: '#a855f7',
        enviado: '#6366f1', concluido: '#22c55e', cancelado: '#ef4444',
      }
      const circum = 188.5
      let offset = 0
      return Object.entries(estados).map(([key, val]) => {
        const dash = (val / total) * circum
        const seg  = { cor: cores[key] || '#71717a', dash, offset: -offset }
        offset += dash
        return seg
      })
    },
  },

  async created () {
    await Promise.all([this.fetchDados(), this.fetchEncomendas()])
  },

  methods: {
    fmtDate (d) {
      return d.toISOString().split('T')[0]
    },

    fmt (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },

    fmtDia (dia) {
      if (!dia) return ''
      const d = new Date(dia)
      return `${d.getDate()}/${d.getMonth() + 1}`
    },

    fmtData (d) {
      return new Date(d).toLocaleDateString('pt-PT')
    },

    estadoCor (estado) {
      const map = {
        pendente: '#eab308', pago: '#3b82f6', preparando: '#a855f7',
        enviado: '#6366f1', concluido: '#22c55e', cancelado: '#ef4444',
      }
      return map[estado] || '#71717a'
    },

    entregaCor (status) {
      const map = {
        atribuido: '#3b82f6', a_caminho: '#6366f1',
        entregue: '#22c55e', falhou: '#ef4444',
      }
      return map[status] || '#71717a'
    },

    entregaLabel (status) {
      const map = {
        atribuido: 'Atribuído', a_caminho: 'A caminho',
        entregue: 'Entregue', falhou: 'Falhou',
      }
      return map[status] || status
    },

    statusColor (s) {
      const map = {
        pendente:  'bg-yellow-500/15 text-yellow-400',
        pago:      'bg-blue-500/15 text-blue-400',
        preparando:'bg-purple-500/15 text-purple-400',
        enviado:   'bg-indigo-500/15 text-indigo-400',
        concluido: 'bg-green-500/15 text-green-400',
        cancelado: 'bg-red-500/15 text-red-400',
      }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },

    barWidth (qty) {
      const max = Math.max(...(this.dados?.produtos_top || []).map(p => p.qty), 1)
      return (qty / max) * 100
    },

    aplicarAtalho (atalho) {
      this.atalhoActivo = atalho.label
      const hoje = new Date()
      if (atalho.dias === 0) {
        this.dataInicio = this.fmtDate(hoje)
        this.dataFim    = this.fmtDate(hoje)
      } else if (atalho.dias) {
        const inicio = new Date(hoje)
        inicio.setDate(hoje.getDate() - atalho.dias)
        this.dataInicio = this.fmtDate(inicio)
        this.dataFim    = this.fmtDate(hoje)
      } else if (atalho.mesActual) {
        this.dataInicio = this.fmtDate(new Date(hoje.getFullYear(), hoje.getMonth(), 1))
        this.dataFim    = this.fmtDate(hoje)
      } else if (atalho.anoActual) {
        this.dataInicio = this.fmtDate(new Date(hoje.getFullYear(), 0, 1))
        this.dataFim    = this.fmtDate(hoje)
      }
      this.fetchDados()
    },

    aplicarDatas () {
      this.atalhoActivo = ''
      this.fetchDados()
    },

    async fetchDados () {
      this.loading = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/dashboard/`, {
          params: { data_inicio: this.dataInicio, data_fim: this.dataFim }
        })
        this.dados = data
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },

    async exportarPdf () {
      this.loadingPdf = true
      const { gerarPdfLoja } = usePdfRelatorio()
      const nomeLoja = this.$route?.params?.nomeLoja || `Loja ${this.lojaId}`
      const periodo  = `${this.dataInicio} a ${this.dataFim}`
      try {
        await gerarPdfLoja(this.dados, nomeLoja, periodo)
      } catch (e) {
        console.error('Erro ao gerar PDF:', e)
      } finally {
        this.loadingPdf = false
      }
    },

    async fetchEncomendas () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/encomendas/`, {
          params: { limit: 8 }
        })
        this.encomendas = data.results || data
      } catch (e) {
        console.error(e)
      }
    },
  },
}
</script>