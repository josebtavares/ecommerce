<template>
  <!-- Mensagens da loja: Clientes (caixa da loja — quem atende o chat) · Equipa (todos os membros) -->
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <button v-if="caixaLoja" type="button" @click="mudar('clientes')"
              :class="['px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2',
                       modo === 'clientes' ? 'bg-red-600 text-white' : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        <font-awesome-icon :icon="['fas', 'store']" /> Clientes
        <span v-if="caixaLoja.restrita" class="text-[11px] opacity-80">(as tuas entregas)</span>
        <span v-if="caixaLoja.nao_lidas" class="min-w-[20px] h-5 px-1.5 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center">
          {{ caixaLoja.nao_lidas }}
        </span>
      </button>
      <button type="button" @click="mudar('equipa')"
              :class="['px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2',
                       modo === 'equipa' ? 'bg-red-600 text-white' : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        <font-awesome-icon :icon="['fas', 'users']" /> Equipa
      </button>
      <p class="text-xs text-zinc-500 ml-auto">
        {{ modo === 'clientes'
          ? 'Os clientes falam com a loja — a equipa vê quem respondeu.'
          : 'Grupo da equipa e conversas entre colegas. Os clientes não vêem isto.' }}
      </p>
    </div>

    <p v-if="!caixaLoja && pronto" class="text-xs text-zinc-500 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3">
      Não atendes o chat dos clientes desta loja. Se precisares, pede ao dono para te dar acesso na secção Staff.
    </p>

    <div class="h-[calc(100vh-230px)] min-h-[480px] rounded-2xl border border-zinc-800 overflow-hidden">
      <ChatPainel v-if="pronto" :key="modo" :isDark="true" :compacto="ecraPequeno" semCaixas :semFiltros="modo === 'equipa'" />
      <div v-else class="h-full flex items-center justify-center text-sm text-zinc-500">A carregar…</div>
    </div>
  </div>
</template>

<script>
import ChatPainel from '@/components/chat/ChatPainel.vue'
import api from '@/services/api'
import { chat, iniciarChat, carregarCaixas, escolherCaixa, carregarConversas, fecharConversa } from '@/services/chat'

export default {
  name: 'BackofficeMensagens',
  components: { ChatPainel },
  props: {
    lojaId: { type: [String, Number], required: true },
  },

  data () {
    return { chat, modo: 'clientes', pronto: false, ecraPequeno: false }
  },

  computed: {
    caixaLoja () {
      return chat.caixas.find(c => c.tipo === 'loja' && String(c.loja_id) === String(this.lojaId)) || null
    },
    caixaPessoal () {
      return chat.caixas.find(c => c.tipo === 'pessoal') || null
    },
  },

  async mounted () {
    chat.painelEmbutido = true
    this.medir()
    window.addEventListener('resize', this.medir)
    if (!chat.pronto) await iniciarChat()
    else await carregarCaixas()
    // garante o grupo da equipa desta loja
    if (this.caixaPessoal) {
      await api.post('/api/chat/conversas/', { caixa: this.caixaPessoal.caixa_id, destino: 'equipa_grupo', loja_id: this.lojaId })
        .catch(() => {})
    }
    await this.mudar(this.caixaLoja ? 'clientes' : 'equipa')
  },

  beforeUnmount () {
    window.removeEventListener('resize', this.medir)
    // devolve o chat ao estado normal (o balão volta a mostrar tudo)
    chat.painelEmbutido = false
    chat.filtroLoja = null
    chat.filtroTipo = ''
    fecharConversa()
    if (this.caixaPessoal) chat.caixaId = this.caixaPessoal.caixa_id
  },

  methods: {
    medir () { this.ecraPequeno = window.innerWidth < 900 },

    async mudar (modo) {
      this.pronto = false
      this.modo = modo
      fecharConversa()
      if (modo === 'clientes' && this.caixaLoja) {
        chat.filtroLoja = null
        await escolherCaixa(this.caixaLoja.caixa_id)
      } else if (this.caixaPessoal) {
        this.modo = 'equipa'
        await escolherCaixa(this.caixaPessoal.caixa_id)
        chat.filtroTipo = 'equipa'
        chat.filtroLoja = this.lojaId
        await carregarConversas()
      }
      this.pronto = true
    },
  },
}
</script>
