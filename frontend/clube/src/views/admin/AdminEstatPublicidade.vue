<!-- AdminEstatPublicidade.vue — Admin → Estatísticas → Publicidade: impressões, cliques e CTR dos anúncios da home
     (backend utils/publicidade_stats.py). Só contagens, sem dados de quem viu. CSV para mandar ao anunciante. -->
<template>
  <div class="space-y-5" data-teste="estat-publicidade">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-xs text-zinc-500 max-w-xl">
        Uma impressão é contada quando o anúncio fica pelo menos metade à vista durante 1 segundo; um clique quando
        abrem o link. Cada visitante conta no máximo uma vez por anúncio a cada {{ d?.janela_min || 30 }} minutos.
        Não se guarda quem viu.
      </p>
      <div class="flex flex-wrap items-center gap-2">
        <select v-if="d?.anunciantes.length" v-model="anunciante" @change="carregar" data-teste="estat-pub-anunciante"
          class="px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-zinc-200 focus:outline-none focus:border-red-500">
          <option value="">Todos os anunciantes</option>
          <option v-for="a in d.anunciantes" :key="a" :value="a">{{ a }}</option>
        </select>
        <div class="flex rounded-xl border border-zinc-700 overflow-hidden" role="group" aria-label="Período">
          <button v-for="p in PERIODOS" :key="p" type="button" @click="mudar(p)" :data-teste="'estat-pub-dias-' + p"
            :aria-pressed="dias === p"
            :class="['px-3 py-1.5 text-xs font-semibold transition', dias === p ? 'bg-red-600 text-white' : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200']">
            {{ p }} dias
          </button>
        </div>
        <button type="button" @click="exportar" :disabled="aExportar || !d" data-teste="estat-pub-csv"
          class="px-3 py-1.5 rounded-xl border border-zinc-700 bg-zinc-900 text-xs font-semibold text-zinc-300 hover:border-zinc-500 disabled:opacity-40 flex items-center gap-1.5">
          <font-awesome-icon :icon="['fas', 'file-csv']" /> {{ aExportar ? 'A preparar…' : 'Exportar CSV' }}
        </button>
      </div>
    </div>

    <div v-if="loading && !d" class="space-y-3">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3"><div v-for="n in 4" :key="n" class="h-20 bg-zinc-900 rounded-2xl animate-pulse"></div></div>
      <div class="h-56 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>
    <p v-else-if="erro" class="text-sm text-red-400">{{ erro }}</p>

    <template v-else-if="d">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3" :class="loading && 'opacity-60'" data-teste="estat-pub-resumo">
        <div v-for="k in kpis" :key="k.label" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
          <p class="text-2xl font-extrabold" :class="k.cor">{{ k.valor }}</p>
          <p class="text-xs text-zinc-500 mt-0.5">{{ k.label }}</p>
          <p v-if="k.nota" class="text-[11px] text-zinc-600 mt-1">{{ k.nota }}</p>
        </div>
      </div>

      <div v-if="!d.anuncios.length" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center" data-teste="estat-pub-vazio">
        <font-awesome-icon :icon="['fas', 'rectangle-ad']" class="text-2xl text-zinc-600" />
        <p class="mt-3 text-sm text-zinc-400">Ainda não há anúncios publicados. Cria-os em Página inicial → secção Publicidade.</p>
      </div>

      <template v-else>
        <div class="grid lg:grid-cols-2 gap-5">
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
            <GraficoTempo titulo="Impressões por dia" :dados="d.por_dia" granularidade="dia" :dinheiro="false"
                          :series="[{ chave: 'impressoes', label: 'Impressões', cor: COR_1 }]"
                          chave-total="impressoes" label-total="Impressões" vazio="Sem impressões neste período" />
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5">
            <GraficoTempo titulo="Cliques por dia" :dados="d.por_dia" granularidade="dia" :dinheiro="false"
                          :series="[{ chave: 'cliques', label: 'Cliques', cor: COR_2 }]"
                          chave-total="cliques" label-total="Cliques" vazio="Sem cliques neste período" />
          </div>
        </div>

        <section class="bg-zinc-900 rounded-2xl border border-zinc-800 p-5" data-teste="estat-pub-anuncios">
          <h3 class="text-sm font-bold text-zinc-400 uppercase tracking-wider">Por anúncio</h3>
          <p class="text-xs text-zinc-600 mt-0.5 mb-3">CTR = cliques ÷ impressões. Os anúncios que já saíram da home continuam aqui com os números do período.</p>
          <div class="overflow-x-auto -mx-1">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-[11px] text-zinc-500 uppercase tracking-wider">
                  <th class="text-left font-semibold px-1 pb-2">Anúncio</th>
                  <th class="hidden sm:table-cell text-right font-semibold px-1 pb-2">Impressões</th>
                  <th class="hidden sm:table-cell text-right font-semibold px-1 pb-2">Cliques</th>
                  <th class="hidden sm:table-cell text-right font-semibold px-1 pb-2">CTR</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.anuncios" :key="a.chave" class="border-t border-zinc-800" :data-teste="'estat-pub-linha-' + a.chave">
                  <td class="px-1 py-2">
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="w-16 h-10 rounded-md bg-zinc-800 overflow-hidden flex-shrink-0 flex items-center justify-center">
                        <img v-if="a.miniatura" :src="a.miniatura" alt="" class="w-full h-full object-cover" loading="lazy" />
                        <font-awesome-icon v-else :icon="['fas', 'rectangle-ad']" class="text-zinc-600" />
                      </div>
                      <div class="min-w-0">
                        <p class="text-zinc-200 truncate max-w-[14rem] sm:max-w-[18rem]">{{ a.titulo || 'Anúncio sem título' }}</p>
                        <p class="text-[11px] text-zinc-500 truncate max-w-[14rem] sm:max-w-[18rem]">
                          <span :class="COR_ESTADO[a.estado]" :data-teste="'estat-pub-estado-' + a.chave">{{ d.estados[a.estado] }}</span>
                          <template v-if="a.anunciante"> · {{ a.anunciante }}</template>
                          <template v-if="a.link"> · {{ a.link }}</template>
                        </p>
                        <!-- telemóvel: os números por baixo (as colunas não cabem) -->
                        <p class="sm:hidden text-xs text-zinc-300 mt-0.5 tabular-nums" :data-teste="'estat-pub-movel-' + a.chave">
                          {{ n(a.impressoes) }} impressões · {{ n(a.cliques) }} cliques · CTR {{ pct(a.ctr) }}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td class="hidden sm:table-cell px-1 py-2 text-right text-zinc-300 tabular-nums">{{ n(a.impressoes) }}</td>
                  <td class="hidden sm:table-cell px-1 py-2 text-right text-zinc-300 tabular-nums">{{ n(a.cliques) }}</td>
                  <td class="hidden sm:table-cell px-1 py-2 text-right text-zinc-400 tabular-nums">{{ pct(a.ctr) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'
import GraficoTempo from '@/components/relatorios/GraficoTempo.vue'

const PERIODOS = [7, 30, 90]
const CHAVE_DIAS = 'admin_publicidade_dias'

export default {
  name: 'AdminEstatPublicidade',
  components: { GraficoTempo },
  data () {
    return {
      PERIODOS, dias: 30, anunciante: '', d: null, loading: false, erro: '', aExportar: false,
      COR_1: '#3987e5', COR_2: '#d95926',
      COR_ESTADO: { ativo: 'text-green-400', agendado: 'text-amber-400', escondido: 'text-amber-400',
                    terminado: 'text-zinc-500', removido: 'text-zinc-500' },
    }
  },
  computed: {
    kpis () {
      const r = this.d.resumo
      return [
        { label: 'Impressões', valor: this.n(r.impressoes), cor: 'text-zinc-100' },
        { label: 'Cliques', valor: this.n(r.cliques), cor: 'text-zinc-100' },
        { label: 'CTR', valor: this.pct(r.ctr), cor: 'text-emerald-400', nota: 'cliques ÷ impressões' },
        { label: 'Anúncios activos', valor: String(r.ativos), cor: 'text-zinc-100', nota: `${r.anuncios} no período` },
      ]
    },
  },
  mounted () {
    try { const v = Number(localStorage.getItem(CHAVE_DIAS)); if (PERIODOS.includes(v)) this.dias = v } catch (e) { /* sem localStorage */ }
    this.carregar()
  },
  methods: {
    n (v) { return (v || 0).toLocaleString('pt-PT') },
    pct (v) { return v == null ? '—' : `${v.toLocaleString('pt-PT')}%` },
    mudar (p) {
      this.dias = p
      try { localStorage.setItem(CHAVE_DIAS, String(p)) } catch (e) { /* nada */ }
      this.carregar()
    },
    async carregar () {
      this.loading = true
      this.erro = ''
      try {
        const { data } = await api.get('/app/admin/estatisticas/publicidade/', { params: { dias: this.dias, anunciante: this.anunciante || undefined } })
        this.d = data
      } catch (e) {
        this.erro = e.response?.status === 403 ? 'Sem permissão para ver as estatísticas.' : 'Não foi possível carregar as estatísticas da publicidade.'
      } finally { this.loading = false }
    },
    async exportar () {
      this.aExportar = true
      try {
        const r = await api.get('/app/admin/estatisticas/publicidade/csv/',
          { params: { dias: this.dias, anunciante: this.anunciante || undefined }, responseType: 'blob' })
        // o cabeçalho Content-Disposition não chega ao browser noutro domínio (CORS): o nome faz-se aqui
        const nome = `publicidade_${this.d.desde.replaceAll('-', '')}_${this.d.ate.replaceAll('-', '')}.csv`
        const url = URL.createObjectURL(r.data)
        const a = document.createElement('a')
        a.href = url
        a.download = nome
        a.click()
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      } catch (e) {
        toast.error('Não foi possível exportar.')
      } finally { this.aExportar = false }
    },
  },
}
</script>
