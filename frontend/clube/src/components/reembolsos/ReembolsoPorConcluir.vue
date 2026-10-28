<!-- ReembolsoPorConcluir.vue — o reembolso foi aceite mas o pagamento online recusou devolvê-lo
     (backend utils/devolucoes.py, estado por_reembolsar; também as marcações). A loja e a Bendi vêem o
     motivo e podem tentar de novo; só a Bendi (gerir_pagamentos) o dá como devolvido (com a referência).
     Incerto: o fornecedor não respondeu e pode já ter devolvido — só a Bendi tenta, depois de confirmar. -->
<template>
  <section class="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3" data-teste="reembolso-por-concluir">
    <div>
      <p class="text-sm font-bold text-amber-200">Reembolso de {{ dinheiro(valor) }} por concluir</p>
      <p v-if="incerto" class="text-xs text-amber-300 mt-1" data-teste="reembolso-incerto">
        O pagamento online não respondeu — o dinheiro pode já ter saído<template v-if="erro">: <span class="text-amber-200">“{{ semPonto(erro) }}”</span></template>.
        {{ podeTentar || porFora ? 'Confirma no painel do fornecedor antes de tentar de novo ou de o dar como devolvido.'
                                 : 'A equipa da Bendi vai confirmar se o dinheiro já saiu.' }}
      </p>
      <p v-else class="text-xs text-amber-300 mt-1">
        A devolução foi aceite, mas o pagamento online recusou-a<template v-if="erro">: <span class="text-amber-200">“{{ semPonto(erro) }}”</span></template>.
        <template v-if="proxima">Tentamos de novo sozinhos a {{ dataHora(proxima) }}.</template>
        <template v-else>Já não tentamos sozinhos — {{ porFora ? 'tenta de novo ou dá-o como devolvido.' : 'a equipa da Bendi foi avisada e vai tratar disso.' }}</template>
      </p>
      <p class="text-[11px] text-zinc-500 mt-1">{{ tentativas }} tentativa(s) até agora.<template v-if="!incerto"> Tentar de novo nunca devolve duas vezes.</template></p>
    </div>
    <template v-if="podeTentar">
      <label v-if="incerto" class="flex items-start gap-2 text-xs text-zinc-300">
        <input type="checkbox" v-model="confirmei" class="mt-0.5" data-teste="reembolso-confirmei" />
        Confirmei no painel do fornecedor que este reembolso não saiu.
      </label>
      <button type="button" @click="$emit('tentar', { confirmado: incerto && confirmei })" :disabled="aEnviar || (incerto && !confirmei)"
        data-teste="reembolso-tentar"
        class="w-full py-2.5 rounded-xl text-sm font-bold text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-60">
        {{ aEnviar ? 'A tentar…' : 'Tentar de novo' }}
      </button>
    </template>

    <template v-if="porFora">
      <button v-if="!foraAberto" type="button" @click="foraAberto = true" data-teste="reembolso-por-fora-abrir"
        class="w-full py-2 rounded-xl text-xs font-semibold border border-zinc-700 text-zinc-300 hover:bg-zinc-800">
        {{ incerto ? 'Já foi devolvido (confirmado no fornecedor ou por transferência)' : 'Já devolvemos por fora (ex.: transferência)' }}
      </button>
      <div v-else class="space-y-2 pt-1">
        <input v-model.trim="referencia" maxlength="100" placeholder="Referência da devolução (obrigatória)" data-teste="reembolso-por-fora-ref"
          class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-500" />
        <input v-model.trim="nota" maxlength="300" placeholder="Nota (opcional, o cliente vê)"
          class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-500" />
        <div class="flex gap-2">
          <button type="button" @click="foraAberto = false" class="flex-1 py-2 rounded-xl text-sm border border-zinc-700 text-zinc-300">Voltar</button>
          <button type="button" @click="$emit('por-fora', { referencia, nota })" :disabled="aEnviar || referencia.length < 3"
            data-teste="reembolso-por-fora-confirmar"
            class="flex-1 py-2 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-50">
            Dar como devolvido
          </button>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { formatarDinheiro } from '@/utils/dinheiro'
import { dataHora } from '@/utils/reembolsos'

defineProps({
  valor:      { type: [String, Number], default: 0 },
  erro:       { type: String, default: '' },
  tentativas: { type: Number, default: 0 },
  proxima:    { type: String, default: null },
  incerto:    { type: Boolean, default: false },     // o fornecedor não respondeu — pode já ter devolvido
  podeTentar: { type: Boolean, default: true },
  porFora:    { type: Boolean, default: false },     // só a Bendi com gerir_pagamentos
  aEnviar:    { type: Boolean, default: false },
})
defineEmits(['tentar', 'por-fora'])

const foraAberto = ref(false)
const confirmei = ref(false)
const referencia = ref('')
const nota = ref('')
const dinheiro = v => formatarDinheiro(v || 0)
const semPonto = t => (t || '').replace(/[.\s]+$/, '')     // a frase já fecha com ponto
</script>
