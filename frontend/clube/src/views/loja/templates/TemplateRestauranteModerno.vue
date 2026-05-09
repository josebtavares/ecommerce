<!-- TemplateRestauranteModerno.vue — Professional Restaurant Template
     Hero full-bleed · Horizontal sticky nav · Editorial grid with numbered sections
     Typography: Playfair Display (títulos) + Inter (corpo) + JetBrains Mono (labels)
     Acento configurável via --cor-primaria (default: #f97316 laranja)
-->
<template>
  <div
    class="resto-root transition-colors duration-500"
    :class="isDark ? 'dark' : 'light'"
    :style="cssVars"
  >
    <ProductInfoCard
      :produto="selectedProduct"
      :loja="loja"
      :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)"
    />

    <MultiCart ref="cart" :isDark="isDark" />

    <Profile
      :data="user"
      :isDark="isDark"
      class="z-40"
      @log_out="logOut()"
    />

    <!-- Loading -->
    <div v-if="loading" class="resto-loading">
      <div class="resto-loading__flame">
        <div class="resto-loading__flame-inner"></div>
      </div>
      <span class="resto-loading__text">A preparar...</span>
    </div>

    <template v-else-if="loja">
      <!-- ══════════════════════════════════════════
           HERO
      ══════════════════════════════════════════ -->
      <section class="resto-hero" ref="heroRef">
        <video
          v-if="isVideo(loja.banner_url)"
          :src="loja.banner_url"
          class="resto-hero__media"
          autoplay
          muted
          loop
          playsinline
        ></video>
        <img
          v-else
          :src="loja.banner_url || backendUrl + '/media/lojas/default_banner.jpg'"
          :alt="loja.nome"
          class="resto-hero__media"
        />
        
        <!-- Grain overlay for texture -->
        <div class="resto-hero__grain"></div>
        
        <!-- Gradient overlays -->
        <div class="resto-hero__overlay"></div>
        <div class="resto-hero__vignette"></div>

        <!-- Top Nav -->
        <nav class="resto-hero__nav">
          <div class="resto-hero__nav-left">
            <button @click="$router.back()" class="resto-nav-back">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
              <span>Voltar</span>
            </button>

            <button @click="toggleDark" class="resto-nav-icon">
              <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            </button>
          </div>

          <!-- Center brand indicator (hidden on mobile) -->
          <div class="resto-hero__nav-center">
            <span class="resto-hero__nav-tag">{{ loja.categoria || 'Restaurante' }}</span>
          </div>

          <!-- Right spacer for UserProfile/NotificacaoSino/MultiCart -->
          <div class="resto-hero__nav-right"></div>
        </nav>

        <!-- Hero Content -->
        <div class="resto-hero__content">
          <!-- Decorative line + label -->
          <div class="resto-hero__label-row">
            <div class="resto-hero__label-line"></div>
            <span class="resto-hero__label">
              {{ loja.localizacao || 'Portugal' }} · Est. {{ currentYear }}
            </span>
          </div>

          <!-- Title with split styling -->
          <h1 class="resto-hero__title">
            <span class="resto-hero__title-main">{{ firstWord }}</span>
            <span class="resto-hero__title-outline">{{ restWords }}</span>
          </h1>

          <!-- Description + CTAs + Stats row -->
          <div class="resto-hero__bottom">
            <div class="resto-hero__info">
              <p v-if="loja.descricao" class="resto-hero__desc">
                {{ truncateText(loja.descricao, 140) }}
              </p>

              <div class="resto-hero__ctas">
                <button @click="scrollToId('resto-menu')" class="resto-btn-primary">
                  <span>Ver Menu</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </button>

                <button @click="scrollToId('resto-avaliacoes')" class="resto-btn-ghost">
                  Avaliações
                </button>
              </div>
            </div>

            <!-- Stats -->
            <div class="resto-hero__stats">
              <div v-if="loja.rating_medio" class="resto-hero__stat">
                <span class="resto-hero__stat-value resto-hero__stat-value--accent">
                  {{ ratingFormatted }}
                </span>
                <span class="resto-hero__stat-label">Avaliação</span>
              </div>

              <div v-if="loja.total_avaliacoes" class="resto-hero__stat">
                <span class="resto-hero__stat-value">{{ loja.total_avaliacoes }}</span>
                <span class="resto-hero__stat-label">Reviews</span>
              </div>

              <div v-if="loja.entrega_ativa" class="resto-hero__stat">
                <span class="resto-hero__stat-value resto-hero__stat-value--accent">✓</span>
                <span class="resto-hero__stat-label">Delivery</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Large decorative year -->
        <div class="resto-hero__year" aria-hidden="true">{{ currentYear }}</div>

        <!-- Scroll indicator -->
        <div class="resto-hero__scroll">
          <span>Scroll</span>
          <div class="resto-hero__scroll-line"></div>
        </div>
      </section>

      <!-- ══════════════════════════════════════════
           STICKY HORIZONTAL NAV
      ══════════════════════════════════════════ -->
      <nav class="resto-nav" ref="stickyNav">
        <div class="resto-nav__inner hide-scroll">
          <button
            class="resto-nav__item"
            :class="{ 'resto-nav__item--active': activeSection === 'resto-sobre' }"
            @click="scrollToId('resto-sobre')"
          >
            Sobre
          </button>

          <button
            class="resto-nav__item"
            :class="{ 'resto-nav__item--active': activeSection === 'resto-destaques' }"
            @click="scrollToId('resto-destaques')"
          >
            Destaques
          </button>

          <button
            v-for="tipo in tiposExistentes"
            :key="tipo.id"
            class="resto-nav__item capitalize"
            :class="{ 'resto-nav__item--active': activeSection === 'resto-tipo-' + tipo.id }"
            @click="scrollToId('resto-tipo-' + tipo.id)"
          >
            {{ tipo.nome }}
          </button>

          <button
            v-for="cat in categoriasExistentes"
            :key="cat.id"
            class="resto-nav__item capitalize"
            :class="{ 'resto-nav__item--active': activeSection === 'resto-cat-' + cat.id }"
            @click="scrollToId('resto-cat-' + cat.id)"
          >
            {{ cat.nome }}
          </button>

          <button
            class="resto-nav__item"
            :class="{ 'resto-nav__item--active': activeSection === 'resto-menu' }"
            @click="scrollToId('resto-menu')"
          >
            Menu
          </button>

          <button
            class="resto-nav__item"
            :class="{ 'resto-nav__item--active': activeSection === 'resto-avaliacoes' }"
            @click="scrollToId('resto-avaliacoes')"
          >
            Avaliações
          </button>
        </div>
      </nav>

      <!-- ══════════════════════════════════════════
           MAIN CONTENT
      ══════════════════════════════════════════ -->
      <main class="resto-main">
        <!-- 00 — SOBRE -->
        <section class="resto-section" id="resto-sobre">
          <div class="resto-section__grid">
            <div class="resto-section__num-col">
              <span class="resto-section__num">00</span>
            </div>

            <div class="resto-section__body">
              <div class="resto-about">
                <div class="resto-about__text-col">
                  <div class="resto-section__sub">Sobre Nós</div>
                  <p class="resto-about__text">
                    {{ loja.descricao || 'Um restaurante construído com paixão pela gastronomia, onde cada prato conta uma história e cada refeição é uma experiência memorável.' }}
                  </p>
                </div>

                <div class="resto-about__meta">
                  <!-- Delivery options -->
                  <div v-if="opcoesEntrega.length" class="resto-meta-block">
                    <div class="resto-meta-label">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="1" y="3" width="15" height="13" rx="2"/>
                        <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                        <circle cx="5.5" cy="18.5" r="2.5"/>
                        <circle cx="18.5" cy="18.5" r="2.5"/>
                      </svg>
                      <span>Entrega</span>
                    </div>
                    <div class="resto-meta-rows">
                      <div
                        v-for="opcao in opcoesEntrega"
                        :key="opcao.id"
                        class="resto-meta-row"
                      >
                        <span>{{ opcao.nome }}</span>
                        <span class="resto-meta-row__price">
                          {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Payment methods -->
                  <div v-if="metodosPagamento.length" class="resto-meta-block">
                    <div class="resto-meta-label">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="1" y="4" width="22" height="16" rx="2"/>
                        <line x1="1" y1="10" x2="23" y2="10"/>
                      </svg>
                      <span>Pagamento</span>
                    </div>
                    <div class="resto-meta-chips">
                      <span
                        v-for="m in metodosPagamento"
                        :key="m.id"
                        class="resto-chip"
                      >
                        {{ m.tipo }}
                      </span>
                    </div>
                  </div>

                  <!-- Location -->
                  <div v-if="loja.localizacao" class="resto-meta-block">
                    <div class="resto-meta-label">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                        <circle cx="12" cy="10" r="3"/>
                      </svg>
                      <span>Localização</span>
                    </div>
                    <p class="resto-meta-location">{{ loja.localizacao }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 01 — DESTAQUES -->
        <section class="resto-section" id="resto-destaques">
          <div class="resto-section__grid">
            <div class="resto-section__num-col">
              <span class="resto-section__num">01</span>
            </div>

            <div class="resto-section__body">
              <div class="resto-section__header">
                <div>
                  <div class="resto-section__sub">Chef&apos;s Selection</div>
                  <h2 class="resto-section__title">Destaques</h2>
                </div>
                <div class="resto-section__line"></div>
              </div>

              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="240px"
                image-height="300px"
                card-height="420px"
                card-border-radius="rounded-sm"
                hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-500"
                hover-border-class=""
                product-name-class="resto-product-name"
                price-class="resto-product-price"
                badge-text="CHEF"
                badge-class="resto-badge"
                :show-store-name="false"
                :show-stock="false"
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- POR TIPO -->
        <section
          v-for="(tipo, idx) in tiposExistentes"
          :key="tipo.id"
          :id="'resto-tipo-' + tipo.id"
          class="resto-section"
        >
          <div class="resto-section__grid">
            <div class="resto-section__num-col">
              <span class="resto-section__num">
                {{ String(idx + 2).padStart(2, '0') }}
              </span>
            </div>

            <div class="resto-section__body">
              <div class="resto-section__header">
                <div>
                  <div class="resto-section__sub">Categoria</div>
                  <h2 class="resto-section__title capitalize">{{ tipo.nome }}</h2>
                </div>
                <div class="resto-section__line"></div>
              </div>

              <ProductSlider
                :title="tipo.nome"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark"
                card-width="220px"
                image-height="280px"
                card-height="400px"
                card-border-radius="rounded-sm"
                hover-effect="hover:-translate-y-2 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                product-name-class="resto-product-name"
                price-class="resto-product-price"
                :show-store-name="false"
                :show-stock="false"
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- POR CATEGORIA -->
        <section
          v-for="(cat, idx) in categoriasExistentes"
          :key="cat.id"
          :id="'resto-cat-' + cat.id"
          class="resto-section"
        >
          <div class="resto-section__grid">
            <div class="resto-section__num-col">
              <span class="resto-section__num">
                {{ String(tiposExistentes.length + idx + 2).padStart(2, '0') }}
              </span>
            </div>

            <div class="resto-section__body">
              <div class="resto-section__header">
                <div>
                  <div class="resto-section__sub">Especialidade</div>
                  <h2 class="resto-section__title capitalize">{{ cat.nome }}</h2>
                </div>
                <div class="resto-section__line"></div>
              </div>

              <ProductSlider
                :title="cat.nome"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark"
                card-width="220px"
                image-height="280px"
                card-height="400px"
                card-border-radius="rounded-sm"
                hover-effect="hover:-translate-y-2 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                product-name-class="resto-product-name"
                price-class="resto-product-price"
                :show-store-name="false"
                :show-stock="false"
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- MENU COMPLETO -->
        <section class="resto-section" id="resto-menu">
          <div class="resto-section__grid">
            <div class="resto-section__num-col">
              <span class="resto-section__num resto-section__num--text">MENU</span>
            </div>

            <div class="resto-section__body">
              <div class="resto-section__header">
                <div>
                  <div class="resto-section__sub">A Carta</div>
                  <h2 class="resto-section__title">Menu Completo</h2>
                </div>
                <div class="resto-section__line"></div>
              </div>

              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="280px"
                card-border-radius="rounded-sm"
                hover-effect="hover:-translate-y-2 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                tab-border-radius="rounded-none"
                :active-tab-class="'resto-tab--active'"
                :inactive-tab-dark-class="'resto-tab resto-tab--dark'"
                :inactive-tab-light-class="'resto-tab resto-tab--light'"
                input-border-radius="rounded-sm"
                filter-container-radius="rounded-sm"
                product-name-class="resto-product-name"
                product-name-hover-class="group-hover:opacity-70"
                price-class="resto-product-price"
                :show-stock="false"
                :show-badges="true"
                :show-category-badges="false"
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- AVALIAÇÕES -->
        <section class="resto-section" id="resto-avaliacoes">
          <div class="resto-section__grid">
            <div class="resto-section__num-col">
              <span class="resto-section__num resto-section__num--text">REVIEWS</span>
            </div>

            <div class="resto-section__body">
              <div class="resto-section__header">
                <div>
                  <div class="resto-section__sub">Comunidade</div>
                  <h2 class="resto-section__title">Avaliações</h2>
                </div>
                <div class="resto-section__line"></div>
              </div>

              <AvaliacaoLoja
                :loja-id="lojaId"
                :isDark="isDark"
                summary-border-radius="rounded-sm"
                form-border-radius="rounded-sm"
                review-card-border-radius="rounded-sm"
                button-border-radius="rounded-sm"
                textarea-border-radius="rounded-sm"
                :star-active-class="'resto-star-active'"
                :star-inactive-class="'resto-star-inactive'"
                progress-bar-class="resto-progress-bar"
                :submit-button-class="'resto-btn-primary w-full justify-center'"
                :review-card-class="'resto-review-card'"
                :own-review-border-class="isDark ? 'border-b resto-border resto-own-review' : 'border-b resto-border resto-own-review-light'"
                :load-more-button-class="'resto-btn-ghost text-xs tracking-widest uppercase'"
                @rating-updated="onRatingUpdated"
              />
            </div>
          </div>
        </section>

        <!-- FOOTER -->
        <footer class="resto-footer">
          <div class="resto-footer__top">
            <div class="resto-footer__brand-col">
              <div class="resto-footer__brand">{{ loja.nome }}</div>
              <div class="resto-footer__tagline">
                {{ loja.categoria || 'Restaurante' }} · {{ loja.localizacao || 'Portugal' }}
              </div>
            </div>

            <div class="resto-footer__links">
              <button
                v-if="loja.politica_devolucao"
                @click="modalPolitica = 'devolucao'"
                class="resto-footer__link"
              >
                Devoluções
              </button>

              <button
                v-if="loja.termos_servico"
                @click="modalPolitica = 'termos'"
                class="resto-footer__link"
              >
                Termos
              </button>

              <button
                v-if="loja.politica_privacidade"
                @click="modalPolitica = 'privacidade'"
                class="resto-footer__link"
              >
                Privacidade
              </button>
            </div>
          </div>

          <div class="resto-footer__bottom">
            <span class="resto-footer__copy">
              &copy; {{ currentYear }} {{ loja.nome }}. Todos os direitos reservados.
            </span>
          </div>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div
        v-if="modalPolitica"
        class="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-0 md:p-4 bg-black/70 backdrop-blur-sm"
        @click.self="modalPolitica = null"
      >
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto resto-modal">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0 resto-modal__header">
            <h3 class="resto-modal__title">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null" class="resto-modal__close">&times;</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap resto-modal__body">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <!-- 404 -->
    <div v-else-if="!loading" class="resto-not-found">
      <p class="resto-not-found__code">404</p>
      <p class="resto-not-found__text">Restaurante não encontrado</p>
      <button @click="$router.back()" class="resto-btn-ghost mt-6">
        &larr; Voltar
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
  name: 'TemplateRestauranteModerno',

  components: {
    ProductInfoCard,
    MultiCart,
    ProductSlider,
    Profile,
    ProductCatalog,
    AvaliacaoLoja,
  },

  emits: ['toggle-dark'],

  props: {
    tema: {
      type: Object,
      default: () => ({}),
    },
  },

  setup(props, { emit }) {
    const isDark = ref(props.tema?.darkMode !== false)
    const activeSection = ref('resto-sobre')
    const modalPolitica = ref(null)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#f97316',
      '--cor-secundaria': props.tema?.corSecundaria || '#0c0a09',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
    const currentYear = new Date().getFullYear()

    const firstWord = computed(() => {
      if (!lojaData.loja?.value?.nome) return ''
      const parts = lojaData.loja.value.nome.split(' ')
      return parts[0]
    })

    const restWords = computed(() => {
      if (!lojaData.loja?.value?.nome) return ''
      const parts = lojaData.loja.value.nome.split(' ')
      return parts.slice(1).join(' ')
    })

    const ratingFormatted = computed(() => {
      if (!lojaData.loja?.value?.rating_medio) return '—'
      return parseFloat(lojaData.loja.value.rating_medio).toFixed(1)
    })

    function toggleDark() {
      isDark.value = !isDark.value
      emit('toggle-dark', isDark.value)
    }

    function isVideo(url) {
      return /\.(mp4|webm|mov|mkv)$/i.test(url || '')
    }

    function truncateText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    function scrollToId(id) {
      const el = document.getElementById(id)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }

    function onRatingUpdated(data) {
      if (lojaData.loja?.value) {
        lojaData.loja.value.rating_medio = data.rating_medio
        lojaData.loja.value.total_avaliacoes = data.total_avaliacoes
      }
    }

    function logOut() {
      localStorage.removeItem('user')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.reload()
    }

    let sectionObserver = null

    function setupSectionObserver() {
      const sections = document.querySelectorAll('[id^="resto-"]')

      sectionObserver = new IntersectionObserver(entries => {
        entries.forEach(e => {
          if (e.isIntersecting) activeSection.value = e.target.id
        })
      }, {
        rootMargin: '-40% 0px -55% 0px',
      })

      sections.forEach(s => sectionObserver.observe(s))
    }

    onMounted(() => {
      setupSectionObserver()
    })

    onUnmounted(() => {
      sectionObserver?.disconnect()
    })

    return {
      isDark,
      activeSection,
      modalPolitica,
      cssVars,
      user,
      currentYear,
      firstWord,
      restWords,
      ratingFormatted,
      toggleDark,
      isVideo,
      truncateText,
      scrollToId,
      onRatingUpdated,
      logOut,
      ...lojaData,
    }
  },
}
</script>

<style scoped>
/* ── Fonts ──
   Add to index.html or global CSS:
   @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
*/

/* ══════════════════════════════════════════════════════════
   ROOT & THEME TOKENS
══════════════════════════════════════════════════════════ */
.resto-root {
  --accent: var(--cor-primaria, #f97316);
  --bg: #0c0a09;
  --bg2: #1c1917;
  --bg3: #292524;
  --fg: #fafaf9;
  --fg2: #a8a29e;
  --fg3: #57534e;
  --border: rgba(255,255,255,0.08);
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-body);
  overflow-x: hidden;
  min-height: 100vh;
}

.resto-root.light {
  --bg: #fafaf9;
  --bg2: #f5f5f4;
  --bg3: #e7e5e4;
  --fg: #1c1917;
  --fg2: #78716c;
  --fg3: #a8a29e;
  --border: rgba(0,0,0,0.08);
}

/* ══════════════════════════════════════════════════════════
   LOADING
══════════════════════════════════════════════════════════ */
.resto-loading {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.resto-loading__flame {
  width: 32px;
  height: 48px;
  position: relative;
}

.resto-loading__flame-inner {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 24px;
  height: 36px;
  background: linear-gradient(to top, var(--accent), #fbbf24, #fef3c7);
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  transform: translateX(-50%);
  animation: flameFlicker 0.8s ease-in-out infinite alternate;
}

@keyframes flameFlicker {
  0% {
    transform: translateX(-50%) scaleY(1) scaleX(1);
    filter: brightness(1);
  }
  50% {
    transform: translateX(-50%) scaleY(1.1) scaleX(0.95);
    filter: brightness(1.1);
  }
  100% {
    transform: translateX(-50%) scaleY(0.95) scaleX(1.05);
    filter: brightness(0.95);
  }
}

.resto-loading__text {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--fg2);
}

/* ══════════════════════════════════════════════════════════
   HERO
══════════════════════════════════════════════════════════ */
.resto-hero {
  position: relative;
  height: 100svh;
  min-height: 640px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.resto-hero__media {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.resto-hero__grain {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
}

.resto-hero__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(12,10,9,0.95) 0%,
    rgba(12,10,9,0.7) 40%,
    rgba(12,10,9,0.3) 70%,
    rgba(12,10,9,0.15) 100%
  );
  pointer-events: none;
}

.resto-root.light .resto-hero__overlay {
  background: linear-gradient(
    to top,
    rgba(250,250,249,0.98) 0%,
    rgba(250,250,249,0.75) 40%,
    rgba(250,250,249,0.4) 70%,
    rgba(250,250,249,0.2) 100%
  );
}

.resto-hero__vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 0%, rgba(12,10,9,0.4) 100%);
  pointer-events: none;
}

