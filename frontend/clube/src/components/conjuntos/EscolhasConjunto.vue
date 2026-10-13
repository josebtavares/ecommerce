<template>
  <!-- Escolhas do cliente num conjunto (loja e POS):
       - peças em que o cliente escolhe a variação (ex.: o tamanho da T-shirt)
       - grupos de opções (ex.: "Bebida — escolhe 1"), e a variação da opção escolhida se for livre
       v-model = { "<grupo_id>": [opcao_id, ...], variantes: { "c<id>" | "o<id>": variante_id } } -->
  <div class="space-y-4">
    <!-- ── Peças: escolher a variação ── -->
    <div v-for="c in pecasLivres" :key="'c' + c.id" role="group" :aria-label="c.nome">
      <div class="flex items-baseline justify-between gap-2 mb-2">
        <p class="text-sm font-bold" :class="t('text-zinc-100', 'text-zinc-900', 'text-slate-950')">
          <template v-if="c.quantidade > 1">{{ c.quantidade }}× </template>{{ c.nome }}
        </p>
        <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
              :class="variante('c' + c.id) ? t('bg-zinc-800 text-zinc-400', 'bg-gray-100 text-zinc-500', 'bg-slate-100 text-slate-500') : 'bg-red-500/15 text-red-500'">
          {{ variante('c' + c.id) ? nomeVariante(c, variante('c' + c.id)) : 'Escolhe ' + rotulo(c) }}
        </span>
      </div>
      <BotoesVariante :item="c" :valor="variante('c' + c.id)" :t="t" @escolher="v => definirVariante('c' + c.id, v)" />
    </div>

    <!-- ── Grupos de opções ── -->
    <div v-for="g in grupos" :key="g.id" role="group" :aria-label="g.nome">
      <div class="flex items-baseline justify-between gap-2 mb-2">
        <p class="text-sm font-bold" :class="t('text-zinc-100', 'text-zinc-900', 'text-slate-950')">{{ g.nome }}</p>
        <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
              :class="falta(g) ? 'bg-red-500/15 text-red-500' : t('bg-zinc-800 text-zinc-400', 'bg-gray-100 text-zinc-500', 'bg-slate-100 text-slate-500')">
          {{ regra(g) }}
        </span>
      </div>
      <div class="grid gap-2" :class="compacto ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'">
        <div v-for="o in g.opcoes" :key="o.id" :class="marcada(g, o) && o.variante_livre ? (compacto ? 'sm:col-span-2' : '') : ''">
          <button type="button"
                  :disabled="!o.disponivel || (!marcada(g, o) && cheio(g) && g.maximo > 1)"
                  :aria-pressed="marcada(g, o) ? 'true' : 'false'"
                  @click="alternar(g, o)"
                  class="w-full flex items-center gap-3 p-2 rounded-xl border text-left transition disabled:cursor-not-allowed"
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
                <span v-else-if="o.variante_livre && variante('o' + o.id)" :class="t('text-zinc-500', 'text-zinc-400', 'text-slate-400')"> · {{ nomeVariante(o, variante('o' + o.id)) }}</span>
              </span>
              <span v-if="!o.disponivel" class="block text-[11px] font-semibold text-red-500">Esgotado</span>
            </span>
            <span class="text-xs font-bold flex-shrink-0" :class="Number(o.preco_extra) > 0 ? 'text-red-500' : t('text-zinc-500', 'text-zinc-400', 'text-slate-400')">
              {{ Number(o.preco_extra) > 0 ? '+' + dinheiro(o.preco_extra) : 'incluído' }}
            </span>
          </button>
          <!-- opção escolhida com variação à escolha (ex.: tamanho das meias) -->
          <div v-if="marcada(g, o) && o.variante_livre" class="mt-2 ml-7">
            <p v-if="!variante('o' + o.id)" class="text-[11px] font-semibold text-red-500 mb-1">Escolhe {{ rotulo(o) }}</p>
            <BotoesVariante :item="o" :valor="variante('o' + o.id)" :t="t" @escolher="v => definirVariante('o' + o.id, v)" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { h } from 'vue'

const dinheiro = v => new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)

