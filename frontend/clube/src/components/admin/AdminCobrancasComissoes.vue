<!-- AdminCobrancasComissoes.vue — Admin → Comissões: cobranças mensais às lojas (gerir_pagamentos).
     Registar um pagamento recebido por fora (transferência, dinheiro, oferta), anular (solta as comissões para a
     cobrança seguinte) ou emitir já as que faltam. Atraso não suspende nada sozinho — decide-se aqui.
     Backend: /app/admin/comissoes/cobrancas/ (Views/cobrancaComissoesView.py). -->
<template>
  <div v-if="!semAcesso" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" data-teste="admin-cobrancas">
    <div class="px-5 pt-4 pb-3 flex flex-wrap items-center gap-3">
      <div class="flex-1 min-w-[200px]">
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Cobranças mensais</p>
        <p v-if="d" class="text-xs text-zinc-500 mt-0.5">
          Por pagar {{ $dinheiro(d.total_por_pagar) }}
          <template v-if="d.n_em_atraso"> · <span class="text-red-400 font-semibold">{{ d.n_em_atraso }} em atraso ({{ $dinheiro(d.total_em_atraso) }})</span></template>
        </p>
      </div>
      <div class="flex gap-1">
        <button v-for="f in FILTROS" :key="f.v" type="button" @click="estado = f.v; carregar()"
          :data-teste="`cobrancas-filtro-${f.v || 'todas'}`"
          :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                   estado === f.v ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">{{ f.label }}</button>
      </div>
      <button type="button" @click="emitir" :disabled="aEmitir" data-teste="cobrancas-emitir"
        title="Emite já as cobranças do mês anterior que ainda faltam (o worker fá-lo sozinho todos os dias)"
        class="px-3 py-1.5 rounded-lg text-xs font-bold bg-zinc-700 hover:bg-zinc-600 text-zinc-100 disabled:opacity-50">
        {{ aEmitir ? 'A emitir…' : 'Emitir em falta' }}
      </button>
    </div>
    <p v-if="msg" class="px-5 pb-3 text-xs" :class="msgOk ? 'text-green-400' : 'text-red-400'" role="status" data-teste="cobrancas-admin-msg">{{ msg }}</p>

    <p v-if="carregando" class="px-5 pb-5 text-xs text-zinc-500">A carregar…</p>
    <p v-else-if="!d?.resultados.length" class="px-5 pb-5 text-xs text-zinc-500">Sem cobranças{{ estado ? ' neste filtro' : '' }}.</p>
    <div v-else class="divide-y divide-zinc-800 border-t border-zinc-800">
      <div v-for="c in d.resultados" :key="c.id" class="px-5 py-3" data-teste="admin-cobranca">
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex-1 min-w-[180px]">
            <p class="text-sm font-semibold text-zinc-200">{{ c.loja_nome }} <span class="text-zinc-500 font-normal">· até {{ mes(c.mes) }}</span></p>
            <p class="text-xs text-zinc-500">
              {{ $dinheiro(c.valor_comissoes) }}<template v-if="Number(c.valor_creditos)"> − {{ $dinheiro(c.valor_creditos) }} créditos</template>
              · <template v-if="c.estado === 'paga'">paga {{ data(c.paga_em) }} ({{ c.metodo_nome }}<template v-if="c.referencia"> {{ c.referencia }}</template>)</template>
              <template v-else-if="c.estado === 'anulada'">anulada</template>
              <template v-else>vence {{ data(c.vencimento) }}</template>
            </p>
            <p v-if="c.notas" class="text-[11px] text-zinc-500 italic">{{ c.notas }}</p>
          </div>
          <span :class="['px-2 py-0.5 rounded-lg text-[11px] font-bold', cor(c)]">{{ c.em_atraso ? 'Em atraso' : c.estado_nome }}</span>
          <span class="text-sm font-bold text-zinc-100 w-28 text-right">{{ $dinheiro(c.valor) }}</span>
          <button v-if="c.estado === 'pendente'" type="button" @click="abrir(c)" :data-teste="`admin-cobranca-abrir-${c.id}`"
            class="px-3 py-1.5 rounded-lg text-xs font-bold bg-zinc-800 hover:bg-zinc-700 text-zinc-200">
            {{ aberta === c.id ? 'Fechar' : 'Registar' }}
          </button>
        </div>

        <div v-if="aberta === c.id" class="mt-3 grid sm:grid-cols-4 gap-2" data-teste="admin-cobranca-form">
          <select v-model="form.metodo" data-teste="admin-cobranca-metodo"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none">
            <option value="">Como foi pago?</option>
            <option v-for="m in d.metodos" :key="m.valor" :value="m.valor">{{ m.nome }}</option>
          </select>
          <input v-model="form.referencia" maxlength="100" placeholder="Referência (opcional)" data-teste="admin-cobranca-ref"
            class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none" />
          <input v-model="form.notas" maxlength="300" placeholder="Notas / motivo (obrigatório para oferta ou anular)" data-teste="admin-cobranca-notas"
            class="sm:col-span-2 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none" />
          <div class="sm:col-span-4 flex flex-wrap gap-2">
            <button type="button" @click="pagar(c)" :disabled="aGuardar || !form.metodo" data-teste="admin-cobranca-pagar"
              class="px-3 py-1.5 rounded-lg text-xs font-bold bg-green-600 hover:bg-green-500 text-white disabled:opacity-50">Registar pagamento</button>
            <button type="button" @click="anular(c)" :disabled="aGuardar" data-teste="admin-cobranca-anular"
              title="As comissões voltam a ficar por cobrar e entram na cobrança seguinte"
              class="px-3 py-1.5 rounded-lg text-xs font-bold bg-zinc-700 hover:bg-zinc-600 text-zinc-100 disabled:opacity-50">Anular</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const FILTROS = [
  { v: 'pendente', label: 'Por pagar' }, { v: 'atraso', label: 'Em atraso' }, { v: 'paga', label: 'Pagas' },
  { v: 'anulada', label: 'Anuladas' }, { v: '', label: 'Todas' },
]

