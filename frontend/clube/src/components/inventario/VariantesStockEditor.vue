<!-- VariantesStockEditor.vue — grelha de stock por variação de um produto
     Uso: <VariantesStockEditor :lojaId="lojaId" :produtoId="p.id" @guardado="..." />
     Lê/grava em /app/loja/<loja>/produtos/<id>/variantes/ (GET/PUT).
     Não usa <form> para poder viver dentro do formulário do produto. -->
<template>
  <!-- Enter não submete o formulário do produto onde o editor pode estar embebido -->
  <div class="space-y-3" @keydown.enter.prevent>
    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 3" :key="n" class="h-10 bg-zinc-800/60 rounded-lg animate-pulse"></div>
    </div>

    <p v-else-if="erroCarregar" class="text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2">{{ erroCarregar }}</p>

    <!-- Sem atributos-variante -->
    <div v-else-if="!linhas.length"
         class="text-xs text-zinc-500 leading-relaxed px-3 py-3 border border-dashed border-zinc-800 rounded-xl">
      Este produto não tem opções com stock próprio. Para gerir stock por tamanho, cor, etc.,
      marca o atributo como <span class="text-amber-300 font-semibold">📦 Stock por opção</span> no tipo do produto
      e selecciona as opções no produto.
    </div>

    <template v-else>
      <!-- Estado -->
      <div v-if="!grelha.stock_por_variante"
           class="flex items-start gap-2.5 px-3 py-2.5 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-amber-200/90 leading-relaxed">
        <span class="text-base leading-none">⚠️</span>
        <span>
          Este produto ainda usa o <b>stock total</b> ({{ grelha.stock_total_antigo ?? 0 }} un.).
          Distribui as unidades pelas combinações e guarda para activar o stock por variação.
        </span>
      </div>
      <div v-else class="flex items-center gap-2 text-[11px] text-green-400">
        <span class="w-1.5 h-1.5 rounded-full bg-green-400"></span>
        Stock por variação activo — o carrinho valida cada combinação.
      </div>

      <!-- Acções em massa -->
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-[11px] text-zinc-500">Aplicar a todas:</span>
        <input v-model.number="qtdEmMassa" type="number" min="0" placeholder="qtd"
          class="w-20 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
        <button type="button" @click="aplicarATodas" :disabled="qtdEmMassa === '' || qtdEmMassa < 0"
          class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 disabled:opacity-40 transition">Aplicar</button>
        <button type="button" @click="zerar"
          class="px-2.5 py-1 rounded-lg text-xs text-zinc-500 hover:text-zinc-300 transition">Zerar</button>
        <label class="ml-auto flex items-center gap-1.5 text-[11px] text-zinc-500 cursor-pointer select-none">
          <input v-model="mostrarExtras" type="checkbox" class="w-3 h-3 accent-red-500" />
          Preço e SKU por variação
        </label>
      </div>

      <!-- Grelha -->
      <div class="overflow-x-auto rounded-xl border border-zinc-800">
        <table class="w-full text-xs">
          <thead class="bg-zinc-800/60 text-zinc-500">
            <tr>
              <th v-for="a in grelha.atributos_variante" :key="a" class="px-3 py-2 text-left font-semibold capitalize whitespace-nowrap">{{ a }}</th>
              <th class="px-3 py-2 text-left font-semibold whitespace-nowrap">Quantidade</th>
              <th v-if="mostrarExtras" class="px-3 py-2 text-left font-semibold whitespace-nowrap">Preço</th>
              <th v-if="mostrarExtras" class="px-3 py-2 text-left font-semibold whitespace-nowrap">SKU</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in linhas" :key="l.chave" class="border-t border-zinc-800"
                :class="Number(l.quantidade) === 0 ? 'bg-red-500/[0.03]' : ''">
              <td v-for="a in grelha.atributos_variante" :key="a" class="px-3 py-2 text-zinc-200 whitespace-nowrap">
                {{ l.combinacao[a] ?? '—' }}
              </td>
              <td class="px-3 py-1.5">
                <div class="flex items-center gap-1">
                  <button type="button" @click="l.quantidade = Math.max(0, Number(l.quantidade || 0) - 1)"
                    class="w-6 h-6 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400">−</button>
                  <input v-model.number="l.quantidade" type="number" min="0" step="1"
                    :class="['w-16 px-2 py-1 bg-zinc-800 border rounded-md text-center text-zinc-100 focus:outline-none focus:border-red-500',
                             qtdValida(l.quantidade) ? 'border-zinc-700' : 'border-red-500']" />
                  <button type="button" @click="l.quantidade = Number(l.quantidade || 0) + 1"
                    class="w-6 h-6 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400">+</button>
                  <span v-if="Number(l.quantidade) === 0" class="ml-1 text-[10px] text-red-400">esgotado</span>
                  <span v-else-if="Number(l.quantidade) <= 5" class="ml-1 text-[10px] text-amber-400">baixo</span>
                </div>
              </td>
              <td v-if="mostrarExtras" class="px-3 py-1.5">
                <input v-model="l.preco" type="number" min="0" step="0.01" :placeholder="grelha.preco_produto"
                  class="w-24 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-md text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
              </td>
              <td v-if="mostrarExtras" class="px-3 py-1.5">
                <input v-model="l.sku" maxlength="100" placeholder="—"
                  class="w-28 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-md text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
              </td>
            </tr>
          </tbody>
          <tfoot class="border-t border-zinc-700 bg-zinc-800/40">
            <tr>
              <td :colspan="grelha.atributos_variante.length" class="px-3 py-2 text-zinc-400 font-semibold">
                Total · {{ linhas.length }} combinações
              </td>
              <td class="px-3 py-2 text-zinc-100 font-bold">{{ total }} un.</td>
              <td v-if="mostrarExtras" colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p v-if="mostrarExtras" class="text-[10px] text-zinc-600">Preço vazio = usa o preço do produto ({{ grelha.preco_produto }}).</p>

      <p v-if="erro" class="text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2">{{ erro }}</p>

      <!-- Acções -->
      <div class="flex items-center gap-2 flex-wrap">
        <span v-if="sujo" class="text-[11px] text-amber-400 flex items-center gap-1.5 mr-auto">
          <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Alterações por guardar
        </span>
        <button v-if="grelha.stock_por_variante" type="button" @click="desactivar" :disabled="saving"
          class="px-3 py-2 rounded-xl text-xs text-zinc-500 hover:text-zinc-300 transition"
          :class="!sujo && 'mr-auto'">
          Voltar ao stock total
        </button>
        <button type="button" @click="guardar" :disabled="saving || !valido || (!sujo && grelha.stock_por_variante)"
          :class="['px-4 py-2 rounded-xl text-xs font-bold transition ml-auto',
                   saving || !valido || (!sujo && grelha.stock_por_variante)
                     ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
          {{ saving ? 'A guardar…' : grelha.stock_por_variante ? 'Guardar stock' : 'Activar stock por variação' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'

export default {
  name: 'VariantesStockEditor',

  props: {
    lojaId:    { type: [String, Number], required: true },
    produtoId: { type: [String, Number], required: true },
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
    total () { return this.linhas.reduce((s, l) => s + (Number(l.quantidade) || 0), 0) },
    valido () { return this.linhas.every(l => this.qtdValida(l.quantidade)) },
    sujo () { return JSON.stringify(this.payload()) !== this.original },
  },

  watch: {
    produtoId () { this.carregar() },
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
        const { data } = await api.get(`/app/loja/${this.lojaId}/produtos/${this.produtoId}/variantes/`)
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
        const { data } = await api.put(`/app/loja/${this.lojaId}/produtos/${this.produtoId}/variantes/`,
          { variantes: this.payload() })
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
        const { data } = await api.put(`/app/loja/${this.lojaId}/produtos/${this.produtoId}/variantes/`,
          { stock_por_variante: false })
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
