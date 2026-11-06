<!-- LandingCartoes.vue — secções "Para clientes" (passos numerados) e "Para lojas" (funcionalidades, com imagem
     opcional ao lado). Cada cartão: ícone (Font Awesome), título e texto. -->
<template>
  <section :id="s.tipo" class="landing-seccao py-20 sm:py-24 px-5 sm:px-8" :data-teste="'landing-' + s.tipo"
           :class="alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : ''">
    <div class="max-w-7xl mx-auto">
      <LandingTitulo :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" :centro="!temMedia" />

      <div class="mt-12" :class="temMedia ? 'grid lg:grid-cols-2 gap-10 items-center' : ''">
        <div v-if="temMedia" class="order-first lg:order-last rounded-3xl overflow-hidden shadow-2xl aspect-[4/3] bg-black">
          <video v-if="s.media.tipo === 'video'" :src="s.media.url" :poster="s.media.poster || undefined" autoplay muted loop playsinline
                 class="w-full h-full object-cover" aria-hidden="true"></video>
          <img v-else :src="s.media.url" alt="" loading="lazy" class="w-full h-full object-cover" />
        </div>

        <ol class="grid gap-5" :class="grelha">
          <li v-for="(c, n) in cartoes" :key="c.id" data-teste="cartao"
              class="relative rounded-2xl border p-6 transition hover:-translate-y-0.5 hover:shadow-lg"
              :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
            <div class="flex items-center gap-3">
              <span class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                    :class="isDark ? 'bg-red-600/15 text-red-400' : 'bg-orange-100 text-orange-600'">
                <font-awesome-icon :icon="['fas', icone(c.icone)]" class="w-5 h-5" />
              </span>
              <span v-if="numerado" class="text-xs font-bold tracking-widest" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
                {{ String(n + 1).padStart(2, '0') }}</span>
            </div>
            <h3 class="mt-4 text-lg font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ c.titulo }}</h3>
            <p v-if="c.texto" class="mt-1.5 text-sm leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ c.texto }}</p>
          </li>
        </ol>
      </div>

      <div v-if="s.botao" class="mt-10" :class="temMedia ? '' : 'text-center'">
        <a :href="s.botao.link" @click="clique($event, s.botao.link)" :data-teste="s.tipo + '-botao'"
           class="inline-flex items-center gap-2 px-6 py-3 rounded-2xl font-bold text-white shadow transition hover:opacity-90"
           :class="isDark ? 'bg-red-600' : 'bg-orange-500'">
          {{ s.botao.texto }} <font-awesome-icon :icon="['fas', 'arrow-right']" class="w-4 h-4" />
        </a>
      </div>
    </div>
  </section>
</template>

<script>
import { findIconDefinition } from '@fortawesome/fontawesome-svg-core'
import LandingTitulo from './LandingTitulo.vue'

export default {
  name: 'LandingCartoes',
  components: { LandingTitulo },
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
  emits: ['acao'],
  computed: {
    numerado () { return this.s.tipo === 'clientes' },
    cartoes () { return this.s.passos || this.s.itens || [] },
    temMedia () { return !!this.s.media },
    grelha () {
      const n = this.cartoes.length
      if (this.temMedia) return 'sm:grid-cols-2'
      if (n % 4 === 0 || n > 6) return 'sm:grid-cols-2 lg:grid-cols-4'
      return 'sm:grid-cols-2 lg:grid-cols-3'
    },
  },
  methods: {
    // ícone que não exista no Font Awesome → um genérico (o admin escreve o nome)
    icone (nome) { return nome && findIconDefinition({ prefix: 'fas', iconName: nome }) ? nome : 'circle-check' },
    clique (e, link) {
      if (e.ctrlKey || e.metaKey || e.shiftKey) return
      e.preventDefault()
      this.$emit('acao', link)
    },
  },
}
</script>
