<template>
  <!-- Backups da base de dados (só super-admin) — Views/backupView.py, utils/backups.py -->
  <div class="space-y-5 max-w-4xl" data-teste="admin-backups">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Backups da base de dados</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Cópia completa de todos os dados da plataforma, guardada fora do Railway</p>
      </div>
      <button type="button" @click="fazer" :disabled="aFazer || resumo.a_correr" data-teste="backup-fazer"
        class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-bold transition flex items-center gap-2">
        <font-awesome-icon :icon="['fas', aFazer ? 'spinner' : 'database']" :spin="aFazer" class="w-4 h-4" />
        {{ aFazer ? 'A fazer o backup…' : 'Fazer backup agora' }}
      </button>
    </div>

    <p v-if="mensagem" :class="['text-sm', mensagem.erro ? 'text-red-400' : 'text-green-400']" role="status">{{ mensagem.texto }}</p>

    <div v-if="loading" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>

    <template v-else>
      <!-- resumo -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" data-teste="backup-resumo">
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Último backup</p>
          <p :class="['text-sm font-bold mt-1', atrasado ? 'text-amber-400' : 'text-zinc-100']">
            {{ resumo.ultimo_ok ? quando(resumo.ultimo_ok) : 'Nenhum' }}
          </p>
          <p v-if="atrasado" class="text-[11px] text-amber-400/80 mt-0.5">Há mais de 1 dia</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Próximo automático</p>
          <p class="text-sm font-bold text-zinc-100 mt-1">{{ quando(resumo.proximo_automatico) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Guardados</p>
          <p class="text-sm font-bold text-zinc-100 mt-1">{{ resumo.guardados }} · {{ tamanho(resumo.espaco) }}</p>
        </div>
        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
          <p class="text-xs text-zinc-500">Onde</p>
          <p class="text-sm font-bold text-zinc-100 mt-1">{{ resumo.armazenamento }}</p>
        </div>
      </div>
      <p class="text-xs text-zinc-500">
        Ficam {{ resumo.retencao }}; os mais antigos apagam-se sozinhos. Se um backup falhar, os super-admins recebem um email.
        Repor um backup não se faz aqui (apagava os dados atuais): pede-se ao suporte técnico, que o testa primeiro numa cópia.
      </p>

      <!-- lista -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800" data-teste="backup-lista">
        <p v-if="!lista.length" class="p-6 text-sm text-zinc-500 text-center">Ainda não há backups.</p>
        <div v-for="b in lista" :key="b.id" class="p-4 flex flex-wrap items-center gap-x-4 gap-y-2" data-teste="backup-linha">
          <font-awesome-icon :icon="['fas', ICONE[b.estado]]" :spin="b.estado === 'a_correr'"
            :class="['w-4 h-4 shrink-0', COR[b.estado]]" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-zinc-100">
              {{ quando(b.criado_em) }}
              <span :class="['ml-2 px-2 py-0.5 rounded-md text-[11px] font-bold',
                             b.tipo === 'manual' ? 'bg-sky-500/10 text-sky-300' : 'bg-zinc-800 text-zinc-400']">
                {{ b.tipo === 'manual' ? 'Manual' : 'Automático' }}
              </span>
            </p>
            <p class="text-xs text-zinc-500 mt-0.5 break-all">
              <template v-if="b.estado === 'ok'">{{ tamanho(b.tamanho) }} · {{ b.duracao_s }} s</template>
              <template v-else-if="b.estado === 'a_correr'">A correr…</template>
              <span v-else class="text-red-400">Falhou: {{ b.erro }}</span>
              <template v-if="b.pedido_por"> · por {{ b.pedido_por }}</template>
              <template v-if="b.descargas"> · descarregado {{ b.descargas }}×</template>
            </p>
          </div>
          <button v-if="b.disponivel" type="button" @click="descarregar(b)" :disabled="aDescarregar === b.id"
            class="px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500 text-xs font-semibold text-zinc-200 disabled:opacity-40 transition flex items-center gap-1.5">
            <font-awesome-icon :icon="['fas', 'download']" class="w-3 h-3" /> Descarregar
          </button>
        </div>
      </div>

      <!-- registo de descargas -->
      <div v-if="descargas.length" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4" data-teste="backup-descargas">
        <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Últimas descargas</h3>
        <p class="text-xs text-zinc-500 mt-1 mb-3">Cada backup tem os dados pessoais de todos os utilizadores: fica registado quem o descarregou.</p>
        <ul class="space-y-1.5">
          <li v-for="(d, i) in descargas" :key="i" class="text-xs text-zinc-400 break-all">
            <span class="text-zinc-200">{{ quando(d.quando) }}</span> · {{ d.por || '—' }} · {{ d.backup }}
            <span v-if="d.ip" class="text-zinc-600"> · IP {{ d.ip }}</span>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'

const ICONE = { ok: 'circle-check', erro: 'circle-xmark', a_correr: 'spinner' }
const COR = { ok: 'text-green-400', erro: 'text-red-400', a_correr: 'text-zinc-400' }

export default {
  name: 'AdminBackups',
  data () {
    return { loading: true, lista: [], resumo: {}, descargas: [], aFazer: false, aDescarregar: null, mensagem: null, ICONE, COR }
  },
  computed: {
    atrasado () {
      const u = this.resumo.ultimo_ok
      return !u || Date.now() - new Date(u).getTime() > 26 * 3600 * 1000
    },
  },
  mounted () { this.carregar() },
  methods: {
    async carregar () {
      try {
        const { data } = await api.get('/app/admin/backups/')
        this.lista = data.backups
        this.resumo = data.resumo
        this.descargas = data.descargas
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível carregar os backups.' }
      } finally { this.loading = false }
    },
    async fazer () {
      this.aFazer = true; this.mensagem = null
      try {
        const { data } = await api.post('/app/admin/backups/fazer/')
        this.mensagem = data.estado === 'ok'
          ? { texto: `Backup feito (${this.tamanho(data.tamanho)}).` }
          : { erro: true, texto: `O backup falhou: ${data.erro}` }
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'O backup falhou.' }
      } finally {
        this.aFazer = false
        this.carregar()
      }
    },
    async descarregar (b) {
      this.aDescarregar = b.id; this.mensagem = null
      try {
        const { data } = await api.post(`/app/admin/backups/${b.id}/descarregar/`)
        const a = document.createElement('a')
        a.href = data.url; a.download = data.nome; a.rel = 'noopener'
        document.body.appendChild(a); a.click(); a.remove()
        this.carregar()
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível descarregar.' }
      } finally { this.aDescarregar = null }
    },
    quando (d) {
      return d ? new Date(d).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
    },
    tamanho (b) {
      if (!b) return '0 KB'
      return b >= 1e6 ? `${(b / 1e6).toFixed(1).replace('.', ',')} MB` : `${Math.max(1, Math.round(b / 1e3))} KB`
    },
  },
}
</script>
