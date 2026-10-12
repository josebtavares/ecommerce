<template>
  <div class="flex flex-col h-full min-h-0" :class="isDark ? 'bg-zinc-900' : 'bg-white'">

    <!-- Cabeçalho -->
    <div class="px-3 pt-3 pb-2 flex-shrink-0">
      <div class="flex items-center gap-2">
        <h2 class="flex-1 text-base font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">Mensagens</h2>
        <button type="button" :aria-label="aNovar ? 'Fechar' : 'Nova conversa'" :title="aNovar ? 'Fechar' : 'Nova conversa'"
                class="h-8 w-8 rounded-lg flex items-center justify-center" :class="botao" @click="alternarNova">
          <font-awesome-icon :icon="['fas', aNovar ? 'xmark' : 'pen-to-square']" />
        </button>
        <button v-if="podeExpandir" type="button" aria-label="Abrir em ecrã inteiro" title="Abrir em ecrã inteiro"
                class="h-8 w-8 rounded-lg flex items-center justify-center" :class="botao" @click="$emit('expandir')">
          <font-awesome-icon :icon="['fas', 'up-right-and-down-left-from-center']" />
        </button>
        <button v-if="podeFechar" type="button" aria-label="Fechar" class="h-8 w-8 rounded-lg flex items-center justify-center"
                :class="botao" @click="$emit('fechar')">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
      </div>

      <!-- Caixas: Pessoal · Loja X · Suporte -->
      <div v-if="chat.caixas.length > 1" class="mt-2 flex gap-1.5 overflow-x-auto pb-1">
        <button v-for="c in chat.caixas" :key="c.caixa_id" type="button" @click="escolher(c.caixa_id)"
                class="flex-shrink-0 flex items-center gap-1.5 pl-1 pr-2.5 py-1 rounded-full text-xs font-semibold border transition-colors"
                :class="c.caixa_id === chat.caixaId
                  ? (isDark ? 'bg-red-600 border-red-600 text-white' : 'bg-orange-500 border-orange-500 text-white')
                  : (isDark ? 'border-zinc-700 text-zinc-300 hover:border-zinc-500' : 'border-gray-200 text-zinc-600 hover:border-gray-400')">
          <ChatAvatar :nome="c.nome" :foto="c.foto" :tipo="c.tipo" :tamanho="20" />
          {{ c.tipo === 'pessoal' ? 'Pessoal' : c.nome }}
          <span v-if="c.restrita" class="opacity-70">(entregas)</span>
          <span v-if="c.nao_lidas" class="ml-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-white/90 text-red-600 text-[10px] flex items-center justify-center">
            {{ c.nao_lidas }}
          </span>
        </button>
      </div>

      <!-- Atalho na página de uma loja -->
      <button v-if="lojaContexto && caixa && caixa.tipo === 'pessoal' && !aNovar" type="button" @click="$emit('falar-loja')"
              class="mt-2 w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold text-white"
              :class="isDark ? 'bg-red-600 hover:bg-red-500' : 'bg-orange-500 hover:bg-orange-400'">
        <font-awesome-icon :icon="['fas', 'store']" /> Enviar mensagem a esta loja
      </button>

      <!-- Pesquisa -->
      <div class="mt-2 relative">
        <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="absolute left-3 top-1/2 -translate-y-1/2 text-xs"
                           :class="isDark ? 'text-zinc-500' : 'text-zinc-400'" />
        <input v-model="termo" type="search" :placeholder="aNovar ? textoPesquisaContactos : 'Pesquisar conversas'"
               class="w-full pl-8 pr-3 py-2 rounded-xl text-sm border focus:outline-none"
               :class="isDark ? 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:border-red-500'
                              : 'bg-gray-50 border-gray-200 text-zinc-900 placeholder-zinc-400 focus:border-orange-400'"
               @input="aoPesquisar" />
      </div>

      <!-- Filtros -->
      <div v-if="filtros.length" class="mt-2 flex gap-1.5 overflow-x-auto pb-1">
        <button v-for="f in filtros" :key="f.valor" type="button" @click="filtrar(f.valor)"
                class="flex-shrink-0 px-2.5 py-1 rounded-full text-[11px] font-semibold transition-colors"
                :class="filtroActivo === f.valor
                  ? (isDark ? 'bg-zinc-100 text-zinc-900' : 'bg-zinc-900 text-white')
                  : (isDark ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200' : 'bg-gray-100 text-zinc-500 hover:text-zinc-700')">
          {{ f.nome }}
        </button>
      </div>
    </div>

    <!-- Nova conversa: contactos -->
    <div v-if="aNovar" class="flex-1 min-h-0 overflow-y-auto">
      <p v-if="termo.trim().length < 2" class="px-4 py-6 text-center text-xs" :class="vazio">{{ dicaNova }}</p>
      <p v-else-if="aPesquisar" class="px-4 py-6 text-center text-xs" :class="vazio">A pesquisar…</p>
      <p v-else-if="!contactos.length" class="px-4 py-6 text-center text-xs" :class="vazio">Ninguém encontrado.</p>
      <button v-for="c in contactos" :key="c.tipo + c.id" type="button" @click="comecar(c)"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors" :class="linha">
        <ChatAvatar :nome="c.nome" :foto="c.foto" :tamanho="40" />
        <span class="min-w-0 flex-1">
          <span class="block text-sm font-semibold truncate" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ c.nome }}</span>
          <span class="block text-[11px] truncate" :class="vazio">
            {{ c.tipo === 'loja' ? 'Loja' : rotuloPapel(c.papel) }}{{ c.username ? ' · @' + c.username : '' }}
          </span>
        </span>
      </button>
      <p v-if="erroNova" class="px-4 py-2 text-xs text-red-400">{{ erroNova }}</p>
      <div v-if="caixa && caixa.tipo === 'pessoal'" class="px-3 py-3">
        <button type="button" class="w-full py-2 rounded-xl text-sm font-semibold border" :class="botaoContorno" @click="$emit('suporte')">
          <font-awesome-icon :icon="['fas', 'headset']" class="mr-1.5" /> Falar com o Suporte Bendi
        </button>
      </div>
    </div>

    <!-- Conversas -->
    <div v-else class="flex-1 min-h-0 overflow-y-auto">
      <div v-if="!chat.conversas.length" class="px-4 py-10 text-center">
        <p class="text-sm" :class="vazio">Ainda não tens conversas.</p>
        <button v-if="caixa && caixa.tipo === 'pessoal'" type="button" class="mt-3 px-4 py-2 rounded-xl text-sm font-semibold border"
                :class="botaoContorno" @click="$emit('suporte')">
          <font-awesome-icon :icon="['fas', 'headset']" class="mr-1.5" /> Falar com o Suporte Bendi
        </button>
      </div>
      <button v-for="c in chat.conversas" :key="c.id" type="button" @click="$emit('abrir', c)"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors"
              :class="[linha, chat.conversa && chat.conversa.id === c.id ? (isDark ? 'bg-zinc-800' : 'bg-orange-50') : '']">
        <ChatAvatar :nome="c.outro.nome" :foto="c.outro.foto" :tipo="c.outro.tipo" :tamanho="44" />
        <span class="min-w-0 flex-1">
          <span class="flex items-center gap-2">
            <span class="flex-1 text-sm font-semibold truncate" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ c.titulo }}</span>
            <span class="text-[10px] flex-shrink-0" :class="c.nao_lidas ? 'text-emerald-500 font-semibold' : vazio">{{ quando(c.ultima_mensagem_em) }}</span>
          </span>
          <span class="flex items-center gap-2">
            <span class="flex-1 text-xs truncate" :class="c.nao_lidas ? (isDark ? 'text-zinc-200' : 'text-zinc-800') : vazio">
              <template v-if="aEscrever(c)"><span class="text-emerald-500">a escrever…</span></template>
              <template v-else>
                <span v-if="c.encomenda_id" class="mr-1 font-semibold">#{{ c.encomenda_id }}</span>{{ resumo(c) }}
              </template>
            </span>
            <span v-if="c.nao_lidas" class="flex-shrink-0 min-w-[20px] h-5 px-1.5 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center">
              {{ c.nao_lidas }}
            </span>
          </span>
        </span>
      </button>
    </div>
  </div>
