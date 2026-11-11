<template>
  <!-- Admin → Pagamentos → Cartão (vinti4): cada ida de alguém à página da SISP e o que a SISP respondeu
       (Views/pagamentosAdminView.py vinti4_lista / vinti4_detalhe). Serve os testes de certificação e o suporte. -->
  <div class="space-y-4" data-teste="pagamentos-vinti4">
    <div class="flex flex-wrap gap-2">
      <button v-for="e in estados" :key="e.valor" type="button" @click="filtrar(e.valor)" :data-teste="`v4-estado-${e.valor}`"
        :class="['px-3 py-1.5 rounded-lg text-xs font-semibold border transition',
                 f.estado === e.valor ? 'bg-zinc-700 border-zinc-600 text-zinc-100' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ e.nome }} <span class="opacity-70 tabular-nums">{{ e.n }}</span>
      </button>
      <button v-if="f.estado" type="button" @click="filtrar('')" class="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200">Todos</button>
    </div>
    <form class="flex flex-wrap items-end gap-2" @submit.prevent="carregar(0)">
      <input v-model.trim="f.q" placeholder="Referência, loja, cliente…" maxlength="60" data-teste="v4-q"
             class="px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 w-56" />
      <select v-model="f.credenciais" @change="carregar(0)" class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200">
        <option value="">Bendi e lojas</option><option value="bendi">Só da Bendi (mensalidades, comissões)</option><option value="lojas">Só das lojas</option>
      </select>
      <button type="submit" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold">Procurar</button>
    </form>
    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <div v-if="carregando && !d" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <div v-else-if="d" class="bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800" data-teste="v4-lista">
      <div v-for="t in d.results" :key="t.id" class="px-4 py-3" :data-teste="`v4-${t.ref}`">
        <button type="button" class="w-full text-left flex flex-wrap items-center gap-x-3 gap-y-1" @click="abrir(t)">
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', COR[t.estado] || 'bg-zinc-700 text-zinc-300']">{{ t.estado_nome }}</span>
          <div class="flex-1 min-w-[200px]">
            <p class="text-sm text-zinc-200">{{ t.descricao || t.referencia }}
              <span class="text-[11px] text-zinc-500">· {{ t.ref }}</span></p>
            <p class="text-[11px] text-zinc-500">
              {{ TIPOS[t.tipo] || t.tipo }} · {{ t.loja ? t.loja.nome : 'Bendi' }} · {{ t.pagador || '—' }} · {{ t.criada_em }}
              <template v-if="t.pan"> · {{ t.pan }}</template>
            </p>
            <p v-if="t.mensagem || t.erro" class="text-[11px] text-amber-300 mt-0.5">{{ t.mensagem || t.erro }}</p>
          </div>
          <span class="text-sm font-bold tabular-nums text-zinc-100">{{ t.montante }} CVE</span>
        </button>
        <div v-if="aberto && aberto.id === t.id" class="mt-3 rounded-xl bg-zinc-950/60 border border-zinc-800 p-3 space-y-2 text-[11px] text-zinc-400" data-teste="v4-ficha">
          <div class="grid sm:grid-cols-2 gap-x-6 gap-y-1">
            <p>Nossa referência: <span class="text-zinc-200">{{ aberto.referencia }}</span></p>
            <p>POS ID: <span class="text-zinc-200">{{ aberto.pos_id }}</span></p>
            <p v-if="aberto.transacao">Nº da transação: <span class="text-zinc-200">{{ aberto.transacao }}</span></p>
            <p v-if="aberto.confirmada_por">Confirmada por: <span class="text-zinc-200">{{ CONFIRMADA[aberto.confirmada_por] || aberto.confirmada_por }}</span></p>
            <p v-if="aberto.efeito">Efeito: <span class="text-zinc-200">{{ aberto.efeito }}</span></p>
            <p v-if="aberto.erro_codigo">Código de erro: <span class="text-zinc-200">{{ aberto.erro_codigo }}</span></p>
            <p v-if="aberto.terminada_em">Terminada a: <span class="text-zinc-200">{{ aberto.terminada_em }}</span></p>
            <p>Consultas à API de estado: <span class="text-zinc-200">{{ aberto.consultas }}</span></p>
          </div>
          <p v-if="aberto.erro" class="text-amber-300">Detalhe: {{ aberto.erro }}</p>
          <router-link v-if="aberto.destino" :to="aberto.destino" class="inline-block text-zinc-300 hover:text-white">Ver o que se pagava →</router-link>
          <div>
            <p class="font-semibold text-zinc-300 mb-1">O que a SISP respondeu</p>
            <p v-if="!aberto.respostas?.length" class="text-zinc-500">Nada ainda (o cliente não voltou da página da SISP).</p>
            <details v-for="(r, i) in aberto.respostas" :key="i" class="mb-1">
              <summary class="cursor-pointer text-zinc-300">{{ r.origem === 'estado' ? 'API de estado' : 'Resposta' }} · {{ quando(r.em) }}</summary>
              <pre class="mt-1 p-2 rounded-lg bg-black/40 text-zinc-300 overflow-x-auto whitespace-pre-wrap break-all">{{ formatar(r.campos) }}</pre>
            </details>
          </div>
        </div>
      </div>
      <p v-if="!d.results.length" class="text-center py-10 text-sm text-zinc-500">Nenhuma transação com cartão neste período.</p>
    </div>
    <PaginacaoLista v-if="d" :count="d.count" :limit="LIMITE" :offset="offset" @ir="carregar" />
  </div>
