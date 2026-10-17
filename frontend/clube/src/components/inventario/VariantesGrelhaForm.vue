<!-- VariantesGrelhaForm.vue — grelha de stock por variação DENTRO do formulário do produto.
     Não chama a API: o pai calcula as combinações (utils/variantes.js → combinacoesDe/mesclarLinhas)
     e envia a grelha junto com o produto, num só pedido (campos stock_por_variante + variantes).
     Uso:
       <VariantesGrelhaForm v-model:ativo="g.ativo" v-model:linhas="g.linhas"
                            :atributos="['tamanho','cor']" :preco-produto="form.preco" claro /> -->
<template>
  <div class="space-y-3" @keydown.enter.prevent>
    <!-- Interruptor -->
    <label :class="['flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition', ativo ? c.ativoBox : c.box]">
      <button type="button" role="switch" :aria-checked="ativo" @click="$emit('update:ativo', !ativo)"
        :class="['relative mt-0.5 h-6 w-10 flex-shrink-0 rounded-full transition', ativo ? 'bg-amber-500' : c.switchOff]">
        <span :class="['absolute top-1 h-4 w-4 rounded-full bg-white transition-all', ativo ? 'left-5' : 'left-1']"></span>
      </button>
      <span class="text-xs leading-relaxed">
        <span :class="['block font-bold', c.forte]">Stock por variação</span>
        <span :class="c.muted">
          {{ ativo
              ? 'Cada combinação tem stock próprio — o cliente só pode escolher as que têm unidades.'
              : (stockTotalAntigo !== null
                  ? `Desligado: o produto usa o stock total (${stockTotalAntigo} un.). Ao ligar, o total passa a ser a soma das combinações.`
                  : 'Desligado: o produto usa um stock total, sem distinguir combinações.') }}
        </span>
      </span>
    </label>

    <template v-if="ativo">
      <!-- Acções em massa -->
      <div class="flex flex-wrap items-center gap-2">
        <span :class="['text-[11px]', c.muted]">Aplicar a todas:</span>
        <input v-model.number="qtdEmMassa" type="number" min="0" placeholder="qtd"
          :class="['w-20 rounded-lg border px-2 py-1 text-xs focus:outline-none', c.input]" />
        <button type="button" @click="aplicarATodas" :disabled="qtdEmMassa === '' || qtdEmMassa < 0"
          :class="['rounded-lg px-2.5 py-1 text-xs transition disabled:opacity-40', c.btn]">Aplicar</button>
        <label :class="['ml-auto flex cursor-pointer select-none items-center gap-1.5 text-[11px]', c.muted]">
          <input v-model="mostrarExtras" type="checkbox" class="h-3 w-3 accent-red-500" />
          Preço e SKU por variação
        </label>
      </div>

      <div :class="['overflow-x-auto rounded-xl border', c.borda]">
        <table class="w-full text-xs">
          <thead :class="c.thead">
            <tr>
              <th v-for="a in atributos" :key="a" class="whitespace-nowrap px-3 py-2 text-left font-semibold capitalize">{{ a }}</th>
              <th class="whitespace-nowrap px-3 py-2 text-left font-semibold">Quantidade</th>
              <th v-if="mostrarExtras" class="whitespace-nowrap px-3 py-2 text-left font-semibold">Preço</th>
              <th v-if="mostrarExtras" class="whitespace-nowrap px-3 py-2 text-left font-semibold">SKU</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(l, i) in linhas" :key="l.chave" :class="['border-t', c.borda]">
              <td v-for="a in atributos" :key="a" :class="['whitespace-nowrap px-3 py-2', c.cel]">{{ l.combinacao[a] ?? '—' }}</td>
              <td class="px-3 py-1.5">
                <div class="flex items-center gap-1">
                  <button type="button" @click="setCampo(i, 'quantidade', Math.max(0, Number(l.quantidade || 0) - 1))"
                    :class="['h-6 w-6 rounded-md', c.btn]">−</button>
                  <input :value="l.quantidade" @input="setCampo(i, 'quantidade', $event.target.value === '' ? '' : Number($event.target.value))"
                    type="number" min="0" step="1"
                    :class="['w-16 rounded-md border px-2 py-1 text-center focus:outline-none', c.input, !qtdValida(l.quantidade) && '!border-red-500']" />
                  <button type="button" @click="setCampo(i, 'quantidade', Number(l.quantidade || 0) + 1)"
                    :class="['h-6 w-6 rounded-md', c.btn]">+</button>
                  <span v-if="Number(l.quantidade) === 0" class="ml-1 text-[10px] text-red-500">esgotado</span>
                </div>
              </td>
              <td v-if="mostrarExtras" class="px-3 py-1.5">
                <input :value="l.preco" @input="setCampo(i, 'preco', $event.target.value)" type="number" min="0" step="1"
                  :placeholder="precoProduto !== '' && precoProduto !== null ? String(precoProduto) : 'preço'"
                  :class="['w-24 rounded-md border px-2 py-1 focus:outline-none', c.input]" />
              </td>
              <td v-if="mostrarExtras" class="px-3 py-1.5">
                <input :value="l.sku" @input="setCampo(i, 'sku', $event.target.value)" maxlength="100" placeholder="—"
                  :class="['w-28 rounded-md border px-2 py-1 focus:outline-none', c.input]" />
              </td>
            </tr>
          </tbody>
          <tfoot :class="['border-t', c.tfoot]">
            <tr>
              <td :colspan="atributos.length" class="px-3 py-2 font-semibold">Total · {{ linhas.length }} combinações</td>
              <td :class="['px-3 py-2 font-bold', c.forte]">{{ total }} un.</td>
              <td v-if="mostrarExtras" colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p v-if="mostrarExtras" :class="['text-[10px]', c.muted]">Preço vazio = usa o preço do produto.</p>
    </template>
  </div>
