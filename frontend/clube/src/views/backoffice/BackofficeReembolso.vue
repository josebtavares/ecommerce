<template>
  <!-- Painel de um pedido de reembolso no backoffice (regras: backend utils/devolucoes.py) -->
  <div class="fixed inset-0 z-50 flex justify-end">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('fechar')"></div>

    <aside class="relative w-full max-w-2xl h-full bg-zinc-950 border-l border-zinc-800 flex flex-col">
      <header class="flex items-center gap-3 px-4 h-14 border-b border-zinc-800 flex-shrink-0">
        <button type="button" aria-label="Fechar" @click="$emit('fechar')"
                class="h-9 w-9 rounded-lg hover:bg-zinc-800 text-zinc-300 flex items-center justify-center">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2 class="font-bold text-zinc-100 truncate">
          {{ r ? `${r.tipo === 'cancelamento' ? 'Cancelamento' : 'Reembolso'} · Encomenda #${r.encomenda_id}` : 'Pedido' }}
        </h2>
        <EstadoReembolso v-if="r" :metodo="r.metodo" class="ml-auto" :estado="r.estado" :valor="r.valor_aprovado ?? undefined" />
      </header>

      <div v-if="carregando" class="flex-1 flex items-center justify-center">
        <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
      </div>
      <div v-else-if="erro" class="flex-1 flex items-center justify-center text-sm text-zinc-500 p-6 text-center">{{ erro }}</div>

      <div v-else-if="r" class="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
        <!-- resumo -->
        <section class="rounded-2xl border border-zinc-800 bg-zinc-900 p-4 space-y-3">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs text-zinc-500">{{ r.cliente_nome }} · {{ dataHora(r.data_criacao) }}</p>
              <p class="font-semibold text-zinc-100">{{ r.motivo_label }}</p>
            </div>
            <div class="text-right flex-shrink-0">
              <p class="text-xs text-zinc-500">Pedido</p>
              <p class="font-bold text-zinc-100">{{ dinheiro(r.valor_pedido) }}</p>
            </div>
          </div>
          <p v-if="r.descricao" class="text-sm text-zinc-300 whitespace-pre-line">{{ r.descricao }}</p>
          <div class="border-t border-zinc-800 pt-3 space-y-1 text-sm">
            <div v-for="i in r.itens" :key="i.item_id" class="flex justify-between gap-3">
              <span class="text-zinc-300 min-w-0 truncate">{{ i.quantidade }}× {{ i.nome }}<span v-if="textoAtributos(i.atributos)" class="text-zinc-500"> · {{ textoAtributos(i.atributos) }}</span></span>
              <span class="text-zinc-400 flex-shrink-0">{{ dinheiro(i.valor) }}</span>
            </div>
            <div v-if="Number(r.valor_entrega) > 0" class="flex justify-between text-xs text-zinc-500">
              <span>Taxa de entrega</span><span>{{ dinheiro(r.valor_entrega) }}</span>
            </div>
            <div class="flex justify-between text-xs text-zinc-500 pt-1">
              <span>Encomenda: {{ dinheiro(r.encomenda.valor_total) }} · {{ r.encomenda.status }}</span>
              <span v-if="Number(r.encomenda.reembolsado) > 0">Já reembolsado: {{ dinheiro(r.encomenda.reembolsado) }}</span>
            </div>
          </div>
        </section>

        <!-- ── o que a loja pode fazer ── -->
        <section v-if="r.estado === 'pedido'" class="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3">
          <p class="text-sm text-amber-100">
            <font-awesome-icon :icon="['fas', 'clock']" class="mr-1" />
            Responde até <b>{{ dataHora(r.prazo_resposta) }}</b> — depois disso o pedido vai para a equipa da Bendi.
          </p>

          <!-- cancelamento antes de enviar -->
          <template v-if="r.tipo === 'cancelamento'">
            <p class="text-sm text-zinc-300">
              O cliente quer cancelar a encomenda, que já está em preparação. Se aceitares, a encomenda é cancelada,
              o stock volta e o cliente recebe {{ dinheiro(r.valor_pedido) }}. Se a enviares, o pedido conta como recusado.
            </p>
            <div v-if="!aRecusar" class="flex flex-col sm:flex-row gap-2">
              <button type="button" @click="acao('aceitar')" :disabled="aEnviar"
                class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-60">
                Aceitar cancelamento
              </button>
              <button type="button" @click="aRecusar = true" class="flex-1 py-2.5 rounded-xl text-sm border border-zinc-700 text-zinc-200 hover:border-zinc-500">
                Recusar
              </button>
            </div>
          </template>

          <!-- devolução depois de receber -->
          <template v-else-if="!aRecusar">
            <div class="space-y-2">
              <label class="flex items-center gap-2 text-sm text-zinc-200 cursor-pointer">
                <input type="radio" value="total" v-model="modo" class="accent-red-600" />
                Reembolsar o valor pedido ({{ dinheiro(r.valor_pedido) }})
              </label>
              <label class="flex items-center gap-2 text-sm text-zinc-200 cursor-pointer">
                <input type="radio" value="proposta" v-model="modo" class="accent-red-600" />
                Propor outro valor
              </label>
              <div v-if="modo === 'proposta'" class="pl-6">
                <div class="relative max-w-[200px]">
                  <input v-model="valorProposta" type="number" min="1" step="1" :max="Number(r.valor_pedido)"
                    class="w-full pl-3 pr-12 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
                  <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">CVE</span>
                </div>
                <p class="text-xs text-zinc-500 mt-1">O cliente pode aceitar ou pedir à Bendi para decidir.</p>
              </div>
            </div>
            <label v-if="['defeito', 'errado'].includes(r.motivo)" class="flex items-start gap-2 text-sm text-zinc-200 cursor-pointer">
              <input type="checkbox" v-model="devolverProduto" class="accent-red-600 mt-0.5" />
              <span>Pedir o produto de volta antes de reembolsar
                <span class="block text-xs text-zinc-500">Os portes de devolução são da loja (o problema é do produto).</span></span>
            </label>
            <p v-if="r.motivo === 'mudei_ideias'" class="text-xs text-zinc-400">
              Mudança de ideias: o cliente devolve o produto (com os portes por conta dele) e o reembolso é feito quando o receberes.
            </p>
            <div class="flex flex-col sm:flex-row gap-2">
              <button type="button" @click="aceitar" :disabled="aEnviar || (modo === 'proposta' && !propostaValida)"
                class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-50">
                {{ textoAceitar }}
              </button>
              <button type="button" @click="aRecusar = true" class="flex-1 py-2.5 rounded-xl text-sm border border-zinc-700 text-zinc-200 hover:border-zinc-500">
                Recusar
              </button>
            </div>
          </template>

          <div v-if="aRecusar" class="space-y-2">
            <textarea v-model="motivoRecusa" rows="3" maxlength="2000" placeholder="Explica ao cliente porque recusas (obrigatório)"
              class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 resize-none"></textarea>
            <p class="text-xs text-zinc-500">O cliente pode pedir à equipa da Bendi para analisar a decisão.</p>
            <div class="flex gap-2">
              <button type="button" @click="aRecusar = false" class="flex-1 py-2 rounded-xl text-sm border border-zinc-700 text-zinc-300">Voltar</button>
              <button type="button" @click="acao('recusar', { motivo: motivoRecusa })" :disabled="aEnviar || motivoRecusa.trim().length < 5"
                class="flex-1 py-2 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50">
                Recusar pedido
              </button>
            </div>
          </div>
        </section>

        <section v-else-if="r.estado === 'aguarda_produto'" class="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-4 space-y-3">
          <p class="text-sm text-zinc-200">
            O cliente vai devolver o produto. Quando o receberes, confirma aqui e o cliente recebe
            <b>{{ dinheiro(r.valor_aprovado ?? r.valor_pedido) }}</b>.
          </p>
          <template v-if="!aRecusar">
            <label class="flex items-start gap-2 text-sm text-zinc-200 cursor-pointer">
              <input type="checkbox" v-model="reporStock" class="accent-red-600 mt-0.5" />
              <span>Repor no stock<span class="block text-xs text-zinc-500">Só se o produto voltou em condições de ser vendido.</span></span>
            </label>
            <div class="flex flex-col sm:flex-row gap-2">
              <button type="button" @click="acao('recebido', { repor_stock: reporStock })" :disabled="aEnviar"
                class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-60">
                Recebi o produto — reembolsar
              </button>
              <button type="button" @click="aRecusar = true" class="flex-1 py-2.5 rounded-xl text-sm border border-zinc-700 text-zinc-200 hover:border-zinc-500">
                O produto não voltou em condições
              </button>
            </div>
          </template>
          <div v-else class="space-y-2">
            <textarea v-model="motivoRecusa" rows="3" maxlength="2000" placeholder="O que se passou com o produto devolvido? (obrigatório)"
              class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 resize-none"></textarea>
            <div class="flex gap-2">
              <button type="button" @click="aRecusar = false" class="flex-1 py-2 rounded-xl text-sm border border-zinc-700 text-zinc-300">Voltar</button>
              <button type="button" @click="acao('recusar', { motivo: motivoRecusa })" :disabled="aEnviar || motivoRecusa.trim().length < 5"
                class="flex-1 py-2 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50">
                Recusar reembolso
              </button>
            </div>
          </div>
        </section>

        <ReembolsoPorConcluir v-else-if="r.estado === 'por_reembolsar' && r.por_concluir" :valor="r.valor_aprovado"
          :erro="r.por_concluir.erro" :tentativas="r.por_concluir.tentativas" :proxima="r.por_concluir.proxima_tentativa"
          :incerto="r.por_concluir.incerto" :podeTentar="r.por_concluir.pode_tentar"
          :aEnviar="aEnviar" @tentar="acao('tentar_reembolso')" />

        <section v-else-if="r.estado === 'a_devolver'" class="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3">
          <template v-if="!r.entregue_em">
            <p class="text-sm text-amber-100">
              O cliente pagou {{ r.por_transferencia ? 'por transferência' : 'em dinheiro' }}: devolve-lhe <b>{{ dinheiro(r.valor_aprovado) }}</b> {{ r.por_transferencia ? 'por transferência' : 'em mão' }} até <b>{{ dataHora(r.prazo_resposta) }}</b>
              e marca aqui. Se não marcares, o pedido vai para a equipa da Bendi.
            </p>
            <button type="button" @click="acao('dinheiro_entregue')" :disabled="aEnviar"
              class="w-full py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-60">
              {{ r.por_transferencia ? 'Transferência feita' : 'Dinheiro entregue ao cliente' }}
            </button>
          </template>
          <p v-else class="text-sm text-zinc-300">
            Devolveste {{ dinheiro(r.valor_aprovado) }} {{ r.por_transferencia ? 'por transferência' : 'em mão' }} a {{ dataHora(r.entregue_em) }}. À espera da confirmação do cliente —
            fica confirmado sozinho a {{ dataHora(r.prazo_resposta) }}.
          </p>
        </section>

        <section v-else-if="aviso" class="rounded-2xl border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-300">
          {{ aviso }}
          <p v-if="r.motivo_recusa && r.estado === 'recusado'" class="mt-2 text-zinc-400">“{{ r.motivo_recusa }}”</p>
        </section>

        <section class="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <p class="text-xs font-bold uppercase tracking-wider mb-3 text-zinc-500">Estado</p>
          <ReembolsoLinhaTempo :reembolso="r" papel="loja" />
        </section>

        <ReembolsoConversa :reembolso="r" meuPapel="loja" :podeEscrever="podeEscrever" @atualizado="r = $event" />
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { formatarAtributos, temAtributos } from '@/utils/atributos'
import { dataHora } from '@/utils/reembolsos'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import ReembolsoLinhaTempo from '@/components/reembolsos/ReembolsoLinhaTempo.vue'
import ReembolsoConversa from '@/components/reembolsos/ReembolsoConversa.vue'
import ReembolsoPorConcluir from '@/components/reembolsos/ReembolsoPorConcluir.vue'
import { useTempoRealReembolsos } from '@/composables/useTempoRealReembolsos'

