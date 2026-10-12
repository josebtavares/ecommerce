<template>
  <!-- Superchat: a caixa "Suporte Bendi" — fala com qualquer loja ou utilizador (atender_suporte) -->
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <button v-for="f in filtros" :key="f.valor" type="button" @click="filtrar(f.valor)"
              :class="['px-4 py-2 rounded-xl text-sm font-semibold transition',
                       chat.filtroEstado === f.valor ? 'bg-red-600 text-white' : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ f.nome }}
      </button>
      <p class="text-xs text-zinc-500 ml-auto">
        Para falar com alguém novo, usa <font-awesome-icon :icon="['fas', 'pen-to-square']" /> e filtra por lojas, donos, staff, clientes ou admin.
      </p>
    </div>

    <p v-if="semAcesso" class="text-sm text-zinc-500 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3">
      O teu papel não atende o suporte.
    </p>
    <div v-else class="h-[calc(100vh-230px)] min-h-[480px] rounded-2xl border border-zinc-800 overflow-hidden">
      <ChatPainel v-if="pronto" :isDark="true" :compacto="ecraPequeno" semCaixas semFiltros />
      <div v-else class="h-full flex items-center justify-center text-sm text-zinc-500">A carregar…</div>
    </div>
  </div>
</template>

<script>
import ChatPainel from '@/components/chat/ChatPainel.vue'
import { chat, iniciarChat, carregarCaixas, escolherCaixa, carregarConversas, fecharConversa } from '@/services/chat'

export default {
  name: 'AdminSuporte',
  components: { ChatPainel },

  data () {
    return {
      chat, pronto: false, semAcesso: false, ecraPequeno: false,
      filtros: [{ valor: 'aberta', nome: 'Pedidos abertos' }, { valor: 'fechada', nome: 'Fechados' }, { valor: '', nome: 'Todos' }],
    }
  },

  async mounted () {
    chat.painelEmbutido = true
    this.medir()
    window.addEventListener('resize', this.medir)
    if (!chat.pronto) await iniciarChat()
    else await carregarCaixas()
    const suporte = chat.caixas.find(c => c.tipo === 'suporte')
    if (!suporte) { this.semAcesso = true; return }
    await escolherCaixa(suporte.caixa_id)
    chat.filtroEstado = 'aberta'
    await carregarConversas()
    this.pronto = true
  },

  beforeUnmount () {
    window.removeEventListener('resize', this.medir)
    chat.painelEmbutido = false
    chat.filtroEstado = ''
    fecharConversa()
    const pessoal = chat.caixas.find(c => c.tipo === 'pessoal')
    if (pessoal) chat.caixaId = pessoal.caixa_id
  },

  methods: {
    medir () { this.ecraPequeno = window.innerWidth < 900 },
    async filtrar (valor) {
      chat.filtroEstado = valor
      fecharConversa()
      await carregarConversas()
    },
  },
}
</script>
