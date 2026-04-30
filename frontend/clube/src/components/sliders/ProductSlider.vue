<template>
  <div v-if="produtos.length > 0 || loading" :class="['mb-10', containerClass]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4 gap-3">
      <div class="flex items-center gap-2 min-w-0">
        <!--<span v-if="icon" :class="['text-xl', iconClass]">{{ icon }}</span> -->

        <h2
          :class="[
            'font-bold truncate',
            titleSize,
            isDark ? 'text-zinc-100' : 'text-zinc-900',
            titleClass
          ]"
        >
          {{ title }}
        </h2>

        <span
          v-if="!loading"
          :class="[
            'text-xs flex-shrink-0',
            isDark ? 'text-zinc-600' : 'text-zinc-400',
            countClass
          ]"
        >
          ({{ total }})
        </span>
      </div>

      <div class="flex items-center gap-2 flex-shrink-0">
        <slot name="header-right" />

        <!-- Slider controls -->
        <div
          v-if="showControls"
          class="flex items-center gap-1.5"
        >
          <button
            type="button"
            class="product-slider-control"
            :class="[
              isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800 hover:text-white hover:border-zinc-700'
                : 'bg-white border-gray-200 text-zinc-600 hover:bg-gray-50 hover:text-zinc-900 hover:border-gray-300 shadow-sm',
              !canSlidePrev ? 'opacity-40 cursor-not-allowed pointer-events-none' : ''
            ]"
            :disabled="!canSlidePrev"
            aria-label="Scroll left"
            @click="slidePrev"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <button
            type="button"
            class="product-slider-control"
            :class="[
              isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800 hover:text-white hover:border-zinc-700'
                : 'bg-white border-gray-200 text-zinc-600 hover:bg-gray-50 hover:text-zinc-900 hover:border-gray-300 shadow-sm',
              !canSlideNext ? 'opacity-40 cursor-not-allowed pointer-events-none' : ''
            ]"
            :disabled="!canSlideNext"
            aria-label="Scroll right"
            @click="slideNext"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Skeleton -->
    <div v-if="loading && produtos.length === 0" class="flex gap-4 overflow-hidden">
      <div
        v-for="n in 5"
        :key="n"
        :class="[
          'flex-shrink-0 animate-pulse',
          skeletonClass,
          isDark ? 'bg-zinc-800' : 'bg-gray-200'
        ]"
        :style="{ width: cardWidth, height: cardHeight }"
      ></div>
    </div>

    <!-- Swiper -->
    <swiper
      v-else
      ref="swiperRef"
      :slides-per-view="'auto'"
      :space-between="cardGap"
      :modules="swiperModules"
      :free-mode="true"
      :watch-overflow="true"
      class="pb-3 product-slider-swiper"
      @swiper="onSwiper"
      @slide-change="updateNavigationState"
      @reach-end="loadMore"
      @from-edge="updateNavigationState"
      @to-edge="updateNavigationState"
      @resize="updateNavigationState"
    >
      <swiper-slide
        v-for="produto in produtos"
        :key="produto.id"
        :style="{ width: cardWidth }"
      >
        <div
          @click="$emit('product-click', produto)"
          :class="[
            'group overflow-hidden border transition-all cursor-pointer',
            cardBorderRadius,
            hoverEffect,
            isDark
              ? `bg-zinc-900 border-zinc-800 ${hoverBorderClass || 'hover:border-red-500/40'}`
              : `bg-white border-gray-200 ${hoverBorderClass || 'hover:border-red-400/50'} shadow-sm`,
            cardClass
          ]"
        >
          <!-- Image -->
          <div
            :class="['relative overflow-hidden', imageContainerClass]"
            :style="{ height: imageHeight }"
          >
            <img
              :src="produto.ficheiro_url || defaultImg"
              :alt="produto.nome"
              :class="[
                'w-full h-full object-cover transition-transform duration-300',
                imageHoverEffect
              ]"
            />

            <span
              v-if="produto.destaque && showBadges"
              :class="['absolute top-2 right-2 px-1.5 py-0.5 text-white text-[10px] font-bold', badgeClass]"
            >
              {{ badgeText }}
            </span>

            <div
              v-if="produto.stock && produto.stock.quantidade === 0"
              class="absolute inset-0 bg-black/60 flex items-center justify-center text-xs font-bold text-zinc-300"
            >
              Sem stock
            </div>
          </div>

          <!-- Info -->
          <div :class="['p-3', contentClass]">
            <p
              :class="[
                'font-semibold truncate',
                productNameSize,
                isDark ? 'text-zinc-100' : 'text-zinc-900',
                productNameClass
              ]"
            >
              {{ produto.nome }}
            </p>

            <p
              v-if="showStoreName"
              :class="[
                'text-xs mt-0.5 truncate',
                isDark ? 'text-zinc-500' : 'text-zinc-400',
                storeNameClass
              ]"
            >
              {{ produto.loja?.nome }}
            </p>

            <div class="flex items-center justify-between mt-2">
              <span :class="['font-bold', priceSize, priceClass]">
                {{ formatPrice(produto.preco) }}
              </span>

              <span
                v-if="produto.stock && showStock"
                :class="[
                  'text-[10px]',
                  isDark ? 'text-zinc-600' : 'text-zinc-400'
                ]"
              >
                {{ produto.stock.quantidade }} un.
              </span>
            </div>
          </div>
        </div>
      </swiper-slide>

      <swiper-slide v-if="loadingMore" :style="{ width: cardWidth }">
        <div
          :class="[
            'animate-pulse flex-shrink-0',
            skeletonClass,
            isDark ? 'bg-zinc-800' : 'bg-gray-200'
          ]"
          :style="{ width: cardWidth, height: cardHeight }"
        ></div>
      </swiper-slide>
    </swiper>
  </div>
