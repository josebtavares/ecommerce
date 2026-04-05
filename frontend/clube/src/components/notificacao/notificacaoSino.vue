<template>
  <div class="relative" ref="sinoRef">

    <!-- Botão sino -->
    <button @click="toggle"
      class="relative w-9 h-9 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <!-- Badge contador -->
      <span v-if="naoLidas > 0"
        class="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-red-600 text-white text-[10px] font-bold
               rounded-full flex items-center justify-center">
        {{ naoLidas > 99 ? '99+' : naoLidas }}
      </span>
    </button>

    <!-- Dropdown -->
    <div v-if="aberto"
         class="absolute right-0 top-12 w-96 max-h-[85vh] bg-zinc-900 border border-zinc-800 rounded-2xl
                shadow-2xl z-50 flex flex-col overflow-hidden">

      <!-- Header dropdown -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-zinc-800 flex-shrink-0">
        <h3 class="text-sm font-bold text-zinc-100">Notificações</h3>
        <div class="flex items-center gap-2">
          <button v-if="naoLidas > 0" @click="marcarTodasLidas"
            class="text-xs text-zinc-500 hover:text-zinc-300 transition">
            Marcar todas como lidas
          </button>
          <span v-if="naoLidas > 0"
            class="px-2 py-0.5 bg-red-600/20 text-red-400 text-xs font-bold rounded-full">
            {{ naoLidas }} novas
          </span>
        </div>
      </div>

      <!-- Abas por loja (se tiver mais de uma) -->
      <div v-if="lojas.length > 1" class="flex gap-1 px-3 py-2 border-b border-zinc-800 overflow-x-auto scrollbar-hide flex-shrink-0">
        <button @click="lojaFiltro = null"
          :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                   lojaFiltro === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          Todas
        </button>
        <button v-for="loja in lojas" :key="loja.id"
          @click="lojaFiltro = loja.id"
          :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                   lojaFiltro === loja.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ loja.nome }}
        </button>
        <button @click="lojaFiltro = 'pessoal'"
          :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                   lojaFiltro === 'pessoal' ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          Pessoal
        </button>
      </div>

      <!-- Lista notificações -->
      <div class="overflow-y-auto flex-1">
        <div v-if="loading" class="p-4 space-y-3">
          <div v-for="n in 4" :key="n" class="h-14 bg-zinc-800 rounded-xl animate-pulse"></div>
        </div>

        <div v-else-if="notificacoesFiltradas.length === 0"
             class="flex flex-col items-center justify-center py-12 text-zinc-500 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mb-2 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          Sem notificações
        </div>

        <div v-else>
          <div v-for="notif in notificacoesFiltradas" :key="notif.id"
               @click="clicarNotificacao(notif)"
               :class="[
                 'flex items-start gap-3 px-4 py-3 border-b border-zinc-800/50 cursor-pointer transition',
                 notif.lida ? 'hover:bg-zinc-800/30' : 'bg-red-500/5 hover:bg-red-500/10'
               ]">
            <!-- Ícone tipo -->
            <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 mt-0.5',
                           iconeBg(notif.tipo)]">
              {{ icone(notif.tipo) }}
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <p :class="['text-xs font-semibold leading-snug', notif.lida ? 'text-zinc-400' : 'text-zinc-100']">
                  {{ notif.titulo }}
                </p>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span v-if="!notif.lida" class="w-2 h-2 rounded-full bg-red-500 flex-shrink-0"></span>
                  <button @click.stop="apagar(notif)"
                    class="w-5 h-5 rounded flex items-center justify-center text-zinc-600 hover:text-red-400 transition opacity-0 group-hover:opacity-100">
                    ×
                  </button>
                </div>
              </div>
              <p v-if="notif.mensagem" class="text-[11px] text-zinc-500 mt-0.5 line-clamp-2">{{ notif.mensagem }}</p>
              <div class="flex items-center gap-2 mt-1">
                <p class="text-[10px] text-zinc-600">{{ notif.data_criacao }}</p>
                <span v-if="notif.loja_nome" class="text-[10px] text-zinc-600">· {{ notif.loja_nome }}</span>
              </div>
            </div>
          </div>

          <!-- Carregar mais -->
          <div v-if="temMais" class="p-3 text-center">
            <button @click="carregarMais"
              class="text-xs text-zinc-500 hover:text-zinc-300 transition">
              Ver mais
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const ICONES = {
  // Admin
  loja_pendente:            { icon: '🏪', bg: 'bg-yellow-500/20' },
  comissao_recebida:        { icon: '💰', bg: 'bg-green-500/20'  },
  // Loja
  loja_aprovada:            { icon: '✅', bg: 'bg-green-500/20'  },
  loja_rejeitada:           { icon: '❌', bg: 'bg-red-500/20'    },
  nova_encomenda:           { icon: '🛍️', bg: 'bg-blue-500/20'  },
  pagamento_aprovado:       { icon: '💳', bg: 'bg-green-500/20'  },
  encomenda_concluida_loja: { icon: '🎉', bg: 'bg-green-500/20'  },
  encomenda_cancelada_loja: { icon: '🚫', bg: 'bg-red-500/20'    },
  stock_baixo:              { icon: '⚠️', bg: 'bg-yellow-500/20' },
  novo_staff:               { icon: '👥', bg: 'bg-purple-500/20' },
  avaliacao_recebida:       { icon: '⭐', bg: 'bg-yellow-500/20' },
  // Condutor
  entrega_atribuida:        { icon: '🚗', bg: 'bg-blue-500/20'   },
  entrega_cancelada:        { icon: '🚨', bg: 'bg-red-500/20'    },
  // Comprador
  encomenda_paga:           { icon: '💳', bg: 'bg-green-500/20'  },
  encomenda_atualizada:     { icon: '📦', bg: 'bg-blue-500/20'   },
  encomenda_enviada:        { icon: '🚚', bg: 'bg-indigo-500/20' },
  encomenda_concluida:      { icon: '🎉', bg: 'bg-green-500/20'  },
  encomenda_cancelada:      { icon: '🚫', bg: 'bg-red-500/20'    },
}

