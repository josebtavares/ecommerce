<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100">

    <!-- Profile + Cart + ProductPopup -->
    <Profile :data="user" class="z-10" @log_out="log_out()" />
    <ProductInfoCard
      :produto="selectedProduct"
      :loja="selectedLoja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)"
    />
    <MultiCart ref="cart" />

    <div class="flex overflow-x-hidden">

      <!-- ═══ SIDEBAR ═══ -->
      <aside class="fixed left-0 top-0 h-[100vh] w-64 bg-zinc-900 border-r border-zinc-800 overflow-y-auto hidden lg:block z-10">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-zinc-100 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            Categorias
          </h2>

          <!-- Skeleton -->
          <div v-if="loadingCategorias" class="space-y-2">
            <div v-for="n in 5" :key="n" class="h-10 bg-zinc-800 rounded-lg animate-pulse"></div>
          </div>

          <ul v-else class="space-y-1">
            <!-- Categorias dinâmicas -->
            <li
              v-for="cat in categoriasExistentes" :key="cat.value"
              @click="selectCategoria(cat)"
              :class="[
                'px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-3',
                selectedCategoria === cat.value
                  ? 'bg-red-600 text-white'
                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
              ]"
            >
              <span class="w-2 h-2 rounded-full flex-shrink-0"
                    :class="selectedCategoria === cat.value ? 'bg-white' : 'bg-zinc-600'"></span>
              {{ cat.label }}
            </li>

            <!-- Ver Todas -->
            <li
              @click="clearCategoria"
              :class="[
                'px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-3 mt-4 border border-dashed',
                !selectedCategoria
                  ? 'border-red-500 text-red-500'
                  : 'border-zinc-700 text-zinc-500 hover:border-zinc-600 hover:text-zinc-400'
              ]"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              Ver Todas
            </li>

            <!-- Produtos + Explorar -->
            <li @click="scrollToSection('produtos')"
              class="px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-3 mt-4 border-t border-zinc-800 pt-5
                     text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
              <span class="w-2 h-2 rounded-full bg-zinc-600 flex-shrink-0"></span>
              Produtos
            </li>
            <li @click="scrollToSection('catalogo')"
              class="px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-3
                     text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
              <span class="w-2 h-2 rounded-full bg-zinc-600 flex-shrink-0"></span>
              Explorar Lojas
            </li>
          </ul>
        </div>

        <!-- Lojas da categoria seleccionada -->
        <div v-if="selectedCategoria && storesByCategory.length > 0" class="p-6 border-t border-zinc-800">
          <h3 class="text-sm font-medium text-zinc-400 mb-3 uppercase tracking-wider">
            Lojas em {{ selectedCategoriaLabel }}
          </h3>
          <ul class="space-y-2">
            <li
              v-for="store in storesByCategory" :key="store.id"
              @click="goToStore(store.id)"
              class="flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-800 cursor-pointer transition-colors"
            >
              <img v-if="store.logo_url" :src="store.logo_url" :alt="store.nome"
                   class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
              <div v-else class="w-10 h-10 rounded-lg bg-zinc-700 flex items-center justify-center flex-shrink-0">
                <span class="text-sm font-bold text-zinc-400">{{ store.nome.charAt(0) }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-zinc-200 truncate">{{ store.nome }}</p>
                <p class="text-xs text-zinc-500 truncate">{{ store.localizacao }}</p>
              </div>
            </li>
          </ul>
        </div>
      </aside>

      <!-- ═══ MAIN ═══ -->
      <main class="flex-1 lg:ml-64 overflow-x-hidden">

        <!-- ── HERO ── -->
        <section class="relative overflow-hidden">
          <swiper
            ref="heroSwiper"
            :pagination="heroPagination"
            :modules="modules"
            :autoplay="{ delay: 3000, disableOnInteraction: false }"
            :speed="800"
            :effect="'fade'"
            class="h-[70vh]"
            @mouseenter="stopHeroAutoplay"
            @mouseleave="startHeroAutoplay"
          >
            <swiper-slide v-for="store in newStores" :key="store.id"
              @click="goToStore(store.id)" class="cursor-pointer">
              <div class="relative h-full w-full">
                <img :src="store.banner_url || '/placeholder-banner.jpg'" :alt="store.nome"
                     class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-transparent"></div>
                <div class="absolute inset-0 bg-gradient-to-r from-zinc-950/80 to-transparent"></div>
                <div class="absolute bottom-0 left-0 p-8 md:p-12 max-w-2xl">
                  <span class="inline-block px-3 py-1 bg-red-600 text-white text-xs font-semibold rounded-full mb-4 uppercase tracking-wider">
                    Nova Loja
                  </span>
                  <h1 class="text-4xl md:text-6xl font-bold text-white mb-3">{{ store.nome }}</h1>
                  <p class="text-lg text-zinc-300 mb-4 line-clamp-2">{{ store.descricao }}</p>
                  <div class="flex items-center gap-4 text-zinc-400 text-sm flex-wrap">
                    <span v-if="store.localizacao" class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      </svg>
                      {{ store.localizacao }}
                    </span>
                    <span class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      {{ store.categoria }}
                    </span>
                    <span v-if="store.rating_medio" class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                      {{ store.rating_medio }}
                    </span>
                  </div>
                  <button class="mt-6 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition flex items-center gap-2">
                    Visitar Loja
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </button>
                </div>
              </div>
            </swiper-slide>
          </swiper>
        </section>

        <!-- ── SLIDERS DE LOJAS POR CATEGORIA (dinâmico) ── -->
        <div v-if="loadingCategorias" class="py-10 px-6 md:px-12 space-y-10">
          <div v-for="n in 3" :key="n">
            <div class="h-5 w-40 bg-zinc-800 rounded animate-pulse mb-4"></div>
            <div class="flex gap-4">
              <div v-for="m in 4" :key="m" class="w-64 h-48 bg-zinc-800 rounded-2xl animate-pulse flex-shrink-0"></div>
            </div>
          </div>
        </div>

        <template v-else>
          <section
            v-for="(cat, index) in categoriasExistentes" :key="cat.value"
            :ref="el => { if (el) sectionRefs[cat.value] = el }"
            class="py-8 px-6 md:px-12"
            :class="{ 'bg-zinc-900/40': index % 2 !== 0 }"
          >
            <StoreSlider
              :title="cat.label" :icon="cat.icon"
              :params="{ categoria: cat.value }"
              @store-click="goToStore($event.id)"
            />
          </section>
        </template>

        <!-- ── PRODUTOS ── -->
        <section :ref="el => { if (el) sectionRefs['produtos'] = el }"
                 class="py-10 px-6 md:px-12 border-t bg-zinc-900/50 border-zinc-800">
          <div class="mb-2">
            <h2 class="text-2xl md:text-3xl font-bold text-white">Produtos</h2>
            <p class="text-zinc-400 mt-1">Descobre produtos de todas as lojas</p>
          </div>

          <ProductSlider title="Em Destaque" icon="⭐"
            :params="{ destaque: true }"
            @product-click="openProduct($event)" />

          <ProductSlider
            v-for="tipo in tiposExistentes" :key="tipo.id"
            :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
            :params="{ tipo: tipo.nome }"
            @product-click="openProduct($event)"
          />
        </section>

        <!-- ── CATÁLOGO COMPLETO ── -->
        <section :ref="el => { if (el) sectionRefs['catalogo'] = el }"
                 class="py-12 px-6 md:px-12 border-t border-zinc-800 bg-zinc-900/20">
          <div class="mb-8">
            <h2 class="text-2xl md:text-3xl font-bold text-white">Explorar Lojas</h2>
            <p class="text-zinc-400 mt-1">Pesquisa e filtra todas as lojas da plataforma</p>
          </div>
          <StoreCatalog @store-click="goToStore($event.id)" />
        </section>

        <!-- ── FOOTER ── -->
        <footer class="bg-zinc-900 border-t border-zinc-800 py-12 px-6 md:px-12">
          <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 class="text-xl font-bold text-white mb-4">Marketplace</h3>
              <p class="text-zinc-400 text-sm">A melhor plataforma para descobrir lojas e produtos incríveis.</p>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Explorar</h4>
              <ul class="space-y-2 text-zinc-400 text-sm">
                <li @click="scrollToSection('catalogo')" class="hover:text-white cursor-pointer transition">Todas as Lojas</li>
                <li @click="scrollToSection('produtos')" class="hover:text-white cursor-pointer transition">Produtos</li>
              </ul>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Suporte</h4>
              <ul class="space-y-2 text-zinc-400 text-sm">
                <li class="hover:text-white cursor-pointer transition">Ajuda</li>
                <li class="hover:text-white cursor-pointer transition">Contacto</li>
                <li class="hover:text-white cursor-pointer transition">FAQ</li>
              </ul>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Legal</h4>
              <ul class="space-y-2 text-zinc-400 text-sm">
                <li class="hover:text-white cursor-pointer transition">Termos de Serviço</li>
                <li class="hover:text-white cursor-pointer transition">Privacidade</li>
              </ul>
            </div>
          </div>
          <div class="max-w-7xl mx-auto mt-8 pt-8 border-t border-zinc-800 text-center text-zinc-500 text-sm">
            <p>&copy; {{ new Date().getFullYear() }} Marketplace. Todos os direitos reservados.</p>
          </div>
        </footer>
      </main>
    </div>

    <!-- Mobile FAB -->
    <button @click="showMobileCategories = true"
      class="fixed bottom-6 right-6 z-40 lg:hidden p-4 bg-red-600 hover:bg-red-700 text-white rounded-full shadow-lg transition">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>

    <!-- Mobile Drawer -->
    <div v-if="showMobileCategories" class="fixed inset-0 z-50 lg:hidden" @click="showMobileCategories = false">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
      <div class="absolute left-0 top-0 h-full w-72 bg-zinc-900 p-6 overflow-y-auto" @click.stop>
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-white">Categorias</h2>
          <button @click="showMobileCategories = false" class="p-2 hover:bg-zinc-800 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <ul class="space-y-1">
          <li v-for="cat in categoriasExistentes" :key="cat.value"
            @click="selectCategoria(cat); showMobileCategories = false"
            :class="[
              'px-4 py-3 rounded-lg cursor-pointer transition-all flex items-center gap-3',
              selectedCategoria === cat.value
                ? 'bg-red-600 text-white'
                : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
            ]">
            <span class="w-2 h-2 rounded-full flex-shrink-0"
                  :class="selectedCategoria === cat.value ? 'bg-white' : 'bg-zinc-600'"></span>
            {{ cat.label }}
          </li>
          <li @click="clearCategoria; showMobileCategories = false"
            :class="[
              'px-4 py-3 rounded-lg cursor-pointer transition-all flex items-center gap-3 mt-4 border border-dashed',
              !selectedCategoria ? 'border-red-500 text-red-500' : 'border-zinc-700 text-zinc-500'
            ]">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            Ver Todas
          </li>
          <li @click="scrollToSection('produtos'); showMobileCategories = false"
            class="px-4 py-3 rounded-lg cursor-pointer transition-all flex items-center gap-3 mt-4 border-t border-zinc-800 pt-5
                   text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
            <span class="w-2 h-2 rounded-full bg-zinc-600 flex-shrink-0"></span>
            Produtos
          </li>
          <li @click="scrollToSection('catalogo'); showMobileCategories = false"
            class="px-4 py-3 rounded-lg cursor-pointer transition-all flex items-center gap-3
                   text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
            <span class="w-2 h-2 rounded-full bg-zinc-600 flex-shrink-0"></span>
            Explorar Lojas
          </li>
        </ul>
      </div>
    </div>

  </div>
