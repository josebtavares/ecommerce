<!-- TemplateModaBoutique — Elegante, sofisticado, tipografia serif, cores neutras premium -->
<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-neutral-950 text-neutral-100' : 'bg-stone-50 text-neutral-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-50" @log_out="logOut()" />

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="w-12 h-12 border-2 rounded-full animate-spin"
           :style="{ borderColor: 'var(--cor-primaria)', borderTopColor: 'transparent' }"></div>
    </div>

    <template v-else-if="loja">
      <!-- HERO Boutique - Split asymmetric com padding-top para nao sobrepor header fixo -->
      <section class="relative min-h-screen overflow-hidden pt-20">
        <div class="absolute inset-0">
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome" class="w-full h-full object-cover" />
          <div class="absolute inset-0" :class="isDark ? 'bg-neutral-950/60' : 'bg-stone-900/40'"></div>
        </div>

        <!-- Botoes de navegacao -->
        <div class="absolute top-24 left-6 z-20 flex items-center gap-3">
          <button @click="$router.back()"
            class="w-10 h-10 rounded-full flex items-center justify-center bg-white/20 hover:bg-white/30 backdrop-blur-sm transition-all duration-300">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button @click="toggleDark"
            class="w-10 h-10 rounded-full flex items-center justify-center bg-white/20 hover:bg-white/30 backdrop-blur-sm transition-all duration-300">
            <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21.64 13.02A9 9 0 1 1 10.98 2.36 7 7 0 0 0 21.64 13.02Z" />
            </svg>
          </button>
        </div>

        <!-- Content overlay -->
        <div class="relative min-h-screen flex items-end">
          <div class="w-full max-w-7xl mx-auto px-6 pb-16 pt-32">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-end">
              <!-- Left: Brand info -->
              <div>
                <p class="font-serif italic text-lg mb-4" :class="isDark ? 'text-neutral-400' : 'text-white/70'">
                  {{ loja.categoria }}
                </p>
                <h1 class="font-serif text-5xl md:text-7xl lg:text-8xl font-light tracking-tight text-white leading-none mb-6">
                  {{ loja.nome }}
                </h1>
                <p v-if="loja.descricao" class="text-lg leading-relaxed max-w-md text-white/80">
                  {{ loja.descricao.substring(0, 150) }}{{ loja.descricao.length > 150 ? '...' : '' }}
                </p>
                <div class="flex items-center gap-6 mt-8">
                  <button @click="scrollToId('colecao')"
                    class="px-8 py-4 font-medium tracking-widest text-sm uppercase transition-all duration-300 hover:scale-105"
                    :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
                    Ver Colecao
                  </button>
                  <button v-if="loja.rating_medio" @click="scrollToId('avaliacoes')"
                    class="flex items-center gap-2 text-white/80 hover:text-white transition group">
                    <span class="text-3xl font-serif">{{ loja.rating_medio }}</span>
                    <div class="flex flex-col">
                      <div class="flex gap-0.5">
                        <svg v-for="n in 5" :key="n" :class="['h-3 w-3', n <= Math.round(loja.rating_medio) ? 'text-amber-400' : 'text-white/30']" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                      </div>
                      <span class="text-xs text-white/50">{{ loja.total_avaliacoes }} reviews</span>
                    </div>
                  </button>
                </div>
              </div>

              <!-- Right: Quick info cards -->
              <div class="hidden lg:flex flex-col gap-4">
                <div v-if="loja.localizacao" class="bg-white/10 backdrop-blur-md rounded-2xl p-5 border border-white/10">
                  <p class="text-white/50 text-xs uppercase tracking-wider mb-1">Localizacao</p>
                  <p class="text-white font-medium">{{ loja.localizacao }}</p>
                </div>
                <div v-if="loja.entrega_ativa" class="bg-white/10 backdrop-blur-md rounded-2xl p-5 border border-white/10">
                  <p class="text-white/50 text-xs uppercase tracking-wider mb-1">Entrega</p>
                  <p class="text-emerald-400 font-medium">Disponivel</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Scroll indicator -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
          <div class="w-px h-16 bg-gradient-to-b from-transparent via-white/50 to-white/20 animate-pulse"></div>
        </div>
      </section>

      <!-- Main content -->
      <main class="max-w-7xl mx-auto px-6">
        
        <!-- About section - Elegant typography -->
        <section id="colecao" class="py-20 border-b" :class="isDark ? 'border-neutral-800' : 'border-stone-200'">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-12">
            <div class="lg:col-span-2">
              <p class="text-xs uppercase tracking-[0.3em] mb-4" :style="{ color: 'var(--cor-primaria)' }">Sobre a marca</p>
              <p class="font-serif text-2xl md:text-3xl leading-relaxed" :class="isDark ? 'text-neutral-200' : 'text-neutral-800'">
                {{ loja.descricao || 'Uma boutique com curadoria cuidada e pecas unicas.' }}
              </p>
            </div>
            <div class="flex flex-col gap-6">
              <div v-if="metodosPagamento.length">
                <p class="text-xs uppercase tracking-wider mb-3" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Pagamento</p>
                <div class="flex flex-wrap gap-2">
                  <span v-for="m in metodosPagamento" :key="m.id"
                    class="px-3 py-1.5 rounded-full text-xs font-medium"
                    :class="isDark ? 'bg-neutral-800 text-neutral-300' : 'bg-stone-200 text-neutral-700'">
                    {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
                  </span>
                </div>
              </div>
              <div v-if="opcoesEntrega.length">
                <p class="text-xs uppercase tracking-wider mb-3" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">Envio</p>
                <div class="flex flex-col gap-2">
                  <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="flex items-center justify-between">
                    <span class="text-sm" :class="isDark ? 'text-neutral-300' : 'text-neutral-600'">{{ opcao.nome }}</span>
                    <span class="font-medium" :style="{ color: 'var(--cor-primaria)' }">
                      {{ opcao.preco == 0 ? 'Gratis' : formatPrice(opcao.preco) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Featured slider - Boutique style cards -->
        <section class="py-16">
          <ProductSlider 
            title="Destaques"
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            card-width="220px"
            image-height="280px"
            card-height="380px"
            card-border-radius="rounded-none"
            hover-effect="hover:shadow-2xl"
            hover-border-class="hover:border-amber-500/50"
            title-size="text-xl"
            title-class="font-serif tracking-wide"
            product-name-class="font-serif"
            price-class="text-amber-600"
            badge-class="bg-amber-600"
            :show-stock="false"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Collections by Type - Magazine layout -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
            class="py-16 border-t" :class="isDark ? 'border-neutral-800' : 'border-stone-200'">
            <div class="flex items-end justify-between mb-10">
              <div>
                <p class="text-xs uppercase tracking-[0.3em] mb-2" :style="{ color: 'var(--cor-primaria)' }">Colecao {{ idx + 1 }}</p>
                <h2 class="font-serif text-4xl md:text-5xl capitalize" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">
                  {{ tipo.nome }}
                </h2>
              </div>
              <span class="text-6xl font-serif" :class="isDark ? 'text-neutral-800' : 'text-stone-200'">
                {{ String(idx + 1).padStart(2, '0') }}
              </span>
            </div>
            <ProductSlider 
              :title="tipo.nome"
              :params="{ loja_id: lojaId, tipo: tipo.nome }"
              :isDark="isDark"
              card-width="200px"
              image-height="260px"
              card-height="360px"
              card-border-radius="rounded-none"
              hover-effect="hover:shadow-2xl"
              hover-border-class="hover:border-amber-500/50"
              title-class="font-serif"
              product-name-class="font-serif"
              price-class="text-amber-600"
              :show-stock="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Categories grid -->
        <template v-if="categoriasExistentes.length > 0">
          <section class="py-16 border-t" :class="isDark ? 'border-neutral-800' : 'border-stone-200'">
            <p class="text-xs uppercase tracking-[0.3em] mb-2" :style="{ color: 'var(--cor-primaria)' }">Explorar</p>
            <h2 class="font-serif text-4xl mb-12" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">Por Categoria</h2>
            
            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
              <div class="flex items-center gap-4 mb-6">
                <span class="text-2xl">{{ cat.icone }}</span>
                <h3 class="font-serif text-2xl capitalize" :class="isDark ? 'text-neutral-200' : 'text-neutral-800'">{{ cat.nome }}</h3>
                <div class="flex-1 h-px" :class="isDark ? 'bg-neutral-800' : 'bg-stone-200'"></div>
              </div>
              <ProductSlider 
                :title="cat.nome"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark"
                card-width="180px"
                image-height="240px"
                card-height="340px"
                card-border-radius="rounded-none"
                hover-border-class="hover:border-amber-500/50"
                product-name-class="font-serif"
                price-class="text-amber-600"
                :show-stock="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Full Catalog - Boutique style -->
        <section id="catalogo" class="py-16 border-t" :class="isDark ? 'border-neutral-800' : 'border-stone-200'">
          <div class="flex items-end justify-between mb-10">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] mb-2" :style="{ color: 'var(--cor-primaria)' }">Catalogo</p>
              <h2 class="font-serif text-4xl" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">Todas as Pecas</h2>
            </div>
          </div>
          <ProductCatalog 
            :loja-id="lojaId" 
            :isDark="isDark"
            grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
            image-height="220px"
            card-border-radius="rounded-none"
            hover-effect="hover:shadow-2xl"
            hover-border-class="hover:border-amber-500/50"
            tab-border-radius="rounded-none"
            active-tab-class="bg-amber-600 text-white"
            input-border-radius="rounded-none"
            input-focus-class="focus:border-amber-500"
            filter-container-radius="rounded-none"
            product-name-hover-class="group-hover:text-amber-600"
            price-class="text-amber-600"
            spinner-class="text-amber-600"
            clear-all-class="text-amber-600 hover:text-amber-500"
            :show-stock="false"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Reviews - Elegant style -->
        <section id="avaliacoes" class="py-16 border-t" :class="isDark ? 'border-neutral-800' : 'border-stone-200'">
          <p class="text-xs uppercase tracking-[0.3em] mb-2" :style="{ color: 'var(--cor-primaria)' }">Feedback</p>
          <h2 class="font-serif text-4xl mb-10" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">O Que Dizem</h2>
          <AvaliacaoLoja 
            :loja-id="lojaId" 
            :isDark="isDark"
            summary-border-radius="rounded-none"
            form-border-radius="rounded-none"
            review-card-border-radius="rounded-none"
            button-border-radius="rounded-none"
            textarea-border-radius="rounded-none"
            star-active-class="text-amber-500"
            progress-bar-class="bg-amber-500"
            submit-button-class="bg-amber-600 hover:bg-amber-500 text-white"
            own-review-border-class="bg-neutral-900 border border-amber-500/40"
            own-badge-class="bg-amber-500/20 text-amber-400"
            link-class="text-amber-500 hover:text-amber-400"
            @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer elegante -->
        <footer class="py-12 border-t" :class="isDark ? 'border-neutral-800' : 'border-stone-200'">
          <div class="flex flex-col md:flex-row items-center justify-between gap-6">
            <div class="flex items-center gap-4">
              <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-12 h-12 rounded-full object-cover" />
              <div>
                <p class="font-serif text-xl" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">{{ loja.nome }}</p>
                <p class="text-sm" :class="isDark ? 'text-neutral-500' : 'text-neutral-400'">{{ loja.categoria }}</p>
              </div>
            </div>
            <div class="flex gap-6 text-sm" :class="isDark ? 'text-neutral-400' : 'text-neutral-500'">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="hover:underline">Devolucoes</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="hover:underline">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="hover:underline">Privacidade</button>
            </div>
          </div>
          <p class="text-center text-xs mt-8" :class="isDark ? 'text-neutral-600' : 'text-neutral-400'">
            {{ new Date().getFullYear() }} {{ loja.nome }}. Todos os direitos reservados.
          </p>
        </footer>
      </main>

      <!-- Modal politicas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-neutral-900 border border-neutral-800' : 'bg-white'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-neutral-900 border-neutral-800' : 'bg-white border-stone-100'">
            <h3 class="font-serif text-lg" :class="isDark ? 'text-neutral-100' : 'text-neutral-900'">
              {{ modalPolitica === 'devolucao' ? 'Politica de Devolucoes' : modalPolitica === 'termos' ? 'Termos de Servico' : 'Politica de Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 flex items-center justify-center transition"
              :class="isDark ? 'bg-neutral-800 hover:bg-neutral-700' : 'bg-stone-100 hover:bg-stone-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-neutral-400' : 'text-neutral-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-neutral-300' : 'text-neutral-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center pt-20">
      <p class="font-serif text-2xl mb-4" :class="isDark ? 'text-neutral-400' : 'text-neutral-600'">Boutique nao encontrada</p>
      <button @click="$router.back()" class="text-sm hover:underline" :style="{ color: 'var(--cor-primaria)' }">Voltar</button>
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
  name: 'TemplateModaBoutique',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup(props) {
    const isDark = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()
    
    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#b8860b',
      '--cor-secundaria': props.tema?.corSecundaria || '#1c1c1e',
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
.font-serif {
  font-family: 'Playfair Display', 'Georgia', serif;
}
</style>
