<template>
  <div class="space-y-5">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs text-zinc-500">{{ total }} avaliaç{{ total !== 1 ? 'ões' : 'ão' }}</p>
      </div>
      <!-- Filtro estrelas -->
      <div class="flex gap-1">
        <button @click="filtroEstrelas = null; fetchAvaliacoes()"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition',
                   filtroEstrelas === null ? 'bg-zinc-200 text-zinc-900' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          Todas
        </button>
        <button v-for="n in [5,4,3,2,1]" :key="n"
          @click="filtroEstrelas = n; fetchAvaliacoes()"
          :class="['px-2.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1',
                   filtroEstrelas === n ? 'bg-yellow-500/20 text-yellow-400' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ n }}⭐
        </button>
      </div>
    </div>

    <!-- Resumo -->
    <div v-if="total > 0" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 flex items-center gap-6">
      <div class="text-center flex-shrink-0">
        <p class="text-4xl font-extrabold text-white">{{ mediaFormatada }}</p>
        <div class="flex gap-0.5 mt-1 justify-center">
          <svg v-for="n in 5" :key="n"
               :class="['h-4 w-4', n <= Math.round(media) ? 'text-yellow-400' : 'text-zinc-700']"
               fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
        <p class="text-xs text-zinc-500 mt-1">{{ total }} avaliações</p>
      </div>
      <div class="flex-1 space-y-1.5">
        <div v-for="n in [5,4,3,2,1]" :key="n" class="flex items-center gap-2">
          <span class="text-xs text-zinc-500 w-3">{{ n }}</span>
          <svg class="h-3 w-3 text-yellow-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <div class="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div class="h-full bg-yellow-400 rounded-full"
                 :style="{ width: percentagem(n) + '%' }"></div>
          </div>
          <span class="text-xs text-zinc-600 w-6 text-right">{{ contagem[n] || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 5" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Vazio -->
    <div v-else-if="avaliacoes.length === 0"
         class="text-center py-16 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
      Sem avaliações {{ filtroEstrelas ? `de ${filtroEstrelas} estrela${filtroEstrelas !== 1 ? 's' : ''}` : '' }}.
    </div>

    <!-- Lista -->
    <div v-else class="space-y-3">
      <div v-for="av in avaliacoes" :key="av.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">

        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-full overflow-hidden flex-shrink-0">
              <img v-if="av.utilizador_foto" :src="av.utilizador_foto" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-zinc-700 flex items-center justify-center text-sm font-bold text-zinc-300">
                {{ av.utilizador_username?.charAt(0)?.toUpperCase() || '?' }}
              </div>
            </div>
            <div>
              <p class="text-sm font-semibold text-zinc-200">{{ av.utilizador_username }}</p>
              <p class="text-[10px] text-zinc-600">{{ formatDate(av.data_criacao) }}</p>
            </div>
          </div>

          <div class="flex items-center gap-3 flex-shrink-0">
            <!-- Estrelas -->
            <div class="flex gap-0.5">
              <svg v-for="n in 5" :key="n"
                   :class="['h-4 w-4', n <= av.pontuacao ? 'text-yellow-400' : 'text-zinc-700']"
                   fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <!-- Ocultar -->
            <button @click="ocultarAvaliacao(av)"
              :class="['px-2.5 py-1 rounded-lg text-xs font-semibold transition',
                       av.oculta
                         ? 'bg-zinc-700 text-zinc-400 hover:bg-zinc-600'
                         : 'bg-red-500/10 hover:bg-red-500/20 text-red-400']">
              {{ av.oculta ? '👁 Mostrar' : '🚫 Ocultar' }}
            </button>
          </div>
        </div>

        <p v-if="av.comentario" class="text-sm text-zinc-400 leading-relaxed mt-3">{{ av.comentario }}</p>
        <p v-if="av.oculta" class="text-xs text-red-500/70 mt-2 italic">Esta avaliação está oculta ao público.</p>
      </div>
    </div>

    <!-- Paginação -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
      <p class="text-xs text-zinc-500">
        {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, total) }} de {{ total }}
      </p>
      <div class="flex gap-2">
        <button @click="irParaPagina(page - 1)" :disabled="page <= 1"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button v-for="p in paginasVisiveis" :key="p" @click="irParaPagina(p)"
          :class="['w-8 h-8 rounded-lg text-xs font-bold transition',
                   p === page ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700']">
          {{ p }}
        </button>
        <button @click="irParaPagina(page + 1)" :disabled="page >= totalPages"
          class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition disabled:opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'BackofficeAvaliacoes',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading:        false,
      avaliacoes:     [],
      total:          0,
      page:           1,
      limit:          10,
      filtroEstrelas: null,
    }
  },

  computed: {
    totalPages () { return Math.ceil(this.total / this.limit) },
    paginasVisiveis () {
      const start = Math.max(1, this.page - 2)
      const end   = Math.min(this.totalPages, this.page + 2)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    },
    media () {
      if (!this.avaliacoes.length) return 0
      return this.avaliacoes.reduce((s, a) => s + a.pontuacao, 0) / this.avaliacoes.length
    },
    mediaFormatada () { return this.media ? this.media.toFixed(1) : '—' },
    contagem () {
      const c = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
      this.avaliacoes.forEach(a => { c[a.pontuacao] = (c[a.pontuacao] || 0) + 1 })
      return c
    },
  },

  async created () { await this.fetchAvaliacoes() },

  methods: {
    formatDate (d) { return new Date(d).toLocaleDateString('pt-PT') },

    percentagem (n) {
      if (!this.total) return 0
      return Math.round(((this.contagem[n] || 0) / this.total) * 100)
    },

    irParaPagina (p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.fetchAvaliacoes()
    },

    async fetchAvaliacoes () {
      this.loading = true
      try {
        const params = { offset: (this.page - 1) * this.limit, limit: this.limit }
        if (this.filtroEstrelas) params.pontuacao = this.filtroEstrelas
        const { data } = await api.get(`/app/loja/${this.lojaId}/avaliacoes/`, {
          params: { ...params, incluir_ocultas: 'true' }
        })
        this.avaliacoes = data.results || data
        this.total      = data.count ?? this.avaliacoes.length
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async ocultarAvaliacao (av) {
      try {
        await api.patch(`/app/loja/${this.lojaId}/avaliacoes/${av.id}/ocultar/`)
        av.oculta = !av.oculta
      } catch (e) { console.error(e) }
    },
  },
}
</script>