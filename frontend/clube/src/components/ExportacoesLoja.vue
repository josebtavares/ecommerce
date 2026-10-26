<!-- ExportacoesLoja.vue — exportar os dados de uma loja (ZIP com CSV). Usado no backoffice (dono) e no admin (Lojas).
     base: '/app/loja/<id>/exportacoes/' ou '/app/admin/lojas/<id>/exportacoes/' — Views/exportacaoLojaView.py -->
<template>
  <div class="space-y-3" data-teste="exportacoes-loja">
    <p class="text-xs text-zinc-400 leading-relaxed">
      Um ficheiro ZIP com os dados da loja em folhas de cálculo (abrem no Excel): produtos e stock, encomendas,
      clientes, devoluções, avaliações, serviços e marcações, vendas do POS e o arquivo fiscal com as faturas.
      Serve para guardar e consultar — não se importa de volta. Fica disponível {{ dias }} dias.
    </p>
    <p class="text-[11px] text-amber-300/90 leading-relaxed">
      <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="mr-1" />
      Tem dados pessoais dos clientes (nomes, emails, telefones, moradas). Guarda-o num lugar seguro.
    </p>

    <div class="flex flex-wrap items-center gap-3">
      <label class="flex items-center gap-2 text-xs text-zinc-300">
        <input type="checkbox" v-model="comImagens" class="accent-red-600" data-teste="exportar-imagens" />
        Incluir imagens e vídeos <span class="text-zinc-500">(ficheiro bem maior)</span>
      </label>
      <button type="button" @click="pedir" :disabled="aPedir || emCurso" data-teste="exportar"
        class="ml-auto px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold transition flex items-center gap-2">
        <font-awesome-icon :icon="['fas', emCurso ? 'spinner' : 'file-zipper']" :spin="emCurso" class="w-3.5 h-3.5" />
        {{ emCurso ? 'A preparar o ficheiro…' : 'Exportar dados' }}
      </button>
    </div>
    <p v-if="emCurso" class="text-[11px] text-zinc-500">Pode demorar uns minutos. Recebes uma notificação quando estiver pronto — podes sair desta página.</p>
    <p v-if="mensagem" :class="['text-xs', mensagem.erro ? 'text-red-400' : 'text-green-400']" role="status">{{ mensagem.texto }}</p>

    <div v-if="lista.results.length" class="rounded-xl border border-zinc-800 divide-y divide-zinc-800" data-teste="exportacoes-lista">
      <div v-for="e in lista.results" :key="e.id" class="px-3 py-2.5 flex flex-wrap items-center gap-x-3 gap-y-1.5" data-teste="exportacao-linha">
        <div class="min-w-0 flex-1">
          <p class="text-xs font-semibold text-zinc-200">
            {{ quando(e.criado_em) }}
            <span :class="['ml-1.5 px-1.5 py-0.5 rounded text-[10px] font-bold', COR[e.estado]]">{{ e.estado_label }}</span>
            <span v-if="e.com_imagens" class="ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-400">com imagens</span>
          </p>
          <p class="text-[11px] text-zinc-500 mt-0.5 break-words">
            <template v-if="e.pedido_por">por {{ e.pedido_por }}</template>
            <template v-if="e.estado === 'ok'"> · {{ tamanho(e.tamanho) }} · disponível até {{ quando(e.expira_em) }}</template>
            <template v-if="e.descargas"> · descarregado {{ e.descargas }}×</template>
            <template v-if="e.avisos"> · {{ e.avisos }} aviso(s) no LEIA-ME</template>
            <span v-if="e.estado === 'erro'" class="text-red-400"> · {{ e.erro || 'Falhou' }}</span>
          </p>
        </div>
        <button v-if="e.disponivel" type="button" @click="descarregar(e)" :disabled="aDescarregar === e.id"
          class="px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500 text-xs font-semibold text-zinc-200 disabled:opacity-40 transition flex items-center gap-1.5">
          <font-awesome-icon :icon="['fas', 'download']" class="w-3 h-3" /> Descarregar
        </button>
      </div>
    </div>
    <PaginacaoLista :count="lista.count" :limit="LIMITE" :offset="offset" @ir="carregar" />
  </div>
</template>

<script>
import api from '@/services/api'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'

const LIMITE = 10
const COR = {
  pendente: 'bg-zinc-800 text-zinc-300', a_correr: 'bg-sky-500/10 text-sky-300', ok: 'bg-green-500/10 text-green-400',
  erro: 'bg-red-500/10 text-red-400', expirada: 'bg-zinc-800 text-zinc-500',
}

export default {
  name: 'ExportacoesLoja',
  components: { PaginacaoLista },
  props: {
    base: { type: String, required: true },
  },
  data () {
    return {
      lista: { count: 0, results: [] }, offset: 0, emCurso: false, dias: 7,
      comImagens: false, aPedir: false, aDescarregar: null, mensagem: null, temporizador: null, LIMITE, COR,
    }
  },
  mounted () { this.carregar(0) },
  beforeUnmount () { clearTimeout(this.temporizador) },
  watch: { base () { this.carregar(0) } },
  methods: {
    async carregar (offset = this.offset) {
      clearTimeout(this.temporizador)
      try {
        const { data } = await api.get(this.base, { params: { limit: LIMITE, offset } })
        const estava = this.emCurso
        this.lista = data
        this.offset = offset
        this.emCurso = data.em_curso
        this.dias = data.dias_validade
        if (estava && !data.em_curso) {
          const ultima = data.results[0]
          this.mensagem = ultima?.estado === 'ok' ? { texto: 'O ficheiro está pronto.' } : { erro: true, texto: 'A exportação falhou. Tenta outra vez.' }
        }
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível carregar as exportações.' }
      }
      // enquanto há uma na fila, vai vendo de 5 em 5 segundos
      if (this.emCurso) this.temporizador = setTimeout(() => this.carregar(0), 5000)
    },
    async pedir () {
      this.aPedir = true; this.mensagem = null
      try {
        await api.post(this.base, { imagens: this.comImagens })
        this.emCurso = true
      } catch (e) {
        this.mensagem = { erro: true, texto: e.response?.data?.detail || 'Não foi possível pedir a exportação.' }
      } finally {
        this.aPedir = false
        this.carregar(0)
      }
    },
    async descarregar (e) {
      this.aDescarregar = e.id; this.mensagem = null
      try {
        const { data } = await api.post(`${this.base}${e.id}/descarregar/`)
        const a = document.createElement('a')
        a.href = data.url; a.download = data.nome; a.rel = 'noopener'
        document.body.appendChild(a); a.click(); a.remove()
      } catch (x) {
        this.mensagem = { erro: true, texto: x.response?.data?.detail || 'Não foi possível descarregar.' }
      } finally {
        this.aDescarregar = null
        this.carregar()
      }
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
