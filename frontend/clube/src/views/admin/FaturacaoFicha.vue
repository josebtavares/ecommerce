<template>
  <!-- Admin → Faturação → ficha fiscal de uma loja ou POS (backend admin_ficha / admin_loja_vendas / admin_historico) -->
  <div class="space-y-5" data-teste="ficha-fiscal">
    <button type="button" @click="$emit('fechar')" class="text-xs text-zinc-400 hover:text-zinc-200">← Voltar</button>

    <div v-if="carregando && !ficha" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <p v-else-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <template v-else-if="ficha">
      <!-- cabeçalho -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 flex flex-wrap items-start gap-4">
        <div class="flex-1 min-w-[220px]">
          <p class="text-[11px] uppercase tracking-wider text-zinc-500">{{ ficha.tipo === 'pos' ? `POS · ${ficha.codigo_pos}` : 'Loja' }}</p>
          <h3 class="text-xl font-bold text-zinc-100" data-teste="ficha-nome">{{ ficha.nome }}</h3>
          <p class="text-xs text-zinc-400 mt-1">{{ ficha.dono.nome }} · {{ ficha.dono.email }}<template v-if="ficha.dono.telefone"> · {{ ficha.dono.telefone }}</template></p>
          <p v-if="ficha.tipo === 'pos' && ficha.loja" class="text-xs text-zinc-500 mt-1">
            Ligado à loja <button type="button" class="underline text-zinc-300" @click="$emit('abrir', 'loja', ficha.loja.id)">{{ ficha.loja.nome }}</button>
          </p>
        </div>
        <div class="text-right">
          <p class="text-[11px] text-zinc-500">NIF</p>
          <p class="text-lg font-bold tabular-nums text-zinc-100">{{ ficha.nif || '—' }}</p>
          <span :class="['inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold', regimeClasse(ficha)]">{{ regimeNome(ficha) }}</span>
        </div>
        <!-- pacote para a DNRE: CSVs + comprovativos, extratos e faturas (em vigor e anuladas) do período -->
        <form @submit.prevent="exportar" class="w-full border-t border-zinc-800 pt-3 flex flex-wrap items-end gap-2" data-teste="exportar-zip">
          <span class="text-xs text-zinc-400 mr-1">Exportar arquivo (ZIP)</span>
          <label class="text-[11px] text-zinc-500">De <input type="date" v-model="zip.de" class="ml-1 px-2 py-1.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <label class="text-[11px] text-zinc-500">a <input type="date" v-model="zip.ate" class="ml-1 px-2 py-1.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <button type="submit" :disabled="zip.aExportar" data-teste="exportar-zip-botao"
            class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-200 text-xs font-semibold">
            <font-awesome-icon :icon="['fas', 'file-zipper']" class="mr-1" />{{ zip.aExportar ? 'A preparar…' : 'Descarregar ZIP' }}
          </button>
          <span class="text-[11px] text-zinc-500">{{ zip.de || zip.ate ? '' : 'Sem datas: desde sempre.' }} Dados fiscais, vendas, comprovativos e todas as faturas — para a DNRE.</span>
          <p v-if="zip.erro" class="w-full text-xs text-red-400" role="alert">{{ zip.erro }}</p>
        </form>
      </div>

      <div v-if="ficha.totais" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="t in cartoes" :key="t.label" class="bg-zinc-900 rounded-xl border border-zinc-800 px-4 py-3">
          <p class="text-[11px] text-zinc-500">{{ t.label }}</p>
          <p :class="['text-lg font-bold', t.cor]">{{ t.valor }}</p>
        </div>
      </div>

      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 w-fit max-w-full overflow-x-auto" role="tablist">
        <button v-for="t in abas" :key="t.key" type="button" role="tab" :aria-selected="aba === t.key ? 'true' : 'false'" @click="mudarAba(t.key)"
          :class="['px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap', aba === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t.label }}
        </button>
      </div>

      <!-- ═══ DADOS FISCAIS ═══ -->
      <template v-if="aba === 'dados'">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-x-auto">
          <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-5 pt-4 pb-1">Histórico dos dados fiscais</p>
          <p class="text-[11px] text-zinc-500 px-5 pb-3">Cada vez que o dono grava o NIF e aceita a declaração fica uma linha — o que valia em cada data.</p>
          <table class="w-full text-sm min-w-[640px]" data-teste="historico-fiscal">
            <thead>
              <tr class="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-y border-zinc-800">
                <th class="px-5 py-2">Desde</th><th class="px-5 py-2">NIF</th><th class="px-5 py-2">Vende como</th><th class="px-5 py-2">Nome</th><th class="px-5 py-2">Gravado por</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800">
              <tr v-for="(h, i) in ficha.historico_fiscal" :key="i">
                <td class="px-5 py-2 text-zinc-300">{{ quando(h.aceites_em) }} <span v-if="h.atual" class="ml-1 px-1.5 py-0.5 rounded bg-green-500/15 text-green-400 text-[10px] font-bold">em vigor</span></td>
                <td class="px-5 py-2 tabular-nums text-zinc-200">{{ h.nif }}</td>
                <td class="px-5 py-2 text-zinc-300">{{ h.regime_fiscal === 'atividade' ? 'Atividade declarada' : 'Particular' }}</td>
                <td class="px-5 py-2 text-zinc-400">{{ h.nome }}</td>
                <td class="px-5 py-2 text-zinc-400">{{ h.alterado_por ? h.alterado_por.nome : '—' }}</td>
              </tr>
              <tr v-if="!ficha.historico_fiscal.length"><td colspan="5" class="px-5 py-5 text-center text-zinc-500">Ainda não preencheu os dados fiscais.</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="ficha.tipo === 'loja'" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">POS desta loja</p>
          <p v-if="!ficha.pos.length" class="text-sm text-zinc-500">Esta loja não tem POS ligado.</p>
          <div v-for="p in ficha.pos" :key="p.id" class="flex flex-wrap items-center gap-3 py-2 border-t border-zinc-800 first:border-0">
            <span class="text-sm text-zinc-200 font-semibold flex-1">{{ p.nome }} <span class="text-zinc-500 font-normal">· {{ p.codigo_pos }}</span></span>
            <span class="text-xs tabular-nums text-zinc-400">NIF {{ p.nif || '—' }}</span>
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', regimeClasse(p)]">{{ regimeNome(p) }}</span>
            <button type="button" @click="$emit('abrir', 'pos', p.id)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Ficha</button>
          </div>
        </div>
      </template>

      <!-- ═══ VENDAS ═══ -->
      <template v-else-if="aba === 'vendas'">
        <form @submit.prevent="carregarVendas(0)" class="flex flex-wrap items-end gap-2">
          <input v-model.trim="fv.q" type="search" placeholder="Nº encomenda, nº fatura (também anulada), cliente" aria-label="Pesquisar vendas" data-teste="vendas-q"
            class="flex-1 min-w-[220px] px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
          <select v-model="fv.estado" aria-label="Estado da fatura" data-teste="vendas-estado" class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
            <option value="">Todas</option><option value="por_faturar">Por faturar</option><option value="faturada">Faturadas</option><option value="com_anuladas">Com faturas anuladas</option>
          </select>
          <label class="text-[11px] text-zinc-500">De <input type="date" v-model="fv.de" class="ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <label class="text-[11px] text-zinc-500">a <input type="date" v-model="fv.ate" class="ml-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
          <input v-model.trim="fv.min" inputmode="decimal" placeholder="Valor mín." aria-label="Valor mínimo" class="w-24 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200" />
          <input v-model.trim="fv.max" inputmode="decimal" placeholder="Valor máx." aria-label="Valor máximo" class="w-24 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200" />
          <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
          <button type="button" @click="limparVendas" class="px-2 py-1.5 text-xs text-zinc-400 hover:text-zinc-200">Limpar</button>
          <button type="button" @click="csv" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs ml-auto" :title="'Vendas do período com as faturas (CSV)'">
            <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV
          </button>
        </form>
        <p v-if="vendas.totais" class="text-xs text-zinc-500">
          {{ vendas.totais.vendas }} venda(s) · {{ dinheiro(vendas.totais.valor) }} · <span class="text-green-400">{{ vendas.totais.faturadas }} faturada(s)</span> ·
          <span :class="vendas.totais.por_faturar ? 'text-amber-300' : ''">{{ vendas.totais.por_faturar }} por faturar</span>
        </p>
        <!-- fora da tabela: no telemóvel a tabela desliza para o lado e o histórico ficava escondido -->
        <div v-if="historicoVenda" class="relative">
          <HistoricoFatura :key="historicoVenda" :referencia="historicoVenda" />
          <button type="button" @click="historicoVenda = ''" aria-label="Fechar histórico" class="absolute top-2 right-3 text-xs text-zinc-400 hover:text-zinc-200">Fechar ✕</button>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-x-auto">
          <table class="w-full text-sm min-w-[860px]" data-teste="tabela-vendas">
            <thead>
              <tr class="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
                <th class="px-4 py-3">Encomenda</th><th class="px-4 py-3">Data</th><th class="px-4 py-3">Cliente</th><th class="px-4 py-3 text-right">Valor</th>
                <th class="px-4 py-3">Estado</th><th class="px-4 py-3">Fatura</th><th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800">
              <template v-for="e in vendas.results" :key="e.id">
                <tr>
                  <td class="px-4 py-3"><p class="font-semibold text-zinc-200">#{{ e.id }}</p><p class="text-[11px] text-zinc-500">{{ e.referencia }}</p></td>
                  <td class="px-4 py-3 text-xs text-zinc-400">{{ quando(e.data) }}</td>
                  <td class="px-4 py-3"><p class="text-zinc-300">{{ e.cliente.nome }}</p><p class="text-[11px] text-zinc-500">{{ e.cliente.email }}</p></td>
                  <td class="px-4 py-3 text-right text-zinc-200">{{ dinheiro(e.valor) }}</td>
                  <td class="px-4 py-3 text-xs text-zinc-400">{{ e.status_nome }}</td>
                  <td class="px-4 py-3 text-xs">
                    <a v-if="e.fatura && e.fatura.pdf_url" :href="urlFicheiro(e.fatura.pdf_url)" target="_blank" rel="noopener" class="text-green-400 underline font-semibold">{{ e.fatura.numero }}</a>
                    <span v-else-if="e.fatura" class="text-green-400 font-semibold">{{ e.fatura.numero }}</span>
                    <span v-else class="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-bold">Por faturar</span>
                    <span v-if="e.anuladas" class="ml-1 px-1.5 py-0.5 rounded bg-red-500/15 text-red-300 font-bold">{{ e.anuladas }} anulada(s)</span>
                  </td>
                  <td class="px-4 py-3 text-right whitespace-nowrap">
                    <button v-if="e.comprovativo" type="button" @click="descarregarComprovativoEncomenda(e.id)" class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Comprovativo</button>
                    <button type="button" @click="historicoVenda = historicoVenda === e.referencia ? '' : e.referencia" :aria-expanded="historicoVenda === e.referencia ? 'true' : 'false'" data-teste="ver-historico"
                      class="ml-1 px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Histórico</button>
                  </td>
                </tr>
              </template>
              <tr v-if="!vendas.results.length"><td colspan="7" class="px-4 py-6 text-center text-zinc-500">{{ carregandoVendas ? 'A carregar…' : 'Nenhuma venda com estes filtros.' }}</td></tr>
            </tbody>
          </table>
        </div>
        <PaginacaoLista :count="vendas.count" :limit="LIMITE" :offset="offsetVendas" @ir="carregarVendas" />
      </template>

      <!-- ═══ DOCUMENTOS DO BENDE ═══ -->
      <template v-else>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="ficha-mensalidades">
          <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-5 pt-4 pb-3">Mensalidades pagas</p>
          <p v-if="!ficha.mensalidades.length" class="text-sm text-zinc-500 px-5 pb-5">Nenhuma mensalidade paga.</p>
          <div v-for="f in ficha.mensalidades" :key="f.id" class="px-5 py-3 border-t border-zinc-800 space-y-2">
            <div class="flex flex-wrap items-center gap-3">
              <div class="flex-1 min-w-[200px]">
                <p class="text-sm font-semibold text-zinc-200">{{ f.descricao }} <span class="text-[11px] text-zinc-500 font-normal">· {{ f.referencia }}</span></p>
                <p class="text-[11px] text-zinc-500">Paga a {{ quando(f.paga_em) }} · {{ f.metodo_nome }}<template v-if="f.anuladas"> · <span class="text-red-300">{{ f.anuladas }} fatura(s) anulada(s)</span></template></p>
              </div>
              <span class="text-sm font-bold text-zinc-100">{{ dinheiro(f.valor) }}</span>
              <button type="button" @click="descarregarComprovativoSubscricao(f)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Comprovativo</button>
              <button type="button" @click="alternar(f.referencia)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Histórico</button>
              <RegistarFaturaBende :fatura="f.fatura" :url="`/app/admin/faturacao/subscricoes/${f.id}/fatura/`" @atualizado="d => atualizado(f, d)" />
            </div>
            <HistoricoFatura v-if="aberto[f.referencia]" :key="f.referencia + versao" :referencia="f.referencia" />
          </div>
        </div>
        <div v-if="ficha.tipo === 'loja'" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="ficha-comissoes">
          <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-5 pt-4 pb-1">Comissões por mês</p>
          <p class="text-[11px] text-zinc-500 px-5 pb-3">Uma fatura do Bende por mês; o extrato vai em anexo no email à loja.</p>
          <p v-if="!ficha.comissoes.length" class="text-sm text-zinc-500 px-5 pb-5">Sem comissões.</p>
          <div v-for="c in ficha.comissoes" :key="c.mes" class="px-5 py-3 border-t border-zinc-800 space-y-2">
            <div class="flex flex-wrap items-center gap-3">
              <div class="flex-1 min-w-[200px]">
                <p class="text-sm font-semibold text-zinc-200">{{ nomeMes(c.mes) }} <span class="text-[11px] text-zinc-500 font-normal">· {{ c.referencia }}</span></p>
                <p class="text-[11px] text-zinc-500">{{ c.comissoes }} venda(s)<template v-if="c.anuladas"> · <span class="text-red-300">{{ c.anuladas }} fatura(s) anulada(s)</span></template></p>
              </div>
              <span class="text-sm font-bold text-zinc-100">{{ dinheiro(c.total) }}</span>
              <button type="button" @click="extrato(c)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Extrato</button>
              <button type="button" @click="alternar(c.referencia)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Histórico</button>
              <RegistarFaturaBende :fatura="c.fatura" :url="`/app/admin/faturacao/comissoes/${ficha.id}/${c.mes}/fatura/`" @atualizado="d => atualizado(c, d)" />
            </div>
            <HistoricoFatura v-if="aberto[c.referencia]" :key="c.referencia + versao" :referencia="c.referencia" />
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, descarregarComprovativoEncomenda, descarregarComprovativoSubscricao, urlFicheiro } from '@/utils/documentos'
import HistoricoFatura from '@/components/fiscal/HistoricoFatura.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import RegistarFaturaBende from '@/components/fiscal/RegistarFaturaBende.vue'

