<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100">
    <Profile :data="user" class=" z-10" @log_out="log_out()"/>
    <ProductInfoCard

        :produto="selectedProduct"
        :loja="selectedLoja"
        @close="selectedProduct = null"
        @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)"
    />

    <MultiCart ref="cart" />

    <div class="flex overflow-x-hidden">
      <!-- Sidebar -->
      <aside class="fixed left-0 top-0 h-[100vh] w-64 bg-zinc-900 border-r border-zinc-800 overflow-y-auto hidden lg:block">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-zinc-100 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            Categorias
          </h2>
          <ul class="space-y-1">
            <li
              v-for="categoria in categorias"
              :key="categoria"
              @click="selectCategoria(categoria)"
              :class="[
                'px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-3',
                selectedCategoria === categoria
                  ? 'bg-red-600 text-white'
                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
              ]"
            >
              <span class="w-2 h-2 rounded-full" :class="selectedCategoria === categoria ? 'bg-white' : 'bg-zinc-600'"></span>
              {{ categoria }}
            </li>
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
          </ul>
        </div>

        <!-- Stores by Category -->
        <div v-if="selectedCategoria && storesByCategory.length > 0" class="p-6 border-t border-zinc-800">
          <h3 class="text-sm font-medium text-zinc-400 mb-3 uppercase tracking-wider">
            Lojas em {{ selectedCategoria }}
          </h3>
          <ul class="space-y-2">
            <li
              v-for="store in storesByCategory"
              :key="store.id"
              @click="goToStore(store.id)"
              class="flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-800 cursor-pointer transition-colors"
            >
              <img
                v-if="store.logo_url"
                :src="store.logo_url"
                :alt="store.nome"
                class="w-10 h-10 rounded-lg object-cover"
              />
              <div v-else class="w-10 h-10 rounded-lg bg-zinc-700 flex items-center justify-center">
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

      <!-- Main Content -->
      <main class="flex-1 lg:ml-64  overflow-x-hidden">
        <!-- Hero Section - 3 New Stores -->
        <section class="relative overflow-hidden">
          <swiper
            ref="heroSwiper"
            :pagination="heroPagination"
            :modules="modules"
            :autoplay="{ delay: 2000, disableOnInteraction: false }"
            :speed="800"
            :effect="'fade'"
            class="h-[70vh]"
            @mouseenter="stopHeroAutoplay"
            @mouseleave="startHeroAutoplay"
          >
            <swiper-slide
              v-for="store in newStores"
              :key="store.id"
              @click="goToStore(store.id)"
              class="cursor-pointer"
            >
              <div class="relative h-full w-full">
                <img
                  :src="store.banner_url || '/placeholder-banner.jpg'"
                  :alt="store.nome"
                  class="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                />
                <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-transparent"></div>
                <div class="absolute inset-0 bg-gradient-to-r from-zinc-950/80 to-transparent"></div>
                
                <!-- Store Info -->
                <div class="absolute bottom-0 left-0 p-8 md:p-12 max-w-2xl">
                  <span class="inline-block px-3 py-1 bg-red-600 text-white text-xs font-semibold rounded-full mb-4 uppercase tracking-wider">
                    Nova Loja
                  </span>
                  <h1 class="text-4xl md:text-6xl font-bold text-white mb-3">{{ store.nome }}</h1>
                  <p class="text-lg md:text-xl text-zinc-300 mb-4 line-clamp-2">{{ store.descricao }}</p>
                  <div class="flex items-center gap-4 text-zinc-400">
                    <span class="flex items-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {{ store.localizacao }}
                    </span>
                    <span class="flex items-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      {{ store.categoria }}
                    </span>
                    <span v-if="store.rating_medio" class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                      {{ store.rating_medio }}
                    </span>
                  </div>
                  <button class="mt-6 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2">
                    Visitar Loja
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </button>
                </div>
              </div>
            </swiper-slide>
          </swiper>
        </section>

        <!-- Top 5 Stores Section -->
        <section class="py-12 px-6 md:px-12 bg-zinc-900/50">
          <div class="flex items-center justify-between mb-8">
            <div>
              <h2 class="text-2xl md:text-3xl font-bold text-white">Lojas em Destaque</h2>
              <p class="text-zinc-400 mt-1">As melhores lojas da plataforma</p>
            </div>
            <div class="flex gap-2">
              <button
                @click="prevTopStore"
                class="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                @click="nextTopStore"
                class="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          <swiper
            ref="topStoresSwiper"
            :slides-per-view="1.2"
            :space-between="20"
            :breakpoints="{
              640: { slidesPerView: 2.2 },
              1024: { slidesPerView: 3.2 },
              1280: { slidesPerView: 4.2 }
            }"
            :modules="[Navigation]"
            class="top-stores-swiper !overflow-hidden"
          >
            <swiper-slide v-for="store in topStores" :key="store.id">
              <div
                @click="goToStore(store.id)"
                class="group relative rounded-2xl overflow-hidden cursor-pointer bg-zinc-800 h-72"
              >
                <img
                  :src="store.banner_url || store.logo_url || '/placeholder-store.jpg'"
                  :alt="store.nome"
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent"></div>
                
                <!-- Store Logo -->
                <div class="absolute top-4 left-4">
                  <img
                    v-if="store.logo_url"
                    :src="store.logo_url"
                    :alt="store.nome"
                    class="w-14 h-14 rounded-xl object-cover border-2 border-zinc-700 shadow-lg"
                  />
                  <div v-else class="w-14 h-14 rounded-xl bg-zinc-700 flex items-center justify-center border-2 border-zinc-600">
                    <span class="text-xl font-bold text-zinc-400">{{ store.nome.charAt(0) }}</span>
                  </div>
                </div>

                <!-- Rating Badge -->
                <div v-if="store.rating_medio" class="absolute top-4 right-4 px-2 py-1 bg-zinc-900/80 backdrop-blur rounded-lg flex items-center gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  <span class="text-sm font-semibold text-white">{{ store.rating_medio }}</span>
                </div>

                <!-- Store Info -->
                <div class="absolute bottom-0 left-0 right-0 p-5">
                  <span class="inline-block px-2 py-0.5 bg-red-600/90 text-white text-xs font-medium rounded mb-2">
                    {{ store.categoria }}
                  </span>
                  <h3 class="text-xl font-bold text-white mb-1 group-hover:text-red-400 transition-colors">
                    {{ store.nome }}
                  </h3>
                  <p class="text-sm text-zinc-400 flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    </svg>
                    {{ store.localizacao }}
                  </p>
                  
                  <!-- Delivery Tags -->
                  <div class="flex gap-2 mt-3">
                    <span v-if="store.entrega_ativa" class="px-2 py-0.5 bg-green-600/20 text-green-400 text-xs rounded flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      Entrega
                    </span>
                    <span v-if="store.levantamento_ativo" class="px-2 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      Takeaway
                    </span>
                  </div>
                </div>
              </div>
            </swiper-slide>
          </swiper>
        </section>

        <!-- Products by Category Section -->
        <section class="py-12 px-6 md:px-12">
          <div class="mb-8">
            <h2 class="text-2xl md:text-3xl font-bold text-white">Produtos por Categoria</h2>
            <p class="text-zinc-400 mt-1">Descubra produtos de diversas lojas</p>
          </div>

          <!-- Product Type Tabs -->
          <div class="flex gap-2 mb-8 overflow-x-auto pb-2 scrollbar-hide">
            <button
              v-for="tipo in productTypes"
              :key="tipo.id"
              @click="selectProductType(tipo)"
              :class="[
                'px-5 py-2.5 rounded-full font-medium transition-all whitespace-nowrap',
                selectedProductType?.id === tipo.id
                  ? 'bg-red-600 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200'
              ]"
            >
              {{ tipo.nome }}
            </button>
          </div>

          <!-- Products Grid -->
          <div v-if="loadingProducts" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <div v-for="n in 8" :key="n" class="animate-pulse">
              <div class="bg-zinc-800 rounded-2xl h-64"></div>
              <div class="mt-3 h-4 bg-zinc-800 rounded w-3/4"></div>
              <div class="mt-2 h-3 bg-zinc-800 rounded w-1/2"></div>
            </div>
          </div>

          <div v-else-if="productsByType.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <div
              v-for="product in productsByType"
              :key="product.id"
              @click="openProduct(product)"
              class="group bg-zinc-900 rounded-2xl overflow-hidden cursor-pointer border border-zinc-800 hover:border-red-600/50 transition-all duration-300"
            >
              <div class="relative h-48 overflow-hidden">
                <img
                  :src="product.ficheiro_url || '/placeholder-product.jpg'"
                  :alt="product.nome"
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div class="absolute top-3 left-3">
                  <span class="px-2 py-1 bg-zinc-900/80 backdrop-blur text-xs font-medium text-zinc-300 rounded">
                    {{ product.tipo?.nome || 'Produto' }}
                  </span>
                </div>
                <div v-if="product.destaque" class="absolute top-3 right-3">
                  <span class="px-2 py-1 bg-red-600 text-xs font-medium text-white rounded flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                    Destaque
                  </span>
                </div>
              </div>
              <div class="p-4">
                <h3 class="text-lg font-semibold text-white group-hover:text-red-400 transition-colors line-clamp-1">
                  {{ product.nome }}
                </h3>
                <p class="text-sm text-zinc-500 mt-1 line-clamp-2">{{ product.descricao }}</p>
                <div class="flex items-center justify-between mt-4">
                  <span class="text-xl font-bold text-red-500">{{ formatPrice(product.preco) }}</span>
                  <span v-if="product.stock" class="text-xs text-zinc-500">
                    {{ product.stock.quantidade }} em stock
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-16">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-zinc-700 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p class="text-zinc-500 text-lg">Nenhum produto encontrado nesta categoria</p>
          </div>

          <!-- Load More Button -->
          <div v-if="productsByType.length > 0 && hasMoreProducts" class="text-center mt-10">
            <button
              @click="loadMoreProducts"
              :disabled="loadingMore"
              class="px-8 py-3 bg-zinc-800 hover:bg-zinc-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2 mx-auto"
            >
              <svg v-if="loadingMore" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ loadingMore ? 'A carregar...' : 'Ver mais produtos' }}
            </button>
          </div>
        </section>

        <section class="py-4 px-6 md:px-12 bg-zinc-900/50">
          <StoreSlider title="Lojas em Destaque" icon="🏪"
           @store-click="goToStore($event.id)" />
          
        </section>
        
        <section class="py-4 px-6 md:px-12 bg-zinc-900/50">
          <StoreSlider title="Restaurantes" icon="🍔"
            :params="{ categoria: 'restaurante' }"
            @store-click="goToStore($event.id)" />

        </section>

        <section class="py-4 px-6 md:px-12 bg-zinc-900/50">
          <StoreSlider title="Modas" icon="👗"
            :params="{ categoria: 'moda' }"
            @store-click="goToStore($event.id)" />

        </section>

        <section class="py-4 px-6 md:px-12 bg-zinc-900/50">
          <StoreSlider title="Eletronicos" icon="📱"
            :params="{ categoria: 'eletronica' }"
            @store-click="goToStore($event.id)" />

        </section>

        <section class="py-4 px-6 md:px-12 bg-zinc-900/50">
        <ProductSlider title="Produtos em Destaque" icon="⭐"
          :params="{ destaque: true }"
          @product-click="openProduct($event)" />
        </section>

        <section class="py-4 px-6 md:px-12 bg-zinc-900/50">
          <StoreCatalog @store-click="goToStore($event.id)" />
        </section>
        


        <!-- Footer -->
        <footer class="bg-zinc-900 border-t border-zinc-800 py-12 px-6 md:px-12">
          <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 class="text-xl font-bold text-white mb-4">Marketplace</h3>
              <p class="text-zinc-400 text-sm">A melhor plataforma para descobrir lojas e produtos incriveis.</p>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Explorar</h4>
              <ul class="space-y-2 text-zinc-400">
                <li class="hover:text-white cursor-pointer transition-colors">Todas as Lojas</li>
                <li class="hover:text-white cursor-pointer transition-colors">Categorias</li>
                <li class="hover:text-white cursor-pointer transition-colors">Promocoes</li>
              </ul>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Suporte</h4>
              <ul class="space-y-2 text-zinc-400">
                <li class="hover:text-white cursor-pointer transition-colors">Ajuda</li>
                <li class="hover:text-white cursor-pointer transition-colors">Contacto</li>
                <li class="hover:text-white cursor-pointer transition-colors">FAQ</li>
              </ul>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Legal</h4>
              <ul class="space-y-2 text-zinc-400">
                <li class="hover:text-white cursor-pointer transition-colors">Termos de Servico</li>
                <li class="hover:text-white cursor-pointer transition-colors">Privacidade</li>
              </ul>
            </div>
          </div>
          <div class="max-w-7xl mx-auto mt-8 pt-8 border-t border-zinc-800 text-center text-zinc-500 text-sm">
            <p>&copy; {{ new Date().getFullYear() }} Marketplace. Todos os direitos reservados.</p>
          </div>
        </footer>
      </main>
    </div>

    <!-- Mobile Category Drawer -->
    <div
      v-if="showMobileCategories"
      class="fixed inset-0 z-50 lg:hidden"
      @click="showMobileCategories = false"
    >
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
      <div
        class="absolute left-0 top-0 h-full w-72 bg-zinc-900 p-6 overflow-y-auto"
        @click.stop
      >
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-white">Categorias</h2>
          <button @click="showMobileCategories = false" class="p-2 hover:bg-zinc-800 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <ul class="space-y-1">
          <li
            v-for="categoria in categorias"
            :key="categoria"
            @click="selectCategoria(categoria); showMobileCategories = false"
            :class="[
              'px-4 py-3 rounded-lg cursor-pointer transition-all duration-200',
              selectedCategoria === categoria
                ? 'bg-red-600 text-white'
                : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
            ]"
          >
            {{ categoria }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Mobile Category Button -->
    <button
      @click="showMobileCategories = true"
      class="fixed bottom-6 right-6 z-40 lg:hidden p-4 bg-red-600 hover:bg-red-700 text-white rounded-full shadow-lg transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
  </div>
</template>

<script>
import { Navigation, Pagination, Autoplay, EffectFade } from 'swiper/modules'
import { Swiper, SwiperSlide } from 'swiper/vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import StoreSlider from '@/components/sliders/StoreSlider.vue'
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import StoreCatalog from '@/components/catalog/StoreCatalog.vue'


import api from '@/services/api'

import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/navigation'
import 'swiper/css/effect-fade'

export default {
  name: 'AppHome',
  components: {
    Swiper,
    SwiperSlide,
    Profile,
    ProductInfoCard,
    MultiCart,
    StoreSlider,
    ProductSlider,
    StoreCatalog
  },
  data() {
    return {
      // Stores
      newStores: [],
      topStores: [],
      storesByCategory: [],


      // Categories
      categorias: [
        'Restaurante',
        'Moda',
        'Tecnologia',
        'Supermercado',
        'Farmacia',
        'Desporto',
        'Casa e Jardim',
        'Beleza',
        'Livraria',
        'Outros'
      ],
      selectedCategoria: null,
      selectedLoja: null,
      selectedProduct: null,

      // Products
      productTypes: [],
      selectedProductType: null,
      productsByType: [],
      loadingProducts: false,
      loadingMore: false,
      productOffset: 0,
      productLimit: 12,
      hasMoreProducts: true,

      // Mobile
      showMobileCategories: false,

      // User
      user: {},
    }
  },
  async created() {
  const user = localStorage.getItem('user')
  this.user = user ? JSON.parse(user) : {}

  await Promise.all([
    this.fetchNewStores(),
    this.fetchTopStores(),
    this.fetchProductTypes(),
  ])
},
  methods: {
    // Navigation
    goToStore(id) {
      this.$router.push(`/loja/${id}`)
    },
    async openProduct(produto) {
        console.log('Produto selecionado:', produto)
        
        this.selectedLoja = produto.loja
        this.selectedProduct = produto
    },

    // Hero Swiper Controls
    stopHeroAutoplay() {
      if (this.$refs.heroSwiper?.swiper) {
        this.$refs.heroSwiper.swiper.autoplay.stop()
      }
    },
    startHeroAutoplay() {
      if (this.$refs.heroSwiper?.swiper) {
        this.$refs.heroSwiper.swiper.autoplay.start()
      }
    },

    // Top Stores Swiper Controls
    prevTopStore() {
      if (this.$refs.topStoresSwiper?.swiper) {
        this.$refs.topStoresSwiper.swiper.slidePrev()
      }
    },
    nextTopStore() {
      if (this.$refs.topStoresSwiper?.swiper) {
        this.$refs.topStoresSwiper.swiper.slideNext()
      }
    },

    // Category Selection
    selectCategoria(categoria) {
      this.selectedCategoria = categoria
      this.fetchStoresByCategory()
    },
    clearCategoria() {
      this.selectedCategoria = null
      this.storesByCategory = []
    },

    // Product Type Selection
    selectProductType(tipo) {
      this.selectedProductType = tipo
      this.productOffset = 0
      this.productsByType = []
      this.hasMoreProducts = true
      this.fetchProductsByType()
    },

    // Format price
    formatPrice(price) {
      return new Intl.NumberFormat('pt-PT', {
        style: 'currency',
        currency: 'EUR'
      }).format(price)
    },

    // API Calls
    async fetchNewStores() {
      try {
        const res = await api.get('/app/loja/?offset=0&limit=3')
        this.newStores = res.data.results || res.data
        console.log('Novas lojas:', this.newStores)
      } catch (error) {
        console.error('Erro ao buscar novas lojas:', error)
      }
    },

    async fetchTopStores() {
      try {
        const res = await api.get('/app/loja/?offset=0&limit=5')
        this.topStores = res.data.results || res.data
      } catch (error) {
        console.error('Erro ao buscar lojas populares:', error)
      }
    },

    async fetchStoresByCategory() {
      if (!this.selectedCategoria) return
      try {
        const res = await api.get(`/app/loja/?categoria=${encodeURIComponent(this.selectedCategoria)}&offset=0&limit=10`)
        this.storesByCategory = res.data.results || res.data
      } catch (error) {
        console.error('Erro ao buscar lojas por categoria:', error)
      }
    },

    async fetchProductTypes() {
      try {
        const res = await api.get('/app/produto/tipos/')
        this.productTypes = res.data
        if (this.productTypes.length > 0) {
          this.selectedProductType = this.productTypes[0]
          await this.fetchProductsByType()
        }
      } catch (error) {
        console.error('Erro ao buscar tipos de produto:', error)
      }
    },

    async fetchProductsByType() {
      if (!this.selectedProductType) return
      this.loadingProducts = true
      try {
        const res = await api.get(`/app/produto/?tipo=${encodeURIComponent(this.selectedProductType.nome)}&offset=${this.productOffset}&limit=${this.productLimit}`)
        const results = res.data.results || res.data
        this.productsByType = results
        this.hasMoreProducts = results.length === this.productLimit
      } catch (error) {
        console.error('Erro ao buscar produtos:', error)
      } finally {
        this.loadingProducts = false
      }
    },

    async loadMoreProducts() {
      if (!this.selectedProductType || this.loadingMore) return
      this.loadingMore = true
      this.productOffset += this.productLimit
      try {
        const res = await api.get(`/app/produto/?tipo=${encodeURIComponent(this.selectedProductType.nome)}&offset=${this.productOffset}&limit=${this.productLimit}`)
        const results = res.data.results || res.data
        this.productsByType = [...this.productsByType, ...results]
        this.hasMoreProducts = results.length === this.productLimit
      } catch (error) {
        console.error('Erro ao carregar mais produtos:', error)
      } finally {
        this.loadingMore = false
      }
    },
    log_out() {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
            this.user = {}
            this.user_credit_card = {}
            this.cart_data = []
            this.cart_id = 0
            this.show_cart = false;
            this.show_produtoCard = false;
            this.info_card_data = [];
            console.log("User logged out")
            this.$router.push('/login')
        },
  },
  setup() {
    return {
      heroPagination: {
        clickable: true,
        renderBullet: function (index, className) {
          return '<span class="' + className + '"></span>'
        },
      },
      modules: [Navigation, Pagination, Autoplay, EffectFade],
      Navigation,
    }
  },
}
</script>

<style scoped>
.swiper {
  --swiper-pagination-bullet-inactive-color: rgba(255, 255, 255, 0.4);
  --swiper-pagination-color: #dc2626;
  --swiper-pagination-bullet-size: 10px;
  --swiper-pagination-bullet-horizontal-gap: 6px;
}

.swiper-pagination {
  bottom: 30px !important;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
