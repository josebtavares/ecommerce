<!-- Seletor de templates no backoffice da loja -->
<template>
  <div class="space-y-6 max-w-4xl">

    <div>
      <h2 class="text-lg font-bold text-zinc-100">Aparência da loja</h2>
      <p class="text-xs text-zinc-500 mt-0.5">
        Escolhe o template e as cores que definem o aspecto da tua loja.
      </p>
    </div>

    <!-- Cores -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 space-y-4">
      <h3 class="text-sm font-bold text-zinc-200">🎨 Cores</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-zinc-500 mb-2 block">Cor primária</label>
          <div class="flex items-center gap-3">
            <input type="color" v-model="form.cor_primaria"
              class="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent" />
            <input v-model="form.cor_primaria" type="text" maxlength="7"
              class="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 font-mono" />
          </div>
          <p class="text-[10px] text-zinc-600 mt-1">Botões, destaques, badges</p>
        </div>
        <div>
          <label class="text-xs text-zinc-500 mb-2 block">Cor secundária</label>
          <div class="flex items-center gap-3">
            <input type="color" v-model="form.cor_secundaria"
              class="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent" />
            <input v-model="form.cor_secundaria" type="text" maxlength="7"
              class="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                     focus:outline-none focus:border-red-500 font-mono" />
          </div>
          <p class="text-[10px] text-zinc-600 mt-1">Fundos, backgrounds</p>
        </div>
      </div>
      <!-- Preview das cores -->
      <div class="flex items-center gap-3 pt-2">
        <div class="flex-1 h-8 rounded-lg" :style="{ backgroundColor: form.cor_primaria }"></div>
        <div class="flex-1 h-8 rounded-lg border border-zinc-700" :style="{ backgroundColor: form.cor_secundaria }"></div>
        <p class="text-xs text-zinc-600">Preview</p>
      </div>
    </div>

    <!-- Modo dark/light por defeito -->
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
      <h3 class="text-sm font-bold text-zinc-200 mb-3">🌙 Modo de cor por defeito</h3>
      <div class="flex gap-3">
        <button @click="form.dark_mode = true"
          :class="['flex-1 py-3 rounded-xl border text-sm font-semibold transition flex items-center justify-center gap-2',
                   form.dark_mode ? 'bg-zinc-800 border-red-500/50 text-zinc-100' : 'border-zinc-700 text-zinc-500 hover:border-zinc-600']">
          🌙 Dark
        </button>
        <button @click="form.dark_mode = false"
          :class="['flex-1 py-3 rounded-xl border text-sm font-semibold transition flex items-center justify-center gap-2',
                   !form.dark_mode ? 'bg-zinc-800 border-red-500/50 text-zinc-100' : 'border-zinc-700 text-zinc-500 hover:border-zinc-600']">
          ☀️ Light
        </button>
      </div>
      <p class="text-[10px] text-zinc-600 mt-2">O visitante pode sempre mudar na página da loja.</p>
    </div>

    <!-- Seletor de templates -->
    <div>
      <h3 class="text-sm font-bold text-zinc-200 mb-3">📐 Template</h3>

      <!-- Filtro por categoria -->
      <div class="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide">
        <button @click="filtroCategoria = null"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap',
                   filtroCategoria === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          Todos
        </button>
        <button v-for="cat in categoriasFiltro" :key="cat.value"
          @click="filtroCategoria = cat.value"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap capitalize',
                   filtroCategoria === cat.value ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ cat.label }}
        </button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="template in templatesFiltrados" :key="template.id"
             @click="form.template_id = template.id"
             :class="['relative rounded-2xl border-2 p-4 cursor-pointer transition-all',
                      form.template_id === template.id
                        ? 'border-red-500 bg-red-500/10'
                        : 'border-zinc-800 bg-zinc-900 hover:border-zinc-600']">
          <!-- Preview emoji -->
          <div class="w-full aspect-video rounded-xl flex items-center justify-center text-5xl mb-3"
               :class="form.template_id === template.id ? 'bg-red-500/20' : 'bg-zinc-800'">
            {{ template.preview }}
          </div>
          <div class="flex items-start justify-between gap-2">
            <div>
              <p class="text-sm font-bold" :class="form.template_id === template.id ? 'text-zinc-100' : 'text-zinc-200'">
                {{ template.nome }}
              </p>
              <p class="text-xs mt-0.5" :class="form.template_id === template.id ? 'text-zinc-300' : 'text-zinc-500'">
                {{ template.descricao }}
              </p>
            </div>
            <div v-if="form.template_id === template.id"
                 class="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <!-- Tags de categoria -->
          <div class="flex flex-wrap gap-1 mt-2">
            <span v-for="cat in template.categorias" :key="cat"
                  class="px-1.5 py-0.5 bg-zinc-800 text-zinc-500 text-[10px] rounded capitalize">
              {{ cat === 'todos' ? 'genérico' : cat }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Preview link -->
    <div class="flex items-center gap-3 p-4 bg-zinc-900/50 rounded-2xl border border-zinc-800 border-dashed">
      <span class="text-zinc-500 text-sm">
        Vê como fica em tempo real:
      </span>
      <a :href="`/loja/${lojaId}?preview=1`" target="_blank"
         class="text-red-400 hover:text-red-300 text-sm font-semibold transition flex items-center gap-1">
        Abrir pré-visualização
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </div>

    <!-- Guardar -->
    <div v-if="erro" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">{{ erro }}</div>
    <div class="flex justify-end">
      <button @click="guardar" :disabled="loading"
        :class="['px-6 py-2.5 rounded-xl text-sm font-bold transition flex items-center gap-2',
                 loading ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
        <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
          <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" class="opacity-75"/>
        </svg>
        {{ loading ? 'A guardar...' : 'Guardar aparência' }}
      </button>
    </div>

  </div>
</template>

<script>
import { TEMPLATES } from '@/config/lojaTemplates'
import api from '@/services/api'

export default {
  name: 'BackofficeTemplates',
  props: { lojaId: [String, Number] },

  data () {
    return {
      loading: false,
      erro: '',
      filtroCategoria: null,
      form: {
        template_id:    'classico',
        cor_primaria:   '#dc2626',
        cor_secundaria: '#1c1c1e',
        dark_mode:      true,
      },
      categoriasFiltro: [
        { value: 'todos',       label: 'Genéricos' },
        { value: 'restaurante', label: 'Restaurante' },
        { value: 'moda',        label: 'Moda' },
        { value: 'tecnologia',  label: 'Tecnologia' },
      ],
    }
  },

  computed: {
    templatesFiltrados () {
      if (!this.filtroCategoria) return TEMPLATES
      return TEMPLATES.filter(t =>
        t.categorias.includes('todos') || t.categorias.includes(this.filtroCategoria)
      )
    },
  },

  async created () {
    await this.fetchAparencia()
  },

  methods: {
    async fetchAparencia () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/`)
        this.form.template_id    = data.template_id    || 'classico'
        this.form.cor_primaria   = data.cor_primaria   || '#dc2626'
        this.form.cor_secundaria = data.cor_secundaria || '#1c1c1e'
        this.form.dark_mode      = data.dark_mode      !== undefined ? data.dark_mode : true
      } catch (e) { console.error(e) }
    },

    async guardar () {
      this.loading = true; this.erro = ''
      try {
        await api.patch(`/app/loja/${this.lojaId}/aparencia/`, this.form)
        // actualiza cache local para a loja
        const cacheKey = `loja_template_${this.lojaId}`
        localStorage.setItem(cacheKey, JSON.stringify({
          templateId:    this.form.template_id,
          corPrimaria:   this.form.cor_primaria,
          corSecundaria: this.form.cor_secundaria,
          darkMode:      this.form.dark_mode,
        }))
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao guardar.'
      } finally { this.loading = false }
    },
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>