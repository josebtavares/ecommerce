<template>
  <!-- Marcação manual (cliente ao telefone / ao balcão): fica confirmada, paga no local -->
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="$emit('fechar')">
    <form @submit.prevent="criar" role="dialog" aria-label="Nova marcação" data-teste="marcacao-nova"
          class="bg-zinc-900 border border-zinc-800 rounded-t-2xl sm:rounded-2xl p-5 w-full sm:max-w-lg max-h-[92vh] overflow-y-auto space-y-4">
      <h3 class="text-base font-bold text-zinc-100">Nova marcação</h3>
      <label class="block"><span class="text-xs text-zinc-500">Serviço</span>
        <select v-model="servicoId" required :class="[CAMPO, 'mt-1']" @change="aoMudar">
          <option :value="null" disabled>Escolhe o serviço</option>
          <option v-for="s in servicos.filter(s => s.ativo)" :key="s.id" :value="s.id">{{ s.nome }} · {{ duracaoTexto(s.duracao_min) }} · {{ s.preco_texto }}</option>
        </select></label>
      <div class="grid grid-cols-2 gap-3">
        <label class="block"><span class="text-xs text-zinc-500">Profissional</span>
          <select v-model="profId" :class="[CAMPO, 'mt-1']" @change="carregarHoras">
            <option :value="null">Qualquer um livre</option>
            <option v-for="p in profsDoServico" :key="p.id" :value="p.id">{{ p.nome }}</option>
          </select></label>
        <label class="block"><span class="text-xs text-zinc-500">Dia</span>
          <input v-model="dia" type="date" required :min="hoje" :class="[CAMPO, 'mt-1']" @change="carregarHoras" /></label>
      </div>

      <div v-if="servicoId && dia">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs text-zinc-500">Hora</span>
          <label class="flex items-center gap-1.5 text-[11px] text-zinc-400">
            <input type="checkbox" v-model="foraHorario" class="accent-red-600" /> Outra hora (fora do horário)</label>
        </div>
        <input v-if="foraHorario" v-model="horaLivre" type="time" step="300" required aria-label="Hora" :class="CAMPO" />
        <template v-else>
          <p v-if="aCarregar" class="text-xs text-zinc-500">A ver as horas livres…</p>
          <p v-else-if="!horas.length" class="text-xs text-amber-300">Sem horas livres neste dia{{ profId ? ' para este profissional' : '' }}.</p>
          <div v-else class="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto" role="radiogroup" aria-label="Horas livres">
            <button v-for="h in horas" :key="h.inicio" type="button" role="radio" :aria-checked="escolhida === h.inicio"
              @click="escolhida = h.inicio"
              :class="['px-2.5 py-1 rounded-lg border text-xs font-semibold tabular-nums',
                       escolhida === h.inicio ? 'border-red-500 bg-red-600 text-white' : 'border-zinc-700 text-zinc-300 hover:border-zinc-500']">
              {{ hora(h.inicio) }}</button>
          </div>
        </template>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <label class="block col-span-2 sm:col-span-1"><span class="text-xs text-zinc-500">Nome do cliente</span>
          <input v-model="clienteNome" required maxlength="120" :class="[CAMPO, 'mt-1']" /></label>
        <label class="block col-span-2 sm:col-span-1"><span class="text-xs text-zinc-500">Telefone (opcional)</span>
          <input v-model="clienteTelefone" maxlength="30" inputmode="tel" :class="[CAMPO, 'mt-1']" /></label>
        <label class="block"><span class="text-xs text-zinc-500">Preço (CVE)</span>
          <input v-model="preco" type="number" min="0" step="1" :class="[CAMPO, 'mt-1']" :placeholder="servico ? String(Number(servico.preco)) : ''" /></label>
        <label class="block"><span class="text-xs text-zinc-500">Notas internas</span>
          <input v-model="notas" maxlength="500" :class="[CAMPO, 'mt-1']" /></label>
      </div>
      <p class="text-[11px] text-zinc-500">Fica confirmada e paga no local.</p>
      <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
      <div class="flex gap-2">
        <button type="submit" :disabled="aGuardar || !podeCriar"
          class="flex-1 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Marcar</button>
        <button type="button" @click="$emit('fechar')" class="px-4 py-2.5 rounded-xl border border-zinc-700 text-zinc-300 text-sm">Cancelar</button>
      </div>
    </form>
  </div>
