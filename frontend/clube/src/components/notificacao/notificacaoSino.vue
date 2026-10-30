<template>
  <!-- visitante sem conta: não há notificações — o sino não aparece -->
  <div v-if="autenticado" class="relative" ref="sinoRef">

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
           class="sino-dropdown fixed z-[9999] border flex flex-col shadow-2xl rounded-2xl"
           :class="[
             isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200',
             abreParaCima ? 'sino-dropdown--cima' : 'sino-dropdown--baixo',
           ]"
           :style="dropdownStyle">

        <!-- Seta a apontar para o sino -->
        <span class="sino-seta"
              :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'"
              :style="{ left: setaLeft + 'px' }"></span>

        <div class="flex flex-col min-h-0 flex-1 overflow-hidden rounded-2xl">

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
                <font-awesome-icon :icon="['fas', icone(notif.tipo)]" class="w-3.5 h-3.5" />
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
                      class="w-5 h-5 rounded flex items-center justify-center text-lg leading-none transition sm:opacity-0 sm:group-hover:opacity-100"
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
      </div>
    </teleport>
  </div>
</template>

<script>
import api, { urlWebSocketComBilhete } from '@/services/api'
import { EVENTO_REEMBOLSO, EVENTO_RELIGADO, marcarLigacao } from '@/composables/useTempoRealReembolsos'
import { estaAutenticado } from '@/services/sessao'
// ícone Font Awesome (solid) + cores por tipo de notificação
const ICONES = {
  loja_pendente:            { icon: 'store',               bg: 'bg-yellow-500/20 text-yellow-500' },
  comissao_recebida:        { icon: 'coins',               bg: 'bg-green-500/20 text-green-500'   },
  loja_aprovada:            { icon: 'circle-check',        bg: 'bg-green-500/20 text-green-500'   },
  loja_rejeitada:           { icon: 'circle-xmark',        bg: 'bg-red-500/20 text-red-500'       },
  nova_encomenda:           { icon: 'bag-shopping',        bg: 'bg-blue-500/20 text-blue-500'     },
  pagamento_aprovado:       { icon: 'credit-card',         bg: 'bg-green-500/20 text-green-500'   },
  encomenda_concluida_loja: { icon: 'circle-check',        bg: 'bg-green-500/20 text-green-500'   },
  encomenda_cancelada_loja: { icon: 'ban',                 bg: 'bg-red-500/20 text-red-500'       },
  stock_baixo:              { icon: 'triangle-exclamation', bg: 'bg-yellow-500/20 text-yellow-500' },
  novo_staff:               { icon: 'user-plus',           bg: 'bg-purple-500/20 text-purple-500' },
  avaliacao_recebida:       { icon: 'star',                bg: 'bg-yellow-500/20 text-yellow-500' },
  entrega_atribuida:        { icon: 'car-side',            bg: 'bg-blue-500/20 text-blue-500'     },
  agendadas_hoje:           { icon: 'calendar-day',        bg: 'bg-sky-500/20 text-sky-500'       },
  entrega_cancelada:        { icon: 'circle-exclamation',  bg: 'bg-red-500/20 text-red-500'       },
  encomenda_paga:           { icon: 'credit-card',         bg: 'bg-green-500/20 text-green-500'   },
  encomenda_atualizada:     { icon: 'box',                 bg: 'bg-blue-500/20 text-blue-500'     },
  encomenda_enviada:        { icon: 'truck',               bg: 'bg-indigo-500/20 text-indigo-500' },
  encomenda_concluida:      { icon: 'circle-check',        bg: 'bg-green-500/20 text-green-500'   },
  encomenda_cancelada:      { icon: 'ban',                 bg: 'bg-red-500/20 text-red-500'       },
  documento_loja:           { icon: 'id-card',             bg: 'bg-emerald-500/20 text-emerald-500' },
  vinti4:                   { icon: 'credit-card',         bg: 'bg-sky-500/20 text-sky-500' },
  qualidade_catalogo:       { icon: 'clipboard-check',     bg: 'bg-amber-500/20 text-amber-500'   },
}

