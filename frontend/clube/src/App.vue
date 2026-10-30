<template>
  <!-- "Confirma o teu email" (services/confirmarEmail.js) — fora do POS e das páginas de entrada -->
  <AvisoConfirmarEmail v-if="mostrarAviso" faixa @fechar="fechado = true" />
  <router-view />
  <!-- "Entra ou cria conta" — partilhado por todas as páginas públicas (services/sessao.js) -->
  <PedirLogin />
  <!-- balão do chat (só nas páginas onde faz sentido — ver ChatFlutuante.vue) -->
  <ChatFlutuante />
</template>

<script>
import PedirLogin from '@/components/auth/PedirLogin.vue'
import ChatFlutuante from '@/components/chat/ChatFlutuante.vue'
import AvisoConfirmarEmail from '@/components/auth/AvisoConfirmarEmail.vue'
import { EVENTO, emailPorConfirmar, atualizarDoServidor } from '@/services/confirmarEmail'

const SEM_AVISO = /^\/(pos|login|register|confirmar_email|recuperar_senha|auth)(\/|$)/i

export default {
  name: 'App',
  components: {
    PedirLogin,
    ChatFlutuante,
    AvisoConfirmarEmail,
  },

  data () {
    return { porConfirmar: emailPorConfirmar(), fechado: false, verificado: false }
  },

  computed: {
    mostrarAviso () {
      return this.porConfirmar && !this.fechado && !SEM_AVISO.test(this.$route.path)
    },
  },

  watch: {
    // entrou/saiu/registou-se noutra página: o utilizador guardado mudou
    '$route.path' () { this.atualizar() },
  },

  mounted () {
    window.addEventListener(EVENTO, this.atualizar)
    window.addEventListener('storage', this.atualizar)       // outro separador (ex.: o do link)
    this.atualizar()
  },

  beforeUnmount () {
    window.removeEventListener(EVENTO, this.atualizar)
    window.removeEventListener('storage', this.atualizar)
  },

  methods: {
    atualizar (e) {
      const antes = this.porConfirmar
      this.porConfirmar = emailPorConfirmar()
      if (e?.type === EVENTO && this.porConfirmar && !antes) this.fechado = false   // voltou a ser preciso (ex.: no checkout)
      // uma vez por visita confirma no servidor: o link pode ter sido aberto noutro browser
      if (this.porConfirmar && !this.verificado) {
        this.verificado = true
        atualizarDoServidor().catch(() => {})
      }
    },
  },
}
</script>



<style>
</style>
