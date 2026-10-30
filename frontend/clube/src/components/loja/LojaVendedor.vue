<!-- LojaVendedor.vue — "Vendido por": quem vende, contactos e políticas da loja.
     No checkout (compacto). Só mostra as políticas que a loja escreveu: as da Bende estão no rodapé do site. -->
<template>
  <section :class="compacto ? '' : ['border-t py-8 px-6 md:px-12', isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-stone-50 border-stone-200']"
           data-teste="loja-vendedor">
    <div :class="compacto ? '' : 'max-w-7xl mx-auto'">
      <p class="text-[11px] font-bold uppercase tracking-[0.18em]" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Vendido por</p>
      <p class="text-base font-bold mt-0.5" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
        {{ v.nome }} <SeloVerificada :loja="loja" class="ml-1" />
      </p>
      <ul class="mt-2 space-y-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
        <li v-if="v.nif">NIF {{ v.nif }}</li>
        <li v-if="v.morada" class="flex items-start gap-2">
          <font-awesome-icon :icon="['fas', 'location-dot']" class="w-3.5 h-3.5 mt-1 opacity-70" fixed-width />{{ v.morada }}
        </li>
        <li v-if="v.email" class="flex items-start gap-2">
          <font-awesome-icon :icon="['fas', 'envelope']" class="w-3.5 h-3.5 mt-1 opacity-70" fixed-width />
          <a :href="'mailto:' + v.email" class="hover:text-red-500 break-all">{{ v.email }}</a>
        </li>
        <li v-if="v.telefone" class="flex items-start gap-2">
          <font-awesome-icon :icon="['fas', 'phone']" class="w-3.5 h-3.5 mt-1 opacity-70" fixed-width />
          <a :href="'tel:' + v.telefone.replace(/[^\d+]/g, '')" class="hover:text-red-500">{{ v.telefone }}</a>
        </li>
      </ul>
      <p class="mt-3 text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
        A loja é responsável pelos produtos, pela entrega e pelas devoluções.
      </p>
      <div v-if="politicas.length || politicasBende.length" class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <button v-for="p in politicas" :key="p.chave" type="button" @click="aberta = p" :data-teste="'politica-' + p.chave"
          class="font-semibold text-red-500 hover:text-red-400 underline-offset-2 hover:underline">{{ p.titulo }}</button>
        <!-- a loja não escreveu a sua: aplicam-se as da Bende (contrato SISP, cl.3: devoluções e entregas visíveis) -->
        <router-link v-for="p in politicasBende" :key="p.chave" :to="'/' + p.chave" target="_blank" :data-teste="'politica-bende-' + p.chave"
          class="font-semibold text-red-500 hover:text-red-400 underline-offset-2 hover:underline">{{ p.titulo }}</router-link>
      </div>
    </div>

    <PaginaInfoModal v-if="aberta" :pagina="{ slug: aberta.chave, seccao: 'legal', titulo: `${aberta.titulo} — ${v.nome}`, conteudo: aberta.texto }"
      :isDark="isDark" @close="aberta = null" />
  </section>
</template>

<script>
import PaginaInfoModal from '@/components/paginas/PaginaInfoModal.vue'
import SeloVerificada from './SeloVerificada.vue'

export default {
  name: 'LojaVendedor',
  components: { PaginaInfoModal, SeloVerificada },

  props: {
    loja:     { type: Object, required: true },   // LojaPublicSerializer: vendedor + políticas
    isDark:   { type: Boolean, default: true },
    compacto: { type: Boolean, default: false },   // checkout: sem faixa nem margens
  },

  data () {
    return { aberta: null }
  },

  computed: {
    v () { return this.loja.vendedor || { nome: this.loja.nome } },

    politicas () {
      const l = this.loja
      const prazo = l.prazo_devolucao_dias ? `Prazo para pedir a devolução: ${l.prazo_devolucao_dias} dias.` : ''
      const devolucao = [prazo, l.politica_devolucao].filter(x => String(x || '').trim()).join('\n\n')
      return [
        { chave: 'devolucoes',  titulo: 'Devoluções',  texto: l.politica_devolucao ? devolucao : '' },
        { chave: 'entregas',    titulo: 'Entregas',    texto: l.politica_entregas },
        { chave: 'termos',      titulo: 'Termos',      texto: l.termos_servico },
        { chave: 'privacidade', titulo: 'Privacidade', texto: l.politica_privacidade },
      ].map(p => ({ ...p, texto: String(p.texto || '').trim() })).filter(p => p.texto)   // só as da loja
    },

    politicasBende () {
      const proprias = this.politicas.map(p => p.chave)
      return [{ chave: 'devolucoes', titulo: 'Devoluções' }, { chave: 'entregas', titulo: 'Entregas' }]
        .filter(p => !proprias.includes(p.chave))
    },
  },
}
</script>