const props = defineProps({
  lojaId:      { type: [String, Number], required: true },
  reembolsoId: { type: [String, Number], required: true },
})
const emit = defineEmits(['fechar', 'alterado'])

const r          = ref(null)
const carregando = ref(true)
const erro       = ref('')
const aEnviar    = ref(false)
const aRecusar   = ref(false)
const motivoRecusa = ref('')
const modo       = ref('total')
const valorProposta = ref('')
const devolverProduto = ref(false)
const reporStock = ref(false)

const dinheiro = v => formatarDinheiro(v || 0)
const textoAtributos = a => temAtributos(a) ? Object.values(formatarAtributos(a)).join(' · ') : ''

const podeEscrever = computed(() => ['pedido', 'proposta', 'em_disputa', 'aguarda_produto', 'a_devolver', 'recusado'].includes(r.value?.estado))
const propostaValida = computed(() => {
  const v = Number(valorProposta.value)
  return v >= 1 && v < Number(r.value?.valor_pedido)
})
const textoAceitar = computed(() => {
  if (modo.value === 'proposta') return 'Enviar proposta'
  if (r.value?.motivo === 'mudei_ideias' || devolverProduto.value) return 'Aceitar e pedir o produto'
  return `Aceitar e reembolsar ${dinheiro(r.value?.valor_pedido)}`
})

