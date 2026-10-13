<template>
  <!-- Produtos de um conjunto (menu, pack) — usado no backoffice da loja e no POS.
       v-model         = produtos fixos [{ origem, produto_id, variante_id, quantidade }]
       v-model:grupos  = escolhas do cliente [{ id?, nome, minimo, maximo,
                          opcoes: [{ id?, origem, produto_id, variante_id, quantidade, preco_extra }] }]
       catalogo = produtos que podem entrar: [{ origem, id, nome, preco, imagem, ativo, variantes: [{ id, nome, preco }] }] -->
  <div class="space-y-5">
    <!-- ── Produtos fixos: vêm sempre ── -->
    <section class="space-y-2">
      <p class="text-xs font-semibold" :class="claro ? 'text-gray-600' : 'text-zinc-400'">Vem sempre</p>
      <div v-for="(l, i) in linhas" :key="'f' + chave(l) + ':' + i"
           class="flex items-center gap-3 p-2 rounded-xl border" :class="caixa(l)">
        <Miniatura :item="item(l)" :claro="claro" />
        <div class="flex-1 min-w-0">
          <NomeLinha :item="item(l)" :l="l" :mostrar-origem="mostrarOrigem" :claro="claro" />
          <select v-if="item(l)?.variantes?.length" :value="l.variante_id || ''"
                  @change="mudarFixo(i, { variante_id: Number($event.target.value) || null })"
                  class="mt-1 w-full max-w-[240px] px-2 py-1 rounded-lg text-xs border focus:outline-none" :class="selectCls(l)">
            <option value="" disabled>Escolhe a variação…</option>
            <option v-for="v in item(l).variantes" :key="v.id" :value="v.id">{{ v.nome }} · {{ dinheiro(v.preco) }}</option>
          </select>
          <p v-else class="text-xs" :class="claro ? 'text-gray-500' : 'text-zinc-500'">{{ dinheiro(precoLinha(l)) }} / un.</p>
          <p v-if="problemaDe(l)" class="text-[11px] text-amber-500 mt-0.5">{{ problemaDe(l) }}</p>
        </div>
        <div class="flex items-center rounded-lg border flex-shrink-0" :class="claro ? 'border-gray-300' : 'border-zinc-700'">
          <button type="button" aria-label="Menos" @click="mudarFixo(i, { quantidade: Math.max(1, l.quantidade - 1) })"
                  class="w-7 h-7 text-sm" :class="claro ? 'text-gray-600' : 'text-zinc-300'">−</button>
          <span class="w-7 text-center text-sm font-semibold" :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ l.quantidade }}</span>
          <button type="button" aria-label="Mais" @click="mudarFixo(i, { quantidade: Math.min(99, l.quantidade + 1) })"
                  class="w-7 h-7 text-sm" :class="claro ? 'text-gray-600' : 'text-zinc-300'">+</button>
        </div>
        <BotaoRetirar :claro="claro" :nome="item(l)?.nome" @click="emitir(linhas.filter((_, j) => j !== i))" />
      </div>
      <p v-if="!linhas.length" class="text-xs px-3 py-2 border border-dashed rounded-xl"
         :class="claro ? 'text-gray-500 border-gray-300' : 'text-zinc-500 border-zinc-700'">
        Nenhum produto fixo{{ gruposLista.length ? ' — o conjunto é só de escolhas.' : '.' }}
      </p>
      <PesquisaProduto :catalogo="catalogo" :usados="linhas.map(chave)" :claro="claro" :mostrar-origem="mostrarOrigem"
                       @escolher="adicionarFixo" />
    </section>

    <!-- ── Escolhas do cliente ── -->
    <section class="space-y-3">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs font-semibold" :class="claro ? 'text-gray-600' : 'text-zinc-400'">
          O cliente escolhe <span class="font-normal opacity-70">· ex.: a bebida, o acompanhamento, extras</span>
        </p>
        <button type="button" @click="novoGrupo"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex-shrink-0"
                :class="claro ? 'border-gray-300 text-gray-700 hover:bg-gray-50' : 'border-zinc-700 text-zinc-300 hover:border-zinc-500'">
          + Escolha
        </button>
      </div>

      <div v-for="(g, gi) in gruposLista" :key="'g' + gi" class="rounded-xl border p-3 space-y-2"
           :class="claro ? 'border-gray-200 bg-gray-50' : 'border-zinc-700 bg-zinc-800/40'">
        <div class="flex flex-wrap items-end gap-2">
          <label class="flex-1 min-w-[140px]">
            <span class="block text-[11px] mb-1" :class="claro ? 'text-gray-500' : 'text-zinc-500'">Nome da escolha</span>
            <input :value="g.nome" @input="mudarGrupo(gi, { nome: $event.target.value })" maxlength="60" placeholder="Ex.: Bebida"
                   class="w-full px-2.5 py-1.5 rounded-lg text-sm border focus:outline-none focus:border-red-500" :class="inputCls" />
          </label>
          <label class="w-20">
            <span class="block text-[11px] mb-1" :class="claro ? 'text-gray-500' : 'text-zinc-500'">Mínimo</span>
            <input type="number" min="0" :max="g.maximo" :value="g.minimo"
                   @input="mudarGrupo(gi, { minimo: Math.max(0, Number($event.target.value) || 0) })"
                   class="w-full px-2.5 py-1.5 rounded-lg text-sm border focus:outline-none focus:border-red-500" :class="inputCls" />
          </label>
          <label class="w-20">
            <span class="block text-[11px] mb-1" :class="claro ? 'text-gray-500' : 'text-zinc-500'">Máximo</span>
            <input type="number" min="1" :value="g.maximo"
                   @input="mudarGrupo(gi, { maximo: Math.max(1, Number($event.target.value) || 1) })"
                   class="w-full px-2.5 py-1.5 rounded-lg text-sm border focus:outline-none focus:border-red-500" :class="inputCls" />
          </label>
          <BotaoRetirar :claro="claro" :nome="g.nome || 'escolha'" @click="emitirGrupos(gruposLista.filter((_, j) => j !== gi))" />
        </div>
        <p class="text-[11px]" :class="avisoGrupo(g) ? 'text-amber-500' : (claro ? 'text-gray-500' : 'text-zinc-500')">
          {{ avisoGrupo(g) || resumoGrupo(g) }}
        </p>

        <div v-for="(o, oi) in g.opcoes" :key="'o' + chave(o) + ':' + oi"
             class="flex items-center gap-3 p-2 rounded-lg border" :class="caixa(o)">
          <Miniatura :item="item(o)" :claro="claro" pequena />
          <div class="flex-1 min-w-0">
            <NomeLinha :item="item(o)" :l="o" :mostrar-origem="mostrarOrigem" :claro="claro" />
            <select v-if="item(o)?.variantes?.length" :value="o.variante_id || ''"
                    @change="mudarOpcao(gi, oi, { variante_id: Number($event.target.value) || null })"
                    class="mt-1 w-full max-w-[220px] px-2 py-1 rounded-lg text-xs border focus:outline-none" :class="selectCls(o)">
              <option value="" disabled>Escolhe a variação…</option>
              <option v-for="v in item(o).variantes" :key="v.id" :value="v.id">{{ v.nome }}</option>
            </select>
            <p v-if="problemaDe(o)" class="text-[11px] text-amber-500 mt-0.5">{{ problemaDe(o) }}</p>
          </div>
          <label class="flex items-center gap-1 flex-shrink-0" title="Custo extra desta opção (0 = incluída no preço)">
            <span class="text-xs" :class="claro ? 'text-gray-500' : 'text-zinc-500'">+</span>
            <input type="number" min="0" step="0.01" :value="o.preco_extra"
                   @input="mudarOpcao(gi, oi, { preco_extra: $event.target.value })"
                   class="w-20 px-2 py-1 rounded-lg text-xs border text-right focus:outline-none focus:border-red-500" :class="inputCls" />
            <span class="text-xs" :class="claro ? 'text-gray-500' : 'text-zinc-500'">€</span>
          </label>
          <BotaoRetirar :claro="claro" :nome="item(o)?.nome" @click="mudarGrupo(gi, { opcoes: g.opcoes.filter((_, j) => j !== oi) })" />
        </div>

        <PesquisaProduto :catalogo="catalogo" :usados="g.opcoes.map(chave)" :claro="claro" :mostrar-origem="mostrarOrigem"
                         placeholder="Adicionar opção a esta escolha…" @escolher="p => adicionarOpcao(gi, p)" />
      </div>
    </section>

    <!-- preço: soma em separado vs preço do conjunto -->
    <div v-if="linhas.length || gruposLista.length" class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs px-3 py-2 rounded-xl"
         :class="claro ? 'bg-gray-50 text-gray-600' : 'bg-zinc-800/60 text-zinc-400'">
      <span>Separados{{ temObrigatorias ? ' (opções mais baratas)' : '' }}: <b :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ dinheiro(soma) }}</b></span>
      <span v-if="precoNum > 0">Conjunto: <b :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ dinheiro(precoNum) }}</b></span>
      <span v-if="precoNum > 0 && soma - precoNum >= 0.01" class="font-semibold text-green-500">o cliente poupa {{ dinheiro(soma - precoNum) }}</span>
      <span v-else-if="precoNum > 0 && precoNum - soma >= 0.01" class="font-semibold text-amber-500">custa mais {{ dinheiro(precoNum - soma) }} do que em separado</span>
    </div>
  </div>
