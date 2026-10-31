<template>
  <!-- Fechar uma entrega não se desfaz: confirma o que se recebeu ou pede o motivo da falha.
       Usado na lista de Entregas e no Calendário -->
  <div class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
       @click.self="$emit('fechar')">
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 space-y-4 shadow-2xl" role="dialog" aria-modal="true">
      <template v-if="falhou">
        <h3 class="text-base font-bold text-zinc-100">{{ isCondutor ? 'Não conseguiste entregar?' : 'A entrega falhou?' }}</h3>
        <p class="text-sm text-zinc-400">A encomenda <strong>#{{ encomendaId }}</strong> volta à loja e o cliente é avisado.</p>
        <div class="space-y-1.5">
          <label v-for="m in MOTIVOS" :key="m.valor"
                 class="flex items-center gap-2 px-3 py-2 rounded-lg border border-zinc-800 text-sm text-zinc-200 cursor-pointer">
            <input v-model="motivo" type="radio" name="motivo_falha" :value="m.valor" class="accent-red-500" />{{ m.texto }}
          </label>
        </div>
        <input v-model="nota" type="text" maxlength="200" placeholder="Nota para a loja (opcional)" aria-label="Nota para a loja"
               class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
      </template>
      <template v-else>
        <h3 class="text-base font-bold text-zinc-100">Confirmar a entrega?</h3>
        <p class="text-sm text-zinc-400">A encomenda <strong>#{{ encomendaId }}</strong> fica concluída. Isto não se pode desfazer.</p>
        <p v-if="aCobrar" class="px-3 py-2 rounded-lg bg-amber-500/15 text-amber-300 text-sm font-semibold">
          Recebeste {{ dinheiro(aCobrar) }} em dinheiro?
        </p>
      </template>

      <div class="flex gap-3">
        <button type="button" @click="$emit('fechar')"
          class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
          Voltar
        </button>
        <button type="button" @click="confirmar" :disabled="aGuardar || (falhou && !motivo)"
          :class="['flex-1 py-2.5 rounded-xl text-white text-sm font-bold transition disabled:opacity-40',
                   falhou ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500']">
          {{ falhou ? 'Confirmar' : aCobrar ? 'Sim, recebi' : 'Sim, entreguei' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'

const MOTIVOS = [
  { valor: 'cliente_ausente', texto: 'Cliente ausente' },
  { valor: 'sem_contacto',    texto: 'Cliente não atende' },
  { valor: 'morada_errada',   texto: 'Morada errada ou incompleta' },
  { valor: 'recusada',        texto: 'O cliente recusou' },
  { valor: 'outro',           texto: 'Outro motivo' },
]

export default {
  name: 'ConfirmarEntrega',
  props: {
    falhou:     { type: Boolean, default: false },
    encomendaId: { type: [String, Number], required: true },
    aCobrar:    { type: [String, Number], default: null },
    isCondutor: { type: Boolean, default: false },
    aGuardar:   { type: Boolean, default: false },
  },
  emits: ['confirmar', 'fechar'],

  data () {
    return { MOTIVOS, motivo: '', nota: '' }
  },

  methods: {
    dinheiro: formatarDinheiro,
    confirmar () {
      this.$emit('confirmar', this.falhou ? { motivo_falha: this.motivo, nota_falha: this.nota } : {})
    },
  },
}
</script>
