<!-- FormRegisto.vue — formulário de criar conta Bende (Turnstile + armadilha para bots, email por confirmar).
     Usado na página /Register e na janela da landing page (/sobre). Guarda a sessão e emite 'criou' (res.data);
     quem o usa decide para onde ir. modal=true: o link "Entrar" emite 'trocar' em vez de mudar de página. -->
<template>
  <div>
    <form @submit.prevent="handleRegister" class="space-y-4" data-teste="form-registo">
  
      <!-- Foto -->
      <div class="flex items-center gap-4">
        <div class="relative flex-shrink-0 cursor-pointer group" @click="$refs.fileInput.click()">
          <img :src="previewUrl" alt="Foto"
               class="w-14 h-14 rounded-full object-cover border-2 transition-colors"
               :class="isDark ? 'border-zinc-700 group-hover:border-red-500' : 'border-gray-300 group-hover:border-orange-400'" />
          <div class="absolute inset-0 rounded-full bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            </svg>
          </div>
        </div>
        <div>
          <p class="text-xs font-medium transition-colors" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
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
          <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Primeiro nome *</label>
          <input v-model="first_name" required autocomplete="given-name"
            class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
            placeholder="Ana" />
        </div>
        <div>
          <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Apelido</label>
          <input v-model="last_name" autocomplete="family-name"
            class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
            placeholder="Silva" />
        </div>
      </div>
  
      <!-- Username -->
      <div>
        <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Username *</label>
        <input v-model="username" required autocomplete="username" @input="verUsername.verificar(username)"
          class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
          :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
          placeholder="ana_silva" />
        <EstadoDisponibilidade :verificador="verUsername" :isDark="isDark" @usar="u => { username = u; verUsername.verificar(u) }" />
      </div>
  
      <!-- Email -->
      <div>
        <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Email *</label>
        <input v-model="email" type="email" required autocomplete="email" @input="verEmail.verificar(email)"
          class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
          :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
          placeholder="ana@exemplo.pt" />
        <EstadoDisponibilidade :verificador="verEmail" :isDark="isDark" />
      </div>
  
      <!-- Telemóvel + Cidade -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Telemóvel</label>
          <input v-model="telefone" type="tel" autocomplete="tel"
            class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
            placeholder="+238 9xx xx xx" />
        </div>
        <div>
          <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Cidade</label>
          <input v-model="morada" autocomplete="address-level2"
            class="w-full px-3 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
            placeholder="Praia" />
        </div>
      </div>
  
      <!-- Password -->
      <div>
        <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Password *</label>
        <div class="relative">
          <input v-model="password" :type="verPassword ? 'text' : 'password'" required autocomplete="new-password"
            class="w-full px-3 pr-10 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600' : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
            placeholder="Mínimo 8 caracteres" />
          <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
        </div>
  
        <!-- Barra de força + checklist -->
        <PasswordForca :password="password" :isDark="isDark" />
      </div>
  
      <!-- Confirmar password -->
      <div>
        <label class="text-xs font-medium mb-1.5 block transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Confirmar password *</label>
        <div class="relative">
          <input v-model="passwordConfirm" :type="verPassword ? 'text' : 'password'" required autocomplete="new-password"
            class="w-full px-3 pr-10 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
            :class="[
              isDark ? 'bg-zinc-900 text-zinc-100 placeholder-zinc-600' : 'bg-gray-50 text-zinc-900 placeholder-zinc-400',
              passwordsDiferentes ? 'border-red-500'
                : (isDark ? 'border-zinc-800 focus:border-red-500' : 'border-gray-200 focus:border-orange-400')
            ]"
            placeholder="Repete a password" />
          <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
        </div>
        <p v-if="passwordsDiferentes" class="mt-1 text-[11px] text-red-400">As passwords não coincidem.</p>
      </div>
  
      <!-- armadilha para bots (utils/turnstile.py): uma pessoa não vê nem preenche este campo -->
      <div aria-hidden="true" class="absolute -left-[9999px] w-px h-px overflow-hidden">
        <label>Website <input v-model="website" type="text" name="website" tabindex="-1" autocomplete="off" /></label>
      </div>
      <Turnstile ref="turnstile" v-model="turnstile" :isDark="isDark" />
  
      <!-- Erros -->
      <div v-if="errors.length" class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 space-y-0.5">
        <p v-for="(e, i) in errors" :key="i" class="text-red-400 text-xs">{{ e }}</p>
      </div>
  
      <!-- Botão registo principal -->
      <button type="submit" :disabled="loading"
        class="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all
               flex items-center justify-center gap-2"
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
  
      <!-- Separador -->
      <div class="flex items-center gap-3">
        <div class="flex-1 h-px transition-colors" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
        <span class="text-[10px] font-medium transition-colors" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">ou regista-te com</span>
        <div class="flex-1 h-px transition-colors" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
      </div>
  
      <BotaoGoogle :isDark="isDark" :seguinte="seguinte" texto-erro="Erro ao iniciar registo com Google." />
    </form>

    <p class="mt-5 text-center text-xs transition-colors" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
      Já tens conta?
      <button v-if="modal" type="button" @click="$emit('trocar')" data-teste="ir-entrar"
        class="font-semibold transition-colors"
        :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">Entrar</button>
      <router-link v-else :to="{ name: 'Login', query: $route.query }"
        class="font-semibold transition-colors"
        :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
        Entrar
      </router-link>
    </p>
  </div>
