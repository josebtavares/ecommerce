<template>
  <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
              leave-active-class="transition duration-150" leave-to-class="opacity-0">
    <div v-if="produto" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
         @click.self="$emit('close')">

      <div class="bg-zinc-900 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto
                  border border-zinc-800 shadow-2xl">

        <!-- Imagem -->
        <div class="relative h-64 overflow-hidden rounded-t-2xl">
          <img v-if="produto.ficheiro_url" :src="produto.ficheiro_url" :alt="produto.nome"
               class="w-full h-full object-cover" />
          <div v-else class="w-full h-full bg-zinc-800 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <span v-if="produto.destaque"
                class="absolute top-3 left-3 px-2 py-1 bg-red-600 text-white text-xs font-bold rounded">
            ⭐ Destaque
          </span>
          <button @click="$emit('close')"
            class="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70
                   flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Conteúdo -->
        <div class="p-6">

          <!-- Loja info -->
          <div class="flex items-center gap-2 mb-3">
            <img v-if="loja?.logo_url" :src="loja.logo_url" :alt="loja.nome"
                 class="w-6 h-6 rounded object-cover" />
            <span class="text-xs text-zinc-500 font-medium">{{ loja?.nome }}</span>
            <span class="text-zinc-700">·</span>
            <span class="text-xs text-zinc-500">{{ produto.categoria }}</span>
          </div>

          <!-- Nome e preço -->
          <h2 class="text-2xl font-bold text-zinc-100 mb-1">{{ produto.nome }}</h2>
          <p class="text-2xl font-bold text-red-400 mb-4">{{ formatPrice(produto.preco) }}</p>

          <!-- Descrição -->
          <p class="text-sm text-zinc-400 leading-relaxed mb-4">{{ produto.descricao || 'Sem descrição.' }}</p>

          <!-- ── ATRIBUTOS ── -->

          <!-- Choices — botões de selecção -->
          <div v-if="atributosChoices.length > 0" class="space-y-4 mb-4">
            <div v-for="attr in atributosChoices" :key="attr.nome">
              <p class="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <span class="capitalize">{{ attr.nome }}</span>
                <span v-if="attr.obrigatorio" class="text-red-500">*</span>
              </p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="opcao in attr.opcoes" :key="opcao"
                  @click="toggleSeleccao(attr.nome, opcao)"
                  :class="[
                    'px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border',
                    seleccoes[attr.nome] === opcao
                      ? 'bg-red-600 border-red-500 text-white'
                      : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-zinc-100'
                  ]">
                  {{ opcao }}
                </button>
              </div>
            </div>
          </div>

          <!-- Atributos texto/número + fallback JSON -->
          <div v-if="atributosVisiveis.length > 0"
               class="grid grid-cols-2 gap-2 mb-4">
            <div v-for="(item, idx) in atributosVisiveis" :key="idx"
                 class="bg-zinc-800 rounded-lg px-3 py-2">
              <p class="text-xs text-zinc-500 capitalize">{{ item.key }}</p>
              <p class="text-sm font-medium text-zinc-200">{{ item.val }}</p>
            </div>
          </div>

          <!-- ── STOCK ── -->
          <div class="flex items-center gap-2 mb-6">
            <div :class="['w-2 h-2 rounded-full', stock > 0 ? 'bg-green-500' : 'bg-red-500']"></div>
            <span class="text-sm text-zinc-400">
              {{ stock > 0 ? `${stock} em stock` : 'Sem stock' }}
            </span>
          </div>

          <!-- Aviso atributos obrigatórios -->
          <p v-if="obrigatoriosPorPreencher.length > 0"
             class="text-xs text-yellow-500 mb-4 flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Selecciona: {{ obrigatoriosPorPreencher.join(', ') }}
          </p>

          <!-- ── QUANTIDADE ── -->
          <div class="flex items-center gap-4 mb-6">
            <span class="text-sm font-medium text-zinc-400">Quantidade:</span>
            <div class="flex items-center gap-3">
              <button @click="qty > 1 && qty--"
                :disabled="qty <= 1 || loading"
                class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition
                       disabled:opacity-40 disabled:cursor-not-allowed">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M20 12H4" />
                </svg>
              </button>
              <span class="text-lg font-bold text-zinc-100 w-8 text-center">{{ qty }}</span>
              <button @click="qty < stock && qty++"
                :disabled="qty >= stock || loading"
                class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition
                       disabled:opacity-40 disabled:cursor-not-allowed">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
            <span class="text-sm font-bold text-zinc-300 ml-auto">
              Total: {{ formatPrice(produto.preco * qty) }}
            </span>
          </div>

          <!-- ── BOTÃO ADICIONAR ── -->
          <button
            @click="addToCart"
            :disabled="stock === 0 || loading || !podeAdicionar"
            :class="[
              'w-full py-3 rounded-xl font-bold text-white transition-all flex items-center justify-center gap-2',
              stock === 0 || !podeAdicionar
                ? 'bg-zinc-700 cursor-not-allowed opacity-60'
                : loading
                  ? 'bg-red-700 cursor-not-allowed opacity-80'
                  : 'bg-red-600 hover:bg-red-500 hover:-translate-y-0.5 shadow-lg shadow-red-600/20'
            ]"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              A adicionar…
            </span>
            <span v-else-if="stock === 0">Sem stock</span>
            <span v-else class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Adicionar ao carrinho
            </span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { useAsyncAction } from '@/composables/useAsyncAction'
