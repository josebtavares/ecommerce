<template>
  <!-- lista + conversa; compacto (janela flutuante / telemóvel) mostra uma de cada vez -->
  <div class="flex h-full min-h-0 w-full overflow-hidden" :class="isDark ? 'bg-zinc-950' : 'bg-gray-50'">
    <div v-show="!compacto || !chat.conversa" class="h-full min-h-0 border-r flex-shrink-0"
         :class="[compacto ? 'w-full' : 'w-[340px]', isDark ? 'border-zinc-800' : 'border-gray-200']">
      <ChatLista :isDark="isDark" :podeExpandir="janela" :podeFechar="janela" :lojaContexto="lojaContexto"
                 @abrir="abrir" @expandir="$emit('expandir')" @fechar="$emit('fechar')"
                 @suporte="suporte" @falar-loja="falarLoja" />
    </div>

    <div v-show="!compacto || chat.conversa" class="flex-1 min-w-0 h-full min-h-0">
      <ChatConversa v-if="chat.conversa" :key="chat.conversa.id" :isDark="isDark" :compacto="compacto"
                    :podeExpandir="janela" @voltar="voltar" @expandir="$emit('expandir')" />
      <div v-else class="h-full flex flex-col items-center justify-center gap-2 px-6 text-center">
        <font-awesome-icon :icon="['fas', 'comments']" class="text-4xl" :class="isDark ? 'text-zinc-700' : 'text-gray-300'" />
        <p class="text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Escolhe uma conversa ou começa uma nova.</p>
      </div>
    </div>
  </div>
</template>

<script>
import ChatLista from './ChatLista.vue'
import ChatConversa from './ChatConversa.vue'
import { chat, abrirConversa, fecharConversa, contactarSuporte, contactarLoja, carregarConversas } from '@/services/chat'

export default {
  name: 'ChatPainel',
  components: { ChatLista, ChatConversa },
  props: {
    isDark:       { type: Boolean, default: true },
    compacto:     { type: Boolean, default: false },
    janela:       { type: Boolean, default: false },   // dentro da janela flutuante (mostra ⤢ e ✕)
    lojaContexto: { type: [String, Number], default: null },
  },
  emits: ['expandir', 'fechar'],

  data () {
    return { chat }
  },

  mounted () {
    carregarConversas().catch(() => {})
  },

  methods: {
    abrir (c) {
      if (!c) return
      if (chat.conversa?.id !== c.id) abrirConversa(c)
    },
    voltar () {
      fecharConversa()
      carregarConversas().catch(() => {})
    },
    suporte () { contactarSuporte() },
    falarLoja () { contactarLoja(this.lojaContexto) },
  },
}
</script>
