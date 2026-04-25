<template>
  <div class="min-h-screen flex items-center justify-center"
       :style="{ background: isDark ? '#0a0a0a' : '#f9fafb' }">
    <div class="text-center">
      <svg class="animate-spin h-10 w-10 mx-auto mb-4"
           :class="isDark ? 'text-red-500' : 'text-orange-500'"
           viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
        <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
      </svg>
      <p class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
        {{ mensagem }}
      </p>
    </div>
  </div>
</template>

<script>
import api from '@/services/api.js'
import { toast } from 'vue3-toastify'

export default {
  name: 'GoogleCallback',

  data () {
    const savedTheme = localStorage.getItem('theme_preference')
    return {
      isDark: savedTheme ? savedTheme === 'dark' : true,
      mensagem: 'A autenticar com Google...',
    }
  },

  async created () {
    // Ler o código da URL (?code=...)
    const code = new URLSearchParams(window.location.search).get('code')

    if (!code) {
      this.mensagem = 'Erro: código não encontrado.'
      setTimeout(() => this.$router.push('/Login'), 2000)
      return
    }

    try {
      this.mensagem = 'A criar sessão...'
      const { data } = await api.post('/app/utilizador/google/callback/', { code })

      // Guardar tokens e dados do utilizador (igual ao login normal)
      localStorage.setItem('access_token',  data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user',          JSON.stringify(data.user))

      toast.success(
        data.criado ? 'Conta criada com Google!' : 'Login com Google bem-sucedido!',
        { autoClose: 2000 }
      )

      this.$router.push({ name: 'Home' })

    } catch (e) {
      const msg = e.response?.data?.detail || 'Erro ao autenticar com Google.'
      toast.error(msg, { autoClose: 3000 })
      this.$router.push('/Login')
    }
  }
}
</script>