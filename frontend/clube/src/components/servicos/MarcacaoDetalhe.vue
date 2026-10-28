<template>
  <!-- Detalhe de uma marcação: confirmar, remarcar, reatribuir a outro profissional, cancelar, notas -->
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="$emit('fechar')">
    <div role="dialog" aria-label="Marcação" data-teste="marcacao-detalhe"
         class="bg-zinc-900 border border-zinc-800 rounded-t-2xl sm:rounded-2xl p-5 w-full sm:max-w-lg max-h-[92vh] overflow-y-auto space-y-4">
      <div v-if="!m" class="h-32 bg-zinc-800 rounded-xl animate-pulse"></div>
      <template v-else>
        <div class="flex items-start gap-3">
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-bold text-zinc-100">{{ m.servico_nome }}</h3>
            <p v-if="m.componentes && m.componentes.length" class="text-xs text-zinc-400" data-teste="inclui">
              Inclui: {{ m.componentes.map(c => c.nome).join(' + ') }}</p>
            <p class="text-sm text-zinc-300">{{ rotuloDia(diaDe(m.inicio), true) }} · {{ hora(m.inicio) }}–{{ hora(m.fim) }}</p>
            <p class="text-sm text-zinc-400">com <b class="text-zinc-200">{{ m.profissional_nome }}</b></p>
          </div>
          <span :class="['px-2.5 py-1 rounded-full text-[11px] font-bold border', ESTADOS[m.estado].cor.replace('line-through', '')]">{{ m.estado_nome }}</span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs">
          <div class="rounded-xl bg-zinc-800/50 px-3 py-2">
            <p class="text-zinc-500">Cliente</p>
            <p class="text-zinc-200 font-semibold">{{ m.cliente_nome || '—' }}</p>
            <a v-if="m.cliente_telefone" :href="`tel:${m.cliente_telefone}`" class="text-sky-300">{{ m.cliente_telefone }}</a>
          </div>
          <div class="rounded-xl bg-zinc-800/50 px-3 py-2">
            <p class="text-zinc-500">Preço</p>
            <p class="text-zinc-200 font-semibold">{{ m.preco_texto }}</p>
            <p class="text-zinc-500">{{ m.pagamento === 'antecipado' ? (m.pago ? `Pago antecipado (${dinheiro(m.valor_pago)})` : 'Antecipado — por pagar') : 'Paga no local' }}</p>
            <p v-if="m.pago && Number(m.falta_pagar) > 0 && ativa" class="text-amber-300">Falta {{ dinheiro(m.falta_pagar) }} no local</p>
            <p v-if="Number(m.valor_reembolsado) > 0" class="text-green-400">Devolvido: {{ dinheiro(m.valor_reembolsado) }}</p>
            <button v-if="m.pago" type="button" @click="comprovativo" data-teste="comprovativo-marcacao"
              class="mt-1 text-[11px] text-zinc-400 hover:text-zinc-200 underline">Comprovativo de pagamento</button>
            <p v-if="m.preco_final && m.preco_final_motivo" class="text-zinc-500">Preço final: {{ m.preco_final_motivo }} ({{ m.preco_final_por }})</p>
          </div>
        </div>
        <!-- o pagamento online recusou a devolução: quem gere tenta de novo (o worker também tenta sozinho) -->
        <ReembolsoPorConcluir v-if="m.reembolso_por_concluir && podeGerir" :valor="m.reembolso_por_concluir.valor"
          :erro="m.reembolso_por_concluir.erro" :tentativas="m.reembolso_por_concluir.tentativas"
          :proxima="m.reembolso_por_concluir.proxima_tentativa" :aEnviar="aGuardar" @tentar="tentarReembolso" />
        <p v-if="m.notas_cliente" class="text-xs text-zinc-300 rounded-xl bg-zinc-800/50 px-3 py-2"><span class="text-zinc-500">Nota do cliente:</span> {{ m.notas_cliente }}</p>
        <p v-if="m.estado === 'cancelada'" class="text-xs text-zinc-400">Cancelada por {{ m.cancelada_por || '—' }}<template v-if="m.cancelada_motivo">: {{ m.cancelada_motivo }}</template></p>

        <div v-if="podeGerir">
          <label class="block"><span class="text-xs text-zinc-500">Notas internas (o cliente não vê)</span>
            <div class="flex gap-2 mt-1">
              <input v-model="notas" maxlength="500" :class="CAMPO" />
              <button type="button" @click="acao({ acao: 'notas', notas_internas: notas })" :disabled="notas === m.notas_internas || aGuardar"
                class="px-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-xs text-zinc-200">Guardar</button>
            </div></label>
        </div>
        <p v-else-if="m.notas_internas" class="text-xs text-zinc-400">Notas: {{ m.notas_internas }}</p>

        <!-- estado: confirmar · concluir (com preço final) · falta — os dois últimos só a partir da hora marcada -->
        <div v-if="ativa" class="rounded-xl border border-zinc-700 p-3 space-y-2" data-teste="fechar-marcacao">
          <p class="text-xs font-semibold text-zinc-300">Estado: {{ m.estado_nome }}</p>
          <button v-if="m.estado === 'pendente' && podeGerir" type="button" @click="acao({ acao: 'confirmar' }, 'Marcação confirmada.')" :disabled="aGuardar"
            class="w-full px-3 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-bold" data-teste="confirmar">Confirmar marcação</button>
          <template v-if="comecou">
            <p class="text-[11px] text-zinc-500">Como correu?</p>
            <div class="flex gap-2">
              <input v-model="precoFinal" type="number" min="0" step="1" :placeholder="`Preço final (${m.preco_texto})`" aria-label="Preço final" :class="CAMPO" />
              <button type="button" @click="concluir" :disabled="aGuardar" data-teste="concluir"
                class="px-4 rounded-xl bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-xs font-bold whitespace-nowrap">Concluir</button>
            </div>
            <input v-if="precoFinal !== '' && Number(precoFinal) !== Number(m.preco_indicado)" v-model="motivoPreco" maxlength="200"
              placeholder="Porquê o preço mudou (o cliente vê)" aria-label="Motivo do preço final" :class="CAMPO" />
            <button type="button" @click="acao({ acao: 'falta' }, 'Marcada falta.', 'O cliente não veio?')" :disabled="aGuardar" data-teste="falta"
              class="text-xs text-red-300 hover:text-red-200">O cliente não veio — marcar falta</button>
          </template>
          <div v-else class="flex flex-wrap items-center gap-2" data-teste="fechar-depois">
            <button type="button" disabled class="px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-500 text-xs font-semibold cursor-not-allowed">Concluir</button>
            <button type="button" disabled class="px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-500 text-xs font-semibold cursor-not-allowed">Falta</button>
            <p class="text-[11px] text-zinc-500 flex-1 min-w-[180px]">Ficam disponíveis a partir da hora marcada ({{ rotuloDia(diaDe(m.inicio)) }} às {{ hora(m.inicio) }}).
              Antes disso podes remarcar, passar a outro profissional ou cancelar.</p>
          </div>
        </div>

        <!-- acções -->
        <div v-if="podeGerir && ['pendente', 'confirmada'].includes(m.estado)" class="space-y-3 pt-1 border-t border-zinc-800">
          <div class="flex flex-wrap gap-2 pt-3" role="group" aria-label="Acções">
            <button v-for="p in PAINEIS.filter(x => x.k !== 'preco' || m.pode_conversar)" :key="p.k" type="button" @click="abrirPainel(p.k)"
              :class="['px-3 py-2 rounded-xl text-xs font-semibold border', painel === p.k ? 'border-zinc-300 text-zinc-100' : 'border-zinc-700 text-zinc-300 hover:text-white',
                       p.k === 'cancelar' && 'text-red-300']">{{ p.t }}</button>
          </div>

          <div v-if="painel === 'remarcar'" class="space-y-2" data-teste="remarcar">
            <input v-model="novoDia" type="date" :min="hoje" aria-label="Novo dia" :class="CAMPO" @change="carregarHoras" />
            <label class="flex items-center gap-1.5 text-[11px] text-zinc-400"><input type="checkbox" v-model="foraHorario" class="accent-red-600" /> Outra hora (fora do horário)</label>
            <input v-if="foraHorario" v-model="horaLivre" type="time" step="300" aria-label="Nova hora" :class="CAMPO" />
            <div v-else class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
              <p v-if="!horas.length" class="text-xs text-amber-300">Sem horas livres para {{ m.profissional_nome }} neste dia.</p>
              <button v-for="h in horas" :key="h.inicio" type="button" @click="escolhida = h.inicio" :aria-pressed="escolhida === h.inicio"
                :class="['px-2.5 py-1 rounded-lg border text-xs font-semibold tabular-nums', escolhida === h.inicio ? 'border-red-500 bg-red-600 text-white' : 'border-zinc-700 text-zinc-300']">{{ hora(h.inicio) }}</button>
            </div>
            <button type="button" :disabled="aGuardar || !(foraHorario ? horaLivre : escolhida)"
              @click="acao({ acao: 'remarcar', inicio: foraHorario ? `${novoDia}T${horaLivre.slice(0, 5)}` : escolhida, ignorar_horario: foraHorario }, 'Remarcada — o cliente foi avisado.')"
              class="w-full px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Remarcar</button>
          </div>

          <div v-else-if="painel === 'reatribuir'" class="space-y-2" data-teste="reatribuir">
            <p v-if="!livres.length" class="text-xs text-zinc-500">Não há outros profissionais activos.</p>
            <label v-for="p in livres" :key="p.id"
              :class="['flex items-start gap-2 rounded-xl border px-3 py-2', p.livre ? 'border-zinc-700 cursor-pointer' : 'border-zinc-800 opacity-50']">
              <input type="radio" name="novo-prof" :value="p.id" v-model="novoProf" :disabled="!p.livre" class="mt-0.5 accent-red-600" />
              <span class="text-sm">
                <span class="text-zinc-100 font-semibold">{{ p.nome }}</span>
                <span class="block text-[11px]" :class="p.livre ? (p.faz_o_servico ? 'text-green-400' : 'text-amber-300') : 'text-zinc-500'">
                  {{ !p.livre ? p.razao : p.faz_o_servico ? 'Livre a essa hora' : 'Livre, mas não está associado a este serviço' }}</span>
              </span>
            </label>
            <input v-model="motivo" maxlength="200" placeholder="Motivo (opcional), ex.: o Rui está doente" :class="CAMPO" />
            <button type="button" :disabled="aGuardar || !novoProf"
              @click="acao({ acao: 'reatribuir', profissional_id: novoProf, motivo }, 'Passou para outro profissional — o cliente foi avisado.')"
              class="w-full px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Reatribuir</button>
          </div>

          <div v-else-if="painel === 'preco'" class="space-y-2" data-teste="propor-preco">
            <p class="text-[11px] text-zinc-500">O cliente recebe a proposta na conversa e aceita ou recusa. Agora: {{ m.preco_texto }}.</p>
            <input v-model="novoPreco" type="number" min="0" step="1" placeholder="Novo preço (CVE)" aria-label="Novo preço" :class="CAMPO" />
            <input v-model="motivo" maxlength="300" placeholder="Porquê (opcional), ex.: tatuagem maior com sombra" :class="CAMPO" />
            <button type="button" :disabled="aGuardar || novoPreco === ''" @click="acao({ acao: 'propor_preco', valor: String(novoPreco), motivo }, 'Proposta enviada ao cliente.')"
              class="w-full px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Enviar proposta</button>
          </div>

          <div v-else-if="painel === 'cancelar'" class="space-y-2" data-teste="cancelar">
            <input v-model="motivo" maxlength="200" placeholder="Motivo (o cliente vê)" aria-label="Motivo do cancelamento" :class="CAMPO" />
            <button type="button" :disabled="aGuardar || !motivo.trim()" @click="acao({ acao: 'cancelar', motivo }, 'Marcação cancelada.')"
              class="w-full px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Cancelar a marcação</button>
          </div>
        </div>

        <div v-if="m.reatribuicoes?.length" class="space-y-1 pt-2 border-t border-zinc-800">
          <p class="text-xs font-semibold text-zinc-400">Mudanças de profissional</p>
          <p v-for="(r, i) in m.reatribuicoes" :key="i" class="text-[11px] text-zinc-500">
            {{ rotuloDia(diaDe(r.em)) }} {{ hora(r.em) }} · {{ r.de }} → {{ r.para }} · por {{ r.por }}<template v-if="r.motivo"> · {{ r.motivo }}</template>
          </p>
        </div>
        <p class="text-[11px] text-zinc-600">Criada {{ m.criada_por ? 'por ' + m.criada_por : 'pelo cliente' }}</p>

        <!-- fatura do serviço (só depois de render: concluída, ou falta paga); o cliente com conta vê-a e recebe-a por email -->
        <FaturaVenda v-if="podeGerir && (m.faturavel || m.fatura)" :documento="m" :url="base() + 'fatura/'" teste="fatura-marcacao"
          :cancelada="!m.faturavel" :dica="m.cliente_id ? 'Emite a fatura no e-Fatura e regista-a aqui: o cliente vê-a na marcação.' : 'Emite a fatura no e-Fatura e regista-a aqui.'"
          @atualizada="faturaAtualizada" />

        <MarcacaoConversa v-if="m.pode_conversar" :marcacao-id="m.id" :is-dark="true" :versao="versao" @mudou="carregar" />

        <p v-for="(a, i) in avisos" :key="'a' + i" class="text-sm text-amber-300" role="status">{{ a }}</p>
        <p v-if="ok" class="text-sm text-green-400" role="status">{{ ok }}</p>
        <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
        <button type="button" @click="$emit('fechar')" class="w-full px-4 py-2.5 rounded-xl border border-zinc-700 text-zinc-300 text-sm">Fechar</button>
      </template>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { CAMPO, ESTADOS_MARCACAO, diaDe, hora, hojeCV, rotuloDia, ouvirMarcacoes } from '@/utils/servicos'
