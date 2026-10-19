<template>
  <!-- Admin → Devoluções: disputas para decidir, pedidos em curso e métricas por loja e cliente -->
  <div class="space-y-4">
    <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
      <button v-for="g in GRUPOS" :key="g.key" type="button" @click="mudarGrupo(g.key)"
        :class="['px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-2',
                 grupo === g.key ? 'bg-red-600 text-white' : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ g.label }}
        <span v-if="contagem[g.key]" :class="['min-w-[18px] h-[18px] px-1 rounded-full text-[10px] flex items-center justify-center',
                                             grupo === g.key ? 'bg-white/25' : (g.key === 'disputa' ? 'bg-purple-500 text-white' : 'bg-zinc-800')]">
          {{ contagem[g.key] }}
        </span>
      </button>
    </div>

    <div v-if="filtro" class="flex items-center gap-2 text-xs">
      <span class="px-2.5 py-1 rounded-full bg-zinc-800 text-zinc-300">{{ filtro.label }}</span>
      <button type="button" @click="limparFiltro" class="text-zinc-500 hover:text-zinc-300">Limpar filtro</button>
    </div>

    <!-- métricas -->
    <template v-if="grupo === 'metricas'">
      <div class="flex items-center gap-2">
        <select v-model.number="periodo" @change="carregarMetricas"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-200">
          <option :value="30">Últimos 30 dias</option>
          <option :value="90">Últimos 90 dias</option>
          <option :value="365">Último ano</option>
        </select>
      </div>
      <div v-if="metricas" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div v-for="k in kpis" :key="k.label" class="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <p class="text-xs text-zinc-500">{{ k.label }}</p>
          <p class="text-xl font-bold text-zinc-100 mt-1">{{ k.valor }}</p>
        </div>
      </div>
      <section v-if="metricas" class="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
        <p class="px-4 pt-4 pb-2 text-xs font-bold uppercase tracking-wider text-zinc-500">Por loja</p>
        <div class="overflow-x-auto">
          <table class="w-full text-sm min-w-[560px]">
            <thead class="text-xs text-zinc-500 text-left">
              <tr><th class="px-4 py-2">Loja</th><th class="px-2">Pedidos</th><th class="px-2">Taxa</th><th class="px-2">Reembolsados</th>
                  <th class="px-2">Recusados</th><th class="px-2">Disputas</th><th class="px-4 text-right">Valor</th></tr>
            </thead>
            <tbody>
              <tr v-for="l in metricas.lojas" :key="l.loja_id" @click="filtrar('loja_id', l.loja_id, `Loja: ${l.loja_nome}`)"
                  class="border-t border-zinc-800 hover:bg-zinc-800/50 cursor-pointer text-zinc-300">
                <td class="px-4 py-2 text-zinc-100">{{ l.loja_nome }}</td>
                <td class="px-2">{{ l.pedidos }}</td>
                <td class="px-2" :class="l.taxa >= 10 ? 'text-red-400 font-bold' : ''">{{ l.taxa === null ? '—' : l.taxa + '%' }}</td>
                <td class="px-2">{{ l.reembolsados }}</td><td class="px-2">{{ l.recusados }}</td><td class="px-2">{{ l.disputas }}</td>
                <td class="px-4 text-right">{{ dinheiro(l.valor) }}</td>
              </tr>
              <tr v-if="!metricas.lojas.length"><td colspan="7" class="px-4 py-6 text-center text-zinc-500">Sem pedidos no período.</td></tr>
            </tbody>
          </table>
        </div>
        <p class="px-4 py-3 text-[11px] text-zinc-600">Taxa = pedidos de reembolso ÷ encomendas pagas no período. Acima de 10% a vermelho.</p>
      </section>
      <section v-if="metricas" class="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
        <p class="px-4 pt-4 pb-2 text-xs font-bold uppercase tracking-wider text-zinc-500">Clientes com mais pedidos</p>
        <div class="overflow-x-auto">
          <table class="w-full text-sm min-w-[480px]">
            <thead class="text-xs text-zinc-500 text-left">
              <tr><th class="px-4 py-2">Cliente</th><th class="px-2">Pedidos</th><th class="px-2">Reembolsados</th><th class="px-2">Recusados</th><th class="px-4 text-right">Valor</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in metricas.clientes" :key="c.utilizador_id" @click="filtrar('comprador_id', c.utilizador_id, `Cliente: ${c.nome}`)"
                  class="border-t border-zinc-800 hover:bg-zinc-800/50 cursor-pointer text-zinc-300">
                <td class="px-4 py-2 text-zinc-100">{{ c.nome }} <span class="text-zinc-500 text-xs">@{{ c.username }}</span></td>
                <td class="px-2">{{ c.pedidos }}</td><td class="px-2">{{ c.reembolsados }}</td><td class="px-2">{{ c.recusados }}</td>
                <td class="px-4 text-right">{{ dinheiro(c.valor) }}</td>
              </tr>
              <tr v-if="!metricas.clientes.length"><td colspan="5" class="px-4 py-6 text-center text-zinc-500">Sem pedidos no período.</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- lista -->
    <template v-else>
      <p class="text-xs text-zinc-500">{{ GRUPOS.find(g => g.key === grupo)?.ajuda }}</p>
      <div v-if="carregando" class="flex justify-center py-16">
        <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
      </div>
      <div v-else-if="!lista.length" class="text-center py-16 text-sm text-zinc-500">Sem pedidos aqui.</div>
      <div v-else class="space-y-2">
        <button v-for="r in lista" :key="r.id" type="button" @click="aberto = r.id"
          class="w-full text-left rounded-2xl border border-zinc-800 bg-zinc-900 hover:border-zinc-600 p-4 flex items-center gap-3 transition">
          <div class="flex-1 min-w-0">
            <p class="text-xs text-zinc-500 truncate">#{{ r.encomenda_id }} · {{ r.loja_nome }} · {{ r.cliente_nome }} · {{ dataHora(r.data_criacao) }}</p>
            <p class="text-sm font-semibold text-zinc-100 truncate">{{ r.tipo === 'cancelamento' && r.motivo !== 'pagamento_tardio' ? 'Pedido de cancelamento' : r.motivo_label }}</p>
          </div>
          <div class="text-right flex-shrink-0 space-y-1">
            <EstadoReembolso :estado="r.estado" :valor="r.valor_aprovado ?? undefined" />
            <p class="text-sm font-bold text-zinc-100">{{ dinheiro(r.valor_aprovado ?? r.valor_pedido) }}</p>
          </div>
        </button>
        <div v-if="proximo !== null" class="text-center pt-2">
          <button type="button" @click="carregar(true)" class="px-4 py-2 rounded-xl text-xs bg-zinc-800 text-zinc-300">Ver mais</button>
        </div>
      </div>
    </template>

    <AdminReembolso v-if="aberto" :reembolso-id="aberto" @fechar="fechar" @alterado="carregar()" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { dataHora } from '@/utils/reembolsos'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import AdminReembolso from './AdminReembolso.vue'