const aviso = computed(() => {
  const x = r.value
  if (!x) return ''
  return {
    proposta: `Propuseste ${formatarDinheiro(x.valor_aprovado)}. À espera da resposta do cliente.`,
    em_disputa: x.disputa_entrega
      ? 'O cliente diz que não recebeu o dinheiro. A equipa da Bendi vai verificar — deixa a tua versão nas mensagens (ex.: quando e como entregaste).'
      : 'A equipa da Bendi está a analisar o pedido e vai decidir. Deixa a tua versão nas mensagens.',
    reembolsado: Number(x.valor_aprovado) > 0
      ? (x.metodo === 'abatido'
          ? `${formatarDinheiro(x.valor_aprovado)} descontados no valor a cobrar na entrega.`
          : `Reembolsado ${formatarDinheiro(x.valor_aprovado)}` + (x.metodo === 'manual' ? ' — pagamento em dinheiro: devolve o valor ao cliente em mão.' : (x.metodo === 'externo' ? ' — devolução confirmada pela Bendi.' : ' para o meio de pagamento do cliente.')))
      : 'Cancelamento aceite — não havia nada pago.',
    recusado: x.decisao_admin ? 'A equipa da Bendi recusou o pedido.' : 'O pedido foi recusado. O cliente ainda pode pedir à Bendi para analisar.',
    cancelado: 'O cliente desistiu do pedido.',
  }[x.estado] || ''
})

