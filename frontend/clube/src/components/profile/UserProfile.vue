<template>
  <div class="text-white fixed top-6 right-[2.5vw] z-20 flex items-center gap-3">
    <NotificacaoSino />
    <font-awesome-icon :icon="['fas', 'user']" size="xl" class="cursor-pointer" @click="toggle" />

    <!-- Backdrop -->
    <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                leave-active-class="transition duration-150" leave-to-class="opacity-0">
      <div v-if="isOpen" class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" @click="toggle"></div>
    </transition>

    <!-- Drawer -->
    <transition enter-active-class="transition duration-300" enter-from-class="translate-x-full"
                leave-active-class="transition duration-200" leave-to-class="translate-x-full">
      <div v-if="isOpen"
           class="fixed top-0 right-0 w-full max-w-sm h-screen bg-zinc-950 border-l border-zinc-800
                  flex flex-col z-50 shadow-2xl overflow-hidden">

        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-zinc-800 flex-shrink-0">
          <div class="flex items-center gap-3">
            <div class="relative group/avatar cursor-pointer" @click="triggerFileSelect">
              <img :src="previewUrl" alt="avatar"
                   class="w-16 h-16 rounded-full object-cover border-2 border-zinc-700 group-hover/avatar:border-red-500 transition" />
              <div class="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover/avatar:opacity-100
                          transition flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" class="hidden" />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <p class="font-bold text-zinc-100">{{ data.username }}</p>
                <span v-if="data.verificado" class="px-1.5 py-0.5 bg-green-500/15 text-green-400 text-[10px] rounded font-bold">✓ Verificado</span>
              </div>
              <p class="text-xs text-zinc-500">{{ data.email }}</p>
            </div>
          </div>
          <button @click="toggle"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex border-b border-zinc-800 flex-shrink-0">
          <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
            :class="[
              'flex-1 py-3 text-xs font-semibold transition border-b-2',
              activeTab === tab.key
                ? 'border-red-500 text-red-400'
                : 'border-transparent text-zinc-500 hover:text-zinc-300'
            ]">
            {{ tab.label }}
          </button>
        </div>

        <!-- Conteúdo scrollável -->
        <div class="flex-1 overflow-y-auto p-5">

          <!-- ═══ TAB: DADOS PESSOAIS ═══ -->
          <div v-if="activeTab === 'dados'">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Informações pessoais</h3>
            <div class="space-y-3">
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Primeiro nome</label>
                <input v-model="form.first_name" type="text"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Apelido</label>
                <input v-model="form.last_name" type="text"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Username</label>
                <input v-model="form.username" type="text"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Email</label>
                <input v-model="form.email" type="email"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Telefone</label>
                <input v-model="form.telefone" type="text"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Morada</label>
                <input v-model="form.morada" type="text"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
            </div>
            <button @click="saveProfile" :disabled="loadingProfile"
              :class="[
                'w-full mt-5 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2',
                loadingProfile
                  ? 'bg-red-700 cursor-not-allowed opacity-70'
                  : 'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5'
              ]">
              <span v-if="loadingProfile" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                  <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
                </svg>
                A guardar…
              </span>
              <span v-else>Guardar alterações</span>
            </button>
          </div>

          <!-- ═══ TAB: PASSWORD ═══ -->
          <div v-if="activeTab === 'password'">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Alterar password</h3>
            <div class="space-y-3">
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Nova password</label>
                <input v-model="formPassword.password" type="password"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <div>
                <label class="text-xs text-zinc-500 mb-1 block">Confirmar password</label>
                <input v-model="formPassword.confirm" type="password"
                  class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-zinc-100
                         focus:outline-none focus:border-red-500 transition" />
              </div>
              <p v-if="passwordError" class="text-xs text-red-400">{{ passwordError }}</p>
            </div>
            <button @click="savePassword" :disabled="loadingPassword"
              :class="[
                'w-full mt-5 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2',
                loadingPassword
                  ? 'bg-red-700 cursor-not-allowed opacity-70'
                  : 'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5'
              ]">
              <span v-if="loadingPassword" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                  <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
                </svg>
                A guardar…
              </span>
              <span v-else>Alterar password</span>
            </button>
          </div>

          <!-- ═══ TAB: ENCOMENDAS ═══ -->
          <div v-if="activeTab === 'encomendas'">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Histórico de encomendas</h3>

            <div v-if="loadingEncomendas" class="flex justify-center py-8">
              <svg class="animate-spin h-6 w-6 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </div>

            <div v-else-if="encomendas.length === 0" class="text-center py-8 text-zinc-500 text-sm">
              Ainda não tens encomendas.
            </div>

            <div v-else class="space-y-3">
              <div v-for="enc in encomendas" :key="enc.id"
                   class="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden transition-all">

                <!-- Cabeçalho — clicável para expandir -->
                <button
                  @click="toggleEncomenda(enc.id)"
                  class="w-full flex items-center justify-between p-4 text-left hover:bg-zinc-800/50 transition"
                >
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-xs font-bold text-zinc-300">#{{ enc.id }}</span>
                      <span class="text-xs text-zinc-500">· {{ enc.loja_nome }}</span>
                    </div>
                    <div class="flex items-center gap-3">
                      <span class="text-xs text-zinc-500">{{ formatDate(enc.data_criacao) }}</span>
                      <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', statusColor(enc.status)]">
                        {{ enc.status }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-3 flex-shrink-0 ml-2">
                    <span class="text-sm font-bold text-red-400">{{ formatPrice(enc.valor_total) }}</span>
                    <svg xmlns="http://www.w3.org/2000/svg"
                         :class="['h-4 w-4 text-zinc-500 transition-transform', expandedEncomenda === enc.id ? 'rotate-180' : '']"
                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                <!-- Detalhe expandido -->
                <div v-if="expandedEncomenda === enc.id"
                     class="border-t border-zinc-800 px-4 pb-4 pt-3 space-y-4">

                  <!-- Loading detalhe -->
                  <div v-if="loadingDetalhe === enc.id" class="flex justify-center py-4">
                    <svg class="animate-spin h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                  </div>

                  <template v-else-if="detalhesEncomenda[enc.id]">
                    <!-- Produtos -->
                    <div>
                      <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Produtos</p>
                      <div class="space-y-2">
                        <div v-for="item in detalhesEncomenda[enc.id].itens" :key="item.id"
                             class="flex items-center gap-3">
                          <img v-if="item.produto?.ficheiro_url"
                               :src="item.produto.ficheiro_url" :alt="item.produto?.nome"
                               class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                          <div v-else class="w-10 h-10 rounded-lg bg-zinc-800 flex-shrink-0"></div>
                          <div class="flex-1 min-w-0">
                            <p class="text-sm text-zinc-200 truncate">{{ item.produto?.nome }}</p>
                            <p class="text-xs text-zinc-500">x{{ item.quantidade }} · {{ formatPrice(item.preco) }} un.</p>
                            <div v-if="item.atributos && Object.keys(item.atributos).length > 0"
                                 class="flex flex-wrap gap-1 mt-1">
                              <span v-for="(val, key) in item.atributos" :key="key"
                                    class="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-[10px] rounded capitalize">
                                {{ key }}: <span class="text-zinc-300 font-medium">{{ val }}</span>
                              </span>
                            </div>
                          </div>
                          <span class="text-sm font-bold text-zinc-300 flex-shrink-0">
                            {{ formatPrice(item.subtotal) }}
                          </span>
                        </div>
                      </div>
                    </div>

                    <!-- Entrega -->
                    <div class="border-t border-zinc-800 pt-3 space-y-2">
                      <div class="flex items-center justify-between text-xs">
                        <span class="text-zinc-500">Tipo de entrega</span>
                        <span class="text-zinc-300 font-medium">
                          {{ detalhesEncomenda[enc.id].tipo_entrega === 'entrega' ? '🚚 Entrega ao domicílio' : '🏪 Takeaway' }}
                        </span>
                      </div>
                      <div v-if="detalhesEncomenda[enc.id].morada_entrega"
                           class="flex items-start justify-between text-xs gap-2">
                        <span class="text-zinc-500 flex-shrink-0">Morada</span>
                        <span class="text-zinc-300 text-right">{{ detalhesEncomenda[enc.id].morada_entrega }}</span>
                      </div>
                      <div v-if="detalhesEncomenda[enc.id].notas"
                           class="flex items-start justify-between text-xs gap-2">
                        <span class="text-zinc-500 flex-shrink-0">Notas</span>
                        <span class="text-zinc-300 text-right italic">{{ detalhesEncomenda[enc.id].notas }}</span>
                      </div>
                    </div>

                    <!-- Total -->
                    <div class="border-t border-zinc-800 pt-3 flex items-center justify-between">
                      <span class="text-sm font-bold text-zinc-400">Total</span>
                      <span class="text-base font-bold text-red-400">{{ formatPrice(detalhesEncomenda[enc.id].valor_total) }}</span>
                    </div>
                  </template>
                </div>
              </div>
              <!-- Carregar mais -->
              <div class="pt-2 text-center">
                <button
                  v-if="temMais"
                  @click="carregarMais"
                  :disabled="loadingMais"
                  class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-400
                         hover:text-zinc-200 transition disabled:opacity-50 disabled:cursor-not-allowed">
                  <span v-if="loadingMais" class="flex items-center gap-2 justify-center">
                    <svg class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                      <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
                    </svg>
                    A carregar...
                  </span>
                  <span v-else>Ver mais ({{ encomendaTotal - encomendas.length }} restantes)</span>
                </button>
                <p v-else-if="encomendas.length > 0 && !temMais"
                   class="text-xs text-zinc-600">
                  Todas as encomendas carregadas
                </p>
              </div>
            </div>
          </div>

          <!-- ═══ TAB: LOJAS ═══ -->
          <div v-if="activeTab === 'lojas'">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">As minhas lojas</h3>
              <button @click="goToCreateStore"
                class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold transition">
                + Nova loja
              </button>
            </div>

            <div v-if="loadingLojas" class="flex justify-center py-8">
              <svg class="animate-spin h-6 w-6 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </div>

            <div v-else-if="lojas.length === 0" class="text-center py-8 text-zinc-500 text-sm">
              Ainda não tens lojas.<br/>
              <button @click="goToCreateStore" class="text-red-400 hover:text-red-300 mt-2 text-sm">
                Criar a primeira loja →
              </button>
            </div>

            <div v-else class="space-y-3">
              <div v-for="loja in lojas" :key="loja.id"
                   class="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden
                          hover:border-red-500/30 transition cursor-pointer group"
                   @click="goToBackoffice(loja.id)">
                <div class="flex items-center gap-3 p-3">
                  <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
                       class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                  <div v-else class="w-10 h-10 rounded-lg bg-zinc-700 flex items-center justify-center flex-shrink-0">
                    <span class="text-sm font-bold text-zinc-400">{{ loja.nome.charAt(0) }}</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-semibold text-sm text-zinc-100 truncate group-hover:text-red-400 transition">{{ loja.nome }}</p>
                    <p class="text-xs text-zinc-500">{{ loja.categoria }} · {{ loja.minha_role }}</p>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-600 group-hover:text-red-500 transition flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Footer — logout -->
        <div class="border-t border-zinc-800 p-4 flex-shrink-0">
          <button v-if="data.is_staff" @click="$router.push('/admin'); isOpen = false"
            class="w-full py-2 text-xs text-purple-400 hover:text-purple-300 transition">
            ⚙️ Painel de Admin
          </button>
          <button @click="$emit('log_out')"
            class="w-full py-2.5 rounded-xl border border-zinc-700 hover:border-red-500 hover:text-red-500
                   text-sm font-semibold text-zinc-400 transition flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Terminar sessão
          </button>
        </div>

      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'
import { toast } from 'vue3-toastify'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
})
defineEmits(['log_out'])

