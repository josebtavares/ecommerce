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

      <!-- ═══ Estado ═══ -->
      <div class="rounded-[1.5rem] border border-slate-200 bg-white p-5 sm:p-6">
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

      <!-- ═══ Faturas ═══ -->
      <div class="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white">
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
import api from '@/services/api'
import { gerarReciboSubscricao } from '@/utils/reciboSubscricao'

export default {
  name: 'POSSubscricao',
  props: { posId: { type: [String, Number], required: true } },
  emits: ['alterado'],

  data () {
    return { dados: null, carregando: true, erro: '', aviso: '', aPagar: null, aGuardar: false }
  },

  computed: {
    sub () { return this.dados?.subscricao },
    podeEscolher () { return this.sub && ['teste', 'ativa', 'em_atraso'].includes(this.sub.estado) },
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
    euros (v) { return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0) },
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
    async mudarAuto () {
      this.aGuardar = true
      await this.enviar(() => api.patch(`/api/pos/${this.posId}/subscricao/`, { auto_renovar: !this.sub.auto_renovar }))
      this.aGuardar = false
    },
  },
}
</script>
