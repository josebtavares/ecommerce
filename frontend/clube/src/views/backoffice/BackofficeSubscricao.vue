<template>
  <!-- Backoffice → Subscrição: como a loja paga à plataforma (comissão ou subscrição),
       faturas e pagamento (simulado). GET /app/loja/<id>/subscricao/ -->
  <div class="space-y-5 max-w-4xl">
    <div v-if="carregando" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <p v-else-if="erro && !dados" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <template v-else-if="dados">
      <!-- ═══ Comissão ═══ -->
      <div v-if="dados.modelo === 'comissao'" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Como pagas à plataforma</p>
        <p class="text-2xl font-black text-zinc-100 mt-2">Comissão de {{ Number(dados.percentagem_comissao) }}% por venda</p>
        <p class="text-sm text-zinc-400 mt-1">Pagas só quando vendes. Não há mensalidade.</p>
        <!-- pedido de mudança à espera da 1.ª fatura -->
        <div v-if="dados.pedido" class="mt-5 rounded-xl border border-sky-500/30 bg-sky-500/10 p-4">
          <p class="text-sm font-bold text-sky-200">Pediste para mudar para o plano {{ dados.pedido.plano.nome }}</p>
          <p class="text-xs text-sky-200/80 mt-1">A subscrição começa quando pagares a 1.ª fatura. Até lá continuas em comissão.</p>
          <div v-if="dados.pode_pagar" class="flex flex-wrap gap-2 mt-3">
            <button v-if="dados.pedido.fatura" type="button" @click="pagar(dados.pedido.fatura)" :disabled="aPagar"
              class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold">
              Pagar {{ euros(dados.pedido.fatura.valor) }} e mudar já
            </button>
            <button type="button" @click="mudar({ acao: 'cancelar_pedido' })" :disabled="aGuardar"
              class="px-4 py-2 rounded-xl border border-zinc-600 text-zinc-300 hover:text-white text-xs font-semibold">Cancelar pedido</button>
          </div>
        </div>
        <div v-else-if="dados.planos.length" class="mt-5 pt-5 border-t border-zinc-800">
          <p class="text-sm font-semibold text-zinc-200">Preferes uma mensalidade, sem comissão nas vendas?</p>
          <div class="grid sm:grid-cols-3 gap-2 mt-3">
            <div v-for="p in dados.planos" :key="p.id" class="rounded-xl border border-zinc-800 bg-zinc-800/40 p-3 flex flex-col">
              <p class="text-sm font-semibold text-zinc-100">{{ p.nome }}</p>
              <p v-if="p.tipo === 'loja_pos'" class="text-[11px] font-semibold text-violet-300">Inclui o POS</p>
              <p class="text-lg font-black text-zinc-100">{{ euros(p.preco) }}</p>
              <p class="text-[11px] text-zinc-500 flex-1">{{ p.periodicidade_nome }}<template v-if="p.meses > 1"> · {{ euros(p.preco_mes) }}/mês</template></p>
              <button v-if="dados.pode_pagar && !dados.troca_livre_em" type="button" @click="pedirSubscricao(p)" :disabled="aGuardar"
                class="mt-3 px-3 py-1.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-900 text-xs font-bold">Mudar para este plano</button>
            </div>
          </div>
          <p v-if="dados.troca_livre_em" class="text-xs text-amber-300 mt-3">Mudaste de modelo há pouco tempo — podes mudar outra vez a partir de {{ data(dados.troca_livre_em) }}.</p>
          <p v-else-if="!dados.pode_pagar" class="text-xs text-zinc-500 mt-3">Só o dono da loja pode mudar.</p>
        </div>
      </div>

      <!-- ═══ Subscrição ═══ -->
      <template v-else-if="sub">
        <p v-if="dados.aviso" role="alert"
           :class="['rounded-xl border px-4 py-3 text-sm font-semibold',
                    dados.aviso.tipo === 'vence' ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' : 'bg-red-500/10 border-red-500/30 text-red-300']">
          {{ dados.aviso.texto }}
        </p>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
          <div class="flex flex-wrap items-start gap-4">
            <div class="flex-1 min-w-0">
              <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">A tua subscrição</p>
              <p v-if="sub.plano_em_curso" class="text-2xl font-black text-zinc-100 mt-2">{{ sub.plano_em_curso.nome }}
                <span class="block sm:inline text-sm font-semibold text-sky-300"><span class="hidden sm:inline">· </span>a partir de {{ data(diaSeguinte(sub.pago_ate)) }}: {{ sub.plano.nome }} ({{ euros(sub.preco) }})</span>
              </p>
              <p v-else class="text-2xl font-black text-zinc-100 mt-2">{{ sub.plano.nome }}
                <span class="block sm:inline text-sm font-semibold text-zinc-400"><span class="hidden sm:inline">· </span>{{ euros(sub.preco) }} / {{ sub.meses === 1 ? 'mês' : sub.meses + ' meses' }}</span>
              </p>
              <p class="text-sm mt-1" :class="corEstadoTexto">{{ resumoEstado }}</p>
              <p v-if="(sub.plano_em_curso || sub.plano).tipo === 'loja_pos'" class="text-xs mt-1 font-semibold text-violet-300">
                Plano Loja + POS:
                <template v-if="posIncluidos.length">inclui o POS {{ posIncluidos.map(p => p.nome).join(', ') }} — o POS não paga à parte.</template>
                <template v-else-if="(dados.pos_ligados || []).length">o POS ligado passa a estar incluído no início do período deste plano.</template>
                <template v-else>inclui o POS quando ligares um POS a esta loja.</template>
              </p>
            </div>
            <span :class="['px-3 py-1 rounded-full text-xs font-bold', corEstado]">{{ sub.estado_nome }}</span>
          </div>

          <div class="grid sm:grid-cols-3 gap-3 mt-5">
            <div class="rounded-xl bg-zinc-800/50 px-4 py-3">
              <template v-if="sub.estado === 'teste' && sub.teste_ate">
                <p class="text-[11px] text-zinc-500 uppercase tracking-wide">Teste grátis até</p>
                <p class="text-base font-bold text-zinc-100">{{ data(sub.teste_ate) }}</p>
                <p v-if="sub.pago_ate && sub.pago_ate > sub.teste_ate" class="text-[11px] text-green-400">e já pago até {{ data(sub.pago_ate) }}</p>
              </template>
              <template v-else>
                <p class="text-[11px] text-zinc-500 uppercase tracking-wide">Pago até</p>
                <p class="text-base font-bold text-zinc-100">{{ sub.pago_ate ? data(sub.pago_ate) : '—' }}</p>
              </template>
            </div>
            <div class="rounded-xl bg-zinc-800/50 px-4 py-3">
              <p class="text-[11px] text-zinc-500 uppercase tracking-wide">Por pagar</p>
              <p class="text-base font-bold" :class="Number(dados.por_pagar) ? 'text-amber-300' : 'text-zinc-100'">{{ euros(dados.por_pagar) }}</p>
            </div>
            <div class="rounded-xl bg-zinc-800/50 px-4 py-3 flex items-center justify-between gap-3">
              <div>
                <p class="text-[11px] text-zinc-500 uppercase tracking-wide">Pagamento automático</p>
                <p class="text-sm font-semibold text-zinc-200">{{ sub.auto_renovar ? 'Ligado' : 'Desligado' }}</p>
              </div>
              <button v-if="dados.pode_pagar" type="button" role="switch" :aria-checked="sub.auto_renovar ? 'true' : 'false'"
                aria-label="Pagamento automático" @click="mudarAuto" :disabled="aGuardar"
                :class="['w-11 h-6 rounded-full transition-colors relative flex-shrink-0', sub.auto_renovar ? 'bg-red-600' : 'bg-zinc-700']">
                <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow', sub.auto_renovar ? 'left-5.5' : 'left-0.5']" style="transition: left 0.2s"></span>
              </button>
            </div>
          </div>
          <p class="text-[11px] text-zinc-500 mt-3">
            Com o pagamento automático ligado, cada fatura é paga no dia em que vence. Os pagamentos ainda são simulados.
          </p>
        </div>

        <!-- Mudar: plano ou passar para comissão (só o dono) -->
        <div v-if="dados.pode_pagar && ['teste', 'ativa', 'em_atraso'].includes(sub.estado)"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-4">
          <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Mudar</p>
          <div v-if="sub.fim_agendado" class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex flex-wrap items-center gap-3">
            <p class="flex-1 text-sm text-amber-200">
              A loja passa para <b>comissão ({{ Number(dados.percentagem_comissao) }}%)</b> a {{ data(sub.fim_agendado) }}, quando acaba o período pago.
            </p>
            <button type="button" @click="mudar({ acao: 'cancelar_comissao' })" :disabled="aGuardar"
              class="px-3 py-1.5 rounded-lg border border-zinc-600 text-zinc-200 text-xs font-semibold">Ficar em subscrição</button>
          </div>
          <template v-else>
            <div class="flex flex-wrap items-center gap-2">
              <select v-model="novoPlano" aria-label="Novo plano"
                class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
                <option :value="null" disabled>Mudar de plano…</option>
                <option v-for="p in dados.planos.filter(p => p.id !== (sub.plano_seguinte || sub.plano).id)" :key="p.id" :value="p.id">
                  {{ p.nome }}{{ p.tipo === 'loja_pos' ? ' (inclui o POS)' : '' }} — {{ euros(p.preco) }} / {{ p.periodicidade_nome.toLowerCase() }}
                </option>
              </select>
              <button type="button" @click="mudarPlano" :disabled="!novoPlano || aGuardar"
                class="px-4 py-2 rounded-xl bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-900 text-xs font-bold">Mudar de plano</button>
            </div>
            <p v-if="sub.plano_seguinte" class="text-xs text-sky-300">
              A partir da próxima renovação passas para o plano <b>{{ sub.plano_seguinte.nome }}</b> ({{ euros(sub.plano_seguinte.preco) }}).
            </p>
            <p class="text-xs text-zinc-500">O plano novo vale a partir da próxima renovação — o que já pagaste não muda.</p>
            <div class="pt-3 border-t border-zinc-800 flex flex-wrap items-center gap-3">
              <p class="flex-1 text-sm text-zinc-400">Preferes voltar a pagar só quando vendes ({{ Number(dados.percentagem_comissao) }}% por venda)?</p>
              <button v-if="!dados.troca_livre_em" type="button" @click="passarComissao" :disabled="aGuardar"
                class="px-4 py-2 rounded-xl border border-zinc-600 text-zinc-200 hover:text-white text-xs font-semibold">Passar para comissão</button>
              <p v-else class="text-xs text-amber-300">Podes mudar a partir de {{ data(dados.troca_livre_em) }}.</p>
            </div>
          </template>
        </div>
      </template>

      <!-- ═══ Módulo Serviços ═══ -->
      <div v-if="serv && (serv.ativo || serv.subscricao)" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 space-y-4"
           data-teste="sub-servicos">
        <p v-if="serv.aviso" role="alert"
           :class="['rounded-xl border px-4 py-3 text-sm font-semibold',
                    serv.aviso.tipo === 'vence' ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' : 'bg-red-500/10 border-red-500/30 text-red-300']">
          {{ serv.aviso.texto }}
        </p>
        <div class="flex flex-wrap items-start gap-4">
          <div class="flex-1 min-w-0">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Serviços e marcações</p>
            <template v-if="serv.incluido">
              <p class="text-lg font-black text-zinc-100 mt-2">Incluídos na tua subscrição</p>
              <p class="text-sm text-zinc-400 mt-1">Não pagas nada a mais pelos Serviços.</p>
            </template>
            <template v-else-if="serv.subscricao">
              <p class="text-lg font-black text-zinc-100 mt-2">{{ serv.subscricao.plano.nome }}
                <span class="text-sm font-semibold text-zinc-400">· {{ euros(serv.subscricao.preco) }} / {{ serv.subscricao.meses === 1 ? 'mês' : serv.subscricao.meses + ' meses' }}</span>
              </p>
              <p class="text-sm text-zinc-400 mt-1">{{ resumoServicos }}</p>
              <p v-if="limitesTexto" class="text-xs text-zinc-500 mt-1">{{ limitesTexto }}</p>
            </template>
          </div>
          <span v-if="serv.subscricao && !serv.incluido" :class="['px-3 py-1 rounded-full text-xs font-bold', corEstadoDe(serv.subscricao.estado)]">
            {{ serv.subscricao.estado_nome }}
          </span>
        </div>
        <template v-if="!serv.incluido && serv.subscricao && dados.pode_pagar && ['teste', 'ativa', 'em_atraso'].includes(serv.subscricao.estado)">
          <div v-if="serv.subscricao.fim_agendado" class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
            A subscrição de Serviços termina a {{ data(serv.subscricao.fim_agendado) }} (fim do período pago).
          </div>
          <template v-else>
            <div class="flex flex-wrap items-center gap-2">
              <select v-model="novoPlanoServ" aria-label="Novo plano de Serviços"
                class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
                <option :value="null" disabled>Mudar de plano…</option>
                <option v-for="p in serv.planos.filter(p => p.id !== (serv.subscricao.plano_seguinte || serv.subscricao.plano).id)" :key="p.id" :value="p.id">
                  {{ p.nome }} — {{ euros(p.preco) }} / {{ p.periodicidade_nome.toLowerCase() }}
                </option>
              </select>
              <button type="button" @click="mudarPlanoServ" :disabled="!novoPlanoServ || aGuardar"
                class="px-4 py-2 rounded-xl bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-900 text-xs font-bold">Mudar de plano</button>
              <label class="sm:ml-auto flex items-center gap-2 text-xs text-zinc-300">
                <input type="checkbox" :checked="serv.subscricao.auto_renovar" @change="mudarAutoServ" :disabled="aGuardar" class="accent-red-600" />
                Pagamento automático
              </label>
            </div>
            <p v-if="serv.subscricao.plano_seguinte" class="text-xs text-sky-300">
              A partir da próxima renovação: <b>{{ serv.subscricao.plano_seguinte.nome }}</b> ({{ euros(serv.subscricao.plano_seguinte.preco) }}).
            </p>
          </template>
        </template>
      </div>

      <!-- comissões do Bende por mês: extrato + fatura (components/fiscal) -->
      <ComissoesMensais :loja-id="lojaId" />

      <!-- cobrança mensal das comissões (a SISP não divide pagamentos: paga-se à parte) -->
      <CobrancasComissoes :loja-id="lojaId" @alterado="$emit('alterado')" />

      <!-- Faturas (também o histórico de uma loja que voltou à comissão) -->
      <div v-if="sub || dados.faturas.length" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">
        <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider px-6 pt-5 pb-3">Mensalidades</p>
        <!-- todas as mensalidades, paginadas e com procura (GET /app/loja/<id>/subscricao/faturas/) -->
        <ListaCobrancas :url="`/app/loja/${lojaId}/subscricao/faturas/`" :versao="versao" embutida>
          <template #default="{ f }">
          <div class="px-6 py-4 flex flex-wrap items-center gap-3" :data-teste="`mensalidade-S-${f.id}`">
            <div class="flex-1 min-w-[200px]">
              <p class="text-sm font-semibold text-zinc-200">
                <span v-if="f.servicos" class="mr-1.5 px-1.5 py-0.5 rounded bg-violet-500/15 text-violet-300 text-[10px] font-bold uppercase align-middle">Serviços</span>{{ f.descricao }}
              </p>
              <p class="text-xs text-zinc-500">
                <template v-if="f.estado === 'paga'">Paga a {{ data(f.paga_em) }} · {{ f.metodo_nome }}</template>
                <template v-else-if="f.estado === 'pendente'">Vence a {{ data(f.vencimento) }}<span v-if="f.atrasada" class="text-red-400 font-semibold"> · em atraso</span></template>
                <template v-else>{{ f.notas || 'Anulada' }}</template>
              </p>
            </div>
            <span class="text-sm font-bold text-zinc-100">{{ euros(f.valor) }}</span>
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', corFatura(f)]">{{ f.atrasada ? 'Em atraso' : f.estado_nome }}</span>
            <button v-if="f.estado === 'paga'" type="button" @click="recibo(f)" :aria-label="`Comprovativo do pagamento ${f.id}`"
              class="px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold">
              <font-awesome-icon :icon="['fas', 'file-arrow-down']" class="mr-1" />Comprovativo
            </button>
            <!-- fatura legal do Bende (e-Fatura), registada pelo admin -->
            <a v-if="f.fatura" :href="f.fatura.pdf_url ? urlFicheiro(f.fatura.pdf_url) : null" target="_blank" rel="noopener"
              :title="f.fatura.pdf_url ? 'Descarregar a fatura' : 'Fatura registada sem PDF'"
              class="px-3 py-2 rounded-xl bg-green-500/10 hover:bg-green-500/20 text-green-400 text-xs font-semibold">
              <font-awesome-icon :icon="['fas', 'file-invoice']" class="mr-1" />Fatura {{ f.fatura.numero }}
            </a>
            <span v-else-if="f.estado === 'paga' && Number(f.valor) > 0" class="text-[11px] text-zinc-500">Fatura em breve</span>
            <button v-if="f.estado === 'pendente' && dados.pode_pagar" type="button" @click="pagar(f)" :disabled="aPagar === f.id"
              class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold">
              {{ aPagar === f.id ? 'A pagar…' : 'Pagar ' + euros(f.valor) }}
            </button>
          </div>
          </template>
        </ListaCobrancas>
        <p v-if="!dados.pode_pagar && Number(dados.por_pagar)" class="text-xs text-zinc-500 px-6 pb-4">Só o dono da loja pode pagar.</p>
      </div>

      <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
      <p v-if="aviso" class="text-sm text-green-400" role="status">{{ aviso }}</p>
    </template>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { descarregarComprovativoSubscricao, urlFicheiro } from '@/utils/documentos'
