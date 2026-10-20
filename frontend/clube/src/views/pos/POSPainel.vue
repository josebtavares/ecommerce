<template>
  <div class="rel-claro space-y-5">
    <!-- Cabeçalho + período -->
    <div class="flex flex-col gap-1">
      <h2 class="text-2xl font-black text-slate-950">Painel</h2>
      <p class="text-sm font-semibold text-slate-500">Como está o POS: vendas, caixa, produtos e equipa.</p>
    </div>

    <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
      <FiltroPeriodo padrao="mes" :carregando="carregando" @mudar="mudarPeriodo" />
    </section>

    <div v-if="erro" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{{ erro }}</div>

    <div v-if="!d && carregando" class="grid grid-cols-2 gap-3 lg:grid-cols-3">
      <div v-for="n in 6" :key="n" class="h-24 animate-pulse rounded-[1.5rem] bg-slate-100"></div>
    </div>

    <template v-if="d">
      <!-- Caixa (turno) + agora -->
      <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex min-w-0 items-start gap-3">
            <div :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-lg',
                          d.turno ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500']">
              <font-awesome-icon :icon="['fas', 'cash-register']" />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-black text-slate-950">
                {{ d.turno ? `Caixa aberta desde ${hora(d.turno.aberto_em)}` : 'Caixa fechada' }}
                <span v-if="d.turno?.operador" class="font-semibold text-slate-500">· {{ d.turno.operador }}</span>
              </p>
              <p v-if="d.turno" class="mt-1 text-sm font-semibold text-slate-600">
                Fundo {{ dinheiro(d.turno.valor_abertura) }} · Dinheiro recebido {{ dinheiro(d.turno.vendas_dinheiro) }} ·
                <span class="font-black text-slate-950">Esperado na caixa {{ dinheiro(d.turno.esperado) }}</span>
              </p>
              <p v-else-if="d.ultimo_turno" class="mt-1 text-sm font-semibold text-slate-600">
                Último turno fechado {{ dataHora(d.ultimo_turno.fechado_em) }} ·
                <span :class="corDiferenca(d.ultimo_turno.diferenca)">{{ textoDiferenca(d.ultimo_turno.diferenca) }}</span>
              </p>
              <p v-else class="mt-1 text-sm font-semibold text-slate-500">Abre a caixa no início do dia para controlar o dinheiro.</p>
              <p class="mt-1 text-xs font-semibold text-slate-500">
                Agora: {{ d.agora.contas_abertas }} {{ d.agora.contas_abertas === 1 ? 'conta aberta' : 'contas abertas' }}
                <template v-if="d.agora.contas_abertas"> · {{ dinheiro(d.agora.valor_aberto) }} por cobrar</template>
              </p>
            </div>
          </div>

          <form v-if="d.pode_gerir_turno" class="flex flex-wrap items-end gap-2" @submit.prevent="acaoTurno">
            <label class="flex flex-col gap-1">
              <span class="text-xs font-black text-slate-600">{{ d.turno ? 'Dinheiro contado' : 'Fundo de caixa' }}</span>
              <input v-model.trim="valorTurno" type="text" inputmode="decimal" placeholder="0" required
                     class="h-11 w-36 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none focus:border-slate-950 focus:bg-white" />
            </label>
            <button type="submit" :disabled="aGuardarTurno"
                    class="h-11 rounded-2xl bg-slate-950 px-5 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-60">
              {{ d.turno ? 'Fechar caixa' : 'Abrir caixa' }}
            </button>
          </form>
        </div>
        <p v-if="erroTurno" class="mt-3 text-sm font-bold text-red-700">{{ erroTurno }}</p>
        <p v-if="resultadoTurno" class="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700">{{ resultadoTurno }}</p>
      </section>

      <!-- Indicadores -->
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-3" :class="carregando ? 'opacity-60' : ''">
        <div v-for="k in kpis" :key="k.label" class="min-w-0 rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-black uppercase tracking-wide text-slate-500">{{ k.label }}</p>
          <p class="mt-1 break-words text-xl font-black tabular-nums text-slate-950 sm:text-2xl">{{ k.valor }}</p>
          <p v-if="k.variacao !== undefined" class="mt-1 text-xs font-bold" :class="corVariacao(k.variacao)">
            {{ textoVariacao(k.variacao) }}
          </p>
          <p v-else-if="k.nota" class="mt-1 text-xs font-semibold text-slate-500">{{ k.nota }}</p>
        </div>
      </div>

      <!-- Vendas no tempo -->
      <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm" :class="carregando ? 'opacity-60' : ''">
        <GraficoTempo titulo="Vendas" :subtitulo="`Contas fechadas, por ${d.periodo.granularidade === 'mes' ? 'mês' : 'dia'}`"
                      :dados="d.grafico" :series="[{ chave: 'vendas', label: 'Vendas', cor: '#3987e5' }]"
                      :granularidade="d.periodo.granularidade" />
      </section>

      <!-- Por hora -->
      <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm" :class="carregando ? 'opacity-60' : ''">
        <div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h3 class="text-sm font-black uppercase tracking-wide text-slate-500">Vendas por hora do dia</h3>
            <p class="text-xs font-semibold text-slate-500">Somadas em todo o período · para ver as horas de mais movimento</p>
          </div>
          <p class="text-xs font-bold text-slate-700 tabular-nums" aria-live="polite">
            <template v-if="horaAtiva !== null">{{ horaAtiva }}h–{{ horaAtiva + 1 }}h: {{ dinheiro(d.por_hora[horaAtiva].vendas) }}
              · {{ d.por_hora[horaAtiva].contas }} {{ d.por_hora[horaAtiva].contas === 1 ? 'conta' : 'contas' }}</template>
            <template v-else-if="horaPico !== null">Pico: {{ horaPico }}h–{{ horaPico + 1 }}h</template>
          </p>
        </div>
        <div v-if="!maxHora" class="flex h-28 items-center justify-center text-sm text-slate-500">Sem vendas neste período</div>
        <template v-else>
          <div class="flex h-28 items-end gap-[2px]" @mouseleave="horaAtiva = null">
            <button v-for="h in d.por_hora" :key="h.hora" type="button"
                    class="flex h-full min-w-0 flex-1 items-end rounded-t focus:outline-none"
                    :class="horaAtiva === h.hora ? 'bg-slate-100' : ''"
                    :aria-label="`${h.hora}h: ${dinheiro(h.vendas)}, ${h.contas} contas`"
                    @mouseenter="horaAtiva = h.hora" @focus="horaAtiva = h.hora" @blur="horaAtiva = null">
              <span class="block w-full rounded-t" :style="{ height: (h.vendas / maxHora * 100) + '%', background: '#3987e5',
                                                           minHeight: h.vendas > 0 ? '2px' : '0' }"></span>
            </button>
          </div>
          <div class="mt-1 flex justify-between text-[10px] font-semibold text-slate-500">
            <span v-for="h in [0, 6, 12, 18, 23]" :key="h">{{ h }}h</span>
          </div>
        </template>
      </section>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2" :class="carregando ? 'opacity-60' : ''">
        <!-- Por método -->
        <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 text-sm font-black uppercase tracking-wide text-slate-500">Pagamentos por método</h3>
          <p v-if="!d.por_metodo.length" class="py-6 text-center text-sm text-slate-500">Sem pagamentos neste período</p>
          <ul v-else class="space-y-3">
            <li v-for="m in d.por_metodo" :key="m.metodo">
              <div class="flex items-baseline justify-between gap-3 text-sm">
                <span class="font-bold text-slate-700">{{ m.nome }} <span class="font-semibold text-slate-500">· {{ m.contas }}</span></span>
                <span class="font-black tabular-nums text-slate-950">{{ dinheiro(m.valor) }}
                  <span class="text-xs font-semibold text-slate-500">{{ pct(m.valor, d.vendas.total) }}</span></span>
              </div>
              <div class="mt-1 h-2 rounded-full bg-slate-100">
                <div class="h-2 rounded-full" :style="{ width: pct(m.valor, d.vendas.total), background: '#3987e5' }"></div>
              </div>
            </li>
          </ul>
        </section>

        <!-- Top produtos -->
        <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 text-sm font-black uppercase tracking-wide text-slate-500">Produtos mais vendidos</h3>
          <p v-if="!d.top_produtos.length" class="py-6 text-center text-sm text-slate-500">Sem vendas neste período</p>
          <table v-else class="w-full text-sm">
            <thead><tr class="text-left text-xs font-black text-slate-500">
              <th class="pb-2">Produto</th><th class="pb-2 text-right">Unid.</th><th class="pb-2 text-right">Vendido</th></tr></thead>
            <tbody>
              <tr v-for="p in d.top_produtos" :key="p.origem + p.nome" class="border-t border-slate-100">
                <td class="py-2 pr-2 font-bold text-slate-800">{{ p.nome }}
                  <span v-if="p.origem === 'loja'" class="ml-1 rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-black text-blue-700">loja</span></td>
                <td class="py-2 text-right tabular-nums text-slate-600">{{ p.unidades }}</td>
                <td class="py-2 text-right font-black tabular-nums text-slate-950">{{ dinheiro(p.valor) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Por atendente -->
        <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 text-sm font-black uppercase tracking-wide text-slate-500">Vendas por atendente</h3>
          <p v-if="!d.por_atendente.length" class="py-6 text-center text-sm text-slate-500">Sem vendas neste período</p>
          <table v-else class="w-full text-sm">
            <thead><tr class="text-left text-xs font-black text-slate-500">
              <th class="pb-2">Atendente</th><th class="pb-2 text-right">Contas</th><th class="pb-2 text-right">Vendas</th></tr></thead>
            <tbody>
              <tr v-for="a in d.por_atendente" :key="a.nome" class="border-t border-slate-100">
                <td class="py-2 pr-2 font-bold text-slate-800">{{ a.nome }}</td>
                <td class="py-2 text-right tabular-nums text-slate-600">{{ a.contas }}</td>
                <td class="py-2 text-right font-black tabular-nums text-slate-950">{{ dinheiro(a.total) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Por mesa -->
        <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 text-sm font-black uppercase tracking-wide text-slate-500">Vendas por mesa</h3>
          <p v-if="!d.por_mesa.length" class="py-6 text-center text-sm text-slate-500">Sem vendas neste período</p>
          <table v-else class="w-full text-sm">
            <thead><tr class="text-left text-xs font-black text-slate-500">
              <th class="pb-2">Mesa</th><th class="pb-2 text-right">Contas</th><th class="pb-2 text-right">Ticket médio</th>
              <th class="pb-2 text-right">Vendas</th></tr></thead>
            <tbody>
              <tr v-for="m in d.por_mesa" :key="m.mesa" class="border-t border-slate-100">
                <td class="py-2 pr-2 font-bold text-slate-800">{{ m.mesa }}</td>
                <td class="py-2 text-right tabular-nums text-slate-600">{{ m.contas }}</td>
                <td class="py-2 text-right tabular-nums text-slate-600">{{ dinheiro(m.ticket_medio) }}</td>
                <td class="py-2 text-right font-black tabular-nums text-slate-950">{{ dinheiro(m.total) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <p class="text-xs font-semibold text-slate-500">
        As vendas contam quando a conta é fechada (paga). Para exportar em Excel, PDF ou CSV, usa a aba Relatórios.
      </p>
    </template>
  </div>
</template>

<script setup>
// Painel do POS: vendas do período (com a variação face ao período anterior), caixa (turno), por hora,
// por método, produtos, atendentes e mesas. Dono e membros com "ver relatórios"; só o dono abre/fecha a caixa.
import '@/assets/relatorios-claro.css'
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import FiltroPeriodo from '@/components/relatorios/FiltroPeriodo.vue'
import GraficoTempo from '@/components/relatorios/GraficoTempo.vue'
import { formatarDinheiro } from '@/utils/dinheiro'
import { intervaloAtalho } from '@/utils/periodos'

const props = defineProps({
  posId: { type: [Number, String], required: true },
})

const periodo = ref(intervaloAtalho('mes'))
const d = ref(null)
const erro = ref('')
const carregando = ref(false)
const horaAtiva = ref(null)
const valorTurno = ref('')
const aGuardarTurno = ref(false)
const erroTurno = ref('')
const resultadoTurno = ref('')

const dinheiro = (v) => formatarDinheiro(v || 0)
const p2 = (n) => String(n).padStart(2, '0')
function hora (iso) {
  const t = new Date(iso)
  const hoje = new Date()
  const hh = `${p2(t.getHours())}:${p2(t.getMinutes())}`
  return t.toDateString() === hoje.toDateString() ? hh : `${p2(t.getDate())}/${p2(t.getMonth() + 1)} ${hh}`
}
function dataHora (iso) {
  const t = new Date(iso)
  return `${p2(t.getDate())}/${p2(t.getMonth() + 1)} ${p2(t.getHours())}:${p2(t.getMinutes())}`
}
function pct (v, total) {
  const t = Number(total) || 0
  return t ? `${Math.round(Number(v) / t * 100)}%` : '0%'
}
function textoVariacao (v) {
  if (v === null) return 'sem comparação com o período anterior'
  return `${v > 0 ? '▲' : v < 0 ? '▼' : '='} ${Math.abs(v).toLocaleString('pt-PT', { maximumFractionDigits: 1 })}% vs período anterior`
}
const corVariacao = (v) => v === null || v === 0 ? 'text-slate-500' : v > 0 ? 'text-emerald-700' : 'text-red-700'
function textoDiferenca (v) {
  const n = Number(v)
  if (v === null || v === undefined) return ''
  if (!n) return 'caixa certa'
  return n < 0 ? `faltaram ${dinheiro(-n)}` : `sobraram ${dinheiro(n)}`
}
const corDiferenca = (v) => !Number(v) ? 'font-black text-emerald-700' : 'font-black text-red-700'

const maxHora = computed(() => Math.max(0, ...(d.value?.por_hora || []).map(h => h.vendas)))
const horaPico = computed(() => {
  if (!maxHora.value) return null
  return d.value.por_hora.find(h => h.vendas === maxHora.value).hora
})

const kpis = computed(() => {
  const v = d.value.vendas
  const m = d.value.margem
  const c = d.value.cancelamentos
  const canc = Number(c.valor_contas) + Number(c.valor_artigos)
  return [
    { label: 'Vendas', valor: dinheiro(v.total), variacao: v.variacao },
    { label: 'Contas fechadas', valor: v.contas.toLocaleString('pt-PT'), variacao: v.contas_variacao },
    { label: 'Ticket médio', valor: dinheiro(v.ticket_medio), variacao: v.ticket_variacao },
    { label: 'Taxa de serviço', valor: dinheiro(v.taxa_servico),
      nota: Number(v.gorjetas) || Number(v.descontos) ? `Gorjetas ${dinheiro(v.gorjetas)} · Descontos ${dinheiro(v.descontos)}` : `${v.unidades} artigos vendidos` },
    { label: 'Margem', valor: m.margem === null ? '—' : dinheiro(m.margem),
      nota: m.margem === null ? 'Preenche o preço de custo nos Produtos' : `Em ${Number(m.cobertura).toLocaleString('pt-PT', { maximumFractionDigits: 1 })}% das vendas (produtos com custo)` },
    { label: 'Cancelamentos', valor: dinheiro(canc),
      nota: `${c.contas} ${c.contas === 1 ? 'conta' : 'contas'} · ${c.artigos} ${c.artigos === 1 ? 'artigo' : 'artigos'}` },
  ]
})

let pedido = 0
async function carregar () {
  const meu = ++pedido
  carregando.value = true
  erro.value = ''
  try {
    const { data } = await api.get(`/api/pos/${props.posId}/painel/`, {
      params: { data_inicio: periodo.value.inicio, data_fim: periodo.value.fim },
    })
    if (meu === pedido) d.value = data
  } catch (e) {
    if (meu === pedido) erro.value = e.response?.data?.detail || 'Não foi possível carregar o painel.'
  } finally {
    if (meu === pedido) carregando.value = false
  }
}

function mudarPeriodo (p) { periodo.value = p; carregar() }

async function acaoTurno () {
  erroTurno.value = ''
  resultadoTurno.value = ''
  const valor = valorTurno.value.replace(',', '.')
  aGuardarTurno.value = true
  try {
    if (d.value.turno) {
      const { data } = await api.post(`/api/pos/${props.posId}/turnos/${d.value.turno.id}/fechar/`, { valor_fecho: valor })
      resultadoTurno.value = `Caixa fechada: ${textoDiferenca(data.diferenca)}.`
    } else {
      await api.post(`/api/pos/${props.posId}/turnos/abrir/`, { valor_abertura: valor })
      resultadoTurno.value = 'Caixa aberta.'
    }
    valorTurno.value = ''
    await carregar()
  } catch (e) {
    erroTurno.value = e.response?.data?.detail || 'Não foi possível guardar.'
  } finally {
    aGuardarTurno.value = false
  }
}

onMounted(carregar)
</script>
