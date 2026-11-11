<template>
  <!-- Admin → Pagamentos → Cartão (vinti4) → Reconciliação: ficheiros VBVT diários da SISP (Plan Test 36–37).
       Backend: Views/pagamentosAdminView.py vbvt / vbvt_detalhe, pagamentos/vbvt.py -->
  <div class="space-y-4" data-teste="vbvt">
    <form class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-3" @submit.prevent="enviar">
      <div>
        <p class="text-sm font-semibold text-zinc-200">Carregar ficheiro de reconciliação (VBVT)</p>
        <p class="text-[11px] text-zinc-500 mt-0.5">
          O ficheiro diário do Portal do Comerciante da SISP. Cada compra e estorno é comparado com os nossos pagamentos;
          o ficheiro nunca dá nada como pago — o que a SISP aprovou e cá não está pago confirma-se com "Perguntar à SISP".
          Os ficheiros têm de ser carregados por ordem (cada um diz qual é o anterior).
        </p>
      </div>
      <p v-if="semMerchantId" class="text-[11px] text-amber-300">
        O Merchant ID da Bendi não está definido (variável VINTI4_MERCHANT_ID): só se aceitam ficheiros das lojas com contrato.
      </p>
      <div class="flex flex-wrap items-center gap-3">
        <input ref="ficheiro" type="file" accept=".txt,.dat,.vbvt,text/plain" @change="escolhido = $event.target.files[0] || null"
               data-teste="vbvt-ficheiro" class="text-xs text-zinc-300 file:mr-3 file:px-3 file:py-1.5 file:rounded-lg file:border-0 file:bg-zinc-800 file:text-zinc-200" />
        <label v-if="sequenciaPartida" class="flex items-center gap-2 text-xs text-amber-300">
          <input v-model="forcar" type="checkbox" data-teste="vbvt-forcar" />
          Aceitar mesmo com a sequência partida (falta um ficheiro — fica registado)
        </label>
        <button type="submit" :disabled="!escolhido || enviando" data-teste="vbvt-enviar"
                class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-bold">
          {{ enviando ? 'A processar…' : 'Processar' }}
        </button>
      </div>
      <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>
    </form>

    <div v-if="carregando && !d" class="h-32 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <div v-else-if="d" class="bg-zinc-900 rounded-2xl border border-zinc-800 divide-y divide-zinc-800" data-teste="vbvt-lista">
      <div v-for="f in d.results" :key="f.id" class="px-4 py-3">
        <button type="button" class="w-full text-left flex flex-wrap items-center gap-x-3 gap-y-1" @click="abrir(f)">
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold',
                         f.estado === 'aplicado' ? 'bg-green-500/15 text-green-300' : 'bg-red-500/15 text-red-300']">{{ f.estado_nome }}</span>
          <div class="flex-1 min-w-[200px]">
            <p class="text-sm text-zinc-200">{{ dataCurta(f.data) || '—' }} · nº {{ tres(f.sequencia) }}
              <span class="text-[11px] text-zinc-500">· {{ f.dono }} · Merchant ID {{ f.merchant_id || '—' }}</span></p>
            <p class="text-[11px] text-zinc-500">{{ f.nome }} · {{ f.carregado_por }} · {{ f.carregado_em }}
              <template v-if="f.forcado"> · <span class="text-amber-300">sequência aceite à mão</span></template></p>
            <p v-if="f.n_erros" class="text-[11px] text-red-300">{{ f.n_erros }} erro(s)</p>
            <p v-else-if="f.resumo?.problemas" class="text-[11px] text-amber-300">{{ f.resumo.problemas }} diferença(s) a ver</p>
          </div>
          <span v-if="f.resumo?.registos !== undefined" class="text-xs text-zinc-400 tabular-nums">
            {{ f.resumo.compras_aprovadas }} compras · {{ f.resumo.total_compras }} CVE</span>
        </button>

        <div v-if="aberto && aberto.id === f.id" class="mt-3 rounded-xl bg-zinc-950/60 border border-zinc-800 p-3 space-y-3 text-[11px] text-zinc-400" data-teste="vbvt-ficha">
          <div v-if="aberto.erros.length">
            <p class="font-semibold text-red-300 mb-1">Erros — o ficheiro não foi aplicado</p>
            <p v-for="(e, i) in aberto.erros" :key="'e' + i">Linha {{ e.linha }}: {{ e.erro }}</p>
          </div>
          <div v-if="aberto.avisos.length">
            <p class="font-semibold text-amber-300 mb-1">Avisos</p>
            <p v-for="(e, i) in aberto.avisos" :key="'a' + i">Linha {{ e.linha }}: {{ e.erro }}</p>
          </div>
          <div v-if="aberto.resumo?.registos !== undefined" class="grid sm:grid-cols-3 gap-x-6 gap-y-1">
            <p>Compras aprovadas: <span class="text-zinc-200">{{ aberto.resumo.compras_aprovadas }} · {{ aberto.resumo.total_compras }} CVE</span></p>
            <p>Estornos: <span class="text-zinc-200">{{ aberto.resumo.estornos }} · {{ aberto.resumo.total_estornos }} CVE</span></p>
            <p>Comissões SISP: <span class="text-zinc-200">{{ aberto.resumo.comissoes }} CVE</span></p>
            <p>Líquido: <span class="text-zinc-200">{{ aberto.resumo.liquido }} CVE</span></p>
            <p>Anterior: <span class="text-zinc-200">{{ dataCurta(aberto.data_anterior) || '—' }} nº {{ tres(aberto.sequencia_anterior) }}</span></p>
          </div>
          <div v-if="aberto.linhas.length" class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="text-zinc-500">
                <tr><th class="py-1 pr-3">Linha</th><th class="pr-3">Tipo</th><th class="pr-3">merchantRef</th><th class="pr-3">Quando</th>
                  <th class="pr-3">Cartão</th><th class="pr-3 text-right">Valor</th><th class="pr-3">Resultado</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-for="l in aberto.linhas" :key="l.linha" :class="aberto.problemas.includes(l.resultado) ? 'text-amber-200' : 'text-zinc-300'">
                  <td class="py-1 pr-3 tabular-nums">{{ l.linha }}</td>
                  <td class="pr-3">{{ l.tipo }}{{ l.aprovada ? '' : ' (recusada)' }}</td>
                  <td class="pr-3 font-mono">{{ l.ref }}<template v-if="l.ref_original"> → {{ l.ref_original }}</template></td>
                  <td class="pr-3 whitespace-nowrap">{{ l.quando }}</td>
                  <td class="pr-3">{{ l.cartao }} {{ l.pan }}</td>
                  <td class="pr-3 text-right tabular-nums whitespace-nowrap">{{ l.valor }}<template v-if="l.valor_nosso"> (cá {{ l.valor_nosso }})</template></td>
                  <td class="pr-3">{{ aberto.resultados[l.resultado] || l.resultado }}</td>
                  <td>
                    <button v-if="l.resultado === 'paga_so_na_sisp' && l.tx_id" type="button" :disabled="perguntando === l.tx_id"
                            @click="perguntar(l)" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 whitespace-nowrap">
                      {{ perguntando === l.tx_id ? 'A perguntar…' : 'Perguntar à SISP' }}</button>
                    <span v-if="respostas[l.tx_id]" class="block text-zinc-400">{{ respostas[l.tx_id] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="aberto.linhas.length < (aberto.resumo?.registos || 0)" class="mt-1 text-zinc-500">
              Mostram-se as primeiras {{ aberto.linhas.length }} linhas.</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button type="button" @click="copiar" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold">
              {{ copiado ? 'Copiado ✓' : 'Copiar relatório (para enviar à SISP)' }}</button>
          </div>
        </div>
      </div>
      <p v-if="!d.results.length" class="text-center py-10 text-sm text-zinc-500">Ainda não foi carregado nenhum ficheiro.</p>
    </div>
    <PaginacaoLista v-if="d" :count="d.count" :limit="LIMITE" :offset="offset" @ir="carregar" />
  </div>
</template>

<script>
import api from '@/services/api'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'

const LIMITE = 20

export default {
  name: 'ReconciliacaoVBVT',
  components: { PaginacaoLista },
  emits: ['mudou'],
  data () {
    return {
      LIMITE, d: null, offset: 0, carregando: false, erro: '', escolhido: null, enviando: false, forcar: false,
      sequenciaPartida: false, aberto: null, copiado: false, perguntando: null, respostas: {},
    }
  },
  computed: {
    semMerchantId () { return this.d && this.d.merchant_id_bendi === false },
  },
  created () { this.carregar(0) },
  methods: {
    tres (n) { return n || n === 0 ? String(n).padStart(3, '0') : '—' },
    dataCurta (iso) { return iso ? iso.split('-').reverse().join('/') : '' },
    async carregar (offset = this.offset) {
      this.offset = offset
      const silencioso = !!this.d          // tempo real: recarrega por baixo, sem esconder a lista
      if (!silencioso) this.carregando = true
      try {
        const { data } = await api.get('/app/admin/pagamentos/vbvt/', { params: { limit: LIMITE, offset } })
        this.d = data
      } catch (e) {
        if (!silencioso) this.erro = e.response?.data?.detail || 'Não foi possível carregar os ficheiros.'
      } finally { this.carregando = false }
    },
    async enviar () {
      if (!this.escolhido) return
      this.enviando = true
      this.erro = ''
      try {
        const fd = new FormData()
        fd.append('ficheiro', this.escolhido)
        if (this.forcar) fd.append('forcar', '1')
        const { data } = await api.post('/app/admin/pagamentos/vbvt/', fd)
        this.sequenciaPartida = data.estado === 'rejeitado' && data.erros.some(e => e.erro.startsWith('Sequência'))
        this.forcar = false
        if (data.estado === 'aplicado') {
          this.escolhido = null
          if (this.$refs.ficheiro) this.$refs.ficheiro.value = ''
          this.$emit('mudou')
        }
        await this.carregar(0)
        this.aberto = data
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível processar o ficheiro.'
      } finally { this.enviando = false }
    },
    async abrir (f) {
      if (this.aberto?.id === f.id) { this.aberto = null; return }
      try {
        const { data } = await api.get(`/app/admin/pagamentos/vbvt/${f.id}/`)
        this.aberto = data
        this.copiado = false
      } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível abrir o ficheiro.' }
    },
    async copiar () {
      try {
        await navigator.clipboard.writeText(this.aberto.relatorio)
        this.copiado = true
      } catch (e) { this.erro = 'Não foi possível copiar — seleciona o texto à mão.' }
    },
    async perguntar (l) {
      this.perguntando = l.tx_id
      try {
        const { data } = await api.post(`/app/admin/pagamentos/vinti4/${l.tx_id}/consultar/`)
        this.respostas = { ...this.respostas, [l.tx_id]: `${data.resposta?.msg || ''} → ${data.transacao.estado_nome}` }
        this.$emit('mudou')
      } catch (e) {
        this.respostas = { ...this.respostas, [l.tx_id]: e.response?.data?.detail || 'Sem resposta da SISP.' }
      } finally { this.perguntando = null }
    },
  },
}
</script>
