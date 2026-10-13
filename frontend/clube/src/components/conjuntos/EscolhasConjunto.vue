<template>
  <!-- Escolhas do cliente num conjunto (ex.: "Bebida — escolhe 1"). Usado na loja e no POS.
       v-model = { "<grupo_id>": [opcao_id, ...] } -->
  <div class="space-y-4">
    <div v-for="g in grupos" :key="g.id" role="group" :aria-label="g.nome">
      <div class="flex items-baseline justify-between gap-2 mb-2">
        <p class="text-sm font-bold" :class="t('text-zinc-100', 'text-zinc-900', 'text-slate-950')">{{ g.nome }}</p>
        <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
              :class="falta(g) ? 'bg-red-500/15 text-red-500' : t('bg-zinc-800 text-zinc-400', 'bg-gray-100 text-zinc-500', 'bg-slate-100 text-slate-500')">
          {{ regra(g) }}
        </span>
      </div>
      <div class="grid gap-2" :class="compacto ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'">
        <button v-for="o in g.opcoes" :key="o.id" type="button"
                :disabled="!o.disponivel || (!marcada(g, o) && cheio(g) && g.maximo > 1)"
                :aria-pressed="marcada(g, o) ? 'true' : 'false'"
                @click="alternar(g, o)"
                class="flex items-center gap-3 p-2 rounded-xl border text-left transition disabled:cursor-not-allowed"
                :class="marcada(g, o)
                  ? 'border-red-500 ' + t('bg-red-500/10', 'bg-red-50', 'bg-red-50')
                  : o.disponivel ? t('border-zinc-800 hover:border-zinc-600', 'border-gray-200 hover:border-gray-400', 'border-slate-200 hover:border-slate-400')
                                 : t('border-zinc-900 opacity-50', 'border-gray-100 opacity-50', 'border-slate-100 opacity-50')">
          <span class="w-4 h-4 flex-shrink-0 border-2 flex items-center justify-center"
                :class="[g.maximo === 1 ? 'rounded-full' : 'rounded', marcada(g, o) ? 'border-red-500 bg-red-500' : t('border-zinc-600', 'border-gray-300', 'border-slate-300')]">
            <span v-if="marcada(g, o)" class="text-white text-[10px] leading-none">✓</span>
          </span>
          <img v-if="o.imagem" :src="o.imagem" :alt="o.nome" class="w-9 h-9 rounded-lg object-cover flex-shrink-0" />
          <span class="flex-1 min-w-0">
            <span class="block text-sm truncate" :class="t('text-zinc-200', 'text-zinc-800', 'text-slate-900')">
              <template v-if="o.quantidade > 1">{{ o.quantidade }}× </template>{{ o.nome }}
              <span v-if="o.variante" :class="t('text-zinc-500', 'text-zinc-400', 'text-slate-400')"> · {{ o.variante }}</span>
            </span>
            <span v-if="!o.disponivel" class="block text-[11px] font-semibold text-red-500">Esgotado</span>
          </span>
          <span class="text-xs font-bold flex-shrink-0" :class="Number(o.preco_extra) > 0 ? 'text-red-500' : t('text-zinc-500', 'text-zinc-400', 'text-slate-400')">
            {{ Number(o.preco_extra) > 0 ? '+' + dinheiro(o.preco_extra) : 'incluído' }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
const dinheiro = v => new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)

export default {
  name: 'EscolhasConjunto',
  props: {
    grupos:     { type: Array, default: () => [] },
    modelValue: { type: Object, default: () => ({}) },
    isDark:     { type: Boolean, default: true },
    pos:        { type: Boolean, default: false },   // tema do POS (claro, slate)
    compacto:   { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],

  methods: {
    dinheiro,
    // classes por tema: escuro (loja) / claro (loja) / POS
    t (escuro, claro, pos) { return this.pos ? pos : (this.isDark ? escuro : claro) },
    escolhidas (g) { return this.modelValue[String(g.id)] || [] },
    marcada (g, o) { return this.escolhidas(g).includes(o.id) },
    cheio (g) { return this.escolhidas(g).length >= g.maximo },
    falta (g) { return this.escolhidas(g).length < g.minimo },
    regra (g) {
      if (g.minimo === 0) return g.maximo === 1 ? 'Opcional' : `Opcional · até ${g.maximo}`
      if (g.minimo === g.maximo) return g.minimo === 1 ? 'Escolhe 1' : `Escolhe ${g.minimo}`
      return `Escolhe ${g.minimo} a ${g.maximo}`
    },
    alternar (g, o) {
      if (!o.disponivel) return
      let lista = this.escolhidas(g).slice()
      if (lista.includes(o.id)) lista = lista.filter(x => x !== o.id)
      else if (g.maximo === 1) lista = [o.id]           // só uma: troca
      else if (lista.length < g.maximo) lista.push(o.id)
      const novo = { ...this.modelValue, [String(g.id)]: lista }
      if (!lista.length) delete novo[String(g.id)]
      this.$emit('update:modelValue', novo)
    },
  },
}

// todas as escolhas obrigatórias feitas?
export function escolhasCompletas (grupos, escolhas) {
  return (grupos || []).every(g => (escolhas[String(g.id)] || []).length >= g.minimo)
}

// soma dos custos extra das opções escolhidas
export function extrasDe (grupos, escolhas) {
  let total = 0
  ;(grupos || []).forEach(g => {
    const ids = escolhas[String(g.id)] || []
    g.opcoes.forEach(o => { if (ids.includes(o.id)) total += Number(o.preco_extra) || 0 })
  })
  return total
}

// "Bebida: Fanta" — para mostrar antes de adicionar
export function faltaEscolher (grupos, escolhas) {
  return (grupos || []).filter(g => (escolhas[String(g.id)] || []).length < g.minimo).map(g => g.nome)
}
</script>
