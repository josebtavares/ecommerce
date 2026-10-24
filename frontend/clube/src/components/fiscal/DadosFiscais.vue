<!-- DadosFiscais.vue — NIF, particular/atividade e declaração de responsabilidade (criar loja, backoffice, POS).
     v-model: { nif, regime_fiscal, declaracao_fiscal }. tema 'escuro' (Bende) ou 'claro' (POS). -->
<template>
  <div class="space-y-4" data-teste="dados-fiscais">
    <div>
      <label class="mb-1.5 block text-xs" :class="c.label">NIF *</label>
      <input :value="modelValue.nif" @input="atualizar('nif', $event.target.value)" inputmode="numeric" maxlength="11"
        placeholder="9 dígitos" autocomplete="off" data-teste="nif"
        class="w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none" :class="[c.input, nifErrado ? 'border-red-500' : '']" />
      <p v-if="nifErrado" class="mt-1 text-xs text-red-400">O NIF tem 9 dígitos.</p>
    </div>

    <div>
      <p class="mb-1.5 text-xs" :class="c.label">Como vendes? *</p>
      <div class="grid gap-2 sm:grid-cols-2">
        <button v-for="r in regimes" :key="r.valor" type="button" @click="atualizar('regime_fiscal', r.valor)"
          :data-teste="`regime-${r.valor}`"
          class="rounded-xl border px-4 py-3 text-left transition"
          :class="modelValue.regime_fiscal === r.valor ? c.opcaoAtiva : c.opcao">
          <span class="block text-sm font-semibold">{{ r.titulo }}</span>
          <span class="mt-0.5 block text-xs" :class="c.ajuda">{{ r.texto }}</span>
        </button>
      </div>
    </div>

    <label class="flex cursor-pointer items-start gap-3 text-xs leading-relaxed" :class="c.texto">
      <input type="checkbox" :checked="modelValue.declaracao_fiscal" @change="atualizar('declaracao_fiscal', $event.target.checked)"
        data-teste="declaracao" class="mt-0.5 h-4 w-4 flex-shrink-0" :class="c.check" />
      <span>Declaro que estes dados são verdadeiros e que sou responsável pelas minhas obrigações fiscais,
        incluindo emitir faturas no e-Fatura quando aplicável.</span>
    </label>
  </div>
</template>

<script>
import { REGIMES, nifLimpo } from '@/utils/fiscal'

const TEMAS = {
  escuro: {
    label: 'text-zinc-500', texto: 'text-zinc-400', ajuda: 'text-zinc-500', check: 'accent-red-600',
    input: 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:border-red-500',
    opcao: 'border-zinc-700 bg-zinc-800 text-zinc-300 hover:border-zinc-500',
    opcaoAtiva: 'border-red-500 bg-red-500/10 text-zinc-100',
  },
  claro: {
    label: 'font-black text-slate-700', texto: 'text-slate-600', ajuda: 'text-slate-500', check: 'accent-slate-950',
    input: 'border-slate-200 bg-slate-50 text-slate-950 focus:border-slate-950 focus:bg-white',
    opcao: 'border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-400',
    opcaoAtiva: 'border-slate-950 bg-white text-slate-950 ring-2 ring-slate-950/10',
  },
}

export default {
  name: 'DadosFiscais',
  props: {
    modelValue: { type: Object, required: true },
    tema: { type: String, default: 'escuro' },
  },
  emits: ['update:modelValue'],
  computed: {
    c () { return TEMAS[this.tema] || TEMAS.escuro },
    regimes () { return REGIMES },
    // só avisa depois de escrever qualquer coisa
    nifErrado () { return !!this.modelValue.nif && nifLimpo(this.modelValue.nif).length !== 9 },
  },
  methods: {
    atualizar (campo, valor) {
      this.$emit('update:modelValue', { ...this.modelValue, [campo]: valor })
    },
  },
}
</script>
