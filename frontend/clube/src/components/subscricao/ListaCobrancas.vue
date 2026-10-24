<!-- ListaCobrancas.vue — mensalidades (FaturaSubscricao) paginadas no servidor, com procura (S-12, descrição, nº da fatura…),
     estado (por pagar, em atraso, pagas, anuladas) e período. Cada linha é desenhada pelo slot default { f }.
     url: /app/admin/faturas/ | /app/loja/<id>/subscricao/faturas/ | /api/pos/<id>/subscricao/faturas/
     params: filtros fixos (ex.: { loja: 12 }). versao: muda → recarrega (depois de uma ação). claro: páginas de fundo branco (POS).
     recarregar() mantém a página. -->
<template>
  <div data-teste="lista-cobrancas">
    <div v-if="mostrarFiltros" :class="['flex flex-wrap items-center gap-2', claro ? 'px-5 sm:px-6 pb-3' : (embutida ? 'px-4 sm:px-6 pb-3' : 'pb-3')]">
      <input v-model.trim="q" type="search" @keyup.enter="ir(0)" @search="ir(0)" placeholder="Procurar S-12, descrição, nº da fatura…"
        aria-label="Procurar mensalidade" data-teste="cobrancas-q" :class="[campo, 'w-full sm:w-64']" />
      <select v-model="estado" @change="ir(0)" aria-label="Estado" data-teste="cobrancas-estado" :class="campo">
        <option value="">Todas</option>
        <option value="pendente">Por pagar</option>
        <option value="atraso">Em atraso</option>
        <option value="paga">Pagas</option>
        <option value="anulada">Anuladas</option>
      </select>
      <label :class="['flex items-center gap-1 text-xs', claro ? 'text-slate-500 font-semibold' : 'text-zinc-500']">
        De <input v-model="de" type="date" @change="ir(0)" aria-label="Período de" data-teste="cobrancas-de" :class="[campo, claro ? '' : '[color-scheme:dark]']" />
      </label>
      <label :class="['flex items-center gap-1 text-xs', claro ? 'text-slate-500 font-semibold' : 'text-zinc-500']">
        a <input v-model="ate" type="date" @change="ir(0)" aria-label="Período até" data-teste="cobrancas-ate" :class="[campo, claro ? '' : '[color-scheme:dark]']" />
      </label>
      <button v-if="filtrado" type="button" @click="limpar" data-teste="cobrancas-limpar"
        :class="['text-xs', claro ? 'text-slate-500 hover:text-slate-800 font-bold' : 'text-zinc-500 hover:text-zinc-200']">Limpar</button>
      <span :class="['ml-auto text-xs', claro ? 'text-slate-400 font-semibold' : 'text-zinc-500']" data-teste="cobrancas-count">{{ lista.count }} {{ lista.count === 1 ? 'mensalidade' : 'mensalidades' }}</span>
    </div>

    <p v-if="erro" :class="['text-sm', claro ? 'px-5 sm:px-6 pb-4 text-red-600 font-bold' : 'text-red-400 pb-3', embutida ? 'px-4 sm:px-6' : '']" role="alert">{{ erro }}</p>
    <div v-if="aCarregar && !lista.results.length" :class="['space-y-2', claro ? 'px-5 sm:px-6 pb-5' : (embutida ? 'px-4 sm:px-6 pb-4' : '')]">
      <div v-for="n in 3" :key="n" :class="['h-14 rounded-2xl animate-pulse', claro ? 'bg-slate-100' : 'bg-zinc-800/60']"></div>
    </div>
    <div v-else-if="!lista.results.length"
      :class="['text-sm', claro ? 'px-5 sm:px-6 pb-6 text-slate-500 font-semibold' : (embutida ? 'px-4 sm:px-6 pb-4 text-zinc-500' : 'text-center py-10 text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800')]">
      {{ filtrado ? 'Nenhuma mensalidade com estes filtros.' : vazio }}
    </div>
    <div v-else :class="['transition-opacity', aCarregar ? 'opacity-50' : '', embutida || claro ? (claro ? 'divide-y divide-slate-100' : 'divide-y divide-zinc-800') : 'space-y-2']">
      <template v-for="f in lista.results" :key="f.id"><slot :f="f" /></template>
    </div>
    <div :class="claro ? 'px-5 sm:px-6 py-3' : (embutida ? 'px-4 sm:px-6 py-3' : 'pt-3')">
      <PaginacaoLista :count="lista.count" :limit="limite" :offset="offset" :claro="claro" @ir="ir" />
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'

export default {
  name: 'ListaCobrancas',
  components: { PaginacaoLista },
  props: {
    url:     { type: String, required: true },
    params:  { type: Object, default: () => ({}) },
    limite:  { type: Number, default: 10 },
    estadoInicial: { type: String, default: '' },
    versao:  { type: Number, default: 0 },
    vazio:   { type: String, default: 'Ainda não há mensalidades.' },
    claro:   { type: Boolean, default: false },
    embutida: { type: Boolean, default: false },    // dentro de um cartão (linhas separadas por traços, sem margens próprias)
  },
  emits: ['carregada'],
  data () {
    return { lista: { count: 0, results: [] }, offset: 0, q: '', estado: this.estadoInicial, de: '', ate: '', aCarregar: false, erro: '', pedido: 0 }
  },
  computed: {
    chaveParams () { return JSON.stringify(this.params) },
    filtrado () { return !!(this.q || this.estado || this.de || this.ate) },
    // dentro de um cartão, com tudo numa página, os filtros só ocupam espaço
    mostrarFiltros () { return !this.embutida || this.filtrado || this.lista.count > this.limite },
    campo () {
      return this.claro
        ? 'px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 font-semibold focus:outline-none focus:border-slate-400'
        : 'px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-red-500'
    },
  },
  watch: {
    versao () { this.recarregar() },
    url () { this.ir(0) },
    chaveParams () { this.ir(0) },      // só quando os filtros fixos mudam mesmo (o pai pode passar um objeto novo a cada render)
  },
  created () { this.ir(0) },
  methods: {
    async ir (offset) {
      const n = ++this.pedido
      this.offset = offset
      this.aCarregar = true
      this.erro = ''
      try {
        const params = { ...this.params, limit: this.limite, offset }
        if (this.q) params.q = this.q
        if (this.estado) params.estado = this.estado
        if (this.de) params.de = this.de
        if (this.ate) params.ate = this.ate
        const { data } = await api.get(this.url, { params })
        if (n !== this.pedido) return
        // depois de uma ação a última página pode ficar vazia: volta uma
        if (!data.results.length && offset > 0 && data.count) return this.ir(Math.max(0, offset - this.limite))
        this.lista = data
        this.$emit('carregada', data)
      } catch (e) {
        if (n === this.pedido) this.erro = e.response?.data?.detail || 'Não foi possível carregar as mensalidades.'
      } finally {
        if (n === this.pedido) this.aCarregar = false
      }
    },
    recarregar () { return this.ir(this.offset) },
    limpar () {
      this.q = ''; this.estado = ''; this.de = ''; this.ate = ''
      this.ir(0)
    },
  },
}
</script>
