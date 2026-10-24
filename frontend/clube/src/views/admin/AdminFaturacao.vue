<template>
  <!-- Admin → Faturação (como Admin → Comissões): uma aba por loja (e POS sem loja) com a sua vista — ficha, vendas, POS,
       faturas do Bende, pesquisa; "Todas" = visão geral (vendedores, pesquisa global, faturas do Bende). Backend faturacaoView.py -->
  <div class="space-y-5">
    <div>
      <h2 class="text-lg font-bold text-zinc-100">Faturação</h2>
      <p class="text-xs text-zinc-500 mt-0.5">Arquivo fiscal de todas as lojas e POS — nada se apaga: faturas substituídas ou anuladas ficam no histórico</p>
    </div>
    <AbasVendedores ref="abas" url="/app/admin/faturacao/abas/" :ativo="abaAtiva" titulo="Documentos por faturar (vendas + faturas do Bende)" @selecionar="selecionar" />

    <FaturacaoFicha v-if="ficha" :key="ficha.tipo + ficha.id" :tipo="ficha.tipo" :id="ficha.id" :aba-inicial="ficha.aba" :q-inicial="ficha.q"
      @abrir="abrirFicha" @alterado="carregarAbas" @carregada="f => lojaDoPos = f.tipo === 'pos' && f.loja ? f.loja.id : null" />

    <template v-else>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-sm font-semibold text-zinc-300">Todas as lojas e POS</p>
        <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 max-w-full overflow-x-auto" role="tablist">
          <button v-for="t in TABS" :key="t.key" type="button" role="tab" :aria-selected="tab === t.key ? 'true' : 'false'" @click="mudarTab(t.key)"
            :class="['px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap transition', tab === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
            {{ t.label }}
          </button>
        </div>
      </div>

      <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

      <!-- ═══ VENDEDORES ═══ -->
      <template v-if="tab === 'vendedores'">
        <form @submit.prevent="carregarVendedores(0)" class="flex flex-wrap items-end gap-2">
          <input v-model.trim="fl.q" type="search" placeholder="Nome, NIF, código POS, email ou telefone do dono" aria-label="Pesquisar vendedores" data-teste="vendedores-q"
            class="flex-1 min-w-[220px] px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
          <select v-model="fl.tipo" @change="carregarVendedores(0)" aria-label="Tipo" class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
            <option value="">Lojas e POS</option><option value="loja">Só lojas</option><option value="pos">Só POS</option>
          </select>
          <select v-model="fl.regime" @change="carregarVendedores(0)" aria-label="Vende como" class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
            <option value="">Qualquer regime</option><option value="particular">Particular</option><option value="atividade">Atividade declarada</option>
          </select>
          <select v-model="fl.dados" @change="carregarVendedores(0)" aria-label="Dados fiscais" data-teste="vendedores-dados" class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
            <option value="">Dados fiscais: todos</option><option value="completos">Completos</option><option value="incompletos">Por preencher</option>
          </select>
          <label class="flex items-center gap-1.5 text-xs text-zinc-400 px-1">
            <input type="checkbox" v-model="fl.por_faturar" @change="carregarVendedores(0)" class="accent-red-600" /> Com vendas por faturar
          </label>
          <label class="text-[11px] text-zinc-500">Vendas de <input type="date" v-model="fl.de" @change="carregarVendedores(0)" class="ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <label class="text-[11px] text-zinc-500">a <input type="date" v-model="fl.ate" @change="carregarVendedores(0)" class="ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
        </form>
        <p class="text-xs text-zinc-500">{{ vend.count }} resultado(s) · as vendas contam {{ fl.de || fl.ate ? 'no período escolhido' : 'desde sempre' }}</p>

        <div v-if="carregando && !vend.results.length" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
        <div v-else class="space-y-3" data-teste="lista-vendedores">
          <div v-for="v in vend.results" :key="v.tipo + v.id" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" :data-teste="`vendedor-${v.tipo}-${v.id}`">
            <div class="px-5 py-4 flex flex-wrap items-center gap-x-4 gap-y-2">
              <div class="flex-1 min-w-[200px]">
                <p class="font-semibold text-zinc-100">{{ v.nome }}</p>
                <p class="text-[11px] text-zinc-500">
                  {{ v.tipo === 'pos' ? `POS · ${v.codigo_pos}` : 'Loja' }} · {{ v.dono.nome }} · {{ v.dono.email }}
                  <template v-if="v.tipo === 'pos' && v.loja"> · loja {{ v.loja.nome }}</template>
                </p>
              </div>
              <div class="text-xs"><span class="text-zinc-500">NIF </span><span class="tabular-nums text-zinc-200">{{ v.nif || '—' }}</span></div>
              <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', regimeClasse(v)]">{{ regimeNome(v) }}</span>
              <span class="text-[11px] text-zinc-500">Declaração {{ v.aceites_em ? data(v.aceites_em) : '—' }}</span>
              <div v-if="v.tipo === 'loja'" class="text-xs flex gap-3">
                <span class="text-zinc-400">{{ v.vendas }} vendas</span>
                <span class="text-green-400">{{ v.faturadas }} faturadas</span>
                <span :class="v.por_faturar ? 'text-amber-300 font-bold' : 'text-zinc-500'">{{ v.por_faturar }} por faturar</span>
              </div>
              <button type="button" @click="abrirFicha(v.tipo, v.id)" data-teste="abrir-ficha"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">Abrir ficha</button>
            </div>
            <!-- POS desta loja -->
            <div v-if="v.pos && v.pos.length" class="border-t border-zinc-800 bg-zinc-950/40">
              <div v-for="p in v.pos" :key="p.id" class="pl-9 pr-5 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-zinc-800/60 first:border-0">
                <p class="flex-1 min-w-[180px] text-sm text-zinc-300">↳ {{ p.nome }} <span class="text-[11px] text-zinc-500">· {{ p.codigo_pos }}</span></p>
                <span class="text-xs tabular-nums text-zinc-400">NIF {{ p.nif || '—' }}</span>
                <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', regimeClasse(p)]">{{ regimeNome(p) }}</span>
                <button type="button" @click="abrirFicha('pos', p.id)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Ficha</button>
              </div>
            </div>
          </div>
          <p v-if="!vend.results.length" class="text-center py-10 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Sem resultados.</p>
        </div>
        <PaginacaoLista :count="vend.count" :limit="LIMITE" :offset="offset" @ir="carregarVendedores" />
      </template>

      <!-- ═══ PESQUISAR DOCUMENTOS ═══ -->
      <template v-else-if="tab === 'pesquisa'">
        <form @submit.prevent="pesquisar(0)" class="flex flex-wrap gap-2">
          <input v-model.trim="pq" type="search" placeholder="Nº de fatura, E-123 / S-45 / C-12-202610, nº de encomenda, NIF, loja, email do cliente…"
            aria-label="Pesquisar documentos" data-teste="pesquisa-q"
            class="flex-1 min-w-[240px] px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
          <button type="submit" :disabled="pq.length < 2" class="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">Pesquisar</button>
        </form>
        <p class="text-[11px] text-zinc-500">Procura em todas as lojas e POS: faturas em vigor e anuladas, comprovativos (E- encomenda, S- mensalidade), extratos de comissões (C-loja-AAAAMM), vendedores e clientes.</p>
        <ResultadosPesquisa v-if="pRes" :res="pRes" :limit="LIMITE" :offset="pOffset" @ir="pesquisar" @abrir="abrirResultado" />
      </template>

      <!-- ═══ FATURAS DO BENDE (agrupadas por loja, com os seus POS) ═══ -->
      <template v-else>
        <form @submit.prevent="carregarBende(0)" class="flex flex-wrap items-end gap-2">
          <input v-model.trim="fb.q" type="search" placeholder="Loja, POS, NIF ou dono" aria-label="Pesquisar nas faturas do Bende" data-teste="bende-q"
            class="flex-1 min-w-[200px] px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
          <label class="text-[11px] text-zinc-500">De <input type="month" v-model="fb.de" @change="carregarBende(0)" aria-label="Mês inicial" data-teste="bende-de"
            class="ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <label class="text-[11px] text-zinc-500">a <input type="month" v-model="fb.ate" @change="carregarBende(0)" aria-label="Mês final" data-teste="bende-ate"
            class="ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <label class="flex items-center gap-1.5 text-xs text-zinc-400 px-1">
            <input type="checkbox" v-model="fb.por_faturar" @change="carregarBende(0)" class="accent-red-600" data-teste="bende-por-faturar" /> Só por faturar
          </label>
          <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
        </form>
        <p v-if="bende" class="text-xs text-zinc-500" data-teste="bende-totais">
          {{ bende.totais.grupos }} loja(s)/POS · {{ bende.totais.documentos }} documento(s) · {{ euros(bende.totais.valor) }} ·
          <span :class="bende.totais.por_faturar ? 'text-amber-300 font-bold' : ''">{{ bende.totais.por_faturar }} por faturar</span>
        </p>
        <div v-if="carregando && !bende" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
        <div v-else-if="bende" class="space-y-3" data-teste="bende-grupos">
          <div v-for="g in bende.results" :key="g.tipo + g.id" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" :data-teste="`bende-${g.tipo}-${g.id}`">
            <div class="px-5 py-3 flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-zinc-800">
              <div class="flex-1 min-w-[200px]">
                <p class="font-semibold text-zinc-100">{{ g.nome }}</p>
                <p class="text-[11px] text-zinc-500">{{ g.tipo === 'pos' ? `POS · ${g.codigo_pos}` : 'Loja' }} · NIF {{ g.nif || '—' }} · {{ g.dono.email }}</p>
              </div>
              <span class="text-sm font-bold text-zinc-100">{{ euros(g.valor) }}</span>
              <span :class="['text-xs', g.por_faturar ? 'text-amber-300 font-bold' : 'text-green-400']">{{ g.por_faturar ? `${g.por_faturar} por faturar` : 'Tudo faturado' }}</span>
              <button type="button" @click="abrirFicha(g.tipo, g.id, 'bende')" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Ficha</button>
            </div>
            <div class="divide-y divide-zinc-800">
              <div v-for="d in g.documentos" :key="d.referencia" class="px-5 py-3 flex flex-wrap items-center gap-3" :data-teste="`doc-${d.referencia}`">
                <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', d.tipo === 'comissoes' ? 'bg-sky-500/15 text-sky-300' : 'bg-violet-500/15 text-violet-300']">
                  {{ d.tipo === 'comissoes' ? 'Comissões' : 'Mensalidade' }}
                </span>
                <div class="flex-1 min-w-[180px]">
                  <p class="text-sm text-zinc-200">{{ d.titulo }} <span class="text-[11px] text-zinc-500">· {{ d.referencia }}</span></p>
                  <p class="text-[11px] text-zinc-500">
                    <template v-if="d.tipo === 'mensalidade'">{{ d.alvo_tipo === 'pos' ? d.alvo + ' · ' : '' }}paga a {{ data(d.data) }} · {{ d.metodo_nome }}</template>
                    <template v-else>{{ d.comissoes }} venda(s)</template>
                    <template v-if="d.anuladas"> · <span class="text-red-300">{{ d.anuladas }} anulada(s)</span></template>
                  </p>
                </div>
                <span class="text-sm font-bold text-zinc-100">{{ euros(d.valor) }}</span>
                <button type="button" @click="d.tipo === 'comissoes' ? extrato(g, d) : comprovativo(d)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">
                  {{ d.tipo === 'comissoes' ? 'Extrato' : 'Comprovativo' }}
                </button>
                <RegistarFaturaBende :fatura="d.fatura" :url="d.url" @atualizado="r => aposFaturaBende(g, d, r)" />
              </div>
            </div>
          </div>
          <p v-if="!bende.results.length" class="text-center py-10 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Nada para faturar neste período.</p>
          <PaginacaoLista :count="bende.count" :limit="LIMITE" :offset="bOffset" @ir="carregarBende" />
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, descarregarComprovativoSubscricao } from '@/utils/documentos'
import FaturacaoFicha from './FaturacaoFicha.vue'
import AbasVendedores from '@/components/fiscal/AbasVendedores.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import RegistarFaturaBende from '@/components/fiscal/RegistarFaturaBende.vue'
import ResultadosPesquisa from '@/components/fiscal/ResultadosPesquisa.vue'

