<!-- AdminPesquisas.vue — Admin → Pesquisas: o que os clientes procuram na barra, o que não encontram e onde
     clicam (backend utils/pesquisa_stats.py). Sem utilizadores nem IPs — só contagens. Permissão ver_stats. -->
<template>
  <div class="space-y-5" data-teste="admin-pesquisas">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-xs text-zinc-500 max-w-xl">
        Conta uma pesquisa quando o cliente vê os resultados e pára de escrever (ou clica num). Os registos têm
        {{ 180 }} dias e não guardam quem pesquisou.
      </p>
      <div class="flex rounded-xl border border-zinc-700 overflow-hidden" role="group" aria-label="Período">
        <button v-for="p in PERIODOS" :key="p" type="button" @click="mudar(p)" :data-teste="'pesq-dias-' + p"
          :aria-pressed="dias === p"
          :class="['px-3 py-1.5 text-xs font-semibold transition', dias === p ? 'bg-red-600 text-white' : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200']">
          {{ p }} dias
        </button>
      </div>
    </div>

    <div v-if="loading && !d" class="space-y-3">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="n in 4" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div>
      </div>
      <div class="h-56 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>
    <p v-else-if="erro" class="text-sm text-red-400">{{ erro }}</p>

    <template v-else-if="d">
      <!-- indicadores -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3" :class="loading && 'opacity-60'" data-teste="pesq-resumo">
        <div v-for="k in kpis" :key="k.label" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
          <p class="text-2xl font-extrabold" :class="k.cor">{{ k.valor }}</p>
          <p class="text-xs text-zinc-500 mt-0.5">{{ k.label }}</p>
          <p v-if="k.nota" class="text-[11px] text-zinc-600 mt-1">{{ k.nota }}</p>
        </div>
      </div>

      <div v-if="!d.resumo.total" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center" data-teste="pesq-vazio">
        <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="text-2xl text-zinc-600" />
        <p class="mt-3 text-sm text-zinc-400">Ainda não há pesquisas nos últimos {{ dias }} dias.</p>
      </div>

      <template v-else>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
          <GraficoTempo titulo="Pesquisas por dia" subtitulo="a vermelho, as que não encontraram nada"
                        :dados="grafico" granularidade="dia" :dinheiro="false"
                        :series="[{ chave: 'com', label: 'Com resultados', cor: COR_1 }, { chave: 'sem', label: 'Sem resultados', cor: COR_2 }]"
                        chave-total="total" label-total="Pesquisas" vazio="Sem pesquisas neste período" />
        </div>

        <div class="grid lg:grid-cols-2 gap-5">
          <!-- sem resultados: o que mais interessa -->
          <section class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5" data-teste="pesq-sem-resultados">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Procuram e não encontram</h3>
            <p class="text-xs text-zinc-600 mt-0.5 mb-3">Produtos que faltam no catálogo, lojas a convidar ou palavras que a pesquisa não conhece.</p>
            <Tabela :linhas="d.sem_resultados" vazio="Todas as pesquisas encontraram alguma coisa."
                    :colunas="[{ k: 'total', t: 'Vezes' }, { k: 'sessoes', t: 'Pessoas' }, { k: 'ultima', t: 'Última' }]" />
          </section>

          <section class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5" data-teste="pesq-top">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Mais procuradas</h3>
            <p class="text-xs text-zinc-600 mt-0.5 mb-3">"Cliques": em quantas dessas pesquisas o cliente abriu um resultado.</p>
            <Tabela :linhas="d.top" vazio="—"
                    :colunas="[{ k: 'total', t: 'Vezes' }, { k: 'sessoes', t: 'Pessoas' }, { k: 'cliques', t: 'Cliques', pct: true }]" />
          </section>

          <section class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5" data-teste="pesq-sem-clique">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Encontram mas não clicam</h3>
            <p class="text-xs text-zinc-600 mt-0.5 mb-3">Têm resultados mas ninguém abriu nenhum: talvez não sejam o que procuravam.</p>
            <Tabela :linhas="d.sem_clique" vazio="Nada a assinalar."
                    :colunas="[{ k: 'total', t: 'Vezes' }, { k: 'resultados', t: 'Resultados' }]" />
          </section>

          <section class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5" data-teste="pesq-clicados">
            <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Mais abertos a partir da pesquisa</h3>
            <p class="text-xs text-zinc-600 mt-0.5 mb-3">Produtos, lojas e serviços em que os clientes clicaram.</p>
            <p v-if="!d.mais_clicados.length" class="text-sm text-zinc-500 py-3">Ainda sem cliques.</p>
            <ul v-else class="divide-y divide-zinc-800">
              <li v-for="c in d.mais_clicados" :key="c.tipo + (c.id || c.nome)" class="flex items-center gap-3 py-2">
                <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase flex-shrink-0" :class="CORES_TIPO[c.tipo] || 'bg-zinc-800 text-zinc-400'">{{ ROTULO_TIPO[c.tipo] || c.tipo }}</span>
                <a v-if="ligacao(c)" :href="ligacao(c)" target="_blank" rel="noopener" class="flex-1 min-w-0 truncate text-sm text-zinc-200 hover:text-red-400">{{ c.nome }}</a>
                <span v-else class="flex-1 min-w-0 truncate text-sm text-zinc-500">{{ c.nome }}{{ c.existe ? '' : ' (já não existe)' }}</span>
                <span class="text-sm font-semibold text-zinc-300 tabular-nums">{{ c.total }}</span>
              </li>
            </ul>
          </section>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { h } from 'vue'
