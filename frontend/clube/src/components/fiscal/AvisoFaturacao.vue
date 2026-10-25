<!-- AvisoFaturacao.vue — aviso no backoffice (loja/POS) sobre faturação, conforme os dados fiscais.
     Por preencher → pede ao dono para os completar. Atividade/particular → lembrete, que se pode esconder. -->
<template>
  <div v-if="visivel" role="status" data-teste="aviso-faturacao" :data-tipo="tipo"
       :class="['px-4 py-3 rounded-xl border text-sm flex flex-col sm:flex-row sm:items-center gap-3', cores]">
    <div class="flex-1 min-w-0">
      <template v-if="tipo === 'incompleto'">
        <p class="font-semibold">Faltam os dados fiscais</p>
        <p class="text-xs opacity-80 mt-0.5">Indica o NIF e se vendes como particular ou com atividade declarada.</p>
      </template>
      <template v-else-if="tipo === 'atividade'">
        <p class="font-semibold">Faturação</p>
        <p class="text-xs opacity-80 mt-0.5">
          Tens de emitir uma fatura de cada venda no e-Fatura. O Bende ainda não emite faturas automaticamente:
          podes usar o <a :href="emissorUrl" target="_blank" rel="noopener" class="underline font-semibold">Emissor Público</a>
          gratuito da DNRE (efatura.cv) e registar o número da fatura em cada venda (encomenda, marcação ou conta do POS).
        </p>
      </template>
      <template v-else>
        <p class="font-semibold">Vendes como particular</p>
        <p class="text-xs opacity-80 mt-0.5">
          Se passares a vender com regularidade, deves declarar atividade nas Finanças e mudar para
          "Com atividade declarada" nas configurações.
        </p>
      </template>
    </div>
    <button v-if="tipo === 'incompleto' && podeEditar" type="button" @click="$emit('preencher')"
      class="px-4 py-2 rounded-lg text-xs font-bold transition flex-shrink-0" :class="botao">Preencher</button>
    <button v-else-if="tipo !== 'incompleto'" type="button" @click="esconder" aria-label="Esconder aviso"
      class="text-xs underline opacity-70 hover:opacity-100 flex-shrink-0">Ok, percebi</button>
  </div>
</template>

<script>
import { EMISSOR_PUBLICO_URL } from '@/utils/fiscal'

export default {
  name: 'AvisoFaturacao',
  props: {
    fiscal:     { type: Object, default: null },
    chave:      { type: String, required: true },   // ex.: 'loja-2' — guarda o "Ok, percebi" por loja/POS
    podeEditar: { type: Boolean, default: false },
    tema:       { type: String, default: 'escuro' },
  },
  emits: ['preencher'],
  data () {
    return { escondido: this.lerEscondido() }
  },
  computed: {
    tipo () {
      if (!this.fiscal?.completos) return 'incompleto'
      return this.fiscal.regime_fiscal === 'atividade' ? 'atividade' : 'particular'
    },
    // por preencher só interessa a quem pode preencher; os lembretes escondem-se por regime
    visivel () {
      if (!this.fiscal) return false
      if (this.tipo === 'incompleto') return this.podeEditar
      return this.escondido !== this.tipo
    },
    emissorUrl () { return EMISSOR_PUBLICO_URL },
    cores () {
      if (this.tema === 'claro') {
        return this.tipo === 'incompleto' ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-slate-50 border-slate-200 text-slate-700'
      }
      return this.tipo === 'incompleto' ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' : 'bg-zinc-800/60 border-zinc-700 text-zinc-300'
    },
    botao () {
      return this.tema === 'claro' ? 'bg-slate-950 text-white hover:bg-slate-800' : 'bg-zinc-100 hover:bg-white text-zinc-900'
    },
  },
  watch: {
    chave () { this.escondido = this.lerEscondido() },
  },
  methods: {
    lerEscondido () {
      try { return localStorage.getItem(`aviso_faturacao_${this.chave}`) || '' } catch { return '' }
    },
    esconder () {
      this.escondido = this.tipo
      try { localStorage.setItem(`aviso_faturacao_${this.chave}`, this.tipo) } catch { /* sem storage: volta a aparecer */ }
    },
  },
}
</script>
