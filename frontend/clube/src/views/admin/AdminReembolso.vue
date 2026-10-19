<template>
  <!-- Admin → Devoluções: um pedido e a decisão da Bendi (regras: backend utils/devolucoes.py) -->
  <div class="fixed inset-0 z-50 flex justify-end">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('fechar')"></div>

    <aside class="relative w-full max-w-2xl h-full bg-zinc-950 border-l border-zinc-800 flex flex-col">
      <header class="flex items-center gap-3 px-4 h-14 border-b border-zinc-800 flex-shrink-0">
        <button type="button" aria-label="Fechar" @click="$emit('fechar')"
                class="h-9 w-9 rounded-lg hover:bg-zinc-800 text-zinc-300 flex items-center justify-center">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2 class="font-bold text-zinc-100 truncate">{{ r ? `Pedido #${r.id} · Encomenda #${r.encomenda_id}` : 'Pedido' }}</h2>
        <EstadoReembolso v-if="r" class="ml-auto" :estado="r.estado" :valor="r.valor_aprovado ?? undefined" />
      </header>

      <div v-if="carregando" class="flex-1 flex items-center justify-center">
        <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
      </div>
      <div v-else-if="erro" class="flex-1 flex items-center justify-center text-sm text-zinc-500 p-6 text-center">{{ erro }}</div>

      <div v-else-if="r" class="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
        <section class="rounded-2xl border border-zinc-800 bg-zinc-900 p-4 space-y-3">
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><p class="text-xs text-zinc-500">Loja</p><p class="text-zinc-100 truncate">{{ r.loja_nome }}</p></div>
            <div><p class="text-xs text-zinc-500">Cliente</p><p class="text-zinc-100 truncate">{{ r.cliente_nome }}</p></div>
            <div><p class="text-xs text-zinc-500">Motivo</p><p class="text-zinc-100">{{ r.motivo_label }}</p></div>
            <div><p class="text-xs text-zinc-500">Valor pedido</p><p class="text-zinc-100 font-bold">{{ dinheiro(r.valor_pedido) }}</p></div>
          </div>
          <p v-if="r.descricao" class="text-sm text-zinc-300 whitespace-pre-line">{{ r.descricao }}</p>
          <div class="border-t border-zinc-800 pt-3 space-y-1 text-sm">
            <div v-for="i in r.itens" :key="i.item_id" class="flex justify-between gap-3">
              <span class="text-zinc-300 truncate">{{ i.quantidade }}× {{ i.nome }}</span>
              <span class="text-zinc-400 flex-shrink-0">{{ dinheiro(i.valor) }}</span>
            </div>
            <div v-if="Number(r.valor_entrega) > 0" class="flex justify-between text-xs text-zinc-500">
              <span>Taxa de entrega</span><span>{{ dinheiro(r.valor_entrega) }}</span>
            </div>
            <p class="text-xs text-zinc-500 pt-1">
              Encomenda {{ dinheiro(r.encomenda.valor_total) }} · {{ r.encomenda.status }}
              <span v-if="Number(r.encomenda.reembolsado) > 0"> · já reembolsado {{ dinheiro(r.encomenda.reembolsado) }}</span>
            </p>
          </div>
          <p v-if="r.motivo_recusa" class="text-sm rounded-xl px-3 py-2 bg-zinc-950 text-zinc-400">
            Recusa{{ r.resposta_loja === 'recusado' ? ' da loja' : '' }}: “{{ r.motivo_recusa }}”
          </p>
        </section>

        <!-- decisão -->
        <section v-if="podeDecidir" class="rounded-2xl border border-purple-500/30 bg-purple-500/5 p-4 space-y-3">
          <p class="text-sm font-semibold text-purple-200">Decisão da Bendi</p>
          <p v-if="r.motivo === 'pagamento_tardio'" class="text-xs text-zinc-400">
            O gateway cobrou depois de a encomenda ser cancelada. Devolve o dinheiro no gateway e confirma aqui.
            {{ r.descricao }}
          </p>
          <p v-else class="text-xs text-zinc-400">A decisão é final: o cliente e a loja são avisados.</p>
          <div class="flex flex-wrap items-center gap-3">
            <label class="text-xs text-zinc-500">Valor a reembolsar</label>
            <div class="relative w-40">
              <input v-model="valor" type="number" min="1" step="1"
                class="w-full pl-3 pr-12 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-purple-500" />
              <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">CVE</span>
            </div>
          </div>
          <label v-if="r.tipo === 'devolucao' && ['defeito', 'errado', 'mudei_ideias'].includes(r.motivo) && r.estado !== 'aguarda_produto'"
                 class="flex items-center gap-2 text-sm text-zinc-200 cursor-pointer">
            <input type="checkbox" v-model="devolverProduto" class="accent-purple-600" />
            Reembolsar só quando a loja receber o produto
          </label>
          <textarea v-model="nota" rows="3" maxlength="2000" placeholder="Nota para o cliente e a loja (obrigatória para recusar)"
            class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-purple-500 resize-none"></textarea>
          <div class="flex flex-col sm:flex-row gap-2">
            <button type="button" @click="decidir('reembolsar')" :disabled="aEnviar || !(Number(valor) > 0)"
              class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-50">
              Reembolsar {{ dinheiro(valor) }}
            </button>
            <button type="button" @click="decidir('recusar')" :disabled="aEnviar || nota.trim().length < 5"
              class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50">
              Recusar
            </button>
          </div>
        </section>

        <section class="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <p class="text-xs font-bold uppercase tracking-wider mb-3 text-zinc-500">Estado</p>
          <ReembolsoLinhaTempo :reembolso="r" papel="admin" />
        </section>

        <ReembolsoConversa :reembolso="r" meuPapel="admin" :podeEscrever="r.estado === 'em_disputa'" @atualizado="r = $event" />
        <p v-if="r.estado !== 'em_disputa'" class="text-xs text-zinc-600 text-center">A Bendi só escreve nos pedidos em análise.</p>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { ATIVOS } from '@/utils/reembolsos'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import ReembolsoLinhaTempo from '@/components/reembolsos/ReembolsoLinhaTempo.vue'
