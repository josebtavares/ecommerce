<template>
  <!-- Botão de descarregar um PDF (fatura, comprovativo): ícone, e o texto se houver. Com href é um link (abre o
       ficheiro noutro separador); sem href emite click (PDF gerado no servidor). claro: fundo branco (POS, cliente). -->
  <a v-if="href" :href="href" target="_blank" rel="noopener" :title="titulo" :aria-label="texto ? null : titulo" :class="classes" :data-teste="teste || null">
    <font-awesome-icon :icon="['fas', 'file-arrow-down']" /><span v-if="texto">{{ texto }}</span>
  </a>
  <button v-else type="button" @click="$emit('click')" :title="titulo" :aria-label="texto ? null : titulo" :class="classes" :data-teste="teste || null">
    <font-awesome-icon :icon="['fas', 'file-arrow-down']" /><span v-if="texto">{{ texto }}</span>
  </button>
</template>

<script>
export default {
  name: 'BotaoPdf',
  props: {
    href: { type: String, default: '' },
    texto: { type: String, default: '' },
    titulo: { type: String, default: 'Descarregar PDF' },
    claro: { type: Boolean, default: false },
    teste: { type: String, default: '' },
  },
  emits: ['click'],
  computed: {
    classes () {
      return ['inline-flex items-center justify-center gap-1.5 h-7 rounded-lg border text-[11px] font-semibold transition flex-shrink-0',
        this.texto ? 'px-2.5' : 'w-7',
        this.claro ? 'border-slate-200 bg-white hover:bg-slate-100 text-slate-700' : 'border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-200']
    },
  },
}
</script>
