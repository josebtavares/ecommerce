<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-black text-slate-950">Produtos POS</h2>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          Gere produtos próprios do POS e produtos da loja Bendi.
        </p>
      </div>

      <div v-if="podeGerirProdutos" class="flex gap-2">
        <button
          v-if="podeCriarProdutoPOS"
          type="button"
          @click="showTiposModal = true"
          class="inline-flex h-11 items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 text-sm font-black text-slate-700 transition hover:bg-slate-50"
        >
          <font-awesome-icon :icon="['fas', 'tags']" class="mr-1.5" />Tipos
        </button>
        <button
          type="button"
          @click="abrirModalCriar"
          class="inline-flex h-11 items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
        >
          + Novo produto
        </button>
      </div>
    </div>

    <TiposModal v-if="showTiposModal" :pos-id="posId" @close="showTiposModal = false" @alterado="carregarProdutos" />

    <!-- Info modo -->
    <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-sm font-black text-slate-950">Modo atual: {{ modoLabel }}</p>
          <p class="mt-1 text-xs font-semibold text-slate-500">
            <span v-if="modo === 'standalone'">Este POS usa apenas produtos próprios.</span>
            <span v-else-if="modo === 'integrado'">Este POS usa apenas produtos da loja Bendi vinculada.</span>
            <span v-else-if="modo === 'hibrido'">Este POS usa produtos próprios e produtos da loja Bendi.</span>
            <span v-else>A carregar configuração do POS...</span>
          </p>
        </div>

        <div
          v-if="lojaVinculada"
          class="rounded-2xl bg-blue-50 px-4 py-2 text-sm font-black text-blue-700"
        >
          Loja: {{ lojaVinculada.nome }}
        </div>
        <div
          v-else
          class="rounded-2xl bg-amber-50 px-4 py-2 text-sm font-black text-amber-700"
        >
          Sem loja vinculada
        </div>
      </div>
    </section>

    <!-- Alertas -->
    <div
      v-if="error"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
    >
      {{ error }}
    </div>

    <div
      v-if="success"
      class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
    >
      {{ success }}
    </div>

    <!-- Filtros -->
    <section class="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-[1fr_180px_180px_180px]">
        <input
          v-model.trim="searchQuery"
          type="text"
          placeholder="Pesquisar por nome, categoria ou descrição..."
          class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        />

        <select
          v-model="origemFiltro"
          class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        >
          <option value="">Todas origens</option>
          <option value="pos">Produtos POS</option>
          <option value="loja">Loja Bendi</option>
        </select>

        <select
          v-model="categoriaFiltro"
          class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        >
          <option value="">Todas categorias</option>
          <option v-for="cat in categorias" :key="cat" :value="cat">{{ cat }}</option>
        </select>

        <select
          v-model="ativoFiltro"
          class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
        >
          <option value="">Todos</option>
          <option value="true">Ativos</option>
          <option value="false">Inativos</option>
        </select>
      </div>
    </section>

    <!-- Loading -->
    <div
      v-if="loading && produtos.length === 0"
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5"
    >
      <div v-for="i in 10" :key="i" class="h-64 animate-pulse rounded-[1.5rem] bg-slate-100"></div>
    </div>

    <!-- Empty -->
    <section
      v-else-if="produtosFiltrados.length === 0"
      class="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-10 text-center"
    >
      <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl text-slate-400 shadow-sm"><font-awesome-icon :icon="['fas', 'box']" /></div>
      <h3 class="mt-5 text-xl font-black text-slate-950">Nenhum produto encontrado</h3>
      <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
        <span v-if="podeGerirProdutos">
          Cria produtos próprios do POS ou liga o POS a uma loja Bendi para importar o catálogo.
        </span>
        <span v-else>
          Ainda não existem produtos disponíveis neste POS.
        </span>
      </p>

      <button
        v-if="podeGerirProdutos"
        type="button"
        @click="abrirModalCriar"
        class="mt-6 inline-flex h-11 items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-800"
      >
        Criar produto
      </button>
    </section>

    <!-- Grid -->
    <section
      v-else
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5"
    >
      <article
        v-for="produto in produtosFiltrados"
        :key="produto.uid || `${produto.origem}-${produto.id}`"
        class="group overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl"
      >
        <div class="relative aspect-square bg-slate-100">
          <img
            v-if="produto.imagem_url"
            :src="produto.imagem_url"
            :alt="produto.nome"
            class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
          />
          <div v-else class="flex h-full w-full items-center justify-center text-4xl text-slate-300"><font-awesome-icon :icon="['fas', 'box']" /></div>

          <!-- direita livre para o selo Ativo/Inativo -->
          <div class="absolute left-2 right-20 top-2 flex flex-wrap gap-1">
            <span
              :class="[
                'rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide',
                produto.origem === 'pos' ? 'bg-purple-600 text-white' : 'bg-blue-600 text-white'
              ]"
            >
              {{ produto.origem === 'pos' ? 'POS' : 'Loja' }}
            </span>

            <span
              v-if="produto.e_conjunto"
              class="rounded-full bg-sky-600 px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-white"
            >
              <font-awesome-icon :icon="['fas', 'layer-group']" /> Menu
            </span>

            <span
              v-if="produto.disponivel === false"
              class="rounded-full bg-amber-500 px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-white"
            >
              Indisp.
            </span>
          </div>

          <div
            :class="[
              'absolute right-2 top-2 rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide',
              produtoAtivo(produto) ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
            ]"
          >
            {{ produtoAtivo(produto) ? 'Ativo' : 'Inativo' }}
          </div>
        </div>

        <div class="p-4">
          <h3 class="line-clamp-2 min-h-[40px] text-sm font-black text-slate-950">
            {{ produto.nome }}
          </h3>

          <p class="mt-1 truncate text-xs font-semibold text-slate-500">
            {{ produto.categoria || 'Sem categoria' }}
          </p>

          <div class="mt-3 flex items-center justify-between gap-2">
            <span class="text-lg font-black text-slate-950">{{ money(produto.preco) }}</span>
            <span class="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-black text-slate-500">
              Stock: {{ produto.stock ?? '—' }}
            </span>
          </div>

          <!-- menu: o que leva; indisponível → motivo e "Corrigir menu" -->
          <template v-if="produto.e_conjunto">
            <p class="mt-2 line-clamp-2 text-[11px] font-semibold text-slate-500">
              {{ produto.componentes.map(c => c.quantidade + '× ' + c.nome).join(', ') }}
            </p>
            <p v-if="produto.grupos?.length" class="mt-1 text-[11px] font-bold text-sky-700">
              Escolhe: {{ produto.grupos.map(g => g.nome).join(', ') }}
            </p>
            <p v-if="produto.conjunto?.motivo" class="mt-2 rounded-lg bg-amber-50 px-2 py-1 text-[11px] font-bold text-amber-800">
              <font-awesome-icon :icon="['fas', 'triangle-exclamation']" /> {{ produto.conjunto.motivo }}
            </p>
            <button v-if="podeCorrigir(produto)" type="button" @click="abrirSubstituir(produto)"
              class="mt-2 w-full rounded-lg bg-slate-950 px-2 py-1.5 text-[11px] font-black text-white hover:bg-slate-800">
              <font-awesome-icon :icon="['fas', 'wrench']" /> Corrigir menu
            </button>
          </template>

          <!-- stock por variação -->
          <p v-else-if="produto.stock_por_variante" class="mt-2 text-[11px] font-bold text-slate-500">
            <font-awesome-icon :icon="['fas', 'boxes-stacked']" /> {{ produto.variantes.length }} variações
            <span v-if="produto.variantes.some(v => v.quantidade === 0)" class="text-red-600">
              · {{ produto.variantes.filter(v => v.quantidade === 0).length }} esgotada(s)
            </span>
          </p>
          <button v-else-if="produto.variantes_pendentes && podeGerirProdutos" type="button" @click="editarProduto(produto)"
            class="mt-2 w-full rounded-lg bg-amber-50 px-2 py-1 text-left text-[11px] font-black text-amber-700 hover:bg-amber-100">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" /> Definir stock por variação
          </button>

          <!-- Ações só visíveis se tiver permissão -->
          <div v-if="podeGerirProdutos" class="mt-4 grid grid-cols-2 gap-2">
            <button
              type="button"
              @click="editarProduto(produto)"
              class="h-9 rounded-xl bg-slate-100 text-xs font-black text-slate-700 transition hover:bg-slate-200"
            >
              Editar
            </button>

            <button
              type="button"
              @click="toggleAtivo(produto)"
              :class="[
                'h-9 rounded-xl text-xs font-black transition',
                produtoAtivo(produto)
                  ? 'bg-red-50 text-red-700 hover:bg-red-100'
                  : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
              ]"
            >
              {{ produtoAtivo(produto) ? 'Desativar' : 'Ativar' }}
            </button>
          </div>
        </div>
      </article>
    </section>

    <!-- Modal Criar/Editar Produto -->
    <div
      v-if="showProdutoModal"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      @click.self="fecharModal"
    >
      <div class="max-h-[95vh] w-full max-w-2xl overflow-hidden rounded-t-[2rem] bg-white shadow-2xl sm:rounded-[2rem]">
        <header class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-white p-5">
          <div>
            <h3 class="text-xl font-black text-slate-950">
              {{ produtoEditando ? 'Editar produto' : 'Novo produto' }}
            </h3>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              {{ produtoEditando ? 'Atualiza os dados do produto.' : 'Escolhe se o produto será próprio do POS ou da loja Bendi.' }}
            </p>
          </div>

          <button
            type="button"
            @click="fecharModal"
            class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </header>

        <form class="max-h-[calc(95vh-88px)] space-y-4 overflow-y-auto p-5" @submit.prevent="salvarProduto">
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Origem do produto</label>
            <select
              v-model="formProduto.origem"
              :disabled="!!produtoEditando"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10 disabled:cursor-not-allowed disabled:opacity-70"
            >
              <option v-if="podeCriarProdutoPOS" value="pos">Produto próprio do POS</option>
              <option v-if="podeCriarProdutoLoja" value="loja">Produto da loja Bendi</option>
            </select>
            <p class="mt-2 text-xs font-semibold text-slate-400">
              Em modo standalone só podes criar produtos próprios do POS. Em híbrido podes criar nos dois lados.
            </p>
          </div>

          <!-- Produto simples ou menu (conjunto de produtos que já vendes) -->
          <div>
            <div class="grid grid-cols-2 gap-1 rounded-2xl bg-slate-100 p-1" role="tablist">
              <button type="button" role="tab" :aria-selected="!conjunto.ativo" @click="conjunto.ativo = false"
                :class="['h-10 rounded-xl text-sm font-black transition', !conjunto.ativo ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800']">
                Produto
              </button>
              <button type="button" role="tab" :aria-selected="conjunto.ativo" @click="conjunto.ativo = true"
                :class="['h-10 rounded-xl text-sm font-black transition', conjunto.ativo ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800']">
                Menu / conjunto
              </button>
            </div>
            <p v-if="conjunto.ativo" class="mt-2 text-xs font-semibold text-slate-400">
              Junta produtos que já vendes (ex.: hambúrguer + batata + bebida) com um preço só.
              Ao vender, sai do stock de cada produto{{ formProduto.origem === 'pos' && modo === 'hibrido' ? ' — do POS ou da loja Bendi' : '' }}.
            </p>
          </div>


          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Nome *</label>
            <input
              v-model.trim="formProduto.nome"
              type="text"
              required
              placeholder="Ex: Café expresso"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Descrição</label>
            <textarea
              v-model.trim="formProduto.descricao"
              rows="3"
              placeholder="Descrição do produto..."
              class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
            ></textarea>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Preço *</label>
              <input
                v-model.number="formProduto.preco"
                type="number"
                step="1"
                min="0"
                required
                placeholder="0"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
            </div>

            <!-- preço de custo (produtos do POS; num menu é a soma dos componentes) → margem nos relatórios -->
            <div v-if="formProduto.origem === 'pos' && !conjunto.ativo">
              <label for="pos-preco-custo" class="mb-2 block text-sm font-black text-slate-700">Preço de custo</label>
              <input
                id="pos-preco-custo"
                v-model.trim="formProduto.preco_custo"
                type="text"
                inputmode="decimal"
                placeholder="Opcional"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
              <p class="mt-1 text-xs font-semibold text-slate-500">Quanto te custa uma unidade. Serve para a margem nos relatórios.</p>
            </div>

            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Categoria</label>
              <input
                v-model.trim="formProduto.categoria"
                type="text"
                list="categorias-list"
                placeholder="Ex: Bebidas"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
              <datalist id="categorias-list">
                <option v-for="cat in categorias" :key="cat" :value="cat" />
              </datalist>
            </div>
          </div>

          <div v-if="conjunto.ativo" class="space-y-2">
            <label class="block text-sm font-black text-slate-700">Produtos do menu *</label>
            <ConjuntoEditor v-model="conjunto.linhas" v-model:grupos="conjunto.grupos" claro :catalogo="catalogoConjunto"
              :preco-conjunto="formProduto.preco" :problemas="problemasConjunto"
              :mostrar-origem="formProduto.origem === 'pos' && modo === 'hibrido'" />
          </div>

          <!-- Tipo + atributos -->
          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Tipo de produto</label>
            <select
              v-model="formProduto.tipo_id"
              @change="onTipoChange"
              class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white"
            >
              <option value="">Sem tipo</option>
              <optgroup v-for="g in gruposTipos" :key="g.label" :label="g.label">
                <option v-for="t in g.itens" :key="t.id" :value="String(t.id)" class="capitalize">{{ t.nome }}</option>
              </optgroup>
            </select>
            <p class="mt-2 text-xs font-semibold text-slate-400">
              {{ formProduto.origem === 'loja'
                  ? 'Produtos da loja usam os tipos globais e os da loja Bendi.'
                  : 'Produtos do POS usam os tipos globais e os tipos deste POS (botão Tipos).' }}
            </p>
          </div>

          <div v-if="!conjunto.ativo && tipoSelecionado && schemaTipo.length" class="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-black uppercase tracking-wider text-slate-500 capitalize">Atributos · {{ tipoSelecionado.nome }}</p>
            <div v-for="a in schemaTipo" :key="a.nome">
              <label class="mb-2 flex items-center gap-1 text-xs font-black capitalize text-slate-600">
                <font-awesome-icon v-if="a.variante" :icon="['fas', 'boxes-stacked']" title="Stock por opção" class="text-amber-600" /> {{ a.nome }}
                <span v-if="a.obrigatorio" class="text-red-500">*</span>
                <span v-if="a.tipo === 'choices'" class="font-semibold normal-case text-slate-400">· escolhe uma ou mais</span>
              </label>
              <div v-if="a.tipo === 'choices'" class="flex flex-wrap gap-2">
                <button v-for="op in a.opcoes" :key="op" type="button" @click="toggleOpcao(a.nome, op)"
                  :class="['h-9 rounded-xl border px-3 text-xs font-black transition',
                           opcaoSelecionada(a.nome, op) ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-400']">
                  {{ op }}
                </button>
              </div>
              <input v-else v-model="formProduto.atributos[a.nome]" :type="a.tipo === 'numero' ? 'number' : 'text'" :placeholder="a.nome"
                class="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-slate-950" />
            </div>
          </div>

          <div v-if="conjunto.ativo" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold text-slate-500">
            <font-awesome-icon :icon="['fas', 'layer-group']" class="mr-1" />Um menu não tem stock próprio — vende-se enquanto houver stock de todos os produtos dele.
          </div>
          <div v-else-if="grelhaAtiva" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold text-slate-500">
            <font-awesome-icon :icon="['fas', 'boxes-stacked']" class="mr-1" />Stock gerido por variação — define as quantidades em <b>Stock por variação</b> abaixo.
          </div>
          <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50 px-4">
              <input
                v-model="formProduto.controlar_stock"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 accent-slate-950"
              />
              <span class="ml-2 text-sm font-black text-slate-700">Controlar stock</span>
            </label>

            <div>
              <label class="mb-2 block text-sm font-black text-slate-700">Stock</label>
              <input
                v-model.number="formProduto.stock"
                type="number"
                min="0"
                placeholder="0"
                class="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
            </div>
          </div>

          <!-- Stock por variação (vai no mesmo pedido do produto) -->
          <div v-if="!conjunto.ativo && atributosVarianteForm.length" class="space-y-3">
            <p class="text-sm font-black text-slate-700"><font-awesome-icon :icon="['fas', 'boxes-stacked']" class="mr-1" />Stock por variação
              <span class="ml-1 rounded-lg bg-amber-100 px-2 py-0.5 text-[11px] text-amber-800">{{ atributosVarianteForm.join(' × ') }}</span>
            </p>
            <p v-if="!combinacoesForm.length" class="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-xs font-semibold text-slate-500">
              Escolhe as opções de {{ atributosVarianteForm.join(' / ') }} acima para definir o stock de cada combinação.
            </p>
            <VariantesGrelhaForm v-else claro
              v-model:ativo="grelha.ativo" v-model:linhas="grelha.linhas"
              :atributos="atributosVarianteComOpcoes" :preco-produto="formProduto.preco"
              :stock-total-antigo="produtoEditando && !produtoEditando.stock_por_variante ? Number(produtoEditando.stock || 0) : null" />
          </div>

          <div>
            <label class="mb-2 block text-sm font-black text-slate-700">Imagem/Ficheiro</label>
            <input
              type="file"
              accept="image/*,video/*"
              @change="handleImagemUpload"
              class="block w-full cursor-pointer rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 file:mr-4 file:rounded-xl file:border-0 file:bg-slate-950 file:px-4 file:py-2 file:text-sm file:font-black file:text-white hover:file:bg-slate-800"
            />

            <div v-if="imagemPreview" class="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
              <img v-if="isImagePreview" :src="imagemPreview" class="h-44 w-full object-cover" />
              <div v-else class="flex h-24 items-center justify-center text-sm font-bold text-slate-500">
                Ficheiro selecionado
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50 px-4">
              <input v-model="formProduto.ativo" type="checkbox" class="h-4 w-4 rounded border-slate-300 accent-slate-950" />
              <span class="ml-2 text-sm font-black text-slate-700">Produto ativo</span>
            </label>

            <label class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50 px-4">
              <input v-model="formProduto.disponivel_pos" type="checkbox" class="h-4 w-4 rounded border-slate-300 accent-slate-950" />
              <span class="ml-2 text-sm font-black text-slate-700">Disponível no POS</span>
            </label>
          </div>

          <p v-if="error" class="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{{ error }}</p>

          <div class="grid grid-cols-2 gap-3 pt-4">
            <button
              type="button"
              @click="fecharModal"
              class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
            >
              Cancelar
            </button>

            <button
              type="submit"
              :disabled="salvando || !formProduto.origem"
              class="flex h-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span v-if="!salvando">{{ produtoEditando ? 'Atualizar' : 'Criar' }}</span>
              <span v-else class="flex items-center gap-2">
                <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
                A guardar...
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Corrigir menu: trocar o produto que o deixou indisponível (ex.: loja Bendi suspensa) -->
    <div v-if="substituir.produto" class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-sm sm:items-center sm:p-4"
         @click.self="substituir.produto = null">
      <div class="w-full max-w-md rounded-t-[2rem] bg-white p-5 shadow-2xl sm:rounded-[2rem]">
        <h3 class="text-lg font-black text-slate-950">Corrigir "{{ substituir.produto.nome }}"</h3>
        <p class="mt-1 text-sm font-semibold text-slate-500">
          {{ substituir.produto.conjunto?.motivo }}. Troca-o por um produto do POS para o menu voltar a vender.
        </p>

        <div class="mt-4 space-y-2 rounded-2xl border border-slate-200 p-4">
          <p class="text-sm font-black text-slate-800">Criar no POS e substituir</p>
          <p class="text-xs font-semibold text-slate-500">
            Cria "{{ substituir.componente?.nome }}" no POS com o mesmo nome, preço e foto. O stock da loja não passa para o POS.
          </p>
          <label class="flex items-center gap-2 text-sm font-bold text-slate-700">
            <input v-model="substituir.controlar_stock" type="checkbox" class="h-4 w-4 accent-slate-950" /> Controlar stock
          </label>
          <input v-if="substituir.controlar_stock" v-model.number="substituir.stock" type="number" min="0" placeholder="Quantidade que tens"
                 class="h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-slate-950" />
          <button type="button" :disabled="substituir.aGuardar" @click="confirmarSubstituir(true)"
                  class="h-11 w-full rounded-xl bg-slate-950 text-sm font-black text-white hover:bg-slate-800 disabled:opacity-60">
            Criar e substituir
          </button>
        </div>

        <div v-if="produtosPOSParaSubstituir.length" class="mt-3 space-y-2 rounded-2xl border border-slate-200 p-4">
          <p class="text-sm font-black text-slate-800">Ou usar um produto do POS que já existe</p>
          <select v-model="substituir.produto_pos_id" class="h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-bold text-slate-700 outline-none">
            <option :value="null" disabled>Escolhe o produto…</option>
            <option v-for="p in produtosPOSParaSubstituir" :key="p.id" :value="p.id">{{ p.nome }} · {{ money(p.preco) }}</option>
          </select>
          <select v-if="variantesSubstituto.length" v-model="substituir.variante_pos_id"
                  class="h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-bold text-slate-700 outline-none">
            <option :value="null" disabled>Escolhe a variação…</option>
            <option v-for="v in variantesSubstituto" :key="v.id" :value="v.id">{{ Object.values(v.combinacao || {}).join(' · ') }}</option>
          </select>
          <button type="button" :disabled="substituir.aGuardar || !substituir.produto_pos_id" @click="confirmarSubstituir(false)"
                  class="h-11 w-full rounded-xl border border-slate-950 text-sm font-black text-slate-950 hover:bg-slate-50 disabled:opacity-50">
            Substituir
          </button>
        </div>

        <p v-if="substituir.erro" class="mt-3 rounded-xl bg-red-50 px-3 py-2 text-sm font-bold text-red-700">{{ substituir.erro }}</p>
        <button type="button" @click="substituir.produto = null" class="mt-3 h-10 w-full rounded-xl text-sm font-bold text-slate-500 hover:text-slate-800">Fechar</button>
      </div>
    </div>
  </div>
