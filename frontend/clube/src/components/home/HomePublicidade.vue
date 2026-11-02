<!-- HomePublicidade.vue — secção "Publicidade" da home (Admin → Página inicial; backend utils/home.py _resolver_publicidade)
     • Tamanho: UMA proporção enquanto está na página (computador e telemóvel, calculada no servidor), por isso
       nada salta ao trocar de anúncio. Cada anúncio aparece inteiro (object-contain) por cima de uma cópia
       desfocada de si próprio — nunca é cortado.
     • Passa sozinho: imagens ao fim de `intervalo` s; vídeos quando acabam. Pára com o rato em cima, ao tocar,
       com o foco dentro, com o separador escondido ou a secção fora do ecrã; com "reduzir movimento" não passa
       sozinho e os vídeos ficam na capa. Botão de pausa (conteúdo que se move > 5 s precisa de um).
     • Só o vídeo do anúncio visível toca (sem som); os outros ficam parados e sem descarregar.
     • Estatísticas (utils/publicidade.js): impressão quando o anúncio activo está ≥ 50% à vista durante 1 s com o
       separador visível; clique ao abrir o link. Nunca na pré-visualização (`modo` ou `contar` = false).
     • `modo` ('computador' | 'telemovel'): pré-visualização do Admin — força o aspecto (proporção, setas, tamanhos de
       letra e versão para telemóvel) independentemente do ecrã, sem tecto de altura e sem links a navegar. -->
