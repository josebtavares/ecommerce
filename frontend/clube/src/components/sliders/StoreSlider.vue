<template>
  <div v-if="lojas.length > 0 || loading" class="mb-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span v-if="icon" class="text-xl">{{ icon }}</span>
        <h2 class="text-lg font-bold transition-colors"
            :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ title }}</h2>
        <span v-if="!loading" class="text-xs transition-colors"
              :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">({{ total }})</span>
      </div>
      <slot name="header-right" />
    </div>

    <!-- Skeleton -->
    <div v-if="loading && lojas.length === 0" class="flex gap-4 overflow-hidden">
      <div v-for="n in 4" :key="n"
           class="flex-shrink-0 rounded-2xl animate-pulse transition-colors"
           :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"
           style="width:260px;height:200px"></div>
    </div>

    <!-- Swiper -->
    <swiper
      v-else
      :slides-per-view="'auto'"
      :space-between="20"
      :modules="swiperModules"
      class="pb-3"
      @reach-end="loadMore"
    >
      <swiper-slide v-for="loja in lojas" :key="loja.id" class="!w-64">
        <div
          @click="$emit('store-click', loja)"
          class="group relative rounded-2xl overflow-hidden cursor-pointer h-60
                 transition-all hover:-translate-y-1 hover:shadow-xl border"
          :class="isDark
            ? 'bg-zinc-800 border-zinc-700 hover:ring-2 hover:ring-red-500/50 hover:border-transparent'
            : 'bg-stone-100 border-stone-200 hover:ring-2 hover:ring-red-400/40 hover:border-transparent shadow-sm'"
        >
          <img
            :src="loja.banner_url || loja.logo_url || defaultImg"
            :alt="loja.nome"
            class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
          <!-- Gradiente overlay — ligeiramente diferente no light para não escurecer tanto -->
          <div class="absolute inset-0 transition-opacity"
               :class="isDark
                 ? 'bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent'
                 : 'bg-gradient-to-t from-black/80 via-black/30 to-transparent'">
          </div>

          <!-- Logo -->
          <div class="absolute top-3 left-3">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
                 class="w-10 h-10 rounded-xl object-cover shadow-lg border-2 transition-colors"
                 :class="isDark ? 'border-zinc-700' : 'border-white/50'" />
            <div v-else
                 class="w-10 h-10 rounded-xl flex items-center justify-center border-2 transition-colors"
                 :class="isDark
                   ? 'bg-zinc-700 border-zinc-600'
                   : 'bg-white/80 border-white/60'">
              <span class="text-sm font-bold transition-colors"
                    :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
                {{ loja.nome.charAt(0) }}
              </span>
            </div>
          </div>

          <!-- Rating -->
          <div v-if="loja.rating_medio"
               class="absolute top-3 right-3 px-2 py-0.5 backdrop-blur rounded-lg flex items-center gap-1 transition-colors"
               :class="isDark ? 'bg-zinc-900/80' : 'bg-black/50'">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <span class="text-xs font-semibold text-white">{{ loja.rating_medio }}</span>
          </div>

          <!-- Info (fundo sempre escuro para legibilidade sobre imagem) -->
          <div class="absolute bottom-0 left-0 right-0 p-3">
            <span class="inline-block px-1.5 py-0.5 bg-red-600/90 text-white text-[10px] font-bold rounded mb-1">
              {{ loja.categoria }}
            </span>
            <h3 class="text-sm font-bold text-white truncate group-hover:text-red-400 transition-colors">
              {{ loja.nome }}
            </h3>
            <p v-if="loja.localizacao" class="text-xs text-zinc-300 truncate mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 inline mr-0.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              </svg>
              {{ loja.localizacao }}
            </p>
            <div class="flex gap-1.5 mt-1.5">
              <span v-if="loja.entrega_ativa"
                    class="px-1.5 py-0.5 bg-green-600/20 text-green-400 text-[10px] rounded">
                Entrega
              </span>
              <span v-if="loja.levantamento_ativo"
                    class="px-1.5 py-0.5 bg-blue-600/20 text-blue-400 text-[10px] rounded">
                Takeaway
              </span>
            </div>
          </div>
        </div>
      </swiper-slide>

      <!-- Loading mais -->
      <swiper-slide v-if="loadingMore" class="!w-64">
        <div class="w-64 h-48 rounded-2xl animate-pulse flex-shrink-0 transition-colors"
             :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
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
  name: 'StoreSlider',
  components: { Swiper, SwiperSlide },

  props: {
    title:    { type: String,  required: true },
    icon:     { type: String,  default: '' },
    params:   { type: Object,  default: () => ({}) },
    endpoint: { type: String,  default: '/app/loja/' },
    limit:    { type: Number,  default: 8 },
    isDark:   { type: Boolean, default: true },
  },

  emits: ['store-click'],

  data () {
    return {
      swiperModules: [FreeMode],
      lojas: [],
      offset: 0,
      total: 0,
      loading: false,
      loadingMore: false,
      reachedEnd: false,
      defaultImg: (process.env.VUE_APP_URL_BASE || 'http://localhost:8000') + '/media/lojas/default_banner.jpg',
    }
  },

  async created () {
    await this.fetch(true)
  },

  methods: {
    async fetch (reset = false) {
      if (this.reachedEnd && !reset) return
      if (reset) {
        this.loading = true
        this.lojas = []
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
        this.lojas.push(...results)
        this.total = data.count ?? this.lojas.length
        this.offset = data.next_offset ?? null
        this.reachedEnd = !this.offset
      } catch (e) {
        console.error('StoreSlider erro:', e)
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