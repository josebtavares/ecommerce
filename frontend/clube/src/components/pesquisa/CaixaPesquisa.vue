<!-- CaixaPesquisa.vue — campo de pesquisa com resultados enquanto se escreve (services/pesquisa.js).
     grande: a barra da home (lista por baixo, flutuante). painel: dentro do PesquisaGlobal (lista no fluxo, ocupa o painel).
     Teclado: ↑ ↓ escolhem, Enter abre (ou "ver todos"), Esc fecha. -->
<template>
  <div class="relative w-full" ref="raiz" @keydown="tecla">
    <!-- no painel o campo fica preso em cima enquanto a lista rola -->
    <div class="flex items-center gap-2" :class="painel && ['sticky top-0 z-10 pb-2', isDark ? 'bg-zinc-950' : 'bg-white']">
    <form role="search" @submit.prevent="enter" class="relative flex-1 min-w-0">
      <font-awesome-icon :icon="['fas', 'magnifying-glass']"
        class="absolute top-1/2 -translate-y-1/2 pointer-events-none"
        :class="[grande ? 'left-5 text-base' : 'left-4 text-sm', isDark ? 'text-zinc-400' : 'text-zinc-500']" />
      <input ref="campo" v-model="q" type="search" enterkeyhint="search" autocomplete="off" spellcheck="false"
        :placeholder="placeholder" maxlength="80" data-teste="pesquisa-campo"
        role="combobox" aria-autocomplete="list" :aria-expanded="mostrarLista ? 'true' : 'false'"
        :aria-controls="idLista" :aria-activedescendant="ativo >= 0 ? `${idLista}-${ativo}` : undefined"
        aria-label="Pesquisar produtos, lojas e serviços"
        @input="agendar" @focus="aberto = true"
        class="w-full border outline-none transition appearance-none"
        :class="[grande ? 'h-14 md:h-16 pl-12 pr-12 rounded-2xl text-base md:text-lg shadow-2xl' : 'h-12 pl-11 pr-11 rounded-xl text-base',
                 isDark ? 'bg-zinc-900/95 border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:border-red-500'
                        : 'bg-white border-stone-300 text-zinc-900 placeholder-zinc-400 focus:border-red-500']" />
      <span v-if="aCarregar" class="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-red-500 border-t-transparent animate-spin"
            :class="grande ? 'right-12' : 'right-10'"></span>
      <button v-if="q" type="button" @click="limpar" aria-label="Limpar pesquisa"
        class="absolute top-1/2 -translate-y-1/2 w-8 h-8 rounded-full flex items-center justify-center transition"
        :class="[grande ? 'right-3' : 'right-2', isDark ? 'text-zinc-400 hover:bg-zinc-800' : 'text-zinc-500 hover:bg-stone-100']">
        <font-awesome-icon :icon="['fas', 'xmark']" />
      </button>
    </form>
    <slot name="lado" />
    </div>

    <div v-if="mostrarLista" :id="idLista" role="listbox" data-teste="pesquisa-lista"
         :class="[painel ? 'mt-1' : 'absolute z-40 left-0 right-0 mt-2 rounded-2xl border shadow-2xl max-h-[70vh] overflow-y-auto',
                  !painel && (isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-stone-200')]">

      <!-- ainda sem letras suficientes: pesquisas recentes -->
      <template v-if="curta">
        <div v-if="listaRecentes.length" class="py-2">
          <div class="flex items-center justify-between px-4 py-1.5">
            <span class="text-[11px] font-bold uppercase tracking-wider" :class="tSub">Pesquisas recentes</span>
            <button type="button" @mousedown.prevent="apagarRecentes" class="text-[11px] font-semibold text-red-500 hover:text-red-400">Limpar</button>
          </div>
          <button v-for="(r, i) in listaRecentes" :key="r" type="button" :id="`${idLista}-${i}`" role="option"
            :aria-selected="ativo === i" @mousedown.prevent="usarRecente(r)"
            class="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm transition" :class="linha(i)">
            <font-awesome-icon :icon="['fas', 'clock-rotate-left']" class="w-4" :class="tSub" />
            <span class="truncate">{{ r }}</span>
          </button>
        </div>
        <p v-else class="px-4 py-4 text-sm" :class="tSub">Procura produtos, lojas, serviços ou categorias.</p>
      </template>

      <template v-else>
        <div v-if="!dados && aCarregar" class="p-3 space-y-2">
          <div v-for="n in 4" :key="n" class="h-12 rounded-xl animate-pulse" :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'"></div>
        </div>

        <template v-else-if="dados">
          <!-- categorias: atalhos para o catálogo filtrado -->
          <div v-if="dados.categorias.length" class="flex flex-wrap gap-2 px-4 pt-3 pb-1">
            <button v-for="c in dados.categorias" :key="c.valor" type="button" :id="`${idLista}-${indice('categoria', c)}`"
              role="option" :aria-selected="ativo === indice('categoria', c)" @mousedown.prevent="abrir('categoria', c)"
              class="px-3 py-1.5 rounded-full border text-xs font-semibold transition"
              :class="ativo === indice('categoria', c) ? 'border-red-500 text-red-500'
                      : isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-stone-300 text-zinc-700 hover:border-stone-400'">
              <font-awesome-icon :icon="['fas', 'tags']" class="mr-1 opacity-70" />{{ c.nome }}
            </button>
          </div>

          <div v-for="g in grupos" :key="g.tipo" class="py-1.5">
            <p class="px-4 pt-2 pb-1 text-[11px] font-bold uppercase tracking-wider" :class="tSub">{{ g.titulo }}</p>
            <button v-for="r in g.itens" :key="g.tipo + r.id" type="button" :id="`${idLista}-${indice(g.tipo, r)}`"
              role="option" :aria-selected="ativo === indice(g.tipo, r)" @mousedown.prevent="abrir(g.tipo, r)"
              :data-teste="`pesquisa-${g.tipo}-${r.id}`"
              class="w-full flex items-center gap-3 px-4 py-2 text-left transition" :class="linha(indice(g.tipo, r))">
              <div class="w-10 h-10 flex-shrink-0 overflow-hidden flex items-center justify-center"
                   :class="[g.tipo === 'loja' ? 'rounded-full' : 'rounded-lg', isDark ? 'bg-zinc-800' : 'bg-stone-100']">
                <img v-if="imagem(g.tipo, r)" v-img :src="$miniatura(imagem(g.tipo, r))" alt="" class="w-full h-full object-cover" />
                <font-awesome-icon v-else :icon="['fas', g.icone]" :class="tSub" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                  <span v-for="(p, k) in destacar(r.nome, q)" :key="k" :class="p.m && 'text-red-500 font-bold'">{{ p.t }}</span>
                </p>
                <p class="text-xs truncate" :class="tSub">{{ subtitulo(g.tipo, r) }}</p>
              </div>
              <span v-if="r.esgotado" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-500 flex-shrink-0">Esgotado</span>
              <span v-else-if="g.tipo === 'produto'" class="text-sm font-bold text-red-500 flex-shrink-0">{{ $dinheiro(r.preco) }}</span>
            </button>
          </div>

          <!-- nada encontrado -->
          <div v-if="semNada" class="px-4 py-5 text-sm" :class="tSub" data-teste="pesquisa-vazia">
            <p>Sem resultados para <b :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">«{{ q.trim() }}»</b>.</p>
            <p v-if="dados.sugestao" class="mt-2">
              Querias dizer
              <button type="button" @mousedown.prevent="usarRecente(dados.sugestao)" class="font-semibold text-red-500 hover:underline"
                data-teste="pesquisa-sugestao">{{ dados.sugestao }}</button>?
            </p>
            <p v-else class="mt-2">Experimenta outra palavra ou menos palavras.</p>
          </div>

          <button v-else type="button" :id="`${idLista}-${total}`" role="option" :aria-selected="ativo === total"
            @mousedown.prevent="verTudo" data-teste="pesquisa-ver-tudo"
            class="w-full px-4 py-3 border-t text-sm font-semibold text-left transition flex items-center gap-2"
            :class="[isDark ? 'border-zinc-800' : 'border-stone-200', linha(total), 'text-red-500']">
            Ver todos os resultados para «{{ q.trim() }}»
            <font-awesome-icon :icon="['fas', 'arrow-right']" class="ml-auto" />
          </button>
        </template>
      </template>
    </div>
  </div>
</template>

<script>
import { procurar, foiCancelado, recentes, guardarRecente, limparRecentes, destacar, destino, MIN_LETRAS } from '@/services/pesquisa'

let seq = 0

export default {
  name: 'CaixaPesquisa',

  props: {
    isDark:      { type: Boolean, default: true },
    grande:      { type: Boolean, default: false },
    painel:      { type: Boolean, default: false },   // lista sempre aberta, no fluxo (dentro do PesquisaGlobal)
    inicial:     { type: String,  default: '' },
    placeholder: { type: String,  default: 'Procurar produtos, lojas, serviços…' },
  },

  emits: ['fechar'],

  data () {
    return { q: this.inicial, dados: null, aCarregar: false, aberto: false, ativo: -1,
             listaRecentes: recentes(), idLista: `pesquisa-lista-${++seq}`, temporizador: null }
  },

  computed: {
    curta () { return this.q.trim().length < MIN_LETRAS },
    mostrarLista () { return this.painel || this.aberto },
    tSub () { return this.isDark ? 'text-zinc-500' : 'text-zinc-500' },
    grupos () {
      if (!this.dados) return []
      return [
        { tipo: 'produto', titulo: 'Produtos', icone: 'box', itens: this.dados.produtos },
        { tipo: 'loja', titulo: 'Lojas', icone: 'store', itens: this.dados.lojas },
        { tipo: 'servico', titulo: 'Serviços', icone: 'calendar-check', itens: this.dados.servicos },
      ].filter(g => g.itens.length)
    },
    // ordem do teclado: categorias, depois os grupos, por fim "ver todos"
    navegaveis () {
      if (this.curta) return this.listaRecentes.map(r => ({ tipo: 'recente', r }))
      if (!this.dados) return []
      return [...this.dados.categorias.map(r => ({ tipo: 'categoria', r })),
              ...this.grupos.flatMap(g => g.itens.map(r => ({ tipo: g.tipo, r })))]
    },
    total () { return this.navegaveis.length },
    semNada () { return this.dados && !this.total },
  },

  mounted () {
    document.addEventListener('pointerdown', this.foraDaCaixa)
    if (this.q.trim().length >= MIN_LETRAS) this.pesquisar()
  },

  beforeUnmount () {
    document.removeEventListener('pointerdown', this.foraDaCaixa)
    clearTimeout(this.temporizador)
  },

  methods: {
    destacar,

    focar () { this.$refs.campo?.focus() },

    foraDaCaixa (e) {
      if (!this.painel && this.aberto && !this.$refs.raiz?.contains(e.target)) this.aberto = false
    },

    agendar () {
      this.aberto = true
      this.ativo = -1
      clearTimeout(this.temporizador)
      if (this.curta) { this.dados = null; this.aCarregar = false; this.listaRecentes = recentes(); return }
      this.temporizador = setTimeout(this.pesquisar, 200)
    },

    async pesquisar () {
      const q = this.q
      this.aCarregar = true
      try {
        const dados = await procurar(q)
        if (q === this.q) this.dados = dados
      } catch (e) {
        if (!foiCancelado(e)) this.dados = { produtos: [], lojas: [], servicos: [], categorias: [], sugestao: null }
      } finally {
        if (q === this.q) this.aCarregar = false
      }
    },

    indice (tipo, r) { return this.navegaveis.findIndex(n => n.tipo === tipo && n.r === r) },

    linha (i) {
      return this.ativo === i
        ? (this.isDark ? 'bg-zinc-800' : 'bg-stone-100')
        : (this.isDark ? 'hover:bg-zinc-800/60 text-zinc-200' : 'hover:bg-stone-50 text-zinc-800')
    },

    imagem (tipo, r) { return tipo === 'loja' ? r.logo : r.imagem },

    subtitulo (tipo, r) {
      if (tipo === 'loja') return [r.categoria, r.localizacao].filter(Boolean).join(' · ')
      if (tipo === 'servico') return `${r.loja.nome} · ${r.preco_texto}`
      return r.loja.nome
    },

    tecla (e) {
      if (e.key === 'Escape') {
        if (this.q && !this.painel) { this.aberto = false } else { this.$emit('fechar') }
        return
      }
      if (!['ArrowDown', 'ArrowUp'].includes(e.key) || !this.mostrarLista) return
      e.preventDefault()
      const n = this.total + (this.curta || this.semNada ? 0 : 1)       // + "ver todos"
      if (!n) return
      this.ativo = e.key === 'ArrowDown' ? (this.ativo + 1) % n : (this.ativo <= 0 ? n - 1 : this.ativo - 1)
      this.$nextTick(() => document.getElementById(`${this.idLista}-${this.ativo}`)?.scrollIntoView({ block: 'nearest' }))
    },

    enter () {
      const n = this.navegaveis[this.ativo]
      if (n) return n.tipo === 'recente' ? this.usarRecente(n.r) : this.abrir(n.tipo, n.r)
      if (!this.curta) this.verTudo()
    },

    abrir (tipo, r) {
      guardarRecente(this.q)
      this.aberto = false
      this.$emit('fechar')
      this.$router.push(destino(tipo, r))
    },

    verTudo () {
      const q = this.q.trim()
      if (q.length < MIN_LETRAS) return
      guardarRecente(q)
      this.aberto = false
      this.$refs.campo?.blur()
      this.$emit('fechar')
      this.$router.push({ path: '/pesquisa', query: { q } })
    },

    usarRecente (r) {
      this.q = r
      this.agendar()
      this.focar()
    },

    limpar () {
      this.q = ''
      this.dados = null
      this.agendar()
      this.focar()
    },

    apagarRecentes () { limparRecentes(); this.listaRecentes = [] },
  },
}
</script>

<style scoped>
/* o "x" nativo do type=search duplicava o nosso botão de limpar */
input[type='search']::-webkit-search-cancel-button { -webkit-appearance: none; appearance: none; }
</style>
