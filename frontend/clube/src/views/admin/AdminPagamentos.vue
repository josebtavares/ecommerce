<template>
  <!-- Admin → Pagamentos (gerir_pagamentos): o estado do dinheiro — o que entrou, o que está pendente ou falhou, o que
       falta devolver. A parte fiscal (faturas) é a Faturação. Backend Views/pagamentosAdminView.py. -->
  <div class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Pagamentos</h2>
        <p class="text-xs text-zinc-500 mt-0.5">{{ vista === 'lojas' ? 'Pagamentos dos clientes às lojas: encomendas e marcações pagas online' : 'O dinheiro que é do Bende: mensalidades e comissões pagas' }}</p>
      </div>
      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1" role="tablist">
        <button v-for="t in VISTAS" :key="t.key" type="button" role="tab" :aria-selected="vista === t.key ? 'true' : 'false'"
          @click="mudarVista(t.key)" :data-teste="`vista-${t.key}`"
          :class="['px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap transition', vista === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- período (as duas vistas) -->
    <div class="flex flex-wrap items-end gap-2">
      <label class="text-[11px] text-zinc-500">Período
        <select v-model="periodo" @change="mudarPeriodo" data-teste="pag-periodo"
          class="block mt-1 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
          <option v-for="p in PERIODOS" :key="p.v" :value="p.v">{{ p.t }}</option>
        </select>
      </label>
      <template v-if="periodo === 'personalizado'">
        <label class="text-[11px] text-zinc-500">De <input type="date" v-model="de" @change="recarregar()" data-teste="pag-de"
          class="block mt-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
        <label class="text-[11px] text-zinc-500">a <input type="date" v-model="ate" @change="recarregar()" data-teste="pag-ate"
          class="block mt-1 px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" /></label>
      </template>
      <p class="text-xs text-zinc-500 pb-2">{{ textoPeriodo }}</p>
    </div>
    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <!-- ═══ PAGAMENTOS DAS LOJAS ═══ -->
    <template v-if="vista === 'lojas'">
      <!-- cartões (clicáveis = filtram a lista) -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" data-teste="pag-resumo">
        <button type="button" @click="filtrarEstado('')" data-teste="cartao-recebido"
          class="text-left bg-zinc-900 rounded-2xl border border-zinc-800 hover:border-zinc-600 px-4 py-3 transition">
          <p class="text-[11px] text-zinc-500">Recebido no período</p>
          <p class="text-lg font-bold tabular-nums text-green-400">{{ res ? euros(res.recebido.valor) : '…' }}</p>
          <p class="text-[11px] text-zinc-500">{{ res ? `${res.recebido.n} pagamento(s)` : '' }}<template v-if="res && Number(res.devolvido)"> · devolvido {{ euros(res.devolvido) }}</template></p>
        </button>
        <button type="button" @click="filtrarEstado('pendente')" data-teste="cartao-pendentes"
          :class="['text-left bg-zinc-900 rounded-2xl border px-4 py-3 transition', res && res.pendentes.transferencias.perto_do_prazo ? 'border-red-500/50 hover:border-red-400' : 'border-zinc-800 hover:border-zinc-600']">
          <p class="text-[11px] text-zinc-500">Pendentes (agora)</p>
          <p class="text-lg font-bold tabular-nums text-amber-300">{{ res ? res.pendentes.n : '…' }} <span class="text-xs font-semibold text-zinc-400">{{ res ? euros(res.pendentes.valor) : '' }}</span></p>
          <p v-if="res" class="text-[11px] text-zinc-500">
            {{ res.pendentes.transferencias.n }} transferência(s)<template v-if="res.pendentes.transferencias.perto_do_prazo"> ·
              <span class="text-red-300 font-bold" data-teste="perto-do-prazo">{{ res.pendentes.transferencias.perto_do_prazo }} perto do prazo</span></template>
            · {{ res.pendentes.dinheiro.n }} na entrega · {{ res.pendentes.online.n }} online
          </p>
        </button>
        <button type="button" @click="filtrarEstado('falhado')" data-teste="cartao-falhados"
          class="text-left bg-zinc-900 rounded-2xl border border-zinc-800 hover:border-zinc-600 px-4 py-3 transition">
          <p class="text-[11px] text-zinc-500">Falhados no período</p>
          <p :class="['text-lg font-bold tabular-nums', res && res.falhados.n ? 'text-red-400' : 'text-zinc-300']">{{ res ? res.falhados.n : '…' }}</p>
          <p class="text-[11px] text-zinc-500">{{ res ? euros(res.falhados.valor) : '' }}</p>
        </button>
        <button type="button" @click="$emit('ir', 'devolucoes')" data-teste="cartao-reembolsos"
          :class="['text-left bg-zinc-900 rounded-2xl border px-4 py-3 transition', res && res.reembolsos_por_concluir ? 'border-amber-500/40 hover:border-amber-400' : 'border-zinc-800 hover:border-zinc-600']">
          <p class="text-[11px] text-zinc-500">Reembolsos por concluir</p>
          <p :class="['text-lg font-bold tabular-nums', res && res.reembolsos_por_concluir ? 'text-amber-300' : 'text-zinc-300']">{{ res ? res.reembolsos_por_concluir : '…' }}</p>
          <p class="text-[11px] text-zinc-500">{{ res && res.incertos ? `${res.incertos} a confirmar no fornecedor · ` : '' }}Abrir Devoluções →</p>
        </button>
      </div>

      <AbasVendedores ref="abas" url="/app/admin/pagamentos/abas/" :ativo="loja ? `loja-${loja.id}` : null" titulo="Pagamentos pendentes"
        @selecionar="selecionarLoja" />

      <form @submit.prevent="carregar(0)" class="flex flex-wrap items-end gap-2" data-teste="pag-filtros">
        <input v-model.trim="f.q" type="search" placeholder="E-123, M-45, cliente, loja ou referência" aria-label="Pesquisar pagamentos" data-teste="pag-q"
          class="flex-1 min-w-[200px] px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
        <select v-model="f.origem" @change="carregar(0)" aria-label="Origem" data-teste="pag-origem" :class="sel">
          <option value="">Encomendas e marcações</option><option value="encomendas">Só encomendas</option><option value="marcacoes">Só marcações</option>
        </select>
        <select v-model="f.estado" @change="carregar(0)" aria-label="Estado" data-teste="pag-estado" :class="sel">
          <option value="">Todos os estados</option>
          <option v-for="(t, k) in ESTADOS" :key="k" :value="k">{{ t }}</option>
        </select>
        <select v-model="f.metodo" @change="carregar(0)" aria-label="Método" data-teste="pag-metodo" :class="sel">
          <option value="">Todos os métodos</option>
          <option v-for="m in METODOS" :key="m.v" :value="m.v">{{ m.t }}</option>
        </select>
        <select v-model="f.fornecedor" @change="carregar(0)" aria-label="Fornecedor" data-teste="pag-fornecedor" :class="sel">
          <option value="">Qualquer fornecedor</option><option value="nenhum">Sem fornecedor (dinheiro / transferência)</option>
          <option v-for="x in fornecedores" :key="x" :value="x">{{ x }}</option>
        </select>
        <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
        <button type="button" @click="csv" data-teste="pag-csv" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">
          <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV
        </button>
      </form>
      <p class="text-xs text-zinc-500">{{ lista.count }} pagamento(s){{ loja ? ` · ${loja.nome}` : '' }} · pedidos no período</p>

      <div v-if="carregando && !lista.results.length" class="space-y-2"><div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div></div>
      <div v-else class="space-y-2" data-teste="pag-lista">
        <div v-for="p in lista.results" :key="p.origem + p.id" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" :data-teste="`pag-${p.referencia_doc}`">
          <button type="button" @click="aberto = aberto === p.referencia_doc ? '' : p.referencia_doc" :aria-expanded="aberto === p.referencia_doc ? 'true' : 'false'"
            class="w-full flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left hover:bg-zinc-800/40 transition">
            <div class="w-9 h-9 rounded-xl bg-zinc-800 text-zinc-300 flex items-center justify-center flex-shrink-0">
              <font-awesome-icon :icon="['fas', p.origem === 'marcacao' ? 'calendar-check' : iconeMetodo(p.metodo)]" class="w-4 h-4" />
            </div>
            <div class="flex-1 min-w-[180px]">
              <p class="text-sm font-semibold text-zinc-200">{{ p.loja.nome }} <span class="text-[11px] text-zinc-500 font-normal">· {{ p.referencia_doc }}</span></p>
              <p class="text-[11px] text-zinc-500">{{ p.cliente || '—' }} · {{ p.metodo_label }}<template v-if="p.fornecedor"> · {{ p.fornecedor }}</template> · {{ quando(p.criado_em) }}</p>
            </div>
            <span v-if="p.prazo" :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', p.prazo_perto ? 'bg-red-500/20 text-red-300' : 'bg-zinc-800 text-zinc-400']" data-teste="pag-prazo">
              Confirmar até {{ quando(p.prazo) }}
            </span>
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', COR[p.estado]]" data-teste="pag-estado-linha">{{ p.estado_label }}</span>
            <span class="text-sm font-bold tabular-nums text-zinc-100 w-28 text-right">{{ euros(p.valor) }}</span>
            <font-awesome-icon :icon="['fas', aberto === p.referencia_doc ? 'chevron-up' : 'chevron-down']" class="text-zinc-600 text-xs" />
          </button>
          <div v-if="aberto === p.referencia_doc" class="border-t border-zinc-800 px-4 py-4 space-y-3" data-teste="pag-detalhe">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div class="bg-zinc-800/60 rounded-xl p-3"><p class="text-[10px] text-zinc-500">Valor</p><p class="text-sm font-bold text-zinc-100">{{ euros(p.valor) }}</p></div>
              <div class="bg-zinc-800/60 rounded-xl p-3"><p class="text-[10px] text-zinc-500">Devolvido ao cliente</p>
                <p :class="['text-sm font-bold', Number(p.reembolsado) ? 'text-sky-300' : 'text-zinc-500']">{{ Number(p.reembolsado) ? '− ' + euros(p.reembolsado) : '—' }}</p></div>
              <div class="bg-zinc-800/60 rounded-xl p-3"><p class="text-[10px] text-zinc-500">Comissão do Bende</p>
                <p :class="['text-sm font-bold', Number(p.comissao) ? 'text-red-300' : 'text-zinc-500']" data-teste="pag-comissao">{{ Number(p.comissao) ? '− ' + euros(p.comissao) : '—' }}</p></div>
              <div class="bg-zinc-800/60 rounded-xl p-3"><p class="text-[10px] text-zinc-500">Fica para a loja</p>
                <p class="text-sm font-bold text-green-400" data-teste="pag-receita">{{ p.receita_loja !== null ? euros(p.receita_loja) : 'ainda não pago' }}</p></div>
            </div>
            <div class="grid sm:grid-cols-2 gap-x-6 gap-y-1 text-xs">
              <p class="flex justify-between gap-3"><span class="text-zinc-500">Pedido em</span><span class="text-zinc-300">{{ quando(p.criado_em) }}</span></p>
              <p class="flex justify-between gap-3"><span class="text-zinc-500">Pago em</span><span class="text-zinc-300">{{ p.pago_em ? quando(p.pago_em) : '—' }}</span></p>
              <p class="flex justify-between gap-3"><span class="text-zinc-500">Método</span><span class="text-zinc-300">{{ p.metodo_label }}</span></p>
              <p class="flex justify-between gap-3"><span class="text-zinc-500">Fornecedor</span><span class="text-zinc-300">{{ p.fornecedor || '—' }}</span></p>
              <p class="flex justify-between gap-3 sm:col-span-2"><span class="text-zinc-500">Referência da transação</span><span class="text-zinc-300 break-all text-right">{{ p.referencia || '—' }}</span></p>
            </div>
            <div class="flex flex-wrap gap-2">
              <router-link v-if="p.origem === 'encomenda'" :to="`/admin/encomendas/${p.doc_id}`" data-teste="pag-ver-encomenda"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">
                <font-awesome-icon :icon="['fas', 'bag-shopping']" class="mr-1" />Ver encomenda</router-link>
              <router-link :to="{ path: '/admin/faturacao', query: { ficha: `loja-${p.loja.id}`, aba: 'vendas', q: p.referencia_doc } }" data-teste="pag-ver-faturacao"
                class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">
                <font-awesome-icon :icon="['fas', 'file-invoice']" class="mr-1" />Ver na Faturação</router-link>
            </div>
          </div>
        </div>
        <p v-if="!lista.results.length" class="text-center py-10 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Nenhum pagamento com estes filtros.</p>
      </div>
      <PaginacaoLista :count="lista.count" :limit="LIMITE" :offset="offset" @ir="carregar" />
    </template>

    <!-- ═══ RECEBIMENTOS DO BENDE ═══ -->
    <template v-else>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3" data-teste="bende-totais">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3">
          <p class="text-[11px] text-zinc-500">Recebido pelo Bende</p>
          <p class="text-lg font-bold tabular-nums text-green-400">{{ bende ? euros(bende.totais.valor) : '…' }}</p>
          <p class="text-[11px] text-zinc-500">{{ bende ? `${bende.count} pagamento(s)` : '' }}</p>
        </div>
        <button type="button" @click="fb.tipo = fb.tipo === 'mensalidade' ? '' : 'mensalidade'; carregarBende(0)"
          :class="['text-left bg-zinc-900 rounded-2xl border px-4 py-3 transition', fb.tipo === 'mensalidade' ? 'border-violet-400/60' : 'border-zinc-800 hover:border-zinc-600']">
          <p class="text-[11px] text-zinc-500">Mensalidades</p>
          <p class="text-lg font-bold tabular-nums text-zinc-100">{{ bende ? euros(bende.totais.mensalidades.valor) : '…' }}</p>
          <p class="text-[11px] text-zinc-500">{{ bende ? `${bende.totais.mensalidades.n} paga(s)` : '' }}</p>
        </button>
        <button type="button" @click="fb.tipo = fb.tipo === 'cobranca' ? '' : 'cobranca'; carregarBende(0)"
          :class="['text-left bg-zinc-900 rounded-2xl border px-4 py-3 transition', fb.tipo === 'cobranca' ? 'border-sky-400/60' : 'border-zinc-800 hover:border-zinc-600']">
          <p class="text-[11px] text-zinc-500">Comissões cobradas</p>
          <p class="text-lg font-bold tabular-nums text-zinc-100">{{ bende ? euros(bende.totais.cobrancas.valor) : '…' }}</p>
          <p class="text-[11px] text-zinc-500">{{ bende ? `${bende.totais.cobrancas.n} cobrança(s) paga(s)` : '' }}</p>
        </button>
      </div>
      <form @submit.prevent="carregarBende(0)" class="flex flex-wrap items-end gap-2">
        <input v-model.trim="fb.q" type="search" placeholder="Loja, POS, S-12 ou CC-3" aria-label="Pesquisar recebimentos" data-teste="bende-q"
          class="flex-1 min-w-[200px] px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-red-500" />
        <select v-model="fb.tipo" @change="carregarBende(0)" aria-label="Tipo" data-teste="bende-tipo" :class="sel">
          <option value="">Mensalidades e comissões</option><option value="mensalidade">Só mensalidades</option><option value="cobranca">Só comissões</option>
        </select>
        <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
        <button type="button" @click="csvBende" data-teste="bende-csv" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold">
          <font-awesome-icon :icon="['fas', 'file-csv']" class="mr-1" />CSV
        </button>
      </form>
      <p class="text-[11px] text-zinc-500">As ofertas da plataforma (mensalidades e comissões perdoadas) não contam: não entrou dinheiro.</p>
      <div v-if="carregando && !bende" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
      <div v-else-if="bende" class="bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800" data-teste="bende-lista">
        <div v-for="r in bende.results" :key="r.referencia" class="px-4 py-3 space-y-2" :data-teste="`receb-${r.referencia}`">
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', r.tipo === 'cobranca' ? 'bg-sky-500/15 text-sky-300' : 'bg-violet-500/15 text-violet-300']">
              {{ r.tipo === 'cobranca' ? 'Comissões' : 'Mensalidade' }}</span>
            <div class="flex-1 min-w-[180px]">
              <p class="text-sm text-zinc-200">{{ r.nome }} <span class="text-[11px] text-zinc-500">· {{ r.referencia }}</span></p>
              <p class="text-[11px] text-zinc-500">{{ r.descricao }} · paga a {{ quando(r.pago_em) }} · {{ r.metodo_label }}</p>
            </div>
            <span class="text-sm font-bold tabular-nums text-zinc-100">{{ euros(r.valor) }}</span>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <SecaoDocumento>
              <BotaoPdf texto="Comprovativo" :titulo="`Descarregar o comprovativo ${r.referencia} (PDF)`" teste="receb-comprovativo" @click="comprovativo(r)" />
            </SecaoDocumento>
            <SecaoDocumento tipo="fatura">
              <template v-if="r.tipo === 'mensalidade'">
                <template v-if="r.fatura">
                  <span class="text-xs text-green-400 font-semibold">{{ r.fatura.numero }}</span>
                  <BotaoPdf v-if="r.fatura.pdf_url" :href="urlFicheiro(r.fatura.pdf_url)" titulo="Descarregar a fatura do Bende (PDF)" />
                </template>
                <span v-else class="text-[11px] text-amber-300">Por registar</span>
              </template>
              <span v-else class="text-[11px] text-zinc-500">Uma por mês</span>
              <router-link :to="{ path: '/admin/faturacao', query: { ficha: `${r.alvo}-${r.alvo_id}`, aba: 'bende' } }"
                class="text-[11px] text-zinc-400 hover:text-zinc-200">Faturação →</router-link>
            </SecaoDocumento>
          </div>
        </div>
        <p v-if="!bende.results.length" class="text-center py-10 text-sm text-zinc-500">Nenhum recebimento neste período.</p>
      </div>
      <PaginacaoLista v-if="bende" :count="bende.count" :limit="LIMITE" :offset="bOffset" @ir="carregarBende" />
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatarDinheiro } from '@/utils/dinheiro'
import { descarregarPdf, erroDeBlob, urlFicheiro } from '@/utils/documentos'
import { iconePagamento } from '@/utils/icones'
import { PERIODOS, intervalo, textoPeriodo } from '@/utils/periodosFaturacao'
import { ouvirPainel } from '@/utils/tempoRealEncomendas'
import AbasVendedores from '@/components/fiscal/AbasVendedores.vue'
import BotaoPdf from '@/components/fiscal/BotaoPdf.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import SecaoDocumento from '@/components/fiscal/SecaoDocumento.vue'

