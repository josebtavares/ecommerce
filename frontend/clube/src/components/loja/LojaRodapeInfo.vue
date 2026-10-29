<!-- LojaRodapeInfo.vue — "Vendido por" dentro do rodapé de cada template da loja: NIF, morada, contactos
     e a política de entregas. Herda a letra e a cor do rodapé do template (sem estilo próprio de tema). -->
<template>
  <div class="lri" data-teste="loja-vendedor">
    <p>
      Vendido por <b>{{ v.nome }}</b> <SeloVerificada :loja="loja" icone />
      <template v-if="v.nif"> · NIF {{ v.nif }}</template>
      <template v-if="v.morada"> · {{ v.morada }}</template>
      <template v-if="v.email"> · <a :href="'mailto:' + v.email">{{ v.email }}</a></template>
      <template v-if="v.telefone"> · <a :href="'tel:' + v.telefone.replace(/[^\d+]/g, '')">{{ v.telefone }}</a></template>
    </p>
    <p>
      A loja é responsável pelos produtos, pela entrega e pelas devoluções.
      <button v-if="entregas" type="button" data-teste="politica-entregas" @click="aberta = true">Política de entregas</button>
    </p>

    <PaginaInfoModal v-if="aberta" :pagina="{ slug: 'entregas', seccao: 'legal', titulo: `Entregas — ${v.nome}`, conteudo: entregas }"
      :isDark="isDark" @close="aberta = false" />
  </div>
</template>

<script>
import PaginaInfoModal from '@/components/paginas/PaginaInfoModal.vue'
import SeloVerificada from './SeloVerificada.vue'

export default {
  name: 'LojaRodapeInfo',
  components: { PaginaInfoModal, SeloVerificada },

  props: {
    loja:   { type: Object, required: true },   // LojaPublicSerializer (vendedor, politica_entregas)
    isDark: { type: Boolean, default: true },
  },

  data () {
    return { aberta: false }
  },

  computed: {
    v () { return this.loja.vendedor || { nome: this.loja.nome } },
    entregas () { return String(this.loja.politica_entregas || '').trim() },
  },
}
</script>

<style scoped>
/* ocupa a linha toda tanto em rodapés em grelha como em flex */
.lri { grid-column: 1 / -1; flex-basis: 100%; width: 100%; margin-top: .75rem; font-size: .75rem; line-height: 1.6; opacity: .8; }
.lri p + p { margin-top: .25rem; }
.lri a, .lri button { color: inherit; text-decoration: underline; text-underline-offset: 2px; }
.lri button { font: inherit; background: none; border: 0; padding: 0; margin-left: .25rem; cursor: pointer; }
</style>