const TABS = [
  { key: 'vendedores', label: 'Vendedores' },
  { key: 'pesquisa',   label: 'Pesquisar documentos' },
  { key: 'bende',      label: 'Faturas do Bende' },
]
const LIMITE = 20

export default {
  name: 'AdminFaturacao',
  components: { AbasVendedores, FaturacaoFicha, PaginacaoLista, RegistarFaturaBende, ResultadosPesquisa },
  data () {
    const hoje = new Date()
    const mesAtual = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`
    return {
      TABS, LIMITE,
      lojaDoPos: null,      // POS de uma loja aberto: a aba ativa é a da loja
      tab: 'vendedores',
      carregando: false,
      erro: '',
      fl: { q: '', tipo: '', regime: '', dados: '', por_faturar: false, de: '', ate: '' },
      vend: { count: 0, results: [] },
      offset: 0,
      ficha: null,            // { tipo, id, aba, q }
      pq: '', pRes: null, pOffset: 0,
      fb: { q: '', de: mesAtual, ate: mesAtual, por_faturar: false },
      bende: null, bOffset: 0,
    }
  },
  computed: {
    abaAtiva () {
      if (!this.ficha) return null
      if (this.ficha.tipo === 'pos' && this.lojaDoPos) return `loja-${this.lojaDoPos}`
      return `${this.ficha.tipo}-${this.ficha.id}`
    },
  },
  created () {
    this.carregarVendedores(0)
    // ?ficha=loja-12&aba=bende (ex.: "Ver na Faturação" em Subscrições → Cobranças)
    const m = /^(loja|pos)-(\d+)$/.exec(this.$route.query.ficha || '')
    if (m) this.abrirFicha(m[1], Number(m[2]), this.$route.query.aba || '')
  },
  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s).toLocaleDateString('pt-PT') : '—' },
    regimeNome (o) { return !o.regime_fiscal ? 'Por preencher' : o.regime_fiscal === 'atividade' ? 'Atividade' : 'Particular' },
    regimeClasse (o) {
      if (!o.regime_fiscal) return 'bg-amber-500/15 text-amber-300'
      return o.regime_fiscal === 'atividade' ? 'bg-sky-500/15 text-sky-300' : 'bg-zinc-700 text-zinc-300'
    },
    mudarTab (t) {
      this.tab = t
      if (t === 'bende' && !this.bende) this.carregarBende()
    },
    async carregar (fn) {
      this.carregando = true; this.erro = ''
      try { await fn() } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar.'
      } finally { this.carregando = false }
    },
    carregarVendedores (offset = this.offset) {
      this.offset = offset
      return this.carregar(async () => {
        const params = { limit: LIMITE, offset }
        for (const [k, v] of Object.entries(this.fl)) if (v) params[k] = k === 'por_faturar' ? 1 : v
        this.vend = (await api.get('/app/admin/faturacao/vendedores/', { params })).data
      })
    },
    pesquisar (offset = 0) {
      this.pOffset = offset
      return this.carregar(async () => {
        this.pRes = (await api.get('/app/admin/faturacao/pesquisa/', { params: { q: this.pq, limit: LIMITE, offset } })).data
      })
    },
    carregarAbas () { this.$refs.abas?.recarregar() },
    selecionar (v) {
      if (v) this.abrirFicha(v.tipo, v.id)
      else this.ficha = null
    },
    abrirFicha (tipo, id, aba = '', q = '') {
      if (tipo !== 'pos') this.lojaDoPos = null
      this.ficha = { tipo, id, aba, q }
      window.scrollTo({ top: 0 })
    },
    abrirResultado (r) {
      const v = r.vendedor
      if (r.tipo === 'venda') return this.abrirFicha('loja', v.id, 'vendas', r.referencia)
      if (r.tipo === 'anulada') return this.abrirFicha(v.tipo, v.id, r.referencia.startsWith('E-') ? 'vendas' : 'bende', r.referencia.startsWith('E-') ? r.referencia : '')
      if (r.tipo === 'mensalidade' || r.tipo === 'comissoes') return this.abrirFicha(v.tipo, v.id, 'bende')
      return this.abrirFicha(v.tipo, v.id)
    },
    carregarBende (offset = this.bOffset) {
      this.bOffset = offset
      return this.carregar(async () => {
        const params = { limit: LIMITE, offset, de: this.fb.de, ate: this.fb.ate }
        if (this.fb.q) params.q = this.fb.q
        if (this.fb.por_faturar) params.por_faturar = 1
        this.bende = (await api.get('/app/admin/faturacao/bende/', { params })).data
      })
    },
    // registar / substituir / anular sem recarregar a lista
    aposFaturaBende (g, d, r) {
      const tinha = !!d.fatura
      d.fatura = r.fatura
      if (tinha) d.anuladas++                       // substituída ou anulada: a anterior fica no histórico
      const passo = (tinha ? 1 : 0) - (d.fatura ? 1 : 0)   // +1 voltou a "por faturar", -1 ficou faturada
      g.por_faturar += passo
      this.bende.totais.por_faturar += passo
      this.carregarAbas()
    },
    comprovativo (d) { descarregarComprovativoSubscricao(d) },
    extrato (g, d) {
      descarregarPdf(`/app/admin/faturacao/comissoes/${g.id}/${d.mes}/extrato/`, `extrato-comissoes-${g.id}-${d.mes}.pdf`)
    },
  },
}
</script>
