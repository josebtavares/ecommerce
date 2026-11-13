<!-- PainelSeccao.vue — painel lateral para editar uma secção da landing page (só o admin com gerir_home).
     Trabalha numa cópia; "Guardar" emite 'gravar' com os campos da secção (o Sobre.vue manda PATCH ao rascunho —
     backend utils/landing.py valida tudo). Nada chega aos visitantes antes de Publicar. -->
<template>
  <aside class="fixed inset-y-0 right-0 z-[960] w-full sm:w-[28rem] bg-zinc-950 border-l border-zinc-800 shadow-2xl flex flex-col text-zinc-100"
         role="dialog" aria-modal="false" :aria-label="`Editar ${nome}`" data-teste="painel-seccao">
    <header class="flex items-center justify-between gap-3 px-5 py-4 border-b border-zinc-800">
      <div>
        <p class="text-[11px] font-bold uppercase tracking-wider text-red-400">Editar secção</p>
        <h2 class="text-base font-bold">{{ nome }}</h2>
      </div>
      <button type="button" @click="fechar" aria-label="Fechar" data-teste="painel-fechar"
              class="w-9 h-9 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800">✕</button>
    </header>

    <div class="flex-1 overflow-y-auto px-5 py-4 space-y-5">
      <label class="flex items-center justify-between gap-3 rounded-xl bg-zinc-900 px-4 py-3 cursor-pointer">
        <span>
          <span class="block text-sm font-semibold">Mostrar aos visitantes</span>
          <span class="block text-[11px] text-zinc-500">Escondida, continua aqui para editares.</span>
        </span>
        <input type="checkbox" v-model="f.ativa" class="w-5 h-5 accent-red-600" data-teste="campo-ativa" />
      </label>

      <div v-if="tipo !== 'hero'">
        <label class="rot">Nome na barra de navegação</label>
        <input v-model="f.nav" maxlength="30" class="campo" placeholder="vazio = não aparece na barra" data-teste="campo-nav" />
      </div>
      <div>
        <label class="rot">Título</label>
        <textarea v-model="f.titulo" maxlength="120" rows="2" class="campo" data-teste="campo-titulo"></textarea>
      </div>
      <div>
        <label class="rot">{{ tipo === 'hero' ? 'Subtítulo' : 'Texto por baixo do título' }}</label>
        <textarea v-model="f.subtitulo" maxlength="300" rows="3" class="campo" data-teste="campo-subtitulo"></textarea>
      </div>

      <!-- HERO -->
      <template v-if="tipo === 'hero'">
        <div>
          <label class="rot">Vídeo ou imagem de fundo</label>
          <CampoMedia v-model="f.media" :media="mediaDe(f.media)" nome="media" :limites="limites" vazio="Sem fundo (usa as cores da Bendi)"
                      @media="m => guardarMedia(m)" />
        </div>
        <div>
          <label class="rot">Versão para telemóvel <span class="text-zinc-500 font-normal">(opcional, ao alto fica melhor)</span></label>
          <CampoMedia v-model="f.media_movel" :media="mediaDe(f.media_movel)" nome="media_movel" :limites="limites"
                      vazio="Usa a mesma do computador" @media="m => guardarMedia(m)" />
        </div>
        <div>
          <label class="rot">Escurecer o fundo: {{ f.escurecer }}%</label>
          <input type="range" min="0" max="80" step="5" v-model.number="f.escurecer" class="w-full accent-red-600" data-teste="campo-escurecer" />
          <p class="text-[11px] text-zinc-500">Mais escuro = o texto lê-se melhor por cima de imagens claras.</p>
        </div>
        <CampoBotao v-model="f.botao" rotulo="Botão principal" nome="botao" />
        <CampoBotao v-model="f.botao2" rotulo="Segundo botão" nome="botao2" />
      </template>

      <!-- PARA CLIENTES / PARA LOJAS -->
      <template v-if="tipo === 'clientes' || tipo === 'lojas'">
        <ListaItens v-model="f[lista]" :novo="() => ({ icone: 'circle-check', titulo: '', texto: '' })"
                    :rotulo="tipo === 'clientes' ? 'Passo' : 'Cartão'" :nome="lista" :maximo="tipo === 'clientes' ? 8 : 12">
          <template #default="{ item }">
            <div class="space-y-2">
              <CampoIcone v-model="item.icone" />
              <input v-model="item.titulo" maxlength="80" class="campo" placeholder="Título" data-teste="item-titulo" />
              <textarea v-model="item.texto" maxlength="300" rows="2" class="campo" placeholder="Texto" data-teste="item-texto"></textarea>
            </div>
          </template>
        </ListaItens>
        <div v-if="tipo === 'lojas'">
          <label class="rot">Imagem ou vídeo de fundo do topo <span class="text-zinc-500 font-normal">(opcional)</span></label>
          <CampoMedia v-model="f.media" :media="mediaDe(f.media)" nome="media" :limites="limites" vazio="Sem fundo (usa as cores da Bendi)" @media="m => guardarMedia(m)" />
        </div>
        <template v-if="tipo === 'clientes'">
          <div>
            <label class="rot">Foto principal <span class="text-zinc-500 font-normal">(opcional)</span></label>
            <CampoMedia v-model="f.media" :media="mediaDe(f.media)" nome="media" :limites="limites" vazio="Sem foto (usa as cores da Bendi)" @media="m => guardarMedia(m)" />
          </div>
          <div>
            <label class="rot">Foto pequena, por cima <span class="text-zinc-500 font-normal">(opcional)</span></label>
            <CampoMedia v-model="f.media2" :media="mediaDe(f.media2)" nome="media2" :limites="limites" vazio="Sem foto (usa as cores da Bendi)" @media="m => guardarMedia(m)" />
          </div>
        </template>
        <CampoBotao v-model="f.botao" nome="botao" />
      </template>

      <!-- BACKOFFICE -->
      <template v-if="tipo === 'backoffice'">
        <p class="text-xs text-zinc-400 rounded-xl bg-zinc-900 px-4 py-3">Um módulo por separador, com a captura de ecrã do backoffice.
          A imagem aparece sempre inteira; fica melhor deitada (ex.: 1600×1000) e com todas do mesmo tamanho. Sem imagem, aparece um esboço com o ícone.</p>
        <ListaItens v-model="f.modulos" :novo="() => ({ icone: 'circle-check', titulo: '', texto: '', pontos: '', media: null })"
                    rotulo="Módulo" nome="modulos" :maximo="12" vazio="Sem módulos: a secção fica escondida aos visitantes.">
          <template #default="{ item }">
            <div class="space-y-2">
              <CampoIcone v-model="item.icone" />
              <input v-model="item.titulo" maxlength="80" class="campo" placeholder="Nome do módulo (ex.: Encomendas)" data-teste="item-titulo" />
              <textarea v-model="item.texto" maxlength="500" rows="3" class="campo" placeholder="Porque é bom (texto)" data-teste="item-texto"></textarea>
              <textarea v-model="item.pontos" maxlength="600" rows="3" class="campo" placeholder="Pontos fortes, um por linha (opcional)" data-teste="item-pontos"></textarea>
              <CampoMedia v-model="item.media" :media="mediaDe(item.media)" :nome="'modulo-' + (item.id || 'novo')" :limites="limites"
                          vazio="Sem captura (mostra um esboço)" @media="m => guardarMedia(m)" />
            </div>
          </template>
        </ListaItens>
        <CampoBotao v-model="f.botao" nome="botao" />
      </template>

      <!-- PLANOS -->
      <template v-if="tipo === 'planos'">
        <p class="text-xs text-zinc-400 rounded-xl bg-zinc-900 px-4 py-3">Os planos e os preços vêm de <b>Admin → Subscrições</b>
          (só os activos). Aqui escolhes quais aparecem.</p>
        <div>
          <label class="rot">Planos a mostrar</label>
          <label v-for="t in TIPOS_PLANO" :key="t.tipo" class="flex items-center gap-2 py-1 text-sm">
            <input type="checkbox" :value="t.tipo" v-model="f.tipos" class="accent-red-600" :data-teste="'campo-tipo-' + t.tipo" /> {{ t.nome }}
          </label>
        </div>
        <label class="flex items-center gap-2 text-sm"><input type="checkbox" v-model="f.mostrar_comissao" class="accent-red-600" data-teste="campo-comissao" />
          Mostrar o cartão da comissão por venda</label>
        <template v-if="f.mostrar_comissao">
          <input v-model="f.comissao_titulo" maxlength="80" class="campo" placeholder="Título do cartão" />
          <textarea v-model="f.comissao_texto" maxlength="300" rows="2" class="campo" placeholder="Texto do cartão"></textarea>
        </template>
        <div>
          <label class="rot">Nota por baixo</label>
          <input v-model="f.nota" maxlength="300" class="campo" placeholder="ex.: Preços em escudos (CVE)." />
        </div>
        <CampoBotao v-model="f.botao" nome="botao" />
      </template>

      <!-- TUTORIAIS -->
      <template v-if="tipo === 'tutoriais'">
        <p class="text-xs text-zinc-400 rounded-xl bg-zinc-900 px-4 py-3">Cola o link do vídeo no YouTube (do separador "Partilhar" ou da barra
          de endereço) e carrega em <b>Ler</b>: o título preenche-se sozinho.</p>
        <ListaItens v-model="f.videos" :novo="() => ({ youtube: '', titulo: '', descricao: '', categoria: '' })"
                    rotulo="Vídeo" nome="videos" :maximo="60" vazio="Ainda não há tutoriais — a secção fica escondida aos visitantes.">
          <template #default="{ item }">
            <div class="space-y-2">
              <div class="flex gap-2">
                <input v-model="item.youtube" class="campo flex-1" placeholder="https://youtu.be/…" data-teste="video-link"
                       @keydown.enter.prevent="lerYoutube(item)" />
                <button type="button" @click="lerYoutube(item)" :disabled="item._aLer" data-teste="video-ler"
                        class="px-3 rounded-lg bg-red-600 text-xs font-bold text-white disabled:opacity-50">{{ item._aLer ? '…' : 'Ler' }}</button>
              </div>
              <p v-if="item._erro" class="text-[11px] text-red-400" data-teste="video-erro">{{ item._erro }}</p>
              <p v-else-if="item._aviso" class="text-[11px] text-amber-400">{{ item._aviso }}</p>
              <img v-if="idYoutube(item.youtube)" :src="`https://i.ytimg.com/vi/${idYoutube(item.youtube)}/mqdefault.jpg`" alt=""
                   class="w-full aspect-video object-cover rounded-lg" data-teste="video-miniatura" />
              <input v-model="item.titulo" maxlength="120" class="campo" placeholder="Título" data-teste="video-titulo" />
              <textarea v-model="item.descricao" maxlength="300" rows="2" class="campo" placeholder="Descrição (opcional)"></textarea>
              <input v-model="item.categoria" maxlength="40" class="campo" placeholder="Categoria (ex.: Para lojas)" list="landing-categorias"
                     data-teste="video-categoria" />
            </div>
          </template>
        </ListaItens>
        <datalist id="landing-categorias"><option v-for="c in categorias" :key="c" :value="c" /></datalist>
      </template>

      <!-- FAQ -->
      <template v-if="tipo === 'faq'">
        <ListaItens v-model="f.perguntas" :novo="() => ({ pergunta: '', resposta: '' })" rotulo="Pergunta" nome="perguntas" :maximo="40">
          <template #default="{ item }">
            <div class="space-y-2">
              <input v-model="item.pergunta" maxlength="200" class="campo" placeholder="Pergunta" data-teste="faq-pergunta" />
              <textarea v-model="item.resposta" maxlength="2000" rows="4" class="campo" placeholder="Resposta" data-teste="faq-resposta"></textarea>
            </div>
          </template>
        </ListaItens>
      </template>

      <!-- BAIXAR A APP -->
      <template v-if="tipo === 'app'">
        <p class="text-xs text-zinc-400 rounded-xl bg-zinc-900 px-4 py-3">Liga <b>Mostrar aos visitantes</b> quando a app estiver publicada.
          Sem link do Google Play, o botão aparece como <b>"Em breve"</b>; o da App Store só aparece com link.</p>
        <div>
          <label class="rot">Link do Google Play</label>
          <input v-model="f.play_store" maxlength="300" class="campo" placeholder="https://play.google.com/store/apps/details?id=…" data-teste="campo-play_store" />
        </div>
        <div>
          <label class="rot">Link da App Store <span class="text-zinc-500 font-normal">(opcional)</span></label>
          <input v-model="f.app_store" maxlength="300" class="campo" placeholder="https://apps.apple.com/…" data-teste="campo-app_store" />
        </div>
        <ListaItens v-model="f.itens" :novo="() => ({ icone: 'circle-check', titulo: '', texto: '' })" rotulo="Vantagem" nome="itens" :maximo="4"
                    vazio="Sem vantagens: só o título, o texto e os botões.">
          <template #default="{ item }">
            <div class="space-y-2">
              <CampoIcone v-model="item.icone" />
              <input v-model="item.titulo" maxlength="80" class="campo" placeholder="Título" data-teste="item-titulo" />
              <textarea v-model="item.texto" maxlength="300" rows="2" class="campo" placeholder="Texto" data-teste="item-texto"></textarea>
            </div>
          </template>
        </ListaItens>
        <div>
          <label class="rot">Ecrã do telemóvel <span class="text-zinc-500 font-normal">(opcional: uma captura da app, ao alto)</span></label>
          <CampoMedia v-model="f.media" :media="mediaDe(f.media)" nome="media" :limites="limites" vazio="Sem captura (mostra o logo da Bendi)" @media="m => guardarMedia(m)" />
        </div>
      </template>

      <!-- CONTACTOS -->
      <template v-if="tipo === 'contactos'">
        <p class="text-xs text-zinc-400 rounded-xl bg-zinc-900 px-4 py-3">Campo vazio = usa o contacto de <b>Admin → Plataforma</b> (o mesmo do rodapé).</p>
        <div v-for="c in CONTACTOS" :key="c.campo">
          <label class="rot">{{ c.nome }}</label>
          <input v-model="f[c.campo]" :maxlength="c.max" class="campo" :placeholder="herdado(c.campo)" :data-teste="'campo-' + c.campo" />
        </div>
        <div>
          <label class="rot">Redes sociais (links https://)</label>
          <div v-for="r in REDES" :key="r.rede" class="flex items-center gap-2 mb-2">
            <i :class="['fa-brands', r.icone, 'w-5 text-center text-zinc-400']" aria-hidden="true"></i>
            <input v-model="f.redes[r.rede]" maxlength="300" class="campo" :placeholder="r.exemplo" :data-teste="'rede-' + r.rede" />
          </div>
        </div>
        <div>
          <label class="rot">Foto ao lado <span class="text-zinc-500 font-normal">(opcional)</span></label>
          <CampoMedia v-model="f.media" :media="mediaDe(f.media)" nome="media" :limites="limites" vazio="Sem foto (usa as cores da Bendi)" @media="m => guardarMedia(m)" />
        </div>
      </template>
    </div>

    <footer class="border-t border-zinc-800 px-5 py-4 space-y-3">
      <p v-if="erro" class="text-xs text-red-400" data-teste="painel-erro">{{ erro }}</p>
      <div v-if="aFechar" class="rounded-xl bg-amber-500/10 border border-amber-500/30 p-3 text-xs text-amber-200 space-y-2" data-teste="painel-por-guardar">
        <p>Tens alterações por guardar nesta secção.</p>
        <div class="flex gap-2">
          <button type="button" @click="$emit('fechar')" class="px-3 py-1.5 rounded-lg border border-zinc-600 font-semibold" data-teste="painel-descartar">Descartar</button>
          <button type="button" @click="aFechar = false" class="px-3 py-1.5 rounded-lg bg-zinc-800 font-semibold">Continuar a editar</button>
        </div>
      </div>
      <div class="flex gap-2">
        <button type="button" @click="fechar" class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-sm font-semibold hover:bg-zinc-900">Fechar</button>
        <button type="button" @click="gravar" :disabled="aGravar || !alterado" data-teste="painel-guardar"
                class="flex-[2] py-2.5 rounded-xl bg-red-600 text-sm font-bold text-white hover:bg-red-500 disabled:opacity-40">
          {{ aGravar ? 'A guardar…' : 'Guardar no rascunho' }}</button>
      </div>
    </footer>
  </aside>
</template>

<script>
import api from '@/services/api'
import CampoMedia from './CampoMedia.vue'
import CampoBotao from './CampoBotao.vue'
import CampoIcone from './CampoIcone.vue'
import ListaItens from './ListaItens.vue'

const CAMPOS = {
  hero: ['media', 'media_movel', 'escurecer', 'botao', 'botao2'],
  clientes: ['passos', 'botao', 'media', 'media2'],
  lojas: ['itens', 'botao', 'media'],
  backoffice: ['modulos', 'botao'],
  planos: ['tipos', 'mostrar_comissao', 'comissao_titulo', 'comissao_texto', 'nota', 'botao'],
  tutoriais: ['videos'],
  faq: ['perguntas'],
  app: ['play_store', 'app_store', 'itens', 'media'],
  contactos: ['email', 'telefone', 'whatsapp', 'morada', 'horario', 'redes', 'media'],
}
const LISTAS = ['passos', 'itens', 'modulos', 'videos', 'perguntas']
const CAMPOS_ITEM = {
  passos: ['id', 'icone', 'titulo', 'texto'], itens: ['id', 'icone', 'titulo', 'texto'],
  modulos: ['id', 'icone', 'titulo', 'texto', 'pontos', 'media'],
  videos: ['id', 'youtube', 'titulo', 'descricao', 'categoria'], perguntas: ['id', 'pergunta', 'resposta'],
}
const TIPOS_PLANO = [{ tipo: 'loja', nome: 'Loja online' }, { tipo: 'pos', nome: 'POS' }, { tipo: 'loja_pos', nome: 'Loja + POS' },
  { tipo: 'servicos', nome: 'Serviços' }]
const CONTACTOS = [{ campo: 'email', nome: 'Email', max: 254 }, { campo: 'telefone', nome: 'Telefone', max: 40 },
  { campo: 'whatsapp', nome: 'WhatsApp', max: 40 }, { campo: 'morada', nome: 'Morada', max: 300 }, { campo: 'horario', nome: 'Horário', max: 120 }]
const REDES = [
  { rede: 'facebook', icone: 'fa-facebook', exemplo: 'https://facebook.com/…' },
  { rede: 'instagram', icone: 'fa-instagram', exemplo: 'https://instagram.com/…' },
  { rede: 'tiktok', icone: 'fa-tiktok', exemplo: 'https://tiktok.com/@…' },
  { rede: 'youtube', icone: 'fa-youtube', exemplo: 'https://youtube.com/@…' },
  { rede: 'linkedin', icone: 'fa-linkedin', exemplo: 'https://linkedin.com/company/…' },
  { rede: 'x', icone: 'fa-x-twitter', exemplo: 'https://x.com/…' },
]
const RE_ID = /^[A-Za-z0-9_-]{11}$/

function copia (s) { return JSON.parse(JSON.stringify(s)) }

export default {
  name: 'PainelSeccao',
  components: { CampoMedia, CampoBotao, CampoIcone, ListaItens },
  props: {
    seccao: { type: Object, required: true },        // rascunho (em bruto) desta secção
    resolvida: { type: Object, default: null },      // como fica na página (contactos herdados)
    medias: { type: Object, default: () => ({}) },   // id → media (estado dos vídeos)
    nome: { type: String, default: '' },
    limites: { type: Object, default: undefined },
    aGravar: { type: Boolean, default: false },
    erro: { type: String, default: '' },
  },
  emits: ['gravar', 'fechar'],
  data () {
    return { f: {}, original: '', aFechar: false, novasMedias: {}, TIPOS_PLANO, CONTACTOS, REDES }
  },
  watch: {
    // depois de guardar, o servidor devolve a secção (com ids novos nos itens): o painel recomeça dela
    seccao () { this.repor() },
  },
  computed: {
    tipo () { return this.seccao.tipo },
    lista () { return this.tipo === 'clientes' ? 'passos' : 'itens' },
    payload () { return this.montar(this.f) },
    alterado () { return JSON.stringify(this.payload) !== this.original },
    categorias () { return [...new Set((this.f.videos || []).map(v => v.categoria).filter(Boolean))] },
  },
  created () { this.repor() },
  mounted () {
    this.tecla = e => { if (e.key === 'Escape') this.fechar() }
    window.addEventListener('keydown', this.tecla)
  },
  beforeUnmount () { window.removeEventListener('keydown', this.tecla) },
  methods: {
    // o que se manda ao servidor: só os campos da secção, botões sem texto = sem botão, listas sem as chaves locais
    montar (f) {
      const d = { ativa: !!f.ativa, titulo: f.titulo || '', subtitulo: f.subtitulo || '' }
      if (this.tipo !== 'hero') d.nav = f.nav || ''
      for (const c of CAMPOS[this.tipo]) {
        let v = f[c]
        if (c === 'botao' || c === 'botao2') v = v && (v.texto || '').trim() ? { texto: v.texto, link: v.link || '' } : null
        else if (LISTAS.includes(c)) {
          v = (v || []).map(it => Object.fromEntries(CAMPOS_ITEM[c].filter(k => k in it && (k !== 'id' || it.id))
            .map(k => [k, k === 'media' ? (it[k] || null) : (it[k] ?? '')])))
        }
        else if (c === 'redes') v = Object.fromEntries(Object.entries(v || {}).filter(([, u]) => (u || '').trim()).map(([k, u]) => [k, u.trim()]))
        else if (c === 'media' || c === 'media_movel' || c === 'media2') v = v || null
        else if (c === 'tipos') v = [...(v || [])]
        else if (c === 'escurecer') v = Number.isInteger(v) ? v : 45
        else if (c === 'mostrar_comissao') v = !!v
        else v = v ?? ''
        d[c] = v
      }
      return d
    },
    repor () {
      const f = copia(this.seccao)
      if (this.tipo === 'contactos') f.redes = { ...(f.redes || {}) }
      for (const l of LISTAS) if (l in f && !Array.isArray(f[l])) f[l] = []
      this.f = f
      this.original = JSON.stringify(this.montar(copia(this.seccao)))
    },
    mediaDe (id) { return id ? (this.novasMedias[id] || this.medias[String(id)] || null) : null },
    guardarMedia (m) { this.novasMedias = { ...this.novasMedias, [m.id]: m } },
    herdado (campo) { return this.resolvida?.[campo] ? `vazio = ${this.resolvida[campo]}` : 'vazio = sem este contacto' },
    idYoutube (t) {
      t = (t || '').trim()
      if (RE_ID.test(t)) return t
      const m = /(?:v=|youtu\.be\/|embed\/|shorts\/|live\/)([A-Za-z0-9_-]{11})/.exec(t)
      return m ? m[1] : ''
    },
    async lerYoutube (item) {
      item._erro = ''; item._aviso = ''
      if (!(item.youtube || '').trim()) { item._erro = 'Cola primeiro o link do vídeo.'; return }
      item._aLer = true
      try {
        const { data } = await api.get('/app/admin/landing/youtube/', { params: { url: item.youtube } })
        item.youtube = data.youtube
        if (!item.titulo && data.titulo) item.titulo = data.titulo
        if (data.aviso) item._aviso = data.aviso
      } catch (e) {
        item._erro = e.response?.data?.detail || 'Não foi possível ler o vídeo.'
      } finally { item._aLer = false }
    },
    fechar () {
      if (this.alterado && !this.aFechar) { this.aFechar = true; return }
      this.$emit('fechar')
    },
    gravar () { this.aFechar = false; this.$emit('gravar', this.payload) },
  },
}
</script>

<style scoped>
.rot { display: block; margin-bottom: 0.35rem; font-size: 0.75rem; font-weight: 600; color: #d4d4d8; }
.campo { width: 100%; padding: 0.5rem 0.75rem; border-radius: 0.6rem; font-size: 0.85rem; background: #18181b; border: 1px solid #3f3f46; color: #f4f4f5; }
.campo:focus { outline: none; border-color: #ef4444; }
textarea.campo { resize: vertical; }
</style>
