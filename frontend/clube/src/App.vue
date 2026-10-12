<template>
  <router-view />
  <!-- "Entra ou cria conta" — partilhado por todas as páginas públicas (services/sessao.js) -->
  <PedirLogin />
  <!-- balão do chat (só nas páginas onde faz sentido — ver ChatFlutuante.vue) -->
  <ChatFlutuante />
</template>

<script>
import PedirLogin from '@/components/auth/PedirLogin.vue'
import ChatFlutuante from '@/components/chat/ChatFlutuante.vue'

export default {
  name: 'App',
  components: {
    PedirLogin,
    ChatFlutuante,
  }
}
</script>



<style>
</style>
