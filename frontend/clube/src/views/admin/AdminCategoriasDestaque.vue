<template>
  <div class="space-y-6">

    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Categorias em destaque</h2>
        <p class="text-xs text-zinc-500 mt-0.5">
          Escolhe categorias de lojas para aparecer na página principal
        </p>
      </div>
    </div>

    <!-- Abas por loja -->
    <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
      <button
        @click="lojaActiva = null; fetchDestaques()"
        :class="['px-4 py-2 rounded-full text-sm font-semibold transition whitespace-nowrap',
                 lojaActiva === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        Todos
      </button>
      <button
        v-for="loja in lojas" :key="loja.id"
        @click="lojaActiva = loja.id; fetchDestaques()"
        :class="['px-4 py-2 rounded-full text-sm font-semibold transition whitespace-nowrap',
                 lojaActiva === loja.id ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ loja.nome }}
      </button>
    </div>

    <!-- Adicionar destaque -->
    <div v-if="lojaActiva" class="bg-zinc-900/50 rounded-2xl border border-zinc-800 border-dashed p-4">
      <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">
        Categorias disponíveis para destacar
      </p>
      <div v-if="loadingDisponiveis" class="text-xs text-zinc-600">A carregar...</div>
      <div v-else-if="disponiveis.length === 0" class="text-xs text-zinc-600">
        Todas as categorias desta loja já estão em destaque.
      </div>
      <div v-else class="flex flex-wrap gap-2">
        <button
          v-for="cat in disponiveis" :key="cat.id"
          @click="adicionarDestaque(cat)"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                 bg-zinc-800 text-zinc-300 hover:bg-red-600/20 hover:text-red-400
                 border border-zinc-700 hover:border-red-500/50 transition capitalize">
          {{ cat.icone }} {{ cat.nome }}
          <span class="text-zinc-600">· {{ cat.total_produtos }} prod.</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <!-- Lista destaques -->
    <div v-else-if="destaques.length > 0" class="space-y-2">
      <p class="text-xs text-zinc-600 mb-3">
        Altera o campo "Ordem" para controlar a sequência no home
      </p>
      <div v-for="d in destaques" :key="d.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-center gap-4 group">

        <span class="text-2xl flex-shrink-0">{{ d.icone_final }}</span>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="text-sm font-bold text-zinc-200 capitalize">{{ d.nome }}</p>
            <span v-if="!d.ativo" class="px-1.5 py-0.5 bg-zinc-700 text-zinc-500 text-[10px] rounded">Inactivo</span>
          </div>
          <p class="text-xs text-zinc-500 mt-0.5">
            {{ d.loja_nome }} · Ordem: {{ d.ordem }}
          </p>
        </div>

        <!-- Acções -->
        <div class="flex items-center gap-2 opacity-100 group-hover:opacity-100 transition">
          <!-- Editar ordem/ícone -->
          <button @click="abrirEditar(d)"
            class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <!-- Toggle -->
          <button @click="toggleDestaque(d)"
            :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition',
                     d.ativo
                       ? 'bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500'
                       : 'bg-green-500/10 hover:bg-green-500/20 text-green-500']">
            {{ d.ativo ? 'Desactivar' : 'Activar' }}
          </button>
          <!-- Remover -->
          <button @click="removerDestaque(d)"
            class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="!loading"
         class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800 border-dashed">
      {{ lojaActiva ? 'Esta loja não tem categorias em destaque.' : 'Sem categorias em destaque. Selecciona uma loja acima.' }}
    </div>

    <!-- Modal editar ordem/ícone -->
    <div v-if="editando"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="editando = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm shadow-2xl p-6 space-y-4">
        <h3 class="text-base font-bold text-zinc-100 capitalize">{{ editando.nome }}</h3>
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Ícone personalizado (opcional)</label>
          <input v-model="formEditar.icone" type="text" maxlength="4" placeholder="deixa vazio para usar o da categoria"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   focus:outline-none focus:border-red-500 transition" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">Ordem no home</label>
          <input v-model.number="formEditar.ordem" type="number" min="0"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                   focus:outline-none focus:border-red-500 transition" />
        </div>
        <div class="flex gap-3 pt-2 border-t border-zinc-800">
          <button @click="editando = null"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
            Cancelar
          </button>
          <button @click="guardarEditar"
            class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition">
            Guardar
          </button>
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
      loadingDisponiveis: false,
      lojas: [],
      lojaActiva: null,
      destaques: [],
      disponiveis: [],
      editando: null,
      formEditar: { icone: '', ordem: 0 },
    }
  },

  async created () {
    await Promise.all([this.fetchLojas(), this.fetchDestaques()])
  },

  methods: {
    async fetchLojas () {
      try {
        const { data } = await api.get('/app/admin/categorias-destaque/lojas/')
        this.lojas = data
      } catch (e) { console.error(e) }
    },

    async fetchDestaques () {
      this.loading = true
      try {
        const params = this.lojaActiva ? { loja_id: this.lojaActiva } : {}
        const { data } = await api.get('/app/admin/categorias-destaque/', { params })
        this.destaques = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }

      if (this.lojaActiva) await this.fetchDisponiveis()
    },

    async fetchDisponiveis () {
      this.loadingDisponiveis = true
      try {
        const { data } = await api.get('/app/admin/categorias-destaque/disponiveis/', {
          params: { loja_id: this.lojaActiva }
        })
        this.disponiveis = data
      } catch (e) { console.error(e) }
      finally { this.loadingDisponiveis = false }
    },

    async adicionarDestaque (cat) {
      try {
        await api.post('/app/admin/categorias-destaque/criar/', {
          categoria_loja_id: cat.id,
          ordem: this.destaques.length,
        })
        await this.fetchDestaques()
      } catch (e) {
        console.error(e)
        alert(e.response?.data?.detail || 'Erro ao adicionar.')
      }
    },

    async toggleDestaque (d) {
      try {
        const { data } = await api.patch(`/app/admin/categorias-destaque/${d.id}/toggle/`)
        d.ativo = data.ativo
      } catch (e) { console.error(e) }
    },

    async removerDestaque (d) {
      if (!confirm(`Remover "${d.nome}" do home?`)) return
      try {
        await api.delete(`/app/admin/categorias-destaque/${d.id}/`)
        await this.fetchDestaques()
      } catch (e) { console.error(e) }
    },

    abrirEditar (d) {
      this.editando = d
      this.formEditar = { icone: d.icone || '', ordem: d.ordem }
    },

    async guardarEditar () {
      try {
        await api.patch(`/app/admin/categorias-destaque/${this.editando.id}/`, this.formEditar)
        this.editando = null
        await this.fetchDestaques()
      } catch (e) { console.error(e) }
    },
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>