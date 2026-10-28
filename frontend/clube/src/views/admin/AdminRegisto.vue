<!-- AdminRegisto.vue — Admin → Registo: o registo das transações (backend utils/registo.py).
     Só de leitura: ninguém o altera nem apaga (nem pela base de dados). "Verificar integridade" refaz
     a cadeia de hashes; "Exportar CSV" leva os filtros actuais. -->
<template>
  <div class="space-y-5" data-teste="admin-registo">
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 sm:p-5 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-start gap-3">
        <div class="flex-1 min-w-0">
          <h2 class="text-sm font-bold text-zinc-200">Registo das transações</h2>
          <p class="text-xs text-zinc-500 mt-0.5">
            Pagamentos de encomendas, reembolsos, marcações pagas, faturas de subscrição e dados bancários das lojas.
            Cada linha fica ligada à anterior e não se pode alterar nem apagar — é a prova em disputas e auditorias.
          </p>
        </div>
        <div class="flex gap-2 flex-shrink-0">
          <button type="button" @click="verificar" :disabled="aVerificar" data-teste="registo-verificar"
            class="px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-bold transition disabled:opacity-50">
            <font-awesome-icon :icon="['fas', 'shield-halved']" class="mr-1.5" />{{ aVerificar ? 'A verificar…' : 'Verificar integridade' }}
          </button>
          <button type="button" @click="exportar" :disabled="aExportar" data-teste="registo-exportar"
            class="px-3 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition disabled:opacity-50">
            <font-awesome-icon :icon="['fas', 'download']" class="mr-1.5" />{{ aExportar ? 'A exportar…' : 'Exportar CSV' }}
          </button>
        </div>
      </div>
      <p v-if="verificacao" data-teste="registo-verificacao"
         :class="['text-xs rounded-lg px-3 py-2 border', verificacao.ok ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400']">
        <template v-if="verificacao.ok">Íntegro — {{ verificacao.total }} linha(s) verificada(s), nenhuma alterada ou em falta.<template
          v-if="verificacao.por_selar"> {{ verificacao.por_selar }} linha(s) ainda por ligar à cadeia (transações em curso).</template></template>
        <template v-else>Problema na linha #{{ verificacao.primeiro_erro.id }}: {{ verificacao.primeiro_erro.motivo }}.</template>
      </p>

      <!-- filtros -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <select v-model="f.tipo" @change="carregar(true)" aria-label="Tipo"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todos os tipos</option>
          <option v-for="t in tipos" :key="t.valor" :value="t.valor">{{ t.label }}</option>
        </select>
        <input v-model.trim="f.loja" @change="carregar(true)" inputmode="numeric" placeholder="Loja (id)" aria-label="Loja (id)"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none" />
        <input v-model.trim="f.encomenda" @change="carregar(true)" inputmode="numeric" placeholder="Encomenda (id)" aria-label="Encomenda (id)"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none" />
        <input v-model="f.de" @change="carregar(true)" type="date" aria-label="De"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none" />
        <input v-model="f.ate" @change="carregar(true)" type="date" aria-label="Até"
          class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-300 focus:outline-none" />
        <button type="button" @click="limpar" class="px-3 py-2 rounded-xl text-xs font-semibold text-zinc-400 hover:text-zinc-200 bg-zinc-800/50">
          Limpar filtros
        </button>
      </div>
    </div>

    <p v-if="erro" class="text-sm text-red-400">{{ erro }}</p>
    <div v-if="carregando && !linhas.length" class="space-y-2">
      <div v-for="n in 6" :key="n" class="h-14 bg-zinc-900 rounded-xl animate-pulse"></div>
    </div>
    <p v-else-if="!linhas.length" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      Nada no registo com estes filtros.
    </p>

    <template v-else>
      <p class="text-xs text-zinc-500">{{ total }} linha(s)</p>
      <div class="space-y-2">
        <div v-for="r in linhas" :key="r.id" data-teste="registo-linha"
             class="bg-zinc-900 rounded-xl border border-zinc-800 px-4 py-3 text-sm">
          <button type="button" class="w-full flex flex-wrap items-center gap-x-3 gap-y-1 text-left" @click="aberta = aberta === r.id ? null : r.id">
            <span class="text-[11px] text-zinc-500 tabular-nums w-36 flex-shrink-0">{{ r.quando }}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-300">{{ r.tipo_label }}</span>
            <span class="font-semibold text-zinc-100">{{ r.evento.replace(/_/g, ' ') }}</span>
            <span v-if="r.estado_anterior || r.estado_novo" class="text-xs text-zinc-500">
              {{ r.estado_anterior || '—' }} → {{ r.estado_novo || '—' }}
            </span>
            <span v-if="r.valor !== null" class="text-xs font-bold text-zinc-200 tabular-nums">{{ $dinheiro(r.valor) }}</span>
            <span class="ml-auto text-xs text-zinc-500 truncate">
              {{ r.loja_id ? 'loja ' + r.loja_id : '' }}{{ r.encomenda_id ? ' · enc. ' + r.encomenda_id : '' }} · {{ r.ator }}
            </span>
          </button>
          <dl v-if="aberta === r.id" class="mt-3 pt-3 border-t border-zinc-800 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-xs">
            <template v-for="(v, k) in detalhe(r)" :key="k">
              <div class="flex gap-2 min-w-0"><dt class="text-zinc-500 flex-shrink-0">{{ k }}</dt><dd class="text-zinc-300 break-all">{{ v }}</dd></div>
            </template>
          </dl>
        </div>
      </div>
      <button v-if="proximo !== null" type="button" @click="carregar(false)" :disabled="carregando"
        class="w-full py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-semibold transition disabled:opacity-50">
        {{ carregando ? 'A carregar…' : 'Ver mais' }}
      </button>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { descarregarPdf } from '@/utils/documentos'

