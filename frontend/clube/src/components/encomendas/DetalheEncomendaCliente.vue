<template>
  <!-- Detalhe de uma encomenda para o cliente: gaveta do perfil (UserProfile), /encomendas e /encomendas/<id>.
       Recebe o GET /app/encomenda/<id>/; quem o usa recarrega-o (tempo real, depois de uma acção). -->
  <div class="space-y-4">
    <div>
      <p class="text-xs font-bold uppercase tracking-wider mb-2"
         :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Produtos</p>
      <div class="space-y-2">
        <div v-for="item in detalhe.itens" :key="item.id"
             class="flex items-center gap-3">
          <img v-img v-if="item.produto?.ficheiro_url" :src="$miniatura(item.produto.ficheiro_url)"
               class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
          <div v-else class="w-10 h-10 rounded-lg flex-shrink-0"
               :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
          <div class="flex-1 min-w-0">
            <p class="text-sm truncate" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ item.produto?.nome }}</p>
            <p v-if="item.componentes?.length" class="text-[11px] leading-snug" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Inclui: {{ item.componentes.map(c => (c.grupo ? c.grupo + ': ' : '') + c.quantidade + '× ' + c.nome).join(', ') }}
            </p>
            <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">x{{ item.quantidade }} · {{ formatPrice(item.preco) }} un.
              <span v-if="item.qtd_reembolsada" class="text-sky-500 font-semibold">· {{ item.qtd_reembolsada }} reembolsada{{ item.qtd_reembolsada > 1 ? 's' : '' }}</span>
            </p>
            <div v-if="temAtributos(item.atributos)" class="flex flex-wrap gap-1 mt-1">
              <span v-for="(val, key) in formatarAtributos(item.atributos)" :key="key"
                    class="px-1.5 py-0.5 text-[10px] rounded capitalize"
                    :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-gray-200 text-zinc-600'">
                {{ key }}: <span class="font-medium">{{ val }}</span>
              </span>
            </div>
          </div>
          <span class="text-sm font-bold flex-shrink-0"
                :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ formatPrice(item.subtotal) }}</span>
        </div>
      </div>
    </div>
    <div class="border-t pt-3 space-y-2"
         :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
      <div class="flex items-center justify-between text-xs">
        <span :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Tipo de entrega</span>
        <span :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
          <font-awesome-icon :icon="['fas', detalhe.e_envio ? 'box' : detalhe.tipo_entrega === 'entrega' ? 'truck' : 'store']" class="mr-1" />
          {{ detalhe.e_envio ? (detalhe.opcao_entrega_nome || 'Envio por transportadora') : detalhe.tipo_entrega === 'entrega' ? 'Entrega ao domicílio' : 'Takeaway' }}
        </span>
      </div>
      <!-- envio por transportadora: a transportadora e o código de rastreio (backend utils/envios.py) -->
      <div v-if="detalhe.envio" class="rounded-xl px-3 py-2.5 space-y-1.5 text-xs" data-teste="enc-envio"
           :class="isDark ? 'bg-sky-500/10 border border-sky-500/25' : 'bg-sky-50 border border-sky-200'">
        <p class="font-semibold" :class="isDark ? 'text-sky-200' : 'text-sky-800'">
          {{ detalhe.envio.estado === 'devolvida' ? 'A transportadora devolveu a encomenda à loja'
             : detalhe.envio.estado === 'entregue' ? 'Entregue' : 'Enviada por ' + detalhe.envio.transportadora }}
        </p>
        <div v-for="c in detalhe.envio.codigos" :key="c.codigo" class="flex items-center justify-between gap-2">
          <span :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Código de rastreio</span>
          <span class="flex items-center gap-2">
            <span class="font-mono select-all" :class="isDark ? 'text-zinc-100' : 'text-zinc-800'">{{ c.codigo }}</span>
            <a v-if="c.link" :href="c.link" target="_blank" rel="noopener noreferrer"
               class="px-2 py-0.5 rounded-md font-semibold bg-red-600 text-white hover:bg-red-500">Seguir envio</a>
          </span>
        </div>
        <p v-if="!detalhe.envio.codigos.length && detalhe.envio.estado !== 'devolvida'" data-teste="enc-sem-codigo"
           :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
          A loja não indicou código de rastreio.
          <button v-if="detalhe.envio.estado === 'a_caminho'" type="button" @click="falarSobreEncomenda"
                  class="underline font-semibold" :class="isDark ? 'text-sky-300' : 'text-sky-700'">Falar com a loja</button>
        </p>
        <p v-if="detalhe.envio.contacto" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
          Contacto da transportadora: {{ detalhe.envio.contacto }}
        </p>
        <!-- a caminho: o cliente confirma que recebeu (conclui) ou avisa a loja que não recebeu -->
        <template v-if="detalhe.envio.estado === 'a_caminho' && detalhe.status === 'enviado'">
          <p v-if="detalhe.envio.nao_recebido_em" class="pt-1" :class="isDark ? 'text-amber-300' : 'text-amber-700'" data-teste="enc-nao-recebido">
            Avisaste a loja de que não recebeste. Ela vai confirmar com a transportadora — podes falar com ela no chat da encomenda.
          </p>
          <button v-if="detalhe.envio.nao_recebido_em" type="button" @click="recebi" :disabled="aEnviarEnvio" data-teste="enc-recebi"
                  class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-40">
            <font-awesome-icon :icon="['fas', 'check']" class="mr-1" />Afinal recebi
          </button>
          <div v-else-if="envioAcao === 'nao'" class="pt-1 space-y-2">
            <input v-model="envioNota" type="text" maxlength="300" placeholder="O que se passa? (opcional)"
                   :class="['w-full px-3 py-2 rounded-lg text-xs border focus:outline-none focus:border-red-500',
                            isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100' : 'bg-white border-zinc-300 text-zinc-800']" />
            <div class="flex justify-end gap-2">
              <button type="button" @click="envioAcao = ''" class="px-3 py-1.5 rounded-lg text-xs" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Voltar</button>
              <button type="button" @click="naoRecebi" :disabled="aEnviarEnvio" data-teste="enc-nao-recebi-confirmar"
                      class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-40">Avisar a loja</button>
            </div>
          </div>
          <div v-else class="flex flex-wrap gap-2 pt-1">
            <button type="button" @click="recebi" :disabled="aEnviarEnvio" data-teste="enc-recebi"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-40">
              <font-awesome-icon :icon="['fas', 'check']" class="mr-1" />Recebi a encomenda
            </button>
            <button type="button" @click="envioAcao = 'nao'" data-teste="enc-nao-recebi"
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold" :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-200 text-zinc-700'">
              Não recebi
            </button>
          </div>
        </template>
      </div>
      <div v-if="detalhe.morada_entrega" class="flex items-start justify-between text-xs gap-2">
        <span class="flex-shrink-0" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Morada</span>
        <span class="text-right" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ detalhe.morada_entrega }}{{ detalhe.concelho_entrega ? ' · ' + nomeConcelho(detalhe.concelho_entrega) : '' }}</span>
      </div>
      <div v-if="detalhe.cliente_nif" class="flex items-start justify-between text-xs gap-2" data-teste="enc-meu-nif">
        <span class="flex-shrink-0" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Fatura com NIF</span>
        <span class="text-right" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ detalhe.cliente_nif }}</span>
      </div>
      <!-- NIF para a fatura: o cliente pode juntá-lo ou corrigi-lo a qualquer momento (a loja é avisada) -->
      <div v-if="nifEnc.aberto" class="space-y-2 pt-1" data-teste="enc-meu-nif-form">
        <input v-model="nifEnc.nif" inputmode="numeric" maxlength="11" placeholder="NIF (9 dígitos)" data-teste="enc-meu-nif-input"
          class="w-full px-3 py-2 rounded-lg text-xs border focus:outline-none focus:border-red-500"
          :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100 placeholder-zinc-600' : 'bg-gray-50 border-gray-300 text-zinc-900 placeholder-zinc-400'" />
        <input v-model="nifEnc.nome_fiscal" maxlength="200" placeholder="Nome na fatura (opcional)"
          class="w-full px-3 py-2 rounded-lg text-xs border focus:outline-none focus:border-red-500"
          :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100 placeholder-zinc-600' : 'bg-gray-50 border-gray-300 text-zinc-900 placeholder-zinc-400'" />
        <input v-model="nifEnc.morada_fiscal" maxlength="300" placeholder="Morada fiscal (opcional)"
          class="w-full px-3 py-2 rounded-lg text-xs border focus:outline-none focus:border-red-500"
          :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-100 placeholder-zinc-600' : 'bg-gray-50 border-gray-300 text-zinc-900 placeholder-zinc-400'" />
        <p v-if="detalhe.fatura" class="text-[11px]" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          A loja já registou a fatura: vamos avisá-la para a corrigir.</p>
        <p v-if="nifEnc.erro" class="text-[11px] text-red-400">{{ nifEnc.erro }}</p>
        <div class="flex gap-2">
          <button type="button" @click="guardarNifEnc" :disabled="nifEnc.aGuardar" data-teste="enc-meu-nif-guardar"
                  class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold disabled:opacity-60">
            {{ nifEnc.aGuardar ? 'A guardar…' : 'Guardar' }}</button>
          <button type="button" @click="nifEnc = { aberto: false }" class="px-3 py-1.5 rounded-lg text-xs"
                  :class="isDark ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-500 hover:text-zinc-800'">Cancelar</button>
        </div>
      </div>
      <button v-else-if="detalhe.status !== 'cancelado'" type="button" @click="abrirNifEnc"
              data-teste="enc-meu-nif-editar" class="text-xs font-semibold text-red-500 hover:text-red-400">
        {{ detalhe.cliente_nif ? 'Corrigir o NIF da fatura' : 'Adicionar NIF para a fatura' }}
      </button>
      <div v-if="detalhe.notas" class="flex items-start justify-between text-xs gap-2">
        <span class="flex-shrink-0" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Notas</span>
        <span class="text-right italic" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ detalhe.notas }}</span>
      </div>
    </div>
    <div class="border-t pt-3 flex items-center justify-between"
         :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
      <span class="text-sm font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Total</span>
      <span class="text-base font-bold text-red-500">{{ formatPrice(detalhe.valor_total) }}</span>
    </div>
    <div v-if="detalhe.valor_a_pagar && Number(detalhe.valor_a_pagar) !== Number(detalhe.valor_total)"
         class="flex items-center justify-between text-xs">
      <span :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">A pagar na entrega (sem os artigos esgotados)</span>
      <span class="font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ formatPrice(detalhe.valor_a_pagar) }}</span>
    </div>
    <!-- por pagar por transferência: o IBAN da loja, o valor e a referência -->
    <DadosTransferencia v-if="detalhe.transferencia" :dados="detalhe.transferencia" :isDark="isDark" />
    <!-- fatura que a loja emitiu no e-Fatura e registou (backend utils/fiscal.py) -->
    <div v-if="['pago', 'preparando', 'enviado', 'concluido'].includes(estadoLinha || detalhe.status)" data-teste="fatura-cliente"
         class="flex items-center justify-between gap-2 text-xs">
      <span :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Fatura</span>
      <span v-if="detalhe.fatura" class="flex items-center gap-2">
        <span class="font-semibold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ detalhe.fatura.numero }}</span>
        <a v-if="detalhe.fatura.pdf_url" :href="urlFicheiro(detalhe.fatura.pdf_url)"
           target="_blank" rel="noopener" class="font-semibold text-red-500 hover:text-red-400 underline">
          <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Descarregar
        </a>
      </span>
      <span v-else :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">A loja ainda não registou a fatura</span>
    </div>
    <!-- comprovativo do pagamento (documento interno da Bendi, também enviado por email) -->
    <div v-if="['aprovado', 'reembolsado', 'reembolsado_parcial'].includes(detalhe.pagamento_status)"
         class="flex items-center justify-between gap-2 text-xs" data-teste="comprovativo-cliente">
      <span :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Comprovativo de pagamento</span>
      <button type="button" @click="descarregarComprovativoEncomenda(detalhe.id)"
        class="font-semibold text-red-500 hover:text-red-400 underline">
        <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Descarregar
      </button>
    </div>
    <!-- chat: conversa própria desta encomenda (o condutor da entrega também a vê) -->
    <button type="button" @click="falarSobreEncomenda"
      class="w-full py-2 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-2"
      :class="isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
      <font-awesome-icon :icon="['fas', 'comment-dots']" /> Falar com a loja sobre esta encomenda
    </button>
    <!-- cancelar / pedir reembolso / acompanhar o pedido -->
    <AcoesEncomenda :encomenda="detalhe" :isDark="isDark"
      @atualizada="emit('atualizada')" @navegar="emit('navegar')" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { nomeConcelho } from '@/utils/geografia'
