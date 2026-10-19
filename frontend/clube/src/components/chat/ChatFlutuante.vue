<template>
  <div v-if="visivel">
    <!-- Balão -->
    <button v-show="!chat.aberto || !ecraPequeno" type="button" @click="alternar"
            :aria-label="naoLidas ? `Mensagens (${naoLidas} por ler)` : 'Mensagens'"
            class="fixed bottom-5 right-5 z-[900] h-14 w-14 rounded-full shadow-2xl flex items-center justify-center text-white text-xl transition-transform hover:scale-105"
            :class="isDark ? 'bg-red-600' : 'bg-orange-500'">
      <font-awesome-icon :icon="['fas', chat.aberto ? 'xmark' : 'comment-dots']" />
      <span v-if="naoLidas && !chat.aberto"
            class="absolute -top-1 -right-1 min-w-[22px] h-[22px] px-1.5 rounded-full bg-emerald-500 text-white text-[11px] font-bold flex items-center justify-center ring-2 ring-white">
        {{ naoLidas > 99 ? '99+' : naoLidas }}
      </span>
    </button>

    <!-- Janela -->
    <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 translate-y-3"
                leave-active-class="transition duration-150" leave-to-class="opacity-0 translate-y-3">
      <div v-if="chat.aberto" role="dialog" aria-label="Mensagens"
           class="fixed z-[950] overflow-hidden shadow-2xl border"
           :class="[ecraPequeno ? 'inset-0' : 'bottom-24 right-5 w-[400px] h-[620px] max-h-[calc(100vh-7rem)] rounded-2xl',
                    isDark ? 'border-zinc-800' : 'border-gray-200']">
        <ChatPainel :isDark="isDark" compacto janela :lojaContexto="lojaContexto"
                    @expandir="expandir" @fechar="chat.aberto = false" />
      </div>
    </transition>
  </div>
</template>

<script>
import ChatPainel from './ChatPainel.vue'
import { chat, totalNaoLidas, iniciarChat, pararChat, carregarConversas } from '@/services/chat'
import { estaAutenticado, pedirLogin } from '@/services/sessao'

// onde o balão aparece (fora: login/registo, checkout, POS, página /mensagens, pré-visualização de templates)
const ROTAS = ['Home', 'Loja', 'Backoffice', 'Admin', 'CriarLoja', 'Reembolso', 'Reembolsos']

export default {
  name: 'ChatFlutuante',
  components: { ChatPainel },

  data () {
    return { chat, isDark: true, ecraPequeno: false }
  },

  computed: {
    visivel () {
      const r = this.$route
      if (!ROTAS.includes(r.name) || chat.painelEmbutido) return false
      return !(r.name === 'Loja' && (r.params.id === 'demo' || r.query.preview))
    },
    naoLidas () { return totalNaoLidas() },
    lojaContexto () {
      const r = this.$route
      return r.name === 'Loja' && /^\d+$/.test(String(r.params.id)) ? Number(r.params.id) : null
    },
  },

  watch: {
    $route () { this.sincronizarSessao() },
    'chat.aberto' (aberto) {
      if (aberto) {
        this.isDark = localStorage.getItem('theme_preference') !== 'light'
        carregarConversas().catch(() => {})
      }
    },
  },

  mounted () {
    this.medir()
    window.addEventListener('resize', this.medir)
    window.addEventListener('keydown', this.onTecla)
    this.sincronizarSessao()
  },

  beforeUnmount () {
    window.removeEventListener('resize', this.medir)
    window.removeEventListener('keydown', this.onTecla)
  },

  methods: {
    medir () { this.ecraPequeno = window.innerWidth < 640 },
    onTecla (e) { if (e.key === 'Escape' && chat.aberto) chat.aberto = false },

    // entrou → liga o chat; saiu → desliga e esquece tudo (nada de eventos da conta anterior)
    sincronizarSessao () {
      if (estaAutenticado() && !chat.pronto) {
        iniciarChat()
      } else if (!estaAutenticado() && chat.pronto) {
        pararChat()
        Object.assign(chat, { pronto: false, aberto: false, caixas: [], caixaId: null, conversas: [],
                              conversa: null, mensagens: [], produtoPendente: null, aEscrever: {} })
      }
    },

    alternar () {
      if (!estaAutenticado()) {
        pedirLogin('Entra ou cria conta para falares com as lojas.')
        return
      }
      chat.aberto = !chat.aberto
    },

    expandir () {
      chat.aberto = false
      this.$router.push('/mensagens')
    },
  },
}
</script>
