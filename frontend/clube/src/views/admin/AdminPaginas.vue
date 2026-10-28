<!-- AdminPaginas.vue — editar as páginas do rodapé (Ajuda, Contacto, FAQ, Termos, Privacidade, Devoluções, Entregas) -->
<template>
  <div class="space-y-5">
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Páginas & Ajuda</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Conteúdo dos links "Suporte" e "Legal" do rodapé — cada página tem também o seu endereço (ex.: /termos).</p>
      </div>
    </div>

    <div v-if="loading" class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-4">
      <div class="space-y-2"><div v-for="n in 5" :key="n" class="h-12 bg-zinc-900 rounded-xl animate-pulse"></div></div>
      <div class="h-96 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <p v-else-if="erroCarregar" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">{{ erroCarregar }}</p>

    <div v-else class="grid grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)] gap-4 items-start">

      <!-- Lista de páginas -->
      <nav class="flex lg:flex-col gap-2 overflow-x-auto pb-1 lg:pb-0 lg:sticky lg:top-4">
        <template v-for="sec in seccoes" :key="sec.key">
          <p class="hidden lg:block text-[10px] font-bold uppercase tracking-wider text-zinc-600 px-1 mt-2 first:mt-0">{{ sec.label }}</p>
          <button v-for="p in paginasDaSeccao(sec.key)" :key="p.slug" @click="selecionar(p.slug)"
            :class="['flex items-center gap-2.5 px-3 py-2.5 rounded-xl border text-sm font-semibold text-left transition whitespace-nowrap flex-shrink-0',
                     slugActivo === p.slug ? 'bg-zinc-800 border-red-500/50 text-zinc-100' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700']">
            <font-awesome-icon :icon="['fas', ICONES[p.slug] || 'file-lines']" class="w-3.5 h-3.5 flex-shrink-0" fixed-width />
            <span class="flex-1 truncate">{{ p.titulo }}</span>
            <span v-if="sujas.has(p.slug)" class="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" title="Alterações por guardar"></span>
            <span v-else-if="!p.ativo" class="px-1.5 py-0.5 bg-zinc-700/60 text-zinc-400 text-[9px] rounded font-bold">OFF</span>
          </button>
        </template>
      </nav>

      <!-- Editor -->
      <div v-if="form" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden">
        <!-- Cabeçalho do editor -->
        <div class="flex items-center justify-between gap-3 px-5 py-3.5 border-b border-zinc-800 flex-wrap">
          <div class="flex items-center gap-2 min-w-0">
            <font-awesome-icon :icon="['fas', ICONES[form.slug] || 'file-lines']" class="w-4 h-4 text-red-400 flex-shrink-0" />
            <span class="text-sm font-bold text-zinc-100 truncate">{{ form.titulo || '—' }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500 uppercase font-bold">{{ form.seccao }}</span>
          </div>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <span class="text-xs" :class="form.ativo ? 'text-green-400' : 'text-zinc-500'">{{ form.ativo ? 'Visível na home' : 'Escondida' }}</span>
            <button type="button" role="switch" :aria-checked="form.ativo" @click="form.ativo = !form.ativo"
              :class="['relative w-10 h-6 rounded-full transition', form.ativo ? 'bg-green-600' : 'bg-zinc-700']">
              <span :class="['absolute top-1 w-4 h-4 rounded-full bg-white transition-all', form.ativo ? 'left-5' : 'left-1']"></span>
            </button>
          </label>
        </div>

        <div class="p-5 space-y-5">
          <!-- Título -->
          <div>
            <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Título</label>
            <input v-model="form.titulo" maxlength="120"
              class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
          </div>

          <!-- Contacto: os contactos são os da plataforma (Definições), os mesmos do rodapé -->
          <div v-if="form.slug === 'contacto'" class="flex items-start gap-3 px-4 py-3 rounded-xl bg-zinc-800/50 text-sm text-zinc-300">
            <font-awesome-icon :icon="['fas', 'circle-info']" class="w-4 h-4 text-zinc-400 mt-0.5" />
            <p>
              O email, telefone, WhatsApp, morada e horário editam-se em
              <router-link to="/admin/plataforma" class="font-semibold text-red-400 hover:text-red-300">Definições</router-link>
              — são os mesmos do rodapé de todas as páginas.
            </p>
          </div>

          <!-- FAQ: perguntas -->
          <div v-if="form.slug === 'faq'" class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-xs text-zinc-400 font-medium">Perguntas ({{ form.dados.perguntas.length }})</label>
              <button @click="adicionarPergunta" class="text-xs font-semibold text-red-400 hover:text-red-300">+ Adicionar pergunta</button>
            </div>
            <p v-if="!form.dados.perguntas.length" class="text-xs text-zinc-600 py-4 text-center border border-dashed border-zinc-800 rounded-xl">
              Sem perguntas. Adiciona a primeira.
            </p>
            <div v-for="(q, i) in form.dados.perguntas" :key="q._id"
                 class="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3 space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-bold text-zinc-600 w-5">{{ i + 1 }}.</span>
                <input v-model="q.pergunta" placeholder="Pergunta" maxlength="300"
                  class="flex-1 min-w-0 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
                <div class="flex gap-1 flex-shrink-0">
                  <button @click="moverPergunta(i, -1)" :disabled="i === 0" title="Subir"
                    class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-xs disabled:opacity-30">↑</button>
                  <button @click="moverPergunta(i, 1)" :disabled="i === form.dados.perguntas.length - 1" title="Descer"
                    class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-xs disabled:opacity-30">↓</button>
                  <button @click="form.dados.perguntas.splice(i, 1)" title="Remover"
                    class="w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm">×</button>
                </div>
              </div>
              <textarea v-model="q.resposta" rows="2" placeholder="Resposta" maxlength="4000"
                class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500 resize-y"></textarea>
            </div>
          </div>

          <!-- Texto livre -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs text-zinc-400 font-medium">
                {{ form.slug === 'faq' ? 'Texto de introdução (opcional)' : form.slug === 'contacto' ? 'Mensagem (opcional)' : 'Conteúdo' }}
              </label>
              <span class="text-[10px] text-zinc-600">{{ form.conteudo.length.toLocaleString('pt-PT') }} caracteres</span>
            </div>
            <textarea v-model="form.conteudo" :rows="form.slug === 'faq' || form.slug === 'contacto' ? 3 : 14"
              class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono leading-relaxed focus:outline-none focus:border-red-500 resize-y"></textarea>
            <p class="text-[10px] text-zinc-600 mt-1.5 leading-relaxed">
              Formatação: linha em branco separa parágrafos · <code class="text-zinc-400">## Título</code> para subtítulos · <code class="text-zinc-400">- item</code> para listas.
            </p>
          </div>

          <p v-if="form.data_atualizacao" class="text-[10px] text-zinc-600">
            Última actualização: {{ formatarData(form.data_atualizacao) }}<template v-if="form.atualizado_por"> por {{ form.atualizado_por }}</template>
          </p>

          <p v-if="erro" class="px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400">{{ erro }}</p>
        </div>

        <!-- Acções -->
        <div class="flex items-center justify-end gap-2 px-5 py-3 border-t border-zinc-800 flex-wrap">
          <span v-if="temAlteracoes" class="text-xs text-amber-400 mr-auto flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Alterações por guardar
          </span>
          <button @click="preview = true"
            class="px-4 py-2 rounded-xl text-sm font-semibold text-zinc-300 border border-zinc-700 hover:border-zinc-500 transition">
            <font-awesome-icon :icon="['fas', 'eye']" class="mr-1" /> Pré-visualizar
          </button>
          <button v-if="temAlteracoes" @click="descartar" :disabled="saving"
            class="px-4 py-2 rounded-xl text-sm font-semibold text-zinc-400 hover:text-zinc-200 transition">
            Descartar
          </button>
          <button @click="guardar" :disabled="saving || !temAlteracoes || !form.titulo.trim()"
            :class="['px-5 py-2 rounded-xl text-sm font-bold transition',
                     saving || !temAlteracoes || !form.titulo.trim() ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white']">
            {{ saving ? 'A guardar…' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Pré-visualização: o mesmo popup que aparece na home -->
    <PaginaInfoModal v-if="preview && form" :pagina="paginaPreview" :isDark="true" @close="preview = false" />
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'
import PaginaInfoModal from '@/components/paginas/PaginaInfoModal.vue'

// ícones Font Awesome (solid) por página
const ICONES = { ajuda: 'life-ring', contacto: 'envelope', faq: 'circle-question', termos: 'file-contract', privacidade: 'lock',
                 devolucoes: 'rotate-left', entregas: 'truck-fast' }

let uid = 0

export default {
  name: 'AdminPaginas',
  components: { PaginaInfoModal },

  data () {
    return {
      ICONES,
      contactos: {},        // da plataforma — só para a pré-visualização da página Contacto
      seccoes: [{ key: 'suporte', label: 'Suporte' }, { key: 'legal', label: 'Legal' }],
      paginas: [],          // estado guardado no servidor
      rascunhos: {},        // slug → form em edição
      slugActivo: null,
      loading: true,
      saving: false,
      erro: '',
      erroCarregar: '',
      preview: false,
    }
  },

  computed: {
    form () { return this.rascunhos[this.slugActivo] || null },

    original () { return this.paginas.find(p => p.slug === this.slugActivo) },

    temAlteracoes () { return this.estaSuja(this.slugActivo) },

    sujas () { return new Set(this.paginas.map(p => p.slug).filter(s => this.estaSuja(s))) },

    paginaPreview () {
      if (!this.form) return null
      return { ...this.form, dados: this.form.slug === 'contacto' ? this.contactos : this.payloadDados(this.form) }
    },
  },

  async created () {
    await this.carregar()
    window.addEventListener('beforeunload', this.avisoSair)
  },

  beforeUnmount () {
    window.removeEventListener('beforeunload', this.avisoSair)
  },

  methods: {
    async carregar () {
      this.loading = true
      try {
        const { data } = await api.get('/app/admin/paginas/')
        this.paginas = data
        this.rascunhos = Object.fromEntries(data.map(p => [p.slug, this.paraForm(p)]))
        this.slugActivo = this.slugActivo || this.paginasDaSeccao('suporte')[0]?.slug || data[0]?.slug
        api.get('/app/plataforma/publica/').then(r => { this.contactos = r.data.contactos }).catch(() => {})
      } catch (e) {
        this.erroCarregar = e.response?.data?.detail || 'Não foi possível carregar as páginas.'
      } finally {
        this.loading = false
      }
    },

    paginasDaSeccao (sec) {
      return this.paginas.filter(p => p.seccao === sec).sort((a, b) => a.ordem - b.ordem)
    },

    paraForm (p) {
      const dados = { ...(p.dados || {}) }
      if (p.slug === 'faq') {
        dados.perguntas = (dados.perguntas || []).map(q => ({ ...q, _id: ++uid }))
      }
      return { ...p, conteudo: p.conteudo || '', dados }
    },

    // dados limpos para enviar/pré-visualizar (sem ids internos)
    payloadDados (f) {
      if (f.slug === 'faq') {
        return { perguntas: f.dados.perguntas.map(({ pergunta, resposta }) => ({ pergunta, resposta })) }
      }
      return {}
    },

    estaSuja (slug) {
      const f = this.rascunhos[slug]
      const o = this.paginas.find(p => p.slug === slug)
      if (!f || !o) return false
      return f.titulo !== o.titulo
        || f.ativo !== o.ativo
        || f.conteudo !== (o.conteudo || '')
        || JSON.stringify(this.payloadDados(f)) !== JSON.stringify(this.payloadDados(this.paraForm(o)))
    },

    selecionar (slug) {
      this.slugActivo = slug
      this.erro = ''
    },

    adicionarPergunta () {
      this.form.dados.perguntas.push({ pergunta: '', resposta: '', _id: ++uid })
    },

    moverPergunta (i, dir) {
      const lista = this.form.dados.perguntas
      const j = i + dir
      if (j < 0 || j >= lista.length) return
      ;[lista[i], lista[j]] = [lista[j], lista[i]]
    },

    descartar () {
      this.rascunhos[this.slugActivo] = this.paraForm(this.original)
      this.erro = ''
    },

    async guardar () {
      const f = this.form
      this.saving = true
      this.erro = ''
      try {
        const { data } = await api.patch(`/app/admin/paginas/${f.slug}/`, {
          titulo:   f.titulo.trim(),
          ativo:    f.ativo,
          conteudo: f.conteudo,
          dados:    this.payloadDados(f),
        })
        const idx = this.paginas.findIndex(p => p.slug === data.slug)
        this.paginas.splice(idx, 1, data)
        this.rascunhos[data.slug] = this.paraForm(data)
        toast.success(`"${data.titulo}" guardada.`)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Erro ao guardar.'
        toast.error(this.erro)
      } finally {
        this.saving = false
      }
    },

    avisoSair (e) {
      if (!this.sujas.size) return
      e.preventDefault()
      e.returnValue = ''
    },

    formatarData (iso) {
      try {
        return new Date(iso).toLocaleString('pt-PT', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
      } catch { return '' }
    },
  },
}
</script>
