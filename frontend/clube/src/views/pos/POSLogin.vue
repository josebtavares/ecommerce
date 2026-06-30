<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
    <div class="w-full max-w-md space-y-6">

      <!-- Logo / título -->
      <div class="text-center">
        <h1 class="text-4xl font-black text-slate-950">POS</h1>
        <p class="mt-2 text-sm font-semibold text-slate-500">Bendi Point of Sale</p>
      </div>

      <!-- Toggle tipo de login -->
      <div class="flex rounded-2xl bg-slate-200 p-1">
        <button
          type="button"
          :class="[
            'flex-1 rounded-xl py-2.5 text-sm font-black transition',
            modo === 'principal'
              ? 'bg-white text-slate-950 shadow'
              : 'text-slate-500 hover:text-slate-700'
          ]"
          @click="mudarModo('principal')"
        >
          Conta Principal
        </button>
        <button
          type="button"
          :class="[
            'flex-1 rounded-xl py-2.5 text-sm font-black transition',
            modo === 'membro'
              ? 'bg-white text-slate-950 shadow'
              : 'text-slate-500 hover:text-slate-700'
          ]"
          @click="mudarModo('membro')"
        >
          Membro de Equipa
        </button>
      </div>

      <!-- Card do formulário -->
      <div class="rounded-[2rem] bg-white p-8 shadow-xl">

        <!-- Erro -->
        <div
          v-if="error"
          class="mb-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
        >
          {{ error }}
        </div>

        <!-- ══════════════════════════════════════
             MODO: CONTA PRINCIPAL (email + pw)
        ══════════════════════════════════════ -->
        <form
          v-if="modo === 'principal'"
          class="space-y-4"
          @submit.prevent="loginPrincipal"
        >
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Email</label>
            <input
              v-model.trim="form.email"
              type="email"
              placeholder="teu@email.com"
              required
              autocomplete="email"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Password</label>
            <input
              v-model="form.password"
              type="password"
              placeholder="••••••••"
              required
              autocomplete="current-password"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
          >
            <span v-if="!loading">Entrar</span>
            <span v-else class="flex items-center gap-2">
              <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
              A entrar...
            </span>
          </button>

          <p class="text-center text-sm font-semibold text-slate-500">
            Não tens conta?
            <router-link
              to="/pos/register"
              class="font-black text-slate-950 underline"
            >
              Registar
            </router-link>
          </p>
        </form>

        <!-- ══════════════════════════════════════
             MODO: MEMBRO DE EQUIPA (username + pw)
        ══════════════════════════════════════ -->
        <form
          v-else
          class="space-y-4"
          @submit.prevent="loginMembro"
        >
          <!-- Info contextual -->
          <div class="rounded-xl bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-500">
            Usa as credenciais que o teu responsável te deu.
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Username</label>
            <input
              v-model.trim="formMembro.username"
              type="text"
              placeholder="ex: joana"
              required
              autocomplete="username"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Password</label>
            <input
              v-model="formMembro.password"
              type="password"
              placeholder="••••••••"
              required
              autocomplete="current-password"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60"
          >
            <span v-if="!loading">Entrar como Membro</span>
            <span v-else class="flex items-center gap-2">
              <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
              A entrar...
            </span>
          </button>
        </form>

        <!-- ══════════════════════════════════════
             ESCOLHA DE POS (username em vários POS)
        ══════════════════════════════════════ -->
        <div v-if="escolherPOS" class="mt-4 space-y-3">
          <p class="text-sm font-black text-slate-700">
            O teu username existe em vários POS. Escolhe qual:
          </p>
          <button
            v-for="pos in posDisponiveis"
            :key="pos.pos_id"
            type="button"
            @click="loginMembroComPOS(pos.pos_id)"
            class="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-slate-950 hover:bg-white"
          >
            <span class="font-black text-slate-950">{{ pos.pos_nome }}</span>
            <span class="text-xs font-bold text-slate-400">{{ pos.codigo_pos }}</span>
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'POSLogin',

  data() {
    return {
      modo: 'principal',   // 'principal' | 'membro'
      loading: false,
      error: null,

      // Conta principal
      form: {
        email: '',
        password: '',
      },

      // Membro de equipa
      formMembro: {
        username: '',
        password: '',
      },

      // Escolha de POS (quando username existe em vários)
      escolherPOS: false,
      posDisponiveis: [],
    }
  },

  methods: {
    mudarModo(m) {
      this.modo = m
      this.error = null
      this.escolherPOS = false
    },

    // ── LOGIN CONTA PRINCIPAL ──────────────────────────────────────
    async loginPrincipal() {
      this.loading = true
      this.error = null

      try {
        const { data } = await api.post('/api/pos/login/', {
          email: this.form.email,
          password: this.form.password,
        })

        this._guardarSessaoPrincipal(data)
        this._redirecionar(data)

      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao entrar'
      } finally {
        this.loading = false
      }
    },

    // ── LOGIN MEMBRO DE EQUIPA ────────────────────────────────────
    async loginMembro() {
      this.loading = true
      this.error = null
      this.escolherPOS = false

      try {
        const { data } = await api.post('/api/pos/login/membro/', {
          username: this.formMembro.username,
          password: this.formMembro.password,
        })

        // Backend pede para escolher POS
        if (data.escolher_pos) {
          this.posDisponiveis = data.pos_disponiveis
          this.escolherPOS = true
          return
        }

        this._guardarSessaoMembro(data)
        this.$router.push('/pos/dashboard')

      } catch (err) {
        this.error = err.response?.data?.detail || 'Credenciais inválidas'
      } finally {
        this.loading = false
      }
    },

    // ── LOGIN MEMBRO COM POS ESPECÍFICO ──────────────────────────
    async loginMembroComPOS(posId) {
      this.loading = true
      this.error = null

      try {
        const { data } = await api.post('/api/pos/login/membro/', {
          username: this.formMembro.username,
          password: this.formMembro.password,
          pos_id: posId,
        })

        this._guardarSessaoMembro(data)
        this.$router.push('/pos/dashboard')

      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao entrar'
      } finally {
        this.loading = false
      }
      
    },

    // ── HELPERS ───────────────────────────────────────────────────
    _guardarSessaoPrincipal(data) {
  const lojas = Array.isArray(data.lojas) ? data.lojas : []
  const posExistentes = Array.isArray(data.pos_existentes) ? data.pos_existentes : []
  const selectedPOS = posExistentes.length > 0 ? posExistentes[0] : null

  const precisaOnboarding = Boolean(
    data.precisa_onboarding || posExistentes.length === 0
  )

  // Sessão principal
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  localStorage.setItem('tipo_sessao', 'principal')

  // User POS
  localStorage.setItem('pos_user', JSON.stringify(data.user || null))

  // Compatibilidade com outros ficheiros antigos que usam "user"
  localStorage.setItem('user', JSON.stringify(data.user || null))

  // Dados do POS
  localStorage.setItem('pos_lojas', JSON.stringify(lojas))
  localStorage.setItem('pos_existentes', JSON.stringify(posExistentes))
  localStorage.setItem('pos_tem_lojas', data.tem_lojas ? 'true' : 'false')
  localStorage.setItem('pos_precisa_onboarding', precisaOnboarding ? 'true' : 'false')

  localStorage.setItem(
    'pos_onboarding_data',
    JSON.stringify({
      tem_lojas: Boolean(data.tem_lojas),
      lojas,
      pos_existentes: posExistentes,
      precisa_onboarding: precisaOnboarding,
      mensagem: data.mensagem || ''
    })
  )

  if (data.permissoes) {
    localStorage.setItem('pos_permissoes', JSON.stringify(data.permissoes))
  } else {
    localStorage.removeItem('pos_permissoes')
  }

  // Se já existe POS, selecionar o primeiro automaticamente
  if (selectedPOS) {
    localStorage.setItem('pos_selected', JSON.stringify(selectedPOS))
    localStorage.setItem('pos_id', String(selectedPOS.id))
    localStorage.setItem('pos_precisa_onboarding', 'false')
  } else {
    localStorage.removeItem('pos_selected')
    localStorage.removeItem('pos_id')
  }

  // Limpar dados de sessão de membro anterior
  localStorage.removeItem('pos_membro')
  localStorage.removeItem('pos_membro_pos')
  localStorage.removeItem('pos_membro_permissoes')
},

    _guardarSessaoMembro(data) {
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('tipo_sessao', 'membro')
      localStorage.setItem('pos_membro', JSON.stringify(data.membro))
      localStorage.setItem('pos_membro_pos', JSON.stringify(data.pos))
      localStorage.setItem('pos_membro_permissoes', JSON.stringify(data.permissoes))

      // Limpar dados de sessão principal anterior
      localStorage.removeItem('pos_user')
      localStorage.removeItem('pos_lojas')
    },

    _redirecionar(data) {
  const posExistentes = Array.isArray(data.pos_existentes) ? data.pos_existentes : []

  if (data.precisa_onboarding && posExistentes.length === 0) {
    this.$router.push('/pos/dashboard?onboarding=1')
    return
  }

  this.$router.push('/pos/dashboard')
},
  },
}
</script>