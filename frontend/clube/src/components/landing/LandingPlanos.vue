<!-- LandingPlanos.vue — "Planos e preços": comissão por venda (opcional) + os planos de subscrição activos,
     lidos do sistema (Admin → Subscrições), com separadores por tipo (Loja online, POS…) quando há vários. -->
<template>
  <section id="planos" class="landing-seccao py-20 sm:py-24 px-5 sm:px-8" data-teste="landing-planos"
           :class="alternado ? (isDark ? 'bg-zinc-900/60' : 'bg-white') : ''">
    <div class="max-w-7xl mx-auto">
      <LandingTitulo :titulo="s.titulo" :subtitulo="s.subtitulo" :isDark="isDark" />

      <div v-if="tipos.length > 1" class="mt-8 flex flex-wrap justify-center gap-2" role="tablist">
        <button v-for="t in tipos" :key="t.tipo" type="button" role="tab" :aria-selected="aba === t.tipo ? 'true' : 'false'"
                @click="aba = t.tipo" :data-teste="'planos-aba-' + t.tipo"
                class="px-4 py-2 rounded-full text-sm font-semibold border transition"
                :class="aba === t.tipo ? (isDark ? 'bg-red-600 border-red-600 text-white' : 'bg-orange-500 border-orange-500 text-white')
                                       : (isDark ? 'border-zinc-700 text-zinc-300 hover:bg-zinc-800' : 'border-stone-300 text-zinc-600 hover:bg-stone-100')">
          {{ t.nome }}</button>
      </div>

      <div class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
        <article v-if="s.mostrar_comissao" data-teste="plano-comissao"
                 class="rounded-3xl border-2 p-7 flex flex-col"
                 :class="isDark ? 'bg-zinc-900 border-red-600/60' : 'bg-white border-orange-400'">
          <p class="text-xs font-bold uppercase tracking-widest" :class="isDark ? 'text-red-400' : 'text-orange-600'">Sem mensalidade</p>
          <h3 class="mt-2 text-xl font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ s.comissao_titulo || 'Comissão por venda' }}</h3>
          <p class="mt-4 flex items-baseline gap-1" :class="isDark ? 'text-white' : 'text-zinc-900'">
            <span class="text-4xl font-extrabold">{{ percentagem }}%</span>
            <span class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">por venda online</span>
          </p>
          <p v-if="s.comissao_texto" class="mt-4 text-sm leading-relaxed whitespace-pre-line" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ s.comissao_texto }}</p>
        </article>

        <article v-for="p in visiveis" :key="p.id" data-teste="plano"
                 class="rounded-3xl border p-7 flex flex-col"
                 :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
          <p class="text-xs font-bold uppercase tracking-widest" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ p.tipo_nome }}</p>
          <h3 class="mt-2 text-xl font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ p.nome }}</h3>
          <p class="mt-4 flex items-baseline gap-1 flex-wrap" :class="isDark ? 'text-white' : 'text-zinc-900'">
            <span class="text-4xl font-extrabold" data-teste="plano-preco">{{ dinheiro(p.preco) }}</span>
            <span class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ POR[p.periodicidade] || '' }}</span>
          </p>
          <p v-if="p.meses > 1" class="mt-1 text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">≈ {{ dinheiro(p.preco / p.meses) }} por mês</p>
          <p v-if="p.descricao" class="mt-4 text-sm leading-relaxed" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ p.descricao }}</p>
          <ul v-if="p.tipo === 'servicos'" class="mt-4 space-y-1.5 text-sm" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
            <li><font-awesome-icon :icon="['fas', 'check']" class="mr-2 opacity-60" />{{ p.limite_marcacoes_mes ? `Até ${p.limite_marcacoes_mes} marcações por mês` : 'Marcações sem limite' }}</li>
            <li><font-awesome-icon :icon="['fas', 'check']" class="mr-2 opacity-60" />{{ p.limite_profissionais ? `Até ${p.limite_profissionais} profissionais` : 'Profissionais sem limite' }}</li>
          </ul>
        </article>
      </div>

      <p v-if="!visiveis.length && !s.mostrar_comissao" class="mt-10 text-center text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
        Em breve.</p>
      <p v-if="s.nota" class="mt-8 text-center text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ s.nota }}</p>
      <div v-if="s.botao" class="mt-8 text-center">
        <a :href="s.botao.link" @click="clique($event, s.botao.link)" data-teste="planos-botao"
           class="inline-flex items-center gap-2 px-6 py-3 rounded-2xl font-bold text-white shadow transition hover:opacity-90"
           :class="isDark ? 'bg-red-600' : 'bg-orange-500'">
          {{ s.botao.texto }} <font-awesome-icon :icon="['fas', 'arrow-right']" class="w-4 h-4" />
        </a>
      </div>
    </div>
  </section>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import LandingTitulo from './LandingTitulo.vue'

const POR = { mensal: '/ mês', trimestral: '/ trimestre', anual: '/ ano' }

export default {
  name: 'LandingPlanos',
  components: { LandingTitulo },
  props: {
    s: { type: Object, required: true },
    isDark: { type: Boolean, default: false },
    alternado: { type: Boolean, default: false },
  },
  emits: ['acao'],
  data () { return { aba: '', POR } },
  computed: {
    planos () { return this.s.planos || [] },
    tipos () {
      const vistos = new Map()
      for (const p of this.planos) if (!vistos.has(p.tipo)) vistos.set(p.tipo, { tipo: p.tipo, nome: p.tipo_nome })
      return [...vistos.values()]
    },
    abaAtual () { return this.tipos.some(t => t.tipo === this.aba) ? this.aba : (this.tipos[0]?.tipo || '') },
    visiveis () { return this.tipos.length > 1 ? this.planos.filter(p => p.tipo === this.abaAtual) : this.planos },
    percentagem () { return String(Number(this.s.comissao_percentagem || 0)).replace('.', ',') },
  },
  watch: { abaAtual: { immediate: true, handler (v) { this.aba = v } } },
  methods: {
    dinheiro (v) { return formatarDinheiro(v) },
    clique (e, link) {
      if (e.ctrlKey || e.metaKey || e.shiftKey) return
      e.preventDefault()
      this.$emit('acao', link)
    },
  },
}
</script>
