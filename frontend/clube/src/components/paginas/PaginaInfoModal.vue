<!-- PaginaInfoModal.vue — popup das páginas institucionais (Ajuda, Contacto, FAQ, Termos, Privacidade, …)
     Uso:
       <PaginaInfoModal :slug="paginaAberta" :isDark="isDark" @close="paginaAberta = null" />
     ou, para pré-visualizar sem pedir à API (admin):
       <PaginaInfoModal :pagina="{ slug, titulo, conteudo, dados }" ... />
-->
<template>
  <Teleport to="body">
    <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                leave-active-class="transition duration-150" leave-to-class="opacity-0">
      <div v-if="aberto"
           class="fixed inset-0 z-[300] flex items-end sm:items-center justify-center sm:p-4 bg-black/60 backdrop-blur-sm"
           @click.self="$emit('close')">

        <div class="pim-painel w-full sm:max-w-2xl max-h-[88vh] sm:max-h-[85vh] flex flex-col overflow-hidden
                    rounded-t-3xl sm:rounded-3xl border shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100' : 'bg-white border-stone-200 text-zinc-900'"
             role="dialog" aria-modal="true" :aria-label="dados?.titulo">

          <!-- Cabeçalho -->
          <div class="flex items-center justify-between gap-3 px-5 sm:px-7 py-4 border-b flex-shrink-0"
               :class="isDark ? 'border-zinc-800' : 'border-stone-200'">
            <div class="min-w-0">
              <p class="text-[10px] font-bold uppercase tracking-[0.18em] text-red-500">
                {{ dados?.seccao === 'legal' ? 'Legal' : 'Suporte' }}
              </p>
              <h2 class="text-lg sm:text-xl font-bold truncate">{{ dados?.titulo || '…' }}</h2>
            </div>
            <button @click="$emit('close')" aria-label="Fechar"
              class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-stone-100 hover:bg-stone-200 text-zinc-600'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Corpo -->
          <div class="flex-1 overflow-y-auto px-5 sm:px-7 py-5 sm:py-6">
            <div v-if="loading" class="space-y-3">
              <div v-for="i in 5" :key="i" class="h-4 rounded animate-pulse"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'" :style="{ width: (95 - i * 9) + '%' }"></div>
            </div>

            <p v-else-if="erro" class="text-sm text-center py-8" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              {{ erro }}
            </p>

            <template v-else-if="dados">
              <PaginaConteudo :pagina="dados" :isDark="isDark" />
            </template>
          </div>

          <!-- Rodapé -->
          <div v-if="dados?.data_atualizacao && !loading"
               class="px-5 sm:px-7 py-3 border-t text-[11px] flex-shrink-0"
               :class="isDark ? 'border-zinc-800 text-zinc-500' : 'border-stone-200 text-zinc-400'">
            Última actualização: {{ formatarData(dados.data_atualizacao) }}
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script>
import api from '@/services/api'
import PaginaConteudo from './PaginaConteudo.vue'

export default {
  name: 'PaginaInfoModal',
  components: { PaginaConteudo },

  props: {
    slug:   { type: String, default: null },   // carrega da API
    pagina: { type: Object, default: null },   // ou recebe o conteúdo directamente (preview)
    isDark: { type: Boolean, default: true },
  },

  emits: ['close'],

  data () {
    return { carregada: null, loading: false, erro: '' }
  },

  computed: {
    aberto () { return !!(this.slug || this.pagina) },
    dados ()  { return this.pagina || this.carregada },
  },

  watch: {
    slug: { immediate: true, handler (s) { if (s) this.carregar(s) } },
    aberto (v) {
      document.body.style.overflow = v ? 'hidden' : ''
      if (v) window.addEventListener('keydown', this.onTecla)
      else   window.removeEventListener('keydown', this.onTecla)
    },
  },

  mounted () {
    if (this.aberto) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', this.onTecla)
    }
  },

  beforeUnmount () {
    document.body.style.overflow = ''
    window.removeEventListener('keydown', this.onTecla)
  },

  methods: {
    async carregar (slug) {
      this.loading = true
      this.erro = ''
      this.carregada = null
      try {
        const { data } = await api.get(`/app/paginas/${slug}/`)
        this.carregada = data
      } catch (e) {
        this.erro = e.response?.status === 404
          ? 'Esta página não está disponível de momento.'
          : 'Não foi possível carregar o conteúdo. Tenta novamente.'
      } finally {
        this.loading = false
      }
    },

    onTecla (e) {
      if (e.key === 'Escape') this.$emit('close')
    },

    formatarData (iso) {
      try {
        return new Date(iso).toLocaleDateString('pt-PT', { day: 'numeric', month: 'long', year: 'numeric' })
      } catch { return '' }
    },
  },
}
</script>

<style scoped>
.pim-painel { animation: pimIn .22s cubic-bezier(.2,.8,.2,1); }
@keyframes pimIn { from { opacity: 0; transform: translateY(16px); } }
</style>
