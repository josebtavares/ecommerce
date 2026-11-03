<!-- SeccaoEndereco.vue — Configurações da loja: o endereço público (bende.store/loja/<endereço>).
     Backend: GET/POST /app/loja/<id>/endereco/ (utils/endereco_loja.py). Os endereços antigos continuam a abrir a loja. -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="seccao-endereco" data-alvo="endereco">
    <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1">Endereço da loja</h2>
    <p class="text-xs text-zinc-600 mb-5">
      É o link que partilhas com os clientes. Se o mudares, os links antigos continuam a funcionar e levam ao novo.
    </p>

    <p v-if="carregando" class="text-xs text-zinc-500">A carregar…</p>
    <p v-else-if="!d" class="text-xs text-red-400">{{ erro || 'Não foi possível carregar.' }}</p>

    <template v-else>
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <a :href="urlCompleto(d.slug)" target="_blank" rel="noopener" data-teste="endereco-atual"
          class="text-sm font-semibold text-zinc-100 hover:text-red-400 break-all">{{ urlCompleto(d.slug) }}</a>
        <button type="button" @click="copiar" data-teste="endereco-copiar"
          class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold">
          <font-awesome-icon :icon="['fas', copiado ? 'check' : 'copy']" class="mr-1" />{{ copiado ? 'Copiado' : 'Copiar' }}
        </button>
      </div>

      <button v-if="!editar" type="button" @click="abrir" data-teste="endereco-mudar"
        :disabled="!d.mudancas_restantes"
        class="px-3 py-2 rounded-xl border border-zinc-700 hover:border-zinc-500 text-zinc-200 text-sm font-semibold disabled:opacity-40">
        <font-awesome-icon :icon="['fas', 'pen']" class="mr-1.5" />Mudar o endereço
      </button>
      <p v-if="!editar && !d.mudancas_restantes" class="text-[11px] text-amber-400 mt-2">
        Já mudaste o endereço {{ d.max_mudancas }} vezes nos últimos {{ d.janela_dias }} dias. Podes voltar a mudar mais tarde.
      </p>

      <form v-if="editar" @submit.prevent="guardar" class="space-y-2" data-teste="endereco-form">
        <label class="text-[11px] text-zinc-500" for="endereco-input">Novo endereço</label>
        <div class="flex items-stretch rounded-xl border bg-zinc-800 overflow-hidden"
          :class="v && !v.livre ? 'border-red-500' : v && v.livre ? 'border-green-600' : 'border-zinc-700'">
          <span class="px-3 flex items-center text-xs text-zinc-500 bg-zinc-800/80 border-r border-zinc-700 whitespace-nowrap">{{ base }}/loja/</span>
          <input id="endereco-input" v-model="novo" @input="aoEscrever" type="text" autocomplete="off" spellcheck="false"
            :maxlength="d.max" data-teste="endereco-input"
            class="flex-1 min-w-0 px-3 py-2 bg-transparent text-sm text-zinc-100 focus:outline-none" />
        </div>
        <p v-if="aVerificar" class="text-[11px] text-zinc-500">A verificar…</p>
        <p v-else-if="v && v.livre && v.slug !== d.slug" class="text-[11px] text-green-400" data-teste="endereco-livre">Disponível.</p>
        <p v-else-if="v && !v.livre" class="text-[11px] text-red-400" data-teste="endereco-erro">
          {{ v.erro }}
          <button v-if="v.sugestao" type="button" @click="usar(v.sugestao)" class="underline text-zinc-300 ml-1" data-teste="endereco-sugestao">
            Usar {{ v.sugestao }}</button>
        </p>
        <p class="text-[11px] text-zinc-600">
          Letras minúsculas, números e hífenes. Podes mudar {{ d.mudancas_restantes }} vez(es) nos próximos {{ d.janela_dias }} dias.
        </p>
        <p v-if="erro" class="text-xs text-red-400" role="alert">{{ erro }}</p>
        <div class="flex gap-2 pt-1">
          <button type="submit" :disabled="!podeGuardar || aGuardar" data-teste="endereco-guardar"
            class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold disabled:opacity-40">
            {{ aGuardar ? 'A guardar…' : 'Guardar' }}
          </button>
          <button type="button" @click="editar = false" class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm">
            Cancelar
          </button>
        </div>
      </form>

      <p v-if="ok" class="text-xs text-green-400 mt-3" data-teste="endereco-ok">{{ ok }}</p>

      <div v-if="d.antigos.length" class="mt-4 text-[11px] text-zinc-500" data-teste="endereco-antigos">
        Endereços antigos que continuam a levar à loja:
        <span v-for="(a, i) in d.antigos" :key="a" class="text-zinc-400">{{ i ? ', ' : ' ' }}/loja/{{ a }}</span>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { esquecerLoja } from '@/utils/enderecoLoja'

// o mesmo que o backend (utils/endereco_loja.normalizar): minúsculas, sem acentos, hífenes
function normalizar (t) {
  return String(t || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '').replace(/[\s_-]+/g, '-').replace(/^-+/, '')
}

export default {
  name: 'SeccaoEndereco',
  props: { lojaId: { type: [String, Number], required: true } },
  emits: ['alterado'],
  data () {
    return {
      d: null, carregando: true, erro: '', ok: '', copiado: false,
      editar: false, novo: '', v: null, aVerificar: false, aGuardar: false, temporizador: null,
      base: window.location.host,
    }
  },
  computed: {
    podeGuardar () { return this.v && this.v.livre && this.v.slug === this.novo.replace(/-+$/, '') && this.novo !== this.d.slug },
  },
  created () { this.carregar() },
  beforeUnmount () { clearTimeout(this.temporizador) },
  methods: {
    urlCompleto (s) { return `${window.location.origin}/loja/${s}` },
    async carregar () {
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/endereco/`)
        this.d = data
      } catch (e) { this.erro = e.response?.data?.detail || '' } finally { this.carregando = false }
    },
    abrir () { this.editar = true; this.novo = this.d.slug; this.v = null; this.erro = ''; this.ok = '' },
    aoEscrever () {
      this.novo = normalizar(this.novo).slice(0, this.d.max)
      this.v = null
      clearTimeout(this.temporizador)
      if (!this.novo) return
      this.temporizador = setTimeout(this.verificar, 350)
    },
    usar (s) { this.novo = s; this.verificar() },
    async verificar () {
      const pedido = this.novo.replace(/-+$/, '')
      if (!pedido) return
      this.aVerificar = true
      try {
        const { data } = await api.get(`/app/loja/${this.lojaId}/endereco/`, { params: { verificar: pedido } })
        if (pedido === this.novo.replace(/-+$/, '')) this.v = data.verificacao
      } catch { this.v = null } finally { this.aVerificar = false }
    },
    async guardar () {
      const novo = this.novo.replace(/-+$/, '')
      this.aGuardar = true; this.erro = ''
      try {
        const antigo = this.d.slug
        const { data } = await api.post(`/app/loja/${this.lojaId}/endereco/`, { slug: novo })
        esquecerLoja(antigo, novo, this.lojaId)
        this.d = data
        this.editar = false
        this.ok = `Endereço mudado. /loja/${antigo} continua a levar à loja.`
        this.$emit('alterado')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível mudar o endereço.'
      } finally { this.aGuardar = false }
    },
    async copiar () {
      try {
        await navigator.clipboard.writeText(this.urlCompleto(this.d.slug))
        this.copiado = true
        setTimeout(() => { this.copiado = false }, 1500)
      } catch { /* sem permissão para copiar */ }
    },
  },
}
</script>
