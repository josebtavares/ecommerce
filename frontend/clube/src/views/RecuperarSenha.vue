<!-- RecuperarSenha.vue — "Esqueceste?" do login.
     Sem uid/token: pede o email e envia o link (POST /app/utilizador/recuperar_senha/).
     Com ?uid=…&token=… (o link do email): define a password nova (POST …/recuperar_senha/confirmar/). -->
<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <video autoplay muted loop playsinline
      class="absolute inset-0 w-full h-full object-cover">
      <source :src="videoFundo" type="video/mp4">
    </video>
    <div class="absolute inset-0" :class="isDark ? 'bg-black/55' : 'bg-black/30'"></div>

    <button @click="isDark = !isDark"
      class="absolute top-4 right-4 z-20 w-9 h-9 rounded-full flex items-center justify-center
             border transition-all shadow-lg"
      :class="isDark
        ? 'bg-zinc-900/80 border-zinc-700 hover:border-zinc-500 text-zinc-300'
        : 'bg-white/80 border-white/60 hover:border-orange-400 text-zinc-700'">
      <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
      </svg>
    </button>

    <div class="relative z-10 w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl transition-all"
         style="min-height: 480px;">

      <!-- Painel ESQUERDO -->
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

      <!-- Painel DIREITO -->
      <div class="flex-1 flex flex-col justify-center p-8 sm:p-10 transition-all"
           :style="isDark
             ? 'background: rgba(12,12,12,0.97); backdrop-filter: blur(20px);'
             : 'background: rgba(255,255,255,0.97); backdrop-filter: blur(20px);'">

        <div class="flex sm:hidden items-center gap-3 mb-8 justify-center">
          <img :src="isDark ? logoLight : logoDefault" alt="Logo" class="w-40 h-40 object-contain" />
        </div>

        <!-- 1) Pedir o link -->
        <template v-if="!temLink">
          <template v-if="!enviado">
            <h2 class="text-xl font-bold mb-1 transition-colors" :class="isDark ? 'text-white' : 'text-zinc-900'">
              Recuperar password
            </h2>
            <p class="text-xs mb-7 transition-colors" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Indica o email da tua conta e enviamos-te um link para criares uma password nova.
            </p>
            <form @submit.prevent="pedirLink" class="space-y-4" data-teste="form-pedir">
              <div>
                <label class="text-xs font-medium mb-1.5 block transition-colors"
                       :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Email</label>
                <input v-model.trim="email" type="email" required autocomplete="email"
                  class="w-full px-4 py-2.5 rounded-xl text-sm border transition-all focus:outline-none placeholder-zinc-400"
                  :class="isDark
                    ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500'
                    : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400'"
                  placeholder="o_teu@email.com" />
              </div>
              <div v-if="erro" class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
                {{ erro }}
              </div>
              <button type="submit" :disabled="loading" class="botao-principal" :class="loading ? 'opacity-60 cursor-not-allowed' : 'hover:opacity-90 active:scale-[0.98]'"
                :style="gradiente">
                {{ loading ? 'A enviar…' : 'Enviar link' }}
              </button>
            </form>
          </template>

          <div v-else data-teste="pedido-enviado">
            <h2 class="text-xl font-bold mb-3 transition-colors" :class="isDark ? 'text-white' : 'text-zinc-900'">
              Verifica o teu email
            </h2>
            <p class="text-sm leading-relaxed transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
              Se existir uma conta com <strong>{{ email }}</strong>, vais receber um email com o link para criares uma password nova.
              Se não o encontrares, procura também no spam.
            </p>
          </div>
        </template>

        <!-- 2) Definir a password nova (veio do link do email) -->
        <template v-else>
          <template v-if="!alterada">
            <h2 class="text-xl font-bold mb-1 transition-colors" :class="isDark ? 'text-white' : 'text-zinc-900'">
              Nova password
            </h2>
            <p class="text-xs mb-7 transition-colors" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Escolhe uma password nova para a tua conta.
            </p>
            <form @submit.prevent="definirPassword" class="space-y-4" data-teste="form-nova">
              <div>
                <label class="text-xs font-medium mb-1.5 block transition-colors"
                       :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Password nova</label>
                <div class="relative">
                  <input v-model="password" :type="verPassword ? 'text' : 'password'" required autocomplete="new-password"
                    class="w-full px-4 pr-10 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
                    :class="isDark
                      ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500 placeholder-zinc-600'
                      : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400 placeholder-zinc-400'"
                    placeholder="Mínimo 8 caracteres" />
                  <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
                </div>
                <PasswordForca :password="password" :isDark="isDark" />
              </div>
              <div>
                <label class="text-xs font-medium mb-1.5 block transition-colors"
                       :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Confirmar password</label>
                <div class="relative">
                  <input v-model="passwordConfirm" :type="verPassword ? 'text' : 'password'" required autocomplete="new-password"
                    class="w-full px-4 pr-10 py-2.5 rounded-xl text-sm border transition-all focus:outline-none"
                    :class="[
                      isDark ? 'bg-zinc-900 text-zinc-100 placeholder-zinc-600' : 'bg-gray-50 text-zinc-900 placeholder-zinc-400',
                      passwordsDiferentes ? 'border-red-500'
                        : (isDark ? 'border-zinc-800 focus:border-red-500' : 'border-gray-200 focus:border-orange-400')
                    ]"
                    placeholder="Repete a password" />
                  <BotaoVerPassword :visivel="verPassword" :isDark="isDark" @toggle="verPassword = !verPassword" />
                </div>
                <p v-if="passwordsDiferentes" class="mt-1 text-xs text-red-400">As passwords não coincidem.</p>
              </div>
              <div v-if="erro" class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
                {{ erro }}
              </div>
              <button type="submit" :disabled="loading" class="botao-principal" :class="loading ? 'opacity-60 cursor-not-allowed' : 'hover:opacity-90 active:scale-[0.98]'"
                :style="gradiente">
                {{ loading ? 'A guardar…' : 'Guardar password' }}
              </button>
            </form>
          </template>

          <div v-else data-teste="password-alterada">
            <h2 class="text-xl font-bold mb-3 transition-colors" :class="isDark ? 'text-white' : 'text-zinc-900'">
              Password alterada
            </h2>
            <p class="text-sm leading-relaxed mb-6 transition-colors" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
              Já podes entrar com a password nova.
            </p>
            <router-link :to="{ name: 'Login' }" class="botao-principal" :style="gradiente">Entrar</router-link>
          </div>
        </template>

        <p class="mt-5 text-center text-xs transition-colors" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Lembraste-te?
          <router-link :to="{ name: 'Login' }" class="font-semibold transition-colors"
            :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-orange-500 hover:text-orange-400'">
            Voltar ao login
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { useAsyncAction } from '@/composables/useAsyncAction'
import api from '@/services/api.js'
import { mediaUrl } from '@/services/media'
import { passwordValida } from '@/utils/password'
import PasswordForca from '@/components/forms/PasswordForca.vue'
import BotaoVerPassword from '@/components/forms/BotaoVerPassword.vue'
import logoDefault from '@/assets/img/login/logo_final_4k.png'
import logoLight from '@/assets/img/login/logo_final_4k_light.png'

