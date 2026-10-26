<template>
  <div class="space-y-5">

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 items-center">
      <div class="relative flex-1 min-w-0 w-full sm:w-auto">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="q" @input="debouncedFetch" placeholder="Pesquisar loja..."
          class="w-full pl-9 pr-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition" />
      </div>
      <div class="flex gap-2 flex-wrap">
        <select v-model="filtroEstado" @change="fetchLojas(1)"
          class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
          <option value="">Todos os estados</option>
          <option v-for="(e, chave) in ESTADOS" :key="chave" :value="chave">{{ e.plural }}</option>
        </select>
        <select v-model="filtroCategoria" @change="fetchLojas(1)"
          class="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none transition">
          <option value="">Todas as categorias</option>
          <option v-for="cat in categorias" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
      <p class="text-xs text-zinc-500 ml-auto">{{ totalCount }} lojas</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista -->
    <div v-else class="space-y-3">
      <div v-for="loja in lojas" :key="loja.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 hover:border-zinc-700 transition cursor-pointer group"
           @click="abrirDetalhe(loja)">

        <!-- Row principal -->
        <div class="flex items-center gap-3">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-12 h-12 rounded-xl object-cover flex-shrink-0" />
          <div v-else class="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center flex-shrink-0">
            <span class="text-zinc-400 font-bold text-lg">{{ loja.nome.charAt(0) }}</span>
          </div>

          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5 flex-wrap">
              <p class="text-sm font-bold text-zinc-200 group-hover:text-red-400 transition">{{ loja.nome }}</p>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', estadoInfo(loja).classe]">
                {{ estadoInfo(loja).label }}
              </span>
            </div>
            <p class="text-xs text-zinc-500 truncate">
              {{ loja.categoria }} · {{ loja.dono.username }}
              · {{ loja.total_produtos }} prod. · {{ loja.total_encomendas }} enc.
            </p>
          </div>

          <!-- Acção rápida conforme o estado (loja fechada pelo dono: só o dono reabre) -->
          <button v-if="acaoRapida(loja)" @click.stop="executarAcao(loja, acaoRapida(loja))"
            :class="['flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-bold transition', ACOES[acaoRapida(loja)].classe]">
            {{ ACOES[acaoRapida(loja)].label }}
          </button>
        </div>

        <!-- Comissão — linha separada no mobile -->
        <div class="flex items-center gap-2 mt-3 pt-3 border-t border-zinc-800" @click.stop>
          <span class="text-xs text-zinc-500">Comissão:</span>
          <input
            v-model="loja._comissao_edit"
            type="number" min="0" max="100" step="0.5"
            class="w-16 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100
                   focus:outline-none focus:border-red-500 transition text-center"
          />
          <span class="text-xs text-zinc-500">%</span>
          <button @click.stop="guardarComissao(loja)"
            class="px-3 py-1 rounded-lg bg-red-600/15 hover:bg-red-600/25 text-red-400 text-xs font-bold transition">
            Guardar
          </button>
          <span class="ml-auto text-xs text-zinc-600">clica para ver detalhe →</span>
        </div>
      </div>

      <div v-if="lojas.length === 0"
           class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Nenhuma loja encontrada.
      </div>
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-2">
        <button @click="fetchLojas(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchLojas(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchLojas(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Modal detalhe -->
    <div v-if="lojaDetalhe"
         class="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/70 backdrop-blur-sm"
         @click.self="lojaDetalhe = null">
      <div class="bg-zinc-900 border border-zinc-800 w-full sm:max-w-2xl max-h-[92vh] sm:max-h-[90vh] overflow-y-auto shadow-2xl rounded-t-2xl sm:rounded-2xl">

        <!-- Handle mobile -->
        <div class="flex justify-center pt-3 pb-1 sm:hidden">
          <div class="w-10 h-1 bg-zinc-700 rounded-full"></div>
        </div>

        <!-- Header -->
        <div class="flex items-center gap-4 p-5 border-b border-zinc-800">
          <img v-if="lojaDetalhe.logo_url" :src="lojaDetalhe.logo_url"
               class="w-14 h-14 rounded-xl object-cover flex-shrink-0" />
          <div v-else class="w-14 h-14 rounded-xl bg-zinc-800 flex items-center justify-center flex-shrink-0">
            <span class="text-2xl font-bold text-zinc-400">{{ lojaDetalhe.nome.charAt(0) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <h2 class="text-base font-bold text-zinc-100">{{ lojaDetalhe.nome }}</h2>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', estadoInfo(lojaDetalhe).classe]">
                {{ estadoInfo(lojaDetalhe).label }}
              </span>
            </div>
            <p class="text-xs text-zinc-500">{{ lojaDetalhe.categoria }} · {{ lojaDetalhe.localizacao || 'Sem localização' }}</p>
            <p class="text-xs text-zinc-600 mt-0.5">Dono: {{ lojaDetalhe.dono.username }}</p>
            <p v-if="lojaDetalhe.estado_motivo" class="text-xs text-zinc-500 mt-0.5">Motivo: {{ lojaDetalhe.estado_motivo }}</p>
          </div>
          <button @click="lojaDetalhe = null"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-5 space-y-5">
          <!-- KPIs -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div v-for="kpi in kpisDetalhe" :key="kpi.label"
                 class="bg-zinc-800 rounded-xl p-3 text-center">
              <p class="text-lg font-extrabold" :class="kpi.color">{{ kpi.valor }}</p>
              <p class="text-[10px] text-zinc-500 mt-0.5">{{ kpi.label }}</p>
            </div>
          </div>

          <!-- Comissões -->
          <div v-if="loadingDetalhe" class="flex justify-center py-4">
            <svg class="animate-spin h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
          </div>

          <template v-else-if="detalheComissoes">
            <div class="bg-zinc-800/60 rounded-xl p-4 space-y-3">
              <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Comissões</h3>
              <div class="grid grid-cols-3 gap-3">
                <div class="text-center">
                  <p class="text-base font-bold text-zinc-100">{{ detalheComissoes.total }}</p>
                  <p class="text-[10px] text-zinc-500">Total</p>
                </div>
                <div class="text-center">
                  <p class="text-base font-bold text-yellow-400">{{ $dinheiro(detalheComissoes.pendente) }}</p>
                  <p class="text-[10px] text-zinc-500">Pendente</p>
                </div>
                <div class="text-center">
                  <p class="text-base font-bold text-green-400">{{ $dinheiro(detalheComissoes.liquidada) }}</p>
                  <p class="text-[10px] text-zinc-500">Liquidado</p>
                </div>
              </div>
            </div>

            <div v-if="detalheComissoes.recentes?.length > 0">
              <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">Últimas comissões</h3>
              <div class="space-y-2">
                <div v-for="c in detalheComissoes.recentes" :key="c.id"
                     class="flex items-center justify-between px-3 py-2 bg-zinc-800/50 rounded-lg">
                  <div>
                    <p class="text-xs text-zinc-300">Encomenda #{{ c.encomenda_id }}</p>
                    <p class="text-[10px] text-zinc-500">{{ c.data_criacao }} · {{ c.percentagem }}%</p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs font-bold text-red-400">{{ $dinheiro(c.valor_comissao) }}</p>
                    <span :class="['text-[10px] font-bold', c.status === 'liquidada' ? 'text-green-400' : 'text-yellow-400']">
                      {{ c.status }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- Acções -->
          <div class="flex flex-col sm:flex-row gap-3 pt-2 border-t border-zinc-800">
            <button v-for="a in acoesDisponiveis(lojaDetalhe)" :key="a" @click="executarAcao(lojaDetalhe, a)"
              :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition', ACOES[a].classe]">
              {{ ACOES[a].label }} loja
            </button>
            <p v-if="lojaDetalhe.estado === 'fechada'" class="flex-1 py-2.5 text-xs text-zinc-500 text-center self-center">
              Fechada pelo dono — só o dono a pode reabrir.
            </p>
            <a :href="`/loja/${lojaDetalhe.id}`" target="_blank"
              class="flex-1 py-2.5 rounded-xl text-sm font-bold bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition text-center">
              Ver loja pública <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="ml-1" />
            </a>
          </div>

          <!-- Exportar dados (super-admin) -->
          <div v-if="podeExportar" class="rounded-xl border border-zinc-800 p-4 space-y-3" data-teste="admin-exportar-loja">
            <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider">
              <font-awesome-icon :icon="['fas', 'file-zipper']" class="mr-1.5" />Exportar dados
            </h3>
            <ExportacoesLoja :base="`/app/admin/lojas/${lojaDetalhe.id}/exportacoes/`" />
          </div>

          <!-- Eliminar definitivamente -->
          <div class="rounded-xl border border-red-500/20 p-4 space-y-3">
            <h3 class="text-xs font-bold text-red-400 uppercase tracking-wider">
              <font-awesome-icon :icon="['fas', 'trash']" class="mr-1.5" />Eliminar definitivamente
            </h3>
            <p v-if="!eliminacao" class="text-xs text-zinc-500">A verificar…</p>
            <template v-else-if="!eliminacao.pode">
              <p class="text-xs text-zinc-400">Esta loja não pode ser eliminada:</p>
              <ul class="text-xs text-zinc-500 list-disc pl-5 space-y-0.5">
                <li v-for="r in eliminacao.razoes" :key="r">{{ r }}</li>
              </ul>
              <p class="text-[11px] text-zinc-600">Registos financeiros (encomendas, pagamentos, comissões, vendas POS) nunca são apagados — suspende a loja em vez disso.</p>
            </template>
            <template v-else>
              <p class="text-xs text-zinc-400">
                Apaga a loja, produtos, categorias e staff. Os ficheiros (logo, banner, imagens, vídeos)
                são removidos em segundo plano. <b class="text-red-400">Não pode ser desfeito.</b>
              </p>
              <input v-model="confirmacaoNome" :placeholder="`Escreve «${lojaDetalhe.nome}» para confirmar`"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
              <button @click="eliminarLoja(lojaDetalhe)" :disabled="confirmacaoNome.trim() !== lojaDetalhe.nome || aEliminar"
                class="w-full py-2.5 rounded-xl text-sm font-bold transition bg-red-600 hover:bg-red-500 text-white disabled:opacity-40 disabled:cursor-not-allowed">
                {{ aEliminar ? 'A eliminar…' : 'Eliminar definitivamente' }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'
import ExportacoesLoja from '@/components/ExportacoesLoja.vue'

// estados da loja (backend: Loja.estado)
const ESTADOS = {
  pendente: { label: 'Pendente', plural: 'Pendentes', classe: 'bg-yellow-500/15 text-yellow-400' },
  ativa:    { label: 'Activa',   plural: 'Activas',   classe: 'bg-green-500/15 text-green-400' },
  fechada:  { label: 'Fechada',  plural: 'Fechadas pelo dono', classe: 'bg-zinc-700 text-zinc-300' },
  suspensa: { label: 'Suspensa', plural: 'Suspensas', classe: 'bg-red-500/15 text-red-400' },
}
// acções do admin (backend: PATCH /app/admin/lojas/<id>/ { acao, motivo })
const ACOES = {
  aprovar:   { label: 'Aprovar',   origens: ['pendente'],           classe: 'bg-green-500/15 text-green-400 hover:bg-green-500/25' },
  rejeitar:  { label: 'Rejeitar',  origens: ['pendente'],           classe: 'bg-red-500/15 text-red-400 hover:bg-red-500/25', motivo: true },
  suspender: { label: 'Suspender', origens: ['ativa', 'fechada'],   classe: 'bg-red-500/15 text-red-400 hover:bg-red-500/25', motivo: true },
  reativar:  { label: 'Reactivar', origens: ['suspensa'],           classe: 'bg-green-500/15 text-green-400 hover:bg-green-500/25' },
}

export default {
  name: 'AdminLojas',
  components: { ExportacoesLoja },
  props: {
    podeExportar: { type: Boolean, default: false },   // permissão exportar_lojas (super-admin)
  },
  data () {
    return {
      ESTADOS, ACOES,
      eliminacao: null, confirmacaoNome: '', aEliminar: false,
      loading: true, lojas: [], totalCount: 0,
      page: 1, limit: 20,
      q: '', filtroEstado: '', filtroCategoria: '',
      debounceTimer: null,
      lojaDetalhe: null,
      categorias: [],
      loadingDetalhe: false,
      detalheComissoes: null,
    }
  },
  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
    kpisDetalhe () {
      if (!this.lojaDetalhe) return []
      return [
        { label: 'Produtos',   valor: this.lojaDetalhe.total_produtos,       color: 'text-zinc-100'  },
        { label: 'Encomendas', valor: this.lojaDetalhe.total_encomendas,     color: 'text-blue-400'  },
        { label: 'Comissão',   valor: `${this.lojaDetalhe._comissao_edit}%`, color: 'text-red-400'   },
        { label: 'Desde',      valor: this.lojaDetalhe.data_criacao?.split(' ')[0] || '—', color: 'text-zinc-400' },
      ]
    },
  },
  async created () { await this.fetchLojas() },
  methods: {
    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchLojas(1), 350)
    },
    async fetchLojas (pagina = this.page) {
      this.page = pagina; this.loading = true
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.q) params.q = this.q
        if (this.filtroEstado) params.estado = this.filtroEstado
        if (this.filtroCategoria) params.categoria = this.filtroCategoria
        const { data } = await api.get('/app/admin/lojas/', { params })
        this.lojas = (data.results || data).map(l => ({ ...l, _comissao_edit: l.percentagem_comissao ?? 10 }))
        this.totalCount = data.count ?? this.lojas.length
        if (pagina === 1 && !this.filtroCategoria && !this.filtroEstado && !this.q) {
          const cats = [...new Set(this.lojas.map(l => l.categoria).filter(Boolean))]
          if (cats.length > this.categorias.length) this.categorias = cats
        }
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    estadoInfo (loja) {
      return ESTADOS[loja.estado] || (loja.ativa ? ESTADOS.ativa : ESTADOS.pendente)
    },
    acoesDisponiveis (loja) {
      return Object.keys(ACOES).filter(a => ACOES[a].origens.includes(loja.estado))
    },
    acaoRapida (loja) {
      return ({ pendente: 'aprovar', ativa: 'suspender', suspensa: 'reativar' })[loja.estado] || null
    },
    async executarAcao (loja, acao) {
      const cfg = ACOES[acao]
      let motivo = ''
      if (cfg.motivo) {
        const aviso = acao === 'suspender' && loja.encomendas_pendentes
          ? `\n\nAtenção: ${loja.encomendas_pendentes} encomenda(s) ainda por pagar vão ser canceladas (stock reposto, clientes avisados).`
          : ''
        motivo = window.prompt(`${cfg.label} "${loja.nome}" — motivo (o dono vai vê-lo):${aviso}`, '')
        if (motivo === null) return          // cancelou
      } else if (!confirm(`${cfg.label} a loja "${loja.nome}"?`)) {
        return
      }
      // POS vinculado: suspender/reactivar também é uma escolha explícita (por defeito não)
      const posAlvo = (loja.pos_vinculados || []).filter(p => acao === 'suspender' ? !p.suspenso : acao === 'reativar' && p.suspenso)
      let incluirPos = false
      if (posAlvo.length) {
        const nomes = posAlvo.map(p => p.nome).join(', ')
        incluirPos = confirm(acao === 'suspender'
          ? `Suspender também o POS vinculado (${nomes})?\n\nOK = suspende o POS por inteiro.\nCancelar = o POS continua a funcionar só com os produtos próprios (os da loja ficam indisponíveis).`
          : `Reactivar também o POS vinculado (${nomes}), que está suspenso?`)
      }
      try {
        const { data } = await api.patch(`/app/admin/lojas/${loja.id}/`, { acao, motivo, incluir_pos: incluirPos })
        Object.assign(loja, { ativa: data.ativa, estado: data.estado, estado_motivo: data.estado_motivo })
        if (data.encomendas_canceladas) loja.encomendas_pendentes = 0
        if (data.pos_alterados?.length) posAlvo.forEach(p => { p.suspenso = acao === 'suspender' })
        if (this.lojaDetalhe?.id === loja.id) this.verificarEliminacao(loja)
      } catch (e) {
        alert(e.response?.data?.detail || 'Não foi possível alterar o estado da loja.')
      }
    },
    async verificarEliminacao (loja) {
      this.eliminacao = null
      this.confirmacaoNome = ''
      try {
        const { data } = await api.get(`/app/admin/lojas/${loja.id}/eliminar/`)
        this.eliminacao = data
      } catch (e) {
        this.eliminacao = { pode: false, razoes: ['não foi possível verificar'] }
      }
    },
    async eliminarLoja (loja) {
      this.aEliminar = true
      try {
        await api.delete(`/app/admin/lojas/${loja.id}/eliminar/`, { data: { confirmacao: this.confirmacaoNome.trim() } })
        this.lojaDetalhe = null
        await this.fetchLojas()
      } catch (e) {
        const d = e.response?.data
        alert([d?.detail || 'Não foi possível eliminar a loja.', ...(d?.razoes || [])].join('\n• '))
        this.verificarEliminacao(loja)
      } finally { this.aEliminar = false }
    },
    async guardarComissao (loja) {
      try {
        await api.patch(`/app/admin/lojas/${loja.id}/comissao/editar/`, { percentagem_comissao: loja._comissao_edit })
      } catch (e) { console.error(e) }
    },
    async abrirDetalhe (loja) {
      this.lojaDetalhe = loja
      this.verificarEliminacao(loja)
      this.detalheComissoes = null
      this.loadingDetalhe = true
      try {
        const { data } = await api.get('/app/admin/comissoes/', { params: { loja_id: loja.id, limit: 5 } })
        const items = data.results || data
        this.detalheComissoes = {
          total:     data.count ?? items.length,
          pendente:  parseFloat(items.filter(c => c.status === 'pendente').reduce((s, c) => s + parseFloat(c.valor_comissao), 0)).toFixed(2),
          liquidada: parseFloat(items.filter(c => c.status === 'liquidada').reduce((s, c) => s + parseFloat(c.valor_comissao), 0)).toFixed(2),
          recentes:  items.slice(0, 5),
        }
      } catch (e) { console.error(e) }
      finally { this.loadingDetalhe = false }
    },
  },
}
</script>