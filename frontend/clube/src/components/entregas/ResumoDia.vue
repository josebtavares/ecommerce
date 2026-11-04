<!-- ResumoDia.vue — Entregas → resumo do dia (backend: Views/entregaProvaView.resumo_dia, utils/resumo_entregas.py).
     Entregues, falhadas, por fazer (só hoje), dinheiro cobrado e por entregar à loja. Navega entre dias.
     A loja vê o total e cada condutor; o condutor só o seu. -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 mb-4" data-teste="resumo-dia">
    <div class="flex items-center justify-between gap-2 mb-3">
      <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider">
        <font-awesome-icon :icon="['fas', 'chart-simple']" class="mr-1" />Resumo {{ d && !d.hoje ? 'do dia' : 'de hoje' }}
      </p>
      <div class="flex items-center gap-1">
        <button type="button" @click="mudar(-1)" aria-label="Dia anterior" data-teste="resumo-anterior"
          class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-xs">
          <font-awesome-icon :icon="['fas', 'chevron-left']" />
        </button>
        <span class="text-xs font-semibold text-zinc-300 min-w-[5.5rem] text-center" data-teste="resumo-data">{{ rotulo }}</span>
        <button type="button" @click="mudar(1)" :disabled="ehHoje" aria-label="Dia seguinte" data-teste="resumo-seguinte"
          class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-xs disabled:opacity-30">
          <font-awesome-icon :icon="['fas', 'chevron-right']" />
        </button>
      </div>
    </div>

    <div v-if="!d" class="h-14 bg-zinc-800/50 rounded-xl animate-pulse"></div>
    <template v-else>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div class="rounded-xl bg-zinc-800/50 px-3 py-2">
          <p class="text-[10px] text-zinc-500 uppercase font-bold">Entregues</p>
          <p class="text-lg font-black text-green-400" data-teste="resumo-entregues">{{ d.total.entregues }}</p>
        </div>
        <div class="rounded-xl bg-zinc-800/50 px-3 py-2">
          <p class="text-[10px] text-zinc-500 uppercase font-bold">Falhadas</p>
          <p :class="['text-lg font-black', d.total.falhadas ? 'text-red-400' : 'text-zinc-400']" data-teste="resumo-falhadas">{{ d.total.falhadas }}</p>
        </div>
        <div v-if="d.hoje" class="rounded-xl bg-zinc-800/50 px-3 py-2">
          <p class="text-[10px] text-zinc-500 uppercase font-bold">Por fazer</p>
          <p :class="['text-lg font-black', d.total.por_fazer ? 'text-blue-400' : 'text-zinc-400']" data-teste="resumo-por-fazer">{{ d.total.por_fazer }}</p>
        </div>
        <div class="rounded-xl bg-zinc-800/50 px-3 py-2">
          <p class="text-[10px] text-zinc-500 uppercase font-bold">Cobrado</p>
          <p class="text-lg font-black text-zinc-200" data-teste="resumo-cobrado">{{ $dinheiro(d.total.cobrado) }}</p>
        </div>
      </div>
      <p v-if="d.hoje && Number(d.total.por_acertar) > 0" class="mt-2 text-xs text-amber-300" data-teste="resumo-por-acertar">
        <font-awesome-icon :icon="['fas', 'money-bill-wave']" class="mr-1" />
        {{ isCondutor ? 'Tens' : 'Os condutores têm' }} {{ $dinheiro(d.total.por_acertar) }} por entregar à loja.
      </p>
      <p v-if="d.total.entregues" class="mt-1 text-[11px] text-zinc-500">
        {{ d.total.com_prova }} de {{ d.total.entregues }} com prova de entrega (foto, assinatura ou nome).
      </p>

      <!-- loja: cada condutor -->
      <div v-if="d.condutores.length > 1 || (d.condutores.length === 1 && d.condutores[0].condutor_id === null)"
           class="mt-3 border-t border-zinc-800 pt-2">
        <button type="button" @click="aberto = !aberto" class="text-xs font-semibold text-zinc-400 hover:text-zinc-200" data-teste="resumo-por-condutor">
          <font-awesome-icon :icon="['fas', aberto ? 'chevron-up' : 'chevron-down']" class="mr-1" />Por condutor
        </button>
        <div v-if="aberto" class="mt-2 overflow-x-auto">
          <table class="w-full text-xs">
            <thead class="text-zinc-500">
              <tr><th class="text-left font-semibold py-1">Condutor</th><th class="font-semibold">Entregues</th><th class="font-semibold">Falhadas</th>
                <th v-if="d.hoje" class="font-semibold">Por fazer</th><th class="text-right font-semibold">Cobrado</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in d.condutores" :key="c.condutor_id ?? 'sem'" class="border-t border-zinc-800 text-zinc-300">
                <td class="py-1.5">{{ c.nome || '—' }}</td>
                <td class="text-center">{{ c.entregues }}</td>
                <td class="text-center">{{ c.falhadas }}</td>
                <td v-if="d.hoje" class="text-center">{{ c.por_fazer }}</td>
                <td class="text-right whitespace-nowrap">{{ $dinheiro(c.cobrado) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

function iso (d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default {
  name: 'ResumoDia',
  props: {
    lojaId:     { type: [String, Number], required: true },
    isCondutor: { type: Boolean, default: false },
  },
  data () {
    return { d: null, dia: null, aberto: false, pedido: 0 }
  },
  computed: {
    ehHoje () { return !this.dia || this.dia === iso(new Date()) },
    rotulo () {
      if (this.ehHoje) return 'Hoje'
      const ontem = new Date(); ontem.setDate(ontem.getDate() - 1)
      if (this.dia === iso(ontem)) return 'Ontem'
      const [a, m, d] = this.dia.split('-')
      return `${d}/${m}/${a}`
    },
  },
  created () { this.carregar() },
  methods: {
    mudar (n) {
      const [a, m, d] = (this.dia || iso(new Date())).split('-').map(Number)
      const x = new Date(a, m - 1, d + n)
      if (iso(x) > iso(new Date())) return
      this.dia = iso(x) === iso(new Date()) ? null : iso(x)
      this.d = null
      this.carregar()
    },
    // chamado pela página quando a lista muda (tempo real / intervalo)
    async carregar () {
      const pedido = ++this.pedido
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/entrega/resumo-dia/`, { params: this.dia ? { data: this.dia } : {} })
        if (pedido === this.pedido) this.d = data
      } catch (e) { console.error(e) }
    },
  },
}
</script>