export default {
  name: 'RecuperarSenha',
  components: { PasswordForca, BotaoVerPassword },

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    const savedTheme = localStorage.getItem('theme_preference')
    return {
      videoFundo:      mediaUrl('videos/background.mp4'),
      email:           '',
      enviado:         false,
      password:        '',
      passwordConfirm: '',
      verPassword:     false,
      alterada:        false,
      // lidos uma vez: o token sai do endereço depois de usado
      uid:             this.$route.query.uid || '',
      token:           this.$route.query.token || '',
      erro:            '',
      isDark: savedTheme ? savedTheme === 'dark' : true,
      logoDefault,
      logoLight,
    }
  },

  computed: {
    temLink () { return !!(this.uid && this.token) },
    passwordsDiferentes () {
      return this.passwordConfirm.length > 0 && this.passwordConfirm !== this.password
    },
    gradiente () {
      return this.isDark
        ? 'background: linear-gradient(135deg, #dc2626, #b91c1c);'
        : 'background: linear-gradient(135deg, #f97316, #ea580c);'
    },
  },

  watch: {
    isDark (val) {
      localStorage.setItem('theme_preference', val ? 'dark' : 'light')
    }
  },

  methods: {
    // mensagem do backend: {detail} ou {campo: [erros]}
    mensagemErro (err, padrao) {
      const d = err.response?.data
      if (err.response?.status === 429) return d?.detail || 'Demasiados pedidos. Tenta novamente mais tarde.'
      if (d?.detail) return d.detail
      const primeiro = d && typeof d === 'object' ? Object.values(d)[0] : null
      return (Array.isArray(primeiro) ? primeiro[0] : primeiro) || padrao
    },

    async pedirLink () {
      await this.wrap(async () => {
        this.erro = ''
        try {
          await api.post('/app/utilizador/recuperar_senha/', { email: this.email })
          this.enviado = true
        } catch (err) {
          this.erro = this.mensagemErro(err, 'Não foi possível enviar o email. Tenta novamente.')
        }
      })
    },

    async definirPassword () {
      await this.wrap(async () => {
        this.erro = ''
        if (!passwordValida(this.password)) {
          this.erro = 'A password não cumpre todos os requisitos de segurança.'
          return
        }
        if (this.password !== this.passwordConfirm) {
          this.erro = 'As passwords não coincidem.'
          return
        }
        try {
          await api.post('/app/utilizador/recuperar_senha/confirmar/', {
            uid: this.uid, token: this.token, new_password: this.password,
          })
          this.alterada = true
          // tira o token do endereço (não fica no histórico)
          this.$router.replace({ query: {} })
        } catch (err) {
          this.erro = this.mensagemErro(err, 'O link é inválido ou expirou. Pede um novo.')
        }
      })
    },
  }
}
</script>

<style scoped>
.botao-principal {
  width: 100%;
  padding: 0.625rem 0;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 150ms ease, transform 150ms ease;
}
</style>
