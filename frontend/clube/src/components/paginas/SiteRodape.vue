<!-- SiteRodape.vue — rodapé comum (home, lojas, checkout, páginas institucionais):
     links Suporte/Legal com endereço próprio, contactos e titular do site (Admin → Definições).
     A SISP e o banco revêem estes dados antes de activar o pagamento com cartão.
     Slots: "marca" (coluna da esquerda) e "colunas" (colunas extra, ex.: Explorar na home). -->
<template>
  <footer class="border-t pt-10 pb-28 px-6 md:px-12" data-teste="site-rodape"
          :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
    <div class="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8">
      <div>
        <slot name="marca">
          <router-link to="/" aria-label="Página inicial">
            <img :src="(temaEscuro ?? isDark) ? logoLight : logoDefault" alt="Logo" class="w-24 h-24 object-contain mb-2" />
          </router-link>
        </slot>
      </div>
      <slot name="colunas" />
      <div v-for="sec in seccoes" :key="sec.key">
        <h4 class="text-xs font-semibold uppercase tracking-wider mb-4" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">{{ sec.label }}</h4>
        <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
          <li v-for="p in sec.paginas" :key="p.slug">
            <router-link :to="'/' + p.slug" class="hover:text-red-500 transition">{{ p.titulo }}</router-link>
          </li>
        </ul>
      </div>
      <div v-if="contactos.length" data-teste="rodape-contactos">
        <h4 class="text-xs font-semibold uppercase tracking-wider mb-4" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">Contactos</h4>
        <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
          <li v-for="c in contactos" :key="c.chave" class="flex items-start gap-2">
            <font-awesome-icon :icon="['fas', c.icone]" class="w-3.5 h-3.5 mt-1 flex-shrink-0 opacity-70" fixed-width />
            <a v-if="c.href" :href="c.href" :target="c.externo ? '_blank' : null" rel="noopener"
               class="hover:text-red-500 transition break-words min-w-0">{{ c.valor }}</a>
            <span v-else class="break-words min-w-0">{{ c.valor }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- tudo à esquerda: o botão do chat fica no canto inferior direito -->
    <div class="max-w-7xl mx-auto mt-8 pt-6 border-t flex flex-col gap-4 text-xs"
         :class="isDark ? 'border-zinc-800 text-zinc-500' : 'border-stone-200 text-zinc-400'">
      <div class="space-y-1">
        <p v-if="d.titular_nome" data-teste="rodape-titular">
          Site explorado por <b :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">{{ d.titular_nome }}</b><template v-if="d.titular_nif"> · NIF {{ d.titular_nif }}</template>
        </p>
        <p>Preços em escudos cabo-verdianos (CVE). © {{ ano }} Todos os direitos reservados.</p>
      </div>
      <!-- logótipos dos cartões: só depois do contrato com a SISP (trocar pelos do kit oficial) -->
      <div v-if="d.mostrar_logos_pagamento" class="flex items-center gap-2" data-teste="rodape-logos" aria-label="Cartões aceites">
        <span v-for="l in LOGOS" :key="l" class="px-2 py-1 rounded-md border text-[11px] font-bold tracking-wide"
              :class="isDark ? 'border-zinc-700 text-zinc-300 bg-zinc-800' : 'border-stone-200 text-zinc-600 bg-stone-50'">{{ l }}</span>
      </div>
    </div>
  </footer>
</template>

<script>
import logoDefault from '@/assets/img/login/logo_final_640.webp'
import logoLight from '@/assets/img/login/logo_final_640_light.webp'
import { dadosPlataforma, listaContactos } from '@/utils/paginas'

const SECCOES = [{ key: 'suporte', label: 'Suporte' }, { key: 'legal', label: 'Legal' }]

export default {
  name: 'SiteRodape',

  props: {
    isDark: { type: Boolean, default: true },
    // páginas escritas em escuro (checkout): isDark fica true e o tema-claro.css troca as cores,
    // mas o logótipo é uma imagem — escolhe-se pelo tema real
    temaEscuro: { type: Boolean, default: null },
  },

  data () {
    return { d: {}, logoDefault, logoLight, LOGOS: ['vinti4', 'VISA', 'Mastercard'], ano: new Date().getFullYear() }
  },

  computed: {
    seccoes () {
      const paginas = this.d.paginas || []
      return SECCOES
        .map(s => ({ ...s, paginas: paginas.filter(p => p.seccao === s.key).sort((a, b) => a.ordem - b.ordem) }))
        .filter(s => s.paginas.length)
    },
    contactos () { return listaContactos(this.d.contactos) },
  },

  async created () {
    this.d = (await dadosPlataforma()) || {}
  },
}
</script>
