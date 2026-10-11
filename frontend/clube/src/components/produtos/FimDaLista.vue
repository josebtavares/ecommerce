<!-- FimDaLista.vue — sentinela de scroll infinito.
     Emite "visivel" quando entra no ecrã (ou perto dele). Funciona dentro de filas com
     overflow horizontal: o recorte do contentor conta para a visibilidade.
     Muda :chave (ex.: itens.length) depois de carregar para voltar a verificar —
     se continuar visível, pede a página seguinte.
     O conteúdo do slot (ex.: um cartão-esqueleto) é o que o utilizador vê enquanto carrega.
-->
<template>
  <div ref="el" aria-hidden="true">
    <slot />
  </div>
</template>

<script>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'

export default {
  name: 'FimDaLista',

  props: {
    chave:  { type: [Number, String], default: 0 },
    margem: { type: String, default: '300px 600px 300px 600px' },
  },

  emits: ['visivel'],

  setup (props, { emit }) {
    const el = ref(null)
    let observer = null

    onMounted(() => {
      if (typeof IntersectionObserver === 'undefined') return
      observer = new IntersectionObserver(entries => {
        if (entries.some(e => e.isIntersecting)) emit('visivel')
      }, { rootMargin: props.margem })
      observer.observe(el.value)
    })

    // observar de novo dispara o callback com o estado actual
    watch(() => props.chave, async () => {
      await nextTick()
      if (!observer || !el.value) return
      observer.unobserve(el.value)
      observer.observe(el.value)
    })

    onUnmounted(() => observer?.disconnect())

    return { el }
  },
}
</script>
