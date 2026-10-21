<template>
  <!--
    Serviços na página da loja (todos os templates): sliders por categoria, catálogo com pesquisa e o modal
    para marcar. Só aparece se a loja aceitar marcações. ?servico=<id> abre logo esse serviço (cartões da
    home, voltar do login).
  -->
  <section v-if="dados && dados.disponivel && dados.servicos.length" :id="ancora" data-teste="seccao-servicos">
   <div :class="contido ? 'max-w-6xl mx-auto px-5 sm:px-8' : ''">
    <div class="flex flex-wrap items-end gap-3 mb-5">
      <div class="flex-1 min-w-[200px]">
        <h2 class="text-2xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo }}</h2>
        <p class="text-sm mt-0.5" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Escolhe o serviço e marca a tua hora.</p>
      </div>
      <div v-if="dados.servicos.length > 6" class="relative w-full sm:w-64">
        <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'" />
        <input v-model="q" placeholder="Procurar serviço…" aria-label="Procurar serviço"
          class="w-full pl-8 pr-3 py-2 rounded-xl text-sm border focus:outline-none"
          :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100 placeholder-zinc-500' : 'bg-white border-gray-300 text-zinc-900 placeholder-zinc-400'" />
      </div>
    </div>

    <!-- catálogo: categorias e pesquisa -->
    <div v-if="categorias.length > 1" class="flex gap-2 overflow-x-auto pb-3 mb-2" style="scrollbar-width: none" role="tablist" aria-label="Categorias de serviços">
      <button v-for="c in ['', ...categorias]" :key="c || 'todas'" type="button" role="tab" :aria-selected="categoria === c" @click="categoria = c"
        class="px-4 py-1.5 rounded-full text-sm font-semibold whitespace-nowrap flex-shrink-0 border"
        :class="categoria === c ? 'text-white' : (isDark ? 'border-zinc-700 text-zinc-300' : 'border-gray-300 text-zinc-600')"
        :style="categoria === c ? { backgroundColor: cor, borderColor: cor } : {}">{{ c || 'Todos' }}</button>
    </div>

    <template v-if="!q && !categoria && categorias.length > 1">
      <ServicoSlider v-for="c in categorias" :key="c" :titulo="c" :servicos="porCategoria[c]" :isDark="isDark" :cor="cor" @abrir="abrir" />
      <ServicoSlider v-if="porCategoria['']?.length" titulo="Outros" :servicos="porCategoria['']" :isDark="isDark" :cor="cor" @abrir="abrir" />
    </template>
    <ServicoSlider v-else-if="!q && !categoria && filtrados.length <= 8" :titulo="`${filtrados.length} serviço${filtrados.length === 1 ? '' : 's'}`"
      :servicos="filtrados" :isDark="isDark" :cor="cor" @abrir="abrir" />
    <div v-else data-teste="catalogo-servicos-loja">
      <p v-if="!filtrados.length" class="text-sm py-6 text-center" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Nenhum serviço encontrado.</p>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        <ServicoCartao v-for="s in filtrados" :key="s.id" :s="s" :isDark="isDark" :cor="cor" class="w-full" @abrir="abrir" />
      </div>
    </div>

   </div>
    <ServicoModal v-if="aberto" :loja-id="lojaId" :servico="aberto" :regras="dados.regras" :profissionais="dados.profissionais"
      :isDark="isDark" :cor="cor" :inicial="inicial" @fechar="fechar" />
  </section>
</template>

<script>
import api from '@/services/api'
import ServicoCartao from './ServicoCartao.vue'
import ServicoModal, { GUARDADO } from './ServicoModal.vue'
import ServicoSlider from './ServicoSlider.vue'

export default {
  name: 'SeccaoServicos',
  components: { ServicoCartao, ServicoModal, ServicoSlider },
  props: {
    lojaId: { type: [String, Number], required: true },
    isDark: { type: Boolean, default: true },
    cor: { type: String, default: '#dc2626' },
    titulo: { type: String, default: 'Serviços' },
    ancora: { type: String, default: 'servicos' },
    // o template não dá largura nem margens às secções (os estilos dele não chegam cá dentro): a secção põe as suas
    contido: { type: Boolean, default: false },
  },
  emits: ['carregado'],
  data () { return { dados: null, q: '', categoria: '', aberto: null, inicial: null } },
  computed: {
    categorias () { return [...new Set((this.dados?.servicos || []).map(s => s.categoria).filter(Boolean))] },
    porCategoria () {
      const out = {}
      ;(this.dados?.servicos || []).forEach(s => { (out[s.categoria || ''] = out[s.categoria || ''] || []).push(s) })
      return out
    },
    filtrados () {
      const q = this.q.trim().toLowerCase()
      return (this.dados?.servicos || []).filter(s => (!this.categoria || s.categoria === this.categoria)
        && (!q || s.nome.toLowerCase().includes(q) || (s.descricao || '').toLowerCase().includes(q) || (s.categoria || '').toLowerCase().includes(q)))
    },
  },
  watch: { lojaId () { this.carregar() } },
  created () { this.carregar() },
  methods: {
    async carregar () {
      try {
        this.dados = (await api.get(`/app/lojas/${this.lojaId}/servicos/publico/`)).data
      } catch { this.dados = { disponivel: false } }
      this.$emit('carregado', !!(this.dados.disponivel && this.dados.servicos?.length))
      this.abrirPedido()
    },
    abrir (s) { this.inicial = null; this.aberto = s },
    fechar () {
      this.aberto = null
      if (this.$route.query.servico) this.$router.replace({ query: { ...this.$route.query, servico: undefined } })
    },
    // ?servico=<id>: vem de um cartão da home ou do login (a escolha guardada volta)
    abrirPedido () {
      const sid = Number(this.$route.query.servico)
      if (!sid || !this.dados?.disponivel) return
      const s = this.dados.servicos.find(x => x.id === sid)
      if (!s) return
      let g = null
      try { g = JSON.parse(sessionStorage.getItem(GUARDADO) || 'null') } catch { g = null }
      sessionStorage.removeItem(GUARDADO)
      this.inicial = g && String(g.loja) === String(this.lojaId) && g.servico === sid ? g : null
      this.aberto = s
      this.$nextTick(() => this.$el?.scrollIntoView?.({ block: 'start' }))
    },
  },
}
</script>
