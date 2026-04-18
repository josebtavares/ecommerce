<template>
  <!-- Cart Toggle Button -->
  <!-- Alinhado com UserProfile: top-2 md:top-6, à esquerda do sino+user (~5.5rem) -->
  <div class="fixed top-2 md:top-[1.35rem] right-[6rem] md:right-[calc(2.5vw+5.5rem)] z-30">
    <button
      @click="toggleCart"
      class="relative p-2.5 rounded-full transition-all shadow-lg group border"
      :class="isDark
        ? 'bg-zinc-900 border-zinc-700 hover:border-red-500'
        : 'bg-white border-gray-300 hover:border-red-400 shadow-md'"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"
           :class="isDark ? 'text-zinc-300 group-hover:text-red-500' : 'text-zinc-600 group-hover:text-red-500'">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <span v-if="totalItems > 0"
        class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-600 text-white
               text-xs font-bold flex items-center justify-center animate-pulse">
        {{ totalItems }}
      </span>
    </button>
  </div>

  <!-- Backdrop -->
  <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
              leave-active-class="transition duration-150" leave-to-class="opacity-0">
    <div v-if="isOpen" class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" @click="toggleCart"></div>
  </transition>

  <!-- Cart Sidebar — dark/light -->
  <transition enter-active-class="transition duration-300" enter-from-class="translate-x-full"
              leave-active-class="transition duration-200" leave-to-class="translate-x-full">
    <div v-if="isOpen"
         class="fixed top-0 right-0 h-full w-full max-w-md z-50 flex flex-col shadow-2xl"
         :class="isDark ? 'bg-zinc-950 border-l border-zinc-800' : 'bg-white border-l border-gray-200'">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b flex-shrink-0"
           :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h2 class="text-lg font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Carrinho</h2>
          <span class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
            ({{ lojas.length }} {{ lojas.length === 1 ? 'loja' : 'lojas' }})
          </span>
        </div>
        <button @click="toggleCart"
          class="w-8 h-8 rounded-full flex items-center justify-center transition"
          :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
               :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
               fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Tabs das lojas -->
      <div v-if="lojas.length > 0" class="flex-shrink-0 border-b overflow-x-auto"
           :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
        <div class="flex min-w-max">
          <button v-for="loja in lojas" :key="loja.id"
            @click="activeLojaId = loja.id"
            :class="[
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all border-b-2 whitespace-nowrap',
              activeLojaId === loja.id
                ? 'border-red-500 text-red-500'
                : isDark
                  ? 'border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                  : 'border-transparent text-zinc-400 hover:text-zinc-700 hover:bg-gray-50'
            ]">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-5 h-5 rounded object-cover" />
            <span v-else class="w-5 h-5 rounded flex items-center justify-center text-xs font-bold"
                  :class="isDark ? 'bg-zinc-700 text-zinc-400' : 'bg-gray-200 text-zinc-500'">
              {{ loja.nome.charAt(0) }}
            </span>
            <span>{{ loja.nome }}</span>
            <span class="w-4 h-4 rounded-full bg-red-600 text-white text-[10px] font-bold flex items-center justify-center">
              {{ getLojaItemCount(loja.id) }}
            </span>
          </button>
        </div>
      </div>

      <!-- Conteúdo -->
      <div class="flex-1 overflow-y-auto">

        <!-- Carrinho vazio -->
        <div v-if="lojas.length === 0" class="flex flex-col items-center justify-center h-full text-center p-8">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4"
               :class="isDark ? 'text-zinc-700' : 'text-gray-300'"
               fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 class="text-lg font-semibold mb-1" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Carrinho vazio</h3>
          <p class="text-sm" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Adiciona produtos de qualquer loja para começar.</p>
        </div>

        <!-- Loading -->
        <div v-else-if="loadingLoja" class="flex items-center justify-center h-32">
          <svg class="animate-spin h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </div>

        <!-- Itens da loja activa -->
        <div v-else-if="activeLoja">
          <!-- Info da loja -->
          <div class="px-5 py-3 border-b flex items-center gap-3"
               :class="isDark ? 'bg-zinc-900/50 border-zinc-800/50' : 'bg-gray-50 border-gray-100'">
            <img v-if="activeLoja.logo_url" :src="activeLoja.logo_url" :alt="activeLoja.nome"
                 class="w-8 h-8 rounded-lg object-cover" />
            <div v-else class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
                 :class="isDark ? 'bg-zinc-700 text-zinc-400' : 'bg-gray-200 text-zinc-500'">
              {{ activeLoja.nome.charAt(0) }}
            </div>
            <div>
              <p class="text-sm font-semibold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ activeLoja.nome }}</p>
              <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ activeLoja.categoria }}</p>
            </div>
          </div>

          <!-- Lista de itens -->
          <div class="divide-y" :class="isDark ? 'divide-zinc-800/50' : 'divide-gray-100'">
            <div v-for="item in activeItens" :key="item.id"
                 class="flex gap-3 p-4 transition"
                 :class="isDark ? 'hover:bg-zinc-900/30' : 'hover:bg-gray-50'">

              <div class="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0"
                   :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'">
                <img v-if="item.produto?.ficheiro_url"
                     :src="item.produto.ficheiro_url" :alt="item.produto?.nome"
                     class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center"
                     :class="isDark ? 'text-zinc-600' : 'text-gray-400'">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
              </div>

              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold truncate" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ item.produto?.nome }}</p>
                <p class="text-sm font-bold text-red-500 mt-0.5">{{ formatPrice(item.produto?.preco) }}</p>

                <div v-if="item.atributos && Object.keys(item.atributos).length > 0" class="flex flex-wrap gap-1 mt-1.5">
                  <span v-for="(val, key) in item.atributos" :key="key"
                        class="px-1.5 py-0.5 text-[10px] rounded capitalize"
                        :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-gray-100 text-zinc-500'">
                    {{ key }}: <span class="font-medium" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ val }}</span>
                  </span>
                </div>

                <div class="flex items-center gap-2 mt-2">
                  <button @click="updateQty(item, -1)" :disabled="item.quantidade <= 1"
                    class="w-7 h-7 rounded-lg flex items-center justify-center transition disabled:opacity-40"
                    :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3"
                         :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M20 12H4" />
                    </svg>
                  </button>
                  <span class="text-sm font-bold w-6 text-center"
                        :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ item.quantidade }}</span>
                  <button @click="updateQty(item, 1)"
                    class="w-7 h-7 rounded-lg flex items-center justify-center transition"
                    :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3"
                         :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>
              </div>

              <div class="flex flex-col items-end justify-between flex-shrink-0">
                <button @click="removeItem(item)"
                  class="w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
                <p class="text-sm font-bold" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
                  {{ formatPrice(parseFloat(item.produto?.preco || 0) * item.quantidade) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div v-if="activeLoja && activeItens.length > 0"
           class="border-t p-5 flex-shrink-0"
           :class="isDark ? 'border-zinc-800 bg-zinc-950' : 'border-gray-200 bg-white'">
        <div class="space-y-2 mb-4">
          <div class="flex justify-between text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
            <span>Subtotal ({{ getLojaItemCount(activeLojaId) }} itens)</span>
            <span>{{ formatPrice(activeSubtotal) }}</span>
          </div>
          <div v-if="activeLoja.entrega_ativa" class="flex justify-between text-sm">
            <span :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Entrega</span>
            <span class="text-green-500">A calcular</span>
          </div>
          <div class="flex justify-between text-base font-bold pt-2 border-t"
               :class="[isDark ? 'border-zinc-800' : 'border-gray-200', isDark ? 'text-zinc-100' : 'text-zinc-900']">
            <span>Total</span>
            <span class="text-red-500">{{ formatPrice(activeSubtotal) }}</span>
          </div>
        </div>

        <button @click="goToCheckout"
          class="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold
                 transition-all hover:-translate-y-0.5 shadow-lg shadow-red-600/20 flex items-center justify-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
          Finalizar Compra
        </button>

        <button @click="clearLoja"
          class="w-full mt-2 py-2 text-xs transition"
          :class="isDark ? 'text-zinc-600 hover:text-red-500' : 'text-zinc-400 hover:text-red-500'">
          Limpar carrinho desta loja
        </button>
      </div>

    </div>
  </transition>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'multiCart',

  props: {
    isDark: { type: Boolean, default: true },  // default true = comportamento original
  },

  data () {
    return {
      isOpen: false,
      lojas: [],
      carrinhos: {},
      activeLojaId: null,
      loadingLoja: false,
    }
  },

  async mounted () {
    const user = localStorage.getItem('user')
    if (user) await this.restoreCarrinhos()
    window.addEventListener('carrinho-limpo', (e) => {
      this.limparLojaAposCheckout(e.detail.lojaId)
    })
  },

  beforeUnmount () {
    window.removeEventListener('carrinho-limpo', () => {})
  },

  computed: {
    totalItems () {
      return Object.values(this.carrinhos).reduce((total, c) => {
        return total + (c.itens || []).reduce((s, i) => s + i.quantidade, 0)
      }, 0)
    },
    activeLoja ()    { return this.lojas.find(l => l.id === this.activeLojaId) || null },
    activeItens ()   { return this.carrinhos[this.activeLojaId]?.itens || [] },
    activeSubtotal () {
      return this.activeItens.reduce((s, i) => s + (parseFloat(i.produto?.preco || 0) * i.quantidade), 0)
    },
  },

  watch: {
    '$route' (to) {
      const rotasCheckout = ['EncomendaSucesso', 'Checkout']
      if (!rotasCheckout.includes(to.name)) {
        const user = localStorage.getItem('user')
        if (user) this.restoreCarrinhos()
      }
    }
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },
    getLojaItemCount (lojaId) {
      return (this.carrinhos[lojaId]?.itens || []).reduce((s, i) => s + i.quantidade, 0)
    },
    toggleCart () { this.isOpen = !this.isOpen },

    async openForLoja (loja) {
      if (!this.lojas.find(l => l.id === loja.id)) this.lojas.push(loja)
      this.activeLojaId = loja.id
      this.isOpen = true
      await this.fetchCarrinho(loja.id)
    },

    async fetchCarrinho (lojaId) {
      this.loadingLoja = true
      try {
        const { data } = await api.get(`/app/loja/${lojaId}/carrinho/`)
        this.carrinhos = { ...this.carrinhos, [lojaId]: { carrinho_id: data.id, itens: data.itens || [] } }
      } catch (e) {
        this.carrinhos = { ...this.carrinhos, [lojaId]: { carrinho_id: null, itens: [] } }
      } finally { this.loadingLoja = false }
    },

    async updateQty (item, delta) {
      const novaQty = item.quantidade + delta
      if (novaQty < 1) return
      const lojaId  = this.activeLojaId
      const itemRef = this.carrinhos[lojaId]?.itens.find(i => i.id === item.id)
      if (itemRef) itemRef.quantidade = novaQty
      try {
        await api.patch(`/app/loja/${lojaId}/carrinho/item/${item.id}/`, { quantidade: novaQty })
      } catch (e) {
        if (itemRef) itemRef.quantidade = novaQty - delta
        console.error(e)
      }
    },

    async removeItem (item) {
      const lojaId = this.activeLojaId
      try {
        await api.patch(`/app/loja/${lojaId}/carrinho/item/${item.id}/`, { quantidade: 0 })
        this.carrinhos[lojaId].itens = this.carrinhos[lojaId].itens.filter(i => i.id !== item.id)
        if (this.carrinhos[lojaId].itens.length === 0) {
          this.lojas = this.lojas.filter(l => l.id !== lojaId)
          this.activeLojaId = this.lojas[0]?.id || null
        }
      } catch (e) { console.error(e) }
    },

    async clearLoja () {
      const lojaId = this.activeLojaId
      try {
        await api.delete(`/app/loja/${lojaId}/carrinho/limpar/`)
        this.carrinhos[lojaId].itens = []
        this.lojas = this.lojas.filter(l => l.id !== lojaId)
        this.activeLojaId = this.lojas[0]?.id || null
      } catch (e) { console.error(e) }
    },

    goToCheckout () {
      this.$router.push(`/checkout/${this.activeLojaId}`)
      this.isOpen = false
    },

    async restoreCarrinhos () {
      try {
        const { data } = await api.get('/app/carrinho/')
        for (const carrinho of data) {
          if (!this.lojas.find(l => l.id === carrinho.loja.id)) this.lojas.push(carrinho.loja)
          this.carrinhos = {
            ...this.carrinhos,
            [carrinho.loja.id]: { carrinho_id: carrinho.id, itens: carrinho.itens || [] }
          }
        }
        if (this.lojas.length > 0) this.activeLojaId = this.lojas[0].id
      } catch (e) { console.error('Erro ao restaurar carrinhos', e) }
    },

    limparLojaAposCheckout (lojaId) {
      const id = parseInt(lojaId)
      if (this.carrinhos[id]) this.carrinhos[id].itens = []
      this.lojas = this.lojas.filter(l => l.id !== id)
      this.activeLojaId = this.lojas[0]?.id || null
    },
  }
}
</script>