import api from '@/services/api'
import GraficoTempo from '@/components/relatorios/GraficoTempo.vue'

const PERIODOS = [7, 30, 90]

// tabela simples: pesquisa (como foi escrita) + colunas numéricas
const Tabela = {
  props: { linhas: Array, colunas: Array, vazio: String },
  setup (props) {
    return () => !props.linhas?.length
      ? h('p', { class: 'text-sm text-zinc-500 py-3' }, props.vazio)
      : h('div', { class: 'overflow-x-auto -mx-1' }, h('table', { class: 'w-full text-sm' }, [
        h('thead', h('tr', { class: 'text-[11px] text-zinc-500 uppercase tracking-wider' }, [
          h('th', { class: 'text-left font-semibold px-1 pb-2' }, 'Pesquisa'),
          ...props.colunas.map(c => h('th', { class: 'text-right font-semibold px-1 pb-2 whitespace-nowrap' }, c.t)),
        ])),
        h('tbody', props.linhas.map(l => h('tr', { class: 'border-t border-zinc-800' }, [
          h('td', { class: 'px-1 py-1.5 text-zinc-200 max-w-[14rem] truncate', title: l.texto }, l.texto),
          ...props.colunas.map(c => h('td', { class: 'px-1 py-1.5 text-right text-zinc-400 tabular-nums whitespace-nowrap' },
            c.pct ? `${l[c.k]} (${l.total ? Math.round(100 * l[c.k] / l.total) : 0}%)` : String(l[c.k]))),
        ]))),
      ]))
  },
}

export default {
  name: 'AdminPesquisas',
  components: { GraficoTempo, Tabela },

  data () {
    return {
      PERIODOS, dias: 30, d: null, loading: false, erro: '',
      COR_1: '#3987e5', COR_2: '#d95926',
      ROTULO_TIPO: { produto: 'Produto', loja: 'Loja', servico: 'Serviço', categoria: 'Categoria' },
      CORES_TIPO: { produto: 'bg-sky-500/15 text-sky-300', loja: 'bg-emerald-500/15 text-emerald-300',
                    servico: 'bg-violet-500/15 text-violet-300', categoria: 'bg-amber-500/15 text-amber-300' },
    }
  },

  computed: {
    kpis () {
      const r = this.d.resumo
      const pct = v => v == null ? '—' : `${v.toLocaleString('pt-PT')}%`
      return [
        { label: 'Pesquisas', valor: r.total.toLocaleString('pt-PT'), cor: 'text-zinc-100',
          nota: r.na_pagina ? `${r.na_pagina} na página de resultados` : '' },
        { label: 'Pessoas (separadores)', valor: r.sessoes.toLocaleString('pt-PT'), cor: 'text-zinc-100' },
        { label: 'Sem resultados', valor: pct(r.taxa_sem_resultados), cor: r.taxa_sem_resultados > 20 ? 'text-amber-400' : 'text-zinc-100',
          nota: `${r.sem_resultados} pesquisa(s)` },
        { label: 'Abriram um resultado', valor: pct(r.taxa_clique), cor: 'text-emerald-400', nota: 'das que tinham resultados' },
      ]
    },
    grafico () {
      return this.d.por_dia.map(l => ({ dia: l.dia, com: l.total - l.sem_resultados, sem: l.sem_resultados, total: l.total }))
    },
  },

  mounted () {
    try { const v = Number(localStorage.getItem('admin_pesquisas_dias')); if (PERIODOS.includes(v)) this.dias = v } catch (e) { /* sem localStorage */ }
    this.carregar()
  },

  methods: {
    mudar (p) {
      this.dias = p
      try { localStorage.setItem('admin_pesquisas_dias', String(p)) } catch (e) { /* nada */ }
      this.carregar()
    },
    async carregar () {
      this.loading = true
      this.erro = ''
      try {
        const { data } = await api.get('/app/admin/pesquisas/', { params: { dias: this.dias } })
        this.d = data
      } catch (e) {
        this.erro = e.response?.status === 403 ? 'Sem permissão para ver as pesquisas.' : 'Não foi possível carregar as pesquisas.'
      } finally {
        this.loading = false
      }
    },
    ligacao (c) {
      if (!c.existe || !c.id) return ''
      if (c.tipo === 'loja') return `/loja/${c.id}`
      if (c.tipo === 'produto' && c.loja_id) return `/loja/${c.loja_id}?produto=${c.id}`
      if (c.tipo === 'servico' && c.loja_id) return `/loja/${c.loja_id}?servico=${c.id}`
      return ''
    },
  },
}
</script>
