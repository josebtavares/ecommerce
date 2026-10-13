<template>
  <!-- Backoffice → Configurações → Horário. Cada dia tem o seu interruptor e os seus intervalos
       (a pausa é o espaço entre dois intervalos). Grava em PUT /app/loja/<id>/horario/. -->
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
    <div class="flex items-start justify-between gap-4 mb-5">
      <div>
        <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Horário</h2>
        <p class="text-xs text-zinc-500 mt-1">
          Quando a loja abre e fecha. Horas de {{ nomeFuso }}<template v-if="agora"> — agora são {{ agora }}</template>.
        </p>
      </div>
      <button type="button" role="switch" :aria-checked="form.horario_ativo ? 'true' : 'false'" aria-label="Usar horário"
        @click="form.horario_ativo = !form.horario_ativo"
        :class="['w-11 h-6 rounded-full transition-colors relative flex-shrink-0', form.horario_ativo ? 'bg-red-600' : 'bg-zinc-700']">
        <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow', form.horario_ativo ? 'left-5.5' : 'left-0.5']" style="transition: left 0.2s"></span>
      </button>
    </div>

    <div v-if="carregando" class="h-24 rounded-xl bg-zinc-800/50 animate-pulse"></div>

    <template v-else>
      <p v-if="!form.horario_ativo" class="text-sm text-zinc-400 bg-zinc-800/50 rounded-xl px-4 py-3 mb-4">
        Desligado — a loja está aberta 24 horas, todos os dias. Liga para definir o horário.
      </p>

      <div :class="{ 'opacity-50 pointer-events-none select-none': !form.horario_ativo }" :aria-disabled="!form.horario_ativo">
        <!-- estado agora (do último horário gravado) -->
        <div v-if="estado?.ativo" class="flex items-center gap-2 text-sm mb-4 px-4 py-3 rounded-xl bg-zinc-800/50">
          <span class="w-2 h-2 rounded-full" :class="estado.aberta ? 'bg-green-500' : 'bg-amber-500'"></span>
          <span class="text-zinc-300">Agora: <b class="text-zinc-100">{{ estado.texto }}</b></span>
          <span v-if="alterado" class="ml-auto text-xs text-amber-400">alterações por gravar</span>
        </div>

        <!-- dias da semana -->
        <div class="space-y-2">
          <div v-for="d in form.dias" :key="d.dia"
               :class="['rounded-xl border px-3 py-3 sm:flex sm:items-start sm:gap-4',
                        d.dia === hoje ? 'border-red-500/40 bg-red-500/5' : 'border-zinc-800 bg-zinc-800/30']">
            <div class="flex items-center gap-3 sm:w-44 sm:pt-1.5 flex-shrink-0">
              <button type="button" role="switch" :aria-checked="d.intervalos.length ? 'true' : 'false'"
                :aria-label="`${NOMES[d.dia]} aberto`" @click="alternarDia(d)"
                :class="['w-9 h-5 rounded-full transition-colors relative flex-shrink-0', d.intervalos.length ? 'bg-green-600' : 'bg-zinc-700']">
                <span :class="['absolute top-0.5 w-4 h-4 rounded-full bg-white shadow', d.intervalos.length ? 'left-4.5' : 'left-0.5']" style="transition: left 0.2s"></span>
              </button>
              <span class="text-sm font-semibold text-zinc-200">{{ NOMES[d.dia] }}</span>
              <span v-if="d.dia === hoje" class="text-[10px] font-bold uppercase tracking-wide text-red-400">Hoje</span>
            </div>

            <div class="flex-1 mt-2 sm:mt-0">
              <p v-if="!d.intervalos.length" class="text-sm text-zinc-500 sm:pt-1.5">Fechado</p>
              <div v-else class="flex flex-wrap items-center gap-2">
                <template v-for="(i, n) in d.intervalos" :key="n">
                  <span v-if="n > 0" class="text-[11px] text-zinc-500 px-1">pausa</span>
                  <div class="flex items-center gap-1 rounded-lg bg-zinc-800 border border-zinc-700 pl-2 pr-1 py-1">
                    <input type="time" v-model="i.abre" :aria-label="`${NOMES[d.dia]}: abre`"
                      class="bg-transparent text-sm text-zinc-100 focus:outline-none w-[6.75rem]" />
                    <span class="text-zinc-500 text-xs">–</span>
                    <input type="time" v-model="i.fecha" :aria-label="`${NOMES[d.dia]}: fecha`"
                      class="bg-transparent text-sm text-zinc-100 focus:outline-none w-[6.75rem]" />
                    <button type="button" @click="d.intervalos.splice(n, 1)" :aria-label="`Remover ${i.abre}–${i.fecha}`"
                      class="w-6 h-6 rounded-md text-zinc-500 hover:text-red-400 hover:bg-zinc-700 text-base leading-none">×</button>
                  </div>
                </template>
                <button v-if="d.intervalos.length < MAX" type="button" @click="adicionarIntervalo(d)"
                  class="text-xs font-semibold text-zinc-400 hover:text-zinc-100 px-2 py-1.5 rounded-lg hover:bg-zinc-800">
                  + intervalo
                </button>
              </div>
              <p v-if="avisoDia(d)" class="text-xs text-amber-400 mt-1.5">{{ avisoDia(d) }}</p>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-2 mt-3">
          <button type="button" @click="copiar([1, 2, 3, 4])"
            class="text-xs font-semibold text-zinc-300 border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5">
            Copiar segunda para os dias úteis
          </button>
          <button type="button" @click="copiar([1, 2, 3, 4, 5, 6])"
            class="text-xs font-semibold text-zinc-300 border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5">
            Copiar segunda para todos os dias
          </button>
        </div>
        <p class="text-[11px] text-zinc-500 mt-2">
          Para fechar depois da meia-noite usa, por exemplo, 18:00–02:00. 00:00–00:00 = aberto o dia todo.
        </p>

        <!-- loja fechada -->
        <p class="text-sm font-semibold text-zinc-200 mt-6 mb-2">Quando a loja está fechada</p>
        <div class="grid sm:grid-cols-2 gap-2">
          <label v-for="o in REGRAS" :key="o.valor"
            :class="['flex gap-3 p-3 rounded-xl border cursor-pointer transition',
                     form.fora_horario === o.valor ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 hover:border-zinc-600']">
            <input type="radio" name="fora_horario" :value="o.valor" v-model="form.fora_horario" class="mt-1 accent-red-600" />
            <span>
              <span class="block text-sm font-semibold text-zinc-100">{{ o.titulo }}</span>
              <span class="block text-xs text-zinc-500 mt-0.5">{{ o.texto }}</span>
            </span>
          </label>
        </div>
      </div>

      <!-- o cliente escolhe dia e hora (funciona também sem horário: qualquer hora do dia) -->
      <div class="mt-6 pt-5 border-t border-zinc-800">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-semibold text-zinc-200">O cliente escolhe dia e hora</p>
            <p class="text-xs text-zinc-500 mt-0.5">
              No checkout o cliente pode pedir para receber ou levantar mais tarde{{ form.horario_ativo ? ', só dentro do horário' : '' }}.
              A encomenda é feita e paga logo, e aparece no calendário das Entregas.
            </p>
          </div>
          <button type="button" role="switch" :aria-checked="form.agendamento.ativo ? 'true' : 'false'"
            aria-label="O cliente escolhe dia e hora" @click="form.agendamento.ativo = !form.agendamento.ativo"
            :class="['w-11 h-6 rounded-full transition-colors relative flex-shrink-0', form.agendamento.ativo ? 'bg-red-600' : 'bg-zinc-700']">
            <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow', form.agendamento.ativo ? 'left-5.5' : 'left-0.5']" style="transition: left 0.2s"></span>
          </button>
        </div>
        <div v-if="form.agendamento.ativo" class="grid sm:grid-cols-3 gap-3 mt-4">
          <label class="block">
            <span class="text-xs text-zinc-500 mb-1 block">Horas de</span>
            <select v-model.number="form.agendamento.intervalo" aria-label="Intervalo entre horas"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
              <option :value="15">15 em 15 min</option>
              <option :value="30">30 em 30 min</option>
              <option :value="60">hora a hora</option>
              <option :value="120">2 em 2 horas</option>
            </select>
          </label>
          <label class="block">
            <span class="text-xs text-zinc-500 mb-1 block">Até quantos dias à frente</span>
            <select v-model.number="form.agendamento.dias" aria-label="Dias à frente"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
              <option v-for="d in [1, 2, 3, 7, 14, 30, 60]" :key="d" :value="d">{{ d === 1 ? 'Só hoje' : d + ' dias' }}</option>
            </select>
          </label>
          <label class="block">
            <span class="text-xs text-zinc-500 mb-1 block">Antecedência mínima</span>
            <select v-model.number="form.agendamento.antecedencia" aria-label="Antecedência mínima"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
              <option v-for="a in ANTECEDENCIAS" :key="a.v" :value="a.v">{{ a.t }}</option>
            </select>
          </label>
        </div>
      </div>

      <p v-if="erro" class="text-sm text-red-400 mt-4" role="alert">{{ erro }}</p>
      <div class="flex items-center gap-3 mt-5">
        <button type="button" @click="guardar" :disabled="aGuardar || !alterado"
          class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition">
          {{ aGuardar ? 'A guardar…' : 'Guardar horário' }}
        </button>
        <span v-if="guardado" class="text-sm text-green-400">Horário guardado.</span>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