</template>

<script>
const TEMAS = {
  escuro: {
    box: 'border-zinc-700/60 hover:border-zinc-600', ativoBox: 'border-amber-500/40 bg-amber-500/5', switchOff: 'bg-zinc-700',
    forte: 'text-zinc-100', muted: 'text-zinc-500', cel: 'text-zinc-200',
    input: 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-600 focus:border-red-500',
    btn: 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300', borda: 'border-zinc-800',
    thead: 'bg-zinc-800/60 text-zinc-500', tfoot: 'border-zinc-700 bg-zinc-800/40 text-zinc-400',
  },
  claro: {
    box: 'border-slate-200 bg-white hover:border-slate-300', ativoBox: 'border-amber-300 bg-amber-50', switchOff: 'bg-slate-300',
    forte: 'text-slate-900', muted: 'text-slate-500', cel: 'text-slate-800',
    input: 'bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-slate-950',
    btn: 'bg-slate-100 hover:bg-slate-200 text-slate-700', borda: 'border-slate-200',
    thead: 'bg-slate-50 text-slate-500', tfoot: 'border-slate-200 bg-slate-50 text-slate-600',
  },
}

export default {
  name: 'VariantesGrelhaForm',

  props: {
    ativo:            { type: Boolean, default: true },
    linhas:           { type: Array, default: () => [] },   // [{ chave, combinacao, quantidade, preco, sku }]
    atributos:        { type: Array, default: () => [] },   // nomes das colunas (ex.: ['tamanho', 'cor'])
    precoProduto:     { type: [Number, String], default: '' },
    stockTotalAntigo: { type: Number, default: null },       // produto existente ainda sem variações
    claro:            { type: Boolean, default: false },
  },

  emits: ['update:ativo', 'update:linhas'],

  data () {
    return { qtdEmMassa: '', mostrarExtras: this.linhas.some(l => (l.preco !== '' && l.preco !== null) || l.sku) }
  },

  computed: {
    c () { return this.claro ? TEMAS.claro : TEMAS.escuro },
    total () { return this.linhas.reduce((s, l) => s + (Number(l.quantidade) || 0), 0) },
  },

  methods: {
    qtdValida (q) { return q !== '' && Number.isInteger(Number(q)) && Number(q) >= 0 },

    setCampo (i, campo, valor) {
      const novas = this.linhas.map((l, j) => (j === i ? { ...l, [campo]: valor } : l))
      this.$emit('update:linhas', novas)
    },

    aplicarATodas () {
      const q = Math.max(0, Math.floor(Number(this.qtdEmMassa) || 0))
      this.$emit('update:linhas', this.linhas.map(l => ({ ...l, quantidade: q })))
    },
  },
}
</script>