</template>

<script>
import api from '@/services/api'
import { CAMPO, duracaoTexto, hora, hojeCV } from '@/utils/servicos'

export default {
  name: 'MarcacaoNova',
  props: {
    lojaId: { type: [String, Number], required: true },
    servicos: { type: Array, default: () => [] },
    profissionais: { type: Array, default: () => [] },
    inicial: { type: Object, default: () => ({}) },      // { dia, hora 'HH:MM', profissional_id }
  },
  emits: ['fechar', 'criada'],
  data () {
    return {
      servicoId: null, profId: this.inicial.profissional_id || null, dia: this.inicial.dia || hojeCV(),
      horas: [], escolhida: null, foraHorario: false, horaLivre: this.inicial.hora || '', aCarregar: false,
      clienteNome: '', clienteTelefone: '', preco: '', notas: '', erro: '', aGuardar: false, hoje: hojeCV(), CAMPO,
    }
  },
  computed: {
    servico () { return this.servicos.find(s => s.id === this.servicoId) },
    profsDoServico () {
      const ids = this.servico?.profissionais || []
      return this.profissionais.filter(p => p.ativo && (!this.servico || ids.includes(p.id)))
    },
    podeCriar () { return this.servicoId && this.dia && (this.foraHorario ? !!this.horaLivre : !!this.escolhida) && this.clienteNome.trim() },
  },
  created () {
    const activos = this.servicos.filter(s => s.ativo)
    const doProf = this.inicial.profissional_id ? activos.filter(s => s.profissionais.includes(this.inicial.profissional_id)) : activos
    if (doProf.length === 1 || (doProf.length && this.inicial.profissional_id)) { this.servicoId = doProf[0].id; this.carregarHoras() }
  },
  methods: {
    hora, duracaoTexto,
    aoMudar () {
      if (this.profId && !this.profsDoServico.some(p => p.id === this.profId)) this.profId = null
      this.carregarHoras()
    },
    async carregarHoras () {
      this.escolhida = null
      if (!this.servicoId || !this.dia) return
      this.aCarregar = true
      try {
        const params = { servico: this.servicoId, dia: this.dia }
        if (this.profId) params.profissional = this.profId
        const { data } = await api.get(`/app/loja/${this.lojaId}/servicos/disponibilidade/`, { params })
        this.horas = data.horas
        // clicou numa hora da agenda: escolhe-a se estiver livre
        if (this.inicial.hora && this.dia === this.inicial.dia) {
          const h = this.horas.find(x => hora(x.inicio) === this.inicial.hora)
          if (h) this.escolhida = h.inicio
        }
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível ver as horas livres.'
      } finally { this.aCarregar = false }
    },
    async criar () {
      this.erro = ''; this.aGuardar = true
      const corpo = {
        servico_id: this.servicoId, profissional_id: this.profId,
        inicio: this.foraHorario ? `${this.dia}T${this.horaLivre.slice(0, 5)}` : this.escolhida,
        cliente_nome: this.clienteNome.trim(), cliente_telefone: this.clienteTelefone.trim(), notas_internas: this.notas.trim(),
        ignorar_horario: this.foraHorario,
      }
      if (this.preco !== '' && this.preco !== null) corpo.preco = String(this.preco)
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/servicos/marcacoes/`, corpo)
        this.$emit('criada', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível marcar.'
        if (!this.foraHorario) this.carregarHoras()
      } finally { this.aGuardar = false }
    },
  },
}
</script>
