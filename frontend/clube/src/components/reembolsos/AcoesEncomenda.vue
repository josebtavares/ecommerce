<template>
  <!-- Perfil → Encomendas: cancelar, pedir reembolso e acompanhar o pedido (regras no backend: utils/devolucoes.py) -->
  <div class="border-t pt-3 space-y-2" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">

    <button v-if="encomenda.reembolso" type="button" @click="abrir(encomenda.reembolso.id)"
      class="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl border text-xs transition"
      :class="isDark ? 'border-zinc-700 hover:border-zinc-500 text-zinc-300' : 'border-gray-300 hover:border-gray-400 text-zinc-700'">
      <span class="font-semibold flex items-center gap-1.5">
        <font-awesome-icon :icon="['fas', 'rotate-left']" />
        {{ encomenda.reembolso.tipo === 'cancelamento' ? 'Pedido de cancelamento' : 'Pedido de reembolso' }}
      </span>
      <span class="flex items-center gap-2">
        <EstadoReembolso :estado="encomenda.reembolso.estado" :valor="encomenda.reembolso.valor" />
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-[10px] opacity-60" />
      </span>
    </button>

    <div v-if="Number(encomenda.valor_reembolsado) > 0" class="flex items-center justify-between text-xs">
      <span :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Reembolsado</span>
      <span class="font-semibold text-green-500">{{ formatarDinheiro(encomenda.valor_reembolsado) }}</span>
    </div>

    <p v-if="carregando" class="text-xs text-center py-1" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">A verificar opções…</p>

    <template v-else-if="op && !op.reembolso_ativo && !confirmar">
      <button v-if="op.cancelar" type="button" @click="confirmar = true"
        class="w-full py-2 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-2"
        :class="isDark ? 'border-red-500/40 text-red-400 hover:bg-red-500/10' : 'border-red-300 text-red-600 hover:bg-red-50'">
        <font-awesome-icon :icon="['fas', 'ban']" />
        {{ op.cancelar === 'pedido' ? 'Pedir cancelamento' : 'Cancelar encomenda' }}
      </button>
      <button v-if="op.motivos.length" type="button" @click="pedirReembolso"
        class="w-full py-2 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-2"
        :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
        <font-awesome-icon :icon="['fas', 'rotate-left']" /> Pedir reembolso ou devolução
      </button>
      <p v-else-if="encomenda.status === 'concluido' && Number(op.reembolsavel) > 0"
         class="text-[11px] text-center" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
        O prazo para pedir reembolso desta encomenda já terminou.
      </p>
      <p v-if="encomenda.status === 'enviado'" class="text-[11px] text-center" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
        A encomenda já vai a caminho. Se houver algum problema, podes pedir reembolso depois de a receberes.
      </p>
    </template>

    <!-- confirmação do cancelamento -->
    <div v-if="confirmar" class="rounded-xl border p-3 space-y-2"
         :class="isDark ? 'border-red-500/30 bg-red-500/5' : 'border-red-200 bg-red-50'">
      <p class="text-xs font-semibold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ tituloConfirmar }}</p>
      <p class="text-xs" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ textoConfirmar }}</p>
      <textarea v-if="op.cancelar === 'pedido' || Number(op.reembolsavel) > 0" v-model="motivo" rows="2" maxlength="500"
        placeholder="Motivo (opcional)"
        class="w-full px-3 py-2 rounded-lg text-xs border focus:outline-none focus:border-red-500 resize-none"
        :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea>
      <div class="flex gap-2">
        <button type="button" @click="confirmar = false" :disabled="aEnviar"
          class="flex-1 py-2 rounded-lg text-xs font-semibold transition"
          :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-gray-200 hover:bg-gray-300 text-zinc-700'">
          Voltar
        </button>
        <button type="button" @click="cancelar" :disabled="aEnviar"
          class="flex-1 py-2 rounded-lg text-xs font-bold text-white bg-red-600 hover:bg-red-500 transition disabled:opacity-60">
          {{ aEnviar ? 'A enviar…' : (op.cancelar === 'pedido' ? 'Enviar pedido' : 'Cancelar encomenda') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import EstadoReembolso from './EstadoReembolso.vue'

const props = defineProps({
  encomenda: { type: Object, required: true },   // detalhe (/app/encomenda/<id>/)
  isDark:    { type: Boolean, default: true },
})
const emit = defineEmits(['atualizada', 'navegar'])

const router    = useRouter()
const op        = ref(null)
const carregando = ref(false)
const confirmar = ref(false)
const motivo    = ref('')
const aEnviar   = ref(false)

async function carregar () {
  if (['cancelado'].includes(props.encomenda.status) && !props.encomenda.reembolso) { op.value = null; return }
  carregando.value = true
  try {
    const { data } = await api.get(`/app/encomendas/${props.encomenda.id}/reembolso/opcoes/`)
    op.value = data
  } catch { op.value = null }
  finally { carregando.value = false }
}
onMounted(carregar)
watch(() => [props.encomenda.status, props.encomenda.reembolso?.estado], carregar)

const tituloConfirmar = computed(() =>
  op.value?.cancelar === 'pedido' ? 'Pedir à loja para cancelar?' : 'Cancelar esta encomenda?')

const textoConfirmar = computed(() => {
  const o = op.value
  if (!o) return ''
  if (o.cancelar === 'pedido') {
    return 'A loja já está a preparar a encomenda, por isso tem de aceitar o cancelamento. ' +
           'Se não responder em 48 horas, a equipa da Bendi decide.' +
           (Number(o.reembolsavel) > 0 ? ` Se for aceite, recebes ${formatarDinheiro(o.reembolsavel)}.` : '')
  }
  if (Number(o.reembolsavel) > 0) {
    return `A encomenda é cancelada e recebes ${formatarDinheiro(o.reembolsavel)} no meio de pagamento que usaste.`
  }
  return 'A encomenda é cancelada. Não foi cobrado nada.'
})

async function cancelar () {
  aEnviar.value = true
  try {
    const { data } = await api.post(`/app/encomendas/${props.encomenda.id}/cancelar/`, { descricao: motivo.value })
    confirmar.value = false
    motivo.value = ''
    const r = data.reembolso
    if (!r) toast.success('Encomenda cancelada.')
    else if (r.estado === 'reembolsado') toast.success(`Encomenda cancelada. Reembolso de ${formatarDinheiro(r.valor_aprovado)} feito.`)
    else toast.info('Pedido de cancelamento enviado à loja.')
    emit('atualizada')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível cancelar a encomenda.')
    carregar()
  } finally { aEnviar.value = false }
}

function abrir (id) {
  emit('navegar')
  router.push(`/perfil/reembolsos/${id}`)
}

function pedirReembolso () {
  emit('navegar')
  router.push(`/encomenda/${props.encomenda.id}/reembolso`)
}
</script>
