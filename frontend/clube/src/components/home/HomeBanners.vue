<!-- HomeBanners.vue — faixas promocionais da home (Admin → Página inicial); 1 a toda a largura, 2+ em grelha -->
<template>
  <div>
    <div v-if="titulo" class="mb-4">
      <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo }}</h2>
      <p v-if="subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ subtitulo }}</p>
    </div>
    <div class="grid gap-4" :class="banners.length === 1 ? 'grid-cols-1' : banners.length === 2 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1 md:grid-cols-3'">
      <component :is="b.link ? 'button' : 'div'" v-for="(b, i) in banners" :key="i" type="button"
        @click="b.link && $emit('abrir', b.link)"
        class="relative overflow-hidden rounded-3xl text-left group"
        :class="[banners.length === 1 ? 'min-h-[220px] md:min-h-[300px]' : 'min-h-[200px]', b.link ? 'cursor-pointer' : '']">
        <img v-if="b.imagem_url" :src="b.imagem_url" :alt="b.titulo"
          class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition duration-700" />
        <div v-else class="absolute inset-0 bg-gradient-to-br from-red-700 via-red-900 to-zinc-950"></div>
        <div v-if="b.titulo || b.texto" class="absolute inset-0 bg-gradient-to-r from-zinc-950/85 via-zinc-950/40 to-transparent"></div>
        <div v-if="b.titulo || b.texto || b.link" class="relative h-full flex flex-col justify-end p-6 md:p-8 max-w-xl"
             :class="banners.length === 1 ? 'min-h-[220px] md:min-h-[300px]' : 'min-h-[200px]'">
          <h3 v-if="b.titulo" class="text-2xl md:text-3xl font-bold text-white leading-tight">{{ b.titulo }}</h3>
          <p v-if="b.texto" class="text-sm text-zinc-200 mt-2 line-clamp-2">{{ b.texto }}</p>
          <span v-if="b.link" class="inline-flex items-center gap-2 mt-4 self-start px-4 py-2 bg-white/95 group-hover:bg-white text-zinc-900 text-xs font-bold rounded-xl transition">
            Saber mais <font-awesome-icon :icon="['fas', 'arrow-right']" />
          </span>
        </div>
      </component>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeBanners',
  props: {
    banners:   { type: Array,  default: () => [] },
    titulo:    { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark:    { type: Boolean, default: true },
  },
  emits: ['abrir'],
}
</script>
