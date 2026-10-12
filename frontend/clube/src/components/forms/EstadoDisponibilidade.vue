<template>
  <!-- resultado da verificação ao vivo (services/disponibilidade.js), por baixo do input -->
  <div v-if="verificador.estado" class="mt-1.5 text-[11px]">
    <p v-if="verificador.estado === 'a_verificar'" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
      A verificar…
    </p>
    <p v-else-if="verificador.estado === 'disponivel'" class="text-green-500 font-semibold">
      ✓ {{ textoDisponivel }}
    </p>
    <template v-else>
      <p :class="avisoClass">{{ textoIndisponivel || verificador.motivo }}</p>
      <div v-if="verificador.sugestoes.length" class="mt-1.5 flex flex-wrap items-center gap-1.5">
        <span :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Sugestões:</span>
        <button v-for="s in verificador.sugestoes" :key="s" type="button"
                class="px-2 py-0.5 rounded-full border transition-colors"
                :class="isDark
                  ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500'
                  : 'border-gray-300 text-zinc-600 hover:border-gray-400'"
                @click="$emit('usar', s)">
          {{ s }}
        </button>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'EstadoDisponibilidade',
  props: {
    verificador:       { type: Object, required: true },
    isDark:            { type: Boolean, default: true },
    textoDisponivel:   { type: String, default: 'Disponível' },
    // substitui a mensagem do servidor (ex.: no POS um email existente serve para entrar)
    textoIndisponivel: { type: String, default: '' },
    // aviso em vez de erro, quando não impede de continuar
    soAviso:           { type: Boolean, default: false },
  },
  emits: ['usar'],
  computed: {
    avisoClass () {
      return this.soAviso ? 'text-amber-500 font-semibold' : 'text-red-400 font-semibold'
    },
  },
}
</script>
