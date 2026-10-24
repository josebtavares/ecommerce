<!-- ComissoesMensais.vue — backoffice (Subscrição): comissões do Bende por mês (12 por página, filtro por ano), extrato e fatura do Bende.
     Cada mês abre as suas vendas com a comissão de cada uma, paginadas e com procura pelo nº da encomenda. -->
<template>
  <div v-if="count || ano" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="comissoes-mensais">
    <div class="flex flex-wrap items-end justify-between gap-2 px-6 pt-5 pb-3">
      <div>
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider pb-1">Comissões por mês</p>
        <p class="text-xs text-zinc-500">O Bende emite uma fatura por mês com as comissões das tuas vendas.</p>
      </div>
      <select v-if="anos.length > 1" v-model="ano" @change="carregar(0)" aria-label="Ano" data-teste="comissoes-ano"
        class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-red-500">
        <option value="">Todos os anos</option>
        <option v-for="a in anos" :key="a" :value="a">{{ a }}</option>
      </select>
    </div>
    <div :class="['divide-y divide-zinc-800 transition-opacity', aCarregar ? 'opacity-50' : '']">
      <div v-for="m in meses" :key="m.mes" :data-teste="`comissoes-mes-${m.mes}`">
        <div class="px-6 py-4 flex flex-wrap items-center gap-3">
          <div class="flex-1 min-w-[160px]">
            <p class="text-sm font-semibold text-zinc-200">{{ nomeMes(m.mes) }}</p>
            <p class="text-xs text-zinc-500">{{ m.comissoes }} {{ m.comissoes === 1 ? 'venda' : 'vendas' }}</p>
          </div>
          <span class="text-sm font-bold text-zinc-100">{{ dinheiro(m.total) }}</span>
          <button type="button" @click="abrir(m)" :aria-expanded="aberto === m.mes ? 'true' : 'false'" data-teste="comissoes-ver-vendas"
            class="px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold">
            <font-awesome-icon :icon="['fas', aberto === m.mes ? 'chevron-up' : 'list']" class="mr-1" />Vendas
          </button>
          <button type="button" @click="extrato(m)" class="px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold">
            <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Extrato
          </button>
          <a v-if="m.fatura" :href="m.fatura.pdf_url ? urlFicheiro(m.fatura.pdf_url) : null" target="_blank" rel="noopener"
            class="px-3 py-2 rounded-xl bg-green-500/10 hover:bg-green-500/20 text-green-400 text-xs font-semibold">
            <font-awesome-icon :icon="['fas', 'file-invoice']" class="mr-1" />Fatura {{ m.fatura.numero }}
          </a>
          <span v-else class="text-[11px] text-zinc-500">Fatura em breve</span>
        </div>

        <!-- vendas do mês -->
        <div v-if="aberto === m.mes" class="px-6 pb-4" data-teste="comissoes-vendas">
          <div class="flex flex-wrap items-center gap-2 pb-2">
            <input v-model.trim="vq" type="search" @keyup.enter="vendas(0)" @search="vendas(0)" placeholder="Nº da encomenda…" aria-label="Procurar encomenda"
              data-teste="comissoes-vendas-q" class="w-full sm:w-48 px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
            <span class="ml-auto text-xs text-zinc-500">{{ v.count }} {{ v.count === 1 ? 'venda' : 'vendas' }} · {{ dinheiro(v.total) }}</span>
          </div>
          <p v-if="vErro" class="text-sm text-red-400" role="alert">{{ vErro }}</p>
          <p v-else-if="!v.results.length && !vCarregar" class="text-sm text-zinc-500 py-2">Nenhuma venda{{ vq ? ` com "${vq}"` : '' }}.</p>
          <div v-else class="rounded-xl border border-zinc-800 overflow-x-auto">
            <table class="w-full text-sm min-w-[460px]">
              <thead class="bg-zinc-950 text-[10px] uppercase tracking-wider text-zinc-500">
                <tr><th class="text-left px-3 py-2">Encomenda</th><th class="text-left px-3 py-2">Data</th><th class="text-right px-3 py-2">Venda</th>
                  <th class="text-right px-3 py-2">%</th><th class="text-right px-3 py-2">Comissão</th><th class="text-left px-3 py-2">Estado</th></tr>
              </thead>
              <tbody class="divide-y divide-zinc-800">
                <tr v-for="c in v.results" :key="c.encomenda_id">
                  <td class="px-3 py-2 font-semibold text-zinc-200">#{{ c.encomenda_id }}</td>
                  <td class="px-3 py-2 text-zinc-400">{{ new Date(c.data).toLocaleDateString('pt-PT') }}</td>
                  <td class="px-3 py-2 text-right text-zinc-300 tabular-nums">{{ dinheiro(c.valor_encomenda) }}</td>
                  <td class="px-3 py-2 text-right text-zinc-400 tabular-nums">{{ Number(c.percentagem) }}%</td>
                  <td class="px-3 py-2 text-right font-semibold text-zinc-100 tabular-nums">{{ dinheiro(c.valor_comissao) }}</td>
                  <td class="px-3 py-2 text-xs text-zinc-400">{{ c.estado_nome }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pt-2"><PaginacaoLista :count="v.count" :limit="10" :offset="vOffset" @ir="vendas" /></div>
        </div>
      </div>
      <p v-if="!meses.length && !aCarregar" class="px-6 py-4 text-sm text-zinc-500">Sem comissões em {{ ano }}.</p>
    </div>
    <div class="px-6 py-3"><PaginacaoLista :count="count" :limit="12" :offset="offset" @ir="carregar" /></div>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, urlFicheiro } from '@/utils/documentos'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'