import { formatarAtributos, temAtributos } from '@/utils/atributos'
import { descarregarComprovativoEncomenda, urlFicheiro } from '@/utils/documentos'
import { contactarLoja } from '@/services/chat'
import { utilizadorGuardado } from '@/services/confirmarEmail'
import AcoesEncomenda from '@/components/reembolsos/AcoesEncomenda.vue'
import DadosTransferencia from '@/components/loja/DadosTransferencia.vue'

const props = defineProps({
  detalhe:     { type: Object, required: true },
  isDark:      { type: Boolean, default: true },
  // a gaveta mostra a fatura pelo estado da linha da lista (como sempre fez); as páginas usam o do detalhe
  estadoLinha: { type: String, default: '' },
})
// detalhe: o NIF mudou (dados novos da encomenda) · atualizada: cancelou/pediu reembolso → recarregar
// navegar: vai sair desta vista (a gaveta fecha-se)
const emit = defineEmits(['detalhe', 'atualizada', 'navegar'])

function formatPrice (val) { return formatarDinheiro(val || 0) }

// envio por transportadora: "Recebi" conclui a encomenda; "Não recebi" avisa a loja (backend utils/envios.py)
const envioAcao = ref('')
const envioNota = ref('')
const aEnviarEnvio = ref(false)
async function acaoEnvio (sufixo, corpo, ok) {
  if (aEnviarEnvio.value) return
  aEnviarEnvio.value = true
  try {
    await api.post(`/app/encomenda/${props.detalhe.id}/envio/${sufixo}/`, corpo)
    envioAcao.value = ''
    toast.success(ok)
    emit('atualizada')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível guardar.')
  } finally { aEnviarEnvio.value = false }
}
function recebi () {
  if (!confirm('Confirmas que recebeste a encomenda? Fica concluída.')) return
  acaoEnvio('recebi', {}, 'Obrigado! A encomenda ficou concluída.')
}
function naoRecebi () { acaoEnvio('nao-recebi', { nota: envioNota.value }, 'A loja foi avisada.') }

