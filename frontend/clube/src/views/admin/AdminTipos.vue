<template>
  <div class="space-y-5 max-w-3xl">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Tipos de produto globais</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Visíveis para todas as lojas da plataforma</p>
      </div>
      <button @click="abrirCriar"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition flex items-center gap-2">
        + Novo tipo
      </button>
    </div>

    <div v-if="loading" class="space-y-3">
      <div v-for="n in 4" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-2">
      <div v-for="tipo in tipos" :key="tipo.id"
           class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-start gap-4 group">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-2">
            <p class="text-sm font-bold text-zinc-200 capitalize">{{ tipo.nome }}</p>
            <span v-if="!tipo.ativo" class="px-1.5 py-0.5 bg-red-500/15 text-red-400 text-[10px] rounded font-bold">Inactivo</span>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="attr in tipo.atributos_schema" :key="attr.nome"
                  :class="['px-2 py-0.5 rounded-lg text-xs font-medium',
                           attr.tipo === 'choices' ? 'bg-blue-500/15 text-blue-400' :
                           attr.tipo === 'numero'  ? 'bg-green-500/15 text-green-400' :
                                                     'bg-zinc-800 text-zinc-400']">
              {{ attr.nome }}
              <span v-if="attr.tipo === 'choices'" class="opacity-60 ml-1">({{ attr.opcoes?.join(', ') }})</span>
            </span>
          </div>
        </div>
        <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition">
          <button @click="abrirEditar(tipo)" class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          </button>
          <button @click="eliminar(tipo)" class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
          </button>
        </div>
      </div>
      <div v-if="tipos.length === 0" class="text-center py-12 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800 border-dashed">
        Sem tipos globais. Cria o primeiro.
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" @click.self="fecharModal">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800 sticky top-0 bg-zinc-900">
          <h2 class="text-base font-bold text-zinc-100">{{ tipoEditando ? 'Editar tipo' : 'Novo tipo global' }}</h2>
          <button @click="fecharModal" class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div class="p-6 space-y-5">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Nome *</label>
            <input v-model="form.nome" type="text" placeholder="ex: roupa, bebida, eletronico..."
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Descricao</label>
            <input v-model="form.descricao" type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <div class="flex items-center justify-between mb-3">
              <label class="text-xs text-zinc-500">Atributos</label>
              <button @click="adicionarAtributo" type="button"
                class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 transition">
                + Atributo
              </button>
            </div>
            <div class="space-y-3">
              <div v-for="(attr, idx) in form.atributos_schema" :key="idx" class="bg-zinc-800/60 rounded-xl p-4 space-y-3">
                <div class="flex items-center gap-3">
                  <div class="flex-1">
                    <label class="text-[10px] text-zinc-500 mb-1 block">Nome</label>
                    <input v-model="attr.nome" type="text" placeholder="ex: tamanho"
                      class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition" />
                  </div>
                  <div class="w-32">
                    <label class="text-[10px] text-zinc-500 mb-1 block">Tipo</label>
                    <select v-model="attr.tipo"
                      class="w-full px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-red-500 transition">
                      <option value="texto">Texto</option>
                      <option value="choices">Choices</option>
                      <option value="numero">Numero</option>
                    </select>
                  </div>
                  <div class="flex items-center gap-1.5 pt-4">
                    <input v-model="attr.obrigatorio" type="checkbox" :id="`obrig-${idx}`" class="w-3.5 h-3.5" />
                    <label :for="`obrig-${idx}`" class="text-[10px] text-zinc-500">Obrig.</label>
                  </div>
                  <button @click="form.atributos_schema.splice(idx, 1)" type="button"
                    class="mt-4 w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <div v-if="attr.tipo === 'choices'">
                  <label class="text-[10px] text-zinc-500 mb-1.5 block">Opcoes · Enter ou virgula para adicionar</label>
                  <div class="flex flex-wrap gap-1.5 mb-2">
                    <span v-for="(op, oi) in attr.opcoes" :key="oi"
                          class="flex items-center gap-1 px-2 py-0.5 bg-blue-500/15 text-blue-400 text-xs rounded-lg">
                      {{ op }}
                      <button @click="attr.opcoes.splice(oi, 1)" type="button" class="hover:text-red-400 transition">×</button>
                    </span>
                  </div>
                  <input
                    v-model="novasOpcoes[idx]"
                    @keydown.enter.prevent="adicionarOpcao(idx)"
                    @keydown.comma.prevent="adicionarOpcao(idx)"
                    type="text" placeholder="Escreve e pressiona Enter..."
                    class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-blue-500 transition" />
                </div>
              </div>
            </div>
          </div>
          <div class="flex gap-3 pt-2 border-t border-zinc-800">
            <button @click="fecharModal" type="button"
              class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
              Cancelar
            </button>
            <button @click="guardar" :disabled="loadingGuardar || !form.nome.trim()"
              :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition',
                       loadingGuardar || !form.nome.trim() ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
              {{ tipoEditando ? 'Guardar' : 'Criar tipo' }}
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
  name: 'AdminTipos',
  data () {
    return {
      loading: true, tipos: [], showModal: false,
      tipoEditando: null, loadingGuardar: false,
      novasOpcoes: {},
      form: { nome: '', descricao: '', atributos_schema: [] },
    }
  },
  async created () { await this.fetchTipos() },
  methods: {
    async fetchTipos () {
      this.loading = true
      try { const { data } = await api.get('/app/admin/tipos/'); this.tipos = data }
      catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    abrirCriar () { this.tipoEditando = null; this.novasOpcoes = {}; this.form = { nome: '', descricao: '', atributos_schema: [] }; this.showModal = true },
    abrirEditar (tipo) {
      this.tipoEditando = tipo; this.novasOpcoes = {}
      this.form = { nome: tipo.nome, descricao: tipo.descricao || '', atributos_schema: JSON.parse(JSON.stringify(tipo.atributos_schema || [])) }
      this.showModal = true
    },
    fecharModal () { this.showModal = false; this.tipoEditando = null },
    adicionarAtributo () { this.form.atributos_schema.push({ nome: '', tipo: 'texto', opcoes: [], obrigatorio: false }) },
    adicionarOpcao (idx) {
      const val = (this.novasOpcoes[idx] || '').trim()
      if (!val) return
      val.split(',').map(v => v.trim()).filter(Boolean).forEach(v => {
        if (!this.form.atributos_schema[idx].opcoes.includes(v)) this.form.atributos_schema[idx].opcoes.push(v)
      })
      this.novasOpcoes = { ...this.novasOpcoes, [idx]: '' }
    },
    async guardar () {
      if (!this.form.nome.trim()) return
      this.loadingGuardar = true
      try {
        if (this.tipoEditando) await api.patch(`/app/admin/tipos/${this.tipoEditando.id}/`, this.form)
        else await api.post('/app/admin/tipos/', this.form)
        this.fecharModal()
        await this.fetchTipos()
      } catch (e) { console.error(e) }
      finally { this.loadingGuardar = false }
    },
    async eliminar (tipo) {
      if (!confirm(`Eliminar o tipo "${tipo.nome}"?`)) return
      try { await api.delete(`/app/admin/tipos/${tipo.id}/`); await this.fetchTipos() }
      catch (e) { console.error(e) }
    },
  },
}
</script>
