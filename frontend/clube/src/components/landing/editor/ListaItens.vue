<!-- ListaItens.vue — lista editável (passos, funcionalidades, tutoriais, perguntas): acrescentar, apagar, subir/descer.
     Altera o array recebido (v-model). O conteúdo de cada item vem do slot (item, n). -->
<template>
  <div class="space-y-3" :data-teste="'lista-' + nome">
    <div v-for="(it, n) in modelValue" :key="it.id || it._k" class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3" data-teste="lista-item">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-500">{{ rotulo }} {{ n + 1 }}</span>
        <div class="flex gap-1">
          <button type="button" class="botao-mini" :disabled="n === 0" @click="mover(n, -1)" aria-label="Subir" data-teste="item-subir">
            <font-awesome-icon :icon="['fas', 'arrow-up']" /></button>
          <button type="button" class="botao-mini" :disabled="n === modelValue.length - 1" @click="mover(n, 1)" aria-label="Descer" data-teste="item-descer">
            <font-awesome-icon :icon="['fas', 'arrow-down']" /></button>
          <button type="button" class="botao-mini hover:!text-red-400" @click="apagar(n)" aria-label="Apagar" data-teste="item-apagar">
            <font-awesome-icon :icon="['fas', 'trash']" /></button>
        </div>
      </div>
      <slot :item="it" :n="n" />
    </div>
    <p v-if="!modelValue.length" class="text-xs text-zinc-500">{{ vazio }}</p>
    <button v-if="modelValue.length < maximo" type="button" @click="acrescentar" :data-teste="'acrescentar-' + nome"
            class="w-full py-2 rounded-xl border border-dashed border-zinc-700 text-xs font-semibold text-zinc-300 hover:bg-zinc-800">
      <font-awesome-icon :icon="['fas', 'plus']" class="mr-1" />Acrescentar {{ rotulo.toLowerCase() }}</button>
    <p v-else class="text-[11px] text-zinc-500">Máximo de {{ maximo }}.</p>
  </div>
</template>

<script>
let seq = 0

export default {
  name: 'ListaItens',
  props: {
    modelValue: { type: Array, required: true },
    novo: { type: Function, required: true },        // () => item vazio
    rotulo: { type: String, default: 'Item' },
    nome: { type: String, default: 'itens' },
    maximo: { type: Number, default: 20 },
    vazio: { type: String, default: 'Ainda não há nenhum.' },
  },
  emits: ['update:modelValue', 'novo'],
  methods: {
    atualizar (lista) { this.$emit('update:modelValue', lista) },
    acrescentar () {
      // sem id: o servidor dá-lhe um ao gravar; _k só serve de chave aqui
      const it = { ...this.novo(), _k: 'n' + (++seq) }
      this.atualizar([...this.modelValue, it])
      this.$emit('novo', it)
    },
    apagar (n) { this.atualizar(this.modelValue.filter((_, i) => i !== n)) },
    mover (n, d) {
      const l = [...this.modelValue]
      ;[l[n], l[n + d]] = [l[n + d], l[n]]
      this.atualizar(l)
    },
  },
}
</script>

<style scoped>
.botao-mini { width: 1.75rem; height: 1.75rem; border-radius: 0.5rem; font-size: 0.7rem; color: #a1a1aa; background: #27272a; }
.botao-mini:hover:not(:disabled) { background: #3f3f46; color: #fff; }
.botao-mini:disabled { opacity: 0.3; }
</style>
