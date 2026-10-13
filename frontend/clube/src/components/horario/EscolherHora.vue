<template>
  <!-- Checkout: "o mais cedo possível" ou dia + hora (GET /app/loja/<id>/agendamento/vagas/).
       v-model: null = o mais cedo possível · '' = a escolher · '2026-10-14T13:30' = escolhida -->
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
    <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
      {{ tipoEntrega === 'entrega' ? 'Quando queres receber?' : 'Quando vais levantar?' }}
    </h2>

    <div class="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Quando">
      <button type="button" role="radio" :aria-checked="modelValue === null ? 'true' : 'false'" @click="escolherModo(null)"
        :class="['p-3 rounded-xl border-2 text-left transition', modelValue === null ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
        <p class="text-sm font-semibold text-zinc-200">O mais cedo possível</p>
        <p class="text-xs text-zinc-500 mt-0.5">{{ textoAsap }}</p>
      </button>
      <button type="button" role="radio" :aria-checked="modelValue !== null ? 'true' : 'false'" @click="escolherModo('')"
        :class="['p-3 rounded-xl border-2 text-left transition', modelValue !== null ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
        <p class="text-sm font-semibold text-zinc-200">Escolher dia e hora</p>
        <p class="text-xs text-zinc-500 mt-0.5">{{ escolhidaTexto || 'Agenda para mais tarde' }}</p>
      </button>
    </div>

    <div v-if="modelValue !== null" class="mt-4">
      <div v-if="carregando" class="h-20 rounded-xl bg-zinc-800/60 animate-pulse"></div>
      <p v-else-if="erro" class="text-sm text-red-400">{{ erro }}</p>
      <p v-else-if="!dias.length" class="text-sm text-zinc-400 bg-zinc-800/50 rounded-xl px-4 py-3">
        Não há horas disponíveis nos próximos dias.
      </p>
      <template v-else>
        <!-- dias -->
        <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1" role="tablist" aria-label="Dia">
          <button v-for="d in dias" :key="d.data" type="button" role="tab" :aria-selected="d.data === dia ? 'true' : 'false'"
            @click="dia = d.data"
            :class="['flex-shrink-0 px-3 py-2 rounded-xl border text-left transition min-w-[84px]',
                     d.data === dia ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
            <span class="block text-xs font-bold text-zinc-200">{{ d.rotulo }}</span>
            <span class="block text-[11px] text-zinc-500">{{ d.horas.length }} hora{{ d.horas.length === 1 ? '' : 's' }}</span>
          </button>
        </div>
        <!-- horas -->
        <div class="grid grid-cols-4 sm:grid-cols-6 gap-2 mt-3" role="radiogroup" aria-label="Hora">
          <button v-for="h in diaAtual?.horas || []" :key="h" type="button" role="radio"
            :aria-checked="modelValue === `${dia}T${h}` ? 'true' : 'false'" @click="$emit('update:modelValue', `${dia}T${h}`)"
            :class="['py-2 rounded-lg text-sm font-semibold border transition',
                     modelValue === `${dia}T${h}` ? 'border-red-500 bg-red-600 text-white' : 'border-zinc-700 text-zinc-300 hover:border-zinc-500']">
            {{ h }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'EscolherHora',
  props: {
    lojaId:      { type: [String, Number], required: true },
    modelValue:  { type: String, default: null },
    tipoEntrega: { type: String, default: 'levantamento' },
    textoAsap:   { type: String, default: 'Assim que a loja preparar' },
  },
  emits: ['update:modelValue'],

  data () {
    return { dias: [], dia: null, carregando: false, erro: '', carregado: false }
  },

  computed: {
    diaAtual () { return this.dias.find(d => d.data === this.dia) },
    escolhidaTexto () {
      if (!this.modelValue) return ''
      const [data, hora] = this.modelValue.split('T')
      const d = this.dias.find(x => x.data === data)
      return d ? `${d.rotulo} às ${hora}` : ''
    },
  },

  methods: {
    escolherModo (v) {
      if (v === null) { this.$emit('update:modelValue', null); return }
      if (this.modelValue === null) this.$emit('update:modelValue', '')
      if (!this.carregado) this.carregar()
    },
    // também chamado pelo checkout quando a hora escolhida deixou de estar livre
    async carregar () {
      this.carregando = true
      this.erro = ''
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/agendamento/vagas/`)
        this.dias = data.dias || []
        this.carregado = true
        if (!this.dias.find(d => d.data === this.dia)) this.dia = this.dias[0]?.data || null
        // a hora escolhida já não existe → volta a "a escolher"
        if (this.modelValue) {
          const [d, h] = this.modelValue.split('T')
          if (!this.dias.find(x => x.data === d)?.horas.includes(h)) this.$emit('update:modelValue', '')
        }
      } catch (e) {
        this.erro = 'Não foi possível carregar as horas disponíveis.'
      } finally {
        this.carregando = false
      }
    },
  },
}
</script>
