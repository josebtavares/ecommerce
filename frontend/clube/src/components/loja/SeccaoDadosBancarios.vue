<!-- SeccaoDadosBancarios.vue — Configurações da loja (só o dono): a conta bancária da loja (as vendas com cartão
     vão direto para a conta do contrato vinti4 — components/loja/SeccaoVinti4).
     Backend: GET/PUT /app/loja/<id>/banco/ (utils/banco.py). Mudar pede a password; fica no registo das
     transações e o dono recebe um email. -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="seccao-banco">
    <h2 class="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-1">Dados bancários</h2>
    <p class="text-xs text-zinc-600 mb-5">
      A conta bancária da loja (a mesma do contrato vinti4, se o tiveres). Precisas dela para aceitar transferências:
      o banco, o titular e o IBAN são mostrados <strong class="text-zinc-400">só aos clientes que encomendarem por transferência</strong>,
      para saberem para onde pagar. Só tu alteras estes dados; cada alteração fica registada e recebes um email.
    </p>

    <p v-if="carregando" class="text-xs text-zinc-500">A carregar…</p>

    <!-- resumo -->
    <div v-else-if="dados && !editar" class="flex flex-col sm:flex-row sm:items-center gap-4" data-teste="banco-resumo">
      <div class="flex-1 min-w-0 text-sm space-y-0.5">
        <p class="text-zinc-100 font-semibold">{{ dados.banco }}</p>
        <p class="text-zinc-300 font-mono tracking-wide break-all">{{ dados.iban }}</p>
        <p class="text-xs text-zinc-500">Titular: {{ dados.titular }}</p>
        <p v-if="dados.atualizado_em" class="text-[11px] text-zinc-600">Atualizado em {{ data(dados.atualizado_em) }}</p>
      </div>
      <button type="button" @click="abrir" data-teste="banco-alterar"
        class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-semibold transition flex-shrink-0">
        Alterar
      </button>
    </div>

    <!-- formulário -->
    <form v-else @submit.prevent="guardar" class="space-y-4" data-teste="banco-form">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-zinc-500 mb-1 block" for="banco-banco">Banco</label>
          <select id="banco-banco" v-model="form.banco" data-teste="banco-banco"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition">
            <option value="" disabled>Escolhe o banco</option>
            <option v-for="b in bancos" :key="b" :value="b">{{ b }}</option>
          </select>
          <p v-if="erros.banco" class="mt-1 text-xs text-red-400">{{ erros.banco }}</p>
        </div>
        <div>
          <label class="text-xs text-zinc-500 mb-1 block" for="banco-titular">Titular da conta</label>
          <input id="banco-titular" v-model="form.titular" autocomplete="off" maxlength="120" data-teste="banco-titular"
            placeholder="Nome como aparece no banco"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500 transition" />
          <p v-if="erros.titular" class="mt-1 text-xs text-red-400">{{ erros.titular }}</p>
        </div>
        <div class="sm:col-span-2">
          <label class="text-xs text-zinc-500 mb-1 block" for="banco-nib">NIB ou IBAN</label>
          <input id="banco-nib" v-model="form.nib" autocomplete="off" inputmode="text" maxlength="40" data-teste="banco-nib"
            placeholder="CV64 0003 0000 0000 0000 0000 0"
            class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 font-mono placeholder-zinc-600 focus:outline-none focus:border-red-500 transition" />
          <p v-if="erros.nib" class="mt-1 text-xs text-red-400">{{ erros.nib }}</p>
          <p v-else class="mt-1 text-[11px] text-zinc-600">21 dígitos do NIB, ou o IBAN completo (começa por CV64). Está no extracto ou na app do banco.</p>
        </div>
        <div v-if="pedePassword" class="sm:col-span-2">
          <label class="text-xs text-zinc-500 mb-1 block" for="banco-password">A tua password (para confirmar)</label>
          <input id="banco-password" v-model="form.password" type="password" autocomplete="current-password" data-teste="banco-password"
            class="w-full sm:w-72 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
          <p v-if="erros.password" class="mt-1 text-xs text-red-400">{{ erros.password }}</p>
        </div>
      </div>
      <p v-if="erroGeral" class="text-xs text-red-400">{{ erroGeral }}</p>
      <div class="flex items-center gap-3">
        <button type="submit" :disabled="aGuardar" data-teste="banco-guardar"
          class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold transition">
          {{ aGuardar ? 'A guardar…' : 'Guardar dados bancários' }}
        </button>
        <button v-if="dados" type="button" @click="editar = false" class="text-sm text-zinc-400 hover:text-zinc-200">Cancelar</button>
      </div>
    </form>
    <p v-if="guardado" class="mt-3 text-xs text-green-500" data-teste="banco-guardado">Guardado ✓ — enviámos-te um email a confirmar.</p>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'SeccaoDadosBancarios',

  props: {
    lojaId: { type: [String, Number], required: true },
  },

  data () {
    return {
      // quem entrou só com Google e ainda não definiu password não tem password para confirmar
      pedePassword: true,
      carregando: true, dados: null, bancos: [], editar: false, aGuardar: false, guardado: false,
      form: { banco: '', nib: '', titular: '', password: '' }, erros: {}, erroGeral: '',
    }
  },

  emits: ['guardado'],

  async created () {
    try {
      const { data } = await api.get(`/app/loja/${this.lojaId}/banco/`)
      this.dados = data.dados
      this.bancos = data.bancos
      this.pedePassword = data.pede_password !== false
    } catch { this.erroGeral = 'Não foi possível carregar os dados bancários.' }
    finally { this.carregando = false }
  },

  methods: {
    data (iso) { return new Date(iso).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) },

    abrir () {
      this.form = { banco: this.dados?.banco || '', nib: this.dados?.iban || '', titular: this.dados?.titular || '', password: '' }
      this.erros = {}; this.erroGeral = ''; this.guardado = false
      this.editar = true
    },

    async guardar () {
      this.aGuardar = true; this.erros = {}; this.erroGeral = ''; this.guardado = false
      try {
        const { data } = await api.put(`/app/loja/${this.lojaId}/banco/`, this.form)
        this.dados = data.dados
        this.editar = false
        this.guardado = true
        this.form.password = ''
        this.$emit('guardado')         // a transferência passa a aparecer aos clientes
      } catch (e) {
        const d = e.response?.data
        if (d && typeof d === 'object' && !d.detail) this.erros = d
        else this.erroGeral = d?.detail || 'Não foi possível guardar.'
      } finally { this.aGuardar = false }
    },
  },
}
</script>
