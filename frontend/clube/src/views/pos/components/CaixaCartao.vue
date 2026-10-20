<template>
  <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm" data-teste="caixa">
    <div v-if="!c" class="h-11 animate-pulse rounded-2xl bg-slate-100"></div>
    <div v-else class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div class="flex min-w-0 items-start gap-3">
        <div :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-lg',
                      c.turno ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500']">
          <font-awesome-icon :icon="['fas', 'cash-register']" />
        </div>
        <div class="min-w-0">
          <p class="text-sm font-black text-slate-950">
            {{ c.turno ? `Caixa aberta desde ${hora(c.turno.aberto_em)}` : 'Caixa fechada' }}
            <span v-if="c.turno?.operador" class="font-semibold text-slate-500">· {{ c.turno.operador }}</span>
          </p>
          <p v-if="c.turno && c.ver_esperado" class="mt-1 text-sm font-semibold text-slate-600">
            Fundo {{ dinheiro(c.turno.valor_abertura) }} · Dinheiro recebido {{ dinheiro(c.turno.vendas_dinheiro) }} ·
            <span class="font-black text-slate-950">Esperado na caixa {{ dinheiro(c.turno.esperado) }}</span>
          </p>
          <p v-else-if="c.turno" class="mt-1 text-sm font-semibold text-slate-600">
            Fundo {{ dinheiro(c.turno.valor_abertura) }} · No fecho, conta o dinheiro da caixa e escreve o total.
          </p>
          <p v-else-if="c.ultimo_turno" class="mt-1 text-sm font-semibold text-slate-600">
            Último turno fechado {{ dataHora(c.ultimo_turno.fechado_em) }}
            <template v-if="c.ultimo_turno.fechado_por"> por {{ c.ultimo_turno.fechado_por }}</template> ·
            <span :class="corDiferenca(c.ultimo_turno.diferenca)">{{ textoDiferenca(c.ultimo_turno.diferenca) }}</span>
          </p>
          <p v-else class="mt-1 text-sm font-semibold text-slate-500">Abre a caixa no início do dia para controlar o dinheiro.</p>
          <slot />
        </div>
      </div>

      <form v-if="c.pode_gerir" class="flex flex-wrap items-end gap-2" @submit.prevent="acao">
        <label class="flex flex-col gap-1">
          <span class="text-xs font-black text-slate-600">{{ c.turno ? 'Dinheiro contado' : 'Fundo de caixa' }}</span>
          <input v-model.trim="valor" type="text" inputmode="decimal" placeholder="0" required
                 :aria-label="c.turno ? 'Dinheiro contado' : 'Fundo de caixa'"
                 class="h-11 w-36 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none focus:border-slate-950 focus:bg-white" />
        </label>
        <button type="submit" :disabled="aGuardar"
                class="h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60">
          {{ c.turno ? 'Fechar caixa' : 'Abrir caixa' }}
        </button>
      </form>
    </div>
    <p v-if="erro" class="mt-3 text-sm font-bold text-red-700">{{ erro }}</p>
    <p v-if="resultado" class="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700">{{ resultado }}</p>
  </section>
</template>

<script setup>
// Caixa (turno) do POS: estado, fundo e esperado; abrir/fechar para o dono e os membros com "Abrir/Fechar turno".
// Quem não vê os relatórios fecha "às cegas" (não vê o esperado) — vê a diferença só depois de fechar.
import { onMounted, ref } from 'vue'
import api from '@/services/api'
import { formatarDinheiro, lerCentavos } from '@/utils/dinheiro'

const props = defineProps({
  posId: { type: [Number, String], required: true },
})
const emit = defineEmits(['mudou'])

const c = ref(null)
const valor = ref('')
const aGuardar = ref(false)
const erro = ref('')
const resultado = ref('')

const dinheiro = (v) => formatarDinheiro(v || 0)
const p2 = (n) => String(n).padStart(2, '0')
function hora (iso) {
  const t = new Date(iso)
  const hh = `${p2(t.getHours())}:${p2(t.getMinutes())}`
  return t.toDateString() === new Date().toDateString() ? hh : `${p2(t.getDate())}/${p2(t.getMonth() + 1)} ${hh}`
}
function dataHora (iso) {
  const t = new Date(iso)
  return `${p2(t.getDate())}/${p2(t.getMonth() + 1)} ${p2(t.getHours())}:${p2(t.getMinutes())}`
}
function textoDiferenca (v) {
  const n = Number(v)
  if (v === null || v === undefined) return ''
  if (!n) return 'caixa certa'
  return n < 0 ? `faltaram ${dinheiro(-n)}` : `sobraram ${dinheiro(n)}`
}
const corDiferenca = (v) => !Number(v) ? 'font-black text-emerald-700' : 'font-black text-red-700'

async function carregar () {
  try {
    const { data } = await api.get(`/api/pos/${props.posId}/turnos/atual/`)
    c.value = data
  } catch (e) {
    erro.value = e.response?.data?.detail || 'Não foi possível carregar a caixa.'
  }
}

async function acao () {
  erro.value = ''
  resultado.value = ''
  const centavos = lerCentavos(valor.value)
  if (Number.isNaN(centavos)) { erro.value = 'Escreve um valor válido, por exemplo 5.000 ou 5000,00.'; return }
  const v = (centavos / 100).toFixed(2)
  aGuardar.value = true
  try {
    if (c.value.turno) {
      const { data } = await api.post(`/api/pos/${props.posId}/turnos/${c.value.turno.id}/fechar/`, { valor_fecho: v })
      resultado.value = `Caixa fechada: ${textoDiferenca(data.diferenca)}.`
    } else {
      await api.post(`/api/pos/${props.posId}/turnos/abrir/`, { valor_abertura: v })
      resultado.value = 'Caixa aberta.'
    }
    valor.value = ''
    await carregar()
    emit('mudou')
  } catch (e) {
    erro.value = e.response?.data?.detail || 'Não foi possível guardar.'
  } finally {
    aGuardar.value = false
  }
}

defineExpose({ carregar })
onMounted(carregar)
</script>
