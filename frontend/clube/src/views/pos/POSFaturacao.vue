<!-- POSFaturacao.vue — aba Faturação do POS (dono e membros com pode_ver_relatorios, como o Histórico).
     Todas as contas fechadas do POS com a fatura que se emitiu no e-Fatura (registar, substituir, anular, histórico).
     O arquivo fiscal segue o NIF: vendidas com o NIF da loja ligada → arquivo da loja (também faturáveis aqui);
     de uma loja a que o POS já não está ligado → só leitura. O ZIP é só o arquivo do POS; o CSV é a lista.
     Backend: pos/views_faturacao.py -->
<template>
  <div class="space-y-5" data-teste="faturacao-pos">
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex-1 min-w-[220px]">
        <h2 class="text-2xl font-black text-slate-950">Faturação</h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">Emite cada fatura no e-Fatura (DNRE) e regista-a aqui na conta.</p>
      </div>
      <div v-if="resumo" class="text-right">
        <p class="text-[11px] font-bold text-slate-500">NIF</p>
        <p class="text-sm font-black tabular-nums text-slate-950">{{ resumo.pos.nif || '—' }}</p>
        <p v-if="resumo.pos.loja_do_arquivo" class="text-[11px] font-semibold text-slate-500">da loja {{ resumo.pos.loja.nome }}</p>
      </div>
    </div>

    <!-- onde ficam as vendas (só quando o POS está ligado a uma loja) -->
    <p v-if="resumo && resumo.pos.loja" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-600" data-teste="faturacao-arquivo-info">
      <template v-if="resumo.pos.loja_do_arquivo">
        Este POS vende com o NIF da loja <b>{{ resumo.pos.loja.nome }}</b>: as vendas ficam no arquivo fiscal da loja (a loja também as vê
        e fatura na Faturação dela). Fatura cada venda uma vez, aqui ou na loja.
      </template>
      <template v-else>
        Este POS está ligado à loja <b>{{ resumo.pos.loja.nome }}</b> mas vende com NIF próprio: as vendas ficam no arquivo do POS.
      </template>
    </p>

    <!-- por faturar em todas as datas (as que se faturam aqui) -->
    <button v-if="resumo && resumo.por_faturar_sempre" type="button" @click="verPorFaturar" data-teste="faturacao-por-faturar"
      class="w-full rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-left text-sm font-bold text-amber-900 transition hover:bg-amber-100">
      {{ resumo.por_faturar_sempre }} {{ resumo.por_faturar_sempre === 1 ? 'conta por faturar' : 'contas por faturar' }} (todas as datas) — ver e registar as faturas →
    </button>

    <!-- período -->
    <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-end gap-3" data-teste="faturacao-periodo">
      <label class="text-xs font-black text-slate-700">Período
        <select v-model="periodo" @change="mudarPeriodo" data-teste="periodo" :class="['mt-1 block', campo]">
          <option v-for="p in PERIODOS" :key="p.v" :value="p.v">{{ p.t }}</option>
        </select>
      </label>
      <template v-if="periodo === 'personalizado'">
        <label class="text-xs font-black text-slate-700">De <input type="date" v-model="de" @change="recarregar" data-teste="periodo-de" :class="['mt-1 block', campo]" /></label>
        <label class="text-xs font-black text-slate-700">a <input type="date" v-model="ate" @change="recarregar" data-teste="periodo-ate" :class="['mt-1 block', campo]" /></label>
      </template>
      <p class="pb-3 text-xs font-semibold text-slate-500">{{ textoPeriodo }}</p>
      <button type="button" @click="exportar" :disabled="aExportar" data-teste="faturacao-zip"
        class="ml-auto h-11 rounded-2xl border border-slate-200 bg-white px-4 text-xs font-black text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
        title="Dados fiscais, vendas do arquivo do POS, faturas e documentos do Bende do período — para o contabilista ou a DNRE">
        <font-awesome-icon :icon="['fas', 'file-zipper']" class="mr-1" />{{ aExportar ? 'A preparar…' : 'Arquivo do POS (ZIP)' }}
      </button>
    </section>
    <p v-if="erro" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700" role="alert">{{ erro }}</p>

    <!-- resumo do período (todas as contas do POS) -->
    <div v-if="resumo" class="grid grid-cols-2 gap-3 sm:grid-cols-5" data-teste="faturacao-resumo">
      <div v-for="t in cartoes" :key="t.label" class="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <p class="text-[11px] font-bold text-slate-500">{{ t.label }}</p>
        <p :class="['text-lg font-black tabular-nums', t.cor]">{{ t.valor }}</p>
      </div>
    </div>

    <div class="flex w-fit max-w-full gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1" role="tablist">
      <button v-for="t in ABAS" :key="t.key" type="button" role="tab" :aria-selected="aba === t.key ? 'true' : 'false'" @click="aba = t.key"
        :data-teste="`aba-${t.key}`"
        :class="['whitespace-nowrap rounded-xl px-4 py-2 text-sm font-black transition', aba === t.key ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800']">
        {{ t.label }}
      </button>
      <button v-if="!isMembro" type="button" @click="$emit('ver-subscricao')" data-teste="faturas-bende"
        class="whitespace-nowrap rounded-xl px-4 py-2 text-sm font-black text-slate-500 transition hover:text-slate-800"
        title="As faturas que o Bende emite ao POS (mensalidades) estão na Subscrição">Faturas do Bende ↗</button>
    </div>

    <!-- ═══ VENDAS ═══ -->
    <template v-if="aba === 'vendas'">
      <!-- arquivos: só quando há vendas no arquivo de uma loja -->
      <div v-if="resumo && resumo.arquivos.length > 1" class="flex w-fit max-w-full gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1"
           role="tablist" aria-label="Arquivo fiscal" data-teste="faturacao-arquivos">
        <button v-for="a in separadores" :key="a.chave" type="button" role="tab" :aria-selected="arquivo === a.chave ? 'true' : 'false'"
          @click="mudarArquivo(a.chave)" :data-teste="`arquivo-${a.chave || 'todas'}`"
          :class="['whitespace-nowrap rounded-xl px-3 py-1.5 text-xs font-black transition', arquivo === a.chave ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800']">
          {{ a.nome }}<template v-if="a.so_leitura"> · só leitura</template>
          <span v-if="a.por_faturar" class="text-amber-700"> · {{ a.por_faturar }} por faturar</span>
        </button>
      </div>

      <form @submit.prevent="carregarVendas(0)" class="flex flex-wrap items-end gap-2" data-teste="faturacao-filtros">
        <input v-model.trim="f.q" type="search" placeholder="V-…, nº de fatura (também anulada), NIF do cliente, mesa" aria-label="Pesquisar contas"
          data-teste="vendas-q" :class="['min-w-[200px] flex-1', campo]" />
        <select v-model="f.estado" @change="carregarVendas(0)" aria-label="Estado da fatura" data-teste="vendas-estado" :class="campo">
          <option value="">Todas</option><option value="por_faturar">Por faturar</option><option value="faturada">Faturadas</option>
          <option value="com_anuladas">Com faturas anuladas</option>
        </select>
        <input v-model.trim="f.min" inputmode="decimal" placeholder="Valor mín." aria-label="Valor mínimo" :class="['w-28', campo]" />
        <input v-model.trim="f.max" inputmode="decimal" placeholder="Valor máx." aria-label="Valor máximo" :class="['w-28', campo]" />
        <button type="submit" class="h-11 rounded-2xl bg-slate-950 px-4 text-xs font-black text-white transition hover:bg-slate-800">Procurar</button>
        <button type="button" @click="limpar" class="h-11 px-2 text-xs font-bold text-slate-500 hover:text-slate-900">Limpar</button>
        <button type="button" @click="csv" data-teste="faturacao-csv" title="A lista com estes filtros, em CSV (Excel)"
          class="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-xs font-black text-slate-700 transition hover:bg-slate-50 sm:ml-auto">
          <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV
        </button>
      </form>
      <p v-if="vendas.totais" class="text-xs font-semibold text-slate-500" data-teste="vendas-totais">
        {{ vendas.totais.vendas }} conta(s) · {{ dinheiro(vendas.totais.valor) }} · <span class="text-emerald-700">{{ vendas.totais.faturadas }} faturada(s)</span> ·
        <span :class="vendas.totais.por_faturar ? 'text-amber-700' : ''">{{ vendas.totais.por_faturar }} por faturar</span> · valores sem a gorjeta
      </p>

      <div class="space-y-2" data-teste="faturacao-lista">
        <div v-for="v in vendas.results" :key="v.id" class="rounded-2xl border border-slate-200 bg-white shadow-sm" :data-teste="`venda-${v.referencia}`">
          <div class="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
            <div class="min-w-[160px] flex-1">
              <p class="text-sm font-black text-slate-950">{{ v.titulo }}</p>
              <p class="text-[11px] font-semibold text-slate-500">{{ v.referencia }} · {{ quando(v.data) }}</p>
            </div>
            <div class="min-w-[120px]">
              <p class="truncate text-sm font-semibold text-slate-700">{{ v.cliente.nome }}</p>
              <p v-if="v.arquivo.tipo === 'loja'" class="truncate text-[11px] font-bold text-slate-500" data-teste="venda-arquivo">Arquivo: {{ v.arquivo.loja.nome }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-black tabular-nums text-slate-950">{{ dinheiro(v.valor) }}</p>
              <p v-if="Number(v.gorjeta) > 0" class="text-[11px] font-semibold text-slate-500">+ gorjeta {{ dinheiro(v.gorjeta) }}</p>
            </div>
            <div class="flex w-full flex-wrap items-center gap-1.5 sm:w-auto">
              <span v-if="v.fatura" class="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-black text-emerald-700">Fatura {{ v.fatura.numero }}</span>
              <span v-else-if="v.faturavel && !v.arquivo.so_leitura" class="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-black text-amber-800">Por faturar</span>
              <span v-else-if="v.arquivo.so_leitura" class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-black text-slate-600">Só leitura</span>
              <span v-if="v.anuladas" class="rounded bg-red-100 px-1.5 py-0.5 text-[11px] font-black text-red-700">{{ v.anuladas }} anulada(s)</span>
              <button type="button" @click="alternar(v, 'fatura')" :aria-expanded="aberto[v.referencia] === 'fatura' ? 'true' : 'false'" data-teste="abrir-fatura"
                class="rounded-xl bg-slate-950 px-3 py-1.5 text-xs font-black text-white transition hover:bg-slate-800">Fatura</button>
              <button type="button" @click="alternar(v, 'historico')" :aria-expanded="aberto[v.referencia] === 'historico' ? 'true' : 'false'" data-teste="abrir-historico"
                class="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-black text-slate-700 transition hover:bg-slate-50">Histórico</button>
            </div>
          </div>
          <div v-if="aberto[v.referencia] === 'fatura'" class="px-4 pb-4">
            <p v-if="v.arquivo.so_leitura" class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-600" data-teste="venda-so-leitura">
              Vendida com o NIF da loja <b>{{ v.arquivo.loja.nome }}</b>, quando o POS lhe estava ligado: é do arquivo fiscal dessa loja e a fatura
              regista-se na Faturação dela.<template v-if="v.fatura"> Fatura em vigor: <b>{{ v.fatura.numero }}</b>.</template>
            </p>
            <FaturaVenda v-else-if="v.faturavel || v.fatura" :documento="v" :url="`/api/pos/${posId}/contas/${v.id}/fatura/`" tema="claro" teste="fatura-venda"
              :cancelada="!v.faturavel" :dica="dica(v)" @atualizada="atualizada" />
            <p v-else class="text-xs font-semibold text-slate-500">Esta conta não se fatura (sem valor).</p>
          </div>
          <div v-else-if="aberto[v.referencia] === 'historico'" class="px-4 pb-4">
            <HistoricoFatura :key="`${v.referencia}-${versao}`" :referencia="v.referencia" :url="`/api/pos/${posId}/faturacao/historico/`" claro />
          </div>
        </div>
        <p v-if="!vendas.results.length" class="rounded-2xl border border-slate-200 bg-white py-10 text-center text-sm font-semibold text-slate-500">
          {{ carregando ? 'A carregar…' : 'Nenhuma conta com estes filtros neste período.' }}</p>
      </div>
      <PaginacaoLista :count="vendas.count" :limit="LIMITE" :offset="offset" claro @ir="carregarVendas" />
    </template>

    <!-- ═══ PESQUISAR DOCUMENTOS (todas as datas) ═══ -->
    <template v-else>
      <form @submit.prevent="pesquisar(0)" class="flex flex-wrap gap-2">
        <input v-model.trim="pq" type="search" placeholder="Nº de fatura (também anulada), V-123, S-45, NIF do cliente"
          aria-label="Pesquisar documentos" data-teste="faturacao-pesquisa-q" :class="['min-w-[220px] flex-1', campo]" />
        <button type="submit" :disabled="pq.length < 2" class="h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-50">Pesquisar</button>
      </form>
      <p class="text-[11px] font-semibold text-slate-500">Em todos os documentos do POS, de sempre: contas, faturas em vigor e anuladas, mensalidades do Bende.</p>
      <ResultadosPesquisa v-if="pRes" :res="pRes" :limit="LIMITE" :offset="pOffset" claro @ir="pesquisar" @abrir="abrirResultado" />
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf } from '@/utils/documentos'
import { PERIODOS, intervalo, textoPeriodo } from '@/utils/periodosFaturacao'
import FaturaVenda from '@/components/fiscal/FaturaVenda.vue'
import HistoricoFatura from '@/components/fiscal/HistoricoFatura.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import ResultadosPesquisa from '@/components/fiscal/ResultadosPesquisa.vue'

