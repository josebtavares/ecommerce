<!-- TemplateRestauranteBistro — Acolhedor, rustico, tons quentes, estilo cafe parisiense -->
<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-amber-950 text-amber-50' : 'bg-amber-50 text-amber-950'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="w-12 h-12 border-4 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <template v-else-if="loja">
      <!-- HERO Bistro - Warm and inviting -->
      <section class="relative h-[70vh] min-h-[500px] overflow-hidden">
        <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
             :alt="loja.nome" class="w-full h-full object-cover" />
        <!-- Warm overlay -->
        <div class="absolute inset-0 bg-gradient-to-t from-amber-950 via-amber-950/60 to-amber-900/30"></div>
        
        <!-- Decorative frame corners -->
        <div class="absolute top-8 left-8 w-24 h-24 border-l-2 border-t-2 border-amber-400/40"></div>
        <div class="absolute top-8 right-8 w-24 h-24 border-r-2 border-t-2 border-amber-400/40"></div>
        <div class="absolute bottom-8 left-8 w-24 h-24 border-l-2 border-b-2 border-amber-400/40"></div>
        <div class="absolute bottom-8 right-8 w-24 h-24 border-r-2 border-b-2 border-amber-400/40"></div>

        <!-- Navigation -->
        <div class="absolute top-0 left-0 right-0 p-6 flex items-center justify-between z-10">
          <button @click="$router.back()"
            class="w-11 h-11 rounded-full bg-amber-900/60 hover:bg-amber-800/80 backdrop-blur-sm flex items-center justify-center transition border border-amber-600/30">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button @click="toggleDark"
            class="w-11 h-11 rounded-full bg-amber-900/60 hover:bg-amber-800/80 backdrop-blur-sm flex items-center justify-center transition border border-amber-600/30">
            <span class="text-lg">{{ isDark ? '&#9728;' : '&#9790;' }}</span>
          </button>
        </div>

        <!-- Hero content -->
        <div class="absolute bottom-0 left-0 right-0 text-center pb-16 px-6">
          <!-- Logo -->
          <div class="inline-flex items-center justify-center mb-6">
            <div class="w-px h-8 bg-amber-400/50"></div>
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" 
                 class="w-24 h-24 rounded-full object-cover mx-6 border-4 border-amber-400/30 shadow-2xl" />
            <div v-else class="w-24 h-24 rounded-full mx-6 border-4 border-amber-400/30 flex items-center justify-center"
                 :style="{ backgroundColor: 'var(--cor-primaria)' }">
              <span class="text-3xl font-bold text-white">{{ loja.nome.charAt(0) }}</span>
            </div>
            <div class="w-px h-8 bg-amber-400/50"></div>
          </div>

          <p class="text-amber-300 text-sm uppercase tracking-[0.4em] mb-3">{{ loja.categoria }}</p>
          <h1 class="text-5xl md:text-7xl font-bold text-amber-50 mb-4 bistro-title">{{ loja.nome }}</h1>
          
          <div class="flex items-center justify-center gap-6 text-amber-200 text-sm flex-wrap">
            <span v-if="loja.localizacao" class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {{ loja.localizacao }}
            </span>
            <span v-if="loja.rating_medio" class="flex items-center gap-1">
              <svg class="h-4 w-4 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {{ loja.rating_medio }}
            </span>
            <span v-if="loja.entrega_ativa" class="text-emerald-400">Entrega disponivel</span>
          </div>

          <!-- Menu button -->
          <button @click="scrollToId('menu')"
            class="mt-8 px-10 py-4 rounded-full font-semibold text-amber-950 transition-all hover:scale-105 shadow-xl"
            :style="{ backgroundColor: 'var(--cor-primaria)' }">
            Ver Menu
          </button>
        </div>
      </section>

      <!-- Decorative banner -->
      <div class="py-4 text-center overflow-hidden" :style="{ backgroundColor: 'var(--cor-primaria)' }">
        <div class="flex items-center justify-center gap-8 animate-marquee whitespace-nowrap">
          <span v-for="n in 6" :key="n" class="text-amber-950 font-medium flex items-center gap-4">
            <span class="w-2 h-2 rounded-full bg-amber-950/30"></span>
            Feito com amor
            <span class="w-2 h-2 rounded-full bg-amber-950/30"></span>
            Ingredientes frescos
          </span>
        </div>
      </div>

      <!-- Main content -->
      <main class="max-w-5xl mx-auto px-6">
        
        <!-- About the bistro -->
        <section class="py-16">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <div class="inline-block px-4 py-1 rounded-full text-xs uppercase tracking-wider mb-4"
                   :class="isDark ? 'bg-amber-900/50 text-amber-300' : 'bg-amber-200 text-amber-800'">
                A Nossa Historia
              </div>
              <h2 class="text-3xl font-bold mb-4" :class="isDark ? 'text-amber-100' : 'text-amber-900'">
                Bem-vindo ao {{ loja.nome }}
              </h2>
              <p class="leading-relaxed" :class="isDark ? 'text-amber-200/80' : 'text-amber-800'">
                {{ loja.descricao || 'Um espaco acolhedor onde cada refeicao e uma experiencia. Servimos pratos preparados com ingredientes frescos e muito carinho.' }}
              </p>
            </div>
            
            <!-- Info cards -->
            <div class="grid grid-cols-2 gap-4">
              <div class="rounded-2xl p-5 text-center" :class="isDark ? 'bg-amber-900/40' : 'bg-amber-100'">
                <div class="text-3xl mb-2">&#127869;</div>
                <p class="font-bold text-lg" :class="isDark ? 'text-amber-100' : 'text-amber-900'">Menu</p>
                <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">Variedade de pratos</p>
              </div>
              <div v-if="loja.entrega_ativa" class="rounded-2xl p-5 text-center" :class="isDark ? 'bg-amber-900/40' : 'bg-amber-100'">
                <div class="text-3xl mb-2">&#128690;</div>
                <p class="font-bold text-lg" :class="isDark ? 'text-amber-100' : 'text-amber-900'">Entrega</p>
                <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">Rapida e segura</p>
              </div>
              <div v-if="loja.rating_medio" class="rounded-2xl p-5 text-center" :class="isDark ? 'bg-amber-900/40' : 'bg-amber-100'">
                <div class="text-3xl mb-2">&#11088;</div>
                <p class="font-bold text-lg" :class="isDark ? 'text-amber-100' : 'text-amber-900'">{{ loja.rating_medio }}</p>
                <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">{{ loja.total_avaliacoes }} avaliacoes</p>
              </div>
              <div v-if="metodosPagamento.length" class="rounded-2xl p-5 text-center" :class="isDark ? 'bg-amber-900/40' : 'bg-amber-100'">
                <div class="text-3xl mb-2">&#128179;</div>
                <p class="font-bold text-lg" :class="isDark ? 'text-amber-100' : 'text-amber-900'">Pagamento</p>
                <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">{{ metodosPagamento.length }} metodos</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Menu sections -->
        <section id="menu" class="py-8">
          <!-- Featured -->
          <div class="mb-12">
            <div class="flex items-center gap-4 mb-8">
              <div class="w-12 h-12 rounded-full flex items-center justify-center" :style="{ backgroundColor: 'var(--cor-primaria)' }">
                <span class="text-xl text-amber-950">&#9733;</span>
              </div>
              <div>
                <h2 class="text-2xl font-bold" :class="isDark ? 'text-amber-100' : 'text-amber-900'">Especialidades da Casa</h2>
                <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">Os favoritos dos nossos clientes</p>
              </div>
            </div>
            <ProductSlider title="Destaques" icon=""
              :params="{ loja_id: lojaId, destaque: true }"
              :isDark="isDark"
              @product-click="selectedProduct = $event" />
          </div>

          <!-- By Type -->
          <template v-if="tiposExistentes.length > 0">
            <div v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id" class="mb-12">
              <div class="flex items-center gap-4 mb-8">
                <div class="w-12 h-12 rounded-full flex items-center justify-center"
                     :class="isDark ? 'bg-amber-800' : 'bg-amber-200'">
                  <span class="text-xl">{{ tipoIcon(tipo.nome) }}</span>
                </div>
                <div>
                  <h2 class="text-2xl font-bold capitalize" :class="isDark ? 'text-amber-100' : 'text-amber-900'">{{ tipo.nome }}</h2>
                </div>
              </div>
              <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark" :show-title="false"
                @product-click="selectedProduct = $event" />
            </div>
          </template>

          <!-- By Category -->
          <template v-if="categoriasExistentes.length > 0">
            <!-- Category tabs -->
            <div class="flex items-center gap-3 overflow-x-auto py-4 mb-8 scrollbar-hide">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-5 py-2.5 rounded-full font-medium whitespace-nowrap transition-all flex items-center gap-2"
                :class="isDark ? 'bg-amber-900/50 text-amber-200 hover:bg-amber-800' : 'bg-amber-200 text-amber-800 hover:bg-amber-300'">
                {{ cat.icone }} {{ cat.nome }}
              </button>
            </div>

            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
              <div class="flex items-center gap-4 mb-6">
                <span class="text-3xl">{{ cat.icone }}</span>
                <h3 class="text-xl font-bold capitalize" :class="isDark ? 'text-amber-100' : 'text-amber-900'">{{ cat.nome }}</h3>
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800' : 'bg-amber-300'"></div>
              </div>
              <ProductSlider :title="cat.nome" :icon="cat.icone"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark" :show-title="false"
                @product-click="selectedProduct = $event" />
            </div>
          </template>
        </section>

        <!-- Full catalog -->
        <section id="catalogo" class="py-12">
          <div class="text-center mb-10">
            <h2 class="text-3xl font-bold mb-2" :class="isDark ? 'text-amber-100' : 'text-amber-900'">Menu Completo</h2>
            <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">Pesquisa e filtra o que desejas</p>
          </div>
          <ProductCatalog :loja-id="lojaId" :isDark="isDark" @product-click="selectedProduct = $event" />
        </section>

        <!-- Delivery & Payment -->
        <section class="py-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="rounded-2xl p-6 border" :class="isDark ? 'bg-amber-900/30 border-amber-800' : 'bg-amber-100 border-amber-200'">
            <h3 class="font-bold text-lg mb-4 flex items-center gap-2" :class="isDark ? 'text-amber-100' : 'text-amber-900'">
              <span class="text-2xl">&#128666;</span> Opcoes de Entrega
            </h3>
            <div v-if="opcoesEntrega.length === 0" class="text-sm" :class="isDark ? 'text-amber-400' : 'text-amber-700'">
              Sem opcoes configuradas.
            </div>
            <div v-else class="space-y-3">
              <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                   class="flex items-center justify-between py-2 border-b last:border-0"
                   :class="isDark ? 'border-amber-800' : 'border-amber-200'">
                <div>
                  <p class="font-medium" :class="isDark ? 'text-amber-100' : 'text-amber-900'">{{ opcao.nome }}</p>
                  <p v-if="opcao.tempo_estimado" class="text-xs" :class="isDark ? 'text-amber-400' : 'text-amber-600'">{{ opcao.tempo_estimado }}</p>
                </div>
                <span class="font-bold" :style="{ color: 'var(--cor-primaria)' }">
                  {{ opcao.preco == 0 ? 'Gratis' : formatPrice(opcao.preco) }}
                </span>
              </div>
            </div>
          </div>

          <div class="rounded-2xl p-6 border" :class="isDark ? 'bg-amber-900/30 border-amber-800' : 'bg-amber-100 border-amber-200'">
            <h3 class="font-bold text-lg mb-4 flex items-center gap-2" :class="isDark ? 'text-amber-100' : 'text-amber-900'">
              <span class="text-2xl">&#128179;</span> Formas de Pagamento
            </h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="m in metodosPagamento" :key="m.id"
                    class="px-4 py-2 rounded-full text-sm font-medium"
                    :class="isDark ? 'bg-amber-800 text-amber-200' : 'bg-amber-200 text-amber-800'">
                {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
              </span>
            </div>
          </div>
        </section>

        <!-- Reviews -->
        <section id="avaliacoes" class="py-12">
          <div class="text-center mb-10">
            <h2 class="text-3xl font-bold mb-2" :class="isDark ? 'text-amber-100' : 'text-amber-900'">O Que Dizem de Nos</h2>
            <p class="text-sm" :class="isDark ? 'text-amber-300' : 'text-amber-700'">Avaliacoes dos nossos clientes</p>
          </div>
          <AvaliacaoLoja :loja-id="lojaId" :isDark="isDark" @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer -->
        <footer class="py-10 border-t text-center" :class="isDark ? 'border-amber-800' : 'border-amber-200'">
          <div class="flex items-center justify-center gap-3 mb-4">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-10 h-10 rounded-full object-cover" />
            <span class="font-bold text-xl" :class="isDark ? 'text-amber-100' : 'text-amber-900'">{{ loja.nome }}</span>
          </div>
          <div class="flex justify-center gap-6 text-sm mb-6" :class="isDark ? 'text-amber-400' : 'text-amber-600'">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="hover:underline">Devolucoes</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="hover:underline">Termos</button>
          </div>
          <p class="text-xs" :class="isDark ? 'text-amber-600' : 'text-amber-400'">
            {{ new Date().getFullYear() }} {{ loja.nome }}. Bom apetite!
          </p>
        </footer>
      </main>

      <!-- Modal politicas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-amber-900 border border-amber-800' : 'bg-amber-50 border border-amber-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-amber-900 border-amber-800' : 'bg-amber-50 border-amber-200'">
            <h3 class="font-bold" :class="isDark ? 'text-amber-100' : 'text-amber-900'">
              {{ modalPolitica === 'devolucao' ? 'Politica de Devolucoes' : 'Termos de Servico' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="isDark ? 'bg-amber-800 hover:bg-amber-700' : 'bg-amber-200 hover:bg-amber-300'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-amber-200' : 'text-amber-800'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : loja.termos_servico }}
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-amber-950' : 'bg-amber-50'">
      <p class="text-2xl font-bold mb-4" :class="isDark ? 'text-amber-400' : 'text-amber-700'">Bistro nao encontrado</p>
      <button @click="$router.back()" class="hover:underline" :style="{ color: 'var(--cor-primaria)' }">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateRestauranteBistro',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup(props) {
    const isDark = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()
    
    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#f59e0b',
      '--cor-secundaria': props.tema?.corSecundaria || '#451a03',
    }))
    
    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark() { isDark.value = !isDark.value }

    return { isDark, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>

<style scoped>
.bistro-title {
  font-family: 'Georgia', serif;
}
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  animation: marquee 20s linear infinite;
}
</style>
