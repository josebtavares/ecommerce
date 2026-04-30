<!-- TemplateModaEditorial.vue — Remake aprovado
     Hero full-bleed · Índice horizontal sticky · Grid editorial com números de secção
     Tipografia: Barlow Condensed (títulos) + Barlow (corpo) + DM Mono (labels)
     Acento configurável via --cor-primaria (default: #c8ff00 limão)
-->
<template>
  <div
    class="editorial-root transition-colors duration-500"
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
    <div v-if="loading" class="editorial-loading">
      <div class="editorial-loading__bars">
        <div
          v-for="i in 5"
          :key="i"
          class="editorial-loading__bar"
          :style="{ animationDelay: (i * 0.12) + 's' }"
        ></div>
      </div>
    </div>

    <template v-else-if="loja">
      <!-- ══════════════════════════════════════════
           HERO
      ══════════════════════════════════════════ -->
      <section class="editorial-hero" ref="heroRef">
        <div
          class="editorial-hero__bg"
          :style="{ backgroundImage: `url(${loja.banner_url || backendUrl + '/media/lojas/default_banner.jpg'})` }"
          :class="{ 'editorial-hero__bg--loaded': bgLoaded }"
        ></div>

        <!-- Nav -->
        <nav class="editorial-hero__nav">
          <div class="editorial-hero__left-controls">
            <button @click="$router.back()" class="editorial-hero__back">
              ← Voltar
            </button>

            <button @click="toggleDark" class="editorial-btn-icon">
              <svg
                v-if="isDark"
                xmlns="http://www.w3.org/2000/svg"
                width="13"
                height="13"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>

              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="13"
                height="13"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M21.64 13.02A9 9 0 1 1 10.98 2.36 7 7 0 0 0 21.64 13.02Z"
                />
              </svg>
            </button>
          </div>
        </nav>

        <!-- Content -->
        <div class="editorial-hero__content">
          <div class="editorial-hero__issue">
            <div class="editorial-hero__issue-line"></div>
            <span class="editorial-hero__issue-label">
              {{ loja.categoria }} · {{ loja.localizacao || 'PT' }} · AW25
            </span>
          </div>

          <h1 class="editorial-hero__title">
            <span>{{ firstWord }}</span>
            <span class="editorial-hero__title--outline">{{ restWords }}</span>
          </h1>

          <div class="editorial-hero__bottom">
            <div>
              <p v-if="loja.descricao" class="editorial-hero__desc">
                {{ loja.descricao.substring(0, 150) }}{{ loja.descricao.length > 150 ? '…' : '' }}
              </p>

              <div class="editorial-hero__ctas">
                <button @click="scrollToId('edit-colecao')" class="editorial-btn-primary">
                  Ver Coleção →
                </button>

                <button @click="scrollToId('edit-catalogo')" class="editorial-btn-ghost">
                  Catálogo
                </button>
              </div>
            </div>

            <div class="editorial-hero__stats">
              <div v-if="loja.rating_medio">
                <div class="editorial-hero__stat-val editorial-hero__stat-val--ac">
                  {{ loja.rating_medio }}
                </div>
                <div class="editorial-hero__stat-label">Rating</div>
              </div>

              <div v-if="loja.total_avaliacoes">
                <div class="editorial-hero__stat-val">
                  {{ loja.total_avaliacoes }}
                </div>
                <div class="editorial-hero__stat-label">Reviews</div>
              </div>

              <div v-if="loja.entrega_ativa">
                <div class="editorial-hero__stat-val editorial-hero__stat-val--ac">
                  ✓
                </div>
                <div class="editorial-hero__stat-label">Entrega</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Ghost year -->
        <div class="editorial-hero__year" aria-hidden="true">
          {{ currentYear }}
        </div>
      </section>

      <!-- ══════════════════════════════════════════
           ÍNDICE HORIZONTAL STICKY
      ══════════════════════════════════════════ -->
      <nav class="editorial-nav" ref="stickyNav">
        <div class="editorial-nav__inner hide-scroll">
          <button
            class="editorial-nav__item"
            :class="{ 'editorial-nav__item--active': activeSection === 'edit-sobre' }"
            @click="scrollToId('edit-sobre')"
          >
            Sobre
          </button>

          <button
            class="editorial-nav__item"
            :class="{ 'editorial-nav__item--active': activeSection === 'edit-colecao' }"
            @click="scrollToId('edit-colecao')"
          >
            Destaques
          </button>

          <button
            v-for="tipo in tiposExistentes"
            :key="tipo.id"
            class="editorial-nav__item capitalize"
            :class="{ 'editorial-nav__item--active': activeSection === 'edit-tipo-' + tipo.id }"
            @click="scrollToId('edit-tipo-' + tipo.id)"
          >
            {{ tipo.nome }}
          </button>

          <button
            v-for="cat in categoriasExistentes"
            :key="cat.id"
            class="editorial-nav__item capitalize"
            :class="{ 'editorial-nav__item--active': activeSection === 'edit-cat-' + cat.id }"
            @click="scrollToId('edit-cat-' + cat.id)"
          >
            {{ cat.nome }}
          </button>

          <button
            class="editorial-nav__item"
            :class="{ 'editorial-nav__item--active': activeSection === 'edit-catalogo' }"
            @click="scrollToId('edit-catalogo')"
          >
            Catálogo
          </button>

          <button
            class="editorial-nav__item"
            :class="{ 'editorial-nav__item--active': activeSection === 'edit-avaliacoes' }"
            @click="scrollToId('edit-avaliacoes')"
          >
            Reviews
          </button>
        </div>
      </nav>

      <!-- ══════════════════════════════════════════
           MAIN
      ══════════════════════════════════════════ -->
      <main>
        <!-- 00 — SOBRE -->
        <section class="editorial-section" id="edit-sobre">
          <div class="editorial-section__grid">
            <div class="editorial-section__num-col">
              <span class="editorial-section__num">00</span>
            </div>

            <div class="editorial-section__body">
              <div class="editorial-about">
                <div>
                  <div class="editorial-section__sub">About</div>

                  <p class="editorial-about__text">
                    {{ loja.descricao || 'Uma loja construída em torno de um único princípio: qualidade sem compromisso, design sem ruído.' }}
                  </p>
                </div>

                <div class="editorial-about__meta">
                  <div v-if="opcoesEntrega.length" class="editorial-meta-block">
                    <div class="editorial-meta-label">Envio</div>

                    <div
                      v-for="opcao in opcoesEntrega"
                      :key="opcao.id"
                      class="editorial-meta-row"
                    >
                      <span>{{ opcao.nome }}</span>
                      <span>{{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}</span>
                    </div>
                  </div>

                  <div v-if="metodosPagamento.length" class="editorial-meta-block">
                    <div class="editorial-meta-label">Pagamento</div>

                    <div class="editorial-meta-chips">
                      <span
                        v-for="m in metodosPagamento"
                        :key="m.id"
                        class="editorial-chip"
                      >
                        {{ m.tipo }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 01 — DESTAQUES -->
        <section class="editorial-section" id="edit-colecao">
          <div class="editorial-section__grid">
            <div class="editorial-section__num-col">
              <span class="editorial-section__num">01</span>
            </div>

            <div class="editorial-section__body">
              <div class="editorial-section__header">
                <div>
                  <div class="editorial-section__sub">New Season</div>
                  <h2 class="editorial-section__title">Destaques</h2>
                </div>

                <div class="editorial-section__line"></div>
              </div>

              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="220px"
                image-height="290px"
                card-height="390px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-2xl transition-all duration-500"
                hover-border-class=""
                product-name-class="editorial-product-name"
                price-class="editorial-product-price"
                badge-text="NEW"
                badge-class="editorial-badge"
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
          :id="'edit-tipo-' + tipo.id"
          class="editorial-section"
        >
          <div class="editorial-section__grid">
            <div class="editorial-section__num-col">
              <span class="editorial-section__num">
                {{ String(idx + 2).padStart(2, '0') }}
              </span>
            </div>

            <div class="editorial-section__body">
              <div class="editorial-section__header">
                <div>
                  <div class="editorial-section__sub">Collection</div>
                  <h2 class="editorial-section__title capitalize">
                    {{ tipo.nome }}
                  </h2>
                </div>

                <div class="editorial-section__line"></div>
              </div>

              <ProductSlider
                :title="tipo.nome"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark"
                card-width="200px"
                image-height="260px"
                card-height="360px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                product-name-class="editorial-product-name"
                price-class="editorial-product-price"
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
          :id="'edit-cat-' + cat.id"
          class="editorial-section"
        >
          <div class="editorial-section__grid">
            <div class="editorial-section__num-col">
              <span class="editorial-section__num">
                {{ String(tiposExistentes.length + idx + 2).padStart(2, '0') }}
              </span>
            </div>

            <div class="editorial-section__body">
              <div class="editorial-section__header">
                <div>
                  <div class="editorial-section__sub">Collection</div>
                  <h2 class="editorial-section__title capitalize">
                    {{ cat.nome }}
                  </h2>
                </div>

                <div class="editorial-section__line"></div>
              </div>

              <ProductSlider
                :title="cat.nome"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark"
                card-width="200px"
                image-height="260px"
                card-height="360px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                product-name-class="editorial-product-name"
                price-class="editorial-product-price"
                :show-store-name="false"
                :show-stock="false"
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- CATÁLOGO COMPLETO -->
        <section class="editorial-section" id="edit-catalogo">
          <div class="editorial-section__grid">
            <div class="editorial-section__num-col">
              <span class="editorial-section__num editorial-section__num--text">
                CATALOG
              </span>
            </div>

            <div class="editorial-section__body">
              <div class="editorial-section__header">
                <div>
                  <div class="editorial-section__sub">Full Collection</div>
                  <h2 class="editorial-section__title">Coleção Completa</h2>
                </div>

                <div class="editorial-section__line"></div>
              </div>

              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="260px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                tab-border-radius="rounded-none"
                :active-tab-class="'editorial-tab--active'"
                :inactive-tab-dark-class="'editorial-tab editorial-tab--dark'"
                :inactive-tab-light-class="'editorial-tab editorial-tab--light'"
                input-border-radius="rounded-none"
                filter-container-radius="rounded-none"
                product-name-class="editorial-product-name"
                product-name-hover-class="group-hover:opacity-60"
                price-class="editorial-product-price"
                :show-stock="false"
                :show-badges="false"
                :show-category-badges="false"
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- AVALIAÇÕES -->
        <section class="editorial-section" id="edit-avaliacoes">
          <div class="editorial-section__grid">
            <div class="editorial-section__num-col">
              <span class="editorial-section__num editorial-section__num--text">
                REVIEWS
              </span>
            </div>

            <div class="editorial-section__body">
              <div class="editorial-section__header">
                <div>
                  <div class="editorial-section__sub">Community</div>
                  <h2 class="editorial-section__title">Avaliações</h2>
                </div>

                <div class="editorial-section__line"></div>
              </div>

              <AvaliacaoLoja
                :loja-id="lojaId"
                :isDark="isDark"
                summary-border-radius="rounded-none"
                form-border-radius="rounded-none"
                review-card-border-radius="rounded-none"
                button-border-radius="rounded-none"
                textarea-border-radius="rounded-none"
                :star-active-class="'editorial-star-active'"
                :star-inactive-class="'editorial-star-inactive'"
                progress-bar-class="editorial-progress-bar"
                :submit-button-class="'editorial-btn-primary w-full justify-center'"
                :review-card-class="'editorial-review-card'"
                :own-review-border-class="isDark ? 'border-b editorial-border editorial-own-review' : 'border-b editorial-border editorial-own-review-light'"
                :load-more-button-class="'editorial-btn-ghost text-xs tracking-widest uppercase'"
                @rating-updated="onRatingUpdated"
              />
            </div>
          </div>
        </section>

        <!-- FOOTER -->
        <footer class="editorial-footer">
          <div class="editorial-footer__top">
            <div>
              <div class="editorial-footer__brand">
                {{ loja.nome }}
              </div>

              <div class="editorial-footer__tagline">
                {{ loja.localizacao || 'Portugal' }} · {{ currentYear }}
              </div>
            </div>

            <div class="editorial-footer__links">
              <button
                v-if="loja.politica_devolucao"
                @click="modalPolitica = 'devolucao'"
                class="editorial-footer__link"
              >
                Devoluções
              </button>

              <button
                v-if="loja.termos_servico"
                @click="modalPolitica = 'termos'"
                class="editorial-footer__link"
              >
                Termos
              </button>

              <button
                v-if="loja.politica_privacidade"
                @click="modalPolitica = 'privacidade'"
                class="editorial-footer__link"
              >
                Privacidade
              </button>
            </div>
          </div>

          <div class="editorial-footer__bottom">
            <span class="editorial-footer__copy">
              © {{ currentYear }} {{ loja.nome }}. All rights reserved.
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
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto editorial-modal">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0 editorial-modal__header">
            <h3 class="editorial-modal__title">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>

            <button @click="modalPolitica = null" class="editorial-modal__close">
              ×
            </button>
          </div>

          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap editorial-modal__body">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="editorial-not-found">
      <p class="editorial-not-found__title">404</p>

      <button @click="$router.back()" class="editorial-not-found__back">
        ← Voltar
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
  name: 'TemplateModaEditorial',

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
    const bgLoaded = ref(false)
    const activeSection = ref('edit-sobre')
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#c8ff00',
      '--cor-secundaria': props.tema?.corSecundaria || '#0a0a0a',
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

    function toggleDark() {
      isDark.value = !isDark.value
      emit('toggle-dark', isDark.value)
    }

    let sectionObserver = null

    function setupSectionObserver() {
      const sections = document.querySelectorAll('[id^="edit-"]')

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
      setTimeout(() => {
        bgLoaded.value = true
      }, 120)

      setupSectionObserver()
    })

    onUnmounted(() => {
      sectionObserver?.disconnect()
    })

    return {
      isDark,
      bgLoaded,
      activeSection,
      cssVars,
      user,
      currentYear,
      firstWord,
      restWords,
      toggleDark,
      ...lojaData,
    }
  },
}
</script>

