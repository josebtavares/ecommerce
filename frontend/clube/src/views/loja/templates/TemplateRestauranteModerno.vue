<!-- TemplateRestauranteModerno.vue — Cinematic Restaurant Template
     Split-screen hero · Vertical side nav · Bento grid sections
     Typography: Instrument Serif (títulos) + Inter (corpo)
     Acento configurável via --cor-primaria (default: #c9a961 dourado)
-->
<template>
  <div
    class="resto-root"
    :class="isDark ? 'resto-dark' : 'resto-light'"
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

    <!-- Loading State -->
    <div v-if="loading" class="resto-loading">
      <div class="resto-loading__ring">
        <div class="resto-loading__ring-inner"></div>
      </div>
      <span class="resto-loading__text">Carregando</span>
    </div>

    <template v-else-if="loja">
      <!-- ══════════════════════════════════════════
           HERO — Split Screen Cinematic
      ══════════════════════════════════════════ -->
      <section class="resto-hero">
        <!-- Left Panel - Content -->
        <div class="resto-hero__left">
          <!-- Top Bar -->
          <div class="resto-hero__topbar">
            <button @click="$router.back()" class="resto-back">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
            </button>
            
            <div class="resto-hero__brand-tag">
              {{ loja.categoria || 'Restaurante' }}
            </div>

            <button @click="toggleDark" class="resto-theme-toggle">
              <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="5"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            </button>
          </div>

          <!-- Hero Content -->
          <div class="resto-hero__content">
            <div class="resto-hero__location">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>{{ loja.localizacao || 'Portugal' }}</span>
            </div>

            <h1 class="resto-hero__title">
              {{ loja.nome }}
            </h1>

            <p v-if="loja.descricao" class="resto-hero__desc">
              {{ truncateText(loja.descricao, 160) }}
            </p>

            <!-- Stats Row -->
            <div class="resto-hero__stats">
              <div v-if="loja.rating_medio" class="resto-stat">
                <span class="resto-stat__value">{{ ratingFormatted }}</span>
                <span class="resto-stat__label">Rating</span>
              </div>
              <div v-if="loja.total_avaliacoes" class="resto-stat">
                <span class="resto-stat__value">{{ loja.total_avaliacoes }}+</span>
                <span class="resto-stat__label">Reviews</span>
              </div>
              <div v-if="loja.entrega_ativa" class="resto-stat">
                <span class="resto-stat__value resto-stat__value--icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M5 12l5 5L20 7"/>
                  </svg>
                </span>
                <span class="resto-stat__label">Delivery</span>
              </div>
            </div>

            <!-- CTAs -->
            <div class="resto-hero__ctas">
              <button @click="scrollToId('resto-menu')" class="resto-btn resto-btn--primary">
                <span>Explorar Menu</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M7 17L17 7M17 7H7M17 7v10"/>
                </svg>
              </button>
              <button @click="scrollToId('resto-avaliacoes')" class="resto-btn resto-btn--outline">
                Ver Avaliações
              </button>
            </div>
          </div>

          <!-- Bottom Info -->
          <div class="resto-hero__bottom">
            <div class="resto-hero__scroll-hint">
              <span>Scroll para explorar</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 5v14M19 12l-7 7-7-7"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Right Panel - Media -->
        <div class="resto-hero__right">
          <div class="resto-hero__media-wrapper">
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
            <!-- Subtle corner gradient only -->
            <div class="resto-hero__media-corners"></div>
          </div>

          <!-- Floating Rating Badge -->
          <div v-if="loja.rating_medio" class="resto-hero__floating-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <span>{{ ratingFormatted }}</span>
          </div>
        </div>
      </section>

      <!-- ══════════════════════════════════════════
           NAVIGATION - Horizontal Tabs
      ══════════════════════════════════════════ -->
      <nav class="resto-tabs" ref="stickyNav">
        <div class="resto-tabs__inner hide-scroll">
          <button
            class="resto-tabs__item"
            :class="{ 'resto-tabs__item--active': activeSection === 'resto-sobre' }"
            @click="scrollToId('resto-sobre')"
          >
            Sobre
          </button>
          <button
            class="resto-tabs__item"
            :class="{ 'resto-tabs__item--active': activeSection === 'resto-destaques' }"
            @click="scrollToId('resto-destaques')"
          >
            Destaques
          </button>
          <button
            v-for="tipo in tiposExistentes"
            :key="tipo.id"
            class="resto-tabs__item"
            :class="{ 'resto-tabs__item--active': activeSection === 'resto-tipo-' + tipo.id }"
            @click="scrollToId('resto-tipo-' + tipo.id)"
          >
            {{ tipo.nome }}
          </button>
          <button
            v-for="cat in categoriasExistentes"
            :key="cat.id"
            class="resto-tabs__item"
            :class="{ 'resto-tabs__item--active': activeSection === 'resto-cat-' + cat.id }"
            @click="scrollToId('resto-cat-' + cat.id)"
          >
            {{ cat.nome }}
          </button>
          <button
            class="resto-tabs__item"
            :class="{ 'resto-tabs__item--active': activeSection === 'resto-menu' }"
            @click="scrollToId('resto-menu')"
          >
            Menu
          </button>
          <button
            class="resto-tabs__item"
            :class="{ 'resto-tabs__item--active': activeSection === 'resto-avaliacoes' }"
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
        <!-- SOBRE - Bento Style -->
        <section class="resto-section" id="resto-sobre">
          <div class="resto-section__header">
            <span class="resto-section__tag">01</span>
            <h2 class="resto-section__title">Sobre Nós</h2>
          </div>

          <div class="resto-bento">
            <!-- Main About Card -->
            <div class="resto-bento__card resto-bento__card--large">
              <div class="resto-bento__card-content">
                <p class="resto-about-text">
                  {{ loja.descricao || 'Um restaurante construído com paixão pela gastronomia, onde cada prato conta uma história e cada refeição é uma experiência memorável.' }}
                </p>
              </div>
            </div>

            <!-- Delivery Card -->
            <div v-if="opcoesEntrega.length" class="resto-bento__card">
              <div class="resto-bento__card-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="1" y="3" width="15" height="13" rx="2"/>
                  <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                  <circle cx="5.5" cy="18.5" r="2.5"/>
                  <circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
                <span>Entrega</span>
              </div>
              <div class="resto-bento__card-body">
                <div
                  v-for="opcao in opcoesEntrega"
                  :key="opcao.id"
                  class="resto-delivery-row"
                >
                  <span>{{ opcao.nome }}</span>
                  <span class="resto-delivery-price">
                    {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Payment Card -->
            <div v-if="metodosPagamento.length" class="resto-bento__card">
              <div class="resto-bento__card-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="1" y="4" width="22" height="16" rx="2"/>
                  <line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
                <span>Pagamento</span>
              </div>
              <div class="resto-bento__card-body">
                <div class="resto-chips">
                  <span v-for="m in metodosPagamento" :key="m.id" class="resto-chip">
                    {{ m.tipo }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Location Card -->
            <div v-if="loja.localizacao" class="resto-bento__card resto-bento__card--accent">
              <div class="resto-bento__card-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                  <circle cx="12" cy="10" r="3"/>
                </svg>
                <span>Localização</span>
              </div>
              <div class="resto-bento__card-body">
                <p class="resto-location-text">{{ loja.localizacao }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- DESTAQUES -->
        <section class="resto-section" id="resto-destaques">
          <div class="resto-section__header">
            <span class="resto-section__tag">02</span>
            <h2 class="resto-section__title">Destaques do Chef</h2>
          </div>

          <ProductSlider
            title="Destaques"
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            card-width="280px"
            image-height="320px"
            card-height="460px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:scale-[1.02] hover:shadow-2xl transition-all duration-500"
            hover-border-class=""
            product-name-class="resto-product-name"
            price-class="resto-product-price"
            badge-text="CHEF"
            badge-class="resto-badge-chef"
            :show-store-name="false"
            :show-stock="false"
            @product-click="selectedProduct = $event"
          />
        </section>

        <!-- POR TIPO -->
        <section
          v-for="(tipo, idx) in tiposExistentes"
          :key="tipo.id"
          :id="'resto-tipo-' + tipo.id"
          class="resto-section"
        >
          <div class="resto-section__header">
            <span class="resto-section__tag">{{ String(idx + 3).padStart(2, '0') }}</span>
            <h2 class="resto-section__title">{{ tipo.nome }}</h2>
          </div>

          <ProductSlider
            :title="tipo.nome"
            :params="{ loja_id: lojaId, tipo: tipo.nome }"
            :isDark="isDark"
            card-width="260px"
            image-height="300px"
            card-height="440px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:scale-[1.02] hover:shadow-xl transition-all duration-500"
            hover-border-class=""
            product-name-class="resto-product-name"
            price-class="resto-product-price"
            :show-store-name="false"
            :show-stock="false"
            @product-click="selectedProduct = $event"
          />
        </section>

        <!-- POR CATEGORIA -->
        <section
          v-for="(cat, idx) in categoriasExistentes"
          :key="cat.id"
          :id="'resto-cat-' + cat.id"
          class="resto-section"
        >
          <div class="resto-section__header">
            <span class="resto-section__tag">{{ String(tiposExistentes.length + idx + 3).padStart(2, '0') }}</span>
            <h2 class="resto-section__title">{{ cat.nome }}</h2>
          </div>

          <ProductSlider
            :title="cat.nome"
            :params="{ loja_id: lojaId, categoria_id: cat.id }"
            :isDark="isDark"
            card-width="260px"
            image-height="300px"
            card-height="440px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:scale-[1.02] hover:shadow-xl transition-all duration-500"
            hover-border-class=""
            product-name-class="resto-product-name"
            price-class="resto-product-price"
            :show-store-name="false"
            :show-stock="false"
            @product-click="selectedProduct = $event"
          />
        </section>

        <!-- MENU COMPLETO -->
        <section class="resto-section resto-section--full" id="resto-menu">
          <div class="resto-section__header">
            <span class="resto-section__tag">MENU</span>
            <h2 class="resto-section__title">Carta Completa</h2>
          </div>

          <ProductCatalog
            :loja-id="lojaId"
            :isDark="isDark"
            grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
            image-height="280px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:scale-[1.02] hover:shadow-xl transition-all duration-500"
            hover-border-class=""
            tab-border-radius="rounded-full"
            :active-tab-class="'resto-catalog-tab--active'"
            :inactive-tab-dark-class="'resto-catalog-tab resto-catalog-tab--dark'"
            :inactive-tab-light-class="'resto-catalog-tab resto-catalog-tab--light'"
            input-border-radius="rounded-xl"
            filter-container-radius="rounded-2xl"
            product-name-class="resto-product-name"
            product-name-hover-class="group-hover:opacity-80"
            price-class="resto-product-price"
            :show-stock="false"
            :show-badges="true"
            :show-category-badges="false"
            @product-click="selectedProduct = $event"
          />
        </section>

        <!-- AVALIAÇÕES -->
        <section class="resto-section" id="resto-avaliacoes">
          <div class="resto-section__header">
            <span class="resto-section__tag">REVIEWS</span>
            <h2 class="resto-section__title">Avaliações</h2>
          </div>

          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-2xl"
            form-border-radius="rounded-2xl"
            review-card-border-radius="rounded-2xl"
            button-border-radius="rounded-xl"
            textarea-border-radius="rounded-xl"
            :star-active-class="'resto-star--active'"
            :star-inactive-class="'resto-star--inactive'"
            progress-bar-class="resto-progress"
            :submit-button-class="'resto-btn resto-btn--primary w-full justify-center'"
            :review-card-class="'resto-review-card'"
            :own-review-border-class="isDark ? 'resto-review--own-dark' : 'resto-review--own-light'"
          />
        </section>
      </main>

      <!-- ══════════════════════════════════════════
           FOOTER
      ══════════════════════════════════════════ -->
      <footer class="resto-footer">
        <div class="resto-footer__inner">
          <div class="resto-footer__brand">
            <span class="resto-footer__name">{{ loja.nome }}</span>
            <span class="resto-footer__tagline">Experiência Gastronómica</span>
          </div>

          <div class="resto-footer__links">
            <button @click="showPoliticaPrivacidade = true" class="resto-footer__link">
              Privacidade
            </button>
            <button @click="showTermosServico = true" class="resto-footer__link">
              Termos
            </button>
          </div>

          <div class="resto-footer__copy">
            &copy; {{ currentYear }} {{ loja.nome }}
          </div>
        </div>
      </footer>

      <!-- Modals -->
      <Teleport to="body">
        <div v-if="showPoliticaPrivacidade" class="resto-modal-overlay" @click.self="showPoliticaPrivacidade = false">
          <div class="resto-modal">
            <div class="resto-modal__header">
              <h3>Política de Privacidade</h3>
              <button @click="showPoliticaPrivacidade = false" class="resto-modal__close">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="resto-modal__body">
              <p>{{ loja.politica_privacidade || 'Respeitamos a sua privacidade e protegemos os seus dados pessoais de acordo com a legislação aplicável.' }}</p>
            </div>
          </div>
        </div>

        <div v-if="showTermosServico" class="resto-modal-overlay" @click.self="showTermosServico = false">
          <div class="resto-modal">
            <div class="resto-modal__header">
              <h3>Termos de Serviço</h3>
              <button @click="showTermosServico = false" class="resto-modal__close">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="resto-modal__body">
              <p>{{ loja.termos_servico || 'Ao utilizar os nossos serviços, concorda com os termos e condições aqui descritos.' }}</p>
            </div>
          </div>
        </div>
      </Teleport>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import ProductCatalog    from '@/components/catalog/ProductCatalog.vue'
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import Profile from '@/components/profile/UserProfile.vue'


const backendUrl = import.meta.env.VITE_BACKEND_URL || ''

const props = defineProps({
  tema: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['toggle-dark'])

const route = useRoute()
const router = useRouter()

// State
const loading = ref(true)
const loja = ref(null)
const user = ref(null)
const selectedProduct = ref(null)
const activeSection = ref('resto-sobre')
const showPoliticaPrivacidade = ref(false)
const showTermosServico = ref(false)

// Theme
const isDark = computed(() => props.tema?.modo_escuro ?? false)

const toggleDark = () => {
  emit('toggle-dark')
}

// Computed
const lojaId = computed(() => route.params.loja_id || route.params.id)
const currentYear = computed(() => new Date().getFullYear())

const ratingFormatted = computed(() => {
  if (!loja.value?.rating_medio) return '0.0'
  return Number(loja.value.rating_medio).toFixed(1)
})

const tiposExistentes = computed(() => loja.value?.tipos_existentes || [])
const categoriasExistentes = computed(() => loja.value?.categorias_existentes || [])
const opcoesEntrega = computed(() => loja.value?.opcoes_entrega || [])
const metodosPagamento = computed(() => loja.value?.metodos_pagamento || [])

const cssVars = computed(() => ({
  '--cor-primaria': props.tema?.cor_primaria || '#c9a961',
  '--cor-secundaria': props.tema?.cor_secundaria || '#1a1a1a'
}))

// Methods
const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const formatPrice = (price) => {
  return new Intl.NumberFormat('pt-PT', {
    style: 'currency',
    currency: 'EUR'
  }).format(price)
}

const isVideo = (url) => {
  if (!url) return false
  return /\.(mp4|webm|ogg)$/i.test(url)
}

const scrollToId = (id) => {
  const element = document.getElementById(id)
  if (element) {
    const navHeight = 64
    const top = element.getBoundingClientRect().top + window.scrollY - navHeight
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

const logOut = async () => {
  try {
    await api.post('/api/logout/')
    router.push('/')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

// Intersection Observer for active section
let observer = null

const setupIntersectionObserver = () => {
  const options = {
    root: null,
    rootMargin: '-100px 0px -50% 0px',
    threshold: 0
  }

  observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        activeSection.value = entry.target.id
      }
    })
  }, options)

  const sections = document.querySelectorAll('.resto-section[id]')
  sections.forEach((section) => observer.observe(section))
}

// Fetch data
const fetchData = async () => {
  loading.value = true
  try {
    const [lojaRes, userRes] = await Promise.all([
      api.get(`/api/lojas/${lojaId.value}/`),
      api.get('/api/user/').catch(() => ({ data: null }))
    ])
    loja.value = lojaRes.data
    user.value = userRes.data
  } catch (error) {
    console.error('Error fetching data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchData()
  setTimeout(setupIntersectionObserver, 100)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})

watch(lojaId, fetchData)
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   FONTS
═══════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════════
   ROOT & THEME
═══════════════════════════════════════════════════════════════ */
.resto-root {
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-body: 'Inter', system-ui, sans-serif;
  
  font-family: var(--font-body);
  min-height: 100vh;
  transition: background-color 0.4s ease, color 0.4s ease;
}

.resto-light {
  --bg-primary: #fafafa;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f5f5f5;
  --text-primary: #0a0a0a;
  --text-secondary: #525252;
  --text-tertiary: #a3a3a3;
  --border-color: #e5e5e5;
  --border-subtle: #f0f0f0;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.resto-dark {
  --bg-primary: #0a0a0a;
  --bg-secondary: #141414;
  --bg-tertiary: #1f1f1f;
  --text-primary: #fafafa;
  --text-secondary: #a3a3a3;
  --text-tertiary: #525252;
  --border-color: #262626;
  --border-subtle: #1a1a1a;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

/* ═══════════════════════════════════════════════════════════════
   LOADING
═══════════════════════════════════════════════════════════════ */
.resto-loading {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  background: var(--bg-primary);
  z-index: 100;
}

.resto-loading__ring {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  border-top-color: var(--cor-primaria);
  animation: resto-spin 1s linear infinite;
}

.resto-loading__text {
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

@keyframes resto-spin {
  to { transform: rotate(360deg); }
}

/* ═══════════════════════════════════════════════════════════════
   HERO - SPLIT SCREEN
═══════════════════════════════════════════════════════════════ */
.resto-hero {
  display: grid;
  grid-template-columns: 1fr;
  min-height: 100vh;
}

@media (min-width: 1024px) {
  .resto-hero {
    grid-template-columns: 1fr 1fr;
  }
}

/* Left Panel */
.resto-hero__left {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  position: relative;
}

@media (min-width: 768px) {
  .resto-hero__left {
    padding: 2rem 3rem;
  }
}

@media (min-width: 1024px) {
  .resto-hero__left {
    padding: 2.5rem 4rem;
  }
}

.resto-hero__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-right: 120px; /* Space for UserProfile/Cart */
}

@media (min-width: 1024px) {
  .resto-hero__topbar {
    padding-right: 0;
  }
}

.resto-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  transition: all 0.2s ease;
  cursor: pointer;
}

.resto-back:hover {
  background: var(--bg-tertiary);
  transform: scale(1.05);
}

.resto-hero__brand-tag {
  font-size: 0.7rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--cor-primaria);
  padding: 0.5rem 1rem;
  border: 1px solid var(--cor-primaria);
  border-radius: 100px;
}

.resto-theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  transition: all 0.2s ease;
  cursor: pointer;
}

.resto-theme-toggle:hover {
  background: var(--bg-tertiary);
}

/* Hero Content */
.resto-hero__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 560px;
}

.resto-hero__location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.resto-hero__title {
  font-family: var(--font-display);
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: 400;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.resto-hero__desc {
  font-size: 1rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin-bottom: 2rem;
  max-width: 480px;
}

/* Stats */
.resto-hero__stats {
  display: flex;
  gap: 2.5rem;
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border-color);
}

.resto-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.resto-stat__value {
  font-family: var(--font-display);
  font-size: 1.75rem;
  color: var(--text-primary);
}

.resto-stat__value--icon {
  color: var(--cor-primaria);
}

.resto-stat__label {
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

/* CTAs */
.resto-hero__ctas {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.resto-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 100px;
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
}

.resto-btn--primary {
  background: var(--cor-primaria);
  color: #0a0a0a;
}

.resto-btn--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(201, 169, 97, 0.3);
}

.resto-btn--outline {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.resto-btn--outline:hover {
  background: var(--bg-secondary);
  border-color: var(--text-primary);
}

/* Bottom */
.resto-hero__bottom {
  margin-top: auto;
  padding-top: 2rem;
}

.resto-hero__scroll-hint {
  display: none;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  letter-spacing: 0.1em;
}

@media (min-width: 1024px) {
  .resto-hero__scroll-hint {
    display: flex;
  }
}

/* Right Panel - Media */
.resto-hero__right {
  position: relative;
  min-height: 50vh;
  overflow: hidden;
}

@media (min-width: 1024px) {
  .resto-hero__right {
    min-height: 100vh;
  }
}

.resto-hero__media-wrapper {
  position: absolute;
  inset: 0;
}

.resto-hero__media {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.resto-hero__media-corners {
  position: absolute;
  inset: 0;
  background: 
    linear-gradient(135deg, var(--bg-primary) 0%, transparent 15%),
    linear-gradient(-135deg, transparent 85%, var(--bg-primary) 100%);
  pointer-events: none;
}

/* Floating Badge */
.resto-hero__floating-badge {
  position: absolute;
  bottom: 2rem;
  left: 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 100px;
  color: #0a0a0a;
  font-weight: 600;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.resto-hero__floating-badge svg {
  color: var(--cor-primaria);
}

/* ═══════════════════════════════════════════════════════════════
   NAVIGATION TABS
═══════════════════════════════════════════════════════════════ */
.resto-tabs {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.resto-tabs__inner {
  display: flex;
  gap: 0.25rem;
  padding: 0.75rem 1.5rem;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

@media (min-width: 768px) {
  .resto-tabs__inner {
    padding: 0.75rem 3rem;
    justify-content: center;
  }
}

.resto-tabs__item {
  flex-shrink: 0;
  padding: 0.625rem 1.25rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.resto-tabs__item:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.resto-tabs__item--active {
  color: #0a0a0a;
  background: var(--cor-primaria);
}

/* ═══════════════════════════════════════════════════════════════
   MAIN CONTENT
═══════════════════════════════════════════════════════════════ */
.resto-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

@media (min-width: 768px) {
  .resto-main {
    padding: 0 3rem;
  }
}

.resto-section {
  padding: 4rem 0;
  border-bottom: 1px solid var(--border-subtle);
}

@media (min-width: 768px) {
  .resto-section {
    padding: 6rem 0;
  }
}

.resto-section--full {
  max-width: none;
}

.resto-section__header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.resto-section__tag {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-style: italic;
  color: var(--cor-primaria);
  padding: 0.5rem 1rem;
  border: 1px solid var(--cor-primaria);
  border-radius: 100px;
}

.resto-section__title {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
}

/* ═══════════════════════════════════════════════════════════════
   BENTO GRID
═══════════════════════════════════════════════════════════════ */
.resto-bento {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .resto-bento {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .resto-bento {
    grid-template-columns: repeat(3, 1fr);
  }
}

.resto-bento__card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1.5rem;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.resto-bento__card:hover {
  border-color: var(--cor-primaria);
}

.resto-bento__card--large {
  grid-column: 1 / -1;
}

@media (min-width: 1024px) {
  .resto-bento__card--large {
    grid-column: span 2;
  }
}

.resto-bento__card--accent {
  background: var(--cor-primaria);
  border-color: var(--cor-primaria);
  color: #0a0a0a;
}

.resto-bento__card--accent .resto-bento__card-header {
  color: #0a0a0a;
}

.resto-bento__card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 1.25rem;
}

.resto-bento__card-body {
  font-size: 0.9rem;
}

.resto-about-text {
  font-size: 1.125rem;
  line-height: 1.8;
  color: var(--text-secondary);
}

.resto-delivery-row {
  display: flex;
  justify-content: space-between;
  padding: 0.625rem 0;
  border-bottom: 1px solid var(--border-subtle);
}

.resto-delivery-row:last-child {
  border-bottom: none;
}

.resto-delivery-price {
  font-weight: 500;
  color: var(--cor-primaria);
}

.resto-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.resto-chip {
  padding: 0.375rem 0.875rem;
  font-size: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 100px;
  color: var(--text-secondary);
}

.resto-location-text {
  font-size: 1rem;
  line-height: 1.6;
}

/* ═══════════════════════════════════════════════════════════════
   PRODUCT STYLES
═══════════════════════════════════════════════════════════════ */
:deep(.resto-product-name) {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 400;
}

:deep(.resto-product-price) {
  color: var(--cor-primaria);
  font-weight: 500;
}

:deep(.resto-badge-chef) {
  background: var(--cor-primaria);
  color: #0a0a0a;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  padding: 0.25rem 0.75rem;
  border-radius: 100px;
}

/* Catalog Tabs */
:deep(.resto-catalog-tab) {
  padding: 0.5rem 1.25rem;
  font-size: 0.8rem;
  border-radius: 100px;
  transition: all 0.2s ease;
}

:deep(.resto-catalog-tab--light) {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

:deep(.resto-catalog-tab--dark) {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

:deep(.resto-catalog-tab--active) {
  background: var(--cor-primaria) !important;
  color: #0a0a0a !important;
}

/* Stars */
:deep(.resto-star--active) {
  color: var(--cor-primaria);
}

:deep(.resto-star--inactive) {
  color: var(--border-color);
}

:deep(.resto-progress) {
  background: var(--cor-primaria);
}

:deep(.resto-review-card) {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

:deep(.resto-review--own-light) {
  border-color: var(--cor-primaria);
}

:deep(.resto-review--own-dark) {
  border-color: var(--cor-primaria);
}

/* ═══════════════════════════════════════════════════════════════
   FOOTER
═══════════════════════════════════════════════════════════════ */
.resto-footer {
  border-top: 1px solid var(--border-color);
  padding: 3rem 1.5rem;
}

@media (min-width: 768px) {
  .resto-footer {
    padding: 4rem 3rem;
  }
}

.resto-footer__inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  align-items: center;
  text-align: center;
}

@media (min-width: 768px) {
  .resto-footer__inner {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
}

.resto-footer__brand {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.resto-footer__name {
  font-family: var(--font-display);
  font-size: 1.25rem;
}

.resto-footer__tagline {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.resto-footer__links {
  display: flex;
  gap: 2rem;
}

.resto-footer__link {
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s ease;
}

.resto-footer__link:hover {
  color: var(--cor-primaria);
}

.resto-footer__copy {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

/* ═══════════════════════════════════════════════════════════════
   MODALS
═══════════════════════════════════════════════════════════════ */
.resto-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.resto-modal {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1.5rem;
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
}

.resto-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.resto-modal__header h3 {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 400;
}

.resto-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.resto-modal__close:hover {
  background: var(--border-color);
}

.resto-modal__body {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: 60vh;
}

.resto-modal__body p {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-secondary);
}

/* ═══════════════════════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════════════════════ */
.hide-scroll {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.hide-scroll::-webkit-scrollbar {
  display: none;
}
</style>
