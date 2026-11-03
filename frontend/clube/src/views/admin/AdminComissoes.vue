<template>
  <div class="space-y-5">

    <!-- ══ SUMÁRIO DE TOTAIS ══ -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Por receber</p>
        <p class="text-xl font-extrabold text-yellow-400">{{ $dinheiro(totalPendente) }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Pagas</p>
        <p class="text-xl font-extrabold text-green-400">{{ $dinheiro(totalLiquidado) }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Total comissões</p>
        <p class="text-xl font-extrabold text-zinc-100">{{ totalCount }}</p>
      </div>
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4"
           title="Comissão a devolver às lojas: reembolsos de encomendas cuja comissão já estava liquidada">
        <p class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Créditos às lojas</p>
        <p class="text-xl font-extrabold text-sky-400">{{ $dinheiro(totalCreditos) }}</p>
      </div>
    </div>

    <!-- ══ CRÉDITOS DA LOJA (reembolsos depois de liquidar) ══ -->
    <div v-if="lojaSelecionada && Number(lojaSelecionada.credito) > 0"
         class="rounded-2xl border border-sky-500/30 bg-sky-500/5 p-4 flex flex-col sm:flex-row sm:items-center gap-3">
      <div class="flex-1 text-sm text-sky-100">
        <p class="font-semibold">{{ lojaSelecionada.nome }} tem {{ $dinheiro(lojaSelecionada.credito) }} de créditos por descontar.</p>
        <p class="text-xs text-sky-200/70 mt-0.5">
          São comissões de encomendas reembolsadas depois de a comissão já estar paga. Descontam-se sozinhos na próxima
          cobrança mensal: a loja paga {{ $dinheiro(liquidoLoja) }} ({{ $dinheiro(lojaSelecionada.pendente) }} por cobrar − créditos).
          Só os marques à mão se já acertaste com a loja por fora.
        </p>
      </div>
      <button type="button" @click="descontarCreditos" :disabled="aDescontar"
        class="px-4 py-2 rounded-xl text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 flex-shrink-0">
        Marcar créditos como descontados
      </button>
    </div>

    <!-- ══ COBRANÇAS MENSAIS (a loja paga as comissões à parte: a SISP não divide pagamentos) ══ -->
    <AdminCobrancasComissoes :loja-id="filtroLoja" :versao="versao" @alterado="recarregar" />

    <!-- ══ ABAS DE LOJAS ══ -->
    <div v-if="lojas.length > 0"
         class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      <button @click="selectLoja(null)"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === null
                   ? 'bg-red-600 text-white'
                   : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        Todas as lojas
      </button>
      <button v-for="loja in lojas" :key="loja.id"
        @click="selectLoja(loja.id)"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                 filtroLoja === loja.id
                   ? 'bg-red-600 text-white'
                   : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700']">
        {{ loja.nome }}
        <span v-if="loja.pendente" class="ml-1.5 px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-[9px] font-bold">
          {{ $dinheiro(loja.pendente) }}
        </span>
        <span v-if="Number(loja.credito) > 0" title="Créditos por descontar" class="ml-1 px-1.5 py-0.5 bg-sky-500/20 text-sky-400 rounded text-[9px] font-bold">
          −{{ $dinheiro(loja.credito) }}
        </span>
      </button>
    </div>

    <!-- ══ FILTROS ══ -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 space-y-3">
      <div class="flex flex-wrap gap-3">

        <!-- Status -->
        <div class="flex gap-1">
          <button v-for="s in statusOpcoes" :key="s.value" :data-teste="`comissoes-filtro-${s.value || 'todas'}`"
            @click="filtroStatus = s.value; fetchComissoes(1)"
            :class="['px-3 py-2 rounded-xl text-xs font-semibold transition border',
                     filtroStatus === s.value
                       ? s.activeClass
                       : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:text-zinc-200']">
            {{ s.label }}
          </button>
        </div>

        <!-- Data início -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-zinc-500 whitespace-nowrap">De</label>
          <input v-model="filtroDataInicio" @change="atalhoActivo = null; fetchComissoes(1)" type="date"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200
                   focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Data fim -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-zinc-500 whitespace-nowrap">Até</label>
          <input v-model="filtroDataFim" @change="atalhoActivo = null; fetchComissoes(1)" type="date"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200
                   focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Atalhos de datas -->
        <div class="flex gap-1 flex-wrap">
          <button v-for="atalho in atalhosData" :key="atalho.label"
            @click="aplicarAtalho(atalho)"
            :class="['px-2.5 py-1.5 rounded-lg text-[10px] font-semibold transition border',
                     atalhoActivo === atalho.label
                       ? 'bg-red-600/20 border-red-500/50 text-red-400'
                       : 'border-zinc-700 text-zinc-500 hover:text-zinc-200 hover:border-zinc-500']">
            {{ atalho.label }}
          </button>
        </div>

        <!-- Mínimo de comissão -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-zinc-500 whitespace-nowrap">Mín. (CVE)</label>
          <input v-model="filtroMin" @input="debouncedFetch" type="number" min="0" step="1" placeholder="0"
            class="w-24 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200
                   focus:outline-none focus:border-red-500 transition" />
        </div>

        <!-- Ordenação -->
        <select v-model="filtroOrdem" @change="fetchComissoes(1)"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-300
                 focus:outline-none focus:border-red-500 transition cursor-pointer">
          <option value="-data_criacao">Criação mais recente</option>
          <option value="data_criacao">Criação mais antiga</option>
          <option value="-data_liquidacao">Liquidação mais recente</option>
          <option value="data_liquidacao">Liquidação mais antiga</option>
          <option value="-valor_comissao">Maior comissão</option>
          <option value="valor_comissao">Menor comissão</option>
        </select>

        <!-- Itens por página -->
        <select v-model="limit" @change="fetchComissoes(1)"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-300
                 focus:outline-none focus:border-red-500 transition cursor-pointer">
          <option :value="15">15 / pág.</option>
          <option :value="20">20 / pág.</option>
          <option :value="50">50 / pág.</option>
        </select>

        <!-- Limpar filtros -->
        <button v-if="temFiltrosActivos" @click="limparFiltros"
          class="px-3 py-2 rounded-xl text-xs font-semibold text-red-400 hover:text-red-300
                 bg-red-500/10 hover:bg-red-500/20 transition flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Limpar
        </button>
      </div>

      <!-- Indicador de filtros activos -->
      <div v-if="temFiltrosActivos" class="flex flex-wrap gap-2">
        <span v-if="filtroLoja"
              class="flex items-center gap-1 px-2 py-0.5 bg-red-600/15 text-red-400 text-[10px] rounded-lg border border-red-500/30">
          {{ lojaLabel(filtroLoja) }}
          <button @click="selectLoja(null)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroStatus && filtroStatus !== ''"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          {{ statusOpcoes.find(s => s.value === filtroStatus)?.label }}
          <button @click="filtroStatus = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroDataInicio"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          De {{ filtroDataInicio }}
          <button @click="filtroDataInicio = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroDataFim"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          Até {{ filtroDataFim }}
          <button @click="filtroDataFim = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
        <span v-if="filtroMin"
              class="flex items-center gap-1 px-2 py-0.5 bg-zinc-700 text-zinc-300 text-[10px] rounded-lg">
          Mín. {{ $dinheiro(filtroMin) }}
          <button @click="filtroMin = ''; fetchComissoes(1)" class="hover:text-white">×</button>
        </span>
      </div>
    </div>

    <!-- ══ ANULAR (superadmin): comissões registadas por engano ou em testes — deixam de contar, nunca se apagam ══ -->
    <div v-if="souSuperadmin && anular" class="rounded-2xl border border-red-500/30 bg-red-500/5 p-4 space-y-3" data-teste="anular-form">
      <p class="text-sm text-red-100 font-semibold">
        <template v-if="anular.c">Anular a comissão #{{ anular.c.id }} ({{ anular.c.loja_nome }}, {{ $dinheiro(anular.c.valor_comissao) }})?</template>
        <template v-else>Anular todas as comissões por cobrar{{ filtroLoja ? ` de ${lojaLabel(filtroLoja)}` : ' de todas as lojas' }}?</template>
      </p>
      <p class="text-xs text-red-200/70">Deixam de contar nos totais, nas cobranças, nos extratos, no Dashboard e nos Relatórios.
        Não se apagam: ficam na lista "Anuladas" e no registo, com o motivo. As que já estão numa cobrança não são anuladas
        (anula primeiro a cobrança).</p>
      <input v-model="anular.motivo" maxlength="300" placeholder="Motivo (obrigatório)" data-teste="anular-motivo"
        class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
      <div class="flex flex-wrap gap-2">
        <button type="button" @click="confirmarAnular" :disabled="anular.aGuardar || anular.motivo.trim().length < 5" data-teste="anular-confirmar"
          class="px-4 py-2 rounded-xl text-xs font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50">
          {{ anular.aGuardar ? 'A anular…' : 'Anular' }}
        </button>
        <button type="button" @click="anular = null" class="px-4 py-2 rounded-xl text-xs font-bold text-zinc-300 bg-zinc-800 hover:bg-zinc-700">Cancelar</button>
      </div>
      <p v-if="anular.erro" class="text-xs text-red-400" role="alert">{{ anular.erro }}</p>
    </div>
    <p v-if="msgAnular" class="text-xs text-green-400" role="status" data-teste="anular-msg">{{ msgAnular }}</p>

    <!-- Resultado -->
    <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500">
      <span>{{ totalCount }} {{ totalCount === 1 ? 'comissão encontrada' : 'comissões encontradas' }}</span>
      <button v-if="souSuperadmin && Number(totalPorCobrarFiltro) > 0 && !anular" type="button" @click="abrirAnular(null)" data-teste="anular-todas"
        class="px-3 py-1.5 rounded-lg text-xs font-semibold text-red-400 bg-red-500/10 hover:bg-red-500/20">
        Anular por cobrar{{ filtroLoja ? ` (${lojaLabel(filtroLoja)})` : '' }}…
      </button>
      <span v-if="totalCount > 0">Página {{ page }} de {{ totalPages }}</span>
    </div>

    <!-- ══ LOADING ══ -->
    <div v-if="loading && !comissoes.length" class="space-y-2">
      <div v-for="n in limit" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse border border-zinc-800"></div>
    </div>

    <!-- ══ LISTA ══ -->
    <div v-else-if="comissoes.length" class="space-y-2" data-teste="lista-comissoes">
      <div v-for="c in comissoes" :key="c.id" :data-teste="`comissao-${c.id}`"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 hover:border-zinc-700 transition">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <p class="text-sm font-semibold text-zinc-200 truncate">{{ c.loja_nome }}</p>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', ESTADOS[c.status]?.cor]" data-teste="comissao-estado">
                {{ ESTADOS[c.status]?.nome || c.status }}
              </span>
              <span v-if="c.cobranca" class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-zinc-800 text-zinc-400"
                    title="Cobrança mensal em que entrou">
                Cobrança {{ mesCurto(c.cobranca.mes) }} · {{ c.cobranca.estado_nome }}
              </span>
              <span v-else-if="c.status === 'pendente'" class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-zinc-800 text-zinc-500"
                    title="Entra na próxima cobrança mensal">por cobrar</span>
            </div>
            <p class="text-xs text-zinc-500">
              Encomenda #{{ c.encomenda_id }}
              <span class="mx-1 text-zinc-700">·</span>
              Valor {{ $dinheiro(c.valor_encomenda) }}
              <span class="mx-1 text-zinc-700">·</span>
              Taxa {{ c.percentagem }}%
            </p>
            <p class="text-[10px] text-zinc-600 mt-0.5">{{ formatarData(c.data_criacao) }}</p>
            <p v-if="c.data_liquidacao" class="text-[10px] text-green-600 mt-0.5">
              <font-awesome-icon :icon="['fas', 'check']" /> Paga em {{ formatarData(c.data_liquidacao) }}
            </p>
            <p v-if="c.anulada_em" class="text-[10px] text-zinc-500 mt-0.5">Anulada em {{ formatarData(c.anulada_em) }} · {{ ultimaNota(c.notas) }}</p>
          </div>
          <div class="flex flex-col items-end gap-2 flex-shrink-0">
            <p :class="['text-lg font-extrabold', c.status === 'anulada' ? 'text-zinc-500 line-through' : 'text-red-400']">{{ $dinheiro(c.valor_comissao) }}</p>
            <button v-if="souSuperadmin && c.status === 'pendente' && !c.cobranca" type="button" @click="abrirAnular(c)"
              :data-teste="`comissao-anular-${c.id}`"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-400 hover:text-red-300 hover:bg-red-500/10 text-xs font-semibold transition">
              Anular
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading"
         class="text-center py-14 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto mb-3 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
      Nenhuma comissão encontrada.
      <br/>
      <button v-if="temFiltrosActivos" @click="limparFiltros" class="text-red-400 hover:text-red-300 mt-2 text-xs">
        Limpar filtros →
      </button>
    </div>

    <!-- ══ PAGINAÇÃO ══ -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, totalCount) }} de {{ totalCount }}
      </p>
      <div class="flex items-center gap-1.5">
        <button @click="fetchComissoes(1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30 text-xs text-zinc-400">
          «
        </button>
        <button @click="fetchComissoes(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="fetchComissoes(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="fetchComissoes(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button @click="fetchComissoes(totalPages)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30 text-xs text-zinc-400">
          »
        </button>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'
import AdminCobrancasComissoes from '@/components/admin/AdminCobrancasComissoes.vue'
import { ouvirSubscricoes } from '@/utils/tempoRealEncomendas'

const ESTADOS = {
  pendente:  { nome: 'Pendente',  cor: 'bg-yellow-500/15 text-yellow-400' },
  liquidada: { nome: 'Paga',      cor: 'bg-green-500/15 text-green-400' },
  anulada:   { nome: 'Anulada',   cor: 'bg-zinc-700 text-zinc-400' },
}
// avisos das subscrições que mexem nesta página (comissões, créditos, cobranças; null = recarregar tudo)
const TIPOS = ['comissao', 'credito_comissao', 'cobranca_comissoes', 'fatura_comissoes']

export default {
  name: 'AdminComissoes',

  components: { AdminCobrancasComissoes },

  data () {
    const eu = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      ESTADOS,
      souSuperadmin: eu.role_admin === 'superadmin',
      anular: null,          // { c: comissão | null (todas por cobrar do filtro), motivo, aGuardar, erro }
      msgAnular: '',
      versao: 0,             // muda → as cobranças voltam a ler (tempo real)
      pedido: 0,
      loading: true,
      comissoes: [],
      totalCount: 0,
      page: 1,
      limit: 20,           // 20 por defeito

      // filtros
      filtroStatus:     '',
      filtroLoja:       null,
      filtroDataInicio: '',
      filtroDataFim:    '',
      filtroMin:        '',
      filtroOrdem:      '-data_criacao',

      // totais
      totalPendente:  '0.00',
      totalLiquidado: '0.00',
      totalCreditos:  '0.00',
      aDescontar:     false,

      // lojas para as abas
      lojas: [],

      // estado
      debounceTimer: null,
      atalhoActivo: null,

      statusOpcoes: [
        { value: '',         label: 'Todas',     activeClass: 'bg-zinc-700 border-zinc-600 text-zinc-200' },
        { value: 'pendente', label: 'Pendentes', activeClass: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400' },
        { value: 'liquidada',label: 'Pagas',     activeClass: 'bg-green-500/20 border-green-500/50 text-green-400' },
        { value: 'anulada',  label: 'Anuladas',  activeClass: 'bg-zinc-700 border-zinc-500 text-zinc-200' },
      ],

      atalhosData: [
        { label: 'Hoje',       dias: 0  },
        { label: 'Esta semana',dias: 7  },
        { label: 'Este mês',   dias: 30 },
        { label: '3 meses',    dias: 90 },
      ],
    }
  },

  computed: {
    totalPages () { return Math.ceil(this.totalCount / this.limit) },

    lojaSelecionada () { return this.lojas.find(l => l.id === this.filtroLoja) || null },
    // há comissões por cobrar (pendentes) no filtro de loja → mostra "Anular por cobrar…"
    totalPorCobrarFiltro () { return this.filtroLoja ? (this.lojaSelecionada?.pendente || 0) : this.totalPendente },
    liquidoLoja () {
      const l = this.lojaSelecionada
      return l ? Number(l.pendente) - Number(l.credito) : 0
    },

    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },

    temFiltrosActivos () {
      return this.filtroLoja || this.filtroStatus ||
             this.filtroDataInicio || this.filtroDataFim || this.filtroMin
    },
  },

  async created () {
    this.pararTempoReal = ouvirSubscricoes(() => this.atualizarEmTempoReal(),
      { filtro: a => !a || !a.tipo || TIPOS.includes(a.tipo), espera: 600 })
    await this.recarregar()
  },

  beforeUnmount () { this.pararTempoReal?.() },

  methods: {
    recarregar () { return Promise.all([this.fetchLojas(), this.fetchComissoes(this.page)]) },

    // outra sessão (ou uma venda nova, um reembolso, a loja a pagar) mexeu nas comissões: sem esqueleto nem saltos
    atualizarEmTempoReal () {
      this.versao++
      return Promise.all([this.fetchLojas(), this.fetchComissoes(this.page, true)])
    },

    mesCurto (iso) { const [a, m] = iso.split('-'); return `${m}/${a}` },
    ultimaNota (n) { return (n || '').split('\n').filter(Boolean).pop() || '' },

    abrirAnular (c) { this.anular = { c, motivo: '', aGuardar: false, erro: '' }; this.msgAnular = '' },

    async confirmarAnular () {
      const a = this.anular
      a.aGuardar = true; a.erro = ''
      const corpo = a.c ? { ids: [a.c.id] } : { todas_pendentes: true, ...(this.filtroLoja ? { loja_id: this.filtroLoja } : {}) }
      try {
        const { data } = await api.post('/app/admin/comissoes/anular/', { ...corpo, motivo: a.motivo })
        this.anular = null
        this.msgAnular = data.anuladas === 1 ? '1 comissão anulada.' : `${data.anuladas} comissões anuladas.`
        await this.recarregar()
      } catch (e) {
        a.erro = e.response?.data?.detail || 'Não foi possível anular.'
      } finally { a.aGuardar = false }
    },

    async fetchComissoes (pagina = this.page, silencioso = false) {
      this.page = pagina
      if (!silencioso) this.loading = true
      const pedido = ++this.pedido
      try {
        const params = {
          offset:   (this.page - 1) * this.limit,
          limit:    this.limit,
          ordering: this.filtroOrdem,
        }
        if (this.filtroStatus)     params.status       = this.filtroStatus
        if (this.filtroLoja)       params.loja_id      = this.filtroLoja
        if (this.filtroDataInicio) params.data_inicio  = this.filtroDataInicio
        if (this.filtroDataFim)    params.data_fim     = this.filtroDataFim
        if (this.filtroMin)        params.valor_min    = this.filtroMin

        const { data } = await api.get('/app/admin/comissoes/', { params })
        if (pedido !== this.pedido) return          // entretanto pediu-se outra página/filtro
        this.comissoes      = data.results || data
        this.totalCount     = data.count           ?? this.comissoes.length
        this.totalPendente  = data.total_pendente  || '0.00'
        this.totalLiquidado = data.total_liquidado || '0.00'
        this.totalCreditos  = data.total_creditos  || '0.00'
      } catch (e) { console.error(e) }
      finally { if (pedido === this.pedido) this.loading = false }
    },

    async fetchLojas () {
      try {
        // Busca sumário de comissões por loja para mostrar pendentes nas abas
        const { data } = await api.get('/app/admin/comissoes/por-loja/')
        this.lojas = data
      } catch (e) {
        // fallback: sem abas se o endpoint não existir ainda
        this.lojas = []
      }
    },

    selectLoja (id) {
      this.filtroLoja = id
      this.fetchComissoes(1)
    },

    lojaLabel (id) {
      return this.lojas.find(l => l.id === id)?.nome || `Loja #${id}`
    },

    aplicarAtalho (atalho) {
      this.atalhoActivo = atalho.label
      const hoje = new Date()
      const inicio = new Date()
      if (atalho.dias === 0) {
        this.filtroDataInicio = this.formatarDateInput(hoje)
        this.filtroDataFim    = this.formatarDateInput(hoje)
      } else {
        inicio.setDate(hoje.getDate() - atalho.dias)
        this.filtroDataInicio = this.formatarDateInput(inicio)
        this.filtroDataFim    = this.formatarDateInput(hoje)
      }
      this.fetchComissoes(1)
    },

    formatarDateInput (d) {
      return d.toISOString().split('T')[0]
    },

    formatarData (str) {
      if (!str || str === 'null' || str === 'undefined') return ''
      // Backend envia "20-04-2026 11:10" (DD-MM-YYYY HH:MM) → converter para ISO
      const m = str.match(/(\d{2})-(\d{2})-(\d{4})\s+(\d{2}):(\d{2})/)
      if (!m) return str
      const d = new Date(`${m[3]}-${m[2]}-${m[1]}T${m[4]}:${m[5]}`)
      if (isNaN(d.getTime())) return str
      return d.toLocaleDateString('pt-PT', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      })
    },

    debouncedFetch () {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.fetchComissoes(1), 400)
    },

    limparFiltros () {
      this.filtroStatus     = ''
      this.filtroLoja       = null
      this.filtroDataInicio = ''
      this.filtroDataFim    = ''
      this.filtroMin        = ''
      this.filtroOrdem      = '-data_criacao'
      this.atalhoActivo     = null
      this.fetchComissoes(1)
    },

    async descontarCreditos () {
      const l = this.lojaSelecionada
      if (!l || !confirm(`Marcar os créditos de ${l.nome} (${this.$dinheiro(l.credito)}) como descontados nesta liquidação?`)) return
      this.aDescontar = true
      try {
        await api.post('/app/admin/comissoes/creditos/descontar/', { loja_id: l.id })
        await Promise.all([this.fetchLojas(), this.fetchComissoes(this.page)])
      } catch (e) {
        alert(e.response?.data?.detail || 'Não foi possível descontar os créditos.')
      } finally { this.aDescontar = false }
    },

  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>