const VAZIO = () => ({ tipo: '', loja: '', encomenda: '', de: '', ate: '' })

export default {
  name: 'AdminRegisto',

  data () {
    return {
      f: VAZIO(), linhas: [], total: 0, proximo: null, tipos: [], carregando: false, erro: '',
      aberta: null, verificacao: null, aVerificar: false, aExportar: false,
    }
  },

  created () { this.carregar(true) },

  methods: {
    params () {
      return Object.fromEntries(Object.entries(this.f).filter(([, v]) => v))
    },

    async carregar (doZero) {
      this.carregando = true; this.erro = ''
      try {
        const offset = doZero ? 0 : this.proximo
        const { data } = await api.get('/app/admin/registo/', { params: { ...this.params(), offset, limit: 50 } })
        this.linhas = doZero ? data.results : [...this.linhas, ...data.results]
        this.total = data.count
        this.proximo = data.next_offset
        this.tipos = data.tipos
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar o registo.'
      } finally { this.carregando = false }
    },

    limpar () { this.f = VAZIO(); this.carregar(true) },

    detalhe (r) {
      const d = {
        'Linha': '#' + r.id, 'N.º na cadeia': r.seq ?? 'por selar', 'Quando (UTC)': r.criado_em, 'Objeto': r.objeto_id ?? '—', 'POS': r.pos_id ?? '—',
        'Método': r.metodo || '—', 'Referência': r.referencia || '—', 'Quem': r.ator, 'IP': r.ip || '—',
        'Pedido': r.pedido_id || '—',
      }
      for (const [k, v] of Object.entries(r.dados || {})) d[k] = v || '—'
      d['Hash do conteúdo'] = r.hash_conteudo
      d['Hash anterior'] = r.hash_anterior || '—'
      d.Hash = r.hash || 'por selar'
      return d
    },

    async verificar () {
      this.aVerificar = true
      try {
        const { data } = await api.get('/app/admin/registo/verificar/')
        this.verificacao = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível verificar.'
      } finally { this.aVerificar = false }
    },

    async exportar () {
      this.aExportar = true
      try {
        await descarregarPdf('/app/admin/registo/exportar/', `registo-transacoes-${new Date().toISOString().slice(0, 10)}.csv`, this.params())
      } catch { this.erro = 'Não foi possível exportar.' } finally { this.aExportar = false }
    },
  },
}
</script>
