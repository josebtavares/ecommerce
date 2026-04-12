<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100">

    <ProductInfoCard
      :produto="selectedProduct"
      :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)"
    />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="log_out()"/>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <svg class="animate-spin h-10 w-10 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO ── -->
      <section class="relative h-[55vh] min-h-[360px] overflow-hidden">
        <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
             :alt="loja.nome" class="w-full h-full object-cover" />
        <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/50 to-transparent"></div>
        <div class="absolute inset-0 bg-gradient-to-r from-zinc-950/60 to-transparent"></div>

        <button @click="$router.back()"
          class="absolute top-5 left-5 w-9 h-9 rounded-full bg-black/50 hover:bg-black/70
                 flex items-center justify-center transition backdrop-blur-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div class="absolute bottom-0 left-0 p-8 flex items-end gap-5">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-20 h-20 rounded-2xl object-cover border-2 border-zinc-700 shadow-xl flex-shrink-0" />
          <div v-else class="w-20 h-20 rounded-2xl bg-zinc-800 flex items-center justify-center flex-shrink-0 border-2 border-zinc-700">
            <span class="text-3xl font-bold text-zinc-400">{{ loja.nome.charAt(0) }}</span>
          </div>
          <div>
            <span class="inline-block px-2 py-0.5 rounded-full bg-red-600 text-white text-[10px] font-bold uppercase tracking-wider mb-2">
              {{ loja.categoria }}
            </span>
            <h1 class="text-3xl md:text-4xl font-extrabold text-white leading-tight">{{ loja.nome }}</h1>
            <div class="flex items-center gap-4 mt-2 text-sm text-zinc-400 flex-wrap">
              <span v-if="loja.localizacao" class="flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                {{ loja.localizacao }}
              </span>
              <span v-if="loja.rating_medio" class="flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                {{ loja.rating_medio }}
                <span v-if="loja.total_avaliacoes" class="text-zinc-600">({{ loja.total_avaliacoes }})</span>
              </span>
              <span v-if="loja.entrega_ativa" class="flex items-center gap-1 text-green-400">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Entrega disponível
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- ── LAYOUT COM SIDEBAR ── -->
      <div class="flex">

        <!-- SIDEBAR -->
        <transition enter-active-class="transition duration-300" enter-from-class="-translate-x-full"
                    leave-active-class="transition duration-200" leave-to-class="-translate-x-full">
          <aside v-if="sidebarAberta"
                 class="fixed left-0 top-0 h-screen w-64 bg-zinc-900 border-r border-zinc-800
                        overflow-y-auto z-30 pt-6">
            <div class="flex items-center justify-between px-5 mb-5">
              <h3 class="text-sm font-bold text-zinc-300">Navegar</h3>
              <button @click="sidebarAberta = false"
                class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div v-if="tiposExistentes.length > 0" class="px-3 mb-5">
              <p class="text-[10px] font-bold text-zinc-600 uppercase tracking-wider px-2 mb-2">Tipos</p>
              <button v-for="tipo in tiposExistentes" :key="tipo.id"
                @click="scrollToId('tipo-' + tipo.id); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400
                       hover:bg-zinc-800 hover:text-zinc-100 transition text-left">
                <span>{{ tipoIcon(tipo.nome) }}</span>
                <span class="capitalize">{{ tipo.nome }}</span>
              </button>
            </div>
            <div v-if="categoriasExistentes.length > 0" class="px-3 mb-5 border-t border-zinc-800 pt-4">
              <p class="text-[10px] font-bold text-zinc-600 uppercase tracking-wider px-2 mb-2">Categorias</p>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400
                       hover:bg-zinc-800 hover:text-zinc-100 transition text-left">
                <span>{{ cat.icone }}</span>
                <span class="capitalize">{{ cat.nome }}</span>
              </button>
            </div>
            <div class="px-3 border-t border-zinc-800 pt-4">
              <button @click="scrollToId('catalogo'); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400
                       hover:bg-zinc-800 hover:text-zinc-100 transition text-left">
                🔍 Catálogo completo
              </button>
              <button @click="scrollToId('avaliacoes'); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400
                       hover:bg-zinc-800 hover:text-zinc-100 transition text-left">
                ⭐ Avaliações
              </button>
            </div>
          </aside>
        </transition>

        <div v-if="sidebarAberta" class="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm" @click="sidebarAberta = false" />

        <button v-if="temSidebar"
          @click="sidebarAberta = !sidebarAberta"
          class="fixed bottom-6 left-6 z-30 w-12 h-12 bg-zinc-900 border border-zinc-700
                 hover:bg-zinc-800 rounded-xl flex items-center justify-center shadow-lg transition">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- MAIN -->
        <main class="flex-1 min-w-0">
          <div class="max-w-6xl mx-auto px-6 py-8">

            <!-- Info + Entrega -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
              <div class="md:col-span-2 bg-zinc-900 rounded-2xl p-5 border border-zinc-800">
                <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">Sobre a loja</h2>
                <p class="text-zinc-300 text-sm leading-relaxed">{{ loja.descricao || 'Sem descrição disponível.' }}</p>
                <div v-if="metodosPagamento.length > 0" class="mt-4 pt-4 border-t border-zinc-800">
                  <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Pagamento aceite</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="m in metodosPagamento" :key="m.id"
                          class="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-800 rounded-lg text-xs text-zinc-300">
                      <span>{{ metodoPagamentoIcon(m.tipo) }}</span>
                      <span class="capitalize">{{ m.tipo }}</span>
                    </span>
                  </div>
                </div>
              </div>
              <div class="bg-zinc-900 rounded-2xl p-5 border border-zinc-800">
                <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">Entrega</h2>
                <div v-if="opcoesEntrega.length === 0" class="text-zinc-500 text-sm">Sem opções configuradas.</div>
                <div v-else class="space-y-2">
                  <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                       class="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
                    <div>
                      <p class="text-sm font-medium text-zinc-200">{{ opcao.nome }}</p>
                      <p v-if="opcao.tempo_estimado" class="text-xs text-zinc-500">{{ opcao.tempo_estimado }}</p>
                    </div>
                    <span class="text-sm font-bold text-red-400">{{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}</span>
                  </div>
                </div>
                <div v-if="loja.levantamento_ativo" class="mt-3 flex items-center gap-2 text-xs text-blue-400">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  Levantamento disponível
                </div>
              </div>
            </div>

            <!-- Em Destaque -->
            <ProductSlider title="Em Destaque" icon="⭐"
              :params="{ loja_id: $route.params.id, destaque: true }"
              @product-click="selectedProduct = $event" />

            <!-- Sliders por TIPO -->
            <template v-if="tiposExistentes.length > 0">
              <div class="flex items-center gap-3 my-6">
                <div class="h-px flex-1 bg-zinc-800"></div>
                <span class="text-xs font-bold text-zinc-500 uppercase tracking-widest">Por tipo</span>
                <div class="h-px flex-1 bg-zinc-800"></div>
              </div>
              <div v-for="tipo in tiposExistentes" :key="'tipo-' + tipo.id" :id="'tipo-' + tipo.id">
                <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
                  :params="{ loja_id: $route.params.id, tipo: tipo.nome }"
                  @product-click="selectedProduct = $event" />
              </div>
            </template>

            <!-- Sliders por CATEGORIA (M2M) -->
            <template v-if="categoriasExistentes.length > 0">
              <div class="flex items-center gap-3 my-6">
                <div class="h-px flex-1 bg-zinc-800"></div>
                <span class="text-xs font-bold text-zinc-500 uppercase tracking-widest">Por categoria</span>
                <div class="h-px flex-1 bg-zinc-800"></div>
              </div>
              <div v-for="cat in categoriasExistentes" :key="'cat-' + cat.id" :id="'cat-' + cat.id">
                <ProductSlider :title="cat.nome" :icon="cat.icone || '📂'"
                  :params="{ loja_id: $route.params.id, categoria_id: cat.id }"
                  @product-click="selectedProduct = $event" />
              </div>
            </template>

            <!-- Catálogo -->
            <div id="catalogo" class="mt-10 mb-4">
              <h2 class="text-xl font-bold text-zinc-100">Catálogo completo</h2>
              <p class="text-sm text-zinc-500 mt-1">Filtra por tipo, categoria ou pesquisa directamente</p>
            </div>
            <ProductCatalog :loja-id="$route.params.id" @product-click="selectedProduct = $event" />

            <!-- Avaliações -->
            <div id="avaliacoes" class="mt-10">
              <h2 class="text-xl font-bold text-zinc-100 mb-5">Avaliações</h2>
              <AvaliacaoLoja :loja-id="$route.params.id" @rating-updated="onRatingUpdated" />
            </div>

            <!-- Footer -->
            <footer v-if="temFooter" class="mt-16 pt-8 border-t border-zinc-800">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div>
                  <div class="flex items-center gap-3 mb-3">
                    <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-8 h-8 rounded-lg object-cover" />
                    <p class="font-bold text-zinc-200">{{ loja.nome }}</p>
                  </div>
                  <p class="text-xs text-zinc-500 leading-relaxed">{{ loja.descricao }}</p>
                  <p v-if="loja.localizacao" class="text-xs text-zinc-600 mt-2">📍 {{ loja.localizacao }}</p>
                </div>
                <div v-if="loja.politica_devolucao" class="space-y-2">
                  <button @click="modalPolitica = 'devolucao'"
                    class="text-sm font-semibold text-zinc-400 hover:text-zinc-200 transition flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-1.5 4 1.5 4-1.5 4 1.5z" /></svg>
                    Política de devoluções
                  </button>
                  <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                    class="text-sm font-semibold text-zinc-400 hover:text-zinc-200 transition flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5l5 5v11a2 2 0 01-2 2z" /></svg>
                    Termos de serviço
                  </button>
                  <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                    class="text-sm font-semibold text-zinc-400 hover:text-zinc-200 transition flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                    Política de privacidade
                  </button>
                </div>
                <div v-if="metodosPagamento.length > 0">
                  <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Pagamento</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="m in metodosPagamento" :key="m.id"
                          class="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-800 rounded-lg text-xs text-zinc-400">
                      {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="text-center text-xs text-zinc-700 pt-4 border-t border-zinc-900">
                © {{ new Date().getFullYear() }} {{ loja.nome }} — Vendido através da plataforma
              </div>
            </footer>
          </div>
        </main>
      </div>

      <!-- Modal políticas -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl">
          <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800 sticky top-0 bg-zinc-900">
            <h3 class="text-base font-bold text-zinc-100">
              {{ modalPolitica === 'devolucao' ? 'Política de devoluções' : modalPolitica === 'termos' ? 'Termos de serviço' : 'Política de privacidade' }}
            </h3>
            <button @click="modalPolitica = null" class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div class="p-6 text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <div v-else class="flex flex-col items-center justify-center h-screen text-center">
      <p class="text-2xl font-bold text-zinc-400 mb-2">Loja não encontrada</p>
      <button @click="$router.back()" class="text-red-400 hover:text-red-300 text-sm">← Voltar</button>
    </div>
  </div>
</template>

<script>
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Autoplay } from 'swiper/modules'
import 'swiper/css'
import api from '@/services/api'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'LojaPublica',
  components: { Swiper, SwiperSlide, ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },

  data () {
    return {
      swiperModules: [Autoplay],
      backendUrl: process.env.VUE_APP_URL_BASE || 'http://localhost:8000',
      loading: true,
      loja: null,
      opcoesEntrega: [],
      metodosPagamento: [],
      tiposExistentes: [],
      categoriasExistentes: [],  // agora são objectos CategoriaLoja {id, nome, icone}
      selectedProduct: null,
      user: null,
      sidebarAberta: false,
      modalPolitica: null,
    }
  },

  computed: {
    temSidebar () {
      return (this.tiposExistentes.length + this.categoriasExistentes.length) >= 3
    },
    temFooter () {
      return this.loja?.politica_devolucao || this.loja?.termos_servico ||
             this.loja?.politica_privacidade || this.metodosPagamento.length > 0
    },
  },

  async created () {
    const user = localStorage.getItem('user')
    this.user = user ? JSON.parse(user) : {}
    const id = this.$route.params.id
    await Promise.all([
      this.fetchLoja(id),
      this.fetchOpcoesEntrega(id),
      this.fetchMetodosPagamento(id),
      this.fetchTiposExistentes(id),
      this.fetchCategoriasExistentes(id),
    ])
    this.loading = false
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },
    tipoIcon (tipo) {
      const icons = { prato: '🍽️', comida: '🍔', bebida: '🥤', sobremesa: '🍰', roupa: '👗',
        calcado: '👟', acessorio: '👜', eletronico: '📱', telemovel: '📱', tablet: '💻',
        fruta: '🍎', legume: '🥦', carne: '🥩', livro: '📚', manga: '📖', revista: '📰' }
      return icons[tipo?.toLowerCase()] || '📦'
    },
    metodoPagamentoIcon (tipo) {
      const map = { cartao: '💳', dinheiro: '💵', mbway: '📱', paypal: '🅿️', stripe: '💳' }
      return map[tipo] || '💰'
    },
    scrollToId (id) {
      const el = document.getElementById(id)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },
    async fetchLoja (id) {
      try { const { data } = await api.get(`/app/loja/${id}/`); this.loja = data }
      catch (e) { console.error(e) }
    },
    async fetchOpcoesEntrega (id) {
      try { const { data } = await api.get(`/app/loja/${id}/entrega/opcoes/`); this.opcoesEntrega = data.results || data }
      catch (e) { console.error(e) }
    },
    async fetchMetodosPagamento (id) {
      try {
        const { data } = await api.get(`/app/loja/${id}/pagamento/metodos/`)
        this.metodosPagamento = (data.results || data).filter(m => m.ativo)
      } catch (e) { console.error(e) }
    },
    async fetchTiposExistentes (id) {
      try {
        const { data } = await api.get('/app/produto/', { params: { loja_id: id, limit: 200 } })
        const produtos = data.results || data
        const map = {}
        produtos.forEach(p => { if (p.tipo && !map[p.tipo.id]) map[p.tipo.id] = p.tipo })
        this.tiposExistentes = Object.values(map)
      } catch (e) { console.error(e) }
    },
    async fetchCategoriasExistentes (id) {
      try {
        // usa o novo endpoint M2M — devolve objectos {id, nome, icone, total_produtos}
        const { data } = await api.get(`/app/loja/${id}/categorias/`)
        this.categoriasExistentes = data
      } catch (e) { console.error(e) }
    },
    onRatingUpdated ({ media }) {
      if (this.loja && media !== undefined) this.loja.rating_medio = media
    },
    log_out () {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      this.$router.push({ name: 'Login' })
    },
  }
}
</script>

<style scoped>
.swiper { overflow: hidden !important; }
</style>