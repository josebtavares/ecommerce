<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden"
       style="background: #0a0a0a;">

    <!-- Fundo animado -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -left-40 w-96 h-96 rounded-full opacity-20"
           style="background: radial-gradient(circle, #dc2626, transparent); filter: blur(80px);"></div>
      <div class="absolute -bottom-40 -right-40 w-96 h-96 rounded-full opacity-10"
           style="background: radial-gradient(circle, #7f1d1d, transparent); filter: blur(80px);"></div>
      <!-- Grid subtil -->
      <div class="absolute inset-0 opacity-[0.03]"
           style="background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px); background-size: 60px 60px;"></div>
    </div>

    <div class="relative z-10 w-full max-w-sm">

      <!-- Logo / marca -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 border border-red-500/30"
             style="background: linear-gradient(135deg, #1a0000, #2d0000);">
          <img src="@/assets/img/login/store_logo.png" alt="Logo" class="w-8 h-8 object-contain" />
        </div>
        <h1 class="text-2xl font-bold text-white tracking-tight">AI Signal</h1>
        <p class="text-zinc-500 text-sm mt-1">Bem-vindo de volta</p>
      </div>

      <!-- Card -->
      <div class="rounded-2xl border border-zinc-800 p-6 sm:p-8"
           style="background: rgba(18,18,18,0.95); backdrop-filter: blur(20px);">

        <h2 class="text-lg font-bold text-white mb-6">Entrar na conta</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">

          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Username ou Email</label>
            <input v-model="username" required autocomplete="username"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                     focus:outline-none focus:border-red-500 transition"
              style="background: #1a1a1a;"
              placeholder="o_teu_username" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-medium text-zinc-400">Password</label>
              <a href="#" class="text-xs text-red-400 hover:text-red-300 transition">Esqueceste?</a>
            </div>
            <input v-model="password" type="password" required autocomplete="current-password"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                     focus:outline-none focus:border-red-500 transition"
              style="background: #1a1a1a;"
              placeholder="••••••••" />
          </div>

          <div v-if="warning"
               class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
            {{ warningMsg }}
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all mt-2
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

        <p class="mt-5 text-center text-xs text-zinc-500">
          Ainda não tens conta?
          <router-link to="/Register" class="text-red-400 hover:text-red-300 transition font-medium">
            Cria uma agora
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