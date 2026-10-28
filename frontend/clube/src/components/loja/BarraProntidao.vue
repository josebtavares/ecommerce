<!-- BarraProntidao.vue — backoffice: quanto falta para a loja poder ser publicada (app/utils/prontidao.py).
     Vermelha enquanto falta algo, verde a 100%. Cada requisito em falta leva à secção onde se resolve.
     Lojas activas e completas não vêem nada; activas incompletas vêem-na fechada (só avisos). -->
<template>
  <div v-if="dados && (!dados.completa || estado === 'pendente')" data-teste="barra-prontidao"
       :data-completa="dados.completa ? '1' : '0'"
       class="rounded-xl border bg-zinc-900 text-sm"
       :class="dados.completa ? 'border-green-500/40' : 'border-red-500/30'">
    <button type="button" @click="alternar" :aria-expanded="aberta"
      class="w-full flex items-center gap-3 px-4 py-3 text-left">
      <font-awesome-icon :icon="['fas', dados.completa ? 'circle-check' : 'list-check']"
        class="w-4 h-4 flex-shrink-0" :class="dados.completa ? 'text-green-400' : 'text-red-400'" />
      <div class="flex-1 min-w-0">
        <div class="flex items-baseline justify-between gap-3">
          <p class="font-semibold text-zinc-100 truncate">{{ titulo }}</p>
          <span class="text-xs font-bold tabular-nums flex-shrink-0" data-teste="prontidao-percentagem"
                :class="dados.completa ? 'text-green-400' : 'text-red-400'">{{ dados.percentagem }}%</span>
        </div>
        <div class="mt-2 h-2 rounded-full bg-zinc-800 overflow-hidden" role="progressbar"
             :aria-valuenow="dados.percentagem" aria-valuemin="0" aria-valuemax="100" :aria-label="titulo">
          <div class="h-full rounded-full transition-all duration-500"
               :class="dados.completa ? 'bg-green-500' : 'bg-red-500'" :style="{ width: dados.percentagem + '%' }"></div>
        </div>
      </div>
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 flex-shrink-0 text-zinc-500 transition-transform"
           :class="aberta && 'rotate-180'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <div v-if="aberta" class="px-4 pb-4 border-t border-zinc-800 pt-3 space-y-3">
      <p class="text-xs text-zinc-400">{{ explicacao }}</p>
      <ul class="space-y-1.5">
        <li v-for="r in dados.requisitos" :key="r.chave" :data-teste="'requisito-' + r.chave" :data-ok="r.ok ? '1' : '0'"
            class="flex items-start gap-2.5">
          <font-awesome-icon :icon="['fas', r.ok ? 'circle-check' : 'circle-xmark']"
            class="w-4 h-4 mt-0.5 flex-shrink-0" :class="r.ok ? 'text-green-400' : 'text-red-400'" />
          <div class="flex-1 min-w-0">
            <p :class="r.ok ? 'text-zinc-500 line-through decoration-zinc-600' : 'text-zinc-100 font-medium'">{{ r.titulo }}</p>
            <p v-if="!r.ok" class="text-xs text-zinc-500 mt-0.5">{{ r.ajuda }}</p>
          </div>
          <button v-if="!r.ok" type="button" @click="$emit('ir', r.seccao)"
            class="px-3 py-1 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition flex-shrink-0">
            Resolver
          </button>
        </li>
      </ul>
      <div v-if="dados.produtos_incompletos?.length" class="rounded-lg bg-zinc-800/60 px-3 py-2.5" data-teste="produtos-incompletos">
        <p class="text-xs font-semibold text-amber-300">
          {{ dados.produtos_incompletos_total }} produto{{ dados.produtos_incompletos_total === 1 ? '' : 's' }} sem tudo preenchido
          <span class="font-normal text-zinc-400">— aparecem na loja, mas ficam melhor completos.</span>
        </p>
        <ul class="mt-1.5 space-y-0.5">
          <li v-for="p in dados.produtos_incompletos.slice(0, 5)" :key="p.id" class="text-xs text-zinc-400 truncate">
            {{ p.nome }}: <span class="text-zinc-500">falta {{ p.faltas.join(', ') }}</span>
          </li>
        </ul>
        <button type="button" @click="$emit('ir', 'produtos')" class="mt-1.5 text-xs font-semibold text-red-400 hover:text-red-300">
          Ver produtos →
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'BarraProntidao',

  props: {
    lojaId: { type: [String, Number], required: true },
    estado: { type: String, default: '' },
    // muda quando o backoffice muda de secção ou guarda a loja → volta a calcular
    recarregar: { type: [String, Number], default: '' },
  },

  emits: ['ir'],

  data () {
    return { dados: null, abertaManual: null }
  },

  computed: {
    chave () { return `prontidao-aberta-${this.lojaId}` },
    // pendente e incompleta: aberta para se ver o que falta; senão fechada (a pessoa pode abrir)
    aberta () {
      if (this.abertaManual !== null) return this.abertaManual
      return this.estado === 'pendente' && !this.dados?.completa
    },
    titulo () {
      if (this.dados.completa) {
        return this.estado === 'pendente' ? 'Loja pronta — à espera de aprovação' : 'Loja completa'
      }
      const faltam = this.dados.requisitos.filter(r => !r.ok).length
      return `Loja por completar — falta${faltam === 1 ? '' : 'm'} ${faltam} requisito${faltam === 1 ? '' : 's'}`
    },
    explicacao () {
      if (this.dados.completa) return 'Cumpre todos os requisitos. A plataforma vai rever a loja e publicá-la.'
      if (this.estado === 'pendente') {
        return 'Para a loja ser publicada no site tem de cumprir todos estes requisitos. Quando chegar aos 100%, a plataforma revê-a e publica-a.'
      }
      return 'Os clientes confiam mais numa loja que diz quem vende, como contactar e as regras de entregas e devoluções.'
    },
  },

  watch: {
    lojaId () { this.abertaManual = null; this.carregar() },
    recarregar () { this.carregar() },
  },

  created () {
    try {
      const v = localStorage.getItem(this.chave)
      if (v !== null) this.abertaManual = v === '1'
    } catch { /* sem armazenamento: fica o padrão */ }
    this.carregar()
  },

  methods: {
    async carregar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/prontidao/`)
        this.dados = data
      } catch { /* a barra não é essencial */ }
    },
    alternar () {
      this.abertaManual = !this.aberta
      try { localStorage.setItem(this.chave, this.abertaManual ? '1' : '0') } catch { /* idem */ }
    },
  },
}
</script>
