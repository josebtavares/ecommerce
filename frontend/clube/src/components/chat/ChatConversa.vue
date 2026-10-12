<template>
  <div class="flex flex-col h-full min-h-0" :class="isDark ? 'bg-zinc-950' : 'bg-gray-50'">

    <!-- Cabeçalho -->
    <div class="flex items-center gap-3 px-3 py-2.5 border-b flex-shrink-0"
         :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button v-if="compacto" type="button" aria-label="Voltar" @click="$emit('voltar')"
              class="h-8 w-8 rounded-lg flex items-center justify-center"
              :class="isDark ? 'text-zinc-300 hover:bg-zinc-800' : 'text-zinc-600 hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <ChatAvatar :nome="conversa.outro.nome" :foto="conversa.outro.foto" :tipo="conversa.outro.tipo" :tamanho="38" />
      <div class="min-w-0 flex-1">
        <p class="font-semibold text-sm truncate" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ conversa.titulo }}</p>
        <p class="text-[11px] truncate" :class="escrevendo ? 'text-emerald-500' : (isDark ? 'text-zinc-500' : 'text-zinc-400')">
          {{ escrevendo ? `${escrevendo} está a escrever…` : subtitulo }}
        </p>
      </div>
      <div class="relative">
        <button type="button" aria-label="Mais opções" @click="menu = !menu"
                class="h-8 w-8 rounded-lg flex items-center justify-center"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800' : 'text-zinc-500 hover:bg-gray-100'">
          <font-awesome-icon :icon="['fas', 'ellipsis-vertical']" />
        </button>
        <div v-if="menu" class="absolute right-0 top-9 z-20 w-56 rounded-xl border shadow-xl py-1 text-sm"
             :class="isDark ? 'bg-zinc-900 border-zinc-700 text-zinc-200' : 'bg-white border-gray-200 text-zinc-700'">
          <button v-if="podeExpandir" type="button" class="menu-item" :class="hover" @click="acao('expandir')">
            <font-awesome-icon :icon="['fas', 'up-right-and-down-left-from-center']" class="w-4" /> Abrir em ecrã inteiro
          </button>
          <button v-if="souSuporte" type="button" class="menu-item" :class="hover" @click="acao('estado')">
            <font-awesome-icon :icon="['fas', conversa.estado === 'fechada' ? 'folder-open' : 'circle-check']" class="w-4" />
            {{ conversa.estado === 'fechada' ? 'Reabrir pedido' : 'Fechar pedido' }}
          </button>
          <button v-if="podeBloquear" type="button" class="menu-item" :class="hover" @click="acao('bloquear')">
            <font-awesome-icon :icon="['fas', 'ban']" class="w-4" /> Bloquear
          </button>
          <button type="button" class="menu-item text-red-500" :class="hover" @click="acao('denunciar')">
            <font-awesome-icon :icon="['fas', 'flag']" class="w-4" /> Denunciar conversa
          </button>
        </div>
      </div>
    </div>

    <!-- Mensagens -->
    <div ref="lista" class="flex-1 min-h-0 overflow-y-auto px-3 py-3 space-y-1" @scroll="onScroll">
      <div v-if="chat.maisAntigas" class="text-center py-2">
        <button type="button" class="text-xs underline" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'"
                :disabled="chat.aCarregar" @click="carregarAntigas">
          {{ chat.aCarregar ? 'A carregar…' : 'Ver mensagens anteriores' }}
        </button>
      </div>
      <p v-if="!chat.aCarregar && !chat.mensagens.length" class="text-center text-xs py-10"
         :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
        Ainda não há mensagens. Diz olá 👋
      </p>

      <template v-for="(m, i) in chat.mensagens" :key="m.id">
        <div v-if="novoDia(i)" class="flex justify-center py-2">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-white text-zinc-500 shadow-sm'">{{ dia(m.criada_em) }}</span>
        </div>

        <div class="group flex items-end gap-1.5" :class="m.minha ? 'justify-end' : 'justify-start'">
          <div class="max-w-[78%] rounded-2xl px-3 py-2 text-sm shadow-sm"
               :class="m.minha
                 ? (isDark ? 'bg-red-700 text-white rounded-br-md' : 'bg-orange-500 text-white rounded-br-md')
                 : (isDark ? 'bg-zinc-800 text-zinc-100 rounded-bl-md' : 'bg-white text-zinc-800 rounded-bl-md')">
            <p v-if="mostrarRemetente(m)" class="text-[11px] font-semibold mb-0.5 opacity-80">{{ m.remetente.nome }}</p>

            <p v-if="m.apagada" class="italic opacity-70 text-xs">
              <font-awesome-icon :icon="['fas', 'ban']" class="mr-1" />Mensagem apagada
            </p>
            <template v-else>
              <router-link v-if="m.produto" :to="`/loja/${m.produto.loja_id}`"
                           class="flex items-center gap-2 mb-1.5 p-1.5 rounded-xl"
                           :class="m.minha ? 'bg-black/15' : (isDark ? 'bg-zinc-900' : 'bg-gray-50')">
                <img v-if="m.produto.imagem" :src="m.produto.imagem" alt="" class="h-10 w-10 rounded-lg object-cover flex-shrink-0" />
                <span class="min-w-0">
                  <span class="block text-xs font-semibold truncate">{{ m.produto.nome }}</span>
                  <span class="block text-[11px] opacity-80">{{ preco(m.produto.preco) }}</span>
                </span>
              </router-link>
              <button v-if="m.anexo" type="button" class="block mb-1 -mx-1 rounded-xl overflow-hidden" @click="lightbox = m.anexo.url">
                <img :src="m.anexo.url" alt="Imagem enviada" loading="lazy" class="max-h-64 w-auto object-cover"
                     :style="m.anexo.largura ? { aspectRatio: m.anexo.largura + '/' + m.anexo.altura } : null" />
              </button>
              <p v-if="m.texto" class="whitespace-pre-wrap break-words">{{ m.texto }}</p>
            </template>

            <p class="mt-0.5 flex items-center justify-end gap-1 text-[10px] opacity-70">
              <span v-if="m.minha && m.autor" class="mr-1">por {{ m.autor.nome }}</span>
              {{ hora(m.criada_em) }}
              <span v-if="m.minha" :class="m.lida ? 'text-sky-300' : ''" :title="m.lida ? 'Lida' : 'Enviada'">{{ m.lida ? '✓✓' : '✓' }}</span>
            </p>
          </div>
          <!-- apagar só as que escrevi (na caixa da loja, as dos colegas não); denunciar as dos outros -->
          <button v-if="!m.apagada && (!m.minha || escritaPorMim(m))" type="button"
                  class="opacity-0 group-hover:opacity-100 focus:opacity-100 text-[11px] p-1 transition-opacity"
                  :class="isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-600'"
                  :title="m.minha ? 'Apagar' : 'Denunciar'" @click="acaoMensagem(m)">
            <font-awesome-icon :icon="['fas', m.minha ? 'trash' : 'flag']" />
          </button>
        </div>
      </template>
    </div>

    <!-- Escrever -->
    <div class="flex-shrink-0 border-t px-2.5 py-2" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <p v-if="chat.erro" class="text-xs text-red-400 px-1 pb-1.5">{{ chat.erro }}</p>
      <p v-if="conversa.estado === 'fechada'" class="text-[11px] px-1 pb-1.5" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
        Este pedido de suporte está fechado — uma nova mensagem reabre-o.
      </p>

      <div v-if="chat.produtoPendente" class="flex items-center gap-2 mb-2 p-1.5 rounded-xl text-xs"
           :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-gray-100 text-zinc-600'">
        <img v-if="chat.produtoPendente.imagem" :src="chat.produtoPendente.imagem" alt="" class="h-8 w-8 rounded-lg object-cover" />
        <span class="flex-1 truncate">Sobre: <strong>{{ chat.produtoPendente.nome }}</strong></span>
        <button type="button" aria-label="Remover produto" class="px-1.5" @click="chat.produtoPendente = null">✕</button>
      </div>

      <div v-if="previa" class="relative inline-block mb-2">
        <img :src="previa" alt="Pré-visualização" class="h-20 rounded-xl object-cover" />
        <button type="button" aria-label="Remover imagem" @click="limparImagem"
                class="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-black/70 text-white text-xs">✕</button>
      </div>

      <div class="flex items-end gap-1.5">
        <div class="relative">
          <button type="button" aria-label="Emojis" @click="emojis = !emojis"
                  class="h-9 w-9 rounded-full flex items-center justify-center text-lg"
                  :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">😊</button>
          <div v-if="emojis" class="absolute bottom-11 left-0 z-30">
            <ChatEmojis :isDark="isDark" @escolher="inserirEmoji" />
          </div>
        </div>
        <button type="button" aria-label="Anexar imagem" @click="$refs.ficheiro.click()"
                class="h-9 w-9 rounded-full flex items-center justify-center"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800' : 'text-zinc-500 hover:bg-gray-100'">
          <font-awesome-icon :icon="['fas', 'image']" />
        </button>
        <input ref="ficheiro" type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="hidden" @change="escolherImagem" />

        <textarea ref="texto" v-model="texto" rows="1" maxlength="4000" placeholder="Escreve uma mensagem"
                  class="flex-1 resize-none rounded-2xl px-3.5 py-2 text-sm border focus:outline-none max-h-32"
                  :class="isDark ? 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:border-red-500'
                                 : 'bg-gray-50 border-gray-200 text-zinc-900 placeholder-zinc-400 focus:border-orange-400'"
                  @input="aoEscrever" @keydown.enter.exact.prevent="submeter" />

        <button type="button" aria-label="Enviar" :disabled="!podeEnviar" @click="submeter"
                class="h-9 w-9 rounded-full flex items-center justify-center text-white transition-opacity disabled:opacity-40"
                :class="isDark ? 'bg-red-600 hover:bg-red-500' : 'bg-orange-500 hover:bg-orange-400'">
          <font-awesome-icon :icon="['fas', chat.aEnviar ? 'spinner' : 'paper-plane']" :class="{ 'animate-spin': chat.aEnviar }" />
        </button>
      </div>
    </div>

    <!-- Imagem em ecrã inteiro -->
    <Teleport to="body">
      <div v-if="lightbox" class="fixed inset-0 z-[1100] bg-black/90 flex items-center justify-center p-4" @click="lightbox = null">
        <img :src="lightbox" alt="Imagem" class="max-h-full max-w-full rounded-lg" />
        <button type="button" aria-label="Fechar" class="absolute top-4 right-4 h-10 w-10 rounded-full bg-white/10 text-white text-xl">✕</button>
      </div>
    </Teleport>
  </div>
