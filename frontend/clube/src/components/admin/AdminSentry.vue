<template>
  <!-- Sentry: confirma que os erros do servidor e do site chegam (clube/sentry.py, utils/sentry.js) -->
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="admin-sentry">
    <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Monitorização de erros (Sentry)</h3>
    <p class="text-xs text-zinc-500 mt-1 mb-4">
      Envia uma mensagem de teste e confirma no Sentry (Issues) que chegou. Não mexe em nada no site.
    </p>
    <div class="flex flex-wrap items-center gap-3 text-sm">
      <span class="text-zinc-400">Servidor:
        <b :class="servidor === null ? 'text-zinc-500' : servidor.ligado ? 'text-green-400' : 'text-amber-400'">
          {{ servidor === null ? '…' : servidor.ligado ? `ligado (${servidor.ambiente})` : 'desligado' }}</b>
      </span>
      <span class="text-zinc-400">Site:
        <b :class="site ? 'text-green-400' : 'text-amber-400'">{{ site ? `ligado (${ambienteSite})` : 'desligado' }}</b>
      </span>
    </div>
    <div class="flex flex-wrap items-center gap-3 mt-4">
      <button type="button" @click="testarServidor" :disabled="aEnviar || !servidor?.ligado" data-teste="sentry-testar-servidor"
        class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed text-zinc-100 text-sm font-semibold transition">
        Testar servidor
      </button>
      <button type="button" @click="testarSite" :disabled="aEnviar || !site" data-teste="sentry-testar-site"
        class="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed text-zinc-100 text-sm font-semibold transition">
        Testar site
      </button>
      <span v-if="resultado" class="text-sm" :class="resultado.ok ? 'text-green-400' : 'text-red-400'" data-teste="sentry-resultado">
        {{ resultado.texto }}</span>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { sentryLigado, testarSentry } from '@/utils/sentry'

export default {
  name: 'AdminSentry',
  data () {
    return { servidor: null, site: sentryLigado(), ambienteSite: process.env.VUE_APP_SENTRY_AMBIENTE || process.env.NODE_ENV,
             aEnviar: false, resultado: null }
  },
  async created () {
    try { this.servidor = (await api.get('/app/admin/plataforma/sentry/')).data } catch { this.servidor = { ligado: false } }
  },
  methods: {
    async testarServidor () {
      this.aEnviar = true; this.resultado = null
      try {
        const { data } = await api.post('/app/admin/plataforma/sentry/')
        this.resultado = { ok: !!data.evento, texto: data.evento ? `Enviado (${data.evento.slice(0, 8)}…)` : 'Sentry desligado no servidor.' }
      } catch (e) {
        this.resultado = { ok: false, texto: e.response?.data?.detail || 'Não foi possível enviar.' }
      } finally { this.aEnviar = false }
    },
    async testarSite () {
      this.aEnviar = true; this.resultado = null
      try {
        const id = await testarSentry()
        this.resultado = { ok: !!id, texto: id ? `Enviado (${id.slice(0, 8)}…)` : 'Não foi possível enviar.' }
      } finally { this.aEnviar = false }
    },
  },
}
</script>
