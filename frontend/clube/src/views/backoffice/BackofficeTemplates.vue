<!-- BackofficeTemplates.vue — Aparência da loja com previews ricos -->
<template>
  <div class="space-y-6 max-w-5xl">

    <div>
      <h2 class="text-lg font-bold text-zinc-100">Aparência da loja</h2>
      <p class="text-xs text-zinc-500 mt-0.5">Escolhe o template e as cores que definem o aspecto da tua loja.</p>
    </div>

    <!-- Abas principais -->
    <div class="flex gap-1 border-b border-zinc-800">
      <button v-for="tab in tabs" :key="tab.id" @click="abaAtiva = tab.id"
        :class="['px-4 py-2.5 text-sm font-semibold transition-all border-b-2 -mb-px',
                 abaAtiva === tab.id
                   ? 'border-red-500 text-zinc-100'
                   : 'border-transparent text-zinc-500 hover:text-zinc-300']">
        {{ tab.label }}
      </button>
    </div>

    <!-- ── ABA: TEMPLATE ── -->
    <div v-if="abaAtiva === 'template'">
      <!-- Filtro por categoria -->
      <div class="flex gap-2 overflow-x-auto pb-2 mb-5 scrollbar-hide">
        <button @click="filtroCategoria = null"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                   filtroCategoria === null ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          Todos
        </button>
        <button v-for="cat in categoriasFiltro" :key="cat.value"
          @click="filtroCategoria = cat.value"
          :class="['px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap flex-shrink-0',
                   filtroCategoria === cat.value ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ cat.label }}
        </button>
      </div>

      <!-- Grid de templates -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="tpl in templatesFiltrados" :key="tpl.id"
             @click="form.template_id = tpl.id"
             :class="['relative rounded-2xl border-2 overflow-hidden cursor-pointer transition-all duration-200 group',
                      form.template_id === tpl.id
                        ? 'border-red-500 shadow-lg shadow-red-500/10'
                        : 'border-zinc-800 bg-zinc-900 hover:border-zinc-600']">

          <!-- Mini preview visual -->
          <div class="relative w-full overflow-hidden" style="aspect-ratio:16/9">
            <TemplateMiniPreview :template="tpl" />

            <!-- Overlay hover com botão preview -->
            <div class="absolute inset-0 bg-black/60 backdrop-blur-[2px] flex items-center justify-center gap-2
                        opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <button @click.stop="abrirPreview(tpl)"
                class="px-3 py-1.5 rounded-lg bg-white/15 border border-white/20 text-white text-xs font-semibold backdrop-blur-md hover:bg-white/25 transition">
                Preview
              </button>
              <button @click.stop="form.template_id = tpl.id"
                class="px-3 py-1.5 rounded-lg text-white text-xs font-bold transition hover:opacity-90"
                :style="{ background: tpl.primaryDefault || '#dc2626' }">
                Selecionar
              </button>
            </div>

            <!-- Badge selecionado -->
            <div v-if="form.template_id === tpl.id"
                 class="absolute top-2 right-2 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>

          <!-- Info do template -->
          <div class="p-3" :class="form.template_id === tpl.id ? 'bg-red-500/5' : 'bg-zinc-900'">
            <div class="flex items-start justify-between gap-2 mb-1">
              <p class="text-sm font-bold text-zinc-100">{{ tpl.nome }}</p>
              <span class="px-1.5 py-0.5 rounded-full text-[10px] font-semibold flex-shrink-0"
                    :style="tagStyle(tpl.tag)">
                {{ tpl.tag }}
              </span>
            </div>
            <p class="text-xs text-zinc-500 leading-relaxed">{{ tpl.descricao }}</p>
            <!-- Cor primária dot -->
            <div class="flex items-center gap-1.5 mt-2">
              <div class="w-2.5 h-2.5 rounded-full" :style="{ background: tpl.primaryDefault, boxShadow: '0 0 6px '+tpl.primaryDefault+'60' }"></div>
              <span class="text-[10px] text-zinc-600 font-mono">{{ tpl.primaryDefault }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview link -->
      <div class="flex items-center gap-3 p-4 bg-zinc-900/50 rounded-2xl border border-zinc-800 border-dashed mt-4">
        <span class="text-zinc-500 text-sm">Ver como fica em tempo real:</span>
        <a :href="`/loja/${lojaId}?preview=1`" target="_blank"
           class="text-red-400 hover:text-red-300 text-sm font-semibold transition flex items-center gap-1">
          Abrir pré-visualização
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>

    <!-- ── ABA: CORES ── -->
    <div v-if="abaAtiva === 'cores'" class="space-y-5">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 space-y-4">
        <h3 class="text-sm font-bold text-zinc-200">🎨 Cores do tema</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div v-for="(campo, key) in camposCor" :key="key">
            <label class="text-xs text-zinc-500 mb-2 block">{{ campo.label }}</label>
            <div class="flex items-center gap-3">
              <input type="color" v-model="form[key]"
                class="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent flex-shrink-0" />
              <input v-model="form[key]" type="text" maxlength="7"
                class="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100
                       focus:outline-none focus:border-red-500 font-mono" />
            </div>
            <p class="text-[10px] text-zinc-600 mt-1">{{ campo.hint }}</p>
          </div>
        </div>

        <!-- Preview de cor ao vivo -->
        <div class="space-y-2 pt-2">
          <p class="text-xs text-zinc-500">Preview</p>
          <div class="flex gap-3 items-stretch h-10">
            <div class="flex-1 rounded-lg transition-all" :style="{ background: form.cor_primaria }"></div>
            <div class="flex-1 rounded-lg border border-zinc-700 transition-all" :style="{ background: form.cor_secundaria }"></div>
          </div>
          <!-- Mini template preview com as cores selecionadas -->
          <div class="relative rounded-xl overflow-hidden border border-zinc-800 mt-3" style="height:120px">
            <TemplateMiniPreview :template="previewTemplateCores" />
          </div>
        </div>
      </div>

      <!-- Modo dark/light -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h3 class="text-sm font-bold text-zinc-200 mb-3">🌙 Modo por defeito</h3>
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

      <!-- Sugestões de cor por template -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
        <h3 class="text-sm font-bold text-zinc-200 mb-3">💡 Sugestões para <span class="text-red-400">{{ templateAtual?.nome }}</span></h3>
        <div class="flex flex-wrap gap-2">
          <button v-for="sug in sugestoesCor" :key="sug.label"
            @click="aplicarSugestao(sug)"
            class="flex items-center gap-2 px-3 py-2 rounded-xl border border-zinc-700 hover:border-zinc-500 transition text-xs text-zinc-400 hover:text-zinc-200">
            <div class="w-3 h-3 rounded-full" :style="{ background: sug.primary }"></div>
            {{ sug.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Mensagem de erro -->
    <div v-if="erro" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">{{ erro }}</div>

    <!-- Botão guardar -->
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

    <!-- ── MODAL PREVIEW FULLSCREEN ── -->
    <Teleport to="body">
      <div v-if="previewModal"
           class="fixed inset-0 z-[200] flex items-center justify-center p-4"
           style="background:rgba(0,0,0,0.9);backdrop-filter:blur(14px)"
           @click.self="previewModal = null">
        <div class="w-full max-w-3xl max-h-[90vh] rounded-2xl overflow-hidden flex flex-col border border-zinc-800 shadow-2xl"
             style="background:#0a0a0b;animation:scaleIn 0.25s ease">

          <!-- Header modal -->
          <div class="flex items-center justify-between px-5 py-3 border-b border-zinc-800 flex-shrink-0">
            <div class="flex items-center gap-3">
              <div class="w-2.5 h-2.5 rounded-full"
                   :style="{ background: previewModal.primaryDefault, boxShadow: '0 0 8px '+previewModal.primaryDefault+'60' }"></div>
              <span class="text-sm font-bold text-zinc-100">{{ previewModal.nome }}</span>
              <span class="text-xs text-zinc-500">{{ previewModal.tag }}</span>
            </div>
            <div class="flex items-center gap-2">
              <!-- nav prev/next -->
              <button @click="navPreview(-1)"
                class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-xs flex items-center justify-center hover:text-zinc-200 transition">←</button>
              <span class="text-xs text-zinc-600 w-10 text-center">{{ idxPreview + 1 }} / {{ TEMPLATES.length }}</span>
              <button @click="navPreview(1)"
                class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-xs flex items-center justify-center hover:text-zinc-200 transition">→</button>
              <button @click="previewModal = null"
                class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-sm flex items-center justify-center hover:text-zinc-200 transition ml-1">×</button>
            </div>
          </div>

          <!-- Preview content — larger version usando mini preview escalado -->
          <div class="flex-1 overflow-y-auto scrollbar-hide">
            <!-- Hero escalado -->
            <div class="relative w-full" style="aspect-ratio:16/9">
              <TemplateMiniPreview :template="previewModal" style="position:absolute;inset:0;font-size:220%" />
            </div>

            <!-- Info card -->
            <div class="p-5 space-y-3">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="text-base font-bold text-zinc-100">{{ previewModal.nome }}</h3>
                  <p class="text-xs text-zinc-500 mt-1">{{ previewModal.descricao }}</p>
                </div>
                <span class="px-2 py-0.5 rounded-full text-xs font-semibold ml-4 flex-shrink-0"
                      :style="tagStyle(previewModal.tag)">{{ previewModal.tag }}</span>
              </div>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="cat in previewModal.categorias" :key="cat"
                      class="px-2 py-0.5 bg-zinc-800 text-zinc-400 text-xs rounded-full capitalize">
                  {{ cat === 'todos' ? 'Genérico' : cat }}
                </span>
              </div>
              <!-- Cor sugerida -->
              <div class="flex items-center gap-2 pt-1">
                <div class="w-3 h-3 rounded-full flex-shrink-0"
                     :style="{ background: previewModal.primaryDefault, boxShadow: '0 0 6px '+previewModal.primaryDefault+'50' }"></div>
                <span class="text-xs text-zinc-600 font-mono">Cor padrão: {{ previewModal.primaryDefault }}</span>
              </div>
            </div>
          </div>

          <!-- Footer modal -->
          <div class="px-5 py-3 border-t border-zinc-800 flex items-center justify-between flex-shrink-0">
            <div>
              <p class="text-xs text-zinc-500">Ideal para</p>
              <p class="text-xs text-zinc-300 mt-0.5">{{ previewModal.categorias.map(c => c === 'todos' ? 'Genérico' : c).join(', ') }}</p>
            </div>
            <button @click="selecionarDoModal"
              class="px-5 py-2 rounded-xl text-sm font-bold text-white transition hover:opacity-90"
              :style="{ background: previewModal.primaryDefault || '#dc2626', boxShadow: '0 4px 16px '+previewModal.primaryDefault+'40' }">
              Selecionar este template
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script>
import { TEMPLATES, CATEGORIAS_FILTRO } from '@/config/lojaTemplates'
import TemplateMiniPreview from '@/components/templates/TemplateMiniPreview.vue'
import api from '@/services/api'

const TAG_STYLES = {
  'Versátil':  { background:'rgba(220,38,38,0.12)',  color:'#f87171', border:'1px solid rgba(220,38,38,0.25)'   },
  'Luxury':    { background:'rgba(168,162,158,0.1)', color:'#d6d3d1', border:'1px solid rgba(168,162,158,0.2)'  },
  'Fashion':   { background:'rgba(184,134,11,0.1)',  color:'#d4a017', border:'1px solid rgba(184,134,11,0.25)'  },
  'Editorial': { background:'rgba(228,228,231,0.07)',color:'#a1a1aa', border:'1px solid rgba(228,228,231,0.18)' },
  'Food':      { background:'rgba(217,119,6,0.1)',   color:'#f59e0b', border:'1px solid rgba(217,119,6,0.25)'   },
  'Tech':      { background:'rgba(6,182,212,0.1)',   color:'#22d3ee', border:'1px solid rgba(6,182,212,0.25)'   },
  'Bold':      { background:'rgba(244,63,94,0.1)',   color:'#fb7185', border:'1px solid rgba(244,63,94,0.25)'   },
  'Nature':    { background:'rgba(22,163,74,0.1)',   color:'#4ade80', border:'1px solid rgba(22,163,74,0.25)'   },
  'Premium':   { background:'rgba(201,168,76,0.1)',  color:'#d4a843', border:'1px solid rgba(201,168,76,0.25)'  },
  'Sport':     { background:'rgba(249,115,22,0.1)',  color:'#fb923c', border:'1px solid rgba(249,115,22,0.25)'  },
}

export default {
  name: 'BackofficeTemplates',
  components: { TemplateMiniPreview },
  props: { lojaId: [String, Number] },

  data () {
    return {
      TEMPLATES,
      abaAtiva: 'template',
      tabs: [
        { id: 'template', label: '📐 Template' },
        { id: 'cores',    label: '🎨 Cores & Modo' },
      ],
      filtroCategoria: null,
      categoriasFiltro: CATEGORIAS_FILTRO,
      loading: false,
      erro: '',
      previewModal: null,
      form: {
        template_id:    'classico',
        cor_primaria:   '#dc2626',
        cor_secundaria: '#1c1c1e',
        dark_mode:      true,
      },
      camposCor: {
        cor_primaria:   { label: 'Cor primária',   hint: 'Botões, destaques, badges, preços'   },
        cor_secundaria: { label: 'Cor secundária', hint: 'Fundos, backgrounds secundários'     },
      },
      sugestoesCor: [],
    }
  },

  computed: {
    templatesFiltrados () {
      if (!this.filtroCategoria) return TEMPLATES
      return TEMPLATES.filter(t =>
        t.categorias.includes('todos') || t.categorias.includes(this.filtroCategoria)
      )
    },

    templateAtual () {
      return TEMPLATES.find(t => t.id === this.form.template_id) || TEMPLATES[0]
    },

    idxPreview () {
      if (!this.previewModal) return 0
      return TEMPLATES.findIndex(t => t.id === this.previewModal.id)
    },

    // Versão do template com as cores actuais para preview na aba Cores
    previewTemplateCores () {
      return {
        ...this.templateAtual,
        primaryDefault:    this.form.cor_primaria,
        secundariaDefault: this.form.cor_secundaria,
      }
    },
  },

  watch: {
    templateAtual: {
      immediate: true,
      handler (tpl) {
        if (!tpl) return
        this.sugestoesCor = [
          { label: 'Padrão',    primary: tpl.primaryDefault,    secundaria: tpl.secundariaDefault },
          { label: 'Quente',    primary: '#e11d48',              secundaria: '#0f0a0b' },
          { label: 'Frio',      primary: '#06b6d4',              secundaria: '#020617' },
          { label: 'Terra',     primary: '#d97706',              secundaria: '#1a1208' },
          { label: 'Verde',     primary: '#16a34a',              secundaria: '#051a0a' },
          { label: 'Roxo',      primary: '#7c3aed',              secundaria: '#0d0b14' },
        ]
      },
    },
  },

  async created () {
    await this.fetchAparencia()
  },

  methods: {
    tagStyle (tag) {
      return TAG_STYLES[tag] || { background:'rgba(255,255,255,0.06)', color:'#a1a1aa', border:'1px solid rgba(255,255,255,0.1)' }
    },

    abrirPreview (tpl) {
      this.previewModal = tpl
    },

    navPreview (dir) {
      const idx = (this.idxPreview + dir + TEMPLATES.length) % TEMPLATES.length
      this.previewModal = TEMPLATES[idx]
    },

    selecionarDoModal () {
      if (!this.previewModal) return
      this.form.template_id    = this.previewModal.id
      this.form.cor_primaria   = this.previewModal.primaryDefault
      this.form.cor_secundaria = this.previewModal.secundariaDefault
      this.previewModal = null
      this.abaAtiva = 'cores'
    },

    aplicarSugestao (sug) {
      this.form.cor_primaria   = sug.primary
      if (sug.secundaria) this.form.cor_secundaria = sug.secundaria
    },

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
      this.loading = true
      this.erro    = ''
      try {
        await api.patch(`/app/loja/${this.lojaId}/aparencia/`, this.form)
        localStorage.setItem(`loja_template_${this.lojaId}`, JSON.stringify({
          templateId:    this.form.template_id,
          corPrimaria:   this.form.cor_primaria,
          corSecundaria: this.form.cor_secundaria,
          darkMode:      this.form.dark_mode,
        }))
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao guardar.'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1); }
}
</style>
