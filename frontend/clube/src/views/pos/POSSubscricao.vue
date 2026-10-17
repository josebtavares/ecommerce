<template>
  <!-- POS → Subscrição (só o dono): plano, faturas e pagamento (simulado).
       GET /api/pos/<id>/subscricao/ (app/pos/views_subscricao.py) -->
  <div class="mx-auto max-w-4xl space-y-5">
    <div v-if="carregando" class="h-40 animate-pulse rounded-[1.5rem] bg-slate-100"></div>
    <p v-else-if="erro && !dados" class="text-sm font-bold text-red-600" role="alert">{{ erro }}</p>

    <template v-else-if="dados">
      <p v-if="dados.aviso" role="alert"
         :class="['rounded-2xl border px-4 py-3 text-sm font-bold',
                  dados.aviso.tipo === 'vence' || dados.aviso.tipo === 'sem_plano'
                    ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-red-200 bg-red-50 text-red-700']">
        {{ dados.aviso.texto }}
      </p>

      <!-- ═══ Incluído no plano Loja + POS da loja ligada ═══ -->
      <div v-if="cob" class="rounded-[1.5rem] border border-slate-200 bg-white p-5 sm:p-6">
        <div class="flex flex-wrap items-start gap-4">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-black uppercase tracking-wider text-slate-400">Subscrição do POS</p>
            <p class="mt-2 text-2xl font-black text-slate-950">Incluído no plano da loja</p>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              A loja <span class="font-black text-slate-700">{{ cob.loja_nome }}</span> tem o plano
              <span class="font-black text-slate-700">{{ cob.plano.nome }}</span> ({{ euros(cob.plano.preco) }} / {{ cob.plano.meses === 1 ? 'mês' : cob.plano.meses + ' meses' }}),
              que cobre a loja e este POS. Não pagas o POS à parte.
            </p>
          </div>
          <span :class="['rounded-full px-3 py-1 text-xs font-black', cob.estado === 'suspensa' ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700']">
            {{ cob.estado === 'suspensa' ? 'Loja suspensa' : 'Incluído' }}
          </span>
        </div>
        <p class="mt-4 text-[11px] font-semibold text-slate-400">
          As faturas são da loja: vês e pagas no backoffice da loja → Subscrição. Se desligares o POS da loja (ou a loja mudar
          de plano), o POS fica 30 dias grátis e depois passa a ter o seu próprio plano.
        </p>
      </div>

      <!-- ═══ Estado ═══ -->
      <div v-else class="rounded-[1.5rem] border border-slate-200 bg-white p-5 sm:p-6">
        <div class="flex flex-wrap items-start gap-4">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-black uppercase tracking-wider text-slate-400">Subscrição do POS</p>
            <p v-if="!sub.plano" class="mt-2 text-2xl font-black text-slate-950">Sem plano escolhido</p>
            <p v-else-if="sub.plano_em_curso" class="mt-2 text-2xl font-black text-slate-950">{{ sub.plano_em_curso.nome }}
              <span class="block text-sm font-bold text-blue-600 sm:inline"><span class="hidden sm:inline">· </span>a partir de {{ data(diaSeguinte(sub.pago_ate)) }}: {{ sub.plano.nome }} ({{ euros(sub.preco) }})</span>
            </p>
            <p v-else class="mt-2 text-2xl font-black text-slate-950">{{ sub.plano.nome }}
              <span class="block text-sm font-bold text-slate-500 sm:inline"><span class="hidden sm:inline">· </span>{{ euros(sub.preco) }} / {{ sub.meses === 1 ? 'mês' : sub.meses + ' meses' }}</span>
            </p>
            <p class="mt-1 text-sm font-semibold" :class="sub.estado === 'em_atraso' || sub.estado === 'suspensa' ? 'text-red-600' : 'text-slate-500'">{{ resumoEstado }}</p>
          </div>
          <span :class="['rounded-full px-3 py-1 text-xs font-black', corEstado]">{{ sub.estado_nome }}</span>
        </div>

        <div class="mt-5 grid gap-3 sm:grid-cols-3">
          <div class="rounded-2xl bg-slate-50 px-4 py-3">
            <template v-if="sub.estado === 'teste' && sub.teste_ate">
              <p class="text-[11px] font-black uppercase tracking-wide text-slate-400">Grátis até</p>
              <p class="text-base font-black text-slate-950">{{ data(sub.teste_ate) }}</p>
              <p v-if="sub.pago_ate && sub.pago_ate > sub.teste_ate" class="text-[11px] font-bold text-emerald-600">e já pago até {{ data(sub.pago_ate) }}</p>
            </template>
            <template v-else>
              <p class="text-[11px] font-black uppercase tracking-wide text-slate-400">Pago até</p>
              <p class="text-base font-black text-slate-950">{{ sub.pago_ate ? data(sub.pago_ate) : '—' }}</p>
            </template>
          </div>
          <div class="rounded-2xl bg-slate-50 px-4 py-3">
            <p class="text-[11px] font-black uppercase tracking-wide text-slate-400">Por pagar</p>
            <p class="text-base font-black" :class="Number(dados.por_pagar) ? 'text-amber-600' : 'text-slate-950'">{{ euros(dados.por_pagar) }}</p>
          </div>
          <div class="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3">
            <div>
              <p class="text-[11px] font-black uppercase tracking-wide text-slate-400">Pagamento automático</p>
              <p class="text-sm font-bold text-slate-700">{{ sub.auto_renovar ? 'Ligado' : 'Desligado' }}</p>
            </div>
            <button type="button" role="switch" :aria-checked="sub.auto_renovar ? 'true' : 'false'" aria-label="Pagamento automático"
              @click="mudarAuto" :disabled="aGuardar"
              :class="['relative h-6 w-11 flex-shrink-0 rounded-full transition-colors', sub.auto_renovar ? 'bg-slate-950' : 'bg-slate-300']">
              <span :class="['absolute top-0.5 h-5 w-5 rounded-full bg-white shadow', sub.auto_renovar ? 'left-5.5' : 'left-0.5']" style="transition: left 0.2s"></span>
            </button>
          </div>
        </div>
        <p class="mt-3 text-[11px] font-semibold text-slate-400">
          Com o pagamento automático ligado, cada fatura é paga no dia em que vence. Os pagamentos ainda são simulados.
          A equipa do POS está incluída — não paga nada à parte.
        </p>
      </div>

      <!-- ═══ Planos ═══ -->
      <div v-if="podeEscolher" class="rounded-[1.5rem] border border-slate-200 bg-white p-5 sm:p-6">
        <p class="text-xs font-black uppercase tracking-wider text-slate-400">{{ sub.plano ? 'Mudar de plano' : 'Escolhe o teu plano' }}</p>
        <p v-if="!dados.planos.length" class="mt-2 text-sm font-semibold text-slate-500">Ainda não há planos disponíveis — a plataforma vai criá-los em breve.</p>
        <div v-else class="mt-3 grid gap-3 sm:grid-cols-3">
          <div v-for="p in dados.planos" :key="p.id"
               :class="['flex flex-col rounded-2xl border-2 p-4', atual(p) ? 'border-slate-950' : 'border-slate-200']">
            <p class="text-sm font-black text-slate-950">{{ p.nome }}</p>
            <p class="mt-1 text-xl font-black text-slate-950">{{ euros(p.preco) }}</p>
            <p class="text-[11px] font-semibold text-slate-500">{{ p.periodicidade_nome }}<template v-if="p.meses > 1"> · {{ euros(p.preco_mes) }}/mês</template></p>
            <p v-if="p.descricao" class="mt-2 flex-1 text-xs text-slate-500">{{ p.descricao }}</p>
            <span v-if="atual(p)" class="mt-3 text-center text-xs font-black text-slate-950">{{ sub.plano_seguinte ? 'Na próxima renovação' : 'O teu plano' }}</span>
            <button v-else type="button" @click="escolher(p)" :disabled="aGuardar"
              class="mt-3 h-10 rounded-xl bg-slate-950 text-xs font-black text-white transition hover:bg-slate-800 disabled:opacity-50">
              {{ !sub.plano ? 'Escolher' : p.id === sub.plano.id ? 'Manter este' : 'Mudar para este' }}
            </button>
          </div>
        </div>
        <p v-if="sub.plano && sub.plano_seguinte" class="mt-3 text-xs font-bold text-blue-600">
          A partir da próxima renovação passas para o plano {{ sub.plano_seguinte.nome }} ({{ euros(sub.plano_seguinte.preco) }}).
        </p>
        <p v-if="sub.plano" class="mt-2 text-xs font-semibold text-slate-400">O plano novo vale a partir da próxima renovação — o que já pagaste não muda.</p>
      </div>

      <!-- ═══ Plano Loja + POS (a loja ligada é do mesmo dono) ═══ -->
      <div v-if="loja && (cob || loja.planos_combo.length)" class="rounded-[1.5rem] border border-violet-200 bg-violet-50/40 p-5 sm:p-6">
        <p class="text-xs font-black uppercase tracking-wider text-violet-500">Plano Loja + POS</p>

        <!-- incluído: sair do plano -->
        <template v-if="cob">
          <p v-if="loja.plano_seguinte && loja.plano_seguinte.tipo === 'loja'" class="mt-2 text-sm font-bold text-slate-700">
            Na próxima renovação a loja passa para o plano {{ loja.plano_seguinte.nome }}. A partir daí o POS fica 30 dias grátis e depois
            {{ sub.plano ? `paga o plano ${sub.plano.nome} (${euros(sub.plano.preco)})` : 'precisa de um plano próprio' }}.
          </p>
          <template v-else>
            <p class="mt-2 text-sm font-semibold text-slate-600">Queres pagar a loja e o POS em separado? Escolhe o plano da loja e o do POS — muda na próxima renovação da loja.</p>
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <label class="block"><span class="text-[11px] font-black uppercase tracking-wide text-slate-400">Plano da loja</span>
                <select v-model="separar.loja" aria-label="Plano da loja" class="mt-1 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-700">
                  <option :value="null" disabled>Escolhe…</option>
                  <option v-for="p in loja.planos_loja" :key="p.id" :value="p.id">{{ p.nome }} — {{ euros(p.preco) }} / {{ p.periodicidade_nome.toLowerCase() }}</option>
                </select></label>
              <label class="block"><span class="text-[11px] font-black uppercase tracking-wide text-slate-400">Plano do POS</span>
                <select v-model="separar.pos" aria-label="Plano do POS" class="mt-1 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-700">
                  <option :value="null" disabled>Escolhe…</option>
                  <option v-for="p in dados.planos" :key="p.id" :value="p.id">{{ p.nome }} — {{ euros(p.preco) }} / {{ p.periodicidade_nome.toLowerCase() }}</option>
                </select></label>
            </div>
            <p v-if="!loja.planos_loja.length" class="mt-2 text-xs font-semibold text-slate-500">Ainda não há planos só de loja.</p>
            <button type="button" @click="sairCombo" :disabled="aGuardar || !separar.loja || (dados.planos.length && !separar.pos)"
              class="mt-3 h-10 rounded-xl bg-slate-950 px-4 text-xs font-black text-white hover:bg-slate-800 disabled:opacity-40">Pagar em separado</button>
          </template>
        </template>

        <!-- não incluído: passar a loja para Loja + POS -->
        <template v-else>
          <p v-if="loja.pedido" class="mt-2 text-sm font-bold text-slate-700">
            Pediste o plano {{ loja.pedido.nome }} para a loja {{ loja.loja_nome }}. Paga a 1.ª fatura no backoffice da loja → Subscrição —
            a partir daí a loja e o POS ficam num só plano.
          </p>
          <p v-else-if="loja.plano_seguinte && loja.plano_seguinte.tipo === 'loja_pos'" class="mt-2 text-sm font-bold text-slate-700">
            Na próxima renovação a loja {{ loja.loja_nome }} passa para o plano {{ loja.plano_seguinte.nome }} — a partir daí o POS fica incluído.
          </p>
          <template v-else>
            <p class="mt-2 text-sm font-semibold text-slate-600">
              Junta a loja {{ loja.loja_nome }} e este POS num só plano.
              <template v-if="loja.modelo === 'comissao'"> A loja está em comissão: passa para subscrição (sem comissão nas vendas) quando pagares a 1.ª fatura, que vence hoje, no backoffice da loja.</template>
              <template v-else> Muda na próxima renovação da loja.</template>
            </p>
            <p v-if="loja.troca_livre_em" class="mt-2 text-xs font-bold text-amber-700">A loja só pode mudar de modelo a partir de {{ data(loja.troca_livre_em) }}.</p>
            <div class="mt-3 grid gap-3 sm:grid-cols-3">
              <div v-for="p in loja.planos_combo" :key="p.id" class="flex flex-col rounded-2xl border-2 border-violet-200 bg-white p-4">
                <p class="text-sm font-black text-slate-950">{{ p.nome }}</p>
                <p class="mt-1 text-xl font-black text-slate-950">{{ euros(p.preco) }}</p>
                <p class="text-[11px] font-semibold text-slate-500">{{ p.periodicidade_nome }} · loja + POS</p>
                <p v-if="p.descricao" class="mt-2 flex-1 text-xs text-slate-500">{{ p.descricao }}</p>
                <button type="button" @click="passarCombo(p)" :disabled="aGuardar || !!loja.troca_livre_em"
                  class="mt-3 h-10 rounded-xl bg-violet-600 text-xs font-black text-white hover:bg-violet-500 disabled:opacity-40">Passar para este</button>
              </div>
            </div>
          </template>
        </template>
      </div>

      <!-- ═══ Faturas ═══ -->
      <div v-if="!cob || dados.faturas.length" class="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white">
        <p class="px-5 pb-3 pt-5 text-xs font-black uppercase tracking-wider text-slate-400 sm:px-6">Faturas</p>
        <p v-if="!dados.faturas.length" class="px-5 pb-6 text-sm font-semibold text-slate-500 sm:px-6">
          Ainda não há faturas.<template v-if="sub.plano && sub.estado === 'teste'"> A primeira chega 7 dias antes de acabar o período grátis.</template>
        </p>
        <div v-else class="divide-y divide-slate-100">
          <div v-for="f in dados.faturas" :key="f.id" class="flex flex-wrap items-center gap-3 px-5 py-4 sm:px-6">
            <div class="min-w-[200px] flex-1">
              <p class="text-sm font-bold text-slate-900">{{ f.descricao }}</p>
              <p class="text-xs font-semibold text-slate-500">
                <template v-if="f.estado === 'paga'">Paga a {{ data(f.paga_em) }} · {{ f.metodo_nome }}</template>
                <template v-else-if="f.estado === 'pendente'">Vence a {{ data(f.vencimento) }}<span v-if="f.atrasada" class="font-black text-red-600"> · em atraso</span></template>
                <template v-else>{{ f.notas || 'Anulada' }}</template>
              </p>
            </div>
            <span class="text-sm font-black text-slate-950">{{ euros(f.valor) }}</span>
            <span :class="['rounded-full px-2 py-0.5 text-[10px] font-black uppercase', corFatura(f)]">{{ f.atrasada ? 'Em atraso' : f.estado_nome }}</span>
            <button v-if="f.estado === 'paga'" type="button" @click="recibo(f)" :aria-label="`Recibo da fatura ${f.id}`"
              class="rounded-xl bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200">
              <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Recibo
            </button>
            <button v-if="f.estado === 'pendente'" type="button" @click="pagar(f)" :disabled="aPagar === f.id"
              class="rounded-xl bg-slate-950 px-4 py-2 text-xs font-black text-white hover:bg-slate-800 disabled:opacity-50">
              {{ aPagar === f.id ? 'A pagar…' : 'Pagar ' + euros(f.valor) }}
            </button>
          </div>
        </div>
      </div>

      <p v-if="erro" class="text-sm font-bold text-red-600" role="alert">{{ erro }}</p>
      <p v-if="aviso" class="text-sm font-bold text-emerald-600" role="status">{{ aviso }}</p>
    </template>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { gerarReciboSubscricao } from '@/utils/reciboSubscricao'

