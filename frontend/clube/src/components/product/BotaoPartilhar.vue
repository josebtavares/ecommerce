<template>
  <!-- partilhar o link do produto: no telemóvel abre o menu do sistema (WhatsApp, Facebook…), senão copia o link.
       A pré-visualização do link vem do servidor do site (scripts/servidor.js) -->
  <button type="button" data-teste="partilhar-produto" :title="copiado ? 'Link copiado' : 'Partilhar'" aria-label="Partilhar"
          class="flex-shrink-0 inline-flex items-center justify-center rounded-full w-[38px] h-[38px] transition"
          :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200' : 'bg-gray-100 hover:bg-gray-200 text-zinc-700'"
          @click.stop.prevent="partilhar">
    <font-awesome-icon :icon="['fas', copiado ? 'check' : 'share-nodes']" class="w-4 h-4" />
  </button>
</template>

<script>
import { toast } from 'vue3-toastify'

export default {
  name: 'BotaoPartilhar',
  props: {
    caminho: { type: String, required: true },   // ex.: /loja/7?produto=82
    titulo:  { type: String, default: '' },
    isDark:  { type: Boolean, default: true },
  },

  data () {
    return { copiado: false, timer: null }
  },

  beforeUnmount () { clearTimeout(this.timer) },

  methods: {
    async partilhar () {
      const url = window.location.origin + this.caminho
      if (navigator.share) {
        try { await navigator.share({ title: this.titulo, url }); return } catch (e) {
          if (e.name === 'AbortError') return     // a pessoa fechou o menu
        }
      }
      try {
        await navigator.clipboard.writeText(url)
        this.copiado = true
        clearTimeout(this.timer)
        this.timer = setTimeout(() => { this.copiado = false }, 2000)
        toast.success('Link copiado')
      } catch (e) {
        toast.error('Não foi possível copiar o link.')
      }
    },
  },
}
</script>
