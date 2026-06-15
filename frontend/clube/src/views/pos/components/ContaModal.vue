<template>
  <div class="fixed inset-0 z-50 flex items-end justify-center bg-black/55 p-0 backdrop-blur-sm sm:items-center sm:p-4">

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- MOBILE: Bottom Sheet                                        -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div class="flex h-[92vh] w-full flex-col overflow-hidden rounded-t-[2rem] bg-white shadow-2xl lg:hidden">

      <!-- Header Mobile -->
      <header class="shrink-0 border-b border-slate-200 bg-white px-4 py-3">
        <div class="flex items-center justify-between gap-4">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-xl font-black text-slate-950">{{ mesa.numero }}</h2>
              <span
                :class="[
                  'rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-wide',
                  mesa.status === 'ocupada' ? 'bg-blue-50 text-blue-700' : 'bg-emerald-50 text-emerald-700'
                ]"
              >
                {{ mesa.status || 'livre' }}
              </span>
            </div>
            <p class="mt-1 text-xs font-semibold text-slate-500">
              Capacidade: {{ mesa.capacidade }} · Conta #{{ conta?.id || '—' }}
            </p>
          </div>

          <button
            type="button"
            @click="$emit('close')"
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </div>
      </header>

      <!-- Erro Mobile -->
      <div
        v-if="error"
        class="mx-4 mt-3 shrink-0 rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-bold text-red-700"
      >
        {{ error }}
      </div>

      <!-- Mobile Tabs: Produtos / Pedido -->
      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div class="shrink-0 border-b border-slate-200 bg-white">
          <div class="flex">
            <button
              type="button"
              @click="mobileActiveTab = 'produtos'"
              :class="[
                'flex-1 border-b-2 px-4 py-3 text-sm font-black transition',
                mobileActiveTab === 'produtos' ? 'border-slate-950 text-slate-950' : 'border-transparent text-slate-500'
              ]"
            >
              Produtos
              <span class="ml-1 text-xs opacity-70">({{ produtosFiltrados.length }})</span>
            </button>
            <button
              type="button"
              @click="mobileActiveTab = 'pedido'"
              :class="[
                'flex-1 border-b-2 px-4 py-3 text-sm font-black transition',
                mobileActiveTab === 'pedido' ? 'border-slate-950 text-slate-950' : 'border-transparent text-slate-500'
              ]"
            >
              Pedido
              <span class="ml-1 text-xs opacity-70">({{ items.length }})</span>
            </button>
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-hidden">
          <!-- Tab Produtos Mobile -->
          <div v-show="mobileActiveTab === 'produtos'" class="flex h-full flex-col overflow-y-auto p-4">
            <div class="flex h-full flex-col">
              <div class="mb-4 flex shrink-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 class="text-lg font-black text-slate-950">Produtos</h3>
                  <p class="text-xs font-semibold text-slate-500">{{ produtosFiltrados.length }} disponíveis</p>
                </div>
                <button
                  type="button"
                  @click="carregarProdutos"
                  :disabled="loadingProdutos"
                  class="h-10 shrink-0 rounded-2xl bg-slate-100 px-4 text-sm font-black text-slate-700 transition hover:bg-slate-200 disabled:opacity-60"
                >
                  Atualizar
                </button>
              </div>

              <!-- Categorias -->
              <div class="mb-4 shrink-0 overflow-x-auto">
                <div class="flex gap-2 pb-2">
                  <button
                    type="button"
                    @click="categoriaAtiva = ''"
                    :class="['shrink-0 rounded-full px-4 py-2 text-sm font-black transition', categoriaAtiva === '' ? 'bg-slate-950 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
                  >
                    Todos
                  </button>
                  <button
                    v-for="categoria in categorias"
                    :key="categoria"
                    type="button"
                    @click="categoriaAtiva = categoria"
                    :class="['shrink-0 whitespace-nowrap rounded-full px-4 py-2 text-sm font-black transition', categoriaAtiva === categoria ? 'bg-slate-950 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
                  >
                    {{ categoria }}
                  </button>
                </div>
              </div>

              <!-- Filtros -->
              <div class="mb-4 grid shrink-0 grid-cols-1 gap-2 sm:grid-cols-[1fr_140px]">
                <input
                  v-model.trim="searchQuery"
                  type="text"
                  placeholder="Pesquisar..."
                  class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                />
                <select
                  v-model="origemFiltro"
                  class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-3 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
                >
                  <option value="">Todos</option>
                  <option value="pos">POS</option>
                  <option value="loja">Loja</option>
                </select>
              </div>

              <!-- Grid Produtos -->
              <div class="min-h-0 flex-1">
                <div v-if="loadingProdutos && produtos.length === 0" class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div v-for="i in 6" :key="i" class="h-48 animate-pulse rounded-[1.5rem] bg-slate-100"></div>
                </div>

                <div
                  v-else-if="produtosFiltrados.length === 0"
                  class="flex min-h-[240px] flex-col items-center justify-center rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
                >
                  <div class="flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">📦</div>
                  <h4 class="mt-4 text-lg font-black text-slate-950">Sem produtos</h4>
                  <p class="mt-2 text-sm leading-6 text-slate-500">{{ categoriaAtiva ? 'Nesta categoria' : 'Disponíveis' }}</p>
                </div>

                <div v-else class="grid grid-cols-2 gap-3 pb-4 sm:grid-cols-3">
                  <button
                    v-for="produto in produtosFiltrados"
                    :key="produtoUid(produto)"
                    type="button"
                    :disabled="addingProdutoUid === produtoUid(produto) || !produto.disponivel"
                    @click="adicionarProduto(produto)"
                    class="group overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <div class="relative aspect-square bg-slate-100">
                      <img v-if="produto.imagem_url" :src="produto.imagem_url" :alt="produto.nome" class="h-full w-full object-cover transition duration-300 group-hover:scale-105" />
                      <div v-else class="flex h-full w-full items-center justify-center text-4xl text-slate-300">📦</div>
                      <span :class="['absolute left-2 top-2 rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-wide text-white', produto.origem === 'pos' ? 'bg-purple-600' : 'bg-blue-600']">
                        {{ produto.origem === 'pos' ? 'POS' : 'Loja' }}
                      </span>
                    </div>
                    <div class="p-2.5">
                      <p class="line-clamp-2 min-h-[36px] text-xs font-black text-slate-950 sm:text-sm">{{ produto.nome }}</p>
                      <div class="mt-2 flex items-center justify-between gap-2">
                        <span class="text-sm font-black text-slate-950 sm:text-base">{{ money(produto.preco) }}</span>
                        <span v-if="produto.stock !== null && produto.stock !== undefined" class="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-black text-slate-500">
                          {{ produto.stock }}
                        </span>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab Pedido Mobile -->
          <div v-show="mobileActiveTab === 'pedido'" class="flex h-full flex-col overflow-hidden">
            <div class="flex-1 overflow-y-auto p-4">
              <div v-if="!conta" class="flex min-h-[220px] flex-col items-center justify-center text-center">
                <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
                <p class="mt-4 text-sm font-bold text-slate-500">A preparar conta...</p>
              </div>

              <div
                v-else-if="items.length === 0"
                class="flex min-h-[220px] flex-col items-center justify-center rounded-[2rem] border border-dashed border-slate-300 bg-white p-8 text-center"
              >
                <div class="flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-3xl">🛒</div>
                <h4 class="mt-4 text-lg font-black text-slate-950">Pedido vazio</h4>
                <p class="mt-2 text-sm leading-6 text-slate-500">Adiciona produtos para começar</p>
              </div>

              <div v-else class="space-y-3">
                <article
                  v-for="item in items"
                  :key="item.id"
                  class="rounded-[1.25rem] border border-slate-200 bg-white p-3 shadow-sm"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <h4 class="truncate text-sm font-black text-slate-950">{{ item.nome }}</h4>
                        <span :class="['rounded-full px-2 py-0.5 text-[10px] font-black uppercase', item.origem === 'pos' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700']">
                          {{ item.origem === 'pos' ? 'POS' : 'Loja' }}
                        </span>
                      </div>
                      <p class="mt-1 text-xs font-semibold text-slate-500">{{ money(item.preco_unitario) }} × {{ item.quantidade }}</p>
                    </div>

                    <!-- Botão remover: só se tiver permissão -->
                    <button
                      v-if="podeCancelarItems"
                      type="button"
                      @click="removerItem(item)"
                      class="rounded-xl p-2 text-red-500 transition hover:bg-red-50 hover:text-red-700"
                      title="Remover"
                    >
                      ×
                    </button>
                  </div>

                  <div class="mt-3 flex items-center justify-between gap-3">
                    <span class="text-base font-black text-slate-950">{{ money(item.preco_total) }}</span>
                    <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-500">
                      {{ item.status || 'pendente' }}
                    </span>
                  </div>
                </article>
              </div>
            </div>

            <!-- Footer Mobile -->
            <div v-if="conta" class="shrink-0 border-t border-slate-200 bg-white p-4">
              <div class="space-y-2">
                <div class="flex justify-between text-sm font-bold text-slate-500">
                  <span>Subtotal</span><span>{{ money(conta.subtotal) }}</span>
                </div>
                <div v-if="Number(conta.taxa_servico_valor) > 0" class="flex justify-between text-sm font-bold text-slate-500">
                  <span>Taxa ({{ conta.taxa_servico_percentagem }}%)</span><span>{{ money(conta.taxa_servico_valor) }}</span>
                </div>
                <div class="flex justify-between border-t border-slate-200 pt-3 text-lg font-black text-slate-950">
                  <span>Total</span><span>{{ money(conta.total) }}</span>
                </div>
              </div>

              <div class="mt-4 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  @click="$emit('close')"
                  class="h-11 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
                >
                  Fechar
                </button>
                <!-- Botão pagar: só se tiver permissão -->
                <button
                  v-if="podeFecharContas"
                  type="button"
                  @click="finalizarConta"
                  :disabled="items.length === 0"
                  class="h-11 rounded-2xl bg-emerald-600 text-sm font-black text-white shadow-lg shadow-emerald-600/20 transition hover:-translate-y-0.5 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
                >
                  Pagar
                </button>
                <div
                  v-else
                  class="flex h-11 items-center justify-center rounded-2xl bg-slate-100 text-sm font-black text-slate-400"
                >
                  Sem permissão
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- DESKTOP: Modal centrado split-layout                        -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div class="hidden h-[90vh] w-full max-w-7xl flex-col overflow-hidden rounded-[2rem] bg-white shadow-2xl lg:flex">

      <!-- Header Desktop -->
      <header class="shrink-0 border-b border-slate-200 bg-white px-6 py-4">
        <div class="flex items-center justify-between gap-4">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-2xl font-black text-slate-950">{{ mesa.numero }}</h2>
              <span
                :class="[
                  'rounded-full px-3 py-1 text-xs font-black uppercase tracking-wide',
                  mesa.status === 'ocupada' ? 'bg-blue-50 text-blue-700' : 'bg-emerald-50 text-emerald-700'
                ]"
              >
                {{ mesa.status || 'livre' }}
              </span>
            </div>
            <p class="mt-1 text-sm font-semibold text-slate-500">
              Capacidade: {{ mesa.capacidade }} · Conta #{{ conta?.id || '—' }}
            </p>
          </div>

          <button
            type="button"
            @click="$emit('close')"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-xl font-black text-slate-500 transition hover:bg-slate-200 hover:text-slate-950"
          >
            ×
          </button>
        </div>
      </header>

      <!-- Erro Desktop -->
      <div
        v-if="error"
        class="mx-6 mt-4 shrink-0 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
      >
        {{ error }}
      </div>

      <!-- Split Layout Desktop -->
      <div class="min-h-0 flex-1 grid grid-cols-[1fr_420px]">

        <!-- Coluna Produtos -->
        <section class="min-h-0 overflow-hidden border-r border-slate-200 p-6">
          <div class="flex h-full flex-col">
            <div class="mb-4 flex shrink-0 items-center justify-between">
              <div>
                <h3 class="text-xl font-black text-slate-950">Produtos</h3>
                <p class="text-sm font-semibold text-slate-500">{{ produtosFiltrados.length }} disponíveis</p>
              </div>
              <button
                type="button"
                @click="carregarProdutos"
                :disabled="loadingProdutos"
                class="h-10 rounded-2xl bg-slate-100 px-4 text-sm font-black text-slate-700 transition hover:bg-slate-200 disabled:opacity-60"
              >
                Atualizar
              </button>
            </div>

            <!-- Categorias Desktop -->
            <div class="mb-4 shrink-0 overflow-x-auto">
              <div class="flex gap-2 pb-2">
                <button
                  type="button"
                  @click="categoriaAtiva = ''"
                  :class="['shrink-0 rounded-full px-4 py-2 text-sm font-black transition', categoriaAtiva === '' ? 'bg-slate-950 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
                >
                  Todos
                </button>
                <button
                  v-for="categoria in categorias"
                  :key="categoria"
                  type="button"
                  @click="categoriaAtiva = categoria"
                  :class="['shrink-0 whitespace-nowrap rounded-full px-4 py-2 text-sm font-black transition', categoriaAtiva === categoria ? 'bg-slate-950 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
                >
                  {{ categoria }}
                </button>
              </div>
            </div>

            <!-- Filtros Desktop -->
            <div class="mb-4 grid shrink-0 grid-cols-[1fr_140px] gap-2">
              <input
                v-model.trim="searchQuery"
                type="text"
                placeholder="Pesquisar..."
                class="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              />
              <select
                v-model="origemFiltro"
                class="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-3 text-sm font-bold text-slate-700 outline-none transition focus:border-slate-950 focus:bg-white focus:ring-4 focus:ring-slate-950/10"
              >
                <option value="">Todos</option>
                <option value="pos">POS</option>
                <option value="loja">Loja</option>
              </select>
            </div>

            <!-- Grid Produtos Desktop -->
            <div class="min-h-0 flex-1 overflow-y-auto">
              <div v-if="loadingProdutos && produtos.length === 0" class="grid grid-cols-3 gap-3 xl:grid-cols-4">
                <div v-for="i in 8" :key="i" class="h-48 animate-pulse rounded-[1.5rem] bg-slate-100"></div>
              </div>

              <div
                v-else-if="produtosFiltrados.length === 0"
                class="flex min-h-[280px] flex-col items-center justify-center rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
              >
                <div class="flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-3xl shadow-sm">📦</div>
                <h4 class="mt-4 text-lg font-black text-slate-950">Sem produtos</h4>
                <p class="mt-2 text-sm leading-6 text-slate-500">{{ categoriaAtiva ? 'Nesta categoria' : 'Disponíveis' }}</p>
              </div>

              <div v-else class="grid grid-cols-3 gap-3 pb-4 xl:grid-cols-4">
                <button
                  v-for="produto in produtosFiltrados"
                  :key="produtoUid(produto)"
                  type="button"
                  :disabled="addingProdutoUid === produtoUid(produto) || !produto.disponivel"
                  @click="adicionarProduto(produto)"
                  class="group overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <div class="relative aspect-square bg-slate-100">
                    <img v-if="produto.imagem_url" :src="produto.imagem_url" :alt="produto.nome" class="h-full w-full object-cover transition duration-300 group-hover:scale-105" />
                    <div v-else class="flex h-full w-full items-center justify-center text-4xl text-slate-300">📦</div>
                    <span :class="['absolute left-2 top-2 rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-white', produto.origem === 'pos' ? 'bg-purple-600' : 'bg-blue-600']">
                      {{ produto.origem === 'pos' ? 'POS' : 'Loja' }}
                    </span>
                  </div>
                  <div class="p-3">
                    <p class="line-clamp-2 min-h-[40px] text-sm font-black text-slate-950">{{ produto.nome }}</p>
                    <div class="mt-3 flex items-center justify-between gap-2">
                      <span class="text-base font-black text-slate-950">{{ money(produto.preco) }}</span>
                      <span v-if="produto.stock !== null && produto.stock !== undefined" class="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-black text-slate-500">
                        {{ produto.stock }}
                      </span>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Coluna Pedido Desktop -->
        <aside class="flex min-h-0 flex-col bg-slate-50">
          <div class="shrink-0 border-b border-slate-200 bg-white p-4">
            <div class="flex items-center justify-between gap-3">
              <div>
                <h3 class="text-xl font-black text-slate-950">Pedido</h3>
                <p class="text-sm font-semibold text-slate-500">Conta #{{ conta?.id || '—' }}</p>
              </div>
              <div v-if="loadingConta" class="h-7 w-7 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
            </div>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto p-4">
            <div v-if="!conta" class="flex min-h-[220px] flex-col items-center justify-center text-center">
              <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-950"></div>
              <p class="mt-4 text-sm font-bold text-slate-500">A preparar conta...</p>
            </div>

            <div
              v-else-if="items.length === 0"
              class="flex min-h-[220px] flex-col items-center justify-center rounded-[2rem] border border-dashed border-slate-300 bg-white p-8 text-center"
            >
              <div class="flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-3xl">🛒</div>
              <h4 class="mt-4 text-lg font-black text-slate-950">Pedido vazio</h4>
              <p class="mt-2 text-sm leading-6 text-slate-500">Adiciona produtos</p>
            </div>

            <div v-else class="space-y-3">
              <article
                v-for="item in items"
                :key="item.id"
                class="rounded-[1.25rem] border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      <h4 class="truncate text-sm font-black text-slate-950">{{ item.nome }}</h4>
                      <span :class="['rounded-full px-2 py-0.5 text-[10px] font-black uppercase', item.origem === 'pos' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700']">
                        {{ item.origem === 'pos' ? 'POS' : 'Loja' }}
                      </span>
                    </div>
                    <p class="mt-1 text-xs font-semibold text-slate-500">{{ money(item.preco_unitario) }} × {{ item.quantidade }}</p>
                  </div>

                  <!-- Botão remover: só se tiver permissão -->
                  <button
                    v-if="podeCancelarItems"
                    type="button"
                    @click="removerItem(item)"
                    class="rounded-xl p-2 text-red-500 transition hover:bg-red-50 hover:text-red-700"
                    title="Remover"
                  >
                    ×
                  </button>
                </div>

                <div class="mt-3 flex items-center justify-between gap-3">
                  <span class="text-lg font-black text-slate-950">{{ money(item.preco_total) }}</span>
                  <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-500">
                    {{ item.status || 'pendente' }}
                  </span>
                </div>
              </article>
            </div>
          </div>

          <!-- Footer Desktop -->
          <footer v-if="conta" class="shrink-0 border-t border-slate-200 bg-white p-4">
            <div class="space-y-2">
              <div class="flex justify-between text-sm font-bold text-slate-500">
                <span>Subtotal</span><span>{{ money(conta.subtotal) }}</span>
              </div>
              <div v-if="Number(conta.taxa_servico_valor) > 0" class="flex justify-between text-sm font-bold text-slate-500">
                <span>Taxa ({{ conta.taxa_servico_percentagem }}%)</span><span>{{ money(conta.taxa_servico_valor) }}</span>
              </div>
              <div class="flex justify-between border-t border-slate-200 pt-3 text-xl font-black text-slate-950">
                <span>Total</span><span>{{ money(conta.total) }}</span>
              </div>
            </div>

            <div class="mt-4 grid grid-cols-2 gap-2">
              <button
                type="button"
                @click="$emit('close')"
                class="h-12 rounded-2xl border border-slate-200 bg-white text-sm font-black text-slate-700 transition hover:bg-slate-50"
              >
                Fechar
              </button>

              <!-- Botão pagar: só se tiver permissão -->
              <button
                v-if="podeFecharContas"
                type="button"
                @click="finalizarConta"
                :disabled="items.length === 0"
                class="h-12 rounded-2xl bg-emerald-600 text-sm font-black text-white shadow-lg shadow-emerald-600/20 transition hover:-translate-y-0.5 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                Pagar
              </button>
              <div
                v-else
                class="flex h-12 items-center justify-center rounded-2xl bg-slate-100 text-sm font-bold text-slate-400"
                title="Sem permissão para fechar contas"
              >
                Sem permissão
              </div>
            </div>
          </footer>
        </aside>
      </div>
    </div>

    <!-- Modal Pagamento -->
    <PagamentoModal
      v-if="showPagamentoModal"
      :conta="conta"
      :pos-id="posId"
      @close="showPagamentoModal = false"
      @pago="handlePagamentoConcluido"
    />
  </div>
