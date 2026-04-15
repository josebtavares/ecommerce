<template>
  <div class="relative" ref="sinoRef">

    <!-- Botão sino -->
    <button @click="toggle"
      class="relative w-9 h-9 rounded-full flex items-center justify-center transition"
      :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"
           :class="isDark ? 'text-white' : 'text-zinc-700'">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <span v-if="naoLidas > 0"
        class="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-red-600 text-white text-[10px] font-bold
               rounded-full flex items-center justify-center">
        {{ naoLidas > 99 ? '99+' : naoLidas }}
      </span>
    </button>

    <teleport to="body">
      <div v-if="aberto" class="fixed inset-0 z-[9997]" @click="aberto = false" />

      <div v-if="aberto"
           data-sino-dropdown
           class="fixed z-[9999] border flex flex-col overflow-hidden shadow-2xl max-h-[80vh]"
           :class="isDark
             ? 'bg-zinc-900 border-zinc-800 rounded-2xl'
             : 'bg-white border-gray-200 rounded-2xl'"
           :style="dropdownStyle">

        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b flex-shrink-0"
             :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <h3 class="text-sm font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Notificações</h3>
          <div class="flex items-center gap-2">
            <button v-if="naoLidas > 0" @click="marcarTodasLidas"
              class="text-xs transition"
              :class="isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
              Marcar todas como lidas
            </button>
            <span v-if="naoLidas > 0" class="px-2 py-0.5 bg-red-600/20 text-red-400 text-xs font-bold rounded-full">
              {{ naoLidas }}
            </span>
            <button @click="aberto = false"
              class="w-7 h-7 rounded-lg flex items-center justify-center transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                   :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Abas por loja -->
        <div v-if="lojas.length > 1"
             class="flex gap-1 px-3 py-2 border-b overflow-x-auto scrollbar-hide flex-shrink-0"
             :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <button @click="lojaFiltro = null"
            :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                     lojaFiltro === null
                       ? 'bg-red-600 text-white'
                       : isDark ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200' : 'bg-gray-100 text-zinc-500 hover:text-zinc-700']">
            Todas
          </button>
          <button v-for="loja in lojas" :key="loja.id" @click="lojaFiltro = loja.id"
            :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                     lojaFiltro === loja.id
                       ? 'bg-red-600 text-white'
                       : isDark ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200' : 'bg-gray-100 text-zinc-500 hover:text-zinc-700']">
            {{ loja.nome }}
          </button>
          <button @click="lojaFiltro = 'pessoal'"
            :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition whitespace-nowrap',
                     lojaFiltro === 'pessoal'
                       ? 'bg-red-600 text-white'
                       : isDark ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200' : 'bg-gray-100 text-zinc-500 hover:text-zinc-700']">
            Pessoal
          </button>
        </div>

        <!-- Lista -->
        <div class="overflow-y-auto flex-1">
          <div v-if="loading" class="p-4 space-y-3">
            <div v-for="n in 4" :key="n" class="h-14 rounded-xl animate-pulse"
                 :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></div>
          </div>

          <div v-else-if="notificacoesFiltradas.length === 0"
               class="flex flex-col items-center justify-center py-6 text-sm"
               :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mb-2"
                 :class="isDark ? 'text-zinc-700' : 'text-gray-300'"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            Sem notificações
          </div>

          <div v-else>
            <div v-for="notif in notificacoesFiltradas" :key="notif.id"
                 @click="clicarNotificacao(notif)"
                 class="group flex items-start gap-3 px-4 py-3 border-b cursor-pointer transition"
                 :class="[
                   isDark ? 'border-zinc-800/50' : 'border-gray-100',
                   notif.lida
                     ? isDark ? 'hover:bg-zinc-800/30' : 'hover:bg-gray-50'
                     : isDark ? 'bg-red-500/5 hover:bg-red-500/10' : 'bg-red-50/50 hover:bg-red-50'
                 ]">
              <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-sm flex-shrink-0 mt-0.5', iconeBg(notif.tipo)]">
                {{ icone(notif.tipo) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <p class="text-xs font-semibold leading-snug"
                     :class="notif.lida ? (isDark ? 'text-zinc-400' : 'text-zinc-500') : (isDark ? 'text-zinc-100' : 'text-zinc-900')">
                    {{ notif.titulo }}
                  </p>
                  <div class="flex items-center gap-1.5 flex-shrink-0">
                    <span v-if="!notif.lida" class="w-2 h-2 rounded-full bg-red-500 flex-shrink-0"></span>
                    <button @click.stop="apagar(notif)"
                      class="w-5 h-5 rounded flex items-center justify-center text-lg leading-none transition opacity-0 group-hover:opacity-100"
                      :class="isDark ? 'text-zinc-600 hover:text-red-400' : 'text-gray-300 hover:text-red-400'">
                      ×
                    </button>
                  </div>
                </div>
                <p v-if="notif.mensagem" class="text-[11px] mt-0.5 line-clamp-2"
                   :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ notif.mensagem }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <p class="text-[10px]" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">{{ notif.data_criacao }}</p>
                  <span v-if="notif.loja_nome" class="text-[10px]" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">· {{ notif.loja_nome }}</span>
                </div>
              </div>
            </div>

            <div v-if="temMais" class="p-3 text-center">
              <button @click="carregarMais"
                class="text-xs transition px-4 py-2 rounded-lg"
                :class="isDark ? 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800' : 'text-zinc-400 hover:text-zinc-700 hover:bg-gray-100'">
                Ver mais
              </button>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script>
import api from '@/services/api'

const ICONES = {
  loja_pendente:            { icon: '🏪', bg: 'bg-yellow-500/20' },
  comissao_recebida:        { icon: '💰', bg: 'bg-green-500/20'  },
  loja_aprovada:            { icon: '✅', bg: 'bg-green-500/20'  },
  loja_rejeitada:           { icon: '❌', bg: 'bg-red-500/20'    },
  nova_encomenda:           { icon: '🛍️', bg: 'bg-blue-500/20'  },
  pagamento_aprovado:       { icon: '💳', bg: 'bg-green-500/20'  },
  encomenda_concluida_loja: { icon: '🎉', bg: 'bg-green-500/20'  },
  encomenda_cancelada_loja: { icon: '🚫', bg: 'bg-red-500/20'    },
  stock_baixo:              { icon: '⚠️', bg: 'bg-yellow-500/20' },
  novo_staff:               { icon: '👥', bg: 'bg-purple-500/20' },
  avaliacao_recebida:       { icon: '⭐', bg: 'bg-yellow-500/20' },
  entrega_atribuida:        { icon: '🚗', bg: 'bg-blue-500/20'   },
  entrega_cancelada:        { icon: '🚨', bg: 'bg-red-500/20'    },
  encomenda_paga:           { icon: '💳', bg: 'bg-green-500/20'  },
  encomenda_atualizada:     { icon: '📦', bg: 'bg-blue-500/20'   },
  encomenda_enviada:        { icon: '🚚', bg: 'bg-indigo-500/20' },
  encomenda_concluida:      { icon: '🎉', bg: 'bg-green-500/20'  },
  encomenda_cancelada:      { icon: '🚫', bg: 'bg-red-500/20'    },
}

export default {
  name: 'NotificacaoSino',
  props: {
    isDark: { type: Boolean, default: true },   // ← prop nova, default true = comportamento original
  },

  data () {
    return {
      aberto: false, loading: false,
      notificacoes: [], naoLidas: 0,
      lojas: [], lojaFiltro: null,
      offset: 0, temMais: false,
      _ws: null, _wsTimer: null, _wsTentativas: 0,
      isMobile: window.innerWidth < 640,
      dropdownStyle: {},
    }
  },

  computed: {
    notificacoesFiltradas () {
      if (this.lojaFiltro === null)      return this.notificacoes
      if (this.lojaFiltro === 'pessoal') return this.notificacoes.filter(n => !n.loja_id)
      return this.notificacoes.filter(n => n.loja_id === this.lojaFiltro)
    },
  },

  mounted () {
    this.fetchLojas()
    document.addEventListener('click', this.clickFora)
    this._wsLigar()
  },

  beforeUnmount () {
    document.removeEventListener('click', this.clickFora)
    this._wsDesligar()
  },

  methods: {
    icone (tipo)   { return ICONES[tipo]?.icon || '🔔' },
    iconeBg (tipo) { return ICONES[tipo]?.bg   || 'bg-zinc-700' },

    clickFora (e) {
      const dentroSino     = this.$refs.sinoRef?.contains(e.target)
      const dentroDropdown = e.target.closest('[data-sino-dropdown]')
      if (!dentroSino && !dentroDropdown) this.aberto = false
    },

    async toggle () {
      this.isMobile = window.innerWidth < 640
      this.aberto   = !this.aberto
      if (this.aberto && this.notificacoes.length === 0) await this.fetchNotificacoes()
    },

    calcularPosicao () {
      if (!this.$refs.sinoRef) return
      const rect   = this.$refs.sinoRef.getBoundingClientRect()
      const top    = Math.max(8, rect.bottom + 8)
      const mobile = window.innerWidth < 640
      if (mobile) {
        const width = window.innerWidth - 16
        this.dropdownStyle = { top: `${top}px`, right: '8px', left: '8px', width: `${width}px`, maxHeight: `${window.innerHeight - top - 16}px` }
      } else {
        const right = Math.max(8, window.innerWidth - rect.right)
        this.dropdownStyle = { top: `${top}px`, right: `${right}px`, width: '384px', maxHeight: `${window.innerHeight - top - 16}px` }
      }
    },

    async fetchLojas () {
      try {
        const { data } = await api.get('/app/loja/minhas/')
        this.lojas = data || []
      } catch (e) { /* sem lojas */ }
    },

    _wsUrl () {
      const base  = process.env.VUE_APP_WS_URL || 'ws://localhost:8000/ws'
      const token = localStorage.getItem('access_token') || ''
      return `${base}/notificacoes/?token=${token}`
    },

    _wsLigar () {
      if (!localStorage.getItem('access_token')) return
      if (this._ws?.readyState === WebSocket.OPEN) return
      this._ws = new WebSocket(this._wsUrl())
      this._ws.onopen  = () => { this._wsTentativas = 0 }
      this._ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'nova') {
            this.naoLidas = msg.nao_lidas
            if (msg.notificacao && !this.notificacoes.some(n => n.id === msg.notificacao.id)) {
              this.notificacoes.unshift(msg.notificacao)
            }
          }
          if (msg.type === 'contador') this.naoLidas = msg.nao_lidas
        } catch (err) { /* silencioso */ }
      }
      this._ws.onclose = (e) => {
        if (e.code !== 4001) {
          const delay = Math.min(1000 * 2 ** this._wsTentativas, 30000)
          this._wsTentativas++
          this._wsTimer = setTimeout(() => this._wsLigar(), delay)
        } else {
          this._wsTimer = setInterval(() => this.fetchContador(), 30000)
          this.fetchContador()
        }
      }
      this._ws.onerror = () => { this._ws?.close() }
    },

    _wsDesligar () {
      clearTimeout(this._wsTimer); clearInterval(this._wsTimer)
      this._ws?.close(1000); this._ws = null
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
        else        this.notificacoes = results
        this.naoLidas = data.nao_lidas ?? this.naoLidas
        this.temMais  = !!data.next_offset
        this.offset   = data.next_offset ?? 0
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async carregarMais () { await this.fetchNotificacoes(true) },

    async clicarNotificacao (notif) {
      if (!notif.lida) await this.marcarLida(notif)
      if (notif.link) { this.aberto = false; this.$router.push(notif.link) }
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
    lojaFiltro () { this.offset = 0; this.notificacoes = []; this.fetchNotificacoes() },
    async aberto (val) {
      if (val) { await this.$nextTick(); this.calcularPosicao() }
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>