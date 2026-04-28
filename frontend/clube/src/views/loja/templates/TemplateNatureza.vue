<!-- TemplateNatureza.vue — Orgânico, verde, produtos bio/naturais -->
<template>
  <div class="min-h-screen transition-colors duration-500"
       :class="isDark ? 'bg-[#051a0a] text-green-50' : 'bg-[#f0fdf4] text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-[#051a0a]' : 'bg-[#f0fdf4]'">
      <div class="flex flex-col items-center gap-4">
        <div class="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin"
             :style="{ borderColor: 'var(--cor-primaria)', borderTopColor: 'transparent' }"></div>
        <p class="text-xs tracking-[0.3em] uppercase" style="color: var(--cor-primaria)">A crescer…</p>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HEADER fixo ── -->
      <header class="fixed top-0 left-0 right-0 z-30 transition-all duration-500"
              :class="scrolled
                ? (isDark ? 'bg-[#051a0a]/95 backdrop-blur-xl border-b border-green-900/30' : 'bg-[#f0fdf4]/95 backdrop-blur-xl border-b border-green-200')
                : 'bg-transparent'">
        <div class="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <button @click="$router.back()"
              class="text-xs tracking-[0.25em] uppercase transition-colors"
              :class="isDark ? 'text-green-700 hover:text-green-300' : 'text-green-700 hover:text-green-900'">
              ← Voltar
            </button>
            <button @click="toggleDark"
              class="w-7 h-7 rounded-full border flex items-center justify-center transition"
              :class="isDark ? 'border-green-900 text-green-600 hover:border-green-600' : 'border-green-300 text-green-600 hover:border-green-500'">
              <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
          </div>
          <span v-if="scrolled && loja"
                class="absolute left-1/2 -translate-x-1/2 text-xs tracking-[0.3em] uppercase pointer-events-none font-medium"
                :class="isDark ? 'text-green-500' : 'text-green-700'">
            {{ loja.nome }}
          </span>
          <div class="w-20"></div>
        </div>
      </header>

      <!-- ── HERO — split imagem + texto, textura orgânica ── -->
      <section class="min-h-screen grid grid-cols-1 lg:grid-cols-2 pt-14">
        <!-- Imagem -->
        <div class="relative h-[55vh] lg:h-screen overflow-hidden">
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome" class="w-full h-full object-cover transition-transform duration-[8s] scale-105" />
          <div class="absolute inset-0"
               :class="isDark
                 ? 'bg-gradient-to-r from-transparent via-transparent to-[#051a0a]/80'
                 : 'bg-gradient-to-r from-transparent via-transparent to-[#f0fdf4]/60'" />
          <!-- Dot pattern orgânico overlay -->
          <div class="absolute inset-0 pointer-events-none" style="opacity:0.04;background-image:radial-gradient(circle,#4ade80 1px,transparent 1px);background-size:16px 16px"></div>
          <!-- Badge entrega -->
          <div v-if="loja.entrega_ativa"
               class="absolute bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full border text-xs font-medium backdrop-blur-md whitespace-nowrap"
               :class="isDark ? 'bg-green-900/50 border-green-700/30 text-green-300' : 'bg-green-50/80 border-green-300 text-green-800'">
            🌿 Entrega disponível
          </div>
        </div>

        <!-- Texto -->
        <div class="flex flex-col justify-center px-8 md:px-12 lg:px-16 py-12 lg:py-20"
             :class="isDark ? 'bg-[#051a0a]' : 'bg-[#f0fdf4]'">
          <!-- Ornamento folha SVG simples -->
          <div class="flex items-center gap-3 mb-6">
            <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/50' : 'bg-green-200'"></div>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" style="color:var(--cor-primaria)" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 008 20C19 20 22 3 22 3c-1 2-8 10-12 10 1-3 4-6 8-6-1.6-2.6-7.4-2.4-9 2z"/>
            </svg>
            <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/50' : 'bg-green-200'"></div>
          </div>

          <p class="text-xs tracking-[0.4em] uppercase mb-4" style="color:var(--cor-primaria)">
            {{ loja.categoria }}<span v-if="loja.localizacao" class="ml-3 opacity-60">· {{ loja.localizacao }}</span>
          </p>

          <h1 class="leading-tight font-black tracking-tight mb-5"
              style="font-size:clamp(2.4rem,5vw,4.5rem)"
              :class="isDark ? 'text-green-50' : 'text-zinc-900'">
            {{ loja.nome }}
          </h1>

          <p v-if="loja.descricao" class="text-base leading-relaxed mb-8 max-w-sm"
             :class="isDark ? 'text-green-200/50' : 'text-zinc-600'">
            {{ loja.descricao }}
          </p>

          <!-- Selos de confiança -->
          <div class="flex flex-wrap gap-2 mb-8">
            <span v-for="(s, i) in ['🌱 100% Natural','♻️ Sustentável','🐝 Sem crueldade']" :key="i"
                  class="px-3 py-1.5 rounded-full text-xs font-semibold"
                  :class="isDark ? 'bg-green-900/40 text-green-400 border border-green-800/50' : 'bg-green-100 text-green-800 border border-green-200'">
              {{ s }}
            </span>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-3 gap-4 py-5 border-y mb-8"
               :class="isDark ? 'border-green-900/30' : 'border-green-200'">
            <div v-if="loja.rating_medio" class="text-center">
              <p class="text-2xl font-black" style="color:var(--cor-primaria)">{{ loja.rating_medio }}</p>
              <p class="text-[10px] tracking-[0.2em] uppercase mt-1" :class="isDark ? 'text-green-800' : 'text-green-600/60'">Rating</p>
            </div>
            <div v-if="loja.total_avaliacoes" class="text-center border-x" :class="isDark ? 'border-green-900/30' : 'border-green-200'">
              <p class="text-2xl font-black" :class="isDark ? 'text-green-50' : 'text-zinc-900'">{{ loja.total_avaliacoes }}</p>
              <p class="text-[10px] tracking-[0.2em] uppercase mt-1" :class="isDark ? 'text-green-800' : 'text-green-600/60'">Reviews</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-black text-green-400">✓</p>
              <p class="text-[10px] tracking-[0.2em] uppercase mt-1" :class="isDark ? 'text-green-800' : 'text-green-600/60'">Bio</p>
            </div>
          </div>

          <div class="flex flex-wrap gap-3">
            <button @click="scrollToId('produtos')"
              class="px-7 py-3 rounded-2xl font-bold text-sm text-white transition-all hover:scale-[1.02] hover:shadow-lg"
              style="background:var(--cor-primaria);box-shadow:0 4px 20px var(--cor-primaria)30">
              Ver Produtos
            </button>
            <button v-if="loja.rating_medio" @click="scrollToId('avaliacoes')"
              class="px-7 py-3 rounded-2xl font-bold text-sm border transition-all hover:scale-[1.02]"
              :class="isDark ? 'border-green-800 text-green-400 hover:bg-green-900/30' : 'border-green-300 text-green-700 hover:bg-green-50'">
              ★ Avaliações
            </button>
          </div>
        </div>
      </section>

      <!-- ── MAIN ── -->
      <main class="max-w-6xl mx-auto px-6 pb-20">

        <!-- Info sobre + entrega -->
        <section class="py-14 border-b" :class="isDark ? 'border-green-900/20' : 'border-green-100'">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="md:col-span-2">
              <p class="text-[10px] tracking-[0.4em] uppercase mb-3" style="color:var(--cor-primaria)">Sobre</p>
              <p class="text-xl font-light leading-relaxed" :class="isDark ? 'text-green-100/70' : 'text-zinc-700'">
                {{ loja.descricao || 'Uma loja construída em torno de um único princípio: produtos que respeitam a natureza e o teu bem-estar.' }}
              </p>
            </div>
            <div class="space-y-4">
              <div v-if="opcoesEntrega.length">
                <p class="text-[10px] tracking-[0.3em] uppercase mb-3" :class="isDark ? 'text-green-800' : 'text-green-600/60'">Envio</p>
                <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="flex items-center justify-between py-2 border-b last:border-0"
                     :class="isDark ? 'border-green-900/20' : 'border-green-100'">
                  <span class="text-sm" :class="isDark ? 'text-green-200/60' : 'text-zinc-600'">{{ opcao.nome }}</span>
                  <span class="text-sm font-bold" style="color:var(--cor-primaria)">{{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}</span>
                </div>
              </div>
              <div v-if="metodosPagamento.length">
                <p class="text-[10px] tracking-[0.3em] uppercase mb-3" :class="isDark ? 'text-green-800' : 'text-green-600/60'">Pagamento</p>
                <div class="flex flex-wrap gap-2">
                  <span v-for="m in metodosPagamento" :key="m.id"
                        class="px-2.5 py-1 rounded-full text-xs"
                        :class="isDark ? 'bg-green-900/30 text-green-400 border border-green-900/50' : 'bg-green-50 text-green-700 border border-green-200'">
                    {{ m.tipo }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Destaques -->
        <section id="produtos" class="py-12">
          <div class="flex items-center gap-4 mb-8">
            <p class="text-[10px] tracking-[0.4em] uppercase" style="color:var(--cor-primaria)">Destaques</p>
            <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/20' : 'bg-green-100'"></div>
          </div>
          <ProductSlider
            title="Destaques"
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            card-width="200px"
            image-height="240px"
            card-height="330px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-300"
            :hover-border-class="isDark ? 'hover:border-green-700/60' : 'hover:border-green-400/50'"
            price-class="text-green-500 font-bold"
            badge-class="bg-green-600 rounded-lg text-white font-bold"
            badge-text="Bio"
            :show-store-name="false"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Por tipo -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id" class="py-8 border-t"
                   :class="isDark ? 'border-green-900/20' : 'border-green-100'">
            <div class="flex items-center gap-4 mb-6">
              <span class="text-xl">{{ tipoIcon(tipo.nome) }}</span>
              <h2 class="text-xl font-bold capitalize" :class="isDark ? 'text-green-50' : 'text-zinc-900'">{{ tipo.nome }}</h2>
              <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/20' : 'bg-green-100'"></div>
            </div>
            <ProductSlider
              :title="tipo.nome" :params="{ loja_id: lojaId, tipo: tipo.nome }" :isDark="isDark"
              card-width="185px" image-height="220px" card-height="310px"
              card-border-radius="rounded-2xl"
              hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
              :hover-border-class="isDark ? 'hover:border-green-700/50' : 'hover:border-green-400/50'"
              price-class="text-green-500 font-bold"
              :show-store-name="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Por categoria -->
        <template v-if="categoriasExistentes.length > 0">
          <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="py-8 border-t"
                   :class="isDark ? 'border-green-900/20' : 'border-green-100'">
            <div class="flex items-center gap-4 mb-6">
              <span class="text-xl">{{ cat.icone }}</span>
              <h2 class="text-xl font-bold capitalize" :class="isDark ? 'text-green-50' : 'text-zinc-900'">{{ cat.nome }}</h2>
              <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/20' : 'bg-green-100'"></div>
            </div>
            <ProductSlider
              :title="cat.nome" :params="{ loja_id: lojaId, categoria_id: cat.id }" :isDark="isDark"
              card-width="185px" image-height="220px" card-height="310px"
              card-border-radius="rounded-2xl"
              hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
              :hover-border-class="isDark ? 'hover:border-green-700/50' : 'hover:border-green-400/50'"
              price-class="text-green-500 font-bold"
              :show-store-name="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Catálogo completo -->
        <section id="catalogo" class="py-12 border-t" :class="isDark ? 'border-green-900/20' : 'border-green-100'">
          <div class="flex items-center gap-4 mb-8">
            <p class="text-[10px] tracking-[0.4em] uppercase" style="color:var(--cor-primaria)">Catálogo</p>
            <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/20' : 'bg-green-100'"></div>
          </div>
          <ProductCatalog
            :loja-id="lojaId" :isDark="isDark"
            grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
            image-height="200px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
            :hover-border-class="isDark ? 'hover:border-green-700/50' : 'hover:border-green-400/50'"
            tab-border-radius="rounded-full"
            active-tab-class="bg-green-600 text-white"
            :inactive-tab-dark-class="'bg-green-950/60 text-green-500/70 hover:text-green-300 border border-green-900/40'"
            :inactive-tab-light-class="'bg-green-50 text-green-700 hover:text-green-900 border border-green-200'"
            input-border-radius="rounded-xl"
            :input-focus-class="'focus:border-green-500'"
            filter-container-radius="rounded-2xl"
            product-name-hover-class="group-hover:text-green-500"
            price-class="text-green-500 font-bold"
            spinner-class="text-green-500"
            indicator-active-class="bg-green-600/20 text-green-500"
            clear-all-class="text-green-500 hover:text-green-400"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Avaliações -->
        <section id="avaliacoes" class="py-12 border-t" :class="isDark ? 'border-green-900/20' : 'border-green-100'">
          <div class="flex items-center gap-4 mb-8">
            <p class="text-[10px] tracking-[0.4em] uppercase" style="color:var(--cor-primaria)">Avaliações</p>
            <div class="flex-1 h-px" :class="isDark ? 'bg-green-900/20' : 'bg-green-100'"></div>
          </div>
          <AvaliacaoLoja
            :loja-id="lojaId" :isDark="isDark"
            summary-border-radius="rounded-2xl"
            form-border-radius="rounded-2xl"
            review-card-border-radius="rounded-2xl"
            button-border-radius="rounded-xl"
            textarea-border-radius="rounded-xl"
            star-active-class="text-green-500"
            :star-inactive-class="isDark ? 'text-green-900/60' : 'text-green-200'"
            progress-bar-class="bg-green-500"
            submit-button-class="bg-green-600 hover:bg-green-500 text-white"
            :own-review-border-class="isDark ? 'bg-green-950/50 border border-green-800/40' : 'bg-green-50 border border-green-200'"
            own-badge-class="bg-green-600/20 text-green-500"
            link-class="text-green-500 hover:text-green-400"
            @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer -->
        <footer class="border-t pt-10 pb-4" :class="isDark ? 'border-green-900/20' : 'border-green-100'">
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div class="flex items-center gap-3">
              <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-9 h-9 rounded-xl object-cover" />
              <div v-else class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-sm font-black" style="background:var(--cor-primaria)">{{ loja.nome.charAt(0) }}</div>
              <div>
                <p class="font-bold text-sm" :class="isDark ? 'text-green-100' : 'text-zinc-800'">{{ loja.nome }}</p>
                <p class="text-xs" :class="isDark ? 'text-green-800' : 'text-green-600/60'">© {{ new Date().getFullYear() }}</p>
              </div>
            </div>
            <div class="flex gap-5 text-xs">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="transition hover:underline" :class="isDark ? 'text-green-700 hover:text-green-400' : 'text-green-600 hover:text-green-800'">Devoluções</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="transition hover:underline" :class="isDark ? 'text-green-700 hover:text-green-400' : 'text-green-600 hover:text-green-800'">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="transition hover:underline" :class="isDark ? 'text-green-700 hover:text-green-400' : 'text-green-600 hover:text-green-800'">Privacidade</button>
            </div>
          </div>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" @click.self="modalPolitica = null">
        <div class="w-full max-w-lg max-h-[80vh] overflow-y-auto rounded-2xl shadow-2xl"
             :class="isDark ? 'bg-[#071a0c] border border-green-900/40' : 'bg-white border border-green-100'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-[#071a0c] border-green-900/40' : 'bg-white border-green-100'">
            <h3 class="font-bold text-sm" :class="isDark ? 'text-green-100' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null" class="w-8 h-8 rounded-full flex items-center justify-center transition"
                    :class="isDark ? 'bg-green-900/30 hover:bg-green-900/50 text-green-400' : 'bg-green-50 hover:bg-green-100 text-green-700'">×</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap" :class="isDark ? 'text-green-200/60' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center" :class="isDark ? 'bg-[#051a0a]' : 'bg-[#f0fdf4]'">
      <p class="text-xl font-bold mb-4" :class="isDark ? 'text-green-700' : 'text-green-800'">Loja não encontrada</p>
      <button @click="$router.back()" class="text-sm hover:underline" style="color:var(--cor-primaria)">← Voltar</button>
    </div>
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
  name: 'TemplateNatureza',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#16a34a',
      '--cor-secundaria': props.tema?.corSecundaria || '#051a0a',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }
    function onScroll ()   { scrolled.value = window.scrollY > 60 }

    onMounted (() => window.addEventListener('scroll', onScroll, { passive: true }))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrolled, cssVars, user, toggleDark, ...lojaData }
  },
}
</script>
