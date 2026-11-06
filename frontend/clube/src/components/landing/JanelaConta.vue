<!-- JanelaConta.vue — entrar ou criar conta por cima da landing page, sem sair dela (a mesma conta da loja Bende).
     modo: 'entrar' | 'registo'. Emite 'fechar' e 'entrou' (depois de guardar a sessão). -->
<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[1000] flex items-start sm:items-center justify-center p-3 sm:p-6 overflow-y-auto"
         role="dialog" aria-modal="true" :aria-label="modo === 'entrar' ? 'Entrar' : 'Criar conta'" data-teste="janela-conta">
      <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('fechar')"></div>
      <div class="relative w-full max-w-md rounded-2xl border p-6 sm:p-8 shadow-2xl my-auto"
           :class="isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-white border-stone-200'">
        <button type="button" @click="$emit('fechar')" aria-label="Fechar" data-teste="janela-fechar"
          class="absolute right-3 top-3 w-9 h-9 rounded-lg text-lg transition-colors"
          :class="isDark ? 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-900' : 'text-zinc-400 hover:text-zinc-700 hover:bg-stone-100'">✕</button>

        <img :src="isDark ? logoLight : logoDefault" alt="Bende" class="w-16 h-16 object-contain mb-2" />
        <h2 class="text-xl font-bold mb-1" :class="isDark ? 'text-white' : 'text-zinc-900'">
          {{ modo === 'entrar' ? 'Bem-vindo de volta' : 'Criar conta' }}
        </h2>
        <p class="text-xs mb-6" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          {{ modo === 'entrar' ? 'Entra com a tua conta Bende — é a mesma da loja.' : 'Uma conta para comprar, marcar serviços e abrir a tua loja.' }}
        </p>

        <FormEntrar v-if="modo === 'entrar'" :isDark="isDark" :seguinte="seguinte" modal
                    @entrou="d => $emit('entrou', d)" @trocar="$emit('trocar', 'registo')" />
        <FormRegisto v-else :isDark="isDark" :seguinte="seguinte" modal
                     @criou="d => $emit('entrou', d)" @trocar="$emit('trocar', 'entrar')" />
      </div>
    </div>
  </Teleport>
</template>

<script>
import FormEntrar from '@/components/auth/FormEntrar.vue'
import FormRegisto from '@/components/auth/FormRegisto.vue'
import logoDefault from '@/assets/img/login/logo_final_640.webp'
import logoLight from '@/assets/img/login/logo_final_640_light.webp'

export default {
  name: 'JanelaConta',
  components: { FormEntrar, FormRegisto },
  props: {
    modo: { type: String, default: 'entrar' },
    isDark: { type: Boolean, default: false },
    seguinte: { type: String, default: '/sobre' },
  },
  emits: ['fechar', 'entrou', 'trocar'],
  data () { return { logoDefault, logoLight } },
  mounted () {
    this.tecla = e => { if (e.key === 'Escape') this.$emit('fechar') }
    window.addEventListener('keydown', this.tecla)
    document.body.style.overflow = 'hidden'
  },
  beforeUnmount () {
    window.removeEventListener('keydown', this.tecla)
    document.body.style.overflow = ''
  },
}
</script>
