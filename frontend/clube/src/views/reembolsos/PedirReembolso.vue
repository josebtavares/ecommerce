<template>
  <!-- /encomenda/:id/reembolso — pedir reembolso/devolução de uma encomenda já recebida -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b"
            :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="voltar"
              class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold truncate">Pedir reembolso</h1>
    </header>

    <div v-if="carregando" class="flex justify-center py-20">
      <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" />
    </div>
    <div v-else-if="bloqueio" class="max-w-md mx-auto text-center py-20 px-4">
      <p class="text-sm" :class="suave">{{ bloqueio }}</p>
      <button type="button" @click="voltar" class="mt-4 text-sm text-red-500 font-semibold">Voltar</button>
    </div>

    <main v-else class="max-w-2xl mx-auto px-4 py-5 space-y-4 pb-28">
      <p class="text-sm" :class="suave">Encomenda #{{ enc.id }} · {{ enc.loja_nome }} · {{ dinheiro(enc.valor_total) }}</p>

      <!-- 1. motivo -->
      <section class="rounded-2xl border p-4 space-y-2" :class="cartao">
        <p class="text-xs font-bold uppercase tracking-wider" :class="suave">O que aconteceu?</p>
        <label v-for="m in op.motivos" :key="m.valor"
          class="flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition"
          :class="motivo === m.valor
            ? 'border-red-500 bg-red-500/5'
            : (isDark ? 'border-zinc-800 hover:border-zinc-600' : 'border-gray-200 hover:border-gray-300')">
          <input type="radio" name="motivo" :value="m.valor" v-model="motivo" class="mt-1 accent-red-600" />
          <span class="min-w-0">
            <span class="block text-sm font-semibold">{{ MOTIVOS[m.valor]?.label || m.label }}</span>
            <span class="block text-xs" :class="suave">{{ MOTIVOS[m.valor]?.ajuda }}</span>
          </span>
        </label>
        <p class="text-[11px] pt-1" :class="suave">
          <template v-if="op.prazo_problema">Problemas com a encomenda: até {{ dataHora(op.prazo_problema) }}.</template>
          <template v-if="op.prazo_devolucao"> Devoluções por mudança de ideias: até {{ dataHora(op.prazo_devolucao) }}.</template>
          <template v-if="!op.loja_aceita_devolucoes"> Esta loja não aceita devoluções por mudança de ideias.</template>
        </p>
      </section>

      <!-- 2. artigos -->
      <section v-if="motivo && motivo !== 'nao_chegou'" class="rounded-2xl border p-4 space-y-2" :class="cartao">
        <p class="text-xs font-bold uppercase tracking-wider" :class="suave">Que artigos?</p>
        <div v-for="i in op.itens" :key="i.id" class="flex items-center gap-3 py-1.5"
             :class="!i.disponivel && 'opacity-50'">
          <input type="checkbox" :disabled="!i.disponivel" :checked="qtd[i.id] > 0"
                 @change="qtd[i.id] = $event.target.checked ? i.disponivel : 0" class="accent-red-600 h-4 w-4" />
          <img v-img v-if="imagem(i.id)" :src="$miniatura(imagem(i.id))" alt="" class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-sm truncate">{{ i.nome }}</p>
            <p class="text-xs" :class="suave">
              {{ dinheiro(i.preco) }} un.<span v-if="textoAtributos(i.atributos)"> · {{ textoAtributos(i.atributos) }}</span>
              <span v-if="!i.disponivel"> · já pedido</span>
            </p>
          </div>
          <div v-if="i.disponivel > 1 && qtd[i.id] > 0" class="flex items-center gap-1 flex-shrink-0">
            <button type="button" @click="qtd[i.id] = Math.max(1, qtd[i.id] - 1)" aria-label="Menos"
                    class="h-7 w-7 rounded-lg" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'">−</button>
            <span class="w-6 text-center text-sm">{{ qtd[i.id] }}</span>
            <button type="button" @click="qtd[i.id] = Math.min(i.disponivel, qtd[i.id] + 1)" aria-label="Mais"
                    class="h-7 w-7 rounded-lg" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'">+</button>
          </div>
          <span v-else-if="qtd[i.id] > 0" class="text-xs flex-shrink-0" :class="suave">{{ qtd[i.id] }}×</span>
        </div>
      </section>
      <section v-else-if="motivo === 'nao_chegou'" class="rounded-2xl border p-4 text-sm" :class="cartao">
        O pedido é de toda a encomenda, com a taxa de entrega.
      </section>

      <!-- 3. descrição e fotos -->
      <section v-if="motivo" class="rounded-2xl border p-4 space-y-3" :class="cartao">
        <p class="text-xs font-bold uppercase tracking-wider" :class="suave">
          {{ problema ? 'Descreve o problema' : 'Queres dizer alguma coisa à loja?' }}
        </p>
        <textarea v-model="descricao" rows="4" maxlength="2000"
          :placeholder="problema ? 'Ex.: a camisola veio com um rasgão na manga.' : 'Opcional'"
          class="w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500 resize-none"
          :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-gray-50 border-gray-300 text-zinc-900'"></textarea>
        <div>
          <div class="flex flex-wrap gap-2">
            <div v-for="(f, idx) in fotos" :key="f.url" class="relative h-20 w-20 rounded-xl overflow-hidden">
              <img :src="f.url" alt="" class="h-full w-full object-cover" />
              <button type="button" @click="tirarFoto(idx)" aria-label="Remover foto"
                      class="absolute top-1 right-1 h-6 w-6 rounded-full bg-black/70 text-white text-xs">
                <font-awesome-icon :icon="['fas', 'xmark']" />
              </button>
            </div>
            <label v-if="fotos.length < MAX_FOTOS"
              class="h-20 w-20 rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-1 cursor-pointer text-xs transition"
              :class="isDark ? 'border-zinc-700 text-zinc-400 hover:border-zinc-500' : 'border-gray-300 text-zinc-500 hover:border-gray-400'">
              <font-awesome-icon :icon="['fas', 'camera']" class="text-base" />
              Foto
              <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple class="hidden" @change="juntarFotos" />
            </label>
          </div>
          <p class="text-[11px] mt-1.5" :class="suave">
            {{ ['defeito', 'errado', 'em_falta'].includes(motivo) ? 'As fotos ajudam a loja (e a Bendi) a decidir mais depressa.' : 'Fotos opcionais.' }}
            Até {{ MAX_FOTOS }}.
          </p>
        </div>
      </section>

      <details v-if="op.politica_devolucao" class="rounded-2xl border p-4 text-sm" :class="cartao">
        <summary class="cursor-pointer font-semibold">Política de devolução da loja</summary>
        <p class="mt-2 whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ op.politica_devolucao }}</p>
      </details>
    </main>

    <!-- resumo e envio -->
    <footer v-if="!carregando && !bloqueio && motivo" class="fixed bottom-0 inset-x-0 border-t"
            :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <div class="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
        <div class="flex-1 min-w-0">
          <p class="text-xs" :class="suave">Valor a pedir{{ incluiEntrega ? ' (com a entrega)' : '' }}</p>
          <p class="font-bold text-lg">{{ dinheiro(estimativa) }}</p>
        </div>
        <button type="button" @click="enviar" :disabled="!podeEnviar || aEnviar"
          class="px-5 py-3 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500 transition disabled:opacity-40">
          {{ aEnviar ? 'A enviar…' : 'Enviar pedido' }}
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { formatarAtributos, temAtributos } from '@/utils/atributos'
import { MOTIVOS, MOTIVOS_PROBLEMA, dataHora } from '@/utils/reembolsos'
import { temaEscuro } from '@/utils/tema'