</template>

<script>
import { Navigation, Pagination, Autoplay, EffectFade } from 'swiper/modules'
import { Swiper, SwiperSlide } from 'swiper/vue'
import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/effect-fade'

import Profile         from '@/components/profile/UserProfile.vue'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart       from '@/components/cart/multiCart.vue'
import StoreSlider     from '@/components/sliders/StoreSlider.vue'
import ProductSlider   from '@/components/sliders/ProductSlider.vue'
import StoreCatalog    from '@/components/catalog/StoreCatalog.vue'
import api from '@/services/api'

const CATEGORIAS_MAP = {
  restaurante:  { label: 'Restaurantes',  icon: '🍔' },
  moda:         { label: 'Moda',          icon: '👗' },
  tecnologia:   { label: 'Tecnologia',    icon: '📱' },
  supermercado: { label: 'Supermercado',  icon: '🛒' },
  farmacia:     { label: 'Farmácia',      icon: '💊' },
  desporto:     { label: 'Desporto',      icon: '⚽' },
  beleza:       { label: 'Beleza',        icon: '💄' },
  livraria:     { label: 'Livraria',      icon: '📚' },
  casa:         { label: 'Casa e Jardim', icon: '🏠' },
  outros:       { label: 'Outros',        icon: '🏪' },
}

