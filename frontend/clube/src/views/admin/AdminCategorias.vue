<template>
  <div class="space-y-5 ">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Categorias de loja</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Visíveis no formulário de criar loja</p>
      </div>
      <button @click="abrirCriar"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition">
        + Nova categoria
      </button>
    </div>

    <div v-if="loading" class="space-y-2">
      <div v-for="n in 5" :key="n" class="h-14 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-2">
      <div v-for="cat in categorias" :key="cat.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3 flex items-center gap-3 group">
        <span class="text-xl flex-shrink-0">{{ cat.icon }}</span>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-zinc-200">{{ cat.nome }}</p>
          <p class="text-xs text-zinc-500">ordem: {{ cat.ordem }}</p>
        </div>
        <span v-if="!cat.ativo" class="px-1.5 py-0.5 bg-red-500/15 text-red-400 text-[10px] rounded font-bold">Inactiva</span>
        <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition">
          <button @click="abrirEditar(cat)"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button @click="toggleAtivo(cat)"
            :class="['w-8 h-8 rounded-lg flex items-center justify-center transition',
                     cat.ativo ? 'bg-red-500/10 hover:bg-red-500/20' : 'bg-green-500/10 hover:bg-green-500/20']">
            <span class="text-xs">{{ cat.ativo ? '🚫' : '✓' }}</span>
          </button>
        </div>
      </div>
      <div v-if="categorias.length === 0" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800 border-dashed">
        Sem categorias. Cria a primeira.
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="fecharModal">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-6 space-y-4">
        <h3 class="text-base font-bold text-zinc-100">{{ editando ? 'Editar categoria' : 'Nova categoria' }}</h3>

        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-zinc-800 border border-zinc-700 flex items-center justify-center text-2xl flex-shrink-0">
            {{ form.icon || '🏪' }}
          </div>
          <div class="flex-1">
            <label class="text-[10px] text-zinc-500 mb-1 block">Emoji / Ícone</label>
            <input v-model="form.icon" type="text" placeholder="🏪" maxlength="5"
              class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
        </div>

        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Nome *</label>
          <input v-model="form.nome" type="text" placeholder="ex: Restaurante"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
        </div>

        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Ordem (menor = aparece primeiro)</label>
          <input v-model.number="form.ordem" type="number" min="0"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
        </div>

        <div class="flex gap-3 pt-2">
          <button @click="fecharModal"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="guardar" :disabled="!form.nome.trim() || loadingGuardar"
            :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition',
                     !form.nome.trim() ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
            {{ editando ? 'Guardar' : 'Criar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
export default {
  name: 'AdminCategorias',
  data () {
    return {
      loading: true, categorias: [],
      showModal: false, editando: null,
      loadingGuardar: false,
      form: { nome: '', icon: '🏪', ordem: 99 },
    }
  },
  async created () { await this.fetchCategorias() },
  methods: {
    async fetchCategorias () {
      this.loading = true
      try {
        const { data } = await api.get('/app/admin/categorias/')
        this.categorias = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    abrirCriar () {
      this.editando = null
      this.form = { nome: '', icon: '🏪', ordem: 99 }
      this.showModal = true
    },
    abrirEditar (cat) {
      this.editando = cat
      this.form = { nome: cat.nome, icon: cat.icon, ordem: cat.ordem }
      this.showModal = true
    },
    fecharModal () { this.showModal = false; this.editando = null },
    async guardar () {
      if (!this.form.nome.trim()) return
      this.loadingGuardar = true
      try {
        if (this.editando) {
          await api.patch(`/app/admin/categorias/${this.editando.id}/`, this.form)
        } else {
          await api.post('/app/admin/categorias/', this.form)
        }
        this.fecharModal()
        await this.fetchCategorias()
      } catch (e) {
        console.error(e)
      } finally { this.loadingGuardar = false }
    },
    async toggleAtivo (cat) {
      try {
        await api.patch(`/app/admin/categorias/${cat.id}/`, { ativo: !cat.ativo })
        cat.ativo = !cat.ativo
      } catch (e) { console.error(e) }
    },
  },
}
</script>
