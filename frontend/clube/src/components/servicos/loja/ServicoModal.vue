<template>
  <!--
    Modal de um serviço na página da loja (como o do produto): no computador a imagem à esquerda e a
    informação à direita; no telemóvel a imagem em cima. Altura fixa — mudar de dia ou de profissional
    não faz o modal encolher e crescer: o conteúdo antigo fica (esbatido) até chegar o novo.
  -->
  <transition appear enter-active-class="transition duration-200" enter-from-class="opacity-0"
              leave-active-class="transition duration-150" leave-to-class="opacity-0">
    <div class="fixed inset-0 z-[960] flex items-end sm:items-center justify-center sm:p-4"
         :class="isDark ? 'bg-black/80' : 'bg-black/50'" style="backdrop-filter: blur(4px)" @click.self="$emit('fechar')">
      <div role="dialog" :aria-label="servico.nome" data-teste="servico-modal"
           class="relative w-full sm:max-w-2xl md:max-w-4xl h-[92dvh] sm:h-[min(680px,90vh)] rounded-t-3xl sm:rounded-2xl overflow-hidden shadow-2xl border flex flex-col md:flex-row"
           :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100' : 'bg-white border-gray-200 text-zinc-900'">

        <!-- ══ imagens ══ -->
        <div class="relative md:w-1/2 flex-shrink-0 h-52 sm:h-60 md:h-full overflow-hidden" data-teste="servico-imagens">
          <div class="relative w-full h-full group" :class="imagemAtual ? 'cursor-zoom-in' : ''" @click="imagemAtual && (completa = true)">
            <img v-if="imagemAtual" :src="imagemAtual" :alt="servico.nome"
                 class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
            <div v-else class="w-full h-full flex items-center justify-center" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'">
              <font-awesome-icon :icon="['fas', 'calendar-check']" class="text-5xl" :style="{ color: cor }" />
            </div>
            <!-- olho: ver a imagem completa -->
            <div v-if="imagemAtual" data-teste="ver-imagem"
                 class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity hidden md:flex flex-col items-center justify-center gap-2">
              <div class="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center">
                <font-awesome-icon :icon="['fas', 'eye']" class="text-white" />
              </div>
              <span class="text-white text-xs font-medium opacity-80">Ver imagem completa</span>
            </div>
            <!-- no telemóvel não há hover: um botão pequeno -->
            <button v-if="imagemAtual" type="button" @click.stop="completa = true" aria-label="Ver imagem completa"
              class="md:hidden absolute bottom-3 right-3 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center">
              <font-awesome-icon :icon="['fas', 'expand']" class="text-xs" />
            </button>
            <button type="button" @click.stop="$emit('fechar')" aria-label="Fechar"
              class="md:hidden absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center">
              <font-awesome-icon :icon="['fas', 'xmark']" />
            </button>
            <template v-if="imagens.length > 1">
              <button type="button" @click.stop="mover(-1)" aria-label="Imagem anterior"
                class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center">
                <font-awesome-icon :icon="['fas', 'chevron-left']" class="text-xs" /></button>
              <button type="button" @click.stop="mover(1)" aria-label="Imagem seguinte"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center">
                <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-xs" /></button>
            </template>
          </div>
          <div v-if="imagens.length > 1" class="hidden md:flex absolute bottom-0 inset-x-0 gap-1.5 p-2 bg-black/40 backdrop-blur-sm overflow-x-auto">
            <button v-for="(u, i) in imagens" :key="i" type="button" @click.stop="foto = i" :aria-label="`Imagem ${i + 1}`"
              class="w-10 h-10 flex-shrink-0 rounded-lg overflow-hidden border-2 transition"
              :class="foto === i ? 'border-white' : 'border-transparent opacity-60 hover:opacity-100'">
              <img :src="u" alt="" class="w-full h-full object-cover" /></button>
          </div>
          <div v-if="imagens.length > 1" class="md:hidden absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
            <span v-for="(u, i) in imagens" :key="i" :class="['w-2 h-2 rounded-full', foto === i ? 'bg-white' : 'bg-white/40']"></span>
          </div>
        </div>

        <!-- ══ informação ══ -->
        <div class="flex-1 min-h-0 flex flex-col md:w-1/2">
          <div class="flex items-start gap-3 px-5 sm:px-6 pt-5 pb-3 flex-shrink-0">
            <div class="flex-1 min-w-0">
              <p v-if="servico.categoria" class="text-xs mb-0.5" :class="suave">{{ servico.categoria }}</p>
              <h3 class="text-xl sm:text-2xl font-bold leading-tight">{{ servico.nome }}</h3>
              <p class="text-sm mt-1" :class="suave">{{ duracaoTexto(servico.duracao_min) }} · <b class="text-base" :style="{ color: cor }">{{ servico.preco_texto }}</b></p>
            </div>
            <button type="button" @click="$emit('fechar')" aria-label="Fechar"
              class="hidden md:flex w-8 h-8 rounded-full items-center justify-center flex-shrink-0" :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
              <font-awesome-icon :icon="['fas', 'xmark']" :class="suave" />
            </button>
          </div>

          <div class="flex-1 min-h-0 overflow-y-auto overscroll-contain px-5 sm:px-6 pb-4 space-y-4" data-teste="servico-info">
            <div v-if="servico.e_pacote" class="rounded-xl border p-3" :class="isDark ? 'border-zinc-800 bg-zinc-800/40' : 'border-gray-200 bg-gray-50'" data-teste="pacote-inclui">
              <p class="text-xs font-semibold mb-1.5" :class="suave">O pacote inclui</p>
              <ul class="space-y-1">
                <li v-for="(c, i) in servico.componentes" :key="i" class="flex items-center gap-2 text-sm">
                  <font-awesome-icon :icon="['fas', 'check']" class="text-xs" :style="{ color: cor }" />
                  <span class="flex-1">{{ c.nome }}</span><span class="text-xs tabular-nums" :class="suave">{{ duracaoTexto(c.duracao_min) }}</span>
                </li>
              </ul>
              <p class="text-[11px] mt-2" :class="suave">Tudo seguido, com o mesmo profissional.
                <template v-if="servico.poupanca_texto"> Separados custam <s>{{ servico.valor_separado_texto }}</s> —
                  <b class="text-emerald-500">poupas {{ servico.poupanca_texto }}</b>.</template></p>
            </div>
            <p v-if="servico.descricao" class="text-sm whitespace-pre-line" :class="suave">{{ servico.descricao }}</p>
            <p v-if="servico.tipo_preco === 'a_partir'" class="text-[11px]" :class="suave">O preço final acerta-se com a loja — depois de marcar podes falar com ela.</p>

            <div v-if="profs.length > 1">
              <p class="text-xs font-semibold mb-1.5" :class="suave">Com quem?</p>
              <div class="flex flex-wrap gap-2" role="radiogroup" aria-label="Profissional">
                <button type="button" role="radio" :aria-checked="profId === null" @click="mudarProf(null)" :class="chip(profId === null)" :style="estiloChip(profId === null)">Qualquer um</button>
                <button v-for="p in profs" :key="p.id" type="button" role="radio" :aria-checked="profId === p.id" @click="mudarProf(p.id)"
                  :class="[chip(profId === p.id), 'flex items-center gap-1.5']" :style="estiloChip(profId === p.id)">
                  <img v-if="p.foto" :src="p.foto" alt="" class="w-5 h-5 rounded-full object-cover" />{{ p.nome }}
                </button>
              </div>
            </div>
            <p v-else-if="profs.length === 1" class="text-xs" :class="suave">Com {{ profs[0].nome }}</p>

            <div>
              <p class="text-xs font-semibold mb-1.5 flex items-center gap-2" :class="suave">Dia
                <font-awesome-icon v-if="aCarregarDias && dias.length" :icon="['fas', 'spinner']" spin class="text-[10px]" /></p>
              <!-- reserva a altura da fila para não saltar -->
              <div class="min-h-[52px]">
                <div v-if="!dias.length" class="flex gap-1.5">
                  <span v-for="n in 7" :key="n" class="w-[52px] h-[46px] rounded-xl animate-pulse flex-shrink-0" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></span>
                </div>
                <p v-else-if="!dias.some(d => d.livres)" class="text-xs text-amber-500 pt-3">Sem vagas nos próximos dias{{ profId ? ' com este profissional' : '' }}.</p>
                <div v-else class="flex gap-1.5 overflow-x-auto pb-1 transition-opacity" :class="aCarregarDias ? 'opacity-50 pointer-events-none' : ''"
                     role="radiogroup" aria-label="Dia">
                  <button v-for="d in dias" :key="d.dia" type="button" role="radio" :aria-checked="dia === d.dia" :disabled="!d.livres"
                    @click="mudarDia(d.dia)" :data-teste="`dia-${d.dia}`" :title="d.livres ? `${d.livres} horas livres` : 'Sem vagas'"
                    :class="[chip(dia === d.dia), 'flex-shrink-0 flex flex-col items-center leading-tight min-w-[52px] disabled:opacity-30 disabled:cursor-not-allowed']"
                    :style="estiloChip(dia === d.dia)">
                    <span class="text-[10px] uppercase">{{ DIAS_CURTOS[diaSemana(d.dia)] }}</span>
                    <span class="text-sm font-bold">{{ d.dia.slice(8) }}</span>
                  </button>
                </div>
              </div>
            </div>

            <div v-if="dia || !dias.length">
              <p class="text-xs font-semibold mb-1.5 flex items-center gap-2" :class="suave">Hora
                <font-awesome-icon v-if="aCarregar && horas.length" :icon="['fas', 'spinner']" spin class="text-[10px]" /></p>
              <div class="min-h-[76px]">
                <div v-if="!horas.length && (aCarregar || !dias.length)" class="flex flex-wrap gap-1.5">
                  <span v-for="n in 12" :key="n" class="w-[60px] h-[34px] rounded-xl animate-pulse" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></span>
                </div>
                <div v-else class="flex flex-wrap gap-1.5 transition-opacity" :class="aCarregar ? 'opacity-50 pointer-events-none' : ''"
                     role="radiogroup" aria-label="Hora">
                  <button v-for="h in horas" :key="h.inicio" type="button" role="radio" :aria-checked="escolhida === h.inicio" @click="escolhida = h.inicio"
                    :class="[chip(escolhida === h.inicio), 'tabular-nums w-[60px] justify-center']" :style="estiloChip(escolhida === h.inicio)">{{ hora(h.inicio) }}</button>
                </div>
              </div>
            </div>

            <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1"
                        leave-active-class="transition duration-150" leave-to-class="opacity-0">
              <div v-if="escolhida" class="space-y-4">
                <label class="block"><span class="text-xs font-semibold" :class="suave">Nota para a loja (opcional)</span>
                  <textarea v-model="notas" rows="2" maxlength="500" placeholder="ex.: a tua ideia, o comprimento do cabelo…"
                    class="mt-1 w-full px-3 py-2 rounded-xl text-sm border focus:outline-none resize-none"
                    :class="isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'"></textarea></label>
                <fieldset v-if="servico.pagamento === 'ambos'" class="flex flex-wrap gap-x-5 gap-y-1.5">
                  <legend class="text-xs font-semibold mb-1" :class="suave">Pagamento</legend>
                  <label v-for="o in [{ v: 'antecipado', t: 'Pagar já' }, { v: 'local', t: 'Pagar no local' }]" :key="o.v"
                    class="flex items-center gap-2 text-sm"><input type="radio" :value="o.v" v-model="pagamento" :style="{ accentColor: cor }" />{{ o.t }}</label>
                </fieldset>
                <p v-else class="text-xs" :class="suave">{{ servico.pagamento === 'antecipado' ? 'Paga-se ao marcar.' : 'Paga-se no local.' }}</p>
                <div class="rounded-xl p-3 text-xs space-y-1" :class="isDark ? 'bg-zinc-800/60 text-zinc-300' : 'bg-gray-100 text-zinc-600'" data-teste="resumo">
                  <p><b>{{ rotuloDia(dia, true) }} às {{ hora(escolhida) }}</b><template v-if="nomeProf"> com {{ nomeProf }}</template></p>
                  <p>Podes cancelar ou remarcar até {{ regras.cancelar_horas ? regras.cancelar_horas + ' h antes' : 'à hora marcada' }}.</p>
                  <p v-if="pagamentoEfetivo === 'antecipado'">
                    Tens {{ regras.minutos_para_pagar }} min para pagar. Se cancelares mais tarde ou faltares,
                    {{ regras.reembolso_fora_prazo === 'total' ? 'é-te devolvido tudo.' : 'o valor não é devolvido.' }}
                  </p>
                  <p v-if="regras.confirmacao === 'manual'">A loja confirma a marcação.</p>
                </div>
              </div>
            </transition>
          </div>

          <!-- botão sempre à vista -->
          <div class="flex-shrink-0 px-5 sm:px-6 py-3 border-t" :class="isDark ? 'border-zinc-800 bg-zinc-900' : 'border-gray-200 bg-white'"
               style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom))">
            <p v-if="erro" class="text-sm text-red-500 mb-2" role="alert">{{ erro }}</p>
            <button type="button" @click="marcar" :disabled="aMarcar || !escolhida" data-teste="confirmar"
              class="w-full py-3 rounded-xl text-white font-bold disabled:opacity-40 hover:brightness-110 transition" :style="{ backgroundColor: cor }">
              {{ !escolhida ? 'Escolhe o dia e a hora' : !autenticado ? 'Entrar para marcar'
                 : pagamentoEfetivo === 'antecipado' ? `Marcar e pagar ${precoTexto}` : 'Confirmar marcação' }}
            </button>
          </div>
        </div>

        <!-- ══ imagem completa ══ -->
        <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                    leave-active-class="transition duration-150" leave-to-class="opacity-0">
          <div v-if="completa" class="absolute inset-0 z-10 flex flex-col" :class="isDark ? 'bg-zinc-950' : 'bg-white'" data-teste="imagem-completa">
            <div class="flex items-center gap-3 px-4 py-3 border-b flex-shrink-0" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <button type="button" @click="completa = false"
                class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium"
                :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-gray-100 hover:bg-gray-200 text-zinc-700'">
                <font-awesome-icon :icon="['fas', 'chevron-left']" class="text-xs" />Voltar</button>
              <span class="text-sm truncate" :class="suave">{{ servico.nome }}</span>
              <span class="ml-auto text-xs" :class="suave">{{ foto + 1 }} / {{ imagens.length }}</span>
            </div>
            <div class="flex-1 flex items-center justify-center p-4 overflow-hidden relative">
              <img :src="imagemAtual" :alt="servico.nome" class="max-w-full max-h-full object-contain rounded-xl" />
              <template v-if="imagens.length > 1">
                <button type="button" @click="mover(-1)" aria-label="Imagem anterior"
                  class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center">
                  <font-awesome-icon :icon="['fas', 'chevron-left']" /></button>
                <button type="button" @click="mover(1)" aria-label="Imagem seguinte"
                  class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" /></button>
              </template>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </transition>