const TIPO_ICONS = {
  prato: '🍽️', comida: '🍔', bebida: '🥤', sobremesa: '🍰',
  roupa: '👗', calcado: '👟', acessorio: '👜',
  eletronico: '📱', computador: '💻',
  fruta: '🍎', legume: '🥦', carne: '🥩', alimento: '🛒',
  livro: '📚', medicamento: '💊',
}

export default {
  name: 'AppHome',
  components: { Swiper, SwiperSlide, Profile, ProductInfoCard, MultiCart, StoreSlider, ProductSlider, StoreCatalog },

  data () {
    return {
      newStores: [],
      categoriasExistentes: [],
      tiposExistentes: [],
      loadingCategorias: true,
      selectedProduct: null,
      selectedLoja: null,
      selectedCategoria: null,       // value da categoria seleccionada na sidebar
      storesByCategory: [],
      showMobileCategories: false,
      user: {},
      sectionRefs: {},
    }
  },

  computed: {
    selectedCategoriaLabel () {
      return this.categoriasExistentes.find(c => c.value === this.selectedCategoria)?.label || ''
    },
  },

  async created () {
    const user = localStorage.getItem('user')
    this.user = user ? JSON.parse(user) : {}
    await Promise.all([
      this.fetchNewStores(),
      this.fetchCategoriasExistentes(),
      this.fetchTiposExistentes(),
    ])
  },

  methods: {
    goToStore (id) { this.$router.push(`/loja/${id}`) },

    openProduct (produto) {
      this.selectedProduct = produto
      this.selectedLoja = produto.loja
    },

    tipoIcon (nome) {
      return TIPO_ICONS[nome?.toLowerCase()] || '📦'
    },

    scrollToSection (key) {
      const el = this.sectionRefs[key]
      if (el) el.scrollIntoView({ behavior: 'smooth' })
    },

    async selectCategoria (cat) {
      this.selectedCategoria = cat.value
      await this.fetchStoresByCategory(cat.value)
      this.scrollToSection(cat.value)
    },

    clearCategoria () {
      this.selectedCategoria = null
      this.storesByCategory = []
    },

    async fetchStoresByCategory (categoria) {
      try {
        const { data } = await api.get(`/app/loja/?categoria=${encodeURIComponent(categoria)}&limit=10`)
        this.storesByCategory = data.results || data
      } catch (e) { console.error(e) }
    },

    stopHeroAutoplay () { this.$refs.heroSwiper?.swiper?.autoplay.stop() },
    startHeroAutoplay () { this.$refs.heroSwiper?.swiper?.autoplay.start() },

    async fetchNewStores () {
      try {
        const { data } = await api.get('/app/loja/?offset=0&limit=5')
        this.newStores = data.results || data
      } catch (e) { console.error(e) }
    },

    async fetchCategoriasExistentes () {
      try {
        const { data } = await api.get('/app/loja/?limit=100')
        const lojas = data.results || data
        const unicas = [...new Set(lojas.map(l => l.categoria?.toLowerCase()).filter(Boolean))]
        this.categoriasExistentes = unicas.map(val => ({
          value: val,
          label: CATEGORIAS_MAP[val]?.label || (val.charAt(0).toUpperCase() + val.slice(1)),
          icon:  CATEGORIAS_MAP[val]?.icon  || '🏪',
        }))
      } catch (e) { console.error(e) }
      finally { this.loadingCategorias = false }
    },

    async fetchTiposExistentes () {
      try {
        const { data } = await api.get('/app/produto/tipos/')
        this.tiposExistentes = data
      } catch (e) { console.error(e) }
    },

    log_out () {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      this.user = {}
      this.$router.push('/login')
    },
  },

  setup () {
    return {
      heroPagination: {
        clickable: true,
        renderBullet: (index, className) => `<span class="${className}"></span>`,
      },
      modules: [Navigation, Pagination, Autoplay, EffectFade],
    }
  },
}
</script>

<style scoped>
.swiper {
  --swiper-pagination-bullet-inactive-color: rgba(255,255,255,0.4);
  --swiper-pagination-color: #dc2626;
  --swiper-pagination-bullet-size: 10px;
  --swiper-pagination-bullet-horizontal-gap: 6px;
}
.swiper-pagination { bottom: 30px !important; }
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>