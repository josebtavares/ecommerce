<!-- LandingTutoriais.vue — vídeos do YouTube que o admin colou (Tutoriais), com filtro por categoria quando
     há mais de uma. Os primeiros 6 aparecem logo; "Ver mais" mostra os restantes. -->
<template>
  <section id="tutoriais" class="landing-seccao py-20 sm:py-24 px-5 sm:px-8" data-teste="landing-tutoriais"
           :class="alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : ''">
    <div class="max-w-7xl mx-auto">
      <LandingTitulo :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />

      <div v-if="categorias.length > 1" class="mt-8 flex flex-wrap justify-center gap-2">
        <button v-for="c in ['', ...categorias]" :key="c || 'todos'" type="button" @click="filtro = c; todos = false"
                :data-teste="'tutoriais-cat-' + (c || 'todos')" :aria-pressed="filtro === c ? 'true' : 'false'"
                class="px-4 py-2 rounded-full text-sm font-semibold border transition"
                :class="filtro === c ? (isDark ? 'bg-red-600 border-red-600 text-white' : 'bg-orange-500 border-orange-500 text-white')
                                     : (isDark ? 'border-zinc-700 text-zinc-300 hover:bg-zinc-800' : 'border-stone-300 text-zinc-600 hover:bg-stone-100')">
          {{ c || 'Todos' }}</button>
      </div>

      <div class="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <article v-for="v in mostrados" :key="v.id" data-teste="tutorial">
          <VideoYoutube :id="v.youtube" :titulo="v.titulo" :miniatura="v.miniatura" />
          <p v-if="v.categoria" class="mt-3 text-[11px] font-bold uppercase tracking-widest" :class="isDark ? 'text-red-400' : 'text-orange-600'">{{ v.categoria }}</p>
          <h3 class="mt-1 text-base font-bold leading-snug" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ v.titulo }}</h3>
          <p v-if="v.descricao" class="mt-1 text-sm leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ v.descricao }}</p>
        </article>
      </div>

      <div v-if="filtrados.length > INICIAIS && !todos" class="mt-10 text-center">
        <button type="button" @click="todos = true" data-teste="tutoriais-mais"
                class="px-6 py-3 rounded-2xl text-sm font-bold border transition"
                :class="isDark ? 'border-zinc-700 text-zinc-200 hover:bg-zinc-800' : 'border-stone-300 text-zinc-700 hover:bg-stone-100'">
          Ver mais {{ filtrados.length - INICIAIS }} vídeos</button>
      </div>
    </div>
  </section>
</template>

<script>
import LandingTitulo from './LandingTitulo.vue'
import VideoYoutube from './VideoYoutube.vue'

const INICIAIS = 6

export default {
  name: 'LandingTutoriais',
  components: { LandingTitulo, VideoYoutube },
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
  data () { return { filtro: '', todos: false, INICIAIS } },
  computed: {
    videos () { return this.s.videos || [] },
    categorias () { return [...new Set(this.videos.map(v => v.categoria).filter(Boolean))] },
    filtrados () { return this.filtro ? this.videos.filter(v => v.categoria === this.filtro) : this.videos },
    mostrados () { return this.todos ? this.filtrados : this.filtrados.slice(0, INICIAIS) },
  },
}
</script>
