<!-- Pesquisa.vue — /pesquisa?q=…&tipo=produto|loja|servico — todos os resultados, por separador, com filtros.
     O endereço guarda a pesquisa e os filtros (pode partilhar-se). Backend: utils/pesquisa.py -->
<template>
  <div class="min-h-screen transition-colors" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-50 text-zinc-900'">
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="sair" />
    <MultiCart :isDark="isDark" :pesquisa="false" />

    <!-- topo: voltar + campo (o grupo carrinho/perfil fica à direita, fixo) -->
    <header class="sticky top-0 z-20 border-b backdrop-blur"
            :class="isDark ? 'bg-zinc-950/90 border-zinc-800' : 'bg-stone-50/90 border-stone-200'">
      <div class="max-w-6xl mx-auto px-4 md:px-8 h-[52px] md:h-[84px] flex items-center gap-3 pr-[200px] md:pr-[220px]">
        <router-link to="/Home" aria-label="Voltar ao início"
          class="w-9 h-9 rounded-xl flex items-center justify-center border flex-shrink-0 transition"
          :class="isDark ? 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800' : 'bg-white border-stone-300 hover:bg-stone-100'">
          <font-awesome-icon :icon="['fas', 'arrow-left']" class="text-sm" />
        </router-link>
        <h1 class="text-base md:text-lg font-bold truncate">Pesquisa</h1>
      </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 md:px-8 py-5 md:py-8">
      <CaixaPesquisa :key="q" :inicial="q" :isDark="isDark" class="max-w-2xl" />

      <p v-if="!q" class="mt-10 text-center text-sm" :class="tSub">Escreve o que procuras: um produto, uma loja ou um serviço.</p>

      <template v-else>
        <!-- separadores -->
        <div class="mt-6 flex gap-2 overflow-x-auto pb-1" role="tablist">
          <button v-for="t in TIPOS" :key="t.tipo" type="button" role="tab" :aria-selected="tipo === t.tipo"
            @click="mudar({ tipo: t.tipo })" :data-teste="`pesquisa-tab-${t.tipo}`"
            class="px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap transition border"
            :class="tipo === t.tipo ? 'bg-red-600 border-red-600 text-white'
                    : isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-stone-300 text-zinc-700 hover:border-stone-400'">
            {{ t.titulo }}
            <span v-if="totais[t.tipo] != null" class="ml-1 opacity-75">{{ totais[t.tipo] }}</span>
          </button>
        </div>

        <!-- filtros do separador -->
        <div v-if="tipo === 'produto'" class="mt-4 flex flex-wrap items-end gap-3">
          <label class="text-xs" :class="tSub">Preço mín.
            <input v-model.lazy="filtros.preco_min" @change="aplicar" type="number" min="0" inputmode="numeric"
              class="mt-1 block w-28 h-10 px-3 rounded-xl border text-sm" :class="campo" />
          </label>
          <label class="text-xs" :class="tSub">Preço máx.
            <input v-model.lazy="filtros.preco_max" @change="aplicar" type="number" min="0" inputmode="numeric"
              class="mt-1 block w-28 h-10 px-3 rounded-xl border text-sm" :class="campo" />
          </label>
          <label class="text-xs" :class="tSub">Ordenar
            <select v-model="filtros.ordem" @change="aplicar" class="mt-1 block h-10 px-3 rounded-xl border text-sm" :class="campo"
              data-teste="pesquisa-ordem">
              <option value="">Mais relevantes</option>
              <option value="preco">Preço: mais baixo</option>
              <option value="-preco">Preço: mais alto</option>
            </select>
          </label>
          <button v-if="temFiltros" type="button" @click="limparFiltros" class="h-10 text-sm font-semibold text-red-500 hover:text-red-400">
            Limpar filtros
          </button>
        </div>
        <div v-else-if="tipo === 'loja'" class="mt-4 flex flex-wrap items-end gap-3">
          <label class="text-xs" :class="tSub">Localização
            <input v-model.lazy="filtros.localizacao" @change="aplicar" type="text" maxlength="80" placeholder="ex.: Praia"
              class="mt-1 block w-48 h-10 px-3 rounded-xl border text-sm" :class="campo" />
          </label>
          <button v-if="temFiltros" type="button" @click="limparFiltros" class="h-10 text-sm font-semibold text-red-500 hover:text-red-400">
            Limpar filtros
          </button>
        </div>

        <!-- resultados -->
        <div v-if="aCarregar && !resultados.length" class="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div v-for="n in 8" :key="n" class="h-56 rounded-2xl animate-pulse" :class="isDark ? 'bg-zinc-900' : 'bg-stone-200'"></div>
        </div>

        <div v-else-if="!resultados.length" class="mt-12 text-center" data-teste="pesquisa-sem-resultados">
          <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="text-3xl" :class="tSub" />
          <p class="mt-4 font-semibold">Sem {{ rotulo.toLowerCase() }} para «{{ q }}»</p>
          <p v-if="sugestao" class="mt-2 text-sm" :class="tSub">
            Querias dizer <router-link :to="{ path: '/pesquisa', query: { q: sugestao } }" class="font-semibold text-red-500 hover:underline">{{ sugestao }}</router-link>?
          </p>
          <p v-else-if="outro" class="mt-2 text-sm" :class="tSub">
            Há resultados em <button type="button" @click="mudar({ tipo: outro.tipo })" class="font-semibold text-red-500 hover:underline">{{ outro.titulo }}</button>.
          </p>
          <p v-else class="mt-2 text-sm" :class="tSub">Experimenta outra palavra{{ temFiltros ? ' ou tira os filtros' : '' }}.</p>
        </div>

        <!-- produtos -->
        <div v-else-if="tipo === 'produto'" class="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4" data-teste="pesquisa-grelha">
          <router-link v-for="p in resultados" :key="p.id" :to="destino('produto', p)"
            class="group rounded-2xl border overflow-hidden transition"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-stone-200 hover:border-stone-300 shadow-sm'">
            <div class="aspect-square overflow-hidden flex items-center justify-center" :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'">
              <img v-if="p.imagem" v-img :src="$miniatura(p.imagem)" :alt="p.nome" class="w-full h-full object-cover group-hover:scale-105 transition" />
              <font-awesome-icon v-else :icon="['fas', p.video ? 'video' : 'box']" class="text-2xl" :class="tSub" />
            </div>
            <div class="p-3">
              <p class="text-sm font-medium line-clamp-2 min-h-[2.5rem]">
                <span v-for="(x, k) in destacar(p.nome, q)" :key="k" :class="x.m && 'text-red-500 font-bold'">{{ x.t }}</span>
              </p>
              <p class="mt-1 text-xs truncate" :class="tSub">{{ p.loja.nome }}</p>
              <div class="mt-2 flex items-center justify-between gap-2">
                <span class="font-bold text-red-500">{{ $dinheiro(p.preco) }}</span>
                <span v-if="p.esgotado" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-500">Esgotado</span>
              </div>
            </div>
          </router-link>
        </div>

        <!-- lojas -->
        <div v-else-if="tipo === 'loja'" class="mt-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-3" data-teste="pesquisa-grelha">
          <router-link v-for="l in resultados" :key="l.id" :to="destino('loja', l)"
            class="flex items-center gap-3 p-3 rounded-2xl border transition"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-stone-200 hover:border-stone-300 shadow-sm'">
            <div class="w-14 h-14 rounded-full overflow-hidden flex-shrink-0 flex items-center justify-center" :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'">
              <img v-if="l.logo" v-img :src="$miniatura(l.logo)" :alt="l.nome" class="w-full h-full object-cover" />
              <span v-else class="font-bold" :class="tSub">{{ l.nome.charAt(0) }}</span>
            </div>
            <div class="min-w-0">
              <p class="font-semibold truncate">
                <span v-for="(x, k) in destacar(l.nome, q)" :key="k" :class="x.m && 'text-red-500'">{{ x.t }}</span>
              </p>
              <p class="text-xs truncate" :class="tSub">{{ [l.categoria, l.localizacao].filter(Boolean).join(' · ') }}</p>
            </div>
          </router-link>
        </div>

        <!-- serviços -->
        <div v-else class="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4" data-teste="pesquisa-grelha">
          <ServicoCard v-for="s in resultados" :key="s.id" :s="s" :isDark="isDark" />
        </div>

        <div v-if="seguinte != null" class="mt-8 text-center">
          <button type="button" @click="carregar(true)" :disabled="aCarregar" data-teste="pesquisa-mais"
            class="px-6 py-3 rounded-xl text-sm font-semibold border transition disabled:opacity-50"
            :class="isDark ? 'border-zinc-700 hover:bg-zinc-900' : 'border-stone-300 hover:bg-white'">
            {{ aCarregar ? 'A carregar…' : 'Ver mais' }}
          </button>
        </div>
        <p v-if="erro" class="mt-6 text-center text-sm text-red-500">{{ erro }}</p>
      </template>
    </main>

    <SiteRodape :isDark="isDark" />
  </div>