.resto-root.light .resto-hero__vignette {
  background: radial-gradient(ellipse at center, transparent 0%, rgba(250,250,249,0.3) 100%);
}

/* Hero Nav */
.resto-hero__nav {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 48px;
}

.resto-hero__nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.resto-hero__nav-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: none;
}

@media (min-width: 768px) {
  .resto-hero__nav-center {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.resto-hero__nav-tag {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
  padding: 6px 16px;
  border: 1px solid rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
}

.resto-root.light .resto-hero__nav-tag {
  color: rgba(0,0,0,0.4);
  border-color: rgba(0,0,0,0.15);
}

.resto-hero__nav-right {
  width: 140px;
}

.resto-nav-back {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(0,0,0,0.2);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.6);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
}

.resto-root.light .resto-nav-back {
  background: rgba(255,255,255,0.3);
  border-color: rgba(0,0,0,0.1);
  color: rgba(0,0,0,0.6);
}

.resto-nav-back:hover {
  border-color: rgba(255,255,255,0.3);
  color: #fff;
}

.resto-root.light .resto-nav-back:hover {
  border-color: rgba(0,0,0,0.3);
  color: #000;
}

.resto-nav-back span {
  display: none;
}

@media (min-width: 640px) {
  .resto-nav-back span {
    display: inline;
  }
}

.resto-nav-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.2);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.resto-root.light .resto-nav-icon {
  background: rgba(255,255,255,0.3);
  border-color: rgba(0,0,0,0.1);
  color: rgba(0,0,0,0.6);
}

