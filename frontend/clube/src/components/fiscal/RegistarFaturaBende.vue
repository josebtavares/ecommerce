<!-- RegistarFaturaBende.vue — admin: registar/alterar/remover a fatura do Bende (mensalidade ou comissões do mês).
     url: POST/DELETE …/fatura/. Emite 'atualizado' com a resposta do backend. -->
<template>
  <div class="flex flex-wrap items-center gap-2 text-xs" data-teste="fatura-bende">
    <template v-if="fatura && !editar">
      <span class="px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 font-bold">Faturada</span>
      <a v-if="fatura.pdf_url" :href="urlFicheiro(fatura.pdf_url)" target="_blank" rel="noopener" class="text-zinc-200 underline">{{ fatura.numero }}</a>
      <span v-else class="text-zinc-200">{{ fatura.numero }}</span>
      <button type="button" @click="abrir" class="text-zinc-400 hover:text-zinc-200 underline">Alterar</button>
      <button type="button" @click="remover" :disabled="aGuardar" class="text-zinc-500 hover:text-red-400 underline">Remover</button>
    </template>
    <button v-else-if="!editar" type="button" @click="abrir" data-teste="registar-fatura-bende"
      class="px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 font-semibold">Registar fatura</button>
    <form v-else @submit.prevent="guardar" class="flex flex-wrap items-center gap-2">
      <input v-model.trim="numero" maxlength="60" required placeholder="Nº da fatura" data-teste="fatura-bende-numero"
        class="w-36 px-2.5 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-red-500" />
      <input type="file" accept="application/pdf,.pdf" @change="pdf = $event.target.files[0] || null" data-teste="fatura-bende-pdf"
        class="max-w-[210px] text-zinc-400 file:mr-2 file:rounded-md file:border-0 file:bg-zinc-700 file:px-2 file:py-1 file:text-zinc-200" />
      <button type="submit" :disabled="aGuardar || !numero" data-teste="fatura-bende-guardar"
        class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold">{{ aGuardar ? '…' : 'Guardar' }}</button>
      <button type="button" @click="editar = false" class="text-zinc-400 hover:text-zinc-200">Cancelar</button>
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
    return { editar: false, numero: '', pdf: null, aGuardar: false, erro: '' }
  },
  methods: {
    urlFicheiro,
    abrir () {
      this.numero = this.fatura?.numero || ''
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
        this.$emit('atualizado', data)
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
        this.$emit('atualizado', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível remover.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
