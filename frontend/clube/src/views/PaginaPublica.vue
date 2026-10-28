<!-- PaginaPublica.vue — páginas institucionais com endereço próprio (/termos, /privacidade, /devolucoes,
     /entregas, /contacto, /ajuda, /faq): links do rodapé e do checkout; a SISP pede estes URLs. -->
<template>
  <div class="min-h-screen flex flex-col" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-50 text-zinc-900'">
    <header class="border-b px-6 md:px-12 py-3 flex items-center justify-between gap-3"
            :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
      <router-link to="/" class="flex items-center gap-2" aria-label="Página inicial">
        <img :src="isDark ? logoLight : logoDefault" alt="Logo" class="h-12 w-12 object-contain" />
      </router-link>
      <button type="button" @click="isDark = !isDark" :aria-label="isDark ? 'Tema claro' : 'Tema escuro'"
        class="w-9 h-9 rounded-full flex items-center justify-center transition"
        :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-stone-100 hover:bg-stone-200 text-zinc-600'">
        <font-awesome-icon :icon="['fas', isDark ? 'sun' : 'moon']" class="w-4 h-4" />
      </button>
    </header>

    <main class="flex-1 w-full max-w-3xl mx-auto px-6 py-10" data-teste="pagina-publica">
      <div v-if="loading" class="space-y-3">
        <div class="h-8 w-1/2 rounded animate-pulse mb-6" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
        <div v-for="i in 6" :key="i" class="h-4 rounded animate-pulse"
             :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'" :style="{ width: (95 - i * 8) + '%' }"></div>
      </div>

      <p v-else-if="erro" class="text-center py-16" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
        {{ erro }}
        <router-link to="/" class="block mt-4 text-sm font-semibold text-red-500 hover:text-red-400">Voltar à página inicial</router-link>
      </p>

      <article v-else-if="pagina">
        <p class="text-[11px] font-bold uppercase tracking-[0.18em] text-red-500">{{ pagina.seccao === 'legal' ? 'Legal' : 'Suporte' }}</p>
        <h1 class="text-2xl md:text-3xl font-bold mt-1 mb-6">{{ pagina.titulo }}</h1>
        <PaginaConteudo :pagina="pagina" :isDark="isDark" />
        <p v-if="pagina.data_atualizacao" class="mt-10 text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
          Última actualização: {{ formatarData(pagina.data_atualizacao) }}
        </p>
      </article>
    </main>

    <SiteRodape :isDark="isDark" />
  </div>
</template>

<script>
import api from '@/services/api'
import PaginaConteudo from '@/components/paginas/PaginaConteudo.vue'
import SiteRodape from '@/components/paginas/SiteRodape.vue'
import logoDefault from '@/assets/img/login/logo_final_640.webp'
import logoLight from '@/assets/img/login/logo_final_640_light.webp'
import { temaEscuro, guardarTema } from '@/utils/tema'

export default {
  name: 'PaginaPublica',
  components: { PaginaConteudo, SiteRodape },

  data () {
    return { isDark: temaEscuro(), pagina: null, loading: true, erro: '', logoDefault, logoLight }
  },

  watch: {
    isDark (v) { guardarTema(v) },
    '$route.params.slug': { immediate: true, handler (s) { if (s) this.carregar(s) } },
  },

  methods: {
    async carregar (slug) {
      this.loading = true
      this.erro = ''
      try {
        const { data } = await api.get(`/app/paginas/${slug}/`)
        this.pagina = data
      } catch (e) {
        this.pagina = null
        this.erro = e.response?.status === 404
          ? 'Esta página não está disponível de momento.'
          : 'Não foi possível carregar o conteúdo. Tenta novamente.'
      } finally {
        this.loading = false
      }
    },

    formatarData (iso) {
      try {
        return new Date(iso).toLocaleDateString('pt-PT', { day: 'numeric', month: 'long', year: 'numeric' })
      } catch { return '' }
    },
  },
}
</script>
