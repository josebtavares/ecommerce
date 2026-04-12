<!-- Template Moda Editorial — hero full-bleed, grid assimétrico, foco na imagem -->
<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-white text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <!-- Nav flutuante -->
    <nav class="fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-6 py-4
                bg-transparent transition-all duration-300"
         :class="scrolled ? (isDark ? 'bg-zinc-950/95 backdrop-blur-md shadow-lg' : 'bg-white/95 backdrop-blur-md shadow-sm') : ''">
      <button @click="$router.back()"
        class="w-9 h-9 rounded-full flex items-center justify-center transition"
        :class="isDark ? 'bg-white/10 hover:bg-white/20 text-white' : scrolled ? 'bg-gray-100 hover:bg-gray-200 text-zinc-700' : 'bg-black/20 hover:bg-black/30 text-white'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <p v-if="scrolled" class="font-bold tracking-widest uppercase text-sm"
         :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ loja?.nome }}</p>
      <button @click="toggleDark"
        class="w-9 h-9 rounded-full flex items-center justify-center transition"
        :class="isDark ? 'bg-white/10 hover:bg-white/20' : scrolled ? 'bg-gray-100 hover:bg-gray-200' : 'bg-black/20 hover:bg-black/30'">
        <span class="text-sm">{{ isDark ? '☀️' : '🌙' }}</span>
      </button>
    </nav>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin"
           :style="{ borderColor: 'var(--cor-primaria)', borderTopColor: 'transparent' }"></div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO EDITORIAL — split layout ── -->
      <section class="relative h-screen overflow-hidden">
        <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
             :alt="loja.nome" class="w-full h-full object-cover" />
        <div class="absolute inset-0"
             :class="isDark ? 'bg-black/50' : 'bg-black/30'" />

        <!-- Texto editorial vertical esquerdo -->
        <div class="absolute left-8 top-1/2 -translate-y-1/2 hidden md:block">
          <p class="text-white/60 text-xs tracking-[0.5em] uppercase writing-vertical">
            {{ loja.categoria }} · {{ new Date().getFullYear() }}
          </p>
        </div>

        <!-- Info centro/baixo -->
        <div class="absolute bottom-0 left-0 right-0 p-8 md:p-16">
          <div class="flex items-end justify-between max-w-7xl mx-auto">
            <div>
              <p class="text-white/60 text-sm tracking-widest uppercase mb-2">{{ loja.categoria }}</p>
              <h1 class="text-5xl md:text-8xl font-black text-white leading-none tracking-tighter">
                {{ loja.nome }}
              </h1>
              <p v-if="loja.localizacao" class="text-white/60 mt-3 text-sm tracking-widest">
                {{ loja.localizacao }}
              </p>
            </div>
            <div class="hidden md:flex flex-col items-end gap-3 text-right">
              <div v-if="loja.rating_medio" class="text-white">
                <p class="text-4xl font-black">{{ loja.rating_medio }}</p>
                <p class="text-white/50 text-xs">/ 5 estrelas</p>
              </div>
              <button @click="scrollToId('colecao')"
                class="px-6 py-3 font-bold text-sm tracking-wider uppercase transition"
                :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
                Ver Coleção →
              </button>
            </div>
          </div>
        </div>

        <!-- Scroll indicator -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white/40">
          <p class="text-[10px] tracking-widest uppercase">Scroll</p>
          <div class="w-px h-8 animate-pulse" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
        </div>
      </section>

      <main class="max-w-7xl mx-auto px-6">

        <!-- Sobre a marca - editorial strip -->
        <div id="colecao" class="py-16 grid grid-cols-1 md:grid-cols-2 gap-12 items-center border-b"
             :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
          <div>
            <p class="text-[10px] tracking-[0.4em] uppercase mb-4"
               :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Sobre nós</p>
            <p class="text-lg leading-relaxed" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
              {{ loja.descricao || 'Uma marca com identidade própria.' }}
            </p>
          </div>
          <div class="flex flex-col gap-4">
            <div v-if="opcoesEntrega.length" class="flex items-center gap-4">
              <span class="text-2xl">🚚</span>
              <div>
                <p class="font-bold text-sm" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">Entregas disponíveis</p>
                <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
                  {{ opcoesEntrega.find(o => o.preco == 0) ? 'Portes grátis disponíveis' : 'Consulta opções' }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <span class="text-2xl">💳</span>
              <div>
                <p class="font-bold text-sm" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">Pagamentos seguros</p>
                <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
                  {{ metodosPagamento.map(m => m.tipo).join(', ') || 'Vários métodos aceites' }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Sliders por categoria (editorial style) -->
        <div v-if="tiposExistentes.length > 0" class="py-12">
          <div v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id" class="mb-12">
            <div class="flex items-baseline gap-4 mb-6">
              <h2 class="text-3xl font-black capitalize tracking-tight"
                  :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ tipo.nome }}</h2>
              <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></div>
            </div>
            <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
              :params="{ loja_id: lojaId, tipo: tipo.nome }"
              :dark="isDark" :show-title="false"
              @product-click="selectedProduct = $event" />
          </div>
        </div>

        <div v-if="categoriasExistentes.length > 0" class="py-12 border-t"
             :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
          <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
            <div class="flex items-baseline gap-4 mb-6">
              <span class="text-2xl">{{ cat.icone }}</span>
              <h2 class="text-3xl font-black capitalize tracking-tight"
                  :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ cat.nome }}</h2>
              <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></div>
            </div>
            <ProductSlider :title="cat.nome" :icon="cat.icone"
              :params="{ loja_id: lojaId, categoria_id: cat.id }"
              :dark="isDark" :show-title="false"
              @product-click="selectedProduct = $event" />
          </div>
        </div>

        <!-- Catálogo completo -->
        <div id="catalogo" class="py-12 border-t" :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
          <div class="flex items-baseline gap-4 mb-8">
            <h2 class="text-3xl font-black tracking-tight" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Coleção completa</h2>
            <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></div>
          </div>
          <ProductCatalog :loja-id="lojaId" :dark="isDark" @product-click="selectedProduct = $event" />
        </div>

        <!-- Avaliações -->
        <div id="avaliacoes" class="py-12 border-t" :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
          <div class="flex items-baseline gap-4 mb-8">
            <h2 class="text-3xl font-black tracking-tight" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Reviews</h2>
            <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-gray-100'"></div>
          </div>
          <AvaliacaoLoja :loja-id="lojaId" @rating-updated="onRatingUpdated" />
        </div>

        <!-- Footer minimalista -->
        <footer class="py-8 border-t flex items-center justify-between text-xs"
                :class="isDark ? 'border-zinc-800 text-zinc-600' : 'border-gray-100 text-zinc-400'">
          <p>© {{ new Date().getFullYear() }} {{ loja.nome }}</p>
          <div class="flex gap-4">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
              class="hover:underline">Devoluções</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
              class="hover:underline">Termos</button>
          </div>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-2xl border w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-100'">
            <h3 class="font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Política de devoluções' : 'Termos de serviço' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-full flex items-center justify-center transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">✕</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : loja.termos_servico }}
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLojaData }   from '@/composables/useLojaData'
import ProductInfoCard   from '@/components/product/productInfoCard.vue'
import MultiCart         from '@/components/cart/multiCart.vue'
import ProductSlider     from '@/components/sliders/ProductSlider.vue'
import Profile           from '@/components/profile/UserProfile.vue'
import ProductCatalog    from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja     from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateModaEditorial',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props) {
    const isDark  = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()
    const cssVars  = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#18181b',
      '--cor-secundaria': props.tema?.corSecundaria || '#f4f4f5',
    }))
    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value }
    function onScroll () { scrolled.value = window.scrollY > 80 }
    onMounted (() => window.addEventListener('scroll', onScroll))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrolled, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>

<style scoped>
.writing-vertical { writing-mode: vertical-rl; text-orientation: mixed; transform: rotate(180deg); }
</style>
