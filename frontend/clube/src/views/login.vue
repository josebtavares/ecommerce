<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <!-- Background image -->
    <div class="absolute inset-0 bg-[url('/src/assets/img/login/login_back.jpg')] bg-cover bg-center bg-no-repeat"></div>
    <div class="absolute inset-0 bg-black/40"></div>

    <div class="relative z-10 w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl"
         style="min-height: 480px;">

      <!-- Painel ESQUERDO — branding -->
      <div class="hidden sm:flex w-2/5 flex-col items-center justify-center p-10 flex-shrink-0"
           style="background: linear-gradient(160deg, rgba(0,0,0,0.92) 0%, rgba(30,0,0,0.88) 100%); border-right: 1px solid rgba(220,38,38,0.2);">
        <img src="@/assets/img/login/store_logo-1.png" alt="Logo"
             class="w-40 h-40 object-contain mb-5 drop-shadow-lg" />
        <h1 class="text-2xl font-extrabold text-white tracking-tight text-center">NõsLoja</h1>
        <p class="text-zinc-400 text-sm mt-2 text-center leading-relaxed">
          O mercado local<br/>na palma da mão
        </p>
        <div class="mt-8 w-10 h-0.5 rounded-full bg-red-600 opacity-60"></div>
      </div>

      <!-- Painel DIREITO — formulário -->
      <div class="flex-1 flex flex-col justify-center p-8 sm:p-10"
           style="background: rgba(12,12,12,0.96); backdrop-filter: blur(20px);">

        <!-- Logo visível só em mobile -->
        <div class="flex sm:hidden items-center gap-3 mb-8">
          <img src="@/assets/img/login/ai_logo.png" alt="Logo" class="w-9 h-9 object-contain" />
          <span class="text-lg font-extrabold text-white">NõsLoja</span>
        </div>

        <h2 class="text-xl font-bold text-white mb-1">Bem-vindo de volta</h2>
        <p class="text-zinc-500 text-xs mb-7">Entra na tua conta para continuar</p>

        <form @submit.prevent="handleLogin" class="space-y-4">

          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Username ou Email</label>
            <input v-model="username" required autocomplete="username"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                     focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
              style="background: #181818;"
              placeholder="o_teu_username" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-medium text-zinc-400">Password</label>
              <a href="#" class="text-xs text-red-400 hover:text-red-300 transition">Esqueceste?</a>
            </div>
            <input v-model="password" type="password" required autocomplete="current-password"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                     focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
              style="background: #181818;"
              placeholder="••••••••" />
          </div>

          <div v-if="warning"
               class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
            {{ warningMsg }}
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all mt-1
                   flex items-center justify-center gap-2"
            :class="loading ? 'opacity-60 cursor-not-allowed' : 'hover:opacity-90 active:scale-[0.98]'"
            style="background: linear-gradient(135deg, #dc2626, #b91c1c);">
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ loading ? 'A entrar…' : 'Entrar' }}
          </button>
        </form>

        <p class="mt-6 text-center text-xs text-zinc-500">
          Ainda não tens conta?
          <router-link to="/Register" class="text-red-400 hover:text-red-300 transition font-semibold">
            Regista-te
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { toast } from 'vue3-toastify'
import { useAsyncAction } from '@/composables/useAsyncAction'
import api from '@/services/api.js'

export default {
  name: 'AppLogin',

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      username: '',
      password: '',
      warning: false,
      warningMsg: 'Credenciais inválidas.',
    }
  },

  created () {
    if (localStorage.getItem('access_token')) {
      this.$router.push({ name: 'Home' })
    }
  },

  methods: {
    async handleLogin () {
      await this.wrap(async () => {
        this.warning = false
        try {
          const res = await api.post('app/utilizador/login/', {
            username: this.username,
            password: this.password,
          })
          const { access_token, refresh_token, user } = res.data
          localStorage.setItem('access_token',  access_token)
          localStorage.setItem('refresh_token', refresh_token)
          localStorage.setItem('user',          JSON.stringify(user))
          toast.success('Login bem-sucedido!', { autoClose: 2000 })
          this.$router.push({ name: 'Home' })
        } catch (err) {
          const msg = err.response?.data?.detail || 'Credenciais inválidas.'
          this.warningMsg = msg
          this.warning = true
          toast.error(msg, { autoClose: 3000 })
        }
      })
    }
  }
}
</script>