<template>
  <!-- Pagamentos com cartão (vinti4): cada ida de alguém à página da SISP e o que a SISP respondeu.
       Admin → Pagamentos → Cartão (todas: Views/pagamentosAdminView.py vinti4_*) e backoffice da loja → Pagamentos
       (só as da loja: Views/lojaCartaoView.py) — os mesmos filtros e totais (pagamentos/cartao_listas.py). -->
  <div class="space-y-4" data-teste="pagamentos-vinti4">
    <div class="flex gap-1 border-b border-zinc-800">
      <button v-for="a in ABAS" :key="a.key" type="button" @click="aba = a.key" :data-teste="`v4-aba-${a.key}`"
        :class="['px-3 py-2 text-xs font-semibold border-b-2 -mb-px transition',
                 aba === a.key ? 'border-red-500 text-zinc-100' : 'border-transparent text-zinc-500 hover:text-zinc-300']">{{ a.label }}</button>
    </div>
    <p v-if="admin && d?.ambiente" data-teste="v4-ambiente"
       :class="['text-[11px] px-3 py-1.5 rounded-lg border', d.ambiente === 'teste'
         ? 'border-amber-500/30 bg-amber-500/10 text-amber-200' : 'border-green-500/30 bg-green-500/10 text-green-300']">
      Ambiente da SISP: <strong>{{ d.ambiente === 'teste' ? 'TESTE' : 'Produção' }}</strong>
      · vinti4 {{ d.ligado ? 'ligado' : 'desligado (pagamentos simulados)' }}
    </p>
    <ReconciliacaoVBVT v-if="aba === 'vbvt'" ref="vbvt" :base="vbvtBase" :base-cartao="base" :admin="admin"
                       :lojas="lojas" :pode-agir="podeAgir" @mudou="carregar(offset, true)" />
    <template v-else>

    <!-- totais do período (sem o filtro de estado) -->
    <div v-if="d?.totais" class="grid grid-cols-2 lg:grid-cols-5 gap-3" data-teste="v4-totais">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3">
        <p class="text-[11px] text-zinc-500">Pago com cartão</p>
        <p class="text-lg font-bold text-zinc-100 tabular-nums">{{ dinheiro(d.totais.valor_pago) }}</p>
        <p class="text-[11px] text-zinc-500">{{ d.totais.pagas }} pagamento(s)</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3">
        <p class="text-[11px] text-zinc-500">Estornado</p>
        <p class="text-lg font-bold text-zinc-100 tabular-nums">{{ dinheiro(d.totais.valor_estornado) }}</p>
        <p class="text-[11px] text-zinc-500">{{ d.totais.estornos }} estorno(s)</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3">
        <p class="text-[11px] text-zinc-500">Comissões da SISP</p>
        <p class="text-lg font-bold text-zinc-100 tabular-nums">{{ dinheiro(d.totais.comissoes_sisp) }}</p>
        <p class="text-[11px] text-zinc-500">pelos ficheiros VBVT</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3">
        <p class="text-[11px] text-zinc-500">Líquido (deve chegar ao banco)</p>
        <p class="text-lg font-bold text-green-300 tabular-nums">{{ dinheiro(d.totais.liquido) }}</p>
        <p class="text-[11px] text-zinc-500">pago − estornos − comissões</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3 col-span-2 lg:col-span-1">
        <p class="text-[11px] text-zinc-500">A verificar</p>
        <p class="text-sm text-amber-300"><span class="font-bold tabular-nums">{{ d.totais.por_confirmar }}</span> por confirmar</p>
        <p class="text-sm text-zinc-300"><span class="font-bold tabular-nums">{{ d.totais.por_reconciliar }}</span> pagas por reconciliar</p>
      </div>
    </div>

    <div class="flex flex-wrap gap-2">
      <button v-for="e in estados" :key="e.valor" type="button" @click="filtrar(e.valor)" :data-teste="`v4-estado-${e.valor}`"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold border transition',
                 f.estado === e.valor ? 'bg-zinc-700 border-zinc-600 text-zinc-100' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ e.nome }} <span class="opacity-70 tabular-nums">{{ e.n }}</span>
      </button>
      <button v-if="f.estado" type="button" @click="filtrar('')" class="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200">Todos os estados</button>
    </div>
    <form class="flex flex-wrap items-end gap-2" @submit.prevent="carregar(0)">
      <label class="text-[11px] text-zinc-500">Pesquisa
        <input v-model.trim="f.q" :placeholder="admin ? 'Referência, loja, cliente, cartão…' : 'Referência, cliente, cartão…'"
               maxlength="60" data-teste="v4-q"
               class="block mt-1 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 w-56" />
      </label>
      <label class="text-[11px] text-zinc-500">O que se pagava
        <select v-model="f.tipo" @change="carregar(0)" data-teste="v4-tipo"
                class="block mt-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
          <option value="">Tudo</option>
          <option v-for="t in tiposFiltro" :key="t.v" :value="t.v">{{ t.t }}</option>
        </select>
      </label>
      <label class="text-[11px] text-zinc-500">Reconciliação
        <select v-model="f.reconciliacao" @change="carregar(0)" data-teste="v4-reconciliacao"
                class="block mt-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
          <option value="">Todas</option>
          <option value="falta">Pagas por reconciliar</option>
          <option value="feita">Confirmadas no VBVT</option>
        </select>
      </label>
      <template v-if="admin">
        <label class="text-[11px] text-zinc-500">Contrato
          <select v-model="f.credenciais" @change="carregar(0)" class="block mt-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
            <option value="">Bendi e lojas</option><option value="bendi">Só da Bendi (mensalidades, comissões)</option><option value="lojas">Só das lojas</option>
          </select>
        </label>
        <label v-if="lojas.length" class="text-[11px] text-zinc-500">Loja
          <select v-model="f.loja_id" @change="carregar(0)" data-teste="v4-loja"
                  class="block mt-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 max-w-[12rem]">
            <option value="">Todas</option>
            <option v-for="l in lojas" :key="l.id" :value="String(l.id)">{{ l.nome }}</option>
          </select>
        </label>
      </template>
      <template v-if="!temDatas">
        <label class="text-[11px] text-zinc-500">De
          <input v-model="f.de" type="date" @change="carregar(0)" data-teste="v4-de"
                 class="block mt-1 px-2 py-1 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200" />
        </label>
        <label class="text-[11px] text-zinc-500">Até
          <input v-model="f.ate" type="date" @change="carregar(0)" data-teste="v4-ate"
                 class="block mt-1 px-2 py-1 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200" />
        </label>
      </template>
      <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
      <button v-if="filtrado" type="button" @click="limpar" class="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200">Limpar filtros</button>
      <button type="button" @click="csv" :disabled="aDescarregar" data-teste="v4-csv"
              class="ml-auto px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-200 text-xs font-semibold">
        <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV</button>
    </form>
    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <div v-if="carregando && !d" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <div v-else-if="d" class="bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800" data-teste="v4-lista">
      <div v-for="t in d.results" :key="t.id" class="px-4 py-3" :data-teste="`v4-${t.ref}`">
        <button type="button" class="w-full text-left flex flex-wrap items-center gap-x-3 gap-y-1" @click="abrir(t)">
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', COR[t.estado] || 'bg-zinc-700 text-zinc-300']">{{ t.estado_nome }}</span>
          <span v-if="t.estornada_em" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-zinc-700 text-zinc-300">Estornada</span>
          <span v-else-if="t.reconciliada_em" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-500/10 text-green-400" title="Confirmada no ficheiro VBVT da SISP">✓ VBVT</span>
          <div class="flex-1 min-w-[200px]">
            <p class="text-sm text-zinc-200">{{ t.descricao || t.referencia }}
              <span class="text-[11px] text-zinc-500">· {{ t.ref }}</span></p>
            <p class="text-[11px] text-zinc-500">
              {{ t.tipo_nome || t.tipo }}<template v-if="admin"> · {{ t.loja ? t.loja.nome : 'Bendi' }}</template>
              · {{ t.pagador || '—' }} · {{ t.criada_em }}
              <template v-if="t.pan"> · {{ t.pan }}</template>
            </p>
            <p v-if="t.mensagem || t.erro" class="text-[11px] text-amber-300 mt-0.5">{{ t.mensagem || t.erro }}</p>
          </div>
          <span class="text-sm font-bold tabular-nums text-zinc-100">{{ t.montante }} CVE</span>
        </button>
        <div v-if="aberto && aberto.id === t.id" class="mt-3 rounded-xl bg-zinc-950/60 border border-zinc-800 p-3 space-y-2 text-[11px] text-zinc-400" data-teste="v4-ficha">
          <div class="grid sm:grid-cols-2 gap-x-6 gap-y-1">
            <p>Nossa referência: <span class="text-zinc-200">{{ aberto.referencia }}</span></p>
            <p>POS ID: <span class="text-zinc-200">{{ aberto.pos_id }}</span></p>
            <p v-if="aberto.transacao">Nº da transação: <span class="text-zinc-200">{{ aberto.transacao }}</span></p>
            <p v-if="aberto.confirmada_por">Confirmada por: <span class="text-zinc-200">{{ CONFIRMADA[aberto.confirmada_por] || aberto.confirmada_por }}</span></p>
            <p v-if="aberto.efeito">Efeito: <span class="text-zinc-200">{{ aberto.efeito }}</span></p>
            <p v-if="aberto.erro_codigo">Código de erro: <span class="text-zinc-200">{{ aberto.erro_codigo }}</span></p>
            <p v-if="aberto.terminada_em">Terminada a: <span class="text-zinc-200">{{ aberto.terminada_em }}</span></p>
            <p>Consultas à API de estado: <span class="text-zinc-200">{{ aberto.consultas }}</span></p>
            <p v-if="aberto.reconciliada_em">No ficheiro VBVT: <span class="text-zinc-200">{{ aberto.reconciliada_em }}
              <template v-if="aberto.tipo_cartao"> · {{ aberto.tipo_cartao }}</template>
              <template v-if="aberto.comissao_sisp"> · comissão SISP {{ aberto.comissao_sisp }} CVE</template></span></p>
            <p v-if="aberto.estornada_em">Estorno no VBVT: <span class="text-zinc-200">{{ aberto.estornada_em }}</span></p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button v-if="podeAgir" type="button" @click="perguntar" :disabled="perguntando" data-teste="v4-perguntar"
                    class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-200 font-semibold"
                    title="Pergunta já à API de estado da SISP (Portal do Comerciante) se este pagamento foi feito">
              {{ perguntando ? 'A perguntar…' : 'Perguntar à SISP' }}</button>
            <span v-if="consulta" :class="consulta.erro ? 'text-red-300' : 'text-zinc-300'" data-teste="v4-consulta">{{ consulta.texto }}</span>
          </div>
          <div v-if="aberto.reembolsos?.length" class="space-y-1" data-teste="v4-reembolsos">
            <p class="font-semibold text-zinc-300">Reembolsos deste pagamento</p>
            <router-link v-for="r in aberto.reembolsos" :key="r.titulo" :to="r.link" :data-teste="`v4-reembolso-${r.estado}`"
                         class="flex flex-wrap items-center gap-x-2 gap-y-0.5 rounded-lg border border-zinc-800 px-2 py-1.5 hover:bg-zinc-900">
              <span class="text-zinc-200">{{ r.titulo }}</span>
              <span :class="['px-1.5 py-0.5 rounded-full text-[10px] font-semibold', r.estado === 'reembolsado'
                ? 'bg-emerald-500/15 text-emerald-300' : ['recusado', 'cancelado'].includes(r.estado)
                  ? 'bg-zinc-700/60 text-zinc-300' : 'bg-amber-500/15 text-amber-300']">{{ r.estado_nome }}</span>
              <span class="tabular-nums text-zinc-300">{{ r.valor }}</span>
              <span v-if="r.referencia" class="text-zinc-500">· estorno {{ r.referencia }}</span>
              <span v-if="r.em" class="text-zinc-500">· {{ r.em }}</span>
              <span class="ml-auto text-zinc-400">Abrir →</span>
            </router-link>
          </div>
          <p v-if="!admin && aberto.estado === 'paga'" class="text-zinc-500">
            Para devolver o dinheiro ao cliente usa Devoluções; o estorno do cartão faz-se no Portal do Comerciante da SISP.</p>
          <p v-if="aberto.erro" class="text-amber-300">Detalhe: {{ aberto.erro }}</p>
          <router-link v-if="aberto.destino" :to="aberto.destino" class="inline-block text-zinc-300 hover:text-white">Ver o que se pagava →</router-link>
          <div>
            <p class="font-semibold text-zinc-300 mb-1">O que a SISP respondeu</p>
            <p v-if="!aberto.respostas?.length" class="text-zinc-500">Nada ainda (o cliente não voltou da página da SISP).</p>
            <details v-for="(r, i) in aberto.respostas" :key="i" class="mb-1">
              <summary class="cursor-pointer text-zinc-300">{{ r.origem === 'estado' ? 'API de estado' : 'Resposta' }} · {{ quando(r.em) }}</summary>
              <pre class="mt-1 p-2 rounded-lg bg-black/40 text-zinc-300 overflow-x-auto whitespace-pre-wrap break-all">{{ formatar(r.campos) }}</pre>
            </details>
          </div>
        </div>
      </div>
      <p v-if="!d.results.length" class="text-center py-10 text-sm text-zinc-500">
        {{ filtrado ? 'Nenhuma transação com estes filtros.' : 'Ainda não há pagamentos com cartão.' }}</p>
    </div>
    <PaginacaoLista v-if="d" :count="d.count" :limit="LIMITE" :offset="offset" @ir="carregar" />
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import ReconciliacaoVBVT from '@/components/admin/ReconciliacaoVBVT.vue'
import { descarregarPdf } from '@/utils/documentos'
import { formatarDinheiro } from '@/utils/dinheiro'

