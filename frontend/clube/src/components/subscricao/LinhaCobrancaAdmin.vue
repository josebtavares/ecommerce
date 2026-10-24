<!-- LinhaCobrancaAdmin.vue — uma cobrança (FaturaSubscricao) em Admin → Subscrições, com as ações.
     Emite 'acao' com (tipo, f): pagar | adiar | anular | recibo | faturacao. mostrarAlvo: mostra a loja/POS. -->
<template>
  <div :class="['flex flex-wrap items-center gap-3', embutida ? 'px-4 sm:px-6 py-3' : 'bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3']"
    :data-teste="`cobranca-S-${f.id}`">
    <div class="flex-1 min-w-[200px]">
      <p class="text-sm font-semibold text-zinc-200">
        S-{{ f.id }}<template v-if="mostrarAlvo"> · {{ f.loja_nome }}</template>
        <span v-if="f.pos_id && !mostrarAlvo" class="ml-1 text-[10px] font-bold uppercase text-sky-300">POS</span>
        <span v-if="f.servicos" class="ml-1 px-1.5 py-0.5 rounded bg-violet-500/15 text-violet-300 text-[10px] font-bold uppercase align-middle">Serviços</span>
      </p>
      <p class="text-xs text-zinc-500">{{ f.descricao }} ·
        <template v-if="f.estado === 'paga'">paga a {{ data(f.paga_em) }} ({{ f.metodo_nome }})</template>
        <template v-else-if="f.estado === 'pendente'">vence a {{ data(f.vencimento) }}</template>
        <template v-else>{{ f.notas || 'anulada' }}</template>
      </p>
    </div>
    <span class="text-sm font-bold text-zinc-100">{{ euros(f.valor) }}</span>
    <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', f.atrasada ? 'bg-red-500/15 text-red-400' : corFatura(f.estado)]">
      {{ f.atrasada ? 'Em atraso' : f.estado_nome }}
    </span>
    <template v-if="f.estado === 'pendente'">
      <button type="button" @click="$emit('acao', 'pagar', f)" data-teste="cobranca-pagar"
        class="px-3 py-1.5 rounded-lg bg-green-600/20 hover:bg-green-600/30 text-green-300 text-xs font-semibold">Marcar paga</button>
      <button type="button" @click="$emit('acao', 'adiar', f)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Adiar</button>
      <button type="button" @click="$emit('acao', 'anular', f)" class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 text-xs">Anular</button>
    </template>
    <button v-else-if="f.estado === 'paga'" type="button" @click="$emit('acao', 'recibo', f)" :aria-label="`Comprovativo do pagamento ${f.id}`"
      class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Comprovativo</button>
    <a v-if="f.fatura && f.fatura.pdf_url" :href="urlFicheiro(f.fatura.pdf_url)" target="_blank" rel="noopener"
      class="px-3 py-1.5 rounded-lg bg-green-500/10 text-green-400 text-xs">Fatura {{ f.fatura.numero }}</a>
    <span v-else-if="f.fatura" class="text-xs text-green-400">Fatura {{ f.fatura.numero }}</span>
    <span v-else-if="f.estado === 'paga' && Number(f.valor) > 0" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300" data-teste="cobranca-por-faturar">Fatura do Bende por registar</span>
    <button v-if="f.estado === 'paga' && Number(f.valor) > 0" type="button" @click="$emit('acao', 'faturacao', f)" data-teste="ver-na-faturacao"
      class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Ver na Faturação →</button>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import { urlFicheiro } from '@/utils/documentos'

export default {
  name: 'LinhaCobrancaAdmin',
  props: {
    f: { type: Object, required: true },
    mostrarAlvo: { type: Boolean, default: true },
    embutida: { type: Boolean, default: false },
  },
  emits: ['acao'],
  methods: {
    urlFicheiro,
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s.length === 10 ? s + 'T12:00:00' : s).toLocaleDateString('pt-PT') : '' },
    corFatura (e) { return { paga: 'bg-green-500/15 text-green-400', pendente: 'bg-amber-500/15 text-amber-300', anulada: 'bg-zinc-700 text-zinc-400' }[e] },
  },
}
</script>
