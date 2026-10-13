<template>
  <!-- Procurar e escolher um produto do catálogo (conjuntos: produtos fixos e opções das escolhas) -->
  <div class="relative">
    <input v-model="q" type="search" :placeholder="placeholder"
           @focus="aberto = true" @keydown.esc="aberto = false"
           class="w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500"
           :class="claro ? 'bg-white border-gray-300 text-gray-900' : 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500'" />
    <div v-if="aberto" class="absolute z-20 left-0 right-0 mt-1 max-h-64 overflow-y-auto rounded-xl border shadow-xl"
         :class="claro ? 'bg-white border-gray-200' : 'bg-zinc-900 border-zinc-700'">
      <button v-for="p in sugestoes" :key="p.origem + '-' + p.id" type="button" @click="escolher(p)"
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
</template>

<script>
export default {
  name: 'PesquisaProduto',
  props: {
    catalogo:      { type: Array, default: () => [] },
    // chaves 'origem-id' já usadas (produtos sem variações só entram uma vez)
    usados:        { type: Array, default: () => [] },
    placeholder:   { type: String, default: 'Procurar produto para adicionar…' },
    mostrarOrigem: { type: Boolean, default: false },
    claro:         { type: Boolean, default: false },
  },
  emits: ['escolher'],

  data () {
    return { q: '', aberto: false }
  },

  computed: {
    sugestoes () {
      const termo = this.q.trim().toLowerCase()
      const usados = new Set(this.usados)
      return this.catalogo
        .filter(p => p.ativo !== false)
        .filter(p => p.variantes?.length || !usados.has(p.origem + '-' + p.id))
        .filter(p => !termo || p.nome.toLowerCase().includes(termo))
        .slice(0, 40)
    },
  },

  methods: {
    dinheiro (v) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)
    },
    escolher (p) {
      this.$emit('escolher', p)
      this.q = ''
      this.aberto = false
    },
  },
}
</script>
