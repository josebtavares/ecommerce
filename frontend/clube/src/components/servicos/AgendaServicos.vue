<template>
  <!-- Agenda: dia (uma coluna por profissional) ou semana (uma coluna por dia). No telemóvel, lista. -->
  <div class="space-y-3" data-teste="agenda">
    <div class="flex flex-wrap items-center gap-2">
      <div class="flex items-center gap-1">
        <button type="button" @click="mover(-1)" aria-label="Anterior" class="w-9 h-9 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300">‹</button>
        <button type="button" @click="irHoje" class="px-3 h-9 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-300">Hoje</button>
        <button type="button" @click="mover(1)" aria-label="Seguinte" class="w-9 h-9 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300">›</button>
      </div>
      <input v-model="inicio" type="date" aria-label="Dia" @change="carregar"
        class="h-9 px-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200" />
      <p class="text-sm font-bold text-zinc-100 mr-auto" data-teste="agenda-titulo">{{ titulo }}</p>
      <div class="flex gap-1 bg-zinc-800/60 rounded-xl p-1" role="tablist" aria-label="Vista">
        <button v-for="v in [{ k: 1, t: 'Dia' }, { k: 7, t: 'Semana' }]" :key="v.k" type="button" role="tab" :aria-selected="dias === v.k"
          @click="mudarVista(v.k)" :class="['px-3 py-1 rounded-lg text-xs font-semibold', dias === v.k ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400']">{{ v.t }}</button>
      </div>
      <select v-if="dados && dados.profissionais.length > 1" v-model="filtroProf" aria-label="Profissional"
        class="h-9 px-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-200">
        <option :value="null">Todos</option>
        <option v-for="p in dados.profissionais" :key="p.id" :value="p.id">{{ p.nome }}</option>
      </select>
      <!-- serviços feitos (ou faltas pagas) sem a fatura registada -->
      <button v-if="podeGerir && porFaturar.length" type="button" @click="verPorFaturar = !verPorFaturar" data-teste="marcacoes-por-faturar"
        :aria-expanded="verPorFaturar ? 'true' : 'false'"
        class="h-9 px-3 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 text-xs font-bold">Por faturar · {{ porFaturar.length }}</button>
      <button v-if="podeGerir" type="button" @click="novaEm({})" data-teste="nova-marcacao"
        class="h-9 px-4 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold">+ Marcação</button>
    </div>

    <div v-if="verPorFaturar && porFaturar.length" class="bg-zinc-900 rounded-2xl border border-amber-500/30 overflow-hidden" data-teste="lista-por-faturar">
      <p class="px-4 py-2 text-xs text-amber-200 border-b border-zinc-800">Emite a fatura no e-Fatura e regista-a em cada marcação.</p>
      <button v-for="m in porFaturar" :key="m.id" type="button" @click="abrir(m)"
        class="w-full flex flex-wrap items-center gap-x-3 gap-y-0.5 px-4 py-2.5 border-b border-zinc-800/60 last:border-0 text-left hover:bg-zinc-800/50">
        <span class="text-xs tabular-nums text-zinc-400 w-24">{{ rotuloDia(diaDe(m.inicio)) }} {{ hora(m.inicio) }}</span>
        <span class="flex-1 min-w-0 text-sm text-zinc-200 truncate">{{ m.servico_nome }} · {{ m.cliente_nome || '—' }}</span>
        <span class="text-xs text-zinc-400">{{ ESTADOS[m.estado].nome }} · {{ m.preco_texto }}</span>
      </button>
    </div>

    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
    <div v-if="!dados" class="h-64 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <template v-else>
      <p v-if="!profs.length" class="text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800 p-6 text-center">
        Sem profissionais. Cria-os no separador Profissionais.</p>

      <!-- ═══ grelha (computador / tablet) ═══ -->
      <div v-else class="hidden sm:block bg-zinc-900 rounded-2xl border border-zinc-800 overflow-x-auto">
        <div class="flex min-w-full" :style="{ minWidth: (60 + colunas.length * larguraColuna) + 'px' }">
          <!-- horas -->
          <div class="w-14 flex-shrink-0 border-r border-zinc-800">
            <div class="h-10 border-b border-zinc-800"></div>
            <div class="relative" :style="{ height: altura + 'px' }">
              <span v-for="h in horasEixo" :key="h" class="absolute right-2 text-[10px] text-zinc-500 tabular-nums -translate-y-1/2"
                    :style="{ top: (h * 60 - minIni) * PX + 'px' }">{{ String(h).padStart(2, '0') }}:00</span>
            </div>
          </div>
          <!-- colunas -->
          <div v-for="c in colunas" :key="c.chave" class="flex-1 border-r border-zinc-800 last:border-r-0" :style="{ minWidth: larguraColuna + 'px' }">
            <div class="h-10 border-b border-zinc-800 px-2 flex items-center justify-center text-center">
              <p class="text-xs font-semibold truncate" :class="c.hoje ? 'text-red-400' : 'text-zinc-200'">{{ c.titulo }}</p>
            </div>
            <div class="relative" :style="{ height: altura + 'px' }" :class="[podeGerir && 'cursor-pointer', c.semHorario ? '' : 'bg-zinc-950/70']"
                 @click="clicarColuna($event, c)" :data-teste="`coluna-${c.chave}`">
              <div v-for="h in horasEixo" :key="h" class="absolute inset-x-0 border-t border-zinc-800/70" :style="{ top: (h * 60 - minIni) * PX + 'px' }"></div>
              <!-- horário de trabalho -->
              <div v-for="(b, i) in c.blocos" :key="'b' + i" class="absolute inset-x-0 bg-zinc-800/60"
                   :style="caixa(b[0], b[1])"></div>
              <!-- ausências -->
              <div v-for="a in c.ausencias" :key="'a' + a.id" class="absolute inset-x-0 bg-red-500/10 border-y border-red-500/20 flex items-start justify-center pt-1"
                   :style="caixa(a.inicio, a.fim)" style="background-image: repeating-linear-gradient(135deg, transparent 0 6px, rgba(239,68,68,.08) 6px 12px)">
                <span class="text-[10px] text-red-300/80">{{ a.motivo || 'Ausente' }}</span>
              </div>
              <!-- marcações -->
              <button v-for="m in c.marcacoes" :key="m.id" type="button" @click.stop="abrir(m)" :data-teste="`marcacao-${m.id}`"
                :class="['absolute rounded-lg border px-1.5 py-1 text-left overflow-hidden hover:brightness-125 focus:outline-none focus:ring-2 focus:ring-red-500', ESTADOS[m.estado].cor]"
                :style="{ ...caixa(m.inicio, m.fim), left: `calc(${m._faixa * 100 / m._faixas}% + 2px)`, width: `calc(${100 / m._faixas}% - 4px)` }"
                :aria-label="`${hora(m.inicio)} ${m.servico_nome} ${m.cliente_nome}`">
                <p class="text-[11px] font-bold leading-tight truncate">{{ hora(m.inicio) }} {{ m.servico_nome }}</p>
                <p class="text-[10px] leading-tight truncate opacity-80">{{ m.cliente_nome || '—' }}<template v-if="dias > 1 && !filtroProf"> · {{ m.profissional_nome }}</template></p>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ lista (telemóvel) ═══ -->
      <div v-if="profs.length" class="sm:hidden space-y-3" data-teste="agenda-lista">
        <div v-for="d in diasVista" :key="d" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">
          <p class="px-4 py-2 text-xs font-bold border-b border-zinc-800" :class="d === hoje ? 'text-red-400' : 'text-zinc-300'">{{ rotuloDia(d) }}</p>
          <p v-if="!doDia(d).length" class="px-4 py-3 text-xs text-zinc-600">Sem marcações.</p>
          <button v-for="m in doDia(d)" :key="m.id" type="button" @click="abrir(m)"
            class="w-full flex items-center gap-3 px-4 py-2.5 border-b border-zinc-800/60 last:border-0 text-left">
            <span class="text-sm font-bold tabular-nums text-zinc-100 w-12">{{ hora(m.inicio) }}</span>
            <span class="flex-1 min-w-0">
              <span :class="['block text-sm truncate', m.estado === 'cancelada' ? 'line-through text-zinc-500' : 'text-zinc-200']">{{ m.servico_nome }} · {{ m.cliente_nome || '—' }}</span>
              <span class="block text-[11px] text-zinc-500">{{ m.profissional_nome }} · {{ ESTADOS[m.estado].nome }}</span>
            </span>
            <span :class="['w-2 h-2 rounded-full flex-shrink-0', ESTADOS[m.estado].ponto]"></span>
          </button>
        </div>
      </div>

      <div class="flex flex-wrap gap-3 text-[11px] text-zinc-500">
        <span v-for="e in ['pendente', 'confirmada', 'concluida', 'cancelada']" :key="e" class="flex items-center gap-1.5">
          <span :class="['w-2 h-2 rounded-full', ESTADOS[e].ponto]"></span>{{ ESTADOS[e].nome }}</span>
        <span class="hidden sm:flex items-center gap-1.5"><span class="w-3 h-2 rounded-sm bg-zinc-700 border border-zinc-600"></span>Horário de trabalho</span>
        <span class="hidden sm:flex items-center gap-1.5"><span class="w-3 h-2 rounded-sm bg-red-500/30"></span>Ausência</span>
      </div>
    </template>

    <MarcacaoNova v-if="nova" :loja-id="lojaId" :servicos="servicos" :profissionais="profissionaisTodos" :inicial="nova"
      @fechar="nova = null" @criada="aoCriar" />
    <MarcacaoDetalhe v-if="aberta" :loja-id="lojaId" :marcacao-id="aberta" :pode-gerir="podeGerir"
      @fechar="fecharDetalhe" @alterada="carregar" />
  </div>
