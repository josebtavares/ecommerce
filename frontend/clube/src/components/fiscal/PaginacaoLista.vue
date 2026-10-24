<!-- PaginacaoLista.vue — "1–20 de 134" + páginas. count/limit/offset como o backend (?limit=&offset=); emite 'ir' com o novo offset.
     claro: para as páginas de fundo branco (POS). -->
<template>
  <div v-if="count > limit" class="flex flex-wrap items-center justify-between gap-2" data-teste="paginacao">
    <p :class="['text-xs', claro ? 'text-slate-500 font-semibold' : 'text-zinc-500']">{{ offset + 1 }}–{{ Math.min(offset + limit, count) }} de {{ count }}</p>
    <div class="flex items-center gap-1.5">
      <button type="button" @click="ir(pagina - 1)" :disabled="pagina <= 1" aria-label="Página anterior"
        :class="['w-8 h-8 rounded-lg disabled:opacity-30', neutro]">‹</button>
      <button v-for="p in visiveis" :key="p" type="button" @click="ir(p)" :aria-current="p === pagina ? 'page' : null"
        :class="['w-8 h-8 rounded-lg text-xs font-bold', p === pagina ? (claro ? 'bg-slate-900 text-white' : 'bg-red-600 text-white') : neutro]">{{ p }}</button>
      <button type="button" @click="ir(pagina + 1)" :disabled="pagina >= paginas" aria-label="Página seguinte"
        :class="['w-8 h-8 rounded-lg disabled:opacity-30', neutro]">›</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaginacaoLista',
  props: {
    count:  { type: Number, required: true },
    limit:  { type: Number, required: true },
    offset: { type: Number, required: true },
    claro:  { type: Boolean, default: false },
  },
  emits: ['ir'],
  computed: {
    neutro () { return this.claro ? 'bg-slate-100 hover:bg-slate-200 text-slate-600' : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-400' },
    pagina () { return Math.floor(this.offset / this.limit) + 1 },
    paginas () { return Math.ceil(this.count / this.limit) },
    visiveis () {
      const ini = Math.max(1, Math.min(this.pagina - 2, this.paginas - 4))
      const fim = Math.min(this.paginas, ini + 4)
      return Array.from({ length: fim - ini + 1 }, (_, i) => ini + i)
    },
  },
  methods: {
    ir (p) {
      if (p >= 1 && p <= this.paginas && p !== this.pagina) this.$emit('ir', (p - 1) * this.limit)
    },
  },
}
</script>
