<!-- ConjuntoPicker.vue — escolher as opções de um menu (ex.: a bebida) ao adicioná-lo à conta.
     Mesmo componente de escolhas da loja online (components/conjuntos/EscolhasConjunto.vue). -->
<template>
  <div class="fixed inset-0 z-[70] flex items-end justify-center bg-black/50 backdrop-blur-sm sm:items-center sm:p-4"
       @click.self="$emit('close')">
    <div class="flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
      <header class="flex items-start gap-3 border-b border-slate-200 p-5">
        <img v-if="produto.imagem_url" :src="produto.imagem_url" class="h-14 w-14 flex-shrink-0 rounded-2xl object-cover" />
        <div class="min-w-0 flex-1">
          <h3 class="truncate text-lg font-black text-slate-950">{{ produto.nome }}</h3>
          <p v-if="produto.componentes?.length" class="truncate text-xs font-semibold text-slate-500">
            {{ produto.componentes.map(c => c.quantidade + '× ' + c.nome).join(', ') }}
          </p>
          <p class="text-lg font-black text-slate-950">{{ money(precoUnitario) }}</p>
        </div>
        <button type="button" @click="$emit('close')" aria-label="Fechar"
          class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 hover:bg-slate-200">×</button>
      </header>

      <div class="flex-1 overflow-y-auto p-5">
        <EscolhasConjunto v-model="escolhas" :grupos="produto.grupos" :componentes="produto.componentes" pos compacto />
      </div>

      <footer class="border-t border-slate-200 p-5">
        <p v-if="falta.length" class="mb-3 text-xs font-bold text-amber-700">Escolhe: {{ falta.join(', ') }}</p>
        <div class="flex items-center gap-3">
          <div class="flex items-center rounded-2xl border-2 border-slate-200">
            <button type="button" aria-label="Menos" @click="quantidade > 1 && quantidade--" class="h-12 w-12 text-xl font-black text-slate-600">−</button>
            <span class="w-8 text-center text-lg font-black text-slate-950">{{ quantidade }}</span>
            <button type="button" aria-label="Mais" @click="quantidade < 99 && quantidade++" class="h-12 w-12 text-xl font-black text-slate-600">+</button>
          </div>
          <button type="button" :disabled="!!falta.length || aGuardar" @click="confirmar"
            class="h-12 flex-1 rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40">
            Adicionar · {{ money(precoUnitario * quantidade) }}
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import EscolhasConjunto, { extrasDe, faltaEscolher } from '@/components/conjuntos/EscolhasConjunto.vue'

export default {
  name: 'ConjuntoPicker',
  components: { EscolhasConjunto },
  props: {
    produto:  { type: Object, required: true },
    aGuardar: { type: Boolean, default: false },
  },
  emits: ['close', 'confirmar'],

  data () {
    return { escolhas: {}, quantidade: 1 }
  },

  computed: {
    precoUnitario () { return Number(this.produto.preco) + extrasDe(this.produto.grupos, this.escolhas) },
    falta () { return faltaEscolher(this.produto.grupos, this.escolhas, this.produto.componentes) },
  },

  methods: {
    money (v) {
      return formatarDinheiro(Number(v) || 0)
    },
    confirmar () {
      if (this.falta.length) return
      this.$emit('confirmar', { escolhas: this.escolhas, quantidade: this.quantidade })
    },
  },
}
</script>
