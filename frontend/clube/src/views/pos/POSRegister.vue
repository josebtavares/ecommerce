<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
      <!-- Logo/Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800">Criar Conta POS</h1>
        <p class="text-gray-600 mt-2">Sistema Point of Sale</p>
      </div>

      <!-- Formulário -->
      <form @submit.prevent="handleRegister">
        <!-- Primeiro Nome -->
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Primeiro Nome *
          </label>
          <input
            v-model="form.firstName"
            type="text"
            placeholder="João"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>

        <!-- Último Nome -->
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Último Nome *
          </label>
          <input
            v-model="form.lastName"
            type="text"
            placeholder="Silva"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>

        <!-- Email -->
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Email *
          </label>
          <input
            v-model="form.email"
            type="email"
            placeholder="joao.silva@exemplo.com"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>

        <!-- Password -->
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Password *
          </label>
          <input
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            required
            minlength="6"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
          <p class="text-xs text-gray-500 mt-1">Mínimo 6 caracteres</p>
        </div>

        <!-- Confirmar Password -->
        <div class="mb-6">
          <label class="block text-gray-700 text-sm font-semibold mb-2">
            Confirmar Password *
          </label>
          <input
            v-model="form.passwordConfirm"
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
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="!loading">Criar Conta</span>
          <span v-else class="flex items-center justify-center">
            <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            A criar conta...
          </span>
        </button>
      </form>

      <!-- Link para Login -->
      <div class="mt-6 text-center">
        <p class="text-gray-600">
          Já tens conta?
          <router-link to="/pos/login" class="text-blue-600 hover:text-blue-700 font-semibold">
            Fazer Login
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'POSRegister',
  
  data() {
    return {
      form: {
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        passwordConfirm: ''
      },
      loading: false,
      error: null
    }
  },
  
  methods: {
    async handleRegister() {
      this.error = null
      
      // Validações
      if (!this.form.firstName || !this.form.lastName || !this.form.email || !this.form.password) {
        this.error = 'Todos os campos são obrigatórios'
        return
      }
      
      if (this.form.password.length < 6) {
        this.error = 'Password deve ter no mínimo 6 caracteres'
        return
      }
      
      if (this.form.password !== this.form.passwordConfirm) {
        this.error = 'As passwords não coincidem'
        return
      }
      
      this.loading = true
      
      try {
        const response = await axios.post(
          `${process.env.VUE_APP_URL_BASE}/api/pos/register/`,
          {
            first_name: this.form.firstName.trim(),
            last_name: this.form.lastName.trim(),
            email: this.form.email.trim(),
            password: this.form.password
          }
        )
        
        console.log('✅ Registo bem-sucedido:', response.data)
        
        // Guardar tokens
        localStorage.setItem('pos_access_token', response.data.access_token)
        localStorage.setItem('pos_refresh_token', response.data.refresh_token)
        localStorage.setItem('pos_user', JSON.stringify(response.data.user))
        
        // Mostrar sucesso
        alert(`✅ Conta criada com sucesso!\n\nBem-vindo(a), ${this.form.firstName} ${this.form.lastName}!`)
        
        // Redirecionar para login ou dashboard
        this.$router.push('/pos/login')
        
      } catch (err) {
        console.error('❌ Erro no registo:', err)
        
        if (err.response?.data?.detail) {
          this.error = err.response.data.detail
        } else if (err.response?.status === 400) {
          this.error = 'Email já registado ou dados inválidos'
        } else {
          this.error = 'Erro ao criar conta. Tenta novamente.'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
input:focus {
  transform: scale(1.01);
}

button:active {
  transform: scale(0.98);
}
</style>