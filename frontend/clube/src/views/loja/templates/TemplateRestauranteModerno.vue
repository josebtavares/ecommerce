<!-- Template Restaurante Moderno — hero escuro atmosférico, tabs por categoria, grid denso -->
<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-50 text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <button @click="toggleDark"
      class="fixed top-4 right-16 z-40 w-9 h-9 rounded-full flex items-center justify-center transition shadow-lg"
      :class="isDark ? 'bg-zinc-800 text-yellow-400' : 'bg-white text-zinc-700 shadow'">
      <span class="text-sm">{{ isDark ? '☀️' : '🌙' }}</span>
    </button>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <svg class="animate-spin h-10 w-10" :style="{ color: 'var(--cor-primaria)' }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO FULLSCREEN com overlay forte ── -->
      <section class="relative h-[70vh] overflow-hidden">
        <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
             :alt="loja.nome" class="w-full h-full object-cover scale-105" />
        <!-- Overlay gradiente mais escuro para dar ambiente -->
        <div class="absolute inset-0" style="background: linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.5) 50%, rgba(0,0,0,0.2) 100%)"/>

        <button @click="$router.back()"
          class="absolute top-5 left-5 w-9 h-9 rounded-full bg-white/10 hover:bg-white/20
                 flex items-center justify-center transition backdrop-blur-sm border border-white/20">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <!-- Conteúdo hero centrado -->
        <div class="absolute bottom-0 left-0 right-0 p-8 md:p-12 text-center">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-20 h-20 rounded-2xl object-cover mx-auto mb-4 border-2 border-white/20 shadow-2xl" />
          <h1 class="text-4xl md:text-6xl font-black text-white mb-2 tracking-tight">{{ loja.nome }}</h1>
          <p class="text-zinc-300 text-lg mb-4 max-w-xl mx-auto">{{ loja.descricao }}</p>
          <div class="flex items-center justify-center gap-6 text-sm text-zinc-300 flex-wrap">
            <span v-if="loja.localizacao">📍 {{ loja.localizacao }}</span>
            <span v-if="loja.rating_medio">⭐ {{ loja.rating_medio }} ({{ loja.total_avaliacoes }})</span>
            <span v-if="loja.entrega_ativa" class="text-green-400 font-semibold">✓ Entrega disponível</span>
          </div>
          <!-- CTA botões -->
          <div class="flex items-center justify-center gap-3 mt-6">
            <button @click="scrollToId('menu')"
              class="px-6 py-3 rounded-xl font-bold text-white transition"
              :style="{ backgroundColor: 'var(--cor-primaria)' }">
              Ver Menu
            </button>
            <button @click="scrollToId('catalogo')"
              class="px-6 py-3 rounded-xl font-bold border border-white/30 text-white hover:bg-white/10 transition">
              Catálogo completo
            </button>
          </div>
        </div>
      </section>

      <!-- ── TABS DE CATEGORIAS FIXAS ── -->
      <div id="menu" class="sticky top-0 z-20 border-b"
           :class="isDark ? 'bg-zinc-950/95 border-zinc-800 backdrop-blur-md' : 'bg-stone-50/95 border-stone-200 backdrop-blur-md'">
        <div class="max-w-5xl mx-auto px-4">
          <div class="flex gap-1 overflow-x-auto scrollbar-hide py-3">
            <button @click="tabActiva = null"
              :class="['px-4 py-2 rounded-lg text-sm font-semibold transition whitespace-nowrap flex-shrink-0',
                       tabActiva === null
                         ? 'text-white'
                         : isDark ? 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800' : 'text-zinc-600 hover:bg-stone-200']"
              :style="tabActiva === null ? { backgroundColor: 'var(--cor-primaria)' } : {}">
              ✨ Destaques
            </button>
            <button v-for="cat in categoriasExistentes" :key="cat.id"
              @click="tabActiva = cat; scrollToId('cat-' + cat.id)"
              :class="['px-4 py-2 rounded-lg text-sm font-semibold transition whitespace-nowrap flex-shrink-0 capitalize',
                       tabActiva?.id === cat.id
                         ? 'text-white'
                         : isDark ? 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800' : 'text-zinc-600 hover:bg-stone-200']"
              :style="tabActiva?.id === cat.id ? { backgroundColor: 'var(--cor-primaria)' } : {}">
              {{ cat.icone }} {{ cat.nome }}
            </button>
          </div>
        </div>
      </div>

      <main class="max-w-5xl mx-auto px-4 py-8">

        <!-- Destaque slider -->
        <ProductSlider title="Em Destaque" icon="⭐"
          :params="{ loja_id: lojaId, destaque: true }"
          :dark="isDark"
          @product-click="selectedProduct = $event" />

        <!-- Sections por CATEGORIA (layout card de menu) -->
        <template v-if="categoriasExistentes.length > 0">
          <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mt-10">
            <div class="flex items-center gap-3 mb-5">
              <span class="text-2xl">{{ cat.icone }}</span>
              <h2 class="text-2xl font-black capitalize" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ cat.nome }}</h2>
              <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
            </div>
            <ProductSlider :title="cat.nome" :icon="cat.icone"
              :params="{ loja_id: lojaId, categoria_id: cat.id }"
              :dark="isDark"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Catálogo -->
        <div id="catalogo" class="mt-12 mb-4">
          <h2 class="text-2xl font-black" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Menu completo</h2>
          <p class="text-sm mt-1" :class="isDark ? 'text-zinc-500' : 'text-stone-500'">Pesquisa qualquer prato ou bebida</p>
        </div>
        <ProductCatalog :loja-id="lojaId" :dark="isDark" @product-click="selectedProduct = $event" />

        <!-- Entrega + Pagamento -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
          <div class="rounded-2xl p-5 border"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200 shadow-sm'">
            <h3 class="font-bold mb-3 flex items-center gap-2" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">
              🛵 Entrega
            </h3>
            <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                 class="flex items-center justify-between py-2 border-b last:border-0 text-sm"
                 :class="isDark ? 'border-zinc-800' : 'border-stone-100'">
              <span :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">{{ opcao.nome }}</span>
              <span class="font-bold" :style="{ color: 'var(--cor-primaria)' }">
                {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
              </span>
            </div>
          </div>
          <div class="rounded-2xl p-5 border"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200 shadow-sm'">
            <h3 class="font-bold mb-3" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">💳 Pagamento aceite</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="m in metodosPagamento" :key="m.id"
                    class="px-3 py-1.5 rounded-lg text-sm capitalize"
                    :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-stone-100 text-zinc-600'">
                {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
              </span>
            </div>
          </div>
        </div>

        <!-- Avaliações -->
        <div id="avaliacoes" class="mt-12">
          <h2 class="text-2xl font-black mb-5" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">O que dizem os clientes</h2>
          <AvaliacaoLoja :loja-id="lojaId" @rating-updated="onRatingUpdated" />
        </div>
      </main>
    </template>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useLojaData }   from '@/composables/useLojaData'
import ProductInfoCard   from '@/components/product/productInfoCard.vue'
import MultiCart         from '@/components/cart/multiCart.vue'
import ProductSlider     from '@/components/sliders/ProductSlider.vue'
import Profile           from '@/components/profile/UserProfile.vue'
import ProductCatalog    from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja     from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateRestauranteModerno',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props) {
    const isDark     = ref(props.tema?.darkMode !== false)
    const tabActiva  = ref(null)
    const lojaData   = useLojaData()
    const cssVars    = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#e11d48',
      '--cor-secundaria': props.tema?.corSecundaria || '#0f0f0f',
    }))
    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
    function toggleDark () { isDark.value = !isDark.value }
    return { isDark, tabActiva, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>
