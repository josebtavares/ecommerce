<!-- AdminAparencia.vue — Admin → Definições → Aparência: fundo do login, fundo do registo e logótipo do site.
     Backend: app/Views/aparenciaView.py (otimização: utils/aparencia.py). Escolher um ficheiro mostra a
     pré-visualização; só se envia ao carregar em "Aplicar". Um vídeo é otimizado pelo worker e o site continua com
     o anterior até ficar pronto (esta página vai vendo o estado). -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="aparencia">
    <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Aparência</h3>
    <p class="text-xs text-zinc-500 mt-1 mb-5">
      Fundo das páginas de entrar e criar conta, e o logótipo do site. Imagens e vídeos são otimizados
      automaticamente; a mudança chega a todos os visitantes em segundos.
    </p>

    <div v-if="!d" class="h-40 bg-zinc-800/50 rounded-xl animate-pulse"></div>

    <template v-else>
      <!-- ── fundos ── -->
      <div class="grid sm:grid-cols-2 gap-4">
        <div v-for="f in FUNDOS" :key="f.qual" class="rounded-xl border border-zinc-800 p-4" :data-teste="'fundo-' + f.qual">
          <p class="text-sm font-semibold text-zinc-200">{{ f.titulo }}</p>
          <p class="text-xs text-zinc-500 mb-3">{{ f.ajuda }}</p>

          <div class="relative aspect-video rounded-lg overflow-hidden bg-zinc-800">
            <template v-if="previa(f.qual)">
              <video v-if="previa(f.qual).tipo === 'video'" :src="previa(f.qual).url" autoplay muted loop playsinline
                     class="absolute inset-0 w-full h-full object-cover"></video>
              <img v-else :src="previa(f.qual).url" alt="" class="absolute inset-0 w-full h-full object-cover" />
            </template>
            <span class="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/70 text-[11px] font-semibold text-white">
              {{ etiqueta(f.qual) }}
            </span>
          </div>

          <p v-if="novo(f.qual) && emCurso(novo(f.qual))" class="text-xs text-amber-400 mt-2" :data-teste="'fundo-' + f.qual + '-a-otimizar'">
            <font-awesome-icon :icon="['fas', 'spinner']" spin class="mr-1" />
            A otimizar o vídeo novo… o site continua com o anterior até ficar pronto.
          </p>
          <p v-else-if="novo(f.qual) && novo(f.qual).estado === 'erro'" class="text-xs text-red-400 mt-2" role="alert">
            Não foi possível otimizar o vídeo novo. Experimenta outro ficheiro (MP4 de preferência).
          </p>

          <div v-if="escolhido[f.qual]" class="flex flex-wrap gap-2 mt-3">
            <button type="button" @click="aplicarFundo(f.qual)" :disabled="!!aEnviar" :data-teste="'fundo-' + f.qual + '-aplicar'"
              class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-xs font-bold transition">
              {{ aEnviar === f.qual ? 'A enviar…' : 'Aplicar' }}
            </button>
            <button type="button" @click="cancelar(f.qual)" :disabled="!!aEnviar"
              class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold transition">
              Cancelar
            </button>
          </div>
          <div v-else class="flex flex-wrap gap-2 mt-3">
            <label class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-semibold transition cursor-pointer">
              Escolher imagem ou vídeo
              <input type="file" class="hidden" accept="image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime"
                     :data-teste="'fundo-' + f.qual + '-ficheiro'" @change="escolher(f.qual, $event)" />
            </label>
            <button v-if="temProprio(f.qual)" type="button" @click="repor('fundo', f.qual)" :disabled="!!aEnviar"
              :data-teste="'fundo-' + f.qual + '-repor'"
              class="px-4 py-2 rounded-xl text-zinc-400 hover:text-zinc-100 text-xs font-semibold transition">
              {{ f.qual === 'registo' ? 'Usar o do login' : 'Repor o original' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ── logótipo ── -->
      <div class="grid sm:grid-cols-2 gap-4 mt-4">
        <div v-for="l in LOGOS" :key="l.tema" class="rounded-xl border border-zinc-800 p-4" :data-teste="'logo-' + l.tema">
          <p class="text-sm font-semibold text-zinc-200">{{ l.titulo }}</p>
          <p class="text-xs text-zinc-500 mb-3">{{ l.ajuda }}</p>
          <div class="relative h-32 rounded-lg flex items-center justify-center"
               :style="{ background: l.tema === 'claro' ? '#ffffff' : '#09090b', border: '1px solid #3f3f46' }">
            <!-- cores fixas (style): o tema claro do admin troca as classes bg-* e a pré-visualização ficava ao contrário -->
            <img :src="previaLogo(l.tema)" alt="Logótipo" class="max-h-24 max-w-[70%] object-contain" />
            <span class="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/70 text-[11px] font-semibold text-white">
              {{ escolhido[l.tema] ? 'Pré-visualização' : (d[LOGO_CAMPO[l.tema]] ? 'Em uso' : (outroLogo(l.tema) ? 'Usa o outro logótipo' : 'Original')) }}
            </span>
          </div>
          <div v-if="escolhido[l.tema]" class="flex flex-wrap gap-2 mt-3">
            <button type="button" @click="aplicarLogo(l.tema)" :disabled="!!aEnviar" :data-teste="'logo-' + l.tema + '-aplicar'"
              class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-xs font-bold transition">
              {{ aEnviar === l.tema ? 'A enviar…' : 'Aplicar' }}
            </button>
            <button type="button" @click="cancelar(l.tema)" :disabled="!!aEnviar"
              class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold transition">
              Cancelar
            </button>
          </div>
          <div v-else class="flex flex-wrap gap-2 mt-3">
            <label class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-semibold transition cursor-pointer">
              Escolher imagem
              <input type="file" class="hidden" accept="image/png,image/webp,image/jpeg"
                     :data-teste="'logo-' + l.tema + '-ficheiro'" @change="escolher(l.tema, $event)" />
            </label>
            <button v-if="d[LOGO_CAMPO[l.tema]]" type="button" @click="repor('logo', l.tema)" :disabled="!!aEnviar"
              :data-teste="'logo-' + l.tema + '-repor'"
              class="px-4 py-2 rounded-xl text-zinc-400 hover:text-zinc-100 text-xs font-semibold transition">
              Repor o original
            </button>
          </div>
        </div>
      </div>
      <p class="text-xs text-zinc-500 mt-3">
        PNG com fundo transparente fica melhor. Do logótipo para fundos claros geram-se também o ícone do separador do
        browser, o do ecrã inicial do telemóvel e o dos emails.
      </p>

      <p v-if="erro" class="text-sm text-red-400 mt-3" role="alert" data-teste="aparencia-erro">{{ erro }}</p>
      <p v-if="ok" class="text-sm text-green-400 mt-3" data-teste="aparencia-ok">{{ ok }}</p>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { ORIGINAL, carregarAparencia } from '@/utils/aparencia'

const FUNDOS = [
  { qual: 'login', titulo: 'Fundo do login', ajuda: 'Também na página "Recuperar a password".' },
  { qual: 'registo', titulo: 'Fundo do registo', ajuda: 'Sem um próprio, usa o do login.' },
]
const LOGOS = [
  { tema: 'claro', titulo: 'Logótipo para fundos claros', ajuda: 'O principal (tema claro, emails, ícones).' },
  { tema: 'escuro', titulo: 'Logótipo para fundos escuros', ajuda: 'Tema escuro. Sem este, usa o outro.' },
]
const LOGO_CAMPO = { claro: 'logo', escuro: 'logo_escuro' }
const VIDEO = ['mp4', 'webm', 'mov']

export default {
  name: 'AdminAparencia',
  data () {
    return { FUNDOS, LOGOS, LOGO_CAMPO, d: null, escolhido: {}, aEnviar: '', erro: '', ok: '', relogio: null }
  },
  async created () {
    await this.carregar()
  },
  beforeUnmount () {
    clearTimeout(this.relogio)
    Object.values(this.escolhido).forEach(e => e?.url && URL.revokeObjectURL(e.url))
  },
  methods: {
    async carregar () {
      try {
        const { data } = await api.get('/app/admin/plataforma/aparencia/')
        this.receber(data, false)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar a aparência.'
      }
    },
    receber (data, mudou = true) {
      const antes = this.d
      this.d = data
      // um vídeo acabou de ficar pronto (ou outra mudança): o site deste separador actualiza já
      const promovido = antes && FUNDOS.some(f => antes[`fundo_${f.qual}_novo`] && !data[`fundo_${f.qual}_novo`])
      if (mudou || promovido) carregarAparencia(true)
      clearTimeout(this.relogio)
      if (FUNDOS.some(f => this.emCurso(data[`fundo_${f.qual}_novo`]))) {
        this.relogio = setTimeout(() => this.carregar(), 5000)
      }
    },
    novo (qual) { return this.d?.[`fundo_${qual}_novo`] },
    emCurso (m) { return !!m && ['pendente', 'a_processar', 'processando'].includes(m.estado) },
    temProprio (qual) {
      return qual === 'registo' ? !this.d.fundo_registo_igual : (this.d.fundo_login_proprio || !!this.novo('login'))
    },
    previa (qual) {
      if (this.escolhido[qual]) return this.escolhido[qual]
      return this.d[`fundo_${qual}`] || ORIGINAL.fundo()
    },
    etiqueta (qual) {
      if (this.escolhido[qual]) return 'Pré-visualização'
      if (qual === 'registo' && this.d.fundo_registo_igual) return 'Igual ao do login'
      return this.d[`fundo_${qual}_proprio`] ? 'Em uso' : 'Original'
    },
    outroLogo (tema) { return this.d[LOGO_CAMPO[tema === 'claro' ? 'escuro' : 'claro']] },
    previaLogo (tema) {
      if (this.escolhido[tema]) return this.escolhido[tema].url
      return this.d[LOGO_CAMPO[tema]] || this.outroLogo(tema) || ORIGINAL[LOGO_CAMPO[tema]]
    },
    escolher (chave, ev) {
      const ficheiro = ev.target.files?.[0]
      ev.target.value = ''
      if (!ficheiro) return
      this.erro = ''
      this.ok = ''
      const ext = (ficheiro.name.split('.').pop() || '').toLowerCase()
      const limites = this.d.limites || {}
      const video = VIDEO.includes(ext)
      if (video && limites.video_mb && ficheiro.size > limites.video_mb * 1024 * 1024) {
        this.erro = `O vídeo tem de ter no máximo ${limites.video_mb} MB.`
        return
      }
      if (this.escolhido[chave]?.url) URL.revokeObjectURL(this.escolhido[chave].url)
      this.escolhido = { ...this.escolhido, [chave]: { ficheiro, url: URL.createObjectURL(ficheiro), tipo: video ? 'video' : 'imagem' } }
    },
    cancelar (chave) {
      if (this.escolhido[chave]?.url) URL.revokeObjectURL(this.escolhido[chave].url)
      const resto = { ...this.escolhido }
      delete resto[chave]
      this.escolhido = resto
    },
    async enviar (chave, caminho, campos) {
      this.erro = ''
      this.ok = ''
      this.aEnviar = chave
      try {
        const fd = new FormData()
        Object.entries(campos).forEach(([k, v]) => fd.append(k, v))
        fd.append('ficheiro', this.escolhido[chave].ficheiro)
        const { data } = await api.post(caminho, fd)
        const video = this.escolhido[chave].tipo === 'video'
        this.cancelar(chave)
        this.receber(data)
        this.ok = video ? 'Vídeo enviado. Fica em uso assim que acabar de ser otimizado.' : 'Aplicado.'
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível enviar o ficheiro.'
      } finally {
        this.aEnviar = ''
      }
    },
    aplicarFundo (qual) { return this.enviar(qual, '/app/admin/plataforma/aparencia/fundo/', { qual }) },
    aplicarLogo (tema) { return this.enviar(tema, '/app/admin/plataforma/aparencia/logo/', { tema }) },
    async repor (tipo, chave) {
      const msg = tipo === 'logo' ? 'Repor o logótipo original?'
        : chave === 'registo' ? 'O registo volta a usar o fundo do login. Continuar?' : 'Repor o fundo original do login?'
      if (!confirm(msg)) return
      this.erro = ''
      this.ok = ''
      this.aEnviar = chave
      try {
        const params = tipo === 'logo' ? { tema: chave } : { qual: chave }
        const { data } = await api.delete(`/app/admin/plataforma/aparencia/${tipo}/`, { params })
        this.receber(data)
        this.ok = 'Reposto.'
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível repor.'
      } finally {
        this.aEnviar = ''
      }
    },
  },
}
</script>
