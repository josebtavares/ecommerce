<template>
  <!-- Arquivos fiscais preparados em segundo plano (ZIP grande demais para a hora) — backend Views/arquivoFiscalView.py.
       Só aparece quando há algum. `base`: …/arquivos/ (lista) e …/arquivos/<id>/descarregar/. -->
  <div v-if="itens.length" :class="caixa" data-teste="arquivos-fiscais">
    <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
      <p :class="['text-sm font-semibold', claro ? 'text-slate-800' : 'text-zinc-200']">
        <font-awesome-icon :icon="['fas', 'file-zipper']" class="mr-1" />Arquivos preparados
      </p>
      <p :class="['text-[11px]', claro ? 'text-slate-500' : 'text-zinc-500']">Ficam disponíveis {{ dias }} dias</p>
    </div>
    <p v-if="erro" class="text-xs text-red-400 mb-2" role="alert">{{ erro }}</p>
    <div :class="['divide-y', claro ? 'divide-slate-200' : 'divide-zinc-800']">
      <div v-for="a in itens" :key="a.id" class="py-2 flex flex-wrap items-center gap-x-3 gap-y-1" :data-teste="`arquivo-${a.id}`">
        <div class="flex-1 min-w-[180px]">
          <p :class="['text-sm', claro ? 'text-slate-800' : 'text-zinc-200']">{{ a.periodo }}<template v-if="!a.com_bende"> · sem documentos do Bende</template></p>
          <p :class="['text-[11px]', claro ? 'text-slate-500' : 'text-zinc-500']">
            Pedido a {{ quando(a.criado_em) }}<template v-if="a.pedido_por"> por {{ a.pedido_por }}</template>
            <template v-if="a.disponivel"> · {{ tamanho(a.tamanho) }} · até {{ quando(a.expira_em) }}</template>
            <template v-if="a.avisos"> · <span class="text-amber-400">{{ a.avisos }} ficheiro(s) em falta (ver LEIA-ME)</span></template>
          </p>
          <p v-if="a.erro" class="text-[11px] text-red-400">{{ a.erro }}</p>
        </div>
        <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold', cor(a.estado)]" data-teste="arquivo-estado">{{ rotulo(a) }}</span>
        <button v-if="a.disponivel" type="button" @click="descarregar(a)" :disabled="aDescarregar === a.id" data-teste="arquivo-descarregar"
          :class="['px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-50', claro ? 'bg-slate-900 text-white hover:bg-slate-700' : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200']">
          {{ aDescarregar === a.id ? 'A abrir…' : 'Descarregar' }}
        </button>
      </div>
    </div>
    <button v-if="count > itens.length" type="button" @click="carregar(itens.length)"
      :class="['mt-2 text-xs underline', claro ? 'text-slate-500' : 'text-zinc-400']">Ver mais</button>
  </div>
</template>

<script>
import api from '@/services/api'

const CORES = {
  pendente: 'bg-amber-500/15 text-amber-400', a_correr: 'bg-sky-500/15 text-sky-400', ok: 'bg-green-500/15 text-green-500',
  erro: 'bg-red-500/15 text-red-400', expirada: 'bg-zinc-500/15 text-zinc-400',
}

export default {
  name: 'ArquivosFiscais',
  props: {
    base: { type: String, required: true },          // ex.: /app/loja/3/faturacao/arquivos/
    params: { type: Object, default: () => ({}) },    // admin: { alvo, id }
    versao: { type: Number, default: 0 },             // muda → recarrega (acabou de pedir um)
    claro: { type: Boolean, default: false },         // POS (tema claro próprio)
  },
  data () {
    return { itens: [], count: 0, dias: 7, emCurso: false, erro: '', aDescarregar: null }
  },
  computed: {
    caixa () {
      return this.claro ? 'rounded-2xl border border-slate-200 bg-white px-4 py-3' : 'bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3'
    },
  },
  watch: {
    versao () { this.carregar() },
    base () { this.carregar() },
  },
  created () { this.carregar() },
  beforeUnmount () { clearTimeout(this.temporizador) },
  methods: {
    async carregar (offset = 0) {
      clearTimeout(this.temporizador)
      try {
        const { data } = await api.get(this.base, { params: { ...this.params, limit: 10, offset } })
        this.itens = offset ? [...this.itens, ...data.results] : data.results
        this.count = data.count
        this.dias = data.dias_validade
        this.emCurso = data.em_curso
      } catch { /* sem permissão ou offline: não mostra */ }
      // enquanto há algum a ser preparado, vê de 10 em 10 segundos
      if (this.emCurso) this.temporizador = setTimeout(() => this.carregar(), 10000)
    },
    async descarregar (a) {
      this.aDescarregar = a.id; this.erro = ''
      try {
        const { data } = await api.post(`${this.base}${a.id}/descarregar/`)
        const el = document.createElement('a')
        el.href = data.url
        el.download = data.nome
        el.rel = 'noopener'
        el.click()
        a.descargas += 1
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível descarregar.'
        if (e.response?.status === 410) this.carregar()
      } finally { this.aDescarregar = null }
    },
    rotulo (a) {
      return { pendente: 'Na fila', a_correr: 'A preparar…', ok: 'Pronto', erro: 'Falhou', expirada: 'Expirado' }[a.estado] || a.estado_label
    },
    cor (e) { return CORES[e] || CORES.expirada },
    quando (d) {
      return d ? new Date(d).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
    },
    tamanho (b) {
      if (!b) return '0 KB'
      return b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`
    },
  },
}
</script>
