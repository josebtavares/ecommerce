<!-- TemplateVibrante.vue — REDESENHADO v2
     Editorial streetwear / vibrante profissional.
     Layout: hero split assimétrico, navegação por âncoras à esquerda (NÃO sobrepõe
     userProfile / notificacaoSino / multiCart à direita), tipografia oversized,
     cor primária como acento agressivo + secundária como base, marquee minimal,
     grids ritmados com numeração editorial.

     Posição reservada à direita do topo (NÃO MEXER):
       UserProfile  → top-2 md:top-6           right-[2.5vw]
       MultiCart    → top-2 md:top-[1.35rem]   right-[6rem] md:right-[calc(2.5vw+5.5rem)]
       NotificacaoSino → dentro do UserProfile
     Por isso o nav superior fica à esquerda e o sticky de secções abaixo é uma
     bar centrada com padding-right responsivo.
-->
<template>
  <div class="tv2 min-h-screen overflow-x-hidden transition-colors duration-300"
       :class="isDark ? 'tv2--dark' : 'tv2--light'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <!-- Loader -->
    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-white'">
      <div class="tv2-loader">
        <span></span><span></span><span></span>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ───────── TOP BAR (esquerda apenas) ───────── -->
      <header class="relative z-30 flex items-center gap-3 px-5 md:px-8 pt-4 md:pt-6">
        <button @click="$router.back()" class="tv2-iconbtn" aria-label="Voltar">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24"
               stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <button @click="toggleDark" class="tv2-iconbtn" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <span class="text-[13px] font-black leading-none">{{ isDark ? '☀' : '☾' }}</span>
        </button>

        <!-- wordmark mini -->
        <div class="ml-2 hidden md:flex items-center gap-2 select-none">
          <span class="w-1.5 h-1.5 rounded-full" :style="{ background: 'var(--cor-primaria)' }"></span>
          <span class="text-[10px] font-black uppercase tracking-[0.32em] opacity-60">
            {{ loja.categoria || 'Store' }} · {{ new Date().getFullYear() }}
          </span>
        </div>
      </header>

      <!-- ───────── HERO ───────── -->
      <section class="relative px-5 md:px-8 pt-8 md:pt-10 pb-14 md:pb-20">

        <!-- bloco diagonal de cor (atrás) -->
        <div class="absolute right-0 top-0 h-full w-[42%] pointer-events-none"
             :style="{ background: 'var(--cor-primaria)',
                       clipPath: 'polygon(28% 0, 100% 0, 100% 100%, 0% 100%)',
                       opacity: '0.95' }"></div>
        <!-- ruído/textura padrão (atrás) -->
        <div class="absolute inset-0 pointer-events-none tv2-pattern"></div>

        <div class="relative grid grid-cols-12 gap-6 md:gap-10 items-end max-w-[1400px] mx-auto"
             style="min-height: clamp(520px, 78vh, 820px)">

          <!-- Coluna esquerda: tipografia + meta -->
          <div class="col-span-12 lg:col-span-7 pt-4 lg:pt-16">
            <div class="flex items-center gap-3 mb-6">
              <span class="tv2-pill" :style="{ background: 'var(--cor-primaria)' }">
                <span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
                {{ loja.categoria || 'Drop' }} / {{ new Date().getFullYear() }}
              </span>
              <span class="hidden sm:inline-block h-px w-12 opacity-30 bg-current"></span>
              <span class="hidden sm:inline-block text-[10px] font-black uppercase tracking-[0.3em] opacity-50">
                Issue Nº {{ String(loja.id || 1).padStart(3, '0') }}
              </span>
            </div>

            <h1 class="tv2-title">
              <span class="block tv2-title__solid">{{ tituloLinhas[0] }}</span>
              <span v-if="tituloLinhas[1]" class="block tv2-title__outline">{{ tituloLinhas[1] }}</span>
            </h1>

            <p v-if="loja.descricao" class="mt-7 max-w-xl text-[15px] md:text-base leading-relaxed opacity-70">
              {{ loja.descricao.substring(0, 180) }}{{ loja.descricao.length > 180 ? '…' : '' }}
            </p>

            <!-- KPIs inline -->
            <div class="mt-8 md:mt-10 flex flex-wrap items-center gap-x-10 gap-y-5">
              <div v-if="loja.rating_medio">
                <p class="text-4xl md:text-5xl font-black leading-none" style="color:var(--cor-primaria)">
                  {{ Number(loja.rating_medio).toFixed(1) }}
                </p>
                <p class="text-[10px] font-black uppercase tracking-[0.28em] mt-1.5 opacity-60">Rating</p>
              </div>
              <div v-if="loja.total_avaliacoes">
                <p class="text-4xl md:text-5xl font-black leading-none">{{ loja.total_avaliacoes }}</p>
                <p class="text-[10px] font-black uppercase tracking-[0.28em] mt-1.5 opacity-60">Reviews</p>
              </div>
              <div>
                <p class="text-4xl md:text-5xl font-black leading-none">
                  {{ loja.entrega_ativa ? 'ON' : '—' }}
                </p>
                <p class="text-[10px] font-black uppercase tracking-[0.28em] mt-1.5 opacity-60">Delivery</p>
              </div>
            </div>

            <!-- CTAs -->
            <div class="mt-10 flex flex-wrap gap-3">
              <button @click="scrollToId('drops')" class="tv2-btn tv2-btn--solid">
                Ver Drops
                <span class="tv2-btn__arr">→</span>
              </button>
              <button @click="scrollToId('catalogo')" class="tv2-btn tv2-btn--ghost">
                Catálogo Completo
              </button>
            </div>
          </div>

          <!-- Coluna direita: foto/logo emoldurada -->
          <div class="col-span-12 lg:col-span-5 relative pb-2 lg:pb-12">
            <div class="relative mx-auto w-full max-w-md">

              <!-- frame principal -->
              <div class="tv2-frame">
                <video v-if="isVideo(loja.banner_url)"
                       :src="loja.banner_url" autoplay muted loop playsinline
                       class="w-full h-full object-cover"></video>
                <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome"
                     class="w-full h-full object-cover" />
                <img v-else-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
                     class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center"
                     :style="{ background: 'var(--cor-primaria)' }">
                  <span class="text-[140px] font-black text-white leading-none">
                    {{ loja.nome.charAt(0) }}
                  </span>
                </div>

                <!-- numero editorial -->
                <span class="tv2-frame__num">01</span>
                <!-- sticker shop -->
                <div class="tv2-sticker">
                  <svg viewBox="0 0 100 100" class="w-full h-full">
                    <defs>
                      <path id="circle" d="M50,50 m-38,0 a38,38 0 1,1 76,0 a38,38 0 1,1 -76,0" />
                    </defs>
                    <text font-size="11.5" font-weight="900" letter-spacing="2.4" fill="currentColor">
                      <textPath href="#circle">SHOP NOW · NEW DROP · {{ loja.nome.split(' ')[0].toUpperCase() }} · </textPath>
                    </text>
                  </svg>
                  <span class="tv2-sticker__core" :style="{ background: 'var(--cor-primaria)' }">→</span>
                </div>
              </div>

              <!-- mini frame secundário (sobreposto) -->
              <div v-if="loja.logo_url && loja.banner_url" class="tv2-frame-mini">
                <img :src="loja.logo_url" :alt="loja.nome" class="w-full h-full object-cover" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ───────── MARQUEE ───────── -->
      <div class="overflow-hidden tv2-marquee" :style="{ background: 'var(--cor-primaria)' }">
        <div class="flex items-center gap-10 whitespace-nowrap tv2-marquee__track">
          <span v-for="n in 10" :key="n"
                class="text-white font-black uppercase tracking-[0.18em] text-[13px] flex items-center gap-10 flex-shrink-0">
            <span>{{ loja.nome }}</span>
            <span class="tv2-marquee__dot">✦</span>
            <span>NEW SEASON</span>
            <span class="tv2-marquee__dot">✦</span>
            <span>FREE SHIPPING</span>
            <span class="tv2-marquee__dot">✦</span>
            <span>EST. {{ new Date().getFullYear() }}</span>
            <span class="tv2-marquee__dot">✦</span>
          </span>
        </div>
      </div>

      <!-- ───────── SECTION NAV (sticky, respeita right gutter do chrome) ───────── -->
      <nav class="tv2-sectionnav">
        <div class="tv2-sectionnav__inner">
          <a v-for="s in secoes" :key="s.id" :href="`#${s.id}`"
             @click.prevent="scrollToId(s.id)"
             class="tv2-sectionnav__link">
            <span class="tv2-sectionnav__num">{{ s.num }}</span>
            <span>{{ s.label }}</span>
          </a>
        </div>
      </nav>

      <!-- ───────── MAIN ───────── -->
      <main class="px-5 md:px-8 pb-24">
        <div class="max-w-[1400px] mx-auto">

          <!-- DROPS -->
          <section id="drops" class="pt-16 md:pt-24">
            <div class="tv2-secthead">
              <div>
                <span class="tv2-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Hot · Curated</span>
                <h2 class="tv2-secttitle">Drops</h2>
              </div>
              <span class="tv2-sectnum">02</span>
            </div>
            <ProductSlider
              title="Drops"
              :params="{ loja_id: lojaId, destaque: true }"
              :isDark="isDark"
              card-width="240px"
              card-height="340px"
              image-height="220px"
              card-border-radius="rounded-[18px]"
              :card-class="'tv2-card'"
              hover-effect="transition-all duration-300"
              :hover-border-class="'tv2-card-hover'"
              :title-class="'!text-base !font-black uppercase tracking-wider'"
              :product-name-class="'!font-black !uppercase !tracking-wide'"
              :price-class="'tv2-price'"
              :badge-class="'tv2-badge'"
              badge-text="HOT"
              :show-store-name="false"
              @product-click="selectedProduct = $event" />
          </section>

          <!-- POR TIPO -->
          <template v-if="tiposExistentes.length > 0">
            <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                     class="pt-16 md:pt-20 tv2-divider">
              <div class="tv2-secthead">
                <div class="flex items-center gap-4">
                  <div class="tv2-iconbox" :style="{ background: 'var(--cor-primaria)' }">
                    <span>{{ tipoIcon(tipo.nome) }}</span>
                  </div>
                  <div>
                    <span class="tv2-eyebrow opacity-60">Category</span>
                    <h2 class="tv2-secttitle tv2-secttitle--md">{{ tipo.nome }}</h2>
                  </div>
                </div>
                <span class="tv2-sectnum">{{ String(idx + 3).padStart(2, '0') }}</span>
              </div>
              <ProductSlider
                :title="tipo.nome"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark"
                card-width="220px"
                card-height="320px"
                image-height="200px"
                card-border-radius="rounded-[16px]"
                :card-class="'tv2-card'"
                hover-effect="transition-all duration-300"
                :hover-border-class="'tv2-card-hover'"
                :product-name-class="'!font-black !uppercase !tracking-wide'"
                :price-class="'tv2-price'"
                :show-store-name="false"
                @product-click="selectedProduct = $event" />
            </section>
          </template>

          <!-- CATEGORIAS -->
          <template v-if="categoriasExistentes.length > 0">
            <section id="categorias" class="pt-16 md:pt-24 tv2-divider">
              <div class="tv2-secthead">
                <div>
                  <span class="tv2-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Browse</span>
                  <h2 class="tv2-secttitle">Categorias</h2>
                </div>
                <span class="tv2-sectnum">{{ String(tiposExistentes.length + 3).padStart(2, '0') }}</span>
              </div>

              <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-14">
                <button v-for="cat in categoriasExistentes" :key="cat.id"
                        @click="scrollToId('cat-' + cat.id)" class="tv2-cattile">
                  <span class="tv2-cattile__icon">{{ cat.icone }}</span>
                  <span class="tv2-cattile__name">{{ cat.nome }}</span>
                  <span class="tv2-cattile__arrow">→</span>
                </button>
              </div>

              <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-14">
                <div class="flex items-center gap-4 mb-6">
                  <span class="text-2xl">{{ cat.icone }}</span>
                  <h3 class="text-2xl md:text-3xl font-black uppercase tracking-tight">{{ cat.nome }}</h3>
                  <div class="flex-1 h-[2px] rounded-full" :style="{ background: 'var(--cor-primaria)', opacity: '0.3' }"></div>
                </div>
                <ProductSlider
                  :title="cat.nome"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :isDark="isDark"
                  card-width="210px"
                  card-height="310px"
                  image-height="200px"
                  card-border-radius="rounded-[16px]"
                  :card-class="'tv2-card'"
                  hover-effect="transition-all duration-300"
                  :hover-border-class="'tv2-card-hover'"
                  :product-name-class="'!font-black !uppercase !tracking-wide'"
                  :price-class="'tv2-price'"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </div>
            </section>
          </template>

          <!-- INFO ENTREGA + PAGAMENTO -->
          <section class="pt-16 md:pt-20 grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6 tv2-divider">
            <div class="tv2-info">
              <div class="tv2-info__head">
                <div class="tv2-iconbox tv2-iconbox--sm" :style="{ background: 'var(--cor-primaria)' }">
                  <span>🚚</span>
                </div>
                <div>
                  <span class="tv2-eyebrow opacity-60">Shipping</span>
                  <h3 class="tv2-info__title">Entrega</h3>
                </div>
              </div>
              <div v-if="!opcoesEntrega.length" class="text-sm opacity-60 mt-4">Sem opções configuradas.</div>
              <div v-else class="mt-4 divide-y" :class="isDark ? 'divide-white/10' : 'divide-black/10'">
                <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="flex justify-between items-center py-3">
                  <div>
                    <p class="font-black uppercase text-sm tracking-wide">{{ opcao.nome }}</p>
                    <p v-if="opcao.tempo_estimado" class="text-xs opacity-60 mt-0.5">{{ opcao.tempo_estimado }}</p>
                  </div>
                  <span class="font-black text-base" style="color:var(--cor-primaria)">
                    {{ opcao.preco == 0 ? 'FREE' : formatPrice(opcao.preco) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="tv2-info">
              <div class="tv2-info__head">
                <div class="tv2-iconbox tv2-iconbox--sm" :style="{ background: 'var(--cor-primaria)' }">
                  <span>💳</span>
                </div>
                <div>
                  <span class="tv2-eyebrow opacity-60">Checkout</span>
                  <h3 class="tv2-info__title">Pagamento</h3>
                </div>
              </div>
              <div class="mt-4 flex flex-wrap gap-2">
                <span v-for="m in metodosPagamento" :key="m.id" class="tv2-paychip">
                  {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
                </span>
              </div>
            </div>
          </section>

          <!-- CATÁLOGO -->
          <section id="catalogo" class="pt-16 md:pt-24 tv2-divider">
            <div class="tv2-secthead">
              <div>
                <span class="tv2-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Full Collection</span>
                <h2 class="tv2-secttitle">Catálogo</h2>
              </div>
              <span class="tv2-sectnum">{{ String(tiposExistentes.length + 4).padStart(2, '0') }}</span>
            </div>
            <ProductCatalog
              :loja-id="lojaId" :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="220px"
              card-border-radius="rounded-[16px]"
              :card-class="'tv2-card'"
              hover-effect="transition-all duration-300"
              :hover-border-class="'tv2-card-hover'"
              tab-border-radius="rounded-full"
              :active-tab-class="'tv2-tab tv2-tab--active'"
              :inactive-tab-dark-class="'tv2-tab'"
              :inactive-tab-light-class="'tv2-tab'"
              :active-sub-tab-class="'tv2-subtab tv2-subtab--active'"
              :inactive-sub-tab-dark-class="'tv2-subtab'"
              :inactive-sub-tab-light-class="'tv2-subtab'"
              input-border-radius="rounded-xl"
              filter-container-radius="rounded-[18px]"
              :filter-container-class="'tv2-filterbox'"
              :product-name-hover-class="'group-hover:opacity-70'"
              :product-name-class="'!font-black !uppercase !tracking-wide'"
              :price-class="'tv2-price'"
              :badge-class="'tv2-badge'"
              badge-text="HOT"
              :indicator-active-class="'tv2-indicator'"
              :stock-active-class="'tv2-stock-on'"
              :clear-filter-class="'tv2-btn-tiny tv2-btn-tiny--accent'"
              @product-click="selectedProduct = $event" />
          </section>

          <!-- AVALIAÇÕES -->
          <section id="avaliacoes" class="pt-16 md:pt-24 tv2-divider">
            <div class="tv2-secthead">
              <div>
                <span class="tv2-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Community</span>
                <h2 class="tv2-secttitle">Reviews</h2>
              </div>
              <span class="tv2-sectnum">{{ String(tiposExistentes.length + 5).padStart(2, '0') }}</span>
            </div>
            <AvaliacaoLoja
              :loja-id="lojaId" :isDark="isDark"
              summary-border-radius="rounded-[18px]"
              form-border-radius="rounded-[18px]"
              review-card-border-radius="rounded-[16px]"
              button-border-radius="rounded-xl"
              textarea-border-radius="rounded-xl"
              :star-active-class="'tv2-star-on'"
              :star-inactive-class="isDark ? 'text-white/15' : 'text-black/15'"
              :submit-button-class="'tv2-btn tv2-btn--solid'"
              :own-review-border-class="'tv2-review-own'"
              own-badge-class="tv2-ownbadge"
              link-class="tv2-link"
              :progress-bar-class="'tv2-progress'"
              @rating-updated="onRatingUpdated" />
          </section>

          <!-- FOOTER -->
          <footer class="pt-20 md:pt-28 pb-12">
            <div class="tv2-bigword">
              <span>{{ loja.nome.toUpperCase() }}</span>
            </div>
            <div class="mt-10 flex flex-wrap items-center justify-between gap-6 pt-8 border-t-2"
                 :style="{ borderColor: 'var(--cor-primaria)' }">
              <div class="flex items-center gap-3">
                <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
                     class="w-10 h-10 rounded-lg object-cover" />
                <div v-else class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-black"
                     :style="{ background: 'var(--cor-primaria)' }">{{ loja.nome.charAt(0) }}</div>
                <span class="text-xs font-black uppercase tracking-[0.3em] opacity-60">
                  © {{ new Date().getFullYear() }} · Stay Bold
                </span>
              </div>
              <div class="flex flex-wrap gap-5 text-[11px] font-black uppercase tracking-[0.25em]">
                <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="tv2-foot-link">Returns</button>
                <button v-if="loja.termos_servico"   @click="modalPolitica = 'termos'"     class="tv2-foot-link">Terms</button>
                <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="tv2-foot-link">Privacy</button>
              </div>
            </div>
          </footer>
        </div>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-[20px] w-full max-w-lg max-h-[80vh] overflow-y-auto border-2 shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border-zinc-800 text-white' : 'bg-white border-zinc-200 text-zinc-900'">
          <div class="flex items-center justify-between px-6 py-4 border-b-2 sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'">
            <h3 class="font-black uppercase tracking-[0.25em] text-sm">
              {{ modalPolitica === 'devolucao' ? 'Returns' : modalPolitica === 'termos' ? 'Terms' : 'Privacy' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-9 h-9 rounded-xl flex items-center justify-center font-black text-white text-lg"
              :style="{ background: 'var(--cor-primaria)' }">×</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap opacity-80">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao
             : modalPolitica === 'termos'    ? loja.termos_servico
             : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <!-- 404 -->
    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'">
      <p class="text-7xl font-black mb-4" style="color:var(--cor-primaria)">404</p>
      <p class="text-xl font-bold uppercase mb-8 opacity-70">Loja não encontrada</p>
      <button @click="$router.back()" class="tv2-btn tv2-btn--solid">Voltar</button>
    </div>
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
  name: 'TemplateVibrante',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#f43f5e',
      '--cor-secundaria': props.tema?.corSecundaria || '#09090b',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }
    function isVideo (url) { return /\.(mp4|webm|mov|mkv)$/i.test(url || '') }

    const secoes = [
      { id: 'drops',      label: 'Drops',      num: '01' },
      { id: 'categorias', label: 'Categorias', num: '02' },
      { id: 'catalogo',   label: 'Catálogo',   num: '03' },
      { id: 'avaliacoes', label: 'Reviews',    num: '04' },
    ]

    return { isDark, cssVars, user, toggleDark, isVideo, secoes, ...lojaData }
  },

  computed: {
    tituloLinhas () {
      const partes = (this.loja?.nome || '').split(' ')
      if (partes.length === 1) return [partes[0], '']
      const meio = Math.ceil(partes.length / 2)
      return [partes.slice(0, meio).join(' '), partes.slice(meio).join(' ')]
    },
  },
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   CORE TOKENS
   ═══════════════════════════════════════════════════════════════ */
.tv2 { font-family: 'Inter', system-ui, sans-serif; }
.tv2--dark  { background: var(--cor-secundaria, #09090b); color: #fafafa; }
.tv2--light { background: #fafafa; color: #09090b; }

/* ═══════════════════════════════════════════════════════════════
   LOADER
   ═══════════════════════════════════════════════════════════════ */
.tv2-loader { display: flex; gap: 6px; }
.tv2-loader span {
  width: 12px; height: 32px; background: var(--cor-primaria);
  animation: tv2-bounce 0.9s ease-in-out infinite;
}
.tv2-loader span:nth-child(2) { animation-delay: .15s; }
.tv2-loader span:nth-child(3) { animation-delay: .3s; }
@keyframes tv2-bounce {
  0%, 100% { transform: scaleY(.3); opacity: .5; }
  50%      { transform: scaleY(1);  opacity: 1; }
}

/* ═══════════════════════════════════════════════════════════════
   TOP BAR
   ═══════════════════════════════════════════════════════════════ */
.tv2-iconbtn {
  width: 42px; height: 42px;
  border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1.5px solid currentColor; opacity: .85;
  transition: all .25s ease;
  background: transparent;
}
.tv2-iconbtn:hover {
  background: var(--cor-primaria);
  color: #fff !important; opacity: 1;
  border-color: var(--cor-primaria);
  transform: translateY(-1px);
}

/* ═══════════════════════════════════════════════════════════════
   HERO PATTERN + TEXT
   ═══════════════════════════════════════════════════════════════ */
.tv2-pattern {
  background-image: repeating-linear-gradient(
    135deg,
    transparent 0 18px,
    rgba(255,255,255,.04) 18px 19px
  );
}
.tv2--light .tv2-pattern {
  background-image: repeating-linear-gradient(
    135deg,
    transparent 0 18px,
    rgba(0,0,0,.04) 18px 19px
  );
}

.tv2-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 14px; border-radius: 999px;
  font-size: 11px; font-weight: 900;
  text-transform: uppercase; letter-spacing: .14em;
  color: #fff;
}

.tv2-title {
  font-size: clamp(3.2rem, 9.5vw, 9rem);
  line-height: .85;
  letter-spacing: -0.04em;
  font-weight: 900;
  text-transform: uppercase;
  word-break: break-word;
}
.tv2-title__solid   { color: currentColor; }
.tv2-title__outline {
  color: transparent;
  -webkit-text-stroke: 2.5px currentColor;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════ */
.tv2-btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 16px 28px;
  border-radius: 14px;
  font-size: 12px; font-weight: 900;
  text-transform: uppercase; letter-spacing: .14em;
  transition: all .25s ease;
  cursor: pointer;
  white-space: nowrap;
}
.tv2-btn--solid {
  background: var(--cor-primaria); color: #fff;
  box-shadow: 0 10px 30px -8px color-mix(in oklab, var(--cor-primaria), transparent 50%);
}
.tv2-btn--solid:hover { transform: translateY(-2px) rotate(-.6deg); }
.tv2-btn__arr { transition: transform .25s ease; }
.tv2-btn--solid:hover .tv2-btn__arr { transform: translateX(4px); }

.tv2-btn--ghost {
  border: 2px solid currentColor;
  background: transparent;
}
.tv2-btn--ghost:hover {
  background: currentColor;
  color: var(--cor-secundaria);
  transform: translateY(-2px) rotate(.6deg);
}
.tv2--light .tv2-btn--ghost:hover { color: #fff; background: #09090b; }

/* ═══════════════════════════════════════════════════════════════
   FRAME (hero image)
   ═══════════════════════════════════════════════════════════════ */
.tv2-frame {
  position: relative;
  aspect-ratio: 4 / 5;
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255,255,255,.06);
  transform: rotate(2deg);
  box-shadow: 0 30px 60px -20px rgba(0,0,0,.4);
}
.tv2--light .tv2-frame { background: rgba(0,0,0,.04); }
.tv2-frame__num {
  position: absolute; top: 14px; left: 16px;
  font-size: 11px; font-weight: 900; color: #fff;
  letter-spacing: .3em;
  background: rgba(0,0,0,.55);
  padding: 5px 10px; border-radius: 999px;
  backdrop-filter: blur(6px);
}

.tv2-sticker {
  position: absolute; bottom: -28px; right: -28px;
  width: 116px; height: 116px;
  color: #fff;
  animation: tv2-spin 18s linear infinite;
}
.tv2-sticker__core {
  position: absolute; inset: 28%;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 900; color: #fff;
  animation: tv2-spin 18s linear infinite reverse;
}
@keyframes tv2-spin { to { transform: rotate(360deg); } }

.tv2-frame-mini {
  position: absolute; left: -18px; bottom: -18px;
  width: 84px; height: 84px;
  border-radius: 18px;
  overflow: hidden;
  border: 4px solid var(--cor-secundaria);
  background: var(--cor-secundaria);
  transform: rotate(-6deg);
  box-shadow: 0 12px 24px -6px rgba(0,0,0,.4);
}
.tv2--light .tv2-frame-mini { border-color: #fafafa; background: #fafafa; }

/* ═══════════════════════════════════════════════════════════════
   MARQUEE
   ═══════════════════════════════════════════════════════════════ */
.tv2-marquee { padding: 16px 0; border-top: 1px solid rgba(255,255,255,.15); border-bottom: 1px solid rgba(255,255,255,.15); }
.tv2-marquee__track { animation: tv2-marquee 30s linear infinite; }
.tv2-marquee__dot { opacity: .8; font-size: 14px; }
@keyframes tv2-marquee {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* ═══════════════════════════════════════════════════════════════
   SECTION NAV (sticky) — respeita o gutter direito (chrome)
   ═══════════════════════════════════════════════════════════════ */
.tv2-sectionnav {
  position: sticky; top: 0; z-index: 20;
  /* deixar espaço à direita para multiCart/UserProfile/Bell */
  padding: 10px 18rem 10px 20px;
  backdrop-filter: blur(14px);
  background: color-mix(in oklab, var(--cor-secundaria) 70%, transparent);
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.tv2--light .tv2-sectionnav {
  background: color-mix(in oklab, #fafafa 80%, transparent);
  border-bottom-color: rgba(0,0,0,.08);
}
@media (max-width: 768px) {
  .tv2-sectionnav { padding-right: 8.5rem; }
}
.tv2-sectionnav__inner {
  display: flex; gap: 6px; overflow-x: auto;
  scrollbar-width: none;
}
.tv2-sectionnav__inner::-webkit-scrollbar { display: none; }
.tv2-sectionnav__link {
  display: inline-flex; align-items: baseline; gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 11px; font-weight: 900;
  text-transform: uppercase; letter-spacing: .15em;
  white-space: nowrap;
  transition: all .2s ease;
  border: 1px solid transparent;
}
.tv2-sectionnav__link:hover {
  background: var(--cor-primaria); color: #fff;
}
.tv2-sectionnav__num {
  font-size: 9px; opacity: .55; font-feature-settings: 'tnum';
}
.tv2-sectionnav__link:hover .tv2-sectionnav__num { opacity: 1; }

/* ═══════════════════════════════════════════════════════════════
   SECTION HEADERS
   ═══════════════════════════════════════════════════════════════ */
.tv2-divider { border-top: 2px solid var(--cor-primaria); }
.tv2-secthead {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 24px; margin: 56px 0 36px;
}
.tv2-eyebrow {
  display: inline-block;
  font-size: 11px; font-weight: 900;
  text-transform: uppercase; letter-spacing: .25em;
  margin-bottom: 8px;
}
.tv2-secttitle {
  font-size: clamp(2.4rem, 5.5vw, 4.6rem);
  font-weight: 900; line-height: .9;
  letter-spacing: -0.03em;
  text-transform: uppercase;
}
.tv2-secttitle--md {
  font-size: clamp(1.8rem, 3.6vw, 3rem);
  letter-spacing: -0.025em;
}
.tv2-sectnum {
  display: none;
  font-size: clamp(4rem, 7vw, 7rem);
  font-weight: 900; line-height: .9;
  opacity: .08;
  letter-spacing: -0.05em;
}
@media (min-width: 768px) { .tv2-sectnum { display: block; } }

.tv2-iconbox {
  width: 56px; height: 56px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; color: #fff;
  flex-shrink: 0;
}
.tv2-iconbox--sm { width: 44px; height: 44px; font-size: 20px; border-radius: 12px; }

/* ═══════════════════════════════════════════════════════════════
   PRODUCT CARDS (passados por classe via prop)
   ═══════════════════════════════════════════════════════════════ */
:deep(.tv2-card) { border-width: 2px !important; }
:deep(.tv2-card-hover):hover {
  transform: translateY(-4px) rotate(-.4deg);
  border-color: var(--cor-primaria) !important;
  box-shadow: 0 18px 40px -16px color-mix(in oklab, var(--cor-primaria), transparent 60%);
}
:deep(.tv2-price) {
  color: var(--cor-primaria);
  font-weight: 900;
  font-size: 15px;
  letter-spacing: -0.01em;
}
:deep(.tv2-badge) {
  background: var(--cor-primaria);
  color: #fff;
  font-weight: 900;
  border-radius: 6px;
  padding: 3px 7px;
  font-size: 10px;
  letter-spacing: .12em;
}

/* ═══════════════════════════════════════════════════════════════
   CATEGORY TILES
   ═══════════════════════════════════════════════════════════════ */
.tv2-cattile {
  position: relative;
  display: flex; align-items: center; gap: 14px;
  padding: 18px 18px;
  border: 2px solid currentColor;
  border-radius: 16px;
  text-align: left;
  font-weight: 900; text-transform: uppercase;
  font-size: 13px; letter-spacing: .08em;
  transition: all .25s ease;
  background: transparent;
  overflow: hidden;
}
.tv2-cattile::before {
  content: ''; position: absolute; inset: 0;
  background: var(--cor-primaria);
  transform: translateY(101%);
  transition: transform .35s ease;
  z-index: 0;
}
.tv2-cattile:hover::before { transform: translateY(0); }
.tv2-cattile:hover { color: #fff; border-color: var(--cor-primaria); }
.tv2-cattile > * { position: relative; z-index: 1; }
.tv2-cattile__icon { font-size: 22px; }
.tv2-cattile__name { flex: 1; }
.tv2-cattile__arrow { opacity: .4; transition: all .25s ease; }
.tv2-cattile:hover .tv2-cattile__arrow { opacity: 1; transform: translateX(4px); }

/* ═══════════════════════════════════════════════════════════════
   INFO BOXES
   ═══════════════════════════════════════════════════════════════ */
.tv2-info {
  border: 2px solid currentColor;
  border-radius: 22px;
  padding: 24px;
  position: relative;
  overflow: hidden;
}
.tv2-info::after {
  content: ''; position: absolute; inset: auto -40px -40px auto;
  width: 140px; height: 140px; border-radius: 50%;
  background: var(--cor-primaria); opacity: .08;
  pointer-events: none;
}
.tv2-info__head { display: flex; align-items: center; gap: 14px; }
.tv2-info__title {
  font-size: 22px; font-weight: 900;
  text-transform: uppercase; letter-spacing: -0.01em;
  margin-top: 2px;
}
.tv2-paychip {
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 12px; font-weight: 800;
  text-transform: uppercase; letter-spacing: .08em;
  border: 1.5px solid currentColor;
  opacity: .8;
}

/* ═══════════════════════════════════════════════════════════════
   CATALOG TABS / FILTERS / REVIEWS
   ═══════════════════════════════════════════════════════════════ */
:deep(.tv2-tab) {
  background: transparent;
  border: 1.5px solid currentColor;
  color: currentColor; opacity: .65;
  text-transform: uppercase; font-weight: 900;
  font-size: 11px; letter-spacing: .15em;
  padding: 9px 16px !important;
  transition: all .2s ease;
}
:deep(.tv2-tab:hover) { opacity: 1; }
:deep(.tv2-tab--active) {
  background: var(--cor-primaria) !important;
  color: #fff !important;
  border-color: var(--cor-primaria) !important;
  opacity: 1;
}
:deep(.tv2-subtab) {
  background: transparent;
  color: currentColor; opacity: .55;
  font-weight: 800; font-size: 10px;
  text-transform: uppercase; letter-spacing: .12em;
}
:deep(.tv2-subtab--active) {
  color: var(--cor-primaria) !important;
  opacity: 1;
  text-decoration: underline;
  text-underline-offset: 4px;
  text-decoration-thickness: 2px;
}
:deep(.tv2-filterbox) { border-width: 2px !important; }
:deep(.tv2-indicator) {
  background: var(--cor-primaria);
  color: #fff;
  font-weight: 900; text-transform: uppercase;
  letter-spacing: .12em;
}
:deep(.tv2-stock-on) {
  border: 1.5px solid var(--cor-primaria) !important;
  background: color-mix(in oklab, var(--cor-primaria), transparent 85%) !important;
  color: var(--cor-primaria) !important;
}
:deep(.tv2-btn-tiny--accent) {
  color: var(--cor-primaria) !important;
  background: color-mix(in oklab, var(--cor-primaria), transparent 88%) !important;
}

/* Reviews */
:deep(.tv2-star-on) { color: var(--cor-primaria); }
:deep(.tv2-progress) { background: var(--cor-primaria); }
:deep(.tv2-review-own) {
  border: 2px solid var(--cor-primaria) !important;
  background: color-mix(in oklab, var(--cor-primaria), transparent 92%) !important;
}
:deep(.tv2-ownbadge) {
  background: var(--cor-primaria);
  color: #fff;
  font-weight: 900; text-transform: uppercase; letter-spacing: .12em;
}
:deep(.tv2-link) {
  color: var(--cor-primaria); font-weight: 800;
  text-decoration: underline; text-underline-offset: 3px;
}

/* ═══════════════════════════════════════════════════════════════
   FOOTER BIG WORD
   ═══════════════════════════════════════════════════════════════ */
.tv2-bigword {
  font-size: clamp(3rem, 14vw, 12rem);
  font-weight: 900;
  line-height: .85;
  letter-spacing: -0.05em;
  text-transform: uppercase;
  text-align: center;
  color: transparent;
  -webkit-text-stroke: 2px currentColor;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
  user-select: none;
}
.tv2-foot-link { transition: color .2s ease; }
.tv2-foot-link:hover { color: var(--cor-primaria); }
</style>