export default {
  name: 'AdminCobrancasComissoes',

  props: {
    lojaId: { type: [String, Number], default: null },
  },

  emits: ['alterado'],

  data () {
    return { FILTROS, d: null, semAcesso: false, estado: 'pendente', carregando: true, aberta: null, form: this.novoForm(),
             aGuardar: false, aEmitir: false, msg: '', msgOk: false }
  },

  watch: { lojaId () { this.carregar() } },

  created () { this.carregar() },

  methods: {
    novoForm () { return { metodo: '', referencia: '', notas: '' } },
    data (iso) { return new Date(iso.length === 10 ? iso + 'T12:00:00' : iso).toLocaleDateString('pt-PT') },
    mes (iso) { const [a, m] = iso.split('-'); return `${m}/${a}` },
    cor (c) {
      if (c.em_atraso) return 'bg-red-500/15 text-red-400'
      return { paga: 'bg-green-500/15 text-green-400', anulada: 'bg-zinc-700 text-zinc-400' }[c.estado] || 'bg-amber-500/15 text-amber-300'
    },

    async carregar () {
      this.carregando = true
      const params = {}
      if (this.estado) params.estado = this.estado
      if (this.lojaId) params.loja_id = this.lojaId
      try { this.d = (await api.get('/app/admin/comissoes/cobrancas/', { params })).data }
      catch (e) { this.d = null; this.semAcesso = e.response?.status === 403; this.msg = e.response?.data?.detail || 'Não foi possível carregar.'; this.msgOk = false }
      finally { this.carregando = false }
    },

    abrir (c) { this.aberta = this.aberta === c.id ? null : c.id; this.form = this.novoForm(); this.msg = '' },

    async acao (c, corpo, ok) {
      this.aGuardar = true; this.msg = ''
      try {
        await api.post(`/app/admin/comissoes/cobrancas/${c.id}/`, corpo)
        this.msg = ok; this.msgOk = true; this.aberta = null
        await this.carregar()
        this.$emit('alterado')
      } catch (e) { this.msg = e.response?.data?.detail || 'Não foi possível.'; this.msgOk = false }
      finally { this.aGuardar = false }
    },

    pagar (c) {
      this.acao(c, { acao: 'pagar', ...this.form }, `Pagamento de ${c.loja_nome} registado.`)
    },

    anular (c) {
      if (!confirm(`Anular a cobrança de ${c.loja_nome}? As comissões entram na cobrança seguinte.`)) return
      this.acao(c, { acao: 'anular', motivo: this.form.notas }, 'Cobrança anulada.')
    },

    async emitir () {
      this.aEmitir = true; this.msg = ''
      try {
        const { data } = await api.post('/app/admin/comissoes/cobrancas/emitir/', this.lojaId ? { loja_id: this.lojaId } : {})
        this.msg = data.emitidas ? `${data.emitidas} cobrança(s) emitida(s).` : 'Nada por emitir (já emitidas, abaixo do mínimo ou cobrança desligada).'
        this.msgOk = true
        await this.carregar()
      } catch (e) { this.msg = e.response?.data?.detail || 'Não foi possível.'; this.msgOk = false }
      finally { this.aEmitir = false }
    },
  },
}
</script>
