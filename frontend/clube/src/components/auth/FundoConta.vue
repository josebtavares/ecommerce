<!-- FundoConta.vue — fundo do login, registo e recuperar senha: imagem ou vídeo escolhidos em
     Admin → Definições → Aparência (utils/aparencia.js); sem nada escolhido, o vídeo original. -->
<template>
  <img v-if="fundo.tipo === 'imagem' || paradoNoPoster" :key="'i' + (paradoNoPoster ? fundo.poster : fundo.url)"
       :src="paradoNoPoster ? fundo.poster : fundo.url" alt="" aria-hidden="true"
       class="absolute inset-0 w-full h-full object-cover" />
  <video v-else :key="'v' + fundo.url" autoplay muted loop playsinline :poster="fundo.poster || undefined"
         aria-hidden="true" class="absolute inset-0 w-full h-full object-cover">
    <source :src="fundo.url" type="video/mp4">
  </video>
</template>

<script>
import { fundoPara } from '@/utils/aparencia'
import { poupar } from '@/utils/media'

export default {
  name: 'FundoConta',
  props: {
    qual: { type: String, default: 'login' },     // 'login' (também recuperar senha) | 'registo'
  },
  computed: {
    fundo () { return fundoPara(this.qual) },
    // "Poupança de dados" / "Reduzir movimento": fica a imagem do vídeo, quando a há
    paradoNoPoster () { return this.fundo.tipo === 'video' && !!this.fundo.poster && poupar() },
  },
}
</script>