.resto-nav-icon:hover {
  border-color: rgba(255,255,255,0.3);
  color: #fff;
}

.resto-root.light .resto-nav-icon:hover {
  border-color: rgba(0,0,0,0.3);
  color: #000;
}

/* Hero Content */
.resto-hero__content {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0 48px 64px;
}

.resto-hero__label-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.resto-hero__label-line {
  width: 48px;
  height: 2px;
  background: var(--accent);
}

.resto-hero__label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.35);
}

.resto-root.light .resto-hero__label {
  color: rgba(0,0,0,0.4);
}

.resto-hero__title {
  font-family: var(--font-display);
  font-size: clamp(4rem, 10vw, 9rem);
  font-weight: 700;
  line-height: 0.9;
  letter-spacing: -0.02em;
  color: #fff;
  margin-bottom: 28px;
}

.resto-root.light .resto-hero__title {
  color: var(--fg);
}

.resto-hero__title-main,
.resto-hero__title-outline {
  display: block;
}

.resto-hero__title-outline {
  color: transparent;
  -webkit-text-stroke: 1.5px rgba(255,255,255,0.25);
}

.resto-root.light .resto-hero__title-outline {
  -webkit-text-stroke: 1.5px rgba(0,0,0,0.2);
}

.resto-hero__bottom {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
}