import { formatarDinheiro } from '@/utils/dinheiro'
import MarcacaoConversa from './MarcacaoConversa.vue'
import FaturaVenda from '@/components/fiscal/FaturaVenda.vue'
import ReembolsoPorConcluir from '@/components/reembolsos/ReembolsoPorConcluir.vue'
import { descarregarComprovativoMarcacao } from '@/utils/documentos'

const PAINEIS = [{ k: 'remarcar', t: 'Remarcar' }, { k: 'reatribuir', t: 'Outro profissional' }, { k: 'preco', t: 'Propor preço' },
                 { k: 'cancelar', t: 'Cancelar' }]

export default {
  name: 'MarcacaoDetalhe',
  components: { FaturaVenda, MarcacaoConversa, ReembolsoPorConcluir },
  props: {
    lojaId: { type: [String, Number], required: true },
    marcacaoId: { type: Number, required: true },
    podeGerir: { type: Boolean, default: false },
  },
  emits: ['fechar', 'alterada'],
  data () {
    return { m: null, notas: '', painel: null, novoDia: '', horas: [], escolhida: null, foraHorario: false, horaLivre: '',
             livres: [], novoProf: null, motivo: '', novoPreco: '', versao: 0, precoFinal: '', motivoPreco: '', erro: '', ok: '', avisos: [], aGuardar: false, hoje: hojeCV(),
             CAMPO, ESTADOS: ESTADOS_MARCACAO, PAINEIS }
  },
  computed: {
    ativa () { return ['pendente', 'confirmada'].includes(this.m?.estado) },
    comecou () { return this.m && Date.now() >= new Date(this.m.inicio).getTime() - 15 * 60 * 1000 },
  },
  created () { this.carregar() },
  mounted () { this.desligar = ouvirMarcacoes(d => { if ((!d || d.id === this.marcacaoId) && !this.aGuardar) this.carregar() }) },
  beforeUnmount () { this.desligar?.() },
  methods: {
    comprovativo () {
      descarregarComprovativoMarcacao(this.m.id).catch(() => { this.erro = 'Não foi possível descarregar o comprovativo.' })
    },
    diaDe, hora, rotuloDia,
    dinheiro (v) { return formatarDinheiro(Number(v) || 0) },
    base () { return `/app/loja/${this.lojaId}/servicos/marcacoes/${this.marcacaoId}/` },
    async carregar () {
      try {
        this.m = (await api.get(this.base())).data
        this.notas = this.m.notas_internas
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível abrir a marcação.' }
    },
    async abrirPainel (k) {
      this.painel = this.painel === k ? null : k
      this.erro = ''; this.motivo = ''; this.novoProf = null
      if (this.painel === 'remarcar') { this.novoDia = diaDe(this.m.inicio); this.carregarHoras() }
      if (this.painel === 'reatribuir') this.livres = (await api.get(this.base() + 'livres/')).data
    },
    async carregarHoras () {
      this.escolhida = null
      const { data } = await api.get(`/app/loja/${this.lojaId}/servicos/disponibilidade/`,
        { params: { servico: this.m.servico_id, dia: this.novoDia, profissional: this.m.profissional_id, excluir: this.m.id } })
      this.horas = data.horas
    },
    concluir () {
      const corpo = { acao: 'concluir' }
      if (this.precoFinal !== '' && Number(this.precoFinal) !== Number(this.m.preco_indicado)) {
        corpo.preco_final = String(this.precoFinal)
        corpo.motivo = this.motivoPreco
      }
      this.acao(corpo, 'Serviço concluído.')
    },
    async tentarReembolso () {
      await this.acao({ acao: 'tentar_reembolso' }, 'Reembolso feito.')
      if (this.m?.reembolso_por_concluir && !this.erro) { this.ok = ''; this.erro = 'O pagamento online voltou a recusar.' }
    },
    faturaAtualizada (data) {
      this.m = data
      this.ok = data.fatura ? `Fatura ${data.fatura.numero} registada.` : 'Fatura anulada.'
      this.$emit('alterada', data)
    },
    async acao (corpo, ok = '', pergunta = '') {
      if (pergunta && !confirm(pergunta)) return
      this.erro = ''; this.ok = ''; this.avisos = []; this.aGuardar = true
      try {
        const { data } = await api.post(this.base() + 'acao/', corpo)
        this.m = data
        this.notas = data.notas_internas
        this.avisos = data.avisos || []
        this.ok = ok || 'Guardado.'
        this.painel = null
        this.novoPreco = ''
        this.versao++
        this.$emit('alterada', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível.'
      } finally { this.aGuardar = false }
    },
  },
}
</script>