const NOMES = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
const MAX = 4
const REGRAS = [
  { valor: 'agendar',  titulo: 'Aceitar encomendas para a abertura',
    texto: 'O cliente encomenda e paga já; a encomenda aparece marcada para a hora em que a loja abre.' },
  { valor: 'bloquear', titulo: 'Não aceitar encomendas',
    texto: 'O cliente pode ver a loja e encher o carrinho, mas só encomenda com a loja aberta.' },
]
const ANTECEDENCIAS = [
  { v: 0, t: 'Nenhuma' }, { v: 15, t: '15 minutos' }, { v: 30, t: '30 minutos' }, { v: 60, t: '1 hora' },
  { v: 120, t: '2 horas' }, { v: 240, t: '4 horas' }, { v: 1440, t: '1 dia' },
]
const min = h => { const [a, b] = String(h || '').split(':').map(Number); return a * 60 + b }

function copia (dias) { return JSON.parse(JSON.stringify(dias)) }

export default {
  name: 'HorarioEditor',
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['guardado'],

  data () {
    return {
      NOMES, MAX, REGRAS, ANTECEDENCIAS,
      carregando: true, aGuardar: false, guardado: false, erro: '',
      form: { horario_ativo: false, fora_horario: 'agendar', dias: [], agendamento: { ativo: false, intervalo: 30, dias: 7, antecedencia: 30 } },
      original: '', estado: null, fuso: '', agora: '', hoje: null,
    }
  },

  computed: {
    alterado () { return JSON.stringify(this.form) !== this.original },
    nomeFuso () {
      if (this.fuso === 'Atlantic/Cape_Verde') return 'Cabo Verde'
      return (this.fuso || '').split('/').pop().replace(/_/g, ' ')
    },
  },

  watch: {
    form: { deep: true, handler () { this.guardado = false; this.erro = '' } },
  },

  async created () {
    try {
      const { data } = await api.get(`/app/loja/${this.lojaId}/horario/`)
      this.aplicar(data)
    } catch (e) {
      this.erro = e.response?.data?.detail || 'Não foi possível carregar o horário.'
    } finally {
      this.carregando = false
    }
  },

  methods: {
    aplicar (data) {
      this.form = {
        horario_ativo: data.horario_ativo,
        fora_horario:  data.fora_horario,
        dias: data.dias.map(d => ({ dia: d.dia, intervalos: d.intervalos.map(i => ({ ...i })) })),
        agendamento: { ...data.agendamento },
      }
      this.original = JSON.stringify(this.form)
      this.estado = data.estado
      this.fuso = data.fuso
      this.agora = data.agora
      this.hoje = data.hoje
    },

    alternarDia (d) {
      if (d.intervalos.length) { d.intervalos = []; return }
      // abre com o horário do último dia aberto (ou 09:00–18:00)
      const modelo = [...this.form.dias].reverse().find(x => x.dia < d.dia && x.intervalos.length) ||
                     this.form.dias.find(x => x.intervalos.length)
      d.intervalos = modelo ? copia(modelo.intervalos) : [{ abre: '09:00', fecha: '18:00' }]
    },

    adicionarIntervalo (d) {
      const ultimo = d.intervalos[d.intervalos.length - 1]
      if (!ultimo) { d.intervalos.push({ abre: '09:00', fecha: '18:00' }); return }
      // a seguir ao último, com 1h de pausa e 2h abertas
      const ini = Math.min(min(ultimo.fecha) + 60, 22 * 60)
      const h = m => `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
      d.intervalos.push({ abre: h(ini), fecha: h(Math.min(ini + 120, 23 * 60 + 59)) })
    },

    copiar (destinos) {
      const seg = this.form.dias[0]
      destinos.forEach(i => { this.form.dias[i].intervalos = copia(seg.intervalos) })
    },

    // o mesmo que o servidor valida, para avisar antes de gravar
    avisoDia (d) {
      const segs = d.intervalos.map(i => {
        if (!i.abre || !i.fecha) return null
        const a = min(i.abre), f = min(i.fecha)
        return { a, f: f > a || (a === 0 && f === 0) ? (f || 1440) : f + 1440, i }
      })
      if (segs.some(s => !s)) return 'Preenche as horas de abertura e fecho.'
      if (segs.some(s => s.i.abre === s.i.fecha && s.i.abre !== '00:00')) return 'A hora de fecho tem de ser diferente da de abertura.'
      const ord = [...segs].sort((x, y) => x.a - y.a)
      for (let n = 1; n < ord.length; n++) {
        if (ord[n].a < ord[n - 1].f) return `${ord[n - 1].i.abre}–${ord[n - 1].i.fecha} e ${ord[n].i.abre}–${ord[n].i.fecha} sobrepõem-se.`
      }
      return ''
    },

    async guardar () {
      this.erro = ''
      if (this.form.horario_ativo && !this.form.dias.some(d => d.intervalos.length)) {
        this.erro = 'Abre pelo menos um dia antes de ligar o horário.'
        return
      }
      const aviso = this.form.dias.map(d => this.avisoDia(d) && `${NOMES[d.dia]}: ${this.avisoDia(d)}`).find(Boolean)
      if (aviso) { this.erro = aviso; return }
      this.aGuardar = true
      try {
        const { data } = await api.put(`/app/loja/${this.lojaId}/horario/`, this.form)
        this.aplicar(data)
        this.$nextTick(() => { this.guardado = true })   // depois do watch do form
        this.$emit('guardado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar o horário.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
