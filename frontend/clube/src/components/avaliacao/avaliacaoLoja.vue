<template>
  <div class="space-y-6">

    <!-- Resumo -->
    <div v-if="avaliacoes.length > 0"
         class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 flex flex-col sm:flex-row items-center gap-6">

      <!-- Média -->
      <div class="text-center flex-shrink-0">
        <p class="text-5xl font-extrabold text-white">{{ mediaFormatada }}</p>
        <div class="flex gap-1 mt-2 justify-center">
          <svg v-for="n in 5" :key="n"
               :class="['h-5 w-5', n <= Math.round(media) ? 'text-yellow-400' : 'text-zinc-700']"
               fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
        <p class="text-xs text-zinc-500 mt-1">{{ total }} avaliação{{ total !== 1 ? 'ões' : '' }}</p>
      </div>

      <!-- Distribuição -->
      <div class="flex-1 w-full space-y-1.5">
        <div v-for="n in [5,4,3,2,1]" :key="n" class="flex items-center gap-2">
          <span class="text-xs text-zinc-500 w-3">{{ n }}</span>
          <svg class="h-3 w-3 text-yellow-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <div class="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div class="h-full bg-yellow-400 rounded-full transition-all"
                 :style="{ width: percentagem(n) + '%' }"></div>
          </div>
          <span class="text-xs text-zinc-600 w-6 text-right">{{ contagem[n] || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- Formulário criar/editar -->
    <div v-if="isLoggedIn" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
      <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
        Deixa a tua avaliação
        <span v-if="avaliacoesRestantes >= 0"
              class="ml-2 px-1.5 py-0.5 bg-zinc-700 text-zinc-400 text-[10px] rounded font-normal normal-case">
          {{ avaliacoesRestantes }} encomenda{{ avaliacoesRestantes !== 1 ? 's' : '' }} por avaliar
        </span>
      </h3>

      <!-- Sem encomenda concluída e não está a editar -->
      <div v-if="!podeAvaliar && !modoEdicao"
           class="text-center py-4 text-zinc-500 text-sm">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto mb-2 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
        Já avaliaste todas as tuas encomendas nesta loja.
      </div>

      <!-- Formulário — mostra se pode avaliar OU se está a editar -->
      <div v-if="podeAvaliar || modoEdicao">
        <!-- Estrelas interactivas -->
        <div class="flex gap-1 mb-4">
          <button v-for="n in 5" :key="n"
            @click="form.pontuacao = n"
            @mouseover="hoverStar = n"
            @mouseleave="hoverStar = 0"
            class="transition-transform hover:scale-110">
            <svg :class="['h-8 w-8 transition-colors',
                          n <= (hoverStar || form.pontuacao) ? 'text-yellow-400' : 'text-zinc-700']"
                 fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </button>
          <span class="ml-2 text-sm text-zinc-400 self-center">
            {{ labelPontuacao(hoverStar || form.pontuacao) }}
          </span>
        </div>

        <!-- Comentário -->
        <textarea v-model="form.comentario" rows="3"
          placeholder="Partilha a tua experiência com esta loja..."
          class="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                 placeholder-zinc-500 focus:outline-none focus:border-red-500 transition resize-none mb-3" />

        <!-- Erro -->
        <p v-if="erro" class="text-xs text-red-400 mb-3">{{ erro }}</p>

        <div class="flex gap-3">
          <button v-if="modoEdicao" @click="cancelarEdicao"
            class="px-4 py-2 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button v-if="modoEdicao" @click="apagarAvaliacao"
            :disabled="loadingApagar"
            class="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-semibold transition">
            Apagar
          </button>
          <button @click="submeter"
            :disabled="!form.pontuacao || loadingSubmeter"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                     !form.pontuacao || loadingSubmeter
                       ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                       : 'bg-red-600 hover:bg-red-500 text-white']">
            <svg v-if="loadingSubmeter" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
              <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
            </svg>
            {{ modoEdicao ? 'Guardar alterações' : 'Publicar avaliação' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Não autenticado -->
    <div v-else class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 text-center">
      <p class="text-sm text-zinc-500">
        <router-link to="/login" class="text-red-400 hover:text-red-300">Inicia sessão</router-link>
        para deixares a tua avaliação.
      </p>
    </div>

    <!-- Lista de avaliações -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 3" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <div v-else-if="avaliacoes.length === 0" class="text-center py-10 text-zinc-500 text-sm">
      Ainda sem avaliações. Sê o primeiro!
    </div>

    <div v-else class="space-y-3">
      <div v-for="av in avaliacoes" :key="av.id"
           :class="['bg-zinc-900 rounded-2xl border p-4 transition',
                    av.utilizador_username === user.username ? 'border-red-500/40' : 'border-zinc-800']">

        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <!-- Avatar -->
            <div class="w-9 h-9 rounded-full overflow-hidden flex-shrink-0">
              <img v-if="av.utilizador_foto" :src="fotoUrl(av.utilizador_foto)" :alt="av.utilizador_username"
                   class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-zinc-700 flex items-center justify-center text-sm font-bold text-zinc-300">
                {{ av.utilizador_username?.charAt(0)?.toUpperCase() || '?' }}
              </div>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-sm font-semibold text-zinc-200">{{ av.utilizador_username }}</span>
                <span v-if="av.utilizador_username === user.username"
                      class="px-1.5 py-0.5 bg-red-500/20 text-red-400 text-[10px] rounded font-bold">Tu</span>
              </div>
              <p class="text-[10px] text-zinc-600">{{ formatDate(av.data_criacao) }}</p>
            </div>
          </div>

          <div class="flex items-center gap-2 flex-shrink-0">
            <!-- Estrelas -->
            <div class="flex gap-0.5">
              <svg v-for="n in 5" :key="n"
                   :class="['h-3.5 w-3.5', n <= av.pontuacao ? 'text-yellow-400' : 'text-zinc-700']"
                   fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <!-- Editar (só a própria) -->
            <button v-if="av.utilizador_username === user.username" @click="editarAvaliacao(av)"
              class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>
        </div>

        <p v-if="av.comentario" class="text-sm text-zinc-400 leading-relaxed mt-3">{{ av.comentario }}</p>
      </div>

      <!-- Carregar mais -->
      <div v-if="temMais" class="text-center pt-2">
        <button @click="carregarMais" :disabled="loadingMais"
          class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-400 hover:text-zinc-200 transition disabled:opacity-50">
          {{ loadingMais ? 'A carregar...' : 'Ver mais avaliações' }}
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
      // formulário
      form:           { pontuacao: 0, comentario: '' },
      hoverStar:      0,
      erro:           '',
      loadingSubmeter: false,
      loadingApagar:   false,
      // encomendas concluídas
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
      return this.media ? this.media.toFixed(1) : '—'
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
      return ['', 'Péssimo', 'Fraco', 'Razoável', 'Bom', 'Excelente'][n] || ''
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

        // não detecta automaticamente — utilizador escolhe qual editar ao clicar
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
          // editar — PATCH
          const { data } = await api.patch(
            `/app/loja/${this.lojaId}/avaliacoes/${this.minhaAvaliacao.id}/editar/`,
            { pontuacao: this.form.pontuacao, comentario: this.form.comentario }
          )
          const idx = this.avaliacoes.findIndex(a => a.id === this.minhaAvaliacao.id)
          if (idx >= 0) {
            // normaliza a foto para o formato da lista (utilizador_foto)
            const normalizado = {
              ...this.avaliacoes[idx],
              pontuacao:  data.pontuacao,
              comentario: data.comentario,
            }
            this.avaliacoes.splice(idx, 1, normalizado)
          }
          this.minhaAvaliacao = null   // ← limpa para permitir criar novas
          this.modoEdicao     = false
        } else {
          // criar — POST
          const { data } = await api.post(`/app/loja/${this.lojaId}/avaliacoes/criar/`, {
            encomenda_id: this.encomendaId,
            pontuacao:    this.form.pontuacao,
            comentario:   this.form.comentario,
          })
          // normaliza para o formato da lista (AvaliacaoMiniSerializer)
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
        // verifica se ainda há encomendas por avaliar
        await this.verificarEncomenda()
        if (this.podeAvaliar) {
          this.form = { pontuacao: 0, comentario: '' }
        }
      } catch (e) {
        const msg = e.response?.data?.encomenda_id?.[0]
                 || e.response?.data?.encomenda?.[0]
                 || e.response?.data?.detail
                 || 'Erro ao publicar avaliação.'
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
      if (!confirm('Tens a certeza que queres apagar a tua avaliação?')) return
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