.resto-hero__info {
  max-width: 500px;
}

.resto-hero__desc {
  font-size: 14px;
  font-weight: 300;
  line-height: 1.7;
  color: rgba(255,255,255,0.45);
  margin-bottom: 24px;
}

.resto-root.light .resto-hero__desc {
  color: var(--fg2);
}

.resto-hero__ctas {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.resto-hero__stats {
  display: flex;
  gap: 48px;
}

.resto-hero__stat {
  text-align: center;
}

.resto-hero__stat-value {
  display: block;
  font-family: var(--font-display);
  font-size: 44px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

.resto-root.light .resto-hero__stat-value {
  color: var(--fg);
}

.resto-hero__stat-value--accent {
  color: var(--accent);
}

.resto-hero__stat-label {
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.25);
  margin-top: 6px;
}

.resto-root.light .resto-hero__stat-label {
  color: var(--fg3);
}

/* Ghost year */
.resto-hero__year {
  position: absolute;
  bottom: 32px;
  right: 48px;
  font-family: var(--font-display);
  font-size: clamp(6rem, 14vw, 14rem);
  font-weight: 700;
  font-style: italic;
  color: rgba(255,255,255,0.03);
  line-height: 1;
  letter-spacing: -0.04em;
  pointer-events: none;
  user-select: none;
}

.resto-root.light .resto-hero__year {
  color: rgba(0,0,0,0.03);
}

/* Scroll indicator */
.resto-hero__scroll {
  position: absolute;
  bottom: 32px;
  left: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  animation: scrollBounce 2s ease-in-out infinite;
}

@keyframes scrollBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(8px); }
}

