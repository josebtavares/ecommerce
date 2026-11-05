<!-- VerProva.vue — ver a prova de entrega no site (foto, assinatura, quem recebeu), com descarregar cada imagem.
     Os links são assinados (1 h; backend Views/entregaProvaView.prova_ficheiro — ?baixar=1 descarrega). -->
<template>
  <div class="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-sm"
       @click.self="$emit('fechar')">
    <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-2xl max-h-[94vh] overflow-y-auto p-4 sm:p-5 space-y-4 shadow-2xl"
         role="dialog" aria-modal="true" :aria-label="`Prova da encomenda #${entrega.encomenda}`" data-teste="ver-prova">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-base font-bold text-zinc-100">Prova de entrega · #{{ entrega.encomenda }}</h3>
          <p class="text-xs text-zinc-500 mt-0.5">
            <template v-if="entrega.data_entrega">Entregue em {{ entrega.data_entrega }}</template>
            <template v-if="p.recebido_por"> · Recebido por <strong class="text-zinc-300">{{ p.recebido_por }}</strong></template>
          </p>
        </div>
        <button type="button" @click="$emit('fechar')" aria-label="Fechar" data-teste="ver-prova-fechar"
          class="w-8 h-8 flex-shrink-0 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-lg leading-none">×</button>
      </div>

      <section v-if="p.foto" class="space-y-2">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-zinc-300">Foto</p>
          <a :href="baixar(p.foto)" download data-teste="baixar-foto"
             class="text-xs font-semibold text-red-400 hover:text-red-300"><font-awesome-icon :icon="['fas', 'download']" class="mr-1" />Descarregar</a>
        </div>
        <img :src="p.foto" alt="Foto da entrega" class="w-full max-h-[60vh] object-contain rounded-xl bg-black" data-teste="ver-foto" />
      </section>

      <section v-if="p.assinatura" class="space-y-2">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-zinc-300">Assinatura do cliente</p>
          <a :href="baixar(p.assinatura)" download data-teste="baixar-assinatura"
             class="text-xs font-semibold text-red-400 hover:text-red-300"><font-awesome-icon :icon="['fas', 'download']" class="mr-1" />Descarregar</a>
        </div>
        <img :src="p.assinatura" alt="Assinatura do cliente" class="w-full max-h-56 object-contain rounded-xl bg-white" data-teste="ver-assinatura" />
      </section>

      <p v-if="!p.foto && !p.assinatura" class="text-sm text-zinc-400">Só ficou registado o nome de quem recebeu.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VerProva',
  props: { entrega: { type: Object, required: true } },
  emits: ['fechar'],
  computed: { p () { return this.entrega.prova || {} } },
  mounted () { this.tecla = e => { if (e.key === 'Escape') this.$emit('fechar') }; window.addEventListener('keydown', this.tecla) },
  beforeUnmount () { window.removeEventListener('keydown', this.tecla) },
  methods: {
    baixar (url) { return url + (url.includes('?') ? '&' : '?') + 'baixar=1' },
  },
}
</script>
