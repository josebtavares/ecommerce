<!-- AdminVinti4Loja.vue — Admin → Lojas → ficha: contrato vinti4 da loja (gerir_pagamentos).
     Validar as credenciais com a SISP: pôr em testes, ativar, suspender ou recusar (com motivo, a loja vê-o).
     Backend: GET/POST /app/admin/lojas/<id>/vinti4/ (utils/vinti4.py). A chave nunca é mostrada. -->
<template>
  <div class="rounded-xl border border-zinc-800 p-4 space-y-3" data-teste="admin-vinti4">
    <div class="flex items-center justify-between gap-2">
      <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Cartão vinti4</p>
      <span v-if="a" :class="['px-2 py-0.5 rounded-lg text-[11px] font-bold', COR[a.estado]]" data-teste="admin-vinti4-estado">{{ a.estado_nome }}</span>
    </div>
    <p v-if="carregando" class="text-xs text-zinc-500">A carregar…</p>
    <template v-else-if="d">
      <p v-if="!a" class="text-xs text-zinc-500">A loja ainda não pediu a adesão à SISP — só vende com dinheiro/transferência.</p>
      <div v-else class="text-xs space-y-0.5 text-zinc-400">
        <p>POS ID <span class="font-mono text-zinc-200">{{ a.pos_id || '—' }}</span> · Merchant ID
          <span class="font-mono text-zinc-200">{{ a.merchant_id || '—' }}</span> · chave {{ a.chave_definida ? 'guardada' : 'em falta' }}</p>
        <p v-if="a.credenciais_em">Credenciais de {{ data(a.credenciais_em) }} por {{ a.credenciais_por || '—' }}</p>
        <p v-if="a.decidido_em">Última decisão {{ data(a.decidido_em) }} por {{ a.decidido_por || '—' }}</p>
        <p v-if="a.motivo" class="text-amber-400">Motivo: {{ a.motivo }}</p>
      </div>
      <ul class="flex flex-wrap gap-1.5">
        <li v-for="r in d.requisitos" :key="r.chave"
            :class="['px-2 py-0.5 rounded text-[11px]', r.ok ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-300']">
          {{ r.titulo }}
        </li>
      </ul>
      <div v-if="acoes.length" class="space-y-2">
        <input v-model="motivo" maxlength="300" placeholder="Motivo (obrigatório para suspender ou recusar)" data-teste="admin-vinti4-motivo"
          class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none" />
        <div class="flex flex-wrap gap-2">
          <button v-for="ac in acoes" :key="ac.acao" type="button" @click="decidir(ac.acao)" :disabled="aGuardar"
            :data-teste="`admin-vinti4-${ac.acao}`"
            :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition disabled:opacity-50', ac.cls]">{{ ac.label }}</button>
        </div>
      </div>
      <p v-if="erro" class="text-xs text-red-400">{{ erro }}</p>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

const COR = {
  pedida: 'bg-sky-500/15 text-sky-400', por_validar: 'bg-amber-500/15 text-amber-300', teste: 'bg-violet-500/15 text-violet-300',
  ativa: 'bg-green-500/15 text-green-400', suspensa: 'bg-red-500/15 text-red-400',
}
const ACOES = [
  { acao: 'teste', label: 'Pôr em testes', de: ['por_validar', 'suspensa'], cls: 'bg-violet-600 hover:bg-violet-500 text-white' },
  { acao: 'ativar', label: 'Ativar', de: ['por_validar', 'teste', 'suspensa'], cls: 'bg-green-600 hover:bg-green-500 text-white' },
  { acao: 'recusar', label: 'Recusar credenciais', de: ['por_validar'], cls: 'bg-zinc-700 hover:bg-zinc-600 text-zinc-100' },
  { acao: 'suspender', label: 'Suspender', de: ['teste', 'ativa'], cls: 'bg-red-600 hover:bg-red-500 text-white' },
]

export default {
  name: 'AdminVinti4Loja',

  props: {
    lojaId: { type: [String, Number], required: true },
  },

  data () {
    return { COR, carregando: true, d: null, motivo: '', aGuardar: false, erro: '' }
  },

  computed: {
    a () { return this.d?.adesao },
    acoes () { return this.a ? ACOES.filter(x => x.de.includes(this.a.estado)) : [] },
  },

  watch: { lojaId () { this.carregar() } },

  created () { this.carregar() },

  methods: {
    data (iso) { return new Date(iso).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) },

    async carregar () {
      this.carregando = true; this.erro = ''; this.motivo = ''
      try { this.d = (await api.get(`/app/admin/lojas/${this.lojaId}/vinti4/`)).data }
      catch (e) { this.d = null; this.erro = e.response?.data?.detail || 'Sem acesso.' }
      finally { this.carregando = false }
    },

    async decidir (acao) {
      this.aGuardar = true; this.erro = ''
      try {
        this.d = (await api.post(`/app/admin/lojas/${this.lojaId}/vinti4/`, { acao, motivo: this.motivo })).data
        this.motivo = ''
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível.' }
      finally { this.aGuardar = false }
    },
  },
}
</script>