const GRUPOS = [
  { key: 'disputa',    label: 'Para decidir', ajuda: 'A loja não respondeu em 48 horas, recusou ou o cliente rejeitou a proposta. A decisão da Bendi é final.' },
  { key: 'ativos',     label: 'Em curso',     ajuda: 'Todos os pedidos ainda abertos (à espera da loja, do cliente, do produto ou da Bendi).' },
  { key: 'concluidos', label: 'Concluídos',   ajuda: 'Reembolsados, recusados ou desistências.' },
  { key: 'metricas',   label: 'Métricas',     ajuda: '' },
]

const emit = defineEmits(['disputas'])
const route  = useRoute()
const router = useRouter()

const grupo      = ref('disputa')
const lista      = ref([])
const contagem   = ref({})
const proximo    = ref(null)
const carregando = ref(true)
const aberto     = ref(route.query.reembolso ? Number(route.query.reembolso) : null)
const filtro     = ref(null)          // { campo, valor, label }
const metricas   = ref(null)
const periodo    = ref(90)

const dinheiro = v => formatarDinheiro(v || 0)
const kpis = computed(() => {
  const t = metricas.value?.total || {}
  return [
    { label: 'Pedidos', valor: t.pedidos ?? 0 },
    { label: 'Reembolsados', valor: t.reembolsados ?? 0 },
    { label: 'Foram à Bendi', valor: t.disputas ?? 0 },
    { label: 'Valor reembolsado', valor: dinheiro(t.valor) },
  ]
})

async function carregar (mais = false) {
  if (grupo.value === 'metricas') return carregarMetricas()
  try {
    const params = { grupo: grupo.value, offset: mais ? proximo.value : 0, limit: 20 }
    if (filtro.value) params[filtro.value.campo] = filtro.value.valor
    const { data } = await api.get('/app/admin/reembolsos/', { params })
    lista.value = mais ? [...lista.value, ...data.results] : data.results
    proximo.value = data.next_offset
    contagem.value = data.contagem || {}
    emit('disputas', contagem.value.disputa || 0)
  } catch (e) { console.error(e) }
  finally { carregando.value = false }
}

async function carregarMetricas () {
  try {
    const { data } = await api.get('/app/admin/reembolsos/metricas/', { params: { periodo: periodo.value } })
    metricas.value = data
  } catch (e) { console.error(e) }
  finally { carregando.value = false }
}

function mudarGrupo (g) {
  grupo.value = g
  carregando.value = true
  carregar()
}

function filtrar (campo, valor, label) {
  filtro.value = { campo, valor, label }
  mudarGrupo('ativos')
}

function limparFiltro () {
  filtro.value = null
  carregar()
}

function fechar () {
  aberto.value = null
  if (route.query.reembolso) {
    const q = { ...route.query }
    delete q.reembolso
    router.replace({ query: q })
  }
}

onMounted(() => carregar())
watch(() => route.query.reembolso, id => { if (id) aberto.value = Number(id) })
</script>
