<template>
  <!-- separador "Marcações" do perfil: as 5 primeiras (próximas ou anteriores) e "Ver todas" → /minhas-marcacoes. Tempo real. -->
  <div>
    <div role="tablist" class="flex gap-1 p-1 rounded-xl mb-4" :class="isDark ? 'bg-zinc-900' : 'bg-gray-100'">
      <button v-for="t in TIPOS" :key="t.k" type="button" role="tab" :aria-selected="tipo === t.k" @click="mudarTipo(t.k)"
        :data-teste="`perfil-marcacoes-${t.k}`"
        class="flex-1 py-2 rounded-lg text-xs font-semibold transition"
        :class="tipo === t.k
          ? (isDark ? 'bg-zinc-700 text-white' : 'bg-white text-zinc-900 shadow-sm')
          : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-500 hover:text-zinc-800')">{{ t.n }}</button>
    </div>

    <div v-if="carregando" class="flex justify-center py-8"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-xl text-red-500" /></div>
    <p v-else-if="erro" class="text-center text-sm py-8 text-red-400">{{ erro }}</p>
    <p v-else-if="!lista.length" class="text-center text-sm py-8 text-zinc-500" data-teste="perfil-sem-marcacoes">
      {{ tipo === 'proximas' ? 'Não tens marcações por fazer.' : 'Ainda não tens marcações anteriores.' }}
    </p>
    <div v-else class="space-y-2">
      <CartaoMarcacao v-for="m in lista.slice(0, MOSTRAR)" :key="m.id" :m="m" :isDark="isDark" @click="ir(`/minhas-marcacoes/${m.id}`)" />
    </div>

    <div class="text-center pt-4">
      <button type="button" @click="ir(tipo === 'anteriores' ? '/minhas-marcacoes?tipo=anteriores' : '/minhas-marcacoes')"
        data-teste="ver-todas-marcacoes"
        class="px-4 py-2 rounded-xl text-xs font-semibold transition"
        :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-white border border-gray-200 hover:bg-gray-50 text-zinc-600'">
        Ver todas as marcações{{ lista.length > MOSTRAR ? ` (${lista.length})` : '' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { ouvirMarcacoes } from '@/utils/servicos'
import CartaoMarcacao from '@/components/servicos/CartaoMarcacao.vue'

defineProps({ isDark: { type: Boolean, default: true } })
const emit = defineEmits(['fechar'])
const router = useRouter()

const MOSTRAR = 5
const TIPOS = [{ k: 'proximas', n: 'Próximas' }, { k: 'anteriores', n: 'Anteriores' }]
const tipo = ref('proximas')
const lista = ref([])
const carregando = ref(true)
const erro = ref('')
let pedido = 0

async function carregar (silencioso = false) {
  const meu = ++pedido
  if (!silencioso) carregando.value = true
  try {
    const { data } = await api.get('/app/marcacoes/', { params: { tipo: tipo.value } })
    if (meu !== pedido) return
    lista.value = data
    erro.value = ''
  } catch (e) {
    if (meu === pedido && !silencioso) erro.value = 'Não foi possível carregar as marcações.'
  } finally {
    if (meu === pedido) carregando.value = false
  }
}

function mudarTipo (k) {
  if (tipo.value === k) return
  tipo.value = k
  carregar()
}

function ir (caminho) {
  emit('fechar')
  router.push(caminho)
}

// tempo real: a loja confirmou, propôs outra hora, escreveu… (só enquanto o separador está aberto)
let desligar = null
onMounted(() => { carregar(); desligar = ouvirMarcacoes(() => carregar(true)) })
onBeforeUnmount(() => desligar?.())
</script>