async function carregar () {
  erro.value = ''
  try {
    const { data } = await api.get(`/app/reembolsos/${props.reembolsoId}/`)
    r.value = data
    reporStock.value = data.motivo === 'mudei_ideias'
  } catch (e) {
    erro.value = e.response?.status === 404 ? 'Pedido não encontrado.' : 'Não foi possível carregar o pedido.'
  } finally { carregando.value = false }
}

function aceitar () {
  const extra = { devolver_produto: devolverProduto.value }
  if (modo.value === 'proposta') extra.valor = String(Math.round(Number(valorProposta.value)))
  acao('aceitar', extra)
}

async function acao (nome, extra = {}) {
  aEnviar.value = true
  try {
    const { data } = await api.post(`/app/loja/${props.lojaId}/reembolsos/${r.value.id}/acao/`, { acao: nome, ...extra })
    r.value = data
    aRecusar.value = false
    motivoRecusa.value = ''
    if (nome === 'tentar_reembolso' && data.estado === 'por_reembolsar') {
      toast.error('O pagamento online voltou a recusar. ' + (data.por_concluir?.proxima_tentativa ? 'Tentamos de novo sozinhos.' : 'A equipa da Bendi vai tratar disso.'))
      return
    }
    toast.success({
      reembolsado: 'Reembolso feito.', proposta: 'Proposta enviada ao cliente.', aguarda_produto: 'Aceite — à espera do produto.',
      a_devolver: data.entregue_em ? 'Registado — o cliente vai confirmar.' : (data.por_transferencia ? 'Aceite — devolve o valor por transferência.' : 'Aceite — devolve o dinheiro em mão.'),
      recusado: 'Pedido recusado.', por_reembolsar: 'Aceite — o pagamento online ainda não devolveu; tentamos de novo sozinhos.',
    }[data.estado] || 'Feito.')
    emit('alterado')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível concluir a acção.')
    carregar()
  } finally { aEnviar.value = false }
}

onMounted(carregar)
useTempoRealReembolsos(carregar, d => String(d.id) === String(props.reembolsoId))
watch(() => props.reembolsoId, () => { carregando.value = true; carregar() })
</script>
