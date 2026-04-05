<template>
  <div class="space-y-5">

    <!-- Filtros -->
    <div class="flex flex-wrap gap-2 items-center">
      <button v-for="s in statusFiltros" :key="s.value"
        @click="setFiltro(s.value)"
        :class="[
          'px-3 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5',
          filtroStatus === s.value ? s.active : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
        ]">
        {{ s.label }}
        <span v-if="s.value !== 'todos'"
              :class="['px-1.5 py-0.5 rounded-full text-[10px] font-bold min-w-[18px] text-center',
                       filtroStatus === s.value ? 'bg-white/20' : 'bg-zinc-700 text-zinc-400']">
          {{ contagem[s.value] ?? 0 }}
        </span>
      </button>
      <div class="ml-auto text-xs text-zinc-500">{{ totalCount }} encomendas</div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in limit" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Vazio -->
    <div v-else-if="encomendas.length === 0"
         class="text-center py-16 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      Sem encomendas neste estado.
    </div>

    <!-- Lista -->
    <div v-else class="space-y-3">
      <div v-for="enc in encomendas" :key="enc.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">

        <!-- Header -->
        <button @click="toggleExpand(enc.id)"
          class="w-full flex items-center gap-4 p-4 text-left hover:bg-zinc-800/40 transition">
          <div class="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center text-xs font-bold text-zinc-400 flex-shrink-0">
            #{{ enc.id }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-200">{{ enc.comprador_username }}</p>
            <p class="text-xs text-zinc-500">
              {{ formatDate(enc.data_criacao) }} ·
              {{ enc.tipo_entrega === 'entrega' ? '🚚 Entrega' : '🏪 Takeaway' }}
              <span v-if="enc.metodo_pagamento" class="ml-1">·
                {{ enc.metodo_pagamento === 'dinheiro' ? '💵' : enc.metodo_pagamento === 'mbway' ? '📱' : '💳' }}
                {{ enc.metodo_pagamento }}
              </span>
            </p>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', statusColor(enc.status)]">
              {{ enc.status }}
            </span>
            <span class="text-sm font-bold text-red-400">{{ formatPrice(enc.valor_total) }}</span>
            <svg xmlns="http://www.w3.org/2000/svg"
                 :class="['h-4 w-4 text-zinc-600 transition-transform', expandedId === enc.id ? 'rotate-180' : '']"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        <!-- Detalhe expandido -->
        <div v-if="expandedId === enc.id" class="border-t border-zinc-800 p-4 space-y-4">
          <div v-if="loadingDetalhe === enc.id" class="flex justify-center py-4">
            <svg class="animate-spin h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
          </div>

          <template v-else-if="detalhes[enc.id]">
            <!-- Itens -->
            <div>
              <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Produtos</p>
              <div class="space-y-2">
                <div v-for="item in detalhes[enc.id].itens" :key="item.id" class="flex items-center gap-3">
                  <img v-if="item.produto?.ficheiro_url" :src="item.produto.ficheiro_url"
                       class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                  <div v-else class="w-10 h-10 rounded-lg bg-zinc-800 flex-shrink-0"></div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm text-zinc-200 truncate">{{ item.produto?.nome }}</p>
                    <p class="text-xs text-zinc-500">x{{ item.quantidade }} · {{ formatPrice(item.preco) }} un.</p>
                    <div v-if="item.atributos && Object.keys(item.atributos).length > 0"
                         class="flex flex-wrap gap-1 mt-1">
                      <span v-for="(val, key) in item.atributos" :key="key"
                            class="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-[10px] rounded capitalize">
                        {{ key }}: <span class="text-zinc-300 font-medium">{{ val }}</span>
                      </span>
                    </div>
                  </div>
                  <span class="text-sm font-bold text-zinc-300">{{ formatPrice(item.subtotal) }}</span>
                </div>
              </div>
            </div>

            <!-- Info entrega -->
            <div v-if="detalhes[enc.id].morada_entrega || detalhes[enc.id].notas"
                 class="border-t border-zinc-800 pt-3 space-y-1 text-xs">
              <div v-if="detalhes[enc.id].morada_entrega" class="flex gap-2">
                <span class="text-zinc-500 flex-shrink-0">Morada:</span>
                <span class="text-zinc-300">{{ detalhes[enc.id].morada_entrega }}</span>
              </div>
              <div v-if="detalhes[enc.id].notas" class="flex gap-2">
                <span class="text-zinc-500 flex-shrink-0">Notas:</span>
                <span class="text-zinc-300 italic">{{ detalhes[enc.id].notas }}</span>
              </div>
            </div>

            <!-- Condutor atribuído -->
            <div v-if="detalhes[enc.id].entrega_condutor"
                 class="border-t border-zinc-800 pt-3 flex items-center gap-2 text-xs">
              <span class="text-zinc-500">Condutor:</span>
              <span class="text-zinc-300 font-semibold">🚗 {{ detalhes[enc.id].entrega_condutor }}</span>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', entregaStatusColor(detalhes[enc.id].entrega_status)]">
                {{ detalhes[enc.id].entrega_status }}
              </span>
            </div>

            <!-- Resumo financeiro -->
            <div v-if="detalhes[enc.id].comissao_valor" class="border-t border-zinc-800 pt-3 space-y-1.5">
              <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Resumo financeiro</p>
              <div class="flex justify-between text-xs">
                <span class="text-zinc-500">Valor da encomenda</span>
                <span class="text-zinc-300">{{ formatPrice(detalhes[enc.id].valor_total) }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-zinc-500">Comissao ({{ detalhes[enc.id].comissao_percentagem }}%)</span>
                <span class="text-red-400">- {{ formatPrice(detalhes[enc.id].comissao_valor) }}</span>
              </div>
              <div class="flex justify-between text-sm font-bold pt-1 border-t border-zinc-800">
                <span class="text-zinc-300">Receita liquida</span>
                <span class="text-green-400">{{ formatPrice(detalhes[enc.id].receita_liquida) }}</span>
              </div>
            </div>

            <!-- Acções de estado -->
            <div class="border-t border-zinc-800 pt-3 space-y-3">
              <p class="text-xs text-zinc-500">Mudar estado:</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="s in estadosDisponiveis(enc)" :key="s.value"
                  @click="clicarEstado(enc, s.value)"
                  :disabled="s.value === enc.status || loadingStatus === enc.id || estadosBloqueados.includes(enc.status)"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                    s.value === enc.status
                      ? 'ring-1 ring-inset ' + s.ringClass + ' opacity-100 cursor-default'
                      : estadosBloqueados.includes(enc.status)
                        ? 'opacity-30 cursor-not-allowed bg-zinc-800 text-zinc-500'
                        : s.class + ' cursor-pointer'
                  ]">
                  {{ s.value === enc.status ? '✓ ' : '' }}{{ s.label }}
                  <span v-if="s.value === 'enviado' && enc.tipo_entrega === 'entrega' && enc.status === 'preparando'"
                        class="ml-1 text-[9px] opacity-70">+ condutor</span>
                </button>
              </div>
              <p v-if="estadosBloqueados.includes(enc.status)" class="text-xs text-zinc-600">
                Estado {{ enc.status }} — não pode ser alterado.
              </p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="irParaPagina(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="irParaPagina(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="irParaPagina(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Modal atribuir condutor -->
    <div v-if="modalCondutor"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="modalCondutor = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-md p-6 space-y-5 shadow-2xl">

        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold text-zinc-100">Enviar encomenda #{{ modalCondutor.id }}</h3>
            <p class="text-xs text-zinc-500 mt-0.5">{{ modalCondutor.morada_entrega || 'Sem morada definida' }}</p>
          </div>
          <button @click="modalCondutor = null"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Lista condutores -->
        <div>
          <p class="text-xs text-zinc-500 mb-3">Selecciona um condutor (opcional):</p>

          <div v-if="loadingCondutores" class="space-y-2">
            <div v-for="n in 3" :key="n" class="h-12 bg-zinc-800 rounded-xl animate-pulse"></div>
          </div>

          <div v-else-if="condutores.length === 0"
               class="text-center py-6 text-zinc-500 text-sm bg-zinc-800/50 rounded-xl">
            <p>Sem condutores disponíveis.</p>
            <p class="text-xs mt-1 text-zinc-600">Podes enviar sem atribuir condutor.</p>
          </div>

          <div v-else class="space-y-2">
            <!-- Opção sem condutor -->
            <button @click="condutorSelecionado = null"
              :class="['w-full flex items-center gap-3 p-3 rounded-xl border-2 transition text-left',
                       condutorSelecionado === null ? 'border-zinc-500 bg-zinc-800' : 'border-zinc-700 hover:border-zinc-600']">
              <div class="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-zinc-400 flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-semibold text-zinc-300">Sem condutor</p>
                <p class="text-xs text-zinc-500">Enviar sem atribuir condutor</p>
              </div>
              <div v-if="condutorSelecionado === null" class="ml-auto w-4 h-4 rounded-full bg-zinc-500 flex-shrink-0"></div>
            </button>

            <!-- Condutores disponíveis -->
            <button v-for="c in condutores" :key="c.id"
              @click="condutorSelecionado = c.id"
              :class="['w-full flex items-center gap-3 p-3 rounded-xl border-2 transition text-left',
                       condutorSelecionado === c.id ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
              <div class="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-300 font-bold text-sm flex-shrink-0">
                {{ c.nome?.charAt(0)?.toUpperCase() || '?' }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-zinc-200">{{ c.nome }}</p>
                <p class="text-xs text-zinc-500">{{ c.tipo_veiculo || 'Veículo não especificado' }}</p>
              </div>
              <div v-if="condutorSelecionado === c.id" class="w-4 h-4 rounded-full bg-red-500 flex-shrink-0"></div>
            </button>
          </div>
        </div>

        <!-- Botões -->
        <div class="flex gap-3 pt-2">
          <button @click="modalCondutor = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="confirmarEnvio"
            :disabled="loadingEnvio"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     loadingEnvio ? 'bg-red-700 opacity-70 cursor-not-allowed text-white' : 'bg-red-600 hover:bg-red-500 text-white']">
            <svg v-if="loadingEnvio" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ condutorSelecionado ? 'Atribuir e Enviar' : 'Enviar sem condutor' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

