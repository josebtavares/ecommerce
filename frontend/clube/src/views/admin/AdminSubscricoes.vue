<template>
  <!-- Admin → Subscrições (como Admin → Comissões): uma aba por loja (e POS sem loja) com a sua vista — plano, ações,
       cobranças paginadas, POS (SubscricaoFicha.vue); "Todas" = Resumo, Lojas, POS, Cobranças, Planos (utils/subscricoes.py) -->
  <div class="space-y-5">
    <div>
      <h2 class="text-lg font-bold text-zinc-100">Subscrições</h2>
      <p class="text-xs text-zinc-500 mt-0.5">Como cada loja e cada POS pagam à plataforma — comissão por venda ou mensalidade</p>
    </div>
    <AbasVendedores ref="abas" url="/app/admin/subscricoes/abas/" :ativo="abaAtiva" titulo="Cobranças por pagar"
      titulo-alerta="Cobranças por pagar — há em atraso" @selecionar="selecionar" />

    <SubscricaoFicha v-if="ficha" :key="ficha.tipo + ficha.id" :tipo="ficha.tipo" :id="ficha.id" :aba-inicial="ficha.aba" :versao="versao"
      @acao="acaoFicha" @abrir="abrirFicha" @carregada="f => lojaDoPos = f.tipo === 'pos' && f.loja ? f.loja.id : null" />

    <template v-else>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm font-semibold text-zinc-300">Todas as lojas e POS</p>
      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1 max-w-full overflow-x-auto" role="tablist">
        <button v-for="t in TABS" :key="t.key" type="button" role="tab" :aria-selected="tab === t.key ? 'true' : 'false'" @click="tab = t.key"
          :class="['px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap transition', tab === t.key ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300']">
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
            <p class="text-[11px] text-zinc-500 mt-1">{{ resumo.subscricoes.faturas }} cobrança(s) paga(s)<template v-if="resumo.subscricoes.ofertas"> · {{ resumo.subscricoes.ofertas }} oferta(s)</template></p>
            <p v-if="resumo.por_alvo" class="text-[11px] text-zinc-400 mt-1">Lojas {{ euros(resumo.por_alvo.lojas.valor) }}<template v-if="resumo.por_alvo.servicos"> · Serviços {{ euros(resumo.por_alvo.servicos.valor) }}</template> · POS {{ euros(resumo.por_alvo.pos.valor) }}</p>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs text-zinc-500">Comissões</p>
            <p class="text-2xl font-black text-green-400 mt-1">{{ euros(resumo.comissoes.valor) }}</p>
            <p class="text-[11px] text-zinc-500 mt-1">{{ resumo.comissoes.encomendas }} venda(s) · {{ euros(resumo.comissoes.pendente) }} por liquidar</p>
          </div>
          <div class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs text-zinc-500">Em atraso (hoje)</p>
            <p class="text-2xl font-black mt-1" :class="Number(resumo.em_atraso.valor) ? 'text-red-400' : 'text-zinc-100'">{{ euros(resumo.em_atraso.valor) }}</p>
            <p class="text-[11px] text-zinc-500 mt-1">{{ resumo.em_atraso.faturas }} cobrança(s) · {{ euros(resumo.a_receber.valor) }} a vencer no período</p>
          </div>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div v-if="resumo.pos" class="bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
            <p class="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">POS</p>
            <div class="flex justify-between text-sm py-1"><span class="text-zinc-400">Total</span><b class="text-zinc-100">{{ resumo.pos.total }}</b></div>
            <div class="flex justify-between text-sm py-1"><span class="text-zinc-400">Incluídos no plano da loja</span><b class="text-violet-300">{{ resumo.pos.incluidos }}</b></div>
            <div class="flex justify-between text-sm py-1"><span class="text-zinc-400">Sem plano</span><b class="text-zinc-100">{{ resumo.pos.sem_plano }}</b></div>
            <div class="flex justify-between text-sm py-1"><span class="text-zinc-400">Suspensos</span><b :class="resumo.pos.suspensos ? 'text-red-400' : 'text-zinc-100'">{{ resumo.pos.suspensos }}</b></div>
            <div v-for="(n, e) in resumo.pos.por_estado" :key="e" class="flex justify-between text-xs py-0.5 pl-3">
              <span class="text-zinc-500">{{ ESTADOS[e] || e }}</span><span class="text-zinc-300">{{ n }}</span>
            </div>
          </div>
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
        <input v-model="q" @input="debounce(() => carregarLojas(0))" placeholder="Procurar loja…" aria-label="Procurar loja"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 w-56" />
        <select v-model="modelo" @change="carregarLojas(0)" aria-label="Modelo"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todos os modelos</option>
          <option value="subscricao">Subscrição</option>
          <option value="comissao">Comissão</option>
        </select>
        <select v-model="estado" @change="carregarLojas(0)" aria-label="Estado"
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
            <p v-if="l.subscricao_servicos" class="text-xs text-emerald-300/90">
              Serviços: {{ l.subscricao_servicos.plano.nome }} · {{ euros(l.subscricao_servicos.preco) }} · {{ ESTADOS[l.subscricao_servicos.estado] }}
              <template v-if="l.subscricao_servicos.estado === 'teste' && l.subscricao_servicos.teste_ate"> até {{ data(l.subscricao_servicos.teste_ate) }}</template>
              <template v-if="l.subscricao_servicos.fim_agendado"> · termina a {{ data(l.subscricao_servicos.fim_agendado) }}</template>
            </p>
          </div>
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', l.modelo === 'comissao' ? 'bg-zinc-700 text-zinc-300' : corEstado(l.subscricao?.estado)]">
            {{ l.modelo === 'comissao' ? 'Comissão' : ESTADOS[l.subscricao?.estado] }}
          </span>
          <span v-if="l.faturas_pendentes" class="text-xs font-semibold text-amber-300">{{ l.faturas_pendentes }} por pagar · {{ euros(l.valor_pendente) }}</span>
          <button v-if="l.modelo === 'subscricao' && l.subscricao && !['aguarda', 'cancelada'].includes(l.subscricao.estado)" type="button"
            @click="abrirOferta(l)" class="px-3 py-1.5 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300">Oferecer meses</button>
          <button v-if="l.subscricao_servicos && !['aguarda', 'cancelada'].includes(l.subscricao_servicos.estado)" type="button"
            @click="abrirOferta(l, true)" class="px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-xs text-emerald-300">Oferecer meses (Serviços)</button>
          <button type="button" @click="abrirModelo(l)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Mudar modelo</button>
          <button type="button" @click="abrirFicha('loja', l.loja_id)" :data-teste="`abrir-loja-${l.loja_id}`"
            class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Vista da loja →</button>
        </div>
        <PaginacaoLista :count="lojas.count" :limit="LIMITE" :offset="lOffset" @ir="carregarLojas" />
      </div>
    </template>

    <!-- ═══ POS ═══ -->
    <template v-else-if="tab === 'pos'">
      <div class="flex flex-wrap gap-2">
        <input v-model="qPos" @input="debounce(() => carregarPos(0))" placeholder="Procurar POS, código ou dono…" aria-label="Procurar POS"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500 w-64" />
        <select v-model="situacaoPos" @change="carregarPos(0)" aria-label="Situação"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todos</option>
          <option value="incluido">Incluídos no plano da loja</option>
          <option value="sem_plano">Sem plano</option>
          <option value="suspenso">Suspensos</option>
        </select>
        <select v-model="estadoPos" @change="carregarPos(0)" aria-label="Estado da subscrição"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Todos os estados</option>
          <option v-for="k in ['teste', 'ativa', 'em_atraso', 'suspensa']" :key="k" :value="k">{{ ESTADOS[k] }}</option>
        </select>
        <span class="ml-auto text-xs text-zinc-500 self-center">{{ posLista.count }} POS</span>
      </div>

      <div v-if="carregando" class="space-y-2"><div v-for="n in 4" :key="n" class="h-16 bg-zinc-900 rounded-2xl animate-pulse"></div></div>
      <div v-else-if="!posLista.results.length" class="text-center py-12 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">Nenhum POS.</div>
      <div v-else class="space-y-2">
        <div v-for="p in posLista.results" :key="p.pos_id" class="bg-zinc-900 rounded-2xl border border-zinc-800 px-4 py-3 flex flex-wrap items-center gap-3">
          <div class="flex-1 min-w-[200px]">
            <p class="text-sm font-semibold text-zinc-200">{{ p.pos_nome }}
              <span v-if="p.suspenso" class="ml-1 text-[10px] font-bold uppercase text-red-400">suspenso</span>
            </p>
            <p class="text-xs text-zinc-500">{{ p.dono }} · {{ p.dono_email }}<template v-if="p.loja_vinculada"> · ligado a {{ p.loja_vinculada }}</template></p>
            <p class="text-xs text-zinc-400 mt-0.5">
              <template v-if="p.cobertura">Incluído no plano {{ p.cobertura.plano }} da loja {{ p.cobertura.loja_nome }}</template>
              <template v-else-if="p.subscricao">
                {{ p.subscricao.plano ? p.subscricao.plano.nome + ' · ' + euros(p.subscricao.preco) : 'Sem plano' }}
                <template v-if="p.subscricao.plano_seguinte"> → {{ p.subscricao.plano_seguinte.nome }} na renovação</template>
                <template v-if="p.subscricao.estado === 'teste' && p.subscricao.teste_ate"> · grátis até {{ data(p.subscricao.teste_ate) }}</template>
                <template v-else-if="p.subscricao.pago_ate"> · pago até {{ data(p.subscricao.pago_ate) }}</template>
              </template>
            </p>
            <p v-if="p.suspenso && p.suspenso_motivo" class="text-[11px] text-red-300/80 mt-0.5">{{ p.suspenso_motivo }}</p>
          </div>
          <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase', p.cobertura ? 'bg-violet-500/15 text-violet-300' : corEstado(p.subscricao?.estado)]">
            {{ p.cobertura ? 'Incluído' : ESTADOS[p.subscricao?.estado] || '—' }}
          </span>
          <span v-if="p.faturas_pendentes" class="text-xs font-semibold text-amber-300">{{ p.faturas_pendentes }} por pagar · {{ euros(p.valor_pendente) }}</span>
          <template v-if="!p.cobertura && p.subscricao">
            <button type="button" @click="abrirOfertaPos(p)" class="px-3 py-1.5 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300">Oferecer meses</button>
            <button type="button" @click="abrirPlanoPos(p)" class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Plano</button>
          </template>
          <button type="button" @click="abrirFicha('pos', p.pos_id)" :data-teste="`abrir-pos-${p.pos_id}`"
            class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Vista do POS →</button>
        </div>
        <PaginacaoLista :count="posLista.count" :limit="LIMITE" :offset="pOffset" @ir="carregarPos" />
      </div>
    </template>

    <!-- ═══ COBRANÇAS (mensalidades: FaturaSubscricao), paginadas no servidor — a fatura legal do Bende regista-se em Faturação ═══ -->
    <template v-else-if="tab === 'faturas'">
      <div class="flex flex-wrap items-center gap-2">
        <select v-model="tipoFatura" aria-label="Lojas ou POS" data-teste="cobrancas-tipo"
          class="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300 focus:outline-none">
          <option value="">Lojas e POS</option>
          <option value="loja">Só lojas</option>
          <option value="servicos">Só Serviços</option>
          <option value="pos">Só POS</option>
        </select>
      </div>
      <ListaCobrancas url="/app/admin/faturas/" :params="tipoFatura ? { tipo: tipoFatura } : {}" :limite="LIMITE" :versao="versao"
        estado-inicial="pendente" vazio="Nenhuma cobrança.">
        <template #default="{ f }">
          <LinhaCobrancaAdmin :f="f" @acao="acaoFicha" />
        </template>
      </ListaCobrancas>
    </template>

    <!-- ═══ PLANOS ═══ -->
    <template v-else>
      <div class="flex justify-end">
        <button type="button" @click="abrirPlano(null)" class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-bold">+ Novo plano</button>
      </div>
      <div v-if="!planos.length && !carregando" class="text-center py-12 text-sm text-zinc-500 bg-zinc-900 rounded-2xl border border-zinc-800">
        Ainda não há planos — sem planos activos as lojas só podem escolher comissão e os POS começam sem plano.
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="p in planos" :key="p.id" :class="['bg-zinc-900 rounded-2xl border p-4', p.ativo ? 'border-zinc-800' : 'border-zinc-800 opacity-60']">
          <div class="flex items-start justify-between gap-2">
            <div>
              <p class="text-sm font-bold text-zinc-100">{{ p.nome }}</p>
              <p class="text-xs text-zinc-500"><span :class="['font-semibold', corTipo(p.tipo)]">{{ p.tipo_nome }}</span> · {{ p.periodicidade_nome }}<template v-if="!p.ativo"> · inactivo</template></p>
            </div>
            <button type="button" @click="abrirPlano(p)" class="px-2 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300">Editar</button>
          </div>
          <p class="text-2xl font-black text-zinc-100 mt-2">{{ euros(p.preco) }}</p>
          <p v-if="p.meses > 1" class="text-xs text-zinc-500">{{ euros(p.preco_mes) }}/mês</p>
          <p v-if="p.descricao" class="text-xs text-zinc-400 mt-2">{{ p.descricao }}</p>
          <p v-if="p.tipo === 'servicos'" class="text-xs text-emerald-300/80 mt-2">
            {{ p.limite_marcacoes_mes ? p.limite_marcacoes_mes + ' marcações/mês' : 'Marcações sem limite' }} ·
            {{ p.limite_profissionais ? p.limite_profissionais + ' profissional(is)' : 'profissionais sem limite' }}
          </p>
          <p class="text-xs text-zinc-500 mt-2">{{ p.lojas }} {{ p.tipo === 'pos' ? 'POS' : 'loja(s)' }} neste plano</p>
        </div>
      </div>
    </template>

    </template>

    <!-- ═══ Modais ═══ -->
    <div v-if="modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" @click.self="modal = null">
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 w-full max-w-md space-y-4" role="dialog" :aria-label="modal.titulo">
        <h3 class="text-base font-bold text-zinc-100">{{ modal.titulo }}</h3>

        <!-- plano -->
        <template v-if="modal.tipo === 'plano'">
          <label class="block"><span class="text-xs text-zinc-500">Nome</span>
            <input v-model="modal.form.nome" maxlength="80" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
          <label class="block"><span class="text-xs text-zinc-500">Para</span>
            <select v-model="modal.form.tipo" :disabled="modal.plano && modal.plano.lojas > 0"
              class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 disabled:opacity-50">
              <option value="loja">Loja online</option><option value="pos">POS</option><option value="loja_pos">Loja + POS</option>
              <option value="servicos">Serviços (lojas em comissão)</option>
            </select></label>
          <p v-if="modal.form.tipo === 'loja_pos'" class="text-xs text-violet-300">Aparece às lojas: cobre a loja e o POS ligado a ela (o POS deixa de pagar o seu plano).</p>
          <template v-if="modal.form.tipo === 'servicos'">
            <p class="text-xs text-emerald-300">Para lojas em comissão activarem os Serviços. Nas lojas em subscrição os Serviços já estão incluídos.</p>
            <div class="grid grid-cols-2 gap-3">
              <label class="block"><span class="text-xs text-zinc-500">Marcações por mês</span>
                <input v-model="modal.form.limite_marcacoes_mes" type="number" min="1" step="1" placeholder="Sem limite" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
              <label class="block"><span class="text-xs text-zinc-500">Profissionais</span>
                <input v-model="modal.form.limite_profissionais" type="number" min="1" step="1" placeholder="Sem limite" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
            </div>
          </template>
          <div class="grid grid-cols-2 gap-3">
            <label class="block"><span class="text-xs text-zinc-500">Periodicidade</span>
              <select v-model="modal.form.periodicidade" :disabled="modal.plano && modal.plano.lojas > 0"
                class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 disabled:opacity-50">
                <option value="mensal">Mensal</option><option value="trimestral">Trimestral</option><option value="anual">Anual</option>
              </select></label>
            <label class="block"><span class="text-xs text-zinc-500">Preço (CVE)</span>
              <input v-model="modal.form.preco" type="number" min="0" step="1" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500" /></label>
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
          <p class="text-sm text-zinc-300">{{ modal.nome }} · {{ modal.planoNome }}</p>
          <label class="block"><span class="text-xs text-zinc-500">Quantos meses</span>
            <input v-model.number="modal.form.meses" type="number" min="1" max="12" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
          <label class="block"><span class="text-xs text-zinc-500">Motivo (o dono vê-o na notificação)</span>
            <input v-model="modal.form.motivo" maxlength="300" placeholder="ex.: compensação por falha do site" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
          <p class="text-xs text-zinc-500">As cobranças por pagar deste período ficam anuladas e é registada uma cobrança de 0$00 ("Oferta"). Se {{ modal.pos ? "o POS estiver suspenso" : "a loja estiver suspensa" }} por falta de pagamento, volta logo.<template v-if="modal.pos && !modal.pos.subscricao.plano"> Sem plano, os meses contam a partir de hoje.</template></p>
        </template>

        <!-- plano do POS -->
        <template v-else-if="modal.tipo === 'plano_pos'">
          <p class="text-sm text-zinc-400">Agora: <b class="text-zinc-200">{{ modal.pos.subscricao.plano ? modal.pos.subscricao.plano.nome : 'Sem plano' }}</b></p>
          <select v-model="modal.form.plano_id" aria-label="Plano do POS" class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100">
            <option :value="null" disabled>Escolhe um plano de POS</option>
            <option v-for="p in planos.filter(x => x.ativo && x.tipo === 'pos')" :key="p.id" :value="p.id">{{ p.nome }} — {{ euros(p.preco) }} / {{ p.periodicidade_nome.toLowerCase() }}</option>
          </select>
          <p class="text-xs text-zinc-500">
            <template v-if="modal.pos.subscricao.plano">Como quando o dono muda de plano: vale a partir da próxima renovação.</template>
            <template v-else>O POS fica com este plano. Se o período grátis já acabou, a primeira cobrança é emitida já.</template>
            O dono é avisado.
          </p>
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
          <label class="block"><span class="text-xs text-zinc-500">Motivo (fica registado na cobrança)</span>
            <input v-model="modal.form.motivo" maxlength="250" placeholder="ex.: valor errado" class="mt-1 w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100" /></label>
          <p class="text-xs text-zinc-500">A cobrança não se apaga. Se o período ficar por cobrir, é emitida uma nova automaticamente.</p>
        </template>

        <!-- mudar modelo -->
        <template v-else-if="modal.tipo === 'modelo'">
          <p class="text-sm text-zinc-400">Agora: <b class="text-zinc-200">{{ modal.loja.modelo === 'comissao' ? 'Comissão ' + Number(modal.loja.percentagem_comissao) + '%' : 'Subscrição' }}</b></p>
          <div v-if="modal.loja.modelo === 'comissao'" class="space-y-2">
            <p class="text-sm text-zinc-300">Passar para subscrição — escolhe o plano:</p>
            <select v-model="modal.form.plano_id" aria-label="Plano" class="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100">
              <option :value="null" disabled>Escolhe um plano</option>
              <option v-for="p in planos.filter(x => x.ativo && ['loja', 'loja_pos'].includes(x.tipo))" :key="p.id" :value="p.id">{{ p.nome }}{{ p.tipo === 'loja_pos' ? ' (Loja + POS)' : '' }} — {{ euros(p.preco) }}</option>
            </select>
            <p class="text-xs text-zinc-500">Sem período de teste: a primeira cobrança vence hoje. As encomendas já feitas continuam a pagar comissão.</p>
          </div>
          <p v-else class="text-sm text-zinc-300">Passar para <b>comissão ({{ Number(modal.loja.percentagem_comissao) }}%)</b>. A subscrição fica cancelada e as cobranças por pagar anuladas (não se apagam).</p>
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
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import { descarregarComprovativoSubscricao, urlFicheiro } from '@/utils/documentos'
import AbasVendedores from '@/components/fiscal/AbasVendedores.vue'
import PaginacaoLista from '@/components/fiscal/PaginacaoLista.vue'
import ListaCobrancas from '@/components/subscricao/ListaCobrancas.vue'
import LinhaCobrancaAdmin from '@/components/subscricao/LinhaCobrancaAdmin.vue'
import SubscricaoFicha from './SubscricaoFicha.vue'

