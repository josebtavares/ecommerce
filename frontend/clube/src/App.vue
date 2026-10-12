<template>
  <router-view />
  <!-- "Entra ou cria conta" — partilhado por todas as páginas públicas (services/sessao.js) -->
  <PedirLogin />
</template>

<script>
import PedirLogin from '@/components/auth/PedirLogin.vue'

export default {
  name: 'App',
  components: {
    PedirLogin,
  }
}
</script>



<style>
</style>