.resto-hero__scroll span {
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.25);
  writing-mode: vertical-rl;
}

.resto-root.light .resto-hero__scroll span {
  color: var(--fg3);
}

.resto-hero__scroll-line {
  width: 1px;
  height: 48px;
  background: linear-gradient(to bottom, var(--accent), transparent);
}

/* ══════════════════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════════════════ */
.resto-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  background: var(--accent);
  color: #fff;
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: none;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 4px 24px -8px var(--accent);
}

.resto-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px -8px var(--accent);
}

.resto-btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border: 1px solid rgba(255,255,255,0.2);
  color: rgba(255,255,255,0.7);
  background: transparent;
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.25s;
}

.resto-root.light .resto-btn-ghost {
  border-color: var(--border);
  color: var(--fg2);
}

.resto-btn-ghost:hover {
  border-color: rgba(255,255,255,0.5);
  color: #fff;
}

.resto-root.light .resto-btn-ghost:hover {
  border-color: var(--fg3);
  color: var(--fg);
}

/* ══════════════════════════════════════════════════════════
   STICKY HORIZONTAL NAV
══════════════════════════════════════════════════════════ */
.resto-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
}

.resto-nav__inner {
  display: flex;
  white-space: nowrap;
  min-width: max-content;
}

.resto-nav__item {
  padding: 16px 24px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--fg2);
  border: none;
  border-bottom: 2px solid transparent;
  border-right: 1px solid var(--border);
  background: none;
  cursor: pointer;
  transition: all 0.2s;
}

