<template>
  <div class="space-y-5">
    <!-- Header com botão adicionar -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-black text-slate-950">
          Gestão de Equipa
        </h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          Adiciona e gere os membros que têm acesso a este POS
        </p>
      </div>

      <button
        type="button"
        @click="showAddModal = true"
        class="flex h-12 items-center justify-center gap-2 rounded-2xl bg-slate-950 px-6 text-sm font-black text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Adicionar Membro
      </button>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
    </div>

    <!-- Erro -->
    <div
      v-else-if="error"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
    >
      {{ error }}
    </div>

    <!-- Lista de membros -->
    <div v-else class="space-y-4">
      <!-- Stats -->
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <p class="text-xs font-bold text-slate-500">Total</p>
          <p class="mt-1 text-2xl font-black text-slate-950">{{ membros.length }}</p>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-emerald-50 p-4">
          <p class="text-xs font-bold text-emerald-700">Ativos</p>
          <p class="mt-1 text-2xl font-black text-emerald-900">{{ membrosAtivos }}</p>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-blue-50 p-4">
          <p class="text-xs font-bold text-blue-700">Gerentes</p>
          <p class="mt-1 text-2xl font-black text-blue-900">{{ membrosPorPapel.gerente || 0 }}</p>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-purple-50 p-4">
          <p class="text-xs font-bold text-purple-700">Empregados</p>
          <p class="mt-1 text-2xl font-black text-purple-900">{{ membrosPorPapel.empregado || 0 }}</p>
        </div>
      </div>

      <!-- Tabela/Cards -->
      <div class="space-y-3">
        <div
          v-for="membro in membros"
          :key="membro.id"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <!-- Info do membro -->
            <div class="flex items-center gap-4">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-slate-200 text-lg font-black text-slate-700">
                {{ membro.utilizador.nome.charAt(0).toUpperCase() }}
              </div>

              <div class="min-w-0">
                <h3 class="truncate font-black text-slate-950">
                  {{ membro.utilizador.nome }}
                </h3>
                <p class="truncate text-sm font-semibold text-slate-500">
                  {{ membro.utilizador.email }}
                </p>
                <div class="mt-1 flex items-center gap-2">
                  <span
                    :class="[
                      'inline-flex rounded-full px-2 py-0.5 text-xs font-black',
                      papelBadgeClass(membro.papel)
                    ]"
                  >
                    {{ membro.papel_display }}
                  </span>
                  <span
                    v-if="!membro.ativo"
                    class="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-black text-red-700"
                  >
                    Inativo
                  </span>
                </div>
              </div>
            </div>

            <!-- Ações -->
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                @click="verPermissoes(membro)"
                class="h-10 rounded-2xl border border-slate-200 bg-white px-4 text-sm font-black text-slate-700 transition hover:bg-slate-50"
              >
                Ver Permissões
              </button>

              <button
                v-if="membro.papel !== 'dono'"
                type="button"
                @click="editarMembro(membro)"
                class="h-10 rounded-2xl bg-blue-600 px-4 text-sm font-black text-white transition hover:bg-blue-700"
              >
                Editar
              </button>

              <button
                v-if="membro.papel !== 'dono' && membro.ativo"
                type="button"
                @click="confirmarRemover(membro)"
                class="h-10 rounded-2xl bg-red-50 px-4 text-sm font-black text-red-700 transition hover:bg-red-100"
              >
                Remover
              </button>
            </div>
          </div>

          <!-- Permissões resumo (colapsável) -->
          <div
            v-if="membro.id === membroExpandido"
            class="mt-4 grid grid-cols-1 gap-2 rounded-xl bg-slate-50 p-4 sm:grid-cols-2"
          >
            <div
              v-for="(valor, chave) in membro.permissoes"
              :key="chave"
              class="flex items-center justify-between text-sm"
            >
              <span class="font-semibold text-slate-600">{{ formatarPermissao(chave) }}</span>
              <span v-if="valor" class="font-black text-emerald-600">✓</span>
              <span v-else class="font-black text-slate-300">✗</span>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-if="membros.length === 0"
          class="rounded-2xl border border-slate-200 bg-white p-12 text-center"
        >
          <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-3xl">
            👥
          </div>
          <h3 class="mt-4 text-lg font-black text-slate-950">
            Nenhum membro ainda
          </h3>
          <p class="mt-2 text-sm text-slate-500">
            Adiciona o primeiro membro da equipa do POS
          </p>
        </div>
      </div>
    </div>

    <!-- Modal Adicionar Membro -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      @click.self="showAddModal = false"
    >
      <div class="w-full max-w-lg overflow-hidden rounded-[2rem] bg-white shadow-2xl">
        <header class="border-b border-slate-200 p-5">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-xl font-black text-slate-950">Adicionar Membro</h3>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                Convida um utilizador para a equipa do POS
              </p>
            </div>
            <button
              type="button"
              @click="showAddModal = false"
              class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200"
            >
              ×
            </button>
          </div>
        </header>

        <form class="space-y-4 p-5" @submit.prevent="adicionarMembro">
          <div
            v-if="addError"
            class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
          >
            {{ addError }}
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Email do utilizador
            </label>
            <input
              v-model.trim="addForm.email"
              type="email"
              placeholder="colaborador@exemplo.com"
              required
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
            <p class="mt-2 text-xs font-semibold text-slate-400">
              O utilizador precisa ter conta Bendi registada
            </p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Papel
            </label>

            <div class="grid grid-cols-2 gap-3">
              <label
                v-for="papel in papeisDisponiveis"
                :key="papel.value"
                :class="[
                  'cursor-pointer rounded-2xl border-2 p-3 transition',
                  addForm.papel === papel.value
                    ? 'border-slate-950 bg-slate-950 text-white shadow-lg'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                ]"
              >
                <input
                  v-model="addForm.papel"
                  type="radio"
                  :value="papel.value"
                  class="hidden"
                />
                <p class="text-sm font-black">{{ papel.label }}</p>
                <p
                  :class="[
                    'mt-1 text-xs font-semibold',
                    addForm.papel === papel.value ? 'text-slate-300' : 'text-slate-500'
                  ]"
                >
                  {{ papel.description }}
                </p>
              </label>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 pt-2">
            <button
              type="button"
              @click="showAddModal = false"
              class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
            >
              Cancelar
            </button>

            <button
              type="submit"
              :disabled="adding"
              class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span v-if="!adding">Adicionar</span>
              <span v-else class="flex items-center gap-2">
                <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                A adicionar...
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Editar Membro -->
    <div
      v-if="showEditModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      @click.self="showEditModal = false"
    >
      <div class="w-full max-w-lg overflow-hidden rounded-[2rem] bg-white shadow-2xl">
        <header class="border-b border-slate-200 p-5">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-xl font-black text-slate-950">Editar Membro</h3>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                {{ membroEditando?.utilizador.nome }}
              </p>
            </div>
            <button
              type="button"
              @click="showEditModal = false"
              class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200"
            >
              ×
            </button>
          </div>
        </header>

        <form class="space-y-4 p-5" @submit.prevent="salvarEdicao">
          <div
            v-if="editError"
            class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
          >
            {{ editError }}
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">
              Papel
            </label>

            <div class="grid grid-cols-2 gap-3">
              <label
                v-for="papel in papeisDisponiveis"
                :key="papel.value"
                :class="[
                  'cursor-pointer rounded-2xl border-2 p-3 transition',
                  editForm.papel === papel.value
                    ? 'border-slate-950 bg-slate-950 text-white shadow-lg'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                ]"
              >
                <input
                  v-model="editForm.papel"
                  type="radio"
                  :value="papel.value"
                  class="hidden"
                />
                <p class="text-sm font-black">{{ papel.label }}</p>
                <p
                  :class="[
                    'mt-1 text-xs font-semibold',
                    editForm.papel === papel.value ? 'text-slate-300' : 'text-slate-500'
                  ]"
                >
                  {{ papel.description }}
                </p>
              </label>
            </div>
          </div>

          <!-- Permissões customizadas (opcional) -->
          <details class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <summary class="cursor-pointer font-black text-slate-700">
              Permissões personalizadas (avançado)
            </summary>
            <div class="mt-3 space-y-2">
              <label
                v-for="(valor, chave) in editForm.permissoes"
                :key="chave"
                class="flex items-center justify-between py-2"
              >
                <span class="text-sm font-semibold text-slate-600">
                  {{ formatarPermissao(chave) }}
                </span>
                <input
                  v-model="editForm.permissoes[chave]"
                  type="checkbox"
                  class="h-5 w-5 rounded border-slate-300 text-slate-950 focus:ring-2 focus:ring-slate-950"
                />
              </label>
            </div>
          </details>

          <div class="grid grid-cols-2 gap-3 pt-2">
            <button
              type="button"
              @click="showEditModal = false"
              class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
            >
              Cancelar
            </button>

            <button
              type="submit"
              :disabled="editing"
              class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span v-if="!editing">Guardar</span>
              <span v-else class="flex items-center gap-2">
                <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                A guardar...
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'POSEquipa',

  props: {
    posId: {
      type: Number,
      required: true
    }
  },

  data() {
    return {
      loading: false,
      error: null,
      membros: [],
      membroExpandido: null,

      showAddModal: false,
      adding: false,
      addError: null,
      addForm: {
        email: '',
        papel: 'empregado'
      },

      showEditModal: false,
      editing: false,
      editError: null,
      membroEditando: null,
      editForm: {
        papel: '',
        permissoes: {}
      },

      papeisDisponiveis: [
        {
          value: 'gerente',
          label: 'Gerente',
          description: 'Acesso total exceto gerir utilizadores'
        },
        {
          value: 'empregado',
          label: 'Empregado',
          description: 'Abre mesas e vê pedidos'
        },
        {
          value: 'cozinha',
          label: 'Cozinha',
          description: 'Vê e atualiza status de pedidos'
        },
        {
          value: 'caixa',
          label: 'Caixa',
          description: 'Fecha contas e gere turno'
        }
      ]
    }
  },

  computed: {
    membrosAtivos() {
      return this.membros.filter(m => m.ativo).length
    },

    membrosPorPapel() {
      return this.membros.reduce((acc, m) => {
        acc[m.papel] = (acc[m.papel] || 0) + 1
        return acc
      }, {})
    }
  },

  created() {
    this.carregarEquipa()
  },

  methods: {
    async carregarEquipa() {
      this.loading = true
      this.error = null

      try {
        const { data } = await api.get(`/api/pos/${this.posId}/equipa/`)
        this.membros = data
      } catch (err) {
        console.error('Erro ao carregar equipa:', err)
        this.error = err.response?.data?.detail || 'Erro ao carregar equipa'
      } finally {
        this.loading = false
      }
    },

    async adicionarMembro() {
      if (!this.addForm.email) return

      this.adding = true
      this.addError = null

      try {
        const { data } = await api.post(`/api/pos/${this.posId}/equipa/`, {
          email: this.addForm.email,
          papel: this.addForm.papel
        })

        this.membros.push(data)
        this.showAddModal = false
        this.addForm = { email: '', papel: 'empregado' }
      } catch (err) {
        console.error('Erro ao adicionar membro:', err)
        this.addError = err.response?.data?.detail || 'Erro ao adicionar membro'
      } finally {
        this.adding = false
      }
    },

    editarMembro(membro) {
      this.membroEditando = membro
      this.editForm = {
        papel: membro.papel,
        permissoes: { ...membro.permissoes }
      }
      this.editError = null
      this.showEditModal = true
    },

    async salvarEdicao() {
      if (!this.membroEditando) return

      this.editing = true
      this.editError = null

      try {
        const { data } = await api.patch(
          `/api/pos/${this.posId}/equipa/${this.membroEditando.id}/`,
          {
            papel: this.editForm.papel,
            ...this.editForm.permissoes
          }
        )

        const index = this.membros.findIndex(m => m.id === this.membroEditando.id)
        if (index !== -1) {
          this.membros.splice(index, 1, data)
        }

        this.showEditModal = false
        this.membroEditando = null
      } catch (err) {
        console.error('Erro ao editar membro:', err)
        this.editError = err.response?.data?.detail || 'Erro ao editar membro'
      } finally {
        this.editing = false
      }
    },

    async confirmarRemover(membro) {
      if (!confirm(`Tem certeza que deseja remover ${membro.utilizador.nome} da equipa?`)) {
        return
      }

      try {
        await api.delete(`/api/pos/${this.posId}/equipa/${membro.id}/`)

        const index = this.membros.findIndex(m => m.id === membro.id)
        if (index !== -1) {
          this.membros.splice(index, 1)
        }
      } catch (err) {
        console.error('Erro ao remover membro:', err)
        alert(err.response?.data?.detail || 'Erro ao remover membro')
      }
    },

    verPermissoes(membro) {
      if (this.membroExpandido === membro.id) {
        this.membroExpandido = null
      } else {
        this.membroExpandido = membro.id
      }
    },

    papelBadgeClass(papel) {
      const classes = {
        dono: 'bg-purple-100 text-purple-700',
        gerente: 'bg-blue-100 text-blue-700',
        empregado: 'bg-emerald-100 text-emerald-700',
        cozinha: 'bg-orange-100 text-orange-700',
        caixa: 'bg-cyan-100 text-cyan-700'
      }
      return classes[papel] || 'bg-slate-100 text-slate-700'
    },

    formatarPermissao(chave) {
      const nomes = {
        pode_abrir_mesas: 'Abrir mesas',
        pode_fechar_contas: 'Fechar contas',
        pode_cancelar_items: 'Cancelar items',
        pode_dar_descontos: 'Dar descontos',
        pode_gerir_produtos: 'Gerir produtos',
        pode_gerir_mesas: 'Gerir mesas',
        pode_gerir_utilizadores: 'Gerir utilizadores',
        pode_ver_relatorios: 'Ver relatórios',
        pode_abrir_fechar_turno: 'Abrir/Fechar turno',
        pode_ver_pedidos: 'Ver pedidos',
        pode_atualizar_status_items: 'Atualizar status'
      }
      return nomes[chave] || chave
    }
  }
}
</script>