</template>

<script>
import { formatarDinheiro } from '@/utils/dinheiro'
import api from '@/services/api'
import TiposModal from './components/TiposModal.vue'
import VariantesGrelhaForm from '@/components/inventario/VariantesGrelhaForm.vue'
import ConjuntoEditor, { erroConjunto, gruposDoProduto } from '@/components/conjuntos/ConjuntoEditor.vue'
import {
  combinacoesDe, mesclarLinhas, linhasDoProduto, linhasParaPayload, grelhaValida,
} from '@/utils/variantes'

const FORM_VAZIO = () => ({
  origem: 'pos', nome: '', descricao: '', preco: 0, preco_custo: '',
  categoria: '', controlar_stock: false, stock: 0,
  ativo: true, disponivel_pos: true, imagem: null,
  tipo_id: '', atributos: {},
})

export default {
  name: 'POSProdutos',

  components: { TiposModal, VariantesGrelhaForm, ConjuntoEditor },

  props: {
    posId: {
      type: [Number, String],
      required: true
    },
    // Permissões passadas pelo POSDashboard (null = conta principal = tudo permitido)
    permissoes: {
      type: Object,
      default: null
    },
    isMembro: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      produtos: [],
      loading: false,
      searchQuery: '',
      categoriaFiltro: '',
      origemFiltro: '',
      ativoFiltro: '',

      modo: '',
      lojaVinculada: null,

      showProdutoModal: false,
      produtoEditando: null,
      salvando: false,
      imagemPreview: null,
      isImagePreview: true,

      error: '',
      success: '',

      showTiposModal: false,
      tipos: [],          // tipos disponíveis para a origem do formulário
      grelha: { ativo: true, linhas: [] },   // stock por variação do formulário
      conjunto: { ativo: false, linhas: [], grupos: [] },   // menu: produtos fixos e escolhas
      // "Corrigir menu" — trocar o componente que o deixou indisponível
      substituir: { produto: null, componente: null, controlar_stock: true, stock: 0,
                    produto_pos_id: null, variante_pos_id: null, aGuardar: false, erro: '' },
      formProduto: FORM_VAZIO(),
    }
  },

  computed: {
    // Conta principal → tudo permitido. Membro → verificar permissão.
    podeGerirProdutos() {
      if (!this.isMembro) return true
      return this.permissoes?.pode_gerir_produtos ?? false
    },

    modoLabel() {
      return { standalone: 'Standalone', integrado: 'Integrado', hibrido: 'Híbrido' }[this.modo] || '—'
    },

    podeCriarProdutoPOS() {
      return this.modo === 'standalone' || this.modo === 'hibrido'
    },

    podeCriarProdutoLoja() {
      return (this.modo === 'integrado' || this.modo === 'hibrido') && !!this.lojaVinculada
    },

    categorias() {
      return [...new Set(this.produtos.map(p => p.categoria).filter(Boolean))]
    },

    // ── Tipos e variações ────────────────────────────────────
    gruposTipos() {
      const g = (origem, label) => ({ label, itens: this.tipos.filter(t => t.origem === origem) })
      return [
        g('pos', 'Deste POS'),
        g('loja', 'Da loja'),
        g('global', 'Globais'),
      ].filter(x => x.itens.length)
    },

    tipoSelecionado() {
      return this.tipos.find(t => String(t.id) === String(this.formProduto.tipo_id)) || null
    },

    schemaTipo() {
      return (this.tipoSelecionado?.atributos_schema || [])
        .map(a => (typeof a === 'string' ? { nome: a, tipo: 'texto', opcoes: [] } : a))
    },

    atributosVarianteForm() {
      return this.schemaTipo.filter(a => a.tipo === 'choices' && a.variante).map(a => a.nome)
    },

    // combinações calculadas a partir das opções seleccionadas — a grelha acompanha em tempo real
    combinacoesForm() {
      return combinacoesDe(this.schemaTipo, this.formProduto.atributos)
    },

    atributosVarianteComOpcoes() {
      return this.atributosVarianteForm.filter(n => this.combinacoesForm.some(c => n in c.combinacao))
    },

    // stock por variação ligado → os campos de stock total desaparecem
    grelhaAtiva() {
      return this.combinacoesForm.length > 0 && this.grelha.ativo
    },

    // produtos que podem entrar no menu: do POS e (POS híbrido, menu do POS) da loja; sem menus nem ele próprio
    catalogoConjunto() {
      const origem = this.formProduto.origem
      return this.produtos
        .filter(p => !p.e_conjunto)
        .filter(p => !(this.produtoEditando && p.origem === this.produtoEditando.origem && p.id === this.produtoEditando.id))
        .filter(p => origem === 'loja' ? p.origem === 'loja' : (p.origem === 'pos' || this.modo === 'hibrido'))
        .map(p => ({
          origem: p.origem, id: p.id, nome: p.nome, preco: p.preco, imagem: p.imagem_url, ativo: p.ativo,
          variantes: p.stock_por_variante
            ? (p.variantes || []).map(v => ({ id: v.id, nome: Object.values(v.combinacao || {}).join(' · '), preco: v.preco_efetivo }))
            : [],
        }))
    },

    // problemas que o servidor detectou em cada componente (ex.: loja suspensa)
    problemasConjunto() {
      const out = {}
      const todos = [...(this.produtoEditando?.componentes || []),
                     ...(this.produtoEditando?.grupos || []).flatMap(g => g.opcoes)]
      todos.forEach(c => {
        if (c.problema) out[c.origem + '-' + c.produto_id] = c.problema
      })
      return out
    },

    produtosPOSParaSubstituir() {
      const menu = this.substituir.produto
      if (!menu) return []
      const usados = new Set(menu.componentes.filter(c => c.origem === 'pos' && c.id !== this.substituir.componente?.id).map(c => c.produto_id))
      return this.produtos.filter(p => p.origem === 'pos' && !p.e_conjunto && p.ativo && p.id !== menu.id && !usados.has(p.id))
    },

    variantesSubstituto() {
      const p = this.produtos.find(x => x.origem === 'pos' && x.id === this.substituir.produto_pos_id)
      return p?.stock_por_variante ? (p.variantes || []) : []
    },

    produtosFiltrados() {
      const query = this.searchQuery.toLowerCase().trim()

      return this.produtos.filter(produto => {
        const matchesSearch =
          !query ||
          String(produto.nome || '').toLowerCase().includes(query) ||
          String(produto.descricao || '').toLowerCase().includes(query) ||
          String(produto.categoria || '').toLowerCase().includes(query)

        const matchesCategoria = !this.categoriaFiltro || produto.categoria === this.categoriaFiltro
        const matchesOrigem    = !this.origemFiltro    || produto.origem === this.origemFiltro
        const matchesAtivo     = this.ativoFiltro === '' || String(this.produtoAtivo(produto)) === this.ativoFiltro

        return matchesSearch && matchesCategoria && matchesOrigem && matchesAtivo
      })
    }
  },

  created() {
    this.carregarProdutos()
  },

  watch: {
    posId(newId, oldId) {
      if (newId && newId !== oldId) this.carregarProdutos()
    },
    // produtos do POS e da loja usam conjuntos de tipos diferentes
    'formProduto.origem'(origem) {
      if (this.showProdutoModal && origem) this.carregarTipos(origem)
    },
    // novas combinações entram a 0; removidas saem; as quantidades já escritas mantêm-se
    combinacoesForm(combos) {
      this.grelha.linhas = mesclarLinhas(combos, this.grelha.linhas)
    },
  },

  methods: {
    async carregarProdutos() {
      if (!this.posId || this.loading) return

      this.loading = true
      this.error = ''

      try {
        const { data } = await api.get(`/api/pos/${this.posId}/produtos/?gestao=1`)

        this.modo         = data.modo || ''
        this.lojaVinculada = data.loja_vinculada || null

        const lista = Array.isArray(data.results) ? data.results
                    : Array.isArray(data)          ? data
                    : []

        this.produtos = lista.map(this.normalizarProduto)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao carregar produtos.'
      } finally {
        this.loading = false
      }
    },

    abrirModalCriar() {
      if (!this.podeGerirProdutos) return

      this.clearMessages()
      this.produtoEditando = null
      this.resetForm()

      this.formProduto.origem = this.podeCriarProdutoPOS  ? 'pos'
                               : this.podeCriarProdutoLoja ? 'loja'
                               : ''

      this.showProdutoModal = true
      this.grelha = { ativo: true, linhas: [] }   // produto novo: stock por variação ligado por defeito
      this.conjunto = { ativo: false, linhas: [], grupos: [] }
      if (this.formProduto.origem) this.carregarTipos(this.formProduto.origem)
    },

    async carregarTipos(origem) {
      try {
        const { data } = await api.get(`/api/pos/${this.posId}/tipos/`, { params: { para: origem } })
        this.tipos = data
      } catch {
        this.tipos = []
      }
    },

    onTipoChange() {
      // atributos de outro tipo não fazem sentido no novo
      this.formProduto.atributos = {}
    },

    opcaoSelecionada(nome, op) {
      const v = this.formProduto.atributos[nome]
      return Array.isArray(v) ? v.includes(op) : v === op
    },

    toggleOpcao(nome, op) {
      const atual = this.formProduto.atributos[nome]
      const lista = Array.isArray(atual) ? [...atual] : (atual ? [atual] : [])
      const i = lista.indexOf(op)
      if (i >= 0) lista.splice(i, 1)
      else lista.push(op)
      this.formProduto.atributos = { ...this.formProduto.atributos, [nome]: lista }
    },

    editarProduto(produto) {
      if (!this.podeGerirProdutos) return

      this.clearMessages()
      this.produtoEditando = produto
      this.formProduto = {
        origem:          produto.origem || 'pos',
        nome:            produto.nome || '',
        descricao:       produto.descricao || '',
        preco:           Number(produto.preco || 0),
        preco_custo:     produto.preco_custo ?? '',
        categoria:       produto.categoria || '',
        controlar_stock: Boolean(produto.controlar_stock),
        stock:           Number(produto.stock || 0),
        ativo:           this.produtoAtivo(produto),
        disponivel_pos:  produto.disponivel_pos ?? true,
        imagem:          null,
        tipo_id:         produto.tipo_id ? String(produto.tipo_id) : '',
        atributos:       JSON.parse(JSON.stringify(produto.atributos || {})),
      }
      this.imagemPreview = produto.imagem_url || null
      this.isImagePreview = true
      this.showProdutoModal = true
      this.grelha = { ativo: !!produto.stock_por_variante, linhas: linhasDoProduto(produto) }
      this.conjunto = {
        ativo: !!produto.e_conjunto,
        linhas: (produto.componentes || []).map(c => ({
          origem: c.origem, produto_id: c.produto_id, variante_id: c.variante_id, quantidade: c.quantidade,
          variante_livre: !!c.variante_livre,
        })),
        grupos: gruposDoProduto(produto),
      }
      this.carregarTipos(produto.origem || 'pos')
    },

    async toggleAtivo(produto) {
      if (!this.podeGerirProdutos) return

      this.clearMessages()

      try {
        const formData = new FormData()
        formData.append('origem', produto.origem)
        formData.append('ativo', String(!this.produtoAtivo(produto)))

        await this.patchConfirmando(`/api/pos/${this.posId}/produtos/${produto.id}/`, formData)

        this.success = 'Produto atualizado com sucesso.'
        await this.carregarProdutos()
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao atualizar produto.'
      }
    },

    handleImagemUpload(event) {
      const file = event.target.files?.[0]
      if (!file) return

      this.formProduto.imagem = file
      this.isImagePreview = file.type.startsWith('image/')

      if (this.isImagePreview) {
        const reader = new FileReader()
        reader.onload = e => { this.imagemPreview = e.target.result }
        reader.readAsDataURL(file)
      } else {
        this.imagemPreview = 'file'
      }
    },

    async salvarProduto() {
      this.clearMessages()

      const erro = this.validarForm()
      if (erro) { this.error = erro; return }

      this.salvando = true

      try {
        const formData = new FormData()
        formData.append('origem',          this.formProduto.origem)
        formData.append('nome',            this.formProduto.nome.trim())
        formData.append('descricao',       this.formProduto.descricao || '')
        formData.append('preco',           String(this.formProduto.preco))
        if (this.formProduto.origem === 'pos' && !this.conjunto.ativo) {
          formData.append('preco_custo', String(this.formProduto.preco_custo ?? '').replace(',', '.'))
        }
        formData.append('categoria',       this.formProduto.categoria || 'Sem categoria')
        // menu: produtos e variações escolhidas (o servidor valida e grava tudo-ou-nada)
        if (this.conjunto.ativo) {
          const erroMenu = erroConjunto(this.conjunto.linhas, this.conjunto.grupos, this.catalogoConjunto)
          if (erroMenu) {
            this.error = erroMenu
            this.salvando = false
            return
          }
          formData.append('e_conjunto', 'true')
          formData.append('componentes', JSON.stringify(this.conjunto.linhas))
          formData.append('grupos', JSON.stringify(this.conjunto.grupos))
        } else if (this.produtoEditando?.e_conjunto) {
          formData.append('e_conjunto', 'false')
        }
        // com stock por variação o total é a soma das variações
        if (!this.conjunto.ativo && !this.grelhaAtiva) {
          formData.append('controlar_stock', String(Boolean(this.formProduto.controlar_stock)))
          formData.append('stock',           String(Number(this.formProduto.stock || 0)))
        }
        // grelha no mesmo pedido (o backend grava produto + variações tudo-ou-nada)
        if (!this.conjunto.ativo && this.combinacoesForm.length) {
          if (this.grelha.ativo && !grelhaValida(this.grelha.linhas)) {
            this.error = 'Há quantidades inválidas na grelha de stock por variação.'
            this.salvando = false
            return
          }
          formData.append('stock_por_variante', this.grelha.ativo ? 'true' : 'false')
          if (this.grelha.ativo) formData.append('variantes', JSON.stringify(linhasParaPayload(this.grelha.linhas)))
        }
        formData.append('ativo',           String(Boolean(this.formProduto.ativo)))
        formData.append('disponivel_pos',  String(Boolean(this.formProduto.disponivel_pos)))
        formData.append('tipo_id',         this.formProduto.tipo_id || '')
        if (this.tipoSelecionado && !this.conjunto.ativo) {
          formData.append('atributos', JSON.stringify(this.atributosParaEnviar()))
        }

        if (this.formProduto.origem === 'loja' && this.formProduto.categoria) {
          formData.append('novas_categorias', this.formProduto.categoria.trim())
        }

        if (this.formProduto.imagem) {
          formData.append('imagem',   this.formProduto.imagem)
          formData.append('ficheiro', this.formProduto.imagem)
        }

        if (this.produtoEditando) {
          const ok = await this.patchConfirmando(`/api/pos/${this.posId}/produtos/${this.produtoEditando.id}/`, formData)
          if (!ok) { this.salvando = false; return }
          this.success = 'Produto atualizado com sucesso.'
        } else {
          await api.post(`/api/pos/${this.posId}/produtos/criar/`, formData)
          this.success = 'Produto criado com sucesso.'
        }

        this.fecharModal()
        await this.carregarProdutos()
      } catch (err) {
        this.error = err.response?.data?.detail || this.formatBackendError(err.response?.data) || 'Erro ao guardar produto.'
      } finally {
        this.salvando = false
      }
    },

    // PATCH que pode pedir confirmação (desactivar um produto que está dentro de menus)
    async patchConfirmando(url, formData) {
      try {
        await api.patch(url, formData)
      } catch (e) {
        if (e.response?.status !== 409 || !e.response.data?.precisa_confirmar) throw e
        if (!confirm(e.response.data.detail + '\n\nDesactivar mesmo assim?')) return false
        await api.patch(url, formData, { params: { confirmar: 1 } })
      }
      return true
    },

    podeCorrigir(produto) {
      return this.podeGerirProdutos && produto.origem === 'pos' && !!produto.conjunto?.componente_id &&
        produto.componentes.some(c => c.id === produto.conjunto.componente_id && c.origem === 'loja')
    },

    abrirSubstituir(produto) {
      const componente = produto.componentes.find(c => c.id === produto.conjunto.componente_id)
      this.substituir = { produto, componente, controlar_stock: true, stock: 0,
                          produto_pos_id: null, variante_pos_id: null, aGuardar: false, erro: '' }
    },

    async confirmarSubstituir(criar) {
      const s = this.substituir
      s.aGuardar = true
      s.erro = ''
      const corpo = criar
        ? { criar: true, controlar_stock: s.controlar_stock, stock: Number(s.stock || 0) }
        : { produto_pos_id: s.produto_pos_id, variante_pos_id: s.variante_pos_id }
      try {
        const { data } = await api.post(
          `/api/pos/${this.posId}/produtos/${s.produto.id}/componentes/${s.componente.id}/substituir/`, corpo)
        this.success = data.detail
        this.substituir.produto = null
        await this.carregarProdutos()
      } catch (e) {
        s.erro = e.response?.data?.detail || 'Não foi possível substituir.'
      } finally {
        s.aGuardar = false
      }
    },

    // só os atributos do tipo escolhido, sem valores vazios
    atributosParaEnviar() {
      const out = {}
      this.schemaTipo.forEach(a => {
        const v = this.formProduto.atributos[a.nome]
        if (Array.isArray(v) ? v.length : (v !== undefined && v !== null && String(v).trim() !== '')) out[a.nome] = v
      })
      return out
    },

    fecharModal() {
      this.showProdutoModal = false
      this.produtoEditando  = null
      this.resetForm()
    },

    resetForm() {
      this.imagemPreview  = null
      this.isImagePreview = true
      this.formProduto = FORM_VAZIO()
    },

    validarForm() {
      if (!this.formProduto.origem) return 'Escolhe a origem do produto.'
      if (this.formProduto.origem === 'pos'  && !this.podeCriarProdutoPOS  && !this.produtoEditando) return 'Este POS não permite criar produtos próprios.'
      if (this.formProduto.origem === 'loja' && !this.podeCriarProdutoLoja && !this.produtoEditando) return 'Este POS não permite criar produtos da loja.'
      if (!this.formProduto.nome.trim()) return 'O nome do produto é obrigatório.'
      if (Number(this.formProduto.preco) < 0) return 'O preço não pode ser negativo.'
      if (Number(this.formProduto.stock) < 0) return 'O stock não pode ser negativo.'
      return null
    },

    normalizarProduto(produto) {
      return {
        ...produto,
        uid:          produto.uid || `${produto.origem}-${produto.id}`,
        categoria:    produto.categoria || produto.categorias?.[0]?.nome || produto.tipo?.nome || 'Sem categoria',
        imagem_url:   produto.imagem_url || produto.ficheiro_url || null,
        ativo:        produto.ativo ?? true,
        disponivel_pos: produto.disponivel_pos ?? true,
        stock:        produto.e_conjunto ? produto.stock : (produto.stock ?? 0),   // menu sem limite → null
        origem:       produto.origem || 'pos'
      }
    },

    produtoAtivo(produto) { return produto.ativo ?? true },

    money(value) {
      return formatarDinheiro(Number(value || 0))
    },

    formatBackendError(data) {
      if (!data || typeof data !== 'object') return ''
      const key = Object.keys(data)[0]
      const val = data[key]
      if (Array.isArray(val))      return `${key}: ${val.join(', ')}`
      if (typeof val === 'string') return `${key}: ${val}`
      return ''
    },

    clearMessages() { this.error = ''; this.success = '' }
  }
}
</script>