<style scoped>
/* ── Fonts ──
   Adicionar ao index.html ou ao CSS global:
   @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,300;0,400;0,700;0,900;1,400&family=Barlow:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');
*/

/* ── Root tokens ─────────────────────────────────────────── */
.editorial-root {
  --accent: var(--cor-primaria, #c8ff00);
  --bg: #0a0a0a;
  --bg2: #111;
  --fg: #f5f5f5;
  --fg2: #888;
  --fg3: #2a2a2a;
  --border: rgba(255,255,255,0.09);
  --font-head: 'Barlow Condensed', sans-serif;
  --font-body: 'Barlow', sans-serif;
  --font-mono: 'DM Mono', monospace;

  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-body);
  overflow-x: hidden;
}

.editorial-root.light {
  --bg: #f2f2f2;
  --bg2: #e8e8e8;
  --fg: #0a0a0a;
  --fg2: #666;
  --fg3: #d0d0d0;
  --border: rgba(0,0,0,0.1);
}

/* ── Loading ─────────────────────────────────────────────── */
.editorial-loading {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.editorial-loading__bars {
  display: flex;
  gap: 4px;
}

.editorial-loading__bar {
  width: 2px;
  height: 32px;
  border-radius: 1px;
  background: var(--accent);
  animation: editBars 0.9s ease-in-out infinite alternate;
}

@keyframes editBars {
  from {
    transform: scaleY(0.3);
    opacity: 0.3;
  }

  to {
    transform: scaleY(1);
    opacity: 1;
  }
}

/* ── Hero ────────────────────────────────────────────────── */
.editorial-hero {
  position: relative;
  height: 100svh;
  min-height: 600px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editorial-hero__bg {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(to bottom, rgba(10,10,10,0.2) 0%, rgba(10,10,10,0.88) 100%),
    var(--bg) center/cover no-repeat;
  transform: scale(1.04);
  transition: transform 14s ease-out;
}

.editorial-hero__bg--loaded {
  transform: scale(1);
}

.editorial-hero__nav {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 24px 48px;
}

.editorial-hero__left-controls {
  display: flex;
  align-items: center;
  gap: 14px;
}

.editorial-hero__back {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.editorial-hero__back:hover {
  color: #fff;
}

.editorial-btn-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(0,0,0,0.12);
  color: rgba(255,255,255,0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  backdrop-filter: blur(8px);
}

.editorial-btn-icon:hover {
  border-color: rgba(255,255,255,0.6);
  color: #fff;
}

.editorial-hero__content {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0 48px 56px;
}

.editorial-hero__issue {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.editorial-hero__issue-line {
  width: 40px;
  height: 1px;
  background: var(--accent);
}

.editorial-hero__issue-label {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.5em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.35);
}

.editorial-hero__title {
  font-family: var(--font-head);
  font-size: clamp(5rem, 12vw, 11rem);
  font-weight: 900;
  line-height: 0.88;
  letter-spacing: -0.02em;
  color: #fff;
  text-transform: uppercase;
  margin-bottom: 24px;
}

.editorial-hero__title span {
  display: block;
}

.editorial-hero__title--outline {
  color: transparent;
  -webkit-text-stroke: 2px rgba(255,255,255,0.3);
}

.editorial-hero__bottom {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 24px;
}

.editorial-hero__desc {
  font-size: 13px;
  font-weight: 300;
  line-height: 1.7;
  color: rgba(255,255,255,0.4);
  max-width: 460px;
  margin-bottom: 22px;
}

.editorial-hero__ctas {
  display: flex;
  gap: 10px;
}

.editorial-hero__stats {
  display: flex;
  gap: 40px;
  padding-bottom: 4px;
}

.editorial-hero__stat-val {
  font-family: var(--font-head);
  font-size: 48px;
  font-weight: 900;
  color: #fff;
  line-height: 1;
  letter-spacing: -0.02em;
}

.editorial-hero__stat-val--ac {
  color: var(--accent);
}

.editorial-hero__stat-label {
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.2);
  margin-top: 5px;
}

.editorial-hero__year {
  position: absolute;
  bottom: 40px;
  right: 48px;
  font-family: var(--font-head);
  font-size: clamp(8rem,18vw,18rem);
  font-weight: 900;
  color: rgba(255,255,255,0.04);
  line-height: 1;
  letter-spacing: -0.06em;
  pointer-events: none;
  user-select: none;
}

/* ── Buttons ─────────────────────────────────────────────── */
.editorial-btn-primary {
  padding: 12px 28px;
  background: var(--accent);
  color: #0a0a0a;
  font-family: var(--font-head);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}

.editorial-btn-primary:hover {
  opacity: 0.88;
}

.editorial-btn-ghost {
  padding: 12px 28px;
  border: 1px solid rgba(255,255,255,0.22);
  color: rgba(255,255,255,0.65);
  background: none;
  font-family: var(--font-head);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
}

.editorial-root.light .editorial-btn-ghost {
  border-color: var(--fg3);
  color: var(--fg2);
}

.editorial-btn-ghost:hover {
  border-color: rgba(255,255,255,0.65);
  color: #fff;
}

/* ── Horizontal nav ──────────────────────────────────────── */
.editorial-nav {
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  position: sticky;
  top: 0;
  z-index: 50;
  overflow-x: auto;
}

.editorial-nav__inner {
  display: flex;
  white-space: nowrap;
  min-width: max-content;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.editorial-nav__inner::-webkit-scrollbar {
  display: none;
}

.editorial-nav__item {
  padding: 14px 22px;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: var(--fg2);
  border: none;
  border-right: 1px solid var(--border);
  border-bottom: 2px solid transparent;
  background: none;
  cursor: pointer;
  transition: all 0.18s;
}

.editorial-nav__item:hover {
  color: var(--fg);
}

.editorial-nav__item--active {
  color: var(--fg);
  border-bottom-color: var(--accent);
}

/* ── Sections ────────────────────────────────────────────── */
.editorial-section {
  border-bottom: 1px solid var(--border);
  width: 100%;
  min-width: 0;
}

.editorial-section__grid {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  width: 100%;
  min-width: 0;
}

.editorial-section__num-col {
  border-right: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 40px;
  min-width: 0;
}

.editorial-section__num {
  font-family: var(--font-head);
  font-size: 52px;
  font-weight: 900;
  color: var(--accent);
  opacity: 0.25;
  line-height: 1;
  writing-mode: vertical-rl;
  user-select: none;
}

.editorial-section__num--text {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.25em;
  color: var(--fg3);
  opacity: 1;
}

.editorial-section__body {
  padding: 40px 48px 56px;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

.editorial-section__header {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 36px;
  min-width: 0;
}

.editorial-section__sub {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.5em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 6px;
}

.editorial-section__title {
  font-family: var(--font-head);
  font-size: 42px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  line-height: 0.95;
  color: var(--fg);
}

.editorial-section__line {
  flex: 1;
  height: 1px;
  background: var(--border);
  margin-bottom: 6px;
}

/* ── About ───────────────────────────────────────────────── */
.editorial-about {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 64px;
  align-items: start;
  min-width: 0;
}

.editorial-about__text {
  font-size: 20px;
  font-weight: 300;
  line-height: 1.65;
  color: var(--fg2);
}

.editorial-about__meta {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.editorial-meta-label {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: var(--fg3);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.editorial-meta-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.editorial-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}

.editorial-meta-row:last-child {
  border-bottom: none;
}

.editorial-meta-row span:first-child {
  color: var(--fg2);
  font-weight: 300;
}

.editorial-meta-row span:last-child {
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-head);
  font-size: 15px;
}

.editorial-meta-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.editorial-chip {
  padding: 4px 10px;
  border: 1px solid var(--border);
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--fg2);
}

/* ── Product items passed as classes to ProductSlider/ProductCatalog ── */
:deep(.editorial-product-name) {
  font-family: var(--font-head) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
}

:deep(.editorial-product-price) {
  font-family: var(--font-head) !important;
  font-size: 15px !important;
  font-weight: 900 !important;
  color: var(--fg) !important;
}

:deep(.editorial-badge) {
  background: var(--accent) !important;
  color: #0a0a0a !important;
  font-family: var(--font-mono) !important;
  font-size: 8px !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  border-radius: 0 !important;
}

:deep(.editorial-tab) {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  padding-bottom: 8px;
}

:deep(.editorial-tab--active),
:deep(.editorial-tab--dark.active) {
  border-bottom: 2px solid var(--accent);
  color: var(--fg);
  font-weight: 600;
}

/* Fix para ProductSlider horizontal dentro de grid */
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

/* ── Reviews ─────────────────────────────────────────────── */
:deep(.editorial-star-active) {
  color: var(--accent) !important;
}

:deep(.editorial-star-inactive) {
  color: var(--fg3) !important;
}

:deep(.editorial-progress-bar) {
  background: var(--accent) !important;
}

:deep(.editorial-review-card) {
  border-bottom: 1px solid var(--border) !important;
}

:deep(.editorial-own-review) {
  border-bottom: 1px solid var(--border) !important;
  background: rgba(255,255,255,0.02) !important;
}

:deep(.editorial-own-review-light) {
  border-bottom: 1px solid var(--border) !important;
  background: rgba(0,0,0,0.02) !important;
}

/* ── Footer ──────────────────────────────────────────────── */
.editorial-footer {
  padding: 48px 48px 32px;
  border-top: 1px solid var(--border);
}

.editorial-footer__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 40px;
  flex-wrap: wrap;
  gap: 24px;
}

.editorial-footer__brand {
  font-family: var(--font-head);
  font-size: 32px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  color: var(--fg);
}

.editorial-footer__tagline {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: var(--fg2);
  margin-top: 5px;
}

.editorial-footer__links {
  display: flex;
  gap: 32px;
  align-items: center;
  flex-wrap: wrap;
}

.editorial-footer__link {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--fg2);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.18s;
}

.editorial-footer__link:hover {
  color: var(--fg);
}

.editorial-footer__bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.editorial-footer__copy {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--fg3);
}