export default {
  name: 'ComissoesMensais',
  components: { PaginacaoLista },
  props: { lojaId: { type: [String, Number], required: true } },
  data () {
    return { meses: [], count: 0, anos: [], ano: '', offset: 0, aCarregar: false,
             aberto: null, v: { count: 0, total: 0, results: [] }, vq: '', vOffset: 0, vCarregar: false, vErro: '' }
  },
  created () { this.carregar(0) },
  methods: {
    urlFicheiro,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    nomeMes (m) {
      const [a, mm] = m.split('-').map(Number)
      const t = new Date(a, mm - 1, 15).toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })
      return t.charAt(0).toUpperCase() + t.slice(1)
    },
    async carregar (offset) {
      this.offset = offset
      this.aCarregar = true
      try {
        const params = { limit: 12, offset }
        if (this.ano) params.ano = this.ano
        const { data } = await api.get(`/app/loja/${this.lojaId}/comissoes/meses/`, { params })
        this.meses = data.meses || []
        this.count = data.count || 0
        this.anos = data.anos || []
      } catch { this.meses = [] } finally { this.aCarregar = false }
    },
    abrir (m) {
      if (this.aberto === m.mes) { this.aberto = null; return }
      this.aberto = m.mes
      this.vq = ''
      this.v = { count: 0, total: 0, results: [] }
      this.vendas(0)
    },
    async vendas (offset) {
      const mes = this.aberto
      this.vOffset = offset
      this.vCarregar = true
      this.vErro = ''
      try {
        const params = { limit: 10, offset }
        if (this.vq) params.q = this.vq
        const { data } = await api.get(`/app/loja/${this.lojaId}/comissoes/${mes}/vendas/`, { params })
        if (this.aberto === mes) this.v = data
      } catch (e) {
        this.vErro = e.response?.data?.detail || 'Não foi possível carregar as vendas.'
      } finally { this.vCarregar = false }
    },
    extrato (m) {
      descarregarPdf(`/app/loja/${this.lojaId}/comissoes/${m.mes}/extrato/`, `extrato-comissoes-${m.mes}.pdf`)
    },
  },
}
</script>
