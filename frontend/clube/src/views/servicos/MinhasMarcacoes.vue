<template>
  <!-- /minhas-marcacoes — as marcações de serviços do cliente -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="$router.push({ path: '/Home', query: { perfil: 'marcacoes' } })" class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold flex-1">As minhas marcações</h1>
      <NotificacaoSino :isDark="isDark" />
    </header>
    <main class="max-w-2xl mx-auto px-4 py-5 space-y-4 pb-24">
      <div class="flex gap-1 rounded-xl p-1" :class="isDark ? 'bg-zinc-900' : 'bg-white border border-gray-200'" role="tablist">
        <button v-for="t in [{ k: 'proximas', n: 'Próximas' }, { k: 'anteriores', n: 'Anteriores' }]" :key="t.k" type="button" role="tab"
          :aria-selected="tipo === t.k" @click="mudarTipo(t.k)" :data-teste="`tipo-${t.k}`"
          :class="['flex-1 py-2 rounded-lg text-sm font-semibold', tipo === t.k ? 'bg-red-600 text-white' : (isDark ? 'text-zinc-400' : 'text-zinc-500')]">{{ t.n }}</button>
      </div>
      <div v-if="carregando" class="flex justify-center py-10"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-xl text-red-500" /></div>
      <p v-else-if="!lista.length" class="text-center text-sm py-10 text-zinc-500">
        {{ tipo === 'proximas' ? 'Não tens marcações por fazer.' : 'Ainda não tens marcações anteriores.' }}</p>
      <CartaoMarcacao v-for="m in lista" :key="m.id" :m="m" :isDark="isDark" @click="$router.push(`/minhas-marcacoes/${m.id}`)" />
      <div v-if="!carregando && lista.length < total" class="pt-2 text-center">
        <button type="button" @click="carregarMais" :disabled="aCarregarMais" data-teste="ver-mais-marcacoes"
          class="px-4 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
          :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-white border border-gray-200 hover:bg-gray-50 text-zinc-600'">
          {{ aCarregarMais ? 'A carregar…' : `Ver mais (${total - lista.length} restantes)` }}
        </button>
      </div>
    </main>
  </div>
</template>

<script>
import api from '@/services/api'
import { ouvirMarcacoes } from '@/utils/servicos'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import CartaoMarcacao from '@/components/servicos/CartaoMarcacao.vue'
import { temaEscuro } from '@/utils/tema'

const POR_PAGINA = 20

export default {
  name: 'MinhasMarcacoes',
  components: { NotificacaoSino, CartaoMarcacao },
  data () {
    // ?tipo=anteriores (o "Ver todas" do perfil e o voltar da ficha abrem no mesmo separador)
    return { lista: [], total: 0, aCarregarMais: false, tipo: this.$route.query.tipo === 'anteriores' ? 'anteriores' : 'proximas',
             carregando: true, isDark: temaEscuro() }
  },
  created () { this.carregar() },
  // tempo real (utils/servicos.js ouvirMarcacoes): a loja confirmou, propôs outra hora, escreveu…
  mounted () { this.desligar = ouvirMarcacoes(() => this.carregar(true)) },
  beforeUnmount () { this.desligar?.() },
  methods: {
    mudarTipo (k) {
      if (this.tipo === k) return
      this.tipo = k
      this.$router.replace({ query: k === 'anteriores' ? { tipo: k } : {} })
      this.carregar()
    },
    // 20 de cada vez; o tempo real recarrega sem spinner o que já estava mostrado (mantém o "Ver mais")
    async carregar (silencioso = false) {
      const pedido = (this.pedido || 0) + 1
      this.pedido = pedido
      if (!silencioso) this.carregando = true
      const limit = silencioso ? Math.min(Math.max(POR_PAGINA, this.lista.length), 100) : POR_PAGINA
      try {
        const { data } = await api.get('/app/marcacoes/', { params: { tipo: this.tipo, offset: 0, limit } })
        if (pedido !== this.pedido) return
        this.lista = data.results || []
        this.total = data.count ?? this.lista.length
      } catch (e) { /* fica o que havia */ } finally { if (pedido === this.pedido) this.carregando = false }
    },
    async carregarMais () {
      if (this.aCarregarMais) return
      this.aCarregarMais = true
      const pedido = this.pedido
      try {
        const { data } = await api.get('/app/marcacoes/', { params: { tipo: this.tipo, offset: this.lista.length, limit: POR_PAGINA } })
        if (pedido !== this.pedido) return
        const vistos = new Set(this.lista.map(m => m.id))
        this.lista = [...this.lista, ...(data.results || []).filter(m => !vistos.has(m.id))]
        this.total = data.count ?? this.total
      } catch (e) { /* pode tentar outra vez */ } finally { this.aCarregarMais = false }
    },
  },
}
</script>
