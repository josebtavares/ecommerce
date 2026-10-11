<!-- PaginaInfoModal.vue — popup das páginas institucionais (Ajuda, Contacto, FAQ, Termos, Privacidade)
     Uso:
       <PaginaInfoModal :slug="paginaAberta" :isDark="isDark" @close="paginaAberta = null" />
     ou, para pré-visualizar sem pedir à API (admin):
       <PaginaInfoModal :pagina="{ slug, titulo, conteudo, dados }" ... />
-->
<template>
  <Teleport to="body">
    <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                leave-active-class="transition duration-150" leave-to-class="opacity-0">
      <div v-if="aberto"
           class="fixed inset-0 z-[300] flex items-end sm:items-center justify-center sm:p-4 bg-black/60 backdrop-blur-sm"
           @click.self="$emit('close')">

        <div class="pim-painel w-full sm:max-w-2xl max-h-[88vh] sm:max-h-[85vh] flex flex-col overflow-hidden
                    rounded-t-3xl sm:rounded-3xl border shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100' : 'bg-white border-stone-200 text-zinc-900'"
             role="dialog" aria-modal="true" :aria-label="dados?.titulo">

          <!-- Cabeçalho -->
          <div class="flex items-center justify-between gap-3 px-5 sm:px-7 py-4 border-b flex-shrink-0"
               :class="isDark ? 'border-zinc-800' : 'border-stone-200'">
            <div class="min-w-0">
              <p class="text-[10px] font-bold uppercase tracking-[0.18em] text-red-500">
                {{ dados?.seccao === 'legal' ? 'Legal' : 'Suporte' }}
              </p>
              <h2 class="text-lg sm:text-xl font-bold truncate">{{ dados?.titulo || '…' }}</h2>
            </div>
            <button @click="$emit('close')" aria-label="Fechar"
              class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-stone-100 hover:bg-stone-200 text-zinc-600'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Corpo -->
          <div class="flex-1 overflow-y-auto px-5 sm:px-7 py-5 sm:py-6">
            <div v-if="loading" class="space-y-3">
              <div v-for="i in 5" :key="i" class="h-4 rounded animate-pulse"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'" :style="{ width: (95 - i * 9) + '%' }"></div>
            </div>

            <p v-else-if="erro" class="text-sm text-center py-8" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              {{ erro }}
            </p>

            <template v-else-if="dados">
              <!-- Texto livre -->
              <div v-if="blocos.length" class="pim-texto space-y-3 text-sm leading-relaxed"
                   :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
                <template v-for="(b, i) in blocos" :key="i">
                  <h3 v-if="b.tipo === 'titulo'" class="text-base font-bold pt-2"
                      :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ b.texto }}</h3>
                  <ul v-else-if="b.tipo === 'lista'" class="space-y-1.5 pl-1">
                    <li v-for="(item, j) in b.itens" :key="j" class="flex gap-2.5">
                      <span class="mt-2 w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0"></span>
                      <span>{{ item }}</span>
                    </li>
                  </ul>
                  <p v-else class="whitespace-pre-line">{{ b.texto }}</p>
                </template>
              </div>

              <!-- Contacto -->
              <div v-if="dados.slug === 'contacto' && contactos.length"
                   class="grid grid-cols-1 sm:grid-cols-2 gap-3" :class="blocos.length ? 'mt-6' : ''">
                <component :is="c.href ? 'a' : 'div'" v-for="c in contactos" :key="c.chave"
                   :href="c.href" :target="c.externo ? '_blank' : null" rel="noopener"
                   class="flex items-start gap-3 p-4 rounded-2xl border transition"
                   :class="[
                     isDark ? 'bg-zinc-950/50 border-zinc-800' : 'bg-stone-50 border-stone-200',
                     c.href && (isDark ? 'hover:border-red-500/50' : 'hover:border-red-300'),
                   ]">
                  <span class="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0 bg-red-500/10 text-red-500"><font-awesome-icon :icon="['fas', c.icone]" class="w-4 h-4" /></span>
                  <span class="min-w-0">
                    <span class="block text-[11px] uppercase tracking-wider font-semibold"
                          :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ c.label }}</span>
                    <span class="block text-sm font-semibold break-words">{{ c.valor }}</span>
                  </span>
                </component>
              </div>

              <!-- FAQ -->
              <div v-if="dados.slug === 'faq'" class="space-y-2" :class="blocos.length ? 'mt-6' : ''">
                <p v-if="!perguntas.length" class="text-sm text-center py-6" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
                  Ainda não há perguntas frequentes.
                </p>
                <div v-for="(q, i) in perguntas" :key="i"
                     class="rounded-2xl border overflow-hidden transition"
                     :class="[
                       isDark ? 'border-zinc-800' : 'border-stone-200',
                       faqAberta === i && (isDark ? 'bg-zinc-950/50' : 'bg-stone-50'),
                     ]">
                  <button @click="faqAberta = faqAberta === i ? null : i"
                    class="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left text-sm font-semibold"
                    :aria-expanded="faqAberta === i">
                    <span>{{ q.pergunta }}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 flex-shrink-0 transition-transform duration-200"
                         :class="[faqAberta === i && 'rotate-180', isDark ? 'text-zinc-500' : 'text-zinc-400']"
                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <p v-if="faqAberta === i" class="px-4 pb-4 -mt-1 text-sm leading-relaxed whitespace-pre-line"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ q.resposta }}</p>
                </div>
              </div>
            </template>
          </div>

          <!-- Rodapé -->
          <div v-if="dados?.data_atualizacao && !loading"
               class="px-5 sm:px-7 py-3 border-t text-[11px] flex-shrink-0"
               :class="isDark ? 'border-zinc-800 text-zinc-500' : 'border-stone-200 text-zinc-400'">
            Última actualização: {{ formatarData(dados.data_atualizacao) }}
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script>
import api from '@/services/api'

