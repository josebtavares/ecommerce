<!-- BackofficeFaturacao.vue — aba Faturação da loja (gerir_faturacao: dono, gestor, contabilista).
     Todas as vendas da loja — loja online (E-), marcações (M-) e contas do POS vendidas em nome da loja (V-) — com o
     comprovativo do Bende (só o que foi pago no Bende) e a fatura que a loja emitiu no e-Fatura (registar, substituir,
     anular, histórico). Período, filtros, pesquisa de documentos, paginação, CSV e ZIP do arquivo fiscal.
     Backend: app/Views/faturacaoLojaView.py -->
<template>
  <div class="space-y-5 max-w-6xl" data-teste="faturacao-loja">
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex-1 min-w-[220px]">
        <h2 class="text-xl font-black text-zinc-100">Faturação</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Emite cada fatura no e-Fatura (DNRE) e regista-a aqui na venda: o cliente vê-a e recebe-a por email.</p>
      </div>
      <div v-if="resumo" class="text-right">
        <p class="text-[11px] text-zinc-500">NIF</p>
        <p class="text-sm font-bold tabular-nums text-zinc-100">{{ resumo.loja.nif || '—' }}</p>
      </div>
    </div>

    <!-- por faturar em todas as datas: não depende do período escolhido -->
    <button v-if="resumo && resumo.por_faturar_sempre.total" type="button" @click="verPorFaturar" data-teste="faturacao-por-faturar"
      class="w-full text-left rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200 hover:bg-amber-500/15">
      <b>{{ resumo.por_faturar_sempre.total }} {{ resumo.por_faturar_sempre.total === 1 ? 'venda por faturar' : 'vendas por faturar' }}</b>
      (todas as datas) — ver e registar as faturas.
    </button>

    <!-- período -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex flex-wrap items-end gap-3" data-teste="faturacao-periodo">
      <label class="text-[11px] text-zinc-500">Período
        <select v-model="periodo" @change="mudarPeriodo" data-teste="periodo"
          class="block mt-1 px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200">
          <option v-for="p in PERIODOS" :key="p.v" :value="p.v">{{ p.t }}</option>
        </select>
      </label>
      <template v-if="periodo === 'personalizado'">
        <label class="text-[11px] text-zinc-500">De <input type="date" v-model="de" @change="recarregar" data-teste="periodo-de"
          class="block mt-1 px-2 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 [color-scheme:dark]" /></label>
        <label class="text-[11px] text-zinc-500">a <input type="date" v-model="ate" @change="recarregar" data-teste="periodo-ate"
          class="block mt-1 px-2 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 [color-scheme:dark]" /></label>
      </template>
      <p class="text-xs text-zinc-500 pb-2">{{ textoPeriodo }}</p>
      <div class="ml-auto flex flex-wrap gap-2">
        <button type="button" @click="exportar" :disabled="aExportar" data-teste="faturacao-zip"
          class="px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-200 text-xs font-semibold"
          title="Dados fiscais, vendas, comprovativos e todas as faturas do período — para o contabilista ou a DNRE">
          <font-awesome-icon :icon="['fas', 'file-zipper']" class="mr-1" />{{ aExportar ? 'A preparar…' : 'Arquivo (ZIP)' }}
        </button>
      </div>
    </div>
    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <!-- resumo do período -->
    <div v-if="resumo" class="grid grid-cols-2 sm:grid-cols-5 gap-3" data-teste="faturacao-resumo">
      <div v-for="t in cartoes" :key="t.label" class="bg-zinc-900 rounded-xl border border-zinc-800 px-4 py-3">
        <p class="text-[11px] text-zinc-500">{{ t.label }}</p>
        <p :class="['text-lg font-bold tabular-nums', t.cor]">{{ t.valor }}</p>
      </div>
    </div>

    <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 w-fit max-w-full overflow-x-auto" role="tablist">
      <button v-for="t in ABAS" :key="t.key" type="button" role="tab" :aria-selected="aba === t.key ? 'true' : 'false'" @click="aba = t.key"
        :data-teste="`aba-${t.key}`"
        :class="['px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap', aba === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
        {{ t.label }}
      </button>
      <button type="button" @click="$emit('ver-subscricao')" class="px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap text-zinc-500 hover:text-zinc-300"
        title="As faturas que o Bende emite à loja (mensalidades e comissões) estão na Subscrição">Faturas do Bende ↗</button>
    </div>

    <!-- ═══ VENDAS ═══ -->
    <template v-if="aba === 'vendas'">
      <div v-if="resumo && resumo.origens.length > 1" class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 w-fit max-w-full overflow-x-auto"
           role="tablist" aria-label="Origem das vendas" data-teste="faturacao-origens">
        <button v-for="o in resumo.origens" :key="o.origem" type="button" role="tab" :aria-selected="origem === o.origem ? 'true' : 'false'"
          @click="mudarOrigem(o.origem)" :data-teste="`origem-${o.origem}`"
          :class="['px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap', origem === o.origem ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ NOMES[o.origem] }} <span :class="o.por_faturar ? 'text-amber-300' : 'text-zinc-500'">· {{ o.por_faturar ? `${o.por_faturar} por faturar` : o.vendas }}</span>
        </button>
      </div>

      <form @submit.prevent="carregarVendas(0)" class="flex flex-wrap items-end gap-2" data-teste="faturacao-filtros">
        <input v-model.trim="f.q" type="search" :placeholder="PESQUISA[origem]" aria-label="Pesquisar vendas" data-teste="vendas-q"
          class="flex-1 min-w-[200px] px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
        <select v-model="f.estado" @change="carregarVendas(0)" aria-label="Estado da fatura" data-teste="vendas-estado"
          class="px-2 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200">
          <option value="">Todas</option><option value="por_faturar">Por faturar</option><option value="faturada">Faturadas</option>
          <option value="com_anuladas">Com faturas anuladas</option>
        </select>
        <input v-model.trim="f.min" inputmode="decimal" placeholder="Valor mín." aria-label="Valor mínimo" class="w-24 px-2 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200" />
        <input v-model.trim="f.max" inputmode="decimal" placeholder="Valor máx." aria-label="Valor máximo" class="w-24 px-2 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200" />
        <button type="submit" class="px-3 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
        <button type="button" @click="limpar" class="px-2 py-2 text-xs text-zinc-400 hover:text-zinc-200">Limpar</button>
        <button type="button" @click="csv" data-teste="faturacao-csv" class="px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs sm:ml-auto"
          title="A lista com estes filtros, em CSV (Excel)">
          <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV
        </button>
      </form>
      <p v-if="vendas.totais" class="text-xs text-zinc-500" data-teste="vendas-totais">
        {{ vendas.totais.vendas }} venda(s) · {{ dinheiro(vendas.totais.valor) }} · <span class="text-green-400">{{ vendas.totais.faturadas }} faturada(s)</span> ·
        <span :class="vendas.totais.por_faturar ? 'text-amber-300' : ''">{{ vendas.totais.por_faturar }} por faturar</span>
        <template v-if="origem === 'pos'"> · valores sem a gorjeta</template>
      </p>

      <div class="space-y-2" data-teste="faturacao-lista">
        <div v-for="v in vendas.results" :key="v.id" class="bg-zinc-900 rounded-2xl border border-zinc-800" :data-teste="`venda-${v.referencia}`">
          <div class="px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-2">
            <div class="flex-1 min-w-[180px]">
              <p class="text-sm font-semibold text-zinc-100">{{ v.titulo }}</p>
              <p class="text-[11px] text-zinc-500">{{ v.referencia }} · {{ quando(v.data) }}<template v-if="v.pos"> · {{ v.pos.nome }}</template></p>
            </div>
            <div class="min-w-[140px]">
              <p class="text-sm text-zinc-300 truncate">{{ v.cliente.nome }}</p>
              <p v-if="v.cliente.email" class="text-[11px] text-zinc-500 truncate">{{ v.cliente.email }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-bold tabular-nums text-zinc-100">{{ dinheiro(v.valor) }}</p>
              <p class="text-[11px] text-zinc-500">{{ v.status_nome }}</p>
            </div>
            <div class="w-full sm:w-auto flex flex-wrap items-center gap-1.5">
              <span v-if="v.fatura" class="px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 text-[11px] font-bold">Fatura {{ v.fatura.numero }}</span>
              <span v-else-if="v.faturavel" class="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 text-[11px] font-bold">Por faturar</span>
              <span v-if="v.anuladas" class="px-1.5 py-0.5 rounded bg-red-500/15 text-red-300 text-[11px] font-bold">{{ v.anuladas }} anulada(s)</span>
              <button v-if="v.comprovativo_url" type="button" @click="comprovativo(v)" data-teste="comprovativo"
                class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Comprovativo</button>
              <button type="button" @click="alternar(v, 'fatura')" :aria-expanded="aberto[v.referencia] === 'fatura' ? 'true' : 'false'" data-teste="abrir-fatura"
                class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">Fatura</button>
              <button type="button" @click="alternar(v, 'historico')" :aria-expanded="aberto[v.referencia] === 'historico' ? 'true' : 'false'" data-teste="abrir-historico"
                class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Histórico</button>
            </div>
          </div>
          <div v-if="aberto[v.referencia] === 'fatura'" class="px-4 pb-4">
            <FaturaVenda v-if="v.faturavel || v.fatura" :documento="v" :url="urlFatura(v)" teste="fatura-venda"
              :cancelada="!v.faturavel" :dica="dica(v)" @atualizada="atualizada" />
            <p v-else class="text-xs text-zinc-500">Esta venda ainda não se fatura ({{ v.status_nome.toLowerCase() }}).</p>
          </div>
          <div v-else-if="aberto[v.referencia] === 'historico'" class="px-4 pb-4">
            <HistoricoFatura :key="`${v.referencia}-${versao}`" :referencia="v.referencia" :url="`/app/loja/${lojaId}/faturacao/historico/`" />
          </div>
        </div>
        <p v-if="!vendas.results.length" class="text-center py-10 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">
          {{ carregando ? 'A carregar…' : 'Nenhuma venda com estes filtros neste período.' }}</p>
      </div>
      <PaginacaoLista :count="vendas.count" :limit="LIMITE" :offset="offset" @ir="carregarVendas" />
    </template>

    <!-- ═══ PESQUISAR DOCUMENTOS (todas as datas) ═══ -->
    <template v-else>
      <form @submit.prevent="pesquisar(0)" class="flex flex-wrap gap-2">
        <input v-model.trim="pq" type="search" placeholder="Nº de fatura (também anulada), E-123, M-12, V-7, S-45, C-…, cliente, NIF do cliente"
          aria-label="Pesquisar documentos" data-teste="faturacao-pesquisa-q"
          class="flex-1 min-w-[220px] px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
        <button type="submit" :disabled="pq.length < 2" class="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">Pesquisar</button>
      </form>
      <p class="text-[11px] text-zinc-500">Em todos os documentos da loja, de sempre: vendas, faturas em vigor e anuladas, mensalidades e comissões do Bende.</p>
      <ResultadosPesquisa v-if="pRes" :res="pRes" :limit="LIMITE" :offset="pOffset" @ir="pesquisar" @abrir="abrirResultado" />
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, descarregarComprovativoVenda } from '@/utils/documentos'
import { hojeCV } from '@/utils/servicos'
import FaturaVenda from '@/components/fiscal/FaturaVenda.vue'
import HistoricoFatura from '@/components/fiscal/HistoricoFatura.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import ResultadosPesquisa from '@/components/fiscal/ResultadosPesquisa.vue'

