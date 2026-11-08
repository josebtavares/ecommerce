<template>
  <!-- /encomendas — todas as encomendas do cliente, com separadores, pesquisa e "Ver mais". Tempo real. -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="$router.push('/Home')" class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold flex-1">As minhas encomendas</h1>
      <NotificacaoSino :isDark="isDark" />
    </header>

    <main class="max-w-2xl mx-auto px-4 py-5 space-y-4 pb-24">
      <div class="flex gap-1 rounded-xl p-1 overflow-x-auto" :class="isDark ? 'bg-zinc-900' : 'bg-white border border-gray-200'" role="tablist">
        <button v-for="t in SEPARADORES" :key="t.k" type="button" role="tab" :aria-selected="grupo === t.k ? 'true' : 'false'"
          @click="mudarGrupo(t.k)" :data-teste="`sep-${t.k || 'todas'}`"
          :class="['flex-1 py-2 px-2 rounded-lg text-sm font-semibold whitespace-nowrap', grupo === t.k ? 'bg-red-600 text-white' : (isDark ? 'text-zinc-400' : 'text-zinc-500')]">{{ t.n }}</button>
      </div>

      <div class="relative">
        <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm text-zinc-500" />
        <input v-model="termo" type="search" maxlength="100" placeholder="Pesquisar pelo nº da encomenda ou pela loja"
          @input="pesquisarDepois" data-teste="pesquisa-encomendas"
          class="w-full pl-10 pr-3 py-2.5 rounded-xl text-sm border focus:outline-none focus:border-red-500"
          :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 placeholder-zinc-500' : 'bg-white border-gray-200 text-zinc-900 placeholder-zinc-400'" />
      </div>

      <div v-if="carregando" class="flex justify-center py-10"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-xl text-red-500" /></div>
      <p v-else-if="erro" class="text-center text-sm py-10 text-red-400">{{ erro }}</p>
      <p v-else-if="!lista.length" class="text-center text-sm py-10 text-zinc-500" data-teste="sem-encomendas">{{ textoVazio }}</p>

      <template v-else>
        <p class="text-xs text-zinc-500" data-teste="total-encomendas">{{ total }} encomenda{{ total === 1 ? '' : 's' }}</p>
        <router-link v-for="enc in lista" :key="enc.id" :to="`/encomendas/${enc.id}`" :data-teste="`encomenda-${enc.id}`"
          class="block rounded-2xl border p-4" :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-gray-200 hover:border-gray-400'">
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <p class="font-semibold truncate">#{{ enc.id }} · {{ enc.loja_nome }}</p>
              <div class="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                <span class="text-xs text-zinc-500">{{ dataCurta(enc.data_criacao) }}</span>
                <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', corEstado(enc)]">{{ nomeEstado(enc) }}</span>
                <EstadoReembolso v-if="enc.reembolso" :estado="enc.reembolso.estado" :valor="enc.reembolso.valor" :metodo="enc.reembolso.metodo" />
              </div>
              <p v-if="enc.agendada_texto && !['concluido', 'cancelado'].includes(enc.status)"
                 class="text-[11px] font-semibold mt-1" :class="isDark ? 'text-amber-300' : 'text-amber-700'">
                {{ enc.agendamento_origem === 'cliente' ? 'Agendada para' : 'Preparada a partir de' }} {{ enc.agendada_texto }}
              </p>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span class="text-sm font-bold text-red-500">{{ formatarDinheiro(enc.valor_total || 0) }}</span>
              <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-xs text-zinc-500" />
            </div>
          </div>
        </router-link>

        <div class="pt-2 text-center">
          <button v-if="lista.length < total" type="button" @click="carregarMais" :disabled="aCarregarMais" data-teste="ver-mais-encomendas"
            class="px-4 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
            :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-white border border-gray-200 hover:bg-gray-50 text-zinc-600'">
            {{ aCarregarMais ? 'A carregar…' : `Ver mais (${total - lista.length} restantes)` }}
          </button>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
