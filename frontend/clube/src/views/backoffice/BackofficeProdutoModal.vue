<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
       @click.self="$emit('close')">
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800 sticky top-0 bg-zinc-900 z-10">
        <h2 class="text-base font-bold text-zinc-100">{{ produto ? 'Editar produto' : 'Novo produto' }}</h2>
        <button @click="$emit('close')" class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="guardar" class="p-6 space-y-5">

        <!-- Imagem -->
        <div class="flex items-center gap-4">
          <div class="w-20 h-20 rounded-xl overflow-hidden bg-zinc-800 flex-shrink-0 cursor-pointer relative group"
               @click="$refs.fileInput.click()">
            <img v-if="previewUrl" :src="previewUrl" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              </svg>
            </div>
            <div v-if="!previewUrl" class="absolute inset-0 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileChange" />
          <div>
            <p class="text-sm font-medium text-zinc-300">Imagem do produto</p>
            <p class="text-xs text-zinc-500 mt-0.5">Clica para seleccionar</p>
          </div>
        </div>

        <!-- Campos base -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-1 block">Nome *</label>
            <input v-model="form.nome" required type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Preço *</label>
            <input v-model="form.preco" required type="number" step="0.01" min="0"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">SKU</label>
            <input v-model="form.sku" type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>

          <!-- Tipo de produto -->
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Tipo de produto</label>
            <select v-model="form.tipo_id" @change="onTipoChange"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition">
              <option value="">— Sem tipo —</option>
              <optgroup v-if="tiposGlobais.length" label="Globais">
                <option v-for="t in tiposGlobais" :key="t.id" :value="t.id">{{ t.nome }}</option>
              </optgroup>
              <optgroup v-if="tiposLoja.length" label="Da tua loja">
                <option v-for="t in tiposLoja" :key="t.id" :value="t.id">{{ t.nome }}</option>
              </optgroup>
            </select>
          </div>

          <div>
            <label class="text-xs text-zinc-500 mb-1 block">Categoria</label>
            <input v-model="form.categoria" type="text"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition" />
          </div>
          <div class="sm:col-span-2">
            <label class="text-xs text-zinc-500 mb-1 block">Descricao</label>
            <textarea v-model="form.descricao" rows="3"
              class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 transition resize-none"></textarea>
          </div>
          <div class="flex items-center gap-3">
            <input v-model="form.destaque" type="checkbox" id="destaque"
              class="w-4 h-4 rounded border-zinc-600 text-red-600 focus:ring-red-500" />
            <label for="destaque" class="text-sm text-zinc-300">Produto em destaque</label>
          </div>
          <div class="flex items-center gap-3">
            <input v-model="form.ativo" type="checkbox" id="ativo"
              class="w-4 h-4 rounded border-zinc-600 text-red-600 focus:ring-red-500" />
            <label for="ativo" class="text-sm text-zinc-300">Produto activo</label>
          </div>
        </div>

        <!-- Atributos dinamicos do tipo -->
        <div v-if="tipoSelecionado && schemaNormalizado.length > 0">
          <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            Atributos
            <span class="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 rounded text-[10px] font-medium capitalize">
              {{ tipoSelecionado.nome }}
            </span>
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div v-for="attr in schemaNormalizado" :key="attr.nome">
              <label class="text-xs text-zinc-500 mb-1 block capitalize flex items-center gap-1">
                {{ attr.nome }}
                <span v-if="attr.obrigatorio" class="text-red-500">*</span>
              </label>

              <!-- choices — dropdown -->
              <select
                v-if="attr.tipo === 'choices'"
                v-model="form.atributos[attr.nome]"
                :required="attr.obrigatorio"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition">
                <option value="">— Escolher —</option>
                <option v-for="op in attr.opcoes" :key="op" :value="op">{{ op }}</option>
              </select>

              <!-- numero — input number -->
              <input
                v-else-if="attr.tipo === 'numero'"
                v-model="form.atributos[attr.nome]"
                type="number" step="any"
                :required="attr.obrigatorio"
                :placeholder="attr.nome"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition" />

              <!-- texto — input text -->
              <input
                v-else
                v-model="form.atributos[attr.nome]"
                type="text"
                :required="attr.obrigatorio"
                :placeholder="attr.nome"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 transition" />
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-2 border-t border-zinc-800">
          <button type="button" @click="$emit('close')"
            class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 hover:text-zinc-200 text-sm font-semibold transition">
            Cancelar
          </button>
          <button type="submit" :disabled="loading"
            :class="[
              'flex-1 py-2.5 rounded-xl text-sm font-bold transition flex items-center justify-center gap-2',
              loading ? 'bg-red-700 cursor-not-allowed opacity-70' : 'bg-red-600 hover:bg-red-500 text-white'
            ]">
            <span v-if="loading" class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
                <path d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" fill="currentColor" class="opacity-75"/>
              </svg>
              A guardar...
            </span>
            <span v-else>{{ produto ? 'Guardar alteracoes' : 'Criar produto' }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { useAsyncAction } from '@/composables/useAsyncAction'

export default {
  name: 'BackofficeProdutoModal',
  props: {
    lojaId:  [String, Number],
    produto: { type: Object, default: null },
  },
  emits: ['close', 'saved'],

  setup () {
    const { loading, wrap } = useAsyncAction()
    return { loading, wrap }
  },

  data () {
    return {
      tipos: [],
      ficheiro: null,
      previewUrl: '',
      form: {
        nome: '', preco: '', sku: '', categoria: '', descricao: '',
        tipo_id: '', destaque: false, ativo: true, atributos: {},
      },
    }
  },

  computed: {
    tiposGlobais () {
      return this.tipos.filter(t => t.is_global)
    },
    tiposLoja () {
      return this.tipos.filter(t => !t.is_global)
    },

    tipoSelecionado () {
      if (!this.form.tipo_id) return null
      return this.tipos.find(t => t.id === parseInt(this.form.tipo_id)) || null
    },

    // schema sempre normalizado como lista de objectos
    schemaNormalizado () {
      if (!this.tipoSelecionado?.atributos_schema) return []
      return this.tipoSelecionado.atributos_schema.map(a =>
        typeof a === 'string'
          ? { nome: a, tipo: 'texto', opcoes: [], obrigatorio: false }
          : a
      )
    },
  },

  async created () {
    // usa o endpoint da loja para ter globais + da loja
    await this.fetchTipos()
    if (this.produto) {
      this.form = {
        nome:      this.produto.nome      || '',
        preco:     this.produto.preco     || '',
        sku:       this.produto.sku       || '',
        categoria: this.produto.categoria || '',
        descricao: this.produto.descricao || '',
        tipo_id:   this.produto.tipo?.id  || '',
        destaque:  this.produto.destaque  || false,
        ativo:     this.produto.ativo     !== false,
        atributos: { ...(this.produto.atributos || {}) },
      }
      this.previewUrl = this.produto.ficheiro_url || ''
    }
  },

  methods: {
    onFileChange (e) {
      const file = e.target.files[0]
      if (!file) return
      this.ficheiro   = file
      this.previewUrl = URL.createObjectURL(file)
    },

    onTipoChange () {
      // limpa atributos ao mudar de tipo para evitar valores de outro schema
      this.form.atributos = {}
      // pre-preenche com valores existentes se o produto ja tem atributos
      if (this.produto?.atributos) {
        this.schemaNormalizado.forEach(attr => {
          if (this.produto.atributos[attr.nome] !== undefined) {
            this.form.atributos[attr.nome] = this.produto.atributos[attr.nome]
          }
        })
      }
    },

    async fetchTipos () {
      try {
        // usa endpoint da loja para ter globais + tipos da loja
        const { data } = await api.get(`/app/loja/${this.lojaId}/tipos/`)
        this.tipos = data
      } catch (e) {
        // fallback para endpoint publico
        try {
          const { data } = await api.get('/app/produto/tipos/')
          this.tipos = data
        } catch (e2) { console.error(e2) }
      }
    },

    async guardar () {
      await this.wrap(async () => {
        const fd = new FormData()
        Object.entries(this.form).forEach(([k, v]) => {
          if (k === 'atributos') {
            fd.append('atributos', JSON.stringify(v))
          } else if (k === 'tipo_id') {
            if (v) fd.append('tipo_id', v)
          } else if (typeof v === 'boolean') {
            fd.append(k, v ? 'true' : 'false')
          } else if (v !== '' && v !== null && v !== undefined) {
            fd.append(k, v)
          }
        })
        if (this.ficheiro) fd.append('ficheiro', this.ficheiro)

        if (this.produto) {
          await api.patch(
            `/app/loja/${this.lojaId}/produtos/${this.produto.id}/editar/`, fd,
            { headers: { 'Content-Type': 'multipart/form-data' } }
          )
        } else {
          await api.post(
            `/app/loja/${this.lojaId}/produtos/criar/`, fd,
            { headers: { 'Content-Type': 'multipart/form-data' } }
          )
        }
        this.$emit('saved')
      })
    },
  }
}
</script>