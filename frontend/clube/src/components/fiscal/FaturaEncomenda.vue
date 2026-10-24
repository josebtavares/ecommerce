<!-- FaturaEncomenda.vue — backoffice: registar a fatura que a loja emitiu no e-Fatura (nº + PDF opcional).
     encomenda: detalhe (EncomendaSerializer). Emite 'atualizada' com a encomenda devolvida pelo backend. -->
<template>
  <div class="border-t border-zinc-800 pt-3" data-teste="fatura-encomenda">
    <p class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Fatura</p>

    <!-- já registada -->
    <div v-if="encomenda.fatura && !editar" class="flex flex-wrap items-center gap-2 text-xs">
      <span class="px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 font-bold">Faturada</span>
      <span class="text-zinc-200 font-semibold" data-teste="fatura-numero">{{ encomenda.fatura.numero }}</span>
      <a v-if="encomenda.fatura.pdf_url" :href="encomenda.fatura.pdf_url" target="_blank" rel="noopener"
         class="text-red-400 hover:text-red-300 underline">Ver PDF</a>
      <span class="flex-1"></span>
      <button type="button" @click="abrirEditar" class="text-zinc-400 hover:text-zinc-200 underline">Alterar</button>
      <button type="button" @click="remover" :disabled="aGuardar" class="text-zinc-500 hover:text-red-400 underline">Remover</button>
    </div>

    <!-- por faturar: o botão abre o formulário -->
    <div v-else-if="!editar" class="flex flex-wrap items-center gap-2 text-xs">
      <span class="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-bold">Por faturar</span>
      <span class="text-zinc-500">Emite a fatura no e-Fatura e regista-a aqui: o cliente vê-a na encomenda.</span>
      <button type="button" @click="abrirEditar" data-teste="registar-fatura"
        class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold transition">
        Registar fatura
      </button>
    </div>

    <form v-else @submit.prevent="guardar" class="rounded-xl border border-zinc-700 bg-zinc-800/40 p-3 space-y-3">
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
      <p v-if="erro" class="text-xs text-red-400">{{ erro }}</p>
      <div class="flex items-center gap-2">
        <button type="submit" :disabled="aGuardar || !numero" data-teste="fatura-guardar"
          class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold transition">
          {{ aGuardar ? 'A guardar…' : 'Guardar' }}
        </button>
        <button type="button" @click="editar = false" class="text-xs text-zinc-400 hover:text-zinc-200">Cancelar</button>
      </div>
    </form>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'FaturaEncomenda',
  props: {
    encomenda: { type: Object, required: true },
    lojaId:    { type: [String, Number], required: true },
  },
  emits: ['atualizada'],
  data () {
    return { editar: false, numero: '', pdf: null, aGuardar: false, erro: '' }
  },
  computed: {
    url () { return `/app/loja/${this.lojaId}/encomendas/${this.encomenda.id}/fatura/` },
  },
  methods: {
    abrirEditar () {
      this.numero = this.encomenda.fatura?.numero || ''
      this.pdf = null; this.erro = ''; this.editar = true
    },
    async guardar () {
      this.aGuardar = true; this.erro = ''
      try {
        const fd = new FormData()
        fd.append('numero', this.numero)
        if (this.pdf) fd.append('pdf', this.pdf)
        const { data } = await api.post(this.url, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        this.editar = false
        this.$emit('atualizada', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível registar a fatura.'
      } finally {
        this.aGuardar = false
      }
    },
    async remover () {
      this.aGuardar = true; this.erro = ''
      try {
        const { data } = await api.delete(this.url)
        this.$emit('atualizada', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível remover a fatura.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
