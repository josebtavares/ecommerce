<!-- LandingFoto.vue — a imagem ou o vídeo (sem som, em ciclo) de uma secção da landing, a encher o sítio onde está
     (cortada nas pontas) ou, com `inteira`, completa: largura toda e altura pela proporção do ficheiro. -->
<template>
  <video v-if="media.tipo === 'video'" :src="media.url" :poster="media.poster || undefined" autoplay muted loop playsinline
         :class="classe" aria-hidden="true"></video>
  <img v-else :src="media.url" alt="" :loading="inteira ? 'eager' : 'lazy'" :class="classe" />
</template>

<script>
export default {
  name: 'LandingFoto',
  props: { media: { type: Object, required: true }, inteira: { type: Boolean, default: false } },
  computed: {
    classe () { return this.inteira ? 'block w-full h-auto max-h-[80vh] object-contain' : 'w-full h-full object-cover' },
  },
}
</script>
