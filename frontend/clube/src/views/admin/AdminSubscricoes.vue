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

    <!-- ═══ RESUMO (receita do período) ═══ -->
    <template v-if="tab === 'resumo'">
      <div class="flex flex-wrap items-center gap-2">
        <button v-for="p in PERIODOS" :key="p.key" type="button" @click="escolherPeriodo(p.key)"
          :class="['px-3 py-1.5 rounded-lg text-xs font-semibold transition', periodo === p.key ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200']">
          {{ p.label }}
        </button>
        <input type="date" v-model="inicio" aria-label="Início" @change="periodo = ''; carregarResumo()"
          class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" />
        <span class="text-xs text-zinc-500">a</span>
        <input type="date" v-model="fim" aria-label="Fim" @change="periodo = ''; carregarResumo()"
          class="px-2 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-200 [color-scheme:dark]" />
      </div>
      <div v-if="carregando && !resumo" class="h-40 bg-zinc-900 rounded-2xl animate-pulse"></div>
      <template v-else-if="resumo">
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs text-zinc-500">Receita total</p>
            <p class="text-2xl font-black text-zinc-100 mt-1">{{ euros(resumo.total) }}</p>
            <p class="text-[11px] text-zinc-500 mt-1">subscrições + comissões</p>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs text-zinc-500">Subscrições</p>
            <p class="text-2xl font-black text-sky-300 mt-1">{{ euros(resumo.subscricoes.valor) }}</p>
            <p class="text-[11px] text-zinc-500 mt-1">{{ resumo.subscricoes.faturas }} fatura(s) paga(s)<template v-if="resumo.subscricoes.ofertas"> · {{ resumo.subscricoes.ofertas }} oferta(s)</template></p>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs text-zinc-500">Comissões</p>
            <p class="text-2xl font-black text-green-400 mt-1">{{ euros(resumo.comissoes.valor) }}</p>
            <p class="text-[11px] text-zinc-500 mt-1">{{ resumo.comissoes.encomendas }} venda(s) · {{ euros(resumo.comissoes.pendente) }} por liquidar</p>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs text-zinc-500">Em atraso (hoje)</p>
            <p class="text-2xl font-black mt-1" :class="Number(resumo.em_atraso.valor) ? 'text-red-400' : 'text-zinc-100'">{{ euros(resumo.em_atraso.valor) }}</p>
            <p class="text-[11px] text-zinc-500 mt-1">{{ resumo.em_atraso.faturas }} fatura(s) · {{ euros(resumo.a_receber.valor) }} a vencer no período</p>
          </div>
        </div>
        <div class="grid lg:grid-cols-3 gap-3">
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">Lojas</p>
            <div class="flex justify-between text-sm py-1"><span class="text-zinc-400">Em comissão</span><b class="text-zinc-100">{{ resumo.lojas.comissao }}</b></div>
            <div class="flex justify-between text-sm py-1"><span class="text-zinc-400">Em subscrição</span><b class="text-zinc-100">{{ resumo.lojas.subscricao }}</b></div>
            <div v-for="(n, e) in resumo.por_estado" :key="e" class="flex justify-between text-xs py-0.5 pl-3">
              <span class="text-zinc-500">{{ ESTADOS[e] || e }}</span><span class="text-zinc-300">{{ n }}</span>
            </div>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">Por plano</p>
            <p v-if="!resumo.subscricoes.por_plano.length" class="text-sm text-zinc-500">Sem pagamentos no período.</p>
            <div v-for="x in resumo.subscricoes.por_plano" :key="x.plano" class="flex justify-between text-sm py-1">
              <span class="text-zinc-400">{{ x.plano }} <span class="text-xs text-zinc-600">· {{ x.faturas }}</span></span><b class="text-zinc-100">{{ euros(x.valor) }}</b>
            </div>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">Por método</p>
            <p v-if="!resumo.subscricoes.por_metodo.length" class="text-sm text-zinc-500">Sem pagamentos no período.</p>
            <div v-for="x in resumo.subscricoes.por_metodo" :key="x.metodo" class="flex justify-between text-sm py-1">
              <span class="text-zinc-400">{{ x.nome }} <span class="text-xs text-zinc-600">· {{ x.faturas }}</span></span><b class="text-zinc-100">{{ euros(x.valor) }}</b>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- ═══ LOJAS ═══ -->
    <template v-else-if="tab === 'lojas'">
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
          <button v-if="l.modelo === 'subscricao' && l.subscricao && !['aguarda', 'cancelada'].includes(l.subscricao.estado)" type="button"
            @click="abrirOferta(l)" class="px-3 py-1.5 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300">Oferecer meses</button>
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
          <template v-if="f.estado === 'pendente'">
            <button type="button" @click="abrirPagar(f)"
              class="px-3 py-1.5 rounded-lg bg-green-600/20 hover:bg-green-600/30 text-green-300 text-xs font-semibold">Marcar paga</button>
            <button type="button" @click="abrirAdiar(f)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Adiar</button>
            <button type="button" @click="abrirAnular(f)" class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 text-xs">Anular</button>
          </template>
          <button v-else-if="f.estado === 'paga'" type="button" @click="recibo(f)" :aria-label="`Recibo da fatura ${f.id}`"
            class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs">Recibo</button>
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

        <!-- oferecer meses -->
        <template v-else-if="modal.tipo === 'oferta'">
          <p class="text-sm text-zinc-300">{{ modal.loja.loja_nome }} · {{ modal.loja.subscricao.plano.nome }}</p>
          <label class="block"><span class="text-xs text-zinc-500">Quantos meses</span>
            <input v-model.number="modal.form.meses" type="number" min="1" max="12" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
          <label class="block"><span class="text-xs text-zinc-500">Motivo (o dono vê-o na notificação)</span>
            <input v-model="modal.form.motivo" maxlength="300" placeholder="ex.: compensação por falha do site" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
          <p class="text-xs text-zinc-500">As faturas por pagar deste período ficam anuladas e é registada uma fatura de 0 € ("Oferta"). Se a loja estiver suspensa por falta de pagamento, volta logo.</p>
        </template>

        <!-- adiar -->
        <template v-else-if="modal.tipo === 'adiar'">
          <p class="text-sm text-zinc-300">{{ modal.fatura.loja_nome }} · {{ modal.fatura.descricao }} · vence a {{ data(modal.fatura.vencimento) }}</p>
          <label class="block"><span class="text-xs text-zinc-500">Mais quantos dias (a contar de hoje, se já venceu)</span>
            <input v-model.number="modal.form.dias" type="number" min="1" max="60" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
        </template>

        <!-- anular -->
        <template v-else-if="modal.tipo === 'anular'">
          <p class="text-sm text-zinc-300">{{ modal.fatura.loja_nome }} · {{ modal.fatura.descricao }} · <b>{{ euros(modal.fatura.valor) }}</b></p>
          <label class="block"><span class="text-xs text-zinc-500">Motivo (fica registado na fatura)</span>
            <input v-model="modal.form.motivo" maxlength="250" placeholder="ex.: valor errado" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
          <p class="text-xs text-zinc-500">A fatura não se apaga. Se o período ficar por cobrir, é emitida uma nova automaticamente.</p>
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
import { gerarReciboSubscricao } from '@/utils/reciboSubscricao'

