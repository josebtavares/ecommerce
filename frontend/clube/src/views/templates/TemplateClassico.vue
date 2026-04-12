<!-- Template Clássico — dark mode, layout equilibrado, funciona para qualquer loja -->
<template>
  <div class="min-h-screen text-zinc-100 transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950' : 'bg-gray-50 text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <!-- Toggle dark/light -->
    <button @click="toggleDark"
      class="fixed top-4 right-16 z-40 w-9 h-9 rounded-full flex items-center justify-center transition shadow-lg"
      :class="isDark ? 'bg-zinc-800 text-yellow-400 hover:bg-zinc-700' : 'bg-white text-zinc-700 hover:bg-gray-100 shadow'">
      <span class="text-sm">{{ isDark ? '☀️' : '🌙' }}</span>
    </button>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <svg class="animate-spin h-10 w-10" :class="isDark ? 'text-red-500' : 'text-[var(--cor-primaria)]'"
           xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO ── -->
      <section class="relative h-[55vh] min-h-[360px] overflow-hidden">
        <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
             :alt="loja.nome" class="w-full h-full object-cover" />
        <div class="absolute inset-0 bg-gradient-to-t"
             :class="isDark ? 'from-zinc-950 via-zinc-950/50 to-transparent' : 'from-gray-900/80 via-gray-900/30 to-transparent'"/>

        <button @click="$router.back()"
          class="absolute top-5 left-5 w-9 h-9 rounded-full bg-black/50 hover:bg-black/70
                 flex items-center justify-center transition backdrop-blur-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div class="absolute bottom-0 left-0 p-8 flex items-end gap-5">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-20 h-20 rounded-2xl object-cover border-2 border-white/20 shadow-xl flex-shrink-0" />
          <div v-else class="w-20 h-20 rounded-2xl flex items-center justify-center flex-shrink-0 border-2 border-white/20"
               :style="{ backgroundColor: 'var(--cor-primaria)' }">
            <span class="text-3xl font-bold text-white">{{ loja.nome.charAt(0) }}</span>
          </div>
          <div>
            <span class="inline-block px-2 py-0.5 rounded-full text-white text-[10px] font-bold uppercase tracking-wider mb-2"
                  :style="{ backgroundColor: 'var(--cor-primaria)' }">
              {{ loja.categoria }}
            </span>
            <h1 class="text-3xl md:text-4xl font-extrabold text-white leading-tight">{{ loja.nome }}</h1>
            <div class="flex items-center gap-4 mt-2 text-sm text-zinc-300 flex-wrap">
              <span v-if="loja.localizacao" class="flex items-center gap-1">📍 {{ loja.localizacao }}</span>
              <span v-if="loja.rating_medio" class="flex items-center gap-1">
                ⭐ {{ loja.rating_medio }}
                <span v-if="loja.total_avaliacoes" class="text-zinc-500">({{ loja.total_avaliacoes }})</span>
              </span>
              <span v-if="loja.entrega_ativa" class="text-green-400">✓ Entrega disponível</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ── SIDEBAR + MAIN ── -->
      <div class="flex">
        <!-- Sidebar -->
        <transition enter-active-class="transition duration-300" enter-from-class="-translate-x-full"
                    leave-active-class="transition duration-200" leave-to-class="-translate-x-full">
          <aside v-if="sidebarAberta"
                 class="fixed left-0 top-0 h-screen w-64 overflow-y-auto z-30 pt-6"
                 :class="isDark ? 'bg-zinc-900 border-r border-zinc-800' : 'bg-white border-r border-gray-200 shadow-xl'">
            <div class="flex items-center justify-between px-5 mb-5">
              <h3 class="text-sm font-bold" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">Navegar</h3>
              <button @click="sidebarAberta = false"
                class="w-7 h-7 rounded-lg flex items-center justify-center transition"
                :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <!-- Tipos -->
            <div v-if="tiposExistentes.length > 0" class="px-3 mb-5">
              <p class="text-[10px] font-bold uppercase tracking-wider px-2 mb-2" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Tipos</p>
              <button v-for="tipo in tiposExistentes" :key="tipo.id"
                @click="scrollToId('tipo-' + tipo.id); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100 hover:text-zinc-900'">
                <span>{{ tipoIcon(tipo.nome) }}</span>
                <span class="capitalize">{{ tipo.nome }}</span>
              </button>
            </div>
            <!-- Categorias -->
            <div v-if="categoriasExistentes.length > 0" class="px-3 mb-5 border-t pt-4"
                 :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <p class="text-[10px] font-bold uppercase tracking-wider px-2 mb-2" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Categorias</p>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100 hover:text-zinc-900'">
                <span>{{ cat.icone }}</span>
                <span class="capitalize">{{ cat.nome }}</span>
              </button>
            </div>
            <div class="px-3 border-t pt-4" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <button @click="scrollToId('catalogo'); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100'">
                🔍 Catálogo completo
              </button>
              <button @click="scrollToId('avaliacoes'); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100'">
                ⭐ Avaliações
              </button>
            </div>
          </aside>
        </transition>
        <div v-if="sidebarAberta" class="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm" @click="sidebarAberta = false" />
        <button v-if="temSidebar" @click="sidebarAberta = !sidebarAberta"
          class="fixed bottom-6 left-6 z-30 w-12 h-12 rounded-xl flex items-center justify-center shadow-lg transition border"
          :class="isDark ? 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800' : 'bg-white border-gray-200 hover:bg-gray-50 shadow-md'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- Main -->
        <main class="flex-1 min-w-0">
          <div class="max-w-6xl mx-auto px-6 py-8">

            <!-- Info cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
              <div class="md:col-span-2 rounded-2xl p-5 border"
                   :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200 shadow-sm'">
                <h2 class="text-sm font-bold uppercase tracking-wider mb-3"
                    :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Sobre a loja</h2>
                <p class="text-sm leading-relaxed" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
                  {{ loja.descricao || 'Sem descrição disponível.' }}
                </p>
                <div v-if="metodosPagamento.length > 0" class="mt-4 pt-4 border-t"
                     :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                  <p class="text-xs font-bold uppercase tracking-wider mb-2" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Pagamento aceite</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="m in metodosPagamento" :key="m.id"
                          class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs"
                          :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-gray-100 text-zinc-600'">
                      {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="rounded-2xl p-5 border"
                   :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200 shadow-sm'">
                <h2 class="text-sm font-bold uppercase tracking-wider mb-3"
                    :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Entrega</h2>
                <div v-if="opcoesEntrega.length === 0" class="text-sm"
                     :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Sem opções configuradas.</div>
                <div v-else class="space-y-2">
                  <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                       class="flex items-center justify-between py-2 border-b last:border-0"
                       :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                    <div>
                      <p class="text-sm font-medium" :class="isDark ? 'text-zinc-200' : 'text-zinc-700'">{{ opcao.nome }}</p>
                      <p v-if="opcao.tempo_estimado" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ opcao.tempo_estimado }}</p>
                    </div>
                    <span class="text-sm font-bold" :style="{ color: 'var(--cor-primaria)' }">
                      {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sliders -->
            <ProductSlider title="Em Destaque" icon="⭐"
              :params="{ loja_id: lojaId, destaque: true }"
              :dark="isDark"
              @product-click="selectedProduct = $event" />

            <template v-if="tiposExistentes.length > 0">
              <div class="flex items-center gap-3 my-6">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                <span class="text-xs font-bold uppercase tracking-widest"
                      :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Por tipo</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
              </div>
              <div v-for="tipo in tiposExistentes" :key="'tipo-' + tipo.id" :id="'tipo-' + tipo.id">
                <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }"
                  :dark="isDark"
                  @product-click="selectedProduct = $event" />
              </div>
            </template>

            <template v-if="categoriasExistentes.length > 0">
              <div class="flex items-center gap-3 my-6">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                <span class="text-xs font-bold uppercase tracking-widest"
                      :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Por categoria</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
              </div>
              <div v-for="cat in categoriasExistentes" :key="'cat-' + cat.id" :id="'cat-' + cat.id">
                <ProductSlider :title="cat.nome" :icon="cat.icone || '📂'"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :dark="isDark"
                  @product-click="selectedProduct = $event" />
              </div>
            </template>

            <!-- Catálogo -->
            <div id="catalogo" class="mt-10 mb-4">
              <h2 class="text-xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Catálogo completo</h2>
              <p class="text-sm mt-1" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">Filtra por tipo, categoria ou pesquisa</p>
            </div>
            <ProductCatalog :loja-id="lojaId" :dark="isDark" @product-click="selectedProduct = $event" />

            <!-- Avaliações -->
            <div id="avaliacoes" class="mt-10">
              <h2 class="text-xl font-bold mb-5" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Avaliações</h2>
              <AvaliacaoLoja :loja-id="lojaId" @rating-updated="onRatingUpdated" />
            </div>

            <!-- Footer loja -->
            <footer v-if="temFooter" class="mt-16 pt-8 border-t"
                    :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div>
                  <div class="flex items-center gap-3 mb-3">
                    <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-8 h-8 rounded-lg object-cover" />
                    <p class="font-bold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ loja.nome }}</p>
                  </div>
                  <p class="text-xs leading-relaxed" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ loja.descricao }}</p>
                </div>
                <div v-if="loja.politica_devolucao" class="space-y-2">
                  <button @click="modalPolitica = 'devolucao'"
                    class="text-sm font-semibold flex items-center gap-2 transition"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-500 hover:text-zinc-800'">
                    📦 Política de devoluções
                  </button>
                  <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                    class="text-sm font-semibold flex items-center gap-2 transition"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-500 hover:text-zinc-800'">
                    📄 Termos de serviço
                  </button>
                </div>
              </div>
              <div class="text-center text-xs pt-4 border-t" :class="isDark ? 'text-zinc-700 border-zinc-900' : 'text-zinc-400 border-gray-200'">
                © {{ new Date().getFullYear() }} {{ loja.nome }}
              </div>
            </footer>
          </div>
        </main>
      </div>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-2xl border w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
            <h3 class="text-base font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Política de devoluções' : 'Termos de serviço' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-full flex items-center justify-center transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : loja.termos_servico }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center text-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-gray-50'">
      <p class="text-2xl font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Loja não encontrada</p>
      <button @click="$router.back()" class="mt-2 text-sm" :style="{ color: 'var(--cor-primaria)' }">← Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart       from '@/components/cart/multiCart.vue'
import ProductSlider   from '@/components/sliders/ProductSlider.vue'
import Profile         from '@/components/profile/UserProfile.vue'
import ProductCatalog  from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja   from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateClassico',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },

  props: {
    tema: { type: Object, default: () => ({ id: 'classico', corPrimaria: '#dc2626', corSecundaria: '#1c1c1e', darkMode: true }) }
  },

  setup (props) {
    const isDark = ref(props.tema?.darkMode !== false)

    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#dc2626',
      '--cor-secundaria': props.tema?.corSecundaria || '#1c1c1e',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value }

    return {
      isDark, cssVars, user,
      toggleDark,
      ...lojaData,
    }
  }
}
</script>