const TABS = [{ key: 'resumo', label: 'Resumo' }, { key: 'lojas', label: 'Lojas' }, { key: 'pos', label: 'POS' }, { key: 'faturas', label: 'Cobranças' }, { key: 'planos', label: 'Planos' }]
const PERIODOS = [{ key: 'este_mes', label: 'Este mês' }, { key: 'mes_passado', label: 'Mês passado' },
                  { key: 'ult30', label: 'Últimos 30 dias' }, { key: 'este_ano', label: 'Este ano' }]
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const LIMITE = 20
const ESTADOS = { aguarda: 'Aguarda aprovação', teste: 'Em teste', ativa: 'Em dia', em_atraso: 'Em atraso', suspensa: 'Suspensa', cancelada: 'Cancelada' }

export default {
  name: 'AdminSubscricoes',
  components: { AbasVendedores, LinhaCobrancaAdmin, ListaCobrancas, PaginacaoLista, SubscricaoFicha },
  data () {
    return { TABS, PERIODOS, ESTADOS, LIMITE, tab: 'resumo', carregando: false, erro: '', periodo: 'este_mes', inicio: '', fim: '', resumo: null,
             lojas: { count: 0, results: [] }, q: '', modelo: '', estado: '', lOffset: 0,
             posLista: { count: 0, results: [] }, qPos: '', situacaoPos: '', estadoPos: '', pOffset: 0,
             tipoFatura: '', versao: 0,
             ficha: null, lojaDoPos: null,     // aba de uma loja/POS aberta; POS de uma loja → a aba ativa é a da loja
             planos: [], modal: null, t: null }
  },

  computed: {
    abaAtiva () {
      if (!this.ficha) return null
      if (this.ficha.tipo === 'pos' && this.lojaDoPos) return `loja-${this.lojaDoPos}`
      return `${this.ficha.tipo}-${this.ficha.id}`
    },
  },

  watch: {
    tab (t) {
      if (t === 'resumo') this.carregarResumo()
      else if (t === 'lojas') this.carregarLojas()
      else if (t === 'pos') this.carregarPos()
      else if (t === 'planos') this.carregarPlanos()
    },
  },

  created () { this.escolherPeriodo('este_mes'); this.carregarPlanos() },

  methods: {
    euros (v) { return formatarDinheiro(Number(v) || 0) },
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
    carregarLojas (offset = this.lOffset) {
      this.lOffset = offset
      return this.pedir(async () => {
        const params = { limit: LIMITE, offset }
        if (this.q.trim()) params.q = this.q.trim()
        if (this.modelo) params.modelo = this.modelo
        if (this.estado) params.estado = this.estado
        this.lojas = (await api.get('/app/admin/subscricoes/', { params })).data
      })
    },
    carregarPlanos () {
      return this.pedir(async () => { this.planos = (await api.get('/app/admin/planos/')).data })
    },
    selecionar (v) {
      if (v) return this.abrirFicha(v.tipo, v.id)
      this.ficha = null
      // de volta a "Todas": a lista aberta pode ter mudado com as ações feitas na vista da loja
      if (this.tab === 'lojas') this.carregarLojas()
      else if (this.tab === 'pos') this.carregarPos()
      else if (this.tab === 'resumo') this.carregarResumo()
    },
    abrirFicha (tipo, id, aba = '') {
      if (tipo !== 'pos') this.lojaDoPos = null
      this.ficha = { tipo, id, aba }
      window.scrollTo({ top: 0 })
    },
    // ações pedidas na vista da loja/POS ou numa linha de cobrança → os modais (ou o comprovativo / a Faturação)
    acaoFicha (tipo, x, extra) {
      const f = { oferta: () => this.abrirOferta(x, extra), modelo: () => this.abrirModelo(x), ofertaPos: () => this.abrirOfertaPos(x),
                  planoPos: () => this.abrirPlanoPos(x), pagar: () => this.abrirPagar(x), adiar: () => this.abrirAdiar(x),
                  anular: () => this.abrirAnular(x), recibo: () => this.recibo(x), faturacao: () => this.verNaFaturacao(x) }[tipo]
      if (f) f()
    },
    // depois de uma ação: as listas (versao), a vista aberta e os contadores das abas
    alterado () {
      this.versao++
      this.$refs.abas?.recarregar()
    },

    abrirPlano (p) {
      this.modal = { tipo: 'plano', plano: p, titulo: p ? `Editar "${p.nome}"` : 'Novo plano', botao: p ? 'Guardar' : 'Criar plano', erro: '', aGuardar: false,
                     form: p ? { nome: p.nome, tipo: p.tipo, periodicidade: p.periodicidade, preco: p.preco, descricao: p.descricao, ativo: p.ativo,
                                 limite_marcacoes_mes: p.limite_marcacoes_mes ?? '', limite_profissionais: p.limite_profissionais ?? '' }
                             : { nome: '', tipo: 'loja', periodicidade: 'mensal', preco: '', descricao: '', ativo: true,
                                 limite_marcacoes_mes: '', limite_profissionais: '' } }
    },
    corTipo (t) { return { loja: 'text-zinc-300', pos: 'text-sky-300', loja_pos: 'text-violet-300', servicos: 'text-emerald-300' }[t] || '' },
    abrirPagar (f) {
      this.modal = { tipo: 'pagar', fatura: f, titulo: `Marcar a fatura #${f.id} como paga`, botao: 'Marcar paga', erro: '', aGuardar: false,
                     form: { metodo: 'transferencia', notas: '' } }
    },
    recibo (f) { descarregarComprovativoSubscricao(f) },
    // a fatura legal do Bende (registar, substituir, anular, histórico) vive em Admin → Faturação, na ficha da loja/POS
    verNaFaturacao (f) {
      this.$router.push({ path: '/admin/faturacao', query: { ficha: f.loja_id ? `loja-${f.loja_id}` : `pos-${f.pos_id}`, aba: 'bende' } })
    },
    urlFicheiro,
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
    abrirOferta (l, servicos = false) {
      const sub = servicos ? l.subscricao_servicos : l.subscricao
      this.modal = { tipo: 'oferta', loja: l, nome: l.loja_nome, planoNome: sub.plano.nome,
                     titulo: `Oferecer meses${servicos ? ' de Serviços' : ''} — ${l.loja_nome}`, botao: 'Oferecer', erro: '', aGuardar: false,
                     form: servicos ? { meses: 1, motivo: '', servicos: true } : { meses: 1, motivo: '' } }
    },
    carregarPos (offset = this.pOffset) {
      this.pOffset = offset
      return this.pedir(async () => {
        const params = { limit: LIMITE, offset }
        if (this.qPos.trim()) params.q = this.qPos.trim()
        if (this.situacaoPos) params.situacao = this.situacaoPos
        if (this.estadoPos) params.estado = this.estadoPos
        this.posLista = (await api.get('/app/admin/subscricoes/pos/', { params })).data
      })
    },
    abrirOfertaPos (p) {
      this.modal = { tipo: 'oferta', pos: p, nome: p.pos_nome, planoNome: p.subscricao.plano ? p.subscricao.plano.nome : 'sem plano',
                     titulo: `Oferecer meses — ${p.pos_nome}`, botao: 'Oferecer', erro: '', aGuardar: false, form: { meses: 1, motivo: '' } }
    },
    abrirPlanoPos (p) {
      this.modal = { tipo: 'plano_pos', pos: p, titulo: `Plano do POS — ${p.pos_nome}`, botao: 'Guardar plano', erro: '', aGuardar: false,
                     form: { plano_id: null } }
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
          if (m.plano && m.plano.lojas > 0) { delete corpo.periodicidade; delete corpo.tipo }
          // os limites só contam nos planos de Serviços (vazio = sem limite)
          if (m.form.tipo !== 'servicos') { delete corpo.limite_marcacoes_mes; delete corpo.limite_profissionais }
          if (m.plano) await api.patch(`/app/admin/planos/${m.plano.id}/`, corpo)
          else await api.post('/app/admin/planos/', corpo)
          await this.carregarPlanos()
        } else if (m.tipo === 'pagar') {
          await api.post(`/app/admin/faturas/${m.fatura.id}/pagar/`, m.form)
        } else if (m.tipo === 'adiar' || m.tipo === 'anular') {
          await api.post(`/app/admin/faturas/${m.fatura.id}/${m.tipo}/`, m.form)
        } else if (m.tipo === 'oferta' && m.pos) {
          await api.post(`/app/admin/pos/${m.pos.pos_id}/subscricao/oferecer/`, m.form)
          if (this.tab === 'pos' && !this.ficha) await this.carregarPos()
        } else if (m.tipo === 'oferta') {
          await api.post(`/app/admin/lojas/${m.loja.loja_id}/subscricao/oferecer/`, m.form)
          if (this.tab === 'lojas' && !this.ficha) await this.carregarLojas()
        } else if (m.tipo === 'plano_pos') {
          if (!m.form.plano_id) throw { response: { data: { detail: 'Escolhe o plano.' } } }
          await api.post(`/app/admin/pos/${m.pos.pos_id}/subscricao/plano/`, m.form)
          if (this.tab === 'pos' && !this.ficha) await this.carregarPos()
        } else {
          const corpo = m.loja.modelo === 'comissao' ? { modelo: 'subscricao', plano_id: m.form.plano_id } : { modelo: 'comissao' }
          await api.patch(`/app/admin/lojas/${m.loja.loja_id}/cobranca/`, corpo)
          if (this.tab === 'lojas' && !this.ficha) await this.carregarLojas()
        }
        if (m.tipo !== 'plano') this.alterado()
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
