<!-- LandingCabecalho.vue — cabeçalho das secções com fotografia (clientes, lojas, contactos): letreiro manuscrito com
     um traço ("— Para clientes"), título com a parte inicial fina e o fim a negrito, e o texto por baixo.
     Título com várias linhas: a primeira fina, o resto a negrito. Numa linha só: a última palavra a negrito. -->
<template>
  <div :class="centro ? 'text-center mx-auto max-w-3xl' : 'max-w-xl'">
    <p v-if="etiqueta" class="flex items-center gap-4 letreiro text-2xl sm:text-[1.7rem] leading-none"
       :class="[centro ? 'justify-center' : '', corDestaque]">
      <span class="w-12 h-0.5 rounded" :class="corTraco"></span>{{ etiqueta }}<span v-if="centro" class="w-12 h-0.5 rounded" :class="corTraco"></span>
    </p>
    <h2 class="titulo-landing mt-4 text-[2.1rem] sm:text-5xl leading-[1.15] tracking-tight" :class="corTitulo">
      <span class="font-light">{{ partes[0] }}</span><br v-if="partes.quebra" /><span class="font-bold">{{ partes[0] && !partes.quebra ? ' ' : '' }}{{ partes[1] }}</span>
    </h2>
    <p v-if="subtitulo" class="mt-6 text-base sm:text-lg leading-relaxed whitespace-pre-line" :class="corTexto">{{ subtitulo }}</p>
  </div>
</template>

<script>
export default {
  name: 'LandingCabecalho',
  props: {
    etiqueta: { type: String, default: '' },
    titulo: { type: String, default: '' },
    subtitulo: { type: String, default: '' },
    isDark: { type: Boolean, default: false },
    centro: { type: Boolean, default: false },
    claro: { type: Boolean, default: false },    // letras brancas (por cima de uma foto escura)
  },
  computed: {
    partes () {
      const t = (this.titulo || '').trim()
      const linhas = t.split('\n').map(l => l.trim()).filter(Boolean)
      if (linhas.length > 1) return Object.assign([linhas[0], linhas.slice(1).join(' ')], { quebra: true })
      const i = t.lastIndexOf(' ')
      return i > 0 ? [t.slice(0, i), t.slice(i + 1)] : ['', t]
    },
    corDestaque () { return this.claro ? 'text-white' : (this.isDark ? 'text-red-400' : 'text-orange-500') },
    corTraco () { return this.claro ? 'bg-white/70' : (this.isDark ? 'bg-red-500' : 'bg-orange-500') },
    corTitulo () { return this.claro ? 'text-white' : (this.isDark ? 'text-white' : 'text-slate-900') },
    corTexto () { return this.claro ? 'text-white/80' : (this.isDark ? 'text-zinc-400' : 'text-slate-500') },
  },
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600&family=Montserrat:wght@300;600;700&display=swap');
.letreiro { font-family: 'Dancing Script', cursive; font-weight: 600; }
.titulo-landing { font-family: 'Montserrat', system-ui, sans-serif; }
</style>
