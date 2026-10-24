<!-- ComissoesMensais.vue — backoffice (Subscrição): comissões do Bende por mês, extrato e fatura do Bende -->
<template>
  <div v-if="meses.length" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="comissoes-mensais">
    <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-6 pt-5 pb-1">Comissões por mês</p>
    <p class="text-xs text-zinc-500 px-6 pb-3">O Bende emite uma fatura por mês com as comissões das tuas vendas.</p>
    <div class="divide-y divide-zinc-800">
      <div v-for="m in meses" :key="m.mes" class="px-6 py-4 flex flex-wrap items-center gap-3">
        <div class="flex-1 min-w-[160px]">
          <p class="text-sm font-semibold text-zinc-200">{{ nomeMes(m.mes) }}</p>
          <p class="text-xs text-zinc-500">{{ m.comissoes }} {{ m.comissoes === 1 ? 'venda' : 'vendas' }}</p>
        </div>
        <span class="text-sm font-bold text-zinc-100">{{ dinheiro(m.total) }}</span>
        <button type="button" @click="extrato(m)" class="px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold">
          <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Extrato
        </button>
        <a v-if="m.fatura" :href="m.fatura.pdf_url ? urlFicheiro(m.fatura.pdf_url) : null" target="_blank" rel="noopener"
          class="px-3 py-2 rounded-xl bg-green-500/10 hover:bg-green-500/20 text-green-400 text-xs font-semibold">
          <font-awesome-icon :icon="['fas', 'file-invoice']" class="mr-1" />Fatura {{ m.fatura.numero }}
        </a>
        <span v-else class="text-[11px] text-zinc-500">Fatura em breve</span>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, urlFicheiro } from '@/utils/documentos'

export default {
  name: 'ComissoesMensais',
  props: { lojaId: { type: [String, Number], required: true } },
  data () {
    return { meses: [] }
  },
  async created () {
    try {
      const { data } = await api.get(`/app/loja/${this.lojaId}/comissoes/meses/`)
      this.meses = data.meses || []
    } catch { this.meses = [] }
  },
  methods: {
    urlFicheiro,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    nomeMes (m) {
      const [a, mm] = m.split('-').map(Number)
      const t = new Date(a, mm - 1, 15).toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })
      return t.charAt(0).toUpperCase() + t.slice(1)
    },
    extrato (m) {
      descarregarPdf(`/app/loja/${this.lojaId}/comissoes/${m.mes}/extrato/`, `extrato-comissoes-${m.mes}.pdf`)
    },
  },
}
</script>