</template>

<script>
import CaixaPesquisa from '@/components/pesquisa/CaixaPesquisa.vue'
import Profile from '@/components/profile/UserProfile.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import ServicoCard from '@/components/servicos/ServicoCard.vue'
import SiteRodape from '@/components/paginas/SiteRodape.vue'
import { procurar, destacar, destino, guardarRecente } from '@/services/pesquisa'
import { terminarSessao } from '@/services/api'
import { temaEscuro } from '@/utils/tema'

const TIPOS = [
  { tipo: 'produto', titulo: 'Produtos' },
  { tipo: 'loja', titulo: 'Lojas' },
  { tipo: 'servico', titulo: 'Serviços' },
]
const POR_PAGINA = 24
const FILTROS = ['preco_min', 'preco_max', 'ordem', 'localizacao']

export default {
  name: 'PaginaPesquisa',
  components: { CaixaPesquisa, Profile, MultiCart, ServicoCard, SiteRodape },

  data () {
    let user = {}
    try { user = JSON.parse(localStorage.getItem('user') || '{}') } catch { /* nada */ }
    return { TIPOS, isDark: temaEscuro(), user, resultados: [], totais: {}, seguinte: null, sugestao: null,
             aCarregar: false, erro: '', filtros: this.lerFiltros(), pedido: 0 }
  },

  computed: {
    q () { return String(this.$route.query.q || '').trim().slice(0, 80) },
    tipo () { return TIPOS.some(t => t.tipo === this.$route.query.tipo) ? this.$route.query.tipo : '' },
    rotulo () { return TIPOS.find(t => t.tipo === this.tipo)?.titulo || 'Resultados' },
    tSub () { return 'text-zinc-500' },
    campo () { return this.isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100' : 'bg-white border-stone-300 text-zinc-900' },
    temFiltros () { return FILTROS.some(f => this.$route.query[f]) },
    outro () { return TIPOS.find(t => t.tipo !== this.tipo && this.totais[t.tipo] > 0) || null },
  },

  watch: {
    '$route.query': { handler: 'aoMudar', immediate: true },
  },

  methods: {
    destacar,
    destino,

    lerFiltros () {
      const q = this.$route?.query || {}
      return Object.fromEntries(FILTROS.map(f => [f, q[f] || '']))
    },

    async aoMudar (novo, antigo) {
      if (this.$route.name !== 'Pesquisa') return
      this.filtros = this.lerFiltros()
      document.title = this.q ? `${this.q} — Pesquisa — Bende` : 'Pesquisa — Bende'
      if (!this.q) { this.resultados = []; return }
      guardarRecente(this.q)
      // pesquisa nova: contar em cada separador e abrir o primeiro que tem resultados
      if (!antigo || antigo.q !== novo.q) await this.contar()
      if (!this.tipo) {
        const primeiro = TIPOS.find(t => this.totais[t.tipo] > 0) || TIPOS[0]
        return this.$router.replace({ query: { ...this.$route.query, tipo: primeiro.tipo } })
      }
      this.carregar(false)
    },

    async contar () {
      const n = ++this.pedido
      this.totais = {}
      const r = await Promise.allSettled(TIPOS.map(t => procurar(this.q, { tipo: t.tipo, limit: POR_PAGINA })))
      if (n !== this.pedido) return
      TIPOS.forEach((t, i) => { this.totais[t.tipo] = r[i].status === 'fulfilled' ? r[i].value.total : null })
    },

    async carregar (mais) {
      const n = ++this.pedido
      this.aCarregar = true
      this.erro = ''
      try {
        const filtros = { ...this.filtros }
        delete filtros.ordem
        if (this.tipo !== 'produto') { delete filtros.preco_min; delete filtros.preco_max }
        if (this.tipo !== 'loja') delete filtros.localizacao
        const d = await procurar(this.q, { tipo: this.tipo, offset: mais ? this.resultados.length : 0, limit: POR_PAGINA,
                                           filtros, ordem: this.tipo === 'produto' ? this.filtros.ordem : '' })
        if (n !== this.pedido) return
        this.resultados = mais ? [...this.resultados, ...d.resultados] : d.resultados
        this.seguinte = d.seguinte
        this.sugestao = d.sugestao || null
        if (!mais) this.totais = { ...this.totais, [this.tipo]: d.total }
      } catch (e) {
        if (n === this.pedido) this.erro = e.response?.status === 429 ? e.response.data.detail : 'Não foi possível pesquisar. Tenta outra vez.'
      } finally {
        if (n === this.pedido) this.aCarregar = false
      }
    },

    mudar (extra) {
      this.$router.replace({ query: { ...this.$route.query, ...extra } })
    },

    aplicar () {
      const query = { q: this.q, tipo: this.tipo }
      for (const f of FILTROS) if (this.filtros[f] !== '' && this.filtros[f] != null) query[f] = String(this.filtros[f])
      this.$router.replace({ query })
    },

    limparFiltros () {
      this.$router.replace({ query: { q: this.q, tipo: this.tipo } })
    },

    sair () {
      terminarSessao('access_token', 'refresh_token')
      for (const k of ['access_token', 'refresh_token', 'user']) localStorage.removeItem(k)
      this.user = {}
    },
  },
}
</script>
