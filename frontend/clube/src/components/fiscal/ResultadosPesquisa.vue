<!-- ResultadosPesquisa.vue — resultados de /app/admin/faturacao/pesquisa/ (todas as lojas ou só uma).
     Emite 'abrir' com o resultado e 'ir' com o novo offset (paginação). claro: fundo branco (POS). -->
<template>
  <div class="space-y-2" data-teste="pesquisa-resultados">
    <p :class="['text-xs', c.suave]">{{ res.count }} resultado(s)</p>
    <div v-for="r in res.results" :key="r.tipo + r.referencia"
      :class="['rounded-xl border px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-1', c.cartao]">
      <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', claro ? 'bg-slate-100 text-slate-700' : TIPOS[r.tipo].cor]">{{ r.tipo === 'venda' ? ORIGENS[r.origem || 'loja'] : TIPOS[r.tipo].nome }}</span>
      <div class="flex-1 min-w-[200px]">
        <p :class="['text-sm font-semibold', c.forte]">{{ r.titulo }} <span :class="['text-[11px] font-normal', c.suave]">· {{ r.referencia }}</span></p>
        <p :class="['text-[11px]', c.suave]">{{ r.vendedor.nome }}<template v-if="r.detalhe"> · {{ r.detalhe }}</template><template v-if="r.data"> · {{ data(r.data) }}</template></p>
      </div>
      <span v-if="r.valor" :class="['text-sm font-bold', c.forte]">{{ dinheiro(r.valor) }}</span>
      <span v-if="r.fatura" :class="['text-xs', claro ? 'text-emerald-700 font-bold' : 'text-green-400']">Fatura {{ r.fatura.numero }}</span>
      <span v-else-if="['venda', 'mensalidade', 'comissoes'].includes(r.tipo)" :class="['text-xs', claro ? 'text-amber-700 font-bold' : 'text-amber-300']">Por faturar</span>
      <button v-if="r.vendedor.id" type="button" @click="$emit('abrir', r)" data-teste="abrir-resultado"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold', c.botao]">Abrir</button>
    </div>
    <p v-if="!res.results.length" :class="['text-center py-8 text-sm', c.suave]">Nada encontrado.</p>
    <PaginacaoLista :count="res.count" :limit="limit" :offset="offset" :claro="claro" @ir="o => $emit('ir', o)" />
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import PaginacaoLista from './PaginacaoLista.vue'

// vendas: encomenda (loja online), marcação ou conta do POS
const ORIGENS = { loja: 'Venda', marcacoes: 'Marcação', pos: 'Venda POS' }
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
    claro:  { type: Boolean, default: false },
  },
  emits: ['abrir', 'ir'],
  data () {
    return { TIPOS, ORIGENS }
  },
  computed: {
    c () {
      return this.claro
        ? { suave: 'text-slate-500', forte: 'text-slate-900', cartao: 'bg-white border-slate-200', botao: 'bg-slate-950 hover:bg-slate-800 text-white' }
        : { suave: 'text-zinc-500', forte: 'text-zinc-200', cartao: 'bg-zinc-900 border-zinc-800', botao: 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200' }
    },
  },
  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return new Date(s).toLocaleDateString('pt-PT') },
  },
}
</script>
