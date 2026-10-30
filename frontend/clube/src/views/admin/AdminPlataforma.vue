<template>
  <!-- Definições do site — por agora o fuso horário em que se lêem os horários das lojas -->
  <div class="space-y-5 max-w-2xl">
    <div>
      <h2 class="text-lg font-bold text-zinc-100">Definições da plataforma</h2>
      <p class="text-xs text-zinc-500 mt-0.5">Valem para todas as lojas do site</p>
    </div>

    <div v-if="loading" class="h-48 bg-zinc-900 rounded-2xl animate-pulse"></div>

    <!-- quem explora o site e contactos: rodapé de todas as páginas e página Contacto
         (a SISP e o banco revêem isto antes de activar o pagamento com cartão) -->
    <div v-if="!loading" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="plataforma-identificacao">
      <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Identificação e contactos</h3>
      <p class="text-xs text-zinc-500 mt-1 mb-4">
        Aparecem no rodapé de todas as páginas (home, lojas e checkout) e na página Contacto.
      </p>
      <div class="grid sm:grid-cols-2 gap-3">
        <label v-for="c in CAMPOS" :key="c.k" :class="['block', c.largo && 'sm:col-span-2']">
          <span class="text-xs font-semibold text-zinc-400 mb-1 block">{{ c.label }}</span>
          <input v-model="ident[c.k]" :type="c.tipo || 'text'" :placeholder="c.ph" :maxlength="c.max" :inputmode="c.modo"
            :data-teste="'ident-' + c.k"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
        </label>
      </div>
      <label class="flex items-start gap-3 mt-4 cursor-pointer">
        <input v-model="ident.mostrar_logos_pagamento" type="checkbox" data-teste="ident-logos"
          class="mt-0.5 w-4 h-4 accent-red-600" />
        <span class="text-sm text-zinc-300">
          Mostrar os logótipos vinti4 / Visa / Mastercard no rodapé
          <span class="block text-xs text-zinc-500">Liga só depois de teres o contrato com a SISP.</span>
        </span>
      </label>
      <label class="flex items-start gap-3 mt-3 cursor-pointer">
        <input v-model="ident.mostrar_selo_verificada" type="checkbox" data-teste="ident-selo"
          class="mt-0.5 w-4 h-4 accent-red-600" />
        <span class="text-sm text-zinc-300">
          Mostrar o selo "Loja verificada" na página da loja e nos cards
          <span class="block text-xs text-zinc-500">
            Lojas com o documento de identificação e o início de atividade aprovados (Admin → Lojas → Documentos).
            Desligado, só tu e o dono da loja o vêem.
          </span>
        </span>
      </label>
      <p v-if="erroIdent" class="text-sm text-red-400 mt-3" role="alert">{{ erroIdent }}</p>
      <div class="flex items-center gap-3 mt-4">
        <button type="button" @click="guardarIdent" :disabled="aGuardar || !identMudou" data-teste="ident-guardar"
          class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition">
          Guardar
        </button>
        <span v-if="guardadoIdent" class="text-sm text-green-400">Guardado.</span>
      </div>
    </div>

    <div v-if="!loading" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="cobrar-comissoes">
      <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Cobrança mensal das comissões</h3>
      <p class="text-xs text-zinc-500 mt-1 mb-4">
        A SISP não divide pagamentos: o dinheiro das vendas vai direto para a loja e a Bende cobra-lhe as comissões
        uma vez por mês (Admin → Comissões). Ao ligar, só contam as comissões a partir desse momento.
        Liga só quando os pagamentos forem a sério — com o pagamento simulado as lojas seriam cobradas por vendas de teste.
      </p>
      <div class="flex flex-wrap items-center gap-3">
        <button type="button" @click="alternarCobranca" :disabled="aGuardarCobranca" data-teste="cobrar-comissoes-alternar"
          :class="['px-5 py-2.5 rounded-xl text-sm font-bold transition disabled:opacity-40',
                   dados.cobrar_comissoes ? 'bg-zinc-700 hover:bg-zinc-600 text-zinc-100' : 'bg-red-600 hover:bg-red-500 text-white']">
          {{ dados.cobrar_comissoes ? 'Desligar' : 'Ligar a cobrança' }}
        </button>
        <span class="text-sm" :class="dados.cobrar_comissoes ? 'text-green-400' : 'text-zinc-500'" data-teste="cobrar-comissoes-estado">
          {{ dados.cobrar_comissoes ? `Ligada desde ${dados.cobrar_comissoes_desde}` : 'Desligada' }}
        </span>
      </div>
      <p v-if="erroCobranca" class="text-sm text-red-400 mt-3" role="alert">{{ erroCobranca }}</p>
    </div>

    <div v-if="!loading" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
      <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Fuso horário</h3>
      <p class="text-xs text-zinc-500 mt-1 mb-4">
        Os horários das lojas são lidos neste fuso: uma loja das 8h às 22h abre às 8h na hora daqui.
        Se o mudares, as lojas continuam com as mesmas horas, mas na hora local nova.
      </p>

      <div class="flex items-center gap-3 px-4 py-3 rounded-xl bg-zinc-800/50 mb-4">
        <font-awesome-icon :icon="['fas', 'clock']" class="w-4 h-4 text-zinc-400" />
        <span class="text-sm text-zinc-300">
          Agora: <b class="text-zinc-100">{{ dados.hora_local }}</b>
          <span class="text-zinc-500"> · {{ nome(dados.fuso_horario) }} (UTC{{ offset(dados.utc_offset) }})</span>
        </span>
      </div>

      <p class="text-xs font-semibold text-zinc-400 mb-2">Sugestões</p>
      <div class="flex flex-wrap gap-2 mb-4">
        <button v-for="s in SUGESTOES" :key="s.fuso" type="button" @click="escolhido = s.fuso"
          :class="['px-3 py-1.5 rounded-lg text-xs font-semibold border transition',
                   escolhido === s.fuso ? 'border-red-500 bg-red-500/10 text-red-300' : 'border-zinc-700 text-zinc-300 hover:border-zinc-500']">
          {{ s.nome }}
        </button>
      </div>

      <label for="fuso-pesquisa" class="text-xs font-semibold text-zinc-400 mb-1 block">Ou procura outro fuso</label>
      <input id="fuso-pesquisa" v-model="pesquisa" placeholder="ex.: Lisbon, Luanda, Sao_Paulo…"
        class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
      <div v-if="pesquisa.trim()" class="mt-2 max-h-48 overflow-y-auto rounded-xl border border-zinc-800 divide-y divide-zinc-800">
        <button v-for="f in filtrados" :key="f" type="button" @click="escolhido = f; pesquisa = ''"
          class="w-full text-left px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800">{{ f }}</button>
        <p v-if="!filtrados.length" class="px-3 py-2 text-sm text-zinc-500">Nenhum fuso encontrado.</p>
      </div>

      <p class="text-sm text-zinc-300 mt-4">
        Escolhido: <b class="text-zinc-100">{{ nome(escolhido) }}</b>
        <span class="text-zinc-500 text-xs"> ({{ escolhido }})</span>
      </p>

      <p v-if="erro" class="text-sm text-red-400 mt-3" role="alert">{{ erro }}</p>
      <div class="flex items-center gap-3 mt-4">
        <button type="button" @click="guardar" :disabled="aGuardar || escolhido === dados.fuso_horario"
          class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition">
          {{ aGuardar ? 'A guardar…' : 'Guardar fuso horário' }}
        </button>
        <span v-if="guardado" class="text-sm text-green-400">Guardado.</span>
      </div>
    </div>

    <!-- subscrições: dias grátis das lojas novas -->
    <div v-if="!loading" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
      <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Subscrições — período de teste</h3>
      <p class="text-xs text-zinc-500 mt-1 mb-4">
        Dias grátis das lojas novas que escolhem subscrição, contados a partir da aprovação. 0 = pagam desde o primeiro dia.
      </p>
      <div class="flex flex-wrap items-center gap-3">
        <input id="dias-teste" v-model.number="diasTeste" type="number" min="0" max="365" aria-label="Dias de teste"
          class="w-28 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" />
        <span class="text-sm text-zinc-400">dias</span>
        <button type="button" @click="guardarTeste" :disabled="aGuardar || diasTeste === dados.subscricao_dias_teste"
          class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition">
          Guardar
        </button>
        <span v-if="guardadoTeste" class="text-sm text-green-400">Guardado.</span>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const CAMPOS = [
  { k: 'titular_nome',      label: 'Nome do titular (pessoa ou empresa)', ph: 'ex.: Maria Silva', max: 200 },
  { k: 'titular_nif',       label: 'NIF do titular', ph: '9 dígitos', max: 9, modo: 'numeric' },
  { k: 'contacto_email',    label: 'Email de contacto', ph: 'ex.: suporte@bende.store', max: 254, tipo: 'email' },
  { k: 'contacto_telefone', label: 'Telefone', ph: 'ex.: +238 900 00 00', max: 40, tipo: 'tel' },
  { k: 'contacto_whatsapp', label: 'WhatsApp', ph: 'ex.: +238 900 00 00', max: 40, tipo: 'tel' },
  { k: 'contacto_horario',  label: 'Horário de atendimento', ph: 'ex.: Segunda a sexta, 9h–18h', max: 120 },
  { k: 'contacto_morada',   label: 'Morada', ph: 'ex.: Rua…, Praia, Cabo Verde', max: 300, largo: true },
]
const CHAVES_IDENT = [...CAMPOS.map(c => c.k), 'mostrar_logos_pagamento', 'mostrar_selo_verificada']