</template>

<script>
import { h } from 'vue'
import PesquisaProduto from './PesquisaProduto.vue'

const dinheiro = v => new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)

// pequenas peças de apresentação partilhadas pelas linhas fixas e pelas opções
const Miniatura = {
  props: { item: Object, claro: Boolean, pequena: Boolean },
  setup (p) {
    return () => {
      const t = p.pequena ? 'w-8 h-8' : 'w-10 h-10'
      return p.item?.imagem
        ? h('img', { src: p.item.imagem, alt: '', class: `${t} rounded-lg object-cover flex-shrink-0` })
        : h('span', { class: `${t} rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold ` +
                             (p.claro ? 'bg-gray-100 text-gray-400' : 'bg-zinc-700 text-zinc-400') }, (p.item?.nome || '?').charAt(0))
    }
  },
}
const NomeLinha = {
  props: { item: Object, l: Object, mostrarOrigem: Boolean, claro: Boolean },
  setup (p) {
    return () => h('p', { class: 'text-sm font-semibold truncate ' + (p.claro ? 'text-gray-900' : 'text-zinc-100') }, [
      p.item?.nome || 'Produto removido',
      p.mostrarOrigem ? h('span', {
        class: 'ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold align-middle ' +
               (p.l.origem === 'pos' ? 'bg-sky-500/15 text-sky-500' : 'bg-red-500/15 text-red-500'),
      }, p.l.origem === 'pos' ? 'POS' : 'Loja') : null,
    ])
  },
}
const BotaoRetirar = {
  props: { claro: Boolean, nome: String },
  emits: ['click'],
  setup (p, { emit }) {
    return () => h('button', {
      type: 'button', 'aria-label': 'Retirar ' + (p.nome || ''), onClick: () => emit('click'),
      class: 'w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition ' +
             (p.claro ? 'text-gray-400 hover:text-red-500 hover:bg-red-50' : 'text-zinc-500 hover:text-red-400 hover:bg-red-500/10'),
    }, '✕')
  },
}

