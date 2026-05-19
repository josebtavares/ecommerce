<template>
  <div
    @click="$emit('click')"
    :class="[
      'relative p-6 rounded-lg shadow-md cursor-pointer transition-all hover:shadow-lg',
      statusColor
    ]"
  >
    <!-- Status Badge -->
    <div class="absolute top-2 right-2 px-2 py-1 bg-white bg-opacity-90 rounded text-xs font-semibold">
      {{ statusText }}
    </div>

    <!-- Número da Mesa -->
    <div class="text-center mb-4">
      <div class="text-4xl font-bold text-gray-800 mb-1">
        {{ mesa.numero }}
      </div>
      <div class="text-sm text-gray-600">
        Capacidade: {{ mesa.capacidade }}
      </div>
    </div>

    <!-- Informações adicionais -->
    <div v-if="mesa.tem_conta_aberta" class="text-center text-sm text-gray-700 font-medium">
      Conta aberta
    </div>
    
    <div v-if="mesa.atendente_atual" class="text-center text-xs text-gray-500 mt-1">
      {{ mesa.atendente_atual.nome }}
    </div>

    <!-- Botões de ação -->
    <div class="flex justify-center space-x-2 mt-4">
      <button
        @click.stop="$emit('editar')"
        class="px-3 py-1 bg-white bg-opacity-70 hover:bg-opacity-100 rounded text-xs font-medium transition"
      >
        Editar
      </button>
      <button
        @click.stop="$emit('apagar')"
        class="px-3 py-1 bg-red-500 bg-opacity-70 hover:bg-opacity-100 text-white rounded text-xs font-medium transition"
      >
        Apagar
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MesaCard',
  
  props: {
    mesa: {
      type: Object,
      required: true
    }
  },
  
  computed: {
    statusColor() {
      const colors = {
        'livre': 'bg-green-100 border-2 border-green-300',
        'ocupada': 'bg-blue-100 border-2 border-blue-300',
        'reservada': 'bg-yellow-100 border-2 border-yellow-300',
        'limpeza': 'bg-gray-100 border-2 border-gray-300'
      }
      return colors[this.mesa.status] || 'bg-white border-2 border-gray-200'
    },
    
    statusText() {
      const texts = {
        'livre': 'Livre',
        'ocupada': 'Ocupada',
        'reservada': 'Reservada',
        'limpeza': 'Limpeza'
      }
      return texts[this.mesa.status] || this.mesa.status
    }
  }
}
</script>