</template>

<script>
import ChatAvatar from './ChatAvatar.vue'
import ChatEmojis from './ChatEmojis.vue'
import {
  chat, enviar, carregarMensagens, avisarAEscrever, apagarMensagem, denunciar, bloquear, mudarEstado,
} from '@/services/chat'

const TIPOS = { cliente_loja: 'Loja · cliente', suporte: 'Suporte Bendi', equipa_grupo: 'Grupo da equipa', equipa_direta: 'Equipa' }

export default {
  name: 'ChatConversa',
  components: { ChatAvatar, ChatEmojis },
  props: {
    isDark:      { type: Boolean, default: true },
    compacto:    { type: Boolean, default: false },
    podeExpandir: { type: Boolean, default: false },
  },
  emits: ['voltar', 'expandir'],

  data () {
    return { chat, texto: '', imagem: null, previa: null, emojis: false, menu: false, lightbox: null, agora: Date.now() }
  },

  computed: {
    conversa () { return chat.conversa },
    hover () { return this.isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100' },
    souSuporte () {
      return this.conversa.tipo === 'suporte' && chat.caixas.some(c => c.caixa_id === this.conversa.caixa_id && c.tipo === 'suporte')
    },
    podeBloquear () {
      return !['suporte', 'equipa_grupo'].includes(this.conversa.tipo)
    },
    subtitulo () {
      if (this.conversa.encomenda_id) return `Encomenda #${this.conversa.encomenda_id}`
      if (this.conversa.estado === 'fechada') return 'Pedido de suporte fechado'
      return TIPOS[this.conversa.tipo] || ''
    },
    escrevendo () {
      const e = chat.aEscrever[this.conversa.id]
      return e && e.ate > this.agora ? e.nome : null
    },
    podeEnviar () {
      return !chat.aEnviar && (this.texto.trim() || this.imagem)
    },
  },

  watch: {
    'chat.mensagens.length' (novo, antigo) {
      // novas no fim → desce se já estava perto do fundo; anteriores no topo → mantém a posição
      const el = this.$refs.lista
      if (!el) return
      const perto = el.scrollHeight - el.scrollTop - el.clientHeight < 160
      if (antigo === 0 || perto) this.$nextTick(() => { el.scrollTop = el.scrollHeight })
    },
    'conversa.id' () {
      this.texto = ''
      this.limparImagem()
      this.menu = false
      this.$nextTick(() => this.$refs.texto?.focus())
    },
  },

  mounted () {
    this.relogio = setInterval(() => { this.agora = Date.now() }, 1000)
    this.$nextTick(() => this.$refs.texto?.focus())
  },

  beforeUnmount () {
    clearInterval(this.relogio)
    this.limparImagem()
  },

  methods: {
    hora (iso) {
      return new Date(iso).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })
    },
    dia (iso) {
      const d = new Date(iso)
      const hoje = new Date()
      const ontem = new Date(); ontem.setDate(hoje.getDate() - 1)
      if (d.toDateString() === hoje.toDateString()) return 'Hoje'
      if (d.toDateString() === ontem.toDateString()) return 'Ontem'
      return d.toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', year: 'numeric' })
    },
    novoDia (i) {
      if (i === 0) return true
      return new Date(chat.mensagens[i - 1].criada_em).toDateString() !== new Date(chat.mensagens[i].criada_em).toDateString()
    },
    preco (v) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v || 0))
    },
    escritaPorMim (m) {
      // na caixa pessoal a API não manda `autor` (sou sempre eu); nas partilhadas compara o autor
      if (!m.autor) return true
      try { return m.autor.utilizador_id === JSON.parse(localStorage.getItem('user') || '{}').id } catch { return false }
    },
    mostrarRemetente (m) {
      return !m.minha && this.conversa.tipo === 'equipa_grupo'
    },

    async onScroll () {
      const el = this.$refs.lista
      if (el && el.scrollTop < 40 && chat.maisAntigas && !chat.aCarregar) this.carregarAntigas()
    },
    async carregarAntigas () {
      const el = this.$refs.lista
      const antes = el.scrollHeight
      await carregarMensagens(true)
      this.$nextTick(() => { el.scrollTop = el.scrollHeight - antes })
    },

    aoEscrever (e) {
      const t = e.target
      t.style.height = 'auto'
      t.style.height = Math.min(t.scrollHeight, 128) + 'px'
      if (this.texto.trim()) avisarAEscrever()
    },
    inserirEmoji (emoji) {
      const t = this.$refs.texto
      const ini = t.selectionStart ?? this.texto.length
      const fim = t.selectionEnd ?? this.texto.length
      this.texto = this.texto.slice(0, ini) + emoji + this.texto.slice(fim)
      this.$nextTick(() => { t.focus(); t.selectionStart = t.selectionEnd = ini + emoji.length })
    },
    escolherImagem (e) {
      const f = e.target.files[0]
      e.target.value = ''
      if (!f) return
      if (f.size > 10 * 1024 * 1024) { chat.erro = 'A imagem tem mais de 10 MB.'; return }
      this.limparImagem()
      this.imagem = f
      this.previa = URL.createObjectURL(f)
    },
    limparImagem () {
      if (this.previa) URL.revokeObjectURL(this.previa)
      this.imagem = null
      this.previa = null
    },
    async submeter () {
      if (!this.podeEnviar) return
      const ok = await enviar(this.texto.trim(), this.imagem)
      if (ok) {
        this.texto = ''
        this.limparImagem()
        this.emojis = false
        if (this.$refs.texto) this.$refs.texto.style.height = 'auto'
      }
    },

    async acaoMensagem (m) {
      if (m.minha) {
        if (confirm('Apagar esta mensagem para todos?')) {
          try { await apagarMensagem(m) } catch (e) { chat.erro = e.response?.data?.detail || 'Não foi possível apagar.' }
        }
        return
      }
      const motivo = prompt('Porque queres denunciar esta mensagem?')
      if (motivo && motivo.trim()) {
        try { await denunciar(motivo.trim(), m.id); alert('Obrigado. A equipa da Bendi vai analisar.') } catch { chat.erro = 'Não foi possível denunciar.' }
      }
    },

    async acao (qual) {
      this.menu = false
      try {
        if (qual === 'expandir') this.$emit('expandir')
        if (qual === 'estado') await mudarEstado(this.conversa.estado === 'fechada' ? 'aberta' : 'fechada')
        if (qual === 'bloquear' && confirm(`Bloquear ${this.conversa.titulo}? Deixam de poder trocar mensagens.`)) {
          await bloquear(true)
          alert('Bloqueado.')
        }
        if (qual === 'denunciar') {
          const motivo = prompt('Porque queres denunciar esta conversa?')
          if (motivo && motivo.trim()) { await denunciar(motivo.trim()); alert('Obrigado. A equipa da Bendi vai analisar.') }
        }
      } catch (e) {
        chat.erro = e.response?.data?.detail || 'Não foi possível concluir a acção.'
      }
    },
  },
}
</script>

<style scoped>
.menu-item { display: flex; align-items: center; gap: .6rem; width: 100%; padding: .5rem .85rem; text-align: left; }
</style>
