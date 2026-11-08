<template>
  <!-- separador "Reembolsos" do perfil: os 5 pedidos mais recentes e "Ver todos" → /perfil/reembolsos. Tempo real. -->
  <div>
    <div v-if="carregando" class="flex justify-center py-8"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-xl text-red-500" /></div>
    <p v-else-if="erro" class="text-center text-sm py-8 text-red-400">{{ erro }}</p>
    <p v-else-if="!lista.length" class="text-center text-sm py-8 text-zinc-500" data-teste="perfil-sem-reembolsos">
      Ainda não fizeste nenhum pedido de reembolso.<br />Podes pedi-lo na ficha de uma encomenda.
    </p>
    <div v-else class="space-y-2">
      <CartaoReembolso v-for="r in lista" :key="r.id" :r="r" :isDark="isDark" @click="ir(`/perfil/reembolsos/${r.id}`)" />
    </div>

    <div v-if="!carregando && total" class="text-center pt-4">
      <button type="button" @click="ir('/perfil/reembolsos')" data-teste="ver-todos-reembolsos"
        class="px-4 py-2 rounded-xl text-xs font-semibold transition"
        :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-white border border-gray-200 hover:bg-gray-50 text-zinc-600'">
        Ver todos os reembolsos ({{ total }})
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import CartaoReembolso from '@/components/reembolsos/CartaoReembolso.vue'
import { useTempoRealReembolsos } from '@/composables/useTempoRealReembolsos'

defineProps({ isDark: { type: Boolean, default: true } })
const emit = defineEmits(['fechar'])
const router = useRouter()

const MOSTRAR = 5
const lista = ref([])
const total = ref(0)
const carregando = ref(true)
const erro = ref('')
let pedido = 0

async function carregar (silencioso = false) {
  const meu = ++pedido
  if (!silencioso) carregando.value = true
  try {
    const { data } = await api.get('/app/reembolsos/', { params: { offset: 0, limit: MOSTRAR } })
    if (meu !== pedido) return
    lista.value = data.results || []
    total.value = data.count ?? lista.value.length
    erro.value = ''
  } catch (e) {
    if (meu === pedido && !silencioso) erro.value = 'Não foi possível carregar os reembolsos.'
  } finally {
    if (meu === pedido) carregando.value = false
  }
}

function ir (caminho) {
  emit('fechar')
  router.push(caminho)
}

onMounted(() => carregar())
// tempo real: a loja respondeu, aprovou, reembolsou… (só enquanto o separador está aberto)
useTempoRealReembolsos(() => carregar(true))
</script>
