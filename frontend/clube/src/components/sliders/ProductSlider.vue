<template>
  <div v-if="produtos.length > 0 || loading" :class="['mb-10', containerClass]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <!--<span v-if="icon" :class="['text-xl', iconClass]">{{ icon }}</span> -->
        <h2 :class="[
          'font-bold',
          titleSize,
          isDark ? 'text-zinc-100' : 'text-zinc-900',
          titleClass
        ]">{{ title }}</h2>
        <span v-if="!loading" :class="[
          'text-xs',
          isDark ? 'text-zinc-600' : 'text-zinc-400',
          countClass
        ]">({{ total }})</span>
      </div>
      <slot name="header-right" />
    </div>

    <!-- Skeleton -->
    <div v-if="loading && produtos.length === 0" class="flex gap-4 overflow-hidden">
      <div v-for="n in 5" :key="n"
           :class="[
             'flex-shrink-0 animate-pulse',
             skeletonClass,
             isDark ? 'bg-zinc-800' : 'bg-gray-200'
           ]"
           :style="{ width: cardWidth, height: cardHeight }"></div>
    </div>

    <!-- Swiper -->
    <swiper v-else ref="swiperRef" :slides-per-view="'auto'" :space-between="cardGap"
            :modules="swiperModules" class="pb-3" @reach-end="loadMore">
      <swiper-slide v-for="produto in produtos" :key="produto.id" :style="{ width: cardWidth }">
        <div @click="$emit('product-click', produto)"
             :class="[
               'group overflow-hidden border transition-all cursor-pointer',
               cardBorderRadius,
               hoverEffect,
               isDark
                 ? `bg-zinc-900 border-zinc-800 ${hoverBorderClass || 'hover:border-red-500/40'}`
                 : `bg-white border-gray-200 ${hoverBorderClass || 'hover:border-red-400/50'} shadow-sm`,
               cardClass
             ]">
          <!-- Image -->
          <div :class="['relative overflow-hidden', imageContainerClass]" :style="{ height: imageHeight }">
            <img :src="produto.ficheiro_url || defaultImg" :alt="produto.nome"
                 :class="[
                   'w-full h-full object-cover transition-transform duration-300',
                   imageHoverEffect
                 ]" />
            <span v-if="produto.destaque && showBadges"
                  :class="['absolute top-2 right-2 px-1.5 py-0.5 text-white text-[10px] font-bold', badgeClass]">
              {{ badgeText }}
            </span>
            <div v-if="produto.stock && produto.stock.quantidade === 0"
                 class="absolute inset-0 bg-black/60 flex items-center justify-center text-xs font-bold text-zinc-300">
              Sem stock
            </div>
          </div>
          <!-- Info -->
          <div :class="['p-3', contentClass]">
            <p :class="[
              'font-semibold truncate',
              productNameSize,
              isDark ? 'text-zinc-100' : 'text-zinc-900',
              productNameClass
            ]">{{ produto.nome }}</p>
            <p v-if="showStoreName" :class="[
              'text-xs mt-0.5 truncate',
              isDark ? 'text-zinc-500' : 'text-zinc-400',
              storeNameClass
            ]">
              {{ produto.loja?.nome }}
            </p>
            <div class="flex items-center justify-between mt-2">
              <span :class="['font-bold', priceSize, priceClass]">{{ formatPrice(produto.preco) }}</span>
              <span v-if="produto.stock && showStock" :class="[
                'text-[10px]',
                isDark ? 'text-zinc-600' : 'text-zinc-400'
              ]">
                {{ produto.stock.quantidade }} un.
              </span>
            </div>
          </div>
        </div>
      </swiper-slide>

      <swiper-slide v-if="loadingMore" :style="{ width: cardWidth }">
        <div :class="[
          'animate-pulse flex-shrink-0',
          skeletonClass,
          isDark ? 'bg-zinc-800' : 'bg-gray-200'
        ]" :style="{ width: cardWidth, height: cardHeight }"></div>
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
  components: { Swiper, SwiperSlide },

  props: {
    // Core
    title:    { type: String, required: true },
    icon:     { type: String, default: '' },
    params:   { type: Object, default: () => ({}) },
    endpoint: { type: String, default: '/app/produto/' },
    limit:    { type: Number, default: 10 },
    isDark:   { type: Boolean, default: true },
    
    // Card dimensions
    cardWidth:    { type: String, default: '176px' },   // w-44 = 176px
    cardHeight:   { type: String, default: '220px' },
    imageHeight:  { type: String, default: '144px' },   // h-36 = 144px
    cardGap:      { type: Number, default: 16 },
    
    // Styling classes
    containerClass:     { type: String, default: '' },
    cardClass:          { type: String, default: '' },
    cardBorderRadius:   { type: String, default: 'rounded-2xl' },
    imageContainerClass:{ type: String, default: '' },
    contentClass:       { type: String, default: '' },
    skeletonClass:      { type: String, default: 'rounded-2xl' },
    
    // Typography
    titleSize:        { type: String, default: 'text-lg' },
    titleClass:       { type: String, default: '' },
    productNameSize:  { type: String, default: 'text-sm' },
    productNameClass: { type: String, default: '' },
    priceSize:        { type: String, default: 'text-sm' },
    priceClass:       { type: String, default: 'text-red-500' },
    storeNameClass:   { type: String, default: '' },
    iconClass:        { type: String, default: '' },
    countClass:       { type: String, default: '' },
    
    // Hover effects
    hoverEffect:      { type: String, default: 'hover:-translate-y-1 hover:shadow-xl' },
    hoverBorderClass: { type: String, default: '' },
    imageHoverEffect: { type: String, default: 'group-hover:scale-105' },
    
    // Badge
    showBadges:  { type: Boolean, default: true },
    badgeText:   { type: String, default: '⭐' },
    badgeClass:  { type: String, default: 'bg-red-600 rounded' },
    
    // Display options
    showStoreName: { type: Boolean, default: true },
    showStock:     { type: Boolean, default: true },
  },

  emits: ['product-click'],

  data () {
    return {
      swiperModules: [FreeMode],
      produtos: [], offset: 0, total: 0,
      loading: false, loadingMore: false, reachedEnd: false,
      defaultImg: (process.env.VUE_APP_URL_BASE || 'http://localhost:8000') + '/media/produtos/default.jpg',
    }
  },

  async created () { await this.fetch(true) },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },
    async fetch (reset = false) {
      if (this.reachedEnd && !reset) return
      reset ? (this.loading = true, this.produtos = [], this.offset = 0, this.reachedEnd = false)
            : (this.loadingMore = true)
      try {
        const { data } = await api.get(this.endpoint, {
          params: { ...this.params, limit: this.limit, offset: this.offset }
        })
        const results = data.results || data
        this.produtos.push(...results)
        this.total    = data.count ?? this.produtos.length
        this.offset   = data.next_offset ?? null
        this.reachedEnd = !this.offset
      } catch (e) { console.error('ProductSlider erro:', e) }
      finally { this.loading = false; this.loadingMore = false }
    },
    loadMore () { if (!this.reachedEnd && !this.loadingMore) this.fetch(false) },
  }
}
</script>

<style scoped>
.swiper { overflow: hidden !important; }
</style>
