<template>
  <div v-if="produtos.length > 0 || loading" class="mb-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span v-if="icon" class="text-xl">{{ icon }}</span>
        <h2 class="text-lg font-bold text-zinc-100">{{ title }}</h2>
        <span v-if="!loading" class="text-xs text-zinc-600">({{ total }})</span>
      </div>
      <slot name="header-right" />
    </div>

    <!-- Skeleton loading -->
    <div v-if="loading && produtos.length === 0" class="flex gap-4 overflow-hidden">
      <div v-for="n in 5" :key="n"
           class="w-44 flex-shrink-0 bg-zinc-800 rounded-2xl animate-pulse" style="height:220px"></div>
    </div>

    <!-- Swiper -->
    <swiper
      v-else
      ref="swiperRef"
      :slides-per-view="'auto'"
      :space-between="16"
      :modules="swiperModules"
      class="pb-3"
      @reach-end="loadMore"
    >
      <swiper-slide v-for="produto in produtos" :key="produto.id" class="!w-44">
        <div
          @click="$emit('product-click', produto)"
          class="group bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800
                 hover:border-red-500/40 transition-all cursor-pointer hover:-translate-y-1 hover:shadow-xl"
        >
          <div class="relative h-36 overflow-hidden">
            <img
              :src="produto.ficheiro_url || defaultImg"
              :alt="produto.nome"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <span v-if="produto.destaque"
                  class="absolute top-2 right-2 px-1.5 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded">
              ⭐
            </span>
            <div v-if="produto.stock && produto.stock.quantidade === 0"
                 class="absolute inset-0 bg-black/60 flex items-center justify-center text-xs font-bold text-zinc-300">
              Sem stock
            </div>
          </div>
          <div class="p-3">
            <p class="text-sm font-semibold text-zinc-100 truncate">{{ produto.nome }}</p>
            <p class="text-xs text-zinc-500 mt-0.5 truncate">{{ produto.loja?.nome }}</p>
            <div class="flex items-center justify-between mt-2">
              <span class="text-sm font-bold text-red-400">{{ formatPrice(produto.preco) }}</span>
              <span v-if="produto.stock" class="text-[10px] text-zinc-600">
                {{ produto.stock.quantidade }} un.
              </span>
            </div>
          </div>
        </div>
      </swiper-slide>

      <!-- Loading mais -->
      <swiper-slide v-if="loadingMore" class="!w-44">
        <div class="w-44 h-52 bg-zinc-800 rounded-2xl animate-pulse flex-shrink-0"></div>
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
    title:    { type: String, required: true },
    icon:     { type: String, default: '' },
    params:   { type: Object, default: () => ({}) },
    endpoint: { type: String, default: '/app/produto/' },
    limit:    { type: Number, default: 10 },
  },

  emits: ['product-click'],

  data () {
    return {
      swiperModules: [FreeMode],
      produtos: [],
      offset: 0,
      total: 0,
      loading: false,
      loadingMore: false,
      reachedEnd: false,
      defaultImg: (process.env.VUE_APP_URL_BASE || 'http://localhost:8000') + '/media/produtos/default.jpg',
    }
  },

  async created () {
    await this.fetch(true)
  },

  methods: {
    formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    },

    async fetch (reset = false) {
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
          params: { ...this.params, limit: this.limit, offset: this.offset }
        })
        const results = data.results || data
        this.produtos.push(...results)
        this.total = data.count ?? this.produtos.length
        this.offset = data.next_offset ?? null
        this.reachedEnd = !this.offset
      } catch (e) {
        console.error('ProductSlider erro:', e)
      } finally {
        this.loading = false
        this.loadingMore = false
      }
    },

    loadMore () {
      if (!this.reachedEnd && !this.loadingMore) {
        this.fetch(false)
      }
    },
  }
}
</script>

<style scoped>
.swiper { overflow: hidden !important; }
</style>