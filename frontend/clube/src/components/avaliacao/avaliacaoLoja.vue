<template>
  <div :class="['space-y-6', containerClass]">

    <!-- Resumo -->
    <div v-if="avaliacoes.length > 0"
         :class="[
           'p-6 flex flex-col sm:flex-row items-center gap-6',
           summaryBorderRadius,
           summaryClass,
           isDark ? 'bg-zinc-900 border border-zinc-800' : 'bg-white border border-gray-200 shadow-sm'
         ]">

      <!-- Media -->
      <div class="text-center flex-shrink-0">
        <p :class="['text-5xl font-extrabold', isDark ? 'text-white' : 'text-zinc-900', averageClass]">{{ mediaFormatada }}</p>
        <div class="flex gap-1 mt-2 justify-center">
          <svg v-for="n in 5" :key="n"
               :class="['h-5 w-5', n <= Math.round(media) ? starActiveClass : starInactiveClass]"
               fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
        <p :class="['text-xs mt-1', isDark ? 'text-zinc-500' : 'text-zinc-400']">{{ total }} avaliacao{{ total !== 1 ? 'es' : '' }}</p>
      </div>

      <!-- Distribuicao -->
      <div class="flex-1 w-full space-y-1.5">
        <div v-for="n in [5,4,3,2,1]" :key="n" class="flex items-center gap-2">
          <span :class="['text-xs w-3', isDark ? 'text-zinc-500' : 'text-zinc-400']">{{ n }}</span>
          <svg :class="['h-3 w-3 flex-shrink-0', starActiveClass]" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <div :class="['flex-1 h-1.5 rounded-full overflow-hidden', isDark ? 'bg-zinc-800' : 'bg-gray-200']">
            <div :class="['h-full rounded-full transition-all', progressBarClass]"
                 :style="{ width: percentagem(n) + '%' }"></div>
          </div>
          <span :class="['text-xs w-6 text-right', isDark ? 'text-zinc-600' : 'text-zinc-400']">{{ contagem[n] || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- Formulario criar/editar -->
    <div v-if="isLoggedIn" :class="[
      'p-5',
      formBorderRadius,
      formClass,
      isDark ? 'bg-zinc-900 border border-zinc-800' : 'bg-white border border-gray-200 shadow-sm'
    ]">
      <h3 :class="['text-sm font-bold uppercase tracking-wider mb-4', isDark ? 'text-zinc-400' : 'text-zinc-500']">
        Deixa a tua avaliacao
        <span v-if="avaliacoesRestantes >= 0"
              :class="['ml-2 px-1.5 py-0.5 text-[10px] rounded font-normal normal-case', remainingBadgeClass]">
          {{ avaliacoesRestantes }} encomenda{{ avaliacoesRestantes !== 1 ? 's' : '' }} por avaliar
        </span>
      </h3>

      <!-- Sem encomenda concluida e nao esta a editar -->
      <div v-if="!podeAvaliar && !modoEdicao"
           :class="['text-center py-4 text-sm', isDark ? 'text-zinc-500' : 'text-zinc-400']">
        <svg xmlns="http://www.w3.org/2000/svg" :class="['h-8 w-8 mx-auto mb-2', isDark ? 'text-zinc-700' : 'text-gray-300']" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
        Ja avaliaste todas as tuas encomendas nesta loja.
      </div>

      <!-- Formulario — mostra se pode avaliar OU se esta a editar -->
      <div v-if="podeAvaliar || modoEdicao">
        <!-- Estrelas interactivas -->
        <div class="flex gap-1 mb-4">
          <button v-for="n in 5" :key="n"
            @click="form.pontuacao = n"
            @mouseover="hoverStar = n"
            @mouseleave="hoverStar = 0"
            class="transition-transform hover:scale-110">
            <svg :class="['h-8 w-8 transition-colors',
                          n <= (hoverStar || form.pontuacao) ? starActiveClass : starInactiveClass]"
                 fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </button>
          <span :class="['ml-2 text-sm self-center', isDark ? 'text-zinc-400' : 'text-zinc-500']">
            {{ labelPontuacao(hoverStar || form.pontuacao) }}
          </span>
        </div>

        <!-- Comentario -->
        <textarea v-model="form.comentario" rows="3"
          placeholder="Partilha a tua experiencia com esta loja..."
          :class="[
            'w-full px-4 py-3 text-sm resize-none mb-3 transition',
            textareaBorderRadius,
            inputFocusClass,
            isDark 
              ? 'bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder-zinc-500' 
              : 'bg-gray-50 border border-gray-300 text-zinc-900 placeholder-zinc-400'
          ]" />

        <!-- Erro -->
        <p v-if="erro" :class="['text-xs mb-3', errorClass]">{{ erro }}</p>

        <div class="flex gap-3">
          <button v-if="modoEdicao" @click="cancelarEdicao"
            :class="[
              'px-4 py-2 text-sm font-semibold transition',
              buttonBorderRadius,
              isDark ? 'border border-zinc-700 text-zinc-400 hover:text-zinc-200' : 'border border-gray-300 text-zinc-600 hover:text-zinc-900'
            ]">
            Cancelar
          </button>
          <button v-if="modoEdicao" @click="apagarAvaliacao"
            :disabled="loadingApagar"
            :class="['px-4 py-2 text-sm font-semibold transition', buttonBorderRadius, deleteButtonClass]">
            Apagar
          </button>
          <button @click="submeter"
            :disabled="!form.pontuacao || loadingSubmeter"
            :class="[
              'px-4 py-2.5 text-sm font-bold transition flex items-center justify-center gap-2',
              buttonBorderRadius,
              !form.pontuacao || loadingSubmeter
                ? disabledButtonClass
                : submitButtonClass.includes('editorial') 
                  ? 'avaliacao-btn-primary w-full justify-center'
                  : submitButtonClass
            ]">
            <svg v-if="loadingSubmeter" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ modoEdicao ? 'Guardar alteracoes' : 'Publicar avaliacao' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Nao autenticado -->
    <div v-else :class="[
      'p-5 text-center',
      formBorderRadius,
      isDark ? 'bg-zinc-900 border border-zinc-800' : 'bg-white border border-gray-200 shadow-sm'
    ]">
      <p :class="['text-sm', isDark ? 'text-zinc-500' : 'text-zinc-400']">
        <router-link to="/login" :class="linkClass">Inicia sessao</router-link>
        para deixares a tua avaliacao.
      </p>
    </div>

    <!-- Lista de avaliacoes -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 3" :key="n" :class="['h-20 animate-pulse', skeletonClass, isDark ? 'bg-zinc-900' : 'bg-gray-200']"></div>
    </div>

    <div v-else-if="avaliacoes.length === 0" :class="['text-center py-10 text-sm', isDark ? 'text-zinc-500' : 'text-zinc-400']">
      Ainda sem avaliacoes. Se o primeiro!
    </div>

    <div v-else class="space-y-3">
      <div v-for="av in avaliacoes" :key="av.id"
           :class="[
             'p-4 transition',
             reviewCardBorderRadius,
             reviewCardClass,
             av.utilizador_username === user.username 
               ? ownReviewBorderClass 
               : isDark ? 'bg-zinc-900 border border-zinc-800' : 'bg-white border border-gray-200 shadow-sm'
           ]">

        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <!-- Avatar -->
            <div :class="['w-9 h-9 rounded-full overflow-hidden flex-shrink-0', avatarClass]">
              <img v-if="av.utilizador_foto" :src="fotoUrl(av.utilizador_foto)" :alt="av.utilizador_username"
                   class="w-full h-full object-cover" />
              <div v-else :class="['w-full h-full flex items-center justify-center text-sm font-bold', avatarPlaceholderClass]">
                {{ av.utilizador_username?.charAt(0)?.toUpperCase() || '?' }}
              </div>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span :class="['text-sm font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800']">{{ av.utilizador_username }}</span>
                <span v-if="av.utilizador_username === user.username"
                      :class="['px-1.5 py-0.5 text-[10px] rounded font-bold', ownBadgeClass]">Tu</span>
              </div>
              <p :class="['text-[10px]', isDark ? 'text-zinc-600' : 'text-zinc-400']">{{ formatDate(av.data_criacao) }}</p>
            </div>
          </div>

          <div class="flex items-center gap-2 flex-shrink-0">
            <!-- Estrelas -->
            <div class="flex gap-0.5">
              <svg v-for="n in 5" :key="n"
                   :class="['h-3.5 w-3.5', n <= av.pontuacao ? starActiveClass : starInactiveClass]"
                   fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <!-- Editar (so a propria) -->
            <button v-if="av.utilizador_username === user.username" @click="editarAvaliacao(av)"
              :class="['w-7 h-7 rounded-lg flex items-center justify-center transition', editButtonClass]">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" :class="editIconClass" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>
        </div>

        <p v-if="av.comentario" :class="['text-sm leading-relaxed mt-3', isDark ? 'text-zinc-400' : 'text-zinc-600']">{{ av.comentario }}</p>
      </div>

      <!-- Carregar mais -->
      <div v-if="temMais" class="text-center pt-2">
        <button @click="carregarMais" :disabled="loadingMais"
          :class="['px-4 py-2 text-xs transition disabled:opacity-50', loadMoreButtonClass]">
          {{ loadingMais ? 'A carregar...' : 'Ver mais avaliacoes' }}
        </button>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AvaliacaoLoja',
  props: {
    lojaId: { type: [String, Number], required: true },
    isDark: { type: Boolean, default: true },
    
    // Container
    containerClass: { type: String, default: '' },
    
    // Summary section
    summaryClass:        { type: String, default: '' },
    summaryBorderRadius: { type: String, default: 'rounded-2xl' },
    averageClass:        { type: String, default: '' },
    progressBarClass:    { type: String, default: 'bg-yellow-400' },
    
    // Stars
    starActiveClass:   { type: String, default: 'text-yellow-400' },
    starInactiveClass: { type: String, default: 'text-zinc-700' },
    
    // Form section
    formClass:           { type: String, default: '' },
    formBorderRadius:    { type: String, default: 'rounded-2xl' },
    textareaBorderRadius:{ type: String, default: 'rounded-xl' },
    buttonBorderRadius:  { type: String, default: 'rounded-xl' },
    inputFocusClass:     { type: String, default: 'focus:outline-none focus:border-red-500' },
    remainingBadgeClass: { type: String, default: 'bg-zinc-700 text-zinc-400' },
    
    // Buttons
    submitButtonClass:   { type: String, default: 'bg-red-600 hover:bg-red-500 text-white disabled:bg-zinc-700 disabled:text-zinc-500 disabled:cursor-not-allowed' },
    disabledButtonClass: { type: String, default: 'bg-zinc-700 text-zinc-500 cursor-not-allowed' },
    deleteButtonClass:   { type: String, default: 'bg-red-500/10 hover:bg-red-500/20 text-red-400' },
    loadMoreButtonClass: { type: String, default: 'rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200' },
    
    // Review cards
    reviewCardClass:        { type: String, default: '' },
    reviewCardBorderRadius: { type: String, default: 'rounded-2xl' },
    ownReviewBorderClass:   { type: String, default: 'bg-zinc-900 border border-red-500/40' },
    ownBadgeClass:          { type: String, default: 'bg-red-500/20 text-red-400' },
    
    // Avatar
    avatarClass:           { type: String, default: '' },
    avatarPlaceholderClass:{ type: String, default: 'bg-zinc-700 text-zinc-300' },
    
    // Actions
    editButtonClass: { type: String, default: 'bg-zinc-800 hover:bg-zinc-700' },
    editIconClass:   { type: String, default: 'text-zinc-400' },
    
    // Other
    linkClass:     { type: String, default: 'text-red-400 hover:text-red-300' },
    errorClass:    { type: String, default: 'text-red-400' },
    skeletonClass: { type: String, default: 'rounded-2xl' },
  },
  emits: ['rating-updated'],

  data () {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      user,
      avaliacoes:    [],
      loading:       false,
      total:         0,
      offset:        0,
      limit:         10,
      temMais:       false,
      loadingMais:   false,
      form:           { pontuacao: 0, comentario: '' },
      hoverStar:      0,
      erro:           '',
      loadingSubmeter: false,
      loadingApagar:   false,
      encomendaId:          null,
      podeAvaliar:          false,
      avaliacoesRestantes:  0,
      minhaAvaliacao:       null,
      modoEdicao:           false,
    }
  },

  computed: {
    isLoggedIn () { return !!this.user?.id },

    media () {
      if (!this.avaliacoes.length) return 0
      return this.avaliacoes.reduce((s, a) => s + a.pontuacao, 0) / this.avaliacoes.length
    },

    mediaFormatada () {
      return this.media ? parseFloat(this.media.toFixed(1)) : '—'
    },

    contagem () {
      const c = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
      this.avaliacoes.forEach(a => { c[a.pontuacao] = (c[a.pontuacao] || 0) + 1 })
      return c
    },
  },

  async created () {
    await Promise.all([
      this.fetchAvaliacoes(),
      this.isLoggedIn ? this.verificarEncomenda() : Promise.resolve(),
    ])
  },

  methods: {
    formatDate (d) { return new Date(d).toLocaleDateString('pt-PT') },

    percentagem (n) {
      if (!this.total) return 0
      return Math.round(((this.contagem[n] || 0) / this.total) * 100)
    },

    labelPontuacao (n) {
      return ['', 'Pessimo', 'Fraco', 'Razoavel', 'Bom', 'Excelente'][n] || ''
    },

    async fetchAvaliacoes (append = false) {
      this.loading = !append
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/avaliacoes/`, {
          params: { offset: this.offset, limit: this.limit }
        })
        const results = data.results || data
        if (append) this.avaliacoes.push(...results)
        else this.avaliacoes = results
        this.total   = data.count ?? results.length
        this.temMais = !!data.next_offset
        this.offset  = data.next_offset ?? 0
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async carregarMais () {
      this.loadingMais = true
      await this.fetchAvaliacoes(true)
      this.loadingMais = false
    },

    async verificarEncomenda () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/avaliacoes/pode-avaliar/`)
        this.podeAvaliar         = data.pode_avaliar
        this.encomendaId         = data.encomenda_id
        this.avaliacoesRestantes = data.avaliacoes_restantes ?? 0
      } catch (e) { console.error(e) }
    },

    async submeter () {
      if (!this.form.pontuacao) return
      this.loadingSubmeter = true
      this.erro = ''
      try {
        if (this.minhaAvaliacao) {
          const { data } = await api.patch(
            `/app/loja/${this.lojaId}/avaliacoes/${this.minhaAvaliacao.id}/editar/`,
            { pontuacao: this.form.pontuacao, comentario: this.form.comentario }
          )
          const idx = this.avaliacoes.findIndex(a => a.id === this.minhaAvaliacao.id)
          if (idx >= 0) {
            const normalizado = {
              ...this.avaliacoes[idx],
              pontuacao:  data.pontuacao,
              comentario: data.comentario,
            }
            this.avaliacoes.splice(idx, 1, normalizado)
          }
          this.minhaAvaliacao = null
          this.modoEdicao     = false
        } else {
          const { data } = await api.post(`/app/loja/${this.lojaId}/avaliacoes/criar/`, {
            encomenda_id: this.encomendaId,
            pontuacao:    this.form.pontuacao,
            comentario:   this.form.comentario,
          })
          const novaAvaliacao = {
            id:                  data.id,
            utilizador_username: data.utilizador?.username || this.user.username,
            utilizador_foto:     data.utilizador?.foto_url || null,
            pontuacao:           data.pontuacao,
            comentario:          data.comentario,
            data_criacao:        data.data_criacao,
          }
          this.avaliacoes.unshift(novaAvaliacao)
          this.minhaAvaliacao = null
          this.total++
        }
        this.$emit('rating-updated', { media: this.media })
        await this.verificarEncomenda()
        if (this.podeAvaliar) {
          this.form = { pontuacao: 0, comentario: '' }
        }
      } catch (e) {
        const msg = e.response?.data?.encomenda_id?.[0]
                 || e.response?.data?.encomenda?.[0]
                 || e.response?.data?.detail
                 || 'Erro ao publicar avaliacao.'
        this.erro = msg
      } finally { this.loadingSubmeter = false }
    },

    editarAvaliacao (av) {
      this.modoEdicao      = true
      this.minhaAvaliacao  = av
      this.form.pontuacao  = av.pontuacao
      this.form.comentario = av.comentario
    },

    fotoUrl (url) {
      if (!url) return null
      if (url.startsWith('http')) return url
      const base = process.env.VUE_APP_URL_BASE || 'http://localhost:8000'
      return base + url
    },

    cancelarEdicao () {
      this.modoEdicao     = false
      this.minhaAvaliacao = null
      this.form = { pontuacao: 0, comentario: '' }
    },

    async apagarAvaliacao () {
      if (!confirm('Tens a certeza que queres apagar a tua avaliacao?')) return
      this.loadingApagar = true
      try {
        await api.delete(`/app/loja/${this.lojaId}/avaliacoes/${this.minhaAvaliacao.id}/apagar/`)
        this.avaliacoes = this.avaliacoes.filter(a => a.id !== this.minhaAvaliacao.id)
        this.minhaAvaliacao = null
        this.form = { pontuacao: 0, comentario: '' }
        this.total--
        this.$emit('rating-updated', { media: this.media })
        this.modoEdicao = false
        await this.verificarEncomenda()
      } catch (e) { console.error(e) }
      finally { this.loadingApagar = false }
    },
  },
}
</script>

<style>
/* Button styling that uses accent color from parent editorial context */
.avaliacao-btn-primary {
  background: var(--accent, #c8ff00);
  color: var(--bg, #0a0a0a);
  font-weight: 800;
  text-transform: uppercase;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}

.avaliacao-btn-primary:hover:not(:disabled) {
  opacity: 0.88;
}

.avaliacao-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
