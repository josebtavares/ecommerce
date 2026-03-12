<template>
  <div class="relative w-screen h-screen overflow-hidden
           bg-[url('/src/assets/img/login/login_background2.jpg')]
           bg-cover bg-center bg-no-repeat">
    <div class="absolute inset-0 bg-black/40"></div>

    <div class="relative z-10 flex items-center justify-center h-full gap-0">

      <!-- Painel ESQUERDO -->
      <div class="w-96 h-[50%] p-8 shadow-md flex flex-col items-center justify-center
               bg-gradient-to-b from-black via-gray-800 to-gray-600
               rounded-tl-lg rounded-bl-lg">
        <img src="@/assets/img/login/ai_logo.png" alt="Logo" class="w-32 mb-4" />
        <h1 class="text-3xl font-bold text-white mb-4">AI Signal</h1>
        <p class="text-lg text-white text-center">Bem-vindo.</p>
      </div>

      <!-- Painel DIREITO -->
      <div class="w-96 h-[50%] bg-white p-8 shadow-md rounded-tr-lg rounded-br-lg">

        <h2 class="text-2xl font-bold mb-6 text-center">Login</h2>

        <form @submit.prevent="handleLogin">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700" for="username">
              Username ou Email
            </label>
            <input
              id="username" v-model="username" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700" for="password">
              Password
            </label>
            <input
              id="password" v-model="password" type="password" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <button
            type="submit"
            :disabled="loading"
            :class="[
              'w-full py-2 rounded text-white transition',
              loading ? 'bg-blue-400 cursor-not-allowed opacity-70'
                      : 'bg-blue-500 hover:bg-blue-600'
            ]">
            <span v-if="!loading">Login</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              A entrar…
            </span>
          </button>
        </form>

        <p v-if="warning" class="text-red-500 text-center mt-2 text-sm">
          {{ warningMsg }}
        </p>

        <p class="mt-4 text-center text-sm">
          Ainda não tens conta?
          <router-link to="/Register" class="text-blue-500">Regista-te</router-link>
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
    // já autenticado → vai para Home
    if (localStorage.getItem('access_token')) {
      //this.$router.push({ name: 'Home' })
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

          // backend devolve: { access_token, refresh_token, user }
          const { access_token, refresh_token, user } = res.data

          localStorage.setItem('access_token',  access_token)
          localStorage.setItem('refresh_token', refresh_token)
          localStorage.setItem('user',          JSON.stringify(user))

          toast.success('Login bem-sucedido!', { autoClose: 2000 })
          //this.$router.push({ name: 'Home' })
          console.log('Login bem-sucedido:', user)

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