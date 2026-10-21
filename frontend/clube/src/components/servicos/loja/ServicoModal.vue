<template>
  <!-- Modal de um serviço na página da loja: ver o serviço e marcar (profissional, dia com vagas, hora, pagamento) -->
  <div class="fixed inset-0 z-[60] flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-0 sm:p-4" @click.self="$emit('fechar')">
    <div role="dialog" :aria-label="servico.nome" data-teste="servico-modal"
         class="w-full sm:max-w-lg max-h-[94vh] overflow-y-auto rounded-t-3xl sm:rounded-3xl shadow-2xl"
         :class="isDark ? 'bg-zinc-900 text-zinc-100' : 'bg-white text-zinc-900'">
      <!-- imagens -->
      <div v-if="servico.imagens.length" class="relative aspect-[16/9] overflow-hidden" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'">
        <img :src="servico.imagens[foto]" alt="" class="w-full h-full object-cover" />
        <div v-if="servico.imagens.length > 1" class="absolute bottom-2 inset-x-0 flex justify-center gap-1.5">
          <button v-for="(u, i) in servico.imagens" :key="i" type="button" @click="foto = i" :aria-label="`Imagem ${i + 1}`"
            :class="['w-2 h-2 rounded-full', foto === i ? 'bg-white' : 'bg-white/50']"></button>
        </div>
      </div>
      <div class="p-5 space-y-4">
        <div class="flex items-start gap-3">
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-bold leading-tight">{{ servico.nome }}</h3>
            <p class="text-sm mt-0.5" :class="suave">{{ duracaoTexto(servico.duracao_min) }} · <b :style="{ color: cor }">{{ servico.preco_texto }}</b></p>
          </div>
          <button type="button" @click="$emit('fechar')" aria-label="Fechar"
            class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">✕</button>
        </div>
        <p v-if="servico.descricao" class="text-sm whitespace-pre-line" :class="suave">{{ servico.descricao }}</p>
        <p v-if="servico.tipo_preco === 'a_partir'" class="text-[11px]" :class="suave">O preço final acerta-se com a loja — depois de marcar podes falar com ela.</p>

        <div v-if="profs.length > 1">
          <p class="text-xs font-semibold mb-1.5" :class="suave">Com quem?</p>
          <div class="flex flex-wrap gap-2" role="radiogroup" aria-label="Profissional">
            <button type="button" role="radio" :aria-checked="profId === null" @click="mudarProf(null)" :class="chip(profId === null)" :style="estiloChip(profId === null)">Qualquer um</button>
            <button v-for="p in profs" :key="p.id" type="button" role="radio" :aria-checked="profId === p.id" @click="mudarProf(p.id)"
              :class="[chip(profId === p.id), 'flex items-center gap-1.5']" :style="estiloChip(profId === p.id)">
              <img v-if="p.foto" :src="p.foto" alt="" class="w-5 h-5 rounded-full object-cover" />{{ p.nome }}
            </button>
          </div>
        </div>
        <p v-else-if="profs.length === 1" class="text-xs" :class="suave">Com {{ profs[0].nome }}</p>

        <div>
          <p class="text-xs font-semibold mb-1.5" :class="suave">Dia</p>
          <p v-if="aCarregarDias" class="text-xs" :class="suave">A ver os dias com vagas…</p>
          <p v-else-if="!dias.some(d => d.livres)" class="text-xs text-amber-500">Sem vagas nos próximos dias{{ profId ? ' com este profissional' : '' }}.</p>
          <div v-else class="flex gap-1.5 overflow-x-auto pb-1" role="radiogroup" aria-label="Dia">
            <button v-for="d in dias" :key="d.dia" type="button" role="radio" :aria-checked="dia === d.dia" :disabled="!d.livres"
              @click="mudarDia(d.dia)" :data-teste="`dia-${d.dia}`" :title="d.livres ? `${d.livres} horas livres` : 'Sem vagas'"
              :class="[chip(dia === d.dia), 'flex-shrink-0 flex flex-col items-center leading-tight min-w-[52px] disabled:opacity-30 disabled:cursor-not-allowed']"
              :style="estiloChip(dia === d.dia)">
              <span class="text-[10px] uppercase">{{ DIAS_CURTOS[diaSemana(d.dia)] }}</span>
              <span class="text-sm font-bold">{{ d.dia.slice(8) }}</span>
            </button>
          </div>
        </div>

        <div v-if="dia">
          <p class="text-xs font-semibold mb-1.5" :class="suave">Hora</p>
          <p v-if="aCarregar" class="text-xs" :class="suave">A ver as horas livres…</p>
          <div v-else class="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Hora">
            <button v-for="h in horas" :key="h.inicio" type="button" role="radio" :aria-checked="escolhida === h.inicio" @click="escolhida = h.inicio"
              :class="[chip(escolhida === h.inicio), 'tabular-nums']" :style="estiloChip(escolhida === h.inicio)">{{ hora(h.inicio) }}</button>
          </div>
        </div>

        <template v-if="escolhida">
          <label class="block"><span class="text-xs font-semibold" :class="suave">Nota para a loja (opcional)</span>
            <textarea v-model="notas" rows="2" maxlength="500" placeholder="ex.: a tua ideia, o comprimento do cabelo…"
              class="mt-1 w-full px-3 py-2 rounded-xl text-sm border focus:outline-none resize-none"
              :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea></label>
          <fieldset v-if="servico.pagamento === 'ambos'" class="space-y-1.5">
            <legend class="text-xs font-semibold mb-1" :class="suave">Pagamento</legend>
            <label v-for="o in [{ v: 'antecipado', t: 'Pagar já' }, { v: 'local', t: 'Pagar no local' }]" :key="o.v"
              class="flex items-center gap-2 text-sm"><input type="radio" :value="o.v" v-model="pagamento" :style="{ accentColor: cor }" />{{ o.t }}</label>
          </fieldset>
          <p v-else class="text-xs" :class="suave">{{ servico.pagamento === 'antecipado' ? 'Paga-se ao marcar.' : 'Paga-se no local.' }}</p>
          <div class="rounded-xl p-3 text-xs space-y-1" :class="isDark ? 'bg-zinc-800/60 text-zinc-300' : 'bg-gray-100 text-zinc-600'" data-teste="resumo">
            <p><b>{{ rotuloDia(dia, true) }} às {{ hora(escolhida) }}</b><template v-if="nomeProf"> com {{ nomeProf }}</template></p>
            <p>Podes cancelar ou remarcar até {{ regras.cancelar_horas ? regras.cancelar_horas + ' h antes' : 'à hora marcada' }}.</p>
            <p v-if="pagamentoEfetivo === 'antecipado'">
              Tens {{ regras.minutos_para_pagar }} min para pagar. Se cancelares mais tarde ou faltares,
              {{ regras.reembolso_fora_prazo === 'total' ? 'é-te devolvido tudo.' : 'o valor não é devolvido.' }}
            </p>
            <p v-if="regras.confirmacao === 'manual'">A loja confirma a marcação.</p>
          </div>
        </template>
        <p v-if="erro" class="text-sm text-red-500" role="alert">{{ erro }}</p>
        <button type="button" @click="marcar" :disabled="aMarcar || !escolhida" data-teste="confirmar"
          class="w-full py-3 rounded-xl text-white font-bold disabled:opacity-40 hover:brightness-110 transition" :style="{ backgroundColor: cor }">
          {{ !escolhida ? 'Escolhe o dia e a hora' : !autenticado ? 'Entrar para marcar'
             : pagamentoEfetivo === 'antecipado' ? `Marcar e pagar ${precoTexto}` : 'Confirmar marcação' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { estaAutenticado } from '@/services/sessao'
import { formatarDinheiro } from '@/utils/dinheiro'
import { DIAS_CURTOS, diaSemana, duracaoTexto, hora, rotuloDia } from '@/utils/servicos'

export const GUARDADO = 'servicos_escolha'

export default {
  name: 'ServicoModal',
  props: {
    lojaId: { type: [String, Number], required: true },
    servico: { type: Object, required: true },
    regras: { type: Object, default: () => ({}) },
    profissionais: { type: Array, default: () => [] },
    isDark: { type: Boolean, default: true },
    cor: { type: String, default: '#dc2626' },
    inicial: { type: Object, default: null },        // escolha guardada antes do login
  },
  emits: ['fechar'],
  data () {
    const i = this.inicial || {}
    return { foto: 0, profId: i.prof ?? null, dia: null, dias: [], horas: [], escolhida: null, aCarregar: false, aCarregarDias: false,
             notas: i.notas || '', pagamento: i.pagamento || (this.servico.pagamento === 'local' ? 'local' : 'antecipado'),
             erro: '', aMarcar: false, autenticado: estaAutenticado(), DIAS_CURTOS }
  },
  computed: {
    suave () { return this.isDark ? 'text-zinc-400' : 'text-zinc-500' },
    profs () { return this.regras.cliente_escolhe_profissional ? this.profissionais.filter(p => this.servico.profissionais.includes(p.id)) : [] },
    nomeProf () { return this.profs.find(p => p.id === this.profId)?.nome || (this.profs.length === 1 ? this.profs[0].nome : '') },
    pagamentoEfetivo () { return this.servico.pagamento === 'ambos' ? this.pagamento : this.servico.pagamento },
    precoTexto () { return formatarDinheiro(Number(this.servico.preco) || 0) },
  },
  async created () {
    await this.carregarDias(this.inicial?.dia)
    if (this.inicial?.inicio && this.horas.some(h => h.inicio === this.inicial.inicio)) this.escolhida = this.inicial.inicio
  },
  mounted () { document.body.style.overflow = 'hidden' },
  beforeUnmount () { document.body.style.overflow = '' },
  methods: {
    hora, rotuloDia, diaSemana, duracaoTexto,
    chip (ativo) {
      return ['px-3 py-1.5 rounded-xl border text-sm font-semibold',
              ativo ? 'text-white' : (this.isDark ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400')]
    },
    estiloChip (ativo) { return ativo ? { backgroundColor: this.cor, borderColor: this.cor } : {} },
    params () {
      const p = { servico: this.servico.id }
      if (this.profId) p.profissional = this.profId
      return p
    },
    // os dias com vagas; abre no pedido (se tiver vagas) ou no primeiro com vagas
    async carregarDias (preferido = null) {
      this.aCarregarDias = true
      try {
        const { data } = await api.get(`/app/lojas/${this.lojaId}/servicos/dias/`, { params: this.params() })
        this.dias = data.dias
        const ok = d => this.dias.some(x => x.dia === d && x.livres)
        this.dia = ok(preferido) ? preferido : ok(this.dia) ? this.dia : data.primeiro_livre
      } finally { this.aCarregarDias = false }
      await this.carregarHoras()
    },
    mudarProf (id) { this.profId = id; this.carregarDias(this.dia) },
    mudarDia (d) { this.dia = d; this.carregarHoras() },
    async carregarHoras () {
      this.escolhida = null
      this.horas = []
      if (!this.dia) return
      this.aCarregar = true
      try {
        this.horas = (await api.get(`/app/lojas/${this.lojaId}/servicos/horas/`, { params: { ...this.params(), dia: this.dia } })).data.horas
      } finally { this.aCarregar = false }
    },
    async marcar () {
      if (!this.autenticado) {
        sessionStorage.setItem(GUARDADO, JSON.stringify({ loja: String(this.lojaId), servico: this.servico.id, prof: this.profId, dia: this.dia,
                                                         inicio: this.escolhida, notas: this.notas, pagamento: this.pagamento }))
        this.$router.push({ name: 'Login', query: { seguinte: `/loja/${this.lojaId}?servico=${this.servico.id}` } })
        return
      }
      this.erro = ''; this.aMarcar = true
      try {
        const { data } = await api.post(`/app/lojas/${this.lojaId}/servicos/marcar/`, {
          servico_id: this.servico.id, profissional_id: this.profId, inicio: this.escolhida, pagamento: this.pagamentoEfetivo, notas: this.notas.trim() })
        let m = data
        if (m.pagamento === 'antecipado' && !m.pago && confirm(`Pagar ${formatarDinheiro(Number(m.preco_indicado))}?\n\n(Pagamento simulado)`)) {
          m = (await api.post(`/app/marcacoes/${m.id}/acao/`, { acao: 'pagar' })).data
        }
        this.$router.push({ path: `/minhas-marcacoes/${m.id}`, query: { nova: 1 } })
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível marcar.'
        this.carregarDias(this.dia)
      } finally { this.aMarcar = false }
    },
  },
}
</script>
