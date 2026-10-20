<template>
  <div class="flex flex-wrap gap-3 items-end">
    <!-- atalhos -->
    <div class="flex gap-1 flex-wrap">
      <button v-for="a in ATALHOS" :key="a.id" type="button" @click="escolher(a)"
              :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                       atalho === a.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ a.label }}
      </button>
    </div>

    <!-- datas à escolha -->
    <div class="flex items-end gap-2 flex-wrap">
      <label class="flex flex-col gap-1">
        <span class="text-[10px] text-zinc-500 uppercase tracking-wider">De</span>
        <input type="date" v-model="inicio" :max="fim"
               class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-[10px] text-zinc-500 uppercase tracking-wider">Até</span>
        <input type="date" v-model="fim" :min="inicio"
               class="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200 focus:outline-none focus:border-red-500" />
      </label>
      <button type="button" @click="aplicar" :disabled="carregando || !inicio || !fim || fim < inicio"
              class="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded-xl transition disabled:opacity-50 flex items-center gap-2">
        <font-awesome-icon v-if="carregando" :icon="['fas', 'spinner']" class="animate-spin" />
        Aplicar
      </button>
      <slot />
    </div>
  </div>
</template>

<script setup>
// Período dos dashboards e relatórios: atalhos ou duas datas. Emite { inicio, fim } (AAAA-MM-DD, datas locais).
import { ref } from 'vue'
import { dataISO, intervaloAtalho } from '@/utils/periodos'

const props = defineProps({
  padrao:     { type: String, default: 'mes' },   // atalho inicial
  carregando: { type: Boolean, default: false },
})
const emit = defineEmits(['mudar'])

const ATALHOS = [
  { id: 'hoje',        label: 'Hoje' },
  { id: '7d',          label: '7 dias' },
  { id: '30d',         label: '30 dias' },
  { id: 'mes',         label: 'Este mês' },
  { id: 'mes_passado', label: 'Mês passado' },
  { id: 'ano',         label: 'Este ano' },
  { id: '12m',         label: '12 meses' },
  { id: 'ano_passado', label: 'Ano passado' },
]

const inicial = intervaloAtalho(props.padrao)
const atalho = ref(props.padrao)
const inicio = ref(inicial.inicio)
const fim = ref(inicial.fim)

function escolher (a) {
  atalho.value = a.id
  const r = intervaloAtalho(a.id)
  inicio.value = r.inicio
  fim.value = r.fim
  emit('mudar', r)
}

function aplicar () {
  atalho.value = ''
  emit('mudar', { inicio: inicio.value, fim: fim.value })
}

defineExpose({ periodo: () => ({ inicio: inicio.value, fim: fim.value }), dataISO })
</script>
