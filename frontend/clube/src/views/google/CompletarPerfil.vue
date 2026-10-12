<template>
  <div class="min-h-screen w-full flex items-center justify-center px-4 py-8 transition-colors"
       :style="{ background: isDark ? '#0a0a0a' : '#f9fafb' }">

    <div class="w-full max-w-lg rounded-2xl border p-6 sm:p-8 shadow-2xl transition-all"
         :class="isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-white border-gray-200'">

      <div class="flex items-center gap-4 mb-6">
        <img v-if="foto" :src="foto" alt="Foto"
             class="w-14 h-14 rounded-full object-cover border"
             :class="isDark ? 'border-zinc-700' : 'border-gray-200'" />
        <div>
          <h2 class="text-xl font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">
            Completa o teu perfil
          </h2>
          <p class="text-xs mt-0.5" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
            A conta foi criada com o Google. Confirma os teus dados e acrescenta o que falta.
          </p>
        </div>
      </div>

      <div v-if="carregando" class="py-10 flex justify-center">
        <svg class="animate-spin h-6 w-6" :class="isDark ? 'text-red-500' : 'text-orange-500'" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
          <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
        </svg>
      </div>

      <form v-else @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label :class="labelClass">Primeiro nome *</label>
            <input v-model.trim="form.first_name" required autocomplete="given-name"
                   :class="inputClass" placeholder="Ana" />
            <p v-if="erros.first_name" class="mt-1 text-xs text-red-400">{{ erros.first_name }}</p>
          </div>
          <div>
            <label :class="labelClass">Último nome</label>
            <input v-model.trim="form.last_name" autocomplete="family-name"
                   :class="inputClass" placeholder="Silva" />
            <p v-if="erros.last_name" class="mt-1 text-xs text-red-400">{{ erros.last_name }}</p>
          </div>
        </div>

        <div>
          <label :class="labelClass">Username *</label>
          <input v-model.trim="form.username" required autocomplete="username"
                 @input="erros.username = ''; verUsername.verificar(form.username, usernameInicial)"
                 :class="inputClass" placeholder="o_teu_username" />
          <p v-if="erros.username" class="mt-1 text-xs text-red-400">{{ erros.username }}</p>
          <EstadoDisponibilidade v-else-if="verUsername.estado" :verificador="verUsername" :isDark="isDark"
                                 @usar="u => { form.username = u; verUsername.verificar(u, usernameInicial) }" />
          <p v-else class="mt-1 text-xs" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
            Gerado a partir do email — podes mudá-lo.
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label :class="labelClass">Telefone</label>
            <input v-model.trim="form.telefone" type="tel" autocomplete="tel"
                   :class="inputClass" placeholder="O teu número" />
            <p v-if="erros.telefone" class="mt-1 text-xs text-red-400">{{ erros.telefone }}</p>
          </div>
          <div>
            <label :class="labelClass">Morada</label>
            <input v-model.trim="form.morada" autocomplete="street-address"
                   :class="inputClass" placeholder="Rua, cidade" />
            <p v-if="erros.morada" class="mt-1 text-xs text-red-400">{{ erros.morada }}</p>
          </div>
        </div>
        <p class="text-xs -mt-2" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
          O telefone e a morada são usados nos pagamentos e nas entregas das tuas encomendas.
        </p>

        <div v-if="erroGeral"
             class="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
          {{ erroGeral }}
        </div>

        <div class="flex flex-col-reverse sm:flex-row gap-3 pt-2">
          <button type="button" @click="continuar"
                  class="sm:flex-1 py-2.5 rounded-xl text-sm font-semibold border transition-all"
                  :class="isDark
                    ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500'
                    : 'border-gray-300 text-zinc-600 hover:border-gray-400'">
            Fazer depois
          </button>
          <button type="submit" :disabled="aGuardar"
                  class="sm:flex-1 py-2.5 rounded-xl text-sm font-bold text-white transition-all flex items-center justify-center gap-2"
                  :class="aGuardar ? 'opacity-60 cursor-not-allowed' : 'hover:opacity-90 active:scale-[0.98]'"
                  :style="isDark
                    ? 'background: linear-gradient(135deg, #dc2626, #b91c1c);'
                    : 'background: linear-gradient(135deg, #f97316, #ea580c);'">
            {{ aGuardar ? 'A guardar...' : 'Guardar e continuar' }}
          </button>
        </div>

        <p class="text-xs text-center pt-1" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
          Entras sempre com o Google. Se quiseres entrar também com email e password,
          podes definir uma password no teu perfil.
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'
import EstadoDisponibilidade from '@/components/forms/EstadoDisponibilidade.vue'
import { criarVerificador } from '@/services/disponibilidade'

