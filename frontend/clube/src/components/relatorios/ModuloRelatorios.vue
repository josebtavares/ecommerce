<template>
  <div class="space-y-5">

    <!-- Catálogo: lista de escolha no telemóvel, cartões a partir de tablet -->
    <label class="sm:hidden flex flex-col gap-1">
      <span class="text-[10px] text-zinc-500 uppercase tracking-wider">Relatório</span>
      <select :value="atual?.id" @change="escolher(catalogo.find(r => r.id === $event.target.value))"
              class="px-3 py-2.5 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
        <optgroup v-for="g in grupos" :key="g.nome" :label="g.nome">
          <option v-for="r in g.itens" :key="r.id" :value="r.id">{{ r.titulo }}</option>
        </optgroup>
      </select>
    </label>
    <div class="hidden sm:block space-y-3">
      <div v-for="g in grupos" :key="g.nome">
        <p class="text-[11px] font-bold text-zinc-500 uppercase tracking-wider mb-2">{{ g.nome }}</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-2">
          <button v-for="r in g.itens" :key="r.id" type="button" @click="escolher(r)"
                  :class="['text-left rounded-xl border p-3 transition',
                           atual?.id === r.id ? 'border-red-500/60 bg-red-500/10' : 'border-zinc-800 bg-zinc-900 hover:border-zinc-700']">
            <p class="text-sm font-semibold" :class="atual?.id === r.id ? 'text-red-300' : 'text-zinc-200'">{{ r.titulo }}</p>
            <p class="text-[11px] text-zinc-500 mt-0.5 leading-snug line-clamp-2">{{ r.descricao }}</p>
          </button>
        </div>
      </div>
    </div>
    <p v-if="erroCatalogo" class="text-sm text-red-400">{{ erroCatalogo }}</p>

    <template v-if="atual">
      <!-- Filtros -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-4">
        <div v-if="atual.sem_periodo" class="flex flex-wrap items-center justify-between gap-3">
          <p class="text-sm text-zinc-400"><font-awesome-icon :icon="['fas', 'camera']" class="mr-1.5 text-zinc-500" />Situação de hoje (o período não se aplica)</p>
          <div class="flex gap-1.5">
            <button v-for="f in FORMATOS" :key="f.id" type="button" @click="exportar(f.id)" :disabled="!!aExportar || !dados"
                    class="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-semibold rounded-xl transition flex items-center gap-2 disabled:opacity-50">
              <font-awesome-icon :icon="['fas', aExportar === f.id ? 'spinner' : f.icon]" :class="aExportar === f.id ? 'animate-spin' : f.cor" />
              {{ f.label }}
            </button>
          </div>
        </div>
        <FiltroPeriodo v-else :padrao="atual.max_dias > 400 ? 'ano' : 'mes'" :key="atual.id" :carregando="carregando" @mudar="mudarPeriodo">
          <div class="flex gap-1.5">
            <button v-for="f in FORMATOS" :key="f.id" type="button" @click="exportar(f.id)" :disabled="!!aExportar || !dados"
                    class="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-semibold rounded-xl transition flex items-center gap-2 disabled:opacity-50">
              <font-awesome-icon :icon="['fas', aExportar === f.id ? 'spinner' : f.icon]" :class="aExportar === f.id ? 'animate-spin' : f.cor" />
              {{ f.label }}
            </button>
          </div>
        </FiltroPeriodo>

        <div v-if="atual.filtros.length" class="flex flex-wrap gap-3 items-end">
          <label v-for="f in atual.filtros" :key="f.nome" class="flex flex-col gap-1 min-w-[150px]">
            <span class="text-[10px] text-zinc-500 uppercase tracking-wider">{{ f.label }}</span>
            <select v-if="f.tipo === 'select'" v-model="valores[f.nome]" @change="carregar(0)"
                    class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500 max-w-[260px]">
              <option v-if="f.todos" value="">{{ f.todos }}</option>
              <option v-for="o in f.opcoes" :key="o.valor" :value="o.valor">{{ o.label }}</option>
            </select>
            <input v-else v-model="valores[f.nome]" @input="carregarDepois" :placeholder="f.placeholder || ''" maxlength="80"
                   class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
          </label>
          <button v-if="temFiltros" type="button" @click="limparFiltros" class="text-xs text-zinc-500 hover:text-zinc-300 pb-2">Limpar filtros</button>
        </div>
        <p class="text-[11px] text-zinc-600">
          {{ atual.descricao }}<template v-if="!atual.sem_periodo"> Período até {{ atual.max_dias > 400 ? '10 anos' : '1 ano' }}.</template>
        </p>
      </div>

      <p v-if="erro" class="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">{{ erro }}</p>

      <div v-if="carregando && !dados" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div v-for="n in 4" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
      </div>

      <template v-if="dados">
        <!-- Resumo -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" :class="carregando ? 'opacity-60' : ''">
          <div v-for="r in dados.resumo" :key="r.label" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 min-w-0">
            <p class="text-[11px] text-zinc-500 leading-tight">{{ r.label }}</p>
            <p class="text-lg sm:text-xl font-extrabold text-zinc-100 tabular-nums mt-1 break-words">{{ fmt(r.valor, r.tipo) || '—' }}</p>
          </div>
        </div>

        <!-- Tabela -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800" :class="carregando ? 'opacity-60' : ''">
          <div class="flex items-center justify-between gap-3 px-4 py-3 border-b border-zinc-800 flex-wrap">
            <p class="text-sm font-bold text-zinc-300">{{ dados.relatorio.titulo }}
              <span class="text-zinc-500 font-normal">· {{ dados.total_linhas }} {{ dados.total_linhas === 1 ? 'linha' : 'linhas' }}</span>
            </p>
            <p class="text-xs text-zinc-500">{{ dados.relatorio.sem_periodo ? 'Hoje' : `${dataCurta(dados.periodo.inicio)} a ${dataCurta(dados.periodo.fim)}` }}</p>
          </div>
          <div v-if="!dados.linhas.length" class="px-4 py-10 text-center text-sm text-zinc-600">Sem resultados para estes filtros.</div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead class="bg-zinc-800/50 text-zinc-400">
                <tr>
                  <th v-for="c in dados.colunas" :key="c.chave"
                      :class="['px-3 py-2 font-semibold whitespace-nowrap', NUMERICOS.includes(c.tipo) ? 'text-right' : 'text-left']">{{ c.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(l, i) in dados.linhas" :key="i" class="border-t border-zinc-800/80 text-zinc-300 hover:bg-zinc-800/30">
                  <td v-for="c in dados.colunas" :key="c.chave"
                      :class="['px-3 py-2', NUMERICOS.includes(c.tipo) ? 'text-right tabular-nums whitespace-nowrap' : '',
                               ['data', 'datahora', 'mes'].includes(c.tipo) ? 'whitespace-nowrap' : '']">{{ fmt(l[c.chave], c.tipo) }}</td>
                </tr>
              </tbody>
              <tfoot v-if="Object.keys(dados.totais).length">
                <tr class="border-t-2 border-zinc-700 bg-zinc-800/40 text-zinc-100 font-bold">
                  <td v-for="(c, i) in dados.colunas" :key="c.chave"
                      :class="['px-3 py-2', NUMERICOS.includes(c.tipo) ? 'text-right tabular-nums whitespace-nowrap' : '']">
                    {{ i === 0 ? 'Total' : (c.chave in dados.totais ? fmt(dados.totais[c.chave], c.tipo) : '') }}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
          <!-- paginação -->
          <div v-if="dados.total_linhas > dados.limit" class="flex items-center justify-between gap-3 px-4 py-3 border-t border-zinc-800 text-xs text-zinc-400">
            <span>{{ dados.offset + 1 }}–{{ Math.min(dados.offset + dados.limit, dados.total_linhas) }} de {{ dados.total_linhas }} · os totais são de todas as linhas</span>
            <div class="flex gap-1">
              <button type="button" :disabled="dados.offset === 0 || carregando" @click="carregar(dados.offset - dados.limit)"
                      class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40">Anterior</button>
              <button type="button" :disabled="dados.offset + dados.limit >= dados.total_linhas || carregando" @click="carregar(dados.offset + dados.limit)"
                      class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40">Seguinte</button>
            </div>
          </div>
        </div>

        <div class="text-[11px] text-zinc-500 space-y-1 leading-relaxed">
          <p v-if="dados.truncado" class="text-amber-400">O relatório tem demasiadas linhas: reduz o período ou usa mais filtros.</p>
          <p v-for="n in dados.notas" :key="n">{{ n }}</p>
          <p>Documento de apoio à contabilidade. Não é um documento fiscal.</p>
        </div>
      </template>
    </template>

    <!-- Exportações recentes -->
    <div v-if="historico" class="bg-zinc-900 rounded-2xl border border-zinc-800">
      <button type="button" @click="abrirHistorico" class="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-zinc-300">
        <span><font-awesome-icon :icon="['fas', 'clock-rotate-left']" class="mr-2 text-zinc-500" />Exportações recentes</span>
        <font-awesome-icon :icon="['fas', verHistorico ? 'chevron-up' : 'chevron-down']" class="text-zinc-500" />
      </button>
      <div v-if="verHistorico" class="border-t border-zinc-800 overflow-x-auto">
        <p v-if="!listaHistorico.length" class="px-4 py-6 text-sm text-zinc-600">Ainda não há exportações.</p>
        <table v-else class="w-full text-xs">
          <thead class="text-zinc-500">
            <tr><th class="text-left px-4 py-2 font-semibold">Quando</th><th class="text-left px-4 py-2 font-semibold">Relatório</th>
              <th class="text-left px-4 py-2 font-semibold">Período</th><th class="text-left px-4 py-2 font-semibold">Formato</th>
              <th class="text-right px-4 py-2 font-semibold">Linhas</th><th class="text-left px-4 py-2 font-semibold">Por</th></tr>
          </thead>
          <tbody>
            <tr v-for="h in listaHistorico" :key="h.id" class="border-t border-zinc-800/80 text-zinc-300">
              <td class="px-4 py-2 whitespace-nowrap">{{ agoraCurto(h.data) }}</td>
              <td class="px-4 py-2">{{ h.titulo }}</td>
              <td class="px-4 py-2 whitespace-nowrap">{{ h.sem_periodo ? '—' : `${dataCurta(h.inicio)} a ${dataCurta(h.fim)}` }}</td>
              <td class="px-4 py-2 uppercase">{{ h.formato }}</td>
              <td class="px-4 py-2 text-right tabular-nums">{{ h.linhas }}</td>
              <td class="px-4 py-2">{{ h.por }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
// Módulo de relatórios (admin e loja): escolhe-se um relatório do catálogo, os filtros, e vê-se o resumo e as
// linhas (paginadas). As exportações (CSV, Excel, PDF) são geradas no servidor com todas as linhas.
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/services/api'
import FiltroPeriodo from '@/components/relatorios/FiltroPeriodo.vue'
import { dataCurta, intervaloAtalho } from '@/utils/periodos'
import { formatarCelula as fmt, NUMERICOS, nomeFicheiro, agoraCurto } from '@/utils/relatorios'

const props = defineProps({
  base:     { type: String, required: true },          // '/app/admin/relatorios' ou '/app/loja/7/relatorios'
  prefixo:  { type: String, default: 'bendi' },        // nome dos ficheiros
  historico:{ type: Boolean, default: true },
})

const FORMATOS = [
  { id: 'xlsx', label: 'Excel', icon: 'file-excel', cor: 'text-green-400' },
  { id: 'pdf',  label: 'PDF',   icon: 'file-pdf',   cor: 'text-red-400' },
  { id: 'csv',  label: 'CSV',   icon: 'file-csv',   cor: 'text-sky-400' },
]

const catalogo = ref([])
const erroCatalogo = ref('')
const atual = ref(null)
const valores = reactive({})
const periodo = ref(intervaloAtalho('mes'))
const dados = ref(null)
const erro = ref('')
const carregando = ref(false)
const aExportar = ref('')
const verHistorico = ref(false)
const listaHistorico = ref([])

const grupos = computed(() => {
  const g = {}
  for (const r of catalogo.value) (g[r.grupo] ||= []).push(r)
  return Object.entries(g).map(([nome, itens]) => ({ nome, itens }))
})
const temFiltros = computed(() => atual.value?.filtros.some(f => f.todos && valores[f.nome]) || false)

function parametros (extra = {}) {
  const p = { data_inicio: periodo.value.inicio, data_fim: periodo.value.fim, ...extra }
  for (const [k, v] of Object.entries(valores)) if (v) p[k] = v
  return p
}

function escolher (r) {
  if (atual.value?.id === r.id) return
  atual.value = r
  for (const k of Object.keys(valores)) delete valores[k]
  // filtros sem "todos" (ex.: "Contar pela data") começam na primeira opção
  for (const f of r.filtros) valores[f.nome] = f.tipo === 'select' && !f.todos ? f.opcoes[0]?.valor : ''
  periodo.value = intervaloAtalho(r.max_dias > 400 ? 'ano' : 'mes')
  dados.value = null
  carregar(0)
}

function mudarPeriodo (p) { periodo.value = p; carregar(0) }

function limparFiltros () {
  for (const f of atual.value.filtros) if (f.todos) valores[f.nome] = ''
  carregar(0)
}

let pedido = 0
async function carregar (offset = 0) {
  if (!atual.value) return
  const meu = ++pedido
  carregando.value = true
  erro.value = ''
  try {
    const { data } = await api.get(`${props.base}/r/${atual.value.id}/`, { params: parametros({ offset, limit: 50 }) })
    if (meu === pedido) dados.value = data
  } catch (e) {
    if (meu === pedido) { erro.value = e.response?.data?.detail || 'Não foi possível gerar o relatório.'; dados.value = null }
  } finally {
    if (meu === pedido) carregando.value = false
  }
}

let espera = null
function carregarDepois () { clearTimeout(espera); espera = setTimeout(() => carregar(0), 400) }

async function exportar (formato) {
  aExportar.value = formato
  erro.value = ''
  try {
    const resp = await api.get(`${props.base}/r/${atual.value.id}/exportar/`, { params: parametros({ formato }), responseType: 'blob' })
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = nomeFicheiro(props.prefixo, atual.value.id, periodo.value.inicio, periodo.value.fim, formato)
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 2000)
    if (verHistorico.value) carregarHistorico()
  } catch (e) {
    let msg = 'Não foi possível exportar.'
    try { msg = JSON.parse(await e.response.data.text()).detail || msg } catch { /* resposta sem JSON */ }
    erro.value = msg
  } finally { aExportar.value = '' }
}

async function carregarHistorico () {
  try { listaHistorico.value = (await api.get(`${props.base}/historico/`)).data } catch { listaHistorico.value = [] }
}
function abrirHistorico () {
  verHistorico.value = !verHistorico.value
  if (verHistorico.value) carregarHistorico()
}

onMounted(async () => {
  try {
    catalogo.value = (await api.get(`${props.base}/catalogo/`)).data.relatorios
    if (catalogo.value.length) escolher(catalogo.value[0])
  } catch (e) {
    erroCatalogo.value = e.response?.data?.detail || 'Não foi possível carregar os relatórios.'
  }
})
</script>