import api from '@/services/api'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import { temaEscuro } from '@/utils/tema'
import { formatarDinheiro } from '@/utils/dinheiro'
import { ouvirEncomendas } from '@/utils/tempoRealEncomendas'
import { SEPARADORES, nomeEstado, corEstado, dataCurta } from '@/utils/encomendasCliente'

const POR_PAGINA = 20
const GRUPOS = SEPARADORES.map(s => s.k)

export default {
  name: 'MinhasEncomendas',
  components: { NotificacaoSino, EstadoReembolso },
  data () {
    // separador e pesquisa ficam no endereço: voltar da ficha volta ao mesmo sítio
    const q = this.$route.query
    return {
      lista: [], total: 0, carregando: true, aCarregarMais: false, erro: '',
      grupo: GRUPOS.includes(q.estado) ? q.estado : '',
      termo: typeof q.q === 'string' ? q.q.slice(0, 100) : '',
      isDark: temaEscuro(), SEPARADORES,
    }
  },
  computed: {
    textoVazio () {
      if (this.termo.trim()) return 'Nenhuma encomenda encontrada.'
      return { em_curso: 'Não tens encomendas em curso.', concluidas: 'Ainda não tens encomendas concluídas.',
               canceladas: 'Não tens encomendas canceladas.' }[this.grupo] || 'Ainda não tens encomendas.'
    },
  },
  created () { this.carregar() },
  // tempo real (utils/tempoRealEncomendas.js): a loja mudou o estado, anexou a fatura… — sem spinner, mantém o "Ver mais"
  mounted () { this.desligar = ouvirEncomendas(() => this.carregar(true)) },
  beforeUnmount () { this.desligar?.(); clearTimeout(this.tempoPesquisa) },
  methods: {
    formatarDinheiro, nomeEstado, corEstado, dataCurta,
    filtros (limit, offset) {
      const p = { limit, offset }
      if (this.grupo) p.grupo = this.grupo
      if (this.termo.trim()) p.q = this.termo.trim()
      return p
    },
    async carregar (silencioso = false) {
      const pedido = (this.pedido || 0) + 1
      this.pedido = pedido
      if (!silencioso) this.carregando = true
      const limite = silencioso ? Math.max(POR_PAGINA, this.lista.length) : POR_PAGINA
      try {
        const { data } = await api.get('/app/encomenda/', { params: this.filtros(limite, 0) })
        if (pedido !== this.pedido) return            // chegou depois de outro pedido (mudou o separador/pesquisa)
        this.lista = data.results || []
        this.total = data.count ?? this.lista.length
        this.erro = ''
      } catch (e) {
        if (pedido === this.pedido && !silencioso) this.erro = 'Não foi possível carregar as encomendas.'
      } finally {
        if (pedido === this.pedido) this.carregando = false
      }
    },
    async carregarMais () {
      if (this.aCarregarMais) return
      this.aCarregarMais = true
      const pedido = this.pedido
      try {
        const { data } = await api.get('/app/encomenda/', { params: this.filtros(POR_PAGINA, this.lista.length) })
        if (pedido !== this.pedido) return
        const vistos = new Set(this.lista.map(e => e.id))
        this.lista = [...this.lista, ...(data.results || []).filter(e => !vistos.has(e.id))]
        this.total = data.count ?? this.total
      } catch (e) { /* fica o que havia; pode tentar outra vez */ } finally { this.aCarregarMais = false }
    },
    guardarNoEndereco () {
      const query = {}
      if (this.grupo) query.estado = this.grupo
      if (this.termo.trim()) query.q = this.termo.trim()
      this.$router.replace({ query })
    },
    mudarGrupo (k) {
      if (this.grupo === k) return
      this.grupo = k
      this.guardarNoEndereco()
      this.carregar()
    },
    pesquisarDepois () {
      clearTimeout(this.tempoPesquisa)
      this.tempoPesquisa = setTimeout(() => { this.guardarNoEndereco(); this.carregar() }, 350)
    },
  },
}
</script>