/** Converte o texto livre em blocos: "## Título", linhas "- item" e parágrafos. */
function parseConteudo (texto) {
  const blocos = []
  String(texto || '').replace(/\r\n/g, '\n').split(/\n{2,}/).forEach(par => {
    const linhas = par.split('\n').map(l => l.trimEnd()).filter(l => l.trim())
    if (!linhas.length) return
    let paragrafo = []
    const fecharParagrafo = () => {
      if (paragrafo.length) blocos.push({ tipo: 'paragrafo', texto: paragrafo.join('\n') })
      paragrafo = []
    }
    linhas.forEach(l => {
      const t = l.trim()
      if (/^#{1,3}\s+/.test(t)) {
        fecharParagrafo()
        blocos.push({ tipo: 'titulo', texto: t.replace(/^#{1,3}\s+/, '') })
      } else if (/^[-*•]\s+/.test(t)) {
        fecharParagrafo()
        const item = t.replace(/^[-*•]\s+/, '')
        const ultimo = blocos[blocos.length - 1]
        if (ultimo?.tipo === 'lista') ultimo.itens.push(item)
        else blocos.push({ tipo: 'lista', itens: [item] })
      } else {
        paragrafo.push(t)
      }
    })
    fecharParagrafo()
  })
  return blocos
}

export default {
  name: 'PaginaInfoModal',

  props: {
    slug:   { type: String, default: null },   // carrega da API
    pagina: { type: Object, default: null },   // ou recebe o conteúdo directamente (preview)
    isDark: { type: Boolean, default: true },
  },

  emits: ['close'],

  data () {
    return { carregada: null, loading: false, erro: '', faqAberta: null }
  },

  computed: {
    aberto () { return !!(this.slug || this.pagina) },
    dados ()  { return this.pagina || this.carregada },
    blocos () { return parseConteudo(this.dados?.conteudo) },
    perguntas () { return this.dados?.dados?.perguntas || [] },

    contactos () {
      const d = this.dados?.dados || {}
      const so = v => String(v || '').replace(/[^\d+]/g, '')
      return [
        d.email    && { chave: 'email',    icone: 'envelope', label: 'Email',    valor: d.email,    href: `mailto:${d.email}` },
        d.telefone && { chave: 'telefone', icone: 'phone', label: 'Telefone', valor: d.telefone, href: `tel:${so(d.telefone)}` },
        d.whatsapp && { chave: 'whatsapp', icone: 'comment-dots', label: 'WhatsApp', valor: d.whatsapp, href: `https://wa.me/${so(d.whatsapp).replace('+', '')}`, externo: true },
        d.morada   && { chave: 'morada',   icone: 'location-dot', label: 'Morada',   valor: d.morada,   href: `https://maps.google.com/?q=${encodeURIComponent(d.morada)}`, externo: true },
        d.horario  && { chave: 'horario',  icone: 'clock', label: 'Horário',  valor: d.horario },
      ].filter(Boolean)
    },
  },

  watch: {
    slug: { immediate: true, handler (s) { if (s) this.carregar(s) } },
    aberto (v) {
      document.body.style.overflow = v ? 'hidden' : ''
      if (v) window.addEventListener('keydown', this.onTecla)
      else   window.removeEventListener('keydown', this.onTecla)
    },
  },

  mounted () {
    if (this.aberto) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', this.onTecla)
    }
  },

  beforeUnmount () {
    document.body.style.overflow = ''
    window.removeEventListener('keydown', this.onTecla)
  },

  methods: {
    async carregar (slug) {
      this.loading = true
      this.erro = ''
      this.faqAberta = null
      this.carregada = null
      try {
        const { data } = await api.get(`/app/paginas/${slug}/`)
        this.carregada = data
      } catch (e) {
        this.erro = e.response?.status === 404
          ? 'Esta página não está disponível de momento.'
          : 'Não foi possível carregar o conteúdo. Tenta novamente.'
      } finally {
        this.loading = false
      }
    },

    onTecla (e) {
      if (e.key === 'Escape') this.$emit('close')
    },

    formatarData (iso) {
      try {
        return new Date(iso).toLocaleDateString('pt-PT', { day: 'numeric', month: 'long', year: 'numeric' })
      } catch { return '' }
    },
  },
}
</script>

<style scoped>
.pim-painel { animation: pimIn .22s cubic-bezier(.2,.8,.2,1); }
@keyframes pimIn { from { opacity: 0; transform: translateY(16px); } }
</style>
