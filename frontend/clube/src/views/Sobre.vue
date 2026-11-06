<!-- Sobre.vue — landing page da Bende (/sobre): apresenta a plataforma numa página só. O conteúdo vem de
     GET /app/landing/ (o admin edita e publica — backend utils/landing.py). A navegação desliza até cada secção;
     entrar e criar conta abrem uma janela por cima (a mesma conta da loja Bende) e a pessoa fica aqui.
     Links dos botões: "/caminho" (dentro do site), "https://…" (separador novo), "#secção", "#entrar", "#criar-conta". -->
<template>
  <div class="min-h-screen" :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-50 text-zinc-900'" data-teste="pagina-sobre">
    <LandingNav :links="links" :ativa="ativa" :isDark="isDark" :user="user" :lojas="lojas" :sobreHero="sobreHero"
                @ir="ir" @entrar="janela = 'entrar'" @registo="janela = 'registo'" @tema="isDark = !isDark" @sair="sair" />

    <div v-if="aCarregar" class="min-h-[100svh] flex items-center px-5 sm:px-8" :class="isDark ? 'bg-zinc-950' : 'bg-orange-50'">
      <div class="max-w-7xl w-full mx-auto space-y-5">
        <div class="h-14 w-3/4 max-w-2xl rounded-xl animate-pulse" :class="isDark ? 'bg-zinc-800' : 'bg-orange-100'"></div>
        <div class="h-5 w-2/3 max-w-xl rounded animate-pulse" :class="isDark ? 'bg-zinc-800' : 'bg-orange-100'"></div>
        <div class="h-12 w-48 rounded-2xl animate-pulse" :class="isDark ? 'bg-zinc-800' : 'bg-orange-100'"></div>
      </div>
    </div>

    <div v-else-if="erro" class="min-h-[100svh] flex flex-col items-center justify-center text-center px-6 gap-4" data-teste="sobre-erro">
      <p class="text-lg font-semibold">Não foi possível carregar esta página.</p>
      <div class="flex gap-3">
        <button type="button" @click="carregar" class="px-5 py-2.5 rounded-xl border text-sm font-semibold"
                :class="isDark ? 'border-zinc-700' : 'border-stone-300'">Tentar outra vez</button>
        <router-link to="/Home" class="px-5 py-2.5 rounded-xl text-sm font-bold text-white" :class="isDark ? 'bg-red-600' : 'bg-orange-500'">Ir à loja</router-link>
      </div>
    </div>

    <main v-else :class="editar ? 'pt-12' : ''">
      <div v-for="(s, n) in visiveis" :key="s.tipo" class="relative" :class="comMolduras ? 'seccao-editavel' : ''"
           :data-teste="'seccao-' + s.tipo">
        <div v-if="comMolduras" class="absolute z-30 right-3 sm:right-6 flex items-center gap-2" :class="s.tipo === 'hero' ? 'top-32' : 'top-4'">
          <span v-if="!s.ativa" class="px-2.5 py-1 rounded-lg bg-zinc-800 text-zinc-300 text-[11px] font-bold" data-teste="marca-escondida">
            <font-awesome-icon :icon="['fas', 'eye-slash']" class="mr-1" />Escondida</span>
          <span v-else-if="s.vazia" class="px-2.5 py-1 rounded-lg bg-amber-500 text-black text-[11px] font-bold" data-teste="marca-vazia">
            Sem conteúdo — os visitantes não a vêem</span>
          <button type="button" @click="abrirPainel(s.tipo)" :data-teste="'editar-' + s.tipo"
                  class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold shadow-lg">
            <font-awesome-icon :icon="['fas', 'pen']" class="mr-1" />Editar</button>
        </div>
        <div :class="comMolduras && !s.ativa ? 'opacity-50' : ''">
          <LandingHero v-if="s.tipo === 'hero'" :s="heroVisivel(s)" :isDark="isDark" :seguinte="visiveis[n + 1]?.tipo || ''" @acao="acao" />
          <LandingCartoes v-else-if="s.tipo === 'clientes' || s.tipo === 'lojas'" :s="s" :isDark="isDark" :alternado="alternado(n)" @acao="acao" />
          <LandingPlanos v-else-if="s.tipo === 'planos'" :s="s" :isDark="isDark" :alternado="alternado(n)" @acao="acao" />
          <LandingTutoriais v-else-if="s.tipo === 'tutoriais'" :s="s" :isDark="isDark" :alternado="alternado(n)" />
          <LandingFaq v-else-if="s.tipo === 'faq'" :s="s" :isDark="isDark" :alternado="alternado(n)" />
          <LandingContactos v-else-if="s.tipo === 'contactos'" :s="s" :isDark="isDark" :alternado="alternado(n)" />
        </div>
      </div>
    </main>

    <!-- edição (admin com gerir_home): rascunho → Publicar -->
    <button v-if="podeEditar && !editar && !aCarregar" type="button" @click="entrarEdicao" data-teste="editar-pagina"
            class="fixed bottom-5 left-5 z-40 px-4 py-3 rounded-2xl bg-zinc-900 text-white text-sm font-bold shadow-2xl border border-zinc-700 hover:bg-zinc-800">
      <font-awesome-icon :icon="['fas', 'pen-to-square']" class="mr-2" />Editar página</button>
    <BarraEdicao v-if="editar && estado" :seccoes="estado.rascunho" :nomes="nomesSeccoes" :alteracoes="estado.alteracoes"
                 :visitante="visitante" :ocupado="ocupado" :historico="historico"
                 @visitante="v => { visitante = v; depoisDeMudar() }" @sair="sairEdicao" @historico="carregarHistorico"
                 @publicar="publicar" @descartar="acaoEditor('/app/admin/landing/descartar/', 'Alterações descartadas.')"
                 @padrao="acaoEditor('/app/admin/landing/padrao/', 'Textos de origem repostos no rascunho.')"
                 @restaurar="id => acaoEditor(`/app/admin/landing/publicacoes/${id}/restaurar/`, 'Publicação carregada no rascunho.')"
                 @ordem="ordenar" @visibilidade="mudarVisibilidade" />
    <PainelSeccao v-if="editar && painelTipo && seccaoRascunho" :seccao="seccaoRascunho" :resolvida="seccaoResolvida"
                  :medias="estado.medias || {}" :nome="nomesSeccoes[painelTipo]" :limites="limites" :aGravar="aGravar" :erro="erroPainel"
                  @gravar="gravarSeccao" @fechar="painelTipo = ''; erroPainel = ''" />

    <SiteRodape :isDark="isDark" />

    <JanelaConta v-if="janela" :modo="janela" :isDark="isDark" seguinte="/sobre"
                 @fechar="janela = null" @trocar="m => (janela = m)" @entrou="aoEntrar" />
  </div>
