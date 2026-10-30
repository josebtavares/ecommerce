<!-- CobrancasComissoes.vue — backoffice (Subscrição): o que a loja paga à Bende pelas comissões, uma vez por mês.
     A SISP não divide pagamentos: o dinheiro das vendas vai direto para a loja e a comissão cobra-se à parte.
     Backend: GET /app/loja/<id>/comissoes/cobrancas/, POST …/<cid>/pagar/ (utils/cobranca_comissoes.py). -->
<template>
  <div v-if="d && (d.ligada || d.cobrancas.length)" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden"
       data-teste="cobrancas-comissoes">
    <div class="px-6 pt-5 pb-3">
      <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider pb-1">Comissões a pagar</p>
      <p class="text-xs text-zinc-500">
        O dinheiro das tuas vendas vai direto para ti. No início de cada mês a Bende cobra as comissões do mês anterior
        (menos os créditos de reembolsos); tens {{ d.dias_para_pagar }} dias para pagar. Abaixo de {{ dinheiro(d.minimo) }} passa para o mês seguinte.
      </p>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 px-6 pb-4">
      <div class="rounded-xl bg-zinc-800/50 px-4 py-3">
        <p class="text-[11px] text-zinc-500 uppercase tracking-wide">Por pagar</p>
        <p class="text-base font-bold" :class="Number(d.por_pagar) ? 'text-amber-300' : 'text-zinc-100'" data-teste="cobrancas-por-pagar">{{ dinheiro(d.por_pagar) }}</p>
      </div>
      <div class="rounded-xl bg-zinc-800/50 px-4 py-3">
        <p class="text-[11px] text-zinc-500 uppercase tracking-wide">A acumular este mês</p>
        <p class="text-base font-bold text-zinc-100" data-teste="cobrancas-acumular">{{ dinheiro(d.a_acumular) }}</p>
      </div>
      <div v-if="Number(d.creditos)" class="rounded-xl bg-zinc-800/50 px-4 py-3">
        <p class="text-[11px] text-zinc-500 uppercase tracking-wide">Créditos a descontar</p>
        <p class="text-base font-bold text-green-400">−{{ dinheiro(d.creditos) }}</p>
      </div>
    </div>

    <div v-if="d.cobrancas.length" class="divide-y divide-zinc-800 border-t border-zinc-800">
      <div v-for="c in d.cobrancas" :key="c.id" class="px-6 py-4 flex flex-wrap items-center gap-3" data-teste="cobranca">
        <div class="flex-1 min-w-[180px]">
          <p class="text-sm font-semibold text-zinc-200">Comissões até {{ nomeMes(c.mes) }}</p>
          <p class="text-xs text-zinc-500">
            <template v-if="Number(c.valor_creditos)">{{ dinheiro(c.valor_comissoes) }} − {{ dinheiro(c.valor_creditos) }} de créditos · </template>
            <template v-if="c.estado === 'paga'">paga a {{ data(c.paga_em) }} ({{ c.metodo_nome }})</template>
            <template v-else>vence a {{ data(c.vencimento) }}</template>
          </p>
        </div>
        <span :class="['px-2 py-0.5 rounded-lg text-[11px] font-bold', cor(c)]">{{ c.em_atraso ? 'Em atraso' : c.estado_nome }}</span>
        <span class="text-sm font-bold text-zinc-100 w-28 text-right">{{ dinheiro(c.valor) }}</span>
        <button v-if="c.estado === 'pendente' && d.pode_pagar" type="button" @click="pagar(c)" :disabled="aPagar === c.id"
          data-teste="cobranca-pagar"
          class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold">
          {{ aPagar === c.id ? 'A pagar…' : 'Pagar' }}
        </button>
      </div>
    </div>
    <p v-else class="px-6 pb-5 text-xs text-zinc-500">Ainda não há cobranças.</p>
    <p v-if="msg" class="px-6 pb-4 text-xs" :class="msgOk ? 'text-green-400' : 'text-red-400'" role="status" data-teste="cobrancas-msg">{{ msg }}</p>
    <p v-if="d.cobrancas.some(c => c.estado === 'pendente')" class="px-6 pb-5 text-[11px] text-zinc-500">
      Preferes transferência? Fala com a Bende pelo chat de suporte — registamos o pagamento quando recebermos.
    </p>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { seguirPagamento } from '@/utils/pagamentoOnline'

const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

export default {
  name: 'CobrancasComissoes',

  props: {
    lojaId: { type: [String, Number], required: true },
  },

  emits: ['alterado'],

  data () {
    return { d: null, aPagar: null, msg: '', msgOk: false }
  },

  created () { this.carregar() },

  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v)) },
    data (iso) { return new Date(iso.length === 10 ? iso + 'T12:00:00' : iso).toLocaleDateString('pt-PT') },
    nomeMes (iso) { const [a, m] = iso.split('-'); return `${MESES[Number(m) - 1]} de ${a}` },
    cor (c) {
      if (c.em_atraso) return 'bg-red-500/15 text-red-400'
      return c.estado === 'paga' ? 'bg-green-500/15 text-green-400' : 'bg-amber-500/15 text-amber-300'
    },

    async carregar () {
      try { this.d = (await api.get(`/app/loja/${this.lojaId}/comissoes/cobrancas/`)).data } catch { this.d = null }
    },

    async pagar (c) {
      if (!confirm(`Pagar ${this.dinheiro(c.valor)} de comissões à Bende?\n\n(Pagamento simulado)`)) return
      this.aPagar = c.id; this.msg = ''
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/comissoes/cobrancas/${c.id}/pagar/`)
        if (seguirPagamento(data)) return
        this.d = data
        this.msg = 'Pagamento recebido. Obrigado!'; this.msgOk = true
        this.$emit('alterado')
      } catch (e) {
        this.msg = e.response?.data?.detail || 'Não foi possível pagar.'; this.msgOk = false
      } finally { this.aPagar = null }
    },
  },
}
</script>
