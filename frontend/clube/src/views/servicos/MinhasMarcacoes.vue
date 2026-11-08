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
    </main>
  </div>
</template>

<script>
import api from '@/services/api'
import { ouvirMarcacoes } from '@/utils/servicos'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import CartaoMarcacao from '@/components/servicos/CartaoMarcacao.vue'
import { temaEscuro } from '@/utils/tema'

export default {
  name: 'MinhasMarcacoes',
  components: { NotificacaoSino, CartaoMarcacao },
  data () {
    // ?tipo=anteriores (o "Ver todas" do perfil e o voltar da ficha abrem no mesmo separador)
    return { lista: [], tipo: this.$route.query.tipo === 'anteriores' ? 'anteriores' : 'proximas', carregando: true, isDark: temaEscuro() }
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
    async carregar (silencioso = false) {
      const pedido = (this.pedido || 0) + 1
      this.pedido = pedido
      if (!silencioso) this.carregando = true
      try {
        const { data } = await api.get('/app/marcacoes/', { params: { tipo: this.tipo } })
        if (pedido === this.pedido) this.lista = data
      } catch (e) { /* fica o que havia */ } finally { if (pedido === this.pedido) this.carregando = false }
    },
  },
}
</script>
