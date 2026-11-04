<!-- HistoricoAcertos.vue — acertos do dinheiro dos condutores (DinheiroCondutores.vue): condutor vê os seus;
     a loja vê todos e pode anular (emite 'anular'). -->
<template>
    <div v-if="acertos.length" class="bg-zinc-900 rounded-2xl border border-zinc-800" data-teste="acertos">
      <p class="px-4 pt-4 pb-2 text-xs font-bold text-zinc-500 uppercase tracking-wider">Entregue à loja</p>
      <div class="divide-y divide-zinc-800">
        <div v-for="a in acertos" :key="a.id" class="px-4 py-3 flex items-start justify-between gap-3 text-sm" :data-teste="'acerto-' + a.id">
          <div class="min-w-0">
            <p :class="a.anulado ? 'text-zinc-500 line-through' : 'text-zinc-200'">
              <span class="font-semibold">{{ $dinheiro(a.valor) }}</span>
              <span v-if="mostrarCondutor"> · {{ a.condutor_nome }}</span>
              <span class="text-zinc-500"> · {{ a.n_entregas }} entrega{{ a.n_entregas !== 1 ? 's' : '' }}</span>
            </p>
            <p class="text-xs text-zinc-500">{{ quando(a.criado_em) }}<span v-if="a.recebido_por"> · recebido por {{ a.recebido_por }}</span>
              <span v-if="a.nota"> · {{ a.nota }}</span></p>
            <p v-if="a.anulado" class="text-xs text-red-300">Anulado{{ a.anulado_por ? ' por ' + a.anulado_por : '' }}: {{ a.motivo_anulacao }}</p>
          </div>
          <button v-if="podeAnular && !a.anulado" type="button" @click="$emit('anular', a)" data-teste="acerto-anular"
            class="px-2 py-1 rounded-lg border border-zinc-700 hover:border-red-500/60 text-zinc-400 hover:text-red-300 text-[11px] whitespace-nowrap">Anular</button>
        </div>
      </div>
    </div>
</template>

<script>
export default {
  name: 'HistoricoAcertos',
  props: { acertos: { type: Array, default: () => [] }, quando: { type: Function, required: true },
           mostrarCondutor: Boolean, podeAnular: Boolean },
  emits: ['anular'],
}
</script>
