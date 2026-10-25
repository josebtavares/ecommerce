<!-- MarcacoesFaturas.vue — as marcações que renderam dinheiro (ou tiveram fatura), para registar/ver as faturas
     quando o módulo Serviços está desligado: as vendas já feitas continuam a precisar de fatura.
     Não mostra nada se a loja nunca teve marcações faturáveis. -->
<template>
  <div v-if="lista.length || filtro !== 'todas'" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="marcacoes-faturas">
    <div class="px-4 py-3 border-b border-zinc-800 flex flex-wrap items-center gap-2">
      <div class="flex-1 min-w-0">
        <p class="text-sm font-bold text-zinc-100">Marcações anteriores e faturas</p>
        <p class="text-xs text-zinc-500">Os Serviços estão desligados, mas as faturas das marcações já feitas continuam a registar-se aqui.</p>
      </div>
      <div class="flex gap-1" role="group" aria-label="Filtrar marcações">
        <button v-for="f in FILTROS" :key="f.v" type="button" @click="mudar(f.v)" :aria-pressed="filtro === f.v ? 'true' : 'false'"
          :data-teste="`filtro-${f.v}`"
          :class="['h-8 px-3 rounded-lg text-xs font-bold', filtro === f.v ? 'bg-zinc-100 text-zinc-900' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700']">
          {{ f.t }}</button>
      </div>
    </div>
    <p v-if="!lista.length" class="px-4 py-6 text-sm text-zinc-500 text-center">Nenhuma marcação por faturar.</p>
    <button v-for="m in lista" :key="m.id" type="button" @click="aberta = m.id"
      class="w-full flex flex-wrap items-center gap-x-3 gap-y-0.5 px-4 py-2.5 border-b border-zinc-800/60 last:border-0 text-left hover:bg-zinc-800/50">
      <span class="text-xs tabular-nums text-zinc-400 w-28">{{ rotuloDia(diaDe(m.inicio)) }} {{ hora(m.inicio) }}</span>
      <span class="order-last w-full sm:order-none sm:w-auto sm:flex-1 min-w-0 text-sm text-zinc-200 truncate">{{ m.servico_nome }} · {{ m.cliente_nome || '—' }}</span>
      <span v-if="m.fatura" class="ml-auto sm:ml-0 text-xs text-green-400">Fatura {{ m.fatura.numero }}</span>
      <span v-else class="ml-auto sm:ml-0 text-xs text-amber-300">Por faturar</span>
    </button>
    <p v-if="erro" class="px-4 py-2 text-sm text-red-400" role="alert">{{ erro }}</p>

    <MarcacaoDetalhe v-if="aberta" :loja-id="lojaId" :marcacao-id="aberta" :pode-gerir="true"
      @fechar="aberta = null; carregar()" @alterada="carregar" />
  </div>
</template>

<script>
import api from '@/services/api'
import { diaDe, hora, rotuloDia } from '@/utils/servicos'
import MarcacaoDetalhe from './MarcacaoDetalhe.vue'

const FILTROS = [{ v: 'por_faturar', t: 'Por faturar' }, { v: 'todas', t: 'Todas' }]

export default {
  name: 'MarcacoesFaturas',
  components: { MarcacaoDetalhe },
  props: { lojaId: { type: [String, Number], required: true } },
  data () { return { lista: [], filtro: 'todas', aberta: null, erro: '', FILTROS } },
  mounted () { this.carregar() },
  methods: {
    diaDe, hora, rotuloDia,
    mudar (f) { this.filtro = f; this.carregar() },
    async carregar () {
      this.erro = ''
      try {
        const fatura = this.filtro === 'por_faturar' ? 'por_faturar' : 'arquivo'
        this.lista = (await api.get(`/app/loja/${this.lojaId}/servicos/marcacoes/`, { params: { fatura } })).data
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar as marcações.' }
    },
  },
}
</script>