export default {
  name: 'NotificacaoSino',
  props: {
    isDark: { type: Boolean, default: true },   // ← prop nova, default true = comportamento original
  },

  data () {
    return {
      autenticado: estaAutenticado(),
      aberto: false, loading: false,
      notificacoes: [], naoLidas: 0,
      lojas: [], lojaFiltro: null,
      offset: 0, temMais: false,
      dropdownStyle: {},
      setaLeft: 0,
      abreParaCima: false,
    }
  },

  computed: {
    notificacoesFiltradas () {
      if (this.lojaFiltro === null)      return this.notificacoes
      if (this.lojaFiltro === 'pessoal') return this.notificacoes.filter(n => !n.loja_id)
      return this.notificacoes.filter(n => n.loja_id === this.lojaFiltro)
    },
  },

  created () {
    // estado do WebSocket — não reactivo (chaves com "_" não são expostas pelo Vue 3)
    this.ws = null
    this.wsTimer = null
    this.pollTimer = null
    this.wsTentativas = 0
    this.wsALigar = false
    this.destruido = false
  },

  async mounted () {
    document.addEventListener('click', this.clickFora)
    if (!this.autenticado) return
    this.fetchLojas()
    // 1) contador por HTTP — o interceptor renova o token se tiver expirado
    await this.fetchContador()
    // 2) só depois liga o WebSocket, já com um token válido
    this.wsLigar()
  },

  beforeUnmount () {
    this.destruido = true
    document.removeEventListener('click', this.clickFora)
    window.removeEventListener('resize', this.onReposicionar)
    window.removeEventListener('scroll', this.onReposicionar, true)
    window.removeEventListener('keydown', this.onTecla)
    cancelAnimationFrame(this.rafPos)
    this.wsDesligar()
  },

  methods: {
    icone (tipo)   { return ICONES[tipo]?.icon || 'bell' },
    iconeBg (tipo) { return ICONES[tipo]?.bg   || 'bg-zinc-700 text-zinc-300' },

    clickFora (e) {
      const dentroSino     = this.$refs.sinoRef?.contains(e.target)
      const dentroDropdown = e.target.closest('[data-sino-dropdown]')
      if (!dentroSino && !dentroDropdown) this.aberto = false
    },

    async toggle () {
      if (!this.aberto) this.calcularPosicao()   // posição pronta antes do 1º frame
      this.aberto = !this.aberto
      if (this.aberto && this.notificacoes.length === 0) await this.fetchNotificacoes()
    },

    /**
     * Ancora o popup ao sino:
     *  - largura fluida: min(384px, largura do ecrã − 2×margem)
     *  - borda direita alinhada com a do sino; desliza para não sair do ecrã
     *  - abre para baixo; se não houver espaço (≥ 260px), abre para cima
     *  - altura máxima = espaço disponível nesse lado
     *  - seta sempre apontada ao centro do sino
     */
    calcularPosicao () {
      const sino = this.$refs.sinoRef
      if (!sino) return
      const r  = sino.getBoundingClientRect()
      const vw = document.documentElement.clientWidth   // sem a barra de scroll
      const vh = window.innerHeight
      const M  = vw < 640 ? 8 : 12      // margem às bordas do ecrã
      const GAP = 10                    // distância ao sino (espaço para a seta)

      const width = Math.min(384, vw - 2 * M)
      let left = r.right - width
      left = Math.max(M, Math.min(left, vw - width - M))

      const espacoBaixo = vh - r.bottom - GAP - M
      const espacoCima  = r.top - GAP - M
      this.abreParaCima = espacoBaixo < 260 && espacoCima > espacoBaixo

      const maxH = Math.max(160, Math.min(560, this.abreParaCima ? espacoCima : espacoBaixo))
      const style = { left: `${left}px`, width: `${width}px`, maxHeight: `${maxH}px` }
      if (this.abreParaCima) style.bottom = `${vh - r.top + GAP}px`
      else                   style.top    = `${r.bottom + GAP}px`
      this.dropdownStyle = style

      // seta: centro do sino relativo ao popup, sem encostar aos cantos arredondados
      this.setaLeft = Math.max(16, Math.min(r.left + r.width / 2 - left - 6, width - 28))
    },

    onReposicionar () {
      if (!this.aberto) return
      cancelAnimationFrame(this.rafPos)
      this.rafPos = requestAnimationFrame(() => this.calcularPosicao())
    },

    onTecla (e) {
      if (e.key === 'Escape' && this.aberto) this.aberto = false
    },

    async fetchLojas () {
      try {
        const { data } = await api.get('/app/loja/minhas/')
        this.lojas = data || []
      } catch (e) { /* sem lojas */ }
    },

    async wsLigar () {
      if (this.destruido || !localStorage.getItem('access_token') || this.wsALigar) return
      if (this.ws && this.ws.readyState <= WebSocket.OPEN) return   // a ligar ou ligado

      this.wsALigar = true
      const url = await urlWebSocketComBilhete('notificacoes/').finally(() => { this.wsALigar = false })
      if (this.destruido || (this.ws && this.ws.readyState <= WebSocket.OPEN)) return
      const ws = new WebSocket(url)
      this.ws = ws

      ws.onopen = () => {
        // voltou depois de cair: pode ter perdido avisos — as páginas de reembolso abertas recarregam
        marcarLigacao(true)
        if (this.wsJaLigou) window.dispatchEvent(new CustomEvent(EVENTO_RELIGADO))
        this.wsJaLigou = true
        this.wsTentativas = 0
        clearInterval(this.pollTimer); this.pollTimer = null   // tempo real activo → sem polling
      }

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'nova') {
            this.naoLidas = msg.nao_lidas
            if (msg.notificacao && !this.notificacoes.some(n => n.id === msg.notificacao.id)) {
              this.notificacoes.unshift(msg.notificacao)
            }
          }
          if (msg.type === 'contador') this.naoLidas = msg.nao_lidas
          // pedido de reembolso mudou (só ids) — quem o está a ver vai buscá-lo (useTempoRealReembolsos)
          if (msg.type === 'reembolso') window.dispatchEvent(new CustomEvent(EVENTO_REEMBOLSO, { detail: msg.reembolso }))
          // marcação de serviços mudou (utils/servicos.js ouvirMarcacoes)
          if (msg.type === 'marcacao') window.dispatchEvent(new CustomEvent('bendi:marcacao', { detail: msg.marcacao }))
        } catch (err) { /* silencioso */ }
      }

      // Uma ligação recusada (ex.: token expirado) chega como 1006, não 4001.
      // Em qualquer queda: actualiza o contador por HTTP (renova o token),
      // garante polling enquanto não houver socket, e tenta religar com backoff.
      ws.onclose = (e) => {
        if (this.ws === ws) { this.ws = null; marcarLigacao(false) }
        if (this.destruido || e.code === 1000) return

        if (!this.pollTimer) this.pollTimer = setInterval(() => this.fetchContador(), 30000)

        const delay = Math.min(1000 * 2 ** this.wsTentativas, 30000)
        this.wsTentativas = Math.min(this.wsTentativas + 1, 6)
        clearTimeout(this.wsTimer)
        this.wsTimer = setTimeout(async () => {
          await this.fetchContador()
          this.wsLigar()
        }, delay)
      }

      ws.onerror = () => { ws.close() }
    },

    wsDesligar () {
      clearTimeout(this.wsTimer)
      clearInterval(this.pollTimer)
      this.wsTimer = this.pollTimer = null
      if (this.ws) { this.ws.onclose = null; this.ws.close(1000); this.ws = null; marcarLigacao(false) }
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
    // enquanto aberto, acompanha redimensionamento, rotação e scroll
    aberto (val) {
      const fn = val ? 'addEventListener' : 'removeEventListener'
      window[fn]('resize', this.onReposicionar)
      window[fn]('scroll', this.onReposicionar, true)
      window[fn]('keydown', this.onTecla)
      if (val) this.$nextTick(() => this.calcularPosicao())
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* Popup (teleportado para o body — estilos scoped continuam a aplicar-se) */
.sino-dropdown { animation: sinoIn .16s ease-out; }
.sino-dropdown--baixo { transform-origin: top right; }
.sino-dropdown--cima  { transform-origin: bottom right; animation-name: sinoInCima; }

.sino-seta {
  position: absolute;
  width: 12px;
  height: 12px;
  border-style: solid;
  transform: rotate(45deg);
  pointer-events: none;
}
.sino-dropdown--baixo .sino-seta { top: -7px;    border-width: 1px 0 0 1px; }
.sino-dropdown--cima  .sino-seta { bottom: -7px; border-width: 0 1px 1px 0; }

@keyframes sinoIn     { from { opacity: 0; transform: translateY(-4px) scale(.98); } }
@keyframes sinoInCima { from { opacity: 0; transform: translateY(4px)  scale(.98); } }
</style>