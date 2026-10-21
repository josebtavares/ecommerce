<template>
  <!-- Backoffice → Serviços: ligar o módulo (incluído na subscrição ou com subscrição própria em comissão)
       e as regras das marcações. GET /app/loja/<id>/servicos/ -->
  <div class="space-y-5" :class="aba === 'agenda' && dados?.ativo ? 'max-w-none' : 'max-w-4xl'" data-teste="servicos">
    <!-- profissional com conta mas sem gerir_marcacoes: só a sua agenda -->
    <AgendaServicos v-if="soAgenda" :loja-id="lojaId" :pode-gerir="false" />
    <div v-else-if="carregando" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <p v-else-if="erro && !dados" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <template v-else-if="dados">
      <!-- ═══ Desligado: activar ═══ -->
      <div v-if="!dados.ativo" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Serviços e marcações</p>
        <p class="text-2xl font-black text-zinc-100 mt-2">Vende serviços com marcação online</p>
        <p class="text-sm text-zinc-400 mt-1 max-w-2xl">
          Cortes, tratamentos, tatuagens, explicações… Os clientes escolhem o serviço, o profissional e a hora livre,
          e pagam já ou no local. Os produtos da loja continuam como estão.
        </p>

        <!-- à espera da 1.ª fatura (voltou a ligar depois de cancelar) -->
        <div v-if="aguardaPagamento" class="mt-5 rounded-xl border border-sky-500/30 bg-sky-500/10 p-4">
          <p class="text-sm font-bold text-sky-200">Falta pagar a 1.ª fatura ({{ euros(dados.fatura_pendente.valor) }})</p>
          <p class="text-xs text-sky-200/80 mt-1">O módulo abre assim que a fatura for paga.</p>
          <button v-if="dados.pode_pagar" type="button" @click="$emit('ver-subscricao')"
            class="mt-3 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Ir para a Subscrição</button>
        </div>

        <template v-else-if="dados.incluido">
          <p class="text-sm text-green-400 mt-4 font-semibold">
            <font-awesome-icon :icon="['fas', 'circle-check']" class="mr-1.5" />Incluído na tua subscrição — sem custo extra.
          </p>
          <button v-if="dados.pode_pagar" type="button" @click="ativar(null)" :disabled="aGuardar" data-teste="ativar"
            class="mt-4 px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
            Activar Serviços
          </button>
        </template>

        <!-- desligou mas a subscrição de Serviços ainda está paga -->
        <template v-else-if="dados.acesso">
          <p class="text-sm text-zinc-300 mt-4">
            A tua subscrição de Serviços ({{ dados.subscricao?.plano?.nome }}) continua activa
            <template v-if="dados.subscricao?.fim_agendado">até {{ data(dados.subscricao.fim_agendado) }}</template>.
          </p>
          <button v-if="dados.pode_pagar" type="button" @click="ativar(null)" :disabled="aGuardar" data-teste="ativar"
            class="mt-4 px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
            Voltar a ligar os Serviços
          </button>
        </template>

        <template v-else>
          <p class="text-sm text-zinc-300 mt-4">
            A tua loja está em comissão. Os Serviços têm uma subscrição própria (sem comissão nas marcações);
            os produtos continuam em comissão.
            <span v-if="!dados.ja_teve_teste && dados.dias_teste" class="text-green-400 font-semibold">
              Os primeiros {{ dados.dias_teste }} dias são grátis.
            </span>
          </p>
          <p v-if="!dados.planos.length" class="text-sm text-amber-300 mt-4">Ainda não há planos de Serviços disponíveis. Tenta mais tarde.</p>
          <div v-else class="grid sm:grid-cols-3 gap-3 mt-4">
            <div v-for="p in dados.planos" :key="p.id" class="rounded-xl border border-zinc-800 bg-zinc-800/40 p-4 flex flex-col"
                 :data-teste="`plano-${p.id}`">
              <p class="text-sm font-semibold text-zinc-100">{{ p.nome }}</p>
              <p class="text-xl font-black text-zinc-100 mt-1">{{ euros(p.preco) }}</p>
              <p class="text-[11px] text-zinc-500">{{ p.periodicidade_nome }}<template v-if="p.meses > 1"> · {{ euros(p.preco_mes) }}/mês</template></p>
              <p class="text-[11px] text-zinc-400 mt-2 flex-1">{{ limitesDe(p) }}</p>
              <p v-if="p.descricao" class="text-[11px] text-zinc-500 mt-1">{{ p.descricao }}</p>
              <button v-if="dados.pode_pagar" type="button" @click="ativar(p)" :disabled="aGuardar"
                class="mt-3 px-3 py-2 rounded-lg bg-zinc-100 hover:bg-white disabled:opacity-50 text-zinc-900 text-xs font-bold">
                {{ !dados.ja_teve_teste && dados.dias_teste ? `Começar ${dados.dias_teste} dias grátis` : 'Escolher este plano' }}
              </button>
            </div>
          </div>
        </template>
        <p v-if="!dados.pode_pagar" class="text-xs text-zinc-500 mt-4">Só o dono da loja pode activar os Serviços.</p>
      </div>

      <!-- ═══ Ligado ═══ -->
      <template v-else>
        <p v-if="!dados.acesso" role="alert" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <template v-if="dados.subscricao?.estado === 'suspensa'">
            As marcações novas estão paradas: a subscrição de Serviços está por pagar. A loja continua a vender.
          </template>
          <template v-else-if="aguardaPagamento">Falta pagar a 1.ª fatura da subscrição de Serviços.</template>
          <template v-else>A loja está em comissão e os Serviços precisam de uma subscrição própria.</template>
          <button v-if="dados.pode_pagar" type="button" @click="$emit('ver-subscricao')" class="underline font-semibold ml-1">Ver subscrição</button>
        </p>

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 flex flex-wrap items-start gap-4">
          <div class="flex-1 min-w-0">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Serviços e marcações</p>
            <p class="text-xl font-black text-zinc-100 mt-2">
              {{ dados.disponivel ? 'Activo — os clientes podem marcar' : 'Activo, mas sem marcações novas' }}
            </p>
            <p class="text-sm text-zinc-400 mt-1">{{ resumoCobranca }}</p>
            <p v-if="limitesTexto" class="text-xs text-zinc-500 mt-1">{{ limitesTexto }}</p>
          </div>
          <span :class="['px-3 py-1 rounded-full text-xs font-bold', dados.disponivel ? 'bg-green-500/15 text-green-400' : 'bg-amber-500/15 text-amber-300']">
            {{ dados.disponivel ? 'Disponível' : 'Parado' }}
          </span>
          <button v-if="dados.pode_pagar" type="button" @click="desativar" :disabled="aGuardar" data-teste="desativar"
            class="w-full sm:w-auto px-4 py-2 rounded-xl border border-zinc-700 text-zinc-300 hover:text-white text-xs font-semibold">
            Desligar Serviços
          </button>
        </div>

        <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 overflow-x-auto" role="tablist" aria-label="Serviços">
          <button v-for="a in abas" :key="a.k" type="button" role="tab" :aria-selected="aba === a.k" @click="aba = a.k" :data-teste="`aba-${a.k}`"
            :class="['flex-1 min-w-[90px] px-3 py-2 rounded-lg text-xs font-bold whitespace-nowrap', aba === a.k ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-200']">
            {{ a.t }}<span v-if="a.n !== undefined" class="ml-1 opacity-60">{{ a.n }}</span></button>
        </div>

        <!-- primeiros passos -->
        <div v-if="aba === 'agenda' && (!servicos.length || !profissionais.length)"
             class="rounded-xl border border-sky-500/30 bg-sky-500/10 px-4 py-3 text-sm text-sky-200">
          Para receber marcações: {{ !servicos.length ? 'cria os teus serviços' : '' }}{{ !servicos.length && !profissionais.length ? ' e ' : '' }}{{ !profissionais.length ? 'os profissionais' : '' }}
          <button type="button" class="underline font-semibold ml-1" @click="aba = !servicos.length ? 'servicos' : 'profissionais'">Começar</button>
        </div>

        <AgendaServicos v-if="aba === 'agenda'" :loja-id="lojaId" :servicos="servicos" :profissionais-todos="profissionais" :pode-gerir="true" />
        <CatalogoServicos v-else-if="aba === 'servicos'" :loja-id="lojaId" :profissionais="profissionais" :pode-gerir="dados.pode_gerir" @alterado="carregarListas" />
        <ProfissionaisServicos v-else-if="aba === 'profissionais'" :loja-id="lojaId" :profissionais="profissionais" :equipa="equipa"
          :limites="dados.limites" :servicos="servicos" :pode-gerir="dados.pode_gerir" @alterado="carregarListas" />

        <!-- Regras das marcações -->
        <form v-else-if="aba === 'regras' && dados.pode_gerir" @submit.prevent="guardarRegras" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-5"
              data-teste="regras">
          <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Regras das marcações</p>

          <div class="grid sm:grid-cols-2 gap-4">
            <label class="block">
              <span class="text-sm font-semibold text-zinc-200">Confirmação</span>
              <select v-model="regras.confirmacao" :class="[CAMPO, 'mt-1']">
                <option value="auto">Automática — o horário fica logo marcado</option>
                <option value="manual">A loja confirma cada marcação</option>
              </select>
            </label>
            <label class="block">
              <span class="text-sm font-semibold text-zinc-200">Antecedência mínima</span>
              <select v-model.number="regras.antecedencia_min" :class="[CAMPO, 'mt-1']">
                <option v-for="o in OPCOES_ANTECEDENCIA" :key="o.v" :value="o.v">{{ o.t }}</option>
              </select>
              <span class="text-[11px] text-zinc-500">Quanto tempo antes os clientes ainda podem marcar.</span>
            </label>
            <label class="block">
              <span class="text-sm font-semibold text-zinc-200">Marcar até quantos dias à frente</span>
              <input v-model.number="regras.dias_max" type="number" min="1" max="365" :class="[CAMPO, 'mt-1']" />
            </label>
            <label class="block">
              <span class="text-sm font-semibold text-zinc-200">O cliente pode cancelar até</span>
              <select v-model.number="regras.cancelar_horas" :class="[CAMPO, 'mt-1']">
                <option v-for="o in OPCOES_CANCELAR" :key="o.v" :value="o.v">{{ o.t }}</option>
              </select>
            </label>
            <label class="block sm:col-span-2">
              <span class="text-sm font-semibold text-zinc-200">Pagou antecipado e cancelou fora do prazo (ou faltou)</span>
              <select v-model="regras.reembolso_fora_prazo" :class="[CAMPO, 'mt-1']">
                <option value="nenhum">Não devolvemos o dinheiro</option>
                <option value="total">Devolvemos tudo</option>
              </select>
              <span class="text-[11px] text-zinc-500">O cliente vê esta regra antes de pagar.</span>
            </label>
          </div>

          <div class="space-y-3">
            <label class="flex items-start gap-3">
              <input v-model="regras.cliente_escolhe_profissional" type="checkbox" class="mt-1 accent-red-600" />
              <span>
                <span class="text-sm font-semibold text-zinc-200">O cliente escolhe o profissional</span>
                <span class="block text-[11px] text-zinc-500">Desligado: o cliente só escolhe a hora e a loja atribui o profissional.</span>
              </span>
            </label>
            <label class="flex items-start gap-3">
              <input v-model="regras.profissional_altera_preco" type="checkbox" class="mt-1 accent-red-600" />
              <span>
                <span class="text-sm font-semibold text-zinc-200">Os profissionais podem registar o preço final</span>
                <span class="block text-[11px] text-zinc-500">O dono e o gestor podem sempre.</span>
              </span>
            </label>
          </div>

          <div class="flex items-center gap-3">
            <button type="submit" :disabled="aGuardar || !mudou"
              class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Guardar regras</button>
            <span v-if="guardado" class="text-sm text-green-400" role="status">Guardado.</span>
          </div>
        </form>
      </template>

      <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import AgendaServicos from '@/components/servicos/AgendaServicos.vue'