export default {
  name: 'NotificacaoSino',

  data () {
    return {
      aberto:        false,
      loading:       false,
      notificacoes:  [],
      naoLidas:      0,
      lojas:         [], // carregadas internamente
      lojaFiltro:    null,
      offset:        0,
      temMais:       false,
      pollingTimer:  null,
    }
  },

  computed: {
    notificacoesFiltradas () {
      if (this.lojaFiltro === null) return this.notificacoes
      if (this.lojaFiltro === 'pessoal') return this.notificacoes.filter(n => !n.loja_id)
      return this.notificacoes.filter(n => n.loja_id === this.lojaFiltro)
    },
  },

  mounted () {
    this.fetchContador()
    this.fetchLojas()
    // polling a cada 30 segundos para actualizar contador
    this.pollingTimer = setInterval(() => this.fetchContador(), 30000)
    // fecha ao clicar fora
    document.addEventListener('click', this.clickFora)
  },

  beforeUnmount () {
    clearInterval(this.pollingTimer)
    document.removeEventListener('click', this.clickFora)
  },

  methods: {
    icone (tipo)   { return ICONES[tipo]?.icon || '🔔' },
    iconeBg (tipo) { return ICONES[tipo]?.bg   || 'bg-zinc-700' },

    clickFora (e) {
      if (this.$refs.sinoRef && !this.$refs.sinoRef.contains(e.target)) {
        this.aberto = false
      }
    },

    async toggle () {
      this.aberto = !this.aberto
      if (this.aberto && this.notificacoes.length === 0) {
        await this.fetchNotificacoes()
      }
    },

    async fetchLojas () {
      try {
        const { data } = await api.get('/app/loja/minhas/')
        this.lojas = data || []
      } catch (e) { /* sem lojas */ }
    },

    async fetchContador () {
      try {
        const { data } = await api.get('/app/notificacoes/contador/')
        this.naoLidas = data.nao_lidas
      } catch (e) { /* silencioso */ }
    },

    async fetchNotificacoes (append = false) {
      this.loading = !append
      try {
        const params = { offset: this.offset, limit: 20 }
        if (this.lojaFiltro && this.lojaFiltro !== 'pessoal') params.loja_id = this.lojaFiltro
        const { data } = await api.get('/app/notificacoes/', { params })
        const results = data.results || data
        if (append) this.notificacoes.push(...results)
        else this.notificacoes = results
        this.naoLidas = data.nao_lidas ?? this.naoLidas
        this.temMais  = !!data.next_offset
        this.offset   = data.next_offset ?? 0
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async carregarMais () {
      await this.fetchNotificacoes(true)
    },

    async clicarNotificacao (notif) {
      if (!notif.lida) await this.marcarLida(notif)
      if (notif.link) {
        this.aberto = false
        this.$router.push(notif.link)
      }
    },

    async marcarLida (notif) {
      try {
        await api.patch(`/app/notificacoes/${notif.id}/lida/`)
        notif.lida = true
        this.naoLidas = Math.max(0, this.naoLidas - 1)
      } catch (e) { console.error(e) }
    },

    async marcarTodasLidas () {
      try {
        const payload = {}
        if (this.lojaFiltro && this.lojaFiltro !== 'pessoal') payload.loja_id = this.lojaFiltro
        await api.patch('/app/notificacoes/todas-lidas/', payload)
        this.notificacoes.forEach(n => { n.lida = true })
        this.naoLidas = 0
      } catch (e) { console.error(e) }
    },

    async apagar (notif) {
      try {
        await api.delete(`/app/notificacoes/${notif.id}/apagar/`)
        this.notificacoes = this.notificacoes.filter(n => n.id !== notif.id)
        if (!notif.lida) this.naoLidas = Math.max(0, this.naoLidas - 1)
      } catch (e) { console.error(e) }
    },
  },

  watch: {
    lojaFiltro () {
      this.offset = 0
      this.notificacoes = []
      this.fetchNotificacoes()
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>