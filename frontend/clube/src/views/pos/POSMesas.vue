<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-black text-slate-950">Mesas</h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          {{ mesas.length }} mesas ativas
        </p>
      </div>

      <button
        type="button"
        @click="abrirModalCriarMesa"
        class="inline-flex h-11 items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        + Nova mesa
      </button>
    </div>

    <!-- Alertas -->
    <div
      v-if="error"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
    >
      {{ error }}
    </div>

    <div
      v-if="success"
      class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
    >
      {{ success }}
    </div>

    <!-- Filtros -->
    <div class="rounded-[1.5rem] border border-slate-200 bg-white p-3 shadow-sm">
      <div class="flex gap-2 overflow-x-auto">
        <button
          v-for="filtro in filtros"
          :key="filtro.value"
          type="button"
          @click="filtroAtivo = filtro.value"
          :class="[
            'shrink-0 rounded-2xl px-4 py-2.5 text-sm font-black transition',
            filtroAtivo === filtro.value
              ? 'bg-slate-950 text-white shadow-lg shadow-slate-950/10'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-950'
          ]"
        >
          {{ filtro.label }}
          <span class="ml-1 opacity-80">({{ contarMesas(filtro.value) }})</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="loading && mesas.length === 0"
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5"
    >
      <div
        v-for="item in 10"
        :key="item"
        class="h-40 animate-pulse rounded-[1.5rem] bg-slate-100"
      ></div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="mesasFiltradas.length === 0"
      class="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-10 text-center"
    >
      <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">
        🍽️
      </div>

      <h3 class="mt-5 text-xl font-black text-slate-950">
        Nenhuma mesa encontrada
      </h3>

      <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
        Cria mesas para começar a abrir contas, adicionar produtos e processar pagamentos.
      </p>

      <button
        type="button"
        @click="abrirModalCriarMesa"
        class="mt-6 inline-flex h-11 items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        Criar primeira mesa
      </button>
    </div>

    <!-- Grid -->
    <div
      v-else
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5"
    >
      <MesaCard
        v-for="mesa in mesasFiltradas"
        :key="mesa.id"
        :mesa="mesa"
        @click="abrirMesa(mesa)"
        @editar="editarMesa(mesa)"
        @apagar="apagarMesa(mesa)"
      />
    </div>

    <!-- Refresh loading -->
    <div v-if="loading && mesas.length > 0" class="py-4 text-center">
      <div class="mx-auto h-7 w-7 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
    </div>

    <!-- Modal Criar Mesa -->
    <div
      v-if="showMesaModal"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharModalMesa"
    >
      <div class="w-full max-w-md rounded-t-[2rem] bg-white p-6 shadow-2xl sm:rounded-[2rem]">
        <div class="mb-5 flex items-start justify-between gap-4">
          <div>
            <h3 class="text-xl font-black text-slate-950">
              Nova mesa
            </h3>
            <p class="mt-1 text-sm text-slate-500">
              Define o número/nome e a capacidade.
            </p>
          </div>

          <button
            type="button"
            @click="fecharModalMesa"
            class="rounded-2xl p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-950"
          >
            ✕
          </button>
        </div>

        <form class="space-y-4" @submit.prevent="criarMesa">
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Número/Nome
            </label>

            <input
              v-model.trim="novaMesa.numero"
              type="text"
              placeholder="Ex: Mesa 5, Balcão, Esplanada 2"
              required
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Capacidade
            </label>

            <input
              v-model.number="novaMesa.capacidade"
              type="number"
              min="1"
              max="20"
              required
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div class="flex gap-3 pt-2">
            <button
              type="button"
              @click="fecharModalMesa"
              class="h-11 flex-1 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
            >
              Cancelar
            </button>

            <button
              type="submit"
              :disabled="saving"
              class="h-11 flex-1 rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {{ saving ? 'A criar...' : 'Criar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Conta -->
    <ContaModal
  v-if="mesaSelecionada"
  :mesa="mesaSelecionada"
  :pos-id="posId"
  @close="fecharContaModal"
  @atualizar="carregarMesas(true)"
/>
    
  </div>
</template>

<script>
import api from '@/services/api'
import MesaCard from './components/MesaCard.vue'
import ContaModal from './components/ContaModal.vue'