</template>

<script>
import ChatAvatar from './ChatAvatar.vue'
import { chat, carregarConversas, escolherCaixa, pesquisarContactos, iniciarConversaCom } from '@/services/chat'

const FILTROS = {
  pessoal: [{ valor: '', nome: 'Todas' }, { valor: 'cliente_loja', nome: 'Lojas' }, { valor: 'suporte', nome: 'Suporte' }, { valor: 'equipa_grupo', nome: 'Equipa' }],
  loja: [{ valor: '', nome: 'Todas' }, { valor: 'cliente_loja', nome: 'Clientes' }, { valor: 'suporte', nome: 'Suporte' }],
  suporte: [],
}
const FILTROS_CONTACTOS = {
  pessoal: [{ valor: '', nome: 'Todos' }, { valor: 'loja', nome: 'Lojas' }, { valor: 'equipa', nome: 'Equipa' }],
  loja: [],
  suporte: [{ valor: '', nome: 'Todos' }, { valor: 'loja', nome: 'Lojas' }, { valor: 'dono', nome: 'Donos' },
            { valor: 'staff', nome: 'Staff' }, { valor: 'cliente', nome: 'Clientes' }, { valor: 'admin', nome: 'Admin' }],
}
const PAPEIS = { equipa: 'Equipa', cliente: 'Cliente', dono: 'Dono de loja', staff: 'Staff', admin: 'Admin', utilizador: 'Utilizador' }

