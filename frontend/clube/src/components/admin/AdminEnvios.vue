<template>
  <!-- Admin → Encomendas: envios por transportadora com problemas (backend utils/envios.problemas).
       Não recebidos, devolvidos por resolver, sem código de rastreio, fecho parado. Abrir → ficha da encomenda. -->
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800" data-teste="admin-envios">
    <button type="button" @click="aberto = !aberto"
            class="w-full flex items-center justify-between gap-3 px-4 py-3 text-left">
      <span class="text-sm font-semibold text-zinc-200">
        <font-awesome-icon :icon="['fas', 'box']" class="mr-1.5 text-zinc-500" />Envios por transportadora
      </span>
      <span class="flex items-center gap-2">
        <span v-if="contagens.problemas" class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/15 text-amber-300"
              data-teste="admin-envios-problemas">{{ contagens.problemas }} com problemas</span>
        <span v-else-if="carregado" class="text-[11px] text-zinc-500">{{ contagens.a_caminho || 0 }} a caminho</span>
        <font-awesome-icon :icon="['fas', aberto ? 'chevron-up' : 'chevron-down']" class="text-zinc-500 text-xs" />
      </span>
    </button>

    <div v-if="aberto" class="border-t border-zinc-800 px-4 py-3 space-y-3">
      <div class="flex flex-wrap gap-2">
        <button v-for="f in FILTROS" :key="f.key" type="button" @click="mudar(f.key)" :data-teste="`admin-envios-filtro-${f.key}`"
                :class="['px-3 py-1 rounded-full text-xs font-semibold transition',
                         filtro === f.key ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ f.label }} <span class="opacity-70">{{ contagens[f.key] ?? '' }}</span>
        </button>
      </div>
      <p class="text-[11px] text-zinc-500">{{ AJUDA[filtro] }}</p>

      <div v-if="aCarregar" class="h-16 rounded-xl bg-zinc-800/50 animate-pulse"></div>
      <p v-else-if="!linhas.length" class="text-xs text-zinc-500 py-2">Nada aqui.</p>
      <div v-else class="space-y-2">
        <button v-for="l in linhas" :key="l.encomenda_id" type="button" @click="$emit('abrir', l.encomenda_id)"
                class="w-full text-left rounded-xl bg-zinc-800/50 hover:bg-zinc-800 px-3 py-2 text-xs transition" data-teste="admin-envio-linha">
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
            <b class="text-zinc-200">#{{ l.encomenda_id }}</b>
            <span class="text-zinc-300">{{ l.loja_nome }}</span>
            <span class="text-zinc-500">{{ l.transportadora }}</span>
            <span class="font-mono text-zinc-400">{{ l.codigos.join(', ') || 'sem código' }}</span>
            <span class="ml-auto flex flex-wrap gap-1.5">
              <span v-if="l.nao_recebido_em" class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 font-semibold">Não recebido</span>
              <span v-if="l.estado === 'devolvida'" class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 font-semibold">Devolvida</span>
              <span v-if="l.parado && !l.nao_recebido_em" class="px-1.5 py-0.5 rounded bg-red-500/15 text-red-300 font-semibold">Fecho parado</span>
              <span v-if="l.estado === 'a_caminho' && !l.codigos.length" class="px-1.5 py-0.5 rounded bg-zinc-700 text-zinc-300">Sem código</span>
            </span>
          </div>
          <p class="text-zinc-500 mt-1">
            Enviada {{ l.dias === 0 ? 'hoje' : `há ${l.dias} dia${l.dias === 1 ? '' : 's'}` }} · cliente {{ l.comprador }}
            <template v-if="l.fecho_previsto_em && !l.nao_recebido_em"> · fecha a {{ data(l.fecho_previsto_em) }}</template>
            <template v-if="l.nao_recebido_nota"> · “{{ l.nao_recebido_nota }}”</template>
          </p>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const FILTROS = [
  { key: 'problemas', label: 'Com problemas' },
  { key: 'nao_recebidos', label: 'Não recebidos' },
  { key: 'devolvidos', label: 'Devolvidos' },
  { key: 'sem_codigo', label: 'Sem código' },
  { key: 'a_caminho', label: 'Todos a caminho' },
]
const AJUDA = {
  problemas: 'Clientes que disseram que não receberam, envios devolvidos que a loja ainda não reenviou nem cancelou, e envios cujo fecho automático já passou.',
  nao_recebidos: 'O cliente carregou em "Não recebi": o fecho automático fica parado até a loja corrigir, marcar como devolvida ou concluir.',
  devolvidos: 'A transportadora devolveu à loja: falta reenviar ou cancelar (com reembolso).',
  sem_codigo: 'Enviados sem código de rastreio: o cliente não consegue seguir o envio.',
  a_caminho: 'Todos os envios por transportadora ainda por fechar.',
}

export default {
  name: 'AdminEnvios',
  props: { lojaId: { type: [String, Number], default: '' } },
  emits: ['abrir'],
  data () {
    return { FILTROS, AJUDA, aberto: false, filtro: 'problemas', contagens: {}, linhas: [], aCarregar: false, carregado: false }
  },
  watch: { lojaId () { this.carregar() } },
  created () { this.carregar() },
  methods: {
    data (d) { return new Date(d).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit' }) },
    mudar (f) { this.filtro = f; this.carregar() },
    async carregar (silencioso = false) {
      if (!silencioso) this.aCarregar = true
      try {
        const params = { filtro: this.filtro }
        if (this.lojaId) params.loja_id = this.lojaId
        const { data } = await api.get('/app/admin/envios/', { params })
        this.contagens = data.contagens || {}
        this.linhas = data.resultados || []
        this.carregado = true
      } catch { this.linhas = [] } finally { this.aCarregar = false }
    },
  },
}
</script>
