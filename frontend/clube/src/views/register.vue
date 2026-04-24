<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <!-- Background image -->
    <div class="absolute inset-0 bg-[url('/src/assets/img/login/login_background2.jpg')] bg-cover bg-center bg-no-repeat"></div>
    <div class="absolute inset-0 bg-black/40"></div>

    <div class="relative z-10 w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl">

      <!-- Painel ESQUERDO — branding -->
      <div class="hidden sm:flex w-2/5 flex-col items-center justify-center p-10 flex-shrink-0"
           style="background: linear-gradient(160deg, rgba(0,0,0,0.92) 0%, rgba(30,0,0,0.88) 100%); border-right: 1px solid rgba(220,38,38,0.2);">
        <img src="@/assets/img/login/store_logo-1.png" alt="Logo"
             class="w-40 h-40 object-contain mb-5 drop-shadow-lg" />
        <h1 class="text-2xl font-extrabold text-white tracking-tight text-center">NõsLoja</h1>
        <p class="text-zinc-400 text-sm mt-2 text-center leading-relaxed">
          Junta-te à comunidade<br/>de compradores e vendedores
        </p>
        <div class="mt-8 w-10 h-0.5 rounded-full bg-red-600 opacity-60"></div>
        <div class="mt-6 space-y-2 w-full">
          <div class="flex items-center gap-2 text-zinc-500 text-xs">
            <div class="w-4 h-4 rounded-full bg-red-600/20 flex items-center justify-center flex-shrink-0">
              <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
            </div>
            Cria a tua loja em minutos
          </div>
          <div class="flex items-center gap-2 text-zinc-500 text-xs">
            <div class="w-4 h-4 rounded-full bg-red-600/20 flex items-center justify-center flex-shrink-0">
              <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
            </div>
            Compra de lojas locais
          </div>
          <div class="flex items-center gap-2 text-zinc-500 text-xs">
            <div class="w-4 h-4 rounded-full bg-red-600/20 flex items-center justify-center flex-shrink-0">
              <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
            </div>
            Gestão completa no backoffice
          </div>
        </div>
      </div>

      <!-- Painel DIREITO — formulário -->
      <div class="flex-1 flex flex-col justify-center p-7 sm:p-10 overflow-y-auto max-h-screen"
           style="background: rgba(12,12,12,0.96); backdrop-filter: blur(20px);">

        <!-- Logo visível só em mobile -->
        <div class="flex sm:hidden items-center gap-3 mb-6">
          <img src="@/assets/img/login/ai_logo.png" alt="Logo" class="w-9 h-9 object-contain" />
          <span class="text-lg font-extrabold text-white">NõsLoja</span>
        </div>

        <h2 class="text-xl font-bold text-white mb-1">Criar conta</h2>
        <p class="text-zinc-500 text-xs mb-7">Preenche os dados para começar</p>

        <form @submit.prevent="handleRegister" class="space-y-4">

          <!-- Foto de perfil -->
          <div class="flex items-center gap-4">
            <div class="relative flex-shrink-0 cursor-pointer group" @click="$refs.fileInput.click()">
              <img :src="previewUrl" alt="Foto"
                   class="w-14 h-14 rounded-full object-cover border-2 border-zinc-700 group-hover:border-red-500 transition" />
              <div class="absolute inset-0 rounded-full bg-black/60 opacity-0 group-hover:opacity-100
                          flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                </svg>
              </div>
            </div>
            <div>
              <p class="text-xs font-medium text-zinc-300">Foto de perfil <span class="text-zinc-600">(opcional)</span></p>
              <button type="button" @click="$refs.fileInput.click()"
                class="text-xs text-red-400 hover:text-red-300 transition mt-0.5">
                Escolher ficheiro
              </button>
            </div>
            <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" class="hidden" />
          </div>

          <!-- Nome -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Primeiro nome *</label>
              <input v-model="first_name" required autocomplete="given-name"
                class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                       focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
                style="background: #181818;" placeholder="Ana" />
            </div>
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Apelido</label>
              <input v-model="last_name" autocomplete="family-name"
                class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                       focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
                style="background: #181818;" placeholder="Silva" />
            </div>
          </div>

          <!-- Username -->
          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Username *</label>
            <input v-model="username" required autocomplete="username"
              class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                     focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
              style="background: #181818;" placeholder="ana_silva" />
          </div>

          <!-- Email -->
          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Email *</label>
            <input v-model="email" type="email" required autocomplete="email"
              class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                     focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
              style="background: #181818;" placeholder="ana@exemplo.pt" />
          </div>

          <!-- Telemóvel + Morada -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Telemóvel</label>
              <input v-model="telefone" type="tel" autocomplete="tel"
                class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                       focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
                style="background: #181818;" placeholder="+351 9xx..." />
            </div>
            <div>
              <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Cidade</label>
              <input v-model="morada" autocomplete="address-level2"
                class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                       focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
                style="background: #181818;" placeholder="Lisboa" />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="text-xs font-medium text-zinc-400 mb-1.5 block">Password *</label>
            <input v-model="password" type="password" required autocomplete="new-password"
              class="w-full px-3 py-2.5 rounded-xl text-sm text-zinc-100 border border-zinc-800
                     focus:outline-none focus:border-red-500 transition placeholder-zinc-600"
              style="background: #181818;" placeholder="Mínimo 8 caracteres" />
          </div>

          <!-- Erros -->
          <div v-if="errors.length"
               class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 space-y-0.5">
            <p v-for="(e, i) in errors" :key="i" class="text-red-400 text-xs">{{ e }}</p>
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all
                   flex items-center justify-center gap-2 mt-1"
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
          <router-link to="/Login" class="text-red-400 hover:text-red-300 transition font-semibold">
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