const TABS = [{ key: 'resumo', label: 'Resumo' }, { key: 'lojas', label: 'Lojas' }, { key: 'faturas', label: 'Faturas' }, { key: 'planos', label: 'Planos' }]
const PERIODOS = [{ key: 'este_mes', label: 'Este mês' }, { key: 'mes_passado', label: 'Mês passado' },
                  { key: 'ult30', label: 'Últimos 30 dias' }, { key: 'este_ano', label: 'Este ano' }]
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const ESTADOS = { aguarda: 'Aguarda aprovação', teste: 'Em teste', ativa: 'Em dia', em_atraso: 'Em atraso', suspensa: 'Suspensa', cancelada: 'Cancelada' }

export default {
  name: 'AdminSubscricoes',
  data () {
    return { TABS, PERIODOS, ESTADOS, tab: 'resumo', carregando: false, erro: '', periodo: 'este_mes', inicio: '', fim: '', resumo: null,
             lojas: { count: 0, results: [] }, q: '', modelo: '', estado: '',
             faturas: [], estadoFatura: 'pendente', lojaFiltro: null,
             planos: [], modal: null, t: null }
  },

  watch: {
    tab (t) {
      if (t === 'resumo') this.carregarResumo()
      else if (t === 'lojas') this.carregarLojas()
      else if (t === 'faturas') this.carregarFaturas()
      else this.carregarPlanos()
    },
  },

  created () { this.escolherPeriodo('este_mes'); this.carregarPlanos() },

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
    recibo (f) { gerarReciboSubscricao(f) },
    escolherPeriodo (k) {
      const h = new Date()
      let a = new Date(h.getFullYear(), h.getMonth(), 1), b = h
      if (k === 'mes_passado') { a = new Date(h.getFullYear(), h.getMonth() - 1, 1); b = new Date(h.getFullYear(), h.getMonth(), 0) }
      else if (k === 'ult30') a = new Date(h.getTime() - 29 * 864e5)
      else if (k === 'este_ano') a = new Date(h.getFullYear(), 0, 1)
      this.periodo = k
      this.inicio = iso(a)
      this.fim = iso(b)
      this.carregarResumo()
    },
    carregarResumo () {
      if (!this.inicio || !this.fim) return
      return this.pedir(async () => {
        this.resumo = (await api.get('/app/admin/subscricoes/resumo/', { params: { inicio: this.inicio, fim: this.fim } })).data
      })
    },
    abrirOferta (l) {
      this.modal = { tipo: 'oferta', loja: l, titulo: `Oferecer meses — ${l.loja_nome}`, botao: 'Oferecer', erro: '', aGuardar: false,
                     form: { meses: 1, motivo: '' } }
    },
    abrirAdiar (f) {
      this.modal = { tipo: 'adiar', fatura: f, titulo: `Adiar a fatura #${f.id}`, botao: 'Adiar', erro: '', aGuardar: false, form: { dias: 7 } }
    },
    abrirAnular (f) {
      this.modal = { tipo: 'anular', fatura: f, titulo: `Anular a fatura #${f.id}`, botao: 'Anular fatura', erro: '', aGuardar: false, form: { motivo: '' } }
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
        } else if (m.tipo === 'adiar' || m.tipo === 'anular') {
          await api.post(`/app/admin/faturas/${m.fatura.id}/${m.tipo}/`, m.form)
          await this.carregarFaturas()
        } else if (m.tipo === 'oferta') {
          await api.post(`/app/admin/lojas/${m.loja.loja_id}/subscricao/oferecer/`, m.form)
          await this.carregarLojas()
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
