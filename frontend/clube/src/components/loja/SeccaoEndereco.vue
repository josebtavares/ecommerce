<!-- SeccaoEndereco.vue — o endereço público da loja (e-bendi.cv/loja/<endereço>), utils/endereco_loja.py.
     Dono (Configurações): GET/POST /app/loja/<id>/endereco/ — o antigo continua a levar à loja; 3 mudanças / 30 dias.
     Admin (Lojas → detalhe, admin=true): /app/admin/lojas/<id>/endereco/ — sem limite, motivo (o dono é avisado),
     pode não manter o antigo e desligar endereços antigos (ex.: ofensivos); vê o histórico. -->
<template>
  <div :class="['bg-zinc-900 rounded-2xl border border-zinc-800', admin ? 'p-4' : 'p-6']" data-teste="seccao-endereco" data-alvo="endereco">
    <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1">Endereço da loja</h2>
    <p class="text-xs text-zinc-600 mb-5">
      <template v-if="admin">O link público da loja. Ao mudá-lo, o dono recebe uma notificação com o motivo.</template>
      <template v-else>É o link que partilhas com os clientes. Se o mudares, os links antigos continuam a funcionar e levam ao novo.</template>
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
        :disabled="!admin && !d.mudancas_restantes"
        class="px-3 py-2 rounded-xl border border-zinc-700 hover:border-zinc-500 text-zinc-200 text-sm font-semibold disabled:opacity-40">
        <font-awesome-icon :icon="['fas', 'pen']" class="mr-1.5" />Mudar o endereço
      </button>
      <p v-if="!admin && !editar && !d.mudancas_restantes" class="text-[11px] text-amber-400 mt-2">
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
        <p v-if="!admin" class="text-[11px] text-zinc-600">
          Letras minúsculas, números e hífenes. Podes mudar {{ d.mudancas_restantes }} vez(es) nos próximos {{ d.janela_dias }} dias.
        </p>
        <template v-else>
          <input v-model.trim="motivo" type="text" maxlength="300" placeholder="Motivo (vai na notificação ao dono)" data-teste="endereco-motivo"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
          <label class="flex items-start gap-2 text-xs text-zinc-300">
            <input v-model="manterAntigo" type="checkbox" class="mt-0.5 accent-red-600" data-teste="endereco-manter" />
            <span>Manter /loja/{{ d.slug }} a levar à loja
              <span class="block text-[11px] text-zinc-500">Desliga se o endereço actual for ofensivo ou enganador: deixa de funcionar e fica livre.</span></span>
          </label>
        </template>
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

      <div v-if="d.antigos.length && !admin" class="mt-4 text-[11px] text-zinc-500" data-teste="endereco-antigos">
        Endereços antigos que continuam a levar à loja:
        <span v-for="(a, i) in d.antigos" :key="a" class="text-zinc-400">{{ i ? ', ' : ' ' }}/loja/{{ a }}</span>
      </div>

      <!-- admin: antigos activos (com "Desligar") e o histórico das mudanças -->
      <template v-if="admin">
        <div v-if="d.antigos.length" class="mt-4 space-y-1" data-teste="endereco-antigos">
          <p class="text-[11px] text-zinc-500">Endereços antigos que ainda levam à loja:</p>
          <div v-for="a in d.antigos" :key="a" class="flex items-center justify-between gap-2 text-xs" :data-teste="`antigo-${a}`">
            <span class="text-zinc-300 break-all">/loja/{{ a }}</span>
            <button v-if="aDesligar !== a" type="button" @click="aDesligar = a" data-teste="endereco-desligar"
              class="px-2 py-1 rounded-lg border border-zinc-700 hover:border-red-500/60 text-zinc-400 hover:text-red-300 text-[11px] whitespace-nowrap">
              <font-awesome-icon :icon="['fas', 'ban']" class="mr-1" />Desligar</button>
            <span v-else class="flex items-center gap-1.5 text-[11px] text-zinc-400">
              Deixa de funcionar e fica livre.
              <button type="button" @click="desligar(a)" data-teste="endereco-desligar-sim" class="px-2 py-1 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold">Desligar</button>
              <button type="button" @click="aDesligar = ''" class="px-2 py-1 rounded-lg bg-zinc-800 text-zinc-300">Não</button>
            </span>
          </div>
        </div>
        <details v-if="d.historico && d.historico.length" class="mt-4" data-teste="endereco-historico">
          <summary class="text-[11px] text-zinc-500 cursor-pointer hover:text-zinc-300">Histórico ({{ d.historico.length }})</summary>
          <ul class="mt-2 space-y-1.5">
            <li v-for="(h, i) in d.historico" :key="i" class="text-[11px] text-zinc-400">
              <span class="text-zinc-300">/loja/{{ h.slug }}</span> deixado a {{ quando(h.criado_em) }}
              · {{ h.por_admin ? `Bendi${h.por ? ' (' + h.por + ')' : ''}` : 'dono' }}
              <span v-if="!h.ativo" class="text-red-300"> · desligado</span>
              <span v-if="h.motivo" class="block text-zinc-500">Motivo: {{ h.motivo }}</span>
            </li>
          </ul>
        </details>
      </template>
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
  props: {
    lojaId: { type: [String, Number], required: true },
    admin: { type: Boolean, default: false },   // Admin → Lojas (gerir_lojas)
  },
  emits: ['alterado'],
  data () {
    return {
      d: null, carregando: true, erro: '', ok: '', copiado: false,
      editar: false, novo: '', v: null, motivo: '', manterAntigo: true, aDesligar: '', aVerificar: false, aGuardar: false, temporizador: null,
      base: window.location.host,
    }
  },
  computed: {
    url () { return this.admin ? `/app/admin/lojas/${this.lojaId}/endereco/` : `/app/loja/${this.lojaId}/endereco/` },
    podeGuardar () { return this.v && this.v.livre && this.v.slug === this.novo.replace(/-+$/, '') && this.novo !== this.d.slug },
  },
  created () { this.carregar() },
  beforeUnmount () { clearTimeout(this.temporizador) },
  methods: {
    urlCompleto (s) { return `${window.location.origin}/loja/${s}` },
    async carregar () {
      try {
        const { data } = await api.get(this.url)
        this.d = data
      } catch (e) { this.erro = e.response?.data?.detail || '' } finally { this.carregando = false }
    },
    quando (d) { return d ? new Date(d).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '' },
    async desligar (slug) {
      this.erro = ''
      try {
        const { data } = await api.delete(this.url, { data: { slug } })
        esquecerLoja(slug)
        this.d = data
        this.aDesligar = ''
        this.ok = `/loja/${slug} deixou de funcionar.`
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível desligar.' }
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
        const { data } = await api.get(this.url, { params: { verificar: pedido } })
        if (pedido === this.novo.replace(/-+$/, '')) this.v = data.verificacao
      } catch { this.v = null } finally { this.aVerificar = false }
    },
    async guardar () {
      const novo = this.novo.replace(/-+$/, '')
      this.aGuardar = true; this.erro = ''
      try {
        const antigo = this.d.slug
        const corpo = this.admin ? { slug: novo, motivo: this.motivo, manter_antigo: this.manterAntigo } : { slug: novo }
        const { data } = await api.post(this.url, corpo)
        esquecerLoja(antigo, novo, this.lojaId)
        this.d = data
        this.editar = false
        this.ok = this.admin && !this.manterAntigo ? `Endereço mudado. /loja/${antigo} deixou de funcionar.`
          : `Endereço mudado. /loja/${antigo} continua a levar à loja.`
        this.motivo = ''; this.manterAntigo = true
        this.$emit('alterado', data.slug)
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
