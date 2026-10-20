<template>
  <div class="space-y-6">

    <!-- Período ───────────────────────────────────────────── -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
      <FiltroPeriodo padrao="mes" :carregando="loading" @mudar="mudarPeriodo">
        <button v-if="dados" @click="exportarPdf" :disabled="loadingPdf"
          class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-semibold
                 rounded-xl transition flex items-center gap-2 disabled:opacity-50">
          <font-awesome-icon :icon="['fas', loadingPdf ? 'spinner' : 'download']" :class="loadingPdf ? 'animate-spin' : ''" />
          {{ loadingPdf ? 'A gerar...' : 'PDF' }}
        </button>
      </FiltroPeriodo>
      <p v-if="dados" class="text-xs text-zinc-600 mt-3">
        {{ dataCurta(dataInicio) }} a {{ dataCurta(dataFim) }} · vendas pela data de conclusão, encomendas pela data em que foram feitas
      </p>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !dados" class="space-y-4">
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
      <div class="grid grid-cols-2 lg:grid-cols-3 gap-4" :class="loading ? 'opacity-60' : ''">
        <div v-for="kpi in kpis" :key="kpi.label"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500 mb-1">{{ kpi.label }}</p>
          <p class="text-xl sm:text-2xl font-extrabold" :class="kpi.color">{{ kpi.valor }}</p>
          <div v-if="kpi.variacao !== null && kpi.variacao !== undefined"
               :class="['flex items-center gap-1 mt-1 text-xs font-semibold',
                        kpi.variacao >= 0 ? 'text-green-400' : 'text-red-400']">
            <font-awesome-icon :icon="['fas', kpi.variacao >= 0 ? 'arrow-trend-up' : 'arrow-trend-down']" />
            <span>{{ Math.abs(kpi.variacao) }}% vs período anterior</span>
          </div>
          <p v-else class="text-xs text-zinc-600 mt-1">{{ kpi.sub || '' }}</p>
        </div>
      </div>

      <!-- Gráfico + Por estado ──────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <div class="lg:col-span-2 bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <GraficoTempo titulo="Vendas no período" subtitulo="pela data de conclusão; devoluções abaixo do zero"
                        :dados="dados.grafico_vendas" :granularidade="dados.granularidade || 'dia'"
                        :series="[{ chave: 'vendas', label: 'Vendas', cor: COR_1 }, { chave: 'devolucoes', label: 'Devoluções', cor: COR_2, negativo: true }]"
                        chave-total="total" label-total="Líquido" vazio="Sem vendas concluídas neste período" />
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
                <!-- unidades que saíram dentro de menus/conjuntos -->
                <p v-if="p.qty_conjuntos" class="text-[10px] text-sky-400">{{ p.qty_conjuntos }} em conjuntos</p>
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
            <font-awesome-icon :icon="['fas', 'circle-check']" class="text-2xl mb-2 text-green-500/70" />
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

      <!-- Bendi + Recebimentos + Avaliações ──────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- o que a loja paga à Bendi -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">Custos com a Bendi</h3>
          <template v-if="dados.cobranca?.modelo === 'subscricao'">
            <p class="text-xs text-zinc-500">Subscrição</p>
            <p class="text-lg font-extrabold text-zinc-100">{{ dados.cobranca.subscricao?.plano || '—' }}</p>
            <p v-if="dados.cobranca.subscricao" class="text-xs text-zinc-500 mt-0.5">
              {{ fmt(dados.cobranca.subscricao.preco) }} / {{ dados.cobranca.subscricao.meses === 1 ? 'mês' : dados.cobranca.subscricao.meses + ' meses' }}
              · {{ dados.cobranca.subscricao.estado_nome }} · pago até {{ dataCurta(dados.cobranca.subscricao.pago_ate) }}
            </p>
            <div class="mt-3 space-y-1.5 text-sm">
              <p class="flex justify-between"><span class="text-zinc-400">Faturas pagas no período</span><span class="font-semibold text-zinc-200 tabular-nums">{{ fmt(dados.cobranca.faturas_pagas) }}</span></p>
              <p v-if="dados.cobranca.proxima_fatura" class="flex justify-between">
                <span class="text-zinc-400">{{ dados.cobranca.proxima_fatura.em_atraso ? 'Fatura em atraso' : 'Próxima fatura' }}</span>
                <span :class="['font-semibold tabular-nums', dados.cobranca.proxima_fatura.em_atraso ? 'text-red-400' : 'text-zinc-200']">
                  {{ fmt(dados.cobranca.proxima_fatura.valor) }} · {{ dataCurta(dados.cobranca.proxima_fatura.vencimento) }}
                </span>
              </p>
              <p v-if="dados.comissao_pendente" class="flex justify-between"><span class="text-zinc-400">Comissões antigas por liquidar</span><span class="font-semibold text-yellow-400 tabular-nums">{{ fmt(dados.comissao_pendente) }}</span></p>
            </div>
          </template>
          <template v-else>
            <p class="text-xs text-zinc-500">Comissão de {{ Number(dados.cobranca?.percentagem || 0).toLocaleString('pt-PT') }}% por venda</p>
            <p class="text-lg font-extrabold text-orange-400 tabular-nums">{{ fmt(dados.comissao_periodo) }}</p>
            <p class="text-xs text-zinc-500 mt-0.5">no período</p>
            <div class="mt-3 space-y-1.5 text-sm">
              <p class="flex justify-between"><span class="text-zinc-400">Por liquidar</span><span class="font-semibold text-yellow-400 tabular-nums">{{ fmt(dados.comissao_pendente) }}</span></p>
              <p class="flex justify-between"><span class="text-zinc-400">Liquidadas (total)</span><span class="font-semibold text-green-400 tabular-nums">{{ fmt(dados.comissao_liquidada) }}</span></p>
              <p v-if="dados.credito_comissao" class="flex justify-between"><span class="text-zinc-400">Crédito a teu favor</span><span class="font-semibold text-sky-400 tabular-nums">{{ fmt(dados.credito_comissao) }}</span></p>
            </div>
          </template>
        </div>

        <!-- recebimentos por método -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1">Recebimentos</h3>
          <p class="text-xs text-zinc-600 mb-3">pela data do pagamento</p>
          <p v-if="!dados.recebimentos?.por_metodo?.length" class="text-sm text-zinc-600">Sem pagamentos no período</p>
          <div v-else class="space-y-2.5">
            <div v-for="m in dados.recebimentos.por_metodo" :key="m.metodo">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-zinc-300">{{ m.nome }} <span class="text-zinc-600">· {{ m.count }}</span></span>
                <span class="text-zinc-200 font-semibold tabular-nums">{{ fmt(m.valor) }}</span>
              </div>
              <div class="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div class="h-full rounded-full" :style="{ width: Math.max(2, (Number(m.valor) / (Number(dados.recebimentos.total) || 1)) * 100) + '%', background: COR_1 }"></div>
              </div>
            </div>
            <p class="flex justify-between text-sm border-t border-zinc-800 pt-2">
              <span class="text-zinc-400">Total</span><span class="font-bold text-zinc-100 tabular-nums">{{ fmt(dados.recebimentos.total) }}</span>
            </p>
          </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">Avaliações</h3>
          <div class="flex items-baseline gap-1">
            <p class="text-3xl font-extrabold text-yellow-400">
              {{ dados.rating_medio ? dados.rating_medio.toFixed(1) : '—' }}
            </p>
            <font-awesome-icon :icon="['fas', 'star']" class="text-yellow-400 w-4 h-4" />
          </div>
          <p class="text-xs text-zinc-500 mt-1">
            {{ dados.total_avaliacoes }} no total · {{ dados.avaliacoes_recentes }} novas no período
          </p>
        </div>
      </div>


    </template>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { usePdfRelatorio } from '@/composables/usePdfRelatorio'