</template>

<script>
import { toast } from 'vue3-toastify'
import { defineAsyncComponent } from 'vue'
import api, { terminarSessao } from '@/services/api'
import { estaAutenticado } from '@/services/sessao'
import { temaEscuro, guardarTema } from '@/utils/tema'
import SiteRodape from '@/components/paginas/SiteRodape.vue'
import LandingNav from '@/components/landing/LandingNav.vue'
import LandingHero from '@/components/landing/LandingHero.vue'
import LandingCartoes from '@/components/landing/LandingCartoes.vue'
import LandingPlanos from '@/components/landing/LandingPlanos.vue'
import LandingTutoriais from '@/components/landing/LandingTutoriais.vue'
import LandingFaq from '@/components/landing/LandingFaq.vue'
import LandingContactos from '@/components/landing/LandingContactos.vue'
// só quando são precisos: os visitantes não descarregam o editor nem os formulários de conta
const JanelaConta = defineAsyncComponent(() => import('@/components/landing/JanelaConta.vue'))
const BarraEdicao = defineAsyncComponent(() => import('@/components/landing/editor/BarraEdicao.vue'))
const PainelSeccao = defineAsyncComponent(() => import('@/components/landing/editor/PainelSeccao.vue'))

const ACOES_CONTA = { '#entrar': 'entrar', '#criar-conta': 'registo' }

function lerUser () {
  if (!estaAutenticado()) return null
  try { return JSON.parse(localStorage.getItem('user') || 'null') || {} } catch (e) { return {} }
}

