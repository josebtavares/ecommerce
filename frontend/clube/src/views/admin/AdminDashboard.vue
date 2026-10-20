<template>
  <div class="space-y-6">

    <!-- Período -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
      <FiltroPeriodo padrao="mes" :carregando="loading" @mudar="carregar" />
      <p v-if="d" class="text-xs text-zinc-600 mt-3">
        {{ dataCurta(d.periodo.inicio) }} a {{ dataCurta(d.periodo.fim) }} · comparado com
        {{ dataCurta(d.periodo_anterior.inicio) }} a {{ dataCurta(d.periodo_anterior.fim) }}
      </p>
    </div>

    <p v-if="erro" class="text-sm text-red-400">{{ erro }}</p>

    <div v-if="loading && !d" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="n in 8" :key="n" class="h-28 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <template v-else-if="d">
      <!-- Alertas: o que precisa de alguém -->
      <div v-if="alertas.length" class="flex flex-wrap gap-2">
        <button v-for="a in alertas" :key="a.texto" type="button" @click="$emit('ir', a.seccao)"
                class="flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold transition hover:brightness-125"
                :class="a.cor">
          <font-awesome-icon :icon="['fas', a.icon]" />{{ a.texto }}
          <font-awesome-icon :icon="['fas', 'arrow-right']" class="opacity-60" />
        </button>
      </div>

      <!-- KPIs -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4" :class="loading ? 'opacity-60' : ''">
        <div v-for="k in kpis" :key="k.label" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" :class="k.cor">
              <font-awesome-icon :icon="['fas', k.icon]" class="w-3.5 h-3.5" />
            </span>
            <p class="text-xs text-zinc-500 leading-tight">{{ k.label }}</p>
          </div>
          <p class="text-xl sm:text-2xl font-extrabold text-zinc-100 tabular-nums break-all">{{ k.valor }}</p>
          <p v-if="k.variacao !== undefined && k.variacao !== null"
             :class="['flex items-center gap-1 mt-1 text-xs font-semibold', k.variacao >= 0 ? 'text-green-400' : 'text-red-400']">
            <font-awesome-icon :icon="['fas', k.variacao >= 0 ? 'arrow-trend-up' : 'arrow-trend-down']" />
            {{ Math.abs(k.variacao) }}% vs anterior
          </p>
          <p v-if="k.sub" class="text-[11px] text-zinc-500 mt-1 leading-snug">{{ k.sub }}</p>
        </div>
      </div>

      <!-- Gráficos -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <GraficoTempo titulo="Receita da plataforma" subtitulo="comissões geradas + subscrições pagas"
                        :dados="d.grafico_receita" :granularidade="d.periodo.granularidade"
                        :series="[{ chave: 'comissoes', label: 'Comissões', cor: COR_1 }, { chave: 'subscricoes', label: 'Subscrições', cor: COR_2 }]"
                        chave-total="total" label-total="Receita (− créditos)" vazio="Sem receita neste período" />
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <GraficoTempo titulo="Vendas das lojas" subtitulo="pela data de conclusão; devoluções abaixo do zero"
                        :dados="d.grafico_vendas" :granularidade="d.periodo.granularidade"
                        :series="[{ chave: 'vendas', label: 'Vendas', cor: COR_1 }, { chave: 'devolucoes', label: 'Devoluções', cor: COR_2, negativo: true }]"
                        chave-total="total" label-total="Líquido" vazio="Sem vendas concluídas neste período" />
        </div>
      </div>

      <!-- Subscrições + Comissões -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Subscrições · hoje</h3>
            <button type="button" @click="$emit('ir', 'subscricoes')" class="text-xs text-zinc-500 hover:text-zinc-300">Ver →</button>
          </div>
          <div class="grid grid-cols-2 gap-3 mb-4">
            <div class="bg-zinc-800/60 rounded-xl p-3">
              <p class="text-[11px] text-zinc-500">Lojas em subscrição</p>
              <p class="text-lg font-bold text-zinc-100">{{ d.subscricoes.lojas.subscricao }}</p>
            </div>
            <div class="bg-zinc-800/60 rounded-xl p-3">
              <p class="text-[11px] text-zinc-500">Lojas em comissão</p>
              <p class="text-lg font-bold text-zinc-100">{{ d.subscricoes.lojas.comissao }}</p>
            </div>
          </div>
          <dl class="space-y-2 text-sm">
            <Linha label="Receita mensal recorrente (MRR)" :valor="$dinheiro(d.subscricoes.mrr)" forte />
            <Linha label="· de lojas" :valor="$dinheiro(d.subscricoes.mrr_lojas)" />
            <Linha label="· de POS" :valor="$dinheiro(d.subscricoes.mrr_pos)" />
            <Linha label="Pagas no período" :valor="`${$dinheiro(d.receita.subscricoes)} · ${d.receita.faturas_pagas} faturas`" />
            <Linha label="A vencer nos próximos 30 dias" :valor="`${$dinheiro(d.subscricoes.proximos_30d.valor)} · ${d.subscricoes.proximos_30d.faturas}`" />
            <Linha label="Em atraso" :valor="`${$dinheiro(d.subscricoes.em_atraso.valor)} · ${d.subscricoes.em_atraso.faturas}`"
                   :cor="d.subscricoes.em_atraso.faturas ? 'text-amber-400' : ''" />
          </dl>
          <div class="flex flex-wrap gap-1.5 mt-4">
            <span v-for="(n, estado) in d.subscricoes.por_estado" :key="estado"
                  class="px-2 py-0.5 rounded-full bg-zinc-800 text-[11px] text-zinc-300">{{ ESTADOS_SUB[estado] || estado }}: <b>{{ n }}</b></span>
            <span class="px-2 py-0.5 rounded-full bg-zinc-800 text-[11px] text-zinc-300">
              POS: <b>{{ d.subscricoes.pos.total }}</b> ({{ d.subscricoes.pos.incluidos }} incluídos · {{ d.subscricoes.pos.sem_plano }} sem plano)
            </span>
          </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Comissões</h3>
            <button type="button" @click="$emit('ir', 'comissoes')" class="text-xs text-zinc-500 hover:text-zinc-300">Ver →</button>
          </div>
          <dl class="space-y-2 text-sm">
            <Linha label="Geradas no período" :valor="$dinheiro(d.comissoes.geradas)" forte />
            <Linha label="Liquidadas no período" :valor="$dinheiro(d.comissoes.liquidadas)" />
            <Linha label="Por liquidar (total)" :valor="$dinheiro(d.comissoes.pendentes)" :cor="Number(d.comissoes.pendentes) ? 'text-amber-400' : ''" />
            <Linha label="Créditos a devolver às lojas" :valor="$dinheiro(d.comissoes.creditos_pendentes)" />
            <Linha label="Créditos criados no período" :valor="$dinheiro(d.receita.creditos)" />
          </dl>

          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mt-6 mb-3">Recebimentos por método</h3>
          <p v-if="!d.recebimentos.por_metodo.length" class="text-sm text-zinc-600">Sem pagamentos no período</p>
          <div v-else class="space-y-2.5">
            <div v-for="m in d.recebimentos.por_metodo" :key="m.metodo">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-zinc-300">{{ m.nome }} <span class="text-zinc-600">· {{ m.count }}</span></span>
                <span class="text-zinc-200 font-semibold tabular-nums">{{ $dinheiro(m.valor) }}</span>
              </div>
              <div class="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div class="h-full rounded-full" :style="{ width: pct(m.valor, d.recebimentos.total) + '%', background: COR_1 }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top lojas -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Lojas com mais vendas</h3>
        <p v-if="!d.lojas_top.length" class="text-sm text-zinc-600">Sem vendas concluídas neste período</p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm min-w-[520px]">
            <thead class="text-[11px] text-zinc-500 uppercase tracking-wider">
              <tr>
                <th class="text-left font-semibold pb-2">Loja</th>
                <th class="text-left font-semibold pb-2">Modelo</th>
                <th class="text-right font-semibold pb-2">Encomendas</th>
                <th class="text-right font-semibold pb-2">Vendas</th>
                <th class="text-right font-semibold pb-2">Receita Bendi</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in d.lojas_top" :key="l.id" class="border-t border-zinc-800">
                <td class="py-2 text-zinc-200 font-medium">{{ l.nome }}</td>
                <td class="py-2 text-zinc-400 text-xs">{{ l.modelo === 'subscricao' ? 'Subscrição' : 'Comissão' }}</td>
                <td class="py-2 text-right text-zinc-300 tabular-nums">{{ l.encomendas }}</td>
                <td class="py-2 text-right text-zinc-100 font-semibold tabular-nums">{{ $dinheiro(l.vendas) }}</td>
                <td class="py-2 text-right text-zinc-300 tabular-nums">{{ $dinheiro(l.receita_bendi) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Encomendas + Plataforma -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1">Encomendas feitas no período</h3>
          <p class="text-xs text-zinc-600 mb-4">estado em que estão hoje</p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div v-for="(n, estado) in d.encomendas.por_estado" :key="estado" class="bg-zinc-800 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-zinc-100">{{ n }}</p>
              <p :class="['text-xs font-semibold mt-1', statusColor(estado)]">{{ ESTADOS_ENC[estado] || estado }}</p>
            </div>
          </div>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Plataforma</h3>
          <dl class="space-y-2 text-sm">
            <Linha label="Lojas ativas" :valor="d.lojas.por_estado.ativa || 0" />
            <Linha label="Lojas pendentes de aprovação" :valor="d.lojas.por_estado.pendente || 0" :cor="d.lojas.por_estado.pendente ? 'text-amber-400' : ''" />
            <Linha label="Lojas fechadas / suspensas" :valor="`${d.lojas.por_estado.fechada || 0} / ${d.lojas.por_estado.suspensa || 0}`" />
            <Linha label="Lojas novas no período" :valor="d.lojas.novas" />
            <Linha label="Utilizadores (verificados)" :valor="`${d.utilizadores.total} (${d.utilizadores.verificados})`" />
            <Linha label="Utilizadores novos no período" :valor="d.utilizadores.novos" />
            <Linha label="Produtos ativos" :valor="d.produtos_ativos" />
          </dl>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { h } from 'vue'
import api from '@/services/api'
import FiltroPeriodo from '@/components/relatorios/FiltroPeriodo.vue'
import GraficoTempo from '@/components/relatorios/GraficoTempo.vue'
import { intervaloAtalho, dataCurta } from '@/utils/periodos'
import { formatarDinheiro } from '@/utils/dinheiro'

// uma linha "rótulo …… valor" dos painéis
const Linha = (props) => h('div', { class: 'flex items-center justify-between gap-3' }, [
  h('dt', { class: 'text-zinc-400' }, props.label),
  h('dd', { class: ['tabular-nums text-right', props.forte ? 'font-bold text-zinc-100' : 'font-semibold text-zinc-200', props.cor || ''] }, String(props.valor)),
])
Linha.props = ['label', 'valor', 'forte', 'cor']

export default {
  name: 'AdminDashboard',
  components: { FiltroPeriodo, GraficoTempo, Linha },
  emits: ['ir'],

  data () {
    return {
      loading: true, d: null, erro: '',
      COR_1: '#3987e5', COR_2: '#d95926',     // séries (validadas para o fundo escuro)
      ESTADOS_SUB: { teste: 'Em teste', ativa: 'Em dia', em_atraso: 'Em atraso', suspensa: 'Suspensa', cancelada: 'Cancelada', aguarda: 'A aguardar' },
      ESTADOS_ENC: { pendente: 'Pendente', pago: 'Pago', preparando: 'Em preparação', enviado: 'Enviado', concluido: 'Concluído', cancelado: 'Cancelado' },
    }
  },

  created () { this.carregar(intervaloAtalho('mes')) },

  computed: {
    kpis () {
      const d = this.d
      const $ = formatarDinheiro
      return [
        { icon: 'sack-dollar', cor: 'bg-green-500/10 text-green-400', label: 'Receita da plataforma', valor: $(d.receita.total),
          variacao: d.receita.variacao, sub: `comissões ${$(d.receita.comissoes)} · subscrições ${$(d.receita.subscricoes)}` },
        { icon: 'money-bill-wave', cor: 'bg-blue-500/10 text-blue-400', label: 'Vendas líquidas das lojas', valor: $(d.vendas.liquidas),
          variacao: d.vendas.variacao, sub: `brutas ${$(d.vendas.brutas)} · devoluções ${$(d.vendas.devolucoes)}` },
        { icon: 'arrows-rotate', cor: 'bg-violet-500/10 text-violet-400', label: 'Receita mensal recorrente', valor: $(d.subscricoes.mrr),
          sub: `${d.subscricoes.lojas.subscricao} lojas em subscrição` },
        { icon: 'wallet', cor: 'bg-sky-500/10 text-sky-400', label: 'Recebimentos', valor: $(d.recebimentos.total),
          sub: `${d.recebimentos.count} pagamentos recebidos` },
        { icon: 'bag-shopping', cor: 'bg-amber-500/10 text-amber-400', label: 'Encomendas feitas', valor: d.encomendas.criadas,
          variacao: d.encomendas.variacao, sub: `${d.vendas.encomendas} concluídas · ${d.encomendas.canceladas} canceladas` },
        { icon: 'receipt', cor: 'bg-zinc-500/10 text-zinc-300', label: 'Ticket médio', valor: $(d.vendas.ticket_medio),
          sub: 'por encomenda concluída' },
        { icon: 'rotate-left', cor: 'bg-orange-500/10 text-orange-400', label: 'Reembolsos', valor: $(d.reembolsos.total),
          sub: `${d.reembolsos.count} no período` + (d.reembolsos.em_disputa ? ` · ${d.reembolsos.em_disputa} em disputa` : '') },
        { icon: 'store', cor: 'bg-red-500/10 text-red-400', label: 'Lojas novas', valor: d.lojas.novas,
          sub: `${d.utilizadores.novos} utilizadores novos` },
      ]
    },
    alertas () {
      const a = this.d.alertas, out = []
      if (a.lojas_pendentes) out.push({ seccao: 'lojas', icon: 'hourglass-half', cor: 'border-amber-500/30 bg-amber-500/10 text-amber-300', texto: `${a.lojas_pendentes} loja(s) à espera de aprovação` })
      if (a.reembolsos_disputa) out.push({ seccao: 'devolucoes', icon: 'scale-balanced', cor: 'border-orange-500/30 bg-orange-500/10 text-orange-300', texto: `${a.reembolsos_disputa} reembolso(s) em disputa` })
      if (a.faturas_atraso) out.push({ seccao: 'subscricoes', icon: 'file-invoice-dollar', cor: 'border-red-500/30 bg-red-500/10 text-red-300', texto: `${a.faturas_atraso} fatura(s) em atraso · ${formatarDinheiro(a.faturas_atraso_valor)}` })
      return out
    },
  },

  methods: {
    dataCurta,
    async carregar ({ inicio, fim }) {
      this.loading = true
      this.erro = ''
      try {
        const { data } = await api.get('/app/admin/dashboard/', { params: { data_inicio: inicio, data_fim: fim } })
        this.d = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar o dashboard.'
      } finally { this.loading = false }
    },
    pct (v, total) { return Number(total) ? Math.max(2, (Number(v) / Number(total)) * 100) : 0 },
    statusColor (s) {
      const map = { pendente: 'text-yellow-400', pago: 'text-blue-400', preparando: 'text-purple-400', enviado: 'text-indigo-400', concluido: 'text-green-400', cancelado: 'text-red-400' }
      return map[s] || 'text-zinc-400'
    },
  },
}
</script>
