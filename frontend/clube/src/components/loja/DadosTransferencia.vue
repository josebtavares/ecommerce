<!-- DadosTransferencia.vue — encomenda por pagar por transferência: para onde transferir, quanto e com que referência.
     dados: EncomendaSerializer.transferencia (utils/banco.dados_transferencia) — só o vê quem encomendou. -->
<template>
  <div class="rounded-2xl border p-5 text-left space-y-2"
       :class="isDark ? 'bg-zinc-900 border-amber-500/30' : 'bg-amber-50 border-amber-200'" data-teste="dados-transferencia">
    <p class="text-xs font-bold uppercase tracking-wider pb-1" :class="isDark ? 'text-amber-300' : 'text-amber-700'">
      Falta transferir
    </p>
    <!-- o IBAN, no telemóvel, por baixo do rótulo: cabe numa linha -->
    <div v-for="l in linhas" :key="l.r" class="flex justify-between gap-3 text-sm"
         :class="l.mono ? 'flex-col gap-0.5 sm:flex-row sm:items-center' : 'items-center'">
      <span class="flex-shrink-0" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ l.r }}</span>
      <span class="flex items-center gap-2 min-w-0">
        <span class="text-right font-medium" :class="[isDark ? 'text-zinc-100' : 'text-zinc-900', l.mono ? 'font-mono text-xs sm:text-sm break-words' : 'break-all']"
              :data-teste="l.teste">{{ l.v }}</span>
        <button v-if="l.copiar" type="button" @click="copiar(l)" :aria-label="`Copiar ${l.r}`"
          class="text-[11px] font-semibold flex-shrink-0" :class="copiado === l.r ? 'text-green-500' : 'text-red-500 hover:text-red-400'">
          {{ copiado === l.r ? 'Copiado' : 'Copiar' }}
        </button>
      </span>
    </div>
    <p class="text-xs pt-1" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
      Põe a referência no descritivo da transferência. A loja confirma quando o dinheiro chegar.
      Também te enviámos estes dados por email.
    </p>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'

export default {
  name: 'DadosTransferencia',

  props: {
    dados:  { type: Object, required: true },
    isDark: { type: Boolean, default: true },
  },

  data () {
    return { copiado: '' }
  },

  computed: {
    linhas () {
      const d = this.dados
      return [
        { r: 'Valor', v: formatarDinheiro(Number(d.valor)), copiar: Number(d.valor).toFixed(2).replace('.', ','), teste: 'transf-valor' },
        { r: 'IBAN', v: d.iban, copiar: d.iban_simples, mono: true, teste: 'transf-iban' },
        { r: 'Titular', v: d.titular, teste: 'transf-titular' },
        { r: 'Banco', v: d.banco },
        { r: 'Referência', v: d.referencia, copiar: d.referencia, teste: 'transf-ref' },
      ]
    },
  },

  methods: {
    async copiar (l) {
      try {
        await navigator.clipboard.writeText(l.copiar)
        this.copiado = l.r
        setTimeout(() => { if (this.copiado === l.r) this.copiado = '' }, 2000)
      } catch (e) { /* sem acesso à área de transferência: o texto está à vista */ }
    },
  },
}
</script>
