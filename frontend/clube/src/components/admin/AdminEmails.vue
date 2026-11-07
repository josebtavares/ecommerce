<!-- AdminEmails.vue — Admin → Definições → Emails: quanto do limite do Resend já foi usado (24 h e mês), o que está
     na fila ou à espera de lugar no limite, e os emails que falharam (com "Tentar outra vez").
     Backend: GET/POST /app/admin/emails/ (utils/fila_emails.py). -->
<template>
  <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-6" data-teste="admin-emails">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Emails</h3>
        <p class="text-xs text-zinc-500 mt-1">Saem por uma fila: se o Resend falhar, voltam a ser tentados sozinhos.
          Perto do limite, os essenciais (conta, pagamentos, faturas) passam à frente.</p>
      </div>
      <button type="button" @click="carregar" :disabled="aCarregar" class="text-xs text-zinc-400 hover:text-zinc-200 disabled:opacity-50"
              data-teste="emails-atualizar">{{ aCarregar ? '…' : 'Atualizar' }}</button>
    </div>

    <p v-if="erro" class="mt-4 text-sm text-red-400">{{ erro }}</p>
    <template v-else-if="d">
      <div class="mt-5 grid sm:grid-cols-2 gap-4">
        <div v-for="b in barras" :key="b.nome" :data-teste="'emails-uso-' + b.chave">
          <div class="flex items-baseline justify-between text-xs">
            <span class="font-semibold text-zinc-300">{{ b.nome }}</span>
            <span class="tabular-nums" :class="b.perc >= 90 ? 'text-red-400' : b.perc >= 70 ? 'text-amber-400' : 'text-zinc-400'">
              {{ b.usado }} / {{ b.limite }}</span>
          </div>
          <div class="mt-1.5 h-2 rounded-full bg-zinc-800 overflow-hidden">
            <div class="h-full rounded-full transition-all" :style="{ width: Math.min(100, b.perc) + '%' }"
                 :class="b.perc >= 90 ? 'bg-red-500' : b.perc >= 70 ? 'bg-amber-500' : 'bg-emerald-500'"></div>
          </div>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap gap-2 text-xs">
        <span class="px-2.5 py-1 rounded-lg bg-zinc-800 text-zinc-300" data-teste="emails-pendentes">Na fila: <b>{{ d.pendentes }}</b></span>
        <span v-if="d.adiados" class="px-2.5 py-1 rounded-lg bg-amber-500/15 text-amber-300" data-teste="emails-adiados">
          À espera de lugar no limite: <b>{{ d.adiados }}</b></span>
        <span class="px-2.5 py-1 rounded-lg" :class="d.falhados ? 'bg-red-500/15 text-red-300' : 'bg-zinc-800 text-zinc-300'"
              data-teste="emails-falhados">Falharam: <b>{{ d.falhados }}</b></span>
      </div>

      <div v-if="d.falhas.length" class="mt-5">
        <div class="flex items-center justify-between gap-3 mb-2">
          <p class="text-xs font-semibold text-zinc-400">Emails que não saíram</p>
          <button type="button" @click="reenviar()" :disabled="aReenviar" data-teste="emails-reenviar-todos"
                  class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold disabled:opacity-50">
            Tentar todos outra vez</button>
        </div>
        <ul class="divide-y divide-zinc-800 rounded-xl border border-zinc-800">
          <li v-for="f in d.falhas" :key="f.id" class="px-3 py-2.5 flex items-start justify-between gap-3" data-teste="emails-falha">
            <div class="min-w-0">
              <p class="text-sm text-zinc-200 truncate">{{ f.assunto }}</p>
              <p class="text-[11px] text-zinc-500 truncate">{{ f.para }} · {{ data(f.criado_em) }} · {{ f.tentativas }} tentativas</p>
              <p class="text-[11px] text-red-400/80 break-words">{{ f.erro }}</p>
            </div>
            <button type="button" @click="reenviar([f.id])" :disabled="aReenviar"
                    class="flex-shrink-0 px-2.5 py-1 rounded-lg border border-zinc-700 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50">
              Tentar</button>
          </li>
        </ul>
      </div>
      <p class="mt-4 text-[11px] text-zinc-500">
        Ao mudar de plano no Resend, muda as variáveis <code>EMAIL_LIMITE_DIA</code> e <code>EMAIL_LIMITE_MES</code> no Railway (serviços ecommerce e worker).
        O registo dos emails é apagado ao fim de {{ d.retencao_dias }} dias.</p>
    </template>
    <div v-else class="mt-4 h-16 rounded-xl bg-zinc-800 animate-pulse"></div>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'

export default {
  name: 'AdminEmails',
  data () { return { d: null, erro: '', aCarregar: false, aReenviar: false } },
  computed: {
    barras () {
      const u = this.d?.uso
      if (!u) return []
      return [
        { chave: 'dia', nome: 'Últimas 24 horas', usado: u.dia, limite: u.limite_dia, perc: 100 * u.dia / u.limite_dia },
        { chave: 'mes', nome: 'Este mês', usado: u.mes, limite: u.limite_mes, perc: 100 * u.mes / u.limite_mes },
      ]
    },
  },
  mounted () { this.carregar() },
  methods: {
    async carregar () {
      this.aCarregar = true
      try {
        this.d = (await api.get('/app/admin/emails/')).data
        this.erro = ''
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar os emails.'
      } finally { this.aCarregar = false }
    },
    async reenviar (ids) {
      this.aReenviar = true
      try {
        const { data } = await api.post('/app/admin/emails/', ids ? { ids } : {})
        this.d = data
        toast.success(data.reenviar === 1 ? 'Um email voltou à fila.' : `${data.reenviar} emails voltaram à fila.`)
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível.')
      } finally { this.aReenviar = false }
    },
    data (iso) {
      try { return new Date(iso).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) } catch (e) { return '' }
    },
  },
}
</script>
