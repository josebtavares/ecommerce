<template>
  <div class="space-y-5">

    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-black text-slate-950">Gestão de Equipa</h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          Cria e gere os membros que acedem a este POS
        </p>
      </div>

      <button
        type="button"
        @click="abrirModalAdicionar"
        class="flex h-12 items-center justify-center gap-2 rounded-2xl bg-slate-950 px-6 text-sm font-black text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Novo Membro
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
    </div>

    <!-- Erro -->
    <div
      v-else-if="error"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
    >
      {{ error }}
    </div>

    <!-- Conteúdo -->
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
          <p class="mt-1 text-2xl font-black text-blue-900">{{ contagemPapel('gerente') }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-purple-50 p-4">
          <p class="text-xs font-bold text-purple-700">Empregados</p>
          <p class="mt-1 text-2xl font-black text-purple-900">{{ contagemPapel('empregado') }}</p>
        </div>
      </div>

      <!-- Lista de membros -->
      <div class="space-y-3">
        <div
          v-for="membro in membros"
          :key="membro.id"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

            <!-- Info -->
            <div class="flex items-center gap-4">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-slate-950 text-lg font-black text-white">
                {{ membro.nome.charAt(0).toUpperCase() }}
              </div>

              <div class="min-w-0">
                <h3 class="truncate font-black text-slate-950">{{ membro.nome }}</h3>
                <p class="truncate text-sm font-semibold text-slate-400">@{{ membro.username_pos }}</p>
                <div class="mt-1 flex flex-wrap items-center gap-2">
                  <span
                    :class="['inline-flex rounded-full px-2 py-0.5 text-xs font-black', papelBadgeClass(membro.papel)]"
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
                @click="togglePermissoes(membro.id)"
                class="h-10 rounded-2xl border border-slate-200 bg-white px-4 text-sm font-black text-slate-700 transition hover:bg-slate-50"
              >
                {{ membroExpandido === membro.id ? 'Fechar' : 'Permissões' }}
              </button>

              <button
                type="button"
                @click="abrirModalEditar(membro)"
                class="h-10 rounded-2xl bg-blue-600 px-4 text-sm font-black text-white transition hover:bg-blue-700"
              >
                Editar
              </button>

              <button
                type="button"
                @click="confirmarRemover(membro)"
                class="h-10 rounded-2xl bg-red-50 px-4 text-sm font-black text-red-700 transition hover:bg-red-100"
              >
                Remover
              </button>
            </div>
          </div>

          <!-- Permissões expandidas -->
          <div
            v-if="membroExpandido === membro.id"
            class="mt-4 grid grid-cols-1 gap-1 rounded-xl bg-slate-50 p-4 sm:grid-cols-2"
          >
            <div
              v-for="(valor, chave) in membro.permissoes"
              :key="chave"
              class="flex items-center justify-between py-1 text-sm"
            >
              <span class="font-semibold text-slate-600">{{ nomePermissao(chave) }}</span>
              <span :class="valor ? 'text-emerald-600' : 'text-slate-300'" class="font-black">
                {{ valor ? '✓' : '✗' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-if="membros.length === 0"
          class="rounded-2xl border border-slate-200 bg-white p-12 text-center"
        >
          <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-3xl">👥</div>
          <h3 class="mt-4 text-lg font-black text-slate-950">Sem membros ainda</h3>
          <p class="mt-2 text-sm text-slate-500">
            Cria o primeiro membro da equipa. Ele usará um username e password para entrar no POS.
          </p>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════
         MODAL: ADICIONAR MEMBRO
    ══════════════════════════════════════════════════════ -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharModalAdicionar"
    >
      <div class="w-full max-w-lg overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="border-b border-slate-200 p-5">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-xl font-black text-slate-950">Novo Membro</h3>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                O membro usará o username e password para entrar no POS
              </p>
            </div>
            <button
              type="button"
              @click="fecharModalAdicionar"
              class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200"
            >
              ×
            </button>
          </div>
        </header>

        <div class="max-h-[70vh] overflow-y-auto sm:max-h-none">
          <form class="space-y-4 p-5" @submit.prevent="adicionarMembro">

            <!-- Erro / Sucesso -->
            <div
              v-if="addError"
              class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
            >
              {{ addError }}
            </div>

            <!-- Password gerada (mostrar e manter modal aberto) -->
            <div
              v-if="addSuccess"
              class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4"
            >
              <p class="text-sm font-black text-emerald-800">✓ Membro criado com sucesso!</p>
              <div
                v-if="addSuccess.password_gerada"
                class="mt-3 rounded-xl bg-emerald-100 p-3"
              >
                <p class="text-xs font-bold text-emerald-700">Password gerada automaticamente:</p>
                <p class="mt-1 font-mono text-lg font-black tracking-widest text-emerald-900">
                  {{ addSuccess.password_gerada }}
                </p>
                <p class="mt-1 text-xs font-semibold text-emerald-600">
                  Anota esta password — não será mostrada novamente.
                </p>
                <button
                  type="button"
                  @click="copiarPassword(addSuccess.password_gerada)"
                  class="mt-2 rounded-xl bg-emerald-700 px-3 py-1.5 text-xs font-black text-white"
                >
                  {{ copiado ? '✓ Copiado!' : 'Copiar' }}
                </button>
              </div>
              <button
                type="button"
                @click="fecharModalAdicionar"
                class="mt-3 h-10 w-full rounded-2xl bg-slate-950 text-sm font-black text-white"
              >
                Fechar
              </button>
            </div>

            <!-- Formulário (esconder após sucesso) -->
            <template v-if="!addSuccess">
              <!-- Nome -->
              <div>
                <label class="mb-2 block text-sm font-black text-slate-700">Nome completo</label>
                <input
                  v-model.trim="addForm.nome"
                  type="text"
                  placeholder="Ex: Joana Silva"
                  required
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
              </div>

              <!-- Username -->
              <div>
                <label class="mb-2 block text-sm font-black text-slate-700">Username</label>
                <div class="relative">
                  <span class="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-black text-slate-400">@</span>
                  <input
                    v-model.trim="addForm.username_pos"
                    type="text"
                    placeholder="joana"
                    required
                    minlength="3"
                    pattern="[a-zA-Z0-9_.]*"
                    class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 pl-8 pr-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                  />
                </div>
                <p class="mt-1.5 text-xs font-semibold text-slate-400">
                  Letras, números, _ e . · Único neste POS
                </p>
              </div>

              <!-- Password -->
              <div>
                <label class="mb-2 block text-sm font-black text-slate-700">
                  Password
                  <span class="ml-1 text-xs font-semibold text-slate-400">(opcional — gera automaticamente)</span>
                </label>
                <input
                  v-model="addForm.password"
                  type="text"
                  placeholder="Deixa vazio para gerar"
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 font-mono text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
              </div>

              <!-- Papel -->
              <div>
                <label class="mb-2 block text-sm font-black text-slate-700">Papel</label>
                <div class="grid grid-cols-2 gap-3">
                  <label
                    v-for="p in papeisDisponiveis"
                    :key="p.value"
                    :class="[
                      'cursor-pointer rounded-2xl border-2 p-3 transition',
                      addForm.papel === p.value
                        ? 'border-slate-950 bg-slate-950 text-white shadow-lg'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                    ]"
                  >
                    <input v-model="addForm.papel" type="radio" :value="p.value" class="hidden" />
                    <p class="text-sm font-black">{{ p.label }}</p>
                    <p :class="['mt-1 text-xs font-semibold', addForm.papel === p.value ? 'text-slate-300' : 'text-slate-500']">
                      {{ p.description }}
                    </p>
                  </label>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  @click="fecharModalAdicionar"
                  class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  :disabled="adding"
                  class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
                >
                  <span v-if="!adding">Criar Membro</span>
                  <span v-else class="flex items-center gap-2">
                    <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                    A criar...
                  </span>
                </button>
              </div>
            </template>
          </form>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════
         MODAL: EDITAR MEMBRO
    ══════════════════════════════════════════════════════ -->
    <div
      v-if="showEditModal"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharModalEditar"
    >
      <div class="w-full max-w-lg overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="border-b border-slate-200 p-5">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-xl font-black text-slate-950">Editar Membro</h3>
              <p class="mt-1 text-sm font-semibold text-slate-500">{{ membroEditando?.nome }}</p>
            </div>
            <button
              type="button"
              @click="fecharModalEditar"
              class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200"
            >
              ×
            </button>
          </div>
        </header>

        <div class="max-h-[70vh] overflow-y-auto sm:max-h-none">
          <form class="space-y-4 p-5" @submit.prevent="salvarEdicao">

            <div
              v-if="editError"
              class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
            >
              {{ editError }}
            </div>

            <!-- Nome -->
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Nome completo</label>
              <input
                v-model.trim="editForm.nome"
                type="text"
                required
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
            </div>

            <!-- Username -->
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Username</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-black text-slate-400">@</span>
                <input
                  v-model.trim="editForm.username_pos"
                  type="text"
                  required
                  minlength="3"
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 pl-8 pr-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
              </div>
            </div>

            <!-- Nova password (opcional) -->
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">
                Nova password
                <span class="ml-1 text-xs font-semibold text-slate-400">(deixa vazio para não alterar)</span>
              </label>
              <input
                v-model="editForm.password"
                type="text"
                placeholder="••••••••"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 font-mono text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
            </div>

            <!-- Papel -->
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Papel</label>
              <div class="grid grid-cols-2 gap-3">
                <label
                  v-for="p in papeisDisponiveis"
                  :key="p.value"
                  :class="[
                    'cursor-pointer rounded-2xl border-2 p-3 transition',
                    editForm.papel === p.value
                      ? 'border-slate-950 bg-slate-950 text-white shadow-lg'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                  ]"
                >
                  <input v-model="editForm.papel" type="radio" :value="p.value" class="hidden" />
                  <p class="text-sm font-black">{{ p.label }}</p>
                  <p :class="['mt-1 text-xs font-semibold', editForm.papel === p.value ? 'text-slate-300' : 'text-slate-500']">
                    {{ p.description }}
                  </p>
                </label>
              </div>
            </div>

            <!-- Permissões customizadas -->
            <details class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <summary class="cursor-pointer text-sm font-black text-slate-700">
                Permissões personalizadas (avançado)
              </summary>
              <div class="mt-3 space-y-1">
                <label
                  v-for="(valor, chave) in editForm.permissoes"
                  :key="chave"
                  class="flex items-center justify-between py-1.5"
                >
                  <span class="text-sm font-semibold text-slate-600">{{ nomePermissao(chave) }}</span>
                  <input
                    v-model="editForm.permissoes[chave]"
                    type="checkbox"
                    class="h-5 w-5 rounded border-slate-300 accent-slate-950"
                  />
                </label>
              </div>
            </details>

            <!-- Ativo/Inativo -->
            <label class="flex cursor-pointer items-center justify-between rounded-2xl border border-slate-200 bg-white p-4">
              <span class="text-sm font-black text-slate-700">Membro ativo</span>
              <input v-model="editForm.ativo" type="checkbox" class="h-5 w-5 rounded border-slate-300 accent-slate-950" />
            </label>

            <div class="grid grid-cols-2 gap-3 pt-2">
              <button
                type="button"
                @click="fecharModalEditar"
                class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="editing"
                class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
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

  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'POSEquipa',

  props: {
    posId: { type: Number, required: true },
  },

  data() {
    return {
      loading: false,
      error: null,
      membros: [],
      membroExpandido: null,

      // Modal adicionar
      showAddModal: false,
      adding: false,
      addError: null,
      addSuccess: null,
      copiado: false,
      addForm: {
        nome: '',
        username_pos: '',
        password: '',
        papel: 'empregado',
      },

      // Modal editar
      showEditModal: false,
      editing: false,
      editError: null,
      membroEditando: null,
      editForm: {
        nome: '',
        username_pos: '',
        password: '',
        papel: 'empregado',
        ativo: true,
        permissoes: {},
      },

      papeisDisponiveis: [
        { value: 'gerente',   label: 'Gerente',   description: 'Acesso quase total' },
        { value: 'empregado', label: 'Empregado', description: 'Abre mesas e vê pedidos' },
        { value: 'cozinha',   label: 'Cozinha',   description: 'Vê e atualiza pedidos' },
        { value: 'caixa',     label: 'Caixa',     description: 'Fecha contas e turno' },
      ],
    }
  },

  computed: {
    membrosAtivos() {
      return this.membros.filter(m => m.ativo).length
    },
  },

  created() {
    this.carregarEquipa()
  },

  methods: {
    // ── API ────────────────────────────────────────────────────────
    async carregarEquipa() {
      this.loading = true
      this.error = null
      try {
        const { data } = await api.get(`/api/pos/${this.posId}/equipa/`)
        this.membros = data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao carregar equipa'
      } finally {
        this.loading = false
      }
    },

    async adicionarMembro() {
      this.adding = true
      this.addError = null

      try {
        const payload = {
          nome:        this.addForm.nome,
          username_pos: this.addForm.username_pos,
          papel:       this.addForm.papel,
        }
        if (this.addForm.password) {
          payload.password = this.addForm.password
        }

        const { data } = await api.post(`/api/pos/${this.posId}/equipa/`, payload)

        // Adicionar à lista
        this.membros.push(data)

        // Mostrar sucesso (com password se foi gerada)
        this.addSuccess = {
          password_gerada: data.password_gerada || null,
        }
      } catch (err) {
        this.addError = err.response?.data?.detail || 'Erro ao criar membro'
      } finally {
        this.adding = false
      }
    },

    async salvarEdicao() {
      this.editing = true
      this.editError = null

      try {
        const payload = {
          nome:        this.editForm.nome,
          username_pos: this.editForm.username_pos,
          papel:       this.editForm.papel,
          ativo:       this.editForm.ativo,
          ...this.editForm.permissoes,
        }
        if (this.editForm.password) {
          payload.password = this.editForm.password
        }

        const { data } = await api.patch(
          `/api/pos/${this.posId}/equipa/${this.membroEditando.id}/`,
          payload
        )

        const idx = this.membros.findIndex(m => m.id === this.membroEditando.id)
        if (idx !== -1) this.membros.splice(idx, 1, data)

        this.fecharModalEditar()
      } catch (err) {
        this.editError = err.response?.data?.detail || 'Erro ao guardar'
      } finally {
        this.editing = false
      }
    },

    async confirmarRemover(membro) {
      if (!confirm(`Remover "${membro.nome}" (@${membro.username_pos}) da equipa?`)) return

      try {
        await api.delete(`/api/pos/${this.posId}/equipa/${membro.id}/`)
        this.membros = this.membros.filter(m => m.id !== membro.id)
      } catch (err) {
        alert(err.response?.data?.detail || 'Erro ao remover membro')
      }
    },

    // ── MODAIS ─────────────────────────────────────────────────────
    abrirModalAdicionar() {
      this.addForm    = { nome: '', username_pos: '', password: '', papel: 'empregado' }
      this.addError   = null
      this.addSuccess = null
      this.copiado    = false
      this.showAddModal = true
    },

    fecharModalAdicionar() {
      this.showAddModal = false
      // Se criou membro com sucesso, recarregar lista
      if (this.addSuccess) this.carregarEquipa()
    },

    abrirModalEditar(membro) {
      this.membroEditando = membro
      this.editForm = {
        nome:        membro.nome,
        username_pos: membro.username_pos,
        password:    '',
        papel:       membro.papel,
        ativo:       membro.ativo,
        permissoes:  { ...membro.permissoes },
      }
      this.editError    = null
      this.showEditModal = true
    },

    fecharModalEditar() {
      this.showEditModal  = false
      this.membroEditando = null
    },

    // ── HELPERS ────────────────────────────────────────────────────
    togglePermissoes(id) {
      this.membroExpandido = this.membroExpandido === id ? null : id
    },

    contagemPapel(papel) {
      return this.membros.filter(m => m.papel === papel && m.ativo).length
    },

    papelBadgeClass(papel) {
      return {
        gerente:   'bg-blue-100 text-blue-700',
        empregado: 'bg-emerald-100 text-emerald-700',
        cozinha:   'bg-orange-100 text-orange-700',
        caixa:     'bg-cyan-100 text-cyan-700',
      }[papel] || 'bg-slate-100 text-slate-700'
    },

    nomePermissao(chave) {
      return {
        pode_abrir_mesas:         'Abrir mesas',
        pode_fechar_contas:       'Fechar contas',
        pode_cancelar_items:      'Cancelar items',
        pode_dar_descontos:       'Dar descontos',
        pode_gerir_produtos:      'Gerir produtos',
        pode_gerir_mesas:         'Gerir mesas',
        pode_gerir_utilizadores:  'Gerir utilizadores',
        pode_ver_relatorios:      'Ver relatórios',
        pode_abrir_fechar_turno:  'Abrir/Fechar turno',
        pode_ver_pedidos:         'Ver pedidos',
        pode_atualizar_status_items: 'Atualizar status',
      }[chave] || chave
    },

    async copiarPassword(pw) {
      try {
        await navigator.clipboard.writeText(pw)
        this.copiado = true
        setTimeout(() => { this.copiado = false }, 2000)
      } catch {
        // fallback silencioso
      }
    },
  },
}
</script>