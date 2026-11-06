<!-- LandingContactos.vue — "Fala connosco": um cartão grande dividido. À esquerda, sobre a cor da Bende, o título, o
     atalho principal (WhatsApp ou email) e as redes sociais; à direita, os contactos em lista (email, telefone,
     WhatsApp, morada, horário — os vazios vêm dos contactos da plataforma, utils/landing.py). -->
<template>
  <section id="contactos" class="landing-seccao py-20 sm:py-28 px-5 sm:px-8" data-teste="landing-contactos"
           :class="[alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : '', { visivel }]">
    <div class="cartao max-w-6xl mx-auto rounded-[2rem] overflow-hidden shadow-2xl grid"
         :class="[isDark ? 'shadow-black/50 ring-1 ring-zinc-800' : 'shadow-orange-900/15', contactos.length ? 'lg:grid-cols-[5fr_6fr]' : '']">
      <!-- lado da cor -->
      <div class="relative overflow-hidden p-8 sm:p-12 text-white flex flex-col"
           :class="isDark ? 'bg-gradient-to-br from-red-600 via-red-700 to-zinc-900' : 'bg-gradient-to-br from-orange-500 via-orange-600 to-rose-600'">
        <span aria-hidden="true" class="pointer-events-none absolute -top-24 -right-24 w-72 h-72 rounded-full border-[3rem] border-white/10"></span>
        <span aria-hidden="true" class="pointer-events-none absolute -bottom-16 -left-10 w-48 h-48 rounded-full bg-white/10 blur-2xl"></span>
        <font-awesome-icon :icon="['fas', 'comments']" aria-hidden="true" class="relative self-start text-4xl text-white/90" />
        <h2 class="relative mt-6 text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight whitespace-pre-line">{{ s.titulo }}</h2>
        <p v-if="s.subtitulo" class="relative mt-3 text-lg text-white/85 leading-relaxed whitespace-pre-line">{{ s.subtitulo }}</p>

        <a v-if="principal" :href="principal.href" :target="principal.externo ? '_blank' : undefined" :rel="principal.externo ? 'noopener' : undefined"
           data-teste="contacto-principal"
           class="relative mt-8 self-start inline-flex items-center gap-3 px-5 py-3 rounded-2xl bg-white font-bold shadow-lg transition hover:-translate-y-0.5"
           :class="isDark ? 'text-red-700' : 'text-orange-600'">
          <i v-if="principal.chave === 'whatsapp'" class="fa-brands fa-whatsapp text-xl" aria-hidden="true"></i>
          <font-awesome-icon v-else :icon="['fas', principal.icone]" class="w-4 h-4" />
          {{ principal.chave === 'whatsapp' ? 'Falar no WhatsApp' : 'Enviar um email' }}
        </a>

        <div v-if="redes.length" class="relative mt-auto pt-10" data-teste="redes">
          <p class="text-xs font-bold uppercase tracking-widest text-white/70">Segue a Bende</p>
          <div class="mt-3 flex flex-wrap gap-2.5">
            <a v-for="r in redes" :key="r.rede" :href="r.url" target="_blank" rel="noopener" :aria-label="r.nome" :title="r.nome"
               class="w-11 h-11 rounded-full flex items-center justify-center text-lg bg-white/15 hover:bg-white hover:scale-110 transition"
               :class="isDark ? 'hover:text-red-700' : 'hover:text-orange-600'">
              <i :class="['fa-brands', r.icone]" aria-hidden="true"></i>
            </a>
          </div>
        </div>
      </div>

      <!-- lista dos contactos -->
      <ul v-if="contactos.length" class="p-4 sm:p-8 lg:p-10 flex flex-col justify-center" :class="isDark ? 'bg-zinc-900' : 'bg-white'">
        <li v-for="(c, n) in contactos" :key="c.chave" class="linha" :style="{ '--atraso': (n * 80) + 'ms' }">
          <component :is="c.href ? 'a' : 'div'" :href="c.href || undefined"
                     :target="c.externo ? '_blank' : undefined" :rel="c.externo ? 'noopener' : undefined"
                     :data-teste="'contacto-' + c.chave"
                     class="group flex items-center gap-4 px-3 sm:px-4 py-4 rounded-2xl transition"
                     :class="c.href ? (isDark ? 'hover:bg-zinc-800' : 'hover:bg-orange-50') : ''">
            <span class="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 transition"
                  :class="isDark ? 'bg-zinc-800 text-red-400 group-hover:bg-red-600 group-hover:text-white'
                                 : 'bg-stone-100 text-orange-600 group-hover:bg-orange-500 group-hover:text-white'">
              <i v-if="c.chave === 'whatsapp'" class="fa-brands fa-whatsapp text-xl" aria-hidden="true"></i>
              <font-awesome-icon v-else :icon="['fas', c.icone]" class="w-5 h-5" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ c.label }}</span>
              <span class="block mt-0.5 text-base sm:text-lg font-semibold break-words" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ c.valor }}</span>
            </span>
            <font-awesome-icon v-if="c.href" :icon="['fas', c.externo ? 'arrow-up-right-from-square' : 'arrow-right']"
                               class="w-4 h-4 flex-shrink-0 opacity-0 -translate-x-2 transition group-hover:opacity-100 group-hover:translate-x-0"
                               :class="isDark ? 'text-red-400' : 'text-orange-500'" />
          </component>
          <div v-if="n < contactos.length - 1" class="mx-4 border-t" :class="isDark ? 'border-zinc-800' : 'border-stone-100'"></div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script>
import { listaContactos } from '@/utils/paginas'
import revelar from './revelar'

const REDES = {
  facebook: ['Facebook', 'fa-facebook'], instagram: ['Instagram', 'fa-instagram'], tiktok: ['TikTok', 'fa-tiktok'],
  youtube: ['YouTube', 'fa-youtube'], linkedin: ['LinkedIn', 'fa-linkedin'], x: ['X', 'fa-x-twitter'],
}

export default {
  name: 'LandingContactos',
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
  computed: {
    contactos () { return listaContactos(this.s) },
    // o atalho do lado da cor: WhatsApp se houver, senão o email
    principal () { return this.contactos.find(c => c.chave === 'whatsapp') || this.contactos.find(c => c.chave === 'email') || null },
    redes () {
      return Object.entries(this.s.redes || {}).filter(([k, v]) => REDES[k] && v)
        .map(([k, url]) => ({ rede: k, url, nome: REDES[k][0], icone: REDES[k][1] }))
    },
  },
}
</script>

<style scoped>
.cartao { opacity: 0; transform: translateY(1.5rem); transition: opacity .7s ease, transform .7s ease; }
.visivel .cartao { opacity: 1; transform: none; }
.linha { opacity: 0; }
.visivel .linha { opacity: 1; animation: entrar .5s ease backwards; animation-delay: calc(var(--atraso) + 250ms); }
@keyframes entrar { from { opacity: 0; transform: translateX(1rem); } }
@media (prefers-reduced-motion: reduce) { .cartao, .linha { opacity: 1; transform: none; animation: none; transition: none; } }
</style>