const LIMITE = 20
const VISTAS = [{ key: 'lojas', label: 'Pagamentos das lojas' }, { key: 'bende', label: 'Recebimentos do Bende' }]
const ESTADOS = { aprovado: 'Pago', pendente: 'Pendente', falhado: 'Falhado', reembolsado: 'Reembolsado',
  reembolsado_parcial: 'Reembolsado em parte', cancelado: 'Não pago' }
const COR = { aprovado: 'bg-green-500/15 text-green-400', pendente: 'bg-amber-500/15 text-amber-300', falhado: 'bg-red-500/15 text-red-400',
  reembolsado: 'bg-sky-500/15 text-sky-300', reembolsado_parcial: 'bg-sky-500/15 text-sky-300', cancelado: 'bg-zinc-700/50 text-zinc-400' }
const METODOS = [{ v: 'cartao', t: 'Cartão' }, { v: 'transferencia', t: 'Transferência' }, { v: 'dinheiro', t: 'Dinheiro' },
  { v: 'mobile_money', t: 'Mobile Money' }, { v: 'flutterwave', t: 'Flutterwave' }, { v: 'online', t: 'Online (marcação)' }]

export default {
  name: 'AdminPagamentos',
  components: { AbasVendedores, BotaoPdf, PaginacaoLista, SecaoDocumento },
  emits: ['ir'],
  data () {
    const [de, ate] = intervalo('mes')
    return {
      LIMITE, VISTAS, ESTADOS, COR, METODOS, PERIODOS,
      vista: 'lojas', periodo: 'mes', de, ate,
      res: null, lista: { count: 0, results: [] }, offset: 0, fornecedores: [], aberto: '',
      f: { q: '', origem: '', estado: '', metodo: '', fornecedor: '' }, loja: null,
      bende: null, bOffset: 0, fb: { q: '', tipo: '' },
      carregando: false, erro: '',
      sel: 'px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200',
    }
  },
  computed: {
    textoPeriodo () { return textoPeriodo(this.de, this.ate) },
    datas () { return { ...(this.de ? { de: this.de } : {}), ...(this.ate ? { ate: this.ate } : {}) } },
    params () {
      const p = { ...this.datas }
      for (const [k, v] of Object.entries(this.f)) if (v) p[k] = v
      if (this.loja) p.loja_id = this.loja.id
      return p
    },
  },
  created () {
    this.recarregar()
    // pagamento aprovado/falhado/reembolsado, mensalidade ou cobrança paga — aqui, noutra sessão ou pelo fornecedor
    this.pararTempoReal = ouvirPainel(() => this.recarregar(true))
  },
  beforeUnmount () { this.pararTempoReal?.() },
  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    urlFicheiro,
    iconeMetodo (m) { return iconePagamento(m) || 'credit-card' },
    quando (d) {
      return d ? new Date(d).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
    },
    mudarVista (v) { this.vista = v; this.recarregar() },
    mudarPeriodo () {
      if (this.periodo !== 'personalizado') [this.de, this.ate] = intervalo(this.periodo)
      this.recarregar()
    },
    recarregar (silencioso = false) {
      if (this.vista === 'lojas') {
        this.carregarResumo()
        this.carregar(this.offset, silencioso)
        if (silencioso) this.$refs.abas?.recarregar()
      } else this.carregarBende(this.bOffset, silencioso)
    },
    filtrarEstado (e) { this.f.estado = e; this.carregar(0) },
    selecionarLoja (v) { this.loja = v; this.carregarResumo(); this.carregar(0) },
    async carregarResumo () {
      try {
        const { data } = await api.get('/app/admin/pagamentos/resumo/', { params: { ...this.datas, ...(this.loja ? { loja_id: this.loja.id } : {}) } })
        this.res = data
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar o resumo.' }
    },
    async carregar (offset = this.offset, silencioso = false) {
      this.offset = offset
      if (!silencioso) { this.carregando = true; this.erro = '' }
      try {
        const { data } = await api.get('/app/admin/pagamentos/', { params: { ...this.params, limit: LIMITE, offset } })
        this.lista = data
        this.fornecedores = data.fornecedores || []
      } catch (e) {
        if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar os pagamentos.'
      } finally { if (!silencioso) this.carregando = false }
    },
    async carregarBende (offset = this.bOffset, silencioso = false) {
      this.bOffset = offset
      if (!silencioso) { this.carregando = true; this.erro = '' }
      try {
        const params = { ...this.datas, limit: LIMITE, offset }
        if (this.fb.q) params.q = this.fb.q
        if (this.fb.tipo) params.tipo = this.fb.tipo
        const { data } = await api.get('/app/admin/pagamentos/bende/', { params })
        this.bende = data
      } catch (e) {
        if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar os recebimentos.'
      } finally { if (!silencioso) this.carregando = false }
    },
    async csv () {
      try {
        await descarregarPdf('/app/admin/pagamentos.csv', `pagamentos-${this.de || 'inicio'}-${this.ate || 'hoje'}.csv`, this.params)
      } catch (e) { this.erro = await erroDeBlob(e, 'Não foi possível exportar.') }
    },
    async csvBende () {
      const params = { ...this.datas }
      if (this.fb.q) params.q = this.fb.q
      if (this.fb.tipo) params.tipo = this.fb.tipo
      try {
        await descarregarPdf('/app/admin/pagamentos/bende.csv', `recebimentos-bende-${this.de || 'inicio'}-${this.ate || 'hoje'}.csv`, params)
      } catch (e) { this.erro = await erroDeBlob(e, 'Não foi possível exportar.') }
    },
    comprovativo (r) {
      const url = r.tipo === 'mensalidade' ? `/app/subscricao/faturas/${r.id}/comprovativo/` : `/app/comissoes/cobrancas/${r.id}/comprovativo/`
      descarregarPdf(url, `comprovativo-${r.referencia}.pdf`).catch(() => { this.erro = 'Não foi possível descarregar o comprovativo.' })
    },
  },
}
</script>