<template>
  <div data-teste="publicidade" :data-proporcao-computador="proporcao.computador" :data-proporcao-telemovel="proporcao.telemovel">
    <div v-if="titulo" class="mb-4">
      <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ titulo }}</h2>
      <p v-if="subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ subtitulo }}</p>
    </div>

    <section ref="caixa" class="pub-caixa relative overflow-hidden rounded-3xl bg-zinc-900" :class="{ 'pub-fixa': modo }"
             :style="{ '--r-computador': proporcao.computador, '--r-telemovel': proporcao.telemovel,
                       '--r-fixa': modo ? proporcao[modo] : undefined }"
             aria-roledescription="carrossel" :aria-label="titulo || 'Publicidade'"
             @mouseenter="pausas.rato = true" @mouseleave="pausas.rato = false"
             @focusin="aoEntrarFoco" @focusout="aoSairFoco">
      <swiper :modules="modules" :rewind="anuncios.length > 1" :allow-touch-move="anuncios.length > 1"
              :speed="600" class="h-full" :keyboard="{ enabled: true, onlyInViewport: true }"
              @swiper="s => (swiper = s)" @slide-change="aoMudar" @touch-start="aoTocar" @touch-end="aoLargar">
        <swiper-slide v-for="(a, i) in anuncios" :key="a.chave || i" class="h-full"
                      role="group" aria-roledescription="anúncio" :aria-label="`${i + 1} de ${anuncios.length}`"
                      :data-teste="'pub-anuncio-' + i">
          <component :is="a.link && !modo ? (a.externo ? 'a' : 'router-link') : 'div'"
                     v-bind="ligacao(a)" @click="aoClicar(a)" class="pub-slide group block relative h-full w-full overflow-hidden"
                     :class="a.link ? 'cursor-pointer' : ''" draggable="false">
            <!-- fundo: a mesma imagem desfocada (preenche o que sobra quando a proporção é diferente) -->
            <img v-if="fundo(a)" :src="fundo(a)" alt="" aria-hidden="true" :loading="i === 0 ? 'eager' : 'lazy'"
                 class="absolute inset-0 w-full h-full object-cover scale-110 blur-2xl opacity-60" />
            <div v-else class="absolute inset-0 bg-gradient-to-br from-zinc-800 to-zinc-950"></div>

            <!-- o anúncio, inteiro -->
            <video v-if="media(a).tipo === 'video' && !soCapa"
                   :ref="el => guardarVideo(i, el)" :src="i === ativo || carregados[i] ? fonteVideo(media(a)) : undefined"
                   :poster="media(a).poster || undefined" muted playsinline :loop="anuncios.length === 1"
                   :preload="i === ativo ? 'auto' : 'none'"
                   class="relative w-full h-full object-contain" :data-teste="'pub-video-' + i"
                   @ended="aoAcabarVideo(i)" @error="aoErroVideo($event, a)"></video>
            <img v-else :src="media(a).tipo === 'video' ? media(a).poster : media(a).url"
                 :alt="a.titulo || a.anunciante || 'Publicidade'" :loading="i === 0 ? 'eager' : 'lazy'" decoding="async"
                 class="relative w-full h-full object-contain" draggable="false" />

            <!-- textos e botão -->
            <div v-if="a.titulo || a.texto || a.botao"
                 class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 via-black/35 to-transparent" :class="pc ? 'p-8 pb-10' : 'p-4 pb-9'">
              <div class="max-w-xl">
                <h3 v-if="a.titulo" :class="pc ? 'text-3xl' : 'text-lg'" class="font-bold text-white leading-tight line-clamp-2">{{ a.titulo }}</h3>
                <p v-if="a.texto" :class="pc ? 'text-sm mt-2' : 'text-xs mt-1'" class="text-zinc-200 line-clamp-2">{{ a.texto }}</p>
                <span v-if="a.botao" class="inline-flex items-center gap-2 mt-3 px-4 py-2 bg-white/95 group-hover:bg-white text-zinc-900 font-bold rounded-xl transition" :class="pc ? 'text-sm' : 'text-xs'"
                      :data-teste="'pub-botao-' + i">
                  {{ a.botao }}
                  <font-awesome-icon :icon="['fas', a.externo ? 'arrow-up-right-from-square' : 'arrow-right']" class="text-[11px]" />
                </span>
              </div>
            </div>
          </component>
        </swiper-slide>
      </swiper>

      <!-- etiqueta (transparência: é publicidade, e de quem) -->
      <span class="absolute top-3 left-3 z-10 px-2 py-0.5 rounded-md bg-black/55 text-white/90 text-[10px] font-semibold tracking-wide pointer-events-none"
            data-teste="pub-etiqueta">
        Publicidade<template v-if="atual.anunciante"> · {{ atual.anunciante }}</template>
      </span>

      <template v-if="anuncios.length > 1">
        <button v-if="pc" type="button" @click="anterior" aria-label="Anúncio anterior" data-teste="pub-anterior"
                class="flex absolute left-3 top-1/2 -translate-y-1/2 z-10 w-10 h-10 items-center justify-center rounded-full bg-black/45 hover:bg-black/70 text-white transition">
          <font-awesome-icon :icon="['fas', 'chevron-left']" />
        </button>
        <button v-if="pc" type="button" @click="seguinte" aria-label="Anúncio seguinte" data-teste="pub-seguinte"
                class="flex absolute right-3 top-1/2 -translate-y-1/2 z-10 w-10 h-10 items-center justify-center rounded-full bg-black/45 hover:bg-black/70 text-white transition">
          <font-awesome-icon :icon="['fas', 'chevron-right']" />
        </button>
        <div class="absolute bottom-3 inset-x-0 z-10 flex items-center justify-center gap-1.5">
          <button v-for="(a, i) in anuncios" :key="'p' + i" type="button" @click="irPara(i)"
                  :aria-label="`Ver anúncio ${i + 1}`" :aria-current="i === ativo ? 'true' : undefined"
                  :data-teste="'pub-ponto-' + i"
                  class="h-1.5 rounded-full transition-all" :class="i === ativo ? 'w-6 bg-white' : 'w-1.5 bg-white/50 hover:bg-white/80'"></button>
        </div>
        <button v-if="!reduzirMovimento" type="button" @click="pausas.botao = !pausas.botao"
                :aria-label="pausas.botao ? 'Retomar a passagem automática' : 'Parar a passagem automática'"
                data-teste="pub-pausa"
                class="absolute top-2.5 right-3 z-10 w-7 h-7 flex items-center justify-center rounded-full bg-black/45 hover:bg-black/70 text-white text-[10px] transition">
          <font-awesome-icon :icon="['fas', pausas.botao ? 'play' : 'pause']" />
        </button>
      </template>
    </section>
  </div>
</template>

<script>
import { Keyboard, A11y } from 'swiper/modules'
import { Swiper, SwiperSlide } from 'swiper/vue'
import 'swiper/css'
import { poupar, videoDestaque } from '@/utils/media'
import { contarAnuncio } from '@/utils/publicidade'