export default {
  name: 'POSSubscricao',
  props: { posId: { type: [String, Number], required: true } },
  emits: ['alterado'],

  data () {
    return { dados: null, carregando: true, erro: '', aviso: '', aPagar: null, aGuardar: false, separar: { loja: null, pos: null } }
  },

  computed: {
    sub () { return this.dados?.subscricao },
    cob () { return this.dados?.cobertura },
    loja () { return this.dados?.loja },
    podeEscolher () { return this.sub && !this.cob && ['teste', 'ativa', 'em_atraso'].includes(this.sub.estado) },
    resumoEstado () {
      const s = this.sub
      if (!s) return ''
      if (s.estado === 'suspensa') return 'O POS está suspenso — paga a fatura em atraso e volta logo.'
      if (s.estado === 'em_atraso') return 'Tens faturas em atraso — paga para evitar a suspensão do POS.'
      if (s.estado === 'teste') return s.plano ? `Período grátis até ${this.data(s.teste_ate)}.` : `Grátis até ${this.data(s.teste_ate)} — escolhe um plano antes de acabar.`
      if (s.estado === 'cancelada') return 'Esta subscrição foi cancelada.'
      return s.pago_ate ? `Tudo pago até ${this.data(s.pago_ate)}.` : ''
    },
    corEstado () {
      return { teste: 'bg-blue-50 text-blue-700', ativa: 'bg-emerald-50 text-emerald-700', em_atraso: 'bg-red-50 text-red-700',
               suspensa: 'bg-red-50 text-red-700', cancelada: 'bg-slate-100 text-slate-500' }[this.sub?.estado] || 'bg-slate-100 text-slate-600'
    },
  },

  created () { this.carregar() },

  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s.length === 10 ? s + 'T12:00:00' : s).toLocaleDateString('pt-PT') : '' },
    diaSeguinte (s) { const d = new Date(s + 'T12:00:00'); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10) },
    corFatura (f) {
      if (f.atrasada) return 'bg-red-50 text-red-700'
      return { paga: 'bg-emerald-50 text-emerald-700', pendente: 'bg-amber-50 text-amber-700', anulada: 'bg-slate-100 text-slate-500' }[f.estado]
    },
    atual (p) { return p.id === (this.sub.plano_seguinte || this.sub.plano)?.id },
    recibo (f) { gerarReciboSubscricao(f) },

    async carregar () {
      try {
        const { data } = await api.get(`/api/pos/${this.posId}/subscricao/`)
        this.dados = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar a subscrição.'
      } finally {
        this.carregando = false
      }
    },
    async enviar (pedido, ok) {
      this.erro = ''; this.aviso = ''
      try {
        const { data } = await pedido()
        this.dados = data
        if (ok) this.aviso = ok
        this.$emit('alterado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível concluir.'
      }
    },
    async pagar (f) {
      if (!confirm(`Pagar ${this.euros(f.valor)} — ${f.descricao}?\n\n(Pagamento simulado)`)) return
      this.aPagar = f.id
      await this.enviar(() => api.post(`/api/pos/${this.posId}/subscricao/faturas/${f.id}/pagar/`), 'Pagamento recebido. Obrigado!')
      this.aPagar = null
    },
    async escolher (p) {
      const msg = this.sub.plano
        ? `Mudar para o plano ${p.nome} (${this.euros(p.preco)})?\n\nVale a partir da próxima renovação.`
        : `Escolher o plano ${p.nome} (${this.euros(p.preco)})?`
      if (!confirm(msg)) return
      this.aGuardar = true
      await this.enviar(() => api.post(`/api/pos/${this.posId}/subscricao/plano/`, { plano_id: p.id }),
        this.sub.plano ? 'Plano mudado — vale a partir da próxima renovação.' : 'Plano escolhido.')
      this.aGuardar = false
    },
    async passarCombo (p) {
      const msg = this.loja.modelo === 'comissao'
        ? `Passar a loja ${this.loja.loja_nome} para o plano ${p.nome} (${this.euros(p.preco)})?\n\nA loja deixa a comissão quando pagares a 1.ª fatura (vence hoje) no backoffice da loja. Depois só podes voltar a mudar daqui a 3 meses.`
        : `Passar a loja ${this.loja.loja_nome} para o plano ${p.nome} (${this.euros(p.preco)})?\n\nVale a partir da próxima renovação da loja.`
      if (!confirm(msg)) return
      this.aGuardar = true
      await this.enviar(() => api.post(`/api/pos/${this.posId}/subscricao/loja/`, { acao: 'combo', plano_id: p.id }),
        this.loja.modelo === 'comissao' ? 'Pedido feito — paga a 1.ª fatura no backoffice da loja.' : 'Feito — muda na próxima renovação da loja.')
      this.aGuardar = false
    },
    async sairCombo () {
      if (!confirm('Pagar a loja e o POS em separado a partir da próxima renovação da loja?')) return
      this.aGuardar = true
      await this.enviar(() => api.post(`/api/pos/${this.posId}/subscricao/loja/`,
        { acao: 'separar', plano_id: this.separar.loja, plano_pos_id: this.separar.pos }),
        'Feito — a loja muda na próxima renovação; depois o POS tem 30 dias grátis.')
      this.aGuardar = false
    },
    async mudarAuto () {
      this.aGuardar = true
      await this.enviar(() => api.patch(`/api/pos/${this.posId}/subscricao/`, { auto_renovar: !this.sub.auto_renovar }))
      this.aGuardar = false
    },
  },
}
</script>
