<template>
  <!-- /loja/:id/servicos — o cliente escolhe o serviço, o profissional, o dia e a hora, e marca -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b"
            :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar à loja" @click="$router.push(`/loja/${lojaId}`)"
              class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <img v-if="dados?.loja?.logo" :src="dados.loja.logo" alt="" class="w-8 h-8 rounded-lg object-cover" />
      <h1 class="font-bold truncate flex-1">{{ dados?.loja?.nome || 'Serviços' }}</h1>
      <button type="button" class="h-9 w-9 rounded-lg flex items-center justify-center" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'"
              @click="alternarTema" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', isDark ? 'sun' : 'moon']" />
      </button>
    </header>

    <div v-if="carregando" class="flex justify-center py-20"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" /></div>
    <div v-else-if="!dados?.disponivel" class="max-w-md mx-auto text-center py-20 px-4">
      <p class="text-sm" :class="suave">Esta loja não está a aceitar marcações de momento.</p>
      <button type="button" @click="$router.push(`/loja/${lojaId}`)" class="mt-4 text-sm text-red-500 font-semibold">Voltar à loja</button>
    </div>

    <main v-else class="max-w-5xl mx-auto px-4 py-5 pb-28 grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_380px] gap-5 items-start">
      <!-- ═══ serviços ═══ -->
      <section class="space-y-5 min-w-0" data-teste="lista-servicos">
        <div v-for="(lista, cat) in porCategoria" :key="cat" class="space-y-2">
          <p v-if="cat" class="text-xs font-bold uppercase tracking-wider" :class="suave">{{ cat }}</p>
          <button v-for="s in lista" :key="s.id" type="button" @click="escolher(s)" :data-teste="`servico-${s.id}`"
            :class="['w-full text-left rounded-2xl border p-3 flex gap-3 transition',
                     servico?.id === s.id ? 'border-red-500 ring-1 ring-red-500' : (isDark ? 'border-zinc-800 bg-zinc-900 hover:border-zinc-600' : 'border-gray-200 bg-white hover:border-gray-400')]">
            <img v-if="s.imagens.length" :src="s.imagens[0]" alt="" class="w-20 h-20 rounded-xl object-cover flex-shrink-0" />
            <span class="flex-1 min-w-0">
              <span class="block font-semibold">{{ s.nome }}</span>
              <span class="block text-sm" :class="suave">{{ duracaoTexto(s.duracao_min) }} · <b :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ s.preco_texto }}</b></span>
              <span v-if="s.descricao" class="block text-xs mt-1 line-clamp-2" :class="suave">{{ s.descricao }}</span>
            </span>
          </button>
        </div>
      </section>

      <!-- ═══ marcar ═══ -->
      <section ref="painel" class="rounded-2xl border p-4 space-y-4 lg:sticky lg:top-20 min-w-0" :class="cartao" data-teste="painel-marcar">
        <p v-if="!servico" class="text-sm text-center py-6" :class="suave">Escolhe um serviço para ver as horas livres.</p>
        <template v-else>
          <div>
            <p class="font-bold">{{ servico.nome }}</p>
            <p class="text-sm" :class="suave">{{ duracaoTexto(servico.duracao_min) }} · {{ servico.preco_texto }}</p>
            <p v-if="servico.tipo_preco === 'a_partir'" class="text-[11px] mt-1" :class="suave">O preço final acerta-se com a loja (podes falar com ela depois de marcar).</p>
          </div>

          <div v-if="profsDoServico.length > 1">
            <p class="text-xs font-semibold mb-1.5" :class="suave">Com quem?</p>
            <div class="flex flex-wrap gap-2" role="radiogroup" aria-label="Profissional">
              <button type="button" role="radio" :aria-checked="profId === null" @click="mudarProf(null)" :class="chip(profId === null)">Qualquer um</button>
              <button v-for="p in profsDoServico" :key="p.id" type="button" role="radio" :aria-checked="profId === p.id" @click="mudarProf(p.id)"
                :class="[chip(profId === p.id), 'flex items-center gap-1.5']">
                <img v-if="p.foto" :src="p.foto" alt="" class="w-5 h-5 rounded-full object-cover" />{{ p.nome }}
              </button>
            </div>
          </div>
          <p v-else-if="profsDoServico.length === 1" class="text-xs" :class="suave">Com {{ profsDoServico[0].nome }}</p>

          <div>
            <p class="text-xs font-semibold mb-1.5" :class="suave">Dia</p>
            <div class="flex gap-1.5 overflow-x-auto pb-1" role="radiogroup" aria-label="Dia">
              <button v-for="d in diasPossiveis" :key="d" type="button" role="radio" :aria-checked="dia === d" @click="mudarDia(d)"
                :class="[chip(dia === d), 'flex-shrink-0 flex flex-col items-center leading-tight min-w-[52px]']" :data-teste="`dia-${d}`">
                <span class="text-[10px] uppercase">{{ DIAS_CURTOS[diaSemana(d)] }}</span>
                <span class="text-sm font-bold">{{ d.slice(8) }}</span>
              </button>
            </div>
          </div>

          <div v-if="dia">
            <p class="text-xs font-semibold mb-1.5" :class="suave">Hora</p>
            <p v-if="aCarregar" class="text-xs" :class="suave">A ver as horas livres…</p>
            <p v-else-if="!horas.length" class="text-xs text-amber-500">Sem horas livres neste dia. Experimenta outro.</p>
            <div v-else class="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Hora">
              <button v-for="h in horas" :key="h.inicio" type="button" role="radio" :aria-checked="escolhida === h.inicio" @click="escolhida = h.inicio"
                :class="[chip(escolhida === h.inicio), 'tabular-nums']">{{ hora(h.inicio) }}</button>
            </div>
          </div>

          <template v-if="escolhida">
            <label class="block"><span class="text-xs font-semibold" :class="suave">Nota para a loja (opcional)</span>
              <textarea v-model="notas" rows="2" maxlength="500" placeholder="ex.: a ideia da tatuagem, o comprimento do cabelo…"
                class="mt-1 w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500 resize-none"
                :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea></label>

            <fieldset v-if="servico.pagamento === 'ambos'" class="space-y-1.5">
              <legend class="text-xs font-semibold mb-1" :class="suave">Pagamento</legend>
              <label v-for="o in [{ v: 'antecipado', t: 'Pagar já' }, { v: 'local', t: 'Pagar no local' }]" :key="o.v"
                class="flex items-center gap-2 text-sm"><input type="radio" :value="o.v" v-model="pagamento" class="accent-red-600" />{{ o.t }}</label>
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
            <p v-if="erro" class="text-sm text-red-500" role="alert">{{ erro }}</p>
            <button type="button" @click="marcar" :disabled="aMarcar" data-teste="confirmar"
              class="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold">
              {{ !autenticado ? 'Entrar para marcar' : pagamentoEfetivo === 'antecipado' ? `Marcar e pagar ${precoTexto}` : 'Confirmar marcação' }}
            </button>
          </template>
        </template>
      </section>
    </main>
  </div>