const PRAZO_VIDEO_EXTRA_S = 3      // se o vídeo não avisar que acabou (erro, bloqueado), passa na mesma

export default {
  name: 'HomePublicidade',
  components: { Swiper, SwiperSlide },
  props: {
    anuncios:  { type: Array, default: () => [] },
    proporcao: { type: Object, default: () => ({ computador: 16 / 9, telemovel: 16 / 9 }) },
    intervalo: { type: Number, default: 6 },
    titulo:    { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark:    { type: Boolean, default: true },
    modo:      { type: String, default: '' },     // pré-visualização: 'computador' | 'telemovel'
    contar:    { type: Boolean, default: true },   // false na pré-visualização do rascunho (?preview=1)
  },
  data () {
    return {
      modules: [Keyboard, A11y],
      swiper: null,
      ativo: 0,
      carregados: {},          // índices cujo vídeo já foi pedido (não volta a descarregar ao regressar)
      telemovel: false,
      reduzirMovimento: false,
      soCapa: false,           // poupança de dados / reduzir movimento: vídeos ficam na capa
      visivel: false,
      metade: false,           // ≥ 50% à vista (conta impressões)
      escondido: false,
      pausas: { rato: false, foco: false, toque: false, botao: false },
      temporizador: null,
    }
  },
  computed: {
    atual () { return this.anuncios[this.ativo] || {} },
    movel () { return this.modo ? this.modo === 'telemovel' : this.telemovel },
    pc () { return !this.movel },
    aContar () { return this.contar && !this.modo && this.metade && !this.escondido ? (this.atual.chave || '') : '' },
    assinatura () { return this.anuncios.map(a => `${a.chave || ''}|${a.media?.url || ''}|${a.media_movel?.url || ''}`).join(',') },
    parado () {
      const p = this.pausas
      return this.anuncios.length < 2 || this.reduzirMovimento || !this.visivel || this.escondido ||
        p.rato || p.foco || p.toque || p.botao
    },
  },
  watch: {
    parado () { this.agendar(); this.controlarVideos() },
    aContar: { handler: 'vigiarImpressao', immediate: true },
    modo () { this.$nextTick(() => { this.agendar(); this.controlarVideos() }) },
    // só recomeça quando muda o conjunto de anúncios (no editor do Admin, escrever um título não volta ao primeiro)
    assinatura () { this.ativo = 0; this.swiper?.slideTo(0, 0); this.$nextTick(() => { this.agendar(); this.controlarVideos() }) },
  },
  created () {
    this.videos = {}   // não reactivo; tem de existir antes dos :ref dos <video>
  },
  mounted () {
    this.mqTelemovel = window.matchMedia('(max-width: 767px)')
    this.mqMovimento = window.matchMedia('(prefers-reduced-motion: reduce)')
    this.lerPreferencias = () => {
      this.telemovel = this.mqTelemovel.matches
      this.reduzirMovimento = this.mqMovimento.matches
      this.soCapa = poupar()
    }
    this.lerPreferencias()
    this.mqTelemovel.addEventListener?.('change', this.lerPreferencias)
    this.mqMovimento.addEventListener?.('change', this.lerPreferencias)
    this.aoVisibilidade = () => { this.escondido = document.hidden }
    document.addEventListener('visibilitychange', this.aoVisibilidade)
    this.aoVisibilidade()
    this.observador = new IntersectionObserver(([e]) => {
      this.visivel = e.isIntersecting && e.intersectionRatio >= 0.35
      this.metade = e.isIntersecting && e.intersectionRatio >= 0.5
    }, { threshold: [0, 0.35, 0.5, 0.6] })
    this.observador.observe(this.$refs.caixa)
  },
  beforeUnmount () {
    clearTimeout(this.temporizador)
    clearTimeout(this.tImpressao)
    this.observador?.disconnect()
    document.removeEventListener('visibilitychange', this.aoVisibilidade)
    this.mqTelemovel?.removeEventListener?.('change', this.lerPreferencias)
    this.mqMovimento?.removeEventListener?.('change', this.lerPreferencias)
    Object.values(this.videos || {}).forEach(v => { v.pause(); v.removeAttribute('src'); v.load() })  // liberta o descodificador
  },
  methods: {
    media (a) { return (this.movel && a.media_movel) || a.media },
    fundo (a) { const m = this.media(a); return m.tipo === 'video' ? m.poster : m.url },
    fonteVideo (m) { return videoDestaque(m.url) },
    ligacao (a) {
      if (!a.link || this.modo) return {}
      if (a.externo) return { href: a.link, target: '_blank', rel: 'sponsored noopener noreferrer' }
      return { to: a.link }
    },
    // ── estatísticas ──
    vigiarImpressao (chave) {
      clearTimeout(this.tImpressao)
      if (chave) this.tImpressao = setTimeout(() => contarAnuncio(chave, 'impressao'), 1000)
    },
    aoClicar (a) { if (a.link && this.contar && !this.modo) contarAnuncio(a.chave, 'clique', true) },
    guardarVideo (i, el) { if (el) this.videos[i] = el; else delete this.videos[i] },

    // ── navegação ──
    anterior () { this.swiper?.slidePrev() },
    seguinte () {
      if (!this.swiper) return
      if (this.swiper.isEnd) this.swiper.slideTo(0)
      else this.swiper.slideNext()
    },
    irPara (i) { this.swiper?.slideTo(i) },
    aoMudar (s) {
      this.ativo = s.activeIndex
      this.carregados = { ...this.carregados, [s.activeIndex]: true }
      this.$nextTick(() => { this.controlarVideos(); this.agendar() })
    },
    aoTocar () { this.pausas.toque = true },
    // depois de largar, conta o intervalo inteiro outra vez (não muda logo a seguir a um swipe)
    aoLargar () { setTimeout(() => { this.pausas.toque = false }, 400) },
    // só o foco de teclado pára (um clique com o rato em "Retomar" deixa o foco no botão e não pode voltar a parar)
    aoEntrarFoco (e) { if (e.target?.matches?.(':focus-visible')) this.pausas.foco = true },
    aoSairFoco (e) { if (!this.$refs.caixa?.contains(e.relatedTarget)) this.pausas.foco = false },

    // ── passagem automática ──
    agendar () {
      clearTimeout(this.temporizador)
      this.temporizador = null
      if (this.parado) return
      const m = this.media(this.atual)
      if (m?.tipo === 'video' && !this.soCapa) {
        // o vídeo avisa quando acaba (aoAcabarVideo); isto só cobre o caso de nunca avisar
        const s = (m.duracao || 30) + PRAZO_VIDEO_EXTRA_S
        this.temporizador = setTimeout(() => this.seguinte(), s * 1000)
        return
      }
      this.temporizador = setTimeout(() => this.seguinte(), Math.max(3, this.intervalo) * 1000)
    },
    aoAcabarVideo (i) {
      if (i !== this.ativo) return
      if (this.parado) { this.videos[i]?.play?.()?.catch?.(() => {}); return }   // parado: recomeça e fica
      this.seguinte()
    },
    aoErroVideo (e, a) {
      // versão leve (720p) em falta → original
      const v = e.target
      const m = this.media(a)
      if (v && m && v.getAttribute('src') && v.getAttribute('src') !== m.url) v.setAttribute('src', m.url)
    },
    controlarVideos () {
      Object.entries(this.videos).forEach(([i, v]) => {
        if (Number(i) === this.ativo && this.visivel && !this.escondido) {
          const p = v.play()
          if (p?.catch) p.catch(() => {})       // autoplay bloqueado: fica na capa
        } else {
          v.pause()
          if (Number(i) !== this.ativo) { try { v.currentTime = 0 } catch (e) { /* ainda sem dados */ } }
        }
      })
    },
  },
}
</script>

<style scoped>
/* uma proporção para toda a secção (telemóvel / computador), com tecto na altura do ecrã:
   com a largura definida, o max-height só encurta a altura e o anúncio continua inteiro (object-contain) */
/* width: 100% explícito — sem ele o aspect-ratio encolhia a LARGURA quando batia no max-height */
.pub-caixa { width: 100%; aspect-ratio: var(--r-telemovel); max-height: 80vh; }
@media (min-width: 768px) {
  .pub-caixa { aspect-ratio: var(--r-computador); max-height: 70vh; }
}
.pub-caixa.pub-fixa { aspect-ratio: var(--r-fixa); max-height: none; }
.pub-caixa :deep(.swiper) { height: 100%; }
</style>
