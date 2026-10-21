<template>
  <!-- Pesquisa → separador "Serviços": serviços de todas as lojas com marcações abertas -->
  <div class="w-full" data-teste="catalogo-servicos">
    <div class="rounded-2xl border p-4 mb-6" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200 shadow-sm'">
      <div class="relative">
        <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'" />
        <input v-model="q" @input="adiar" placeholder="Pesquisar serviço, ex.: corte, unhas, tatuagem…" aria-label="Pesquisar serviço"
          class="w-full pl-9 pr-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500"
          :class="isDark ? 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500' : 'bg-stone-50 border-stone-300 text-zinc-900 placeholder-zinc-400'" />
      </div>
    </div>
    <div v-if="carregando" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <div v-for="n in 5" :key="n" class="h-56 rounded-2xl animate-pulse" :class="isDark ? 'bg-zinc-900' : 'bg-stone-200'"></div>
    </div>
    <p v-else-if="!lista.length" class="text-center text-sm py-10" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
      {{ q ? 'Nenhum serviço encontrado.' : 'Ainda não há serviços com marcação online.' }}</p>
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <ServicoCard v-for="s in lista" :key="s.id" :s="s" :isDark="isDark" />
    </div>
    <div v-if="proximo !== null && !carregando" class="flex justify-center mt-6">
      <button type="button" @click="mais" :disabled="aCarregarMais"
        class="px-5 py-2 rounded-xl text-sm font-semibold border" :class="isDark ? 'border-zinc-700 text-zinc-200' : 'border-stone-300 text-zinc-700'">
        {{ aCarregarMais ? 'A carregar…' : 'Ver mais' }}</button>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import ServicoCard from '@/components/servicos/ServicoCard.vue'

export default {
  name: 'ServicoCatalog',
  components: { ServicoCard },
  props: { isDark: { type: Boolean, default: true } },
  data () { return { q: '', lista: [], proximo: null, carregando: true, aCarregarMais: false, relogio: null } },
  created () { this.carregar() },
  beforeUnmount () { clearTimeout(this.relogio) },
  methods: {
    adiar () { clearTimeout(this.relogio); this.relogio = setTimeout(() => this.carregar(), 350) },
    async carregar () {
      this.carregando = true
      try {
        const { data } = await api.get('/app/servicos/pesquisa/', { params: { q: this.q || undefined, limit: 20 } })
        this.lista = data.results
        this.proximo = data.next_offset
      } finally { this.carregando = false }
    },
    async mais () {
      this.aCarregarMais = true
      try {
        const { data } = await api.get('/app/servicos/pesquisa/', { params: { q: this.q || undefined, limit: 20, offset: this.proximo } })
        this.lista.push(...data.results)
        this.proximo = data.next_offset
      } finally { this.aCarregarMais = false }
    },
  },
}
</script>