function falarSobreEncomenda () {
  emit('navegar')
  contactarLoja(props.detalhe.loja, { encomendaId: props.detalhe.id })
}

// NIF da fatura numa encomenda já feita (vem do perfil se a encomenda ainda não tem)
const nifEnc = ref({ aberto: false })
function abrirNifEnc () {
  const d = props.detalhe
  const c = utilizadorGuardado() || {}
  nifEnc.value = { aberto: true, nif: d.cliente_nif || c.nif || '', nome_fiscal: d.cliente_nome_fiscal || c.nome_fiscal || '',
                   morada_fiscal: d.cliente_morada_fiscal || c.morada_fiscal || '', erro: '', aGuardar: false }
}
async function guardarNifEnc () {
  const f = nifEnc.value
  const nif = (f.nif || '').replace(/\D/g, '')
  if (nif && nif.length !== 9) { f.erro = 'O NIF tem 9 dígitos.'; return }
  f.erro = ''; f.aGuardar = true
  try {
    const { data } = await api.patch(`/app/encomenda/${props.detalhe.id}/nif/`,
      { nif, nome_fiscal: f.nome_fiscal, morada_fiscal: f.morada_fiscal })
    emit('detalhe', data)
    nifEnc.value = { aberto: false }
    toast.success(nif ? 'NIF guardado. A loja foi avisada.' : 'NIF retirado.', { autoClose: 2000 })
  } catch (e) {
    f.erro = e.response?.data?.detail || 'Não foi possível guardar o NIF.'
  } finally { f.aGuardar = false }
}
</script>
