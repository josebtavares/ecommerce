<!-- BackofficeTemplates.vue — Aparência da loja com previews ricos -->
<template>
  <div class="space-y-6 max-w-6xl">

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
        <font-awesome-icon :icon="['fas', tab.icon]" class="mr-1.5" />{{ tab.label }}
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
                        opacity-0 group-hover:opacity-100 pointer-coarse:opacity-100 pointer-coarse:bg-transparent pointer-coarse:items-end pointer-coarse:justify-end pointer-coarse:p-2 pointer-coarse:backdrop-blur-none transition-opacity duration-200">
              <button @click.stop="abrirPreview(tpl)"
                class="px-3 py-1.5 rounded-lg bg-white/15 pointer-coarse:bg-black/70 border border-white/20 text-white text-xs font-semibold backdrop-blur-md hover:bg-white/25 transition">
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
        <a :href="previewUrl(form.template_id, form.cor_primaria, form.cor_secundaria, form.dark_mode)" target="_blank"
           class="text-red-400 hover:text-red-300 text-sm font-semibold transition flex items-center gap-1">
          Abrir pré-visualização
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>

    <!-- ── ABA: CORES & MODO ── -->
    <div v-if="abaAtiva === 'cores'" class="grid grid-cols-1 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)] gap-5 items-start">

      <!-- Controlos -->
      <div class="space-y-4">
        <!-- Template actual -->
        <div class="flex items-center gap-3 p-3 bg-zinc-900 rounded-2xl border border-zinc-800">
          <div class="w-14 h-9 rounded-lg overflow-hidden flex-shrink-0 border border-zinc-800">
            <TemplateMiniPreview :template="previewTemplateCores" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-[10px] uppercase tracking-wider text-zinc-500">Template</p>
            <p class="text-sm font-bold text-zinc-100 truncate">{{ templateAtual.nome }}</p>
          </div>
          <button @click="abaAtiva = 'template'" class="text-xs text-zinc-400 hover:text-zinc-200 transition">Trocar</button>
        </div>

        <!-- Cores -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-zinc-200"><font-awesome-icon :icon="['fas', 'palette']" class="mr-1.5 text-zinc-500" />Cores</h3>
            <button @click="reporPadrao"
              class="text-[11px] text-zinc-500 hover:text-zinc-200 transition"><font-awesome-icon :icon="['fas', 'rotate-left']" class="mr-1" />Repor padrão do template</button>
          </div>

          <div v-for="(campo, key) in camposCorVisiveis" :key="key">
            <label class="text-xs text-zinc-400 mb-1.5 block font-medium">{{ campo.label }}</label>
            <div class="flex items-center gap-2">
              <label class="relative w-10 h-10 rounded-xl overflow-hidden border border-zinc-700 cursor-pointer flex-shrink-0"
                     :style="{ background: form[key] }">
                <input type="color" :value="form[key]" @input="form[key] = $event.target.value; textoCor[key] = $event.target.value"
                       class="absolute inset-0 opacity-0 cursor-pointer" />
              </label>
              <input v-model="textoCor[key]" @input="onTextoCor(key)" @blur="textoCor[key] = form[key]"
                type="text" maxlength="7" spellcheck="false"
                :class="['flex-1 min-w-0 px-3 py-2 bg-zinc-800 border rounded-xl text-sm text-zinc-100 focus:outline-none font-mono uppercase',
                         corValida(textoCor[key]) ? 'border-zinc-700 focus:border-red-500' : 'border-red-500/70']" />
            </div>
            <p class="text-[10px] mt-1" :class="corValida(textoCor[key]) ? 'text-zinc-600' : 'text-red-400'">
              {{ corValida(textoCor[key]) ? campo.hint : 'Formato inválido — usa #RRGGBB (ex: #E4572E)' }}
            </p>
            <p v-if="key === 'cor_primaria' && contrasteFraco"
               class="text-[10px] mt-1 text-amber-400">
              <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="mr-1" />Pouco contraste com o fundo {{ form.dark_mode ? 'escuro' : 'claro' }} — textos e botões podem ficar difíceis de ler.
            </p>
          </div>

          <p v-if="!templateAtual.usaCorSecundaria"
             class="text-[10px] text-zinc-600 leading-relaxed border-t border-zinc-800 pt-3">
            Este template usa apenas a cor primária — o fundo é definido pelo próprio design e pelo modo escuro/claro.
          </p>

          <!-- Paletas sugeridas -->
          <div class="border-t border-zinc-800 pt-3">
            <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Paletas sugeridas</p>
            <div class="grid grid-cols-3 gap-2">
              <button v-for="sug in sugestoesCor" :key="sug.label" @click="aplicarSugestao(sug)"
                :class="['group flex flex-col items-center gap-1.5 p-2 rounded-xl border transition',
                         sugestaoActiva(sug) ? 'border-red-500/60 bg-red-500/5' : 'border-zinc-800 hover:border-zinc-600']">
                <span class="flex">
                  <span class="w-5 h-5 rounded-full border-2 border-zinc-900" :style="{ background: sug.primary }"></span>
                  <span v-if="templateAtual.usaCorSecundaria" class="w-5 h-5 -ml-2 rounded-full border-2 border-zinc-900" :style="{ background: sug.secundaria }"></span>
                </span>
                <span class="text-[10px] text-zinc-400 group-hover:text-zinc-200">{{ sug.label }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Modo por defeito -->
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <h3 class="text-sm font-bold text-zinc-200 mb-3"><font-awesome-icon :icon="['fas', 'circle-half-stroke']" class="mr-1.5 text-zinc-500" />Modo por defeito</h3>
          <div class="grid grid-cols-2 gap-2">
            <button v-for="m in [[true, 'moon', 'Escuro'], [false, 'sun', 'Claro']]" :key="String(m[0])"
              @click="form.dark_mode = m[0]"
              :class="['py-3 rounded-xl border text-sm font-semibold transition flex items-center justify-center gap-2',
                       form.dark_mode === m[0] ? 'bg-zinc-800 border-red-500/60 text-zinc-100' : 'border-zinc-700 text-zinc-500 hover:border-zinc-600 hover:text-zinc-300']">
              <font-awesome-icon :icon="['fas', m[1]]" /> {{ m[2] }}
            </button>
          </div>
          <p class="text-[10px] text-zinc-600 mt-2 leading-relaxed">
            É o modo com que a loja abre. O visitante pode alternar na página; se mudares aqui, a tua escolha volta a prevalecer.
          </p>
        </div>
      </div>

      <!-- Preview ao vivo -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-3 lg:sticky lg:top-4">
        <div class="flex items-center justify-between gap-2 mb-3 px-1">
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            <span class="text-xs font-semibold text-zinc-300">Pré-visualização ao vivo</span>
          </div>
          <div class="flex rounded-lg bg-zinc-950 border border-zinc-800 p-0.5">
            <button v-for="d in [['desktop','desktop'],['mobile','mobile-screen']]" :key="d[0]"
              @click="coresDevice = d[0]" :title="d[0] === 'desktop' ? 'Desktop' : 'Mobile'"
              :class="['px-2.5 py-1 rounded-md text-xs transition',
                       coresDevice === d[0] ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
              <font-awesome-icon :icon="['fas', d[1]]" />
            </button>
          </div>
        </div>
        <div class="h-[60vh] min-h-[380px] rounded-xl bg-zinc-950">
          <TemplatePreviewFrame
            :src="coresPreviewSrc"
            :device="coresDevice"
            :tema="{ corPrimaria: form.cor_primaria, corSecundaria: form.cor_secundaria, darkMode: form.dark_mode }"
          />
        </div>
        <p class="text-[10px] text-zinc-600 mt-2 px-1">As alterações aparecem aqui de imediato, mas só ficam visíveis aos clientes depois de guardares.</p>
      </div>
    </div>

    <!-- Mensagem de erro -->
    <div v-if="erro" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">{{ erro }}</div>

    <!-- Barra guardar -->
    <div class="sticky bottom-0 z-10 -mx-1 px-1 py-3 flex items-center justify-end gap-3 flex-wrap"
         :class="temAlteracoes ? 'bg-gradient-to-t from-zinc-950 via-zinc-950/95 to-transparent' : ''">
      <span v-if="temAlteracoes" class="text-xs text-amber-400 flex items-center gap-1.5 mr-auto">
        <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Alterações por guardar
      </span>
      <span v-else-if="guardadoEm" class="text-xs text-green-500 mr-auto"><font-awesome-icon :icon="['fas', 'check']" class="mr-1" />Guardado</span>
      <button v-if="temAlteracoes" @click="descartar" :disabled="loading"
        class="px-4 py-2.5 rounded-xl text-sm font-semibold text-zinc-400 hover:text-zinc-200 border border-zinc-700 hover:border-zinc-500 transition">
        Descartar
      </button>
      <button @click="guardar" :disabled="loading || !temAlteracoes || !formValido"
        :class="['px-6 py-2.5 rounded-xl text-sm font-bold transition flex items-center gap-2',
                 loading || !temAlteracoes || !formValido ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
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
        <div class="w-full max-w-7xl h-[92vh] rounded-2xl overflow-hidden flex flex-col border border-zinc-800 shadow-2xl"
             style="background:#0a0a0b;animation:scaleIn 0.25s ease">

          <!-- Header modal -->
          <div class="flex items-center justify-between gap-3 px-5 py-3 border-b border-zinc-800 flex-shrink-0 flex-wrap">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                   :style="{ background: previewCores.c1, boxShadow: '0 0 8px '+previewCores.c1+'60' }"></div>
              <span class="text-sm font-bold text-zinc-100 truncate">{{ previewModal.nome }}</span>
              <span class="text-xs text-zinc-500 hidden sm:inline">{{ previewModal.tag }}</span>
            </div>

            <!-- Dispositivo + modo -->
            <div class="flex items-center gap-2">
              <div class="flex rounded-lg bg-zinc-900 border border-zinc-800 p-0.5">
                <button v-for="d in [['desktop','desktop','Desktop'],['mobile','mobile-screen','Mobile']]" :key="d[0]"
                  @click="previewDevice = d[0]"
                  :class="['px-2.5 py-1 rounded-md text-xs font-semibold transition',
                           previewDevice === d[0] ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
                  <font-awesome-icon :icon="['fas', d[1]]" class="mr-1" />{{ d[2] }}
                </button>
              </div>
              <div class="flex rounded-lg bg-zinc-900 border border-zinc-800 p-0.5">
                <button v-for="m in [[true,'moon'],[false,'sun']]" :key="String(m[0])"
                  @click="previewDark = m[0]" :title="m[0] ? 'Escuro' : 'Claro'"
                  :class="['px-2.5 py-1 rounded-md text-xs transition',
                           previewDark === m[0] ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
                  <font-awesome-icon :icon="['fas', m[1]]" />
                </button>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <!-- nav prev/next -->
              <button @click="navPreview(-1)"
                class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-xs flex items-center justify-center hover:text-zinc-200 transition"><font-awesome-icon :icon="['fas', 'chevron-left']" /></button>
              <span class="text-xs text-zinc-600 w-10 text-center">{{ idxPreview + 1 }} / {{ TEMPLATES.length }}</span>
              <button @click="navPreview(1)"
                class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-xs flex items-center justify-center hover:text-zinc-200 transition"><font-awesome-icon :icon="['fas', 'chevron-right']" /></button>
              <button @click="previewModal = null"
                class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-sm flex items-center justify-center hover:text-zinc-200 transition ml-1">×</button>
            </div>
          </div>

          <!-- Preview real: a loja verdadeira, com este template, num iframe -->
          <div class="flex-1 min-h-0 p-3 sm:p-5 bg-zinc-950">
            <TemplatePreviewFrame :src="previewSrc" :device="previewDevice" />
          </div>

          <!-- Footer modal -->
          <div class="px-5 py-3 border-t border-zinc-800 flex items-center justify-between gap-3 flex-shrink-0 flex-wrap">
            <div class="min-w-0">
              <p class="text-xs text-zinc-300 truncate">{{ previewModal.descricao }}</p>
              <p class="text-[11px] text-zinc-500 mt-0.5">
                Com os produtos reais da tua loja ·
                {{ previewModal.id === form.template_id ? 'as tuas cores actuais' : 'cores padrão do template' }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <a :href="previewSrc" target="_blank"
                 class="px-3 py-2 rounded-xl text-xs font-semibold text-zinc-400 border border-zinc-700 hover:text-zinc-200 hover:border-zinc-500 transition">
                Abrir em nova aba <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="ml-1" />
              </a>
              <button @click="selecionarDoModal"
                class="px-5 py-2 rounded-xl text-sm font-bold text-white transition hover:opacity-90"
                :style="{ background: previewCores.c1, boxShadow: '0 4px 16px '+previewCores.c1+'40' }">
                Selecionar este template
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script>
import { TEMPLATES, CATEGORIAS_FILTRO } from '@/config/lojaTemplates'
import TemplateMiniPreview from '@/components/templates/TemplateMiniPreview.vue'
import TemplatePreviewFrame from '@/components/templates/TemplatePreviewFrame.vue'
import api from '@/services/api'
import { toast } from 'vue3-toastify'

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
  components: { TemplateMiniPreview, TemplatePreviewFrame },
  props: { lojaId: [String, Number] },

  data () {
    return {
      TEMPLATES,
      abaAtiva: 'template',
      tabs: [
        { id: 'template', label: 'Template',     icon: 'pen-ruler' },
        { id: 'cores',    label: 'Cores & Modo', icon: 'palette' },
      ],
      filtroCategoria: null,
      categoriasFiltro: CATEGORIAS_FILTRO,
      loading: false,
      erro: '',
      previewModal: null,
      previewDevice: 'desktop',
      previewDark: true,
      coresDevice: 'desktop',
      form: {
        template_id:    'classico',
        cor_primaria:   '#dc2626',
        cor_secundaria: '#1c1c1e',
        dark_mode:      true,
      },
      // texto dos inputs de cor — só passa para o form quando é um hex válido
      textoCor: { cor_primaria: '#dc2626', cor_secundaria: '#1c1c1e' },
      // último estado guardado na BD (para detectar alterações)
      guardado: null,
      guardadoEm: null,
      camposCor: {
        cor_primaria:   { label: 'Cor primária',   hint: 'Botões, destaques, preços e ícones.' },
        cor_secundaria: { label: 'Cor secundária', hint: 'Cor de fundo da loja no modo escuro.' },
      },
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

    // Template seleccionado → cores do formulário; outro → cores padrão dele
    previewCores () {
      const t = this.previewModal
      if (!t) return { c1: '#dc2626', c2: '#1c1c1e' }
      if (t.id === this.form.template_id) return { c1: this.form.cor_primaria, c2: this.form.cor_secundaria }
      return { c1: t.primaryDefault, c2: t.secundariaDefault }
    },

    previewSrc () {
      if (!this.previewModal) return ''
      return this.previewUrl(this.previewModal.id, this.previewCores.c1, this.previewCores.c2, this.previewDark)
    },

    // Só muda quando muda o template — cores e modo vão por postMessage, sem recarregar
    coresPreviewSrc () {
      return this.previewUrl(this.form.template_id, this.form.cor_primaria, this.form.cor_secundaria, this.form.dark_mode, true)
    },

    // Versão do template com as cores actuais (miniatura na aba Cores)
    previewTemplateCores () {
      return {
        ...this.templateAtual,
        primaryDefault:    this.form.cor_primaria,
        secundariaDefault: this.form.cor_secundaria,
      }
    },

    camposCorVisiveis () {
      if (this.templateAtual.usaCorSecundaria) return this.camposCor
      return { cor_primaria: this.camposCor.cor_primaria }
    },

    sugestoesCor () {
      const tpl = this.templateAtual
      return [
        { label: 'Padrão', primary: tpl.primaryDefault, secundaria: tpl.secundariaDefault },
        { label: 'Tomate', primary: '#e4572e',          secundaria: '#14110f' },
        { label: 'Rubi',   primary: '#e11d48',          secundaria: '#0f0a0b' },
        { label: 'Oceano', primary: '#0891b2',          secundaria: '#04131a' },
        { label: 'Âmbar',  primary: '#d97706',          secundaria: '#1a1208' },
        { label: 'Folha',  primary: '#16a34a',          secundaria: '#06140a' },
        { label: 'Ameixa', primary: '#7c3aed',          secundaria: '#0d0b14' },
        { label: 'Ouro',   primary: '#c9a84c',          secundaria: '#0b0905' },
        { label: 'Grafite',primary: '#71717a',          secundaria: '#0c0c0e' },
      ]
    },

    formValido () {
      return this.corValida(this.textoCor.cor_primaria) && this.corValida(this.textoCor.cor_secundaria)
    },

    temAlteracoes () {
      if (!this.guardado) return false
      return Object.keys(this.form).some(k => this.form[k] !== this.guardado[k])
    },

    // Contraste (WCAG) da cor primária com o fundo típico do modo escolhido
    contrasteFraco () {
      const fundo = this.form.dark_mode
        ? (this.templateAtual.usaCorSecundaria ? this.form.cor_secundaria : '#111111')
        : '#f7f7f7'
      return contraste(this.form.cor_primaria, fundo) < 2.2
    },
  },

  async created () {
    await this.fetchAparencia()
  },

  beforeUnmount () {
    window.removeEventListener('beforeunload', this.avisoSair)
  },

  mounted () {
    window.addEventListener('beforeunload', this.avisoSair)
  },

  methods: {
    tagStyle (tag) {
      return TAG_STYLES[tag] || { background:'rgba(255,255,255,0.06)', color:'#a1a1aa', border:'1px solid rgba(255,255,255,0.1)' }
    },

    abrirPreview (tpl) {
      this.previewDark  = tpl.id === this.form.template_id ? this.form.dark_mode : tpl.darkDefault !== false
      this.previewModal = tpl
    },

    previewUrl (tplId, c1, c2, dark, semCores = false) {
      const q = new URLSearchParams({ preview: '1', tpl: tplId })
      if (!semCores) {
        q.set('c1', (c1 || '').replace('#', ''))
        q.set('c2', (c2 || '').replace('#', ''))
        q.set('dark', dark ? '1' : '0')
      }
      return `/loja/${this.lojaId}?${q}`
    },

    navPreview (dir) {
      const idx = (this.idxPreview + dir + TEMPLATES.length) % TEMPLATES.length
      this.abrirPreview(TEMPLATES[idx])
    },

    selecionarDoModal () {
      if (!this.previewModal) return
      const cores = this.previewCores
      this.form.template_id = this.previewModal.id
      this.setCor('cor_primaria', cores.c1)
      this.setCor('cor_secundaria', cores.c2)
      this.form.dark_mode   = this.previewDark
      this.previewModal = null
      this.abaAtiva = 'cores'
    },

    // ── Cores ───────────────────────────────────────────────
    corValida (v) {
      return /^#[0-9a-f]{6}$/i.test(v || '')
    },

    normalizarCor (v, fallback) {
      let s = String(v || '').trim()
      if (s && s[0] !== '#') s = '#' + s
      if (/^#[0-9a-f]{3}$/i.test(s)) s = '#' + s.slice(1).split('').map(c => c + c).join('')
      return this.corValida(s) ? s.toLowerCase() : fallback
    },

    setCor (key, valor) {
      const cor = this.normalizarCor(valor, this.form[key])
      this.form[key]     = cor
      this.textoCor[key] = cor
    },

    onTextoCor (key) {
      let v = this.textoCor[key].trim()
      if (v && v[0] !== '#') { v = '#' + v; this.textoCor[key] = v }
      if (this.corValida(v)) this.form[key] = v.toLowerCase()
    },

    aplicarSugestao (sug) {
      this.setCor('cor_primaria', sug.primary)
      if (this.templateAtual.usaCorSecundaria && sug.secundaria) this.setCor('cor_secundaria', sug.secundaria)
    },

    sugestaoActiva (sug) {
      const prim = sug.primary?.toLowerCase() === this.form.cor_primaria
      if (!this.templateAtual.usaCorSecundaria) return prim
      return prim && sug.secundaria?.toLowerCase() === this.form.cor_secundaria
    },

    reporPadrao () {
      const t = this.templateAtual
      this.setCor('cor_primaria', t.primaryDefault)
      this.setCor('cor_secundaria', t.secundariaDefault)
      this.form.dark_mode = t.darkDefault !== false
    },

    descartar () {
      if (!this.guardado) return
      this.form = { ...this.guardado }
      this.textoCor = { cor_primaria: this.form.cor_primaria, cor_secundaria: this.form.cor_secundaria }
      this.erro = ''
    },

    avisoSair (e) {
      if (!this.temAlteracoes) return
      e.preventDefault()
      e.returnValue = ''
    },

    // ── API ─────────────────────────────────────────────────
    async fetchAparencia () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/`)
        this.form = {
          template_id:    TEMPLATES.some(t => t.id === data.template_id) ? data.template_id : 'classico',
          cor_primaria:   this.normalizarCor(data.cor_primaria,   '#dc2626'),
          cor_secundaria: this.normalizarCor(data.cor_secundaria, '#1c1c1e'),
          dark_mode:      data.dark_mode !== undefined ? !!data.dark_mode : true,
        }
        this.textoCor = { cor_primaria: this.form.cor_primaria, cor_secundaria: this.form.cor_secundaria }
        this.guardado = { ...this.form }
      } catch (e) {
        console.error(e)
        this.erro = 'Não foi possível carregar a aparência da loja.'
      }
    },

    async guardar () {
      if (!this.formValido) {
        this.erro = 'Corrige as cores inválidas antes de guardar.'
        return
      }
      this.loading = true
      this.erro    = ''
      try {
        const { data } = await api.patch(`/app/loja/${this.lojaId}/aparencia/`, this.form)
        // usa o que o servidor confirmou como estado guardado
        this.form = {
          template_id:    data.template_id,
          cor_primaria:   data.cor_primaria,
          cor_secundaria: data.cor_secundaria,
          dark_mode:      data.dark_mode,
        }
        this.textoCor = { cor_primaria: this.form.cor_primaria, cor_secundaria: this.form.cor_secundaria }
        this.guardado   = { ...this.form }
        this.guardadoEm = Date.now()
        localStorage.setItem(`loja_template_${this.lojaId}`, JSON.stringify({
          templateId:    this.form.template_id,
          corPrimaria:   this.form.cor_primaria,
          corSecundaria: this.form.cor_secundaria,
          darkMode:      this.form.dark_mode,
        }))
        toast.success('Aparência guardada — já está visível na loja.')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao guardar.'
        toast.error(this.erro)
      } finally {
        this.loading = false
      }
    },
  },
}

// ── Contraste WCAG entre duas cores hex ─────────────────────
function luminancia (hex) {
  const n = parseInt(hex.slice(1), 16)
  return [n >> 16, (n >> 8) & 255, n & 255]
    .map(c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 })
    .reduce((acc, c, i) => acc + c * [0.2126, 0.7152, 0.0722][i], 0)
}

function contraste (a, b) {
  if (!/^#[0-9a-f]{6}$/i.test(a) || !/^#[0-9a-f]{6}$/i.test(b)) return 21
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x)
  return (l1 + 0.05) / (l2 + 0.05)
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
