<template>
  <div class="space-y-5 max-w-2xl">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Membros da equipa</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Gere quem tem acesso ao backoffice desta loja</p>
      </div>
      <button @click="abrirModal"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Adicionar membro
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 3" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista -->
    <div v-else class="space-y-3">
      <div v-for="membro in staff" :key="membro.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl overflow-hidden flex-shrink-0">
          <img v-if="membro.utilizador?.foto_url"
               :src="membro.utilizador.foto_url"
               :alt="membro.utilizador.username"
               class="w-full h-full object-cover" />
          <div v-else class="w-full h-full bg-zinc-700 flex items-center justify-center">
            <span class="text-sm font-bold text-zinc-300">
              {{ membro.utilizador?.nome?.charAt(0) || membro.utilizador?.username?.charAt(0) || '?' }}
            </span>
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-zinc-200">
            {{ membro.utilizador?.nome || membro.utilizador?.username }}
          </p>
          <p class="text-xs text-zinc-500">
            {{ membro.utilizador?.email || '@' + membro.utilizador?.username }}
          </p>
        </div>
        <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', roleColor(membro.role)]">
          {{ membro.role }}
        </span>
        <div v-if="membro.role !== 'dono'" class="flex items-center gap-2">
          <select :value="membro.role" @change="mudarRole(membro, $event.target.value)"
            class="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-300
                   focus:outline-none focus:border-red-500 transition">
            <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
          <button @click="removerMembro(membro)"
            class="w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
        <span v-else class="text-xs text-zinc-600 px-2">Dono</span>
      </div>

      <div v-if="staff.length === 0" class="text-center py-8 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Sem membros na equipa.
      </div>
    </div>

    <!-- Referência de permissões -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
      <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Permissões por role</h3>
      <div class="space-y-2">
        <div v-for="r in rolesInfo" :key="r.role" class="flex items-start gap-3">
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase flex-shrink-0 mt-0.5', roleColor(r.role)]">
            {{ r.role }}
          </span>
          <p class="text-xs text-zinc-500">{{ r.descricao }}</p>
        </div>
      </div>
    </div>

    <!-- Modal adicionar membro -->
    <div v-if="showModal"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="fecharModal">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 shadow-2xl">
        <h3 class="text-base font-bold text-zinc-100 mb-1">Adicionar membro</h3>
        <p class="text-xs text-zinc-500 mb-5">O utilizador já tem de ter conta na plataforma.</p>

        <div class="space-y-4">

          <!-- Pesquisa de utilizador -->
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Pesquisar utilizador</label>
            <div class="relative">
              <input
                v-model="pesquisaUtilizador"
                @input="debouncedPesquisa"
                type="text"
                placeholder="Username ou email..."
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       placeholder-zinc-500 focus:outline-none focus:border-red-500 transition pr-8" />
              <svg v-if="loadingPesquisa"
                   class="animate-spin h-4 w-4 text-zinc-500 absolute right-3 top-1/2 -translate-y-1/2"
                   viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
            </div>

            <!-- Resultados da pesquisa -->
            <div v-if="resultadosPesquisa.length > 0 && !utilizadorSelecionado"
                 class="mt-1 bg-zinc-800 rounded-xl border border-zinc-700 overflow-hidden">
              <button
                v-for="u in resultadosPesquisa" :key="u.id"
                @click="selecionarUtilizador(u)"
                class="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-zinc-700 transition text-left">
                <div class="w-7 h-7 rounded-lg bg-zinc-600 flex items-center justify-center flex-shrink-0">
                  <span class="text-xs font-bold text-zinc-300">{{ u.nome?.charAt(0) || u.username?.charAt(0) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-zinc-200 truncate">{{ u.nome }}</p>
                  <p class="text-xs text-zinc-500 truncate">@{{ u.username }} · {{ u.email }}</p>
                </div>
              </button>
            </div>

            <!-- Sem resultados -->
            <p v-if="pesquisaUtilizador.length >= 2 && resultadosPesquisa.length === 0 && !loadingPesquisa && !utilizadorSelecionado"
               class="text-xs text-zinc-500 mt-2 px-1">
              Nenhum utilizador encontrado.
            </p>
          </div>

          <!-- Utilizador seleccionado -->
          <div v-if="utilizadorSelecionado"
               class="flex items-center gap-3 p-3 bg-zinc-800 rounded-xl border border-red-500/40">
            <div class="w-8 h-8 rounded-lg bg-zinc-700 flex items-center justify-center flex-shrink-0">
              <span class="text-sm font-bold text-zinc-300">
                {{ utilizadorSelecionado.nome?.charAt(0) || '?' }}
              </span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-zinc-200">{{ utilizadorSelecionado.nome }}</p>
              <p class="text-xs text-zinc-500">@{{ utilizadorSelecionado.username }}</p>
            </div>
            <button @click="limparSeleccao" class="text-zinc-500 hover:text-zinc-300 transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Role -->
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Role</label>
            <select v-model="novoRole"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition">
              <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
            </select>
            <p class="text-xs text-zinc-600 mt-1">{{ rolesInfo.find(r => r.role === novoRole)?.descricao }}</p>
          </div>

          <p v-if="erroAdicionar" class="text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2">{{ erroAdicionar }}</p>
        </div>

        <div class="flex gap-3 mt-5">
          <button @click="fecharModal"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="adicionarMembro" :disabled="loadingAdicionar || !utilizadorSelecionado"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     loadingAdicionar || !utilizadorSelecionado
                       ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                       : 'bg-red-600 hover:bg-red-500 text-white']">
            <span v-if="loadingAdicionar" class="flex items-center gap-1">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              A adicionar…
            </span>
            <span v-else>Adicionar à equipa</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'BackofficeStaff',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: true,
      staff: [],
      showModal: false,
      loadingAdicionar: false,
      erroAdicionar: '',

      // pesquisa
      pesquisaUtilizador: '',
      resultadosPesquisa: [],
      loadingPesquisa: false,
      utilizadorSelecionado: null,
      novoRole: 'staff',
      debounceTimer: null,

      roles: [
        { value: 'gestor',       label: 'Gestor'       },
        { value: 'staff',        label: 'Staff'        },
        { value: 'contabilista', label: 'Contabilista' },
        { value: 'condutor',     label: 'Condutor'     },
      ],
      rolesInfo: [
        { role: 'dono',         descricao: 'Acesso total — todas as secções e configurações da loja.' },
        { role: 'gestor',       descricao: 'Quase tudo — produtos, encomendas, staff, entregas, pagamentos. Não pode apagar a loja.' },
        { role: 'staff',        descricao: 'Operações do dia-a-dia — gerir produtos, inventário e encomendas.' },
        { role: 'contabilista', descricao: 'Acesso financeiro — pagamentos e relatórios apenas.' },
        { role: 'condutor',     descricao: 'Gestão de entregas — só vê e actualiza o estado das entregas.' },
      ],
    }
  },

  async created () { await this.fetchStaff() },

  methods: {
    roleColor (role) {
      const map = {
        dono:         'bg-red-500/20 text-red-400',
        gestor:       'bg-orange-500/20 text-orange-400',
        staff:        'bg-blue-500/20 text-blue-400',
        contabilista: 'bg-green-500/20 text-green-400',
        condutor:     'bg-purple-500/20 text-purple-400',
      }
      return map[role] || 'bg-zinc-500/20 text-zinc-400'
    },

    abrirModal () {
      this.showModal = true
      this.erroAdicionar = ''
      this.pesquisaUtilizador = ''
      this.resultadosPesquisa = []
      this.utilizadorSelecionado = null
      this.novoRole = 'staff'
    },

    fecharModal () {
      this.showModal = false
      this.erroAdicionar = ''
      this.pesquisaUtilizador = ''
      this.resultadosPesquisa = []
      this.utilizadorSelecionado = null
    },

    limparSeleccao () {
      this.utilizadorSelecionado = null
      this.pesquisaUtilizador = ''
      this.resultadosPesquisa = []
    },

    debouncedPesquisa () {
      clearTimeout(this.debounceTimer)
      this.resultadosPesquisa = []
      if (this.pesquisaUtilizador.length < 2) return
      this.debounceTimer = setTimeout(() => this.pesquisarUtilizadores(), 400)
    },

    async pesquisarUtilizadores () {
      this.loadingPesquisa = true
      try {
        const { data } = await api.get(`/app/utilizador/search/?q=${encodeURIComponent(this.pesquisaUtilizador)}`)
        // filtra quem já está no staff
        const idsStaff = this.staff.map(m => m.utilizador?.id)
        this.resultadosPesquisa = data.filter(u => !idsStaff.includes(u.id))
      } catch (e) {
        console.error(e)
        this.resultadosPesquisa = []
      } finally {
        this.loadingPesquisa = false
      }
    },

    selecionarUtilizador (u) {
      this.utilizadorSelecionado = u
      this.resultadosPesquisa = []
      this.pesquisaUtilizador = ''
    },

    async fetchStaff () {
      this.loading = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/staff/`)
        this.staff = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

   async mudarRole (membro, novoRole) {
      const roleAnterior = membro.role
      try {
        await api.patch(`/app/loja/${this.lojaId}/staff/${membro.id}/`, { role: novoRole })
        membro.role = novoRole

      } catch (e) {
        if (e.response?.status === 409 && e.response.data.requer_confirmacao) {
          const n = e.response.data.entregas_activas
          const confirmar = confirm(
            `Este condutor tem ${n} entrega(s) activa(s).\n\n` +
            `Ao confirmar:\n` +
            `• As entregas serão canceladas\n` +
            `• As encomendas voltam a "preparando" para reatribuição\n\n` +
            `Confirmar?`
          )
          if (confirmar) {
            try {
              await api.patch(`/app/loja/${this.lojaId}/staff/${membro.id}/`, { role: novoRole, forcar: true })
              membro.role = novoRole
            } catch (e2) { console.error(e2) }
          }
          // se não confirmar, repõe o select para o role anterior
          // (Vue não repõe automaticamente porque o value já mudou no DOM)
          else {
            await this.$nextTick()
            membro.role = roleAnterior
          }
        } else {
          console.error(e)
          membro.role = roleAnterior
        }
      }
    },

    async removerMembro (membro) {
      if (!confirm(`Remover ${membro.utilizador?.nome} da equipa?`)) return
      try {
        await api.delete(`/app/loja/${this.lojaId}/staff/${membro.id}/remover/`)
        this.staff = this.staff.filter(m => m.id !== membro.id)
      } catch (e) { console.error(e) }
    },

    async adicionarMembro () {
      if (!this.utilizadorSelecionado) return
      this.erroAdicionar = ''
      this.loadingAdicionar = true
      try {
        // Associa o utilizador existente à loja via UtilizadorLoja
        await api.post(`/app/loja/${this.lojaId}/staff/adicionar/`, {
          utilizador_id: this.utilizadorSelecionado.id,
          role: this.novoRole,
        })
        this.fecharModal()
        await this.fetchStaff()
      } catch (e) {
        this.erroAdicionar = e.response?.data?.detail || 'Erro ao adicionar membro.'
      } finally {
        this.loadingAdicionar = false
      }
    },
  }
}
</script>