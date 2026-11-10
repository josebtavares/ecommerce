<!-- LandingContactos.vue — "Fala connosco": a toda a largura, a foto da secção à esquerda (ou um bloco com as cores da
     Bendi) e um painel suave à direita com o letreiro, o título, os contactos (email, telefone, WhatsApp, morada,
     horário — os vazios vêm dos contactos da plataforma, utils/landing.py), os botões e as redes sociais. -->
<template>
  <section id="contactos" class="landing-seccao grid lg:grid-cols-[5fr_7fr]" data-teste="landing-contactos" :class="{ visivel }">
    <!-- foto -->
    <div class="foto relative min-h-[16rem] sm:min-h-[22rem] lg:min-h-full overflow-hidden">
      <template v-if="s.media">
        <div class="absolute inset-0"><LandingFoto :media="s.media" /></div>
        <span class="absolute inset-0" :class="isDark ? 'bg-black/30' : 'bg-slate-900/10'"></span>
      </template>
      <div v-else class="absolute inset-0 flex items-center justify-center"
           :class="isDark ? 'bg-gradient-to-br from-red-600 via-red-800 to-zinc-950' : 'bg-gradient-to-br from-orange-400 via-orange-500 to-rose-600'">
        <span aria-hidden="true" class="absolute inset-0 pontos opacity-20"></span>
        <span aria-hidden="true" class="absolute -left-16 -bottom-16 w-72 h-72 rounded-full border-[2.5rem] border-white/10"></span>
        <font-awesome-icon :icon="['fas', 'comments']" class="relative text-[7rem] sm:text-[9rem] text-white/90 drop-shadow-xl" />
      </div>
    </div>

    <!-- painel -->
    <div class="painel px-5 sm:px-12 lg:px-20 py-16 sm:py-24" :class="isDark ? 'bg-zinc-900' : 'bg-slate-100'">
      <div class="max-w-2xl">
        <LandingCabecalho :etiqueta="s.nav" :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />

        <ul v-if="contactos.length" class="mt-10 grid gap-x-8 gap-y-6 sm:grid-cols-2">
          <li v-for="(c, n) in contactos" :key="c.chave" class="contacto"
              :style="{ '--atraso': (n * 90) + 'ms' }">
            <component :is="c.href ? 'a' : 'div'" :href="c.href || undefined"
                       :target="c.externo ? '_blank' : undefined" :rel="c.externo ? 'noopener' : undefined"
                       :data-teste="'contacto-' + c.chave" class="group flex items-center gap-4">
              <span class="w-14 h-14 flex-shrink-0 rounded-lg flex items-center justify-center shadow-sm transition"
                    :class="[isDark ? 'bg-zinc-800 text-red-400' : 'bg-white text-orange-500',
                             c.href ? (isDark ? 'group-hover:bg-red-600 group-hover:text-white' : 'group-hover:bg-orange-500 group-hover:text-white') : '']">
                <i v-if="c.chave === 'whatsapp'" class="fa-brands fa-whatsapp text-2xl" aria-hidden="true"></i>
                <font-awesome-icon v-else :icon="['fas', c.icone]" class="text-xl" />
              </span>
              <span class="min-w-0">
                <span class="block text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-zinc-500' : 'text-slate-400'">{{ c.label }}</span>
                <span class="titulo-landing block mt-0.5 font-semibold break-words transition-colors"
                      :class="[isDark ? 'text-zinc-100' : 'text-slate-900', c.href ? (isDark ? 'group-hover:text-red-400' : 'group-hover:text-orange-600') : '']">{{ c.valor }}</span>
              </span>
            </component>
          </li>
        </ul>

        <div class="mt-12 flex flex-wrap items-center gap-x-8 gap-y-6">
          <a v-if="principal" :href="principal.href" :target="principal.externo ? '_blank' : undefined" :rel="principal.externo ? 'noopener' : undefined"
             data-teste="contacto-principal"
             class="inline-flex items-center gap-3 px-8 py-4 rounded-full font-semibold text-white shadow-lg transition hover:-translate-y-0.5"
             :class="isDark ? 'bg-red-600 shadow-red-900/30' : 'bg-orange-500 shadow-orange-500/30'">
            <i v-if="principal.chave === 'whatsapp'" class="fa-brands fa-whatsapp text-xl" aria-hidden="true"></i>
            <font-awesome-icon v-else :icon="['fas', 'paper-plane']" />
            {{ principal.chave === 'whatsapp' ? 'Falar no WhatsApp' : 'Enviar um email' }}
          </a>
          <div v-if="redes.length" class="flex items-center gap-2.5" data-teste="redes">
            <a v-for="r in redes" :key="r.rede" :href="r.url" target="_blank" rel="noopener" :aria-label="r.nome" :title="r.nome"
               class="w-11 h-11 rounded-full flex items-center justify-center transition hover:-translate-y-0.5"
               :class="isDark ? 'bg-zinc-800 text-zinc-300 hover:bg-red-600 hover:text-white' : 'bg-slate-800 text-white hover:bg-orange-500'">
              <i :class="['fa-brands', r.icone]" aria-hidden="true"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { listaContactos } from '@/utils/paginas'
import revelar from './revelar'
import LandingCabecalho from './LandingCabecalho.vue'
import LandingFoto from './LandingFoto.vue'

const REDES = {
  facebook: ['Facebook', 'fa-facebook-f'], instagram: ['Instagram', 'fa-instagram'], tiktok: ['TikTok', 'fa-tiktok'],
  youtube: ['YouTube', 'fa-youtube'], linkedin: ['LinkedIn', 'fa-linkedin-in'], x: ['X', 'fa-x-twitter'],
}

export default {
  name: 'LandingContactos',
  components: { LandingCabecalho, LandingFoto },
  mixins: [revelar],
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
  },
  computed: {
    contactos () { return listaContactos(this.s) },
    // o botão principal: WhatsApp se houver, senão o email
    principal () { return this.contactos.find(c => c.chave === 'whatsapp') || this.contactos.find(c => c.chave === 'email') || null },
    redes () {
      return Object.entries(this.s.redes || {}).filter(([k, v]) => REDES[k] && v)
        .map(([k, url]) => ({ rede: k, url, nome: REDES[k][0], icone: REDES[k][1] }))
    },
  },
}
</script>

<style scoped>
.pontos { background-image: radial-gradient(circle, #fff 1.5px, transparent 1.5px); background-size: 26px 26px; }
.foto, .contacto { opacity: 0; }
.visivel .foto { opacity: 1; animation: entrar .9s ease backwards; }
.visivel .contacto { opacity: 1; animation: subir .6s ease backwards; animation-delay: calc(var(--atraso) + 250ms); }
@keyframes entrar { from { opacity: 0; } }
@keyframes subir { from { opacity: 0; transform: translateY(1rem); } }
@media (prefers-reduced-motion: reduce) { .foto, .contacto { opacity: 1; animation: none !important; } }
</style>