const SUGESTOES = [
  { fuso: 'Atlantic/Cape_Verde', nome: 'Cabo Verde' },
  { fuso: 'Europe/Lisbon',       nome: 'Portugal (Lisboa)' },
  { fuso: 'Atlantic/Azores',     nome: 'Açores' },
  { fuso: 'Africa/Bissau',       nome: 'Guiné-Bissau' },
  { fuso: 'Africa/Sao_Tome',     nome: 'São Tomé e Príncipe' },
  { fuso: 'Africa/Luanda',       nome: 'Angola' },
  { fuso: 'Africa/Maputo',       nome: 'Moçambique' },
  { fuso: 'America/Sao_Paulo',   nome: 'Brasil (São Paulo)' },
  { fuso: 'UTC',                 nome: 'UTC' },
]

export default {
  name: 'AdminPlataforma',
  data () {
    return { CAMPOS, ident: {}, erroIdent: '', guardadoIdent: false,
             SUGESTOES, loading: true, aGuardar: false, guardado: false, erro: '',
             dados: { fusos: [] }, aGuardarCobranca: false, erroCobranca: '', escolhido: '', pesquisa: '', diasTeste: 30, guardadoTeste: false }
  },

  computed: {
    identMudou () { return CHAVES_IDENT.some(k => this.ident[k] !== this.dados[k]) },
    filtrados () {
      const q = this.pesquisa.trim().toLowerCase().replace(/\s+/g, '_')
      return this.dados.fusos.filter(f => f.toLowerCase().includes(q)).slice(0, 50)
    },
  },

  async created () {
    try {
      const { data } = await api.get('/app/admin/plataforma/')
      this.dados = data
      this.escolhido = data.fuso_horario
      this.diasTeste = data.subscricao_dias_teste
      this.copiarIdent()
    } catch (e) {
      this.erro = e.response?.data?.detail || 'Não foi possível carregar as definições.'
    } finally {
      this.loading = false
    }
  },

  methods: {
    nome (fuso) { return SUGESTOES.find(s => s.fuso === fuso)?.nome || String(fuso || '').split('/').pop().replace(/_/g, ' ') },
    offset (z) { return z ? `${z.slice(0, 3)}:${z.slice(3)}` : '' },
    copiarIdent () { this.ident = Object.fromEntries(CHAVES_IDENT.map(k => [k, this.dados[k] ?? ''])) },
    async guardarIdent () {
      this.erroIdent = ''
      this.guardadoIdent = false
      this.aGuardar = true
      try {
        const { data } = await api.patch('/app/admin/plataforma/', this.ident)
        this.dados = { ...this.dados, ...data }
        this.copiarIdent()
        this.guardadoIdent = true
      } catch (e) {
        this.erroIdent = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
    async alternarCobranca () {
      const ligar = !this.dados.cobrar_comissoes
      if (!confirm(ligar
        ? 'Ligar a cobrança mensal das comissões? As lojas passam a receber cobranças das comissões das vendas a partir de agora.'
        : 'Desligar a cobrança? Deixam de se emitir cobranças novas (as já emitidas continuam por pagar). Ao voltar a ligar, só contam as comissões daí em diante.')) return
      this.erroCobranca = ''
      this.aGuardarCobranca = true
      try {
        const { data } = await api.patch('/app/admin/plataforma/', { cobrar_comissoes: ligar })
        this.dados = { ...this.dados, ...data }
      } catch (e) {
        this.erroCobranca = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardarCobranca = false
      }
    },
    async guardarTeste () {
      this.erro = ''
      this.guardadoTeste = false
      this.aGuardar = true
      try {
        const { data } = await api.patch('/app/admin/plataforma/', { subscricao_dias_teste: this.diasTeste })
        this.dados = { ...this.dados, ...data }
        this.diasTeste = data.subscricao_dias_teste
        this.guardadoTeste = true
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
    async guardar () {
      this.erro = ''
      this.guardado = false
      this.aGuardar = true
      try {
        const { data } = await api.patch('/app/admin/plataforma/', { fuso_horario: this.escolhido })
        this.dados = data
        this.escolhido = data.fuso_horario
        this.guardado = true
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        this.aGuardar = false
      }
    },
  },
}
</script>
