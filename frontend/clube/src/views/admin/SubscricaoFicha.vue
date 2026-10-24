<!-- SubscricaoFicha.vue — Admin → Subscrições, vista de uma loja (aba da loja) ou de um POS:
     modelo/plano/estado e ações, cobranças paginadas com procura, e a aba POS com o plano, as ações e as cobranças de cada POS.
     GET /app/admin/subscricoes/ficha/<loja|pos>/<id>/ (subscricaoView.py). Os modais das ações vivem em AdminSubscricoes:
     emite 'acao' (oferta | modelo | ofertaPos | planoPos | pagar | adiar | anular | recibo | faturacao, ...args),
     'abrir' (tipo, id, aba) e 'carregada' (ficha). versao: muda → recarrega tudo. -->
<template>
  <div class="space-y-4" data-teste="subscricao-ficha">
    <div v-if="!ficha && aCarregar" class="h-32 bg-zinc-900 rounded-2xl animate-pulse"></div>
    <p v-else-if="erro && !ficha" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <template v-else-if="ficha">
      <!-- cabeçalho -->
      <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 sm:p-5 space-y-3">
        <button v-if="ficha.tipo === 'pos' && ficha.loja" type="button" @click="$emit('abrir', 'loja', ficha.loja.id, 'pos')" data-teste="voltar-loja"
          class="text-xs text-zinc-400 hover:text-zinc-200">← {{ ficha.loja.nome }}</button>
        <div class="flex flex-wrap items-start gap-3">
          <div class="flex-1 min-w-[200px]">
            <p class="text-lg font-bold text-zinc-100" data-teste="ficha-nome">
              <span v-if="ficha.tipo === 'pos'" class="mr-1 text-xs font-bold text-sky-300">POS</span>{{ nome }}
              <span v-if="ficha.tipo === 'loja' && l.loja_estado !== 'ativa'" class="ml-1 text-[10px] font-bold uppercase text-zinc-500">{{ l.loja_estado }}</span>
              <span v-if="ficha.tipo === 'pos' && p.suspenso" class="ml-1 text-[10px] font-bold uppercase text-red-400">suspenso</span>
            </p>
            <!-- loja -->
            <template v-if="ficha.tipo === 'loja'">
              <p class="text-sm text-zinc-400 mt-0.5">
                <template v-if="l.modelo === 'comissao'">Comissão {{ Number(l.percentagem_comissao) }}% por venda</template>
                <template v-else-if="l.subscricao">
                  {{ l.subscricao.plano.nome }} · {{ euros(l.subscricao.preco) }}
                  <template v-if="l.subscricao.estado === 'teste' && l.subscricao.teste_ate"> · teste até {{ data(l.subscricao.teste_ate) }}</template>
                  <template v-if="l.subscricao.pago_ate && l.subscricao.pago_ate !== l.subscricao.teste_ate"> · pago até {{ data(l.subscricao.pago_ate) }}</template>
                </template>
              </p>
              <p v-if="l.subscricao_servicos" class="text-xs text-emerald-300/90 mt-0.5">
                Serviços: {{ l.subscricao_servicos.plano.nome }} · {{ euros(l.subscricao_servicos.preco) }} · {{ ESTADOS[l.subscricao_servicos.estado] }}
                <template v-if="l.subscricao_servicos.estado === 'teste' && l.subscricao_servicos.teste_ate"> até {{ data(l.subscricao_servicos.teste_ate) }}</template>
                <template v-if="l.subscricao_servicos.fim_agendado"> · termina a {{ data(l.subscricao_servicos.fim_agendado) }}</template>
              </p>
            </template>
            <!-- POS -->
            <template v-else>
              <p class="text-xs text-zinc-500 mt-0.5">{{ p.codigo_pos }} · {{ p.dono }} · {{ p.dono_email }}</p>
              <p class="text-sm text-zinc-400 mt-0.5">{{ planoPos(p) }}</p>
              <p v-if="p.suspenso && p.suspenso_motivo" class="text-[11px] text-red-300/80 mt-0.5">{{ p.suspenso_motivo }}</p>
            </template>
          </div>
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', estadoCor]">{{ estadoNome }}</span>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span v-if="pendentes.n" class="text-xs font-semibold text-amber-300 mr-1" data-teste="ficha-por-pagar">{{ pendentes.n }} por pagar · {{ euros(pendentes.v) }}</span>
          <template v-if="ficha.tipo === 'loja'">
            <button v-if="l.modelo === 'subscricao' && l.subscricao && !['aguarda', 'cancelada'].includes(l.subscricao.estado)" type="button"
              @click="$emit('acao', 'oferta', l)" data-teste="ficha-oferecer"
              class="px-3 py-1.5 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300">Oferecer meses</button>
            <button v-if="l.subscricao_servicos && !['aguarda', 'cancelada'].includes(l.subscricao_servicos.estado)" type="button"
              @click="$emit('acao', 'oferta', l, true)" class="px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-xs text-emerald-300">Oferecer meses (Serviços)</button>
            <button type="button" @click="$emit('acao', 'modelo', l)" data-teste="ficha-modelo"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Mudar modelo</button>
          </template>
          <template v-else-if="!p.cobertura && p.subscricao">
            <button type="button" @click="$emit('acao', 'ofertaPos', p)" class="px-3 py-1.5 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300">Oferecer meses</button>
            <button type="button" @click="$emit('acao', 'planoPos', p)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Plano</button>
          </template>
        </div>
      </div>

      <!-- abas -->
      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 max-w-full overflow-x-auto w-fit" role="tablist">
        <button v-for="t in abas" :key="t.key" type="button" role="tab" :aria-selected="aba === t.key ? 'true' : 'false'" @click="aba = t.key"
          :class="['px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap transition', aba === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t.label }}
        </button>
      </div>

      <!-- cobranças da loja (loja + Serviços) ou do POS -->
      <ListaCobrancas v-if="aba === 'cobrancas'" url="/app/admin/faturas/" :params="paramsCobrancas" :limite="15" :versao="versao"
        estado-inicial="" vazio="Ainda não há cobranças.">
        <template #default="{ f }">
          <LinhaCobrancaAdmin :f="f" :mostrar-alvo="false" @acao="(t, x) => $emit('acao', t, x)" />
        </template>
      </ListaCobrancas>

      <!-- POS da loja -->
      <template v-else-if="aba === 'pos'">
        <p v-if="!ficha.pos.length" class="text-center py-10 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Esta loja não tem POS ligados.</p>
        <div v-for="x in ficha.pos" :key="x.pos_id" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden" :data-teste="`ficha-pos-${x.pos_id}`">
          <div class="px-4 sm:px-6 py-4 flex flex-wrap items-center gap-3">
            <div class="flex-1 min-w-[200px]">
              <p class="text-sm font-semibold text-zinc-200">{{ x.nome }}
                <span v-if="x.suspenso" class="ml-1 text-[10px] font-bold uppercase text-red-400">suspenso</span>
              </p>
              <p class="text-xs text-zinc-500">{{ x.codigo_pos }} · {{ x.dono }}</p>
              <p class="text-xs text-zinc-400 mt-0.5">{{ planoPos(x) }}</p>
            </div>
            <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', x.cobertura ? 'bg-violet-500/15 text-violet-300' : corEstado(x.subscricao?.estado)]">
              {{ x.cobertura ? 'Incluído' : ESTADOS[x.subscricao?.estado] || '—' }}
            </span>
            <span v-if="x.faturas_pendentes" class="text-xs font-semibold text-amber-300">{{ x.faturas_pendentes }} por pagar · {{ euros(x.valor_pendente) }}</span>
            <template v-if="!x.cobertura && x.subscricao">
              <button type="button" @click="$emit('acao', 'ofertaPos', x)" data-teste="pos-oferecer"
                class="px-3 py-1.5 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300">Oferecer meses</button>
              <button type="button" @click="$emit('acao', 'planoPos', x)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Plano</button>
            </template>
            <button type="button" @click="$emit('abrir', 'pos', x.pos_id)" data-teste="abrir-pos"
              class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Vista do POS →</button>
          </div>
          <div class="border-t border-zinc-800 pt-3">
            <ListaCobrancas url="/app/admin/faturas/" :params="{ pos: x.pos_id }" :limite="5" :versao="versao" embutida
              :vazio="x.cobertura ? 'Incluído no plano da loja: não tem cobranças próprias.' : 'Ainda não há cobranças.'">
              <template #default="{ f }">
                <LinhaCobrancaAdmin :f="f" :mostrar-alvo="false" embutida @acao="(t, y) => $emit('acao', t, y)" />
              </template>
            </ListaCobrancas>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import ListaCobrancas from '@/components/subscricao/ListaCobrancas.vue'
