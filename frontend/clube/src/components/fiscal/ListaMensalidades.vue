<!-- ListaMensalidades.vue — admin: mensalidades pagas (loja/POS) com comprovativo, fatura do Bende e histórico.
     mensalidades: itens da ficha (fatura_payload + referencia + anuladas). Emite 'alterado' depois de registar/substituir/anular. -->
<template>
  <div>
    <p v-if="!mensalidades.length" class="text-sm text-zinc-500 px-5 pb-5">{{ vazio }}</p>
    <div v-for="f in mensalidades" :key="f.id" class="px-5 py-3 border-t border-zinc-800 space-y-2" :data-teste="`mensalidade-${f.referencia}`">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex-1 min-w-[200px]">
          <p class="text-sm font-semibold text-zinc-200">{{ f.descricao }} <span class="text-[11px] text-zinc-500 font-normal">· {{ f.referencia }}</span></p>
          <p class="text-[11px] text-zinc-500">
            <template v-if="f.pos_id && mostrarAlvo">{{ f.loja_nome }} · </template>Paga a {{ quando(f.paga_em) }} · {{ f.metodo_nome }}
            <template v-if="f.anuladas"> · <span class="text-red-300">{{ f.anuladas }} fatura(s) anulada(s)</span></template>
          </p>
        </div>
        <span class="text-sm font-bold text-zinc-100">{{ dinheiro(f.valor) }}</span>
        <button type="button" @click="descarregarComprovativoSubscricao(f)" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Comprovativo</button>
        <button type="button" @click="aberto = aberto === f.referencia ? '' : f.referencia" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Histórico</button>
        <RegistarFaturaBende :fatura="f.fatura" :url="`/app/admin/faturacao/subscricoes/${f.id}/fatura/`" @atualizado="d => atualizado(f, d)" />
      </div>
      <HistoricoFatura v-if="aberto === f.referencia" :key="f.referencia + versao" :referencia="f.referencia" />
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarComprovativoSubscricao } from '@/utils/documentos'
import HistoricoFatura from './HistoricoFatura.vue'
import RegistarFaturaBende from './RegistarFaturaBende.vue'

export default {
  name: 'ListaMensalidades',
  components: { HistoricoFatura, RegistarFaturaBende },
  props: {
    mensalidades: { type: Array, required: true },
    mostrarAlvo:  { type: Boolean, default: true },     // "POS X (código) ·" nas mensalidades dos POS
    vazio:        { type: String, default: 'Nenhuma mensalidade paga.' },
  },
  emits: ['alterado'],
  data () {
    return { aberto: '', versao: 0 }
  },
  methods: {
    descarregarComprovativoSubscricao,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    quando (s) { return s ? new Date(s).toLocaleDateString('pt-PT') : '—' },
    atualizado (f, d) {
      if (f.fatura) f.anuladas++         // substituída ou anulada: a anterior ficou no histórico
      f.fatura = d.fatura
      this.versao++
      this.$emit('alterado')
    },
  },
}
</script>