</template>

<script>
import api from '@/services/api'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'

const LIMITE = 20
const COR = {
  paga: 'bg-green-500/15 text-green-300', iniciada: 'bg-sky-500/15 text-sky-300', falhada: 'bg-red-500/15 text-red-300',
  cancelada: 'bg-zinc-700 text-zinc-300', expirada: 'bg-zinc-700 text-zinc-400', por_confirmar: 'bg-amber-500/15 text-amber-300',
}
const TIPOS = { fatura: 'Mensalidade', comissoes: 'Comissões', encomenda: 'Encomenda', marcacao: 'Marcação' }
const CONFIRMADA = { resposta: 'resposta da SISP', estado: 'API de estado', admin: 'admin' }

export default {
  name: 'PagamentosVinti4',
  components: { PaginacaoLista },
  props: { datas: { type: Object, default: () => ({}) } },
  data () {
    return { LIMITE, COR, TIPOS, CONFIRMADA, d: null, offset: 0, f: { estado: '', q: '', credenciais: '' }, aberto: null, carregando: false, erro: '' }
  },
  computed: {
    estados () { return this.d?.estados || [] },
  },
  watch: {
    datas () { this.carregar(0) },
  },
  created () { this.carregar(0) },
  methods: {
    quando (d) { return d ? new Date(d).toLocaleString('pt-PT') : '' },
    formatar (o) { try { return JSON.stringify(o, null, 2) } catch (e) { return String(o) } },
    filtrar (e) { this.f.estado = e; this.carregar(0) },
    recarregar () { return this.carregar(this.offset, true) },
    async carregar (offset = this.offset, silencioso = false) {
      this.offset = offset
      if (!silencioso) { this.carregando = true; this.erro = '' }
      try {
        const params = { ...this.datas, limit: LIMITE, offset }
        for (const [k, v] of Object.entries(this.f)) if (v) params[k] = v
        const { data } = await api.get('/app/admin/pagamentos/vinti4/', { params })
        this.d = data
      } catch (e) {
        if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar as transações com cartão.'
      } finally { if (!silencioso) this.carregando = false }
    },
    async abrir (t) {
      if (this.aberto?.id === t.id) { this.aberto = null; return }
      try {
        const { data } = await api.get(`/app/admin/pagamentos/vinti4/${t.id}/`)
        this.aberto = data
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível abrir a transação.' }
    },
  },
}
</script>
