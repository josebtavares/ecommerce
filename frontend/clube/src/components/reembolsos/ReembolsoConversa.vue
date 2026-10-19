<template>
  <!-- Mensagens do pedido de reembolso (cliente, loja e, em disputa, a Bendi) — separadas do chat privado -->
  <div class="rounded-2xl border" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
    <p class="px-4 pt-4 pb-2 text-xs font-bold uppercase tracking-wider" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
      Mensagens
    </p>

    <!-- paginadas como o chat: aparecem as últimas; ao subir até ao topo vêm as anteriores -->
    <div ref="caixa" class="px-4 pb-3 space-y-3 max-h-[28rem] overflow-y-auto" @scroll="aoRolar">
      <div v-if="maisAntigas" class="text-center">
        <button type="button" @click="carregarAntigas" :disabled="aCarregar" class="text-xs underline"
                :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          {{ aCarregar ? 'A carregar…' : 'Ver mensagens anteriores' }}
        </button>
      </div>
      <div v-for="m in lista" :key="m.id"
           :class="['flex', m.papel === 'sistema' ? 'justify-center' : (m.papel === meuPapel ? 'justify-end' : 'justify-start')]">
        <p v-if="m.papel === 'sistema'" class="text-[11px] text-center max-w-[90%] px-3 py-1.5 rounded-full"
           :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-gray-100 text-zinc-500'">
          {{ m.texto }}
        </p>
        <div v-else class="max-w-[85%] rounded-2xl px-3 py-2"
             :class="m.papel === meuPapel
               ? 'bg-red-600 text-white rounded-br-sm'
               : (m.papel === 'admin'
                   ? (isDark ? 'bg-purple-500/15 text-purple-100 border border-purple-500/30' : 'bg-purple-50 text-purple-900 border border-purple-200')
                   : (isDark ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-100 text-zinc-800')) + ' rounded-bl-sm'">
          <p class="text-[10px] font-bold mb-0.5 opacity-75">
            {{ m.papel === meuPapel ? 'Tu' : m.autor }}{{ m.papel === 'admin' ? ' · equipa' : '' }} · {{ dataHora(m.criada_em) }}
          </p>
          <p v-if="m.texto" class="text-sm whitespace-pre-line break-words">{{ m.texto }}</p>
          <div v-if="m.fotos.length" class="flex flex-wrap gap-1.5 mt-1.5">
            <button v-for="f in m.fotos" :key="f.id" type="button" @click="lightbox = f.url"
                    class="h-16 w-16 rounded-lg overflow-hidden bg-black/20">
              <img :src="f.url" alt="Foto do pedido" loading="lazy" class="h-full w-full object-cover" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- escrever -->
    <div v-if="podeEscrever" class="border-t p-3 space-y-2" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
      <div v-if="fotos.length" class="flex flex-wrap gap-1.5">
        <div v-for="(f, i) in fotos" :key="f.url" class="relative h-14 w-14 rounded-lg overflow-hidden">
          <img :src="f.url" alt="" class="h-full w-full object-cover" />
          <button type="button" @click="tirarFoto(i)" aria-label="Remover foto"
                  class="absolute top-0.5 right-0.5 h-5 w-5 rounded-full bg-black/70 text-white text-[10px]">
            <font-awesome-icon :icon="['fas', 'xmark']" />
          </button>
        </div>
      </div>
      <div class="flex items-end gap-2">
        <label class="h-10 w-10 flex-shrink-0 rounded-xl flex items-center justify-center cursor-pointer transition"
               :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-gray-100 hover:bg-gray-200 text-zinc-600'"
               title="Juntar fotos">
          <font-awesome-icon :icon="['fas', 'camera']" />
          <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple class="hidden" @change="juntarFotos" />
        </label>
        <textarea v-model="texto" rows="1" maxlength="2000" placeholder="Escreve uma mensagem…"
          @keydown.enter.exact.prevent="enviar"
          class="flex-1 min-w-0 px-3 py-2.5 rounded-xl text-sm border focus:outline-none focus:border-red-500 resize-none"
          :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-gray-50 border-gray-300 text-zinc-900'"></textarea>
        <button type="button" @click="enviar" :disabled="aEnviar || (!texto.trim() && !fotos.length)" aria-label="Enviar"
                class="h-10 w-10 flex-shrink-0 rounded-xl bg-red-600 hover:bg-red-500 text-white transition disabled:opacity-40">
          <font-awesome-icon :icon="['fas', aEnviar ? 'spinner' : 'paper-plane']" :spin="aEnviar" />
        </button>
      </div>
    </div>

    <!-- foto em grande -->
    <div v-if="lightbox" class="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4" @click="lightbox = null">
      <img :src="lightbox" alt="Foto do pedido" class="max-h-full max-w-full rounded-xl" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { dataHora } from '@/utils/reembolsos'

const MAX_FOTOS = 10

const props = defineProps({
  reembolso:    { type: Object, required: true },
  meuPapel:     { type: String, default: 'cliente' },   // 'cliente' | 'loja' | 'admin'
  podeEscrever: { type: Boolean, default: true },
  isDark:       { type: Boolean, default: true },
})
const emit = defineEmits(['atualizado'])

const texto    = ref('')
const caixa    = ref(null)
const lista    = ref([...(props.reembolso.mensagens || [])])   // mensagens carregadas (as mais recentes no fim)
const maisAntigas = ref(!!props.reembolso.mensagens_mais_antigas)
const aCarregar = ref(false)

function pertoDoFim () {
  const el = caixa.value
  return !el || el.scrollHeight - el.scrollTop - el.clientHeight < 120
}
function irParaOFim () {
  nextTick(() => { if (caixa.value) caixa.value.scrollTop = caixa.value.scrollHeight })
}
onMounted(irParaOFim)

// o pedido foi recarregado (acção, mensagem enviada ou aviso em tempo real): junta as mensagens novas
watch(() => props.reembolso, (novo, antigo) => {
  if (!antigo || novo.id !== antigo.id) {
    lista.value = [...(novo.mensagens || [])]
    maisAntigas.value = !!novo.mensagens_mais_antigas
    irParaOFim()
    return
  }
  const ultima = lista.value.length ? lista.value[lista.value.length - 1].id : 0
  const novas = (novo.mensagens || []).filter(m => m.id > ultima)
  if (!novas.length) return
  const descer = pertoDoFim()
  lista.value = [...lista.value, ...novas]
  if (descer) irParaOFim()
})

function aoRolar () {
  if (caixa.value && caixa.value.scrollTop < 40 && maisAntigas.value && !aCarregar.value) carregarAntigas()
}

async function carregarAntigas () {
  if (!lista.value.length) return
  aCarregar.value = true
  const el = caixa.value
  const alturaAntes = el ? el.scrollHeight : 0
  try {
    const { data } = await api.get(`/app/reembolsos/${props.reembolso.id}/mensagens/`, { params: { antes: lista.value[0].id } })
    lista.value = [...data.results, ...lista.value]
    maisAntigas.value = data.mais_antigas
    nextTick(() => { if (el) el.scrollTop = el.scrollHeight - alturaAntes })   // não salta
  } catch (e) {
    toast.error('Não foi possível carregar as mensagens anteriores.')
  } finally { aCarregar.value = false }
}
const fotos    = ref([])      // [{ ficheiro, url }]
const aEnviar  = ref(false)
const lightbox = ref(null)

function totalFotos () {
  return props.reembolso.total_fotos ?? 0
}

function juntarFotos (ev) {
  const novos = [...ev.target.files]
  ev.target.value = ''
  if (totalFotos() + fotos.value.length + novos.length > MAX_FOTOS) {
    toast.error(`Máximo de ${MAX_FOTOS} fotos por pedido.`)
    return
  }
  for (const f of novos) {
    if (f.size > 10 * 1024 * 1024) { toast.error('Cada foto pode ter até 10 MB.'); continue }
    fotos.value.push({ ficheiro: f, url: URL.createObjectURL(f) })
  }
}

function tirarFoto (i) {
  URL.revokeObjectURL(fotos.value[i].url)
  fotos.value.splice(i, 1)
}

async function enviar () {
  if (aEnviar.value || (!texto.value.trim() && !fotos.value.length)) return
  aEnviar.value = true
  try {
    const fd = new FormData()
    fd.append('texto', texto.value.trim())
    fotos.value.forEach(f => fd.append('fotos', f.ficheiro))
    const { data } = await api.post(`/app/reembolsos/${props.reembolso.id}/mensagens/`, fd,
                                    { headers: { 'Content-Type': 'multipart/form-data' } })
    texto.value = ''
    fotos.value.forEach(f => URL.revokeObjectURL(f.url))
    fotos.value = []
    emit('atualizado', data)
    irParaOFim()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível enviar a mensagem.')
  } finally { aEnviar.value = false }
}

onBeforeUnmount(() => fotos.value.forEach(f => URL.revokeObjectURL(f.url)))
</script>
