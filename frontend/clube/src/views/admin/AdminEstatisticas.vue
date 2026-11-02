<!-- AdminEstatisticas.vue — Admin → Estatísticas (ver_stats): separadores Pesquisas e Publicidade.
     O separador vem do endereço (?aba=publicidade); /admin/pesquisas (endereço antigo) abre aqui. -->
<template>
  <div class="space-y-5" data-teste="admin-estatisticas">
    <div class="flex gap-1 border-b border-zinc-800" role="tablist">
      <button v-for="a in ABAS" :key="a.v" type="button" role="tab" :aria-selected="aba === a.v" @click="mudar(a.v)"
        :data-teste="'estat-aba-' + a.v"
        :class="['px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px transition flex items-center gap-2',
                 aba === a.v ? 'border-red-500 text-zinc-100' : 'border-transparent text-zinc-500 hover:text-zinc-300']">
        <font-awesome-icon :icon="['fas', a.icone]" class="text-xs" /> {{ a.n }}
      </button>
    </div>
    <AdminPesquisas v-if="aba === 'pesquisas'" />
    <AdminEstatPublicidade v-else />
  </div>
</template>

<script>
import { defineAsyncComponent } from 'vue'

const ABAS = [
  { v: 'pesquisas', n: 'Pesquisas', icone: 'magnifying-glass' },
  { v: 'publicidade', n: 'Publicidade', icone: 'rectangle-ad' },
]

export default {
  name: 'AdminEstatisticas',
  components: {
    AdminPesquisas: defineAsyncComponent(() => import('./AdminPesquisas.vue')),
    AdminEstatPublicidade: defineAsyncComponent(() => import('./AdminEstatPublicidade.vue')),
  },
  data () { return { ABAS } },
  computed: {
    aba () { return ABAS.some(a => a.v === this.$route.query.aba) ? this.$route.query.aba : 'pesquisas' },
  },
  methods: {
    mudar (v) {
      if (v === this.aba) return
      const query = { ...this.$route.query }
      if (v === 'pesquisas') delete query.aba
      else query.aba = v
      this.$router.replace({ query })
    },
  },
}
</script>