export default {
  name: 'ConjuntoEditor',
  components: { PesquisaProduto, Miniatura, NomeLinha, BotaoRetirar },
  props: {
    modelValue:    { type: Array, default: () => [] },
    grupos:        { type: Array, default: () => [] },
    catalogo:      { type: Array, default: () => [] },
    precoConjunto: { type: [String, Number], default: '' },
    mostrarOrigem: { type: Boolean, default: false },
    problemas:     { type: Object, default: () => ({}) },   // 'origem-id' → texto
    claro:         { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'update:grupos'],

  computed: {
    linhas () { return this.modelValue },
    gruposLista () { return this.grupos },
    porChave () {
      const m = {}
      this.catalogo.forEach(p => { m[p.origem + '-' + p.id] = p })
      return m
    },
    temObrigatorias () { return this.gruposLista.some(g => g.minimo > 0) },
    // fixos + as opções mais baratas de cada escolha obrigatória (como o servidor)
    soma () {
      let t = this.linhas.reduce((s, l) => s + this.precoLinha(l) * l.quantidade, 0)
      this.gruposLista.forEach(g => {
        if (!g.minimo) return
        const precos = g.opcoes.map(o => this.precoLinha(o) * (o.quantidade || 1)).sort((a, b) => a - b)
        t += precos.slice(0, g.minimo).reduce((s, x) => s + x, 0)
      })
      return t
    },
    precoNum () { return Number(this.precoConjunto) || 0 },
    inputCls () { return this.claro ? 'bg-white border-gray-300 text-gray-900' : 'bg-zinc-900 border-zinc-700 text-zinc-100' },
  },

  methods: {
    dinheiro,
    chave (l) { return (l.origem || 'loja') + '-' + l.produto_id },
    item (l) { return this.porChave[this.chave(l)] },
    precoLinha (l) {
      const p = this.item(l)
      if (!p) return 0
      const v = l.variante_id && p.variantes?.find(x => x.id === l.variante_id)
      return Number(v ? v.preco : p.preco) || 0
    },
    problemaDe (l) {
      const p = this.item(l)
      if (!p) return 'Este produto já não existe.'
      if (p.ativo === false) return 'Este produto está desactivado.'
      if (p.variantes?.length && !l.variante_id) return 'Escolhe a variação.'
      return this.problemas[this.chave(l)] || ''
    },
    caixa (l) {
      if (this.problemaDe(l)) return 'border-amber-500/60 ' + (this.claro ? 'bg-amber-50' : 'bg-amber-500/5')
      return this.claro ? 'border-gray-200 bg-white' : 'border-zinc-700 bg-zinc-800/60'
    },
    selectCls (l) {
      return [this.claro ? 'bg-white border-gray-300 text-gray-800' : 'bg-zinc-900 border-zinc-700 text-zinc-200',
              !l.variante_id && 'border-amber-500']
    },
    resumoGrupo (g) {
      const n = g.opcoes.length
      if (g.minimo === 0) return `Opcional · o cliente pode escolher até ${g.maximo} de ${n} opções.`
      if (g.minimo === g.maximo) return `Obrigatório · o cliente escolhe ${g.minimo} de ${n} opções.`
      return `O cliente escolhe entre ${g.minimo} e ${g.maximo} de ${n} opções.`
    },
    avisoGrupo (g) {
      if (!g.nome.trim()) return 'Dá um nome a esta escolha (ex.: Bebida).'
      if (!g.opcoes.length) return 'Adiciona as opções que o cliente pode escolher.'
      if (g.minimo > g.maximo) return 'O mínimo não pode ser maior do que o máximo.'
      if (g.maximo > g.opcoes.length) return `Há só ${g.opcoes.length} opções — o máximo não pode ser ${g.maximo}.`
      return ''
    },

    emitir (linhas) { this.$emit('update:modelValue', linhas) },
    emitirGrupos (gs) { this.$emit('update:grupos', gs) },
    novaLinha (p, extra = {}) {
      return {
        origem: p.origem, produto_id: p.id,
        variante_id: p.variantes?.length === 1 ? p.variantes[0].id : null,
        quantidade: 1, ...extra,
      }
    },
    mudarFixo (i, alt) {
      const linhas = this.linhas.slice()
      linhas[i] = { ...linhas[i], ...alt }
      this.emitir(linhas)
    },
    adicionarFixo (p) { this.emitir([...this.linhas, this.novaLinha(p)]) },

    novoGrupo () {
      this.emitirGrupos([...this.gruposLista, { nome: '', minimo: 1, maximo: 1, opcoes: [] }])
    },
    mudarGrupo (gi, alt) {
      const gs = this.gruposLista.slice()
      gs[gi] = { ...gs[gi], ...alt }
      this.emitirGrupos(gs)
    },
    mudarOpcao (gi, oi, alt) {
      const opcoes = this.gruposLista[gi].opcoes.slice()
      opcoes[oi] = { ...opcoes[oi], ...alt }
      this.mudarGrupo(gi, { opcoes })
    },
    adicionarOpcao (gi, p) {
      this.mudarGrupo(gi, { opcoes: [...this.gruposLista[gi].opcoes, this.novaLinha(p, { preco_extra: '0' })] })
    },
  },
}

// validação partilhada pelos formulários (backoffice e POS) antes de enviar
export function erroConjunto (linhas, grupos, catalogo) {
  const porChave = {}
  catalogo.forEach(p => { porChave[p.origem + '-' + p.id] = p })
  const semVariante = l => porChave[(l.origem || 'loja') + '-' + l.produto_id]?.variantes?.length && !l.variante_id
  if (!linhas.length && !grupos.length) return 'Adiciona produtos ou escolhas ao conjunto.'
  if (linhas.some(semVariante)) return 'Escolhe a variação de cada produto do conjunto.'
  for (const g of grupos) {
    if (!g.nome.trim()) return 'Dá um nome a cada escolha (ex.: Bebida).'
    if (!g.opcoes.length) return `Adiciona opções a "${g.nome}".`
    if (g.minimo > g.maximo) return `Em "${g.nome}", o mínimo não pode ser maior do que o máximo.`
    if (g.maximo > g.opcoes.length) return `Em "${g.nome}" há só ${g.opcoes.length} opções.`
    if (g.opcoes.some(semVariante)) return `Escolhe a variação de cada opção em "${g.nome}".`
    if (g.opcoes.some(o => !(Number(o.preco_extra) >= 0))) return `Em "${g.nome}", o custo extra tem de ser 0 ou mais.`
  }
  return ''
}

// produto vindo do servidor → estado dos formulários
export function gruposDoProduto (produto) {
  return (produto?.grupos || []).map(g => ({
    id: g.id, nome: g.nome, minimo: g.minimo, maximo: g.maximo,
    opcoes: g.opcoes.map(o => ({
      id: o.id, origem: o.origem, produto_id: o.produto_id, variante_id: o.variante_id,
      quantidade: o.quantidade, preco_extra: o.preco_extra,
    })),
  }))
}
</script>