</template>

<script>
import { toast } from 'vue3-toastify'
import { useAsyncAction } from '@/composables/useAsyncAction'
import api from '@/services/api.js'
import { DEFAULT_UTILIZADOR } from '@/services/media'
import { guardarSessao } from '@/services/sessao'
import PasswordForca from '@/components/forms/PasswordForca.vue'
import BotaoVerPassword from '@/components/forms/BotaoVerPassword.vue'
import EstadoDisponibilidade from '@/components/forms/EstadoDisponibilidade.vue'
import Turnstile from '@/components/forms/Turnstile.vue'
import BotaoGoogle from '@/components/auth/BotaoGoogle.vue'
import { criarVerificador } from '@/services/disponibilidade'
import { passwordValida } from '@/utils/password'

export default {
  name: 'FormRegisto',
  components: { PasswordForca, BotaoVerPassword, EstadoDisponibilidade, Turnstile, BotaoGoogle },
  props: {
    isDark: { type: Boolean, default: false },
    seguinte: { type: String, default: '/Home' },     // para onde o Google volta depois de entrar
    modal: { type: Boolean, default: false },
  },
  emits: ['criou', 'trocar'],

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      first_name: '', last_name: '', username: '', email: '', telefone: '', morada: '',
      password: '', passwordConfirm: '', verPassword: false,
      verUsername: criarVerificador('username'),
      verEmail: criarVerificador('email'),
      file: null, previewUrl: DEFAULT_UTILIZADOR, errors: [],
      turnstile: '', website: '',
    }
  },

  computed: {
    isPasswordValid () { return passwordValida(this.password) },
    // só avisa depois de começar a escrever a confirmação
    passwordsDiferentes () { return this.passwordConfirm.length > 0 && this.passwordConfirm !== this.password },
  },

  methods: {
    onFileChange (e) {
      const f = e.target.files[0]
      this.file = f || null
      this.previewUrl = f ? URL.createObjectURL(f) : DEFAULT_UTILIZADOR
    },

    async handleRegister () {
      await this.wrap(async () => {
        this.errors = []
        if (!this.isPasswordValid) {
          this.errors = ['A password não cumpre todos os requisitos de segurança.']
          return
        }
        if (this.password !== this.passwordConfirm) {
          this.errors = ['As passwords não coincidem.']
          return
        }
        if (this.verUsername.bloqueia || this.verEmail.bloqueia) {
          this.errors = [this.verUsername.motivo, this.verEmail.motivo].filter(Boolean)
          return
        }
        const form = new FormData()
        for (const k of ['username', 'email', 'password', 'first_name', 'last_name', 'telefone', 'morada']) {
          form.append(k, this[k])
        }
        if (this.file) form.append('foto', this.file)
        form.append('turnstile', this.turnstile)
        form.append('website', this.website)
        try {
          const res = await api.post('/app/utilizador/registar/', form, { headers: { 'Content-Type': 'multipart/form-data' } })
          guardarSessao(res.data)
          toast.success('Conta criada! Enviámos-te um email para confirmares o endereço.', { autoClose: 4000 })
          this.$emit('criou', res.data)
        } catch (err) {
          const data = err.response?.data
          this.$refs.turnstile?.repor()      // cada resposta do Turnstile só vale uma vez
          if (data?.detail) this.errors = [data.detail]
          else if (data && typeof data === 'object') this.errors = Object.values(data).flat()
          else this.errors = ['Não foi possível criar a conta. Tente novamente.']
          toast.error('Erro no registo.', { autoClose: 3000 })
        }
      })
    },
  },
}
</script>
