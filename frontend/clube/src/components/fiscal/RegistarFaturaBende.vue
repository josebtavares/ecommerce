<!-- RegistarFaturaBende.vue — admin: registar, substituir ou anular a fatura do Bende (mensalidade ou comissões do mês).
     Substituir/anular pede o motivo: a anterior fica no histórico (nada se apaga).
     url: POST/DELETE …/fatura/. Emite 'atualizado' com a resposta do backend. -->
<template>
  <div class="flex flex-wrap items-center gap-2 text-xs" data-teste="fatura-bende">
    <template v-if="fatura && !modo">
      <span class="px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 font-bold">Faturada</span>
      <a v-if="fatura.pdf_url" :href="urlFicheiro(fatura.pdf_url)" target="_blank" rel="noopener" class="text-zinc-200 underline">{{ fatura.numero }}</a>
      <span v-else class="text-zinc-200">{{ fatura.numero }}</span>
      <button type="button" @click="abrir('substituir')" class="text-zinc-400 hover:text-zinc-200 underline">Substituir</button>
      <button type="button" @click="abrir('anular')" data-teste="fatura-bende-anular" class="text-zinc-500 hover:text-red-400 underline">Anular</button>
    </template>
    <button v-else-if="!modo" type="button" @click="abrir('registar')" data-teste="registar-fatura-bende"
      class="px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 font-semibold">Registar fatura</button>
    <form v-else @submit.prevent="guardar" class="flex flex-wrap items-center gap-2">
      <template v-if="modo !== 'anular'">
        <input v-model.trim="numero" maxlength="60" required placeholder="Nº da fatura" data-teste="fatura-bende-numero"
          class="w-36 px-2.5 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-red-500" />
        <input type="file" accept="application/pdf,.pdf" @change="pdf = $event.target.files[0] || null" data-teste="fatura-bende-pdf"
          class="max-w-[210px] text-zinc-400 file:mr-2 file:rounded-md file:border-0 file:bg-zinc-700 file:px-2 file:py-1 file:text-zinc-200" />
      </template>
      <input v-if="modo !== 'registar'" v-model.trim="motivo" maxlength="300" required placeholder="Motivo (fica no histórico)" data-teste="fatura-bende-motivo"
        class="w-56 px-2.5 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-red-500" />
      <button type="submit" :disabled="aGuardar || !podeGuardar" data-teste="fatura-bende-guardar"
        class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold">{{ aGuardar ? '…' : modo === 'anular' ? 'Anular' : 'Guardar' }}</button>
      <button type="button" @click="modo = null" class="text-zinc-400 hover:text-zinc-200">Cancelar</button>
    </form>
    <p v-if="erro" class="w-full text-red-400">{{ erro }}</p>
  </div>
</template>

<script>
import api from '@/services/api'
import { urlFicheiro } from '@/utils/documentos'

export default {
  name: 'RegistarFaturaBende',
  props: {
    fatura: { type: Object, default: null },
    url:    { type: String, required: true },
  },
  emits: ['atualizado'],
  data () {
    // modo: 'registar' | 'substituir' | 'anular' | null
    return { modo: null, numero: '', pdf: null, motivo: '', aGuardar: false, erro: '' }
  },
  computed: {
    podeGuardar () {
      if (this.modo !== 'registar' && this.motivo.length < 3) return false
      return this.modo === 'anular' || !!this.numero
    },
  },
  methods: {
    urlFicheiro,
    abrir (modo) {
      this.numero = modo === 'substituir' ? this.fatura?.numero || '' : ''
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
        this.$emit('atualizado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