const LIMITE = 20
const NOMES = { loja: 'Loja online', marcacoes: 'Marcações', pos: 'POS' }
const PESQUISA = {
  loja: 'Nº da encomenda, nº de fatura (também anulada), cliente',
  marcacoes: 'M-…, nº de fatura (também anulada), cliente, serviço',
  pos: 'V-…, nº de fatura (também anulada), NIF do cliente, mesa',
}
const PERIODOS = [
  { v: 'mes', t: 'Este mês' }, { v: 'mes_passado', t: 'Mês passado' }, { v: 'tres_meses', t: 'Últimos 3 meses' },
  { v: 'ano', t: 'Este ano' }, { v: 'ano_passado', t: 'Ano passado' }, { v: 'todas', t: 'Todas as datas' },
  { v: 'personalizado', t: 'Personalizado…' },
]
const ABAS = [{ key: 'vendas', label: 'Vendas e faturas' }, { key: 'pesquisa', label: 'Pesquisar documentos' }]
const vazio = () => ({ q: '', estado: '', min: '', max: '' })
const iso = d => d.toISOString().slice(0, 10)
// E-… encomenda (loja online), M-… marcação, V-… conta do POS
const ORIGEM_DO_PREFIXO = { E: 'loja', M: 'marcacoes', V: 'pos' }