.resto-nav__item:hover {
  color: var(--fg);
  background: var(--bg2);
}

.resto-nav__item--active {
  color: var(--fg);
  border-bottom-color: var(--accent);
}

/* ══════════════════════════════════════════════════════════
   SECTIONS (Editorial Grid)
══════════════════════════════════════════════════════════ */
.resto-section {
  border-bottom: 1px solid var(--border);
  width: 100%;
  min-width: 0;
}

.resto-section__grid {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr);
  width: 100%;
  min-width: 0;
}

.resto-section__num-col {
  border-right: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 48px;
  min-width: 0;
}

.resto-section__num {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 700;
  font-style: italic;
  color: var(--accent);
  opacity: 0.2;
  line-height: 1;
  writing-mode: vertical-rl;
  user-select: none;
}

.resto-section__num--text {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  font-style: normal;
  letter-spacing: 0.2em;
  color: var(--fg3);
  opacity: 1;
}

.resto-section__body {
  padding: 48px 48px 64px;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

.resto-section__header {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 40px;
  min-width: 0;
}

.resto-section__sub {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 8px;
}

.resto-section__title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1;
  color: var(--fg);
}

.resto-section__line {
  flex: 1;
  height: 1px;
  background: var(--border);
  margin-bottom: 8px;
}