const MAX_FOTOS = 10

const route  = useRoute()
const router = useRouter()
const isDark = ref(temaEscuro())

const enc        = ref(null)
const op         = ref(null)
const carregando = ref(true)
const bloqueio   = ref('')
const motivo     = ref('')
const descricao  = ref('')
const qtd        = reactive({})          // item_id → unidades pedidas
const fotos      = ref([])               // [{ ficheiro, url }]
const aEnviar    = ref(false)

const cartao = computed(() => isDark.value ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200')
const suave  = computed(() => isDark.value ? 'text-zinc-500' : 'text-zinc-500')
const dinheiro = v => formatarDinheiro(v || 0)
const textoAtributos = a => temAtributos(a) ? Object.values(formatarAtributos(a)).join(' · ') : ''
const problema = computed(() => MOTIVOS_PROBLEMA.includes(motivo.value))

function imagem (itemId) {
  return enc.value?.itens?.find(i => i.id === itemId)?.produto?.ficheiro_url || null
}

const disponiveis = computed(() => (op.value?.itens || []).filter(i => i.disponivel > 0))
const todos = computed(() => motivo.value === 'nao_chegou' || disponiveis.value.every(i => qtd[i.id] === i.disponivel))
const incluiEntrega = computed(() => problema.value && todos.value && Number(op.value?.valor_entrega) > 0)

// estimativa (o servidor faz a conta final — p.ex. se a entrega já foi reembolsada noutro pedido)
const estimativa = computed(() => {
  if (!op.value) return 0
  const itens = motivo.value === 'nao_chegou'
    ? disponiveis.value.reduce((s, i) => s + Number(i.preco) * i.disponivel, 0)
    : disponiveis.value.reduce((s, i) => s + Number(i.preco) * (qtd[i.id] || 0), 0)
  return Math.min(itens + (incluiEntrega.value ? Number(op.value.valor_entrega) : 0), Number(op.value.reembolsavel))
})

const podeEnviar = computed(() => {
  if (!motivo.value) return false
  if (problema.value && descricao.value.trim().length < 5) return false
  return motivo.value === 'nao_chegou' || disponiveis.value.some(i => qtd[i.id] > 0)
})

async function carregar () {
  const id = route.params.id
  try {
    const [d, o] = await Promise.all([api.get(`/app/encomenda/${id}/`), api.get(`/app/encomendas/${id}/reembolso/opcoes/`)])
    enc.value = d.data
    op.value  = o.data
    if (o.data.reembolso_ativo) { router.replace(`/perfil/reembolsos/${o.data.reembolso_ativo}`); return }
    if (!o.data.motivos.length) {
      bloqueio.value = enc.value.status !== 'concluido'
        ? 'Só podes pedir reembolso depois de receberes a encomenda. Antes disso, podes cancelá-la no teu perfil.'
        : Number(o.data.reembolsavel) <= 0 ? 'Esta encomenda já foi totalmente reembolsada.'
        : 'O prazo para pedir reembolso desta encomenda já terminou.'
    }
    o.data.itens.forEach(i => { qtd[i.id] = 0 })
  } catch (e) {
    bloqueio.value = e.response?.status === 403 || e.response?.status === 404 ? 'Encomenda não encontrada.' : 'Não foi possível carregar a encomenda.'
  } finally { carregando.value = false }
}

function juntarFotos (ev) {
  const novos = [...ev.target.files]
  ev.target.value = ''
  for (const f of novos) {
    if (fotos.value.length >= MAX_FOTOS) { toast.error(`Máximo de ${MAX_FOTOS} fotos.`); break }
    if (f.size > 10 * 1024 * 1024) { toast.error('Cada foto pode ter até 10 MB.'); continue }
    fotos.value.push({ ficheiro: f, url: URL.createObjectURL(f) })
  }
}

function tirarFoto (i) {
  URL.revokeObjectURL(fotos.value[i].url)
  fotos.value.splice(i, 1)
}

async function enviar () {
  if (!podeEnviar.value) {
    if (problema.value && descricao.value.trim().length < 5) toast.error('Descreve o problema.')
    return
  }
  aEnviar.value = true
  try {
    const fd = new FormData()
    fd.append('motivo', motivo.value)
    fd.append('descricao', descricao.value.trim())
    const itens = motivo.value === 'nao_chegou' ? []
      : Object.entries(qtd).filter(([, q]) => q > 0).map(([id, q]) => ({ item_id: Number(id), quantidade: q }))
    fd.append('itens', JSON.stringify(itens))
    fotos.value.forEach(f => fd.append('fotos', f.ficheiro))
    const { data } = await api.post(`/app/encomendas/${enc.value.id}/reembolsos/`, fd,
                                    { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.success('Pedido enviado à loja.')
    router.replace(`/perfil/reembolsos/${data.id}`)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Não foi possível enviar o pedido.')
  } finally { aEnviar.value = false }
}

function voltar () {
  if (window.history.length > 1) router.back()
  else router.push({ path: '/Home', query: { perfil: 'encomendas' } })
}

onMounted(carregar)
onBeforeUnmount(() => fotos.value.forEach(f => URL.revokeObjectURL(f.url)))
</script>
