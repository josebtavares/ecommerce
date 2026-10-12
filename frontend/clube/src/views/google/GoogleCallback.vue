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
import { validarStateGoogle, seguinteGoogle } from '@/services/google'
import { caminhoSeguro } from '@/services/sessao'
import { guardarSessaoPrincipalPOS, destinoPOS } from '@/services/posSessao'

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
    // Ler o código e o state da URL (?code=...&state=...)
    const params  = new URLSearchParams(window.location.search)
    const code    = params.get('code')
    const destino = validarStateGoogle(params.get('state'))
    const voltar  = destino === 'pos' ? '/pos/login' : '/Login'

    // cancelou no Google, ou o pedido não começou neste separador
    if (!code || !destino) {
      this.mensagem = params.get('error') === 'access_denied'
        ? 'Login com Google cancelado.'
        : 'Pedido de login inválido ou expirado. Tenta outra vez.'
      setTimeout(() => this.$router.push(voltar), 2000)
      return
    }

    try {
      this.mensagem = 'A criar sessão...'

      let data, seguinte
      if (destino === 'pos') {
        ({ data } = await api.post('/api/pos/login/google/', { code }))
        guardarSessaoPrincipalPOS(data)
        seguinte = destinoPOS(data)
      } else {
        ({ data } = await api.post('/app/utilizador/google/callback/', { code }))
        // Guardar tokens e dados do utilizador (igual ao login normal)
        localStorage.setItem('access_token',  data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        localStorage.setItem('user',          JSON.stringify(data.user))
        // volta à página de onde veio (ex.: a loja), se for um caminho interno
        seguinte = caminhoSeguro(seguinteGoogle())
      }

      toast.success(
        data.criado ? 'Conta criada com Google!' : 'Login com Google bem-sucedido!',
        { autoClose: 2000 }
      )

      // conta nova: o Google não dá telefone nem morada → pedir já, com "Fazer depois"
      if (data.criado) {
        // a página fica do lado da sessão certa (/pos/... usa o token do POS)
        const rota = destino === 'pos' ? 'POSCompletarPerfil' : 'CompletarPerfil'
        this.$router.replace({ name: rota, query: { seguinte } })
      } else {
        this.$router.replace(seguinte)
      }

    } catch (e) {
      const msg = e.response?.data?.detail || 'Erro ao autenticar com Google.'
      toast.error(msg, { autoClose: 3000 })
      this.$router.push(voltar)
    }
  }
}
</script>
