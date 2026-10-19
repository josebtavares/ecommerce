<template>
  <!-- /perfil/reembolsos/:id — o cliente acompanha o pedido de reembolso -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b"
            :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="voltar"
              class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold truncate">{{ r ? (r.motivo === 'esgotado' ? 'Artigo esgotado' : r.tipo === 'cancelamento' ? 'Pedido de cancelamento' : 'Pedido de reembolso') : 'Pedido' }}</h1>
      <NotificacaoSino class="ml-auto" :isDark="isDark" />
      <button type="button" class="h-9 w-9 rounded-lg flex items-center justify-center"
              :aria-label="isDark ? 'Modo claro' : 'Modo escuro'" @click="alternarTema"
              :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', isDark ? 'sun' : 'moon']" />
      </button>
    </header>

    <div v-if="carregando" class="flex justify-center py-20">
      <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
    </div>
    <div v-else-if="erro" class="max-w-md mx-auto text-center py-20 px-4">
      <p class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ erro }}</p>
      <button type="button" @click="$router.push('/perfil/reembolsos')" class="mt-4 text-sm text-red-500 font-semibold">Ver os meus pedidos</button>
    </div>

    <main v-else-if="r" class="max-w-2xl mx-auto px-4 py-5 space-y-4">
      <!-- resumo -->
      <section class="rounded-2xl border p-4 space-y-3" :class="cartao">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs" :class="suave">Encomenda #{{ r.encomenda_id }} · {{ r.loja_nome }}</p>
            <p class="font-semibold">{{ r.motivo_label }}</p>
          </div>
          <EstadoReembolso :estado="r.estado" :valor="r.valor_aprovado ?? undefined" :metodo="r.metodo" />
        </div>
        <p v-if="r.descricao" class="text-sm whitespace-pre-line" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ r.descricao }}</p>
        <div class="border-t pt-3 space-y-1.5 text-sm" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <div class="flex justify-between"><span :class="suave">Valor pedido</span><span>{{ dinheiro(r.valor_pedido) }}</span></div>
          <div v-if="Number(r.valor_entrega) > 0" class="flex justify-between text-xs"><span :class="suave">inclui a taxa de entrega</span><span :class="suave">{{ dinheiro(r.valor_entrega) }}</span></div>
          <div v-if="r.estado === 'reembolsado'" class="flex justify-between font-bold">
            <span>Reembolsado</span><span class="text-green-500">{{ dinheiro(r.valor_aprovado) }}</span>
          </div>
          <p v-if="r.estado === 'reembolsado' && Number(r.valor_aprovado) > 0" class="text-xs" :class="suave">
            {{ r.metodo === 'manual' ? (r.recebido_auto ? 'Devolvido em mão pela loja — ficou confirmado sem resposta tua.' : 'Devolvido em mão pela loja — confirmaste que recebeste.')
               : r.metodo === 'abatido' ? 'Ainda não tinhas pago: o valor foi descontado do que pagas na entrega.'
               : 'Devolvido para o meio de pagamento que usaste.' }}
          </p>
          <!-- gateway: os bancos demoram; só depois disso "não recebi" -->
          <template v-if="r.estado === 'reembolsado' && r.metodo === 'gateway' && !r.nao_recebido_em">
            <button v-if="r.pode_nao_recebi && !naoRecebiAberto" type="button" @click="naoRecebiAberto = true"
              class="w-full mt-2 py-2 rounded-xl text-xs font-semibold border" :class="botaoSec">
              Não recebi o dinheiro
            </button>
            <p v-else-if="!r.pode_nao_recebi && r.nao_recebi_a_partir" class="text-[11px]" :class="suave">
              Os bancos podem demorar até 10 dias a mostrar o reembolso. Se não o vires até {{ dataHora(r.nao_recebi_a_partir) }}, podes avisar aqui.
            </p>
          </template>
        </div>
      </section>

      <!-- "não recebi" (gateway) -->
      <section v-if="naoRecebiAberto" class="rounded-2xl border p-4 space-y-2" :class="cartao">
        <textarea v-model="textoNaoRecebi" rows="3" maxlength="2000" placeholder="Conta-nos o que se passa (opcional)"
          class="w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500 resize-none"
          :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea>
        <div class="flex gap-2">
          <button type="button" @click="naoRecebiAberto = false" class="flex-1 py-2 rounded-xl text-sm border" :class="botaoSec">Voltar</button>
          <button type="button" @click="acao('nao_recebi', { texto: textoNaoRecebi })" :disabled="aEnviar"
            class="flex-1 py-2 rounded-xl text-sm font-bold text-white bg-purple-600 hover:bg-purple-500 disabled:opacity-60">
            Avisar a Bendi
          </button>
        </div>
      </section>

      <!-- o que fazer agora -->
      <section v-if="aviso" class="rounded-2xl border p-4 space-y-3"
               :class="isDark ? 'bg-zinc-900 border-amber-500/30' : 'bg-amber-50 border-amber-200'">
        <p class="text-sm" :class="isDark ? 'text-amber-100' : 'text-amber-900'">{{ aviso }}</p>
        <p v-if="r.motivo_recusa && r.estado === 'recusado'" class="text-sm rounded-xl px-3 py-2"
           :class="isDark ? 'bg-zinc-950 text-zinc-300' : 'bg-white text-zinc-700'">“{{ r.motivo_recusa }}”</p>

        <!-- dinheiro em mão: a loja diz que entregou -->
        <div v-if="r.estado === 'a_devolver' && r.entregue_em && !naoRecebiAberto" class="flex flex-col sm:flex-row gap-2">
          <button type="button" @click="acao('recebi')" :disabled="aEnviar"
            class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-60">
            Recebi {{ dinheiro(r.valor_aprovado) }}
          </button>
          <button type="button" @click="naoRecebiAberto = true" :disabled="aEnviar"
            class="flex-1 py-2.5 rounded-xl text-sm font-semibold border" :class="botaoSec">
            Não recebi
          </button>
        </div>

        <div v-if="r.estado === 'proposta'" class="flex flex-col sm:flex-row gap-2">
          <button type="button" @click="acao('aceitar_proposta')" :disabled="aEnviar"
            class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-60">
            Aceitar {{ dinheiro(r.valor_aprovado) }}
          </button>
          <button type="button" @click="escalarAberto = true" :disabled="aEnviar"
            class="flex-1 py-2.5 rounded-xl text-sm font-semibold border" :class="botaoSec">
            Não aceito — pedir ajuda à Bendi
          </button>
        </div>
        <button v-else-if="r.pode_escalar && !escalarAberto" type="button" @click="escalarAberto = true"
          class="w-full py-2.5 rounded-xl text-sm font-semibold border flex items-center justify-center gap-2" :class="botaoSec">
          <font-awesome-icon :icon="['fas', 'headset']" /> Pedir ajuda à Bendi
        </button>

        <div v-if="escalarAberto" class="space-y-2">
          <textarea v-model="textoEscalar" rows="3" maxlength="2000" placeholder="Explica à equipa da Bendi porque não concordas (opcional)"
            class="w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500 resize-none"
            :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea>
          <div class="flex gap-2">
            <button type="button" @click="escalarAberto = false" class="flex-1 py-2 rounded-xl text-sm border" :class="botaoSec">Voltar</button>
            <button type="button" @click="acao('escalar', { texto: textoEscalar })" :disabled="aEnviar"
              class="flex-1 py-2 rounded-xl text-sm font-bold text-white bg-purple-600 hover:bg-purple-500 disabled:opacity-60">
              Enviar à Bendi
            </button>
          </div>
        </div>
      </section>

      <!-- artigos -->
      <section v-if="r.itens.length" class="rounded-2xl border p-4" :class="cartao">
        <p class="text-xs font-bold uppercase tracking-wider mb-2" :class="suave">Artigos</p>
        <div v-for="i in r.itens" :key="i.item_id" class="flex justify-between gap-3 text-sm py-1">
          <span class="min-w-0 truncate">{{ i.quantidade }}× {{ i.nome }}<span v-if="textoAtributos(i.atributos)" :class="suave"> · {{ textoAtributos(i.atributos) }}</span></span>
          <span class="flex-shrink-0">{{ dinheiro(i.valor) }}</span>
        </div>
      </section>

      <!-- estado -->
      <section class="rounded-2xl border p-4" :class="cartao">
        <p class="text-xs font-bold uppercase tracking-wider mb-3" :class="suave">Estado</p>
        <ReembolsoLinhaTempo :reembolso="r" :isDark="isDark" />
      </section>

      <ReembolsoConversa :reembolso="r" meuPapel="cliente" :podeEscrever="podeEscrever" :isDark="isDark" @atualizado="r = $event" />

      <!-- pb-24: o balão do chat fica por cima do fundo da página -->
      <div class="flex flex-col sm:flex-row gap-2 pb-24">
        <button type="button" @click="falarComLoja"
          class="flex-1 py-2.5 rounded-xl text-sm border flex items-center justify-center gap-2" :class="botaoSec">
          <font-awesome-icon :icon="['fas', 'comment-dots']" /> Falar com a loja
        </button>
        <button v-if="podeDesistir && !confirmarDesistir" type="button" @click="confirmarDesistir = true"
          class="flex-1 py-2.5 rounded-xl text-sm border" :class="isDark ? 'border-zinc-700 text-zinc-400 hover:text-red-400' : 'border-gray-300 text-zinc-500 hover:text-red-500'">
          Desistir do pedido
        </button>
        <button v-if="confirmarDesistir" type="button" @click="acao('desistir')" :disabled="aEnviar"
          class="flex-1 py-2.5 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-60">
          Confirmar: desistir do pedido
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { formatarAtributos, temAtributos } from '@/utils/atributos'
import { dataHora } from '@/utils/reembolsos'
import { contactarLoja } from '@/services/chat'
import EstadoReembolso from '@/components/reembolsos/EstadoReembolso.vue'
import ReembolsoLinhaTempo from '@/components/reembolsos/ReembolsoLinhaTempo.vue'
import ReembolsoConversa from '@/components/reembolsos/ReembolsoConversa.vue'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'
import { useTempoRealReembolsos } from '@/composables/useTempoRealReembolsos'

