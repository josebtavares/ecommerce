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
        <!-- a landing page (/sobre) edita-se na própria página (views/Sobre.vue) -->
        <router-link :to="{ path: '/sobre', query: { editar: 1 } }" data-teste="editar-landing"
          class="px-3 py-2 rounded-xl border border-zinc-700 bg-zinc-900 text-xs font-semibold text-zinc-300 hover:border-zinc-500 transition flex items-center gap-1.5">
          <font-awesome-icon :icon="['fas', 'pen-to-square']" /> Editar a landing page
        </router-link>
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

          <p v-if="form.tipo === 'servicos'" class="text-[11px] text-zinc-500" data-teste="home-servicos">
            Só aparecem serviços de lojas com marcações abertas; sem nenhum, a secção não aparece. Cada cartão abre a loja com o serviço pronto a marcar.
          </p>

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

          <!-- publicidade: formato, anúncios e pré-visualização -->
          <template v-if="form.tipo === 'publicidade'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3" data-teste="pub-formato">
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Proporção no computador</label>
                <select v-model="form.parametros.proporcao" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" data-teste="pub-proporcao">
                  <option value="auto">Automática ({{ formatoProporcao(previa.auto.computador) }})</option>
                  <option v-for="k in pubConf.proporcoes" :key="k" :value="k">{{ k }}</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Proporção no telemóvel</label>
                <select v-model="form.parametros.proporcao_movel" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" data-teste="pub-proporcao-movel">
                  <option value="auto">Automática ({{ formatoProporcao(previa.auto.telemovel) }})</option>
                  <option v-for="k in pubConf.proporcoes" :key="k" :value="k">{{ k }}</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-zinc-400 font-medium mb-1.5 block">Muda de anúncio a cada (s)</label>
                <input v-model.number="form.parametros.intervalo" type="number" min="3" max="30" class="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500"
                       :placeholder="String(pubConf.intervalo)" data-teste="pub-intervalo" />
              </div>
            </div>
            <p class="text-[10px] text-zinc-600 -mt-3">
              Automática = o formato mais comum entre os anúncios; fica igual enquanto a página está aberta (nada salta ao mudar de anúncio).
              Anúncios com outro formato aparecem inteiros, com margens desfocadas. Os vídeos passam ao seguinte quando acabam.
            </p>

            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="text-xs text-zinc-400 font-medium block">Anúncios ({{ form.itens.length }})</label>
                <span class="text-[10px] text-zinc-600">máx. {{ pubConf.max_anuncios }} · imagem até {{ pubConf.imagem_max_mb }} MB · vídeo até {{ pubConf.video_max_s }} s e {{ pubConf.video_max_mb }} MB</span>
              </div>
              <div class="space-y-2">
                <div v-for="(it, k) in form.itens" :key="it._k" class="bg-zinc-800/70 border border-zinc-700 rounded-xl p-3 space-y-3"
                     :data-teste="'pub-item-' + k">
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-bold text-zinc-500 w-5">{{ k + 1 }}.</span>
                    <p class="flex-1 min-w-0 text-sm text-zinc-100 truncate">{{ it.titulo || it.anunciante || 'Anúncio sem título' }}</p>
                    <span class="text-[10px] px-1.5 py-0.5 rounded font-bold" :class="ESTADO_ANUNCIO[estadoAnuncio(it)].cor"
                          :data-teste="'pub-item-estado-' + k">{{ ESTADO_ANUNCIO[estadoAnuncio(it)].n }}</span>
                    <button @click="moverItem(k, -1)" :disabled="k === 0" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Subir"><font-awesome-icon :icon="['fas', 'chevron-up']" /></button>
                    <button @click="moverItem(k, 1)" :disabled="k === form.itens.length - 1" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Descer"><font-awesome-icon :icon="['fas', 'chevron-down']" /></button>
                    <button @click="form.itens.splice(k, 1)" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-red-400 transition" aria-label="Remover anúncio"><font-awesome-icon :icon="['fas', 'xmark']" /></button>
                  </div>

                  <!-- estatísticas dos últimos 30 dias (só anúncios já guardados) -->
                  <p v-if="it.chave" class="text-[11px] text-zinc-500 flex flex-wrap items-center gap-x-2 -mt-1" :data-teste="'pub-item-estat-' + k">
                    <font-awesome-icon :icon="['fas', 'chart-simple']" class="text-zinc-600" />
                    <template v-if="estatAnuncio(it)">
                      <span>{{ selecionada?.estatisticas?.dias || 30 }} dias: <b class="text-zinc-300 font-semibold">{{ estatAnuncio(it).impressoes.toLocaleString('pt-PT') }}</b> impressões
                        · <b class="text-zinc-300 font-semibold">{{ estatAnuncio(it).cliques.toLocaleString('pt-PT') }}</b> cliques
                        <template v-if="estatAnuncio(it).ctr != null"> · {{ estatAnuncio(it).ctr.toLocaleString('pt-PT') }}%</template></span>
                    </template>
                    <span v-else>Ainda sem impressões nos últimos 30 dias.</span>
                    <router-link v-if="podeVerEstatisticas" to="/admin/estatisticas?aba=publicidade" class="text-red-400 hover:text-red-300" data-teste="pub-item-estat-link">Ver estatísticas →</router-link>
                  </p>

                  <!-- media principal + versão para telemóvel -->
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div v-for="sl in SLOTS_MEDIA" :key="sl.campo" class="flex items-start gap-3" :data-teste="`pub-item-${k}-${sl.campo}`">
                      <div class="w-28 h-16 rounded-lg border border-zinc-700 bg-zinc-900 overflow-hidden flex items-center justify-center flex-shrink-0">
                        <img v-if="miniatura(it[sl.campo])" :src="miniatura(it[sl.campo])" alt="" class="w-full h-full object-contain" />
                        <font-awesome-icon v-else :icon="['fas', it[sl.campo]?.tipo === 'video' ? 'film' : sl.icone]" class="text-zinc-600" />
                      </div>
                      <div class="min-w-0 flex-1">
                        <p class="text-xs text-zinc-300 font-medium">{{ sl.n }}<span v-if="sl.opcional" class="text-zinc-600 font-normal"> (opcional)</span></p>
                        <p v-if="it[sl.campo]" class="text-[11px] text-zinc-500">
                          {{ it[sl.campo].tipo === 'video' ? 'Vídeo' : 'Imagem' }}<template v-if="it[sl.campo].largura"> · {{ it[sl.campo].largura }}×{{ it[sl.campo].altura }} · {{ formatoProporcao(it[sl.campo].largura / it[sl.campo].altura) }}</template>
                          <template v-if="it[sl.campo].tipo === 'video'"> · {{ Math.round(it[sl.campo].duracao || 0) }} s
                            · <span :class="ESTADO_VIDEO[it[sl.campo].estado]?.cor" :data-teste="`pub-item-${k}-${sl.campo}-estado`">{{ ESTADO_VIDEO[it[sl.campo].estado]?.n || it[sl.campo].estado }}</span></template>
                        </p>
                        <p v-else-if="sl.opcional" class="text-[11px] text-zinc-600">{{ sl.dica }}</p>
                        <p v-if="avisoMedia(it, sl.campo)" class="text-[11px] text-amber-400/90 mt-0.5" :data-teste="`pub-item-${k}-${sl.campo}-aviso`">{{ avisoMedia(it, sl.campo) }}</p>
                        <div class="flex items-center gap-3 mt-1.5">
                          <label class="px-2.5 py-1 rounded-lg border border-zinc-700 text-[11px] font-semibold text-zinc-300 hover:border-zinc-500 cursor-pointer">
                            {{ it['_aCarregar_' + sl.campo] ? 'A carregar…' : it[sl.campo] ? 'Trocar' : 'Carregar imagem ou vídeo' }}
                            <input type="file" accept="image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime,.mov" class="hidden"
                                   :disabled="it['_aCarregar_' + sl.campo]" :data-teste="`pub-item-${k}-${sl.campo}-ficheiro`"
                                   @change="e => carregarMedia(it, sl, e)" />
                          </label>
                          <button v-if="it[sl.campo]" type="button" @click="it[sl.campo] = null; it[sl.id] = null"
                            class="text-[11px] text-zinc-500 hover:text-red-400">Remover</button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <input v-model="it.titulo" maxlength="120" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="Título (opcional)" :data-teste="`pub-item-${k}-titulo`" />
                    <input v-model="it.texto" maxlength="300" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="Texto (opcional)" />
                    <input v-model="it.link" maxlength="300" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="Link: /loja/12 ou https://…" :data-teste="`pub-item-${k}-link`" />
                    <input v-model="it.botao" maxlength="40" class="w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" :disabled="!it.link"
                           :placeholder="it.link ? 'Texto do botão (Saber mais)' : 'Sem link: sem botão'" :data-teste="`pub-item-${k}-botao`" />
                    <input v-model="it.anunciante" maxlength="80" class="sm:col-span-2 w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" placeholder="Anunciante (aparece em &quot;Publicidade · …&quot;)" :data-teste="`pub-item-${k}-anunciante`" />
                    <div class="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <label class="block text-[11px] text-zinc-500">Mostrar a partir de <span class="text-zinc-600">(vazio = já)</span>
                      <input v-model="it.inicio" type="datetime-local" class="mt-1 w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" title="Mostrar a partir de" :data-teste="`pub-item-${k}-inicio`" /></label>
                      <label class="block text-[11px] text-zinc-500">Mostrar até <span class="text-zinc-600">(vazio = sempre)</span>
                      <input v-model="it.fim" type="datetime-local" class="mt-1 w-full px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-500" title="Mostrar até" :data-teste="`pub-item-${k}-fim`" /></label>
                    </div>
                  </div>
                  <p v-if="it.link && /^https?:/i.test(it.link)" class="text-[10px] text-zinc-600 -mt-1">Link externo: abre num separador novo e fica marcado como patrocinado para os motores de busca.</p>
                </div>
              </div>
              <button v-if="form.itens.length < pubConf.max_anuncios" type="button" @click="novoAnuncio" data-teste="pub-adicionar"
                class="mt-2 w-full px-3 py-2 rounded-xl border border-dashed border-zinc-700 text-xs font-semibold text-zinc-300 hover:border-zinc-500">
                + Adicionar anúncio
              </button>
            </div>

            <p v-if="previa.formatosDiferentes" class="text-[11px] text-amber-400/90 px-3 py-2 bg-amber-500/5 border border-amber-500/20 rounded-xl" data-teste="pub-aviso-formatos">
              Os anúncios têm formatos muito diferentes: alguns vão aparecer pequenos, com margens desfocadas grandes.
              Para ficar melhor, usa imagens do mesmo formato ou carrega versões para telemóvel.
            </p>

            <Previa :anuncios="previa.anuncios" :proporcao="previa.proporcao" :fixa="previa.fixa"
                    :intervalo="previa.intervalo" :titulo="form.titulo" :subtitulo="form.subtitulo" :vazio="previa.vazio" />
          </template>

          <!-- itens escolhidos -->
          <div v-if="aceitaItens && form.tipo !== 'publicidade'">
            <div class="flex items-center justify-between mb-2">
              <label class="text-xs text-zinc-400 font-medium block">
                {{ form.fonte === 'misto' ? 'Fixados no início' : 'Escolhidos' }} ({{ form.itens.length }})
              </label>
              <span class="text-[10px] text-zinc-600">máx. {{ MAX_ITENS }}</span>
            </div>
            <div class="space-y-2">
              <div v-for="(it, k) in form.itens" :key="it._k" class="bg-zinc-800 border border-zinc-700 rounded-xl p-2.5">
                <div class="flex items-center gap-2">
                  <font-awesome-icon :icon="['fas', it.loja_id ? 'store' : it.produto_id ? 'box' : it.servico_id ? 'calendar-check' : 'image']" class="text-zinc-500 w-3.5" />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm text-zinc-100 truncate">{{ nomeItem(it) }}</p>
                    <p v-if="avisoItem(it)" class="text-[11px] text-amber-400">{{ avisoItem(it) }}</p>
                  </div>
                  <button @click="moverItem(k, -1)" :disabled="k === 0" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Subir"><font-awesome-icon :icon="['fas', 'chevron-up']" /></button>
                  <button @click="moverItem(k, 1)" :disabled="k === form.itens.length - 1" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-200 disabled:opacity-20 transition" aria-label="Descer"><font-awesome-icon :icon="['fas', 'chevron-down']" /></button>
                  <button @click="form.itens.splice(k, 1)" class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-red-400 disabled:opacity-20 transition" aria-label="Remover"><font-awesome-icon :icon="['fas', 'xmark']" /></button>
                </div>
                <div v-if="form.tipo === 'hero' || !it.loja_id && !it.produto_id && !it.servico_id" class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
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
                @escolher="x => adicionarItem(generoNovo === 'loja' ? { loja_id: x.id, loja: x } : generoNovo === 'servico' ? { servico_id: x.id, servico: x } : { produto_id: x.id, produto: x })" />
            </div>
          </div>

          <!-- limite + datas -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div v-if="form.tipo !== 'cabecalho'">
              <label class="text-xs text-zinc-400 font-medium mb-1.5 block">{{ form.tipo === 'publicidade' ? 'Máximo de anúncios' : form.tipo === 'hero' ? 'Máximo de slides' : GRUPOS.includes(form.tipo) ? 'Máximo por slider' : 'Máximo de itens' }}</label>
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
import Previa, { formatoProporcao } from '@/components/admin/HomePublicidadePreview.vue'

