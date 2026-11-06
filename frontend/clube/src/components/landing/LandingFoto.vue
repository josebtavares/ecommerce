<!-- LandingFoto.vue — a imagem ou o vídeo (sem som, em ciclo) de uma secção da landing, a encher o sítio onde está. -->
<template>
  <video v-if="media.tipo === 'video'" :src="media.url" :poster="media.poster || undefined" autoplay muted loop playsinline
         class="w-full h-full object-cover" aria-hidden="true"></video>
  <img v-else :src="media.url" alt="" loading="lazy" class="w-full h-full object-cover" />
</template>

<script>
export default {
  name: 'LandingFoto',
  props: { media: { type: Object, required: true } },
}
</script>