const LIMITE = 20
const ABAS = [{ key: 'vendas', label: 'Vendas e faturas' }, { key: 'pesquisa', label: 'Pesquisar documentos' }]
const vazio = () => ({ q: '', estado: '', min: '', max: '' })

export default {
  name: 'POSFaturacao',
  components: { FaturaVenda, HistoricoFatura, PaginacaoLista, ResultadosPesquisa },
  props: {
    posId: { type: [String, Number], required: true },
    permissoes: { type: Object, default: null },
    isMembro: { type: Boolean, default: false },
  },
  emits: ['ver-subscricao'],
  data () {
    const [de, ate] = intervalo('mes')
    return {
      LIMITE, PERIODOS, ABAS,
      campo: 'h-11 rounded-2xl border border-slate-200 bg-slate-50 px-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white',
      periodo: 'mes', de, ate, resumo: null, erro: '', aExportar: false,
      aba: 'vendas', arquivo: '', f: vazio(),
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
    textoPeriodo () { return textoPeriodo(this.de, this.ate) },
    cartoes () {
      const t = this.resumo.totais
      return [
        { label: 'Contas', valor: t.vendas, cor: 'text-slate-950' },
        { label: 'Valor (sem gorjeta)', valor: this.dinheiro(t.valor), cor: 'text-slate-950' },
        { label: 'Faturadas', valor: t.faturadas, cor: 'text-emerald-700' },
        { label: 'Por faturar', valor: t.por_faturar, cor: t.por_faturar ? 'text-amber-700' : 'text-slate-400' },
        { label: 'Faturas anuladas', valor: t.anuladas, cor: t.anuladas ? 'text-red-700' : 'text-slate-400' },
      ]
    },
    // "Todas" + um separador por arquivo (este POS, cada loja com cujo NIF vendeu)
    separadores () {
      const t = this.resumo.totais
      return [{ chave: '', nome: 'Todas', por_faturar: t.por_faturar }, ...this.resumo.arquivos]
    },
  },
  created () { this.recarregar() },
  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    quando (s) { return s ? new Date(s).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) : '—' },
    filtros () {
      const p = { ...this.datas }
      if (this.arquivo) p.arquivo = this.arquivo
      for (const [k, v] of Object.entries(this.f)) if (v) p[k] = v
      return p
    },
    mudarPeriodo () {
      if (this.periodo !== 'personalizado') [this.de, this.ate] = intervalo(this.periodo)
      this.recarregar()
    },
    async recarregar () {
      this.erro = ''
      try {
        this.resumo = (await api.get(`/api/pos/${this.posId}/faturacao/resumo/`, { params: this.datas })).data
        if (this.arquivo && !this.resumo.arquivos.some(a => a.chave === this.arquivo)) this.arquivo = ''
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar a faturação.' }
      this.carregarVendas(0)
    },
    async carregarVendas (offset = this.offset) {
      this.offset = offset; this.carregando = true; this.aberto = {}
      try {
        this.vendas = (await api.get(`/api/pos/${this.posId}/faturacao/vendas/`, { params: { ...this.filtros(), limit: LIMITE, offset } })).data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar as contas.'
      } finally { this.carregando = false }
    },
    limpar () { this.f = vazio(); this.carregarVendas(0) },
    mudarArquivo (a) {
      if (a === this.arquivo) return
      this.arquivo = a
      this.carregarVendas(0)
    },
    // aviso "N por faturar": todas as datas, filtro "por faturar"
    verPorFaturar () {
      this.periodo = 'todas'; [this.de, this.ate] = ['', '']
      this.aba = 'vendas'; this.arquivo = ''; this.f = { ...vazio(), estado: 'por_faturar' }
      this.recarregar()
    },
    alternar (v, o) { this.aberto = { [v.referencia]: this.aberto[v.referencia] === o ? null : o } },
    dica (v) {
      const valor = `Valor a faturar: ${this.dinheiro(v.valor)}`
      return Number(v.gorjeta) > 0 ? `Emite a fatura no e-Fatura e regista-a aqui. ${valor} — sem a gorjeta.` : `Emite a fatura no e-Fatura e regista-a aqui. ${valor}.`
    },
    // a fatura mudou: recarrega a lista e os totais (o backend é a fonte)
    async atualizada () {
      this.versao++
      const aberto = this.aberto
      await this.recarregar()
      this.aberto = aberto
    },
    csv () {
      descarregarPdf(`/api/pos/${this.posId}/faturacao/vendas.csv`, `vendas-pos-${this.de || 'inicio'}-${this.ate || 'hoje'}.csv`, this.filtros())
        .catch(() => { this.erro = 'Não foi possível exportar o CSV.' })
    },
    async exportar () {
      this.aExportar = true; this.erro = ''
      try {
        await descarregarPdf(`/api/pos/${this.posId}/faturacao/exportar/`, `arquivo-fiscal-pos-${this.de || 'inicio'}-${this.ate || 'hoje'}.zip`, this.datas)
      } catch (e) {
        let msg = 'Não foi possível exportar.'
        try { msg = JSON.parse(await e.response.data.text()).detail || msg } catch { /* resposta sem JSON */ }
        this.erro = msg
      } finally { this.aExportar = false }
    },
    pesquisar (offset = 0) {
      this.pOffset = offset
      api.get(`/api/pos/${this.posId}/faturacao/pesquisa/`, { params: { q: this.pq, limit: LIMITE, offset } })
        .then(({ data }) => { this.pRes = data })
        .catch(e => { this.erro = e.response?.data?.detail || 'Não foi possível pesquisar.' })
    },
    // conta (ou fatura anulada de uma conta) → a conta na lista; mensalidades → Subscrição
    abrirResultado (r) {
      const ref = r.referencia || ''
      if (/^V-/i.test(ref)) {
        this.periodo = 'todas'; [this.de, this.ate] = ['', '']
        this.arquivo = ''; this.f = { ...vazio(), q: ref }; this.aba = 'vendas'
        return this.recarregar()
      }
      if (!this.isMembro) this.$emit('ver-subscricao')
    },
  },
}
</script>