const ICONES = {
  servicos: 'calendar-check',
  hero: 'panorama', lojas: 'store', produtos: 'box', loja_destaque: 'star', categorias: 'table-cells',
  banner: 'image', cabecalho: 'heading', lojas_por_categoria: 'layer-group', produtos_por_tipo: 'shapes',
  produtos_categorias_destaque: 'fire', publicidade: 'rectangle-ad',
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
  servicos: 'Slider de serviços (marcações): escolhidos ou por critério (novos, mais marcados, de uma loja).',
  publicidade: 'Carrossel de anúncios (imagem ou vídeo, link e botão) que passa sozinho; o tamanho adapta-se aos anúncios.',
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
const TEM_FONTE = ['hero', 'lojas', 'produtos', 'servicos']
const GRUPOS = ['lojas_por_categoria', 'produtos_por_tipo', 'produtos_categorias_destaque']
const ITENS_POR_TIPO = { hero: ['loja', 'produto', 'banner'], lojas: ['loja'], produtos: ['produto'], loja_destaque: ['produto'], banner: ['banner'],
  servicos: ['servico'], publicidade: ['anuncio'] }
const NOVA = {
  hero: { fonte: 'auto', criterio: 'novas' },
  lojas: { titulo: 'Lojas populares', fonte: 'auto', criterio: 'populares' },
  produtos: { titulo: 'Novidades', fonte: 'auto', criterio: 'novos' },
  cabecalho: { titulo: 'Nova secção', parametros: { estilo_titulo: 'titulo' } },
  lojas_por_categoria: {}, produtos_por_tipo: {}, produtos_categorias_destaque: {},
  loja_destaque: {}, categorias: {}, banner: { fonte: 'manual' },
  servicos: { titulo: 'Marca um serviço', fonte: 'auto', criterio: 'novos' },
  publicidade: { fonte: 'manual' },
}
const PUB_PADRAO = { proporcoes: ['21:9', '3:1', '2:1', '16:9', '4:3', '1:1', '4:5', '9:16'],
  limites: { computador: [1.5, 4.0], telemovel: [0.6, 2.4] }, sem_medidas: 1.7778, intervalo: 6, max_anuncios: 20,
  video_max_mb: 25, video_max_s: 30, imagem_max_mb: 20 }
const SLOTS_MEDIA = [
  { campo: 'media', id: 'imagem_id', n: 'Imagem ou vídeo', icone: 'image', opcional: false },
  { campo: 'media_movel', id: 'imagem_movel_id', n: 'Versão para telemóvel', icone: 'mobile-screen', opcional: true,
    dica: 'Sem ela, o telemóvel mostra a mesma. Útil para uma imagem vertical.' },
]
const ESTADO_VIDEO = {
  pendente: { n: 'na fila para preparar…', cor: 'text-amber-400' },
  a_processar: { n: 'a preparar…', cor: 'text-amber-400' },
  pronto: { n: 'pronto', cor: 'text-green-400' },
  erro: { n: 'não se conseguiu preparar — carrega outro', cor: 'text-red-400' },
}
const ESTADO_ANUNCIO = {
  ativo: { n: 'ACTIVO', cor: 'bg-green-500/10 text-green-400' },
  agendado: { n: 'AGENDADO', cor: 'bg-amber-500/10 text-amber-400' },
  terminado: { n: 'TERMINADO', cor: 'bg-zinc-700/60 text-zinc-400' },
  sem_media: { n: 'SEM IMAGEM', cor: 'bg-red-500/10 text-red-400' },
}
const VIDEO_EXT = /\.(mp4|webm|mov)$/i
const SEGUIR_VIDEO_MS = 3000

// proporção como o servidor (utils/home.py proporcao): fixa, ou a mediana dos anúncios dentro dos limites
function calcProporcao (conf, escolha, medias, onde) {
  if (escolha && escolha !== 'auto' && escolha.includes(':')) {
    const [a, b] = escolha.split(':').map(Number)
    if (a && b) return a / b
  }
  const rs = medias.filter(m => m?.largura && m?.altura).map(m => m.largura / m.altura).sort((x, y) => x - y)
  const r = rs.length ? rs[Math.floor(rs.length / 2)] : conf.sem_medidas
  const [mn, mx] = conf.limites[onde]
  return Math.min(Math.max(r, mn), mx)
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
  components: { Procurar, Previa },
  props: {
    podeVerEstatisticas: { type: Boolean, default: false },
  },

  data () {
    return {
      ICONES, DESCRICAO_TIPO, DESCRICAO_FONTE, DESCRICAO_GRUPO, TEM_FONTE, GRUPOS, MAX_SECCOES, MAX_ITENS,
      SLOTS_MEDIA, ESTADO_VIDEO, ESTADO_ANUNCIO,
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
    criteriosDoTipo () {
      if (this.form?.tipo === 'servicos') return this.opcoes.criterios_servicos
      return this.eLojas ? this.opcoes.criterios_lojas : this.opcoes.criterios_produtos
    },
    generosItens () { return this.form ? (ITENS_POR_TIPO[this.form.tipo] || []) : [] },
    aceitaItens () {
      if (!this.form || !this.generosItens.length) return false
      if (this.form.tipo === 'loja_destaque') return !!this.form.parametros.loja_id
      return !TEM_FONTE.includes(this.form.tipo) || this.form.fonte !== 'auto'
    },
    limiteMax () {
      if (this.form?.tipo === 'publicidade') return this.pubConf.max_anuncios
      return ['hero', 'loja_destaque'].includes(this.form?.tipo) ? 20 : (this.opcoes.limite_max || 100)
    },
    pubConf () { return { ...PUB_PADRAO, ...(this.opcoes.publicidade || {}) } },
    // o que a home mostraria agora com este formulário (mesmas regras do servidor: _resolver_publicidade)
    previa () {
      const conf = this.pubConf
      const vazio = { anuncios: [], proporcao: { computador: conf.sem_medidas, telemovel: conf.sem_medidas }, fixa: {},
                      auto: { computador: conf.sem_medidas, telemovel: conf.sem_medidas }, intervalo: conf.intervalo,
                      formatosDiferentes: false, vazio: '' }
      if (this.form?.tipo !== 'publicidade') return vazio
      const f = this.form
      const p = f.parametros
      const limite = Math.min(Math.max(Number(f.limite) || 10, 1), conf.max_anuncios)
      const mostraveis = f.itens.filter(i => this.mostravel(i.media))
      const anuncios = mostraveis.filter(i => this.estadoAnuncio(i) === 'ativo').slice(0, limite).map(i => {
        const link = (i.link || '').trim()
        return {
          chave: i.chave || `novo${i._k}`, titulo: i.titulo || '', texto: i.texto || '', link,
          externo: /^https?:\/\//i.test(link), botao: (i.botao || '').trim() || (link ? 'Saber mais' : ''),
          anunciante: i.anunciante || '', media: this.mediaPublica(i.media),
          media_movel: this.mostravel(i.media_movel) ? this.mediaPublica(i.media_movel) : null,
        }
      })
      const auto = {
        computador: calcProporcao(conf, 'auto', anuncios.map(a => a.media), 'computador'),
        telemovel: calcProporcao(conf, 'auto', anuncios.map(a => a.media_movel || a.media), 'telemovel'),
      }
      const proporcao = {
        computador: calcProporcao(conf, p.proporcao, anuncios.map(a => a.media), 'computador'),
        telemovel: calcProporcao(conf, p.proporcao_movel, anuncios.map(a => a.media_movel || a.media), 'telemovel'),
      }
      const rs = anuncios.map(a => a.media).filter(m => m.largura && m.altura).map(m => m.largura / m.altura)
      const intervalo = Number(p.intervalo) >= 3 && Number(p.intervalo) <= 30 ? Number(p.intervalo) : conf.intervalo
      let msg = ''
      if (!anuncios.length) {
        msg = !f.itens.length ? 'Adiciona um anúncio para ver a pré-visualização.'
          : mostraveis.length ? 'Nenhum anúncio activo agora (vê as datas): a secção não aparece na home.'
            : 'Carrega uma imagem ou um vídeo para ver a pré-visualização.'
      }
      return {
        anuncios, proporcao, auto, intervalo, vazio: msg,
        fixa: { computador: !!p.proporcao && p.proporcao !== 'auto', telemovel: !!p.proporcao_movel && p.proporcao_movel !== 'auto' },
        formatosDiferentes: rs.length > 1 && Math.max(...rs) / Math.min(...rs) > 2.2,
      }
    },
    tiposDisponiveis () { return this.opcoes.tipos },
    placeholderTitulo () {
      return { lojas_por_categoria: 'Sem título: só os sliders', produtos_por_tipo: 'Ex.: Produtos', cabecalho: 'Ex.: Produtos' }[this.form?.tipo] || ''
    },
  },

  async created () {
    await this.carregar()
  },
  mounted () { window.addEventListener('beforeunload', this.avisoSair) },
  beforeUnmount () {
    window.removeEventListener('beforeunload', this.avisoSair)
    this.fechado = true
    Object.values(this.seguidos || {}).forEach(clearTimeout)
  },

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
      } else if (s.tipo === 'publicidade') {
        partes.push(s.itens.length === 1 ? '1 anúncio' : `${s.itens.length} anúncios`)
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
        itens: s.itens.map(i => ({ ...i, inicio: paraLocal(i.inicio), fim: paraLocal(i.fim), _k: ++uid })),
        categoriasSel: (s.parametros?.categoria_ids || []).map(id => s.refs?.categorias?.[id] || { id, nome: `Categoria #${id}`, loja: '' }),
        destaqueAuto: s.tipo === 'loja_destaque' && !s.parametros?.loja_id && !!s.criterio,
      }
      if (s.tipo === 'publicidade') {
        this.form.parametros = { proporcao: 'auto', proporcao_movel: 'auto', ...this.form.parametros }
        this.form.itens.forEach(i => { ['media', 'media_movel'].forEach(c => { if (this.aPreparar(i[c])) this.seguirVideo(i[c]) }) })
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
      if (f.tipo === 'publicidade') {
        if (p.proporcao && p.proporcao !== 'auto') out.proporcao = p.proporcao
        if (p.proporcao_movel && p.proporcao_movel !== 'auto') out.proporcao_movel = p.proporcao_movel
        por('intervalo', p.intervalo)
      }
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
        criterio: (TEM_FONTE.includes(f.tipo) && f.fonte !== 'manual') || (f.tipo === 'loja_destaque' && f.destaqueAuto) ? (f.criterio || '') : '',
        limite: f.limite, parametros: this.parametrosLimpos(),
        itens: comItens ? f.itens.map(i => ({ loja_id: i.loja_id || null, produto_id: i.produto_id || null, servico_id: i.servico_id || null,
                                               imagem_id: i.imagem_id || null,
                                               titulo: i.titulo || '', texto: i.texto || '', link: i.link || '',
                                               ...(f.tipo === 'publicidade' ? {
                                                 imagem_movel_id: i.imagem_movel_id || null, chave: i.chave || '',
                                                 botao: i.botao || '', anunciante: i.anunciante || '',
                                                 inicio: paraIso(i.inicio), fim: paraIso(i.fim) } : {}) })) : [],
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
                       (dados.produto_id && this.form.itens.some(i => i.produto_id === dados.produto_id)) ||
                       (dados.servico_id && this.form.itens.some(i => i.servico_id === dados.servico_id))
      if (repetido) { toast.info('Já está na lista.'); return }
      this.form.itens.push({ loja_id: null, produto_id: null, servico_id: null, imagem_id: null, imagem_url: '', titulo: '', texto: '', link: '', ...dados, _k: ++uid })
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
      if (ficheiro.size > 20 * 1024 * 1024) { toast.error('A imagem tem de ter no máximo 20 MB.'); return }
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

    // ── publicidade ──
    formatoProporcao,
    novoAnuncio () {
      this.form.itens.push({ loja_id: null, produto_id: null, servico_id: null, imagem_id: null, imagem_movel_id: null,
        media: null, media_movel: null, chave: '', titulo: '', texto: '', link: '', botao: '', anunciante: '',
        inicio: '', fim: '', _k: ++uid })
    },
    estatAnuncio (it) { return this.selecionada?.estatisticas?.por_chave?.[it.chave] || null },
    estadoAnuncio (it) {
      if (!it.imagem_id) return 'sem_media'
      const agora = Date.now()
      if (it.fim && new Date(it.fim).getTime() <= agora) return 'terminado'
      if (it.inicio && new Date(it.inicio).getTime() > agora) return 'agendado'
      return 'ativo'
    },
    aPreparar (m) { return m?.tipo === 'video' && ['pendente', 'a_processar'].includes(m.estado) },
    // como o servidor (_media): um vídeo .mov ainda por converter não se mostra (os browsers não o tocam)
    mostravel (m) {
      if (!m?.url) return false
      if (m.tipo !== 'video' || m.estado === 'pronto') return true
      return /\.(mp4|webm)$/i.test(m.url.split('?')[0])
    },
    mediaPublica (m) {
      return { tipo: m.tipo, url: m.url, largura: m.largura, altura: m.altura, poster: m.poster || null, duracao: m.duracao || null }
    },
    miniatura (m) { return m ? (m.tipo === 'video' ? m.poster : m.url) : null },
    avisoMedia (it, campo) {
      const m = it[campo]
      if (!m?.largura || !m?.altura || this.estadoAnuncio(it) !== 'ativo') return ''
      const r = m.largura / m.altura
      const onde = campo === 'media_movel' ? 'telemovel' : 'computador'
      const sec = this.previa.proporcao[onde]
      const dif = Math.max(r / sec, sec / r)
      if (dif > 1.15) return `Formato diferente da secção (${formatoProporcao(sec)}): aparece inteiro, com margens desfocadas.`
      if (campo === 'media' && !it.media_movel && r >= 2.2) return 'Muito larga: no telemóvel fica pequena — considera uma versão para telemóvel.'
      return ''
    },
    async carregarMedia (it, sl, e) {
      const ficheiro = e.target.files?.[0]
      e.target.value = ''
      if (!ficheiro) return
      const conf = this.pubConf
      const eVideo = ficheiro.type.startsWith('video/') || VIDEO_EXT.test(ficheiro.name)
      const maxMb = eVideo ? conf.video_max_mb : conf.imagem_max_mb
      if (ficheiro.size > maxMb * 1024 * 1024) {
        toast.error(`${eVideo ? 'O vídeo' : 'A imagem'} tem de ter no máximo ${maxMb} MB.`)
        return
      }
      const chave = '_aCarregar_' + sl.campo
      it[chave] = true
      try {
        const fd = new FormData()
        fd.append('ficheiro', ficheiro)
        fd.append('video', '1')
        const { data } = await api.post('/app/admin/home/imagens/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        it[sl.campo] = data
        it[sl.id] = data.id
        if (this.aPreparar(it[sl.campo])) this.seguirVideo(it[sl.campo])
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Não foi possível carregar o ficheiro.')
      } finally { it[chave] = false }
    },
    // vídeo novo: o worker converte-o; vai perguntando até ficar pronto (ou dar erro)
    seguirVideo (m) {
      this.seguidos = this.seguidos || {}
      if (!m?.id || this.seguidos[m.id] || this.fechado) return
      const passo = async () => {
        if (this.fechado) return
        try {
          const { data } = await api.get(`/app/admin/home/imagens/${m.id}/`)
          Object.assign(m, data)
        } catch (e) { /* tenta outra vez */ }
        if (this.aPreparar(m) && !this.fechado) this.seguidos[m.id] = setTimeout(passo, SEGUIR_VIDEO_MS)
        else delete this.seguidos[m.id]
      }
      this.seguidos[m.id] = setTimeout(passo, SEGUIR_VIDEO_MS)
    },

    nomeItem (it) {
      if (it.loja_id) return it.loja?.nome || `Loja #${it.loja_id}`
      if (it.produto_id) return it.produto ? `${it.produto.nome} — ${it.produto.loja}` : `Produto #${it.produto_id}`
      if (it.servico_id) return it.servico ? `${it.servico.nome} — ${it.servico.loja}` : `Serviço #${it.servico_id}`
      return it.titulo || (it.imagem_id ? 'Banner com imagem' : 'Banner sem título')
    },

    avisoItem (it) {
      if (it.loja && !it.loja.ativa) return `Loja ${it.loja.estado}: não aparece na home.`
      if (it.produto && (!it.produto.ativo || !it.produto.loja_ativa)) return 'Produto escondido ou loja não activa: não aparece.'
      if (it.servico && (!it.servico.ativo || !it.servico.loja_ativa)) return 'Serviço inactivo ou loja não activa: não aparece.'
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

