<!-- TemplateMinimalista — Clean, espacado, tipografia leve, muito whitespace, ideal para lojas premium/design -->
<template>
  <div class="min-h-screen transition-colors duration-500"
       :class="isDark ? 'bg-neutral-950 text-neutral-100' : 'bg-neutral-50 text-neutral-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <!-- Minimal nav -->
    <nav class="fixed top-0 left-0 right-0 z-30 transition-all duration-500"
         :class="scrolled 
           ? (isDark ? 'bg-neutral-950/90 backdrop-blur-xl' : 'bg-neutral-50/90 backdrop-blur-xl')
           : ''">
      <div class="max-w-6xl mx-auto px-8 py-6 flex items-center justify-between">
        <button @click="$router.back()"
          class="p-2 -ml-2 transition-colors"
          :class="isDark ? 'text-neutral-400 hover:text-neutral-100' : 'text-neutral-500 hover:text-neutral-900'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>

        <!-- Center logo when scrolled -->
        <transition enter-active-class="transition duration-300" enter-from-class="opacity-0 -translate-y-2">
          <span v-if="scrolled && loja" class="text-sm tracking-[0.2em] uppercase"
                :class="isDark ? 'text-neutral-300' : 'text-neutral-700'">
            {{ loja.nome }}
          </span>
        </transition>

        <button @click="toggleDark"
          class="p-2 -mr-2 transition-colors"
          :class="isDark ? 'text-neutral-400 hover:text-neutral-100' : 'text-neutral-500 hover:text-neutral-900'">
          <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>
      </div>
    </nav>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="w-8 h-8 border border-current rounded-full animate-spin"
           style="border-top-color: transparent;"></div>
    </div>

    <template v-else-if="loja">
      <!-- HERO Minimalista - Centered, lots of whitespace -->
      <section class="min-h-screen flex flex-col justify-center px-8">
        <div class="max-w-6xl mx-auto w-full">
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
            <!-- Left: Text -->
            <div class="lg:col-span-7">
              <p class="text-xs tracking-[0.3em] uppercase mb-8"
                 :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">
                {{ loja.categoria }}
              </p>
              
              <h1 class="text-5xl md:text-7xl font-light tracking-tight leading-none mb-8"
                  :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">
                {{ loja.nome }}
              </h1>

              <p v-if="loja.descricao" class="text-lg font-light leading-relaxed max-w-lg mb-12"
                 :class="isDark ? 'text-neutral-400' : 'text-neutral-600'">
                {{ loja.descricao }}
              </p>

              <!-- Minimal stats -->
              <div class="flex items-center gap-12">
                <div v-if="loja.rating_medio">
                  <p class="text-3xl font-light" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">{{ loja.rating_medio }}</p>
                  <p class="text-xs tracking-wider uppercase mt-1" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Rating</p>
                </div>
                <div v-if="loja.total_avaliacoes">
                  <p class="text-3xl font-light" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">{{ loja.total_avaliacoes }}</p>
                  <p class="text-xs tracking-wider uppercase mt-1" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Reviews</p>
                </div>
                <div v-if="loja.localizacao">
                  <p class="text-lg font-light" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">{{ loja.localizacao }}</p>
                  <p class="text-xs tracking-wider uppercase mt-1" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Location</p>
                </div>
              </div>

              <!-- CTA -->
              <div class="flex items-center gap-6 mt-16">
                <button @click="scrollToId('produtos')"
                  class="px-8 py-4 text-sm tracking-wider uppercase transition-all hover:tracking-widest"
                  :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
                  Explorar
                </button>
                <button @click="scrollToId('sobre')"
                  class="px-8 py-4 text-sm tracking-wider uppercase transition-all hover:tracking-widest border"
                  :class="isDark ? 'border-neutral-700 text-neutral-300 hover:border-neutral-500' : 'border-neutral-300 text-neutral-700 hover:border-neutral-500'">
                  Sobre
                </button>
              </div>
            </div>

            <!-- Right: Image -->
            <div class="lg:col-span-5">
              <div class="aspect-[4/5] relative">
                <img v-if="loja.banner_url || loja.logo_url" 
                     :src="loja.banner_url || loja.logo_url" 
                     :alt="loja.nome" 
                     class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center"
                     :class="isDark ? 'bg-neutral-900' : 'bg-neutral-200'">
                  <span class="text-8xl font-light" :class="isDark ? 'text-neutral-700' : 'text-neutral-400'">
                    {{ loja.nome.charAt(0) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Main content -->
      <main class="max-w-6xl mx-auto px-8">
        
        <!-- About section -->
        <section id="sobre" class="py-32 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-16">
            <div>
              <p class="text-xs tracking-[0.3em] uppercase mb-4" :style="{ color: 'var(--cor-primaria)' }">About</p>
              <h2 class="text-4xl font-light mb-8" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">
                {{ loja.nome }}
              </h2>
              <p class="font-light leading-loose" :class="isDark ? 'text-neutral-400' : 'text-neutral-600'">
                {{ loja.descricao || 'Uma loja com foco na qualidade e simplicidade. Cada produto e cuidadosamente selecionado para oferecer a melhor experiencia.' }}
              </p>
            </div>
            
            <div class="grid grid-cols-2 gap-8">
              <div v-if="opcoesEntrega.length">
                <p class="text-xs tracking-[0.2em] uppercase mb-4" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Envio</p>
                <div v-for="opcao in opcoesEntrega.slice(0, 2)" :key="opcao.id" class="mb-3">
                  <p class="font-light" :class="isDark ? 'text-neutral-200' : 'text-neutral-800'">{{ opcao.nome }}</p>
                  <p class="text-sm" :style="{ color: 'var(--cor-primaria)' }">{{ opcao.preco == 0 ? 'Gratis' : formatPrice(opcao.preco) }}</p>
                </div>
              </div>
              <div v-if="metodosPagamento.length">
                <p class="text-xs tracking-[0.2em] uppercase mb-4" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Pagamento</p>
                <div class="space-y-2">
                  <p v-for="m in metodosPagamento.slice(0, 3)" :key="m.id" 
                     class="font-light" :class="isDark ? 'text-neutral-200' : 'text-neutral-800'">
                    {{ m.tipo }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Featured - Minimal section -->
        <section id="produtos" class="py-24 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
          <div class="flex items-end justify-between mb-16">
            <div>
              <p class="text-xs tracking-[0.3em] uppercase mb-3" :style="{ color: 'var(--cor-primaria)' }">Featured</p>
              <h2 class="text-4xl font-light" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">Destaques</h2>
            </div>
            <button @click="scrollToId('catalogo')" 
              class="text-sm tracking-wider uppercase transition-colors"
              :class="isDark ? 'text-neutral-400 hover:text-neutral-100' : 'text-neutral-500 hover:text-neutral-900'">
              Ver todos
            </button>
          </div>
          <ProductSlider title="Destaques" icon=""
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- By Type - Clean sections -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id" 
                   class="py-24 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
            <div class="flex items-end justify-between mb-16">
              <div>
                <p class="text-xs tracking-[0.3em] uppercase mb-3" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Collection</p>
                <h2 class="text-4xl font-light capitalize" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">{{ tipo.nome }}</h2>
              </div>
            </div>
            <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
              :params="{ loja_id: lojaId, tipo: tipo.nome }"
              :isDark="isDark" :show-title="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Categories - Horizontal scroll pills -->
        <template v-if="categoriasExistentes.length > 0">
          <section class="py-24 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
            <p class="text-xs tracking-[0.3em] uppercase mb-3" :style="{ color: 'var(--cor-primaria)' }">Categories</p>
            <h2 class="text-4xl font-light mb-12" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">Por Categoria</h2>
            
            <!-- Category nav -->
            <div class="flex gap-4 overflow-x-auto pb-4 mb-16 scrollbar-hide">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-6 py-3 text-sm tracking-wider whitespace-nowrap transition-all border"
                :class="isDark ? 'border-neutral-800 text-neutral-300 hover:border-neutral-600' : 'border-neutral-200 text-neutral-700 hover:border-neutral-400'">
                {{ cat.nome }}
              </button>
            </div>

            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-20 last:mb-0">
              <h3 class="text-2xl font-light capitalize mb-8" :class="isDark ? 'text-neutral-200' : 'text-neutral-800'">{{ cat.nome }}</h3>
              <ProductSlider :title="cat.nome" :icon="cat.icone"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark" :show-title="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Full Catalog -->
        <section id="catalogo" class="py-24 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
          <div class="flex items-end justify-between mb-16">
            <div>
              <p class="text-xs tracking-[0.3em] uppercase mb-3" :style="{ color: 'var(--cor-primaria)' }">Catalog</p>
              <h2 class="text-4xl font-light" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">Todos os Produtos</h2>
            </div>
          </div>
          <ProductCatalog :loja-id="lojaId" :isDark="isDark" @product-click="selectedProduct = $event" />
        </section>

        <!-- Reviews -->
        <section id="avaliacoes" class="py-24 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
          <div class="mb-16">
            <p class="text-xs tracking-[0.3em] uppercase mb-3" :style="{ color: 'var(--cor-primaria)' }">Feedback</p>
            <h2 class="text-4xl font-light" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">Avaliacoes</h2>
          </div>
          <AvaliacaoLoja :loja-id="lojaId" :isDark="isDark" @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer - Ultra minimal -->
        <footer class="py-24 border-t" :class="isDark ? 'border-neutral-800' : 'border-neutral-200'">
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
            <div>
              <p class="text-2xl font-light mb-2" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">{{ loja.nome }}</p>
              <p class="text-sm" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">{{ loja.categoria }}</p>
            </div>
            
            <div class="flex gap-8 text-sm" :class="isDark ? 'text-neutral-400' : 'text-neutral-500'">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" 
                class="tracking-wider uppercase hover:underline underline-offset-4">Returns</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" 
                class="tracking-wider uppercase hover:underline underline-offset-4">Terms</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" 
                class="tracking-wider uppercase hover:underline underline-offset-4">Privacy</button>
            </div>
          </div>
          
          <div class="mt-16 pt-8 border-t text-center" :class="isDark ? 'border-neutral-900' : 'border-neutral-100'">
            <p class="text-xs tracking-wider" :class="isDark ? 'text-neutral-600' : 'text-neutral-400'">
              {{ new Date().getFullYear() }}
            </p>
          </div>
        </footer>
      </main>

      <!-- Modal politicas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-8"
           @click.self="modalPolitica = null">
        <div class="absolute inset-0" :class="isDark ? 'bg-neutral-950/90' : 'bg-neutral-50/90'" @click="modalPolitica = null"></div>
        <div class="relative w-full max-w-lg max-h-[80vh] overflow-y-auto"
             :class="isDark ? 'bg-neutral-900' : 'bg-white'">
          <div class="flex items-center justify-between p-8 border-b sticky top-0"
               :class="isDark ? 'bg-neutral-900 border-neutral-800' : 'bg-white border-neutral-100'">
            <h3 class="text-sm tracking-[0.2em] uppercase" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">
              {{ modalPolitica === 'devolucao' ? 'Returns' : modalPolitica === 'termos' ? 'Terms' : 'Privacy' }}
            </h3>
            <button @click="modalPolitica = null"
              class="p-2 transition-colors"
              :class="isDark ? 'text-neutral-400 hover:text-neutral-100' : 'text-neutral-500 hover:text-neutral-900'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-8 text-sm leading-loose font-light whitespace-pre-wrap"
               :class="isDark ? 'text-neutral-300' : 'text-neutral-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center px-8">
      <p class="text-4xl font-light mb-4" :class="isDark ? 'text-neutral-300' : 'text-neutral-700'">Not Found</p>
      <p class="text-sm mb-8" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">A loja nao foi encontrada</p>
      <button @click="$router.back()" 
        class="text-sm tracking-wider uppercase" 
        :style="{ color: 'var(--cor-primaria)' }">
        Voltar
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateMinimalista',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup(props) {
    const isDark = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()
    
    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#171717',
      '--cor-secundaria': props.tema?.corSecundaria || '#fafafa',
    }))
    
    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark() { isDark.value = !isDark.value }
    function onScroll() { scrolled.value = window.scrollY > 100 }
    
    onMounted(() => window.addEventListener('scroll', onScroll))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrolled, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>