import ReembolsoConversa from '@/components/reembolsos/ReembolsoConversa.vue'

const props = defineProps({ reembolsoId: { type: [String, Number], required: true } })
const emit = defineEmits(['fechar', 'alterado'])

const r          = ref(null)
const carregando = ref(true)
const erro       = ref('')
const aEnviar    = ref(false)
const valor      = ref('')
const nota       = ref('')
const devolverProduto = ref(false)

const dinheiro = v => formatarDinheiro(v || 0)
const podeDecidir = computed(() => r.value && (ATIVOS.includes(r.value.estado) || (r.value.estado === 'recusado' && !r.value.decisao_admin)))

async function carregar () {
  erro.value = ''
  try {
    const { data } = await api.get(`/app/reembolsos/${props.reembolsoId}/`)
    r.value = data
    valor.value = String(Math.round(Number(data.valor_aprovado ?? data.valor_pedido)))
  } catch (e) {
    erro.value = e.response?.status === 404 ? 'Pedido não encontrado.' : 'Não foi possível carregar o pedido.'
  } finally { carregando.value = false }
}

async function decidir (decisao) {
  aEnviar.value = true
  try {
    const corpo = { decisao, nota: nota.value }
    if (decisao === 'reembolsar') Object.assign(corpo, { valor: String(valor.value), devolver_produto: devolverProduto.value })
    const { data } = await api.post(`/app/admin/reembolsos/${r.value.id}/decidir/`, corpo)
    r.value = data
    nota.value = ''
    toast.success(decisao === 'recusar' ? 'Pedido recusado.' : data.estado === 'aguarda_produto' ? 'Decidido — à espera do produto.' : 'Reembolso feito.')
    emit('alterado')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível decidir.')
  } finally { aEnviar.value = false }
}

onMounted(carregar)
watch(() => props.reembolsoId, () => { carregando.value = true; carregar() })
</script>