</template>

<script>
import api from '@/services/api'
import { estaAutenticado } from '@/services/sessao'
import { formatarDinheiro } from '@/utils/dinheiro'
import { DIAS_CURTOS, diaSemana, duracaoTexto, hora, rotuloDia } from '@/utils/servicos'
import { seguirPagamento } from '@/utils/pagamentoOnline'
import { porConfirmar } from '@/services/confirmarEmail'

export const GUARDADO = 'servicos_escolha'

export default {
  name: 'ServicoModal',
  props: {
    lojaId: { type: [String, Number], required: true },
    servico: { type: Object, required: true },
    regras: { type: Object, default: () => ({}) },
    profissionais: { type: Array, default: () => [] },
    isDark: { type: Boolean, default: true },
    cor: { type: String, default: '#dc2626' },
    inicial: { type: Object, default: null },        // escolha guardada antes do login
  },
  emits: ['fechar'],
  data () {
    const i = this.inicial || {}
    return { foto: 0, completa: false, profId: i.prof ?? null, dia: null, dias: [], horas: [], escolhida: null,
             aCarregar: false, aCarregarDias: false, pedidoDias: 0, pedidoHoras: 0,
             notas: i.notas || '', pagamento: i.pagamento || (this.servico.pagamento === 'local' ? 'local' : 'antecipado'),
             erro: '', aMarcar: false, autenticado: estaAutenticado(), DIAS_CURTOS }
  },
  computed: {
    suave () { return this.isDark ? 'text-zinc-400' : 'text-zinc-500' },
    imagens () { return this.servico.imagens || [] },
    imagemAtual () { return this.imagens[this.foto] || null },
    profs () { return this.regras.cliente_escolhe_profissional ? this.profissionais.filter(p => this.servico.profissionais.includes(p.id)) : [] },
    nomeProf () { return this.profs.find(p => p.id === this.profId)?.nome || (this.profs.length === 1 ? this.profs[0].nome : '') },
    pagamentoEfetivo () { return this.servico.pagamento === 'ambos' ? this.pagamento : this.servico.pagamento },
    precoTexto () { return formatarDinheiro(Number(this.servico.preco) || 0) },
  },
  async created () {
    await this.carregarDias(this.inicial?.dia)
    if (this.inicial?.inicio && this.horas.some(h => h.inicio === this.inicial.inicio)) this.escolhida = this.inicial.inicio
  },
  mounted () {
    document.body.style.overflow = 'hidden'
    this.aoTeclar = (e) => {
      if (e.key === 'Escape') { if (this.completa) this.completa = false; else this.$emit('fechar') }
      if (this.completa && e.key === 'ArrowRight') this.mover(1)
      if (this.completa && e.key === 'ArrowLeft') this.mover(-1)
    }
    window.addEventListener('keydown', this.aoTeclar)
  },
  beforeUnmount () { document.body.style.overflow = ''; window.removeEventListener('keydown', this.aoTeclar) },
  methods: {
    hora, rotuloDia, diaSemana, duracaoTexto,
    mover (d) { this.foto = (this.foto + d + this.imagens.length) % this.imagens.length },
    chip (ativo) {
      return ['px-3 py-1.5 rounded-xl border text-sm font-semibold transition-colors inline-flex',
              ativo ? 'text-white' : (this.isDark ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400')]
    },
    estiloChip (ativo) { return ativo ? { backgroundColor: this.cor, borderColor: this.cor } : {} },
    params () {
      const p = { servico: this.servico.id }
      if (this.profId) p.profissional = this.profId
      return p
    },
    // os dias com vagas; abre no pedido (se tiver vagas) ou no primeiro com vagas. Os dias antigos ficam
    // no ecrã (esbatidos) até chegarem os novos — o modal não muda de tamanho.
    async carregarDias (preferido = null) {
      const n = ++this.pedidoDias
      this.aCarregarDias = true
      try {
        const { data } = await api.get(`/app/lojas/${this.lojaId}/servicos/dias/`, { params: this.params() })
        if (n !== this.pedidoDias) return              // houve outro pedido entretanto
        this.dias = data.dias
        const ok = d => this.dias.some(x => x.dia === d && x.livres)
        this.dia = ok(preferido) ? preferido : ok(this.dia) ? this.dia : data.primeiro_livre
      } finally { if (n === this.pedidoDias) this.aCarregarDias = false }
      await this.carregarHoras()
    },
    mudarProf (id) { if (id !== this.profId) { this.profId = id; this.carregarDias(this.dia) } },
    mudarDia (d) { if (d !== this.dia) { this.dia = d; this.carregarHoras() } },
    async carregarHoras () {
      const n = ++this.pedidoHoras
      if (!this.dia) { this.horas = []; this.escolhida = null; return }
      this.aCarregar = true
      try {
        const horas = (await api.get(`/app/lojas/${this.lojaId}/servicos/horas/`, { params: { ...this.params(), dia: this.dia } })).data.horas
        if (n !== this.pedidoHoras) return
        this.horas = horas
        // a hora escolhida só fica se ainda existir no dia novo
        if (!horas.some(h => h.inicio === this.escolhida)) this.escolhida = null
      } finally { if (n === this.pedidoHoras) this.aCarregar = false }
    },
    async marcar () {
      if (!this.autenticado) {
        sessionStorage.setItem(GUARDADO, JSON.stringify({ loja: String(this.lojaId), servico: this.servico.id, prof: this.profId, dia: this.dia,
                                                         inicio: this.escolhida, notas: this.notas, pagamento: this.pagamento }))
        this.$router.push({ name: 'Login', query: { seguinte: `/loja/${this.lojaId}?servico=${this.servico.id}` } })
        return
      }
      this.erro = ''; this.aMarcar = true
      try {
        const { data } = await api.post(`/app/lojas/${this.lojaId}/servicos/marcar/`, {
          servico_id: this.servico.id, profissional_id: this.profId, inicio: this.escolhida, pagamento: this.pagamentoEfetivo, notas: this.notas.trim() })
        let m = data
        if (m.pagamento === 'antecipado' && !m.pago && confirm(`Pagar ${formatarDinheiro(Number(m.preco_indicado))}?\n\n(Pagamento simulado)`)) {
          const { data: pago } = await api.post(`/app/marcacoes/${m.id}/acao/`, { acao: 'pagar' })
          if (seguirPagamento(pago)) return       // paga na página do fornecedor e volta a /pagamento/callback
          m = pago
        }
        this.$router.push({ path: `/minhas-marcacoes/${m.id}`, query: { nova: 1 } })
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível marcar.'
        if (porConfirmar(e)) return             // conta nova sem o email confirmado (aviso no topo)
        this.carregarDias(this.dia)
      } finally { this.aMarcar = false }
    },
  },
}
</script>
