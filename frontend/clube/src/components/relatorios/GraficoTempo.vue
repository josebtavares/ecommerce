<template>
  <div>
    <div class="flex items-start justify-between gap-3 mb-3">
      <div class="min-w-0">
        <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">{{ titulo }}</h3>
        <p v-if="subtitulo" class="text-xs text-zinc-600 mt-0.5">{{ subtitulo }}</p>
      </div>
      <button type="button" @click="verTabela = !verTabela"
              class="text-[11px] font-semibold text-zinc-500 hover:text-zinc-300 flex items-center gap-1 flex-shrink-0">
        <font-awesome-icon :icon="['fas', verTabela ? 'chart-column' : 'table']" />
        {{ verTabela ? 'Gráfico' : 'Tabela' }}
      </button>
    </div>

    <!-- legenda (só com 2 ou mais séries) -->
    <div v-if="series.length > 1 && !verTabela" class="flex flex-wrap gap-x-4 gap-y-1 mb-3">
      <span v-for="s in series" :key="s.chave" class="flex items-center gap-1.5 text-xs text-zinc-400">
        <span class="w-2.5 h-2.5 rounded-sm" :style="{ background: s.cor }"></span>{{ s.label }}
      </span>
    </div>

    <div v-if="!temDados && !verTabela" class="flex items-center justify-center text-zinc-600 text-sm" :style="{ height: altura + 'px' }">
      {{ vazio }}
    </div>

    <!-- gráfico -->
    <div v-else-if="!verTabela" class="flex gap-2">
      <!-- eixo dos valores -->
      <div class="relative w-14 flex-shrink-0 text-[10px] text-zinc-600 text-right" :style="{ height: altura + 'px' }">
        <span v-for="t in marcas" :key="t.y" class="absolute right-0 -translate-y-1/2" :style="{ top: t.y + '%' }">{{ t.texto }}</span>
      </div>
      <div class="flex-1 min-w-0">
        <div class="relative" :style="{ height: altura + 'px' }" @mouseleave="hover = -1">
          <!-- grelha -->
          <div v-for="t in marcas" :key="'g' + t.y" class="absolute inset-x-0 border-t"
               :class="t.zero ? 'border-zinc-600' : 'border-zinc-800/80'" :style="{ top: t.y + '%' }"></div>
          <!-- colunas -->
          <div class="absolute inset-0 flex">
            <div v-for="(c, i) in colunas" :key="c.dia"
                 class="flex-1 min-w-0 flex flex-col px-[1px] cursor-default"
                 :class="hover === i ? 'bg-zinc-800/50' : ''"
                 @mouseenter="hover = i" @focus="hover = i" tabindex="-1">
              <div class="flex flex-col-reverse gap-[2px]" :style="{ height: zeroPct + '%' }">
                <div v-for="seg in c.pos" :key="seg.chave" class="w-full max-w-[28px] mx-auto"
                     :class="seg.topo ? 'rounded-t' : ''" :style="{ height: seg.pct + '%', background: seg.cor }"></div>
              </div>
              <div class="flex flex-col gap-[2px]" :style="{ height: (100 - zeroPct) + '%' }">
                <div v-for="seg in c.neg" :key="seg.chave" class="w-full max-w-[28px] mx-auto"
                     :class="seg.topo ? 'rounded-b' : ''" :style="{ height: seg.pct + '%', background: seg.cor }"></div>
              </div>
            </div>
          </div>
          <!-- dica -->
          <div v-if="hover >= 0" class="absolute top-0 z-10 pointer-events-none bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 shadow-xl min-w-[150px]"
               :style="dicaPos">
            <p class="text-xs font-bold text-zinc-200 mb-1">{{ rotulo(dados[hover].dia) }}</p>
            <p v-for="s in series" :key="s.chave" class="flex items-center justify-between gap-3 text-xs">
              <span class="flex items-center gap-1.5 text-zinc-400">
                <span class="w-2 h-2 rounded-sm" :style="{ background: s.cor }"></span>{{ s.label }}
              </span>
              <span class="text-zinc-100 font-semibold tabular-nums">{{ s.negativo && valor(dados[hover], s) ? '−' : '' }}{{ fmt(valor(dados[hover], s)) }}</span>
            </p>
            <p v-if="chaveTotal" class="flex justify-between gap-3 text-xs border-t border-zinc-800 mt-1 pt-1">
              <span class="text-zinc-400">{{ labelTotal }}</span>
              <span class="text-zinc-100 font-bold tabular-nums">{{ fmt(dados[hover][chaveTotal]) }}</span>
            </p>
          </div>
        </div>
        <div class="flex justify-between mt-2 text-[10px] text-zinc-600">
          <span>{{ rotulo(dados[0]?.dia) }}</span>
          <span v-if="dados.length > 2">{{ rotulo(dados[Math.floor(dados.length / 2)]?.dia) }}</span>
          <span>{{ rotulo(dados[dados.length - 1]?.dia) }}</span>
        </div>
      </div>
    </div>

    <!-- tabela (o mesmo que o gráfico, para ler os números) -->
    <div v-else class="overflow-auto max-h-80 rounded-lg border border-zinc-800">
      <table class="w-full text-xs">
        <thead class="bg-zinc-800/60 text-zinc-400 sticky top-0">
          <tr>
            <th class="text-left font-semibold px-3 py-2">{{ granularidade === 'mes' ? 'Mês' : 'Dia' }}</th>
            <th v-for="s in series" :key="s.chave" class="text-right font-semibold px-3 py-2">{{ s.label }}</th>
            <th v-if="chaveTotal" class="text-right font-semibold px-3 py-2">{{ labelTotal }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="l in dados" :key="l.dia" class="border-t border-zinc-800 text-zinc-300">
            <td class="px-3 py-1.5">{{ rotulo(l.dia) }}</td>
            <td v-for="s in series" :key="s.chave" class="px-3 py-1.5 text-right tabular-nums">{{ fmt(valor(l, s)) }}</td>
            <td v-if="chaveTotal" class="px-3 py-1.5 text-right tabular-nums font-semibold text-zinc-100">{{ fmt(l[chaveTotal]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
// Gráfico de colunas no tempo (dias ou meses), com séries empilhadas. Uma série com `negativo: true`
// desenha-se abaixo do zero (ex.: devoluções). Passar o rato mostra os valores; "Tabela" mostra os números.
import { computed, ref } from 'vue'
import { formatarDinheiro } from '@/utils/dinheiro'
import { rotuloBalde } from '@/utils/periodos'

const props = defineProps({
  titulo:        { type: String, default: '' },
  subtitulo:     { type: String, default: '' },
  dados:         { type: Array, default: () => [] },     // [{ dia: 'AAAA-MM-DD', <chave>: número… }]
  series:        { type: Array, required: true },        // [{ chave, label, cor, negativo? }]
  granularidade: { type: String, default: 'dia' },
  chaveTotal:    { type: String, default: '' },
  labelTotal:    { type: String, default: 'Total' },
  dinheiro:      { type: Boolean, default: true },
  altura:        { type: Number, default: 180 },
  vazio:         { type: String, default: 'Sem dados neste período' },
})

const verTabela = ref(false)
const hover = ref(-1)

const valor = (linha, s) => Math.abs(Number(linha?.[s.chave]) || 0)
const fmt = (v) => props.dinheiro ? formatarDinheiro(v) : String(Math.round(Number(v) || 0))
const rotulo = (iso) => rotuloBalde(iso, props.granularidade)

const somas = computed(() => props.dados.map(l => ({
  pos: props.series.filter(s => !s.negativo).reduce((t, s) => t + valor(l, s), 0),
  neg: props.series.filter(s => s.negativo).reduce((t, s) => t + valor(l, s), 0),
})))
const maxPos = computed(() => Math.max(0, ...somas.value.map(x => x.pos)))
const maxNeg = computed(() => Math.max(0, ...somas.value.map(x => x.neg)))
const temDados = computed(() => maxPos.value > 0 || maxNeg.value > 0)
const escala = computed(() => (maxPos.value + maxNeg.value) || 1)
// onde fica o zero (percentagem a partir do topo)
const zeroPct = computed(() => maxNeg.value ? (maxPos.value / escala.value) * 100 : 100)

const colunas = computed(() => props.dados.map((l, i) => {
  const seg = (lista, max) => {
    const ativos = lista.filter(s => valor(l, s) > 0)
    return ativos.map((s, k) => ({ chave: s.chave, cor: s.cor, pct: max ? (valor(l, s) / max) * 100 : 0, topo: k === ativos.length - 1 }))
  }
  return { dia: l.dia, pos: seg(props.series.filter(s => !s.negativo), maxPos.value), neg: seg(props.series.filter(s => s.negativo), maxNeg.value), i }
}))

function curto (v) {
  if (!props.dinheiro) return String(Math.round(v))
  const a = Math.abs(v)
  if (a >= 1e6) return `${(v / 1e6).toFixed(1).replace('.', ',')}M`
  if (a >= 1e3) return `${(v / 1e3).toFixed(a >= 1e4 ? 0 : 1).replace('.', ',')}k`
  return String(Math.round(v))
}
const marcas = computed(() => {
  const out = [{ y: zeroPct.value, texto: '0', zero: true }]
  if (maxPos.value) {
    out.push({ y: 0, texto: curto(maxPos.value) })
    out.push({ y: zeroPct.value / 2, texto: curto(maxPos.value / 2) })
  }
  if (maxNeg.value) out.push({ y: 100, texto: '−' + curto(maxNeg.value) })
  return out
})

const dicaPos = computed(() => {
  const n = props.dados.length || 1
  const x = ((hover.value + 0.5) / n) * 100
  return x > 60 ? { right: `${100 - x + 2}%` } : { left: `${x + 2}%` }
})
</script>
