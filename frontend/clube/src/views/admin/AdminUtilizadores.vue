<template>
  <div class="space-y-5">

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 items-center">
      <div class="relative flex-1 min-w-48">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="q" @input="debouncedFetch" placeholder="Pesquisar utilizador..."
          class="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
      </div>
      <select v-model="filtroVerificado" @change="fetchUtilizadores(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todos</option>
        <option value="true">Verificados</option>
        <option value="false">Nao verificados</option>
      </select>
      <select v-model="filtroStatus" @change="fetchUtilizadores(1)"
        class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
        <option value="">Todos os estados</option>
        <option value="ativo">Activos</option>
        <option value="banido">Banidos</option>
        <option value="suspenso">Suspensos</option>
      </select>
      <p class="text-xs text-zinc-500 ml-auto">{{ totalCount }} utilizadores</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista -->
    <div v-else class="space-y-2">
      <div v-for="u in utilizadores" :key="u.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4 group">

        <img v-if="u.foto_url" :src="u.foto_url" :alt="u.username"
             class="w-10 h-10 rounded-full object-cover flex-shrink-0" />
        <div v-else class="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
          <span class="text-zinc-400 text-sm font-bold">{{ u.username.charAt(0).toUpperCase() }}</span>
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <p class="text-sm font-bold text-zinc-200">{{ u.username }}</p>
            <span v-if="u.verificado" class="px-1.5 py-0.5 bg-green-500/15 text-green-400 text-[10px] rounded font-bold">✓ Verificado</span>
            <span v-if="u.is_staff" class="px-1.5 py-0.5 bg-red-500/15 text-red-400 text-[10px] rounded font-bold">Staff</span>
            <span v-if="u.role_admin" class="px-1.5 py-0.5 bg-purple-500/15 text-purple-400 text-[10px] rounded font-bold capitalize">{{ u.role_admin }}</span>
            <span v-if="u.status !== 'ativo'" :class="['px-1.5 py-0.5 text-[10px] rounded font-bold', u.status === 'banido' ? 'bg-red-500/15 text-red-400' : 'bg-yellow-500/15 text-yellow-400']">
              {{ u.status }}
            </span>
          </div>
          <p class="text-xs text-zinc-500">{{ u.email }} · {{ u.total_lojas }} lojas · desde {{ u.data_criacao }}</p>
        </div>

        <div class="flex gap-2 flex-shrink-0 opacity-100 group-hover:opacity-100 transition">
          <button @click="toggleVerificado(u)" :title="u.verificado ? 'Remover verificacao' : 'Verificar'"
            :class="['w-8 h-8 rounded-lg flex items-center justify-center transition text-xs',
                     u.verificado ? 'bg-green-500/15 text-green-400 hover:bg-green-500/25' : 'bg-zinc-800 text-zinc-500 hover:text-green-400']">✓</button>
          <button @click="toggleBan(u)" :title="u.status === 'banido' ? 'Remover ban' : 'Banir'"
            :class="['w-8 h-8 rounded-lg flex items-center justify-center transition text-xs',
                     u.status === 'banido' ? 'bg-red-500/15 text-red-400 hover:bg-red-500/25' : 'bg-zinc-800 text-zinc-500 hover:text-red-400']">🚫</button>
          <button @click="abrirEditarRole(u)"
            class="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-500 hover:text-purple-400 flex items-center justify-center transition text-xs">⚙️</button>
        </div>
      </div>

      <div v-if="utilizadores.length === 0" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Nenhum utilizador encontrado.
      </div>
    </div>

    <!-- Paginacao com números -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchUtilizadores(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchUtilizadores(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchUtilizadores(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>
    </div>

    <!-- Modal editar role -->
    <div v-if="editandoRole"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="editandoRole = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 space-y-4">
        <h3 class="text-base font-bold text-zinc-100">Editar role — {{ editandoRole.username }}</h3>
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Role de admin</label>
          <select v-model="novaRole"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition">
            <option value="">Sem role (utilizador normal)</option>
            <option value="superadmin">Super Admin</option>
            <option value="moderador">Moderador</option>
            <option value="suporte">Suporte</option>
            <option value="contabilista">Contabilista</option>
          </select>
        </div>
        <div class="flex gap-3">
          <button @click="editandoRole = null"
            class="flex-1 py-2 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="guardarRole"
            class="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition">
            Guardar
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'
export default {
  name: 'AdminUtilizadores',
  data () {
    return {
      loading: true, utilizadores: [], totalCount: 0,
      page: 1, limit: 20,
      q: '', filtroVerificado: '', filtroStatus: '',
      debounceTimer: null,
      editandoRole: null, novaRole: '',
    }
  },
  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
  },
  async created () { await this.fetchUtilizadores() },
  methods: {
    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchUtilizadores(1), 350)
    },
    async fetchUtilizadores (pagina = this.page) {
      this.page = pagina; this.loading = true
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.q) params.q = this.q
        if (this.filtroVerificado !== '') params.verificado = this.filtroVerificado
        if (this.filtroStatus) params.status = this.filtroStatus
        const { data } = await api.get('/app/admin/utilizadores/', { params })
        this.utilizadores = data.results || data
        this.totalCount   = data.count ?? this.utilizadores.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async toggleVerificado (u) {
      try { const { data } = await api.patch(`/app/admin/utilizadores/${u.id}/`, { verificado: !u.verificado }); u.verificado = data.verificado } catch (e) { console.error(e) }
    },
    async toggleBan (u) {
      const novoStatus = u.status === 'banido' ? 'ativo' : 'banido'
      try { const { data } = await api.patch(`/app/admin/utilizadores/${u.id}/`, { status: novoStatus }); u.status = data.status } catch (e) { console.error(e) }
    },
    abrirEditarRole (u) { this.editandoRole = u; this.novaRole = u.role_admin || '' },
    async guardarRole () {
      try {
        const payload = this.novaRole ? { role_admin: this.novaRole } : { role_admin: null, is_staff: false }
        const { data } = await api.patch(`/app/admin/utilizadores/${this.editandoRole.id}/`, payload)
        this.editandoRole.role_admin = data.role_admin
        this.editandoRole.is_staff   = data.is_staff
        this.editandoRole = null
      } catch (e) { console.error(e) }
    },
  },
}
</script>