const router = useRouter()
const backend = process.env.VUE_APP_URL_BASE

const isOpen    = ref(false)
const fileInput = ref(null)
const previewUrl = ref('')
const activeTab  = ref('dados')

const tabs = [
  { key: 'dados',      label: 'Perfil'     },
  { key: 'password',   label: 'Password'   },
  { key: 'encomendas', label: 'Encomendas' },
  { key: 'lojas',      label: 'Lojas'      },
]

// ── Dados pessoais ────────────────────────────────────────
const form = ref({ first_name: '', last_name: '', username: '', email: '', telefone: '', morada: '' })
const { loading: loadingProfile, wrap: wrapProfile } = useAsyncAction()

// ── Password ──────────────────────────────────────────────
const formPassword = ref({ password: '', confirm: '' })
const passwordError = ref('')
const { loading: loadingPassword, wrap: wrapPassword } = useAsyncAction()

// ── Encomendas ────────────────────────────────────────────
const encomendas       = ref([])
const loadingEncomendas = ref(false)
const expandedEncomenda = ref(null)   // id da encomenda expandida
const detalhesEncomenda = ref({})     // { [id]: encomenda_completa }
const loadingDetalhe    = ref(null)   // id a carregar detalhe

// ── Lojas ─────────────────────────────────────────────────
const lojas       = ref([])
const loadingLojas = ref(false)

