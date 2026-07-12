<template>
  <div class="relative w-screen h-screen overflow-hidden
           bg-[url('/src/assets/img/login/login_background2.jpg')]
           bg-cover bg-center bg-no-repeat">
    <div class="absolute inset-0 bg-black/40"></div>

    <div class="relative z-10 flex items-center justify-center h-full gap-0">

      <!-- Painel esquerdo -->
      <div class="w-96 h-[60%] p-8 shadow-md flex flex-col items-center justify-center
           bg-gradient-to-b from-black via-gray-800 to-gray-600
           rounded-tl-lg rounded-bl-lg">
        <img src="@/assets/img/login/ai_logo.png" alt="Logo" class="w-32 mb-4" />
        <h1 class="text-3xl font-bold text-white mb-4">AI Signal</h1>
        <p class="text-lg text-white text-center">Junta-te a nós!</p>
      </div>

      <!-- Painel direito -->
      <div class="w-96 h-[60%] bg-white p-8 shadow-md rounded-tr-lg rounded-br-lg overflow-y-auto">

        <h2 class="text-2xl font-bold mb-6 text-center">Registo</h2>

        <form @submit.prevent="handleRegister">

          <!-- Foto de perfil -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700">
              Foto de perfil (opcional)
            </label>
            <div class="mt-2 flex justify-center gap-3">
              <img :src="previewUrl" alt="preview" class="h-20 w-20 rounded-full object-cover border" />
              <input ref="fileInput" id="foto" type="file" accept="image/*"
                @change="onFileChange" class="hidden" />
              <div @click="triggerFileSelect" class="cursor-pointer">
                <i class="fa-solid fa-circle-plus" style="color: #000000;"></i>
              </div>
            </div>
          </div>

          <!-- Nome -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700" for="nome">Nome completo</label>
            <input id="nome" v-model="nome" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Username -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700" for="username">Username</label>
            <input id="username" v-model="username" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Email -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700" for="email">Email</label>
            <input id="email" v-model="email" type="email" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Telemóvel -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700" for="telemovel">Telemóvel</label>
            <input id="telemovel" v-model="telemovel" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- Morada -->
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700" for="morada">Morada</label>
            <input id="morada" v-model="morada" required
              class="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
          </div>

          <!-- ══════════════════════════════════════════════════════
               PASSWORD COM VALIDAÇÃO EM TEMPO REAL
          ══════════════════════════════════════════════════════ -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700" for="password">Password</label>

            <!-- Input + botão mostrar/ocultar -->
            <div class="relative mt-1">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="new-password"
                placeholder="Cria uma password segura"
                :class="[
                  'block w-full p-2 pr-10 border rounded-md transition',
                  password.length === 0
                    ? 'border-gray-300'
                    : passwordValida
                      ? 'border-emerald-400 focus:ring-emerald-200'
                      : 'border-red-300 focus:ring-red-100',
                  'focus:outline-none focus:ring-2'
                ]"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
              >
                <!-- Olho aberto -->
                <svg v-if="!showPassword" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <!-- Olho fechado -->
                <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21" />
                </svg>
              </button>
            </div>

            <!-- Só aparece quando o utilizador começa a escrever -->
            <div v-if="password.length > 0" class="mt-2.5">

              <!-- Label de força + barras -->
              <div class="flex items-center justify-between mb-1">
                <div class="flex gap-1 flex-1">
                  <div
                    v-for="i in 4"
                    :key="i"
                    :class="[
                      'h-1 flex-1 rounded-full transition-all duration-300',
                      i <= passwordStrength.level
                        ? passwordStrength.level === 1 ? 'bg-red-400'
                        : passwordStrength.level === 2 ? 'bg-amber-400'
                        : passwordStrength.level === 3 ? 'bg-blue-400'
                        : 'bg-emerald-500'
                        : 'bg-gray-200'
                    ]"
                  ></div>
                </div>
                <span
                  :class="[
                    'ml-3 text-xs font-semibold w-16 text-right',
                    passwordStrength.level === 1 ? 'text-red-500'
                    : passwordStrength.level === 2 ? 'text-amber-500'
                    : passwordStrength.level === 3 ? 'text-blue-500'
                    : 'text-emerald-600'
                  ]"
                >{{ passwordStrength.label }}</span>
              </div>

              <!-- Lista de requisitos -->
              <ul class="mt-2 space-y-1">
                <li
                  v-for="rule in passwordRules"
                  :key="rule.id"
                  :class="[
                    'flex items-center gap-1.5 text-xs font-medium transition-colors duration-150',
                    rule.met ? 'text-emerald-600' : 'text-red-500'
                  ]"
                >
                  <!-- ✓ -->
                  <svg v-if="rule.met" class="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                  </svg>
                  <!-- ✗ -->
                  <svg v-else class="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {{ rule.label }}
                </li>
              </ul>
            </div>
          </div>
          <!-- ══════════════════════════════════════════════════════ -->

          <!-- Botão -->
          <button
            type="submit"
            :disabled="loading || !podeSubmeter"
            :class="[
              'w-full py-2 rounded text-white transition',
              loading || !podeSubmeter
                ? 'bg-blue-300 cursor-not-allowed opacity-70'
                : 'bg-blue-500 hover:bg-blue-600'
            ]"
          >
            <span v-if="!loading">Criar conta</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25" />
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75" />
              </svg>
            </span>
          </button>
        </form>

        <p v-if="warning" class="text-red-500 text-center mt-2 text-sm">
          Não foi possível criar a conta. Tente novamente.
        </p>

        <p class="mt-4 text-center text-sm">
          Já tens conta?
          <router-link to="/Login" class="text-blue-500">Entra aqui</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { useAsyncAction } from '@/composables/useAsyncAction'