import CatalogoServicos from '@/components/servicos/CatalogoServicos.vue'
import ProfissionaisServicos from '@/components/servicos/ProfissionaisServicos.vue'

const CAMPO = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500'
const OPCOES_ANTECEDENCIA = [
  { v: 0, t: 'Sem mínimo' }, { v: 30, t: '30 minutos' }, { v: 60, t: '1 hora' }, { v: 120, t: '2 horas' },
  { v: 240, t: '4 horas' }, { v: 720, t: '12 horas' }, { v: 1440, t: '1 dia' }, { v: 2880, t: '2 dias' },
]
const OPCOES_CANCELAR = [
  { v: 0, t: 'Até à hora marcada' }, { v: 2, t: '2 horas antes' }, { v: 6, t: '6 horas antes' }, { v: 12, t: '12 horas antes' },
  { v: 24, t: '24 horas antes' }, { v: 48, t: '48 horas antes' }, { v: 72, t: '3 dias antes' },
]

export default {
  name: 'BackofficeServicos',
  components: { AgendaServicos, CatalogoServicos, ProfissionaisServicos },
  props: {
    lojaId: { type: [String, Number], required: true },
    soAgenda: { type: Boolean, default: false },      // profissional com conta, sem gerir_marcacoes
  },
  emits: ['ver-subscricao'],

  data () {
    return { dados: null, carregando: true, erro: '', aGuardar: false, guardado: false, regras: {}, CAMPO, OPCOES_ANTECEDENCIA, OPCOES_CANCELAR,
             aba: 'agenda', servicos: [], profissionais: [], equipa: [] }
  },

  computed: {
    abas () {
      const a = [{ k: 'agenda', t: 'Agenda' }, { k: 'servicos', t: 'Serviços', n: this.servicos.length },
                 { k: 'profissionais', t: 'Profissionais', n: this.profissionais.length }]
      if (this.dados?.pode_gerir) a.push({ k: 'regras', t: 'Regras' })
      return a
    },
    aguardaPagamento () { return this.dados?.subscricao?.estado === 'aguarda' && !!this.dados.fatura_pendente },
    mudou () { return JSON.stringify(this.regras) !== JSON.stringify(this.dados?.config || {}) },
    resumoCobranca () {
      const d = this.dados
      if (d.incluido) return 'Incluído na subscrição da loja.'
      const s = d.subscricao
      if (!s) return 'Sem subscrição de Serviços.'
      if (s.estado === 'teste') return `Plano ${s.plano.nome} · teste grátis até ${this.data(s.teste_ate)}.`
      if (s.fim_agendado) return `Plano ${s.plano.nome} · termina a ${this.data(s.fim_agendado)}.`
      return `Plano ${s.plano.nome} · ${s.estado_nome.toLowerCase()}${s.pago_ate ? ' · pago até ' + this.data(s.pago_ate) : ''}.`
    },
    limitesTexto () {
      const l = this.dados?.limites || {}
      return this.textoLimites(l.marcacoes_mes, l.profissionais)
    },
  },

  created () { if (!this.soAgenda) this.carregar() },

  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s + 'T12:00:00').toLocaleDateString('pt-PT') : '' },
    textoLimites (m, p) {
      const partes = []
      if (m) partes.push(`${m} marcações por mês`)
      if (p) partes.push(p === 1 ? '1 profissional' : `${p} profissionais`)
      return partes.length ? 'Até ' + partes.join(' e ') + '.' : ''
    },
    limitesDe (p) { return this.textoLimites(p.limite_marcacoes_mes, p.limite_profissionais) || 'Sem limites de marcações nem de profissionais.' },
    aplicar (data) {
      this.dados = data
      // as opções da lista têm de conter o valor guardado (o servidor aceita qualquer número)
      this.regras = { ...data.config }
      if (data.ativo && !this.servicos.length && !this.profissionais.length) this.carregarListas()
    },
    async carregarListas () {
      const [s, p] = await Promise.all([api.get(`/app/loja/${this.lojaId}/servicos/catalogo/`),
                                        api.get(`/app/loja/${this.lojaId}/servicos/profissionais/`)])
      this.servicos = s.data
      this.profissionais = p.data.profissionais
      this.equipa = p.data.equipa
    },
    async carregar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/servicos/`)
        this.aplicar(data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar os Serviços.'
      } finally {
        this.carregando = false
      }
    },
    async pedido (fn) {
      this.erro = ''
      this.guardado = false
      this.aGuardar = true
      try {
        const { data } = await fn()
        this.aplicar(data)
        return data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
    async ativar (plano) {
      let texto = 'Activar os Serviços?'
      if (plano) {
        texto = !this.dados.ja_teve_teste && this.dados.dias_teste
          ? `Começar com o plano ${plano.nome}?\n\nOs primeiros ${this.dados.dias_teste} dias são grátis; depois pagas ${this.euros(plano.preco)} / ${plano.periodicidade_nome.toLowerCase()}.`
          : `Escolher o plano ${plano.nome} (${this.euros(plano.preco)} / ${plano.periodicidade_nome.toLowerCase()})?\n\nA 1.ª fatura vence hoje; os Serviços abrem quando a pagares.`
      }
      if (!confirm(texto)) return
      const data = await this.pedido(() => api.post(`/app/loja/${this.lojaId}/servicos/ativar/`, plano ? { plano_id: plano.id } : {}))
      if (data?.fatura_a_pagar && confirm('Pagar já a 1.ª fatura? Vais para o ecrã Subscrição.')) this.$emit('ver-subscricao')
    },
    async desativar () {
      const s = this.dados.subscricao
      const extra = s && !this.dados.incluido && s.pago_ate ? `\n\nA subscrição de Serviços acaba a ${this.data(s.pago_ate)} (o que já pagaste não é devolvido).` : ''
      if (!confirm(`Desligar os Serviços? Deixam de aparecer na loja.${extra}`)) return
      await this.pedido(() => api.post(`/app/loja/${this.lojaId}/servicos/desativar/`))
    },
    async guardarRegras () {
      const data = await this.pedido(() => api.patch(`/app/loja/${this.lojaId}/servicos/config/`, this.regras))
      if (data) this.guardado = true
    },
  },
}
</script>