// ── Helpers ───────────────────────────────────────────────
function formatPrice(val) {
  return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
}
function formatDate(d) {
  return new Date(d).toLocaleDateString('pt-PT')
}
function statusColor(s) {
  const map = {
    pendente:   'bg-yellow-500/15 text-yellow-400',
    pago:       'bg-blue-500/15 text-blue-400',
    preparando: 'bg-purple-500/15 text-purple-400',
    enviado:    'bg-indigo-500/15 text-indigo-400',
    concluido:  'bg-green-500/15 text-green-400',
    cancelado:  'bg-red-500/15 text-red-400',
  }
  return map[s] || 'bg-zinc-500/15 text-zinc-400'
}

// ── Accordion encomendas ───────────────────────────────────
async function toggleEncomenda(id) {
  // fecha se já está aberto
  if (expandedEncomenda.value === id) {
    expandedEncomenda.value = null
    return
  }
  expandedEncomenda.value = id
  // só carrega o detalhe se ainda não foi carregado
  if (detalhesEncomenda.value[id]) return
  loadingDetalhe.value = id
  try {
    const { data } = await api.get(`/app/encomenda/${id}/`)
    detalhesEncomenda.value = { ...detalhesEncomenda.value, [id]: data }
  } catch (e) { console.error(e) }
  finally { loadingDetalhe.value = null }
}