const TODOS_ESTADOS = [
  { value: 'pendente',   label: 'Pendente',   class: 'bg-yellow-500/15 hover:bg-yellow-500/30 text-yellow-400', ringClass: 'ring-yellow-500/40 text-yellow-400'  },
  { value: 'pago',       label: 'Pago',       class: 'bg-blue-500/15 hover:bg-blue-500/30 text-blue-400',       ringClass: 'ring-blue-500/40 text-blue-400'      },
  { value: 'preparando', label: 'Preparando', class: 'bg-purple-500/15 hover:bg-purple-500/30 text-purple-400', ringClass: 'ring-purple-500/40 text-purple-400'  },
  { value: 'enviado',    label: 'Enviado',    class: 'bg-indigo-500/15 hover:bg-indigo-500/30 text-indigo-400', ringClass: 'ring-indigo-500/40 text-indigo-400'  },
  { value: 'concluido',  label: 'Concluído',  class: 'bg-green-500/15 hover:bg-green-500/30 text-green-400',   ringClass: 'ring-green-500/40 text-green-400'    },
  { value: 'cancelado',  label: 'Cancelado',  class: 'bg-red-500/15 hover:bg-red-500/30 text-red-400',         ringClass: 'ring-red-500/40 text-red-400'        },
]

const ESTADOS_BLOQUEADOS = ['concluido', 'cancelado', 'enviado']