function intervalo (p) {
  const h = new Date(hojeCV() + 'T12:00:00Z')
  const a = h.getUTCFullYear(), m = h.getUTCMonth()
  const dia = (y, mm, d) => iso(new Date(Date.UTC(y, mm, d)))
  return {
    mes: [dia(a, m, 1), iso(h)],
    mes_passado: [dia(a, m - 1, 1), dia(a, m, 0)],
    tres_meses: [dia(a, m - 2, 1), iso(h)],
    ano: [dia(a, 0, 1), iso(h)],
    ano_passado: [dia(a - 1, 0, 1), dia(a - 1, 11, 31)],
    todas: ['', ''],
  }[p]
}

export default {
  name: 'BackofficeFaturacao',
  components: { FaturaVenda, HistoricoFatura, PaginacaoLista, ResultadosPesquisa },
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['ver-subscricao'],
  data () {
    const [de, ate] = intervalo('mes')
    return {
      LIMITE, NOMES, PESQUISA, PERIODOS, ABAS,
      periodo: 'mes', de, ate, resumo: null, erro: '', aExportar: false,
      aba: 'vendas', origem: 'loja', f: vazio(),
      vendas: { count: 0, results: [], totais: null }, offset: 0, carregando: false,
      aberto: {}, versao: 0,
      pq: '', pRes: null, pOffset: 0,
    }
  },
  computed: {
    datas () {
      const p = {}
      if (this.de) p.de = this.de
      if (this.ate) p.ate = this.ate
      return p
    },
    textoPeriodo () {
      const f = s => s.split('-').reverse().join('/')
      if (this.de && this.ate) return `${f(this.de)} a ${f(this.ate)}`
      if (this.de) return `desde ${f(this.de)}`
      if (this.ate) return `até ${f(this.ate)}`
      return 'Desde sempre'
    },
    cartoes () {
      const t = this.resumo.totais
      return [
        { label: 'Vendas', valor: t.vendas, cor: 'text-zinc-100' },
        { label: 'Valor', valor: this.dinheiro(t.valor), cor: 'text-zinc-100' },
        { label: 'Faturadas', valor: t.faturadas, cor: 'text-green-400' },
        { label: 'Por faturar', valor: t.por_faturar, cor: t.por_faturar ? 'text-amber-300' : 'text-zinc-500' },
        { label: 'Faturas anuladas', valor: t.anuladas, cor: t.anuladas ? 'text-red-300' : 'text-zinc-500' },
      ]
    },
  },
  created () { this.recarregar(true) },
  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    quando (s) { return s ? new Date(s).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) : '—' },
    mudarPeriodo () {
      if (this.periodo !== 'personalizado') [this.de, this.ate] = intervalo(this.periodo)
      this.recarregar()
    },
    async recarregar (primeira = false) {
      this.erro = ''
      try {
        this.resumo = (await api.get(`/app/loja/${this.lojaId}/faturacao/resumo/`, { params: this.datas })).data
        // a abrir: a origem com vendas por faturar (ou com vendas), não uma vazia
        if (primeira) {
          const os = this.resumo.origens
          const atual = os.find(o => o.origem === this.origem)
          if (atual && !atual.por_faturar) {
            const outra = os.find(o => o.por_faturar) || (!atual.vendas && os.find(o => o.vendas))
            if (outra) this.origem = outra.origem
          }
        }
        if (!this.resumo.origens.some(o => o.origem === this.origem)) this.origem = 'loja'
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar a faturação.' }
      this.carregarVendas(0)
    },
    async carregarVendas (offset = this.offset) {
      this.offset = offset; this.carregando = true; this.aberto = {}
      const params = { ...this.datas, origem: this.origem, limit: LIMITE, offset }
      for (const [k, v] of Object.entries(this.f)) if (v) params[k] = v
      try {
        this.vendas = (await api.get(`/app/loja/${this.lojaId}/faturacao/vendas/`, { params })).data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar as vendas.'
      } finally { this.carregando = false }
    },
    limpar () { this.f = vazio(); this.carregarVendas(0) },
    mudarOrigem (o) {
      if (o === this.origem) return
      this.origem = o; this.f = vazio()
      this.vendas = { count: 0, results: [], totais: null }
      this.carregarVendas(0)
    },
    // aviso "N por faturar": todas as datas, filtro "por faturar", na origem que as tem
    verPorFaturar () {
      const s = this.resumo.por_faturar_sempre.origens
      this.periodo = 'todas'; [this.de, this.ate] = ['', '']
      this.aba = 'vendas'; this.f = { ...vazio(), estado: 'por_faturar' }
      if (!s[this.origem]) this.origem = Object.keys(s).find(o => s[o]) || this.origem
      this.recarregar()
    },
    alternar (v, o) { this.aberto = { [v.referencia]: this.aberto[v.referencia] === o ? null : o } },
    urlFatura (v) {
      const l = `/app/loja/${this.lojaId}`
      return { loja: `${l}/encomendas/${v.id}/fatura/`, marcacoes: `${l}/servicos/marcacoes/${v.id}/fatura/`,
        pos: `${l}/faturacao/contas/${v.id}/fatura/` }[v.origem]
    },
    dica (v) {
      if (v.origem === 'pos') return 'Emite a fatura no e-Fatura (sem a gorjeta) e regista-a aqui. O POS também a vê no Histórico dele.'
      if (v.origem === 'marcacoes' && !v.cliente.email) return 'Emite a fatura no e-Fatura e regista-a aqui.'
      return 'Emite a fatura no e-Fatura e regista-a aqui: o cliente vê-a e recebe-a por email.'
    },
    // a fatura mudou: recarrega a página da lista e os totais (o backend é a fonte)
    atualizada () { this.versao++; this.recarregarSemPerder() },
    async recarregarSemPerder () {
      const aberto = this.aberto
      await this.recarregar()
      this.aberto = aberto
    },
    comprovativo (v) {
      descarregarComprovativoVenda(v).catch(() => { this.erro = 'Não foi possível descarregar o comprovativo.' })
    },
    csv () {
      const params = { ...this.datas, origem: this.origem }
      for (const [k, v] of Object.entries(this.f)) if (v) params[k] = v
      const nome = { loja: 'vendas', marcacoes: 'marcacoes', pos: 'vendas-pos' }[this.origem]
      descarregarPdf(`/app/loja/${this.lojaId}/faturacao/vendas.csv`, `${nome}-${this.de || 'inicio'}-${this.ate || 'hoje'}.csv`, params)
        .catch(() => { this.erro = 'Não foi possível exportar o CSV.' })
    },
    async exportar () {
      this.aExportar = true; this.erro = ''
      try {
        await descarregarPdf(`/app/loja/${this.lojaId}/faturacao/exportar/`, `arquivo-fiscal-${this.de || 'inicio'}-${this.ate || 'hoje'}.zip`, this.datas)
      } catch (e) {
        let msg = 'Não foi possível exportar.'
        try { msg = JSON.parse(await e.response.data.text()).detail || msg } catch { /* resposta sem JSON */ }
        this.erro = msg
      } finally { this.aExportar = false }
    },
    pesquisar (offset = 0) {
      this.pOffset = offset
      api.get(`/app/loja/${this.lojaId}/faturacao/pesquisa/`, { params: { q: this.pq, limit: LIMITE, offset } })
        .then(({ data }) => { this.pRes = data })
        .catch(e => { this.erro = e.response?.data?.detail || 'Não foi possível pesquisar.' })
    },
    // resultado → a venda na lista (todas as datas, pesquisa pela referência); documentos do Bende → Subscrição
    abrirResultado (r) {
      const ref = r.referencia || ''
      if (r.tipo === 'venda' || (r.tipo === 'anulada' && /^[EMV]-/i.test(ref))) {
        this.origem = ORIGEM_DO_PREFIXO[ref.charAt(0).toUpperCase()] || 'loja'
        this.periodo = 'todas'; [this.de, this.ate] = ['', '']
        this.f = { ...vazio(), q: ref }
        this.aba = 'vendas'
        return this.recarregar()
      }
      this.$emit('ver-subscricao')
    },
  },
}
</script>
