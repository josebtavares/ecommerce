<!-- AdminHome.vue — montar a página inicial: secções, ordem, conteúdo, datas; rascunho → publicar -->
<template>
  <div class="space-y-5">
    <!-- Cabeçalho -->
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div>
        <h2 class="text-lg font-bold text-zinc-100">Página inicial</h2>
        <p class="text-xs text-zinc-500 mt-0.5">
          Escolhe as secções da home, a ordem e o conteúdo. As alterações ficam em rascunho até publicares.
          O catálogo de todas as lojas e o rodapé aparecem sempre no fim.
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button @click="abrirPreview" :disabled="loading"
          class="px-3 py-2 rounded-xl border border-zinc-700 bg-zinc-900 text-xs font-semibold text-zinc-300 hover:border-zinc-500 transition flex items-center gap-1.5">
          <font-awesome-icon :icon="['fas', 'eye']" /> Pré-visualizar
        </button>
        <button @click="historicoAberto = true; carregarHistorico()" :disabled="loading"
          class="px-3 py-2 rounded-xl border border-zinc-700 bg-zinc-900 text-xs font-semibold text-zinc-300 hover:border-zinc-500 transition flex items-center gap-1.5">
          <font-awesome-icon :icon="['fas', 'clock-rotate-left']" /> Histórico
        </button>
        <button v-if="temAlteracoes" @click="descartar" :disabled="aGuardar"
          class="px-3 py-2 rounded-xl border border-zinc-700 bg-zinc-900 text-xs font-semibold text-zinc-300 hover:border-zinc-500 transition">
          Descartar alterações
        </button>
        <button @click="publicar" :disabled="aGuardar || !temAlteracoes || formSujo"
          :title="formSujo ? 'Guarda primeiro a secção que estás a editar' : ''"
          class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-bold text-white transition flex items-center gap-1.5">
          <font-awesome-icon :icon="['fas', 'upload']" /> Publicar
        </button>
      </div>
    </div>

    <!-- Estado da publicação -->
    <div v-if="!loading" class="flex items-center gap-2 text-xs flex-wrap">
      <span v-if="temAlteracoes" class="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold">
        Há alterações por publicar
      </span>
      <span v-else class="px-2.5 py-1 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 font-semibold">
        A home está igual ao rascunho
      </span>
      <span class="text-zinc-500">
        {{ publicacao ? `Publicado ${dataHora(publicacao.em)}${publicacao.por ? ' por ' + publicacao.por : ''}` : 'Ainda não publicaste: a home usa o layout original.' }}
      </span>
    </div>

    <div v-if="loading" class="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4">
      <div class="space-y-2"><div v-for="n in 6" :key="n" class="h-16 bg-zinc-900 rounded-xl animate-pulse"></div></div>
      <div class="h-96 bg-zinc-900 rounded-2xl animate-pulse"></div>
    </div>

    <p v-else-if="erroCarregar" class="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">{{ erroCarregar }}</p>

    <div v-else class="grid grid-cols-1 lg:grid-cols-[360px_minmax(0,1fr)] gap-4 items-start">

      <!-- ── Lista de secções ── -->
      <div class="space-y-2 lg:sticky lg:top-4">
        <div class="flex items-center justify-between px-1">
          <p class="text-[10px] font-bold uppercase tracking-wider text-zinc-600">Secções (de cima para baixo)</p>
          <span class="text-[10px] text-zinc-600">{{ seccoes.length }}/{{ MAX_SECCOES }}</span>
        </div>

        <div v-for="(s, i) in seccoes" :key="s.id" data-seccao
             draggable="true"
             @dragstart="arrastar = i" @dragend="arrastar = null; destino = null"
             @dragover.prevent="destino = i" @drop.prevent="largar(i)"
             @click="selecionar(s.id, false, true)"
             :class="['group flex items-center gap-2.5 px-3 py-2.5 rounded-xl border cursor-pointer transition select-none',
                      selecionadaId === s.id ? 'bg-zinc-800 border-red-500/50' : 'bg-zinc-900 border-zinc-800 hover:border-zinc-700',
                      destino === i && arrastar !== null && arrastar !== i ? 'ring-2 ring-red-500/60' : '',
                      !s.ativa ? 'opacity-50' : '']">
          <font-awesome-icon :icon="['fas', 'grip-vertical']" class="text-zinc-600 cursor-grab hidden sm:block" title="Arrasta para mudar a ordem" />
          <span class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-zinc-800 text-red-400">
            <font-awesome-icon :icon="['fas', ICONES[s.tipo] || 'square']" class="w-3.5 h-3.5" />
          </span>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-100 truncate">{{ s.titulo || s.tipo_nome }}</p>
            <p class="text-[11px] text-zinc-500 truncate">{{ resumo(s) }}</p>
          </div>
          <span v-if="s.avisos.length" class="text-amber-400 text-xs" :title="s.avisos.join('\n')">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
          </span>
          <span v-if="selecionadaId === s.id && formSujo" class="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" title="Por guardar"></span>
          <div class="flex flex-col">
            <button @click.stop="mover(i, -1)" :disabled="i === 0" aria-label="Subir"
              class="text-zinc-500 hover:text-zinc-200 disabled:opacity-20 leading-none px-1"><font-awesome-icon :icon="['fas', 'chevron-up']" class="w-3 h-3" /></button>
            <button @click.stop="mover(i, 1)" :disabled="i === seccoes.length - 1" aria-label="Descer"
              class="text-zinc-500 hover:text-zinc-200 disabled:opacity-20 leading-none px-1"><font-awesome-icon :icon="['fas', 'chevron-down']" class="w-3 h-3" /></button>
          </div>
        </div>

        <p v-if="!seccoes.length" class="text-xs text-zinc-600 py-6 text-center border border-dashed border-zinc-800 rounded-xl">
          Sem secções: a home mostra só o catálogo de lojas.
        </p>

        <button @click="escolherTipo = true" :disabled="seccoes.length >= MAX_SECCOES"
          class="w-full px-3 py-2.5 rounded-xl border border-dashed border-zinc-700 text-sm font-semibold text-red-400 hover:border-red-500/60 hover:bg-red-500/5 disabled:opacity-40 transition">
          + Adicionar secção
        </button>
        <button @click="reporPadrao" class="w-full text-[11px] text-zinc-600 hover:text-zinc-400 py-1">
          Repor o layout original no rascunho
        </button>
      </div>

      <!-- ── Editor ── -->
      <div v-if="form" ref="editor" class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden scroll-mt-4">
        <div class="flex items-center justify-between gap-3 px-5 py-3.5 border-b border-zinc-800 flex-wrap">
          <div class="flex items-center gap-2 min-w-0">
            <font-awesome-icon :icon="['fas', ICONES[form.tipo] || 'square']" class="w-4 h-4 text-red-400 flex-shrink-0" />
            <span class="text-sm font-bold text-zinc-100 truncate">{{ form.titulo || nomeTipo(form.tipo) }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500 uppercase font-bold">{{ nomeTipo(form.tipo) }}</span>
          </div>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <span class="text-xs" :class="form.ativa ? 'text-green-400' : 'text-zinc-500'">{{ form.ativa ? 'Visível' : 'Escondida' }}</span>
            <button type="button" role="switch" :aria-checked="form.ativa" @click="form.ativa = !form.ativa"
              :class="['relative w-10 h-6 rounded-full transition', form.ativa ? 'bg-green-600' : 'bg-zinc-700']">
              <span :class="['absolute top-1 w-4 h-4 rounded-full bg-white transition-all', form.ativa ? 'left-5' : 'left-1']"></span>
            </button>
          </label>
        </div>

        <div class="p-5 space-y-5">
          <!-- avisos -->
          <div v-if="selecionada?.avisos.length" class="px-3 py-2.5 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-1">
            <p v-for="(a, k) in selecionada.avisos" :key="k" class="text-xs text-amber-300 flex gap-2">
              <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="mt-0.5 flex-shrink-0" /> {{ a }}
            </p>
          </div>

          <!-- títulos -->
          <div v-if="form.tipo !== 'hero'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Título{{ form.tipo === 'cabecalho' ? '' : ' (opcional)' }}</label>
              <input v-model="form.titulo" maxlength="120" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" :placeholder="placeholderTitulo" />
            </div>
            <div>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Subtítulo (opcional)</label>
              <input v-model="form.subtitulo" maxlength="200" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
            </div>
          </div>
          <div v-if="form.tipo === 'cabecalho' || GRUPOS.includes(form.tipo)" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Estilo do título</label>
              <select v-model="form.parametros.estilo_titulo" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                <option value="titulo">Título grande</option>
                <option value="divisor">Divisor (linha com texto pequeno)</option>
              </select>
            </div>
            <div v-if="form.tipo === 'cabecalho'">
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Âncora do menu (opcional)</label>
              <input v-model="form.parametros.ancora" maxlength="30" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="produtos" />
              <p class="text-[10px] text-zinc-600 mt-1">"produtos" faz o link "Produtos" do menu lateral vir para aqui.</p>
            </div>
          </div>

          <!-- serviços: sempre automático -->
          <div v-if="form.tipo === 'servicos'" data-teste="home-servicos">
            <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Que serviços mostrar</label>
            <select v-model="form.criterio" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-red-500">
              <option v-for="c in opcoes.criterios_servicos" :key="c.valor" :value="c.valor">{{ c.nome }}</option>
            </select>
            <p class="text-[10px] text-zinc-600 mt-1">Só aparecem serviços de lojas com marcações abertas. Sem serviços, a secção não aparece.</p>
          </div>

          <!-- conteúdo: hero / lojas / produtos -->
          <template v-if="TEM_FONTE.includes(form.tipo)">
            <div>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Conteúdo</label>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button v-for="f in opcoes.fontes" :key="f.valor" type="button" @click="form.fonte = f.valor"
                  :class="['px-3 py-2.5 rounded-xl border text-left transition',
                           form.fonte === f.valor ? 'border-red-500/60 bg-red-500/10' : 'border-zinc-700 bg-zinc-800 hover:border-zinc-600']">
                  <p class="text-sm font-semibold text-zinc-100">{{ f.nome }}</p>
                  <p class="text-[11px] text-zinc-500">{{ DESCRICAO_FONTE[f.valor] }}</p>
                </button>
              </div>
            </div>

            <div v-if="form.fonte !== 'manual'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Critério automático</label>
                <select v-model="form.criterio" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                  <option value="" disabled>Escolhe…</option>
                  <option v-for="c in criteriosDoTipo" :key="c.valor" :value="c.valor">{{ c.nome }}</option>
                </select>
              </div>
              <!-- parâmetros do critério -->
              <div v-if="eLojas">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Só da categoria</label>
                <select v-model="form.parametros.categoria" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                  <option value="">Todas as categorias</option>
                  <option v-for="c in opcoes.categorias_lojas" :key="c.valor" :value="c.valor">{{ c.nome }}</option>
                </select>
              </div>
              <div v-else>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Só de lojas da categoria</label>
                <select v-model="form.parametros.categoria_loja" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                  <option value="">Todas as categorias</option>
                  <option v-for="c in opcoes.categorias_lojas" :key="c.valor" :value="c.valor">{{ c.nome }}</option>
                </select>
              </div>
              <div v-if="['novas', 'novos', 'mais_vendidas', 'mais_vendidos'].includes(form.criterio)">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">{{ form.criterio.startsWith('mais') ? 'Vendas dos últimos (dias)' : 'Criadas nos últimos (dias, opcional)' }}</label>
                <input v-model.number="form.parametros.dias" type="number" min="1" max="365" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500"
                       :placeholder="form.criterio.startsWith('mais') ? '30' : 'sem limite'" />
              </div>
              <div v-if="form.criterio === 'populares'">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Mínimo de avaliações</label>
                <input v-model.number="form.parametros.min_avaliacoes" type="number" min="1" max="100" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="3" />
                <p class="text-[10px] text-zinc-600 mt-1">Evita que uma loja com uma só avaliação de 5★ fique à frente de lojas com muitas.</p>
              </div>
              <div v-if="form.criterio === 'tipo'">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Tipo de produto</label>
                <select v-model="form.parametros.tipo_id" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                  <option :value="undefined" disabled>Escolhe…</option>
                  <option v-for="t in opcoes.tipos_produto" :key="t.id" :value="t.id">{{ t.nome }}</option>
                </select>
              </div>
              <div v-if="form.criterio === 'categoria_produto'" class="sm:col-span-2">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Categoria de produtos</label>
                <Procurar tipo="categoria" :valor="categoriaCriterio"
                  @escolher="c => { form.parametros.categoria_id = c.id; categoriaCriterio = { ...c, nome: `${c.nome} — ${c.loja}` } }" />
              </div>
              <div v-if="form.criterio === 'loja'" class="sm:col-span-2">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Loja</label>
                <Procurar tipo="loja" :valor="lojaCriterio" @escolher="l => { form.parametros.loja_id = l.id; lojaCriterio = l }" />
              </div>
              <label v-if="eLojas && ['novas', 'todas', 'abertas'].includes(form.criterio)"
                     class="sm:col-span-2 flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                <input type="checkbox" v-model="form.parametros.abertas_primeiro" class="accent-red-600" />
                Mostrar primeiro as lojas abertas agora
              </label>
            </div>

            <!-- home inteligente: sem repetir o que já aparece em cima, esconder secções quase vazias -->
            <div v-if="['lojas', 'produtos'].includes(form.tipo)" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label v-if="form.fonte !== 'manual'" class="flex items-start gap-2 text-xs text-zinc-400 cursor-pointer">
                <input type="checkbox" v-model="form.parametros.sem_repetidos" class="accent-red-600 mt-0.5" />
                <span>Não repetir {{ form.tipo === 'lojas' ? 'lojas' : 'produtos' }} que já aparecem nas secções de cima
                  <span class="block text-[10px] text-zinc-600">O automático passa ao seguinte; os escolhidos à mão aparecem sempre.</span></span>
              </label>
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Esconder com menos de</label>
                <input v-model.number="form.parametros.minimo" type="number" min="1" max="20" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500"
                       :placeholder="`1 ${form.tipo === 'lojas' ? 'loja' : 'produto'} (mostra sempre)`" />
              </div>
            </div>
          </template>

          <!-- loja em destaque -->
          <div v-if="form.tipo === 'loja_destaque'">
            <p class="text-xs text-zinc-500 mb-3">Os produtos escolhidos aparecem primeiro; o resto é preenchido com os destaques e os mais recentes da loja.</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
              <button v-for="m in [{ v: false, n: 'Escolhida por mim', d: 'Fica sempre a mesma loja.' },
                                   { v: true, n: 'Automática', d: 'Uma das primeiras do critério, muda todos os dias.' }]"
                :key="String(m.v)" type="button" @click="form.destaqueAuto = m.v"
                :class="['px-3 py-2.5 rounded-xl border text-left transition',
                         form.destaqueAuto === m.v ? 'border-red-500/60 bg-red-500/10' : 'border-zinc-700 bg-zinc-800 hover:border-zinc-600']">
                <p class="text-sm font-semibold text-zinc-100">{{ m.n }}</p>
                <p class="text-[11px] text-zinc-500">{{ m.d }}</p>
              </button>
            </div>
            <div v-if="form.destaqueAuto" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Critério</label>
                <select v-model="form.criterio" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                  <option value="" disabled>Escolhe…</option>
                  <option v-for="c in opcoes.criterios_lojas" :key="c.valor" :value="c.valor">{{ c.nome }}</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Só da categoria</label>
                <select v-model="form.parametros.categoria" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500">
                  <option value="">Todas as categorias</option>
                  <option v-for="c in opcoes.categorias_lojas" :key="c.valor" :value="c.valor">{{ c.nome }}</option>
                </select>
              </div>
              <div v-if="form.criterio === 'populares'">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Mínimo de avaliações</label>
                <input v-model.number="form.parametros.min_avaliacoes" type="number" min="1" max="100" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="3" />
              </div>
              <div v-if="['novas', 'mais_vendidas'].includes(form.criterio)">
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">{{ form.criterio === 'mais_vendidas' ? 'Vendas dos últimos (dias)' : 'Criadas nos últimos (dias, opcional)' }}</label>
                <input v-model.number="form.parametros.dias" type="number" min="1" max="365" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500"
                       :placeholder="form.criterio === 'mais_vendidas' ? '30' : 'sem limite'" />
              </div>
            </div>
            <template v-else>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Loja em destaque</label>
              <Procurar tipo="loja" :valor="lojaCriterio" @escolher="l => { form.parametros.loja_id = l.id; lojaCriterio = l; form.itens = [] }" />
            </template>
          </div>

          <!-- grelha de categorias de lojas -->
          <div v-if="form.tipo === 'categorias'">
            <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Categorias a mostrar</label>
            <p class="text-[11px] text-zinc-500 mb-2">Nenhuma escolhida = todas, as que têm mais lojas primeiro. Clicar numa categoria filtra o catálogo.</p>
            <div class="flex flex-wrap gap-2">
              <button v-for="c in opcoes.categorias_lojas" :key="c.valor" type="button" @click="alternarCategoria(c.valor)"
                :class="['px-3 py-1.5 rounded-lg border text-xs font-semibold transition',
                         (form.parametros.categorias || []).includes(c.valor) ? 'border-red-500/60 bg-red-500/10 text-red-300' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500']">
                <span v-if="(form.parametros.categorias || []).includes(c.valor)" class="mr-1 text-red-400">{{ form.parametros.categorias.indexOf(c.valor) + 1 }}.</span>{{ c.nome }}
              </button>
            </div>
          </div>

          <!-- categorias de produtos em destaque (antiga página Categorias em Destaque) -->
          <div v-if="form.tipo === 'produtos_categorias_destaque'">
            <div class="flex items-center justify-between mb-2">
              <label class="text-xs text-zinc-400 font-medium block">Categorias ({{ form.categoriasSel.length }})</label>
              <span class="text-[10px] text-zinc-600">máx. 30 · um slider por categoria</span>
            </div>
            <div class="space-y-2">
              <div v-for="(c, k) in form.categoriasSel" :key="c.id" class="flex items-center gap-2 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2">
                <font-awesome-icon :icon="['fas', 'tags']" class="text-zinc-500 w-3.5" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-zinc-100 truncate">{{ c.nome }} <span class="text-zinc-500">— {{ c.loja }}</span></p>
                  <p v-if="c.loja_ativa === false" class="text-[11px] text-amber-400">Loja não activa: não aparece.</p>
                </div>
                <button @click="moverCategoria(k, -1)" :disabled="k === 0" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Subir"><font-awesome-icon :icon="['fas', 'chevron-up']" /></button>
                <button @click="moverCategoria(k, 1)" :disabled="k === form.categoriasSel.length - 1" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Descer"><font-awesome-icon :icon="['fas', 'chevron-down']" /></button>
                <button @click="form.categoriasSel.splice(k, 1)" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-red-400 disabled:opacity-20 transition" aria-label="Remover"><font-awesome-icon :icon="['fas', 'xmark']" /></button>
              </div>
            </div>
            <Procurar v-if="form.categoriasSel.length < 30" class="mt-2" tipo="categoria" :limpar="true" @escolher="adicionarCategoria" />
          </div>

          <!-- grupos -->
          <p v-if="GRUPOS.includes(form.tipo)" class="text-xs text-zinc-500 px-3 py-2.5 bg-zinc-800/60 rounded-xl">
            {{ DESCRICAO_GRUPO[form.tipo] }}
          </p>

          <!-- itens escolhidos -->
          <div v-if="aceitaItens">
            <div class="flex items-center justify-between mb-2">
              <label class="text-xs text-zinc-400 font-medium block">
                {{ form.fonte === 'misto' ? 'Fixados no início' : 'Escolhidos' }} ({{ form.itens.length }})
              </label>
              <span class="text-[10px] text-zinc-600">máx. {{ MAX_ITENS }}</span>
            </div>
            <div class="space-y-2">
              <div v-for="(it, k) in form.itens" :key="it._k" class="bg-zinc-800 border border-zinc-700 rounded-xl p-2.5">
                <div class="flex items-center gap-2">
                  <font-awesome-icon :icon="['fas', it.loja_id ? 'store' : it.produto_id ? 'box' : 'image']" class="text-zinc-500 w-3.5" />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm text-zinc-100 truncate">{{ nomeItem(it) }}</p>
                    <p v-if="avisoItem(it)" class="text-[11px] text-amber-400">{{ avisoItem(it) }}</p>
                  </div>
                  <button @click="moverItem(k, -1)" :disabled="k === 0" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Subir"><font-awesome-icon :icon="['fas', 'chevron-up']" /></button>
                  <button @click="moverItem(k, 1)" :disabled="k === form.itens.length - 1" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Descer"><font-awesome-icon :icon="['fas', 'chevron-down']" /></button>
                  <button @click="form.itens.splice(k, 1)" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-red-400 disabled:opacity-20 transition" aria-label="Remover"><font-awesome-icon :icon="['fas', 'xmark']" /></button>
                </div>
                <div v-if="form.tipo === 'hero' || !it.loja_id && !it.produto_id" class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                  <input v-model="it.titulo" maxlength="120" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500"
                         :placeholder="it.loja_id || it.produto_id ? 'Título no hero (opcional)' : 'Título do banner (opcional com imagem)'" />
                  <input v-model="it.texto" maxlength="300" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500"
                         :placeholder="it.loja_id || it.produto_id ? 'Texto no hero (opcional)' : 'Texto (opcional)'" />
                  <input v-if="!it.loja_id && !it.produto_id" v-model="it.link" maxlength="300" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500 sm:col-span-2"
                         placeholder="Link: /loja/12 ou https://…" />
                  <div v-if="!it.loja_id && !it.produto_id" class="sm:col-span-2 flex items-center gap-3">
                    <img v-if="it.imagem_url" :src="it.imagem_url" alt="" class="w-28 h-16 rounded-lg object-cover border border-zinc-700" />
                    <label class="px-3 py-1.5 rounded-lg border border-zinc-700 text-xs font-semibold text-zinc-300 hover:border-zinc-500 cursor-pointer">
                      {{ it._aCarregar ? 'A carregar…' : it.imagem_id ? 'Trocar imagem' : 'Carregar imagem' }}
                      <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" :disabled="it._aCarregar"
                             @change="e => carregarImagem(it, e)" />
                    </label>
                    <button v-if="it.imagem_id" type="button" @click="it.imagem_id = null; it.imagem_url = ''"
                      class="text-xs text-zinc-500 hover:text-red-400">Remover imagem</button>
                    <span class="text-[10px] text-zinc-600">JPG, PNG ou WEBP · até 5 MB · ideal 1600×600</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="form.itens.length < MAX_ITENS" class="mt-2 flex flex-col sm:flex-row gap-2">
              <div v-if="generosItens.length > 1" class="flex gap-1 flex-shrink-0">
                <button v-for="g in generosItens" :key="g" type="button" @click="generoNovo = g"
                  :class="['px-2.5 py-2 rounded-lg text-xs font-semibold border transition',
                           generoNovo === g ? 'border-red-500/60 text-red-300 bg-red-500/10' : 'border-zinc-700 text-zinc-400']">
                  {{ { loja: 'Loja', produto: 'Produto', banner: 'Banner' }[g] }}
                </button>
              </div>
              <button v-if="generoNovo === 'banner'" type="button" @click="adicionarItem({})"
                class="flex-1 px-3 py-2 rounded-xl border border-dashed border-zinc-700 text-xs font-semibold text-zinc-300 hover:border-zinc-500">
                + Adicionar banner
              </button>
              <Procurar v-else class="flex-1" :tipo="generoNovo" :limpar="true"
                :loja-id="form.tipo === 'loja_destaque' ? form.parametros.loja_id : null"
                @escolher="x => adicionarItem(generoNovo === 'loja' ? { loja_id: x.id, loja: x } : { produto_id: x.id, produto: x })" />
            </div>
          </div>

          <!-- limite + datas -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div v-if="form.tipo !== 'cabecalho'">
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">{{ form.tipo === 'hero' ? 'Máximo de slides' : GRUPOS.includes(form.tipo) ? 'Máximo por slider' : 'Máximo de itens' }}</label>
              <input v-model.number="form.limite" type="number" min="1" :max="limiteMax" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
            </div>
            <div>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Mostrar a partir de</label>
              <input v-model="form.inicio" type="datetime-local" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
            </div>
            <div>
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Mostrar até</label>
              <input v-model="form.fim" type="datetime-local" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" />
            </div>
          </div>
          <p class="text-[10px] text-zinc-600 -mt-3">Datas vazias = sempre. Úteis para campanhas.</p>

          <p v-if="erro" class="px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400">{{ erro }}</p>

          <div class="flex items-center justify-between gap-2 pt-1 flex-wrap">
            <div class="flex gap-2">
              <button @click="duplicar" :disabled="aGuardar || seccoes.length >= MAX_SECCOES"
                class="px-3 py-2 rounded-xl border border-zinc-700 text-xs font-semibold text-zinc-300 hover:border-zinc-500 disabled:opacity-40">Duplicar</button>
              <button @click="apagar" :disabled="aGuardar"
                class="px-3 py-2 rounded-xl border border-red-500/30 text-xs font-semibold text-red-400 hover:bg-red-500/10">Apagar</button>
            </div>
            <div class="flex gap-2">
              <button v-if="formSujo" @click="carregarForm(selecionada)" :disabled="aGuardar"
                class="px-3 py-2 rounded-xl border border-zinc-700 text-xs font-semibold text-zinc-300">Desfazer</button>
              <button @click="guardar" :disabled="aGuardar || !formSujo"
                class="px-4 py-2 rounded-xl bg-zinc-100 hover:bg-white disabled:opacity-40 text-xs font-bold text-zinc-900">
                {{ aGuardar ? 'A guardar…' : 'Guardar secção' }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="hidden lg:flex h-64 items-center justify-center text-sm text-zinc-600 border border-dashed border-zinc-800 rounded-2xl">
        Escolhe uma secção para editar.
      </div>
    </div>

    <!-- Escolher tipo de secção nova -->
    <div v-if="escolherTipo" class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" @click.self="escolherTipo = false">
      <div class="w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-2xl p-5 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-zinc-100">Nova secção</h3>
          <button @click="escolherTipo = false" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Fechar"><font-awesome-icon :icon="['fas', 'xmark']" /></button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <button v-for="t in tiposDisponiveis" :key="t.valor" @click="criar(t.valor)" :disabled="aGuardar"
            class="flex items-start gap-3 px-3 py-3 rounded-xl border border-zinc-700 bg-zinc-800 hover:border-red-500/50 text-left transition">
            <span class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-zinc-900 text-red-400">
              <font-awesome-icon :icon="['fas', ICONES[t.valor]]" />
            </span>
            <span>
              <span class="block text-sm font-semibold text-zinc-100">{{ t.nome }}</span>
              <span class="block text-[11px] text-zinc-500">{{ DESCRICAO_TIPO[t.valor] }}</span>
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Histórico -->
    <div v-if="historicoAberto" class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" @click.self="historicoAberto = false">
      <div class="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-5 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-1">
          <h3 class="text-base font-bold text-zinc-100">Publicações anteriores</h3>
          <button @click="historicoAberto = false" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Fechar"><font-awesome-icon :icon="['fas', 'xmark']" /></button>
        </div>
        <p class="text-xs text-zinc-500 mb-4">Restaurar carrega essa versão no rascunho. Só muda a home quando publicares.</p>
        <p v-if="!historico.length" class="text-sm text-zinc-600 py-6 text-center">Ainda não há publicações.</p>
        <div v-for="(p, k) in historico" :key="p.id" class="flex items-center gap-3 py-2.5 border-b border-zinc-800 last:border-0">
          <div class="flex-1">
            <p class="text-sm text-zinc-200">{{ dataHora(p.em) }} <span v-if="k === 0" class="text-[10px] text-green-400 font-bold ml-1">EM USO</span></p>
            <p class="text-[11px] text-zinc-500">{{ p.seccoes }} secções{{ p.por ? ' · ' + p.por : '' }}</p>
          </div>
          <button @click="restaurar(p)" class="px-3 py-1.5 rounded-lg border border-zinc-700 text-xs font-semibold text-zinc-300 hover:border-zinc-500">Restaurar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { toast } from 'vue3-toastify'
import Procurar from '@/components/admin/HomeProcurar.vue'

const ICONES = {
  hero: 'panorama', lojas: 'store', produtos: 'box', loja_destaque: 'star', categorias: 'table-cells',
  banner: 'image', cabecalho: 'heading', lojas_por_categoria: 'layer-group', produtos_por_tipo: 'shapes',
  produtos_categorias_destaque: 'fire',
}
const DESCRICAO_TIPO = {
  hero: 'Slides grandes no topo: lojas, produtos ou banners.',
  lojas: 'Slider de lojas escolhidas ou por critério (populares, novas…).',
  produtos: 'Slider de produtos escolhidos ou por critério (novos, mais vendidos…).',
  cabecalho: 'Título ou divisor entre secções.',
  lojas_por_categoria: 'Um slider de lojas por cada categoria.',
  produtos_por_tipo: 'Um slider de produtos por cada tipo global.',
  produtos_categorias_destaque: 'Um slider por cada categoria em destaque.',
  loja_destaque: 'Bloco grande de uma loja com alguns produtos.',
  categorias: 'Grelha de categorias de lojas.',
  banner: 'Faixa promocional com link.',
}
const DESCRICAO_FONTE = {
  manual: 'Só os que escolheres, pela tua ordem.',
  auto: 'Preenchido sozinho pelo critério.',
  misto: 'Os escolhidos primeiro, o resto pelo critério.',
}
const DESCRICAO_GRUPO = {
  lojas_por_categoria: 'Mostra um slider por cada categoria de loja que tenha lojas activas (as lojas abertas primeiro).',
  produtos_por_tipo: 'Mostra um slider por cada tipo global de produto com produtos visíveis.',
  produtos_categorias_destaque: 'Mostra um slider por cada categoria em Admin → Categorias em Destaque.',
}
const TEM_FONTE = ['hero', 'lojas', 'produtos']
const GRUPOS = ['lojas_por_categoria', 'produtos_por_tipo', 'produtos_categorias_destaque']
const ITENS_POR_TIPO = { hero: ['loja', 'produto', 'banner'], lojas: ['loja'], produtos: ['produto'], loja_destaque: ['produto'], banner: ['banner'] }
const NOVA = {
  hero: { fonte: 'auto', criterio: 'novas' },
  lojas: { titulo: 'Lojas populares', fonte: 'auto', criterio: 'populares' },
  produtos: { titulo: 'Novidades', fonte: 'auto', criterio: 'novos' },
  cabecalho: { titulo: 'Nova secção', parametros: { estilo_titulo: 'titulo' } },
  lojas_por_categoria: {}, produtos_por_tipo: {}, produtos_categorias_destaque: {},
  loja_destaque: {}, categorias: {}, banner: { fonte: 'manual' },
  servicos: { titulo: 'Marca um serviço', fonte: 'auto', criterio: 'novos' },
}
const MAX_SECCOES = 40
const MAX_ITENS = 50

let uid = 0

// ISO do servidor ↔ valor do <input type="datetime-local"> (hora local)
function paraLocal (iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}
function paraIso (local) {
  return local ? new Date(local).toISOString() : null
}

export default {
  name: 'AdminHome',
  components: { Procurar },

  data () {
    return {
      ICONES, DESCRICAO_TIPO, DESCRICAO_FONTE, DESCRICAO_GRUPO, TEM_FONTE, GRUPOS, MAX_SECCOES, MAX_ITENS,
      seccoes: [],
      opcoes: { fontes: [], tipos: [], criterios_lojas: [], criterios_produtos: [], criterios_servicos: [], categorias_lojas: [], tipos_produto: [], categorias_destaque: [] },
      publicacao: null,
      temAlteracoes: false,
      selecionadaId: null,
      form: null,
      original: '',
      lojaCriterio: null,
      categoriaCriterio: null,
      generoNovo: 'loja',
      loading: true,
      aGuardar: false,
      erro: '',
      erroCarregar: '',
      escolherTipo: false,
      historicoAberto: false,
      historico: [],
      arrastar: null,
      destino: null,
    }
  },

  computed: {
    selecionada () { return this.seccoes.find(s => s.id === this.selecionadaId) || null },
    formSujo () { return !!this.form && JSON.stringify(this.payload()) !== this.original },
    eLojas () { return this.form && ['hero', 'lojas'].includes(this.form.tipo) },
    criteriosDoTipo () { return this.eLojas ? this.opcoes.criterios_lojas : this.opcoes.criterios_produtos },
    generosItens () { return this.form ? (ITENS_POR_TIPO[this.form.tipo] || []) : [] },
    aceitaItens () {
      if (!this.form || !this.generosItens.length) return false
      if (this.form.tipo === 'loja_destaque') return !!this.form.parametros.loja_id
      return !TEM_FONTE.includes(this.form.tipo) || this.form.fonte !== 'auto'
    },
    limiteMax () { return ['hero', 'loja_destaque'].includes(this.form?.tipo) ? 20 : (this.opcoes.limite_max || 100) },
    tiposDisponiveis () { return this.opcoes.tipos },
    placeholderTitulo () {
      return { lojas_por_categoria: 'Sem título: só os sliders', produtos_por_tipo: 'Ex.: Produtos', cabecalho: 'Ex.: Produtos' }[this.form?.tipo] || ''
    },
  },

  async created () {
    await this.carregar()
  },
  mounted () { window.addEventListener('beforeunload', this.avisoSair) },
  beforeUnmount () { window.removeEventListener('beforeunload', this.avisoSair) },

  methods: {
    nomeTipo (t) { return this.opcoes.tipos.find(x => x.valor === t)?.nome || t },
    dataHora (iso) { return iso ? new Date(iso).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' }) : '' },

    resumo (s) {
      const partes = []
      if (TEM_FONTE.includes(s.tipo)) {
        const crit = [...this.opcoes.criterios_lojas, ...this.opcoes.criterios_produtos].find(c => c.valor === s.criterio)?.nome
        if (s.fonte === 'manual') partes.push(`${s.itens.length} escolhidos`)
        else if (s.fonte === 'misto') partes.push(`${s.itens.length} fixados + ${crit || '?'}`)
        else partes.push(crit || 'Automático')
      } else if (s.tipo === 'loja_destaque' && !s.parametros?.loja_id && s.criterio) {
        partes.push(`Automática: ${this.opcoes.criterios_lojas.find(c => c.valor === s.criterio)?.nome || s.criterio}`)
      } else if (s.tipo === 'servicos') {
        partes.push(this.opcoes.criterios_servicos.find(c => c.valor === s.criterio)?.nome || 'Serviços')
      } else partes.push(s.tipo_nome)
      if (s.parametros?.sem_repetidos) partes.push('sem repetidos')
      if (s.parametros?.minimo > 1) partes.push(`mín. ${s.parametros.minimo}`)
      if (s.inicio || s.fim) partes.push('com datas')
      if (!s.ativa) partes.push('escondida')
      return partes.join(' · ')
    },

    avisoSair (e) {
      if (this.formSujo) { e.preventDefault(); e.returnValue = '' }
    },

    aplicar (data) {
      if (data.seccoes) this.seccoes = data.seccoes
      if (data.opcoes) this.opcoes = data.opcoes
      if ('publicacao' in data) this.publicacao = data.publicacao
      if ('tem_alteracoes' in data) this.temAlteracoes = data.tem_alteracoes
    },

    async carregar () {
      this.loading = true
      try {
        const { data } = await api.get('/app/admin/home/')
        this.aplicar(data)
        const manter = this.seccoes.find(s => s.id === this.selecionadaId)
        this.selecionar(manter ? manter.id : this.seccoes[0]?.id, true)
      } catch (e) {
        this.erroCarregar = e.response?.data?.detail || 'Não foi possível carregar a página inicial.'
      } finally { this.loading = false }
    },

    selecionar (id, forcar = false, rolar = false) {
      if (!forcar && id === this.selecionadaId) return
      if (!forcar && this.formSujo && !confirm('Há alterações por guardar nesta secção. Sair sem guardar?')) return
      this.selecionadaId = id ?? null
      this.carregarForm(this.selecionada)
      // no telemóvel o editor fica por baixo da lista
      if (rolar && window.innerWidth < 1024) this.$nextTick(() => this.$refs.editor?.scrollIntoView({ behavior: 'smooth' }))
    },

    carregarForm (s) {
      this.erro = ''
      if (!s) { this.form = null; return }
      this.form = {
        tipo: s.tipo, titulo: s.titulo, subtitulo: s.subtitulo, ativa: s.ativa,
        inicio: paraLocal(s.inicio), fim: paraLocal(s.fim),
        fonte: s.fonte, criterio: s.criterio, limite: s.limite,
        parametros: { estilo_titulo: 'titulo', categoria: '', categoria_loja: '', ...JSON.parse(JSON.stringify(s.parametros || {})) },
        itens: s.itens.map(i => ({ ...i, _k: ++uid })),
        categoriasSel: (s.parametros?.categoria_ids || []).map(id => s.refs?.categorias?.[id] || { id, nome: `Categoria #${id}`, loja: '' }),
        destaqueAuto: s.tipo === 'loja_destaque' && !s.parametros?.loja_id && !!s.criterio,
      }
      if (['lojas', 'hero'].includes(s.tipo) && this.form.parametros.abertas_primeiro === undefined) {
        this.form.parametros.abertas_primeiro = ['novas', 'todas', ''].includes(s.criterio)
      }
      const lid = this.form.parametros.loja_id
      this.lojaCriterio = lid ? (s.refs?.loja || { id: lid, nome: `Loja #${lid}` }) : null
      const cid = this.form.parametros.categoria_id
      const cat = cid ? s.refs?.categorias?.[cid] : null
      this.categoriaCriterio = cid ? { id: cid, nome: cat ? `${cat.nome} — ${cat.loja}` : `Categoria #${cid}` } : null
      this.generoNovo = (ITENS_POR_TIPO[s.tipo] || ['loja'])[0]
      this.original = JSON.stringify(this.payload())
    },

    // só os parâmetros que fazem sentido para o tipo/critério escolhido
    parametrosLimpos () {
      const f = this.form
      const p = f.parametros
      const out = {}
      const por = (k, v) => { if (v !== undefined && v !== null && v !== '') out[k] = v }
      if (f.tipo === 'cabecalho') { por('estilo_titulo', p.estilo_titulo); por('ancora', p.ancora) }
      if (GRUPOS.includes(f.tipo)) por('estilo_titulo', p.estilo_titulo)
      if (f.tipo === 'loja_destaque' && !f.destaqueAuto) por('loja_id', p.loja_id)
      if (f.tipo === 'loja_destaque' && f.destaqueAuto) {
        por('categoria', p.categoria)
        if (['novas', 'mais_vendidas'].includes(f.criterio)) por('dias', p.dias)
        if (f.criterio === 'populares') por('min_avaliacoes', p.min_avaliacoes)
      }
      if (['lojas', 'produtos'].includes(f.tipo)) {
        por('minimo', p.minimo)
        if (f.fonte !== 'manual' && p.sem_repetidos) out.sem_repetidos = true
      }
      if (f.tipo === 'categorias' && p.categorias?.length) out.categorias = [...p.categorias]
      if (f.tipo === 'produtos_categorias_destaque' && f.categoriasSel.length) out.categoria_ids = f.categoriasSel.map(c => c.id)
      if (TEM_FONTE.includes(f.tipo) && f.fonte !== 'manual') {
        if (this.eLojas) {
          por('categoria', p.categoria)
          if (['novas', 'todas', 'abertas'].includes(f.criterio)) out.abertas_primeiro = !!p.abertas_primeiro
        } else por('categoria_loja', p.categoria_loja)
        if (['novas', 'novos', 'mais_vendidas', 'mais_vendidos'].includes(f.criterio)) por('dias', p.dias)
        if (f.criterio === 'populares') por('min_avaliacoes', p.min_avaliacoes)
        if (f.criterio === 'tipo') por('tipo_id', p.tipo_id)
        if (f.criterio === 'loja') por('loja_id', p.loja_id)
        if (f.criterio === 'categoria_produto') por('categoria_id', p.categoria_id)
      }
      return out
    },

    payload () {
      const f = this.form
      const comItens = this.aceitaItens
      return {
        titulo: f.titulo || '', subtitulo: f.subtitulo || '', ativa: f.ativa,
        inicio: paraIso(f.inicio), fim: paraIso(f.fim),
        fonte: f.fonte,
        criterio: (TEM_FONTE.includes(f.tipo) && f.fonte !== 'manual') || (f.tipo === 'loja_destaque' && f.destaqueAuto) || f.tipo === 'servicos'
          ? (f.criterio || '') : '',
        limite: f.limite, parametros: this.parametrosLimpos(),
        itens: comItens ? f.itens.map(i => ({ loja_id: i.loja_id || null, produto_id: i.produto_id || null,
                                               imagem_id: i.imagem_id || null,
                                               titulo: i.titulo || '', texto: i.texto || '', link: i.link || '' })) : [],
      }
    },

    async guardar () {
      this.aGuardar = true
      this.erro = ''
      try {
        const { data } = await api.patch(`/app/admin/home/seccoes/${this.selecionadaId}/`, this.payload())
        const i = this.seccoes.findIndex(s => s.id === data.seccao.id)
        this.seccoes.splice(i, 1, data.seccao)
        this.aplicar(data)
        this.carregarForm(data.seccao)
        toast.success('Secção guardada no rascunho.')
      } catch (e) {
        this.erro = e.response?.data?.detail || 'Não foi possível guardar.'
      } finally { this.aGuardar = false }
    },

    async criar (tipo) {
      if (this.formSujo && !confirm('Há alterações por guardar nesta secção. Continuar sem guardar?')) return
      this.aGuardar = true
      try {
        const { data } = await api.post('/app/admin/home/seccoes/', { tipo, ...NOVA[tipo] })
        this.seccoes.push(data.seccao)
        this.aplicar(data)
        this.escolherTipo = false
        this.selecionar(data.seccao.id, true)
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível criar a secção.')
      } finally { this.aGuardar = false }
    },

    async duplicar () {
      this.aGuardar = true
      try {
        const { data } = await api.post(`/app/admin/home/seccoes/${this.selecionadaId}/duplicar/`)
        const antes = new Set(this.seccoes.map(s => s.id))
        this.aplicar(data)
        const nova = this.seccoes.find(s => !antes.has(s.id))
        this.selecionar(nova?.id ?? this.selecionadaId, true)
        toast.success('Cópia criada (escondida).')
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível duplicar.')
      } finally { this.aGuardar = false }
    },

    async apagar () {
      if (!confirm('Apagar esta secção do rascunho?')) return
      this.aGuardar = true
      try {
        const { data } = await api.delete(`/app/admin/home/seccoes/${this.selecionadaId}/`)
        const i = this.seccoes.findIndex(s => s.id === this.selecionadaId)
        this.seccoes.splice(i, 1)
        this.aplicar(data)
        this.selecionar(this.seccoes[Math.min(i, this.seccoes.length - 1)]?.id, true)
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível apagar.')
      } finally { this.aGuardar = false }
    },

    async gravarOrdem (nova) {
      const antiga = this.seccoes
      this.seccoes = nova
      try {
        const { data } = await api.post('/app/admin/home/ordem/', { ids: nova.map(s => s.id) })
        this.aplicar(data)
      } catch (e) {
        this.seccoes = antiga
        toast.error(e.response?.data?.detail || 'Não foi possível mudar a ordem.')
        if (e.response?.status === 409) this.carregar()
      }
    },

    mover (i, d) {
      const j = i + d
      if (j < 0 || j >= this.seccoes.length) return
      const nova = [...this.seccoes]
      ;[nova[i], nova[j]] = [nova[j], nova[i]]
      this.gravarOrdem(nova)
    },

    largar (i) {
      const de = this.arrastar
      this.arrastar = null
      this.destino = null
      if (de === null || de === i) return
      const nova = [...this.seccoes]
      const [s] = nova.splice(de, 1)
      nova.splice(i, 0, s)
      this.gravarOrdem(nova)
    },

    adicionarItem (dados) {
      const repetido = (dados.loja_id && this.form.itens.some(i => i.loja_id === dados.loja_id)) ||
                       (dados.produto_id && this.form.itens.some(i => i.produto_id === dados.produto_id))
      if (repetido) { toast.info('Já está na lista.'); return }
      this.form.itens.push({ loja_id: null, produto_id: null, imagem_id: null, imagem_url: '', titulo: '', texto: '', link: '', ...dados, _k: ++uid })
    },

    moverItem (k, d) {
      const j = k + d
      if (j < 0 || j >= this.form.itens.length) return
      const itens = this.form.itens
      ;[itens[k], itens[j]] = [itens[j], itens[k]]
    },

    alternarCategoria (valor) {
      const lista = [...(this.form.parametros.categorias || [])]
      const i = lista.indexOf(valor)
      if (i >= 0) lista.splice(i, 1)
      else lista.push(valor)
      this.form.parametros.categorias = lista
    },

    adicionarCategoria (c) {
      if (this.form.categoriasSel.some(x => x.id === c.id)) { toast.info('Já está na lista.'); return }
      this.form.categoriasSel.push({ id: c.id, nome: c.nome, loja: c.loja, loja_ativa: c.loja_ativa })
    },

    moverCategoria (k, d) {
      const j = k + d
      const l = this.form.categoriasSel
      if (j < 0 || j >= l.length) return
      ;[l[k], l[j]] = [l[j], l[k]]
    },

    async carregarImagem (it, e) {
      const ficheiro = e.target.files?.[0]
      e.target.value = ''
      if (!ficheiro) return
      if (ficheiro.size > 5 * 1024 * 1024) { toast.error('A imagem tem de ter no máximo 5 MB.'); return }
      it._aCarregar = true
      try {
        const fd = new FormData()
        fd.append('ficheiro', ficheiro)
        const { data } = await api.post('/app/admin/home/imagens/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        it.imagem_id = data.id
        it.imagem_url = data.url
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Não foi possível carregar a imagem.')
      } finally { it._aCarregar = false }
    },

    nomeItem (it) {
      if (it.loja_id) return it.loja?.nome || `Loja #${it.loja_id}`
      if (it.produto_id) return it.produto ? `${it.produto.nome} — ${it.produto.loja}` : `Produto #${it.produto_id}`
      return it.titulo || (it.imagem_id ? 'Banner com imagem' : 'Banner sem título')
    },

    avisoItem (it) {
      if (it.loja && !it.loja.ativa) return `Loja ${it.loja.estado}: não aparece na home.`
      if (it.produto && (!it.produto.ativo || !it.produto.loja_ativa)) return 'Produto escondido ou loja não activa: não aparece.'
      return ''
    },

    async publicar () {
      if (!confirm('Publicar o rascunho? A home muda para todos os visitantes (até 1 minuto).')) return
      this.aGuardar = true
      try {
        const { data } = await api.post('/app/admin/home/publicar/')
        this.aplicar(data)
        toast.success('Home publicada.')
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível publicar.')
      } finally { this.aGuardar = false }
    },

    async descartar () {
      if (!confirm('Descartar todas as alterações e voltar ao que está publicado?')) return
      await this.acaoRascunho('/app/admin/home/descartar/', 'Rascunho reposto.')
    },

    async reporPadrao () {
      if (!confirm('Substituir o rascunho pelo layout original da home? (Só muda a home quando publicares.)')) return
      await this.acaoRascunho('/app/admin/home/padrao/', 'Layout original carregado no rascunho.')
    },

    async restaurar (p) {
      if (!confirm('Carregar esta publicação no rascunho? O rascunho actual é substituído.')) return
      await this.acaoRascunho(`/app/admin/home/publicacoes/${p.id}/restaurar/`, 'Versão carregada no rascunho.')
      this.historicoAberto = false
    },

    async acaoRascunho (url, msg) {
      this.aGuardar = true
      try {
        const { data } = await api.post(url)
        this.aplicar(data)
        this.selecionar(this.seccoes[0]?.id, true)
        toast.success(msg)
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Não foi possível.')
      } finally { this.aGuardar = false }
    },

    async carregarHistorico () {
      try {
        const { data } = await api.get('/app/admin/home/publicacoes/')
        this.historico = data
      } catch (e) { this.historico = [] }
    },

    abrirPreview () {
      if (this.formSujo) toast.info('A pré-visualização mostra o rascunho guardado: guarda a secção para a ver.')
      window.open('/?preview=1', '_blank', 'noopener')
    },
  },
}
</script>

