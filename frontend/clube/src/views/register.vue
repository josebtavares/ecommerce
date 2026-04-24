<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <!-- Background image -->
    <div class="absolute inset-0 bg-[url('/src/assets/img/login/login_background2.jpg')] bg-cover bg-center bg-no-repeat"></div>
    <div class="absolute inset-0 transition-all" :class="isDark ? 'bg-black/55' : 'bg-black/30'"></div>

    <!-- Toggle tema — canto superior direito -->
    <button @click="isDark = !isDark"
      class="absolute top-4 right-4 z-20 w-9 h-9 rounded-full flex items-center justify-center
             border transition-all shadow-lg"
      :class="isDark
        ? 'bg-zinc-900/80 border-zinc-700 hover:border-zinc-500 text-zinc-300'
        : 'bg-white/80 border-white/60 hover:border-orange-400 text-zinc-700'">
      <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
      </svg>
    </button>

    <div class="relative z-10 w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl transition-all">

      <!-- Painel ESQUERDO — branding -->
      <div class="hidden sm:flex w-2/5 flex-col items-center justify-center p-10 flex-shrink-0 transition-all"
           :style="isDark
             ? 'background: linear-gradient(160deg, rgba(0,0,0,0.95) 0%, rgba(20,0,0,0.92) 100%); border-right: 1px solid rgba(220,38,38,0.2);'
             : 'background: linear-gradient(160deg, rgba(255,247,237,0.98) 0%, rgba(255,237,213,0.96) 100%); border-right: 1px solid rgba(249,115,22,0.18);'">
        <img :src="isDark ? logoLight : logoDefault" alt="Logo"
             class="w-60 h-60 object-contain mb-5 drop-shadow-lg" />
        <p class="text-sm mt-2 text-center leading-relaxed transition-colors"
           :class="isDark ? 'text-zinc-400' : 'text-zinc-700'">
          Junta-te à comunidade<br/>de compradores e vendedores
        </p>
        <div class="mt-6 w-10 h-0.5 rounded-full opacity-70 transition-colors"
             :class="isDark ? 'bg-red-600' : 'bg-orange-500'"></div>
        <div class="mt-5 space-y-2 w-full">
          <div v-for="item in ['Cria a tua loja em minutos', 'Compra de lojas locais', 'Gestão completa no backoffice']"
               :key="item"
               class="flex items-center gap-2 text-xs transition-colors"
               :class="isDark ? 'text-zinc-500' : 'text-zinc-600'">
            <div class="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-colors"
                 :class="isDark ? 'bg-red-600/20' : 'bg-orange-500/15'">
              <div class="w-1.5 h-1.5 rounded-full transition-colors"
                   :class="isDark ? 'bg-red-500' : 'bg-orange-500'"></div>
            </div>
            {{ item }}
          </div>
        </div>
      </div>

      <!-- Painel DIREITO — formulário -->
      <div class="flex-1 flex flex-col justify-center p-7 sm:p-10 overflow-y-auto max-h-screen transition-all"
           :style="isDark
             ? 'background: rgba(12,12,12,0.97); backdrop-filter: blur(20px);'
             : 'background: rgba(255,255,255,0.97); backdrop-filter: blur(20px);'">

        <!-- Logo mobile -->
        <div class="flex sm:hidden items-center gap-3 mb-6">
          <img :src="isDark ? logoLight : logoDefault" alt="Logo" class="w-9 h-9 object-contain" />
        </div>

        <h2 class="text-xl font-bold mb-1 transition-colors"
            :class="isDark ? 'text-white' : 'text-zinc-900'">
          Criar conta
        </h2>
        <p class="text-xs mb-6 transition-colors"
           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Preenche os dados para começar
        </p>

        <form @submit.prevent="handleRegister" class="space-y-4">

          <!-- Foto de perfil -->
          <div class="flex items-center gap-4">
            <div class="relative flex-shrink-0 cursor-pointer group" @click="$refs.fileInput.click()">
              <img :src="previewUrl" alt="Foto"
                   class="w-14 h-14 rounded-full object-cover border-2 transition-colors"
                   :class="isDark ? 'border-zinc-700 group-hover:border-red-500' : 'border-gray-300 group-hover:border-orange-400'" />
              <div class="absolute inset-0 rounded-full bg-black/60 opacity-0 group-hover:opacity-100
                          flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                </svg>
              </div>
            </div>
            <div>
              <p class="text-xs font-medium transition-colors"
                 :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
                Foto de perfil <span :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">(opcional)</span>
              </p>
              <button type="button" @click="$refs.fileInput.click()"
                class="text-xs transition-colors mt-0.5"
                :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
                Escolher ficheiro
              </button>
            </div>
            <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" class="hidden" />
          </div>

          <!-- Nome -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium mb-1.5 block transition-colors"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Primeiro nome *</label>
              <input v-model="first_name" required autocomplete="given-name"
                class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
                :class="isDark
                  ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                  : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
                placeholder="Ana" />
            </div>
            <div>
              <label class="text-xs font-medium mb-1.5 block transition-colors"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Apelido</label>
              <input v-model="last_name" autocomplete="family-name"
                class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
                :class="isDark
                  ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                  : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
                placeholder="Silva" />
            </div>
          </div>

          <!-- Username -->
          <div>
            <label class="text-xs font-medium mb-1.5 block transition-colors"
                   :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Username *</label>
            <input v-model="username" required autocomplete="username"
              class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
              :class="isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
              placeholder="ana_silva" />
          </div>

          <!-- Email -->
          <div>
            <label class="text-xs font-medium mb-1.5 block transition-colors"
                   :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Email *</label>
            <input v-model="email" type="email" required autocomplete="email"
              class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
              :class="isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
              placeholder="ana@exemplo.pt" />
          </div>

          <!-- Telemóvel + Cidade -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium mb-1.5 block transition-colors"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Telemóvel</label>
              <input v-model="telefone" type="tel" autocomplete="tel"
                class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
                :class="isDark
                  ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                  : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
                placeholder="+351 9xx..." />
            </div>
            <div>
              <label class="text-xs font-medium mb-1.5 block transition-colors"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Cidade</label>
              <input v-model="morada" autocomplete="address-level2"
                class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
                :class="isDark
                  ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                  : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
                placeholder="Lisboa" />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="text-xs font-medium mb-1.5 block transition-colors"
                   :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Password *</label>
            <input v-model="password" type="password" required autocomplete="new-password"
              class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
              :class="isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
              placeholder="Mínimo 8 caracteres" />
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
            :style="isDark
              ? 'background: linear-gradient(135deg, #dc2626, #b91c1c);'
              : 'background: linear-gradient(135deg, #f97316, #ea580c);'">
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ loading ? 'A criar conta…' : 'Criar conta' }}
          </button>
        </form>

        <p class="mt-5 text-center text-xs transition-colors"
           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Já tens conta?
          <router-link to="/Login"
            class="font-semibold transition-colors"
            :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
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
import logoDefault from '@/assets/img/login/logo_final.png'
import logoLight from '@/assets/img/login/logo_final_light.png'

export default {
  name: 'RegisterView',

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    const savedTheme = localStorage.getItem('theme_preference')
    return {
      first_name: '',
      last_name:  '',
      username:   '',
      email:      '',
      telefone:   '',
      morada:     '',
      password:   '',
      file:       null,
      previewUrl: `${process.env.VUE_APP_URL_BASE}/media/utilizadores/default.png`,
      errors:     [],
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