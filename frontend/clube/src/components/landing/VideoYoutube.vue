<!-- VideoYoutube.vue — vídeo do YouTube que só carrega ao clicar (a página fica leve com muitos tutoriais):
     antes mostra a miniatura e um botão play; depois o leitor do YouTube no modo de privacidade (youtube-nocookie,
     permitido no frame-src do CSP — scripts/csp.js). -->
<template>
  <div class="relative aspect-video rounded-2xl overflow-hidden bg-black" data-teste="video-youtube">
    <iframe v-if="aTocar" :src="embed" :title="titulo || 'Vídeo do YouTube'" class="absolute inset-0 w-full h-full" data-teste="youtube-iframe"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
    <button v-else type="button" @click="aTocar = true" :aria-label="`Ver o vídeo: ${titulo}`" data-teste="youtube-play"
            class="group absolute inset-0 w-full h-full">
      <img :src="miniatura" alt="" loading="lazy" class="w-full h-full object-cover transition duration-300 group-hover:scale-105 group-hover:opacity-90" />
      <span class="absolute inset-0 flex items-center justify-center">
        <span class="w-16 h-16 rounded-full bg-red-600 text-white flex items-center justify-center shadow-2xl transition group-hover:scale-110">
          <font-awesome-icon :icon="['fas', 'play']" class="w-6 h-6 ml-1" />
        </span>
      </span>
    </button>
  </div>
</template>

<script>
export default {
  name: 'VideoYoutube',
  props: {
    id: { type: String, required: true },
    titulo: { type: String, default: '' },
    miniatura: { type: String, default: '' },
  },
  data () { return { aTocar: false } },
  computed: {
    embed () {
      return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(this.id)}?autoplay=1&rel=0&playsinline=1`
    },
  },
  watch: { id () { this.aTocar = false } },
}
</script>
