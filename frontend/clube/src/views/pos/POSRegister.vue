<template>
  <main class="min-h-screen overflow-hidden bg-slate-950 text-white">
    <section class="relative flex min-h-screen items-center justify-center px-4 py-8 sm:px-6 lg:px-8">

      <!-- Background -->
      <div class="absolute inset-0">
        <div class="absolute -left-32 -top-32 h-80 w-80 rounded-full bg-emerald-500/20 blur-3xl"></div>
        <div class="absolute -right-32 top-1/3 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl"></div>
        <div class="absolute bottom-0 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-purple-500/10 blur-3xl"></div>
      </div>

      <div class="relative grid w-full max-w-6xl overflow-hidden rounded-[2rem] border border-white/10 bg-white/10 shadow-2xl backdrop-blur-xl lg:grid-cols-[1.05fr_0.95fr]">

        <!-- Painel esquerdo -->
        <aside class="hidden min-h-[680px] flex-col justify-between bg-gradient-to-br from-slate-900 via-slate-950 to-black p-10 lg:flex">
          <div>
            <div class="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-slate-200">
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_22px_rgba(52,211,153,.8)]"></span>
              Criar conta POS
            </div>

            <div class="mt-12">
              <h1 class="max-w-xl text-5xl font-black leading-tight tracking-tight">
                Começa a vender com o POS da Bendi.
              </h1>
              <p class="mt-5 max-w-lg text-base leading-7 text-slate-300">
                Cria a tua conta e escolhe depois se queres usar o POS sozinho, integrado com uma loja Bendi ou em modo híbrido.
              </p>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">01</p>
              <p class="mt-1 text-xs text-slate-400">Conta</p>
            </div>
            <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">02</p>
              <p class="mt-1 text-xs text-slate-400">Escolher modo</p>
            </div>
            <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">03</p>
              <p class="mt-1 text-xs text-slate-400">Começar vendas</p>
            </div>
          </div>
        </aside>

        <!-- Formulário -->
        <div class="bg-white p-6 text-slate-900 sm:p-8 lg:p-12">
          <div class="mx-auto flex min-h-[600px] w-full max-w-md flex-col justify-center">

            <header class="mb-8 text-center lg:text-left">
              <div class="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-950 text-xl font-black text-white shadow-lg lg:mx-0">
                POS
              </div>
              <h2 class="text-3xl font-black tracking-tight text-slate-950">Criar conta POS</h2>
              <p class="mt-2 text-sm text-slate-500">
                Cria uma conta Bendi e configura o teu POS no próximo passo.
              </p>
            </header>

            <form class="space-y-4" @submit.prevent="handleRegister">
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-bold text-slate-700">Primeiro nome</label>
                  <input
                    v-model.trim="form.firstName"
                    type="text"
                    autocomplete="given-name"
                    placeholder="João"
                    required
                    class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                  />
                </div>

                <div>
                  <label class="mb-2 block text-sm font-bold text-slate-700">Último nome</label>
                  <input
                    v-model.trim="form.lastName"
                    type="text"
                    autocomplete="family-name"
                    placeholder="Silva"
                    required
                    class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                  />
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-bold text-slate-700">Email</label>
                <input
                  v-model.trim="form.email"
                  type="email"
                  autocomplete="email"
                  placeholder="joao@exemplo.com"
                  required
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
              </div>

              <div>
                <label class="mb-2 block text-sm font-bold text-slate-700">Password</label>
                <div class="relative">
                  <input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    autocomplete="new-password"
                    placeholder="Mínimo 6 caracteres"
                    required
                    minlength="6"
                    class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 pr-16 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                  />
                  <button
                    type="button"
                    class="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl px-2 py-1 text-xs font-bold text-slate-500 hover:bg-slate-100 hover:text-slate-950"
                    @click="showPassword = !showPassword"
                  >
                    {{ showPassword ? 'Ocultar' : 'Ver' }}
                  </button>
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-bold text-slate-700">Confirmar password</label>
                <input
                  v-model="form.passwordConfirm"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="Repete a password"
                  required
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
              </div>

              <div
                v-if="error"
                class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700"
              >
                {{ error }}
              </div>

              <div
                v-if="successMessage"
                class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700"
              >
                {{ successMessage }}
              </div>

              <button
                type="submit"
                :disabled="loading || !canSubmit"
                class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/20 transition hover:-translate-y-0.5 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                <span v-if="!loading">Criar conta e continuar</span>
                <span v-else class="flex items-center gap-2">
                  <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                  A criar conta...
                </span>
              </button>
            </form>

            <div class="mt-7 rounded-2xl bg-slate-50 p-4 text-center text-sm text-slate-600">
              Já tens conta?
              <router-link to="/pos/login" class="font-black text-slate-950 hover:underline">
                Fazer login POS
              </router-link>
            </div>

            <button
              type="button"
              class="mt-4 text-center text-xs font-bold text-slate-400 hover:text-slate-700"
              @click="$router.push('/Login')"
            >
              Voltar ao login principal da Bendi
            </button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'POSRegister',

  data() {
    return {
      form: {
        firstName:       '',
        lastName:        '',
        email:           '',
        password:        '',
        passwordConfirm: ''
      },
      loading:        false,
      error:          null,
      successMessage: null,
      showPassword:   false
    }
  },

  computed: {
    canSubmit() {
      return (
        this.form.firstName.trim().length > 0 &&
        this.form.lastName.trim().length > 0 &&
        this.form.email.trim().length > 0 &&
        this.form.password.length >= 6 &&
        this.form.passwordConfirm.length > 0
      )
    }
  },

  methods: {
    async handleRegister() {
      this.error          = null
      this.successMessage = null

      const validationError = this.validateForm()
      if (validationError) {
        this.error = validationError
        return
      }

      this.loading = true

      try {
        const { data } = await api.post('/api/pos/register/', {
          first_name: this.form.firstName.trim(),
          last_name:  this.form.lastName.trim(),
          email:      this.form.email.trim(),
          password:   this.form.password
        })

        this.persistSession(data)

        this.successMessage = data.mensagem || 'Conta criada com sucesso.'

        this.$router.push({ name: 'POSDashboard' })
      } catch (err) {
        this.error = this.getErrorMessage(err)
      } finally {
        this.loading = false
      }
    },

    validateForm() {
      if (!this.form.firstName.trim())   return 'O primeiro nome é obrigatório.'
      if (!this.form.lastName.trim())    return 'O último nome é obrigatório.'
      if (!this.form.email.trim())       return 'O email é obrigatório.'
      if (!this.isValidEmail(this.form.email)) return 'Insere um email válido.'
      if (this.form.password.length < 6) return 'A password deve ter no mínimo 6 caracteres.'
      if (this.form.password !== this.form.passwordConfirm) return 'As passwords não coincidem.'
      return null
    },

    isValidEmail(email) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    },

    persistSession(data) {
      const lojas         = Array.isArray(data.lojas) ? data.lojas : []
      const posExistentes = this.resolvePOSList(data)
      const selectedPOS   = posExistentes.length > 0 ? posExistentes[0] : null
      const precisaOnboarding = Boolean(data.precisa_onboarding || posExistentes.length === 0)

      // ── Tokens ──────────────────────────────────────────────────
      localStorage.setItem('access_token',  data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      // ── Sessão principal (conta principal, NÃO membro) ──────────
      localStorage.setItem('tipo_sessao', 'principal')
      localStorage.setItem('pos_user',   JSON.stringify(data.user || null))

      // ── Contexto POS ────────────────────────────────────────────
      localStorage.setItem('pos_lojas',            JSON.stringify(lojas))
      localStorage.setItem('pos_existentes',       JSON.stringify(posExistentes))
      localStorage.setItem('pos_tem_lojas',        data.tem_lojas ? 'true' : 'false')
      localStorage.setItem('pos_precisa_onboarding', precisaOnboarding ? 'true' : 'false')
      localStorage.setItem('pos_onboarding_data', JSON.stringify({
        tem_lojas:          Boolean(data.tem_lojas),
        lojas,
        pos_existentes:     posExistentes,
        precisa_onboarding: precisaOnboarding,
        mensagem:           data.mensagem || ''
      }))

      // ── POS selecionado ─────────────────────────────────────────
      if (selectedPOS) {
        localStorage.setItem('pos_selected', JSON.stringify(selectedPOS))
        localStorage.setItem('pos_id',       String(selectedPOS.id))
      } else {
        localStorage.removeItem('pos_selected')
        localStorage.removeItem('pos_id')
      }

      // ── Limpar dados de sessão de membro (se existia) ───────────
      localStorage.removeItem('pos_membro')
      localStorage.removeItem('pos_membro_pos')
      localStorage.removeItem('pos_membro_permissoes')
    },

    resolvePOSList(data) {
      if (Array.isArray(data.pos_existentes)) return data.pos_existentes
      if (data.pos) return [data.pos]
      return []
    },

    getErrorMessage(err) {
      if (err.response?.data?.detail)    return err.response.data.detail
      if (err.response?.status === 400)  return 'Email já registado ou dados inválidos.'
      if (err.response?.status === 401)  return 'Não foi possível autenticar esta conta.'
      if (!navigator.onLine)             return 'Sem ligação à internet. Verifica a tua conexão.'
      return 'Erro ao criar conta. Tenta novamente.'
    }
  }
}
</script>