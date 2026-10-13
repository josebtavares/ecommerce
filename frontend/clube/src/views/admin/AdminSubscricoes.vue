<template>
  <!-- Admin → Subscrições: lojas (comissão/subscrição), faturas e planos (utils/subscricoes.py) -->
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Subscrições</h2>
        <p class="text-xs text-zinc-500 mt-0.5">Como cada loja paga à plataforma — comissão por venda ou mensalidade</p>
      </div>
      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1" role="tablist">
        <button v-for="t in TABS" :key="t.key" type="button" role="tab" :aria-selected="tab === t.key ? 'true' : 'false'" @click="tab = t.key"
          :class="['px-4 py-1.5 rounded-lg text-sm font-semibold transition', tab === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t.label }}
        </button>
      </div>
    </div>

    <p v-if="erro" class="text-sm text-red-400" role="alert">{{ erro }}</p>

    <!-- ═══ LOJAS ═══ -->
    <template v-if="tab === 'lojas'">
      <div class="flex flex-wrap gap-2">
        <input v-model="q" @input="debounce(carregarLojas)" placeholder="Procurar loja…" aria-label="Procurar loja"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 w-56" />
        <select v-model="modelo" @change="carregarLojas" aria-label="Modelo"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todos os modelos</option>
          <option value="subscricao">Subscrição</option>
          <option value="comissao">Comissão</option>
        </select>
        <select v-model="estado" @change="carregarLojas" aria-label="Estado"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todos os estados</option>
          <option v-for="(n, k) in ESTADOS" :key="k" :value="k">{{ n }}</option>
        </select>
        <span class="ml-auto text-xs text-zinc-500 self-center">{{ lojas.count }} lojas</span>
      </div>

      <div v-if="carregando" class="space-y-2"><div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div></div>
      <div v-else-if="!lojas.results.length" class="text-center py-12 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Nenhuma loja.</div>
      <div v-else class="space-y-2">
        <div v-for="l in lojas.results" :key="l.loja_id" class="bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3 flex flex-wrap items-center gap-3">
          <div class="flex-1 min-w-[180px]">
            <p class="text-sm font-semibold text-zinc-200">{{ l.loja_nome }}
              <span v-if="l.loja_estado !== 'ativa'" class="ml-1 text-[10px] font-bold uppercase text-zinc-500">{{ l.loja_estado }}</span>
            </p>
            <p class="text-xs text-zinc-500">
              <template v-if="l.modelo === 'comissao'">Comissão {{ Number(l.percentagem_comissao) }}%</template>
              <template v-else-if="l.subscricao">
                {{ l.subscricao.plano.nome }} · {{ euros(l.subscricao.preco) }}
                <template v-if="l.subscricao.estado === 'teste' && l.subscricao.teste_ate"> · teste até {{ data(l.subscricao.teste_ate) }}</template>
                <template v-if="l.subscricao.pago_ate && l.subscricao.pago_ate !== l.subscricao.teste_ate"> · pago até {{ data(l.subscricao.pago_ate) }}</template>
              </template>
            </p>
          </div>
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', l.modelo === 'comissao' ? 'bg-zinc-700 text-zinc-300' : corEstado(l.subscricao?.estado)]">
            {{ l.modelo === 'comissao' ? 'Comissão' : ESTADOS[l.subscricao?.estado] }}
          </span>
          <span v-if="l.faturas_pendentes" class="text-xs font-semibold text-amber-300">{{ l.faturas_pendentes }} por pagar · {{ euros(l.valor_pendente) }}</span>
          <button type="button" @click="verFaturas(l)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Faturas</button>
          <button type="button" @click="abrirModelo(l)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Mudar modelo</button>
        </div>
      </div>
    </template>

    <!-- ═══ FATURAS ═══ -->
    <template v-else-if="tab === 'faturas'">
      <div class="flex flex-wrap items-center gap-2">
        <select v-model="estadoFatura" @change="carregarFaturas" aria-label="Estado da fatura"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todas</option>
          <option value="pendente">Por pagar</option>
          <option value="paga">Pagas</option>
          <option value="anulada">Anuladas</option>
        </select>
        <span v-if="lojaFiltro" class="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-800 text-xs text-zinc-300">
          {{ lojaFiltro.loja_nome }}
          <button type="button" @click="lojaFiltro = null; carregarFaturas()" aria-label="Tirar filtro da loja" class="text-zinc-500 hover:text-zinc-200">×</button>
        </span>
      </div>
      <div v-if="carregando" class="space-y-2"><div v-for="n in 4" :key="n" class="h-14 bg-zinc-900 rounded-2xl animate-pulse"></div></div>
      <div v-else-if="!faturas.length" class="text-center py-12 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Nenhuma fatura.</div>
      <div v-else class="space-y-2">
        <div v-for="f in faturas" :key="f.id" class="bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3 flex flex-wrap items-center gap-3">
          <div class="flex-1 min-w-[200px]">
            <p class="text-sm font-semibold text-zinc-200">#{{ f.id }} · {{ f.loja_nome }}</p>
            <p class="text-xs text-zinc-500">{{ f.descricao }} ·
              <template v-if="f.estado === 'paga'">paga a {{ data(f.paga_em) }} ({{ f.metodo_nome }})</template>
              <template v-else-if="f.estado === 'pendente'">vence a {{ data(f.vencimento) }}</template>
              <template v-else>{{ f.notas || 'anulada' }}</template>
            </p>
          </div>
          <span class="text-sm font-bold text-zinc-100">{{ euros(f.valor) }}</span>
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', f.atrasada ? 'bg-red-500/15 text-red-400' : corFatura(f.estado)]">
            {{ f.atrasada ? 'Em atraso' : f.estado_nome }}
          </span>
          <button v-if="f.estado === 'pendente'" type="button" @click="abrirPagar(f)"
            class="px-3 py-1.5 rounded-lg bg-green-600/20 hover:bg-green-600/30 text-green-300 text-xs font-semibold">Marcar paga</button>
        </div>
      </div>
    </template>

    <!-- ═══ PLANOS ═══ -->
    <template v-else>
      <div class="flex justify-end">
        <button type="button" @click="abrirPlano(null)" class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold">+ Novo plano</button>
      </div>
      <div v-if="!planos.length && !carregando" class="text-center py-12 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">
        Ainda não há planos — sem planos activos as lojas só podem escolher comissão.
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="p in planos" :key="p.id" :class="['bg-zinc-900 rounded-2xl border p-4', p.ativo ? 'border-zinc-800' : 'border-zinc-800 opacity-60']">
          <div class="flex items-start justify-between gap-2">
            <div>
              <p class="text-sm font-bold text-zinc-100">{{ p.nome }}</p>
              <p class="text-xs text-zinc-500">{{ p.periodicidade_nome }}<template v-if="!p.ativo"> · inactivo</template></p>
            </div>
            <button type="button" @click="abrirPlano(p)" class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Editar</button>
          </div>
          <p class="text-2xl font-black text-zinc-100 mt-2">{{ euros(p.preco) }}</p>
          <p v-if="p.meses > 1" class="text-xs text-zinc-500">{{ euros(p.preco_mes) }}/mês</p>
          <p v-if="p.descricao" class="text-xs text-zinc-400 mt-2">{{ p.descricao }}</p>
          <p class="text-xs text-zinc-500 mt-2">{{ p.lojas }} loja(s) neste plano</p>
        </div>
      </div>
    </template>

    <!-- ═══ Modais ═══ -->
    <div v-if="modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" @click.self="modal = null">
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 w-full max-w-md space-y-4" role="dialog" :aria-label="modal.titulo">
        <h3 class="text-base font-bold text-zinc-100">{{ modal.titulo }}</h3>

        <!-- plano -->
        <template v-if="modal.tipo === 'plano'">
          <label class="block"><span class="text-xs text-zinc-500">Nome</span>
            <input v-model="modal.form.nome" maxlength="80" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
          <div class="grid grid-cols-2 gap-3">
            <label class="block"><span class="text-xs text-zinc-500">Periodicidade</span>
              <select v-model="modal.form.periodicidade" :disabled="modal.plano && modal.plano.lojas > 0"
                class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 disabled:opacity-50">
                <option value="mensal">Mensal</option><option value="trimestral">Trimestral</option><option value="anual">Anual</option>
              </select></label>
            <label class="block"><span class="text-xs text-zinc-500">Preço (€)</span>
              <input v-model="modal.form.preco" type="number" min="0" step="0.01" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
          </div>
          <label class="block"><span class="text-xs text-zinc-500">Descrição (opcional)</span>
            <input v-model="modal.form.descricao" maxlength="300" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
          <label class="flex items-center gap-2 text-sm text-zinc-300"><input type="checkbox" v-model="modal.form.ativo" class="accent-red-600" /> Activo (as lojas podem escolher)</label>
          <p v-if="modal.plano && modal.plano.lojas" class="text-xs text-zinc-500">Mudar o preço só vale para as lojas que escolherem o plano depois — as {{ modal.plano.lojas }} actuais mantêm o preço contratado.</p>
        </template>

        <!-- marcar paga -->
        <template v-else-if="modal.tipo === 'pagar'">
          <p class="text-sm text-zinc-300">{{ modal.fatura.loja_nome }} · {{ modal.fatura.descricao }} · <b>{{ euros(modal.fatura.valor) }}</b></p>
          <label class="block"><span class="text-xs text-zinc-500">Como foi pago</span>
            <select v-model="modal.form.metodo" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100">
              <option value="dinheiro">Dinheiro</option><option value="transferencia">Transferência</option>
              <option value="oferta">Oferta da plataforma</option><option value="outro">Outro</option>
            </select></label>
          <label class="block"><span class="text-xs text-zinc-500">Notas (opcional — ex.: referência da transferência)</span>
            <input v-model="modal.form.notas" maxlength="300" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
        </template>

        <!-- mudar modelo -->
        <template v-else-if="modal.tipo === 'modelo'">
          <p class="text-sm text-zinc-400">Agora: <b class="text-zinc-200">{{ modal.loja.modelo === 'comissao' ? 'Comissão ' + Number(modal.loja.percentagem_comissao) + '%' : 'Subscrição' }}</b></p>
          <div v-if="modal.loja.modelo === 'comissao'" class="space-y-2">
            <p class="text-sm text-zinc-300">Passar para subscrição — escolhe o plano:</p>
            <select v-model="modal.form.plano_id" aria-label="Plano" class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100">
              <option :value="null" disabled>Escolhe um plano</option>
              <option v-for="p in planos.filter(x => x.ativo)" :key="p.id" :value="p.id">{{ p.nome }} — {{ euros(p.preco) }}</option>
            </select>
            <p class="text-xs text-zinc-500">Sem período de teste: a primeira fatura vence hoje. As encomendas já feitas continuam a pagar comissão.</p>
          </div>
          <p v-else class="text-sm text-zinc-300">Passar para <b>comissão ({{ Number(modal.loja.percentagem_comissao) }}%)</b>. A subscrição fica cancelada e as faturas por pagar anuladas (não se apagam).</p>
        </template>

        <p v-if="modal.erro" class="text-sm text-red-400" role="alert">{{ modal.erro }}</p>
        <div class="flex gap-2 pt-1">
          <button type="button" @click="modal = null" class="flex-1 py-2 rounded-xl border border-zinc-700 text-zinc-400 text-sm font-semibold hover:text-zinc-200">Cancelar</button>
          <button type="button" @click="confirmarModal" :disabled="modal.aGuardar"
            class="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-bold">
            {{ modal.aGuardar ? 'A guardar…' : modal.botao }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

const TABS = [{ key: 'lojas', label: 'Lojas' }, { key: 'faturas', label: 'Faturas' }, { key: 'planos', label: 'Planos' }]
const ESTADOS = { aguarda: 'Aguarda aprovação', teste: 'Em teste', ativa: 'Em dia', em_atraso: 'Em atraso', suspensa: 'Suspensa', cancelada: 'Cancelada' }

export default {
  name: 'AdminSubscricoes',
  data () {
    return { TABS, ESTADOS, tab: 'lojas', carregando: false, erro: '',
             lojas: { count: 0, results: [] }, q: '', modelo: '', estado: '',
             faturas: [], estadoFatura: 'pendente', lojaFiltro: null,
             planos: [], modal: null, t: null }
  },

  watch: {
    tab (t) { if (t === 'lojas') this.carregarLojas(); else if (t === 'faturas') this.carregarFaturas(); else this.carregarPlanos() },
  },

  created () { this.carregarLojas(); this.carregarPlanos() },

  methods: {
    euros (v) { return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(v) || 0) },
    data (s) { return s ? new Date(s.length === 10 ? s + 'T12:00:00' : s).toLocaleDateString('pt-PT') : '' },
    corEstado (e) {
      return { teste: 'bg-sky-500/15 text-sky-300', ativa: 'bg-green-500/15 text-green-400', em_atraso: 'bg-red-500/15 text-red-400',
               suspensa: 'bg-red-500/15 text-red-400', aguarda: 'bg-zinc-700 text-zinc-300', cancelada: 'bg-zinc-700 text-zinc-400' }[e] || 'bg-zinc-700 text-zinc-300'
    },
    corFatura (e) { return { paga: 'bg-green-500/15 text-green-400', pendente: 'bg-amber-500/15 text-amber-300', anulada: 'bg-zinc-700 text-zinc-400' }[e] },
    debounce (fn) { clearTimeout(this.t); this.t = setTimeout(fn, 300) },

    async pedir (fn) {
      this.carregando = true; this.erro = ''
      try { await fn() } catch (e) { this.erro = e.response?.data?.detail || 'Não foi possível carregar.' } finally { this.carregando = false }
    },
    carregarLojas () {
      return this.pedir(async () => {
        const params = { limit: 100 }
        if (this.q.trim()) params.q = this.q.trim()
        if (this.modelo) params.modelo = this.modelo
        if (this.estado) params.estado = this.estado
        this.lojas = (await api.get('/app/admin/subscricoes/', { params })).data
      })
    },
    carregarFaturas () {
      return this.pedir(async () => {
        const params = { limit: 100 }
        if (this.estadoFatura) params.estado = this.estadoFatura
        if (this.lojaFiltro) params.loja = this.lojaFiltro.loja_id
        this.faturas = (await api.get('/app/admin/faturas/', { params })).data.results
      })
    },
    carregarPlanos () {
      return this.pedir(async () => { this.planos = (await api.get('/app/admin/planos/')).data })
    },
    verFaturas (l) { this.lojaFiltro = l; this.estadoFatura = ''; this.tab === 'faturas' ? this.carregarFaturas() : (this.tab = 'faturas') },

    abrirPlano (p) {
      this.modal = { tipo: 'plano', plano: p, titulo: p ? `Editar "${p.nome}"` : 'Novo plano', botao: p ? 'Guardar' : 'Criar plano', erro: '', aGuardar: false,
                     form: p ? { nome: p.nome, periodicidade: p.periodicidade, preco: p.preco, descricao: p.descricao, ativo: p.ativo }
                             : { nome: '', periodicidade: 'mensal', preco: '', descricao: '', ativo: true } }
    },
    abrirPagar (f) {
      this.modal = { tipo: 'pagar', fatura: f, titulo: `Marcar a fatura #${f.id} como paga`, botao: 'Marcar paga', erro: '', aGuardar: false,
                     form: { metodo: 'transferencia', notas: '' } }
    },
    abrirModelo (l) {
      this.modal = { tipo: 'modelo', loja: l, titulo: `Modelo de cobrança — ${l.loja_nome}`, erro: '', aGuardar: false,
                     botao: l.modelo === 'comissao' ? 'Passar para subscrição' : 'Passar para comissão', form: { plano_id: null } }
    },
    async confirmarModal () {
      const m = this.modal
      m.erro = ''; m.aGuardar = true
      try {
        if (m.tipo === 'plano') {
          const corpo = { ...m.form }
          if (m.plano && m.plano.lojas > 0) delete corpo.periodicidade
          if (m.plano) await api.patch(`/app/admin/planos/${m.plano.id}/`, corpo)
          else await api.post('/app/admin/planos/', corpo)
          await this.carregarPlanos()
        } else if (m.tipo === 'pagar') {
          await api.post(`/app/admin/faturas/${m.fatura.id}/pagar/`, m.form)
          await this.carregarFaturas()
        } else {
          const corpo = m.loja.modelo === 'comissao' ? { modelo: 'subscricao', plano_id: m.form.plano_id } : { modelo: 'comissao' }
          await api.patch(`/app/admin/lojas/${m.loja.loja_id}/cobranca/`, corpo)
          await this.carregarLojas()
        }
        this.modal = null
      } catch (e) {
        m.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally {
        if (this.modal) m.aGuardar = false
      }
    },
  },
}
</script>
