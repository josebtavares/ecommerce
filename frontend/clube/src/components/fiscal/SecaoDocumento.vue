<template>
  <!-- Separa os dois downloads de um documento: o documento interno da Bendi (comprovativo / extrato — fundo neutro)
       e a fatura legal (fundo verde). Cada caixa tem o seu título pequeno. -->
  <div role="group" :aria-label="titulo" :data-teste="`secao-${tipo}`"
    :class="['inline-flex flex-wrap items-center gap-2 rounded-xl border px-2.5 py-1.5', tipo === 'fatura'
      ? 'border-emerald-500/25 bg-emerald-500/[0.07]' : 'border-zinc-700/70 bg-zinc-950/50']">
    <span :class="['text-[9px] font-bold uppercase tracking-wider whitespace-nowrap', tipo === 'fatura' ? 'text-emerald-400/90' : 'text-zinc-500']">
      <font-awesome-icon :icon="['fas', tipo === 'fatura' ? 'file-invoice' : 'file-lines']" class="mr-1" />{{ titulo }}
    </span>
    <slot />
  </div>
</template>

<script>
export default {
  name: 'SecaoDocumento',
  props: {
    tipo: { type: String, default: 'interno' },      // 'interno' | 'fatura'
    rotulo: { type: String, default: '' },
  },
  computed: {
    titulo () { return this.rotulo || (this.tipo === 'fatura' ? 'Fatura da Bendi' : 'Documento interno') },
  },
}
</script>
