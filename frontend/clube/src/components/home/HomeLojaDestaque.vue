<!-- HomeLojaDestaque.vue — bloco grande de uma loja escolhida no admin (Admin → Página inicial) -->
<template>
  <div>
    <div v-if="titulo" class="mb-4">
      <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo }}</h2>
      <p v-if="subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ subtitulo }}</p>
    </div>

    <div class="rounded-3xl overflow-hidden border grid grid-cols-1 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]"
         :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200 shadow-sm'">
      <!-- Loja -->
      <button type="button" @click="$emit('store-click', loja)"
        class="relative min-h-[260px] lg:min-h-[380px] text-left group overflow-hidden">
        <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url"
          class="absolute inset-0 w-full h-full object-cover" v-video-visivel="'destaque'" muted loop playsinline></video>
        <img v-else v-img :src="loja.banner_url || bannerPadrao" :alt="loja.nome"
          class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition duration-700" />
        <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/50 to-transparent"></div>
        <div class="absolute bottom-0 left-0 right-0 p-6 md:p-8">
          <div class="flex items-center gap-3 mb-3">
            <img v-if="loja.logo_url" v-img :src="$miniatura(loja.logo_url)" :alt="loja.nome"
              class="w-14 h-14 rounded-2xl object-cover border-2 border-white/20" />
            <span class="px-2.5 py-1 bg-red-600 text-white text-[10px] font-bold rounded-full uppercase tracking-wider">Loja em destaque</span>
          </div>
          <h3 class="text-3xl md:text-4xl font-bold text-white leading-tight">{{ loja.nome }}</h3>
          <p v-if="loja.descricao" class="text-sm text-zinc-300 mt-2 line-clamp-2">{{ loja.descricao }}</p>
          <div class="flex items-center gap-4 text-zinc-300 text-sm flex-wrap mt-3">
            <span v-if="loja.rating_medio" class="flex items-center gap-1">
              <font-awesome-icon :icon="['fas', 'star']" class="text-yellow-400" /> {{ loja.rating_medio }}
              <span class="text-zinc-400">({{ loja.total_avaliacoes }})</span>
            </span>
            <span v-if="loja.localizacao" class="flex items-center gap-1.5">
              <font-awesome-icon :icon="['fas', 'location-dot']" /> {{ loja.localizacao }}
            </span>
            <span v-if="loja.horario?.ativo" :class="loja.horario.aberta ? 'text-green-400' : 'text-zinc-400'">
              {{ loja.horario.aberta ? 'Aberta agora' : 'Fechada' }}
            </span>
          </div>
          <span class="inline-flex items-center gap-2 mt-5 px-5 py-2.5 bg-red-600 group-hover:bg-red-500 text-white text-sm font-bold rounded-xl transition">
            Visitar loja <font-awesome-icon :icon="['fas', 'arrow-right']" />
          </span>
        </div>
      </button>

      <!-- Produtos -->
      <div class="p-5 md:p-6 min-w-0 flex flex-col justify-center">
        <ProductSlider v-if="produtos.length" :title="`Da ${loja.nome}`"
          :inicial="{ results: produtos, count: produtos.length, next_offset: null }"
          :isDark="isDark" :showStoreName="false" containerClass="!mb-0"
          @product-click="$emit('product-click', $event)" />
        <!-- loja só de serviços: os serviços dela -->
        <HomeServicos v-else-if="servicos.length" class="min-w-0" :servicos="servicos"
          :titulo="`Serviços da ${loja.nome}`" tamanhoTitulo="text-lg" :isDark="isDark" />
        <p v-else class="text-sm text-center py-10" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Visita a loja para ver os produtos.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import HomeServicos from './HomeServicos.vue'
import { DEFAULT_BANNER } from '@/services/media'

export default {
  name: 'HomeLojaDestaque',
  components: { ProductSlider, HomeServicos },
  props: {
    loja:      { type: Object, required: true },
    produtos:  { type: Array,  default: () => [] },
    servicos:  { type: Array,  default: () => [] },   // só quando a loja não tem produtos
    titulo:    { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark:    { type: Boolean, default: true },
  },
  emits: ['store-click', 'product-click'],
  data () { return { bannerPadrao: DEFAULT_BANNER } },
  methods: {
    isVideo (url) { return /\.(mp4|webm|mov|mkv)$/i.test(url || '') },
  },
}
</script>
