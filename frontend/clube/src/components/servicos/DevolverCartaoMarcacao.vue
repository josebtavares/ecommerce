<template>
  <!-- Marcação paga com cartão vinti4 (o dinheiro está na loja): a loja devolve por estorno no Portal do Comerciante
       (o normal) ou, quando o estorno não dá, de outra forma com prova em foto — o cliente confirma "Recebi".
       Igual às encomendas (BackofficeReembolso). -->
  <section class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 space-y-2" data-teste="devolver-cartao-marcacao">
    <p class="text-sm text-amber-100">Devolve <b>{{ dinheiro(info.valor) }}</b> ao cliente.</p>

    <!-- à espera do cliente -->
    <p v-if="info.outra_forma" class="text-xs text-zinc-300" data-teste="outra-forma-espera">
      Devolveste de outra forma a {{ data(info.outra_forma.em) }}: {{ info.outra_forma.nota }}<template v-if="info.outra_forma.referencia">
      (referência {{ info.outra_forma.referencia }})</template>. À espera da confirmação do cliente — fica confirmado sozinho a
      {{ data(info.outra_forma.prazo) }}.
    </p>

    <template v-else>
      <p v-if="info.nao_recebida_em" class="text-xs text-red-300" role="alert" data-teste="nao-recebida">
        O cliente diz que não recebeu a devolução de outra forma. A Bendi vai analisar — fala com o cliente pelas mensagens.
        Podes fazer o estorno ou devolver outra vez (com nova prova).</p>
      <div class="flex gap-1 rounded-xl bg-zinc-900 p-1 text-xs" role="tablist">
        <button v-for="o in COMO" :key="o.v" type="button" role="tab" :aria-selected="como === o.v" @click="como = o.v"
          :data-teste="`devolver-${o.v}`"
          :class="['flex-1 py-1.5 rounded-lg font-semibold', como === o.v ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200']">
          {{ o.t }}</button>
      </div>
      <template v-if="como === 'estorno'">
        <!-- regra da SISP (MOP021 2.3, cond. 3): estorno noutro dia só até ao total de compras com cartão desse dia -->
        <p class="text-xs text-zinc-400">
          Faz o estorno no Portal do Comerciante (dá para devolver só parte do valor). Se não for no dia do pagamento, a SISP
          só deixa estornar até ao total das vendas com cartão do dia em que o fazes — se recusar, tenta noutro dia ou usa
          «Devolvi de outra forma».</p>
        <input v-model.trim="referencia" maxlength="100" placeholder="Referência do estorno (opcional)" :class="campo" />
        <p class="text-[11px] text-zinc-500">Ajuda o cliente a encontrar o estorno no banco. Com o ficheiro VBVT em Pagamentos, a SISP confirma-o.</p>
      </template>
      <template v-else>
        <p class="text-xs text-zinc-400">Quando o estorno não for possível (ex.: cartão cancelado) ou se devolveste ao balcão
          ou combinaste outra forma com o cliente. O cliente vê a prova e confirma que recebeu.</p>
        <textarea v-model="nota" rows="2" maxlength="500" placeholder="Como devolveste? (ex.: em dinheiro ao balcão, transferência)"
          data-teste="outra-forma-nota" :class="[campo, 'resize-none']"></textarea>
        <input v-model.trim="referencia" maxlength="100" placeholder="Referência (opcional)" :class="campo" />
        <label class="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
          <span class="px-3 py-1.5 rounded-lg border border-zinc-700 hover:bg-zinc-800">Juntar prova (obrigatório)</span>
          <span class="text-zinc-500">{{ provas.length ? `${provas.length} foto(s)` : '' }}</span>
          <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple class="hidden" data-teste="outra-forma-prova" @change="juntar" />
        </label>
      </template>
      <button type="button" @click="enviar" :disabled="aEnviar || !pronto" data-teste="devolver-confirmar"
        class="w-full py-2.5 rounded-xl text-sm font-bold text-white bg-green-600 hover:bg-green-500 disabled:opacity-50">
        {{ como === 'estorno' ? 'Marcar estorno feito' : 'Devolvi de outra forma' }}</button>
    </template>
  </section>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'

const COMO = [{ v: 'estorno', t: 'Estorno no cartão' }, { v: 'outro', t: 'Devolvi de outra forma' }]

export default {
  name: 'DevolverCartaoMarcacao',
  props: {
    info: { type: Object, required: true },        // marcacao.reembolso_por_concluir
    aEnviar: { type: Boolean, default: false },
  },
  emits: ['estorno', 'outra'],
  data () {
    return { como: 'estorno', referencia: '', nota: '', provas: [], COMO,
             campo: 'w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-500' }
  },
  computed: {
    pronto () {
      if (this.como === 'estorno') return !this.referencia || this.referencia.length >= 3
      return this.nota.trim().length >= 5 && this.provas.length > 0
    },
  },
  methods: {
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s).toLocaleDateString('pt-PT') : '' },
    juntar (ev) {
      const boas = [...ev.target.files].filter(f => f.size <= 10 * 1024 * 1024)
      ev.target.value = ''
      this.provas = [...this.provas, ...boas].slice(0, 5)
    },
    enviar () {
      if (this.como === 'estorno') return this.$emit('estorno', { referencia: this.referencia, nota: '' })
      const fd = new FormData()
      fd.append('acao', 'devolvido_outra_forma')
      fd.append('nota', this.nota.trim())
      fd.append('referencia', this.referencia)
      this.provas.forEach(f => fd.append('fotos', f))
      this.$emit('outra', fd)
    },
  },
}
</script>
