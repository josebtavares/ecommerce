<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-50 text-zinc-900'">

    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="log_out()" />
    <ProductInfoCard :produto="selectedProduct" :loja="selectedLoja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />

    <!-- Botão toggle dark/light — canto superior esquerdo, ao lado do hamburger -->
    <div class="fixed top-2 md:top-4 left-16 z-30 flex items-center gap-2">
      <button @click="isDark = !isDark"
        class="w-9 h-9 rounded-xl flex items-center justify-center border transition shadow-md"
        :class="isDark
          ? 'bg-zinc-900 border-zinc-700 text-yellow-400 hover:border-zinc-500'
          : 'bg-white border-stone-300 text-zinc-600 hover:border-stone-400 shadow-sm'">
        <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>
    </div>

    <div class="flex overflow-x-hidden">

      <!-- ═══ SIDEBAR TOGGLE ═══ -->
      <button @click="sidebarAberta = !sidebarAberta"
        class="fixed top-2 md:top-4 left-4 z-30 w-9 h-9 rounded-xl flex items-center justify-center border transition shadow-md"
        :class="isDark
          ? 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
          : 'bg-white border-stone-300 hover:bg-stone-100 shadow-sm'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
             :class="isDark ? 'text-zinc-300' : 'text-zinc-600'"
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- ═══ OVERLAY ═══ -->
      <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                  leave-active-class="transition duration-150" leave-to-class="opacity-0">
        <div v-if="sidebarAberta" class="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm"
             @click="sidebarAberta = false" />
      </transition>

      <!-- ═══ SIDEBAR ═══ -->
      <transition enter-active-class="transition duration-300" enter-from-class="-translate-x-full"
                  leave-active-class="transition duration-200" leave-to-class="-translate-x-full">
        <aside v-if="sidebarAberta"
               class="fixed left-0 top-0 h-screen w-64 overflow-y-auto z-30 border-r"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200 shadow-xl'">
          <div class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-base font-bold flex items-center gap-2"
                  :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                Categorias
              </h2>
              <button @click="sidebarAberta = false"
                class="w-7 h-7 rounded-lg flex items-center justify-center transition"
                :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-stone-100 hover:bg-stone-200'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                     fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div v-if="loadingCategorias" class="space-y-2">
              <div v-for="n in 5" :key="n" class="h-10 rounded-lg animate-pulse"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'"></div>
            </div>

            <ul v-else class="space-y-1">
              <li v-for="cat in categoriasExistentes" :key="cat.value"
                  @click="selectCategoria(cat)"
                  :class="['px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 text-sm',
                           selectedCategoria === cat.value
                             ? 'bg-red-600 text-white'
                             : isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-stone-100 hover:text-zinc-900']">
                <span>{{ cat.icon }}</span>
                {{ cat.label }}
              </li>

              <li @click="clearCategoria"
                  :class="['px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 mt-4 border border-dashed text-sm',
                           !selectedCategoria
                             ? 'border-red-500 text-red-500'
                             : isDark ? 'border-zinc-700 text-zinc-500 hover:border-zinc-600 hover:text-zinc-400' : 'border-stone-300 text-zinc-400 hover:border-stone-400']">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                Ver Todas
              </li>

              <div class="border-t my-3" :class="isDark ? 'border-zinc-800' : 'border-stone-200'"></div>

              <li @click="scrollToSection('produtos')"
                  class="px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 text-sm"
                  :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-stone-100 hover:text-zinc-900'">
                📦 Produtos
              </li>
              <li @click="scrollToSection('catalogo')"
                  class="px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 text-sm"
                  :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-stone-100 hover:text-zinc-900'">
                🏪 Explorar Lojas
              </li>
            </ul>
          </div>

          <!-- Lojas da categoria -->
          <div v-if="selectedCategoria && storesByCategory.length > 0"
               class="p-6 border-t"
               :class="isDark ? 'border-zinc-800' : 'border-stone-200'">
            <h3 class="text-xs font-bold uppercase tracking-wider mb-3"
                :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Lojas em {{ selectedCategoriaLabel }}
            </h3>
            <ul class="space-y-2">
              <li v-for="store in storesByCategory" :key="store.id"
                  @click="goToStore(store.id)"
                  class="flex items-center gap-3 p-2 rounded-xl cursor-pointer transition"
                  :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-stone-100'">
                <img v-if="store.logo_url" :src="store.logo_url" :alt="store.nome"
                     class="w-9 h-9 rounded-lg object-cover flex-shrink-0" />
                <div v-else class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                     :class="isDark ? 'bg-zinc-700' : 'bg-stone-200'">
                  <span class="text-xs font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ store.nome.charAt(0) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium truncate" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ store.nome }}</p>
                  <p class="text-xs truncate" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ store.localizacao }}</p>
                </div>
              </li>
            </ul>
          </div>
        </aside>
      </transition>

      <!-- ═══ MAIN ═══ -->
      <main class="flex-1 overflow-x-hidden">

        <!-- ── HERO Swiper ── -->
        <section class="relative overflow-hidden">
          <swiper ref="heroSwiper" :pagination="heroPagination" :modules="modules"
                  :autoplay="{ delay: 3500, disableOnInteraction: false }"
                  :speed="800" effect="slide" class="md:h-[90vh] h-[70vh]"
                  @mouseenter="stopHeroAutoplay" @mouseleave="startHeroAutoplay">
            <swiper-slide v-for="store in newStores" :key="store.id"
              @click="goToStore(store.id)" class="cursor-pointer">
              <div class="relative h-full w-full">
                <img :src="store.banner_url || '/placeholder-banner.jpg'" :alt="store.nome"
                     class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-transparent"></div>
                <div class="absolute inset-0 bg-gradient-to-r from-zinc-950/80 to-transparent"></div>
                <div class="absolute bottom-0 left-0 p-8 md:p-12 max-w-2xl">
                  <span class="inline-block px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-full mb-4 uppercase tracking-wider">
                    Nova Loja
                  </span>
                  <h1 class="text-4xl md:text-6xl font-bold text-white mb-3 leading-tight">{{ store.nome }}</h1>
                  <p class="text-base text-zinc-300 mb-4 line-clamp-2">{{ store.descricao }}</p>
                  <div class="flex items-center gap-4 text-zinc-400 text-sm flex-wrap mb-5">
                    <span v-if="store.localizacao">📍 {{ store.localizacao }}</span>
                    <span>🏷 {{ store.categoria }}</span>
                    <span v-if="store.rating_medio" class="flex items-center gap-1">
                      <svg class="h-4 w-4 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                      {{ store.rating_medio }}
                    </span>
                  </div>
                  <button class="px-6 py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl transition flex items-center gap-2">
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

        <!-- ── SLIDERS POR CATEGORIA ── -->
        <div v-if="loadingCategorias" class="py-10 px-6 md:px-12 space-y-10">
          <div v-for="n in 3" :key="n">
            <div class="h-5 w-40 rounded animate-pulse mb-4"
                 :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
            <div class="flex gap-4">
              <div v-for="m in 4" :key="m" class="w-64 h-48 rounded-2xl animate-pulse flex-shrink-0"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
            </div>
          </div>
        </div>

        <template v-else>
          <section v-for="(cat, index) in categoriasExistentes" :key="cat.value"
                   :ref="el => { if (el) sectionRefs[cat.value] = el }"
                   class="py-8 px-6 md:px-12"
                   :class="index % 2 !== 0 ? (isDark ? 'bg-zinc-900/40' : 'bg-stone-100/60') : ''">
            <StoreSlider :title="cat.label" :icon="cat.icon"
              :params="{ categoria: cat.value }" :isDark="isDark"
              @store-click="goToStore($event.id)" />
          </section>
        </template>

        <!-- ── PRODUTOS ── -->
        <section :ref="el => { if (el) sectionRefs['produtos'] = el }"
                 class="py-10 px-6 md:px-12 border-t"
                 :class="isDark ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-stone-200'">
          <div class="mb-4">
            <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Produtos</h2>
            <p class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Descobre produtos de todas as lojas</p>
          </div>

          <ProductSlider title="Em Destaque" icon="⭐"
            :params="{ destaque: true }" :isDark="isDark"
            @product-click="openProduct($event)" />

          <ProductSlider v-for="tipo in tiposExistentes" :key="tipo.id"
            :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
            :params="{ tipo: tipo.nome }" :isDark="isDark"
            @product-click="openProduct($event)" />
        </section>

        <!-- ── POR CATEGORIA PLATAFORMA ── -->
        <template v-if="categoriasPlataforma.length > 0">
          <section class="py-4 px-6 md:px-12">
            <div class="flex items-center gap-3 mb-2">
              <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
              <span class="text-xs font-bold uppercase tracking-widest"
                    :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Por categoria</span>
              <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
            </div>
          </section>
          <section v-for="cat in categoriasPlataforma" :key="'cat-' + cat.categoria_id"
                   class="py-4 px-6 md:px-12">
            <ProductSlider :title="cat.nome" :icon="cat.icone || '📂'"
              :params="{ categoria_id: cat.categoria_id }" :isDark="isDark"
              @product-click="openProduct($event)" />
          </section>
        </template>

        <!-- ── CATÁLOGO COMPLETO ── -->
        <section :ref="el => { if (el) sectionRefs['catalogo'] = el }"
                 class="py-12 px-6 md:px-12 border-t"
                 :class="isDark ? 'border-zinc-800 bg-zinc-900/20' : 'border-stone-200 bg-stone-50'">
          <div class="mb-8">
            <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Explorar Lojas</h2>
            <p class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Pesquisa e filtra todas as lojas da plataforma</p>
          </div>
          <StoreCatalog :isDark="isDark" @store-click="goToStore($event.id)" />
        </section>

        <!-- ── FOOTER ── -->
        <footer class="border-t py-12 px-6 md:px-12"
                :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
          <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <!-- logo here -->
              <img :src="isDark ? logoLight : logoDefault" alt="Logo" class="w-32 h-32 object-contain mb-3" />
              <!-- <h3 class="text-lg font-bold mb-3" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Bendi</h3> -->
              <p class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">A melhor plataforma para descobrir lojas e produtos incríveis.</p>
            </div>
            <div>
              <h4 class="text-xs font-semibold uppercase tracking-wider mb-4"
                  :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">Explorar</h4>
              <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                <li @click="scrollToSection('catalogo')" class="hover:text-red-500 cursor-pointer transition">Todas as Lojas</li>
                <li @click="scrollToSection('produtos')" class="hover:text-red-500 cursor-pointer transition">Produtos</li>
              </ul>
            </div>
            <div>
              <h4 class="text-xs font-semibold uppercase tracking-wider mb-4"
                  :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">Suporte</h4>
              <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                <li class="hover:text-red-500 cursor-pointer transition">Ajuda</li>
                <li class="hover:text-red-500 cursor-pointer transition">Contacto</li>
                <li class="hover:text-red-500 cursor-pointer transition">FAQ</li>
              </ul>
            </div>
            <div>
              <h4 class="text-xs font-semibold uppercase tracking-wider mb-4"
                  :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">Legal</h4>
              <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                <li class="hover:text-red-500 cursor-pointer transition">Termos de Serviço</li>
                <li class="hover:text-red-500 cursor-pointer transition">Privacidade</li>
              </ul>
            </div>
          </div>
          <div class="max-w-7xl mx-auto mt-8 pt-8 border-t text-center text-sm"
               :class="isDark ? 'border-zinc-800 text-zinc-500' : 'border-stone-200 text-zinc-400'">
            © {{ new Date().getFullYear() }} Marketplace. Todos os direitos reservados.
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script>
import { Navigation, Pagination, Autoplay } from 'swiper/modules'
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
import logoDefault from '@/assets/img/login/logo_final_4k.png'
import logoLight from '@/assets/img/login/logo_final_4k_light.png'
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
      isDark: true,   // dark por defeito — pode ser lido de localStorage se quiseres
      newStores: [],
      categoriasExistentes: [],
      tiposExistentes: [],
      loadingCategorias: true,
      selectedProduct: null,
      selectedLoja: null,
      selectedCategoria: null,
      storesByCategory: [],
      sidebarAberta: false,
      categoriasPlataforma: [],
      user: {},
      sectionRefs: {},
      logoDefault,
      logoLight,
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
    // Persistir preferência de tema
    const savedDark = localStorage.getItem('home_dark_mode')
    if (savedDark !== null) this.isDark = savedDark === 'true'

    await Promise.all([
      this.fetchNewStores(),
      this.fetchCategoriasExistentes(),
      this.fetchTiposExistentes(),
      this.fetchCategoriasPlataforma(),
    ])
  },

  watch: {
    isDark (val) {
      localStorage.setItem('home_dark_mode', String(val))
    }
  },

  methods: {
    goToStore (id) { this.sidebarAberta = false; this.$router.push(`/loja/${id}`) },
    openProduct (produto) { this.selectedProduct = produto; this.selectedLoja = produto.loja },
    tipoIcon (nome) { return TIPO_ICONS[nome?.toLowerCase()] || '📦' },

    scrollToSection (key) {
      const el = this.sectionRefs[key]
      if (el) { el.scrollIntoView({ behavior: 'smooth' }); this.sidebarAberta = false }
    },

    async selectCategoria (cat) {
      this.selectedCategoria = cat.value
      await this.fetchStoresByCategory(cat.value)
      this.scrollToSection(cat.value)
    },

    clearCategoria () { this.selectedCategoria = null; this.storesByCategory = [] },

    async fetchStoresByCategory (categoria) {
      try {
        const { data } = await api.get(`/app/loja/?categoria=${encodeURIComponent(categoria)}&limit=10`)
        this.storesByCategory = data.results || data
      } catch (e) { console.error(e) }
    },

    stopHeroAutoplay  () { this.$refs.heroSwiper?.swiper?.autoplay.stop() },
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

    async fetchCategoriasPlataforma () {
      try {
        const { data } = await api.get('/app/categorias-destaque/')
        this.categoriasPlataforma = data
      } catch (e) { console.error(e) }
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
      heroPagination: { clickable: true },
      modules: [Navigation, Pagination, Autoplay],
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
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>