export default {
  name: 'POSMesas',

  components: {
    MesaCard,
    ContaModal
  },

  props: {
    posId: {
      type: [Number, String],
      required: true
    }
  },

  data() {
    return {
      mesas: [],
      loading: false,
      saving: false,
      error: '',
      success: '',
      filtroAtivo: 'todas',
      showMesaModal: false,
      mesaSelecionada: null,

      novaMesa: {
        numero: '',
        capacidade: 4
      },

      filtros: [
        { value: 'todas', label: 'Todas' },
        { value: 'livre', label: 'Livres' },
        { value: 'ocupada', label: 'Ocupadas' },
        { value: 'reservada', label: 'Reservadas' },
        { value: 'limpeza', label: 'Limpeza' }
      ]
    }
  },

  computed: {
    mesasFiltradas() {
      if (this.filtroAtivo === 'todas') return this.mesas
      return this.mesas.filter((mesa) => mesa.status === this.filtroAtivo)
    }
  },

  created() {
    this.carregarMesas()
  },

  watch: {
    posId(newId, oldId) {
      if (newId && newId !== oldId) {
        this.carregarMesas()
      }
    }
  },

  methods: {
    async carregarMesas() {
      if (!this.posId || this.loading) return

      this.loading = true
      this.error = ''

      try {
        const { data } = await api.get(`/api/pos/${this.posId}/mesas/`)

        this.mesas = Array.isArray(data)
          ? data
          : Array.isArray(data.results)
            ? data.results
            : []
      } catch (error) {
        console.error('Erro ao carregar mesas:', error)
        this.error = error.response?.data?.detail || 'Erro ao carregar mesas.'
      } finally {
        this.loading = false
      }
    },

    abrirModalCriarMesa() {
      this.clearMessages()
      this.novaMesa = {
        numero: '',
        capacidade: 4
      }
      this.showMesaModal = true
    },

    fecharModalMesa() {
      this.showMesaModal = false
      this.novaMesa = {
        numero: '',
        capacidade: 4
      }
    },

    fecharContaModal() {
    this.mesaSelecionada = null
    // Recarregar mesas para ver status atualizado
    this.carregarMesas(true)
  },

    async criarMesa() {
      if (!this.novaMesa.numero.trim()) {
        this.error = 'O número/nome da mesa é obrigatório.'
        return
      }

      this.saving = true
      this.clearMessages()

      try {
        await api.post(`/api/pos/${this.posId}/mesas/criar/`, {
          numero: this.novaMesa.numero.trim(),
          capacidade: this.novaMesa.capacidade || 4
        })

        this.success = 'Mesa criada com sucesso.'
        this.fecharModalMesa()
        await this.carregarMesas()
      } catch (error) {
        console.error('Erro ao criar mesa:', error)
        this.error = error.response?.data?.detail || 'Erro ao criar mesa.'
      } finally {
        this.saving = false
      }
    },

    abrirMesa(mesa) {
    // Se mesa está livre, abrir primeiro
    if (mesa.status === 'livre') {
      this.abrirMesaNoBackend(mesa)
    } else {
      // Já está ocupada, abrir modal direto
      this.mesaSelecionada = mesa
    }
  },
  
  async abrirMesaNoBackend(mesa) {
    try {
      const token = localStorage.getItem('pos_access_token')
      await axios.post(
        `${process.env.VUE_APP_URL_BASE}/api/pos/${this.posId}/mesas/${mesa.id}/abrir/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      // Recarregar mesas para ver status atualizado
      await this.carregarMesas(true)
      
      // Agora sim, abrir modal
      const mesaAtualizada = this.mesas.find(m => m.id === mesa.id)
      if (mesaAtualizada) {
        this.mesaSelecionada = mesaAtualizada
      }
      
    } catch (error) {
      console.error('Erro ao abrir mesa:', error)
      alert(error.response?.data?.detail || 'Erro ao abrir mesa')
    }
  },

    editarMesa() {
      this.error = 'A edição de mesas ainda precisa de endpoint no backend.'
    },

    async apagarMesa(mesa) {
      if (!confirm(`Apagar ${mesa.numero}?`)) return

      this.clearMessages()

      try {
        await api.delete(`/api/pos/${this.posId}/mesas/${mesa.id}/apagar/`)

        this.success = 'Mesa apagada com sucesso.'
        await this.carregarMesas()
      } catch (error) {
        console.error('Erro ao apagar mesa:', error)
        this.error = error.response?.data?.detail || 'Erro ao apagar mesa.'
      }
    },

    contarMesas(status) {
      if (status === 'todas') return this.mesas.length
      return this.mesas.filter((mesa) => mesa.status === status).length
    },

    clearMessages() {
      this.error = ''
      this.success = ''
    }
  }
}
</script>