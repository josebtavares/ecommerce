<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-black text-slate-950">Pedidos ativos</h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          {{ pedidos.length }} pedidos em curso
        </p>
      </div>

      <div class="flex items-center gap-3 rounded-2xl bg-white px-4 py-3 shadow-sm">
        <span class="text-sm font-bold text-slate-600">Auto-refresh</span>
        <label class="relative inline-flex cursor-pointer items-center">
          <input
            v-model="autoRefresh"
            type="checkbox"
            class="peer sr-only"
            @change="toggleAutoRefresh"
          />
          <div class="h-6 w-11 rounded-full bg-slate-300 after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-slate-950 peer-checked:after:translate-x-5"></div>
        </label>
      </div>
    </div>

    <!-- Erro -->
    <div
      v-if="error"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
    >
      {{ error }}
    </div>

    <!-- Filtros -->
    <div class="rounded-[1.5rem] border border-slate-200 bg-white p-3 shadow-sm">
      <div class="flex gap-2 overflow-x-auto">
        <button
          v-for="filtro in filtrosStatus"
          :key="filtro.value"
          type="button"
          @click="statusFiltro = filtro.value"
          :class="[
            'shrink-0 rounded-2xl px-4 py-2.5 text-sm font-black transition',
            statusFiltro === filtro.value
              ? 'bg-slate-950 text-white shadow-lg shadow-slate-950/10'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-950'
          ]"
        >
          {{ filtro.label }}
          <span class="ml-1 opacity-80">({{ contarPorStatus(filtro.value) }})</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="rounded-[2rem] bg-white p-10 text-center shadow-sm">
      <div class="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
      <p class="mt-3 text-sm font-bold text-slate-500">A carregar pedidos...</p>
    </div>

    <!-- Lista -->
    <div v-else-if="pedidosFiltrados.length > 0" class="space-y-4">
      <article
        v-for="pedido in pedidosFiltrados"
        :key="pedido.id"
        class="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm"
      >
        <header class="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="text-lg font-black text-slate-950">
                {{ pedido.mesa?.numero || 'Mesa' }}
              </h3>
              <span :class="['rounded-full px-3 py-1 text-xs font-black uppercase', getStatusBadge(pedido.status)]">
                {{ getStatusLabel(pedido.status) }}
              </span>
            </div>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              Conta #{{ pedido.id }} · {{ formatTime(pedido.criada_em) }}
            </p>
          </div>

          <div class="text-left sm:text-right">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Total</p>
            <p class="text-xl font-black text-slate-950">{{ money(pedido.total) }}</p>
          </div>
        </header>

        <div class="space-y-3 p-4">
          <div
            v-for="item in pedido.items"
            :key="item.id"
            class="rounded-2xl bg-slate-50 p-3"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <p class="font-black text-slate-950">
                    {{ item.quantidade }}x {{ item.nome }}
                  </p>
                  <span
                    :class="[
                      'rounded-full px-2 py-0.5 text-[10px] font-black uppercase',
                      item.origem === 'pos' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                    ]"
                  >
                    {{ item.origem === 'pos' ? 'POS' : 'Loja' }}
                  </span>
                </div>

                <p v-if="item.observacoes" class="mt-1 text-xs italic text-slate-500">
                  {{ item.observacoes }}
                </p>

                <p :class="['mt-1 text-xs font-black', getItemStatusColor(item.status)]">
                  {{ getItemStatusLabel(item.status) }}
                </p>
              </div>

              <div class="flex items-center gap-2">
                <span class="text-sm font-black text-slate-700">
                  {{ money(item.preco_total) }}
                </span>

                <!-- Selector de status: só visível se tiver permissão -->
                <select
                  v-if="podeAtualizarStatus"
                  v-model="item.status"
                  @change="atualizarStatusItem(pedido.id, item.id, item.status)"
                  class="h-9 rounded-xl border border-slate-200 bg-white px-2 text-xs font-bold text-slate-700 outline-none focus:border-slate-950"
                >
                  <option value="pendente">Pendente</option>
                  <option value="preparando">A preparar</option>
                  <option value="pronto">Pronto</option>
                  <option value="entregue">Entregue</option>
                  <option value="cancelado">Cancelado</option>
                </select>

                <!-- Sem permissão: mostra só o badge de status -->
                <span
                  v-else
                  :class="['rounded-xl px-3 py-1.5 text-xs font-black', getItemStatusBadge(item.status)]"
                >
                  {{ getItemStatusLabel(item.status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>

    <!-- Empty -->
    <section
      v-else
      class="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-10 text-center"
    >
      <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">
        🛒
      </div>
      <h3 class="mt-5 text-xl font-black text-slate-950">Nenhum pedido ativo</h3>
      <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
        Os pedidos abertos aparecerão aqui depois de adicionares produtos às mesas.
      </p>
    </section>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'POSPedidos',

  props: {
    posId: {
      type: [Number, String],
      required: true
    },
    permissoes: {
      type: Object,
      default: null
    },
    isMembro: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      pedidos: [],
      loading: false,
      error: '',
      statusFiltro: 'todas',
      autoRefresh: false,
      refreshInterval: null,

      filtrosStatus: [
        { value: 'todas',      label: 'Todas' },
        { value: 'aberta',     label: 'Abertas' },
        { value: 'preparando', label: 'A preparar' },
        { value: 'pronto',     label: 'Prontos' },
        { value: 'entregue',   label: 'Entregues' },
      ]
    }
  },

  computed: {
    pedidosFiltrados() {
      if (this.statusFiltro === 'todas') return this.pedidos

      if (['pendente', 'preparando', 'pronto', 'entregue'].includes(this.statusFiltro)) {
        return this.pedidos.filter(p =>
          p.items?.some(i => i.status === this.statusFiltro)
        )
      }

      return this.pedidos.filter(p => p.status === this.statusFiltro)
    },

    // Conta principal → tudo permitido. Membro → verificar permissão.
    podeAtualizarStatus() {
      if (!this.isMembro) return true
      return this.permissoes?.pode_atualizar_status_items ?? false
    },
  },

  created() {
    this.carregarPedidos()
  },

  beforeUnmount() {
    this.stopAutoRefresh()
  },

  methods: {
    async carregarPedidos() {
      this.loading = true
      this.error = ''

      try {
        const { data } = await api.get(`/api/pos/${this.posId}/contas/ativas/`)
        this.pedidos = Array.isArray(data) ? data : (data.results ?? [])
      } catch (err) {
        if (err.response?.status === 404) {
          this.error = 'Endpoint de pedidos ativos não encontrado.'
        } else {
          this.error = err.response?.data?.detail || 'Erro ao carregar pedidos.'
        }
      } finally {
        this.loading = false
      }
    },

    toggleAutoRefresh() {
      if (this.autoRefresh) {
        this.refreshInterval = setInterval(() => this.carregarPedidos(), 10000)
      } else {
        this.stopAutoRefresh()
      }
    },

    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },

    contarPorStatus(status) {
      if (status === 'todas') return this.pedidos.length

      if (['pendente', 'preparando', 'pronto', 'entregue'].includes(status)) {
        return this.pedidos.filter(p =>
          p.items?.some(i => i.status === status)
        ).length
      }

      return this.pedidos.filter(p => p.status === status).length
    },

    async atualizarStatusItem(contaId, itemId, novoStatus) {
      if (!this.podeAtualizarStatus) return

      try {
        await api.patch(
          `/api/pos/${this.posId}/contas/${contaId}/items/${itemId}/status/`,
          { status: novoStatus }
        )
        await this.carregarPedidos()
      } catch (err) {
        alert(err.response?.data?.detail || 'Erro ao atualizar status do item.')
      }
    },

    // ── Labels e badges ────────────────────────────────────────────
    getStatusBadge(status) {
      return {
        aberta:    'bg-blue-100 text-blue-800',
        fechada:   'bg-green-100 text-green-800',
        cancelada: 'bg-red-100 text-red-800',
      }[status] || 'bg-slate-100 text-slate-700'
    },

    getStatusLabel(status) {
      return { aberta: 'Aberta', fechada: 'Fechada', cancelada: 'Cancelada' }[status] || status
    },

    getItemStatusColor(status) {
      return {
        pendente:   'text-slate-600',
        preparando: 'text-orange-600',
        pronto:     'text-green-600',
        entregue:   'text-blue-600',
        cancelado:  'text-red-600',
      }[status] || 'text-slate-600'
    },

    getItemStatusBadge(status) {
      return {
        pendente:   'bg-slate-100 text-slate-700',
        preparando: 'bg-orange-100 text-orange-700',
        pronto:     'bg-green-100 text-green-700',
        entregue:   'bg-blue-100 text-blue-700',
        cancelado:  'bg-red-100 text-red-700',
      }[status] || 'bg-slate-100 text-slate-700'
    },

    getItemStatusLabel(status) {
      return {
        pendente:   '⏳ Pendente',
        preparando: '🔥 A preparar',
        pronto:     '✅ Pronto',
        entregue:   '🎉 Entregue',
        cancelado:  '❌ Cancelado',
      }[status] || status
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      const diff = Math.floor((new Date() - new Date(timestamp)) / 60000)
      if (diff < 1)  return 'Agora mesmo'
      if (diff < 60) return `Há ${diff} min`
      const h = Math.floor(diff / 60)
      return `Há ${h}h ${diff % 60}min`
    },

    money(value) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(value || 0))
    },
  }
}
</script>