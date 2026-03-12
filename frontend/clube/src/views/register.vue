<template>
  <div class="relative w-screen h-screen overflow-hidden
           bg-[url('/src/assets/img/login/login_background2.jpg')]
           bg-cover bg-center bg-no-repeat">
    <div class="absolute inset-0 bg-black/40"></div>

    <div class="relative z-10 flex items-center justify-center h-full gap-0">

      <!-- Painel ESQUERDO -->
      <div class="w-96 h-[60%] p-8 shadow-md flex flex-col items-center justify-center
               bg-gradient-to-b from-black via-gray-800 to-gray-600
               rounded-tl-lg rounded-bl-lg">
        <img src="@/assets/img/login/ai_logo.png" alt="Logo" class="w-32 mb-4" />
        <h1 class="text-3xl font-bold text-white mb-4">AI Signal</h1>
        <p class="text-lg text-white text-center">Junta-te a nós!</p>
      </div>

      <!-- Painel DIREITO -->
      <div class="w-96 h-[60%] bg-white p-8 shadow-md rounded-tr-lg rounded-br-lg overflow-y-auto">

        <h2 class="text-2xl font-bold mb-6 text-center">Registo</h2>

        <form @submit.prevent="handleRegister">

          <!-- Foto de perfil -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700">
              Foto de perfil (opcional)
            </label>
            <div class="mt-2 flex justify-center gap-3">
              <img :src="previewUrl" alt="preview"
                   class="h-20 w-20 rounded-full object-cover border" />
              <input ref="fileInput" type="file" accept="image/*"
                     @change="onFileChange" class="hidden" />
              <div @click="$refs.fileInput.click()" class="cursor-pointer self-center">
                <i class="fa-solid fa-circle-plus text-2xl"></i>
              </div>
            </div>
          </div>

          <!-- First name -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700">Primeiro nome</label>
            <input v-model="first_name" required
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Last name -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700">Apelido</label>
            <input v-model="last_name"
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Username -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700">Username</label>
            <input v-model="username" required
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Email -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700">Email</label>
            <input v-model="email" type="email" required
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Telemóvel -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700">Telemóvel</label>
            <input v-model="telefone"
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Morada -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700">Morada</label>
            <input v-model="morada"
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Password -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700">Password</label>
            <input v-model="password" type="password" required
                   class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <button
            type="submit" :disabled="loading"
            :class="[
              'w-full py-2 rounded text-white transition',
              loading ? 'bg-blue-400 cursor-not-allowed opacity-70'
                      : 'bg-blue-500 hover:bg-blue-600'
            ]">
            <span v-if="!loading">Criar conta</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
            </span>
          </button>
        </form>

        <!-- Erros -->
        <div v-if="errors.length" class="mt-3 text-red-500 text-sm text-center">
          <p v-for="(e, i) in errors" :key="i">{{ e }}</p>
        </div>

        <p class="mt-4 text-center text-sm">
          Já tens conta?
          <router-link to="/Login" class="text-blue-500">Entra aqui</router-link>
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
  name: 'RegisterView',

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      first_name: '',
      last_name: '',
      username: '',
      email: '',
      telefone: '',
      morada: '',
      password: '',
      file: null,
      previewUrl: `${process.env.VUE_APP_URL_BASE}/media/utilizadores/default.png`,
      errors: [],
    }
  },

  methods: {
    onFileChange (e) {
      const f = e.target.files[0]
      if (f) {
        this.file = f
        this.previewUrl = URL.createObjectURL(f)
      } else {
        this.file = null
        this.previewUrl = `${process.env.VUE_APP_URL_BASE}/media/utilizadores/default.png`
      }
    },

    async handleRegister () {
      await this.wrap(async () => {
        this.errors = []

        // monta o FormData com os campos do novo backend
        const form = new FormData()
        form.append('username',   this.username)
        form.append('email',      this.email)
        form.append('password',   this.password)
        form.append('first_name', this.first_name)
        form.append('last_name',  this.last_name)
        form.append('telefone',   this.telefone)
        form.append('morada',     this.morada)
        if (this.file) form.append('foto', this.file)

        try {
          const res = await api.post('/app/utilizador/registar/', form, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })

          // backend devolve auth payload igual ao login
          const { access_token, refresh_token, user } = res.data

          localStorage.setItem('access_token',  access_token)
          localStorage.setItem('refresh_token', refresh_token)
          localStorage.setItem('user',          JSON.stringify(user))

          toast.success('Conta criada com sucesso!', { autoClose: 2000 })
          //this.$router.push({ name: 'Home' })
          console.log('Conta criada com sucesso:', user)

        } catch (err) {
          const data = err.response?.data
          if (data && typeof data === 'object') {
            // mostra erros campo a campo vindos do serializer
            this.errors = Object.values(data).flat()
          } else {
            this.errors = ['Não foi possível criar a conta. Tente novamente.']
          }
          toast.error('Erro no registo.', { autoClose: 3000 })
        }
      })
    }
  }
}
</script>