<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <FundoConta qual="login" />
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
        <img :src="$logo(isDark)" alt="Logo"
             :class="$logoProprio() ? 'w-36 h-36' : 'w-60 h-60'" class="object-contain mb-5 drop-shadow-lg" />
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
          <img :src="$logo(isDark)" alt="Logo" :class="$logoProprio() ? 'w-24 h-24' : 'w-40 h-40'" class="object-contain" />
        </div>

        <h2 class="text-xl font-bold mb-1 transition-colors"
            :class="isDark ? 'text-white' : 'text-zinc-900'">
          Bem-vindo de volta
        </h2>
        <p class="text-xs mb-7 transition-colors"
           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Entra na tua conta para continuar
        </p>

        <FormEntrar :isDark="isDark" :seguinte="seguinte" @entrou="aoEntrar" />
      </div>
    </div>
  </div>
</template>

<script>
import { toast } from 'vue3-toastify'
import { caminhoSeguro } from '@/services/sessao'
import FormEntrar from '@/components/auth/FormEntrar.vue'
import { temaEscuro, guardarTema } from '@/utils/tema'
import FundoConta from '@/components/auth/FundoConta.vue'

export default {
  name: 'AppLogin',
  components: { FundoConta, FormEntrar },

  data () {
    return { isDark: temaEscuro() }
  },

  watch: {
    isDark (val) { guardarTema(val) },
  },

  computed: {
    // página para onde voltar depois de entrar (só caminhos internos)
    seguinte () { return caminhoSeguro(this.$route.query.seguinte) },
  },

  created () {
    if (localStorage.getItem('access_token')) this.$router.replace(this.seguinte)
  },

  methods: {
    async aoEntrar (dados) {
      if (dados.eliminacao_cancelada) {
        // depois de mudar de página: os avisos limpam-se quando o endereço muda
        await this.$router.replace(this.seguinte)
        toast.info('Bem-vindo de volta! O pedido para apagar a tua conta foi cancelado.', { autoClose: 8000, clearOnUrlChange: false })
        return
      }
      toast.success('Login bem-sucedido!', { autoClose: 2000 })
      this.$router.replace(this.seguinte)
    },
  },
}
</script>
