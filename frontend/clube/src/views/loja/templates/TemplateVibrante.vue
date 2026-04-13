<!-- TemplateVibrante — Bold, colorido, energetico, formas geometricas, ideal para lojas jovens/streetwear -->
<template>
  <div class="min-h-screen transition-colors duration-300 overflow-x-hidden"
       :class="isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <!-- Bold floating nav -->
    <nav class="fixed top-4 left-4 right-4 z-30">
      <div class="max-w-7xl mx-auto px-4 py-3 rounded-2xl flex items-center justify-between transition-all"
           :class="scrolled 
             ? (isDark ? 'bg-zinc-900/90 backdrop-blur-xl border border-zinc-800' : 'bg-white/90 backdrop-blur-xl border border-zinc-200 shadow-xl')
             : 'bg-transparent'">
        <button @click="$router.back()"
          class="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg transition-all"
          :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div v-if="scrolled && loja" class="flex items-center gap-3">
          <span class="font-black text-lg uppercase tracking-wider" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.nome }}</span>
        </div>

        <button @click="toggleDark"
          class="w-12 h-12 rounded-xl flex items-center justify-center font-bold transition-all border-2"
          :class="isDark ? 'border-white text-white hover:bg-white hover:text-zinc-900' : 'border-zinc-900 text-zinc-900 hover:bg-zinc-900 hover:text-white'">
          {{ isDark ? 'LT' : 'DK' }}
        </button>
      </div>
    </nav>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="relative">
        <div class="w-20 h-20 rounded-xl animate-spin" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
        <div class="absolute inset-2 rounded-lg" :class="isDark ? 'bg-zinc-950' : 'bg-white'"></div>
      </div>
    </div>

    <template v-else-if="loja">
      <!-- HERO Vibrante - Geometric shapes and bold typography -->
      <section class="relative min-h-screen overflow-hidden">
        <!-- Background with geometric shapes -->
        <div class="absolute inset-0" :class="isDark ? 'bg-zinc-950' : 'bg-zinc-100'">
          <!-- Main background image -->
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome" class="w-full h-full object-cover opacity-40" />
          
          <!-- Geometric overlays -->
          <div class="absolute top-0 right-0 w-1/2 h-full" :style="{ backgroundColor: 'var(--cor-primaria)', opacity: 0.9 }"></div>
          <div class="absolute bottom-0 left-0 w-2/3 h-1/2 -skew-y-6 origin-left" 
               :class="isDark ? 'bg-zinc-900' : 'bg-white'"></div>
          
          <!-- Decorative shapes -->
          <div class="absolute top-20 left-10 w-32 h-32 rounded-full border-4 opacity-20"
               :style="{ borderColor: 'var(--cor-primaria)' }"></div>
          <div class="absolute bottom-40 right-20 w-48 h-48 rounded-full opacity-10"
               :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
          <div class="absolute top-1/3 left-1/4 w-8 h-8 rotate-45"
               :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
        </div>

        <!-- Content -->
        <div class="relative max-w-7xl mx-auto px-6 pt-32 pb-20 min-h-screen flex items-center">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center w-full">
            <!-- Left: Main content -->
            <div class="relative z-10">
              <!-- Tag -->
              <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 font-bold uppercase tracking-wider text-sm"
                   :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
                <span class="w-3 h-3 bg-white rounded-full animate-pulse"></span>
                {{ loja.categoria }}
              </div>

              <!-- Title with outline effect -->
              <h1 class="text-6xl md:text-8xl font-black uppercase leading-none mb-6">
                <span class="block" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.nome.split(' ')[0] }}</span>
                <span v-if="loja.nome.split(' ').length > 1" 
                      class="block stroke-text"
                      :style="{ color: 'transparent', '-webkit-text-stroke': isDark ? '2px white' : '2px black' }">
                  {{ loja.nome.split(' ').slice(1).join(' ') }}
                </span>
              </h1>

              <p v-if="loja.descricao" class="text-lg leading-relaxed mb-8 max-w-md"
                 :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
                {{ loja.descricao.substring(0, 150) }}{{ loja.descricao.length > 150 ? '...' : '' }}
              </p>

              <!-- Stats -->
              <div class="flex items-center gap-6 mb-8">
                <div v-if="loja.rating_medio" class="flex items-center gap-2">
                  <span class="text-4xl font-black" :style="{ color: 'var(--cor-primaria)' }">{{ loja.rating_medio }}</span>
                  <div class="flex flex-col">
                    <div class="flex gap-0.5">
                      <svg v-for="n in 5" :key="n" class="h-4 w-4" :style="{ color: n <= Math.round(loja.rating_medio) ? 'var(--cor-primaria)' : isDark ? '#3f3f46' : '#d4d4d8' }" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                    </div>
                    <span class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ loja.total_avaliacoes }} reviews</span>
                  </div>
                </div>
                <div v-if="loja.entrega_ativa" class="px-4 py-2 rounded-lg font-bold text-sm uppercase bg-emerald-500 text-white">
                  Free Shipping
                </div>
              </div>

              <!-- CTA -->
              <div class="flex items-center gap-4">
                <button @click="scrollToId('produtos')"
                  class="px-10 py-5 rounded-xl font-black uppercase tracking-wider transition-all hover:scale-105 hover:-rotate-1"
                  :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
                  Ver Colecao
                </button>
                <button @click="scrollToId('catalogo')"
                  class="px-10 py-5 rounded-xl font-black uppercase tracking-wider transition-all border-3 hover:scale-105 hover:rotate-1"
                  :class="isDark ? 'border-white text-white hover:bg-white hover:text-zinc-900' : 'border-zinc-900 text-zinc-900 hover:bg-zinc-900 hover:text-white'"
                  style="border-width: 3px;">
                  Catalogo
                </button>
              </div>
            </div>

            <!-- Right: Logo showcase -->
            <div class="relative flex justify-center lg:justify-end">
              <div class="relative">
                <!-- Rotating border -->
                <div class="absolute -inset-4 rounded-3xl animate-spin-slow" 
                     style="border: 4px dashed; animation-duration: 20s;"
                     :style="{ borderColor: 'var(--cor-primaria)' }"></div>
                
                <!-- Logo container -->
                <div class="relative w-72 h-72 md:w-96 md:h-96 rounded-3xl overflow-hidden rotate-3 hover:rotate-0 transition-transform duration-500"
                     :class="isDark ? 'bg-zinc-800' : 'bg-white shadow-2xl'">
                  <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full flex items-center justify-center"
                       :style="{ backgroundColor: 'var(--cor-primaria)' }">
                    <span class="text-9xl font-black text-white">{{ loja.nome.charAt(0) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Scroll down indicator -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center">
          <p class="text-xs font-bold uppercase tracking-widest mb-2" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Scroll</p>
          <div class="w-6 h-10 rounded-full border-2 flex items-start justify-center p-1"
               :class="isDark ? 'border-zinc-700' : 'border-zinc-300'">
            <div class="w-1.5 h-3 rounded-full animate-bounce" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
          </div>
        </div>
      </section>

      <!-- Marquee banner -->
      <div class="py-4 overflow-hidden" :style="{ backgroundColor: 'var(--cor-primaria)' }">
        <div class="flex items-center gap-8 animate-marquee whitespace-nowrap">
          <span v-for="n in 8" :key="n" class="text-white font-black uppercase tracking-wider flex items-center gap-8">
            <span>New Drop</span>
            <span class="w-3 h-3 bg-white rounded-full"></span>
            <span>Limited Edition</span>
            <span class="w-3 h-3 bg-white rounded-full"></span>
            <span>{{ loja.nome }}</span>
            <span class="w-3 h-3 bg-white rounded-full"></span>
          </span>
        </div>
      </div>

      <!-- Main content -->
      <main class="max-w-7xl mx-auto px-6">
        
        <!-- Featured - Bold section -->
        <section id="produtos" class="py-20">
          <div class="flex items-end justify-between mb-10">
            <div>
              <p class="font-bold uppercase tracking-widest text-sm mb-2" :style="{ color: 'var(--cor-primaria)' }">Hot Items</p>
              <h2 class="text-5xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">Destaques</h2>
            </div>
            <div class="hidden md:block">
              <span class="text-8xl font-black" :style="{ color: 'var(--cor-primaria)', opacity: 0.2 }">01</span>
            </div>
          </div>
          <ProductSlider title="Destaques" icon=""
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- By Type with bold headers -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id" 
                   class="py-16 border-t-4"
                   :style="{ borderColor: 'var(--cor-primaria)' }">
            <div class="flex items-end justify-between mb-10">
              <div class="flex items-center gap-6">
                <div class="w-16 h-16 rounded-xl flex items-center justify-center text-2xl"
                     :style="{ backgroundColor: 'var(--cor-primaria)' }">
                  {{ tipoIcon(tipo.nome) }}
                </div>
                <h2 class="text-4xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ tipo.nome }}</h2>
              </div>
              <span class="hidden md:block text-8xl font-black" :style="{ color: 'var(--cor-primaria)', opacity: 0.2 }">
                {{ String(idx + 2).padStart(2, '0') }}
              </span>
            </div>
            <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
              :params="{ loja_id: lojaId, tipo: tipo.nome }"
              :isDark="isDark" :show-title="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Categories - Card grid -->
        <template v-if="categoriasExistentes.length > 0">
          <section class="py-16">
            <p class="font-bold uppercase tracking-widest text-sm mb-2" :style="{ color: 'var(--cor-primaria)' }">Browse</p>
            <h2 class="text-5xl font-black uppercase mb-10" :class="isDark ? 'text-white' : 'text-zinc-900'">Categorias</h2>
            
            <!-- Category cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="p-6 rounded-2xl font-bold uppercase text-center transition-all hover:scale-105 hover:-rotate-1 border-2"
                :class="isDark ? 'bg-zinc-900 border-zinc-800 text-white hover:border-current' : 'bg-white border-zinc-200 text-zinc-900 hover:border-current'"
                :style="{ '--tw-border-opacity': 1 }">
                <span class="text-3xl block mb-2">{{ cat.icone }}</span>
                <span class="text-sm">{{ cat.nome }}</span>
              </button>
            </div>

            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
              <div class="flex items-center gap-4 mb-6">
                <span class="text-3xl">{{ cat.icone }}</span>
                <h3 class="text-2xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ cat.nome }}</h3>
                <div class="flex-1 h-1" :style="{ backgroundColor: 'var(--cor-primaria)', opacity: 0.3 }"></div>
              </div>
              <ProductSlider :title="cat.nome" :icon="cat.icone"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark" :show-title="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Full Catalog -->
        <section id="catalogo" class="py-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="mb-10">
            <p class="font-bold uppercase tracking-widest text-sm mb-2" :style="{ color: 'var(--cor-primaria)' }">Full Collection</p>
            <h2 class="text-5xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">Catalogo</h2>
          </div>
          <ProductCatalog :loja-id="lojaId" :isDark="isDark" @product-click="selectedProduct = $event" />
        </section>

        <!-- Info cards - Delivery & Payment -->
        <section class="py-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="rounded-3xl p-8 border-2"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <div class="w-14 h-14 rounded-xl flex items-center justify-center mb-4 text-2xl text-white"
                 :style="{ backgroundColor: 'var(--cor-primaria)' }">
              &#128666;
            </div>
            <h3 class="text-2xl font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">Shipping</h3>
            <div v-if="opcoesEntrega.length === 0" class="text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
              Sem opcoes configuradas.
            </div>
            <div v-else class="space-y-3">
              <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                   class="flex items-center justify-between py-2 border-b last:border-0"
                   :class="isDark ? 'border-zinc-800' : 'border-zinc-200'">
                <div>
                  <p class="font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ opcao.nome }}</p>
                  <p v-if="opcao.tempo_estimado" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ opcao.tempo_estimado }}</p>
                </div>
                <span class="font-black" :style="{ color: 'var(--cor-primaria)' }">
                  {{ opcao.preco == 0 ? 'FREE' : formatPrice(opcao.preco) }}
                </span>
              </div>
            </div>
          </div>

          <div class="rounded-3xl p-8 border-2"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <div class="w-14 h-14 rounded-xl flex items-center justify-center mb-4 text-2xl text-white"
                 :style="{ backgroundColor: 'var(--cor-primaria)' }">
              &#128179;
            </div>
            <h3 class="text-2xl font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">Payment</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="m in metodosPagamento" :key="m.id"
                    class="px-4 py-2 rounded-xl text-sm font-bold uppercase"
                    :class="isDark ? 'bg-zinc-800 text-white' : 'bg-zinc-100 text-zinc-900'">
                {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
              </span>
            </div>
          </div>
        </section>

        <!-- Reviews -->
        <section id="avaliacoes" class="py-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
          <p class="font-bold uppercase tracking-widest text-sm mb-2" :style="{ color: 'var(--cor-primaria)' }">Community</p>
          <h2 class="text-5xl font-black uppercase mb-10" :class="isDark ? 'text-white' : 'text-zinc-900'">Reviews</h2>
          <AvaliacaoLoja :loja-id="lojaId" :isDark="isDark" @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer -->
        <footer class="py-16 border-t-4 text-center" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-center justify-center gap-4 mb-6">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-16 h-16 rounded-xl object-cover" />
            <span class="font-black text-3xl uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.nome }}</span>
          </div>
          <div class="flex justify-center gap-8 text-sm font-bold uppercase mb-8"
               :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="hover:underline">Returns</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="hover:underline">Terms</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="hover:underline">Privacy</button>
          </div>
          <p class="text-xs" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
            {{ new Date().getFullYear() }} {{ loja.nome }}. Stay Bold.
          </p>
        </footer>
      </main>

      <!-- Modal politicas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-3xl w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl border-2"
             :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b-2 sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <h3 class="font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Returns' : modalPolitica === 'termos' ? 'Terms' : 'Privacy' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-10 h-10 rounded-xl flex items-center justify-center font-bold"
              :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
              X
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center">
      <p class="text-4xl font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">404</p>
      <p class="mb-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Loja nao encontrada</p>
      <button @click="$router.back()" class="font-bold uppercase hover:underline" :style="{ color: 'var(--cor-primaria)' }">Voltar</button>
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
  name: 'TemplateVibrante',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup(props) {
    const isDark = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()
    
    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#ec4899',
      '--cor-secundaria': props.tema?.corSecundaria || '#18181b',
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
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  animation: marquee 30s linear infinite;
}
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 20s linear infinite;
}
.stroke-text {
  -webkit-text-stroke: 2px currentColor;
}
</style>
