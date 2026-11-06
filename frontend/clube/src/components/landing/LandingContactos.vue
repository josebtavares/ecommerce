<!-- LandingContactos.vue — "Fala connosco": email, telefone, WhatsApp, morada, horário (os vazios vêm dos contactos
     da plataforma — utils/landing.py) e as redes sociais. -->
<template>
  <section id="contactos" class="landing-seccao py-20 sm:py-24 px-5 sm:px-8" data-teste="landing-contactos"
           :class="alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : ''">
    <div class="max-w-5xl mx-auto">
      <LandingTitulo :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />

      <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <component :is="c.href ? 'a' : 'div'" v-for="c in contactos" :key="c.chave" :href="c.href || undefined"
                   :target="c.externo ? '_blank' : undefined" :rel="c.externo ? 'noopener' : undefined"
                   :data-teste="'contacto-' + c.chave"
                   class="flex items-start gap-4 rounded-2xl border p-5 transition"
                   :class="[isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200', c.href ? (isDark ? 'hover:border-red-600/60' : 'hover:border-orange-400') : '']">
          <span class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
                :class="isDark ? 'bg-red-600/15 text-red-400' : 'bg-orange-100 text-orange-600'">
            <i v-if="c.chave === 'whatsapp'" class="fa-brands fa-whatsapp text-lg" aria-hidden="true"></i>
            <font-awesome-icon v-else :icon="['fas', c.icone]" class="w-4 h-4" />
          </span>
          <span class="min-w-0">
            <span class="block text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ c.label }}</span>
            <span class="block mt-0.5 font-semibold break-words" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ c.valor }}</span>
          </span>
        </component>
      </div>

      <div v-if="redes.length" class="mt-10 flex justify-center gap-3" data-teste="redes">
        <a v-for="r in redes" :key="r.rede" :href="r.url" target="_blank" rel="noopener" :aria-label="r.nome" :title="r.nome"
           class="w-12 h-12 rounded-full flex items-center justify-center text-lg border transition"
           :class="isDark ? 'border-zinc-700 text-zinc-300 hover:text-white hover:bg-zinc-800' : 'border-stone-300 text-zinc-600 hover:text-zinc-900 hover:bg-stone-100'">
          <i :class="['fa-brands', r.icone]" aria-hidden="true"></i>
        </a>
      </div>
    </div>
  </section>
</template>

<script>
import { listaContactos } from '@/utils/paginas'
import LandingTitulo from './LandingTitulo.vue'

const REDES = {
  facebook: ['Facebook', 'fa-facebook'], instagram: ['Instagram', 'fa-instagram'], tiktok: ['TikTok', 'fa-tiktok'],
  youtube: ['YouTube', 'fa-youtube'], linkedin: ['LinkedIn', 'fa-linkedin'], x: ['X', 'fa-x-twitter'],
}

export default {
  name: 'LandingContactos',
  components: { LandingTitulo },
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
  computed: {
    contactos () { return listaContactos(this.s) },
    redes () {
      return Object.entries(this.s.redes || {}).filter(([k, v]) => REDES[k] && v)
        .map(([k, url]) => ({ rede: k, url, nome: REDES[k][0], icone: REDES[k][1] }))
    },
  },
}
</script>
