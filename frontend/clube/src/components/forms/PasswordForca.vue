<!-- PasswordForca.vue — barra de força + checklist de requisitos da password
     Uso: <PasswordForca :password="password" :isDark="isDark" />
     Validação: import { passwordValida } from '@/utils/password' -->
<template>
  <div v-if="password.length > 0" class="mt-2.5 space-y-2">
    <div class="flex gap-1 h-1.5">
      <div v-for="n in 5" :key="n" class="flex-1 rounded-full transition-colors duration-300"
        :class="forca >= n ? corBarra : (isDark ? 'bg-zinc-800' : 'bg-gray-200')">
      </div>
    </div>
    <p class="text-[11px] font-semibold transition-colors" :class="corTexto">
      Força da password: {{ label }}
    </p>

    <ul class="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-1.5">
      <li v-for="rule in regras" :key="rule.key"
          class="flex items-center gap-1.5 text-[11px] transition-colors"
          :class="rule.valid ? 'text-green-500' : (isDark ? 'text-zinc-600' : 'text-zinc-400')">
        <svg v-if="rule.valid" xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 010 1.42l-7.5 7.5a1 1 0 01-1.42 0l-3.5-3.5a1 1 0 111.42-1.42l2.79 2.79 6.79-6.79a1 1 0 011.42 0z" clip-rule="evenodd" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="10" cy="10" r="7" />
        </svg>
        {{ rule.label }}
      </li>
    </ul>
  </div>
</template>

<script>
import { regrasPassword } from '@/utils/password'

export default {
  name: 'PasswordForca',
  props: {
    password: { type: String, default: '' },
    isDark:   { type: Boolean, default: true },
  },
  computed: {
    regras () { return regrasPassword(this.password) },
    forca ()  { return this.regras.filter(r => r.valid).length },
    label ()  { return ['Muito fraca', 'Fraca', 'Razoável', 'Boa', 'Forte', 'Excelente'][this.forca] },
    corBarra () {
      if (this.forca <= 2) return 'bg-red-500'
      if (this.forca === 3) return 'bg-orange-400'
      if (this.forca === 4) return 'bg-yellow-400'
      return 'bg-green-500'
    },
    corTexto () {
      if (this.forca <= 2) return 'text-red-500'
      if (this.forca === 3) return 'text-orange-400'
      if (this.forca === 4) return 'text-yellow-500'
      return 'text-green-500'
    },
  },
}
</script>
