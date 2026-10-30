<!-- ConfirmarEmail.vue — destino do link do email de confirmação (/confirmar_email?token=…).
     Confirma no backend (POST /app/utilizador/confirmar_email/ — não precisa de sessão, pode ser outro browser)
     e, se houver sessão aqui, actualiza o utilizador guardado para o aviso do topo desaparecer. -->
<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-10"
       :class="isDark ? 'bg-zinc-950' : 'bg-stone-50'">
    <div class="w-full max-w-md rounded-2xl border p-8 text-center shadow-sm"
         :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'" data-teste="confirmar-email">
      <img :src="isDark ? logoLight : logoDefault" alt="Bende" class="w-28 h-28 object-contain mx-auto mb-4" />

      <template v-if="estado === 'a_confirmar'">
        <div class="h-8 w-8 mx-auto animate-spin rounded-full border-2 border-red-500/30 border-t-red-500"></div>
        <p class="mt-4 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">A confirmar o teu email…</p>
      </template>

      <template v-else-if="estado === 'confirmado'">
        <div class="w-14 h-14 mx-auto rounded-full bg-green-500/15 text-green-500 flex items-center justify-center text-2xl">
          <font-awesome-icon :icon="['fas', 'circle-check']" />
        </div>
        <h1 class="mt-4 text-xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'" data-teste="confirmar-ok">Email confirmado</h1>
        <p class="mt-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
          Obrigado! <b v-if="email" class="break-all">{{ email }}</b> está confirmado. Já podes encomendar, marcar serviços e criar a tua loja.
        </p>
        <router-link :to="autenticado ? { name: 'Home' } : { name: 'Login' }"
          class="mt-6 inline-block px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500">
          {{ autenticado ? 'Continuar' : 'Entrar' }}
        </router-link>
      </template>

      <template v-else>
        <div class="w-14 h-14 mx-auto rounded-full bg-red-500/15 text-red-500 flex items-center justify-center text-2xl">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
        </div>
        <h1 class="mt-4 text-xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Não foi possível confirmar</h1>
        <p class="mt-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'" data-teste="confirmar-erro">{{ erro }}</p>
        <div v-if="autenticado && porConfirmar" class="mt-5">
          <AvisoConfirmarEmail :isDark="isDark">O link pode ter expirado.</AvisoConfirmarEmail>
        </div>
        <router-link v-else :to="autenticado ? { name: 'Home' } : { name: 'Login', query: { seguinte: '/Home' } }"
          class="mt-6 inline-block px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500">
          {{ autenticado ? 'Voltar' : 'Entrar e pedir um novo link' }}
        </router-link>
      </template>
    </div>
  </div>
</template>

<script>
import AvisoConfirmarEmail from '@/components/auth/AvisoConfirmarEmail.vue'
import { confirmarLink, atualizarDoServidor, emailPorConfirmar } from '@/services/confirmarEmail'
import { estaAutenticado } from '@/services/sessao'
import logoDefault from '@/assets/img/login/logo_final_640.webp'
import logoLight from '@/assets/img/login/logo_final_640_light.webp'
import { temaEscuro } from '@/utils/tema'

export default {
  name: 'ConfirmarEmail',
  components: { AvisoConfirmarEmail },

  data () {
    return {
      estado: 'a_confirmar', erro: '', email: '',
      // lido uma vez: o token sai do endereço
      token: this.$route.query.token || '',
      autenticado: estaAutenticado(), porConfirmar: emailPorConfirmar(),
      isDark: temaEscuro(), logoDefault, logoLight,
    }
  },

  async mounted () {
    this.$router.replace({ query: {} })
    if (!this.token) {
      this.estado = 'erro'; this.erro = 'Link incompleto. Abre o link do email outra vez.'
      return
    }
    try {
      const { data } = await confirmarLink(this.token)
      this.email = data.email
      this.estado = 'confirmado'
      if (this.autenticado) await atualizarDoServidor().catch(() => {})
    } catch (e) {
      this.estado = 'erro'
      this.erro = e.response?.data?.detail || 'Não foi possível confirmar. Tenta outra vez mais tarde.'
    }
  },
}
</script>
