<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 relative overflow-hidden">

    <FundoConta qual="registo" />
    <div class="absolute inset-0 transition-all" :class="isDark ? 'bg-black/55' : 'bg-black/30'"></div>

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

    <div class="relative z-10 w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl transition-all">

      <!-- Painel ESQUERDO -->
      <div class="hidden sm:flex w-2/5 flex-col items-center justify-center p-10 flex-shrink-0 transition-all"
           :style="isDark
             ? 'background: linear-gradient(160deg, rgba(0,0,0,0.95) 0%, rgba(20,0,0,0.92) 100%); border-right: 1px solid rgba(220,38,38,0.2);'
             : 'background: linear-gradient(160deg, rgba(255,247,237,0.98) 0%, rgba(255,237,213,0.96) 100%); border-right: 1px solid rgba(249,115,22,0.18);'">
        <img :src="$logo(isDark)" alt="Logo"
             :class="$logoProprio() ? 'w-44 h-44' : 'w-60 h-60'" class="object-contain mb-5 drop-shadow-lg" />
        <p class="text-sm mt-2 text-center leading-relaxed transition-colors"
           :class="isDark ? 'text-zinc-400' : 'text-zinc-700'">
          Junta-te à comunidade<br/>de compradores e vendedores
        </p>
        <div class="mt-6 w-10 h-0.5 rounded-full opacity-70 transition-colors"
             :class="isDark ? 'bg-red-600' : 'bg-orange-500'"></div>
        <div class="mt-5 space-y-2 w-full">
          <div v-for="item in ['Cria a tua loja em minutos', 'Compra de lojas locais', 'Gestão completa no backoffice']"
               :key="item" class="flex items-center gap-2 text-xs transition-colors"
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

      <!-- Painel DIREITO -->
      <div class="flex-1 flex flex-col [justify-content:safe_center] p-7 sm:p-10 overflow-y-auto max-h-screen transition-all"
           :style="isDark
             ? 'background: rgba(12,12,12,0.97); backdrop-filter: blur(20px);'
             : 'background: rgba(255,255,255,0.97); backdrop-filter: blur(20px);'">

        <div class="flex sm:hidden items-center gap-3 justify-center">
          <img :src="$logo(isDark)" alt="Logo" :class="$logoProprio() ? 'w-28 h-28' : 'w-40 h-40'" class="object-contain" />
        </div>

        <h2 class="text-xl font-bold mb-1 transition-colors"
            :class="isDark ? 'text-white' : 'text-zinc-900'">Criar conta</h2>
        <p class="text-xs mb-6 transition-colors"
           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Preenche os dados para começar</p>

        <FormRegisto :isDark="isDark" :seguinte="seguinte" @criou="$router.replace(seguinte)" />
      </div>
    </div>
  </div>
</template>

<script>
import { caminhoSeguro } from '@/services/sessao'
import FormRegisto from '@/components/auth/FormRegisto.vue'
import { temaEscuro, guardarTema } from '@/utils/tema'
import FundoConta from '@/components/auth/FundoConta.vue'

export default {
  name: 'RegisterView',
  components: { FundoConta, FormRegisto },
  data () {
    return { isDark: temaEscuro() }
  },
  computed: {
    // página para onde voltar depois de criar a conta (só caminhos internos)
    seguinte () { return caminhoSeguro(this.$route.query.seguinte) },
  },
  watch: {
    isDark (val) { guardarTema(val) },
  },
}
</script>