export default {
  name: 'CompletarPerfil',
  components: { EstadoDisponibilidade },

  data () {
    const savedTheme = localStorage.getItem('theme_preference')
    return {
      isDark: savedTheme ? savedTheme === 'dark' : true,
      carregando: true,
      aGuardar: false,
      foto: null,
      form: { first_name: '', last_name: '', username: '', telefone: '', morada: '' },
      erros: {},
      erroGeral: '',
      verUsername: criarVerificador('username'),
      usernameInicial: '',
    }
  },

  computed: {
    labelClass () {
      return ['text-xs font-medium mb-1.5 block', this.isDark ? 'text-zinc-400' : 'text-zinc-500']
    },
    inputClass () {
      return [
        'w-full px-4 py-2.5 rounded-xl text-sm border transition-all focus:outline-none placeholder-zinc-400',
        this.isDark
          ? 'bg-zinc-900 border-zinc-800 text-zinc-100 focus:border-red-500'
          : 'bg-gray-50 border-gray-200 text-zinc-900 focus:border-orange-400',
      ]
    },
    // só caminhos internos — nunca redirecionar para fora do site
    seguinte () {
      const s = this.$route.query.seguinte
      return typeof s === 'string' && s.startsWith('/') && !s.startsWith('//') ? s : '/Home'
    },
  },

  async created () {
    try {
      const { data } = await api.get('/app/utilizador/me/')
      this.foto = data.foto
      for (const k of Object.keys(this.form)) this.form[k] = data[k] || ''
      this.usernameInicial = this.form.username
    } catch (e) {
      // sem perfil não há nada a completar
      this.continuar()
      return
    }
    this.carregando = false
  },

  methods: {
    async guardar () {
      this.erros = {}
      this.erroGeral = ''
      if (!this.form.first_name) { this.erros.first_name = 'O primeiro nome é obrigatório.'; return }
      if (!this.form.username)   { this.erros.username   = 'O username é obrigatório.'; return }
      if (this.verUsername.bloqueia) { this.erros.username = this.verUsername.motivo; return }

      this.aGuardar = true
      try {
        const fd = new FormData()
        for (const [k, v] of Object.entries(this.form)) fd.append(k, v)
        const { data } = await api.patch('/app/utilizador/me/editar/', fd)

        // actualiza só a sessão onde se está — a Bendi e o POS podem ter contas diferentes
        if (this.$route.path.startsWith('/pos')) {
          localStorage.setItem('pos_user', JSON.stringify({ ...data, nome: [data.first_name, data.last_name].filter(Boolean).join(' ') || data.username }))
        } else {
          localStorage.setItem('user', JSON.stringify(data))
        }

        toast.success('Perfil actualizado!', { autoClose: 2000 })
        this.continuar()
      } catch (e) {
        const d = e.response?.data
        if (d && typeof d === 'object' && !d.detail) {
          for (const [k, v] of Object.entries(d)) this.erros[k.replace(/^new_/, '')] = Array.isArray(v) ? v[0] : String(v)
        } else {
          this.erroGeral = d?.detail || 'Não foi possível guardar. Tenta outra vez.'
        }
      } finally {
        this.aGuardar = false
      }
    },

    continuar () {
      this.$router.replace(this.seguinte)
    },
  },
}
</script>
