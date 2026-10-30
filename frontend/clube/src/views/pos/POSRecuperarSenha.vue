<!-- POSRecuperarSenha.vue — "Esqueceste?" da conta principal do POS (é a mesma conta da Bendi).
     Sem uid/token: pede o email; com ?uid=…&token=… (link do email): define a password nova.
     Lógica partilhada com views/RecuperarSenha.vue em services/recuperarSenha.js. -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
    <div class="w-full max-w-md space-y-6">

      <div class="text-center">
        <h1 class="text-4xl font-black text-slate-950">POS</h1>
        <p class="mt-2 text-sm font-semibold text-slate-500">Bendi Point of Sale</p>
      </div>

      <div class="rounded-[2rem] bg-white p-8 shadow-xl">

        <div v-if="erro" class="mb-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
          {{ erro }}
        </div>

        <!-- 1) Pedir o link -->
        <template v-if="!temLink">
          <form v-if="!enviado" class="space-y-4" data-teste="form-pedir" @submit.prevent="pedirLink">
            <div>
              <h2 class="text-xl font-black text-slate-950">Recuperar password</h2>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                Indica o email da conta principal e enviamos-te um link para criares uma password nova.
              </p>
            </div>
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Email</label>
              <input v-model.trim="email" type="email" placeholder="teu@email.com" required autocomplete="email"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10" />
            </div>
            <Turnstile ref="turnstile" v-model="turnstile" />
            <button type="submit" :disabled="loading"
              class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60">
              {{ loading ? 'A enviar...' : 'Enviar link' }}
            </button>
          </form>

          <div v-else data-teste="pedido-enviado">
            <h2 class="text-xl font-black text-slate-950">Verifica o teu email</h2>
            <p class="mt-2 text-sm font-semibold leading-relaxed text-slate-500">
              Se existir uma conta com <span class="text-slate-950">{{ email }}</span>, vais receber um email com o link
              para criares uma password nova. Se não o encontrares, procura também no spam.
            </p>
          </div>
        </template>

        <!-- 2) Definir a password nova (veio do link do email) -->
        <template v-else>
          <form v-if="!alterada" class="space-y-4" data-teste="form-nova" @submit.prevent="definirPassword">
            <div>
              <h2 class="text-xl font-black text-slate-950">Nova password</h2>
              <p class="mt-1 text-sm font-semibold text-slate-500">Escolhe uma password nova para a tua conta.</p>
            </div>
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Password nova</label>
              <div class="relative">
                <input v-model="password" :type="verPassword ? 'text' : 'password'" placeholder="Mínimo 8 caracteres" required autocomplete="new-password"
                  class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 pr-11 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10" />
                <BotaoVerPassword :visivel="verPassword" :is-dark="false" @toggle="verPassword = !verPassword" />
              </div>
              <PasswordForca :password="password" :is-dark="false" />
            </div>
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Confirmar password</label>
              <div class="relative">
                <input v-model="passwordConfirm" :type="verPassword ? 'text' : 'password'" placeholder="Repete a password" required autocomplete="new-password"
                  class="h-12 w-full rounded-2xl border bg-slate-50 px-4 pr-11 text-sm outline-none transition focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                  :class="passwordsDiferentes ? 'border-red-400' : 'border-slate-200 focus:border-slate-950'" />
                <BotaoVerPassword :visivel="verPassword" :is-dark="false" @toggle="verPassword = !verPassword" />
              </div>
              <p v-if="passwordsDiferentes" class="mt-1 text-xs font-bold text-red-600">As passwords não coincidem.</p>
            </div>
            <button type="submit" :disabled="loading"
              class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60">
              {{ loading ? 'A guardar...' : 'Guardar password' }}
            </button>
          </form>

          <div v-else data-teste="password-alterada">
            <h2 class="text-xl font-black text-slate-950">Password alterada</h2>
            <p class="mt-2 mb-6 text-sm font-semibold text-slate-500">Já podes entrar no POS com a password nova.</p>
            <router-link :to="{ name: 'POSLogin' }"
              class="flex h-12 w-full items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800">
              Entrar no POS
            </router-link>
          </div>
        </template>

        <p class="mt-5 text-center text-sm font-semibold text-slate-500">
          <router-link :to="{ name: 'POSLogin' }" class="font-black text-slate-950 underline">Voltar ao login</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { useAsyncAction } from '@/composables/useAsyncAction'
import { pedirLinkRecuperacao, definirPasswordNova, mensagemErroRecuperacao, erroPasswordNova } from '@/services/recuperarSenha'
import PasswordForca from '@/components/forms/PasswordForca.vue'
import BotaoVerPassword from '@/components/forms/BotaoVerPassword.vue'
import Turnstile from '@/components/forms/Turnstile.vue'

export default {
  name: 'POSRecuperarSenha',
  components: { PasswordForca, BotaoVerPassword, Turnstile },

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
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
      turnstile:       '',
    }
  },

  computed: {
    temLink () { return !!(this.uid && this.token) },
    passwordsDiferentes () {
      return this.passwordConfirm.length > 0 && this.passwordConfirm !== this.password
    },
  },

  methods: {
    async pedirLink () {
      await this.wrap(async () => {
        this.erro = ''
        try {
          await pedirLinkRecuperacao(this.email, 'pos', this.turnstile)
          this.enviado = true
        } catch (err) {
          this.$refs.turnstile?.repor()
          this.erro = mensagemErroRecuperacao(err, 'Não foi possível enviar o email. Tenta novamente.')
        }
      })
    },

    async definirPassword () {
      await this.wrap(async () => {
        this.erro = erroPasswordNova(this.password, this.passwordConfirm)
        if (this.erro) return
        try {
          await definirPasswordNova(this.uid, this.token, this.password)
          this.alterada = true
          // tira o token do endereço (não fica no histórico)
          this.$router.replace({ query: {} })
        } catch (err) {
          this.erro = mensagemErroRecuperacao(err, 'O link é inválido ou expirou. Pede um novo.')
        }
      })
    },
  }
}
</script>
