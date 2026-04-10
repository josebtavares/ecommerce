<template>
  <div class="space-y-6">

    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Categorias em destaque</h2>
        <p class="text-xs text-zinc-500 mt-0.5">
          Escolhe quais as categorias de produtos que aparecem na página principal
        </p>
      </div>
      <button @click="abrirCriar"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nova categoria
      </button>
    </div>

    <!-- Sugestões de categorias existentes na BD -->
    <div v-if="sugestoesBD.length > 0"
         class="bg-zinc-900/50 rounded-2xl border border-zinc-800 border-dashed p-4">
      <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">
        Categorias existentes nos produtos — clica para adicionar
      </p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="s in sugestoesBD" :key="s"
          @click="abrirCriarComNome(s)"
          :class="[
            'px-3 py-1.5 rounded-full text-xs font-semibold transition capitalize',
            categoriaJaExiste(s)
              ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
              : 'bg-zinc-800 text-zinc-300 hover:bg-red-600/20 hover:text-red-400 border border-zinc-700 hover:border-red-500/50'
          ]"
          :disabled="categoriaJaExiste(s)">
          {{ s }}
          <span v-if="categoriaJaExiste(s)" class="ml-1 opacity-50">✓</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista -->
    <div v-else-if="categorias.length > 0" class="space-y-2">
      <!-- Drag hint -->
      <p class="text-xs text-zinc-600 flex items-center gap-1.5 mb-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Altera o campo "Ordem" para controlar a sequência no home
      </p>

      <div v-for="cat in categorias" :key="cat.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4 group">

        <!-- Ícone + info -->
        <div class="text-2xl flex-shrink-0">{{ cat.icone }}</div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="text-sm font-bold text-zinc-200 capitalize">{{ cat.nome }}</p>
            <span v-if="!cat.ativo"
                  class="px-1.5 py-0.5 bg-zinc-700 text-zinc-500 text-[10px] rounded font-medium">
              Inactiva
            </span>
          </div>
          <p class="text-xs text-zinc-500 mt-0.5">
            Ordem: {{ cat.ordem }}
            <span v-if="cat.total_produtos !== undefined" class="ml-2">
              · {{ cat.total_produtos }} produto{{ cat.total_produtos !== 1 ? 's' : '' }}
            </span>
          </p>
        </div>

        <!-- Acções -->
        <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
          <!-- Toggle ativo/inativo -->
          <button @click="toggleAtivo(cat)"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-semibold transition',
              cat.ativo
                ? 'bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500'
                : 'bg-green-500/10 hover:bg-green-500/20 text-green-500'
            ]"
            :title="cat.ativo ? 'Desactivar' : 'Activar'">
            {{ cat.ativo ? 'Desactivar' : 'Activar' }}
          </button>

          <!-- Editar -->
          <button @click="abrirEditar(cat)"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition"
            title="Editar">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>

          <!-- Eliminar -->
          <button @click="eliminar(cat)"
            class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition"
            title="Eliminar definitivamente">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Vazio -->
    <div v-else-if="!loading"
         class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800 border-dashed">
      Ainda não adicionaste nenhuma categoria de destaque.
      <button @click="abrirCriar" class="text-red-400 hover:text-red-300 ml-1">Criar agora →</button>
    </div>

    <!-- ═══ MODAL CRIAR/EDITAR ═══ -->
    <div v-if="showModal"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="fecharModal">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-md shadow-2xl">

        <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <h3 class="text-base font-bold text-zinc-100">
            {{ editando ? 'Editar categoria' : 'Nova categoria de destaque' }}
          </h3>
          <button @click="fecharModal"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-4">
          <!-- Nome -->
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">
              Nome * <span class="text-zinc-600">(deve corresponder ao campo categoria dos produtos)</span>
            </label>
            <input v-model="form.nome" type="text"
              placeholder="ex: menu, conjunto, sobremesa..."
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
            <!-- preview normalizado -->
            <p v-if="form.nome" class="text-[10px] text-zinc-600 mt-1">
              Guardado como: <span class="text-zinc-400 font-mono">{{ form.nome.toLowerCase().trim() }}</span>
            </p>
          </div>

          <!-- Ícone -->
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Ícone (emoji)</label>
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center text-2xl flex-shrink-0">
                {{ form.icone || '📂' }}
              </div>
              <input v-model="form.icone" type="text" maxlength="4"
                placeholder="📂"
                class="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition" />
            </div>
            <!-- Sugestões rápidas de emojis -->
            <div class="flex flex-wrap gap-1.5 mt-2">
              <button v-for="emoji in emojisSugeridos" :key="emoji"
                @click="form.icone = emoji"
                class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition text-lg">
                {{ emoji }}
              </button>
            </div>
          </div>

          <!-- Ordem -->
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Ordem no home</label>
            <input v-model.number="form.ordem" type="number" min="0"
              placeholder="0"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
            <p class="text-[10px] text-zinc-600 mt-1">0 = primeiro, números maiores = mais abaixo</p>
          </div>

          <!-- Erro -->
          <div v-if="erroModal"
               class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">
            {{ erroModal }}
          </div>

          <!-- Acções -->
          <div class="flex gap-3 pt-2 border-t border-zinc-800">
            <button @click="fecharModal"
              class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
              Cancelar
            </button>
            <button @click="guardar" :disabled="loadingSave || !form.nome.trim()"
              :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                       loadingSave || !form.nome.trim()
                         ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                         : 'bg-red-600 hover:bg-red-500 text-white']">
              <svg v-if="loadingSave" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              {{ editando ? 'Guardar' : 'Criar' }}
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AdminCategoriasDestaque',

  data () {
    return {
      loading: false,
      loadingSave: false,
      categorias: [],
      sugestoesBD: [],
      showModal: false,
      editando: null,
      erroModal: '',
      form: { nome: '', icone: '📂', ordem: 0 },
      emojisSugeridos: [
        '🍔', '🍽️', '🥤', '🍰', '👗', '👟', '💻', '📱',
        '📚', '📖', '🛒', '💊', '🏠', '⚽', '💄', '🎮',
        '📂', '🏷️', '✨', '🎁',
      ],
    }
  },

  async created () {
    await Promise.all([this.fetchCategorias(), this.fetchSugestoes()])
  },

  methods: {
    categoriaJaExiste (nome) {
      return this.categorias.some(c => c.nome === nome.toLowerCase().trim())
    },

    async fetchCategorias () {
      this.loading = true
      try {
        const { data } = await api.get('/app/admin/categorias-destaque/')
        this.categorias = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    async fetchSugestoes () {
      try {
        // busca todas as categorias existentes na BD de produtos
        const { data } = await api.get('/app/produto/categorias/?min_produtos=1&limit=50')
        this.sugestoesBD = data.map(c => c.categoria)
      } catch (e) { console.error(e) }
    },

    abrirCriar () {
      this.editando = null
      this.erroModal = ''
      this.form = { nome: '', icone: '📂', ordem: this.categorias.length }
      this.showModal = true
    },

    abrirCriarComNome (nome) {
      this.abrirCriar()
      this.form.nome = nome
    },

    abrirEditar (cat) {
      this.editando = cat
      this.erroModal = ''
      this.form = { nome: cat.nome, icone: cat.icone, ordem: cat.ordem }
      this.showModal = true
    },

    fecharModal () {
      this.showModal = false
      this.editando = null
      this.erroModal = ''
    },

    async guardar () {
      if (!this.form.nome.trim()) return
      this.loadingSave = true
      this.erroModal = ''
      try {
        if (this.editando) {
          await api.patch(`/app/admin/categorias-destaque/${this.editando.id}/`, this.form)
        } else {
          await api.post('/app/admin/categorias-destaque/criar/', this.form)
        }
        this.fecharModal()
        await this.fetchCategorias()
      } catch (e) {
        this.erroModal = e.response?.data?.nome
          || e.response?.data?.detail
          || 'Erro ao guardar.'
      } finally {
        this.loadingSave = false
      }
    },

    async toggleAtivo (cat) {
      try {
        const { data } = await api.patch(`/app/admin/categorias-destaque/${cat.id}/toggle/`)
        cat.ativo = data.ativo
      } catch (e) { console.error(e) }
    },

    async eliminar (cat) {
      if (!confirm(`Eliminar a categoria "${cat.nome}"?\nIsso não afecta os produtos — apenas remove o destaque do home.`)) return
      try {
        await api.delete(`/app/admin/categorias-destaque/${cat.id}/`)
        await this.fetchCategorias()
      } catch (e) { console.error(e) }
    },
  }
}
</script>