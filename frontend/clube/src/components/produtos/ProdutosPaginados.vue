<!-- ProdutosPaginados.vue — lista de produtos paginada pelo servidor, sem markup próprio.
     Pede só a primeira página quando a secção se aproxima do ecrã (lazy) e as seguintes
     quando o template chama carregarMais() — por ex. com <FimDaLista> no fim de uma fila
     horizontal (scroll infinito) ou num botão "Ver mais".

     <ProdutosPaginados :params="{ loja_id, tipo_id: 3 }" :limit="10" v-slot="l">
       <Card v-for="p in l.itens" ... />
       <FimDaLista v-if="l.temMais" :chave="l.itens.length" @visivel="l.carregarMais" />
     </ProdutosPaginados>

     Slot: itens, total, carregando (1.ª página), aCarregarMais, temMais, carregarMais, iniciado
-->
<template>
  <component :is="tag" ref="raiz">
    <slot v-bind="estado" />
  </component>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

export default {
  name: 'ProdutosPaginados',

  props: {
    params:   { type: Object, default: () => ({}) },
    limit:    { type: Number, default: 10 },
    endpoint: { type: String, default: '/app/produto/' },
    lazy:     { type: Boolean, default: true },
    tag:      { type: String, default: 'div' },
  },

  emits: ['total'],

  setup (props, { emit }) {
    const raiz = ref(null)
    const itens = ref([])
    const total = ref(null)
    const offset = ref(0)            // null = não há mais páginas
    const iniciado = ref(false)
    const carregando = ref(false)
    const aCarregarMais = ref(false)
    let pedido = 0                   // ignora respostas de params antigos
    let observer = null

    async function buscar (reset) {
      if (reset) {
        pedido++
        itens.value = []
        offset.value = 0
        total.value = null
        carregando.value = true
      } else {
        if (offset.value === null || carregando.value || aCarregarMais.value) return
        aCarregarMais.value = true
      }
      const meu = pedido
      try {
        const { data } = await api.get(props.endpoint, {
          params: { ...props.params, limit: props.limit, offset: offset.value },
        })
        if (meu !== pedido) return
        const novos = data.results || data
        const vistos = new Set(itens.value.map(p => p.id))
        itens.value.push(...novos.filter(p => !vistos.has(p.id)))
        total.value = data.count ?? itens.value.length
        offset.value = data.next_offset ?? null
        emit('total', total.value)
      } catch (e) {
        console.error('ProdutosPaginados:', e)
        if (meu === pedido) offset.value = null
      } finally {
        if (meu === pedido) {
          carregando.value = false
          aCarregarMais.value = false
        }
      }
    }

    function iniciar () {
      if (iniciado.value) return
      iniciado.value = true
      buscar(true)
    }

    function carregarMais () {
      if (!iniciado.value) return iniciar()
      buscar(false)
    }

    watch(() => JSON.stringify(props.params), () => {
      if (iniciado.value) buscar(true)
    })

    onMounted(() => {
      const el = raiz.value?.$el || raiz.value
      if (!props.lazy || typeof IntersectionObserver === 'undefined' || !el) return iniciar()
      observer = new IntersectionObserver(entries => {
        if (entries.some(e => e.isIntersecting)) {
          observer.disconnect()
          iniciar()
        }
      }, { rootMargin: '400px 0px' })
      observer.observe(el)
    })

    onUnmounted(() => observer?.disconnect())

    const estado = computed(() => ({
      itens: itens.value,
      total: total.value,
      carregando: !iniciado.value || carregando.value,
      aCarregarMais: aCarregarMais.value,
      temMais: iniciado.value && offset.value !== null && !carregando.value,
      iniciado: iniciado.value,
      carregarMais,
    }))

    return { raiz, estado }
  },
}
</script>