import LinhaCobrancaAdmin from '@/components/subscricao/LinhaCobrancaAdmin.vue'

const ESTADOS = { aguarda: 'Aguarda aprovação', teste: 'Em teste', ativa: 'Em dia', em_atraso: 'Em atraso', suspensa: 'Suspensa', cancelada: 'Cancelada' }

export default {
  name: 'SubscricaoFicha',
  components: { ListaCobrancas, LinhaCobrancaAdmin },
  props: {
    tipo: { type: String, required: true },
    id: { type: Number, required: true },
    abaInicial: { type: String, default: '' },
    versao: { type: Number, default: 0 },
  },
  emits: ['acao', 'abrir', 'carregada'],
  data () {
    return { ESTADOS, ficha: null, aCarregar: false, erro: '', aba: this.abaInicial === 'pos' ? 'pos' : 'cobrancas' }
  },
  computed: {
    l () { return this.ficha?.loja || {} },
    p () { return this.ficha?.pos || {} },
    nome () { return this.ficha.tipo === 'loja' ? this.l.loja_nome : this.p.nome },
    abas () {
      const a = [{ key: 'cobrancas', label: 'Cobranças' }]
      if (this.ficha?.tipo === 'loja') a.push({ key: 'pos', label: `POS (${this.ficha.pos.length})` })
      return a
    },
    paramsCobrancas () { return this.tipo === 'loja' ? { loja: this.id } : { pos: this.id } },
    // por pagar: da loja e dos seus POS
    pendentes () {
      if (!this.ficha) return { n: 0, v: 0 }
      if (this.ficha.tipo === 'pos') return { n: this.p.faturas_pendentes, v: Number(this.p.valor_pendente) }
      return this.ficha.pos.reduce((t, x) => ({ n: t.n + x.faturas_pendentes, v: t.v + Number(x.valor_pendente) }),
                                   { n: this.l.faturas_pendentes, v: Number(this.l.valor_pendente) })
    },
    estadoNome () {
      if (this.ficha.tipo === 'loja') return this.l.modelo === 'comissao' ? 'Comissão' : ESTADOS[this.l.subscricao?.estado]
      return this.p.cobertura ? 'Incluído' : ESTADOS[this.p.subscricao?.estado] || '—'
    },
    estadoCor () {
      if (this.ficha.tipo === 'loja') return this.l.modelo === 'comissao' ? 'bg-zinc-700 text-zinc-300' : this.corEstado(this.l.subscricao?.estado)
      return this.p.cobertura ? 'bg-violet-500/15 text-violet-300' : this.corEstado(this.p.subscricao?.estado)
    },
  },
  watch: { versao () { this.carregar() } },
  created () { this.carregar() },
  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
    data (s) { return s ? new Date(s.length === 10 ? s + 'T12:00:00' : s).toLocaleDateString('pt-PT') : '' },
    corEstado (e) {
      return { teste: 'bg-sky-500/15 text-sky-300', ativa: 'bg-green-500/15 text-green-400', em_atraso: 'bg-red-500/15 text-red-400',
               suspensa: 'bg-red-500/15 text-red-400', aguarda: 'bg-zinc-700 text-zinc-300', cancelada: 'bg-zinc-700 text-zinc-400' }[e] || 'bg-zinc-700 text-zinc-300'
    },
    planoPos (x) {
      if (x.cobertura) return `Incluído no plano ${x.cobertura.plano} da loja ${x.cobertura.loja_nome}`
      const s = x.subscricao
      if (!s) return 'Sem subscrição'
      let t = s.plano ? `${s.plano.nome} · ${this.euros(s.preco)}` : 'Sem plano'
      if (s.plano_seguinte) t += ` → ${s.plano_seguinte.nome} na renovação`
      if (s.estado === 'teste' && s.teste_ate) t += ` · grátis até ${this.data(s.teste_ate)}`
      else if (s.pago_ate) t += ` · pago até ${this.data(s.pago_ate)}`
      return t
    },
    async carregar () {
      this.aCarregar = true
      this.erro = ''
      try {
        this.ficha = (await api.get(`/app/admin/subscricoes/ficha/${this.tipo}/${this.id}/`)).data
        this.$emit('carregada', this.ficha)
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível carregar.'
      } finally { this.aCarregar = false }
    },
  },
}
</script>