const LIMITE = 20
const COR = {
  paga: 'bg-green-500/15 text-green-300', iniciada: 'bg-sky-500/15 text-sky-300', falhada: 'bg-red-500/15 text-red-300',
  cancelada: 'bg-zinc-700 text-zinc-300', expirada: 'bg-zinc-700 text-zinc-400', por_confirmar: 'bg-amber-500/15 text-amber-300',
}
const TIPOS = [{ v: 'encomenda', t: 'Encomendas' }, { v: 'marcacao', t: 'Marcações' },
  { v: 'fatura', t: 'Mensalidades' }, { v: 'comissoes', t: 'Comissões' }]
const CONFIRMADA = { resposta: 'resposta da SISP', estado: 'API de estado', admin: 'admin' }
const ABAS = [{ key: 'transacoes', label: 'Transações' }, { key: 'vbvt', label: 'Reconciliação (ficheiros VBVT)' }]
const RESULTADO = { paga: 'a SISP confirma que foi paga', nao_paga: 'a SISP diz que não foi paga' }
const VAZIO = { estado: '', q: '', tipo: '', reconciliacao: '', credenciais: '', loja_id: '', de: '', ate: '' }

export default {
  name: 'PagamentosVinti4',
  components: { PaginacaoLista, ReconciliacaoVBVT },
  emits: ['carregado'],
  props: {
    // período escolhido pela página (Admin → Pagamentos); sem ele, o componente mostra os seus campos De/Até
    datas: { type: Object, default: null },
    base: { type: String, default: '/app/admin/pagamentos/vinti4' },
    vbvtBase: { type: String, default: '/app/admin/pagamentos/vbvt' },
    admin: { type: Boolean, default: true },
    podeAgir: { type: Boolean, default: true },        // false: admin a ver o backoffice (só leitura)
    nomeCsv: { type: String, default: 'cartao-vinti4' },
  },
  data () {
    return {
      LIMITE, COR, CONFIRMADA, ABAS, aba: 'transacoes', d: null, offset: 0,
      f: { ...VAZIO }, aberto: null, carregando: false, erro: '',
      perguntando: false, consulta: null, aDescarregar: false,
    }
  },
  computed: {
    estados () { return this.d?.estados || [] },
    lojas () { return this.d?.lojas || [] },     // só no admin: lojas com pagamentos com cartão
    temDatas () { return this.datas !== null },
    tiposFiltro () { return this.admin ? TIPOS : TIPOS.slice(0, 2) },
    filtrado () { return Object.entries(this.f).some(([k, v]) => v && k !== 'estado') || !!this.f.estado },
    params () {
      const p = { ...(this.datas || {}) }
      for (const [k, v] of Object.entries(this.f)) if (v) p[k] = v
      return p
    },
  },
  watch: {
    datas () { this.carregar(0) },
  },
  created () { this.carregar(0) },
  methods: {
    quando (d) { return d ? new Date(d).toLocaleString('pt-PT') : '' },
    dinheiro (v) { return formatarDinheiro(v) },
    formatar (o) { try { return JSON.stringify(o, null, 2) } catch (e) { return String(o) } },
    filtrar (e) { this.f.estado = e; this.carregar(0) },
    limpar () { this.f = { ...VAZIO }; this.carregar(0) },
    // tempo real (Admin → Pagamentos e backoffice → Pagamentos): a lista, a ficha aberta e a aba de reconciliação
    recarregar () {
      if (this.aba === 'vbvt') return this.$refs.vbvt?.carregar()
      if (this.aberto && !this.perguntando) {
        const id = this.aberto.id
        api.get(`${this.base}/${id}/`)
          .then(({ data }) => { if (this.aberto?.id === id) this.aberto = data })
          .catch(() => {})
      }
      return this.carregar(this.offset, true)
    },
    async carregar (offset = this.offset, silencioso = false) {
      this.offset = offset
      if (!silencioso) { this.carregando = true; this.erro = '' }
      try {
        const { data } = await api.get(`${this.base}/`, { params: { ...this.params, limit: LIMITE, offset } })
        this.d = data
        this.$emit('carregado', data)
        // a página corrente ficou vazia (filtro mudou por baixo, em tempo real): volta à anterior
        if (!data.results.length && offset > 0 && data.count) this.carregar(Math.max(0, offset - LIMITE), silencioso)
      } catch (e) {
        if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar as transações com cartão.'
      } finally { if (!silencioso) this.carregando = false }
    },
    async csv () {
      this.aDescarregar = true
      this.erro = ''
      try {
        await descarregarPdf(`${this.base}/csv/`, `${this.nomeCsv}-${this.f.de || this.datas?.de || 'inicio'}-${this.f.ate || this.datas?.ate || 'hoje'}.csv`, this.params)
      } catch (e) {
        this.erro = 'Não foi possível descarregar o CSV (mais de 5000 transações? escolhe um período mais curto).'
      } finally { this.aDescarregar = false }
    },
    async abrir (t) {
      if (this.aberto?.id === t.id) { this.aberto = null; return }
      this.consulta = null
      try {
        const { data } = await api.get(`${this.base}/${t.id}/`)
        this.aberto = data
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível abrir a transação.' }
    },
    async perguntar () {
      this.perguntando = true
      this.consulta = null
      try {
        const { data } = await api.post(`${this.base}/${this.aberto.id}/consultar/`)
        const r = data.resposta || {}
        this.consulta = {
          erro: !data.resultado,
          texto: data.resultado
            ? `${RESULTADO[data.resultado]} (${r.transactionStatusDescription || r.msg || ''}) · estado: ${data.transacao.estado_nome}`
            : `A SISP não respondeu ao pedido: ${r.msg || r.erro || 'sem resposta'}`,
        }
        this.aberto = data.transacao
        this.carregar(this.offset, true)
      } catch (e) {
        this.consulta = { erro: true, texto: e.response?.data?.detail || 'Não foi possível perguntar à SISP.' }
      } finally { this.perguntando = false }
    },
  },
}
</script>
