<template>
  <!-- Admin → Faturação: dados fiscais e vendas faturadas das lojas; faturas que o Bende emite (backend faturacaoView.py) -->
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Faturação</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Quem vende fatura no e-Fatura e regista a fatura no Bende — aqui fica o registo de tudo</p>
      </div>
      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1" role="tablist">
        <button v-for="t in TABS" :key="t.key" type="button" role="tab" :aria-selected="tab === t.key ? 'true' : 'false'" @click="mudarTab(t.key)"
          :class="['px-4 py-1.5 rounded-lg text-sm font-semibold transition', tab === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t.label }}
        </button>
      </div>
    </div>

    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <!-- ═══ LOJAS E POS ═══ -->
    <template v-if="tab === 'vendedores'">
      <div class="flex flex-wrap items-center gap-2">
        <input v-model.trim="q" @keyup.enter="carregarVendedores" type="search" placeholder="Nome, NIF ou código POS" aria-label="Pesquisar"
          class="w-56 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
        <span class="text-xs text-zinc-500 ml-2">Vendas de</span>
        <input type="date" v-model="de" aria-label="De" @change="carregarVendedores"
          class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" />
        <span class="text-xs text-zinc-500">a</span>
        <input type="date" v-model="ate" aria-label="Até" @change="carregarVendedores"
          class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" />
      </div>
      <div v-if="carregando && !vendedores.length" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
      <div v-else class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-x-auto">
        <table class="w-full text-sm min-w-[860px]" data-teste="tabela-vendedores">
          <thead>
            <tr class="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
              <th class="px-4 py-3">Loja / POS</th><th class="px-4 py-3">NIF</th><th class="px-4 py-3">Vende como</th>
              <th class="px-4 py-3">Declaração</th><th class="px-4 py-3 text-right">Vendas</th>
              <th class="px-4 py-3 text-right">Faturadas</th><th class="px-4 py-3 text-right">Por faturar</th><th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800">
            <tr v-for="v in vendedores" :key="v.tipo + v.id">
              <td class="px-4 py-3">
                <p class="font-semibold text-zinc-200">{{ v.nome }}</p>
                <p class="text-[11px] text-zinc-500">{{ v.tipo === 'pos' ? 'POS' : 'Loja' }} · {{ v.dono }}</p>
              </td>
              <td class="px-4 py-3 text-zinc-300 tabular-nums">{{ v.nif || '—' }}</td>
              <td class="px-4 py-3">
                <span v-if="v.regime_fiscal" :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', v.regime_fiscal === 'atividade' ? 'bg-sky-500/15 text-sky-300' : 'bg-zinc-700 text-zinc-300']">
                  {{ v.regime_fiscal === 'atividade' ? 'Atividade' : 'Particular' }}
                </span>
                <span v-else class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300">Por preencher</span>
              </td>
              <td class="px-4 py-3 text-xs text-zinc-400">{{ v.aceites_em ? data(v.aceites_em) : '—' }}</td>
              <td class="px-4 py-3 text-right text-zinc-300">{{ v.vendas ?? '—' }}</td>
              <td class="px-4 py-3 text-right text-green-400">{{ v.faturadas ?? '—' }}</td>
              <td class="px-4 py-3 text-right" :class="v.por_faturar ? 'text-amber-300 font-bold' : 'text-zinc-500'">{{ v.por_faturar ?? '—' }}</td>
              <td class="px-4 py-3 text-right">
                <button v-if="v.tipo === 'loja' && v.vendas" type="button" @click="csv(v)" :title="`Vendas de ${v.nome} com as faturas (CSV)`"
                  class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">
                  <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV
                </button>
              </td>
            </tr>
            <tr v-if="!vendedores.length"><td colspan="8" class="px-4 py-6 text-center text-zinc-500 text-sm">Sem resultados.</td></tr>
          </tbody>
        </table>
      </div>
      <p class="text-[11px] text-zinc-500">O CSV leva os dados fiscais e a declaração da loja e, por venda, o nº e o PDF da fatura — é o que se entrega se a DNRE pedir.</p>
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
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, descarregarComprovativoSubscricao } from '@/utils/documentos'
import RegistarFaturaBende from '@/components/fiscal/RegistarFaturaBende.vue'

const TABS = [
  { key: 'vendedores', label: 'Lojas e POS' },
  { key: 'bende',      label: 'Faturas do Bende' },
]

function iso (d) { return d.toISOString().slice(0, 10) }

export default {
  name: 'AdminFaturacao',
  components: { RegistarFaturaBende },
  data () {
    const hoje = new Date()
    return {
      TABS,
      tab: 'vendedores',
      carregando: false,
      erro: '',
      q: '',
      de: iso(new Date(hoje.getFullYear(), hoje.getMonth(), 1, 12)),
      ate: iso(hoje),
      vendedores: [],
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
  created () { this.carregarVendedores() },
  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s).toLocaleDateString('pt-PT') : '—' },
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
    carregarVendedores () {
      return this.carregar(async () => {
        const { data } = await api.get('/app/admin/faturacao/vendedores/', { params: { q: this.q, de: this.de, ate: this.ate } })
        this.vendedores = data.itens
      })
    },
    carregarBende () {
      return this.carregar(async () => {
        const { data } = await api.get('/app/admin/faturacao/bende/', { params: { mes: this.mes } })
        this.bende = data
      })
    },
    csv (v) {
      descarregarPdf('/app/admin/faturacao/vendas.csv', `vendas-${v.id}-${this.de}-${this.ate}.csv`, { loja: v.id, de: this.de, ate: this.ate })
    },
    comprovativo (f) { descarregarComprovativoSubscricao(f) },
    extrato (c) {
      descarregarPdf(`/app/admin/faturacao/comissoes/${c.loja_id}/${this.bende.mes}/extrato/`, `extrato-comissoes-${c.loja_id}-${this.bende.mes}.pdf`)
    },
  },
}
</script>
