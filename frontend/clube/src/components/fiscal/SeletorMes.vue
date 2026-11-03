<template>
  <!-- Mês + ano em dois selects (o <input type="month"> é estranho em vários browsers). v-model = 'AAAA-MM'. -->
  <span class="inline-flex gap-1" :data-teste="teste">
    <select :value="mes" @change="mudar(ano, $event.target.value)" :aria-label="`${rotulo}: mês`" :data-teste="teste && `${teste}-mes`"
      class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
      <option v-for="(m, i) in MESES" :key="i" :value="String(i + 1).padStart(2, '0')">{{ m }}</option>
    </select>
    <select :value="ano" @change="mudar($event.target.value, mes)" :aria-label="`${rotulo}: ano`" :data-teste="teste && `${teste}-ano`"
      class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 tabular-nums">
      <option v-for="a in anos" :key="a" :value="String(a)">{{ a }}</option>
    </select>
  </span>
</template>

<script>
const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

export default {
  name: 'SeletorMes',
  props: {
    modelValue: { type: String, default: '' },
    rotulo: { type: String, default: 'Mês' },
    desde: { type: Number, default: 2024 },     // primeiro ano da lista
    teste: { type: String, default: '' },
  },
  emits: ['update:modelValue', 'change'],
  data () { return { MESES } },
  computed: {
    ano () { return (this.modelValue || '').slice(0, 4) || String(new Date().getFullYear()) },
    mes () { return (this.modelValue || '').slice(5, 7) || String(new Date().getMonth() + 1).padStart(2, '0') },
    anos () {
      const atual = new Date().getFullYear()
      const ini = Math.min(this.desde, Number(this.ano) || atual)
      return Array.from({ length: atual - ini + 1 }, (_, i) => atual - i)
    },
  },
  methods: {
    mudar (ano, mes) {
      this.$emit('update:modelValue', `${ano}-${mes}`)
      this.$emit('change')
    },
  },
}
</script>
