<!-- FaturaEncomenda.vue — backoffice: registar a fatura que a loja emitiu no e-Fatura (nº + PDF opcional).
     Substituir ou anular pede o motivo: a fatura anterior fica no histórico (nada se apaga).
     encomenda: detalhe (EncomendaSerializer). Emite 'atualizada' com a encomenda devolvida pelo backend. -->
<template>
  <div class="border-t border-zinc-800 pt-3" data-teste="fatura-encomenda">
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider">Fatura</p>
      <!-- comprovativo do pagamento: o Bende gera-o e envia-o ao cliente; a fatura é da loja -->
      <button v-if="pago" type="button" @click="descarregarComprovativoEncomenda(encomenda.id)" data-teste="comprovativo-loja"
        class="text-[11px] text-zinc-400 hover:text-zinc-200 underline">Comprovativo de pagamento</button>
    </div>

    <!-- já registada -->
    <div v-if="encomenda.fatura && !modo" class="flex flex-wrap items-center gap-2 text-xs">
      <span class="px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 font-bold">Faturada</span>
      <span class="text-zinc-200 font-semibold" data-teste="fatura-numero">{{ encomenda.fatura.numero }}</span>
      <a v-if="encomenda.fatura.pdf_url" :href="urlFicheiro(encomenda.fatura.pdf_url)" target="_blank" rel="noopener"
         class="text-red-400 hover:text-red-300 underline">Ver PDF</a>
      <span class="flex-1"></span>
      <button v-if="!cancelada" type="button" @click="abrir('substituir')" data-teste="fatura-substituir" class="text-zinc-400 hover:text-zinc-200 underline">Substituir</button>
      <button type="button" @click="abrir('anular')" data-teste="fatura-anular" class="text-zinc-500 hover:text-red-400 underline">Anular</button>
      <p v-if="cancelada" class="w-full text-[11px] text-amber-300" data-teste="fatura-cancelada">
        Venda cancelada depois de faturada: emite a nota de crédito no e-Fatura e anula aqui a fatura (com esse motivo).
      </p>
    </div>

    <!-- cancelada e com a fatura já anulada: nada para registar -->
    <p v-else-if="cancelada && !modo" class="text-xs text-zinc-500">Venda cancelada — a fatura foi anulada (fica no histórico).</p>

    <!-- por faturar: o botão abre o formulário -->
    <div v-else-if="!modo" class="flex flex-wrap items-center gap-2 text-xs">
      <span class="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-bold">Por faturar</span>
      <span class="text-zinc-500">Emite a fatura no e-Fatura e regista-a aqui: o cliente vê-a na encomenda.</span>
      <button type="button" @click="abrir('registar')" data-teste="registar-fatura"
        class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold transition">
        Registar fatura
      </button>
    </div>

    <form v-else @submit.prevent="guardar" class="rounded-xl border border-zinc-700 bg-zinc-800/40 p-3 space-y-3">
      <template v-if="modo !== 'anular'">
        <div>
          <label class="text-[11px] text-zinc-500 mb-1 block">Número da fatura *</label>
          <input v-model.trim="numero" maxlength="60" required placeholder="ex: FTE 2026/123" data-teste="fatura-input-numero"
            class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
        </div>
        <div>
          <label class="text-[11px] text-zinc-500 mb-1 block">PDF da fatura (opcional, até 5 MB)</label>
          <input type="file" accept="application/pdf,.pdf" @change="pdf = $event.target.files[0] || null" data-teste="fatura-input-pdf"
            class="block w-full text-xs text-zinc-400 file:mr-3 file:rounded-lg file:border-0 file:bg-zinc-700 file:px-3 file:py-1.5 file:text-zinc-200" />
        </div>
      </template>
      <p v-else class="text-xs text-zinc-300">A fatura <b>{{ encomenda.fatura.numero }}</b> deixa de valer nesta encomenda. Fica guardada no histórico com o motivo.</p>
      <div v-if="modo !== 'registar'">
        <label class="text-[11px] text-zinc-500 mb-1 block">Motivo *</label>
        <input v-model.trim="motivo" maxlength="300" required placeholder="ex: fatura anulada no e-Fatura, NIF errado…" data-teste="fatura-motivo"
          class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-red-500" />
      </div>
      <p v-if="erro" class="text-xs text-red-400">{{ erro }}</p>
      <div class="flex items-center gap-2">
        <button type="submit" :disabled="aGuardar || !podeGuardar" data-teste="fatura-guardar"
          class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold transition">
          {{ aGuardar ? 'A guardar…' : modo === 'anular' ? 'Anular fatura' : 'Guardar' }}
        </button>
        <button type="button" @click="modo = null" class="text-xs text-zinc-400 hover:text-zinc-200">Cancelar</button>
      </div>
    </form>
  </div>
</template>

<script>
import api from '@/services/api'
import { descarregarComprovativoEncomenda, urlFicheiro } from '@/utils/documentos'

export default {
  name: 'FaturaEncomenda',
  props: {
    encomenda: { type: Object, required: true },
    lojaId:    { type: [String, Number], required: true },
  },
  emits: ['atualizada'],
  data () {
    // modo: 'registar' | 'substituir' | 'anular' | null
    return { modo: null, numero: '', pdf: null, motivo: '', aGuardar: false, erro: '' }
  },
  computed: {
    pago () { return ['aprovado', 'reembolsado', 'reembolsado_parcial'].includes(this.encomenda.pagamento_status) },
    cancelada () { return this.encomenda.status === 'cancelado' },
    url () { return `/app/loja/${this.lojaId}/encomendas/${this.encomenda.id}/fatura/` },
    podeGuardar () {
      if (this.modo !== 'registar' && this.motivo.length < 3) return false
      return this.modo === 'anular' || !!this.numero
    },
  },
  methods: {
    urlFicheiro,
    descarregarComprovativoEncomenda,
    abrir (modo) {
      this.numero = modo === 'substituir' ? this.encomenda.fatura?.numero || '' : ''
      this.pdf = null; this.motivo = ''; this.erro = ''; this.modo = modo
    },
    async guardar () {
      this.aGuardar = true; this.erro = ''
      try {
        let data
        if (this.modo === 'anular') {
          ({ data } = await api.delete(this.url, { data: { motivo: this.motivo } }))
        } else {
          const fd = new FormData()
          fd.append('numero', this.numero)
          if (this.pdf) fd.append('pdf', this.pdf)
          if (this.modo === 'substituir') fd.append('motivo', this.motivo)
          ;({ data } = await api.post(this.url, fd, { headers: { 'Content-Type': 'multipart/form-data' } }))
        }
        this.modo = null
        this.$emit('atualizada', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
