<!-- PaginaConteudo.vue — corpo de uma página institucional (texto, contactos, FAQ).
     Usado no popup (PaginaInfoModal) e na página com endereço próprio (views/PaginaPublica.vue). -->
<template>
  <div>
    <!-- Texto livre -->
    <div v-if="blocos.length" class="space-y-3 text-sm leading-relaxed"
         :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
      <template v-for="(b, i) in blocos" :key="i">
        <h3 v-if="b.tipo === 'titulo'" class="text-base font-bold pt-2"
            :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ b.texto }}</h3>
        <ul v-else-if="b.tipo === 'lista'" class="space-y-1.5 pl-1">
          <li v-for="(item, j) in b.itens" :key="j" class="flex gap-2.5">
            <span class="mt-2 w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0"></span>
            <span>{{ item }}</span>
          </li>
        </ul>
        <p v-else class="whitespace-pre-line">{{ b.texto }}</p>
      </template>
    </div>

    <!-- Contacto -->
    <div v-if="pagina.slug === 'contacto' && contactos.length"
         class="grid grid-cols-1 sm:grid-cols-2 gap-3" :class="blocos.length ? 'mt-6' : ''">
      <component :is="c.href ? 'a' : 'div'" v-for="c in contactos" :key="c.chave"
         :href="c.href" :target="c.externo ? '_blank' : null" rel="noopener"
         class="flex items-start gap-3 p-4 rounded-2xl border transition"
         :class="[
           isDark ? 'bg-zinc-950/50 border-zinc-800' : 'bg-stone-50 border-stone-200',
           c.href && (isDark ? 'hover:border-red-500/50' : 'hover:border-red-300'),
         ]">
        <span class="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0 bg-red-500/10 text-red-500"><font-awesome-icon :icon="['fas', c.icone]" class="w-4 h-4" /></span>
        <span class="min-w-0">
          <span class="block text-[11px] uppercase tracking-wider font-semibold"
                :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ c.label }}</span>
          <span class="block text-sm font-semibold break-words">{{ c.valor }}</span>
        </span>
      </component>
    </div>

    <!-- FAQ -->
    <div v-if="pagina.slug === 'faq'" class="space-y-2" :class="blocos.length ? 'mt-6' : ''">
      <p v-if="!perguntas.length" class="text-sm text-center py-6" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
        Ainda não há perguntas frequentes.
      </p>
      <div v-for="(q, i) in perguntas" :key="i"
           class="rounded-2xl border overflow-hidden transition"
           :class="[
             isDark ? 'border-zinc-800' : 'border-stone-200',
             faqAberta === i && (isDark ? 'bg-zinc-950/50' : 'bg-stone-50'),
           ]">
        <button @click="faqAberta = faqAberta === i ? null : i"
          class="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left text-sm font-semibold"
          :aria-expanded="faqAberta === i">
          <span>{{ q.pergunta }}</span>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 flex-shrink-0 transition-transform duration-200"
               :class="[faqAberta === i && 'rotate-180', isDark ? 'text-zinc-500' : 'text-zinc-400']"
               fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <p v-if="faqAberta === i" class="px-4 pb-4 -mt-1 text-sm leading-relaxed whitespace-pre-line"
           :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ q.resposta }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { parseConteudo, listaContactos } from '@/utils/paginas'

export default {
  name: 'PaginaConteudo',

  props: {
    pagina: { type: Object, required: true },   // { slug, conteudo, dados }
    isDark: { type: Boolean, default: true },
  },

  data () {
    return { faqAberta: null }
  },

  computed: {
    blocos () { return parseConteudo(this.pagina.conteudo) },
    perguntas () { return this.pagina.dados?.perguntas || [] },
    contactos () { return listaContactos(this.pagina.dados) },
  },

  watch: {
    'pagina.slug' () { this.faqAberta = null },
  },
}
</script>