export default {
  name: 'PaginaSobre',
  components: {
    SiteRodape, LandingNav, LandingHero, LandingCartoes, LandingPlanos, LandingTutoriais, LandingFaq, LandingContactos, JanelaConta,
    BarraEdicao, PainelSeccao,
  },

  data () {
    return {
      seccoes: [], aCarregar: true, erro: false,
      isDark: temaEscuro(), user: lerUser(), lojas: [],
      ativa: '', noTopo: true, janela: null,
      // edição
      podeEditar: false, editar: false, estado: null, visitante: false, painelTipo: '', aGravar: false, erroPainel: '',
      ocupado: false, historico: [],
    }
  },

  computed: {
    // em edição mostra o rascunho (todas as secções, com as escondidas/vazias marcadas); "Ver como visitante" tira-as
    visiveis () {
      if (!this.editar || !this.estado) return this.seccoes
      return this.visitante ? this.estado.pagina.filter(s => !s.vazia) : this.estado.pagina
    },
    comMolduras () { return this.editar && !this.visitante },
    links () { return this.visiveis.filter(s => s.tipo !== 'hero' && s.nav && (!this.editar || s.ativa)).map(s => ({ tipo: s.tipo, nav: s.nav })) },
    // barra transparente com letras brancas só no topo e por cima de um hero com imagem/vídeo
    sobreHero () {
      const h = this.visiveis[0]
      return !this.editar && this.noTopo && h?.tipo === 'hero' && !!(h.media || h.media_movel)
    },
    nomesSeccoes () {
      return Object.fromEntries((this.estado?.opcoes?.tipos || []).map(t => [t.tipo, t.nome]))
    },
    limites () { return this.estado?.opcoes },
    seccaoRascunho () { return this.estado?.rascunho.find(s => s.tipo === this.painelTipo) || null },
    seccaoResolvida () { return this.estado?.pagina.find(s => s.tipo === this.painelTipo) || null },
  },

  watch: {
    isDark (v) { guardarTema(v) },
  },

  created () {
    document.title = 'Bende — compra e vende nas lojas de Cabo Verde'
    this.carregar()
    if (this.user) { this.carregarLojas(); this.verPermissao() } else if (this.$route.query.editar) this.janela = 'entrar'
  },

  mounted () {
    this.aoScroll = () => { this.noTopo = window.scrollY < 40 }
    window.addEventListener('scroll', this.aoScroll, { passive: true })
    this.aoScroll()
  },

  beforeUnmount () {
    window.removeEventListener('scroll', this.aoScroll)
    this.observador?.disconnect()
  },

  methods: {
    async carregar () {
      this.aCarregar = true
      this.erro = false
      try {
        const { data } = await api.get('/app/landing/')
        this.seccoes = data.seccoes || []
      } catch (e) {
        console.error(e)
        this.erro = true
      } finally {
        this.aCarregar = false
      }
      if (!this.erro) this.$nextTick(() => { this.vigiar(); this.abrirHash() })
    },

    async carregarLojas () {
      try {
        const { data } = await api.get('/app/loja/minhas/')
        this.lojas = (data.results || data || []).map(l => ({ id: l.id, nome: l.nome }))
      } catch (e) { this.lojas = [] }
    },

    alternado (n) { return n % 2 === 1 },

    // ── edição ──────────────────────────────────────────
    // só contas de staff perguntam; o servidor responde 403 a quem não tem gerir_home
    async verPermissao () {
      this.podeEditar = false
      if (!this.user?.is_staff) return
      try {
        const { data } = await api.get('/app/admin/landing/')
        this.estado = data
        this.podeEditar = true
        if (this.$route.query.editar) this.entrarEdicao()
      } catch (e) { this.podeEditar = false }
    },

    async entrarEdicao () {
      this.ocupado = true
      try {
        const { data } = await api.get('/app/admin/landing/')
        this.estado = data
        this.editar = true
        this.depoisDeMudar()
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Sem permissão para editar esta página.')
      } finally { this.ocupado = false }
    },

    sairEdicao () {
      this.editar = false
      this.painelTipo = ''
      this.visitante = false
      if (this.$route.query.editar) this.$router.replace({ query: {} })
      this.carregar()        // o que os visitantes vêem (pode ter sido publicado entretanto)
    },

    depoisDeMudar () { this.$nextTick(() => this.vigiar()) },

    abrirPainel (tipo) { this.erroPainel = ''; this.painelTipo = tipo },

    // erro do servidor: 409 = alguém gravou noutro sítio → recarrega o rascunho
    async falhou (e, alvo = 'toast') {
      const msg = e.response?.data?.detail || 'Não foi possível guardar.'
      if (e.response?.status === 409) {
        toast.error(msg, { autoClose: 6000 })
        try { this.estado = (await api.get('/app/admin/landing/')).data } catch (x) { /* fica o que havia */ }
        return
      }
      if (alvo === 'painel') this.erroPainel = msg
      else toast.error(msg)
    },

    async gravarSeccao (dados) {
      this.aGravar = true
      this.erroPainel = ''
      try {
        const { data } = await api.patch(`/app/admin/landing/seccoes/${this.painelTipo}/`, { versao: this.estado.versao, dados })
        this.estado = data
        toast.success('Guardado no rascunho.', { autoClose: 1500 })
        this.depoisDeMudar()
      } catch (e) {
        await this.falhou(e, 'painel')
      } finally { this.aGravar = false }
    },

    async ordenar (ordem) {
      this.ocupado = true
      try {
        this.estado = (await api.post('/app/admin/landing/ordem/', { versao: this.estado.versao, ordem })).data
        this.depoisDeMudar()
      } catch (e) { await this.falhou(e) } finally { this.ocupado = false }
    },

    async mudarVisibilidade (tipo, ativa) {
      this.ocupado = true
      try {
        this.estado = (await api.patch(`/app/admin/landing/seccoes/${tipo}/`, { versao: this.estado.versao, dados: { ativa } })).data
        this.depoisDeMudar()
      } catch (e) { await this.falhou(e) } finally { this.ocupado = false }
    },

    async acaoEditor (url, mensagem) {
      this.ocupado = true
      this.painelTipo = ''
      try {
        this.estado = (await api.post(url, {})).data
        toast.success(mensagem, { autoClose: 2000 })
        this.depoisDeMudar()
      } catch (e) { await this.falhou(e) } finally { this.ocupado = false }
    },

    async publicar () {
      this.ocupado = true
      try {
        this.estado = (await api.post('/app/admin/landing/publicar/', { versao: this.estado.versao })).data
        this.historico = []
        toast.success('Publicado! Os visitantes já vêem a página nova.', { autoClose: 3000 })
      } catch (e) { await this.falhou(e) } finally { this.ocupado = false }
    },

    async carregarHistorico () {
      try { this.historico = (await api.get('/app/admin/landing/publicacoes/')).data } catch (e) { this.historico = [] }
    },

    // com sessão iniciada, os botões de entrar/criar conta do hero deixam de fazer sentido
    heroVisivel (s) {
      if (!this.user) return s
      const fora = b => b && ACOES_CONTA[b.link] ? null : b
      return { ...s, botao: fora(s.botao), botao2: fora(s.botao2) }
    },

    // secção à vista → marcada na navegação
    vigiar () {
      this.observador?.disconnect()
      if (!('IntersectionObserver' in window)) return
      this.observador = new IntersectionObserver(entradas => {
        for (const e of entradas) if (e.isIntersecting) this.ativa = e.target.id === 'hero' ? '' : e.target.id
      }, { rootMargin: '-45% 0px -50% 0px' })
      for (const s of this.visiveis) {
        const el = document.getElementById(s.tipo)
        if (el) this.observador.observe(el)
      }
    },

    abrirHash () {
      const h = window.location.hash
      if (!h) return
      if (ACOES_CONTA[h]) {
        if (!this.user) this.janela = ACOES_CONTA[h]
        return
      }
      const el = document.getElementById(h.slice(1))
      if (el) setTimeout(() => el.scrollIntoView({ behavior: 'auto' }), 50)
    },

    ir (tipo) {
      const el = document.getElementById(tipo)
      if (!el) return
      const suave = !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
      el.scrollIntoView({ behavior: suave ? 'smooth' : 'auto', block: 'start' })
      // o endereço fica com a secção (para partilhar), sem criar uma entrada nova no histórico
      try { history.replaceState(history.state, '', tipo === 'hero' ? window.location.pathname : '#' + tipo) } catch (e) { /* ignora */ }
    },

    acao (link) {
      if (!link) return
      if (ACOES_CONTA[link]) {
        if (this.user) this.$router.push('/Home')
        else this.janela = ACOES_CONTA[link]
      } else if (link.startsWith('#')) {
        this.ir(link.slice(1))
      } else if (link.startsWith('/') && !link.startsWith('//')) {
        this.$router.push(link)
      } else {
        window.open(link, '_blank', 'noopener')
      }
    },

    aoEntrar (dados) {
      this.janela = null
      this.user = lerUser()
      this.carregarLojas()
      this.verPermissao()
      if (window.location.hash && ACOES_CONTA[window.location.hash]) {
        try { history.replaceState(history.state, '', window.location.pathname) } catch (e) { /* ignora */ }
      }
      if (dados?.eliminacao_cancelada) {
        toast.info('Bem-vindo de volta! O pedido para apagar a tua conta foi cancelado.', { autoClose: 8000 })
      } else {
        toast.success(`Olá, ${this.user?.first_name || this.user?.username || ''}! Já tens a sessão iniciada.`, { autoClose: 2500 })
      }
    },

    sair () {
      terminarSessao('access_token', 'refresh_token')
      for (const k of ['access_token', 'refresh_token', 'user']) localStorage.removeItem(k)
      this.user = null
      this.lojas = []
      if (this.editar) this.sairEdicao()
      this.podeEditar = false
      this.estado = null
      toast.info('Terminaste a sessão.', { autoClose: 2000 })
    },
  },
}
</script>

<style>
/* a barra fixa (h-16) não tapa o título ao deslizar para uma secção */
.landing-seccao { scroll-margin-top: 4rem; }
</style>