/* ══════════════════════════════════════════════════════════
   ABOUT
══════════════════════════════════════════════════════════ */
.resto-about {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: start;
  min-width: 0;
}

.resto-about__text-col .resto-section__sub {
  margin-bottom: 16px;
}

.resto-about__text {
  font-size: 18px;
  font-weight: 300;
  line-height: 1.8;
  color: var(--fg2);
}

.resto-about__meta {
  display: flex;
  flex-direction: column;
  gap: 28px;
  min-width: 0;
}

.resto-meta-block {
  background: var(--bg2);
  padding: 20px;
  border-left: 2px solid var(--accent);
}

.resto-meta-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--fg3);
  margin-bottom: 14px;
}

.resto-meta-label svg {
  color: var(--accent);
}

.resto-meta-rows {
  display: flex;
  flex-direction: column;
}

.resto-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}

.resto-meta-row:last-child {
  border-bottom: none;
}

.resto-meta-row span:first-child {
  color: var(--fg2);
}

.resto-meta-row__price {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--accent) !important;
}

.resto-meta-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.resto-chip {
  padding: 6px 12px;
  border: 1px solid var(--border);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--fg2);
  transition: all 0.2s;
}

.resto-chip:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.resto-meta-location {
  font-size: 14px;
  color: var(--fg2);
  line-height: 1.6;
}

/* ══════════════════════════════════════════════════════════
   PRODUCT STYLING OVERRIDES
══════════════════════════════════════════════════════════ */
:deep(.resto-product-name) {
  font-family: var(--font-body) !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
}

:deep(.resto-product-price) {
  font-family: var(--font-display) !important;
  font-size: 17px !important;
  font-weight: 700 !important;
  color: var(--accent) !important;
}

:deep(.resto-badge) {
  background: var(--accent) !important;
  color: #fff !important;
  font-family: var(--font-mono) !important;
  font-size: 8px !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  border-radius: 2px !important;
  padding: 4px 8px !important;
}

:deep(.resto-tab) {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  padding: 10px 16px;
  transition: all 0.2s;
}

:deep(.resto-tab--active) {
  background: var(--accent) !important;
  color: #fff !important;
  font-weight: 600;
}

/* Fix for ProductSlider horizontal scroll in grid */
:deep(.product-slider),
:deep(.product-slider-wrapper),
:deep(.slider-container),
:deep(.products-slider),
:deep(.products-slider-wrapper),
:deep(.overflow-x-auto),
:deep(.overflow-x-scroll) {
  min-width: 0;
  max-width: 100%;
}

:deep(.overflow-x-auto),
:deep(.overflow-x-scroll) {
  overflow-x: auto !important;
  overscroll-behavior-inline: contain;
  -webkit-overflow-scrolling: touch;
}

/* ══════════════════════════════════════════════════════════
   REVIEWS
══════════════════════════════════════════════════════════ */
:deep(.resto-star-active) {
  color: var(--accent) !important;
}

:deep(.resto-star-inactive) {
  color: var(--fg3) !important;
}

:deep(.resto-progress-bar) {
  background: var(--accent) !important;
}

:deep(.resto-review-card) {
  border-bottom: 1px solid var(--border) !important;
}

:deep(.resto-own-review) {
  border-bottom: 1px solid var(--border) !important;
  background: rgba(249,115,22,0.05) !important;
}

:deep(.resto-own-review-light) {
  border-bottom: 1px solid var(--border) !important;
  background: rgba(249,115,22,0.05) !important;
}

/* ══════════════════════════════════════════════════════════
   FOOTER
══════════════════════════════════════════════════════════ */
.resto-footer {
  padding: 56px 48px 36px;
  border-top: 1px solid var(--border);
}

.resto-footer__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 32px;
  margin-bottom: 48px;
}

.resto-footer__brand {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: -0.01em;
}

.resto-footer__tagline {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--fg2);
  margin-top: 6px;
}

