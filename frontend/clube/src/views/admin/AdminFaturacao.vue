<template>
  <!-- Admin → Faturação: arquivo fiscal das lojas/POS (ficha, vendas, histórico), pesquisa de documentos e faturas do Bende
       (backend faturacaoView.py) -->
  <div class="space-y-5">
    <FaturacaoFicha v-if="ficha" :key="ficha.tipo + ficha.id" :tipo="ficha.tipo" :id="ficha.id" :aba-inicial="ficha.aba" :q-inicial="ficha.q"
      @fechar="ficha = null" @abrir="(t, i) => abrirFicha(t, i)" />

    <template v-else>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-zinc-100">Faturação</h2>
          <p class="text-xs text-zinc-500 mt-0.5">Arquivo fiscal de todas as lojas e POS — nada se apaga: faturas substituídas ou anuladas ficam no histórico</p>
        </div>
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
        <div v-if="pRes" class="space-y-2" data-teste="pesquisa-resultados">
          <p class="text-xs text-zinc-500">{{ pRes.count }} resultado(s)</p>
          <div v-for="r in pRes.results" :key="r.tipo + r.referencia"
            class="bg-zinc-900 rounded-xl border border-zinc-800 px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-1">
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', TIPOS[r.tipo].cor]">{{ TIPOS[r.tipo].nome }}</span>
            <div class="flex-1 min-w-[200px]">
              <p class="text-sm font-semibold text-zinc-200">{{ r.titulo }} <span class="text-[11px] text-zinc-500 font-normal">· {{ r.referencia }}</span></p>
              <p class="text-[11px] text-zinc-500">{{ r.vendedor.nome }}<template v-if="r.detalhe"> · {{ r.detalhe }}</template><template v-if="r.data"> · {{ data(r.data) }}</template></p>
            </div>
            <span v-if="r.valor" class="text-sm font-bold text-zinc-100">{{ euros(r.valor) }}</span>
            <span v-if="r.fatura" class="text-xs text-green-400">Fatura {{ r.fatura.numero }}</span>
            <span v-else-if="['venda', 'mensalidade', 'comissoes'].includes(r.tipo)" class="text-xs text-amber-300">Por faturar</span>
            <button v-if="r.vendedor.id" type="button" @click="abrirResultado(r)" data-teste="abrir-resultado"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">Abrir</button>
          </div>
          <p v-if="!pRes.results.length" class="text-center py-8 text-sm text-zinc-500">Nada encontrado.</p>
          <PaginacaoLista :count="pRes.count" :limit="LIMITE" :offset="pOffset" @ir="pesquisar" />
        </div>
      </template>

      <!-- ═══ FATURAS DO BENDE ═══ -->
      <template v-else>
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-zinc-500">Mês</span>
          <input type="month" v-model="mes" aria-label="Mês" @change="carregarBende"
            class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" />
          <span v-if="bende" class="text-xs text-zinc-500 ml-2">{{ porFaturarBende }} por faturar</span>
        </div>
        <div v-if="carregando && !bende" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
        <template v-else-if="bende">
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="bende-subscricoes">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-5 pt-4 pb-3">Mensalidades pagas</p>
            <p v-if="!bende.subscricoes.length" class="text-sm text-zinc-500 px-5 pb-5">Nenhuma mensalidade paga neste mês.</p>
            <div v-else class="divide-y divide-zinc-800">
              <div v-for="f in bende.subscricoes" :key="f.id" class="px-5 py-3 flex flex-wrap items-center gap-3">
                <div class="flex-1 min-w-[200px]">
                  <p class="text-sm font-semibold text-zinc-200">{{ f.loja_nome }} <span class="text-zinc-500 font-normal">· {{ f.descricao }}</span></p>
                  <p class="text-[11px] text-zinc-500">Paga a {{ data(f.paga_em) }} · {{ f.metodo_nome }} · NIF {{ f.nif || '—' }}</p>
                </div>
                <span class="text-sm font-bold text-zinc-100">{{ euros(f.valor) }}</span>
                <button type="button" @click="comprovativo(f)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Comprovativo</button>
                <RegistarFaturaBende :fatura="f.fatura" :url="`/app/admin/faturacao/subscricoes/${f.id}/fatura/`" @atualizado="d => f.fatura = d.fatura" />
              </div>
            </div>
          </div>

          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="bende-comissoes">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-5 pt-4 pb-1">Comissões do mês</p>
            <p class="text-[11px] text-zinc-500 px-5 pb-3">Uma fatura por loja; o extrato vai em anexo no email à loja.</p>
            <p v-if="!bende.comissoes.length" class="text-sm text-zinc-500 px-5 pb-5">Nenhuma comissão neste mês.</p>
            <div v-else class="divide-y divide-zinc-800">
              <div v-for="c in bende.comissoes" :key="c.loja_id" class="px-5 py-3 flex flex-wrap items-center gap-3">
                <div class="flex-1 min-w-[200px]">
                  <p class="text-sm font-semibold text-zinc-200">{{ c.loja_nome }}</p>
                  <p class="text-[11px] text-zinc-500">{{ c.comissoes }} venda(s) · NIF {{ c.nif || '—' }}</p>
                </div>
                <span class="text-sm font-bold text-zinc-100">{{ euros(c.total) }}</span>
                <button type="button" @click="extrato(c)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Extrato</button>
                <RegistarFaturaBende :fatura="c.fatura" :url="`/app/admin/faturacao/comissoes/${c.loja_id}/${bende.mes}/fatura/`" @atualizado="d => c.fatura = d.fatura" />
              </div>
            </div>
          </div>
        </template>
      </template>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, descarregarComprovativoSubscricao } from '@/utils/documentos'
