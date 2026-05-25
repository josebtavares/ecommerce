<template>
  <div class="min-h-screen bg-slate-100">
    <!-- Header -->
    <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-xl">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
        <div class="flex min-w-0 items-center gap-3">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-lg font-black text-white shadow-lg">
            P
          </div>

          <div class="min-w-0">
            <h1 class="truncate text-lg font-black text-slate-950 sm:text-xl">
              {{ posNome || 'POS Bendi' }}
            </h1>
            <p class="truncate text-xs font-semibold text-slate-500 sm:text-sm">
              {{ posCodigo || 'Sistema POS' }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-4">
          <div class="hidden items-center gap-2 sm:flex">
            <div class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-black text-slate-700">
              {{ userInitial }}
            </div>

            <span class="max-w-[140px] truncate text-sm font-bold text-slate-700">
              {{ userName }}
            </span>
          </div>

          <button
            type="button"
            @click="abrirConfiguracao"
            class="rounded-2xl p-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
            title="Configurar POS"
            :disabled="!posId"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </button>

          <button
            type="button"
            @click="logout"
            class="rounded-2xl p-2 text-red-600 transition hover:bg-red-50"
            title="Sair"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Navegação -->
    <nav
      v-if="posId"
      class="sticky top-[73px] z-30 border-b border-slate-200 bg-white/90 backdrop-blur-xl"
    >
      <div class="mx-auto max-w-7xl px-4">
        <div class="flex gap-2 overflow-x-auto py-3 scrollbar-hide">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            @click="activeTab = tab.id"
            :class="[
              'flex shrink-0 items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-black transition',
              activeTab === tab.id
                ? 'bg-slate-950 text-white shadow-lg shadow-slate-950/15'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-950'
            ]"
          >
            <span>{{ tab.icon }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- Conteúdo -->
    <main class="mx-auto max-w-7xl p-4 sm:p-6">
      <!-- Barra de estado do POS -->
      <section
        v-if="posId"
        class="mb-5 rounded-[2rem] border border-slate-200 bg-white p-4 shadow-sm"
      >
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div
              :class="[
                'inline-flex w-fit items-center rounded-2xl px-4 py-2 text-sm font-black',
                modoBadgeClass
              ]"
            >
              {{ modoLabel }}
            </div>

            <div class="min-w-0">
              <p class="text-sm font-black text-slate-950">
                {{ modoDescription }}
              </p>

              <p class="mt-1 truncate text-xs font-semibold text-slate-500">
                <span v-if="lojaVinculada">
                  Loja vinculada: {{ lojaVinculada.nome }}
                </span>
                <span v-else>
                  Nenhuma loja vinculada. Este POS trabalha apenas com produtos próprios.
                </span>
              </p>
            </div>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              @click="abrirConfiguracao"
              class="h-10 rounded-2xl bg-slate-950 px-4 text-sm font-black text-white transition hover:bg-slate-800"
            >
              Configurar POS
            </button>

            <button
              v-if="lojaVinculada"
              type="button"
              @click="desconectarLoja"
              :disabled="savingConfig"
              class="h-10 rounded-2xl bg-red-50 px-4 text-sm font-black text-red-700 transition hover:bg-red-100 disabled:opacity-60"
            >
              Desconectar loja
            </button>
          </div>
        </div>
      </section>

      <!-- Área principal -->
      <section
        v-if="posId"
        class="rounded-[2rem] border border-slate-200 bg-white p-3 shadow-sm sm:p-5"
      >
        <component
          :is="currentTabComponent"
          :key="`${currentTabComponent}-${posId}-${componentRefreshKey}`"
          :pos-id="posId"
        />
      </section>

      <!-- Loading -->
      <section
        v-else-if="!posLoaded"
        class="rounded-[2rem] border border-slate-200 bg-white p-10 text-center shadow-sm"
      >
        <div class="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
        <p class="font-bold text-slate-600">A carregar dados do POS...</p>
      </section>

      <!-- Fallback caso o onboarding seja fechado/ignorado -->
      <section
        v-else
        class="rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-12"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-3xl">
          🧾
        </div>

        <h2 class="mt-5 text-2xl font-black text-slate-950">
          Configura o teu primeiro POS
        </h2>

        <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
          Escolhe se queres usar o POS sozinho ou integrado com uma loja Bendi.
        </p>

        <div class="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <button
            type="button"
            @click="abrirOnboarding"
            class="inline-flex h-12 items-center justify-center rounded-2xl bg-slate-950 px-6 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
          >
            Escolher configuração
          </button>

          <button
            type="button"
            @click="criarPOS"
            :disabled="creatingPos"
            class="inline-flex h-12 items-center justify-center rounded-2xl bg-slate-100 px-6 text-sm font-black text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span v-if="!creatingPos">Criar standalone rápido</span>
            <span v-else class="flex items-center gap-2">
              <span class="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-slate-900"></span>
              A criar...
            </span>
          </button>
        </div>
      </section>
    </main>

    <!-- Onboarding -->
    <OnboardingModal
      v-if="showOnboardingModal"
      :lojas="lojas"
      :onboarding-data="onboardingData"
      :loading="creatingPos"
      @completed="handleOnboardingCompleted"
      @create-pos="handleOnboardingCreatePOS"
      @close="handleOnboardingClose"
    />

    <!-- Modal Configuração - BOTTOM SHEET MOBILE -->
    <div
      v-if="showConfigModal"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharConfiguracao"
    >
      <div class="w-full max-w-2xl overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-white p-5">
          <div>
            <h3 class="text-xl font-black text-slate-950">
              Configuração do POS
            </h3>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              Define se o POS trabalha sozinho, com loja Bendi ou em modo híbrido.
            </p>
          </div>

          <button
            type="button"
            @click="fecharConfiguracao"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </header>

        <form class="max-h-[65vh] space-y-5 overflow-y-auto p-5 sm:max-h-none" @submit.prevent="guardarConfiguracao">
          <div
            v-if="configError"
            class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
          >
            {{ configError }}
          </div>

          <div
            v-if="configSuccess"
            class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
          >
            {{ configSuccess }}
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Nome do POS
            </label>

            <input
              v-model.trim="configForm.nome"
              type="text"
              placeholder="Ex: POS Principal"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Loja Bendi
            </label>

            <select
              v-model="configForm.loja_id"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            >
              <option value="">Sem loja vinculada</option>
              <option
                v-for="loja in lojas"
                :key="loja.id"
                :value="loja.id"
              >
                {{ loja.nome }}
              </option>
            </select>

            <p class="mt-2 text-xs font-semibold text-slate-400">
              As lojas vêm do login POS. Se criaste uma loja agora, faz logout/login para atualizar a lista.
            </p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Modo de operação
            </label>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label
                v-for="modoOption in modoOptions"
                :key="modoOption.value"
                :class="[
                  'cursor-pointer rounded-[1.25rem] border-2 p-4 transition',
                  configForm.modo === modoOption.value
                    ? 'border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-950/15'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                ]"
              >
                <input
                  v-model="configForm.modo"
                  type="radio"
                  :value="modoOption.value"
                  class="hidden"
                />

                <p class="text-sm font-black">
                  {{ modoOption.label }}
                </p>

                <p
                  :class="[
                    'mt-2 text-xs font-semibold leading-5',
                    configForm.modo === modoOption.value ? 'text-slate-300' : 'text-slate-500'
                  ]"
                >
                  {{ modoOption.description }}
                </p>
              </label>
            </div>
          </div>
        </form>

        <div class="grid grid-cols-2 gap-3 border-t border-slate-200 bg-slate-50 p-5">
          <button
            type="button"
            @click="fecharConfiguracao"
            class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
          >
            Cancelar
          </button>

          <button
            type="button"
            @click="guardarConfiguracao"
            :disabled="savingConfig"
            class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span v-if="!savingConfig">Guardar</span>
            <span v-else class="flex items-center gap-2">
              <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
              A guardar...
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