.resto-footer__links {
  display: flex;
  gap: 32px;
  align-items: center;
  flex-wrap: wrap;
}

.resto-footer__link {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--fg2);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.resto-footer__link:hover {
  color: var(--accent);
}

.resto-footer__bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 28px;
  border-top: 1px solid var(--border);
}

.resto-footer__copy {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--fg3);
}

/* ══════════════════════════════════════════════════════════
   MODAL
══════════════════════════════════════════════════════════ */
.resto-modal {
  background: var(--bg);
  border-top: 1px solid var(--border);
}

@media (min-width: 768px) {
  .resto-modal {
    border: 1px solid var(--border);
    border-radius: 4px;
  }
}

.resto-modal__header {
  background: var(--bg);
  border-color: var(--border);
}

.resto-modal__title {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--fg);
}

.resto-modal__close {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  background: none;
  color: var(--fg2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.2s;
}

.resto-modal__close:hover {
  border-color: var(--fg2);
  color: var(--fg);
}

.resto-modal__body {
  color: var(--fg2);
}

/* ══════════════════════════════════════════════════════════
   404
══════════════════════════════════════════════════════════ */
.resto-not-found {
  min-height: 100svh;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px;
}

.resto-not-found__code {
  font-family: var(--font-display);
  font-size: 8rem;
  font-weight: 700;
  color: var(--fg3);
  line-height: 1;
  letter-spacing: -0.04em;
}

.resto-not-found__text {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--fg2);
  margin-top: 16px;
}

/* ══════════════════════════════════════════════════════════
   RESPONSIVE
══════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  .resto-hero {
    min-height: 580px;
  }

  .resto-hero__nav,
  .resto-hero__content {
    padding-left: 24px;
    padding-right: 24px;
  }

  .resto-hero__nav {
    padding-top: 20px;
  }

  .resto-hero__content {
    padding-bottom: 48px;
  }

  .resto-hero__title {
    font-size: clamp(3.5rem, 14vw, 6rem);
  }

  .resto-hero__stats {
    gap: 32px;
  }

  .resto-hero__stat-value {
    font-size: 36px;
  }

  .resto-hero__year {
    font-size: 5rem;
    right: 24px;
    bottom: 24px;
  }

  .resto-hero__scroll {
    left: 24px;
    bottom: 24px;
  }

  /* Remove number column on mobile */
  .resto-section__grid {
    grid-template-columns: 1fr;
  }

  .resto-section__num-col {
    display: none;
  }

  .resto-section__body {
    padding: 36px 24px 48px;
  }

  .resto-section__title {
    font-size: 32px;
  }

  .resto-about {
    grid-template-columns: 1fr;
    gap: 36px;
  }

  .resto-about__text {
    font-size: 16px;
  }

  .resto-footer {
    padding: 40px 24px 28px;
  }

  .resto-footer__top {
    gap: 24px;
  }

  .resto-footer__links {
    gap: 20px;
  }
}

@media (max-width: 520px) {
  .resto-hero {
    min-height: 540px;
  }

  .resto-hero__nav,
  .resto-hero__content {
    padding-left: 16px;
    padding-right: 16px;
  }

  .resto-hero__nav-right {
    width: 100px;
  }

  .resto-hero__content {
    padding-bottom: 40px;
  }

  .resto-hero__label-row {
    gap: 12px;
    margin-bottom: 16px;
  }

  .resto-hero__label-line {
    width: 32px;
  }

  .resto-hero__title {
    font-size: clamp(3rem, 16vw, 4.5rem);
    margin-bottom: 20px;
  }

  .resto-hero__desc {
    font-size: 13px;
    margin-bottom: 20px;
  }

  .resto-hero__ctas {
    flex-direction: column;
    gap: 10px;
  }

  .resto-btn-primary,
  .resto-btn-ghost {
    padding: 12px 24px;
    font-size: 11px;
    width: 100%;
    justify-content: center;
  }

  .resto-hero__stats {
    gap: 24px;
    margin-top: 24px;
    width: 100%;
    justify-content: center;
  }

  .resto-hero__year {
    display: none;
  }

  .resto-hero__scroll {
    display: none;
  }

  .resto-section__body {
    padding: 32px 16px 40px;
  }

  .resto-section__title {
    font-size: 28px;
  }

  .resto-nav__item {
    padding: 14px 18px;
    font-size: 9px;
    letter-spacing: 0.2em;
  }

  .resto-footer {
    padding-left: 16px;
    padding-right: 16px;
  }
}

/* ══════════════════════════════════════════════════════════
   UTILITIES
══════════════════════════════════════════════════════════ */
.hide-scroll {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.hide-scroll::-webkit-scrollbar {
  display: none;
}

.capitalize {
  text-transform: capitalize;
}
</style>
