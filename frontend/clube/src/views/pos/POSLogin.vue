<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
      <!-- Logo/Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800">POS Login</h1>
        <p class="text-gray-600 mt-2">Acede ao teu sistema POS</p>
      </div>

      <!-- Formulário -->
      <form @submit.prevent="handleLogin">
        <!-- Email -->
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Email
          </label>
          <input
            v-model="form.email"
            type="email"
            placeholder="joao@exemplo.com"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>

        <!-- Password -->
        <div class="mb-6">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Password
          </label>
          <input
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>

        <!-- Mensagem de erro -->
        <div v-if="error" class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
          {{ error }}
        </div>

        <!-- Botão Submit -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition duration-200 disabled:opacity-50"
        >
          <span v-if="!loading">Entrar</span>
          <span v-else>A entrar...</span>
        </button>
      </form>

      <!-- Link para Registo -->
      <div class="mt-6 text-center">
        <p class="text-gray-600">
          Não tens conta?
          <router-link to="/pos/register" class="text-blue-600 hover:text-blue-700 font-semibold">
            Criar Conta
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'POSLogin',
  
  data() {
    return {
      form: {
        email: '',
        password: ''
      },
      loading: false,
      error: null
    }
  },
  
  methods: {
    async handleLogin() {
      this.error = null
      this.loading = true
      
      try {
        const response = await axios.post(
          `${process.env.VUE_APP_URL_BASE}/api/pos/login/`,
          {
            email: this.form.email,
            password: this.form.password
          }
        )
        
        console.log('✅ Login bem-sucedido:', response.data)
        
        // Guardar tokens
        localStorage.setItem('pos_access_token', response.data.access_token)
        localStorage.setItem('pos_refresh_token', response.data.refresh_token)
        localStorage.setItem('pos_user', JSON.stringify(response.data.user))
        
        alert(`✅ Bem-vindo, ${response.data.user.nome}!\n\nLojas: ${response.data.lojas.length}\nPOS existentes: ${response.data.pos_existentes.length}`)
        
        // TODO: Redirecionar para dashboard POS
        this.$router.push('/pos/dashboard')
        
        
      } catch (err) {
        console.error('❌ Erro no login:', err)
        
        if (err.response?.data?.detail) {
          this.error = err.response.data.detail
        } else {
          this.error = 'Erro ao fazer login. Verifica as credenciais.'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>