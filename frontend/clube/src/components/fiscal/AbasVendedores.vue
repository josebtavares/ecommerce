<!-- AbasVendedores.vue — fila de abas das lojas (e POS sem loja), como em Admin → Comissões.
     Carrega do servidor 40 de cada vez (pendentes primeiro) e mais quando chegas ao fim (scroll infinito na horizontal),
     procura no servidor (nome, NIF, código do POS) e tem botões ‹ › para deslizar.
     url: endpoint que devolve {count, results: [{tipo, id, nome, codigo_pos?, contador, alerta?}], fixo}.
     ativo: 'loja-12' | 'pos-3' | null — se ainda não foi carregada, vem em 'fixo' e aparece logo a seguir a "Todas".
     Emite 'selecionar' com o item (ou null = "Todas"). recarregar() atualiza os contadores. -->
<template>
  <div class="flex items-center gap-2" data-teste="abas-vendedores">
    <input v-model.trim="procura" type="search" :placeholder="placeholder" :aria-label="placeholder" data-teste="abas-procurar"
      class="w-36 sm:w-44 flex-shrink-0 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
    <button type="button" @click="deslizar(-1)" :disabled="!podeEsq" aria-label="Abas anteriores" data-teste="abas-esq"
      class="flex-shrink-0 w-7 h-7 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-default">
      <font-awesome-icon :icon="['fas', 'chevron-left']" class="text-[10px]" />
    </button>
    <div ref="fila" @scroll.passive="aoDeslizar(true)" class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide min-w-0 flex-1" role="tablist">
      <button type="button" role="tab" :aria-selected="!ativo ? 'true' : 'false'" @click="$emit('selecionar', null)" data-teste="aba-todas"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 !ativo ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        Todas<span v-if="count" class="ml-1 opacity-60">{{ count }}</span>
      </button>
      <button v-for="v in visiveis" :key="v.tipo + v.id" type="button" role="tab" :aria-selected="ativo === `${v.tipo}-${v.id}` ? 'true' : 'false'"
        @click="$emit('selecionar', v)" :data-teste="`aba-${v.tipo}-${v.id}`"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 ativo === `${v.tipo}-${v.id}` ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        <span v-if="v.tipo === 'pos'" class="mr-1 text-[9px] opacity-70">POS</span>{{ v.nome }}
        <span v-if="v.contador" :title="v.alerta ? tituloAlerta : titulo"
          :class="['ml-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold', v.alerta ? 'bg-red-500/25 text-red-300' : 'bg-yellow-500/20 text-yellow-400']">{{ v.contador }}</span>
      </button>
      <span v-if="aCarregar" class="px-2 py-1.5 text-xs text-zinc-500 whitespace-nowrap" data-teste="abas-a-carregar">
        <font-awesome-icon :icon="['fas', 'spinner']" spin />
      </span>
      <span v-else-if="procura && !itens.length" class="px-2 py-1.5 text-xs text-zinc-500 whitespace-nowrap">Nenhuma loja com "{{ procura }}"</span>
    </div>
    <button type="button" @click="deslizar(1)" :disabled="!podeDir" aria-label="Mais abas" data-teste="abas-dir"
      class="flex-shrink-0 w-7 h-7 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-default">
      <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-[10px]" />
    </button>
  </div>
</template>

<script>
import api from '@/services/api'

const LIMITE = 40

export default {
  name: 'AbasVendedores',
  props: {
    url:    { type: String, required: true },
    ativo:  { type: String, default: null },
    titulo: { type: String, default: '' },          // tooltip do contador
    tituloAlerta: { type: String, default: '' },    // … quando o item tem alerta (contador a vermelho, ex.: em atraso)
    placeholder: { type: String, default: 'Procurar loja…' },
  },
  emits: ['selecionar'],
  data () {
    return { procura: '', itens: [], fixo: null, count: 0, aCarregar: false, parado: false, pedido: 0, podeEsq: false, podeDir: false }
  },
  computed: {
    // a aba ativa ainda não carregada aparece logo a seguir a "Todas"
    visiveis () {
      const f = this.fixo
      if (!f || this.itens.some(v => v.tipo === f.tipo && v.id === f.id)) return this.itens
      return [f, ...this.itens]
    },
    haMais () { return this.itens.length < this.count },
  },
  watch: {
    procura () {
      clearTimeout(this.espera)
      this.espera = setTimeout(() => this.carregar(), 300)
    },
    ativo (a) {
      if (a && !this.visiveis.some(v => `${v.tipo}-${v.id}` === a)) this.carregar(Math.max(LIMITE, this.itens.length))
    },
  },
  mounted () {
    this.carregar()
    window.addEventListener('resize', this.aoDeslizar)
  },
  beforeUnmount () {
    clearTimeout(this.espera)
    window.removeEventListener('resize', this.aoDeslizar)
  },
  methods: {
    // do início (procura nova / recarregar); limite > 40 mantém as abas já carregadas
    async carregar (limite = LIMITE) {
      const n = ++this.pedido
      this.aCarregar = true
      this.parado = false
      try {
        const params = { limit: Math.min(limite, 100), offset: 0 }
        if (this.procura) params.q = this.procura
        if (this.ativo) params.fixar = this.ativo
        const { data } = await api.get(this.url, { params })
        if (n !== this.pedido) return
        this.itens = data.results
        this.count = data.count
        this.fixo = data.fixo
        if (limite === LIMITE) this.$refs.fila.scrollLeft = 0
      } catch { /* as abas são um atalho: sem elas fica a visão geral */ } finally {
        if (n === this.pedido) this.aCarregar = false
        this.$nextTick(this.aoDeslizar)
      }
    },
    async mais () {
      if (this.aCarregar || !this.haMais) return
      const n = ++this.pedido
      this.aCarregar = true
      try {
        const params = { limit: LIMITE, offset: this.itens.length }
        if (this.procura) params.q = this.procura
        const { data } = await api.get(this.url, { params })
        if (n !== this.pedido) return
        const tem = new Set(this.itens.map(v => v.tipo + v.id))
        this.itens = [...this.itens, ...data.results.filter(v => !tem.has(v.tipo + v.id))]
        this.count = data.count
      } catch { this.parado = true /* tenta outra vez no próximo scroll */ } finally {
        if (n === this.pedido) this.aCarregar = false
        this.$nextTick(this.aoDeslizar)
      }
    },
    recarregar () { return this.carregar(Math.max(LIMITE, this.itens.length)) },
    deslizar (dir) {
      const f = this.$refs.fila
      f.scrollBy({ left: dir * Math.max(200, f.clientWidth * 0.8), behavior: 'smooth' })
    },
    // setas + scroll infinito: perto do fim (ou se as abas já cabem todas) carrega as seguintes
    aoDeslizar (doUtilizador = false) {
      const f = this.$refs.fila
      if (!f) return
      if (doUtilizador === true) this.parado = false
      this.podeEsq = f.scrollLeft > 2
      this.podeDir = f.scrollLeft + f.clientWidth < f.scrollWidth - 2 || this.haMais
      if (this.haMais && !this.aCarregar && !this.parado && f.scrollLeft + f.clientWidth >= f.scrollWidth - 200) this.mais()
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>
