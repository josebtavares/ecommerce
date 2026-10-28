<template>
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/70 backdrop-blur-sm"
       @click.self="$emit('fechar')">
    <div class="bg-zinc-900 border border-zinc-800 w-full sm:max-w-2xl max-h-[92vh] sm:max-h-[90vh] overflow-y-auto shadow-2xl rounded-t-2xl sm:rounded-2xl">

      <div class="flex justify-center pt-3 pb-1 sm:hidden">
        <div class="w-10 h-1 bg-zinc-700 rounded-full"></div>
      </div>

      <div v-if="!u" class="p-10 flex justify-center">
        <svg class="animate-spin h-6 w-6 text-red-500" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
      </div>

      <template v-else>
        <!-- Header -->
        <div class="flex items-center gap-4 p-5 border-b border-zinc-800">
          <img v-if="u.foto_url" :src="u.foto_url" class="w-14 h-14 rounded-full object-cover flex-shrink-0" />
          <div v-else class="w-14 h-14 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
            <span class="text-2xl font-bold text-zinc-400">{{ u.username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <h2 class="text-base font-bold text-zinc-100">{{ u.username }}</h2>
              <span :class="['px-1.5 py-0.5 rounded text-[10px] font-bold', estado.classe]">{{ estado.label }}</span>
              <span v-if="u.role_admin" class="px-1.5 py-0.5 bg-purple-500/15 text-purple-400 text-[10px] rounded font-bold capitalize">{{ u.role_admin }}</span>
            </div>
            <p class="text-xs text-zinc-500 truncate">{{ u.nome }} · {{ u.email }}</p>
            <p class="text-xs text-zinc-600 mt-0.5">Desde {{ data(u.data_criacao) }} · último acesso {{ u.ultimo_login ? dataHora(u.ultimo_login) : 'nunca' }}</p>
          </div>
          <button @click="$emit('fechar')" data-teste="fechar-ficha"
            class="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-5 space-y-5">
          <!-- estado actual -->
          <div v-if="u.status !== 'ativo'" data-teste="estado-actual"
               :class="['rounded-xl border px-4 py-3 text-sm', u.status === 'banido' ? 'border-red-500/30 bg-red-500/10 text-red-300' : 'border-amber-500/30 bg-amber-500/10 text-amber-300']">
            <p class="font-bold">{{ u.status === 'banido' ? 'Conta banida' : (u.suspenso_ate ? `Suspensa até ${u.suspenso_ate_txt}` : 'Suspensa até ser reactivada') }}</p>
            <p v-if="u.motivo_estado" class="text-xs mt-0.5">Motivo: {{ u.motivo_estado }}</p>
          </div>

          <!-- dados -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="bg-zinc-800 rounded-xl p-3 text-center">
              <p class="text-lg font-extrabold text-zinc-100">{{ u.lojas.length }}</p><p class="text-[10px] text-zinc-500">Lojas</p>
            </div>
            <div class="bg-zinc-800 rounded-xl p-3 text-center">
              <p class="text-lg font-extrabold text-zinc-100">{{ u.pos.length }}</p><p class="text-[10px] text-zinc-500">POS</p>
            </div>
            <div class="bg-zinc-800 rounded-xl p-3 text-center">
              <p class="text-lg font-extrabold text-blue-400">{{ u.total_encomendas }}</p><p class="text-[10px] text-zinc-500">Encomendas feitas</p>
            </div>
            <div class="bg-zinc-800 rounded-xl p-3 text-center">
              <p class="text-lg font-extrabold" :class="u.verificado ? 'text-green-400' : 'text-zinc-500'">{{ u.verificado ? 'Sim' : 'Não' }}</p><p class="text-[10px] text-zinc-500">Verificado</p>
            </div>
          </div>

          <div v-if="u.lojas.length || u.pos.length" class="space-y-1.5">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Lojas e POS</p>
            <div class="flex flex-wrap gap-2">
              <router-link v-for="l in u.lojas" :key="'l' + l.id" :to="`/admin/lojas/${l.id}`"
                class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 transition">
                {{ l.nome }} <span class="text-zinc-500">· {{ l.estado }}</span>
              </router-link>
              <span v-for="p in u.pos" :key="'p' + p.id" class="px-2.5 py-1 rounded-lg bg-zinc-800 text-xs text-zinc-300">
                POS {{ p.nome }} <span class="text-zinc-500">· {{ p.suspenso ? 'suspenso' : 'activo' }}</span>
              </span>
            </div>
          </div>

          <!-- acções -->
          <div v-if="podeMexer" class="space-y-3" data-teste="moderacao">
            <div v-if="!acao" class="flex flex-wrap gap-2">
              <button v-if="u.status === 'ativo'" @click="abrir('suspender')" data-teste="btn-suspender"
                class="px-4 py-2 rounded-xl bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 text-sm font-bold transition">Suspender</button>
              <button v-if="u.status !== 'banido' && souSuperadmin" @click="abrir('banir')" data-teste="btn-banir"
                class="px-4 py-2 rounded-xl bg-red-500/15 text-red-400 hover:bg-red-500/25 text-sm font-bold transition">Banir</button>
              <button v-if="u.status === 'suspenso' || (u.status === 'banido' && souSuperadmin)" @click="abrir('levantar')" data-teste="btn-levantar"
                class="px-4 py-2 rounded-xl bg-green-500/15 text-green-400 hover:bg-green-500/25 text-sm font-bold transition">
                {{ u.status === 'banido' ? 'Levantar ban' : 'Reactivar' }}
              </button>
              <p v-if="u.status === 'banido' && !souSuperadmin" class="text-xs text-zinc-500">Só o Super Admin pode levantar um ban.</p>
            </div>

            <div v-else class="rounded-xl border border-zinc-800 bg-zinc-950 p-4 space-y-3">
              <p class="text-sm font-bold text-zinc-100">{{ TITULOS[acao] }}</p>
              <p class="text-xs text-zinc-500">{{ AJUDA[acao] }}</p>
              <div v-if="acao !== 'levantar'">
                <label class="text-xs text-zinc-500 mb-1 block">Motivo (o utilizador recebe-o por email)</label>
                <textarea v-model="motivo" rows="2" maxlength="500" data-teste="motivo"
                  class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition"></textarea>
              </div>
              <div v-if="acao === 'suspender'">
                <label class="text-xs text-zinc-500 mb-1 block">Até (opcional — sem data fica suspensa até a reactivares)</label>
                <input v-model="ate" type="date" :min="hoje" data-teste="ate"
                  class="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 transition" />
              </div>
              <p v-if="erro" class="text-xs text-red-400" data-teste="erro">{{ erro }}</p>
              <div class="flex gap-2">
                <button @click="acao = null" class="px-4 py-2 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200 transition">Cancelar</button>
                <button @click="confirmar" :disabled="aGuardar" data-teste="confirmar"
                  :class="['px-4 py-2 rounded-xl text-white text-sm font-bold transition disabled:opacity-50',
                           acao === 'levantar' ? 'bg-green-600 hover:bg-green-500' : acao === 'banir' ? 'bg-red-600 hover:bg-red-500' : 'bg-amber-600 hover:bg-amber-500']">
                  {{ aGuardar ? 'A guardar...' : TITULOS[acao] }}
                </button>
              </div>
            </div>
          </div>

          <!-- histórico -->
          <div class="space-y-1.5">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Histórico de moderação</p>
            <p v-if="!u.moderacoes.length" class="text-xs text-zinc-500">Sem suspensões nem bans.</p>
            <div v-for="m in u.moderacoes" :key="m.id" data-teste="historico-linha"
                 class="flex items-start gap-3 rounded-xl bg-zinc-800/50 px-3 py-2">
              <span :class="['mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-bold flex-shrink-0', CORES[m.acao]]">{{ m.acao_nome }}</span>
              <div class="min-w-0 flex-1">
                <p v-if="m.motivo" class="text-xs text-zinc-300">{{ m.motivo }}</p>
                <p class="text-[11px] text-zinc-500">
                  {{ dataHora(m.criado_em) }}
                  <template v-if="m.feito_por"> · por {{ m.feito_por }}</template>
                  <template v-else-if="m.acao === 'expirou'"> · automático</template>
                  <template v-if="m.acao === 'suspender'"> · {{ m.ate ? `até ${m.ate_txt}` : 'sem data de fim' }}</template>
                </p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const TITULOS = { suspender: 'Suspender conta', banir: 'Banir conta', levantar: 'Reactivar conta' }
const AJUDA = {
  suspender: 'A pessoa deixa de conseguir entrar no site e no POS e as sessões abertas terminam.',
  banir: 'Permanente: só o Super Admin levanta. O email fica bloqueado para contas novas.',
  levantar: 'A conta volta a funcionar e a pessoa recebe um email a avisar.',
}
const CORES = {
  suspender: 'bg-amber-500/15 text-amber-400', banir: 'bg-red-500/15 text-red-400',
  levantar: 'bg-green-500/15 text-green-400', expirou: 'bg-zinc-700 text-zinc-300',
}

export default {
  name: 'UtilizadorFicha',
  props: { id: { type: Number, required: true } },
  emits: ['fechar', 'mudou', 'naoExiste'],
  data () {
    const eu = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      u: null, acao: null, motivo: '', ate: '', erro: '', aGuardar: false,
      souSuperadmin: eu.role_admin === 'superadmin', meuId: eu.id,
      TITULOS, AJUDA, CORES,
    }
  },
  computed: {
    estado () {
      if (!this.u || this.u.status === 'ativo') return { label: 'Activa', classe: 'bg-green-500/15 text-green-400' }
      if (this.u.status === 'banido') return { label: 'Banida', classe: 'bg-red-500/15 text-red-400' }
      return { label: this.u.suspenso_ate ? `Suspensa até ${this.u.suspenso_ate_txt}` : 'Suspensa', classe: 'bg-amber-500/15 text-amber-400' }
    },
    // a própria conta e contas da equipa (sem ser superadmin) não se moderam aqui (o servidor também recusa)
    podeMexer () { return this.u && this.u.id !== this.meuId && (this.souSuperadmin || !this.u.is_staff) },
    hoje () { return new Date().toLocaleDateString('sv') },
  },
  watch: { id: { handler: 'carregar', immediate: true } },
  methods: {
    async carregar () {
      this.u = null; this.acao = null
      try {
        const { data } = await api.get(`/app/admin/utilizadores/${this.id}/`)
        this.u = data
      } catch (e) {
        if (e.response?.status === 404) this.$emit('naoExiste')
      }
    },
    abrir (acao) { this.acao = acao; this.motivo = ''; this.ate = ''; this.erro = '' },
    async confirmar () {
      this.erro = ''
      if (this.acao !== 'levantar' && this.motivo.trim().length < 5) { this.erro = 'Escreve o motivo.'; return }
      this.aGuardar = true
      try {
        const corpo = { acao: this.acao, motivo: this.motivo.trim() }
        if (this.acao === 'suspender' && this.ate) corpo.ate = this.ate
        const { data } = await api.post(`/app/admin/utilizadores/${this.id}/moderar/`, corpo)
        this.u = data; this.acao = null
        this.$emit('mudou', data)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally { this.aGuardar = false }
    },
    data (v) { return v ? new Date(v).toLocaleDateString('pt-PT') : '—' },
    dataHora (v) { return v ? new Date(v).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) : '—' },
  },
}
</script>
