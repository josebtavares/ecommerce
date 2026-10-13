<template>
  <!-- Produtos de um conjunto (menu, pack) — usado no backoffice da loja e no POS.
       v-model = [{ origem, produto_id, variante_id, quantidade }]
       catalogo = produtos que podem entrar: [{ origem, id, nome, preco, imagem, ativo, variantes: [{ id, nome, preco }] }] -->
  <div class="space-y-3">
    <!-- escolhidos -->
    <div v-if="linhas.length" class="space-y-2">
      <div v-for="(l, i) in linhas" :key="chave(l) + ':' + i"
           class="flex items-center gap-3 p-2 rounded-xl border"
           :class="[problemaDe(l) ? 'border-amber-500/60 ' + (claro ? 'bg-amber-50' : 'bg-amber-500/5') : (claro ? 'border-gray-200 bg-white' : 'border-zinc-700 bg-zinc-800/60')]">
        <img v-if="item(l)?.imagem" :src="item(l).imagem" alt="" class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
        <span v-else class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold"
              :class="claro ? 'bg-gray-100 text-gray-400' : 'bg-zinc-700 text-zinc-400'">{{ (item(l)?.nome || '?').charAt(0) }}</span>

        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold truncate" :class="claro ? 'text-gray-900' : 'text-zinc-100'">
            {{ item(l)?.nome || 'Produto removido' }}
            <span v-if="mostrarOrigem" class="ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold align-middle"
                  :class="l.origem === 'pos' ? 'bg-sky-500/15 text-sky-500' : 'bg-red-500/15 text-red-500'">
              {{ l.origem === 'pos' ? 'POS' : 'Loja' }}
            </span>
          </p>
          <!-- variação: obrigatória quando o produto tem stock por variação -->
          <select v-if="item(l)?.variantes?.length" :value="l.variante_id || ''"
                  @change="mudar(i, { variante_id: Number($event.target.value) || null })"
                  class="mt-1 w-full max-w-[240px] px-2 py-1 rounded-lg text-xs border focus:outline-none"
                  :class="[claro ? 'bg-white border-gray-300 text-gray-800' : 'bg-zinc-900 border-zinc-700 text-zinc-200',
                           !l.variante_id && 'border-amber-500']">
            <option value="" disabled>Escolhe a variação…</option>
            <option v-for="v in item(l).variantes" :key="v.id" :value="v.id">{{ v.nome }} · {{ dinheiro(v.preco) }}</option>
          </select>
          <p v-else class="text-xs" :class="claro ? 'text-gray-500' : 'text-zinc-500'">{{ dinheiro(precoLinha(l)) }} / un.</p>
          <p v-if="problemaDe(l)" class="text-[11px] text-amber-500 mt-0.5">{{ problemaDe(l) }}</p>
        </div>

        <div class="flex items-center rounded-lg border flex-shrink-0" :class="claro ? 'border-gray-300' : 'border-zinc-700'">
          <button type="button" aria-label="Menos" @click="mudar(i, { quantidade: Math.max(1, l.quantidade - 1) })"
                  class="w-7 h-7 text-sm" :class="claro ? 'text-gray-600' : 'text-zinc-300'">−</button>
          <span class="w-7 text-center text-sm font-semibold" :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ l.quantidade }}</span>
          <button type="button" aria-label="Mais" @click="mudar(i, { quantidade: Math.min(99, l.quantidade + 1) })"
                  class="w-7 h-7 text-sm" :class="claro ? 'text-gray-600' : 'text-zinc-300'">+</button>
        </div>
        <button type="button" :aria-label="'Retirar ' + (item(l)?.nome || '')" @click="retirar(i)"
                class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition"
                :class="claro ? 'text-gray-400 hover:text-red-500 hover:bg-red-50' : 'text-zinc-500 hover:text-red-400 hover:bg-red-500/10'">✕</button>
      </div>
    </div>
    <p v-else class="text-xs px-3 py-3 border border-dashed rounded-xl"
       :class="claro ? 'text-gray-500 border-gray-300' : 'text-zinc-500 border-zinc-700'">
      Ainda sem produtos. Procura abaixo os produtos que fazem parte deste conjunto.
    </p>

    <!-- adicionar -->
    <div class="relative">
      <input v-model="q" type="search" placeholder="Procurar produto para adicionar…"
             @focus="aberto = true" @keydown.esc="aberto = false"
             class="w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500"
             :class="claro ? 'bg-white border-gray-300 text-gray-900' : 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500'" />
      <div v-if="aberto" class="absolute z-20 left-0 right-0 mt-1 max-h-64 overflow-y-auto rounded-xl border shadow-xl"
           :class="claro ? 'bg-white border-gray-200' : 'bg-zinc-900 border-zinc-700'">
        <button v-for="p in sugestoes" :key="p.origem + '-' + p.id" type="button" @click="adicionar(p)"
                class="w-full flex items-center gap-3 px-3 py-2 text-left transition"
                :class="claro ? 'hover:bg-gray-50' : 'hover:bg-zinc-800'">
          <img v-if="p.imagem" :src="p.imagem" alt="" class="w-8 h-8 rounded-md object-cover flex-shrink-0" />
          <span v-else class="w-8 h-8 rounded-md flex-shrink-0" :class="claro ? 'bg-gray-100' : 'bg-zinc-800'"></span>
          <span class="flex-1 min-w-0">
            <span class="block text-sm truncate" :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ p.nome }}</span>
            <span class="block text-[11px]" :class="claro ? 'text-gray-500' : 'text-zinc-500'">
              {{ dinheiro(p.preco) }}<template v-if="p.variantes?.length"> · {{ p.variantes.length }} variações</template>
              <template v-if="mostrarOrigem"> · {{ p.origem === 'pos' ? 'POS' : 'Loja' }}</template>
            </span>
          </span>
          <span class="text-xs font-bold text-red-500">+</span>
        </button>
        <p v-if="!sugestoes.length" class="px-3 py-3 text-xs" :class="claro ? 'text-gray-500' : 'text-zinc-500'">
          {{ q ? 'Nenhum produto encontrado.' : 'Não há mais produtos para adicionar.' }}
        </p>
      </div>
      <div v-if="aberto" class="fixed inset-0 z-10" @click="aberto = false"></div>
    </div>

    <!-- preço: soma dos produtos em separado vs preço do conjunto -->
    <div v-if="linhas.length" class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs px-3 py-2 rounded-xl"
         :class="claro ? 'bg-gray-50 text-gray-600' : 'bg-zinc-800/60 text-zinc-400'">
      <span>Separados: <b :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ dinheiro(soma) }}</b></span>
      <span v-if="precoNum > 0">Conjunto: <b :class="claro ? 'text-gray-900' : 'text-zinc-100'">{{ dinheiro(precoNum) }}</b></span>
      <span v-if="precoNum > 0 && soma - precoNum >= 0.01" class="font-semibold text-green-500">o cliente poupa {{ dinheiro(soma - precoNum) }}</span>
      <span v-else-if="precoNum > 0 && precoNum - soma >= 0.01" class="font-semibold text-amber-500">custa mais {{ dinheiro(precoNum - soma) }} do que em separado</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConjuntoEditor',
  props: {
    modelValue:    { type: Array, default: () => [] },
    catalogo:      { type: Array, default: () => [] },
    precoConjunto: { type: [String, Number], default: '' },
    mostrarOrigem: { type: Boolean, default: false },
    problemas:     { type: Object, default: () => ({}) },   // 'origem-id' → texto
    claro:         { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],

  data () {
    return { q: '', aberto: false }
  },

  computed: {
    linhas () { return this.modelValue },
    porChave () {
      const m = {}
      this.catalogo.forEach(p => { m[p.origem + '-' + p.id] = p })
      return m
    },
    sugestoes () {
      const termo = this.q.trim().toLowerCase()
      return this.catalogo
        .filter(p => p.ativo !== false)
        // sem variações, um produto só entra uma vez (aumenta-se a quantidade)
        .filter(p => p.variantes?.length || !this.linhas.some(l => this.chave(l) === p.origem + '-' + p.id))
        .filter(p => !termo || p.nome.toLowerCase().includes(termo))
        .slice(0, 40)
    },
    soma () {
      return this.linhas.reduce((t, l) => t + this.precoLinha(l) * l.quantidade, 0)
    },
    precoNum () { return Number(this.precoConjunto) || 0 },
  },

  methods: {
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
      if (p.ativo === false) return 'Este produto está desactivado — o conjunto fica indisponível.'
      if (p.variantes?.length && !l.variante_id) return 'Escolhe a variação que entra no conjunto.'
      return this.problemas[this.chave(l)] || ''
    },
    dinheiro (v) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)
    },
    emitir (linhas) { this.$emit('update:modelValue', linhas) },
    mudar (i, alt) {
      const linhas = this.linhas.slice()
      linhas[i] = { ...linhas[i], ...alt }
      this.emitir(linhas)
    },
    retirar (i) { this.emitir(this.linhas.filter((_, j) => j !== i)) },
    adicionar (p) {
      this.emitir([...this.linhas, {
        origem: p.origem, produto_id: p.id,
        variante_id: p.variantes?.length === 1 ? p.variantes[0].id : null,
        quantidade: 1,
      }])
      this.q = ''
      this.aberto = false
    },
  },
}
</script>
