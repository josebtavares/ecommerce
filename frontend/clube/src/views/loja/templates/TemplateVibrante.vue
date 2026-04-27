<!-- TemplateVibrante.vue — REMODELADO
     Streetwear/jovem. Hero de 3 blocos diagonais, marquee, cards bold.
     FIXES: removidos props inexistentes (show-title, card-style, grid-cols).
-->
<template>
  <div class="min-h-screen overflow-x-hidden transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-white'">
      <div class="relative w-16 h-16">
        <div class="absolute inset-0 rotate-45 animate-spin rounded-xl"
             :style="{ border: '3px solid var(--cor-primaria)', borderTopColor: 'transparent' }"></div>
        <div class="absolute inset-3 rounded-lg"
             :class="isDark ? 'bg-zinc-950' : 'bg-white'"></div>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO — 3 painéis diagonais ── -->
      <section class="relative min-h-screen overflow-hidden flex flex-col">

        <!-- Painel 1: imagem banner (fundo) -->
        <div class="absolute inset-0">
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome" class="w-full h-full object-cover opacity-30" />
        </div>

        <!-- Painel 2: bloco cor primária direita (diagonal) -->
        <div class="absolute inset-0 pointer-events-none">
          <div class="absolute top-0 right-0 h-full w-[45%]"
               :style="{ background: 'var(--cor-primaria)', clipPath: 'polygon(25% 0%, 100% 0%, 100% 100%, 0% 100%)', opacity: '0.92' }"></div>
        </div>

        <!-- Painel 3: bloco escuro no canto inferior esquerdo -->
        <div class="absolute bottom-0 left-0 w-[65%] h-[42%] pointer-events-none"
             :class="isDark ? 'bg-zinc-900' : 'bg-zinc-100'"
             style="clip-path: polygon(0 15%, 100% 0%, 100% 100%, 0% 100%)"></div>

        <!-- Elemento decorativo: círculo outline -->
        <div class="absolute top-20 left-12 w-28 h-28 rounded-full border-4 opacity-15 pointer-events-none"
             :style="{ borderColor: 'var(--cor-primaria)' }"></div>
        <div class="absolute bottom-32 right-12 w-44 h-44 rounded-full opacity-10 pointer-events-none"
             :style="{ background: 'var(--cor-primaria)' }"></div>

        <!-- Nav -->
        <div class="relative flex items-center gap-3 px-6 py-5 z-10">
          <button @click="$router.back()"
            class="w-11 h-11 rounded-xl flex items-center justify-center text-white transition-all hover:scale-110"
            :style="{ background: 'var(--cor-primaria)', boxShadow: '0 4px 14px var(--cor-primaria)50' }">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button @click="toggleDark"
            class="w-11 h-11 rounded-xl flex items-center justify-center font-black text-sm transition-all border-2 hover:scale-110"
            :class="isDark ? 'border-white/20 text-white hover:bg-white/10' : 'border-zinc-300 text-zinc-700 hover:bg-zinc-100'">
            {{ isDark ? '☀' : '🌙' }}
          </button>
        </div>

        <!-- Conteúdo hero -->
        <div class="relative flex-1 flex items-center z-10 px-6 md:px-12 pb-20">
          <div class="grid grid-cols-1 lg:grid-cols-2 items-center gap-12 w-full max-w-7xl mx-auto">

            <!-- Texto esquerda -->
            <div>
              <!-- Category pill -->
              <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-7 font-black uppercase tracking-wider text-sm text-white"
                   :style="{ background: 'var(--cor-primaria)' }">
                <span class="w-2.5 h-2.5 bg-white rounded-full animate-pulse"></span>
                {{ loja.categoria }}
              </div>

              <!-- Título bold, segunda linha outline -->
              <h1 class="font-black leading-[0.88] tracking-tight mb-7" style="font-size:clamp(3.5rem,9vw,7.5rem)">
                <span class="block" :class="isDark ? 'text-white' : 'text-zinc-900'">
                  {{ loja.nome.split(' ')[0] }}
                </span>
                <span v-if="loja.nome.split(' ').length > 1"
                      class="block"
                      :style="{ color:'transparent', WebkitTextStroke: isDark ? '2.5px white' : '2.5px #1a1a1a' }">
                  {{ loja.nome.split(' ').slice(1).join(' ') }}
                </span>
              </h1>

              <p v-if="loja.descricao" class="text-base leading-relaxed max-w-md mb-8"
                 :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
                {{ loja.descricao.substring(0, 150) }}{{ loja.descricao.length > 150 ? '…' : '' }}
              </p>

              <!-- Stats -->
              <div class="flex items-center gap-8 mb-10">
                <div v-if="loja.rating_medio">
                  <p class="text-5xl font-black leading-none" style="color:var(--cor-primaria)">{{ loja.rating_medio }}</p>
                  <p class="text-[9px] font-bold uppercase tracking-widest mt-1.5" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Rating</p>
                </div>
                <div v-if="loja.total_avaliacoes">
                  <p class="text-5xl font-black leading-none" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.total_avaliacoes }}</p>
                  <p class="text-[9px] font-bold uppercase tracking-widest mt-1.5" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Reviews</p>
                </div>
                <div v-if="loja.entrega_ativa"
                     class="px-4 py-2 rounded-lg font-black text-sm uppercase bg-emerald-500 text-white">
                  ✓ Entrega
                </div>
              </div>

              <!-- CTAs -->
              <div class="flex gap-4 flex-wrap">
                <button @click="scrollToId('produtos')"
                  class="px-10 py-4 rounded-xl font-black uppercase tracking-wider text-sm text-white transition-all hover:scale-105 hover:-rotate-1"
                  :style="{ background: 'var(--cor-primaria)', boxShadow: '0 8px 28px var(--cor-primaria)40' }">
                  Ver Coleção
                </button>
                <button @click="scrollToId('catalogo')"
                  class="px-10 py-4 rounded-xl font-black uppercase tracking-wider text-sm transition-all hover:scale-105 hover:rotate-1 border-2"
                  :class="isDark ? 'border-white text-white hover:bg-white hover:text-zinc-900' : 'border-zinc-900 text-zinc-900 hover:bg-zinc-900 hover:text-white'">
                  Catálogo
                </button>
              </div>
            </div>

            <!-- Logo / imagem direita sobre cor -->
            <div class="hidden lg:flex justify-center items-center">
              <div class="relative w-72 h-72 rounded-3xl overflow-hidden rotate-3 hover:rotate-0 transition-transform duration-500"
                   :class="isDark ? 'bg-zinc-800' : 'bg-white shadow-2xl'">
                <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center" :style="{ background: 'var(--cor-primaria)' }">
                  <span class="text-9xl font-black text-white">{{ loja.nome.charAt(0) }}</span>
                </div>
              </div>
              <!-- Dashed spin ring -->
              <div class="absolute w-80 h-80 rounded-3xl border-2 border-dashed rotate-6 pointer-events-none"
                   :style="{ borderColor: 'var(--cor-primaria)', animation: 'spinSlow 20s linear infinite' }"></div>
            </div>
          </div>
        </div>

        <!-- Scroll hint -->
        <div class="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2">
          <p class="text-[9px] font-black uppercase tracking-widest" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Scroll</p>
          <div class="w-6 h-10 rounded-full border-2 flex items-start justify-center p-1.5"
               :class="isDark ? 'border-zinc-700' : 'border-zinc-300'">
            <div class="w-1.5 h-3 rounded-full animate-bounce" :style="{ background: 'var(--cor-primaria)' }"></div>
          </div>
        </div>
      </section>

      <!-- ── MARQUEE ── -->
      <div class="overflow-hidden py-3.5" :style="{ background: 'var(--cor-primaria)' }">
        <div class="flex items-center gap-8 animate-marquee whitespace-nowrap">
          <span v-for="n in 8" :key="n"
                class="text-white font-black uppercase tracking-wider text-sm flex items-center gap-8 flex-shrink-0">
            <span>New Drop</span>
            <span class="w-2.5 h-2.5 bg-white rounded-full inline-block"></span>
            <span>Limited Edition</span>
            <span class="w-2.5 h-2.5 bg-white rounded-full inline-block"></span>
            <span>{{ loja.nome }}</span>
            <span class="w-2.5 h-2.5 bg-white rounded-full inline-block"></span>
          </span>
        </div>
      </div>

      <!-- ── MAIN ── -->
      <main class="max-w-7xl mx-auto px-6 pb-20">

        <!-- Destaques -->
        <section id="produtos" class="py-16">
          <div class="flex items-end justify-between mb-10">
            <div>
              <p class="font-black uppercase tracking-widest text-sm mb-2" style="color:var(--cor-primaria)">Hot Items</p>
              <h2 class="text-5xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">Destaques</h2>
            </div>
            <span class="hidden md:block text-8xl font-black opacity-10" :class="isDark ? 'text-white' : 'text-zinc-900'">01</span>
          </div>
          <ProductSlider
            title="Destaques"
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            card-width="220px"
            image-height="210px"
            card-height="330px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-300"
            :hover-border-class="isDark ? 'hover:border-pink-500/60' : 'hover:border-pink-400/60'"
            :price-class="'font-black text-lg'"
            :badge-class="'text-white font-black rounded-lg px-2 py-0.5 text-[10px]'"
            badge-text="🔥"
            :show-store-name="false"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Por tipo -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                   class="pb-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
            <div class="flex items-end justify-between my-10">
              <div class="flex items-center gap-5">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl text-white"
                     :style="{ background: 'var(--cor-primaria)' }">
                  {{ tipoIcon(tipo.nome) }}
                </div>
                <h2 class="text-4xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ tipo.nome }}</h2>
              </div>
              <span class="hidden md:block text-7xl font-black opacity-8" :class="isDark ? 'text-white' : 'text-zinc-900'">
                {{ String(idx + 2).padStart(2, '0') }}
              </span>
            </div>
            <ProductSlider
              :title="tipo.nome"
              :params="{ loja_id: lojaId, tipo: tipo.nome }"
              :isDark="isDark"
              card-width="200px"
              image-height="190px"
              card-height="310px"
              card-border-radius="rounded-2xl"
              hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
              :hover-border-class="isDark ? 'hover:border-pink-500/50' : 'hover:border-pink-400/50'"
              :show-store-name="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Por categoria -->
        <template v-if="categoriasExistentes.length > 0">
          <section class="pb-16">
            <div class="flex items-end justify-between mb-10">
              <div>
                <p class="font-black uppercase tracking-widest text-sm mb-2" style="color:var(--cor-primaria)">Browse</p>
                <h2 class="text-5xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">Categorias</h2>
              </div>
            </div>
            <!-- Botões de categoria -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-12">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="p-5 rounded-2xl font-black uppercase text-center transition-all hover:scale-105 hover:-rotate-1 border-2"
                :class="isDark ? 'bg-zinc-900 border-zinc-800 text-white hover:border-pink-500/50' : 'bg-white border-zinc-200 text-zinc-900 hover:border-pink-400/50'">
                <span class="text-3xl block mb-2">{{ cat.icone }}</span>
                <span class="text-xs tracking-wide">{{ cat.nome }}</span>
              </button>
            </div>
            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
              <div class="flex items-center gap-4 mb-6">
                <span class="text-2xl">{{ cat.icone }}</span>
                <h3 class="text-2xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ cat.nome }}</h3>
                <div class="flex-1 h-1 rounded-full" :style="{ background: 'var(--cor-primaria)', opacity: '0.25' }"></div>
              </div>
              <ProductSlider
                :title="cat.nome"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark"
                card-width="200px"
                image-height="190px"
                card-height="310px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                :show-store-name="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Info entrega + pagamento -->
        <section class="pb-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="rounded-3xl p-7 border-2"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <div class="w-14 h-14 rounded-xl flex items-center justify-center mb-4 text-2xl text-white" :style="{ background: 'var(--cor-primaria)' }">🚚</div>
            <h3 class="text-xl font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">Entrega</h3>
            <div v-if="!opcoesEntrega.length" class="text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">Sem opções configuradas.</div>
            <div v-else class="space-y-3">
              <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="flex justify-between items-center py-2 border-b last:border-0"
                   :class="isDark ? 'border-zinc-800' : 'border-zinc-100'">
                <div>
                  <p class="font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ opcao.nome }}</p>
                  <p v-if="opcao.tempo_estimado" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ opcao.tempo_estimado }}</p>
                </div>
                <span class="font-black" style="color:var(--cor-primaria)">{{ opcao.preco == 0 ? 'FREE' : formatPrice(opcao.preco) }}</span>
              </div>
            </div>
          </div>
          <div class="rounded-3xl p-7 border-2"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <div class="w-14 h-14 rounded-xl flex items-center justify-center mb-4 text-2xl text-white" :style="{ background: 'var(--cor-primaria)' }">💳</div>
            <h3 class="text-xl font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">Pagamento</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="m in metodosPagamento" :key="m.id"
                    class="px-4 py-2 rounded-xl text-sm font-bold uppercase"
                    :class="isDark ? 'bg-zinc-800 text-white' : 'bg-zinc-100 text-zinc-800'">
                {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
              </span>
            </div>
          </div>
        </section>

        <!-- Catálogo completo -->
        <section id="catalogo" class="pb-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-end justify-between my-10">
            <div>
              <p class="font-black uppercase tracking-widest text-sm mb-2" style="color:var(--cor-primaria)">Full Collection</p>
              <h2 class="text-5xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">Catálogo</h2>
            </div>
          </div>
          <ProductCatalog
            :loja-id="lojaId" :isDark="isDark"
            grid-class="grid-cols-2 sm:grid-cols-3 xl:grid-cols-4"
            image-height="190px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
            :hover-border-class="isDark ? 'hover:border-pink-500/50' : 'hover:border-pink-400/50'"
            tab-border-radius="rounded-full"
            :active-tab-class="'text-white font-black uppercase tracking-wider text-xs shadow-lg'"
            :inactive-tab-dark-class="'bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-700 uppercase tracking-wider text-xs font-bold'"
            :inactive-tab-light-class="'bg-zinc-100 text-zinc-600 hover:text-zinc-900 border border-zinc-200 uppercase tracking-wider text-xs font-bold'"
            input-border-radius="rounded-xl"
            filter-container-radius="rounded-2xl"
            :product-name-hover-class="'group-hover:opacity-70'"
            :price-class="'font-black'"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Avaliações -->
        <section id="avaliacoes" class="pb-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-end justify-between my-10">
            <div>
              <p class="font-black uppercase tracking-widest text-sm mb-2" style="color:var(--cor-primaria)">Community</p>
              <h2 class="text-5xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">Reviews</h2>
            </div>
          </div>
          <AvaliacaoLoja
            :loja-id="lojaId" :isDark="isDark"
            summary-border-radius="rounded-2xl"
            form-border-radius="rounded-2xl"
            review-card-border-radius="rounded-2xl"
            button-border-radius="rounded-xl"
            textarea-border-radius="rounded-xl"
            :star-active-class="'text-yellow-400'"
            :star-inactive-class="isDark ? 'text-zinc-700' : 'text-zinc-300'"
            :submit-button-class="'text-white font-black uppercase tracking-wider text-xs'"
            :own-review-border-class="isDark ? 'bg-zinc-900 border border-pink-500/30' : 'bg-pink-50 border border-pink-200'"
            own-badge-class="bg-pink-500/20 text-pink-400 font-bold uppercase text-xs"
            link-class="text-pink-400 hover:text-pink-300 font-bold"
            @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer -->
        <footer class="border-t-4 py-14 text-center" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-center justify-center gap-4 mb-6">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-14 h-14 rounded-xl object-cover" />
            <span class="text-3xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.nome }}</span>
          </div>
          <div class="flex justify-center gap-8 text-xs font-black uppercase tracking-wider mb-6"
               :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="hover:underline">Returns</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="hover:underline">Terms</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="hover:underline">Privacy</button>
          </div>
          <p class="text-xs" :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">
            © {{ new Date().getFullYear() }} {{ loja.nome }}. Stay Bold.
          </p>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-3xl w-full max-w-lg max-h-[80vh] overflow-y-auto border-2 shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b-2 sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <h3 class="font-black uppercase tracking-wider text-sm" :class="isDark ? 'text-white' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Returns' : modalPolitica === 'termos' ? 'Terms' : 'Privacy' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-9 h-9 rounded-xl flex items-center justify-center font-black text-white"
              :style="{ background: 'var(--cor-primaria)' }">×</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-white'">
      <p class="text-6xl font-black mb-4" style="color:var(--cor-primaria)">404</p>
      <p class="text-xl font-bold uppercase mb-8" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Loja não encontrada</p>
      <button @click="$router.back()"
        class="px-8 py-4 rounded-xl font-black uppercase text-white"
        :style="{ background: 'var(--cor-primaria)' }">
        Voltar
      </button>
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
  name: 'TemplateVibrante',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#f43f5e',
      '--cor-secundaria': props.tema?.corSecundaria || '#18181b',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }

    return { isDark, cssVars, user, toggleDark, ...lojaData }
  },
}
</script>

<style scoped>
@keyframes marquee {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@keyframes spinSlow {
  from { transform: rotate(0deg) rotateX(3deg); }
  to   { transform: rotate(360deg) rotateX(3deg); }
}
.animate-marquee { animation: marquee 25s linear infinite; }
</style>