import FiltroPeriodo from '@/components/relatorios/FiltroPeriodo.vue'
import GraficoTempo from '@/components/relatorios/GraficoTempo.vue'
import { intervaloAtalho, dataCurta } from '@/utils/periodos'

export default {
  name: 'BackofficeDashboard',
  props: { lojaId: [String, Number] },
  components: { FiltroPeriodo, GraficoTempo },

  data () {
    const mes = intervaloAtalho('mes')
    return {
      loading:      true,
      dados:        null,
      encomendas:   [],
      dataInicio:   mes.inicio,
      dataFim:      mes.fim,
      loadingPdf:   false,
      COR_1: '#3987e5', COR_2: '#d95926',     // séries (validadas para o fundo escuro)
    }
  },

  computed: {
    kpis () {
      if (!this.dados) return []
      const d = this.dados
      return [
        // vendas já sem o que foi reembolsado (backend utils/devolucoes.anotar_liquido)
        { label: 'Vendas',         valor: this.fmt(d.total_vendas), color: 'text-red-400',   variacao: d.variacao_vendas,
          sub: d.vendas_devolucoes || d.vendas_ajustes ? `líquidas · brutas ${this.fmt(d.vendas_brutas)}` : '' },
        { label: 'Encomendas',     valor: d.total_encomendas,       color: 'text-blue-400',  variacao: d.variacao_enc    },
        { label: 'Taxa conclusão', valor: `${d.taxa_conclusao}%`,   color: 'text-green-400', sub: `${d.enc_concluidas} concluídas · ${d.enc_canceladas} canceladas` },
        { label: 'Reembolsos',     valor: this.fmt(d.reembolsos_periodo || 0), color: 'text-sky-400',
          sub: `${d.reembolsos_count || 0} no período` + (d.reembolsos_por_responder ? ` · ${d.reembolsos_por_responder} por responder` : '') },
        { label: 'Recebimentos',   valor: this.fmt(d.recebimentos?.total || 0), color: 'text-zinc-100',
          sub: `${d.recebimentos?.count || 0} pagamentos recebidos` },
        { label: 'Ticket médio',   valor: this.fmt(d.ticket_medio || 0), color: 'text-zinc-100',
          sub: `${d.vendas_concluidas || 0} encomendas concluídas` },
      ]
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
    dataCurta,

    fmt (val) {
      return formatarDinheiro(val || 0)
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

    mudarPeriodo ({ inicio, fim }) {
      this.dataInicio = inicio
      this.dataFim    = fim
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