import ComissoesMensais from '@/components/fiscal/ComissoesMensais.vue'
import CobrancasComissoes from '@/components/fiscal/CobrancasComissoes.vue'
import ListaCobrancas from '@/components/subscricao/ListaCobrancas.vue'
import { seguirPagamento } from '@/utils/pagamentoOnline'

export default {
  name: 'BackofficeSubscricao',
  components: { ComissoesMensais, CobrancasComissoes, ListaCobrancas },
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['alterado'],

  data () {
    return { dados: null, carregando: true, erro: '', aviso: '', aPagar: null, aGuardar: false, novoPlano: null, novoPlanoServ: null, versao: 0 }
  },

  computed: {
    posIncluidos () { return (this.dados?.pos_ligados || []).filter(p => p.incluido) },
    sub () { return this.dados?.subscricao },
    serv () { return this.dados?.servicos },
    resumoServicos () {
      const s = this.serv?.subscricao
      if (!s) return ''
      if (s.estado === 'aguarda') return 'Começa quando pagares a 1.ª fatura.'
      if (s.estado === 'teste') return `Período de teste grátis até ${this.data(s.teste_ate)}.`
      if (s.estado === 'em_atraso') return 'Tens uma fatura de Serviços em atraso — paga para não suspender as marcações.'
      if (s.estado === 'suspensa') return 'Suspensa: as marcações novas estão paradas até pagares. A loja continua a vender.'
      return `Pago até ${this.data(s.pago_ate)}.`
    },
    limitesTexto () {
      const l = this.serv?.limites || {}
      const partes = []
      if (l.marcacoes_mes) partes.push(`${l.marcacoes_mes} marcações por mês`)
      if (l.profissionais) partes.push(l.profissionais === 1 ? '1 profissional' : `${l.profissionais} profissionais`)
      return partes.length ? 'Inclui até ' + partes.join(' e ') + '.' : ''
    },
    resumoEstado () {
      const s = this.sub
      if (!s) return ''
      if (s.estado === 'aguarda') return 'Começa quando a plataforma aprovar a loja.'
      if (s.estado === 'teste') return `Período de teste grátis até ${this.data(s.teste_ate)}.`
      if (s.estado === 'cancelada') return 'Esta subscrição foi cancelada.'
      if (s.estado === 'em_atraso') return 'Tens faturas em atraso — paga para evitar a suspensão da loja.'
      return `Tudo pago até ${this.data(s.pago_ate)}.`
    },
    corEstado () { return this.corEstadoDe(this.sub?.estado) },
    corEstadoTexto () { return this.sub?.estado === 'em_atraso' ? 'text-red-400' : 'text-zinc-400' },
  },

  created () { this.carregar() },

  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    corEstadoDe (e) {
      return { teste: 'bg-sky-500/15 text-sky-300', ativa: 'bg-green-500/15 text-green-400', em_atraso: 'bg-red-500/15 text-red-400',
               aguarda: 'bg-zinc-700 text-zinc-300', suspensa: 'bg-red-500/15 text-red-400', cancelada: 'bg-zinc-700 text-zinc-400' }[e] || ''
    },
    async servicosPedido (fn, ok = '') {
      this.erro = ''; this.aviso = ''
      this.aGuardar = true
      try {
        await fn()
        await this.carregar()
        this.novoPlanoServ = null
        if (ok) this.aviso = ok
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível mudar.'
      } finally {
        this.aGuardar = false
      }
    },
    mudarPlanoServ () {
      const p = this.serv.planos.find(x => x.id === this.novoPlanoServ)
      if (!p || !confirm(`Mudar os Serviços para o plano ${p.nome} (${this.euros(p.preco)})?\n\nVale a partir da próxima renovação.`)) return
      this.servicosPedido(() => api.post(`/app/loja/${this.lojaId}/servicos/plano/`, { plano_id: p.id }),
        'Plano de Serviços mudado — vale a partir da próxima renovação.')
    },
    mudarAutoServ () {
      this.servicosPedido(() => api.patch(`/app/loja/${this.lojaId}/servicos/config/`, { auto_renovar: !this.serv.subscricao.auto_renovar }))
    },
    data (s) { return s ? new Date(s.length === 10 ? s + 'T12:00:00' : s).toLocaleDateString('pt-PT') : '' },
    corFatura (f) {
      if (f.atrasada) return 'bg-red-500/15 text-red-400'
      return { paga: 'bg-green-500/15 text-green-400', pendente: 'bg-amber-500/15 text-amber-300', anulada: 'bg-zinc-700 text-zinc-400' }[f.estado]
    },
    async carregar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/subscricao/`)
        this.dados = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar a subscrição.'
      } finally {
        this.carregando = false
      }
    },
    async pagar (f) {
      if (!confirm(`Pagar ${this.euros(f.valor)} — ${f.descricao}?\n\n(Pagamento simulado)`)) return
      this.erro = ''; this.aviso = ''
      this.aPagar = f.id
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/subscricao/faturas/${f.id}/pagar/`)
        if (seguirPagamento(data)) return       // paga na página do fornecedor e volta a /pagamento/callback
        this.dados = data
        this.versao++
        this.aviso = 'Pagamento recebido. Obrigado!'
        this.$emit('alterado')      // o layout volta a ler a loja (pode ter sido reactivada) e a faixa
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível pagar.'
      } finally {
        this.aPagar = null
      }
    },
    recibo (f) { descarregarComprovativoSubscricao(f) },
    urlFicheiro,
    diaSeguinte (s) { const d = new Date(s + 'T12:00:00'); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10) },

    // trocas (POST /subscricao/mudar/) — as regras estão no servidor (utils/subscricoes.py)
    async mudar (corpo, ok = '') {
      this.erro = ''; this.aviso = ''
      this.aGuardar = true
      try {
        const { data } = await api.post(`/app/loja/${this.lojaId}/subscricao/mudar/`, corpo)
        this.dados = data
        this.versao++
        this.novoPlano = null
        if (ok) this.aviso = ok
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível mudar.'
      } finally {
        this.aGuardar = false
      }
    },
    pedirSubscricao (p) {
      const serv = this.serv?.subscricao ? '\n\nOs Serviços passam a estar incluídos: a subscrição de Serviços termina no fim do período já pago.' : ''
      if (!confirm(`Mudar para o plano ${p.nome} (${this.euros(p.preco)})?\n\nA subscrição começa quando pagares a 1.ª fatura — até lá continuas em comissão. Depois só podes voltar a mudar daqui a 3 meses.${serv}`)) return
      this.mudar({ acao: 'subscricao', plano_id: p.id }, 'Pedido feito — paga a 1.ª fatura para começar.')
    },
    mudarPlano () {
      const p = this.dados.planos.find(x => x.id === this.novoPlano)
      if (!p || !confirm(`Mudar para o plano ${p.nome} (${this.euros(p.preco)})?\n\nVale a partir da próxima renovação.`)) return
      this.mudar({ acao: 'plano', plano_id: p.id }, 'Plano mudado — vale a partir da próxima renovação.')
    },
    passarComissao () {
      const serv = this.serv?.ativo ? '\n\nAtenção: em comissão, o módulo Serviços precisa de uma subscrição própria para continuar a receber marcações.' : ''
      if (!confirm(`Passar para comissão (${Number(this.dados.percentagem_comissao)}% por venda)?\n\nContinuas em subscrição até ${this.data(this.sub.pago_ate)} (o que já pagaste não é devolvido). Depois só podes voltar a mudar daqui a 3 meses.${serv}`)) return
      this.mudar({ acao: 'comissao' }, 'Agendado: passas para comissão no fim do período pago.')
    },

    async mudarAuto () {
      this.aGuardar = true
      this.erro = ''
      try {
        const { data } = await api.patch(`/app/loja/${this.lojaId}/subscricao/`, { auto_renovar: !this.sub.auto_renovar })
        this.dados = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível mudar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
