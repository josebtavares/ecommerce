<!-- VariantesStockEditor.vue — grelha de stock por variação de um produto
     Backoffice: <VariantesStockEditor :lojaId="lojaId" :produtoId="p.id" @guardado="..." />
     POS:        <VariantesStockEditor :endpoint="`/api/pos/${posId}/produtos/${id}/variantes/?origem=pos`" claro />
     GET/PUT no mesmo contrato nos dois casos. Não usa <form> para poder viver dentro
     do formulário do produto. -->
<template>
  <!-- Enter não submete o formulário do produto onde o editor pode estar embebido -->
  <div class="space-y-3" @keydown.enter.prevent>
    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 3" :key="n" :class="['h-10 rounded-lg animate-pulse', c.skel]"></div>
    </div>

    <p v-else-if="erroCarregar" :class="['text-xs rounded-lg px-3 py-2', c.erro]">{{ erroCarregar }}</p>

    <!-- Sem atributos-variante -->
    <div v-else-if="!linhas.length" :class="['text-xs leading-relaxed px-3 py-3 border border-dashed rounded-xl', c.vazio]">
      Este produto não tem opções com stock próprio. Para gerir stock por tamanho, cor, etc.,
      marca o atributo como <span :class="['font-semibold', c.amberTxt]"><font-awesome-icon :icon="['fas', 'boxes-stacked']" class="mr-0.5" /> Stock por opção</span> no tipo do produto
      e selecciona as opções no produto.
    </div>

    <template v-else>
      <!-- Estado -->
      <div v-if="!grelha.stock_por_variante"
           :class="['flex items-start gap-2.5 px-3 py-2.5 rounded-xl border text-xs leading-relaxed', c.aviso]">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
        <span>
          Este produto ainda usa o <b>stock total</b> ({{ grelha.stock_total_antigo ?? 0 }} un.).
          Distribui as unidades pelas combinações e guarda para activar o stock por variação.
        </span>
      </div>
      <div v-else :class="['flex items-center gap-2 text-[11px]', c.ok]">
        <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
        Stock por variação activo — cada combinação é validada na venda.
      </div>

      <!-- Acções em massa -->
      <div class="flex items-center gap-2 flex-wrap">
        <span :class="['text-[11px]', c.muted]">Aplicar a todas:</span>
        <input v-model.number="qtdEmMassa" type="number" min="0" placeholder="qtd"
          :class="['w-20 px-2 py-1 border rounded-lg text-xs focus:outline-none', c.input]" />
        <button type="button" @click="aplicarATodas" :disabled="qtdEmMassa === '' || qtdEmMassa < 0"
          :class="['px-2.5 py-1 rounded-lg text-xs disabled:opacity-40 transition', c.btn]">Aplicar</button>
        <button type="button" @click="zerar" :class="['px-2.5 py-1 rounded-lg text-xs transition', c.link]">Zerar</button>
        <label :class="['ml-auto flex items-center gap-1.5 text-[11px] cursor-pointer select-none', c.muted]">
          <input v-model="mostrarExtras" type="checkbox" class="w-3 h-3 accent-red-500" />
          Preço e SKU por variação
        </label>
      </div>

      <!-- Grelha -->
      <div :class="['overflow-x-auto rounded-xl border', c.borda]">
        <table class="w-full text-xs">
          <thead :class="c.thead">
            <tr>
              <th v-for="a in grelha.atributos_variante" :key="a" class="px-3 py-2 text-left font-semibold capitalize whitespace-nowrap">{{ a }}</th>
              <th class="px-3 py-2 text-left font-semibold whitespace-nowrap">Quantidade</th>
              <th v-if="mostrarExtras" class="px-3 py-2 text-left font-semibold whitespace-nowrap">Preço</th>
              <th v-if="mostrarExtras" class="px-3 py-2 text-left font-semibold whitespace-nowrap">SKU</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in linhas" :key="l.chave" :class="['border-t', c.borda, Number(l.quantidade) === 0 ? c.linhaZero : '']">
              <td v-for="a in grelha.atributos_variante" :key="a" :class="['px-3 py-2 whitespace-nowrap', c.cel]">
                {{ l.combinacao[a] ?? '—' }}
              </td>
              <td class="px-3 py-1.5">
                <div class="flex items-center gap-1">
                  <button type="button" @click="l.quantidade = Math.max(0, Number(l.quantidade || 0) - 1)"
                    :class="['w-6 h-6 rounded-md', c.btn]">−</button>
                  <input v-model.number="l.quantidade" type="number" min="0" step="1"
                    :class="['w-16 px-2 py-1 border rounded-md text-center focus:outline-none',
                             c.input, !qtdValida(l.quantidade) && '!border-red-500']" />
                  <button type="button" @click="l.quantidade = Number(l.quantidade || 0) + 1"
                    :class="['w-6 h-6 rounded-md', c.btn]">+</button>
                  <span v-if="Number(l.quantidade) === 0" class="ml-1 text-[10px] text-red-500">esgotado</span>
                  <span v-else-if="Number(l.quantidade) <= 5" class="ml-1 text-[10px] text-amber-500">baixo</span>
                </div>
              </td>
              <td v-if="mostrarExtras" class="px-3 py-1.5">
                <input v-model="l.preco" type="number" min="0" step="1" :placeholder="grelha.preco_produto"
                  :class="['w-24 px-2 py-1 border rounded-md focus:outline-none', c.input]" />
              </td>
              <td v-if="mostrarExtras" class="px-3 py-1.5">
                <input v-model="l.sku" maxlength="100" placeholder="—"
                  :class="['w-28 px-2 py-1 border rounded-md focus:outline-none', c.input]" />
              </td>
            </tr>
          </tbody>
          <tfoot :class="['border-t', c.tfoot]">
            <tr>
              <td :colspan="grelha.atributos_variante.length" class="px-3 py-2 font-semibold">
                Total · {{ linhas.length }} combinações
              </td>
              <td :class="['px-3 py-2 font-bold', c.forte]">{{ total }} un.</td>
              <td v-if="mostrarExtras" colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p v-if="mostrarExtras" :class="['text-[10px]', c.muted]">Preço vazio = usa o preço do produto ({{ grelha.preco_produto }}).</p>

      <p v-if="erro" :class="['text-xs rounded-lg px-3 py-2', c.erro]">{{ erro }}</p>

      <!-- Acções -->
      <div class="flex items-center gap-2 flex-wrap">
        <span v-if="sujo" class="text-[11px] text-amber-500 flex items-center gap-1.5 mr-auto">
          <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Alterações por guardar
        </span>
        <button v-if="grelha.stock_por_variante" type="button" @click="desactivar" :disabled="saving"
          :class="['px-3 py-2 rounded-xl text-xs transition', c.link, !sujo && 'mr-auto']">
          Voltar ao stock total
        </button>
        <button type="button" @click="guardar" :disabled="saving || !valido || (!sujo && grelha.stock_por_variante)"
          :class="['px-4 py-2 rounded-xl text-xs font-bold transition ml-auto',
                   saving || !valido || (!sujo && grelha.stock_por_variante) ? c.primDis : c.prim]">
          {{ saving ? 'A guardar…' : grelha.stock_por_variante ? 'Guardar stock' : 'Activar stock por variação' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'

const TEMAS = {
  escuro: {
    skel: 'bg-zinc-800/60', erro: 'text-red-400 bg-red-500/10', vazio: 'text-zinc-500 border-zinc-800',
    amberTxt: 'text-amber-300', aviso: 'border-amber-500/30 bg-amber-500/5 text-amber-200/90', ok: 'text-green-400',
    muted: 'text-zinc-500', input: 'bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-600 focus:border-red-500',
    btn: 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300', link: 'text-zinc-500 hover:text-zinc-300',
    borda: 'border-zinc-800', thead: 'bg-zinc-800/60 text-zinc-500', cel: 'text-zinc-200', linhaZero: 'bg-red-500/[0.03]',
    tfoot: 'border-zinc-700 bg-zinc-800/40 text-zinc-400', forte: 'text-zinc-100',
    prim: 'bg-red-600 hover:bg-red-500 text-white', primDis: 'bg-zinc-800 text-zinc-500 cursor-not-allowed',
  },
  claro: {
    skel: 'bg-slate-100', erro: 'text-red-700 bg-red-50', vazio: 'text-slate-500 border-slate-200',
    amberTxt: 'text-amber-600', aviso: 'border-amber-300 bg-amber-50 text-amber-800', ok: 'text-emerald-600',
    muted: 'text-slate-500', input: 'bg-slate-50 border-slate-200 text-slate-900 placeholder-slate-400 focus:border-slate-950',
    btn: 'bg-slate-100 hover:bg-slate-200 text-slate-700', link: 'text-slate-500 hover:text-slate-900',
    borda: 'border-slate-200', thead: 'bg-slate-50 text-slate-500', cel: 'text-slate-800', linhaZero: 'bg-red-50/60',
    tfoot: 'border-slate-200 bg-slate-50 text-slate-600', forte: 'text-slate-950',
    prim: 'bg-slate-950 hover:bg-slate-800 text-white', primDis: 'bg-slate-100 text-slate-400 cursor-not-allowed',
  },
}

export default {
  name: 'VariantesStockEditor',

  props: {
    lojaId:    { type: [String, Number], default: null },
    produtoId: { type: [String, Number], default: null },
    // URL completo da grelha (ex.: POS). Por omissão usa o do backoffice da loja.
    endpoint:  { type: String, default: '' },
    claro:     { type: Boolean, default: false },
  },

  emits: ['guardado'],

  data () {
    return {
      loading: true, saving: false,
      erro: '', erroCarregar: '',
      grelha: { atributos_variante: [], variantes: [], stock_por_variante: false },
      linhas: [],
      original: '',
      qtdEmMassa: '',
      mostrarExtras: false,
    }
  },

  computed: {
    c () { return this.claro ? TEMAS.claro : TEMAS.escuro },
    url () { return this.endpoint || `/app/loja/${this.lojaId}/produtos/${this.produtoId}/variantes/` },
    total () { return this.linhas.reduce((s, l) => s + (Number(l.quantidade) || 0), 0) },
    valido () { return this.linhas.every(l => this.qtdValida(l.quantidade)) },
    sujo () { return JSON.stringify(this.payload()) !== this.original },
  },

  watch: {
    url () { this.carregar() },
  },

  created () { this.carregar() },

  methods: {
    qtdValida (q) { return Number.isInteger(Number(q)) && Number(q) >= 0 && q !== '' },

    payload () {
      return this.linhas.map(l => ({
        chave: l.chave,
        quantidade: Number(l.quantidade) || 0,
        preco: l.preco === '' || l.preco === null || l.preco === undefined ? null : String(l.preco),
        sku: (l.sku || '').trim(),
      }))
    },

    aplicar (data) {
      this.grelha = data
      this.linhas = (data.variantes || []).map(v => ({
        chave: v.chave, combinacao: v.combinacao,
        quantidade: v.quantidade ?? 0, preco: v.preco ?? '', sku: v.sku || '',
      }))
      this.mostrarExtras = this.mostrarExtras || this.linhas.some(l => l.preco !== '' || l.sku)
      this.original = JSON.stringify(this.payload())
    },

    async carregar () {
      this.loading = true
      this.erroCarregar = ''
      try {
        const { data } = await api.get(this.url)
        this.aplicar(data)
      } catch (e) {
        this.erroCarregar = e.response?.data?.detail || 'Não foi possível carregar as variações.'
      } finally {
        this.loading = false
      }
    },

    aplicarATodas () {
      const q = Math.max(0, Math.floor(Number(this.qtdEmMassa) || 0))
      this.linhas.forEach(l => { l.quantidade = q })
    },

    zerar () { this.linhas.forEach(l => { l.quantidade = 0 }) },

    async guardar () {
      this.saving = true
      this.erro = ''
      try {
        const { data } = await api.put(this.url, { variantes: this.payload() })
        const activou = !this.grelha.stock_por_variante
        this.aplicar(data)
        toast.success(activou ? 'Stock por variação activado.' : 'Stock guardado.')
        this.$emit('guardado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao guardar.'
      } finally {
        this.saving = false
      }
    },

    async desactivar () {
      if (!confirm(`Voltar ao stock total? O produto passa a ter ${this.grelha.total} unidades sem distinção de variação.`)) return
      this.saving = true
      this.erro = ''
      try {
        const { data } = await api.put(this.url, { stock_por_variante: false })
        this.aplicar(data)
        toast.info('O produto voltou a usar stock total.')
        this.$emit('guardado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao desactivar.'
      } finally {
        this.saving = false
      }
    },
  },
}
</script>