</template>

<script>
import api from '@/services/api'
import PagamentoModal from './PagamentoModal.vue'

export default {
  name: 'ContaModal',

  components: { PagamentoModal },

  props: {
    mesa: {
      type: Object,
      required: true
    },
    posId: {
      type: [Number, String],
      required: true
    },
    // Permissões passadas pelo POSMesas (null = conta principal = tudo permitido)
    permissoes: {
      type: Object,
      default: null
    },
    isMembro: {
      type: Boolean,
      default: false
    }
  },

  emits: ['close', 'atualizar'],

  data() {
    return {
      conta: null,
      produtos: [],
      categorias: [],
      categoriaAtiva: '',
      searchQuery: '',
      origemFiltro: '',
      loadingConta: false,
      loadingProdutos: false,
      addingProdutoUid: null,
      showPagamentoModal: false,
      error: '',
      mobileActiveTab: 'produtos',
      scrollPosition: 0
    }
  },

  computed: {
    items() {
      return Array.isArray(this.conta?.items) ? this.conta.items : []
    },

    produtosFiltrados() {
      const query = this.searchQuery.toLowerCase().trim()
      return this.produtos.filter(produto => {
        const matchesSearch =
          !query ||
          String(produto.nome || '').toLowerCase().includes(query) ||
          String(produto.descricao || '').toLowerCase().includes(query) ||
          String(produto.categoria || '').toLowerCase().includes(query)

        return (
          matchesSearch &&
          (!this.origemFiltro    || produto.origem    === this.origemFiltro) &&
          (!this.categoriaAtiva  || produto.categoria === this.categoriaAtiva)
        )
      })
    },

    // Conta principal → tudo permitido. Membro → verificar permissão.
    podeFecharContas() {
      if (!this.isMembro) return true
      return this.permissoes?.pode_fechar_contas ?? false
    },

    podeCancelarItems() {
      if (!this.isMembro) return true
      return this.permissoes?.pode_cancelar_items ?? false
    },
  },

  async created() {
    await Promise.all([this.iniciarConta(), this.carregarProdutos()])
  },

  mounted() {
    this.scrollPosition = window.scrollY
    document.body.style.overflow  = 'hidden'
    document.body.style.position  = 'fixed'
    document.body.style.width     = '100%'
    document.body.style.top       = `-${this.scrollPosition}px`
  },

  unmounted() {
    document.body.style.overflow  = ''
    document.body.style.position  = ''
    document.body.style.width     = ''
    document.body.style.top       = ''
    window.scrollTo(0, this.scrollPosition)
  },

  methods: {
    async iniciarConta() {
      this.loadingConta = true
      this.error = ''
      try {
        const { data } = await api.post(`/api/pos/${this.posId}/mesas/${this.mesa.id}/conta/`, {})
        this.conta = this.normalizeConta(data)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao iniciar conta.'
      } finally {
        this.loadingConta = false
      }
    },

    async carregarConta(contaId) {
      const { data } = await api.get(`/api/pos/${this.posId}/contas/${contaId}/`)
      this.conta = this.normalizeConta(data)
    },

    async recarregarConta() {
      if (!this.conta?.id) return
      await this.carregarConta(this.conta.id)
    },

    async carregarProdutos() {
      if (this.loadingProdutos) return
      this.loadingProdutos = true
      try {
        const { data } = await api.get(`/api/pos/${this.posId}/produtos/`)
        const lista = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : [])
        this.produtos = lista.map(this.normalizarProduto)

        const cats = new Set()
        this.produtos.forEach(p => { if (p.categoria && p.categoria !== 'Sem categoria') cats.add(p.categoria) })
        this.categorias = Array.from(cats).sort()
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao carregar produtos.'
      } finally {
        this.loadingProdutos = false
      }
    },

    async adicionarProduto(produto) {
      if (!this.conta?.id) { this.error = 'A conta ainda não está pronta.'; return }
      if (!produto.disponivel) { this.error = 'Este produto não está disponível.'; return }

      this.addingProdutoUid = this.produtoUid(produto)
      this.error = ''

      try {
        await api.post(`/api/pos/${this.posId}/contas/${this.conta.id}/items/`, {
          produto_id:  produto.id,
          origem:      produto.origem,
          quantidade:  1,
          observacoes: ''
        })
        await this.recarregarConta()
        await this.carregarProdutos()

        if (window.innerWidth < 1024) this.mobileActiveTab = 'pedido'
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao adicionar produto.'
      } finally {
        this.addingProdutoUid = null
      }
    },

    async removerItem(item) {
      if (!this.podeCancelarItems) return
      if (!confirm(`Remover ${item.nome}?`)) return

      this.error = ''
      try {
        await api.delete(`/api/pos/${this.posId}/contas/${this.conta.id}/items/${item.id}/`)
        await this.recarregarConta()
        await this.carregarProdutos()
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao remover item.'
      }
    },

    finalizarConta() {
      if (!this.podeFecharContas || !this.conta || this.items.length === 0) return
      this.showPagamentoModal = true
    },

    handlePagamentoConcluido() {
      this.showPagamentoModal = false
      this.$emit('atualizar')
      this.$emit('close')
    },

    normalizeConta(conta) {
      return { ...conta, items: Array.isArray(conta.items) ? conta.items : [] }
    },

    normalizarProduto(produto) {
      return {
        ...produto,
        uid:           produto.uid || `${produto.origem}-${produto.id}`,
        categoria:     produto.categoria || produto.categorias?.[0]?.nome || produto.tipo?.nome || 'Sem categoria',
        imagem_url:    produto.imagem_url || produto.ficheiro_url || null,
        ativo:         produto.ativo ?? true,
        disponivel_pos: produto.disponivel_pos ?? true,
        disponivel:    produto.disponivel ?? true,
        stock:         produto.stock ?? 0,
        origem:        produto.origem || 'pos'
      }
    },

    produtoUid(produto) {
      return produto.uid || `${produto.origem}-${produto.id}`
    },

    money(value) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(Number(value || 0))
    }
  }
}
</script>