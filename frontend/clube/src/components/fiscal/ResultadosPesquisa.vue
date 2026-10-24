<!-- ResultadosPesquisa.vue — resultados de /app/admin/faturacao/pesquisa/ (todas as lojas ou só uma).
     Emite 'abrir' com o resultado e 'ir' com o novo offset (paginação). -->
<template>
  <div class="space-y-2" data-teste="pesquisa-resultados">
    <p class="text-xs text-zinc-500">{{ res.count }} resultado(s)</p>
    <div v-for="r in res.results" :key="r.tipo + r.referencia"
      class="bg-zinc-900 rounded-xl border border-zinc-800 px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-1">
      <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', TIPOS[r.tipo].cor]">{{ TIPOS[r.tipo].nome }}</span>
      <div class="flex-1 min-w-[200px]">
        <p class="text-sm font-semibold text-zinc-200">{{ r.titulo }} <span class="text-[11px] text-zinc-500 font-normal">· {{ r.referencia }}</span></p>
        <p class="text-[11px] text-zinc-500">{{ r.vendedor.nome }}<template v-if="r.detalhe"> · {{ r.detalhe }}</template><template v-if="r.data"> · {{ data(r.data) }}</template></p>
      </div>
      <span v-if="r.valor" class="text-sm font-bold text-zinc-100">{{ dinheiro(r.valor) }}</span>
      <span v-if="r.fatura" class="text-xs text-green-400">Fatura {{ r.fatura.numero }}</span>
      <span v-else-if="['venda', 'mensalidade', 'comissoes'].includes(r.tipo)" class="text-xs text-amber-300">Por faturar</span>
      <button v-if="r.vendedor.id" type="button" @click="$emit('abrir', r)" data-teste="abrir-resultado"
        class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">Abrir</button>
    </div>
    <p v-if="!res.results.length" class="text-center py-8 text-sm text-zinc-500">Nada encontrado.</p>
    <PaginacaoLista :count="res.count" :limit="limit" :offset="offset" @ir="o => $emit('ir', o)" />
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import PaginacaoLista from './PaginacaoLista.vue'

const TIPOS = {
  venda:       { nome: 'Venda',          cor: 'bg-zinc-700 text-zinc-200' },
  mensalidade: { nome: 'Mensalidade',    cor: 'bg-violet-500/15 text-violet-300' },
  comissoes:   { nome: 'Comissões',      cor: 'bg-sky-500/15 text-sky-300' },
  anulada:     { nome: 'Fatura anulada', cor: 'bg-red-500/15 text-red-300' },
  loja:        { nome: 'Loja',           cor: 'bg-emerald-500/15 text-emerald-300' },
  pos:         { nome: 'POS',            cor: 'bg-emerald-500/15 text-emerald-300' },
}

export default {
  name: 'ResultadosPesquisa',
  components: { PaginacaoLista },
  props: {
    res:    { type: Object, required: true },     // { count, results }
    limit:  { type: Number, required: true },
    offset: { type: Number, required: true },
  },
  emits: ['abrir', 'ir'],
  data () {
    return { TIPOS }
  },
  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return new Date(s).toLocaleDateString('pt-PT') },
  },
}
</script>
