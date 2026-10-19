<template>
  <!-- Backoffice → Devoluções: pedidos de cancelamento e reembolso dos clientes -->
  <div class="space-y-4">
    <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
      <button v-for="g in GRUPOS" :key="g.key" type="button" @click="mudarGrupo(g.key)"
        :class="['px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-2',
                 grupo === g.key ? 'bg-red-600 text-white' : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ g.label }}
        <span v-if="contagem[g.key]" :class="['min-w-[18px] h-[18px] px-1 rounded-full text-[10px] flex items-center justify-center',
                                             grupo === g.key ? 'bg-white/25' : (g.key === 'novos' ? 'bg-amber-500 text-zinc-950' : 'bg-zinc-800')]">
          {{ contagem[g.key] }}
        </span>
      </button>
    </div>
    <p class="text-xs text-zinc-500">{{ GRUPOS.find(g => g.key === grupo)?.ajuda }}</p>

    <div v-if="carregando" class="flex justify-center py-16">
      <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
    </div>
    <div v-else-if="!lista.length" class="text-center py-16 text-sm text-zinc-500">
      <font-awesome-icon :icon="['fas', 'rotate-left']" class="text-3xl text-zinc-700 mb-3 block mx-auto" />
      Sem pedidos aqui.
    </div>

    <div v-else class="space-y-2">
      <button v-for="r in lista" :key="r.id" type="button" @click="aberto = r.id"
        class="w-full text-left rounded-2xl border border-zinc-800 bg-zinc-900 hover:border-zinc-600 p-4 flex items-center gap-3 transition">
        <div class="flex-1 min-w-0">
          <p class="text-xs text-zinc-500 truncate">#{{ r.encomenda_id }} · {{ r.cliente_nome }} · {{ dataHora(r.data_criacao) }}</p>
          <p class="text-sm font-semibold text-zinc-100 truncate">{{ r.tipo === 'cancelamento' && r.motivo === 'cancelado_cliente' ? 'Pedido de cancelamento' : r.motivo_label }}</p>
          <p v-if="r.estado === 'pedido' && r.prazo_resposta" :class="['text-[11px] font-semibold mt-0.5', urgente(r) ? 'text-red-400' : 'text-amber-400']">
            <font-awesome-icon :icon="['fas', 'clock']" class="mr-1" />{{ tempoRestante(r.prazo_resposta) }}
          </p>
        </div>
        <div class="text-right flex-shrink-0 space-y-1">
          <EstadoReembolso :estado="r.estado" :valor="r.valor_aprovado ?? undefined" :metodo="r.metodo" />
          <p class="text-sm font-bold text-zinc-100">{{ formatarDinheiro(r.valor_aprovado ?? r.valor_pedido) }}</p>
        </div>
      </button>
      <div v-if="proximo !== null" class="text-center pt-2">
        <button type="button" @click="carregar(true)" class="px-4 py-2 rounded-xl text-xs bg-zinc-800 text-zinc-300">Ver mais</button>
      </div>
    </div>

    <BackofficeReembolso v-if="aberto" :loja-id="lojaId" :reembolso-id="aberto"
      @fechar="fechar" @alterado="carregar()" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { dataHora } from '@/utils/reembolsos'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import BackofficeReembolso from './BackofficeReembolso.vue'

const GRUPOS = [
  { key: 'novos',      label: 'Por responder',        ajuda: 'Pedidos à espera da tua resposta. Sem resposta em 48 horas, a equipa da Bendi decide.' },
  { key: 'produto',    label: 'A aguardar o produto', ajuda: 'Aceitaste e o cliente vai devolver o produto. Confirma quando o receberes para o reembolsar.' },
  { key: 'dinheiro',   label: 'Devolver em mão',      ajuda: 'Clientes que pagaram em dinheiro: devolve o valor em mão e marca "Dinheiro entregue". O cliente confirma (ou fica confirmado em 7 dias).' },
  { key: 'analise',    label: 'Em análise',           ajuda: 'À espera do cliente (propostas) ou da decisão da Bendi.' },
  { key: 'concluidos', label: 'Concluídos',           ajuda: 'Reembolsados, recusados ou desistências.' },
]

const props = defineProps({
  lojaId:      { type: [String, Number], required: true },
  reembolsoId: { type: [String, Number], default: null },   // aberto a partir de uma notificação
})
const emit = defineEmits(['contagem'])

const route      = useRoute()
const router     = useRouter()
const grupo      = ref('novos')
const lista      = ref([])
const contagem   = ref({})
const proximo    = ref(null)
const carregando = ref(true)
const aberto     = ref(props.reembolsoId ? Number(props.reembolsoId) : null)
const agora      = ref(Date.now())

async function carregar (mais = false) {
  try {
    const { data } = await api.get(`/app/loja/${props.lojaId}/reembolsos/`,
      { params: { grupo: grupo.value, offset: mais ? proximo.value : 0, limit: 20 } })
    lista.value = mais ? [...lista.value, ...data.results] : data.results
    proximo.value = data.next_offset
    contagem.value = data.contagem || {}
    emit('contagem', (contagem.value.novos || 0) + (contagem.value.dinheiro || 0))
  } catch (e) { console.error(e) }
  finally { carregando.value = false }
}

function mudarGrupo (g) {
  grupo.value = g
  carregando.value = true
  carregar()
}

function fechar () {
  aberto.value = null
  // tira ?reembolso= do endereço (a notificação já foi aberta)
  if (route.query.reembolso) {
    const q = { ...route.query }
    delete q.reembolso
    router.replace({ query: q })
  }
}

function tempoRestante (iso) {
  const ms = new Date(iso).getTime() - agora.value
  if (ms <= 0) return 'Prazo terminado — a passar para a Bendi'
  const h = Math.floor(ms / 3600000)
  return h >= 1 ? `Responde em ${h} h` : `Responde em ${Math.max(1, Math.floor(ms / 60000))} min`
}
const urgente = r => new Date(r.prazo_resposta).getTime() - agora.value < 12 * 3600000

let relogio = null
onMounted(() => {
  carregar()
  relogio = setInterval(() => { agora.value = Date.now() }, 60000)
})
onBeforeUnmount(() => clearInterval(relogio))
watch(() => props.reembolsoId, id => { if (id) aberto.value = Number(id) })
</script>