// ── Toggle drawer ─────────────────────────────────────────
function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value && activeTab.value === 'encomendas') fetchEncomendas()
  if (isOpen.value && activeTab.value === 'lojas') fetchLojas()
}

watch(activeTab, (tab) => {
  if (tab === 'encomendas' && encomendas.value.length === 0) fetchEncomendas()
  if (tab === 'lojas' && lojas.value.length === 0) fetchLojas()
})

// ── Init form ─────────────────────────────────────────────
function initForm() {
  form.value = {
    first_name: props.data.first_name || '',
    last_name:  props.data.last_name  || '',
    username:   props.data.username   || '',
    email:      props.data.email      || '',
    telefone:   props.data.telefone   || '',
    morada:     props.data.morada     || '',
  }
}

onMounted(() => {
  previewUrl.value = props.data.foto || `${backend}/media/utilizadores/default.png`
  initForm()
})

watch(() => props.data, () => {
  previewUrl.value = props.data.foto || `${backend}/media/utilizadores/default.png`
  initForm()
}, { deep: true })

// ── Upload foto ───────────────────────────────────────────
function triggerFileSelect() { fileInput.value?.click() }

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  previewUrl.value = URL.createObjectURL(file)
  wrapProfile(async () => {
    const fd = new FormData()
    fd.append('foto', file)
    const res = await api.put('/app/utilizador/me/editar/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data.foto) previewUrl.value = res.data.foto
    toast.success('Foto actualizada!', { autoClose: 1500 })
  })
}

// ── Guardar perfil ────────────────────────────────────────
async function saveProfile() {
  await wrapProfile(async () => {
    const fd = new FormData()
    Object.entries(form.value).forEach(([k, v]) => { if (v) fd.append(k, v) })
    await api.put('/app/utilizador/me/editar/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    Object.assign(user, form.value)
    localStorage.setItem('user', JSON.stringify(user))
    toast.success('Perfil actualizado!', { autoClose: 1500 })
  })
}

// ── Alterar password ──────────────────────────────────────
async function savePassword() {
  passwordError.value = ''
  if (!formPassword.value.password) { passwordError.value = 'Introduz a nova password.'; return }
  if (formPassword.value.password !== formPassword.value.confirm) {
    passwordError.value = 'As passwords não coincidem.'; return
  }
  await wrapPassword(async () => {
    const fd = new FormData()
    fd.append('password', formPassword.value.password)
    await api.put('/app/utilizador/me/editar/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    formPassword.value = { password: '', confirm: '' }
    toast.success('Password alterada!', { autoClose: 1500 })
  })
}

// ── Fetch encomendas (scroll infinito) ───────────────────
const encomendaOffset  = ref(0)
const encomendaLimit   = ref(6)
const encomendaTotal   = ref(0)
const loadingMais      = ref(false)

const temMais = computed(() =>
  encomendas.value.length < encomendaTotal.value
)

async function fetchEncomendas() {
  loadingEncomendas.value = true
  encomendaOffset.value = 0
  try {
    const { data } = await api.get('/app/encomenda/', {
      params: { limit: encomendaLimit.value, offset: 0 }
    })
    encomendas.value  = data.results || data
    encomendaTotal.value = data.count ?? encomendas.value.length
    encomendaOffset.value = encomendas.value.length
  } catch (e) { console.error(e) }
  finally { loadingEncomendas.value = false }
}

async function carregarMais() {
  if (loadingMais.value || !temMais.value) return
  loadingMais.value = true
  try {
    const { data } = await api.get('/app/encomenda/', {
      params: { limit: encomendaLimit.value, offset: encomendaOffset.value }
    })
    const novas = data.results || data
    encomendas.value = [...encomendas.value, ...novas]
    encomendaOffset.value += novas.length
    encomendaTotal.value = data.count ?? encomendaTotal.value
  } catch (e) { console.error(e) }
  finally { loadingMais.value = false }
}

// ── Fetch lojas ───────────────────────────────────────────
async function fetchLojas() {
  loadingLojas.value = true
  try {
    const { data } = await api.get('/app/loja/minhas/')
    lojas.value = data.results || data
  } catch (e) { console.error(e) }
  finally { loadingLojas.value = false }
}

// ── Navegação ─────────────────────────────────────────────
function goToBackoffice(id) { router.push(`/loja/${id}/backoffice`); isOpen.value = false }
function goToCreateStore()  { router.push('/loja/criar');            isOpen.value = false }
</script>