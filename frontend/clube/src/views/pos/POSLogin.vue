<template>
  <main class="min-h-screen overflow-hidden bg-slate-950 text-white">
    <section class="relative flex min-h-screen items-center justify-center px-4 py-8 sm:px-6 lg:px-8">
      <!-- Background -->
      <div class="absolute inset-0">
        <div class="absolute -left-32 -top-32 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl"></div>
        <div class="absolute -right-32 top-1/3 h-96 w-96 rounded-full bg-purple-500/20 blur-3xl"></div>
        <div class="absolute bottom-0 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-emerald-400/10 blur-3xl"></div>
      </div>

      <div class="relative grid w-full max-w-6xl overflow-hidden rounded-[2rem] border border-white/10 bg-white/10 shadow-2xl backdrop-blur-xl lg:grid-cols-[1.05fr_0.95fr]">
        <!-- Painel esquerdo -->
        <aside class="hidden min-h-[620px] flex-col justify-between bg-gradient-to-br from-slate-900 via-slate-950 to-black p-10 lg:flex">
          <div>
            <div class="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-slate-200">
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_22px_rgba(52,211,153,.8)]"></span>
              POS integrado com Bendi
            </div>

            <div class="mt-12">
              <h1 class="max-w-xl text-5xl font-black leading-tight tracking-tight">
                Vende rápido, gere mesas e controla o teu negócio.
              </h1>

              <p class="mt-5 max-w-lg text-base leading-7 text-slate-300">
                Acede ao teu POS para trabalhar em modo standalone ou integrado com uma loja Bendi.
              </p>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">01</p>
              <p class="mt-1 text-xs text-slate-400">Mesas</p>
            </div>

            <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">02</p>
              <p class="mt-1 text-xs text-slate-400">Produtos</p>
            </div>

            <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">03</p>
              <p class="mt-1 text-xs text-slate-400">Pagamentos</p>
            </div>
          </div>
        </aside>

        <!-- Formulário -->
        <div class="bg-white p-6 text-slate-900 sm:p-8 lg:p-12">
          <div class="mx-auto flex min-h-[540px] w-full max-w-md flex-col justify-center">
            <header class="mb-8 text-center lg:text-left">
              <div class="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-950 text-xl font-black text-white shadow-lg lg:mx-0">
                POS
              </div>

              <h2 class="text-3xl font-black tracking-tight text-slate-950">
                Entrar no POS
              </h2>

              <p class="mt-2 text-sm text-slate-500">
                Usa o teu email ou username da conta Bendi.
              </p>
            </header>

            <form class="space-y-5" @submit.prevent="handleLogin">
              <div>
                <label class="mb-2 block text-sm font-bold text-slate-700">
                  Email ou username
                </label>

                <input
                  v-model.trim="form.email"
                  type="text"
                  autocomplete="username"
                  placeholder="ex: zeny_tavares@outlook.com"
                  required
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
              </div>

              <div>
                <label class="mb-2 block text-sm font-bold text-slate-700">
                  Password
                </label>

                <div class="relative">
                  <input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    autocomplete="current-password"
                    placeholder="••••••••"
                    required
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

              <div
                v-if="error"
                class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700"
              >
                {{ error }}
              </div>

              <button
                type="submit"
                :disabled="loading || !canSubmit"
                class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/20 transition hover:-translate-y-0.5 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                <span v-if="!loading">Entrar no POS</span>

                <span v-else class="flex items-center gap-2">
                  <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                  A entrar...
                </span>
              </button>
            </form>

            <div class="mt-7 rounded-2xl bg-slate-50 p-4 text-center text-sm text-slate-600">
              Ainda não tens conta?
              <router-link
                to="/pos/register"
                class="font-black text-slate-950 hover:underline"
              >
                Criar conta POS
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
  name: 'POSLogin',

  data() {
    return {
      form: {
        email: '',
        password: ''
      },
      loading: false,
      error: null,
      showPassword: false
    }
  },

  computed: {
    canSubmit() {
      return this.form.email.trim().length > 0 && this.form.password.length > 0
    }
  },

  methods: {
    async handleLogin() {
      if (!this.canSubmit || this.loading) return

      this.error = null
      this.loading = true

      try {
        const { data } = await api.post('/api/pos/login/', {
          email: this.form.email.trim(),
          password: this.form.password
        })

        this.persistSession(data)

        this.$router.push({
          name: 'POSDashboard'
        })
      } catch (err) {
        this.error = this.getErrorMessage(err)
      } finally {
        this.loading = false
      }
    },

    persistSession(data) {
      const lojas = Array.isArray(data.lojas) ? data.lojas : []
      const posExistentes = Array.isArray(data.pos_existentes)
        ? data.pos_existentes
        : []

      const selectedPOS = posExistentes.length > 0 ? posExistentes[0] : null

      /*
        O backend agora pode devolver precisa_onboarding=true.
        Mesmo que por algum motivo não venha, se não houver POS existente,
        assumimos que precisa onboarding.
      */
      const precisaOnboarding = Boolean(
        data.precisa_onboarding || posExistentes.length === 0
      )

      // Tokens globais usados pela api.js da Bendi
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.user || null))

      // Dados específicos do POS
      localStorage.setItem('pos_lojas', JSON.stringify(lojas))
      localStorage.setItem('pos_existentes', JSON.stringify(posExistentes))
      localStorage.setItem('pos_tem_lojas', data.tem_lojas ? 'true' : 'false')
      localStorage.setItem('pos_precisa_onboarding', precisaOnboarding ? 'true' : 'false')

      // Dados usados pelo OnboardingModal.vue
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

      // Permissões do POS, caso o backend envie
      if (data.permissoes) {
        localStorage.setItem('pos_permissoes', JSON.stringify(data.permissoes))
      } else {
        localStorage.removeItem('pos_permissoes')
      }

      // Se já existe POS, seleciona o primeiro e entra direto no dashboard
      if (selectedPOS) {
        localStorage.setItem('pos_selected', JSON.stringify(selectedPOS))
        localStorage.setItem('pos_id', String(selectedPOS.id))
      } else {
        // Se não existe POS, o dashboard vai abrir o OnboardingModal
        localStorage.removeItem('pos_selected')
        localStorage.removeItem('pos_id')
      }
    },

    getErrorMessage(err) {
      if (err.response?.data?.detail) {
        return err.response.data.detail
      }

      if (err.response?.status === 400) {
        return 'Verifica os dados preenchidos.'
      }

      if (err.response?.status === 401) {
        return 'Credenciais inválidas.'
      }

      if (err.response?.status === 403) {
        return 'A tua conta está desativada ou sem permissão.'
      }

      if (!navigator.onLine) {
        return 'Sem ligação à internet. Verifica a tua conexão.'
      }

      return 'Não foi possível iniciar sessão no POS. Tenta novamente.'
    }
  }
}
</script>