// botões das variações de uma peça/opção (esgotadas desactivadas)
const BotoesVariante = {
  props: { item: Object, valor: Number, t: Function },
  emits: ['escolher'],
  setup (p, { emit }) {
    return () => h('div', { class: 'flex flex-wrap gap-2' }, (p.item.variantes_livres || []).map(v =>
      h('button', {
        type: 'button', key: v.id, disabled: !v.disponivel, 'aria-pressed': p.valor === v.id ? 'true' : 'false',
        onClick: () => emit('escolher', v.id),
        class: 'min-w-[44px] px-3 py-1.5 rounded-xl border text-xs font-semibold transition disabled:cursor-not-allowed disabled:line-through disabled:opacity-40 ' +
               (p.valor === v.id ? 'border-red-500 bg-red-600 text-white'
                                 : p.t('border-zinc-700 bg-zinc-800 text-zinc-300 hover:border-zinc-500',
                                       'border-gray-300 bg-gray-100 text-zinc-700 hover:border-gray-400',
                                       'border-slate-200 bg-white text-slate-700 hover:border-slate-400')),
      }, v.nome)))
  },
}

export default {
  name: 'EscolhasConjunto',
  components: { BotoesVariante },
  props: {
    grupos:      { type: Array, default: () => [] },
    componentes: { type: Array, default: () => [] },
    modelValue:  { type: Object, default: () => ({}) },
    isDark:      { type: Boolean, default: true },
    pos:         { type: Boolean, default: false },   // tema do POS (claro, slate)
    compacto:    { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],

  computed: {
    pecasLivres () { return this.componentes.filter(c => c.variante_livre) },
  },

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
    variante (chave) { return (this.modelValue.variantes || {})[chave] || null },
    nomeVariante (item, id) { return (item.variantes_livres || []).find(v => v.id === id)?.nome || '' },
    rotulo (item) { return rotuloVariante(item) },
    definirVariante (chave, id) {
      this.$emit('update:modelValue', { ...this.modelValue, variantes: { ...(this.modelValue.variantes || {}), [chave]: id } })
    },
    alternar (g, o) {
      if (!o.disponivel) return
      let lista = this.escolhidas(g).slice()
      const saem = []
      if (lista.includes(o.id)) { lista = lista.filter(x => x !== o.id); saem.push(o.id) } else if (g.maximo === 1) { saem.push(...lista); lista = [o.id] } else if (lista.length < g.maximo) lista.push(o.id)
      const novo = { ...this.modelValue, [String(g.id)]: lista }
      if (!lista.length) delete novo[String(g.id)]
      // a variação de uma opção que deixou de estar escolhida já não conta
      if (saem.length && novo.variantes) {
        novo.variantes = { ...novo.variantes }
        saem.forEach(id => delete novo.variantes['o' + id])
      }
      this.$emit('update:modelValue', novo)
    },
  },
}

// "tamanho" (o nome do atributo da variação) ou "a variação"
function rotuloVariante (item) {
  const v = (item.variantes_livres || [])[0]
  const nomes = v && item.atributos_variante
  return nomes?.length ? nomes.join(' / ') : 'a variação'
}

// todas as escolhas obrigatórias feitas (grupos, variações das peças e das opções escolhidas)?
export function faltaEscolher (grupos, escolhas, componentes = []) {
  const vs = escolhas.variantes || {}
  const falta = componentes.filter(c => c.variante_livre && !vs['c' + c.id]).map(c => c.nome)
  ;(grupos || []).forEach(g => {
    const ids = escolhas[String(g.id)] || []
    if (ids.length < g.minimo) falta.push(g.nome)
    g.opcoes.forEach(o => { if (o.variante_livre && ids.includes(o.id) && !vs['o' + o.id]) falta.push(o.nome) })
  })
  return falta
}

export function escolhasCompletas (grupos, escolhas, componentes = []) {
  return faltaEscolher(grupos, escolhas, componentes).length === 0
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

// o conjunto pede alguma escolha ao cliente?
export function temEscolhas (produto) {
  return !!(produto?.grupos?.length || produto?.componentes?.some(c => c.variante_livre))
}
</script>
