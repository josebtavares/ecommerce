<template>
  <!-- /minhas-marcacoes — as marcações de serviços do cliente -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="$router.push('/Home')" class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold flex-1">As minhas marcações</h1>
      <NotificacaoSino :isDark="isDark" />
    </header>
    <main class="max-w-2xl mx-auto px-4 py-5 space-y-4 pb-24">
      <div class="flex gap-1 rounded-xl p-1" :class="isDark ? 'bg-zinc-900' : 'bg-white border border-gray-200'" role="tablist">
        <button v-for="t in [{ k: 'proximas', n: 'Próximas' }, { k: 'anteriores', n: 'Anteriores' }]" :key="t.k" type="button" role="tab"
          :aria-selected="tipo === t.k" @click="tipo = t.k; carregar()"
          :class="['flex-1 py-2 rounded-lg text-sm font-semibold', tipo === t.k ? 'bg-red-600 text-white' : (isDark ? 'text-zinc-400' : 'text-zinc-500')]">{{ t.n }}</button>
      </div>
      <div v-if="carregando" class="flex justify-center py-10"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-xl text-red-500" /></div>
      <p v-else-if="!lista.length" class="text-center text-sm py-10 text-zinc-500">
        {{ tipo === 'proximas' ? 'Não tens marcações por fazer.' : 'Ainda não tens marcações anteriores.' }}</p>
      <button v-for="m in lista" :key="m.id" type="button" @click="$router.push(`/minhas-marcacoes/${m.id}`)" :data-teste="`minha-${m.id}`"
        class="w-full text-left rounded-2xl border p-4 flex gap-3 items-center" :class="isDark ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600' : 'bg-white border-gray-200 hover:border-gray-400'">
        <div class="w-14 text-center flex-shrink-0">
          <p class="text-[10px] uppercase text-zinc-500">{{ DIAS_CURTOS[diaSemana(diaDe(m.inicio))] }}</p>
          <p class="text-xl font-black leading-none">{{ diaDe(m.inicio).slice(8) }}</p>
          <p class="text-[10px] text-zinc-500">{{ MESES[Number(diaDe(m.inicio).slice(5, 7)) - 1] }}</p>
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-semibold truncate">{{ m.servico_nome }} · {{ hora(m.inicio) }}</p>
          <p class="text-xs text-zinc-500 truncate">{{ m.loja_nome }} · com {{ m.profissional_nome }}</p>
          <p class="text-xs mt-0.5" :class="corEstado(m)">{{ textoEstado(m) }}</p>
        </div>
        <span v-if="m.por_ler" class="min-w-[20px] h-5 px-1.5 rounded-full bg-red-600 text-white text-[11px] font-bold flex items-center justify-center" aria-label="Mensagens por ler">{{ m.por_ler }}</span>
      </button>
    </main>
  </div>
</template>

<script>
import api from '@/services/api'
import { DIAS_CURTOS, diaDe, diaSemana, hora, ouvirMarcacoes } from '@/utils/servicos'
import NotificacaoSino from '@/components/notificacao/notificacaoSino.vue'

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

export default {
  name: 'MinhasMarcacoes',
  components: { NotificacaoSino },
  data () { return { lista: [], tipo: 'proximas', carregando: true, isDark: localStorage.getItem('theme_preference') !== 'light', DIAS_CURTOS, MESES } },
  created () { this.carregar() },
  mounted () { this.desligar = ouvirMarcacoes(() => this.carregar(true)) },
  beforeUnmount () { this.desligar?.() },
  methods: {
    diaDe, diaSemana, hora,
    async carregar (silencioso = false) {
      if (!silencioso) this.carregando = true
      try { this.lista = (await api.get('/app/marcacoes/', { params: { tipo: this.tipo } })).data } finally { this.carregando = false }
    },
    textoEstado (m) {
      if (m.estado === 'pendente' && m.pagamento === 'antecipado' && !m.pago) return 'Por pagar'
      if (m.estado === 'pendente') return 'À espera da confirmação da loja'
      return m.estado_nome
    },
    corEstado (m) {
      return { pendente: 'text-amber-500', confirmada: 'text-sky-400', concluida: 'text-green-500', cancelada: 'text-zinc-500',
               falta: 'text-red-400', expirada: 'text-zinc-500' }[m.estado]
    },
  },
}
</script>
