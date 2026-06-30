<template>
  <div class="space-y-5">

    <!-- Sem permissão -->
    <div
      v-if="isMembro && !podeVerRelatorios"
      class="rounded-[2rem] border border-slate-200 bg-white p-12 text-center shadow-sm"
    >
      <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-3xl">🔒</div>
      <h3 class="mt-4 text-xl font-black text-slate-950">Sem permissão</h3>
      <p class="mt-2 text-sm text-slate-500">Não tens permissão para ver o histórico de contas.</p>
    </div>

    <!-- Conteúdo normal -->
    <template v-else>

      <!-- Header -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-2xl font-black text-slate-950">Histórico</h2>
          <p class="mt-1 text-sm font-semibold text-slate-500">{{ totalCount }} contas registadas</p>
        </div>

        <button
          type="button"
          @click="carregarHistorico(true)"
          class="h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-800"
        >
          Atualizar
        </button>
      </div>

      <!-- Erro -->
      <div
        v-if="error"
        class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
      >
        {{ error }}
      </div>

      <!-- Filtros -->
      <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Data início</label>
            <input
              v-model="filtros.dataInicio"
              type="date"
              @change="carregarHistorico(true)"
              class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Data fim</label>
            <input
              v-model="filtros.dataFim"
              type="date"
              @change="carregarHistorico(true)"
              class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Método pagamento</label>
            <select
              v-model="filtros.metodoPagamento"
              @change="carregarHistorico(true)"
              class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            >
              <option value="">Todos</option>
              <option value="dinheiro">Dinheiro</option>
              <option value="cartao">Cartão</option>
              <option value="mbway">MBWay</option>
              <option value="transferencia">Transferência</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Loading -->
      <div v-if="loading" class="rounded-[2rem] bg-white p-10 text-center shadow-sm">
        <div class="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
        <p class="mt-3 text-sm font-bold text-slate-500">A carregar histórico...</p>
      </div>

      <!-- Tabela desktop + cards mobile -->
      <section
        v-else-if="historico.length > 0"
        class="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm"
      >
        <!-- Tabela desktop -->
        <div class="hidden overflow-x-auto md:block">
          <table class="w-full">
            <thead class="border-b border-slate-200 bg-slate-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-black uppercase text-slate-500">Data/Hora</th>
                <th class="px-4 py-3 text-left text-xs font-black uppercase text-slate-500">Mesa</th>
                <th class="px-4 py-3 text-left text-xs font-black uppercase text-slate-500">Items</th>
                <th class="px-4 py-3 text-left text-xs font-black uppercase text-slate-500">Pagamento</th>
                <th class="px-4 py-3 text-right text-xs font-black uppercase text-slate-500">Total</th>
                <th class="px-4 py-3 text-center text-xs font-black uppercase text-slate-500">Ações</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-100">
              <tr v-for="conta in historico" :key="conta.id" class="hover:bg-slate-50">
                <td class="px-4 py-3 text-sm font-semibold text-slate-700">
                  {{ formatDateTime(conta.fechada_em) }}
                </td>
                <td class="px-4 py-3 text-sm font-black text-slate-950">
                  {{ conta.mesa?.numero || '—' }}
                </td>
                <td class="px-4 py-3 text-sm font-semibold text-slate-600">
                  {{ conta.items?.length || 0 }} item{{ (conta.items?.length || 0) !== 1 ? 's' : '' }}
                </td>
                <td class="px-4 py-3">
                  <span :class="['rounded-full px-3 py-1 text-xs font-black uppercase', getMetodoBadge(conta.metodo_pagamento)]">
                    {{ getMetodoLabel(conta.metodo_pagamento) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right text-sm font-black text-slate-950">
                  {{ money(conta.total) }}
                </td>
                <td class="px-4 py-3 text-center">
                  <button
                    type="button"
                    @click="verDetalhes(conta)"
                    class="rounded-xl bg-slate-100 px-3 py-2 text-xs font-black text-slate-700 transition hover:bg-slate-200"
                  >
                    Ver
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Cards mobile -->
        <div class="space-y-3 p-3 md:hidden">
          <article
            v-for="conta in historico"
            :key="conta.id"
            class="rounded-2xl bg-slate-50 p-4"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-black text-slate-950">{{ conta.mesa?.numero || 'Mesa' }}</p>
                <p class="mt-1 text-xs font-semibold text-slate-500">{{ formatDateTime(conta.fechada_em) }}</p>
              </div>
              <p class="text-lg font-black text-slate-950">{{ money(conta.total) }}</p>
            </div>

            <div class="mt-3 flex items-center justify-between gap-2">
              <span :class="['rounded-full px-3 py-1 text-xs font-black uppercase', getMetodoBadge(conta.metodo_pagamento)]">
                {{ getMetodoLabel(conta.metodo_pagamento) }}
              </span>
              <button
                type="button"
                @click="verDetalhes(conta)"
                class="rounded-xl bg-white px-3 py-2 text-xs font-black text-slate-700 shadow-sm"
              >
                Ver detalhes
              </button>
            </div>
          </article>
        </div>

        <!-- Paginação -->
        <div class="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-4 py-3">
          <button
            type="button"
            @click="carregarHistorico(false, page - 1)"
            :disabled="page <= 1"
            class="h-10 rounded-2xl bg-white px-4 text-sm font-black text-slate-700 shadow-sm transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Anterior
          </button>

          <span class="text-sm font-black text-slate-600">
            Página {{ page }} de {{ totalPages || 1 }}
          </span>

          <button
            type="button"
            @click="carregarHistorico(false, page + 1)"
            :disabled="page >= totalPages"
            class="h-10 rounded-2xl bg-white px-4 text-sm font-black text-slate-700 shadow-sm transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Próxima
          </button>
        </div>
      </section>

      <!-- Empty -->
      <section
        v-else
        class="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-10 text-center"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">📜</div>
        <h3 class="mt-5 text-xl font-black text-slate-950">Nenhum histórico encontrado</h3>
        <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">As contas fechadas aparecerão aqui.</p>
      </section>

    </template>

    <!-- Modal Detalhes -->
    <div
      v-if="contaSelecionada"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="contaSelecionada = null"
    >
      <div class="max-h-[90vh] w-full max-w-2xl overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <h3 class="text-xl font-black text-slate-950">Conta #{{ contaSelecionada.id }}</h3>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              {{ contaSelecionada.mesa?.numero }} · {{ formatDateTime(contaSelecionada.fechada_em) }}
            </p>
          </div>

          <button
            type="button"
            @click="contaSelecionada = null"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </header>

        <div class="max-h-[calc(90vh-100px)] overflow-y-auto p-5">
          <div class="space-y-3">
            <article
              v-for="item in contaSelecionada.items"
              :key="item.id"
              class="rounded-2xl bg-slate-50 p-4"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-black text-slate-950">{{ item.quantidade }}x {{ item.nome }}</p>
                  <p class="mt-1 text-xs font-semibold text-slate-500">
                    {{ item.origem === 'pos' ? 'Produto POS' : 'Produto loja Bendi' }}
                  </p>
                </div>
                <p class="font-black text-slate-950">{{ money(item.preco_total) }}</p>
              </div>
            </article>
          </div>

          <div class="mt-5 rounded-2xl bg-slate-950 p-5 text-white">
            <div class="flex justify-between text-sm font-bold text-slate-300">
              <span>Subtotal</span>
              <span>{{ money(contaSelecionada.subtotal) }}</span>
            </div>
            <div
              v-if="Number(contaSelecionada.taxa_servico_valor) > 0"
              class="mt-2 flex justify-between text-sm font-bold text-slate-300"
            >
              <span>Taxa ({{ contaSelecionada.taxa_servico_percentagem }}%)</span>
              <span>{{ money(contaSelecionada.taxa_servico_valor) }}</span>
            </div>
            <div class="mt-3 flex justify-between text-xl font-black">
              <span>Total</span>
              <span>{{ money(contaSelecionada.total) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'POSHistorico',

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
      historico: [],
      loading: false,
      error: '',
      page: 1,
      limit: 20,
      totalCount: 0,
      contaSelecionada: null,

      filtros: {
        dataInicio:       '',
        dataFim:          '',
        metodoPagamento:  ''
      }
    }
  },

  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.totalCount / this.limit))
    },

    // Conta principal → sempre pode. Membro → verificar permissão.
    podeVerRelatorios() {
      if (!this.isMembro) return true
      return this.permissoes?.pode_ver_relatorios ?? false
    },
  },

  created() {
    // Só carregar se tiver permissão
    if (!this.isMembro || this.podeVerRelatorios) {
      const hoje    = new Date()
      const ha30    = new Date()
      ha30.setDate(hoje.getDate() - 30)
      this.filtros.dataInicio = ha30.toISOString().split('T')[0]
      this.filtros.dataFim    = hoje.toISOString().split('T')[0]
      this.carregarHistorico()
    }
  },

  methods: {
    async carregarHistorico(reset = false, novaPagina = this.page) {
      if (!this.podeVerRelatorios) return

      if (reset) {
        this.page    = 1
        novaPagina   = 1
      } else {
        this.page = novaPagina
      }

      this.loading = true
      this.error   = ''

      try {
        const params = {
          offset: (this.page - 1) * this.limit,
          limit:  this.limit
        }

        if (this.filtros.dataInicio)       params.data_inicio = this.filtros.dataInicio
        if (this.filtros.dataFim)          params.data_fim    = this.filtros.dataFim
        if (this.filtros.metodoPagamento)  params.metodo      = this.filtros.metodoPagamento

        const { data } = await api.get(`/api/pos/${this.posId}/historico/`, { params })

        this.historico  = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : [])
        this.totalCount = data.count || this.historico.length
      } catch (err) {
        this.error = err.response?.status === 404
          ? 'Endpoint de histórico não encontrado.'
          : err.response?.data?.detail || 'Erro ao carregar histórico.'
      } finally {
        this.loading = false
      }
    },

    verDetalhes(conta) {
      this.contaSelecionada = conta
    },

    getMetodoBadge(metodo) {
      return {
        dinheiro:     'bg-green-100 text-green-800',
        cartao:       'bg-blue-100 text-blue-800',
        mbway:        'bg-purple-100 text-purple-800',
        transferencia:'bg-orange-100 text-orange-800',
        dividida:     'bg-slate-100 text-slate-800',
      }[metodo] || 'bg-slate-100 text-slate-800'
    },

    getMetodoLabel(metodo) {
      return {
        dinheiro:     'Dinheiro',
        cartao:       'Cartão',
        mbway:        'MBWay',
        transferencia:'Transferência',
        dividida:     'Dividida',
      }[metodo] || metodo || '—'
    },

    formatDateTime(timestamp) {
      if (!timestamp) return ''
      return new Date(timestamp).toLocaleString('pt-PT', {
        day:    '2-digit',
        month:  '2-digit',
        year:   'numeric',
        hour:   '2-digit',
        minute: '2-digit'
      })
    },

    money(value) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(value || 0))
    }
  }
}
</script>