</template>

<script>
import api from '@/services/api'
import { ESTADOS_MARCACAO, diaDe, diaSemana, hojeCV, hora, minutosDe, ouvirMarcacoes, rotuloDia, somarDias } from '@/utils/servicos'
import MarcacaoNova from './MarcacaoNova.vue'
import MarcacaoDetalhe from './MarcacaoDetalhe.vue'

const PX = 1.2    // píxeis por minuto (72 por hora)

export default {
  name: 'AgendaServicos',
  components: { MarcacaoNova, MarcacaoDetalhe },
  props: {
    lojaId: { type: [String, Number], required: true },
    servicos: { type: Array, default: () => [] },
    profissionaisTodos: { type: Array, default: () => [] },
    podeGerir: { type: Boolean, default: false },
  },
  data () {
    return { dados: null, inicio: hojeCV(), dias: 1, filtroProf: null, erro: '', nova: null, aberta: null,
             hoje: hojeCV(), PX, ESTADOS: ESTADOS_MARCACAO, porFaturar: [], verPorFaturar: false }
  },
  computed: {
    profs () { return (this.dados?.profissionais || []).filter(p => !this.filtroProf || p.id === this.filtroProf) },
    diasVista () { return Array.from({ length: this.dias }, (_, i) => somarDias(this.inicio, i)) },
    titulo () {
      if (this.dias === 1) return rotuloDia(this.inicio, true)
      return `${rotuloDia(this.inicio)} – ${rotuloDia(somarDias(this.inicio, this.dias - 1), true)}`
    },
    marcacoesVisiveis () {
      const ids = new Set(this.profs.map(p => p.id))
      return (this.dados?.marcacoes || []).filter(m => ids.has(m.profissional_id))
    },
    colunas () {
      const aus = this.dados?.ausencias || []
      if (this.dias === 1) {
        return this.profs.map(p => ({
          chave: 'p' + p.id, titulo: p.nome, hoje: false, dia: this.inicio, profissional_id: p.id,
          blocos: p.blocos[this.inicio] || [], semHorario: false,
          ausencias: this.cortarAusencias(aus.filter(a => a.profissional_id === p.id), this.inicio),
          marcacoes: this.faixas(this.marcacoesVisiveis.filter(m => m.profissional_id === p.id && diaDe(m.inicio) === this.inicio)),
        }))
      }
      const um = this.profs.length === 1 ? this.profs[0] : null
      return this.diasVista.map(d => ({
        chave: 'd' + d, titulo: rotuloDia(d), hoje: d === this.hoje, dia: d, profissional_id: um?.id || null,
        blocos: um ? (um.blocos[d] || []) : [], semHorario: !um,
        ausencias: um ? this.cortarAusencias(aus.filter(a => a.profissional_id === um.id), d) : [],
        marcacoes: this.faixas(this.marcacoesVisiveis.filter(m => diaDe(m.inicio) === d)),
      }))
    },
    // janela de horas: o horário de trabalho e as marcações (mínimo 08–20)
    minIni () {
      let min = 8 * 60
      this.colunas.forEach(c => { c.blocos.forEach(b => { min = Math.min(min, minutosDe(b[0])) }); c.marcacoes.forEach(m => { min = Math.min(min, minutosDe(m.inicio)) }) })
      return Math.floor(min / 60) * 60
    },
    minFim () {
      let max = 20 * 60
      this.colunas.forEach(c => {
        c.blocos.forEach(b => { max = Math.max(max, diaDe(b[1]) > c.dia ? 24 * 60 : minutosDe(b[1])) })
        c.marcacoes.forEach(m => { max = Math.max(max, diaDe(m.fim) > c.dia ? 24 * 60 : minutosDe(m.fim)) })
      })
      return Math.min(24 * 60, Math.ceil(max / 60) * 60)
    },
    larguraColuna () { return this.dias > 1 ? 120 : 150 },
    altura () { return (this.minFim - this.minIni) * PX },
    horasEixo () { const out = []; for (let h = this.minIni / 60; h < this.minFim / 60; h++) out.push(h); return out },
  },
  mounted () {
    // uma marcação desta loja mudou (cliente marcou, cancelou, remarcou…): recarrega a agenda (agrupado)
    this.desligar = ouvirMarcacoes(d => {
      if (d && String(d.loja_id) !== String(this.lojaId)) return
      clearTimeout(this.adiado)
      this.adiado = setTimeout(() => this.carregar(), 400)
    })
  },
  beforeUnmount () { this.desligar?.(); clearTimeout(this.adiado) },
  created () {
    this.carregar()
    const q = Number(this.$route.query.marcacao)
    if (q) this.aberta = q
  },
  methods: {
    diaDe, hora, rotuloDia,
    async carregar () {
      this.erro = ''
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/servicos/agenda/`, { params: { inicio: this.inicio, dias: this.dias } })
        this.dados = data
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar a agenda.' }
      this.carregarPorFaturar()
    },
    async carregarPorFaturar () {
      if (!this.podeGerir) return
      try {
        this.porFaturar = (await api.get(`/app/loja/${this.lojaId}/servicos/marcacoes/`, { params: { fatura: 'por_faturar' } })).data
        if (!this.porFaturar.length) this.verPorFaturar = false
      } catch { /* a agenda continua a funcionar sem a lista */ }
    },
    mover (n) { this.inicio = somarDias(this.inicio, n * this.dias); this.carregar() },
    irHoje () { this.inicio = this.dias === 7 ? somarDias(hojeCV(), -diaSemana(hojeCV())) : hojeCV(); this.carregar() },
    mudarVista (d) {
      this.dias = d
      if (d === 7) this.inicio = somarDias(this.inicio, -diaSemana(this.inicio))     // a semana começa à segunda
      this.carregar()
    },
    cortarAusencias (lista, dia) {
      // só a parte deste dia
      return lista.filter(a => diaDe(a.inicio) <= dia && diaDe(a.fim) >= dia && !(diaDe(a.fim) === dia && hora(a.fim) === '00:00'))
        .map(a => ({ ...a, inicio: diaDe(a.inicio) < dia ? `${dia}T00:00:00` : a.inicio, fim: diaDe(a.fim) > dia ? `${dia}T23:59:00` : a.fim }))
    },
    // marcações que se sobrepõem na mesma coluna ficam lado a lado
    faixas (lista) {
      const ord = [...lista].sort((a, b) => a.inicio.localeCompare(b.inicio))
      const grupos = []
      let atual = []
      let fimGrupo = ''
      ord.forEach(m => {
        if (atual.length && m.inicio >= fimGrupo) { grupos.push(atual); atual = []; fimGrupo = '' }
        atual.push(m); if (m.fim > fimGrupo) fimGrupo = m.fim
      })
      if (atual.length) grupos.push(atual)
      const out = []
      grupos.forEach(g => {
        const fins = []
        g.forEach(m => {
          let f = fins.findIndex(x => x <= m.inicio)
          if (f < 0) { f = fins.length; fins.push(m.fim) } else fins[f] = m.fim
          out.push({ ...m, _faixa: f })
        })
        out.filter(m => g.some(x => x.id === m.id)).forEach(m => { m._faixas = fins.length })
      })
      return out
    },
    caixa (a, f) {
      const ini = Math.max(minutosDe(a), this.minIni)
      const fim = f.slice(0, 10) > a.slice(0, 10) ? 24 * 60 : minutosDe(f)
      return { top: (ini - this.minIni) * PX + 'px', height: Math.max(18, (Math.min(fim, this.minFim) - ini) * PX) + 'px' }
    },
    clicarColuna (ev, c) {
      if (!this.podeGerir) return
      const y = ev.clientY - ev.currentTarget.getBoundingClientRect().top
      const min = this.minIni + Math.floor(y / PX / 15) * 15
      const hh = String(Math.floor(min / 60)).padStart(2, '0'), mm = String(min % 60).padStart(2, '0')
      this.novaEm({ dia: c.dia, hora: `${hh}:${mm}`, profissional_id: c.profissional_id })
    },
    novaEm (ini) { this.nova = { dia: ini.dia || this.inicio, hora: ini.hora || '', profissional_id: ini.profissional_id || this.filtroProf || null } },
    aoCriar (m) { this.nova = null; this.carregar(); this.aberta = m.id },
    abrir (m) { this.aberta = m.id },
    fecharDetalhe () {
      this.aberta = null
      if (this.$route.query.marcacao) this.$router.replace({ query: { ...this.$route.query, marcacao: undefined } })
    },
    doDia (d) { return this.marcacoesVisiveis.filter(m => diaDe(m.inicio) === d).sort((a, b) => a.inicio.localeCompare(b.inicio)) },
  },
}
</script>
