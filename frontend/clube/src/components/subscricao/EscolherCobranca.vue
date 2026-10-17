<template>
  <!-- Criar loja: comissão por venda ou subscrição (GET /app/planos/).
       v-model = { modelo: 'comissao' | 'subscricao', plano_id: null | id } -->
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-4">
    <div>
      <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Como pagas à plataforma</h2>
      <p class="text-xs text-zinc-500 mt-1">Podes mudar mais tarde.</p>
    </div>

    <div class="grid sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Modelo de cobrança">
      <button type="button" role="radio" :aria-checked="modelValue.modelo === 'comissao' ? 'true' : 'false'"
        @click="escolher('comissao')"
        :class="['p-4 rounded-xl border-2 text-left transition', modelValue.modelo === 'comissao' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
        <p class="text-sm font-bold text-zinc-100">Comissão por venda</p>
        <p class="text-2xl font-black text-zinc-100 mt-1">{{ comissao }}%</p>
        <p class="text-xs text-zinc-500 mt-1">Só pagas quando vendes. Sem mensalidade.</p>
      </button>
      <button type="button" role="radio" :aria-checked="modelValue.modelo === 'subscricao' ? 'true' : 'false'"
        :disabled="!planos.length" @click="escolher('subscricao')"
        :class="['p-4 rounded-xl border-2 text-left transition disabled:opacity-40 disabled:cursor-not-allowed',
                 modelValue.modelo === 'subscricao' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
        <p class="text-sm font-bold text-zinc-100">Subscrição</p>
        <p class="text-2xl font-black text-zinc-100 mt-1">
          <template v-if="maisBarato">desde {{ euros(maisBarato.preco_mes) }}<span class="text-sm font-semibold text-zinc-400">/mês</span></template>
          <template v-else>—</template>
        </p>
        <p class="text-xs text-zinc-500 mt-1">{{ planos.length ? 'Valor fixo. Sem comissão nas vendas.' : 'Sem planos disponíveis de momento.' }}</p>
      </button>
    </div>

    <div v-if="modelValue.modelo === 'subscricao'" class="space-y-2" role="radiogroup" aria-label="Plano">
      <p class="text-xs font-semibold text-zinc-400">Escolhe o plano</p>
      <button v-for="p in planos" :key="p.id" type="button" role="radio" :aria-checked="modelValue.plano_id === p.id ? 'true' : 'false'"
        @click="$emit('update:modelValue', { modelo: 'subscricao', plano_id: p.id })"
        :class="['w-full flex items-center gap-3 p-3 rounded-xl border-2 text-left transition',
                 modelValue.plano_id === p.id ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
        <span class="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center"
              :class="modelValue.plano_id === p.id ? 'border-red-500' : 'border-zinc-600'">
          <span v-if="modelValue.plano_id === p.id" class="w-2 h-2 rounded-full bg-red-500"></span>
        </span>
        <span class="flex-1 min-w-0">
          <span class="block text-sm font-semibold text-zinc-100">{{ p.nome }} <span class="text-xs font-normal text-zinc-500">· {{ p.periodicidade_nome }}</span>
            <span v-if="p.tipo === 'loja_pos'" class="ml-1 rounded-full bg-violet-500/15 px-1.5 py-0.5 text-[10px] font-bold text-violet-300">Inclui o POS</span></span>
          <span v-if="p.descricao" class="block text-xs text-zinc-500 truncate">{{ p.descricao }}</span>
        </span>
        <span class="text-right flex-shrink-0">
          <span class="block text-sm font-bold text-zinc-100">{{ euros(p.preco) }}</span>
          <span v-if="p.meses > 1" class="block text-[11px] text-zinc-500">{{ euros(p.preco_mes) }}/mês</span>
        </span>
      </button>
      <p v-if="diasTeste" class="text-xs text-green-400">Os primeiros {{ diasTeste }} dias são grátis — só pagas depois de a loja ser aprovada e o teste acabar.</p>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'

export default {
  name: 'EscolherCobranca',
  props: { modelValue: { type: Object, required: true } },
  emits: ['update:modelValue'],

  data () {
    return { planos: [], comissao: '10', diasTeste: 0 }
  },

  computed: {
    maisBarato () {
      return this.planos.reduce((m, p) => (!m || Number(p.preco_mes) < Number(m.preco_mes) ? p : m), null)
    },
  },

  async created () {
    try {
      const { data } = await api.get('/app/planos/')
      this.planos = data.planos || []
      this.comissao = String(Number(data.comissao_padrao))
      this.diasTeste = data.dias_teste || 0
    } catch (e) { /* fica só a comissão */ }
  },

  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    escolher (modelo) {
      const plano = modelo === 'subscricao' ? (this.modelValue.plano_id || this.planos[0]?.id || null) : null
      this.$emit('update:modelValue', { modelo, plano_id: plano })
    },
  },
}
</script>
