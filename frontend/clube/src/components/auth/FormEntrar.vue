<!-- FormEntrar.vue — formulário de entrar na conta Bendi (username/email + password, ou Google).
     Usado na página /Login e na janela da landing page (/sobre). Guarda a sessão e emite 'entrou' (res.data);
     quem o usa decide para onde ir. modal=true: o link "Regista-te" emite 'trocar' em vez de mudar de página. -->
<template>
  <form @submit.prevent="handleLogin" class="space-y-4" data-teste="form-entrar">
    <div>
      <label class="text-xs font-medium mb-1.5 block transition-colors"
             :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Username ou Email</label>
      <input v-model="username" required autocomplete="username"
        class="w-full px-4 py-2.5 rounded-xl text-sm border transition-all focus:outline-none placeholder-zinc-400"
        :class="isDark
          ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500'
          : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400'"
        placeholder="o_teu_username" />
    </div>

    <div>
      <div class="flex items-center justify-between mb-1.5">
        <label class="text-xs font-medium transition-colors"
               :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Password</label>
        <router-link :to="{ name: 'RecuperarSenha' }" class="text-xs transition-colors"
           :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
          Esqueceste?
        </router-link>
      </div>
      <div class="relative">
        <input v-model="password" :type="verPassword ? 'text' : 'password'" required autocomplete="current-password"
          class="w-full px-4 pr-10 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
          :class="isDark
            ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500'
            : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400'"
          placeholder="••••••••" />
        <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
      </div>
    </div>

    <!-- captcha adaptativo (backend utils/auth.py): só aparece depois de tentativas falhadas -->
    <Turnstile v-if="captcha" ref="turnstile" v-model="turnstile" :isDark="isDark" />

    <div v-if="warning"
         class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
      {{ warningMsg }}
    </div>

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
      {{ loading ? 'A entrar…' : 'Entrar' }}
    </button>

    <div class="flex items-center gap-3">
      <div class="flex-1 h-px transition-colors" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
      <span class="text-[10px] font-medium transition-colors"
            :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">ou continua com</span>
      <div class="flex-1 h-px transition-colors" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
    </div>

    <BotaoGoogle :isDark="isDark" :seguinte="seguinte" texto-erro="Erro ao iniciar login com Google." />

    <p class="pt-1 text-center text-xs transition-colors" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
      Ainda não tens conta?
      <button v-if="modal" type="button" @click="$emit('trocar')" data-teste="ir-registo"
        class="font-semibold transition-colors"
        :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">Regista-te</button>
      <router-link v-else :to="{ name: 'Register', query: $route.query }"
        class="font-semibold transition-colors"
        :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
        Regista-te
      </router-link>
    </p>
  </form>
</template>

<script>
import { toast } from 'vue3-toastify'
import { useAsyncAction } from '@/composables/useAsyncAction'
import api from '@/services/api.js'
import BotaoVerPassword from '@/components/forms/BotaoVerPassword.vue'
import BotaoGoogle from '@/components/auth/BotaoGoogle.vue'
import Turnstile from '@/components/forms/Turnstile.vue'
import { guardarSessao } from '@/services/sessao'

export default {
  name: 'FormEntrar',
  components: { BotaoVerPassword, BotaoGoogle, Turnstile },
  props: {
    isDark: { type: Boolean, default: false },
    seguinte: { type: String, default: '/Home' },     // para onde o Google volta depois de entrar
    modal: { type: Boolean, default: false },
  },
  emits: ['entrou', 'trocar'],

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return { username: '', password: '', verPassword: false, warning: false, warningMsg: 'Credenciais inválidas.',
             captcha: false, turnstile: '' }
  },

  methods: {
    async handleLogin () {
      await this.wrap(async () => {
        this.warning = false
        try {
          const corpo = { username: this.username, password: this.password }
          if (this.captcha) corpo.turnstile = this.turnstile
          const res = await api.post('/app/utilizador/login/', corpo)
          guardarSessao(res.data)
          this.$emit('entrou', res.data)
        } catch (err) {
          const msg = err.response?.data?.detail || 'Credenciais inválidas.'
          // depois de algumas falhas o servidor pede o "não sou um robô"; cada resposta só vale uma vez
          if (err.response?.data?.turnstile) {
            if (this.captcha) this.$refs.turnstile?.repor()
            this.captcha = true
          }
          this.warningMsg = msg
          this.warning = true
          toast.error(msg, { autoClose: 3000 })
        }
      })
    },
  },
}
</script>