const route  = useRoute()
const router = useRouter()

const isDark     = ref(localStorage.getItem('theme_preference') !== 'light')
const r          = ref(null)
const carregando = ref(true)
const erro       = ref('')
const aEnviar    = ref(false)
const escalarAberto = ref(false)
const textoEscalar  = ref('')
const confirmarDesistir = ref(false)
const naoRecebiAberto = ref(false)
const textoNaoRecebi  = ref('')

const cartao   = computed(() => isDark.value ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200')
const suave    = computed(() => isDark.value ? 'text-zinc-500' : 'text-zinc-500')
const botaoSec = computed(() => isDark.value ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400')

const dinheiro = v => formatarDinheiro(v || 0)
const textoAtributos = a => temAtributos(a) ? Object.values(formatarAtributos(a)).join(' · ') : ''

const podeEscrever = computed(() => ['pedido', 'proposta', 'em_disputa', 'aguarda_produto', 'a_devolver', 'recusado'].includes(r.value?.estado))
const podeDesistir = computed(() => ['pedido', 'proposta', 'em_disputa', 'aguarda_produto'].includes(r.value?.estado))

// o que o cliente tem de saber (ou fazer) agora
const aviso = computed(() => {
  const x = r.value
  if (!x) return ''
  return {
    pedido: `A loja tem até ${dataHora(x.prazo_resposta)} para responder. Se não responder, a equipa da Bendi decide.`,
    proposta: `A loja propõe reembolsar ${formatarDinheiro(x.valor_aprovado)} (pediste ${formatarDinheiro(x.valor_pedido)}).`,
    em_disputa: x.disputa_entrega
      ? 'Disseste que não recebeste o dinheiro. A equipa da Bendi está a verificar com a loja.'
      : 'A equipa da Bendi está a analisar o pedido. Podes deixar aqui mais informação ou fotos.',
    a_devolver: x.entregue_em
      ? `A loja diz que te devolveu ${formatarDinheiro(x.valor_aprovado)} em mão. Recebeste? Se não disseres nada até ${dataHora(x.prazo_resposta)}, fica confirmado.`
      : `Pagaste em dinheiro: a loja vai devolver-te ${formatarDinheiro(x.valor_aprovado)} em mão (até ${dataHora(x.prazo_resposta)}). Combina pelas mensagens.`,
    aguarda_produto: `Devolve o produto à loja ${x.loja_nome}. Combina a devolução pelas mensagens — o reembolso é feito quando a loja o receber.` +
                     (x.motivo === 'mudei_ideias' ? ' O envio de volta é por tua conta.' : ''),
    recusado: x.decisao_admin ? 'A equipa da Bendi analisou o pedido e recusou-o.'
            : (x.pode_escalar ? 'A loja recusou o pedido. Se não concordas, a equipa da Bendi pode analisá-lo.' : 'O pedido foi recusado.'),
  }[x.estado] || ''
})

async function carregar () {
  erro.value = ''
  try {
    const { data } = await api.get(`/app/reembolsos/${route.params.id}/`)
    r.value = data
  } catch (e) {
    erro.value = e.response?.status === 404 ? 'Pedido não encontrado.' : 'Não foi possível carregar o pedido.'
  } finally { carregando.value = false }
}

async function acao (nome, extra = {}) {
  aEnviar.value = true
  try {
    const { data } = await api.post(`/app/reembolsos/${r.value.id}/acao/`, { acao: nome, ...extra })
    r.value = data
    escalarAberto.value = false
    confirmarDesistir.value = false
    naoRecebiAberto.value = false
    toast.success({ aceitar_proposta: 'Proposta aceite.', escalar: 'Pedido enviado à Bendi.', desistir: 'Desististe do pedido.',
                    recebi: 'Obrigado! Reembolso fechado.', nao_recebi: 'A Bendi foi avisada.' }[nome])
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível concluir a acção.')
  } finally { aEnviar.value = false }
}

function falarComLoja () {
  contactarLoja(r.value.loja_id, { encomendaId: r.value.encomenda_id })
}

function voltar () {
  if (window.history.length > 1) router.back()
  else router.push('/perfil/reembolsos')
}

function alternarTema () {
  isDark.value = !isDark.value
  localStorage.setItem('theme_preference', isDark.value ? 'dark' : 'light')
}

// tempo real: a loja (ou a Bendi) mexeu neste pedido
useTempoRealReembolsos(() => { if (r.value) carregar() }, d => r.value && d.id === r.value.id)

// ao voltar ao separador, mostra o que mudou (resposta da loja, mensagens)
function aoFocar () { if (document.visibilityState === 'visible' && r.value) carregar() }
onMounted(() => { carregar(); document.addEventListener('visibilitychange', aoFocar) })
onBeforeUnmount(() => document.removeEventListener('visibilitychange', aoFocar))
watch(() => route.params.id, id => { if (id) { carregando.value = true; carregar() } })
</script>