import POSMesas from './POSMesas.vue'
import POSPedidos from './POSPedidos.vue'
import POSHistorico from './POSHistorico.vue'
import POSProdutos from './POSProdutos.vue'
import OnboardingModal from './components/OnboardingModal.vue'

export default {
  name: 'POSDashboard',

  components: {
    POSMesas,
    POSPedidos,
    POSHistorico,
    POSProdutos,
    OnboardingModal
  },

  data() {
    return {
      activeTab: 'mesas',

      posId: null,
      posNome: '',
      posCodigo: '',
      modo: 'standalone',
      lojaVinculada: null,
      currentPOS: null,

      userName: '',
      userInitial: '',

      posLoaded: false,
      creatingPos: false,
      savingConfig: false,

      lojas: [],
      onboardingData: null,
      showOnboardingModal: false,

      showConfigModal: false,
      configError: '',
      configSuccess: '',

      componentRefreshKey: 0,

      configForm: {
        nome: '',
        loja_id: '',
        modo: 'standalone'
      },

      tabs: [
        { id: 'mesas', label: 'Mesas', icon: '🍽️' },
        { id: 'pedidos', label: 'Pedidos', icon: '🛒' },
        { id: 'produtos', label: 'Produtos', icon: '📦' },
        { id: 'historico', label: 'Histórico', icon: '📜' }
      ],

      modoOptions: [
        {
          value: 'standalone',
          label: 'Standalone',
          description: 'Usa apenas produtos próprios do POS.'
        },
        {
          value: 'integrado',
          label: 'Integrado',
          description: 'Usa apenas produtos da loja Bendi.'
        },
        {
          value: 'hibrido',
          label: 'Híbrido',
          description: 'Usa produtos próprios e produtos da loja.'
        }
      ]
    }
  },

  computed: {
    currentTabComponent() {
      const componentMap = {
        mesas: 'POSMesas',
        pedidos: 'POSPedidos',
        produtos: 'POSProdutos',
        historico: 'POSHistorico'
      }

      return componentMap[this.activeTab] || 'POSMesas'
    },

    modoLabel() {
      const labels = {
        standalone: 'Standalone',
        integrado: 'Integrado',
        hibrido: 'Híbrido'
      }

      return labels[this.modo] || 'Standalone'
    },

    modoDescription() {
      if (this.modo === 'integrado') {
        return 'O POS usa apenas produtos da loja Bendi vinculada.'
      }

      if (this.modo === 'hibrido') {
        return 'O POS usa produtos próprios e produtos da loja Bendi.'
      }

      return 'O POS usa apenas produtos próprios, sem depender de uma loja.'
    },

    modoBadgeClass() {
      const classes = {
        standalone: 'bg-purple-50 text-purple-700',
        integrado: 'bg-blue-50 text-blue-700',
        hibrido: 'bg-emerald-50 text-emerald-700'
      }

      return classes[this.modo] || classes.standalone
    }
  },

  async created() {
    this.loadUserData()
    this.loadLojasFromStorage()
    this.loadOnboardingData()
    await this.loadPOSData()
  },

  methods: {
    loadUserData() {
      const user = JSON.parse(localStorage.getItem('user') || '{}')

      this.userName = user.nome || user.first_name || user.username || 'Utilizador'
      this.userInitial = this.userName.charAt(0).toUpperCase()
    },

    loadLojasFromStorage() {
      try {
        this.lojas = JSON.parse(localStorage.getItem('pos_lojas') || '[]')
      } catch {
        this.lojas = []
      }
    },

    loadOnboardingData() {
      try {
        this.onboardingData = JSON.parse(localStorage.getItem('pos_onboarding_data') || 'null')
      } catch {
        this.onboardingData = null
      }
    },

    shouldShowOnboarding() {
      const precisaOnboarding = localStorage.getItem('pos_precisa_onboarding') === 'true'
      const posSelecionado = localStorage.getItem('pos_selected')
      const posId = localStorage.getItem('pos_id')

      return precisaOnboarding && !posSelecionado && !posId
    },

    async loadPOSData() {
      try {
        const posSelecionado = JSON.parse(localStorage.getItem('pos_selected') || 'null')
        const posExistentes = JSON.parse(localStorage.getItem('pos_existentes') || '[]')

        const pos = posSelecionado || posExistentes[0] || null

        if (pos?.id) {
          await this.carregarDetalhePOS(pos.id)
        } else if (this.shouldShowOnboarding()) {
          this.showOnboardingModal = true
        }
      } catch (error) {
        console.error('Erro ao carregar POS:', error)

        if (this.shouldShowOnboarding()) {
          this.showOnboardingModal = true
        }
      } finally {
        this.posLoaded = true
      }
    },

    async carregarDetalhePOS(posId) {
      try {
        const { data } = await api.get(`/api/pos/${posId}/`)
        this.setCurrentPOS(data)
      } catch (error) {
        console.error('Erro ao carregar detalhe do POS:', error)

        const posSelecionado = JSON.parse(localStorage.getItem('pos_selected') || 'null')
        if (posSelecionado?.id) {
          this.setCurrentPOS(posSelecionado)
        }
      }
    },

    setCurrentPOS(pos) {
      this.currentPOS = pos
      this.posId = pos.id
      this.posNome = pos.nome || 'POS Principal'
      this.posCodigo = pos.codigo_pos || ''
      this.modo = pos.modo || 'standalone'
      this.lojaVinculada = pos.loja_vinculada || null

      localStorage.setItem('pos_selected', JSON.stringify(pos))
      localStorage.setItem('pos_id', String(pos.id))

      const posExistentes = JSON.parse(localStorage.getItem('pos_existentes') || '[]')
      const updated = posExistentes.length
        ? posExistentes.map((item) => item.id === pos.id ? { ...item, ...pos } : item)
        : [pos]

      localStorage.setItem('pos_existentes', JSON.stringify(updated))
      localStorage.setItem('pos_precisa_onboarding', 'false')

      this.showOnboardingModal = false
      this.componentRefreshKey += 1
    },

    abrirOnboarding() {
      this.loadLojasFromStorage()
      this.loadOnboardingData()
      this.showOnboardingModal = true
    },

    handleOnboardingClose() {
      this.showOnboardingModal = false
    },

    handleOnboardingCompleted(pos) {
      if (pos?.id) {
        this.setCurrentPOS(pos)
      } else {
        this.loadPOSData()
      }
    },

    async handleOnboardingCreatePOS(payload) {
      await this.criarPOSComPayload(payload)
    },

    async criarPOSComPayload(payload = {}) {
      if (this.creatingPos) return

      this.creatingPos = true

      try {
        const body = {
          nome: payload.nome || 'POS Principal',
          modo: payload.modo || 'standalone'
        }

        if (payload.loja_id) {
          body.loja_id = payload.loja_id
        }

        const { data } = await api.post('/api/pos/criar/', body)

        this.setCurrentPOS(data)
      } catch (error) {
        console.error('Erro ao criar POS:', error)
        alert(error.response?.data?.detail || 'Erro ao criar POS.')
      } finally {
        this.creatingPos = false
      }
    },

    async criarPOS() {
      await this.criarPOSComPayload({
        nome: 'POS Principal',
        modo: 'standalone'
      })
    },

    abrirConfiguracao() {
      if (!this.posId) {
        this.abrirOnboarding()
        return
      }

      this.configError = ''
      this.configSuccess = ''

      this.configForm = {
        nome: this.posNome || 'POS Principal',
        loja_id: this.lojaVinculada?.id || '',
        modo: this.modo || 'standalone'
      }

      this.showConfigModal = true
    },

    fecharConfiguracao() {
      this.showConfigModal = false
      this.configError = ''
      this.configSuccess = ''
    },

    async guardarConfiguracao() {
      if (!this.posId || this.savingConfig) return

      this.configError = ''
      this.configSuccess = ''

      if (
        ['integrado', 'hibrido'].includes(this.configForm.modo) &&
        !this.configForm.loja_id
      ) {
        this.configError = 'Para usar modo integrado ou híbrido, escolhe uma loja Bendi.'
        return
      }

      this.savingConfig = true

      try {
        if (this.configForm.loja_id) {
          const { data } = await api.post(`/api/pos/${this.posId}/conectar-loja/`, {
            loja_id: this.configForm.loja_id,
            modo: this.configForm.modo
          })

          const pos = data.pos || data
          this.setCurrentPOS(pos)
        } else {
          const { data } = await api.post(`/api/pos/${this.posId}/desconectar-loja/`)
          const pos = data.pos || data
          this.setCurrentPOS(pos)
        }

        if (this.configForm.nome && this.configForm.nome !== this.posNome) {
          const { data } = await api.patch(`/api/pos/${this.posId}/`, {
            nome: this.configForm.nome
          })

          this.setCurrentPOS(data)
        }

        this.configSuccess = 'Configuração guardada com sucesso.'

        setTimeout(() => {
          this.fecharConfiguracao()
        }, 700)
      } catch (error) {
        console.error('Erro ao guardar configuração:', error)
        this.configError = error.response?.data?.detail || 'Erro ao guardar configuração do POS.'
      } finally {
        this.savingConfig = false
      }
    },

    async desconectarLoja() {
      if (!confirm('Desconectar este POS da loja Bendi? O POS passará para modo standalone.')) return

      this.savingConfig = true

      try {
        const { data } = await api.post(`/api/pos/${this.posId}/desconectar-loja/`)
        const pos = data.pos || data

        this.setCurrentPOS(pos)
      } catch (error) {
        console.error('Erro ao desconectar loja:', error)
        alert(error.response?.data?.detail || 'Erro ao desconectar loja.')
      } finally {
        this.savingConfig = false
      }
    },

    logout() {
      if (!confirm('Tem a certeza que quer sair?')) return

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')

      localStorage.removeItem('pos_lojas')
      localStorage.removeItem('pos_existentes')
      localStorage.removeItem('pos_selected')
      localStorage.removeItem('pos_id')
      localStorage.removeItem('pos_tem_lojas')
      localStorage.removeItem('pos_precisa_onboarding')
      localStorage.removeItem('pos_onboarding_data')
      localStorage.removeItem('pos_permissoes')

      this.$router.push('/pos/login')
    }
  }
}
</script>