const LIMITE = 20
const vazio = () => ({ q: '', estado: '', de: '', ate: '', min: '', max: '' })

export default {
  name: 'FaturacaoFicha',
  components: { HistoricoFatura, PaginacaoLista, RegistarFaturaBende },
  props: {
    tipo: { type: String, required: true },
    id:   { type: [Number, String], required: true },
    abaInicial: { type: String, default: '' },
    qInicial:   { type: String, default: '' },
  },
  emits: ['fechar', 'abrir'],
  data () {
    return {
      LIMITE, ficha: null, carregando: false, erro: '',
      aba: this.abaInicial || 'dados',
      fv: { ...vazio(), q: this.qInicial },
      vendas: { count: 0, results: [], totais: null }, offsetVendas: 0, carregandoVendas: false,
      aberto: {}, versao: 0, historicoVenda: '',
      zip: { de: '', ate: '', aExportar: false, erro: '' },
    }
  },
  computed: {
    abas () {
      return this.tipo === 'loja'
        ? [{ key: 'dados', label: 'Dados fiscais' }, { key: 'vendas', label: 'Vendas e faturas' }, { key: 'bende', label: 'Documentos do Bende' }]
        : [{ key: 'dados', label: 'Dados fiscais' }, { key: 'bende', label: 'Documentos do Bende' }]
    },
    cartoes () {
      const t = this.ficha.totais
      return [
        { label: 'Vendas', valor: t.vendas, cor: 'text-zinc-100' },
        { label: 'Faturadas', valor: t.faturadas, cor: 'text-green-400' },
        { label: 'Por faturar', valor: t.por_faturar, cor: t.por_faturar ? 'text-amber-300' : 'text-zinc-500' },
        { label: 'Faturas anuladas', valor: t.anuladas, cor: t.anuladas ? 'text-red-300' : 'text-zinc-500' },
      ]
    },
  },
  watch: {
    id () { this.carregar() },
    tipo () { this.carregar() },
  },
  created () { this.carregar() },
  methods: {
    urlFicheiro,
    descarregarComprovativoEncomenda,
    descarregarComprovativoSubscricao,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    quando (s) { return s ? new Date(s).toLocaleDateString('pt-PT') : '—' },
    nomeMes (m) {
      const [a, mm] = m.split('-').map(Number)
      const t = new Date(a, mm - 1, 15).toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })
      return t.charAt(0).toUpperCase() + t.slice(1)
    },
    regimeNome (o) { return !o.regime_fiscal ? 'Por preencher' : o.regime_fiscal === 'atividade' ? 'Atividade' : 'Particular' },
    regimeClasse (o) {
      if (!o.regime_fiscal) return 'bg-amber-500/15 text-amber-300'
      return o.regime_fiscal === 'atividade' ? 'bg-sky-500/15 text-sky-300' : 'bg-zinc-700 text-zinc-300'
    },
    async carregar () {
      this.carregando = true; this.erro = ''; this.aberto = {}; this.historicoVenda = ''
      if (!this.abas.some(a => a.key === this.aba)) this.aba = 'dados'
      try {
        this.ficha = (await api.get(`/app/admin/faturacao/ficha/${this.tipo}/${this.id}/`)).data
        if (this.aba === 'vendas') this.carregarVendas(0)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar a ficha.'
      } finally { this.carregando = false }
    },
    mudarAba (a) {
      this.aba = a
      if (a === 'vendas' && !this.vendas.totais) this.carregarVendas(0)
    },
    async carregarVendas (offset = this.offsetVendas) {
      this.offsetVendas = offset; this.carregandoVendas = true; this.erro = ''
      const params = { limit: LIMITE, offset }
      for (const [k, v] of Object.entries(this.fv)) if (v) params[k] = v
      try {
        this.vendas = (await api.get(`/app/admin/faturacao/loja/${this.id}/vendas/`, { params })).data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar as vendas.'
      } finally { this.carregandoVendas = false }
    },
    limparVendas () { this.fv = vazio(); this.carregarVendas(0) },
    alternar (ref) { this.aberto = { ...this.aberto, [ref]: !this.aberto[ref] } },
    atualizado (linha, d) {
      linha.fatura = d.fatura
      this.versao++          // o histórico aberto volta a carregar
    },
    csv () {
      const de = this.fv.de || '2020-01-01'
      const ate = this.fv.ate || new Date().toISOString().slice(0, 10)
      descarregarPdf('/app/admin/faturacao/vendas.csv', `vendas-${this.id}-${de}-${ate}.csv`, { loja: this.id, de, ate })
    },
    async exportar () {
      this.zip.aExportar = true; this.zip.erro = ''
      const params = {}
      if (this.zip.de) params.de = this.zip.de
      if (this.zip.ate) params.ate = this.zip.ate
      try {
        await descarregarPdf(`/app/admin/faturacao/exportar/${this.tipo}/${this.id}/`,
          `arquivo-fiscal-${this.tipo}-${this.id}-${this.zip.de || 'inicio'}-${this.zip.ate || 'hoje'}.zip`, params)
      } catch (e) {
        let msg = 'Não foi possível exportar.'
        try { msg = JSON.parse(await e.response.data.text()).detail || msg } catch { /* resposta sem JSON */ }
        this.zip.erro = msg
      } finally { this.zip.aExportar = false }
    },
    extrato (c) {
      descarregarPdf(`/app/admin/faturacao/comissoes/${this.id}/${c.mes}/extrato/`, `extrato-comissoes-${this.id}-${c.mes}.pdf`)
    },
  },
}
</script>
