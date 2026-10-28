<!-- ReembolsoPorConcluir.vue — o reembolso foi aceite mas o pagamento online recusou devolvê-lo
     (backend utils/devolucoes.py, estado por_reembolsar; também as marcações). A loja e a Bendi vêem o
     motivo e podem tentar de novo; só a Bendi o dá como devolvido por fora (com a referência). -->
<template>
  <section class="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3" data-teste="reembolso-por-concluir">
    <div>
      <p class="text-sm font-bold text-amber-200">Reembolso de {{ dinheiro(valor) }} por concluir</p>
      <p class="text-xs text-amber-300 mt-1">
        A devolução foi aceite, mas o pagamento online recusou-a<template v-if="erro">: <span class="text-amber-200">“{{ erro }}”</span></template>.
        <template v-if="proxima">Tentamos de novo sozinhos a {{ dataHora(proxima) }}.</template>
        <template v-else>Já não tentamos sozinhos — {{ porFora ? 'tenta de novo ou dá-o como devolvido por fora.' : 'a equipa da Bendi foi avisada e vai tratar disso.' }}</template>
      </p>
      <p class="text-[11px] text-zinc-500 mt-1">{{ tentativas }} tentativa(s) até agora. Tentar de novo nunca devolve duas vezes.</p>
    </div>
    <button type="button" @click="$emit('tentar')" :disabled="aEnviar" data-teste="reembolso-tentar"
      class="w-full py-2.5 rounded-xl text-sm font-bold text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-60">
      {{ aEnviar ? 'A tentar…' : 'Tentar de novo' }}
    </button>

    <template v-if="porFora">
      <button v-if="!foraAberto" type="button" @click="foraAberto = true" data-teste="reembolso-por-fora-abrir"
        class="w-full py-2 rounded-xl text-xs font-semibold border border-zinc-700 text-zinc-300 hover:bg-zinc-800">
        Já devolvemos por fora (ex.: transferência)
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
  porFora:    { type: Boolean, default: false },     // só a Bendi
  aEnviar:    { type: Boolean, default: false },
})
defineEmits(['tentar', 'por-fora'])

const foraAberto = ref(false)
const referencia = ref('')
const nota = ref('')
const dinheiro = v => formatarDinheiro(v || 0)
</script>
