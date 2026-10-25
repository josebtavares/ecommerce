<!-- HistoricoFatura.vue — todas as faturas registadas num documento (E-…, M-…, V-…, S-…, C-…), em vigor e anuladas.
     Carrega <url>?ref= quando aparece (admin por omissão; a loja passa o dela). -->
<template>
  <div class="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs" data-teste="historico-fatura">
    <p class="font-bold text-zinc-400 mb-2">Histórico de faturas · {{ referencia }}</p>
    <p v-if="carregando" class="text-zinc-500">A carregar…</p>
    <p v-else-if="!itens.length" class="text-zinc-500">Nenhuma fatura registada neste documento.</p>
    <ol v-else class="space-y-2">
      <li v-for="h in itens" :key="h.id" class="flex flex-wrap items-start gap-x-3 gap-y-1">
        <span :class="['px-2 py-0.5 rounded-full font-bold', h.anulada_em ? 'bg-red-500/15 text-red-300' : 'bg-green-500/15 text-green-400']">
          {{ h.anulada_em ? 'Anulada' : 'Em vigor' }}
        </span>
        <a v-if="h.pdf_url" :href="urlFicheiro(h.pdf_url)" target="_blank" rel="noopener" class="font-semibold text-zinc-200 underline">{{ h.numero }}</a>
        <span v-else class="font-semibold text-zinc-200">{{ h.numero }} <span class="text-zinc-500 font-normal">(sem PDF)</span></span>
        <span class="text-zinc-500">registada {{ quando(h.registada_em) }}<template v-if="h.registada_por"> por {{ h.registada_por.nome }}</template></span>
        <span v-if="h.anulada_em" class="w-full text-zinc-400 pl-1">
          ↳ anulada {{ quando(h.anulada_em) }}<template v-if="h.anulada_por"> por {{ h.anulada_por.nome }}</template> — “{{ h.motivo }}”
        </span>
      </li>
    </ol>
  </div>
</template>

<script>
import api from '@/services/api'
import { urlFicheiro } from '@/utils/documentos'

export default {
  name: 'HistoricoFatura',
  props: {
    referencia: { type: String, required: true },
    url: { type: String, default: '/app/admin/faturacao/historico/' },
  },
  data () {
    return { itens: [], carregando: true }
  },
  async created () {
    try {
      const { data } = await api.get(this.url, { params: { ref: this.referencia } })
      this.itens = data.itens
    } catch { this.itens = [] } finally { this.carregando = false }
  },
  methods: {
    urlFicheiro,
    quando (s) { return new Date(s).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) },
  },
}
</script>
