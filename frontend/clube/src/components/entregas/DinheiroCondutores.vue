<!-- DinheiroCondutores.vue — Entregas → Dinheiro (backend: Views/acertoCondutorView.py, utils/acertos_condutor.py).
     Condutor: quanto dinheiro tem consigo (cobrado nas entregas e ainda não entregue à loja) e os acertos.
     Loja (dono/gestor, gerir_pagamentos): quanto cada condutor tem por entregar; "Receber" regista o acerto
     (escolhe as entregas — por omissão todas); um acerto errado anula-se com motivo (o registo fica). -->
<template>
  <div class="space-y-4" data-teste="dinheiro">
    <div v-if="carregando && !d" class="space-y-3">
      <div v-for="n in 3" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>
    <p v-else-if="erro && !d" class="text-sm text-red-300 bg-zinc-900 rounded-2xl border border-zinc-800 p-4">{{ erro }}</p>

    <!-- ═══ CONDUTOR ═══ -->
    <template v-else-if="d && d.condutor">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5" data-teste="dinheiro-comigo">
        <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider">Dinheiro contigo</p>
        <p :class="['text-3xl font-black mt-1', Number(d.por_acertar) > 0 ? 'text-amber-300' : 'text-zinc-300']">{{ $dinheiro(d.por_acertar) }}</p>
        <p class="text-xs text-zinc-500 mt-1">
          <template v-if="d.n">Cobrado em {{ d.n }} entrega{{ d.n !== 1 ? 's' : '' }}. Entrega-o à loja — ela regista quando o receber.</template>
          <template v-else>Não tens dinheiro de entregas por entregar à loja.</template>
        </p>
      </div>
      <div v-if="d.entregas.length" class="bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800">
        <div v-for="e in d.entregas" :key="e.entrega_id" class="px-4 py-3 flex items-center justify-between gap-3 text-sm" :data-teste="`comigo-${e.encomenda_id}`">
          <div class="min-w-0">
            <p class="text-zinc-200 font-semibold">Encomenda #{{ e.encomenda_id }}<span v-if="e.cliente" class="text-zinc-500 font-normal"> · {{ e.cliente }}</span></p>
            <p class="text-xs text-zinc-500">Entregue {{ quando(e.data_entrega) }}</p>
          </div>
          <span class="font-bold text-amber-300 whitespace-nowrap">{{ $dinheiro(e.valor) }}</span>
        </div>
      </div>
      <Historico :acertos="d.acertos" :quando="quando" />
    </template>

    <!-- ═══ LOJA ═══ -->
    <template v-else-if="d">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider">Por receber dos condutores</p>
          <p :class="['text-2xl font-black mt-0.5', totalLoja > 0 ? 'text-amber-300' : 'text-zinc-300']" data-teste="dinheiro-total">{{ $dinheiro(totalLoja) }}</p>
        </div>
        <p class="text-xs text-zinc-500 max-w-sm">Dinheiro que os condutores cobraram nas entregas e ainda não entregaram à loja.</p>
      </div>

      <div v-if="!d.condutores.length" class="text-center py-10 text-zinc-500 text-sm bg-zinc-900 rounded-2xl border border-zinc-800">
        Sem condutores. Adiciona condutores na secção de Staff.
      </div>
      <div v-else class="space-y-2">
        <div v-for="c in d.condutores" :key="c.condutor_id" :data-teste="`condutor-${c.condutor_id}`"
             class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 flex flex-wrap items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-300 font-bold flex-shrink-0">
            {{ (c.nome || '?').charAt(0).toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-200">{{ c.nome }}<span v-if="!c.ativo" class="ml-2 text-[11px] text-zinc-500 font-normal">(já não é condutor)</span></p>
            <p class="text-xs text-zinc-500">
              <template v-if="c.n">{{ c.n }} entrega{{ c.n !== 1 ? 's' : '' }} · desde {{ quando(c.desde) }}</template>
              <template v-else>Nada por entregar</template>
            </p>
          </div>
          <span :class="['text-base font-black whitespace-nowrap', c.n ? 'text-amber-300' : 'text-zinc-500']">{{ $dinheiro(c.por_acertar) }}</span>
          <button v-if="c.n" type="button" @click="abrir(c)" data-teste="dinheiro-receber"
            class="px-3 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold whitespace-nowrap">
            <font-awesome-icon :icon="['fas', 'hand-holding-dollar']" class="mr-1" />Receber
          </button>
        </div>
      </div>

      <Historico :acertos="d.acertos" :quando="quando" mostrar-condutor pode-anular @anular="aAnular = $event" />
    </template>

    <!-- Modal: receber -->
    <div v-if="modal" class="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-4" @click.self="fechar">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-md p-5 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto"
           role="dialog" aria-modal="true" data-teste="modal-receber">
        <div>
          <h3 class="text-base font-bold text-zinc-100">Receber dinheiro de {{ modal.nome }}</h3>
          <p class="text-xs text-zinc-500 mt-1">Marca as entregas cujo dinheiro recebeste agora. O condutor é avisado.</p>
        </div>
        <div v-if="!modal.entregas" class="h-24 bg-zinc-800 rounded-xl animate-pulse"></div>
        <template v-else>
          <label class="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
            <input type="checkbox" :checked="todas" @change="marcarTodas($event.target.checked)" class="accent-red-600" data-teste="receber-todas" />
            Todas ({{ modal.entregas.length }})
          </label>
          <div class="rounded-xl border border-zinc-800 divide-y divide-zinc-800">
            <label v-for="e in modal.entregas" :key="e.entrega_id" class="px-3 py-2.5 flex items-center gap-3 text-sm cursor-pointer hover:bg-zinc-800/40">
              <input type="checkbox" v-model="escolhidas" :value="e.entrega_id" class="accent-red-600" :data-teste="`receber-${e.encomenda_id}`" />
              <span class="flex-1 min-w-0">
                <span class="text-zinc-200">#{{ e.encomenda_id }}</span>
                <span class="text-zinc-500 text-xs"> · {{ quando(e.data_entrega) }}<template v-if="e.cliente"> · {{ e.cliente }}</template></span>
              </span>
              <span class="font-semibold text-zinc-200 whitespace-nowrap">{{ $dinheiro(e.valor) }}</span>
            </label>
          </div>
          <input v-model.trim="nota" type="text" maxlength="300" placeholder="Nota (opcional)" data-teste="receber-nota"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
        </template>
        <div class="flex gap-2 justify-end">
          <button type="button" @click="fechar" class="px-4 py-2 rounded-xl bg-zinc-800 text-zinc-300 text-sm">Cancelar</button>
          <button type="button" @click="receber" :disabled="!escolhidas.length || aGuardar" data-teste="receber-confirmar"
            class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">
            {{ aGuardar ? 'A guardar…' : `Recebi ${$dinheiro(totalEscolhido)}` }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: anular -->
    <div v-if="aAnular" class="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-4" @click.self="aAnular = null">
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 w-full max-w-sm p-5 space-y-4 shadow-2xl" role="dialog" aria-modal="true" data-teste="modal-anular">
        <div>
          <h3 class="text-base font-bold text-zinc-100">Anular o acerto de {{ $dinheiro(aAnular.valor) }}</h3>
          <p class="text-xs text-zinc-500 mt-1">O registo fica (anulado) e as {{ aAnular.n_entregas }} entrega(s) voltam a contar como dinheiro com {{ aAnular.condutor_nome }}.</p>
        </div>
        <input v-model.trim="motivo" type="text" maxlength="300" placeholder="Motivo (ex.: contei mal)" data-teste="anular-motivo"
          class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
        <div class="flex gap-2 justify-end">
          <button type="button" @click="aAnular = null" class="px-4 py-2 rounded-xl bg-zinc-800 text-zinc-300 text-sm">Não</button>
          <button type="button" @click="anular" :disabled="motivo.length < 5 || aGuardar" data-teste="anular-confirmar"
            class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-sm font-bold">Anular</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'
import { formatarDinheiro } from '@/utils/dinheiro'
import Historico from './HistoricoAcertos.vue'

export default {
  name: 'DinheiroCondutores',
  components: { Historico },
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['alterado'],
  data () {
    return { d: null, carregando: false, erro: '', modal: null, escolhidas: [], nota: '', aGuardar: false,
             aAnular: null, motivo: '' }
  },
  computed: {
    url () { return `/app/loja/${this.lojaId}/entrega/dinheiro/` },
    totalLoja () { return (this.d?.condutores || []).reduce((s, c) => s + Number(c.por_acertar), 0) },
    todas () { return !!this.modal?.entregas && this.escolhidas.length === this.modal.entregas.length },
    totalEscolhido () {
      const sel = new Set(this.escolhidas)
      return (this.modal?.entregas || []).filter(e => sel.has(e.entrega_id)).reduce((s, e) => s + Number(e.valor), 0)
    },
    ocupado () { return !!(this.modal || this.aAnular || this.aGuardar) },
  },
  created () { this.carregar() },
  methods: {
    quando (d) {
      return d ? new Date(d).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''
    },
    // de fora (tempo real / intervalo): não mexe enquanto a pessoa está a meio de uma acção
    async carregar (silencioso = false) {
      if (silencioso && this.ocupado) return
      this.carregando = !silencioso
      try {
        const { data } = await api.get(this.url)
        this.d = data; this.erro = ''
      } catch (e) {
        if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar.'
      } finally { this.carregando = false }
    },
    async abrir (c) {
      this.modal = { condutor_id: c.condutor_id, nome: c.nome, entregas: null }
      this.escolhidas = []; this.nota = ''
      try {
        const { data } = await api.get(`${this.url}${c.condutor_id}/`)
        if (!this.modal) return
        this.modal.entregas = data.entregas
        this.escolhidas = data.entregas.map(e => e.entrega_id)
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível abrir.'); this.modal = null
      }
    },
    fechar () { if (!this.aGuardar) this.modal = null },
    marcarTodas (sim) { this.escolhidas = sim ? this.modal.entregas.map(e => e.entrega_id) : [] },
    async receber () {
      this.aGuardar = true
      try {
        const { data } = await api.post(`${this.url}${this.modal.condutor_id}/receber/`, { entregas: this.escolhidas, nota: this.nota })
        toast.success(`Registado: recebeste ${formatarDinheiro(data.valor)} de ${data.condutor_nome}.`)
        this.modal = null
        this.$emit('alterado')
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível guardar.')
      } finally { this.aGuardar = false }
      this.carregar(true)
    },
    async anular () {
      this.aGuardar = true
      try {
        await api.post(`${this.url}acertos/${this.aAnular.id}/anular/`, { motivo: this.motivo })
        toast.success('Acerto anulado.')
        this.aAnular = null; this.motivo = ''
        this.$emit('alterado')
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível anular.')
      } finally { this.aGuardar = false }
      this.carregar(true)
    },
  },
}
</script>
