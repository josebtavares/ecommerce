<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden"
       style="background: #0a0a0a;">

    <!-- Fundo animado -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-15"
           style="background: radial-gradient(circle, #dc2626, transparent); filter: blur(80px);"></div>
      <div class="absolute -bottom-40 -left-40 w-96 h-96 rounded-full opacity-10"
           style="background: radial-gradient(circle, #7f1d1d, transparent); filter: blur(80px);"></div>
      <div class="absolute inset-0 opacity-[0.03]"
           style="background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px); background-size: 60px 60px;"></div>
    </div>

    <div class="relative z-10 w-full max-w-md">

      <!-- Logo / marca -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 border border-red-500/30"
             style="background: linear-gradient(135deg, #1a0000, #2d0000);">
          <img src="@/assets/img/register/store_logo.png" alt="Logo" class="w-8 h-8 object-contain" />
        </div>
        <h1 class="text-2xl font-bold text-white tracking-tight">AI Signal</h1>
        <p class="text-zinc-500 text-sm mt-1">Cria a tua conta gratuitamente</p>
      </div>

      <!-- Card -->
      <div class="rounded-2xl border border-zinc-800 p-6 sm:p-8"
           style="background: rgba(18,18,18,0.95); backdrop-filter: blur(20px);">

        <h2 class="text-lg font-bold text-white mb-6">Criar conta</h2>

        <form @submit.prevent="handleRegister" class="space-y-5">

          <!-- Foto de perfil -->
          <div class="flex items-center gap-4">
            <div class="relative flex-shrink-0 cursor-pointer group" @click="$refs.fileInput.click()">
              <img :src="previewUrl" alt="Foto"
                   class="w-16 h-16 rounded-full object-cover border-2 border-zinc-700 group-hover:border-red-500 transition" />
              <div class="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100
                          flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                </svg>
              </div>
            </div>
            <div>
              <p class="text-sm font-medium text-zinc-300">Foto de perfil</p>
              <p class="text-xs text-zinc-500 mt-0.5">Opcional · JPG, PNG</p>
              <button type="button" @click="$refs.fileInput.click()"
                class="text-xs text-red-400 hover:text-red-300 transition mt-1">
                Escolher foto
              </button>
            </div>
            <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" class="hidden" />
          </div>

          <!-- Nome — grid 2 colunas em sm -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Primeiro nome *</label>
              <input v-model="first_name" required autocomplete="given-name"
                class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                       focus:outline-none focus:border-red-500 transition"
                style="background: #1a1a1a;" placeholder="Ana" />
            </div>
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Apelido</label>
              <input v-model="last_name" autocomplete="family-name"
                class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                       focus:outline-none focus:border-red-500 transition"
                style="background: #1a1a1a;" placeholder="Silva" />
            </div>
          </div>

          <!-- Username -->
          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Username *</label>
            <input v-model="username" required autocomplete="username"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                     focus:outline-none focus:border-red-500 transition"
              style="background: #1a1a1a;" placeholder="ana_silva" />
          </div>

          <!-- Email -->
          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Email *</label>
            <input v-model="email" type="email" required autocomplete="email"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                     focus:outline-none focus:border-red-500 transition"
              style="background: #1a1a1a;" placeholder="ana@exemplo.pt" />
          </div>

          <!-- Telemóvel + Morada — grid 2 colunas em sm -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Telemóvel</label>
              <input v-model="telefone" type="tel" autocomplete="tel"
                class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                       focus:outline-none focus:border-red-500 transition"
                style="background: #1a1a1a;" placeholder="+351 9xx xxx xxx" />
            </div>
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Morada</label>
              <input v-model="morada" autocomplete="street-address"
                class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                       focus:outline-none focus:border-red-500 transition"
                style="background: #1a1a1a;" placeholder="Lisboa" />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Password *</label>
            <input v-model="password" type="password" required autocomplete="new-password"
              class="w-full px-4 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-700
                     focus:outline-none focus:border-red-500 transition"
              style="background: #1a1a1a;" placeholder="Mínimo 8 caracteres" />
          </div>

          <!-- Erros -->
          <div v-if="errors.length"
               class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 space-y-1">
            <p v-for="(e, i) in errors" :key="i" class="text-red-400 text-xs">{{ e }}</p>
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all
                   flex items-center justify-center gap-2"
            :class="loading ? 'opacity-60 cursor-not-allowed' : 'hover:opacity-90 active:scale-[0.98]'"
            style="background: linear-gradient(135deg, #dc2626, #b91c1c);">
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ loading ? 'A criar conta…' : 'Criar conta' }}
          </button>
        </form>

        <p class="mt-5 text-center text-xs text-zinc-500">
          Já tens conta?
          <router-link to="/Login" class="text-red-400 hover:text-red-300 transition font-medium">
            Entrar
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
          const { access_token, refresh_token, user } = res.data
          localStorage.setItem('access_token',  access_token)
          localStorage.setItem('refresh_token', refresh_token)
          localStorage.setItem('user',          JSON.stringify(user))
          toast.success('Conta criada com sucesso!', { autoClose: 2000 })
          this.$router.push({ name: 'Home' })
        } catch (err) {
          const data = err.response?.data
          if (data && typeof data === 'object') {
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