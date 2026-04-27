<template>
  <div class="space-y-5">

    <!-- Tabs -->
    <div v-if="!isCondutor" class="flex gap-1 bg-zinc-900 rounded-xl p-1 w-fit">
      <button v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        :class="['px-4 py-2 rounded-lg text-sm font-semibold transition',
                 activeTab === tab.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
        {{ tab.label }}
      </button>
    </div>

    <!-- ═══ TAB: ENTREGAS ═══ -->
    <div v-if="activeTab === 'entregas'">

      <!-- Filtros + limit -->
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <button v-for="f in filtrosEntrega" :key="f.value"
          @click="filtroEntrega = f.value; page = 1; fetchEntregas()"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition',
                   filtroEntrega === f.value ? f.active : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ f.label }}
        </button>
        <div class="ml-auto flex items-center gap-2">
          <span class="text-xs text-zinc-500">Por página:</span>
          <select v-model="limit" @change="page = 1; fetchEntregas()"
            class="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-300 focus:outline-none focus:border-red-500">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
          <span class="text-xs text-zinc-500">{{ totalCount }} entregas</span>
        </div>
      </div>

      <div v-if="loadingEntregas" class="space-y-3">
        <div v-for="n in limit" :key="n" class="h-24 bg-zinc-900 rounded-2xl animate-pulse"></div>
      </div>

      <div v-else-if="entregas.length === 0"
           class="text-center py-16 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Sem entregas neste estado.
      </div>

      <div v-else class="space-y-3">
        <div v-for="entrega in entregas" :key="entrega.id"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">

          <!-- Header -->
          <div class="p-4 flex items-start gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span class="text-sm font-bold text-zinc-200">Encomenda #{{ entrega.encomenda }}</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', entregaStatusColor(entrega.status)]">
                  {{ labelStatus(entrega.status) }}
                </span>
                <span v-if="entrega.opcao_entrega_nome"
                      class="px-1.5 py-0.5 rounded text-[10px] bg-zinc-800 text-zinc-400">
                  {{ entrega.opcao_entrega_nome }}
                </span>
              </div>
              <p class="text-xs text-zinc-500">{{ entrega.data_criacao }}</p>
            </div>
            <div class="text-right flex-shrink-0">
              <p v-if="entrega.condutor_nome" class="text-xs font-semibold text-zinc-200">
                🚗 {{ entrega.condutor_nome }}
              </p>
              <p v-if="entrega.condutor_veiculo" class="text-[10px] text-zinc-500">{{ entrega.condutor_veiculo }}</p>
              <p v-if="!entrega.condutor_nome" class="text-xs text-zinc-600 italic">Sem condutor</p>
            </div>
          </div>

          <!-- Contacto do cliente -->
          <div v-if="entrega.comprador_nome || entrega.comprador_email || entrega.comprador_telefone"
               class="border-t border-zinc-800 px-4 py-3 bg-zinc-800/30">
            <p class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Cliente</p>
            <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs">
              <span v-if="entrega.comprador_nome" class="text-zinc-300 font-semibold">
                Nome: {{ entrega.comprador_nome }}
              </span>
              <a v-if="entrega.comprador_email" :href="`mailto:${entrega.comprador_email}`"
                 class="text-white-400 hover:text-red-300 transition">Email: {{ entrega.comprador_email }}</a>
              <a v-if="entrega.comprador_telefone" :href="`tel:${entrega.comprador_telefone}`"
                 class="text-white-400 hover:text-red-300 transition">Contato: {{ entrega.comprador_telefone }}</a>
            </div>
          </div>

          <!-- Detalhe -->
          <div class="border-t border-zinc-800 px-4 py-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
            <div v-if="entrega.morada_entrega" class="col-span-2 flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">Morada:</span>
              <span class="text-zinc-300">{{ entrega.morada_entrega }}</span>
            </div>
            <div v-if="entrega.tipo_entrega" class="flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">Tipo:</span>
              <span class="text-zinc-300">{{ entrega.tipo_entrega === 'entrega' ? '🚚 Domicílio' : '🏪 Levantamento' }}</span>
            </div>
            <div v-if="entrega.opcao_entrega_nome" class="flex gap-2 col-span-2">
              <span class="text-zinc-500 flex-shrink-0">Opção:</span>
              <span class="text-zinc-300 font-semibold">{{ entrega.opcao_entrega_nome }}</span>
              <span v-if="entrega.opcao_entrega_tempo" class="text-zinc-500">· {{ entrega.opcao_entrega_tempo }}</span>
              <span v-if="entrega.opcao_entrega_preco" class="text-zinc-500">
                · {{ parseFloat(entrega.opcao_entrega_preco) === 0 ? 'Gratuito' : '€' + entrega.opcao_entrega_preco }}
              </span>
            </div>
            <div v-if="entrega.metodo_pagamento" class="flex gap-2">
              <span class="text-zinc-500">Pagamento:</span>
              <span class="text-zinc-300 capitalize">
                {{ entrega.metodo_pagamento === 'dinheiro' ? '💵' : entrega.metodo_pagamento === 'mbway' ? '📱' : '💳' }}
                {{ entrega.metodo_pagamento }}
              </span>
            </div>
            <div v-if="entrega.notas" class="col-span-2 flex gap-2">
              <span class="text-zinc-500 flex-shrink-0">📝 Notas:</span>
              <span class="text-zinc-300 italic">{{ entrega.notas }}</span>
            </div>
            <div v-if="entrega.data_entrega" class="col-span-2 text-green-400">
              ✓ Entregue em {{ entrega.data_entrega }}
            </div>
          </div>

          <!-- Acções -->
          <div v-if="!['entregue'].includes(entrega.status)"
               class="border-t border-zinc-800 px-4 py-3 flex flex-wrap gap-2 items-center">
            <template v-if="isCondutor">
              <button v-if="entrega.status === 'atribuido'"
                @click="atualizarEntrega(entrega, 'a_caminho')" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 text-xs font-semibold transition">
                🚗 A caminho
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="atualizarEntrega(entrega, 'entregue')" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 text-xs font-semibold transition">
                ✓ Marcar entregue
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="confirmarFalha(entrega)" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-semibold transition">
                ✗ Não consegui entregar
              </button>
            </template>
            <template v-else>
              <button @click="abrirReatribuir(entrega)"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold transition">
                {{ entrega.condutor_nome ? '↺ Reatribuir' : '+ Atribuir condutor' }}
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="atualizarEntrega(entrega, 'entregue')" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 text-xs font-semibold transition">
                ✓ Concluir entrega
              </button>
              <button v-if="['atribuido','a_caminho'].includes(entrega.status)"
                @click="confirmarFalha(entrega)" :disabled="loadingAcao === entrega.id"
                class="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-semibold transition">
                ✗ Cancelar entrega
              </button>
            </template>
            <svg v-if="loadingAcao === entrega.id" class="animate-spin h-4 w-4 text-zinc-500 ml-auto" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
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
    </div>

    <!-- ═══ TAB: CONDUTORES ═══ -->
    <div v-if="activeTab === 'condutores' && !isCondutor">
      <div v-if="loadingCondutores" class="space-y-3">
        <div v-for="n in 3" :key="n" class="h-14 bg-zinc-900 rounded-2xl animate-pulse"></div>
      </div>
      <div v-else-if="condutores.length === 0"
           class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Sem condutores. Adiciona condutores na secção de Staff.
      </div>
      <div v-else class="space-y-3">
        <div v-for="c in condutores" :key="c.id"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4">
          <div class="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-300 font-bold flex-shrink-0">
            {{ (c.utilizador_nome || c.utilizador_username)?.charAt(0)?.toUpperCase() || '?' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-200">{{ c.utilizador_nome || c.utilizador_username }}</p>
            <p class="text-xs text-zinc-500">{{ c.tipo_veiculo || 'Veículo não especificado' }}</p>
            <div class="flex gap-3 mt-1">
              <a v-if="c.utilizador_email" :href="`mailto:${c.utilizador_email}`"
                 class="text-xs text-red-400 hover:text-red-300 transition">✉️ {{ c.utilizador_email }}</a>
              <a v-if="c.utilizador_telefone" :href="`tel:${c.utilizador_telefone}`"
                 class="text-xs text-red-400 hover:text-red-300 transition">📞 {{ c.utilizador_telefone }}</a>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-zinc-500">
              {{ entregasActivasDoCondutor(c.id) }} activa{{ entregasActivasDoCondutor(c.id) !== 1 ? 's' : '' }}
            </span>
            <span :class="['w-2 h-2 rounded-full', c.ativo ? 'bg-green-500' : 'bg-zinc-600']"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal reatribuir -->
    <div v-if="modalReatribuir"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="modalReatribuir = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-md p-6 space-y-5 shadow-2xl">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold text-zinc-100">
              {{ modalReatribuir.condutor_nome ? 'Reatribuir condutor' : 'Atribuir condutor' }}
            </h3>
            <p class="text-xs text-zinc-500 mt-0.5">Encomenda #{{ modalReatribuir.encomenda }}</p>
          </div>
          <button @click="modalReatribuir = null"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="modalReatribuir.comprador_nome || modalReatribuir.comprador_email || modalReatribuir.comprador_telefone"
             class="bg-zinc-800/50 rounded-xl p-3 space-y-1 text-xs">
          <p class="text-zinc-500 font-semibold mb-1">Cliente</p>
          <p v-if="modalReatribuir.comprador_nome" class="text-zinc-300 font-semibold">👤 {{ modalReatribuir.comprador_nome }}</p>
          <a v-if="modalReatribuir.comprador_email" :href="`mailto:${modalReatribuir.comprador_email}`"
             class="text-red-400 hover:text-red-300 flex items-center gap-1">✉️ {{ modalReatribuir.comprador_email }}</a>
          <a v-if="modalReatribuir.comprador_telefone" :href="`tel:${modalReatribuir.comprador_telefone}`"
             class="text-red-400 hover:text-red-300 flex items-center gap-1">📞 {{ modalReatribuir.comprador_telefone }}</a>
          <p v-if="modalReatribuir.morada_entrega" class="text-zinc-400 mt-1">📍 {{ modalReatribuir.morada_entrega }}</p>
        </div>

        <div v-if="modalReatribuir.condutor_nome"
             class="bg-zinc-800/50 rounded-xl p-3 flex items-center gap-3 text-xs">
          <span class="text-zinc-500">Actual:</span>
          <span class="text-zinc-300 font-semibold">🚗 {{ modalReatribuir.condutor_nome }}</span>
          <span class="text-zinc-500 ml-auto">→ será substituído</span>
        </div>

        <div class="space-y-2 max-h-64 overflow-y-auto">
          <button v-for="c in condutores" :key="c.id"
            @click="novoCondutorId = c.id"
            :disabled="c.id === modalReatribuir.condutor_id_field"
            :class="['w-full flex items-center gap-3 p-3 rounded-xl border-2 transition text-left',
                     c.id === modalReatribuir.condutor_id_field
                       ? 'border-zinc-700 opacity-40 cursor-not-allowed'
                       : novoCondutorId === c.id
                         ? 'border-red-500 bg-red-500/10'
                         : 'border-zinc-700 hover:border-zinc-600']">
            <div class="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-sm flex-shrink-0 text-zinc-300">
              {{ (c.utilizador_nome || c.utilizador_username)?.charAt(0)?.toUpperCase() || '?' }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-zinc-200">{{ c.utilizador_nome || c.utilizador_username }}</p>
              <p class="text-xs text-zinc-500">{{ c.tipo_veiculo || 'Veículo n/d' }}</p>
              <p v-if="c.utilizador_telefone" class="text-xs text-zinc-600">📞 {{ c.utilizador_telefone }}</p>
            </div>
            <span v-if="c.id === modalReatribuir.condutor_id_field" class="text-[10px] text-zinc-500">actual</span>
            <div v-else-if="novoCondutorId === c.id" class="w-4 h-4 rounded-full bg-red-500 flex-shrink-0"></div>
          </button>
          <p v-if="condutores.filter(c => c.id !== modalReatribuir.condutor_id_field).length === 0"
             class="text-center py-4 text-zinc-500 text-sm">Sem outros condutores disponíveis.</p>
        </div>

        <div class="flex gap-3">
          <button @click="modalReatribuir = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="confirmarReatribuicao"
            :disabled="!novoCondutorId || loadingReatribuir"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     !novoCondutorId || loadingReatribuir ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
            <svg v-if="loadingReatribuir" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            Confirmar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal confirmar falha -->
    <div v-if="modalFalha"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="modalFalha = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 space-y-4 shadow-2xl text-center">
        <div class="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 class="text-base font-bold text-zinc-100">Cancelar entrega?</h3>
          <p class="text-sm text-zinc-400 mt-1">
            A encomenda <strong>#{{ modalFalha?.encomenda }}</strong> voltará ao estado <strong>"preparando"</strong>.
          </p>
        </div>
        <div class="flex gap-3">
          <button @click="modalFalha = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Voltar
          </button>
          <button @click="confirmarFalhaEntrega" :disabled="loadingAcao === modalFalha?.id"
            class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition">
            Confirmar
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'BackofficeEntregas',
  props: {
    lojaId:    [String, Number],
    minhaRole: { type: String, default: '' },
  },

  data () {
    return {
      activeTab: 'entregas',
      tabs: [
        { key: 'entregas',   label: '📦 Entregas'  },
        { key: 'condutores', label: '🚗 Condutores' },
      ],
      entregas:      [],
      totalCount:    0,
      page:          1,
      limit:         10,
      loadingEntregas:  false,
      filtroEntrega:    'todos',
      filtrosEntrega: [
        { value: 'todos',     label: 'Todas',      active: 'bg-zinc-200 text-zinc-900'        },
        { value: 'atribuido', label: 'Atribuídas', active: 'bg-blue-500/20 text-blue-400'     },
        { value: 'a_caminho', label: 'A caminho',  active: 'bg-indigo-500/20 text-indigo-400' },
        { value: 'entregue',  label: 'Entregues',  active: 'bg-green-500/20 text-green-400'   },
        { value: 'falhou',    label: 'Falhadas',   active: 'bg-red-500/20 text-red-400'       },
      ],
      condutores:        [],
      loadingCondutores: false,
      modalReatribuir:   null,
      novoCondutorId:    null,
      loadingReatribuir: false,
      modalFalha:        null,
      loadingAcao:       null,
    }
  },

  computed: {
    isCondutor ()  { return this.minhaRole === 'condutor' },
    totalPages ()  { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
  },

  async created () {
    await Promise.all([this.fetchEntregas(), this.fetchCondutores()])
  },

  methods: {
    labelStatus (s) {
      const map = { atribuido: 'Atribuído', a_caminho: 'A caminho', entregue: 'Entregue', falhou: 'Falhou' }
      return map[s] || s
    },

    entregaStatusColor (s) {
      const map = {
        atribuido: 'bg-blue-500/15 text-blue-400',
        a_caminho: 'bg-indigo-500/15 text-indigo-400',
        entregue:  'bg-green-500/15 text-green-400',
        falhou:    'bg-red-500/15 text-red-400',
      }
      return map[s] || 'bg-zinc-500/15 text-zinc-400'
    },

    entregasActivasDoCondutor (condutorId) {
      return this.entregas.filter(e =>
        e.condutor_id_field === condutorId && !['entregue', 'falhou'].includes(e.status)
      ).length
    },

    irParaPagina (p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.fetchEntregas()
    },

    async fetchEntregas () {
      this.loadingEntregas = true
      try {
        const params = {
          limit:  this.limit,
          offset: (this.page - 1) * this.limit,
        }
        if (this.filtroEntrega !== 'todos') params.status = this.filtroEntrega
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/lista/`, { params })
        this.entregas   = data.results || data
        this.totalCount = data.count ?? this.entregas.length
      } catch (e) { console.error(e) }
      finally { this.loadingEntregas = false }
    },

    async fetchCondutores () {
      this.loadingCondutores = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/condutores/`)
        this.condutores = data.results || data
      } catch (e) { console.error(e) }
      finally { this.loadingCondutores = false }
    },

    async atualizarEntrega (entrega, novoStatus) {
      this.loadingAcao = entrega.id
      try {
        await api.patch(
          `/app/loja/${this.lojaId}/encomendas/${entrega.encomenda}/entrega/atualizar/`,
          { status: novoStatus }
        )
        entrega.status = novoStatus
        if (novoStatus === 'entregue') {
          entrega.data_entrega = new Date().toLocaleDateString('pt-PT')
        }
      } catch (e) { console.error(e) }
      finally { this.loadingAcao = null }
    },

    confirmarFalha (entrega) { this.modalFalha = entrega },

    async confirmarFalhaEntrega () {
      if (!this.modalFalha) return
      this.loadingAcao = this.modalFalha.id
      const entregaId = this.modalFalha.id
      try {
        await api.patch(
          `/app/loja/${this.lojaId}/encomendas/${this.modalFalha.encomenda}/entrega/atualizar/`,
          { status: 'falhou' }
        )
        const entrega = this.entregas.find(e => e.id === entregaId)
        if (entrega) entrega.status = 'falhou'
        this.modalFalha = null
      } catch (e) { console.error(e) }
      finally { this.loadingAcao = null }
    },

    abrirReatribuir (entrega) {
      this.modalReatribuir = entrega
      this.novoCondutorId  = null
    },

    async confirmarReatribuicao () {
      if (!this.novoCondutorId || !this.modalReatribuir) return
      this.loadingReatribuir = true
      const entregaFalhou = this.modalReatribuir.status === 'falhou'
      try {
        await api.patch(
          `/app/loja/${this.lojaId}/encomendas/${this.modalReatribuir.encomenda}/entrega/atualizar/`,
          { condutor_id: this.novoCondutorId }
        )
        const condutor = this.condutores.find(c => c.id === this.novoCondutorId)
        const entrega  = this.entregas.find(e => e.id === this.modalReatribuir.id)
        if (entrega && condutor) {
          entrega.condutor_id_field = condutor.id
          entrega.condutor_nome     = condutor.utilizador_nome || condutor.utilizador_username
          entrega.condutor_veiculo  = condutor.tipo_veiculo
          if (entregaFalhou) entrega.status = 'atribuido'
        }
        this.modalReatribuir = null
      } catch (e) { console.error(e) }
      finally { this.loadingReatribuir = false }
    },
  },

  watch: {
    activeTab (tab) {
      if (tab === 'entregas'   && this.entregas.length === 0)   this.fetchEntregas()
      if (tab === 'condutores' && this.condutores.length === 0) this.fetchCondutores()
    },
  },
}
</script>