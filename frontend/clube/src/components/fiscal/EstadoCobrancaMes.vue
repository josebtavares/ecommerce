<!-- EstadoCobrancaMes.vue — em que ponto está o pagamento das comissões de um mês (cobrança mensal):
     paga, em cobrança por pagar, parte paga ou ainda por cobrar. Backend: faturacaoView._estado_cobranca. -->
<template>
  <span v-if="cobranca" :class="['inline-block ml-1 px-1.5 py-0.5 rounded text-[10px] font-semibold align-middle', COR[cobranca.estado]]"
        data-teste="estado-cobranca-mes" :title="TITULO[cobranca.estado]">{{ cobranca.nome }}</span>
</template>

<script>
const COR = {
  paga: 'bg-green-500/15 text-green-400',
  por_pagar: 'bg-amber-500/15 text-amber-300',
  parcial: 'bg-sky-500/15 text-sky-300',
  por_cobrar: 'bg-zinc-800 text-zinc-400',
}
const TITULO = {
  paga: 'As comissões deste mês estão pagas',
  por_pagar: 'Já foram cobradas (cobrança mensal) e esperam pagamento',
  parcial: 'Parte das comissões deste mês já está paga',
  por_cobrar: 'Entram na próxima cobrança mensal',
}

export default {
  name: 'EstadoCobrancaMes',
  props: { cobranca: { type: Object, default: null } },
  data () { return { COR, TITULO } },
}
</script>