</template>

<script>
import { Swiper, SwiperSlide } from 'swiper/vue'
import { FreeMode } from 'swiper/modules'
import 'swiper/css'
import api from '@/services/api'

export default {
  name: 'ProductSlider',

  components: {
    Swiper,
    SwiperSlide,
  },

  props: {
    // Core
    title: { type: String, required: true },
    icon: { type: String, default: '' },
    params: { type: Object, default: () => ({}) },
    endpoint: { type: String, default: '/app/produto/' },
    limit: { type: Number, default: 10 },
    isDark: { type: Boolean, default: true },

    // Card dimensions
    cardWidth: { type: String, default: '176px' },
    cardHeight: { type: String, default: '220px' },
    imageHeight: { type: String, default: '144px' },
    cardGap: { type: Number, default: 16 },

    // Styling classes
    containerClass: { type: String, default: '' },
    cardClass: { type: String, default: '' },
    cardBorderRadius: { type: String, default: 'rounded-2xl' },
    imageContainerClass: { type: String, default: '' },
    contentClass: { type: String, default: '' },
    skeletonClass: { type: String, default: 'rounded-2xl' },

    // Typography
    titleSize: { type: String, default: 'text-lg' },
    titleClass: { type: String, default: '' },
    productNameSize: { type: String, default: 'text-sm' },
    productNameClass: { type: String, default: '' },
    priceSize: { type: String, default: 'text-sm' },
    priceClass: { type: String, default: 'text-red-500' },
    storeNameClass: { type: String, default: '' },
    iconClass: { type: String, default: '' },
    countClass: { type: String, default: '' },

    // Hover effects
    hoverEffect: { type: String, default: 'hover:-translate-y-1 hover:shadow-xl' },
    hoverBorderClass: { type: String, default: '' },
    imageHoverEffect: { type: String, default: 'group-hover:scale-105' },

    // Badge
    showBadges: { type: Boolean, default: true },
    badgeText: { type: String, default: '⭐' },
    badgeClass: { type: String, default: 'bg-red-600 rounded' },

    // Display options
    showStoreName: { type: Boolean, default: true },
    showStock: { type: Boolean, default: true },

    // Controls
    showControls: { type: Boolean, default: true },
    slidesPerClick: { type: Number, default: 2 },
  },

  emits: ['product-click'],

  data() {
    return {
      swiperModules: [FreeMode],
      swiperInstance: null,

      produtos: [],
      offset: 0,
      total: 0,

      loading: false,
      loadingMore: false,
      reachedEnd: false,

      canSlidePrev: false,
      canSlideNext: false,

      defaultImg: (process.env.VUE_APP_URL_BASE || 'http://localhost:8000') + '/media/produtos/default.jpg',
    }
  },

  async created() {
    await this.fetch(true)
  },

  methods: {
    formatPrice(val) {
      return new Intl.NumberFormat('pt-PT', {
        style: 'currency',
        currency: 'EUR',
      }).format(val || 0)
    },

    onSwiper(swiper) {
      this.swiperInstance = swiper

      this.$nextTick(() => {
        this.updateNavigationState()
      })
    },

    updateNavigationState() {
      if (!this.swiperInstance) return

      this.canSlidePrev = !this.swiperInstance.isBeginning
      this.canSlideNext = !this.swiperInstance.isEnd || !this.reachedEnd
    },

    slidePrev() {
      if (!this.swiperInstance) return

      this.swiperInstance.slidePrev(300)

      this.$nextTick(() => {
        this.updateNavigationState()
      })
    },

    slideNext() {
      if (!this.swiperInstance) return

      if (this.swiperInstance.isEnd && !this.reachedEnd && !this.loadingMore) {
        this.loadMore()
        return
      }

      const currentIndex = this.swiperInstance.activeIndex || 0
      const nextIndex = currentIndex + this.slidesPerClick

      this.swiperInstance.slideTo(nextIndex, 300)

      this.$nextTick(() => {
        this.updateNavigationState()
      })
    },

    async fetch(reset = false) {
      if (this.reachedEnd && !reset) return

      if (reset) {
        this.loading = true
        this.produtos = []
        this.offset = 0
        this.reachedEnd = false
      } else {
        this.loadingMore = true
      }

      try {
        const { data } = await api.get(this.endpoint, {
          params: {
            ...this.params,
            limit: this.limit,
            offset: this.offset,
          },
        })

        const results = data.results || data

        this.produtos.push(...results)
        this.total = data.count ?? this.produtos.length
        this.offset = data.next_offset ?? null
        this.reachedEnd = !this.offset

        this.$nextTick(() => {
          if (this.swiperInstance) {
            this.swiperInstance.update()
            this.updateNavigationState()
          }
        })
      } catch (e) {
        console.error('ProductSlider erro:', e)
      } finally {
        this.loading = false
        this.loadingMore = false

        this.$nextTick(() => {
          if (this.swiperInstance) {
            this.swiperInstance.update()
            this.updateNavigationState()
          }
        })
      }
    },

    loadMore() {
      if (!this.reachedEnd && !this.loadingMore) {
        this.fetch(false)
      }
    },
  },
}
</script>

<style scoped>
.product-slider-swiper {
  overflow: hidden !important;
}

.product-slider-control {
  width: 34px;
  height: 34px;
  border-width: 1px;
  border-style: solid;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.product-slider-control:hover {
  transform: translateY(-1px);
}

.product-slider-control:active {
  transform: translateY(0);
}

@media (max-width: 520px) {
  .product-slider-control {
    width: 32px;
    height: 32px;
  }
}
</style>