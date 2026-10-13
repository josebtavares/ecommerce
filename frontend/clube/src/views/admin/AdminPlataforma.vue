<template>
  <!-- Definições do site — por agora o fuso horário em que se lêem os horários das lojas -->
  <div class="space-y-5 max-w-2xl">
    <div>
      <h2 class="text-lg font-bold text-zinc-100">Definições da plataforma</h2>
      <p class="text-xs text-zinc-500 mt-0.5">Valem para todas as lojas do site</p>
    </div>

    <div v-if="loading" class="h-48 bg-zinc-900 rounded-2xl animate-pulse"></div>

    <div v-else class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6">
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
  </div>
</template>

<script>
import api from '@/services/api'

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
    return { SUGESTOES, loading: true, aGuardar: false, guardado: false, erro: '',
             dados: { fusos: [] }, escolhido: '', pesquisa: '' }
  },

  computed: {
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
    } catch (e) {
      this.erro = e.response?.data?.detail || 'Não foi possível carregar as definições.'
    } finally {
      this.loading = false
    }
  },

  methods: {
    nome (fuso) { return SUGESTOES.find(s => s.fuso === fuso)?.nome || String(fuso || '').split('/').pop().replace(/_/g, ' ') },
    offset (z) { return z ? `${z.slice(0, 3)}:${z.slice(3)}` : '' },
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