import FaturacaoFicha from './FaturacaoFicha.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import RegistarFaturaBende from '@/components/fiscal/RegistarFaturaBende.vue'

const TABS = [
  { key: 'vendedores', label: 'Vendedores' },
  { key: 'pesquisa',   label: 'Pesquisar documentos' },
  { key: 'bende',      label: 'Faturas do Bende' },
]
const TIPOS = {
  venda:       { nome: 'Venda',        cor: 'bg-zinc-700 text-zinc-200' },
  mensalidade: { nome: 'Mensalidade',  cor: 'bg-violet-500/15 text-violet-300' },
  comissoes:   { nome: 'Comissões',    cor: 'bg-sky-500/15 text-sky-300' },
  anulada:     { nome: 'Fatura anulada', cor: 'bg-red-500/15 text-red-300' },
  loja:        { nome: 'Loja',         cor: 'bg-emerald-500/15 text-emerald-300' },
  pos:         { nome: 'POS',          cor: 'bg-emerald-500/15 text-emerald-300' },
}
const LIMITE = 20

export default {
  name: 'AdminFaturacao',
  components: { FaturacaoFicha, PaginacaoLista, RegistarFaturaBende },
  data () {
    const hoje = new Date()
    return {
      TABS, TIPOS, LIMITE,
      tab: 'vendedores',
      carregando: false,
      erro: '',
      fl: { q: '', tipo: '', regime: '', dados: '', por_faturar: false, de: '', ate: '' },
      vend: { count: 0, results: [] },
      offset: 0,
      ficha: null,            // { tipo, id, aba, q }
      pq: '', pRes: null, pOffset: 0,
      mes: `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`,
      bende: null,
    }
  },
  computed: {
    porFaturarBende () {
      if (!this.bende) return 0
      return this.bende.subscricoes.filter(f => !f.fatura).length + this.bende.comissoes.filter(c => !c.fatura).length
    },
  },
  created () { this.carregarVendedores(0) },
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
    abrirFicha (tipo, id, aba = '', q = '') {
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
    carregarBende () {
      return this.carregar(async () => {
        const { data } = await api.get('/app/admin/faturacao/bende/', { params: { mes: this.mes } })
        this.bende = data
      })
    },
    comprovativo (f) { descarregarComprovativoSubscricao(f) },
    extrato (c) {
      descarregarPdf(`/app/admin/faturacao/comissoes/${c.loja_id}/${this.bende.mes}/extrato/`, `extrato-comissoes-${c.loja_id}-${this.bende.mes}.pdf`)
    },
  },
}
</script>