</template>

<script>
import api from '@/services/api'
import { estaAutenticado } from '@/services/sessao'
import { formatarDinheiro } from '@/utils/dinheiro'
import { DIAS_CURTOS, diaSemana, duracaoTexto, hojeCV, hora, rotuloDia, somarDias } from '@/utils/servicos'

const GUARDADO = 'servicos_escolha'

export default {
  name: 'LojaServicos',
  data () {
    return { dados: null, carregando: true, servico: null, profId: null, dia: null, horas: [], escolhida: null, aCarregar: false,
             notas: '', pagamento: 'antecipado', erro: '', aMarcar: false, autenticado: estaAutenticado(),
             isDark: localStorage.getItem('theme_preference') !== 'light', DIAS_CURTOS }
  },
  computed: {
    lojaId () { return this.$route.params.id },
    regras () { return this.dados?.regras || {} },
    cartao () { return this.isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200' },
    suave () { return this.isDark ? 'text-zinc-400' : 'text-zinc-500' },
    porCategoria () {
      const out = {}
      ;(this.dados?.servicos || []).forEach(s => { (out[s.categoria || ''] = out[s.categoria || ''] || []).push(s) })
      return out
    },
    profsDoServico () {
      if (!this.servico || !this.regras.cliente_escolhe_profissional) return []
      return (this.dados.profissionais || []).filter(p => this.servico.profissionais.includes(p.id))
    },
    nomeProf () { return this.profsDoServico.find(p => p.id === this.profId)?.nome || (this.profsDoServico.length === 1 ? this.profsDoServico[0].nome : '') },
    diasPossiveis () { return Array.from({ length: Math.min(this.regras.dias_max || 30, 30) }, (_, i) => somarDias(hojeCV(), i)) },
    pagamentoEfetivo () { return this.servico?.pagamento === 'ambos' ? this.pagamento : this.servico?.pagamento },
    precoTexto () { return formatarDinheiro(Number(this.servico?.preco) || 0) },
  },
  async created () {
    try {
      this.dados = (await api.get(`/app/lojas/${this.lojaId}/servicos/publico/`)).data
      this.repor()
    } finally { this.carregando = false }
  },
  methods: {
    hora, rotuloDia, diaSemana, duracaoTexto,
    chip (ativo) {
      return ['px-3 py-1.5 rounded-xl border text-sm font-semibold',
              ativo ? 'border-red-500 bg-red-600 text-white' : (this.isDark ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400')]
    },
    escolher (s) {
      this.servico = s
      this.profId = null
      this.escolhida = null
      this.pagamento = s.pagamento === 'local' ? 'local' : 'antecipado'
      this.erro = ''
      if (!this.dia) this.dia = hojeCV()
      this.carregarHoras()
      if (window.innerWidth < 1024) this.$nextTick(() => this.$refs.painel?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    },
    mudarProf (id) { this.profId = id; this.carregarHoras() },
    mudarDia (d) { this.dia = d; this.carregarHoras() },
    async carregarHoras () {
      this.escolhida = null
      if (!this.servico || !this.dia) return
      this.aCarregar = true
      try {
        const params = { servico: this.servico.id, dia: this.dia }
        if (this.profId) params.profissional = this.profId
        this.horas = (await api.get(`/app/lojas/${this.lojaId}/servicos/horas/`, { params })).data.horas
      } finally { this.aCarregar = false }
    },
    // voltou do login: repõe o que tinha escolhido
    repor () {
      let g = null
      try { g = JSON.parse(sessionStorage.getItem(GUARDADO) || 'null') } catch { g = null }
      sessionStorage.removeItem(GUARDADO)
      if (!g || String(g.loja) !== String(this.lojaId)) return
      const s = this.dados.servicos.find(x => x.id === g.servico)
      if (!s) return
      this.servico = s
      this.profId = g.prof
      this.dia = g.dia
      this.notas = g.notas || ''
      this.pagamento = g.pagamento || this.pagamento
      this.carregarHoras().then(() => { if (this.horas.some(h => h.inicio === g.inicio)) this.escolhida = g.inicio })
    },
    async marcar () {
      if (!this.autenticado) {
        sessionStorage.setItem(GUARDADO, JSON.stringify({ loja: this.lojaId, servico: this.servico.id, prof: this.profId, dia: this.dia,
                                                         inicio: this.escolhida, notas: this.notas, pagamento: this.pagamento }))
        this.$router.push({ name: 'Login', query: { seguinte: this.$route.fullPath } })
        return
      }
      this.erro = ''; this.aMarcar = true
      try {
        const { data } = await api.post(`/app/lojas/${this.lojaId}/servicos/marcar/`, {
          servico_id: this.servico.id, profissional_id: this.profId, inicio: this.escolhida,
          pagamento: this.pagamentoEfetivo, notas: this.notas.trim() })
        let m = data
        if (m.pagamento === 'antecipado' && !m.pago) {
          // pagamento simulado (como no checkout)
          if (confirm(`Pagar ${formatarDinheiro(Number(m.preco_indicado))}?\n\n(Pagamento simulado)`)) {
            m = (await api.post(`/app/marcacoes/${m.id}/acao/`, { acao: 'pagar' })).data
          }
        }
        this.$router.push({ path: `/minhas-marcacoes/${m.id}`, query: { nova: 1 } })
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível marcar.'
        this.carregarHoras()
      } finally { this.aMarcar = false }
    },
    alternarTema () {
      this.isDark = !this.isDark
      localStorage.setItem('theme_preference', this.isDark ? 'dark' : 'light')
    },
  },
}
</script>
