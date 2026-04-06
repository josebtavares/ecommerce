<template>
  <div class="space-y-6">

    <!-- Filtros ──────────────────────────────────────────── -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
      <div class="flex flex-wrap gap-3 items-end">

        <!-- Atalhos de período -->
        <div class="flex gap-1 flex-wrap">
          <button v-for="atalho in atalhos" :key="atalho.label"
            @click="aplicarAtalho(atalho)"
            :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                     atalhoActivo === atalho.label
                       ? 'bg-red-600 text-white'
                       : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
            {{ atalho.label }}
          </button>
        </div>

        <!-- Datas personalizadas -->
        <div class="flex items-center gap-2 flex-wrap">
          <div class="flex flex-col gap-1">
            <label class="text-[10px] text-zinc-500 uppercase tracking-wider">De</label>
            <input type="date" v-model="dataInicio"
              class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-[10px] text-zinc-500 uppercase tracking-wider">Até</label>
            <input type="date" v-model="dataFim"
              class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200
                     focus:outline-none focus:border-red-500 transition" />
          </div>
        </div>

        <!-- Filtro por loja -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] text-zinc-500 uppercase tracking-wider">Loja</label>
          <select v-model="lojaId"
            class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200
                   focus:outline-none focus:border-red-500 transition min-w-[160px]">
            <option value="">Todas as lojas</option>
            <option v-for="l in lojas" :key="l.id" :value="l.id">{{ l.nome }}</option>
          </select>
        </div>

        <!-- Botão pesquisar -->
        <button @click="fetchRelatorio"
          :disabled="loading"
          class="px-5 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded-xl
                 transition disabled:opacity-50 flex items-center gap-2">
          <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
            <path fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" class="opacity-75"/>
          </svg>
          {{ loading ? 'A carregar...' : 'Aplicar' }}
        </button>

        <!-- Exportar CSV -->
        <button v-if="dados" @click="exportarCSV"
          class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-semibold
                 rounded-xl transition flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          CSV
        </button>
      </div>

      <!-- Período activo -->
      <p v-if="dados" class="text-xs text-zinc-600 mt-3">
        A mostrar dados de <span class="text-zinc-400">{{ dataInicio }}</span>
        até <span class="text-zinc-400">{{ dataFim }}</span>
        <span v-if="lojaId" class="ml-1">· <span class="text-red-400">{{ lojaNomeActivo }}</span></span>
      </p>
    </div>

    <!-- Estado vazio -->
    <div v-if="!dados && !loading"
         class="flex flex-col items-center justify-center py-16 text-zinc-600 text-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mb-3 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      Selecciona um período e clica em Aplicar
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-4">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="n in 4" :key="n" class="h-24 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
      </div>
      <div class="h-48 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
    </div>

    <template v-if="dados && !loading">

      <!-- KPIs ─────────────────────────────────────────────── -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="kpi in kpis" :key="kpi.label"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">{{ kpi.label }}</p>
          <p class="text-xl sm:text-2xl font-extrabold" :class="kpi.color">{{ kpi.valor }}</p>
          <p v-if="kpi.sub" class="text-xs text-zinc-600 mt-1">{{ kpi.sub }}</p>
        </div>
      </div>

      <!-- Gráfico + Por estado ──────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Gráfico vendas por dia -->
        <div class="lg:col-span-2 bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Vendas por dia
          </h3>
          <div v-if="dados.grafico.length === 0"
               class="flex items-center justify-center h-40 text-zinc-600 text-sm">
            Sem vendas concluídas neste período
          </div>
          <div v-else class="relative h-44">
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
            <!-- Labels eixo X -->
            <div class="flex justify-between mt-1 text-[10px] text-zinc-600 px-1">
              <span>{{ fmtDia(dados.grafico[0]?.dia) }}</span>
              <span>{{ fmtDia(dados.grafico[Math.floor(dados.grafico.length/2)]?.dia) }}</span>
              <span>{{ fmtDia(dados.grafico[dados.grafico.length-1]?.dia) }}</span>
            </div>
          </div>
        </div>

        <!-- Encomendas por estado -->
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
          <!-- Donut -->
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

      <!-- Comissões ─────────────────────────────────────────── -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Comissões geradas</p>
          <p class="text-2xl font-extrabold text-red-400">{{ fmt(dados.comissoes_geradas) }}</p>
          <p class="text-xs text-zinc-600 mt-1">neste período</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Liquidadas</p>
          <p class="text-2xl font-extrabold text-green-400">{{ fmt(dados.comissoes_liquidadas) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">Pendentes</p>
          <p class="text-2xl font-extrabold text-yellow-400">{{ fmt(dados.comissoes_pendentes) }}</p>
          <p class="text-xs text-zinc-600 mt-1">a liquidar</p>
        </div>
      </div>

      <!-- Top lojas + Top produtos ──────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Top lojas (só quando não filtrado por loja) -->
        <div v-if="!lojaId" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Top lojas
          </h3>
          <div v-if="dados.lojas_top.length === 0"
               class="text-center py-6 text-zinc-600 text-sm">
            Sem vendas neste período
          </div>
          <div v-else class="space-y-3">
            <div v-for="(l, i) in dados.lojas_top" :key="l.id"
                 class="flex items-center gap-3">
              <span class="text-xs font-bold text-zinc-600 w-5 flex-shrink-0">{{ i + 1 }}</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-zinc-200 truncate">{{ l.nome }}</p>
                <div class="mt-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div class="h-full bg-red-500 rounded-full transition-all"
                       :style="{ width: barPct(l.total, dados.lojas_top, 'total') + '%' }"></div>
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <p class="text-xs font-bold text-zinc-200">{{ fmt(l.total) }}</p>
                <p class="text-[10px] text-zinc-500">{{ l.count }} enc.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Top produtos -->
        <div :class="lojaId ? 'lg:col-span-2' : ''"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Top produtos
          </h3>
          <div v-if="dados.produtos_top.length === 0"
               class="text-center py-6 text-zinc-600 text-sm">
            Sem vendas neste período
          </div>
          <div v-else class="space-y-3">
            <div v-for="(p, i) in dados.produtos_top" :key="p.id"
                 class="flex items-center gap-3">
              <span class="text-xs font-bold text-zinc-600 w-5 flex-shrink-0">{{ i + 1 }}</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-zinc-200 truncate">{{ p.nome }}</p>
                <div class="mt-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div class="h-full bg-blue-500 rounded-full transition-all"
                       :style="{ width: barPct(p.qty, dados.produtos_top, 'qty') + '%' }"></div>
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <p class="text-xs font-bold text-zinc-200">{{ p.qty }} un.</p>
                <p class="text-[10px] text-zinc-500">{{ fmt(p.total) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Avaliações -->
      <div v-if="dados.total_avaliacoes > 0 || dados.rating_medio"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 flex items-center gap-6">
        <div class="text-center flex-shrink-0">
          <p class="text-4xl font-extrabold text-yellow-400">
            {{ dados.rating_medio ? dados.rating_medio.toFixed(1) : '—' }}
          </p>
          <p class="text-yellow-400 text-lg">★★★★★</p>
          <p class="text-xs text-zinc-500 mt-1">rating médio</p>
        </div>
        <div class="h-12 w-px bg-zinc-800 flex-shrink-0"></div>
        <div>
          <p class="text-2xl font-extrabold text-zinc-100">{{ dados.total_avaliacoes }}</p>
          <p class="text-xs text-zinc-500">avaliações neste período</p>
        </div>
      </div>

    </template>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AdminRelatorios',

  data () {
    const hoje = new Date()
    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
    return {
      loading:      false,
      dados:        null,
      dataInicio:   this.fmtDate(inicioMes),
      dataFim:      this.fmtDate(hoje),
      lojaId:       '',
      lojas:        [],
      atalhoActivo: 'Este mês',
      svgW:         400,
      svgH:         160,
      atalhos: [
        { label: 'Hoje',       dias: 0  },
        { label: 'Últimos 7d', dias: 7  },
        { label: 'Últimos 30d',dias: 30 },
        { label: 'Este mês',   mesActual: true },
        { label: 'Este ano',   anoActual: true },
      ],
    }
  },

  computed: {
    lojaNomeActivo () {
      const l = this.lojas.find(l => l.id == this.lojaId)
      return l?.nome || ''
    },

    kpis () {
      if (!this.dados) return []
      const d = this.dados
      return [
        { label: 'GMV',              valor: this.fmt(d.gmv),          color: 'text-red-400',   sub: 'vendas concluídas' },
        { label: 'Encomendas',       valor: d.total_encomendas,       color: 'text-blue-400',  sub: `${d.enc_concluidas} concluídas · ${d.enc_canceladas} canceladas` },
        { label: 'Taxa conclusão',   valor: `${d.taxa_conclusao}%`,   color: 'text-green-400', sub: 'encomendas concluídas' },
        { label: 'Comissões',        valor: this.fmt(d.comissoes_geradas), color: 'text-orange-400', sub: 'geradas no período' },
      ]
    },

    chartPoints () {
      const dados = this.dados?.grafico || []
      if (!dados.length) return []
      const max = Math.max(...dados.map(d => d.total), 1)
      return dados.map((d, i) => ({
        x: (i / (dados.length - 1 || 1)) * this.svgW,
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
    await this.fetchLojas()
    await this.fetchRelatorio()
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

    estadoCor (estado) {
      const map = {
        pendente: '#eab308', pago: '#3b82f6', preparando: '#a855f7',
        enviado: '#6366f1', concluido: '#22c55e', cancelado: '#ef4444',
      }
      return map[estado] || '#71717a'
    },

    barPct (val, lista, campo) {
      const max = Math.max(...lista.map(i => i[campo]), 1)
      return (val / max) * 100
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
      this.fetchRelatorio()
    },

    async fetchLojas () {
      try {
        const { data } = await api.get('/app/admin/lojas/', { params: { limit: 200 } })
        this.lojas = (data.results || data).map(l => ({ id: l.id, nome: l.nome }))
      } catch (e) { console.error(e) }
    },

    async fetchRelatorio () {
      this.loading = true
      try {
        const params = { data_inicio: this.dataInicio, data_fim: this.dataFim }
        if (this.lojaId) params.loja_id = this.lojaId
        const { data } = await api.get('/app/admin/relatorios/', { params })
        this.dados = data
        // actualiza lista de lojas se veio na resposta
        if (data.lojas_lista?.length) this.lojas = data.lojas_lista
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    exportarCSV () {
      if (!this.dados) return
      const linhas = [
        ['Relatório', `${this.dataInicio} a ${this.dataFim}`],
        [],
        ['KPI', 'Valor'],
        ['GMV', this.dados.gmv],
        ['Total encomendas', this.dados.total_encomendas],
        ['Concluídas', this.dados.enc_concluidas],
        ['Canceladas', this.dados.enc_canceladas],
        ['Taxa conclusão', `${this.dados.taxa_conclusao}%`],
        ['Comissões geradas', this.dados.comissoes_geradas],
        ['Comissões liquidadas', this.dados.comissoes_liquidadas],
        ['Comissões pendentes', this.dados.comissoes_pendentes],
        [],
        ['Dia', 'Vendas (€)', 'Nº encomendas'],
        ...this.dados.grafico.map(g => [g.dia, g.total, g.count]),
      ]

      if (this.dados.lojas_top.length) {
        linhas.push([], ['Loja', 'Vendas (€)', 'Encomendas'])
        this.dados.lojas_top.forEach(l => linhas.push([l.nome, l.total, l.count]))
      }

      if (this.dados.produtos_top.length) {
        linhas.push([], ['Produto', 'Quantidade', 'Total (€)'])
        this.dados.produtos_top.forEach(p => linhas.push([p.nome, p.qty, p.total]))
      }

      const csv = linhas.map(r => r.join(',')).join('\n')
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `relatorio_${this.dataInicio}_${this.dataFim}.csv`
      a.click()
      URL.revokeObjectURL(url)
    },
  },
}
</script>