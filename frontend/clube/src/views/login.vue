<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <!-- Background image -->
    <div class="absolute inset-0 bg-[url('/src/assets/img/login/login_fundo2.png')] bg-cover bg-center bg-no-repeat"></div>
    <div class="absolute inset-0" :class="isDark ? 'bg-black/55' : 'bg-black/30'"></div>

    <!-- Toggle tema — canto superior direito -->
    <button @click="isDark = !isDark"
      class="absolute top-4 right-4 z-20 w-9 h-9 rounded-full flex items-center justify-center
             border transition-all shadow-lg"
      :class="isDark
        ? 'bg-zinc-900/80 border-zinc-700 hover:border-zinc-500 text-zinc-300'
        : 'bg-white/80 border-white/60 hover:border-orange-400 text-zinc-700'">
      <!-- Sol (light) -->
      <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
      </svg>
      <!-- Lua (dark) -->
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
      </svg>
    </button>

    <div class="relative z-10 w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl transition-all"
         style="min-height: 480px;">

      <!-- Painel ESQUERDO — branding -->
      <div class="hidden sm:flex w-2/5 flex-col items-center justify-center p-10 flex-shrink-0 transition-all"
           :style="isDark
             ? 'background: linear-gradient(160deg, rgba(0,0,0,0.95) 0%, rgba(20,0,0,0.92) 100%); border-right: 1px solid rgba(220,38,38,0.2);'
             : 'background: linear-gradient(160deg, rgba(255,247,237,0.98) 0%, rgba(255,237,213,0.96) 100%); border-right: 1px solid rgba(249,115,22,0.18);'">
        <img :src="isDark ? logoLight : logoDefault" alt="Logo"
             class="w-60 h-60 object-contain mb-5 drop-shadow-lg" />
        <p class="text-sm mt-2 text-center leading-relaxed transition-colors"
           :class="isDark ? 'text-zinc-400' : 'text-zinc-700'">
          O mercado local<br/>na palma da mão
        </p>
        <div class="mt-8 w-10 h-0.5 rounded-full opacity-70 transition-colors"
             :class="isDark ? 'bg-red-600' : 'bg-orange-500'"></div>
      </div>

      <!-- Painel DIREITO — formulário -->
      <div class="flex-1 flex flex-col justify-center p-8 sm:p-10 transition-all"
           :style="isDark
             ? 'background: rgba(12,12,12,0.97); backdrop-filter: blur(20px);'
             : 'background: rgba(255,255,255,0.97); backdrop-filter: blur(20px);'">

        <div class="flex sm:hidden items-center gap-3 mb-8 justify-center">
          <img :src="isDark ? logoLight : logoDefault" alt="Logo" class="w-40 h-40 object-contain" />
        </div>

        <h2 class="text-xl font-bold mb-1 transition-colors"
            :class="isDark ? 'text-white' : 'text-zinc-900'">
          Bem-vindo de volta
        </h2>
        <p class="text-xs mb-7 transition-colors"
           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Entra na tua conta para continuar
        </p>

        <form @submit.prevent="handleLogin" class="space-y-4">

          <div>
            <label class="text-xs font-medium mb-1.5 block transition-colors"
                   :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
              Username ou Email
            </label>
            <input v-model="username" required autocomplete="username"
              class="w-full px-4 py-2.5 rounded-xl text-sm border transition-all
                     focus:outline-none placeholder-zinc-400"
              :class="isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500'
                : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400'"
              placeholder="o_teu_username" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-medium transition-colors"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                Password
              </label>
              <a href="#" class="text-xs transition-colors"
                 :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
                Esqueceste?
              </a>
            </div>
            <input v-model="password" type="password" required autocomplete="current-password"
              class="w-full px-4 py-2.5 rounded-xl text-sm border transition-all
                     focus:outline-none"
              :class="isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500'
                : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400'"
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
            :style="isDark
              ? 'background: linear-gradient(135deg, #dc2626, #b91c1c);'
              : 'background: linear-gradient(135deg, #f97316, #ea580c);'">
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ loading ? 'A entrar…' : 'Entrar' }}
          </button>
        </form>

        <p class="mt-6 text-center text-xs transition-colors"
           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Ainda não tens conta?
          <router-link to="/Register"
            class="font-semibold transition-colors"
            :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
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
import logoDefault from '@/assets/img/login/logo_final_4k.png'
import logoLight from '@/assets/img/login/logo_final_4k_light.png'

export default {
  name: 'AppLogin',

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    const savedTheme = localStorage.getItem('theme_preference')
    return {
      username: '',
      password: '',
      warning: false,
      warningMsg: 'Credenciais inválidas.',
      isDark: savedTheme ? savedTheme === 'dark' : true,
      logoDefault,
      logoLight,
    }
  },

  watch: {
    isDark (val) {
      localStorage.setItem('theme_preference', val ? 'dark' : 'light')
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