<template>
  <!-- /minhas-marcacoes/:id — o cliente vê a marcação, paga, remarca, cancela e fala com a loja -->
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-100 text-zinc-900'">
    <header class="sticky top-0 z-10 flex items-center gap-3 px-4 h-14 border-b" :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
      <button type="button" aria-label="Voltar" @click="$router.push('/minhas-marcacoes')" class="h-9 w-9 rounded-lg flex items-center justify-center" :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-gray-100'">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
      </button>
      <h1 class="font-bold truncate flex-1">{{ m ? m.servico_nome : 'Marcação' }}</h1>
    </header>

    <div v-if="carregando" class="flex justify-center py-20"><font-awesome-icon :icon="['fas', 'spinner']" spin class="text-2xl text-red-500" /></div>
    <div v-else-if="erroCarregar" class="max-w-md mx-auto text-center py-20 px-4">
      <p class="text-sm text-zinc-500">{{ erroCarregar }}</p>
      <button type="button" @click="$router.push('/minhas-marcacoes')" class="mt-4 text-sm text-red-500 font-semibold">As minhas marcações</button>
    </div>

    <main v-else-if="m" class="max-w-2xl mx-auto px-4 py-5 space-y-4 pb-24">
      <p v-if="$route.query.nova && m.estado !== 'expirada'" class="rounded-2xl border px-4 py-3 text-sm font-semibold"
         :class="isDark ? 'bg-green-500/10 border-green-500/30 text-green-300' : 'bg-green-50 border-green-200 text-green-800'" role="status">
        {{ m.estado === 'confirmada' ? 'Marcação feita! Até lá.' : m.pago || m.pagamento === 'local' ? 'Marcação feita — a loja vai confirmar.' : 'Marcação reservada — falta pagar.' }}
      </p>

      <section class="rounded-2xl border p-4 space-y-3" :class="cartao" data-teste="resumo-marcacao">
        <div class="flex items-start gap-3">
          <img v-if="m.loja_logo" :src="m.loja_logo" alt="" class="w-11 h-11 rounded-xl object-cover" />
          <div class="flex-1 min-w-0">
            <p class="text-xs text-zinc-500">{{ m.loja_nome }}</p>
            <p class="font-bold text-lg leading-tight">{{ rotuloDia(diaDe(m.inicio), true) }} · {{ hora(m.inicio) }}–{{ hora(m.fim) }}</p>
            <p class="text-sm" :class="suave">{{ m.servico_nome }} com {{ m.profissional_nome }}</p>
          </div>
          <span class="px-2.5 py-1 rounded-full text-[11px] font-bold" :class="corEstado" data-teste="estado">{{ textoEstado }}</span>
        </div>
        <div class="border-t pt-3 space-y-1 text-sm" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
          <div class="flex justify-between"><span :class="suave">Preço</span><b>{{ m.preco_texto }}</b></div>
          <div class="flex justify-between"><span :class="suave">Pagamento</span>
            <span>{{ m.pagamento === 'local' ? 'No local' : m.pago ? `Pago (${dinheiro(m.valor_pago)})` : 'Antecipado — por pagar' }}</span></div>
          <div v-if="m.pago && ativa && Number(m.falta_pagar) > 0" class="flex justify-between text-amber-500"><span>Falta pagar no local</span><span>{{ dinheiro(m.falta_pagar) }}</span></div>
          <div v-if="Number(m.valor_reembolsado) > 0" class="flex justify-between text-green-500"><span>Devolvido</span><span>{{ dinheiro(m.valor_reembolsado) }}</span></div>
          <p v-if="m.preco_final && m.preco_final_motivo" class="text-xs pt-1" :class="suave">Preço final: {{ m.preco_final_motivo }}</p>
          <p v-if="m.notas_cliente" class="text-xs pt-1" :class="suave">A tua nota: {{ m.notas_cliente }}</p>
          <p v-if="m.estado === 'cancelada'" class="text-xs pt-1" :class="suave">Cancelada{{ m.cancelada_por && m.cancelada_por !== 'Cliente' ? ' pela loja' : '' }}{{ m.cancelada_motivo ? ': ' + m.cancelada_motivo : '' }}</p>
        </div>

        <!-- pagar -->
        <div v-if="porPagar" class="space-y-2">
          <p class="text-xs text-amber-500">Paga até às {{ hora(m.expira_em) }} — depois o horário é libertado.</p>
          <button type="button" @click="acao({ acao: 'pagar' }, 'Pago. Obrigado!', `Pagar ${dinheiro(m.preco_indicado)}?\n\n(Pagamento simulado)`)" :disabled="aEnviar"
            class="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold" data-teste="pagar">Pagar {{ dinheiro(m.preco_indicado) }}</button>
        </div>
      </section>

      <!-- remarcar / cancelar -->
      <section v-if="ativa" class="rounded-2xl border p-4 space-y-3" :class="cartao">
        <p class="text-xs" :class="suave">
          {{ m.dentro_do_prazo ? `Podes remarcar ou cancelar até ${m.cancelar_horas} h antes.` : `Já passou o prazo para remarcar (${m.cancelar_horas} h antes). Fala com a loja pelas mensagens.` }}
          <template v-if="m.pago && !m.dentro_do_prazo"> Se cancelares agora, {{ m.reembolso_fora_prazo === 'total' ? 'é-te devolvido tudo' : 'o valor pago não é devolvido' }}.</template>
        </p>
        <div class="flex flex-col sm:flex-row gap-2">
          <button v-if="m.dentro_do_prazo && !porPagar" type="button" @click="abrirRemarcar"
            class="flex-1 py-2.5 rounded-xl text-sm font-semibold border" :class="botaoSec" data-teste="abrir-remarcar">Remarcar</button>
          <button type="button" @click="cancelarAberto = !cancelarAberto" class="flex-1 py-2.5 rounded-xl text-sm border"
            :class="isDark ? 'border-zinc-700 text-zinc-400 hover:text-red-400' : 'border-gray-300 text-zinc-500 hover:text-red-500'" data-teste="abrir-cancelar">Cancelar marcação</button>
        </div>
        <div v-if="remarcarAberto" class="space-y-2" data-teste="remarcar-cliente">
          <div class="flex gap-1.5 overflow-x-auto pb-1">
            <button v-for="d in dias" :key="d" type="button" @click="novoDia = d; carregarHoras()" :aria-pressed="novoDia === d"
              :class="[chip(novoDia === d), 'flex-shrink-0 min-w-[52px] flex flex-col items-center leading-tight']">
              <span class="text-[10px] uppercase">{{ DIAS_CURTOS[diaSemana(d)] }}</span><span class="text-sm font-bold">{{ d.slice(8) }}</span></button>
          </div>
          <p v-if="!horas.length" class="text-xs text-amber-500">Sem horas livres com {{ m.profissional_nome }} neste dia.</p>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="h in horas" :key="h.inicio" type="button" @click="novaHora = h.inicio" :aria-pressed="novaHora === h.inicio"
              :class="[chip(novaHora === h.inicio), 'tabular-nums']">{{ hora(h.inicio) }}</button>
          </div>
          <button type="button" :disabled="!novaHora || aEnviar" @click="acao({ acao: 'remarcar', inicio: novaHora }, 'Remarcada.')"
            class="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white font-bold text-sm">Remarcar para {{ novaHora ? hora(novaHora) : '…' }}</button>
        </div>
        <div v-if="cancelarAberto" class="space-y-2" data-teste="cancelar-cliente">
          <input v-model="motivo" maxlength="200" placeholder="Motivo (opcional)" aria-label="Motivo"
            class="w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500"
            :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'" />
          <button type="button" @click="acao({ acao: 'cancelar', motivo }, 'Marcação cancelada.')" :disabled="aEnviar"
            class="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold text-sm">Confirmar: cancelar</button>
        </div>
      </section>

      <MarcacaoConversa v-if="m.pode_conversar" :marcacao-id="m.id" :is-dark="isDark" :ocupado="aEnviar" :versao="versao"
        @responder="responder" @mudou="carregar(true)" />
      <p v-if="erro" class="text-sm text-red-500" role="alert">{{ erro }}</p>
    </main>
  </div>