export default {
  name: 'ChatLista',
  components: { ChatAvatar },
  props: {
    isDark:       { type: Boolean, default: true },
    podeExpandir: { type: Boolean, default: false },
    podeFechar:   { type: Boolean, default: false },
    lojaContexto: { type: [String, Number], default: null },
  },
  emits: ['abrir', 'expandir', 'fechar', 'suporte', 'falar-loja'],

  data () {
    return { chat, termo: '', aNovar: false, contactos: [], aPesquisar: false, filtroContactos: '', erroNova: '', agora: Date.now() }
  },

  computed: {
    caixa () { return chat.caixas.find(c => c.caixa_id === chat.caixaId) },
    filtros () {
      const tipo = this.caixa?.tipo
      return (this.aNovar ? FILTROS_CONTACTOS[tipo] : FILTROS[tipo]) || []
    },
    filtroActivo () { return this.aNovar ? this.filtroContactos : chat.filtroTipo },
    textoPesquisaContactos () {
      return { pessoal: 'Pesquisar lojas ou colegas', loja: 'Pesquisar clientes da loja', suporte: 'Pesquisar lojas ou utilizadores' }[this.caixa?.tipo] || 'Pesquisar'
    },
    dicaNova () {
      return {
        pessoal: 'Escreve o nome de uma loja (ou de um colega da tua equipa).',
        loja: 'Escreve o nome de um cliente — a loja só pode iniciar conversa com quem já comprou ou falou com ela.',
        suporte: 'Escreve o nome de uma loja ou utilizador. Usa os filtros para escolher o tipo.',
      }[this.caixa?.tipo] || ''
    },
    botao () { return this.isDark ? 'text-zinc-300 hover:bg-zinc-800' : 'text-zinc-600 hover:bg-gray-100' },
    botaoContorno () { return this.isDark ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400' },
    linha () { return this.isDark ? 'hover:bg-zinc-800/70' : 'hover:bg-gray-50' },
    vazio () { return this.isDark ? 'text-zinc-500' : 'text-zinc-400' },
  },

  mounted () {
    this.relogio = setInterval(() => { this.agora = Date.now() }, 1000)
  },
  beforeUnmount () {
    clearInterval(this.relogio)
    clearTimeout(this.temporizador)
  },

  methods: {
    rotuloPapel (p) { return PAPEIS[p] || '' },
    aEscrever (c) {
      const e = chat.aEscrever[c.id]
      return e && e.ate > this.agora
    },
    resumo (c) {
      const m = c.ultima_mensagem
      if (!m) return c.assunto || 'Sem mensagens'
      const quem = m.minha ? 'Tu: ' : (c.tipo === 'equipa_grupo' ? `${m.remetente.nome.split(' ')[0]}: ` : '')
      if (m.apagada) return quem + 'Mensagem apagada'
      if (m.anexo) return quem + '📷 ' + (m.texto || 'Imagem')
      if (m.produto && !m.texto) return quem + '🛍 ' + m.produto.nome
      return quem + m.texto
    },
    quando (iso) {
      if (!iso) return ''
      const d = new Date(iso)
      const hoje = new Date()
      if (d.toDateString() === hoje.toDateString()) return d.toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })
      const ontem = new Date(); ontem.setDate(hoje.getDate() - 1)
      if (d.toDateString() === ontem.toDateString()) return 'Ontem'
      return d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit' })
    },

    async escolher (id) {
      this.aNovar = false
      this.termo = ''
      chat.pesquisa = ''
      await escolherCaixa(id)
    },
    alternarNova () {
      this.aNovar = !this.aNovar
      this.termo = ''
      this.contactos = []
      this.erroNova = ''
      this.filtroContactos = ''
      if (!this.aNovar) { chat.pesquisa = ''; carregarConversas() }
    },
    filtrar (valor) {
      if (this.aNovar) {
        this.filtroContactos = valor
        this.aoPesquisar()
      } else {
        chat.filtroTipo = valor
        carregarConversas()
      }
    },
    aoPesquisar () {
      clearTimeout(this.temporizador)
      this.temporizador = setTimeout(async () => {
        if (!this.aNovar) {
          chat.pesquisa = this.termo
          carregarConversas()
          return
        }
        if (this.termo.trim().length < 2) { this.contactos = []; return }
        this.aPesquisar = true
        try {
          this.contactos = await pesquisarContactos(this.termo, this.filtroContactos)
        } finally {
          this.aPesquisar = false
        }
      }, 300)
    },
    async comecar (contacto) {
      this.erroNova = ''
      try {
        await iniciarConversaCom(contacto)
        this.aNovar = false
        this.termo = ''
        this.$emit('abrir', chat.conversa)
      } catch (e) {
        this.erroNova = e.response?.data?.detail || 'Não foi possível iniciar a conversa.'
      }
    },
  },
}
</script>
