<!-- BarraEdicao.vue — barra do modo de edição da landing page (admin com gerir_home): estado do rascunho,
     Secções (ordem e visibilidade), Histórico (restaurar uma publicação), Descartar, Repor textos de origem,
     Pré-visualizar como visitante, Publicar e Sair. As acções são emitidas; o Sobre.vue fala com o servidor. -->
<template>
  <div class="fixed top-16 inset-x-0 z-40 bg-zinc-900/95 backdrop-blur border-b border-red-600/40 text-zinc-100 shadow-lg" data-teste="barra-edicao">
    <div class="max-w-7xl mx-auto px-3 sm:px-6 py-2 flex items-center gap-2 overflow-x-auto">
      <span class="flex items-center gap-2 text-xs font-bold whitespace-nowrap pr-2">
        <span class="w-2 h-2 rounded-full" :class="alteracoes ? 'bg-amber-400' : 'bg-emerald-500'"></span>
        <span data-teste="edicao-estado">{{ alteracoes ? 'Rascunho com alterações por publicar' : 'Tudo publicado' }}</span>
      </span>
      <span class="flex-1"></span>
      <label class="flex items-center gap-1.5 text-xs whitespace-nowrap px-2 cursor-pointer">
        <input type="checkbox" :checked="visitante" @change="$emit('visitante', $event.target.checked)" class="accent-red-600" data-teste="edicao-visitante" />
        Ver como visitante
      </label>
      <button type="button" class="botao" @click="painel = painel === 'seccoes' ? '' : 'seccoes'" data-teste="edicao-seccoes">
        <font-awesome-icon :icon="['fas', 'layer-group']" class="mr-1" />Secções</button>
      <button type="button" class="botao" @click="abrirHistorico" data-teste="edicao-historico">
        <font-awesome-icon :icon="['fas', 'clock-rotate-left']" class="mr-1" />Histórico</button>
      <button type="button" class="botao" :disabled="!alteracoes || ocupado" @click="confirmar = 'descartar'" data-teste="edicao-descartar">Descartar</button>
      <button type="button" class="botao !bg-red-600 hover:!bg-red-500 font-bold" :disabled="!alteracoes || ocupado" @click="confirmar = 'publicar'"
              data-teste="edicao-publicar"><font-awesome-icon :icon="['fas', 'upload']" class="mr-1" />Publicar</button>
      <button type="button" class="botao" @click="$emit('sair')" data-teste="edicao-sair">Sair da edição</button>
    </div>

    <!-- confirmações -->
    <div v-if="confirmar" class="border-t border-zinc-800 bg-zinc-950">
      <div class="max-w-7xl mx-auto px-3 sm:px-6 py-3 flex flex-wrap items-center gap-3 text-sm" data-teste="edicao-confirmar">
        <span v-if="confirmar === 'publicar'">Publicar? Os visitantes passam a ver o rascunho já.</span>
        <span v-else-if="confirmar === 'descartar'">Descartar as alterações? O rascunho volta a ficar igual ao que está publicado.</span>
        <span v-else-if="confirmar === 'padrao'">Repor os textos de origem no rascunho? Imagens, vídeos, tutoriais e perguntas que acrescentaste saem
          do rascunho (o publicado não muda até publicares).</span>
        <span v-else>Carregar esta publicação no rascunho? (o publicado não muda até publicares)</span>
        <button type="button" class="botao !bg-red-600 font-bold" @click="ok" data-teste="edicao-confirmar-sim">Sim</button>
        <button type="button" class="botao" @click="confirmar = ''">Cancelar</button>
      </div>
    </div>

    <!-- secções: ordem e visibilidade -->
    <div v-if="painel === 'seccoes'" class="border-t border-zinc-800 bg-zinc-950" data-teste="edicao-painel-seccoes">
      <div class="max-w-xl mx-auto px-3 sm:px-6 py-3 space-y-1.5">
        <div v-for="(s, n) in seccoes" :key="s.tipo" class="flex items-center gap-2 rounded-lg bg-zinc-900 px-3 py-2 text-sm" :data-teste="'ordem-' + s.tipo">
          <span class="flex-1 truncate" :class="s.ativa ? '' : 'text-zinc-500 line-through'">{{ nomes[s.tipo] || s.tipo }}</span>
          <button type="button" class="mini" :disabled="n === 0 || ocupado" @click="mover(n, -1)" aria-label="Subir" :data-teste="'ordem-subir-' + s.tipo">
            <font-awesome-icon :icon="['fas', 'arrow-up']" /></button>
          <button type="button" class="mini" :disabled="n === seccoes.length - 1 || ocupado" @click="mover(n, 1)" aria-label="Descer"
                  :data-teste="'ordem-descer-' + s.tipo"><font-awesome-icon :icon="['fas', 'arrow-down']" /></button>
          <button type="button" class="mini" :disabled="ocupado" @click="$emit('visibilidade', s.tipo, !s.ativa)"
                  :aria-label="s.ativa ? 'Esconder' : 'Mostrar'" :data-teste="'ordem-ver-' + s.tipo">
            <font-awesome-icon :icon="['fas', s.ativa ? 'eye' : 'eye-slash']" /></button>
        </div>
        <button type="button" class="mt-2 text-xs text-zinc-400 hover:text-zinc-200 underline" @click="confirmar = 'padrao'" data-teste="edicao-padrao">
          Repor os textos de origem</button>
      </div>
    </div>

    <!-- histórico -->
    <div v-if="painel === 'historico'" class="border-t border-zinc-800 bg-zinc-950" data-teste="edicao-painel-historico">
      <div class="max-w-xl mx-auto px-3 sm:px-6 py-3 space-y-1.5 max-h-72 overflow-y-auto">
        <p v-if="!historico.length" class="text-xs text-zinc-500">Ainda nada foi publicado — os visitantes vêem os textos de origem.</p>
        <div v-for="(p, n) in historico" :key="p.id" class="flex items-center gap-3 rounded-lg bg-zinc-900 px-3 py-2 text-sm" data-teste="historico-item">
          <span class="flex-1">{{ data(p.em) }} <span class="text-zinc-500">· {{ p.por || '—' }}</span>
            <span v-if="n === 0" class="ml-1 text-[10px] font-bold uppercase text-emerald-400">em uso</span></span>
          <button type="button" class="botao" :disabled="ocupado" @click="aRestaurar = p.id; confirmar = 'restaurar'" data-teste="historico-restaurar">Restaurar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BarraEdicao',
  props: {
    seccoes: { type: Array, default: () => [] },     // rascunho (ordem, ativa)
    nomes: { type: Object, default: () => ({}) },
    alteracoes: { type: Boolean, default: false },
    visitante: { type: Boolean, default: false },
    ocupado: { type: Boolean, default: false },
    historico: { type: Array, default: () => [] },
  },
  emits: ['publicar', 'descartar', 'padrao', 'restaurar', 'ordem', 'visibilidade', 'historico', 'visitante', 'sair'],
  data () { return { painel: '', confirmar: '', aRestaurar: null } },
  methods: {
    abrirHistorico () {
      this.painel = this.painel === 'historico' ? '' : 'historico'
      if (this.painel) this.$emit('historico')
    },
    mover (n, d) {
      const l = this.seccoes.map(s => s.tipo)
      ;[l[n], l[n + d]] = [l[n + d], l[n]]
      this.$emit('ordem', l)
    },
    ok () {
      const c = this.confirmar
      this.confirmar = ''
      if (c === 'restaurar') { this.$emit('restaurar', this.aRestaurar); this.painel = '' } else this.$emit(c)
    },
    data (iso) {
      try { return new Date(iso).toLocaleString('pt-PT', { dateStyle: 'medium', timeStyle: 'short' }) } catch (e) { return iso }
    },
  },
}
</script>

<style scoped>
.botao { white-space: nowrap; padding: 0.4rem 0.75rem; border-radius: 0.6rem; font-size: 0.75rem; font-weight: 600; background: #27272a; color: #e4e4e7; }
.botao:hover:not(:disabled) { background: #3f3f46; }
.botao:disabled { opacity: 0.4; }
.mini { width: 1.9rem; height: 1.9rem; border-radius: 0.5rem; font-size: 0.75rem; background: #27272a; color: #a1a1aa; }
.mini:hover:not(:disabled) { background: #3f3f46; color: #fff; }
.mini:disabled { opacity: 0.3; }
</style>