</template>

<script>
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { DIAS_CURTOS, diaDe, diaSemana, hojeCV, hora, rotuloDia, somarDias } from '@/utils/servicos'
import MarcacaoConversa from '@/components/servicos/MarcacaoConversa.vue'

export default {
  name: 'MarcacaoCliente',
  components: { MarcacaoConversa },
  data () {
    return { m: null, carregando: true, erroCarregar: '', erro: '', aEnviar: false, cancelarAberto: false, remarcarAberto: false, motivo: '',
             novoDia: null, horas: [], novaHora: null, versao: 0, isDark: localStorage.getItem('theme_preference') !== 'light', DIAS_CURTOS }
  },
  computed: {
    cartao () { return this.isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200' },
    suave () { return this.isDark ? 'text-zinc-400' : 'text-zinc-500' },
    botaoSec () { return this.isDark ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400' },
    ativa () { return ['pendente', 'confirmada'].includes(this.m?.estado) },
    porPagar () { return this.m?.estado === 'pendente' && this.m.pagamento === 'antecipado' && !this.m.pago },
    textoEstado () {
      if (this.porPagar) return 'Por pagar'
      if (this.m.estado === 'pendente') return 'À espera da loja'
      return this.m.estado_nome
    },
    corEstado () {
      return { pendente: 'bg-amber-500/15 text-amber-500', confirmada: 'bg-sky-500/15 text-sky-400', concluida: 'bg-green-500/15 text-green-500',
               cancelada: 'bg-zinc-500/15 text-zinc-400', falta: 'bg-red-500/15 text-red-400', expirada: 'bg-zinc-500/15 text-zinc-400' }[this.m.estado]
    },
    dias () { return Array.from({ length: 21 }, (_, i) => somarDias(hojeCV(), i)) },
  },
  watch: { '$route.params.id' () { this.carregando = true; this.carregar() } },
  created () { this.carregar() },
  methods: {
    diaDe, diaSemana, hora, rotuloDia,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    chip (ativo) {
      return ['px-3 py-1.5 rounded-xl border text-sm font-semibold',
              ativo ? 'border-red-500 bg-red-600 text-white' : (this.isDark ? 'border-zinc-700 text-zinc-200' : 'border-gray-300 text-zinc-700')]
    },
    async carregar (silencioso = false) {
      try {
        this.m = (await api.get(`/app/marcacoes/${this.$route.params.id}/`)).data
      } catch (e) {
        if (!silencioso) this.erroCarregar = e.response?.status === 404 ? 'Marcação não encontrada.' : 'Não foi possível carregar a marcação.'
      } finally { this.carregando = false }
    },
    abrirRemarcar () {
      this.remarcarAberto = !this.remarcarAberto
      this.cancelarAberto = false
      if (this.remarcarAberto) { this.novoDia = diaDe(this.m.inicio); this.carregarHoras() }
    },
    async carregarHoras () {
      this.novaHora = null
      const { data } = await api.get(`/app/lojas/${this.m.loja_id}/servicos/horas/`,
        { params: { servico: this.m.servico_id, dia: this.novoDia, profissional: this.m.profissional_id } })
      this.horas = data.horas
    },
    async acao (corpo, ok, pergunta = '') {
      if (pergunta && !confirm(pergunta)) return
      this.erro = ''; this.aEnviar = true
      try {
        this.m = (await api.post(`/app/marcacoes/${this.m.id}/acao/`, corpo)).data
        this.cancelarAberto = false; this.remarcarAberto = false
        this.versao++
        toast.success(ok)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível.'
        if (corpo.acao === 'pagar') this.carregar(true)
      } finally { this.aEnviar = false }
    },
    responder ({ id, aceitar }) {
      this.acao({ acao: aceitar ? 'aceitar_proposta' : 'recusar_proposta', proposta_id: id }, aceitar ? 'Preço aceite.' : 'Proposta recusada.')
    },
  },
}
</script>