/* ── Modal ───────────────────────────────────────────────── */
.editorial-modal {
  background: var(--bg);
  border-top: 1px solid var(--border);
}

@media (min-width: 768px) {
  .editorial-modal {
    border: 1px solid var(--border);
  }
}

.editorial-modal__header {
  background: var(--bg);
  border-color: var(--border);
}

.editorial-modal__title {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  color: var(--fg);
}

.editorial-modal__close {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  background: none;
  color: var(--fg2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.18s;
}

.editorial-modal__close:hover {
  border-color: var(--fg2);
  color: var(--fg);
}

.editorial-modal__body {
  color: var(--fg2);
}

/* ── Not found ───────────────────────────────────────────── */
.editorial-not-found {
  min-height: 100svh;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.editorial-not-found__title {
  font-family: var(--font-head);
  font-size: 6rem;
  font-weight: 900;
  color: var(--fg3);
  letter-spacing: -0.04em;
}

.editorial-not-found__back {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  margin-top: 16px;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 900px) {
  .editorial-hero {
    min-height: 560px;
  }

  .editorial-hero__nav,
  .editorial-hero__content {
    padding-left: 20px;
    padding-right: 20px;
  }

  .editorial-hero__nav {
    justify-content: flex-start;
    padding-top: 20px;
    padding-bottom: 16px;
  }

  .editorial-hero__left-controls {
    gap: 12px;
  }

  .editorial-hero__back {
    font-size: 8px;
    letter-spacing: 0.28em;
  }

  .editorial-btn-icon {
    width: 32px;
    height: 32px;
  }

  .editorial-hero__content {
    padding-bottom: 40px;
  }

  .editorial-hero__issue-label {
    font-size: 8px;
    letter-spacing: 0.32em;
  }

  .editorial-hero__title {
    font-size: clamp(4rem, 20vw, 7rem);
  }

  .editorial-hero__bottom {
    align-items: flex-start;
  }

  .editorial-hero__stats {
    gap: 24px;
  }

  .editorial-hero__stat-val {
    font-size: 36px;
  }

  .editorial-hero__year {
    font-size: 6rem;
    right: 20px;
    bottom: 28px;
  }

  /*
    Mobile:
    remove a coluna lateral dos números 00, 01, 02, 03...
  */
  .editorial-section__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .editorial-section__num-col {
    display: none;
  }

  .editorial-section__body {
    padding: 32px 20px 44px;
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
  }

  .editorial-section__header {
    margin-bottom: 28px;
  }

  .editorial-section__title {
    font-size: 36px;
  }

  .editorial-about {
    grid-template-columns: minmax(0, 1fr);
    gap: 32px;
  }

  .editorial-about__text {
    font-size: 18px;
  }

  .editorial-footer {
    padding: 32px 20px 24px;
  }

  .editorial-footer__top {
    gap: 28px;
  }

  .editorial-footer__links {
    gap: 18px;
  }
}

@media (max-width: 520px) {
  .editorial-hero {
    min-height: 520px;
  }

  .editorial-hero__nav {
    padding-left: 16px;
    padding-right: 16px;
  }

  .editorial-hero__content {
    padding-left: 16px;
    padding-right: 16px;
    padding-bottom: 34px;
  }

  .editorial-hero__issue {
    gap: 9px;
  }

  .editorial-hero__issue-line {
    width: 28px;
  }

  .editorial-hero__issue-label {
    letter-spacing: 0.22em;
  }

  .editorial-hero__title {
    font-size: clamp(3.4rem, 21vw, 5.6rem);
    margin-bottom: 20px;
  }

  .editorial-hero__desc {
    font-size: 12px;
    line-height: 1.6;
    margin-bottom: 18px;
  }

  .editorial-hero__ctas {
    flex-wrap: wrap;
  }

  .editorial-btn-primary,
  .editorial-btn-ghost {
    padding: 11px 20px;
    font-size: 11px;
  }

  .editorial-section__body {
    padding: 30px 16px 42px;
  }

  .editorial-section__title {
    font-size: 32px;
  }

  .editorial-nav__item {
    padding: 13px 18px;
    font-size: 8px;
    letter-spacing: 0.28em;
  }

  .editorial-footer {
    padding-left: 16px;
    padding-right: 16px;
  }
}

.hide-scroll {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.hide-scroll::-webkit-scrollbar {
  display: none;
}
</style>