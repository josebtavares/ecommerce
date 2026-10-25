<!-- FaturaVenda.vue — registar a fatura que o vendedor emitiu no e-Fatura (nº + PDF opcional) numa venda:
     encomenda (FaturaEncomenda), marcação ou conta do POS. Substituir ou anular pede o motivo: a fatura anterior
     fica no histórico (nada se apaga).
     documento: { fatura: {numero, pdf_url} | null }; url: endpoint POST/DELETE …/fatura/ que devolve o documento atualizado.
     cancelada: a venda deixou de valer depois de faturada (só Anular, com o aviso da nota de crédito).
     tema: 'escuro' (backoffice) | 'claro' (POS). Emite 'atualizada' com o documento devolvido. -->
<template>
  <div :class="c.raiz" :data-teste="teste">
    <div class="flex items-center justify-between mb-2">
      <p :class="c.titulo">Fatura</p>
      <slot name="acoes" />
    </div>

    <!-- já registada -->
    <div v-if="documento.fatura && !modo" class="flex flex-wrap items-center gap-2 text-xs">
      <span :class="c.faturada">Faturada</span>
      <span :class="c.numero" data-teste="fatura-numero">{{ documento.fatura.numero }}</span>
      <a v-if="documento.fatura.pdf_url" :href="urlFicheiro(documento.fatura.pdf_url)" target="_blank" rel="noopener" :class="c.link">Ver PDF</a>
      <span class="flex-1"></span>
      <button v-if="!cancelada" type="button" @click="abrir('substituir')" data-teste="fatura-substituir" :class="c.acao">Substituir</button>
      <button type="button" @click="abrir('anular')" data-teste="fatura-anular" :class="c.anular">Anular</button>
      <p v-if="cancelada" :class="['w-full text-[11px]', c.aviso]" data-teste="fatura-cancelada">
        Venda cancelada depois de faturada: emite a nota de crédito no e-Fatura e anula aqui a fatura (com esse motivo).
      </p>
    </div>

    <!-- cancelada e com a fatura já anulada: nada para registar -->
    <p v-else-if="cancelada && !modo" :class="['text-xs', c.suave]">Venda cancelada — a fatura foi anulada (fica no histórico).</p>

    <!-- por faturar: o botão abre o formulário -->
    <div v-else-if="!modo" class="flex flex-wrap items-center gap-2 text-xs">
      <span :class="c.porFaturar">Por faturar</span>
      <span :class="c.suave">{{ dica }}</span>
      <button type="button" @click="abrir('registar')" data-teste="registar-fatura" :class="c.botao">Registar fatura</button>
    </div>

    <form v-else @submit.prevent="guardar" :class="c.form">
      <template v-if="modo !== 'anular'">
        <div>
          <label :class="c.rotulo">Número da fatura *</label>
          <input v-model.trim="numero" maxlength="60" required placeholder="ex: FTE 2026/123" data-teste="fatura-input-numero" :class="c.campo" />
        </div>
        <div>
          <label :class="c.rotulo">PDF da fatura (opcional, até 5 MB)</label>
          <input type="file" accept="application/pdf,.pdf" @change="pdf = $event.target.files[0] || null" data-teste="fatura-input-pdf" :class="c.ficheiro" />
        </div>
      </template>
      <p v-else :class="['text-xs', c.texto]">A fatura <b>{{ documento.fatura.numero }}</b> deixa de valer nesta venda. Fica guardada no histórico com o motivo.</p>
      <div v-if="modo !== 'registar'">
        <label :class="c.rotulo">Motivo *</label>
        <input v-model.trim="motivo" maxlength="300" required placeholder="ex: fatura anulada no e-Fatura, NIF errado…" data-teste="fatura-motivo" :class="c.campo" />
      </div>
      <p v-if="erro" :class="['text-xs', c.erro]" role="alert">{{ erro }}</p>
      <div class="flex items-center gap-2">
        <button type="submit" :disabled="aGuardar || !podeGuardar" data-teste="fatura-guardar"
          class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold transition">
          {{ aGuardar ? 'A guardar…' : modo === 'anular' ? 'Anular fatura' : 'Guardar' }}
        </button>
        <button type="button" @click="modo = null" :class="['text-xs', c.acao]">Cancelar</button>
      </div>
    </form>
  </div>
</template>

<script>
import api from '@/services/api'
import { urlFicheiro } from '@/utils/documentos'

const TEMAS = {
  escuro: {
    raiz: 'border-t border-zinc-800 pt-3',
    titulo: 'text-xs font-bold text-zinc-500 uppercase tracking-wider',
    faturada: 'px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 font-bold',
    porFaturar: 'px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-bold',
    numero: 'text-zinc-200 font-semibold',
    link: 'text-red-400 hover:text-red-300 underline',
    acao: 'text-zinc-400 hover:text-zinc-200 underline',
    anular: 'text-zinc-500 hover:text-red-400 underline',
    suave: 'text-zinc-500',
    aviso: 'text-amber-300',
    erro: 'text-red-400',
    texto: 'text-zinc-300',
    botao: 'px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold transition',
    form: 'rounded-xl border border-zinc-700 bg-zinc-800/40 p-3 space-y-3',
    rotulo: 'text-[11px] text-zinc-500 mb-1 block',
    campo: 'w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-red-500',
    ficheiro: 'block w-full text-xs text-zinc-400 file:mr-3 file:rounded-lg file:border-0 file:bg-zinc-700 file:px-3 file:py-1.5 file:text-zinc-200',
  },
  claro: {
    raiz: 'rounded-2xl border border-slate-200 bg-white p-4',
    titulo: 'text-xs font-black text-slate-500 uppercase tracking-wider',
    faturada: 'px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-black',
    porFaturar: 'px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-black',
    numero: 'text-slate-950 font-black',
    link: 'text-red-600 hover:text-red-700 underline font-bold',
    acao: 'text-slate-500 hover:text-slate-900 underline font-semibold',
    anular: 'text-slate-500 hover:text-red-600 underline font-semibold',
    suave: 'text-slate-500',
    aviso: 'text-amber-700',
    erro: 'text-red-600 font-semibold',
    texto: 'text-slate-700',
    botao: 'px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-white font-black transition',
    form: 'rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-3',
    rotulo: 'text-[11px] font-bold text-slate-500 mb-1 block',
    campo: 'w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-sm text-slate-950 focus:outline-none focus:border-red-500',
    ficheiro: 'block w-full text-xs text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-200 file:px-3 file:py-1.5 file:text-slate-800',
  },
}

export default {
  name: 'FaturaVenda',
  props: {
    documento: { type: Object, required: true },
    url:       { type: String, required: true },
    cancelada: { type: Boolean, default: false },
    dica:      { type: String, default: 'Emite a fatura no e-Fatura e regista-a aqui.' },
    tema:      { type: String, default: 'escuro' },
    teste:     { type: String, default: 'fatura-venda' },
  },
  emits: ['atualizada'],
  data () {
    // modo: 'registar' | 'substituir' | 'anular' | null
    return { modo: null, numero: '', pdf: null, motivo: '', aGuardar: false, erro: '' }
  },
  computed: {
    c () { return TEMAS[this.tema] || TEMAS.escuro },
    podeGuardar () {
      if (this.modo !== 'registar' && this.motivo.length < 3) return false
      return this.modo === 'anular' || !!this.numero
    },
  },
  methods: {
    urlFicheiro,
    abrir (modo) {
      this.numero = modo === 'substituir' ? this.documento.fatura?.numero || '' : ''
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
