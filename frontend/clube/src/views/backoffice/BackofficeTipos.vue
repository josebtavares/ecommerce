<template>
  <div class="space-y-5 max-w-3xl">

    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Tipos de produto</h2>
        <p class="text-xs text-zinc-500 mt-0.5">
          Define as categorias e atributos dos teus produtos
        </p>
      </div>
      <button @click="abrirCriar"
        class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold transition flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Novo tipo
      </button>
    </div>

    <!-- ═══ ABAS ═══ -->
    <div class="flex gap-1 bg-zinc-900 rounded-xl p-1 w-fit">
      <button
        @click="abaActiva = 'loja'"
        :class="['px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2',
                 abaActiva === 'loja'
                   ? 'bg-zinc-700 text-zinc-100'
                   : 'text-zinc-500 hover:text-zinc-300']">
        Da tua loja
        <span v-if="tiposLoja.length > 0"
              class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-red-600/20 text-red-400">
          {{ tiposLoja.length }}
        </span>
      </button>
      <button
        @click="abaActiva = 'globais'"
        :class="['px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2',
                 abaActiva === 'globais'
                   ? 'bg-zinc-700 text-zinc-100'
                   : 'text-zinc-500 hover:text-zinc-300']">
        Globais da plataforma
        <span v-if="tiposGlobais.length > 0"
              class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-zinc-700 text-zinc-400">
          {{ tiposGlobais.length }}
        </span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 4" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <template v-else>

      <!-- ══ ABA: DA TUA LOJA ══ -->
      <div v-if="abaActiva === 'loja'" class="space-y-2">
        <div v-if="tiposLoja.length === 0"
             class="text-center py-8 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800 border-dashed">
          Ainda não criaste nenhum tipo.
          <button @click="abrirCriar" class="text-red-400 hover:text-red-300 ml-1">Criar agora →</button>
        </div>

        <div v-for="tipo in tiposLoja" :key="tipo.id"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-start gap-4 group">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <p class="text-sm font-bold text-zinc-200 capitalize">{{ tipo.nome }}</p>
              <span v-if="!tipo.ativo" class="px-1.5 py-0.5 bg-red-500/15 text-red-400 text-[10px] rounded font-medium">
                Inactivo
              </span>
            </div>
            <p v-if="tipo.descricao" class="text-xs text-zinc-500 mb-2">{{ tipo.descricao }}</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="attr in tipo.atributos_schema" :key="attr.nome"
                    :class="['px-2 py-0.5 rounded-lg text-xs font-medium',
                             attr.tipo === 'choices' ? 'bg-blue-500/15 text-blue-400' :
                             attr.tipo === 'numero'  ? 'bg-green-500/15 text-green-400' :
                                                       'bg-zinc-800 text-zinc-400']">
                {{ attr.nome }}
                <span v-if="attr.tipo === 'choices'" class="opacity-60 ml-1">
                  ({{ attr.opcoes?.join(', ') }})
                </span>
              </span>
              <span v-if="tipo.atributos_schema.length === 0" class="text-xs text-zinc-600">
                Sem atributos definidos
              </span>
            </div>
          </div>

          <!-- Acções -->
          <div class="flex gap-2 opacity-100 sm:group-hover:opacity-100 transition flex-shrink-0">
            <!-- Editar -->
            <button @click="abrirEditar(tipo)" title="Editar"
              class="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <!-- Reactivar (só inactivos) -->
            <button v-if="!tipo.ativo" @click="reativarTipo(tipo)" title="Reactivar"
              class="w-8 h-8 rounded-lg bg-green-500/10 hover:bg-green-500/20 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <!-- Desactivar (só activos) -->
            <button v-if="tipo.ativo" @click="eliminarTipo(tipo)" title="Desactivar"
              class="w-8 h-8 rounded-lg bg-yellow-500/10 hover:bg-yellow-500/20 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </button>
            <!-- Eliminar definitivamente -->
            <button @click="eliminarTipoDefinitivamente(tipo)" title="Eliminar definitivamente"
              class="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- ══ ABA: GLOBAIS ══ -->
      <div v-if="abaActiva === 'globais'" class="space-y-2">
        <p class="text-xs text-zinc-600 bg-zinc-900/50 rounded-xl px-4 py-3 border border-zinc-800">
          Tipos criados pela plataforma. Podes usá-los nos teus produtos mas não os podes editar.
          Se precisares de atributos específicos, cria um tipo próprio na aba "Da tua loja".
        </p>
        <div v-for="tipo in tiposGlobais" :key="tipo.id"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex items-start gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <p class="text-sm font-bold text-zinc-200 capitalize">{{ tipo.nome }}</p>
              <span class="px-1.5 py-0.5 bg-zinc-700 text-zinc-400 text-[10px] rounded font-medium">Global</span>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="attr in tipo.atributos_schema" :key="attr.nome"
                    :class="['px-2 py-0.5 rounded-lg text-xs font-medium',
                             attr.tipo === 'choices' ? 'bg-blue-500/15 text-blue-400' :
                             attr.tipo === 'numero'  ? 'bg-green-500/15 text-green-400' :
                                                       'bg-zinc-800 text-zinc-400']">
                {{ attr.nome }}
                <span v-if="attr.tipo === 'choices'" class="opacity-60 ml-1">
                  ({{ attr.opcoes?.join(', ') }})
                </span>
              </span>
            </div>
          </div>
        </div>
        <p v-if="tiposGlobais.length === 0" class="text-xs text-zinc-600 px-2">
          Sem tipos globais disponíveis.
        </p>
      </div>

    </template>

    <!-- ═══ MODAL CRIAR/EDITAR ═══ -->
    <div v-if="showModal"
         class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
         @click.self="fecharModal">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">

        <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800 sticky top-0 bg-zinc-900 z-10">
          <h2 class="text-base font-bold text-zinc-100">
            {{ tipoEditando ? 'Editar tipo' : 'Novo tipo de produto' }}
          </h2>
          <button @click="fecharModal" class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-5">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Nome do tipo *</label>
            <input v-model="form.nome" type="text" placeholder="ex: roupa, bebida, prato..."
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>

          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Descrição</label>
            <input v-model="form.descricao" type="text" placeholder="Descrição opcional..."
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>

          <!-- Atributos -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <label class="text-xs text-zinc-500">Atributos</label>
              <button @click="adicionarAtributo" type="button"
                class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 transition flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                Adicionar atributo
              </button>
            </div>

            <div v-if="form.atributos_schema.length === 0"
                 class="text-center py-5 text-zinc-600 text-xs border border-dashed border-zinc-800 rounded-xl">
              Sem atributos. Clica em "Adicionar atributo" para começar.
            </div>

            <div class="space-y-3">
              <div v-for="(attr, idx) in form.atributos_schema" :key="idx"
                   class="bg-zinc-800/60 rounded-xl p-4 space-y-3">
                <div class="flex items-center gap-3">
                  <div class="flex-1">
                    <label class="text-[10px] text-zinc-500 mb-1 block">Nome</label>
                    <input v-model="attr.nome" type="text" placeholder="ex: tamanho, cor..."
                      class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100
                             focus:outline-none focus:border-red-500 transition" />
                  </div>
                  <div class="w-32">
                    <label class="text-[10px] text-zinc-500 mb-1 block">Tipo</label>
                    <select v-model="attr.tipo"
                      class="w-full px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100
                             focus:outline-none focus:border-red-500 transition">
                      <option value="texto">Texto livre</option>
                      <option value="choices">Escolha</option>
                      <option value="numero">Número</option>
                    </select>
                  </div>
                  <div class="flex items-center gap-1.5 pt-4">
                    <input v-model="attr.obrigatorio" type="checkbox" :id="'obrig-'+idx"
                      class="w-3.5 h-3.5 rounded border-zinc-600 text-red-600" />
                    <label :for="'obrig-'+idx" class="text-[10px] text-zinc-500">Obrig.</label>
                  </div>
                  <button @click="removerAtributo(idx)" type="button"
                    class="mt-4 w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 flex items-center justify-center transition flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div v-if="attr.tipo === 'choices'">
                  <label class="text-[10px] text-zinc-500 mb-1.5 block">
                    Opções disponíveis
                    <span class="text-zinc-600 ml-1">· separa por vírgula ou pressiona Enter</span>
                  </label>
                  <div class="flex flex-wrap gap-1.5 mb-2">
                    <span v-for="(op, oi) in attr.opcoes" :key="oi"
                          class="flex items-center gap-1 px-2 py-0.5 bg-blue-500/15 text-blue-400 text-xs rounded-lg">
                      {{ op }}
                      <button @click="removerOpcao(idx, oi)" type="button" class="hover:text-red-400 transition">×</button>
                    </span>
                  </div>
                  <input
                    v-model="novasOpcoes[idx]"
                    @keydown.enter.prevent="adicionarOpcao(idx)"
                    @keydown.comma.prevent="adicionarOpcao(idx)"
                    type="text"
                    placeholder="Escreve uma opção e pressiona Enter..."
                    class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-100
                           focus:outline-none focus:border-blue-500 transition" />
                </div>
              </div>
            </div>
          </div>

          <!-- Erro inline -->
          <div v-if="erroModal"
               class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">
            {{ erroModal }}
          </div>

          <div class="flex gap-3 pt-2 border-t border-zinc-800">
            <button @click="fecharModal" type="button"
              class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">
              Cancelar
            </button>
            <button @click="guardar" :disabled="loading || !form.nome.trim()"
              :class="['flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
                       loading || !form.nome.trim()
                         ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                         : 'bg-red-600 hover:bg-red-500 text-white']">
              <span v-if="loading" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                  <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
                </svg>
                A guardar…
              </span>
              <span v-else>{{ tipoEditando ? 'Guardar alterações' : 'Criar tipo' }}</span>
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
  name: 'BackofficeTipos',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: false,
      erroModal: '',
      tipos: [],
      abaActiva: 'loja',   // começa na aba da loja
      showModal: false,
      tipoEditando: null,
      novasOpcoes: {},
      form: { nome: '', descricao: '', atributos_schema: [] },
    }
  },

  computed: {
    tiposGlobais () { return this.tipos.filter(t => t.is_global) },
    tiposLoja    () { return this.tipos.filter(t => !t.is_global) },
  },

  async created () { await this.fetchTipos() },

  methods: {
    async fetchTipos () {
      this.loading = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/tipos/`)
        this.tipos = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },

    abrirCriar () {
      this.tipoEditando = null
      this.erroModal = ''
      this.novasOpcoes = {}
      this.form = { nome: '', descricao: '', atributos_schema: [] }
      this.showModal = true
    },

    abrirEditar (tipo) {
      this.tipoEditando = tipo
      this.erroModal = ''
      this.novasOpcoes = {}
      this.form = {
        nome:             tipo.nome,
        descricao:        tipo.descricao || '',
        atributos_schema: JSON.parse(JSON.stringify(tipo.atributos_schema || [])),
      }
      this.showModal = true
    },

    fecharModal () {
      this.showModal = false
      this.tipoEditando = null
      this.erroModal = ''
      this.novasOpcoes = {}
    },

    adicionarAtributo () {
      this.form.atributos_schema.push({ nome: '', tipo: 'texto', opcoes: [], obrigatorio: false })
    },

    removerAtributo (idx) {
      this.form.atributos_schema.splice(idx, 1)
      delete this.novasOpcoes[idx]
    },

    adicionarOpcao (idx) {
      const val = (this.novasOpcoes[idx] || '').trim()
      if (!val) return
      val.split(',').map(v => v.trim()).filter(Boolean).forEach(v => {
        if (!this.form.atributos_schema[idx].opcoes.includes(v)) {
          this.form.atributos_schema[idx].opcoes.push(v)
        }
      })
      this.novasOpcoes = { ...this.novasOpcoes, [idx]: '' }
    },

    removerOpcao (attrIdx, opIdx) {
      this.form.atributos_schema[attrIdx].opcoes.splice(opIdx, 1)
    },

    async guardar () {
      if (!this.form.nome.trim()) return
      this.loading = true
      this.erroModal = ''
      try {
        if (this.tipoEditando) {
          await api.patch(`/app/loja/${this.lojaId}/tipos/${this.tipoEditando.id}/`, this.form)
        } else {
          await api.post(`/app/loja/${this.lojaId}/tipos/criar/`, this.form)
        }
        this.fecharModal()
        await this.fetchTipos()
      } catch (e) {
        this.erroModal = e.response?.data?.nome
          || e.response?.data?.detail
          || 'Erro ao guardar o tipo.'
      } finally {
        this.loading = false
      }
    },

    async reativarTipo (tipo) {
      try {
        await api.post(`/app/loja/${this.lojaId}/tipos/criar/`, {
          nome: tipo.nome,
          descricao: tipo.descricao,
          atributos_schema: tipo.atributos_schema,
        })
        await this.fetchTipos()
      } catch (e) {
        alert(e.response?.data?.detail || 'Erro ao reactivar.')
      }
    },

    async eliminarTipo (tipo) {
      if (!confirm(`Desactivar o tipo "${tipo.nome}"? Pode ser reactivado depois.`)) return
      try {
        await api.delete(`/app/loja/${this.lojaId}/tipos/${tipo.id}/`)
        await this.fetchTipos()
      } catch (e) {
        alert(e.response?.data?.detail || 'Erro ao desactivar.')
      }
    },

    async eliminarTipoDefinitivamente (tipo) {
      if (!confirm(
        `Eliminar DEFINITIVAMENTE o tipo "${tipo.nome}"?\nEsta acção não pode ser desfeita.`
      )) return
      try {
        await api.delete(`/app/loja/${this.lojaId}/tipos/${tipo.id}/?hard=1`)
        await this.fetchTipos()
      } catch (e) {
        alert(e.response?.data?.detail || 'Erro ao eliminar.')
      }
    },
  }
}
</script>