import api from '@/services/api'

export default {
  name: 'ProductInfoCard',

  props: {
    produto: { type: Object, default: null },
    loja:    { type: Object, default: null },
  },

  emits: ['close', 'added-to-cart'],

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      qty: 1,
      seleccoes: {},
    }
  },

  computed: {
    stock () {
      return this.produto?.inventario?.quantidade ?? this.produto?.stock?.quantidade ?? 0
    },

    // schema normalizado — lista de objectos sempre
    schema () {
      if (!this.produto?.tipo?.atributos_schema) return []
      return this.produto.tipo.atributos_schema.map(a =>
        typeof a === 'string'
          ? { nome: a, tipo: 'texto', opcoes: [], obrigatorio: false }
          : a
      )
    },

    // só os atributos do tipo choices com opções definidas
    atributosChoices () {
      return this.schema.filter(a => a.tipo === 'choices' && a.opcoes?.length > 0)
    },

    // atributos texto/numero — mostra o valor guardado no produto
    // + fallback para produtos sem tipo (JSON livre)
    atributosVisiveis () {
      const atributos = this.produto?.atributos || {}
      if (this.schema.length > 0) {
        // tem tipo — mostra só os que não são choices (choices mostram-se em cima)
        return this.schema
          .filter(a => a.tipo !== 'choices' && atributos[a.nome])
          .map(a => ({ key: a.nome, val: atributos[a.nome] }))
      }
      // sem tipo — mostra tudo como key/value
      return Object.entries(atributos).map(([key, val]) => ({ key, val }))
    },

    // choices obrigatórias ainda não seleccionadas
    obrigatoriosPorPreencher () {
      return this.atributosChoices
        .filter(a => a.obrigatorio && !this.seleccoes[a.nome])
        .map(a => a.nome)
    },

    podeAdicionar () {
      return this.obrigatoriosPorPreencher.length === 0
    },
  },

  watch: {
    produto () {
      this.qty = 1
      this.seleccoes = {}
    },
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },

    toggleSeleccao (nome, opcao) {
      if (this.seleccoes[nome] === opcao) {
        const novas = { ...this.seleccoes }
        delete novas[nome]
        this.seleccoes = novas
      } else {
        this.seleccoes = { ...this.seleccoes, [nome]: opcao }
      }
    },

    async addToCart () {
      if (!this.loja || !this.produto || this.stock === 0 || !this.podeAdicionar) return
      await this.wrap(async () => {
        await api.post(`/app/loja/${this.loja.id}/carrinho/adicionar/`, {
          produto_id: this.produto.id,
          quantidade: this.qty,
          atributos:  this.seleccoes,  // ← envia as escolhas do cliente
        })
        this.$emit('added-to-cart', { loja: this.loja })
        this.$emit('close')
      })
    },
  }
}
</script>