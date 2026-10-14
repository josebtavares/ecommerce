<template>
  <div
    class="fixed inset-0 z-[70] flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
    @click.self="canClose ? $emit('close') : null"
  >
    <div class="flex max-h-[96vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">

      <!-- Header -->
      <header class="relative shrink-0 overflow-hidden border-b border-slate-200 bg-slate-950 p-6 text-white sm:p-8">
        <div class="absolute -right-20 -top-20 h-52 w-52 rounded-full bg-blue-500/20 blur-3xl"></div>
        <div class="absolute -bottom-24 left-1/3 h-52 w-52 rounded-full bg-emerald-500/20 blur-3xl"></div>

        <div class="relative flex items-start justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-200">
              <span class="h-2 w-2 rounded-full bg-emerald-400"></span>
              Configuração inicial
            </div>

            <h2 class="mt-5 text-2xl font-black tracking-tight sm:text-3xl">
              Como queres usar o teu POS?
            </h2>

            <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              Detectámos a tua conta Bendi. Escolhe se queres começar com um POS independente ou ligado a uma das tuas lojas.
            </p>
          </div>

          <button
            v-if="canClose"
            type="button"
            @click="$emit('close')"
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-xl font-black text-white transition hover:bg-white/20"
          >
            ×
          </button>
        </div>
      </header>

      <!-- Body -->
      <section class="min-h-0 flex-1 overflow-y-auto p-5 sm:p-6">

        <!-- Erro -->
        <div
          v-if="error"
          class="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
        >
          {{ error }}
        </div>

        <!-- Tem lojas -->
        <div v-if="temLojas" class="mb-5 rounded-[1.5rem] border border-blue-200 bg-blue-50 p-4">
          <div class="flex items-start gap-3">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-lg text-white"><font-awesome-icon :icon="['fas', 'store']" /></div>
            <div>
              <p class="text-sm font-black text-blue-950">
                Encontrámos {{ lojasDisponiveis.length }} loja{{ lojasDisponiveis.length !== 1 ? 's' : '' }} Bendi na tua conta.
              </p>
              <p class="mt-1 text-sm leading-6 text-blue-700">
                Podes criar um POS integrado para vender diretamente com o catálogo da loja, ou escolher standalone para gerir produtos separados.
              </p>
            </div>
          </div>
        </div>

        <!-- Sem lojas -->
        <div v-else class="mb-5 rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4">
          <div class="flex items-start gap-3">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-amber-500 text-lg text-white"><font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" /></div>
            <div>
              <p class="text-sm font-black text-amber-950">Ainda não tens lojas Bendi associadas.</p>
              <p class="mt-1 text-sm leading-6 text-amber-700">
                Podes começar já com um POS standalone. Mais tarde, se criares uma loja Bendi, podes conectar ou mudar para modo híbrido.
              </p>
            </div>
          </div>
        </div>

        <!-- Nome do POS -->
        <div class="mb-5">
          <label class="mb-2 block text-sm font-black text-slate-700">Nome do POS</label>
          <input
            v-model.trim="form.nome"
            type="text"
            placeholder="Ex: POS Principal"
            class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
          />
        </div>

        <!-- Opções de modo -->
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">

          <!-- Standalone -->
          <button type="button" @click="selecionarModo('standalone')" :class="cardClass('standalone')">
            <div class="flex items-start justify-between gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-2xl text-purple-600"><font-awesome-icon :icon="['fas', 'receipt']" /></div>
              <div
                v-if="form.modo === 'standalone'"
                class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-950 text-xs font-black text-white"
              >
                <font-awesome-icon :icon="['fas', 'check']" />
              </div>
            </div>
            <h3 class="mt-4 text-left text-lg font-black text-slate-950">POS Standalone</h3>
            <p class="mt-2 text-left text-sm leading-6 text-slate-500">
              Começa sem loja Bendi. Vais criar produtos próprios dentro do POS.
            </p>
            <ul class="mt-4 space-y-2 text-left text-xs font-bold text-slate-500">
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Produtos próprios do POS</li>
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Ideal para começar rápido</li>
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Pode conectar loja depois</li>
            </ul>
          </button>

          <!-- Integrado -->
          <button type="button" :disabled="!temLojas" @click="selecionarModo('integrado')" :class="cardClass('integrado')">
            <div class="flex items-start justify-between gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-100 text-2xl text-blue-600"><font-awesome-icon :icon="['fas', 'store']" /></div>
              <div
                v-if="form.modo === 'integrado'"
                class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-950 text-xs font-black text-white"
              >
                <font-awesome-icon :icon="['fas', 'check']" />
              </div>
            </div>
            <h3 class="mt-4 text-left text-lg font-black text-slate-950">Integrado com loja</h3>
            <p class="mt-2 text-left text-sm leading-6 text-slate-500">
              Usa os produtos da tua loja Bendi diretamente no POS.
            </p>
            <ul class="mt-4 space-y-2 text-left text-xs font-bold text-slate-500">
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Catálogo da loja</li>
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Produtos sincronizados</li>
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Melhor para lojas existentes</li>
            </ul>
          </button>

          <!-- Híbrido -->
          <button type="button" :disabled="!temLojas" @click="selecionarModo('hibrido')" :class="cardClass('hibrido')">
            <div class="flex items-start justify-between gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-2xl text-emerald-600"><font-awesome-icon :icon="['fas', 'shuffle']" /></div>
              <div
                v-if="form.modo === 'hibrido'"
                class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-950 text-xs font-black text-white"
              >
                <font-awesome-icon :icon="['fas', 'check']" />
              </div>
            </div>
            <h3 class="mt-4 text-left text-lg font-black text-slate-950">Modo híbrido</h3>
            <p class="mt-2 text-left text-sm leading-6 text-slate-500">
              Usa produtos da loja Bendi e também produtos próprios do POS.
            </p>
            <ul class="mt-4 space-y-2 text-left text-xs font-bold text-slate-500">
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Catálogo da loja</li>
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Produtos extras no POS</li>
              <li><font-awesome-icon :icon="['fas', 'check']" class="mr-1.5 text-emerald-500" /> Mais flexibilidade</li>
            </ul>
          </button>
        </div>

        <!-- Escolha da loja -->
        <div
          v-if="form.modo !== 'standalone' && temLojas"
          class="mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4"
        >
          <label class="mb-2 block text-sm font-black text-slate-700">Escolhe a loja Bendi</label>
          <select
            v-model="form.loja_id"
            class="h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:ring-4 focus:ring-slate-950/10"
          >
            <option value="">Selecionar loja</option>
            <option v-for="loja in lojasDisponiveis" :key="loja.id" :value="loja.id">
              {{ loja.nome }}
            </option>
          </select>
          <p class="mt-2 text-xs font-semibold text-slate-500">
            O POS será criado ligado a esta loja. Podes alterar a configuração depois.
          </p>
        </div>

        <!-- Plano (subscrição do POS) -->
        <div class="mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4">
          <p class="text-sm font-black text-slate-700">Escolhe o plano</p>
          <p class="mt-1 text-xs font-semibold text-slate-500">
            <template v-if="diasTeste">Os primeiros {{ diasTeste }} dias são grátis — só pagas depois. </template>
            A tua equipa entra neste POS sem pagar nada à parte.
          </p>
          <div v-if="carregandoPlanos" class="mt-3 h-20 animate-pulse rounded-2xl bg-slate-200"></div>
          <p v-else-if="!planos.length" class="mt-3 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-600">
            Ainda não há planos disponíveis — começas no período grátis e escolhes o plano depois, na aba Subscrição.
          </p>
          <div v-else class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3" role="radiogroup" aria-label="Plano do POS">
            <button v-for="p in planos" :key="p.id" type="button" role="radio" :aria-checked="form.plano_id === p.id ? 'true' : 'false'"
              @click="form.plano_id = p.id"
              :class="['rounded-2xl border-2 bg-white p-4 text-left transition',
                       form.plano_id === p.id ? 'border-slate-950 shadow-lg shadow-slate-950/10' : 'border-slate-200 hover:border-slate-300']">
              <div class="flex items-start justify-between gap-2">
                <p class="text-sm font-black text-slate-950">{{ p.nome }}</p>
                <span v-if="form.plano_id === p.id" class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-950 text-[10px] text-white">
                  <font-awesome-icon :icon="['fas', 'check']" />
                </span>
              </div>
              <p class="mt-1 text-xl font-black text-slate-950">{{ euros(p.preco) }}</p>
              <p class="text-[11px] font-semibold text-slate-500">{{ p.periodicidade_nome }}<template v-if="p.meses > 1"> · {{ euros(p.preco_mes) }}/mês</template></p>
              <p v-if="p.descricao" class="mt-2 text-xs text-slate-500">{{ p.descricao }}</p>
            </button>
          </div>
        </div>

        <!-- Resumo -->
        <div class="mt-5 rounded-[1.5rem] border border-slate-200 bg-white p-4">
          <p class="text-sm font-black text-slate-950">Resumo da configuração</p>
          <div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-4">
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs font-black uppercase text-slate-400">Plano</p>
              <p class="mt-1 truncate text-sm font-black text-slate-900">{{ planoSelecionado ? planoSelecionado.nome : (planos.length ? '—' : 'Depois') }}</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs font-black uppercase text-slate-400">Modo</p>
              <p class="mt-1 text-sm font-black text-slate-900">{{ modoLabel }}</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs font-black uppercase text-slate-400">Loja</p>
              <p class="mt-1 truncate text-sm font-black text-slate-900">
                {{ lojaSelecionada?.nome || 'Nenhuma' }}
              </p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs font-black uppercase text-slate-400">Produtos</p>
              <p class="mt-1 text-sm font-black text-slate-900">{{ produtosResumo }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Footer -->
      <footer class="grid shrink-0 grid-cols-1 gap-3 border-t border-slate-200 bg-slate-50 p-5 sm:grid-cols-[1fr_auto] sm:items-center">
        <p class="text-xs font-semibold leading-5 text-slate-500">
          Podes alterar esta configuração depois no botão "Configurar POS".
        </p>

        <button
          type="button"
          @click="confirmar"
          :disabled="loading || !canConfirm"
          class="flex h-12 min-w-[190px] items-center justify-center rounded-2xl bg-slate-950 px-6 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
        >
          <span v-if="!loading">Criar POS</span>
          <span v-else class="flex items-center gap-2">
            <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
            A criar...
          </span>
        </button>
      </footer>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'OnboardingModal',

  props: {
    lojas: {
      type: Array,
      default: () => []
    },
    onboardingData: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    // CORRIGIDO: default false — só mostrar X se explicitamente activado
    canClose: {
      type: Boolean,
      default: false
    }
  },

  emits: ['create-pos', 'completed', 'close'],

  data() {
    return {
      error: '',
      form: {
        nome:    'POS Principal',
        modo:    'standalone',
        loja_id: '',
        plano_id: null
      },
      planos: [],
      diasTeste: 0,
      carregandoPlanos: true
    }
  },

  async created () {
    try {
      const { data } = await api.get('/api/pos/planos/')
      this.planos = data.planos || []
      this.diasTeste = data.dias_teste || 0
      if (this.planos.length) this.form.plano_id = this.planos[0].id
    } catch {
      this.planos = []
    } finally {
      this.carregandoPlanos = false
    }
  },

  computed: {
    temLojas() {
      return this.lojasDisponiveis.length > 0
    },

    // CORRIGIDO: fonte única de lojas — prop lojas tem prioridade, fallback para onboardingData
    lojasDisponiveis() {
      if (this.lojas.length > 0) return this.lojas
      return Array.isArray(this.onboardingData?.lojas) ? this.onboardingData.lojas : []
    },

    // CORRIGIDO: usa lojasDisponiveis (não this.lojas)
    lojaSelecionada() {
      if (!this.form.loja_id) return null
      return this.lojasDisponiveis.find(l => String(l.id) === String(this.form.loja_id)) || null
    },

    modoLabel() {
      return { standalone: 'Standalone', integrado: 'Integrado', hibrido: 'Híbrido' }[this.form.modo] || 'Standalone'
    },

    produtosResumo() {
      return { integrado: 'Da loja', hibrido: 'Loja + POS' }[this.form.modo] || 'Próprios'
    },

    planoSelecionado() {
      return this.planos.find(p => p.id === this.form.plano_id) || null
    },

    canConfirm() {
      if (!this.form.nome.trim()) return false
      if (this.carregandoPlanos || (this.planos.length && !this.form.plano_id)) return false
      if (['integrado', 'hibrido'].includes(this.form.modo)) return Boolean(this.form.loja_id)
      return true
    }
  },

  watch: {
    lojas:         { immediate: true, handler: 'prepararDefaults' },
    onboardingData:{ immediate: true, handler: 'prepararDefaults' }
  },

  methods: {
    prepararDefaults() {
      const lojas = this.lojasDisponiveis

      // Auto-selecionar primeira loja se ainda não tiver uma
      if (lojas.length > 0 && !this.form.loja_id) {
        this.form.loja_id = lojas[0].id
      }

      // Sem lojas → forçar standalone
      if (lojas.length === 0) {
        this.form.modo    = 'standalone'
        this.form.loja_id = ''
      }
    },

    selecionarModo(modo) {
      this.error = ''

      if (['integrado', 'hibrido'].includes(modo) && !this.temLojas) {
        this.error = 'Para usar este modo, primeiro precisas ter uma loja Bendi.'
        return
      }

      this.form.modo = modo

      if (modo === 'standalone') {
        this.form.loja_id = ''
      } else if (!this.form.loja_id && this.lojasDisponiveis.length > 0) {
        this.form.loja_id = this.lojasDisponiveis[0].id
      }
    },

    confirmar() {
      this.error = ''

      if (!this.form.nome.trim()) {
        this.error = 'Define um nome para o POS.'
        return
      }

      if (['integrado', 'hibrido'].includes(this.form.modo) && !this.form.loja_id) {
        this.error = 'Escolhe uma loja Bendi para este modo.'
        return
      }

      if (this.planos.length && !this.form.plano_id) {
        this.error = 'Escolhe um plano.'
        return
      }

      const payload = { nome: this.form.nome.trim(), modo: this.form.modo }
      if (this.form.loja_id) payload.loja_id = this.form.loja_id
      if (this.form.plano_id) payload.plano_id = this.form.plano_id

      this.$emit('create-pos', payload)
    },

    euros(v) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0)
    },

    cardClass(modo) {
      const selected = this.form.modo === modo
      const disabled = ['integrado', 'hibrido'].includes(modo) && !this.temLojas

      return [
        'rounded-[1.5rem] border-2 p-5 text-left transition',
        selected
          ? 'border-slate-950 bg-white shadow-xl shadow-slate-950/10'
          : 'border-slate-200 bg-white hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg',
        disabled
          ? 'cursor-not-allowed opacity-50 hover:translate-y-0 hover:shadow-none'
          : 'cursor-pointer'
      ]
    }
  }
}
</script>