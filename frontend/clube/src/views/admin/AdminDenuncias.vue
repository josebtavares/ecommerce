<template>
  <!-- Denúncias do chat (moderar_chat). Só se lê a conversa de uma denúncia — nunca as outras. -->
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <button v-for="e in estados" :key="e.valor" type="button" @click="mudarEstado(e.valor)"
              :class="['px-4 py-2 rounded-xl text-sm font-semibold transition',
                       estado === e.valor ? 'bg-red-600 text-white' : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200']">
        {{ e.nome }}
        <span v-if="e.valor === 'pendente' && pendentes" class="ml-1.5 px-1.5 rounded-full bg-white/20 text-[11px]">{{ pendentes }}</span>
      </button>
      <p class="ml-auto text-xs text-zinc-500">Só vês as conversas que foram denunciadas.</p>
    </div>

    <p v-if="erro" class="text-sm text-red-400">{{ erro }}</p>
    <div v-if="aCarregar" class="text-sm text-zinc-500 py-8 text-center">A carregar…</div>
    <div v-else-if="!lista.length" class="text-sm text-zinc-500 py-10 text-center bg-zinc-900 border border-zinc-800 rounded-2xl">
      {{ estado === 'pendente' ? 'Sem denúncias por analisar. 🎉' : 'Sem denúncias resolvidas.' }}
    </div>

    <div v-for="d in lista" :key="d.id" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 space-y-3">
      <div class="flex flex-wrap items-start gap-3">
        <div class="flex-1 min-w-0">
          <p class="text-sm text-zinc-200"><font-awesome-icon :icon="['fas', 'flag']" class="text-red-400 mr-1.5" />{{ d.motivo }}</p>
          <p class="text-xs text-zinc-500 mt-1">
            Por {{ d.denunciante || 'conta removida' }} · {{ data(d.criada_em) }} ·
            Conversa entre {{ d.conversa.participantes.map(p => p.nome).join(' e ') }}
          </p>
          <p v-if="d.estado === 'resolvida'" class="text-xs text-emerald-400 mt-1">
            Resolvida por {{ d.resolvida_por }} · {{ data(d.resolvida_em) }}<span v-if="d.nota"> — {{ d.nota }}</span>
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                  @click="alternarConversa(d)">
            {{ abertas[d.id] ? 'Esconder conversa' : 'Ver conversa' }}
          </button>
          <button v-if="d.mensagem && !d.mensagem.apagada" type="button"
                  class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-500/15 text-red-400 hover:bg-red-500/25"
                  @click="apagar(d)">Apagar mensagem</button>
          <button v-if="d.estado === 'pendente'" type="button"
                  class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25"
                  @click="resolver(d)">Marcar como resolvida</button>
        </div>
      </div>

      <div v-if="d.mensagem" class="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
        <p class="text-[11px] text-zinc-500 mb-0.5">
          Mensagem denunciada · {{ d.mensagem.remetente.nome }}<span v-if="d.mensagem.autor && d.mensagem.remetente.tipo !== 'pessoal'"> (escrita por {{ d.mensagem.autor }})</span>
        </p>
        <p class="text-sm" :class="d.mensagem.apagada ? 'italic text-zinc-500' : 'text-zinc-200'">
          {{ d.mensagem.apagada ? 'Mensagem apagada' : (d.mensagem.texto || (d.mensagem.tipo === 'imagem' ? '📷 Imagem' : '')) }}
        </p>
      </div>

      <div v-if="abertas[d.id]" class="rounded-xl border border-zinc-800 bg-zinc-950 p-3 max-h-96 overflow-y-auto space-y-2">
        <div v-for="m in abertas[d.id]" :key="m.id"
             :class="['rounded-lg px-3 py-2 text-sm', m.denunciada ? 'bg-red-500/10 border border-red-500/30' : 'bg-zinc-900']">
          <p class="text-[11px] text-zinc-500">
            {{ m.remetente.nome }}<span v-if="m.autor && m.remetente.tipo !== 'pessoal'"> · {{ m.autor }}</span> · {{ data(m.criada_em) }}
            <span v-if="m.denunciada" class="text-red-400 font-semibold"> · denunciada</span>
          </p>
          <p v-if="m.apagada" class="italic text-zinc-500">Mensagem apagada</p>
          <template v-else>
            <img v-if="m.anexo" :src="m.anexo.url" alt="Imagem" class="mt-1 max-h-48 rounded-lg" />
            <p v-if="m.texto" class="text-zinc-200 whitespace-pre-wrap break-words">{{ m.texto }}</p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AdminDenuncias',
  emits: ['pendentes'],

  data () {
    return {
      estado: 'pendente', lista: [], pendentes: 0, aCarregar: false, erro: '', abertas: {},
      estados: [{ valor: 'pendente', nome: 'Por analisar' }, { valor: 'resolvida', nome: 'Resolvidas' }],
    }
  },

  mounted () { this.carregar() },

  methods: {
    data (iso) {
      return iso ? new Date(iso).toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''
    },
    async carregar () {
      this.aCarregar = true
      this.erro = ''
      try {
        const { data } = await api.get('/api/chat/denuncias/', { params: { estado: this.estado } })
        this.lista = data.results
        this.pendentes = data.pendentes
        this.$emit('pendentes', data.pendentes)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar as denúncias.'
      } finally {
        this.aCarregar = false
      }
    },
    mudarEstado (e) {
      this.estado = e
      this.abertas = {}
      this.carregar()
    },
    async alternarConversa (d) {
      if (this.abertas[d.id]) {
        const resto = { ...this.abertas }
        delete resto[d.id]
        this.abertas = resto
        return
      }
      try {
        const { data } = await api.get(`/api/chat/denuncias/${d.id}/conversa/`)
        this.abertas = { ...this.abertas, [d.id]: data.mensagens }
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível abrir a conversa.'
      }
    },
    async apagar (d) {
      if (!confirm('Apagar esta mensagem para todos os participantes?')) return
      try {
        await api.post(`/api/chat/denuncias/${d.id}/apagar-mensagem/`)
        d.mensagem.apagada = true
        if (this.abertas[d.id]) await this.alternarConversa(d).then(() => this.alternarConversa(d))
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível apagar.'
      }
    },
    async resolver (d) {
      const nota = prompt('Nota (opcional): o que foi feito?') ?? null
      if (nota === null) return
      try {
        await api.post(`/api/chat/denuncias/${d.id}/resolver/`, { nota })
        await this.carregar()
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível resolver.'
      }
    },
  },
}
</script>