export default {
  name: 'RegisterView',

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      nome: '',
      username: '',
      email: '',
      telemovel: '',
      morada: '',
      password: '',
      showPassword: false,
      file: null,
      previewUrl: `${process.env.VUE_APP_URL_BASE}/media/utilizadores/default.png`,
      warning: false,
      backendUrl: process.env.VUE_APP_URL_BASE,
    }
  },

  computed: {
    passwordRules () {
      const v = this.password
      return [
        { id: 'len',     label: 'Mínimo 8 caracteres',                     met: v.length >= 8 },
        { id: 'upper',   label: 'Pelo menos uma letra maiúscula (A-Z)',     met: /[A-Z]/.test(v) },
        { id: 'lower',   label: 'Pelo menos uma letra minúscula (a-z)',     met: /[a-z]/.test(v) },
        { id: 'num',     label: 'Pelo menos um número (0-9)',               met: /[0-9]/.test(v) },
        { id: 'special', label: 'Pelo menos um carácter especial (!@#$%…)', met: /[!@#$%^&*()\-_=+\[\]{};':"\\|,.<>/?]/.test(v) },
      ]
    },

    passwordStrength () {
      const score = this.passwordRules.filter(r => r.met).length
      if (score === 0) return { level: 0, label: '' }
      if (score <= 2)  return { level: 1, label: 'Fraca' }
      if (score === 3) return { level: 2, label: 'Razoável' }
      if (score === 4) return { level: 3, label: 'Boa' }
      return             { level: 4, label: 'Forte' }
    },

    passwordValida () {
      return this.passwordRules.every(r => r.met)
    },

    // Botão só fica activo quando a password é válida
    podeSubmeter () {
      return this.passwordValida
    },
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

    triggerFileSelect () {
      this.$refs.fileInput.click()
    },

    async handleRegister () {
      // Guard extra: não submeter se password não cumprir todos os requisitos
      if (!this.passwordValida) {
        this.warning = true
        return
      }

      await this.wrap(async () => {
        this.warning = false

        const form = new FormData()
        form.append('nome',         this.nome)
        form.append('username',     this.username)
        form.append('password',     this.password)
        form.append('nome_contato', this.nome)
        form.append('email',        this.email)
        form.append('telemovel',    this.telemovel)
        form.append('morada',       this.morada)
        form.append('perfil_id',    1)
        form.append('clube_id',     1)
        if (this.file) form.append('foto', this.file)

        try {
          const res = await axios.post(
            `${this.backendUrl}/app/utilizador/registar/`,
            form,
            { headers: { 'Content-Type': 'multipart/form-data' } }
          )

          if (res.status === 201) {
            this.$router.push('/login')
          } else {
            this.warning = true
          }
        } catch (err) {
          this.warning = true
          console.error(err)
        }
      })
    }
  }
}
</script>

<style scoped>
/* estilos extra se necessário */
</style>