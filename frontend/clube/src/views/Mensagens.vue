<template>
  <!-- /mensagens — o chat em ecrã inteiro (o mesmo painel da janela flutuante) -->
  <div class="h-screen flex flex-col" :class="isDark ? 'bg-zinc-950' : 'bg-gray-100'">
    <header class="flex items-center gap-3 px-4 h-14 border-b flex-shrink-0"
            :class="isDark ? 'bg-zinc-900 border-zinc-800 text-white' : 'bg-white border-gray-200 text-zinc-900'">
      <button type="button" aria-label="Voltar" @click="voltar"
              class="h-9 w-9 rounded-lg flex items-center justify-center"
              :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold">Mensagens</h1>
      <button type="button" class="ml-auto h-9 w-9 rounded-lg flex items-center justify-center"
              :aria-label="isDark ? 'Modo claro' : 'Modo escuro'" @click="alternarTema"
              :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', isDark ? 'sun' : 'moon']" />
      </button>
    </header>
    <div class="flex-1 min-h-0 mx-auto w-full max-w-6xl md:my-4 md:rounded-2xl md:border overflow-hidden"
         :class="isDark ? 'md:border-zinc-800' : 'md:border-gray-200'">
      <ChatPainel v-if="chat.pronto" :isDark="isDark" :compacto="ecraPequeno" />
    </div>
  </div>
</template>

<script>
import ChatPainel from '@/components/chat/ChatPainel.vue'
import { chat, iniciarChat } from '@/services/chat'
import { temaEscuro, guardarTema } from '@/utils/tema'

export default {
  name: 'MensagensPagina',
  components: { ChatPainel },

  data () {
    return { chat, isDark: temaEscuro(), ecraPequeno: false }
  },

  async mounted () {
    this.medir()
    window.addEventListener('resize', this.medir)
    if (!chat.pronto) await iniciarChat()
  },

  beforeUnmount () {
    window.removeEventListener('resize', this.medir)
  },

  methods: {
    medir () { this.ecraPequeno = window.innerWidth < 768 },
    voltar () {
      if (window.history.length > 1) this.$router.back()
      else this.$router.push('/Home')
    },
    alternarTema () {
      this.isDark = !this.isDark
      guardarTema(this.isDark)
    },
  },
}
</script>
