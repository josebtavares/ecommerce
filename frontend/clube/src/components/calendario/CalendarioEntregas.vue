<template>
  <!-- Backoffice → Entregas → Calendário (GET /app/loja/<id>/entrega/calendario/).
       Cada encomenda aparece na hora agendada ou, sem agendamento, no dia em que foi feita.
       Dono/gestor vêem tudo e atribuem condutores; o condutor só vê as suas e muda o estado. -->
  <div class="space-y-4">
    <!-- Barra -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="flex items-center gap-1">
        <button type="button" @click="mover(-1)" aria-label="Anterior"
          class="w-9 h-9 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 flex items-center justify-center">
          <font-awesome-icon :icon="['fas', 'chevron-left']" />
        </button>
        <button type="button" @click="irHoje"
          class="h-9 px-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">Hoje</button>
        <button type="button" @click="mover(1)" aria-label="Seguinte"
          class="w-9 h-9 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 flex items-center justify-center">
          <font-awesome-icon :icon="['fas', 'chevron-right']" />
        </button>
      </div>
      <h3 class="text-base font-bold text-zinc-100 mr-auto capitalize" aria-live="polite">{{ titulo }}</h3>

      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1" role="tablist" aria-label="Vista">
        <button v-for="v in VISTAS" :key="v.key" type="button" role="tab" :aria-selected="vista === v.key ? 'true' : 'false'"
          @click="vista = v.key"
          :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition', vista === v.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ v.label }}
        </button>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <select v-if="!isCondutor" v-model="tipo" aria-label="Tipo"
        class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-300 focus:outline-none focus:border-red-500">
        <option value="">Entregas e levantamentos</option>
        <option value="entrega">Só entregas</option>
        <option value="levantamento">Só levantamentos</option>
      </select>
      <label class="inline-flex items-center gap-2 text-xs text-zinc-400 cursor-pointer select-none">
        <input type="checkbox" v-model="soAgendadas" class="accent-red-600" /> Só agendadas
      </label>
      <div class="ml-auto flex flex-wrap items-center gap-3 text-[11px] text-zinc-500">
        <span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-sky-400"></span>Agendada pelo cliente</span>
        <span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400"></span>Para a abertura</span>
        <span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-zinc-500"></span>O mais cedo possível</span>
      </div>
    </div>

    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
    <p v-if="truncado" class="text-xs text-amber-400">Há demasiadas encomendas neste período — mostram-se as primeiras 2000.</p>

    <div :class="['relative', carregando && 'opacity-60 pointer-events-none']">
      <!-- ═══ MÊS ═══ -->
      <div v-if="vista === 'mes'" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">
        <div class="grid grid-cols-7 border-b border-zinc-800">
          <div v-for="d in DIAS_CURTOS" :key="d" class="px-2 py-2 text-[11px] font-bold text-zinc-500 uppercase text-center">{{ d }}</div>
        </div>
        <div class="grid grid-cols-7">
          <div v-for="c in celulasMes" :key="c.data"
               :class="['min-h-[64px] sm:min-h-[104px] border-b border-r border-zinc-800 p-1 sm:p-1.5 flex flex-col gap-1',
                        c.foraDoMes && 'bg-zinc-950/40']">
            <button type="button" @click="abrirDia(c.data)" :aria-label="`Ver dia ${c.data}`"
              :class="['self-start text-xs font-semibold w-6 h-6 rounded-full flex items-center justify-center',
                       c.data === hoje ? 'bg-red-600 text-white' : c.foraDoMes ? 'text-zinc-600' : 'text-zinc-300 hover:bg-zinc-800']">
              {{ Number(c.data.slice(8)) }}
            </button>
            <!-- telemóvel: só o número -->
            <button v-if="porDia[c.data]?.length" type="button" @click="abrirDia(c.data)"
              class="sm:hidden text-[10px] font-bold rounded-md bg-zinc-800 text-zinc-200 px-1 py-0.5">
              {{ porDia[c.data].length }}
            </button>
            <template v-for="(e, n) in porDia[c.data] || []" :key="e.encomenda_id">
              <button v-if="n < 3" type="button" @click="detalhe = e"
                :class="['hidden sm:flex items-center gap-1 text-left text-[11px] rounded-md px-1.5 py-0.5 truncate border-l-2', corItem(e)]">
                <span class="font-semibold">{{ e.hora }}</span><span class="truncate">#{{ e.encomenda_id }} {{ e.cliente }}</span>
              </button>
            </template>
            <button v-if="(porDia[c.data]?.length || 0) > 3" type="button" @click="abrirDia(c.data)"
              class="hidden sm:block text-left text-[11px] font-semibold text-zinc-400 hover:text-zinc-200 px-1.5">
              + {{ porDia[c.data].length - 3 }} mais
            </button>
          </div>
        </div>
      </div>

      <!-- ═══ SEMANA ═══ -->
      <div v-else-if="vista === 'semana'" class="grid gap-2 lg:grid-cols-7">
        <div v-for="d in diasSemana" :key="d"
             :class="['bg-zinc-900 rounded-2xl border p-2 lg:min-h-[320px]', d === hoje ? 'border-red-500/50' : 'border-zinc-800']">
          <button type="button" @click="abrirDia(d)" class="w-full text-left px-1 pb-2 mb-2 border-b border-zinc-800">
            <span class="text-[11px] font-bold uppercase text-zinc-500">{{ DIAS_CURTOS[diaSemana(d)] }}</span>
            <span :class="['ml-1 text-sm font-bold', d === hoje ? 'text-red-400' : 'text-zinc-200']">{{ d.slice(8) }}/{{ d.slice(5, 7) }}</span>
            <span v-if="porDia[d]?.length" class="ml-1 text-[11px] text-zinc-500">· {{ porDia[d].length }}</span>
          </button>
          <p v-if="!porDia[d]?.length" class="text-[11px] text-zinc-600 px-1">Sem encomendas</p>
          <div class="space-y-1.5">
            <button v-for="e in porDia[d] || []" :key="e.encomenda_id" type="button" @click="detalhe = e"
              :class="['w-full text-left rounded-lg px-2 py-1.5 border-l-2 text-xs', corItem(e)]">
              <span class="flex items-center justify-between gap-1">
                <span class="font-bold">{{ e.hora }}</span>
                <font-awesome-icon :icon="['fas', e.tipo_entrega === 'entrega' ? 'truck' : 'store']" class="opacity-70" />
              </span>
              <span class="block truncate">#{{ e.encomenda_id }} · {{ e.cliente }}</span>
              <span v-if="e.entrega" class="block truncate opacity-70">{{ ESTADO_ENTREGA[e.entrega.status] }}{{ e.entrega.condutor_nome ? ' · ' + e.entrega.condutor_nome : '' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ═══ DIA ═══ -->
      <div v-else-if="vista === 'dia'" class="space-y-2">
        <p v-if="!porDia[ref]?.length && !carregando"
           class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">Sem encomendas neste dia.</p>
        <button v-for="e in porDia[ref] || []" :key="e.encomenda_id" type="button" @click="detalhe = e"
          :class="['w-full text-left bg-zinc-900 rounded-2xl border border-zinc-800 border-l-4 p-4 flex gap-4 hover:bg-zinc-800/40', borda(e)]">
          <div class="w-14 flex-shrink-0">
            <p class="text-lg font-black text-zinc-100 leading-none">{{ e.hora }}</p>
            <p class="text-[10px] text-zinc-500 mt-1">{{ e.agendada ? (e.origem === 'cliente' ? 'agendada' : 'abertura') : 'feita' }}</p>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-zinc-200">
              #{{ e.encomenda_id }} · {{ e.cliente }}
              <span :class="['ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase', corEstado(e.status)]">{{ e.status }}</span>
            </p>
            <p class="text-xs text-zinc-400 mt-0.5">
              <font-awesome-icon :icon="['fas', e.tipo_entrega === 'entrega' ? 'truck' : 'store']" class="mr-1" />
              {{ e.tipo_entrega === 'entrega' ? (e.morada || 'Entrega') : 'Levantamento na loja' }}
            </p>
            <p class="text-xs text-zinc-500 mt-0.5 truncate">{{ e.itens }}</p>
            <p v-if="e.entrega" class="text-xs text-zinc-400 mt-1">
              {{ ESTADO_ENTREGA[e.entrega.status] }}{{ e.entrega.condutor_nome ? ' · ' + e.entrega.condutor_nome : ' · sem condutor' }}
            </p>
            <p v-else-if="e.tipo_entrega === 'entrega'" class="text-xs text-amber-400 mt-1">Sem condutor atribuído</p>
          </div>
          <span class="text-sm font-bold text-red-400 flex-shrink-0">{{ dinheiro(e.valor_total) }}</span>
        </button>
      </div>

      <!-- ═══ ANO ═══ -->
      <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="m in mesesAno" :key="m.chave" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3">
          <button type="button" @click="abrirMes(m.chave)" class="text-sm font-bold text-zinc-200 hover:text-white capitalize mb-2">
            {{ m.nome }} <span v-if="m.total" class="text-xs font-semibold text-zinc-500">· {{ m.total }}</span>
          </button>
          <div class="grid grid-cols-7 gap-0.5">
            <span v-for="d in DIAS_CURTOS" :key="d" class="text-[9px] text-zinc-600 text-center">{{ d[0] }}</span>
            <span v-for="n in m.vazios" :key="'v' + n"></span>
            <button v-for="d in m.dias" :key="d" type="button" @click="abrirDia(d)"
              :title="`${d.slice(8)}/${d.slice(5, 7)}: ${resumo[d] || 0} encomenda(s)`"
              :aria-label="`${d}: ${resumo[d] || 0} encomendas`"
              :class="['aspect-square rounded text-[9px] flex items-center justify-center', intensidade(resumo[d]),
                       d === hoje && 'ring-1 ring-red-500']">
              {{ Number(d.slice(8)) }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Detalhe ═══ -->
    <div v-if="detalhe" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="detalhe = null">
      <div class="bg-zinc-900 border border-zinc-800 w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5 max-h-[90vh] overflow-y-auto" role="dialog"
           :aria-label="`Encomenda #${detalhe.encomenda_id}`">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div>
            <p class="text-xs text-zinc-500">{{ dataLonga(detalhe.data) }} · {{ detalhe.hora }}</p>
            <h4 class="text-lg font-bold text-zinc-100">Encomenda #{{ detalhe.encomenda_id }}</h4>
          </div>
          <button type="button" @click="detalhe = null" aria-label="Fechar"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-lg leading-none">×</button>
        </div>
        <p :class="['text-xs font-semibold rounded-lg px-3 py-2 mb-3', detalhe.origem === 'cliente' ? 'bg-sky-500/10 text-sky-300' : detalhe.agendada ? 'bg-amber-500/10 text-amber-300' : 'bg-zinc-800 text-zinc-400']">
          {{ detalhe.origem === 'cliente' ? 'O cliente escolheu esta hora' : detalhe.agendada ? 'Feita com a loja fechada — preparar a partir desta hora' : 'Sem agendamento — feita a esta hora, o mais cedo possível' }}
        </p>
        <dl class="text-sm space-y-2">
          <div class="flex justify-between gap-3"><dt class="text-zinc-500">Cliente</dt><dd class="text-zinc-200 text-right">{{ detalhe.cliente }}</dd></div>
          <div v-if="detalhe.telefone" class="flex justify-between gap-3"><dt class="text-zinc-500">Telefone</dt>
            <dd><a :href="`tel:${detalhe.telefone}`" class="text-red-400 hover:text-red-300">{{ detalhe.telefone }}</a></dd></div>
          <div class="flex justify-between gap-3"><dt class="text-zinc-500">Tipo</dt>
            <dd class="text-zinc-200 text-right">{{ detalhe.tipo_entrega === 'entrega' ? 'Entrega ao domicílio' : 'Levantamento na loja' }}</dd></div>
          <div v-if="detalhe.morada" class="flex justify-between gap-3"><dt class="text-zinc-500">Morada</dt><dd class="text-zinc-200 text-right">{{ detalhe.morada }}</dd></div>
          <div class="flex justify-between gap-3"><dt class="text-zinc-500">Itens</dt><dd class="text-zinc-200 text-right">{{ detalhe.itens }}</dd></div>
          <div v-if="detalhe.notas" class="flex justify-between gap-3"><dt class="text-zinc-500">Notas</dt><dd class="text-zinc-200 text-right">{{ detalhe.notas }}</dd></div>
          <div class="flex justify-between gap-3"><dt class="text-zinc-500">Total</dt><dd class="text-red-400 font-bold">{{ dinheiro(detalhe.valor_total) }}</dd></div>
          <div v-if="detalhe.valor_a_pagar && Number(detalhe.valor_a_pagar) !== Number(detalhe.valor_total)" class="flex justify-between gap-3">
            <dt class="text-zinc-500">A cobrar (sem esgotados)</dt><dd class="text-amber-300 font-bold">{{ dinheiro(detalhe.valor_a_pagar) }}</dd>
          </div>
          <div class="flex justify-between gap-3"><dt class="text-zinc-500">Encomenda</dt>
            <dd><span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', corEstado(detalhe.status)]">{{ detalhe.status }}</span></dd></div>
          <div v-if="detalhe.entrega" class="flex justify-between gap-3"><dt class="text-zinc-500">Entrega</dt>
            <dd class="text-zinc-200 text-right">{{ ESTADO_ENTREGA[detalhe.entrega.status] }} · {{ detalhe.entrega.condutor_nome || 'sem condutor' }}</dd></div>
        </dl>

        <!-- Acções -->
        <div class="mt-5 space-y-2">
          <template v-if="detalhe.entrega && ['atribuido', 'a_caminho'].includes(detalhe.entrega.status) && (!isCondutor || detalhe.entrega.condutor_id)">
            <div class="flex flex-wrap gap-2">
              <button v-if="detalhe.entrega.status === 'atribuido'" type="button" @click="mudarEntrega('a_caminho')" :disabled="aGuardar"
                class="px-3 py-2 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 text-xs font-semibold">
                <font-awesome-icon :icon="['fas', 'car']" class="mr-1" />A caminho
              </button>
              <button type="button" @click="confirmando = 'entregue'" :disabled="aGuardar"
                class="px-3 py-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-300 text-xs font-semibold">
                <font-awesome-icon :icon="['fas', 'check']" class="mr-1" />{{ isCondutor ? 'Marcar entregue' : 'Concluir entrega' }}
              </button>
              <button type="button" @click="confirmando = 'falhou'" :disabled="aGuardar"
                class="px-3 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs font-semibold">
                <font-awesome-icon :icon="['fas', 'xmark']" class="mr-1" />{{ isCondutor ? 'Não consegui entregar' : 'Entrega falhou' }}
              </button>
            </div>
          </template>
          <!-- dono/gestor: atribuir ou trocar o condutor -->
          <div v-if="!isCondutor && podeAtribuir(detalhe)" class="flex gap-2">
            <select v-model="condutorId" aria-label="Condutor"
              class="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500">
              <option :value="null" disabled>{{ condutores.length ? 'Escolhe o condutor' : 'Sem condutores — adiciona em Condutores' }}</option>
              <option v-for="c in condutores" :key="c.id" :value="c.id">{{ c.utilizador_nome || c.utilizador_username }}</option>
            </select>
            <button type="button" @click="atribuir" :disabled="!condutorId || aGuardar"
              class="px-3 py-2 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-xs font-bold">
              {{ detalhe.entrega?.condutor_id ? 'Trocar' : 'Atribuir' }}
            </button>
          </div>
          <p v-if="erroAcao" class="text-xs text-red-400" role="alert">{{ erroAcao }}</p>
        </div>
      </div>
    </div>

    <ConfirmarEntrega v-if="confirmando && detalhe" :falhou="confirmando === 'falhou'" :encomenda-id="detalhe.encomenda_id"
      :a-cobrar="detalhe.valor_a_pagar" :is-condutor="isCondutor" :a-guardar="aGuardar"
      @fechar="confirmando = ''" @confirmar="mudarEntrega(confirmando, $event)" />
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import ConfirmarEntrega from './ConfirmarEntrega.vue'

const DIAS_CURTOS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
const VISTAS = [{ key: 'dia', label: 'Dia' }, { key: 'semana', label: 'Semana' }, { key: 'mes', label: 'Mês' }, { key: 'ano', label: 'Ano' }]
const ESTADO_ENTREGA = { atribuido: 'Atribuída', a_caminho: 'A caminho', entregue: 'Entregue', falhou: 'Falhou', cancelada: 'Cancelada' }

// datas como 'AAAA-MM-DD' (dia no fuso da plataforma, vindo da API) — contas em UTC para não mudar de dia
const D = s => new Date(s + 'T00:00:00Z')
const S = d => d.toISOString().slice(0, 10)
const mais = (s, n) => { const d = D(s); d.setUTCDate(d.getUTCDate() + n); return S(d) }
const diaSemana = s => (D(s).getUTCDay() + 6) % 7          // 0 = segunda
const segunda = s => mais(s, -diaSemana(s))
const inicioMes = s => s.slice(0, 8) + '01'
const fimMes = s => { const d = D(inicioMes(s)); d.setUTCMonth(d.getUTCMonth() + 1); d.setUTCDate(0); return S(d) }

export default {
  name: 'CalendarioEntregas',
  components: { ConfirmarEntrega },
  props: {
    lojaId:     { type: [String, Number], required: true },
    isCondutor: { type: Boolean, default: false },
    condutores: { type: Array, default: () => [] },
  },

  data () {
    const hoje = S(new Date())
    return {
      DIAS_CURTOS, VISTAS, ESTADO_ENTREGA,
      vista: window.innerWidth < 640 ? 'dia' : 'mes',
      hoje, ref: hoje, tipo: '', soAgendadas: false,
      itens: [], resumo: {}, truncado: false, carregando: false, erro: '',
      detalhe: null, condutorId: null, aGuardar: false, erroAcao: '', confirmando: '',
    }
  },

  computed: {
    intervalo () {
      if (this.vista === 'dia') return [this.ref, this.ref]
      if (this.vista === 'semana') return [segunda(this.ref), mais(segunda(this.ref), 6)]
      if (this.vista === 'mes') return [segunda(inicioMes(this.ref)), mais(segunda(fimMes(this.ref)), 6)]
      return [this.ref.slice(0, 4) + '-01-01', this.ref.slice(0, 4) + '-12-31']
    },
    titulo () {
      const r = this.ref
      if (this.vista === 'dia') return this.dataLonga(r)
      if (this.vista === 'semana') {
        const [a, b] = this.intervalo
        return `${a.slice(8)}/${a.slice(5, 7)} – ${b.slice(8)}/${b.slice(5, 7)}/${b.slice(0, 4)}`
      }
      if (this.vista === 'mes') return `${MESES[Number(r.slice(5, 7)) - 1]} ${r.slice(0, 4)}`
      return r.slice(0, 4)
    },
    porDia () {
      const m = {}
      this.itens.forEach(e => { (m[e.data] = m[e.data] || []).push(e) })
      return m
    },
    celulasMes () {
      const [a, b] = this.intervalo
      const mes = this.ref.slice(0, 7)
      const out = []
      for (let d = a; d <= b; d = mais(d, 1)) out.push({ data: d, foraDoMes: d.slice(0, 7) !== mes })
      return out
    },
    diasSemana () { return Array.from({ length: 7 }, (_, i) => mais(this.intervalo[0], i)) },
    mesesAno () {
      const ano = this.ref.slice(0, 4)
      return MESES.map((nome, i) => {
        const ini = `${ano}-${String(i + 1).padStart(2, '0')}-01`
        const dias = []
        for (let d = ini; d <= fimMes(ini); d = mais(d, 1)) dias.push(d)
        return { chave: ini, nome, dias, vazios: diaSemana(ini), total: dias.reduce((s, d) => s + (this.resumo[d] || 0), 0) }
      })
    },
  },

  watch: {
    intervalo () { this.carregar() },
    tipo () { this.carregar() },
    soAgendadas () { this.carregar() },
    detalhe (e) { this.condutorId = e?.entrega?.condutor_id || null; this.erroAcao = '' },
  },

  created () { this.carregar() },

  methods: {
    diaSemana,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    dataLonga (s) {
      const nomes = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
      return `${nomes[diaSemana(s)]}, ${Number(s.slice(8))} de ${MESES[Number(s.slice(5, 7)) - 1]}${s.slice(0, 4) !== this.hoje.slice(0, 4) ? ' de ' + s.slice(0, 4) : ''}`
    },
    corItem (e) {
      const base = e.status === 'concluido' ? 'opacity-60 ' : ''
      if (e.origem === 'cliente') return base + 'bg-sky-500/10 text-sky-200 border-sky-400'
      if (e.agendada) return base + 'bg-amber-500/10 text-amber-200 border-amber-400'
      return base + 'bg-zinc-800 text-zinc-300 border-zinc-500'
    },
    borda (e) { return e.origem === 'cliente' ? 'border-l-sky-400' : e.agendada ? 'border-l-amber-400' : 'border-l-zinc-600' },
    corEstado (s) {
      const m = { pendente: 'bg-yellow-500/15 text-yellow-400', pago: 'bg-blue-500/15 text-blue-400', preparando: 'bg-purple-500/15 text-purple-400',
                  enviado: 'bg-indigo-500/15 text-indigo-400', concluido: 'bg-green-500/15 text-green-400' }
      return m[s] || 'bg-zinc-500/15 text-zinc-400'
    },
    intensidade (n) {
      if (!n) return 'bg-zinc-800/40 text-zinc-600 hover:bg-zinc-800'
      if (n < 3) return 'bg-red-500/25 text-red-100 hover:bg-red-500/40'
      if (n < 8) return 'bg-red-500/50 text-white hover:bg-red-500/60'
      return 'bg-red-500/80 text-white hover:bg-red-500'
    },
    podeAtribuir (e) {
      return e.tipo_entrega === 'entrega' && ['pago', 'preparando', 'enviado'].includes(e.status) &&
        (!e.entrega || ['atribuido', 'a_caminho', 'falhou'].includes(e.entrega.status))
    },

    mover (n) {
      if (this.vista === 'dia') this.ref = mais(this.ref, n)
      else if (this.vista === 'semana') this.ref = mais(this.ref, 7 * n)
      else if (this.vista === 'mes') { const d = D(inicioMes(this.ref)); d.setUTCMonth(d.getUTCMonth() + n); this.ref = S(d) }
      else this.ref = `${Number(this.ref.slice(0, 4)) + n}-01-01`
    },
    irHoje () { this.ref = this.hoje },
    abrirDia (d) { this.ref = d; this.vista = 'dia' },
    abrirMes (d) { this.ref = d; this.vista = 'mes' },

    async carregar () {
      const [inicio, fim] = this.intervalo
      const params = { inicio, fim }
      if (this.tipo) params.tipo = this.tipo
      if (this.soAgendadas) params.agendadas = 1
      if (this.vista === 'ano') params.resumo = 1
      this.carregando = true
      this.erro = ''
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/calendario/`, { params })
        if (data.hoje && data.hoje !== this.hoje) {
          if (this.ref === this.hoje) this.ref = data.hoje      // "hoje" no fuso da plataforma
          this.hoje = data.hoje
        }
        if (this.vista === 'ano') this.resumo = data.dias || {}
        else { this.itens = data.itens || []; this.truncado = !!data.truncado }
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar o calendário.'
      } finally {
        this.carregando = false
      }
    },

    async mudarEntrega (estado, extra = {}) {
      this.confirmando = ''
      await this.acao(() => api.patch(`/app/loja/${this.lojaId}/encomendas/${this.detalhe.encomenda_id}/entrega/atualizar/`, { status: estado, ...extra }))
    },
    async atribuir () {
      const url = `/app/loja/${this.lojaId}/encomendas/${this.detalhe.encomenda_id}/entrega/`
      await this.acao(() => this.detalhe.entrega
        ? api.patch(url + 'atualizar/', { condutor_id: this.condutorId })
        : api.post(url + 'criar/', { condutor_id: this.condutorId }))
    },
    async acao (fn) {
      this.aGuardar = true
      this.erroAcao = ''
      try {
        await fn()
        const id = this.detalhe.encomenda_id
        await this.carregar()
        this.detalhe = this.itens.find(e => e.encomenda_id === id) || null
        this.$emit('alterado')
      } catch (e) {
        this.erroAcao = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
  emits: ['alterado'],
}
</script>