export default {
  name: 'BackofficeEncomendas',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: true,
      encomendas: [],
      totalCount: 0,
      page: 1,
      limit: 10,
      detalhes: {},
      expandedId: null,
      loadingDetalhe: null,
      loadingStatus: null,
      filtroStatus: 'todos',
      contagem: {},
      todosEstados: TODOS_ESTADOS,
      estadosBloqueados: ESTADOS_BLOQUEADOS,
      statusFiltros: [
        { value: 'todos',     label: 'Todas',      active: 'bg-zinc-200 text-zinc-900'        },
        { value: 'pendente',  label: 'Pendentes',  active: 'bg-yellow-500/20 text-yellow-400' },
        { value: 'pago',      label: 'Pagas',      active: 'bg-blue-500/20 text-blue-400'     },
        { value: 'preparando',label: 'Preparando', active: 'bg-purple-500/20 text-purple-400' },
        { value: 'enviado',   label: 'Enviadas',   active: 'bg-indigo-500/20 text-indigo-400' },
        { value: 'concluido', label: 'Concluídas', active: 'bg-green-500/20 text-green-400'   },
        { value: 'cancelado', label: 'Canceladas', active: 'bg-red-500/20 text-red-400'       },
      ],
      // modal condutor
      modalCondutor:      null,
      condutores:         [],
      condutorSelecionado: null,
      loadingCondutores:  false,
      loadingEnvio:       false,
    }
  },

  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
  },

  async created () {
    await Promise.all([this.fetchEncomendas(), this.fetchContagens()])
  },

  methods: {
    formatPrice (val) { return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0) },
    formatDate (d)    { return new Date(d).toLocaleDateString('pt-PT') },

    statusColor (s) {
      const map = { pendente: 'bg-yellow-500/15 text-yellow-400', pago: 'bg-blue-500/15 text-blue-400', preparando: 'bg-purple-500/15 text-purple-400', enviado: 'bg-indigo-500/15 text-indigo-400', concluido: 'bg-green-500/15 text-green-400', cancelado: 'bg-red-500/15 text-red-400' }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },

    entregaStatusColor (s) {
      const map = { atribuido: 'bg-blue-500/15 text-blue-400', a_caminho: 'bg-indigo-500/15 text-indigo-400', entregue: 'bg-green-500/15 text-green-400', falhou: 'bg-red-500/15 text-red-400' }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },

    // filtra estados disponíveis consoante o tipo de entrega
    estadosDisponiveis (enc) {
      if (enc.tipo_entrega === 'levantamento') {
        // takeaway: sem "enviado"
        return this.todosEstados.filter(s => s.value !== 'enviado')
      }
      return this.todosEstados
    },

    setFiltro (valor) {
      this.filtroStatus = valor
      this.page = 1
      this.expandedId = null
      this.fetchEncomendas()
    },

    irParaPagina (p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.expandedId = null
      this.fetchEncomendas()
    },

    async fetchEncomendas () {
      this.loading = true
      try {
        const params = { limit: this.limit, offset: (this.page - 1) * this.limit }
        if (this.filtroStatus !== 'todos') params.status = this.filtroStatus
        const { data } = await api.get(`/app/loja/${this.lojaId}/encomendas/`, { params })
        this.encomendas = data.results || data
        this.totalCount = data.count ?? this.encomendas.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async fetchContagens () {
      const estados = ['pendente', 'pago', 'preparando', 'enviado', 'concluido', 'cancelado']
      try {
        const respostas = await Promise.all(
          estados.map(s => api.get(`/app/loja/${this.lojaId}/encomendas/`, { params: { status: s, limit: 1, offset: 0 } }))
        )
        const novasContagens = {}
        estados.forEach((s, i) => {
          novasContagens[s] = respostas[i].data.count ?? (respostas[i].data.results || respostas[i].data).length
        })
        this.contagem = novasContagens
      } catch (e) { console.error(e) }
    },

    async toggleExpand (id) {
      if (this.expandedId === id) { this.expandedId = null; return }
      this.expandedId = id
      if (this.detalhes[id]) return
      this.loadingDetalhe = id
      try {
        const { data } = await api.get(`/app/encomenda/${id}/`)
        this.detalhes = { ...this.detalhes, [id]: data }
      } catch (e) { console.error(e) }
      finally { this.loadingDetalhe = null }
    },

    // ── Intercept click em estado ───────────────────────────
    clicarEstado (enc, novoStatus) {
      if (novoStatus === enc.status) return
      if (this.estadosBloqueados.includes(enc.status)) return

      // transições válidas — não pode retroceder após enviado
      const ordemEstados = ['pendente', 'pago', 'preparando', 'enviado', 'concluido']
      const idxActual = ordemEstados.indexOf(enc.status)
      const idxNovo   = ordemEstados.indexOf(novoStatus)

      // permite cancelar em qualquer estado não bloqueado
      // não permite retroceder (ex: enviado → preparando)
      if (novoStatus !== 'cancelado' && idxNovo < idxActual) {
        alert('Não é possível retroceder o estado de uma encomenda já enviada.')
        return
      }

      // takeaway não pode ir para "enviado"
      if (novoStatus === 'enviado' && enc.tipo_entrega === 'levantamento') {
        return
      }

      // se é entrega ao domicílio e vai para "enviado" → abre modal condutor
      if (novoStatus === 'enviado' && enc.tipo_entrega === 'entrega') {
        this.abrirModalCondutor(enc)
        return
      }

      // caso contrário muda directamente
      this.mudarStatus(enc, novoStatus)
    },

    async abrirModalCondutor (enc) {
      this.modalCondutor = { ...enc, morada_entrega: this.detalhes[enc.id]?.morada_entrega || '' }
      this.condutorSelecionado = null
      this.loadingCondutores = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/condutores/`)
        this.condutores = (data.results || data).map(c => ({
          id:           c.id,
          nome:         c.utilizador_nome || c.utilizador_username || `Condutor #${c.id}`,
          tipo_veiculo: c.tipo_veiculo,
        }))
      } catch (e) { console.error(e); this.condutores = [] }
      finally { this.loadingCondutores = false }
    },

    async confirmarEnvio () {
      if (!this.modalCondutor) return
      this.loadingEnvio = true
      const encId = this.modalCondutor.id
      try {
        // 1 — cria entrega (com ou sem condutor)
        const payload = {}
        if (this.condutorSelecionado) payload.condutor_id = this.condutorSelecionado
        await api.post(`/app/loja/${this.lojaId}/encomendas/${encId}/entrega/criar/`, payload)

        // 2 — muda status para enviado via API
        await api.patch(`/app/loja/${this.lojaId}/encomendas/${encId}/status/`, { status: 'enviado' })

        // 3 — actualiza a lista e detalhes localmente usando a referência real
        const encReal = this.encomendas.find(e => e.id === encId)
        if (encReal) {
          this.contagem = {
            ...this.contagem,
            [encReal.status]: Math.max(0, (this.contagem[encReal.status] ?? 1) - 1),
            enviado: (this.contagem['enviado'] ?? 0) + 1,
          }
          encReal.status = 'enviado'
        }
        if (this.detalhes[encId]) {
          this.detalhes[encId].status = 'enviado'
          // actualiza também o condutor no detalhe expandido
          if (this.condutorSelecionado) {
            const condutor = this.condutores.find(c => c.id === this.condutorSelecionado)
            if (condutor) this.detalhes[encId].entrega_condutor = condutor.nome
            this.detalhes[encId].entrega_status = 'atribuido'
          }
        }

        this.modalCondutor = null
      } catch (e) {
        console.error(e)
        // em caso de erro, re-busca para ter estado consistente
        await this.fetchEncomendas()
        await this.fetchContagens()
        this.modalCondutor = null
      } finally { this.loadingEnvio = false }
    },

    async mudarStatus (enc, novoStatus) {
      this.loadingStatus = enc.id
      try {
        await api.patch(`/app/loja/${this.lojaId}/encomendas/${enc.id}/status/`, { status: novoStatus })
        this.contagem = {
          ...this.contagem,
          [enc.status]:  Math.max(0, (this.contagem[enc.status] ?? 1) - 1),
          [novoStatus]:  (this.contagem[novoStatus] ?? 0) + 1,
        }
        enc.status = novoStatus
        if (this.detalhes[enc.id]) this.detalhes[enc.id].status = novoStatus
      } catch (e) {
        console.error(e)
        await this.fetchContagens()
      } finally { this.loadingStatus = null }
    },
  }
}
</script>