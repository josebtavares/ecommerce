<!-- HomeProcurar.vue — procurar uma loja ou um produto para o construtor da home (Admin → Página inicial) -->
<template>
  <div class="relative">
    <div v-if="valor && !limpar && !aEditar"
         class="flex items-center gap-2 px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl">
      <font-awesome-icon :icon="['fas', tipo === 'loja' ? 'store' : 'box']" class="text-zinc-500 w-3.5" />
      <span class="flex-1 text-sm text-zinc-100 truncate">{{ valor.nome }}</span>
      <button type="button" @click="aEditar = true; $nextTick(() => $refs.input?.focus())"
        class="text-xs font-semibold text-red-400 hover:text-red-300">Mudar</button>
    </div>
    <template v-else>
      <input ref="input" v-model="q" @input="agendar" @focus="aberto = true; if (!resultados.length) procurar()"
        @keydown.esc="fechar" @blur="fecharDepois"
        :placeholder="tipo === 'loja' ? 'Procurar loja…' : 'Procurar produto ou loja…'"
        class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
      <div v-if="aberto" class="absolute z-20 left-0 right-0 mt-1 max-h-72 overflow-y-auto bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl">
        <p v-if="loading" class="px-3 py-3 text-xs text-zinc-500">A procurar…</p>
        <p v-else-if="!resultados.length" class="px-3 py-3 text-xs text-zinc-500">Sem resultados.</p>
        <button v-for="r in resultados" :key="r.id" type="button" @mousedown.prevent="escolher(r)"
          class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-zinc-800 transition">
          <div class="flex-1 min-w-0">
            <p class="text-sm text-zinc-100 truncate">{{ r.nome }}</p>
            <p class="text-[11px] text-zinc-500 truncate">
              {{ tipo === 'loja' ? r.categoria : `${r.loja} · ${r.preco} €` }}
            </p>
          </div>
          <span v-if="tipo === 'loja' ? !r.ativa : (!r.ativo || !r.loja_ativa)"
                class="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-bold flex-shrink-0">
            {{ tipo === 'loja' ? r.estado : 'escondido' }}
          </span>
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'HomeProcurar',
  props: {
    tipo:   { type: String, required: true },       // 'loja' | 'produto'
    valor:  { type: Object, default: null },        // escolhido (mostra-se em vez da pesquisa)
    limpar: { type: Boolean, default: false },      // depois de escolher volta a pesquisa vazia (para adicionar vários)
    lojaId: { type: Number, default: null },        // só produtos desta loja
  },
  emits: ['escolher'],

  data () {
    return { q: '', resultados: [], aberto: false, loading: false, aEditar: false, timer: null, pedido: 0 }
  },

  watch: {
    tipo () { this.resultados = []; this.q = '' },
    lojaId () { this.resultados = [] },
  },

  beforeUnmount () { clearTimeout(this.timer) },

  methods: {
    agendar () {
      this.aberto = true
      clearTimeout(this.timer)
      this.timer = setTimeout(this.procurar, 250)
    },

    async procurar () {
      const n = ++this.pedido
      this.loading = true
      try {
        const params = { tipo: this.tipo, q: this.q }
        if (this.lojaId) params.loja_id = this.lojaId
        const { data } = await api.get('/app/admin/home/procurar/', { params })
        if (n === this.pedido) this.resultados = data
      } catch (e) {
        if (n === this.pedido) this.resultados = []
      } finally {
        if (n === this.pedido) this.loading = false
      }
    },

    escolher (r) {
      this.$emit('escolher', r)
      this.aberto = false
      this.aEditar = false
      if (this.limpar) this.q = ''
    },

    fechar () { this.aberto = false; this.aEditar = false },
    fecharDepois () { setTimeout(() => { this.aberto = false }, 150) },
  },
}
</script>
