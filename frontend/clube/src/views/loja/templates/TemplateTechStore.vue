<!-- TemplateTechStore — Dashboard tech, layout de 3 colunas, neon cyan, cards tipo spec sheet -->
<template>
  <div class="min-h-screen transition-colors duration-500"
       :class="isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <!-- Loading — estilo terminal -->
    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center font-mono"
         :class="isDark ? 'bg-slate-950' : 'bg-slate-50'">
      <div class="space-y-2 text-center">
        <div class="text-cyan-400 text-xs tracking-widest animate-pulse">[ INITIALIZING ]</div>
        <div class="w-48 h-0.5 relative overflow-hidden rounded"
             :class="isDark ? 'bg-slate-800' : 'bg-slate-200'">
          <div class="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500 to-blue-500 animate-loading-bar rounded"></div>
        </div>
        <div class="text-[10px] text-cyan-500/50 tracking-[0.3em]">LOADING STORE DATA...</div>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO TECH — fullscreen com grid overlay e estatísticas em HUD ── -->
      <section class="relative min-h-screen overflow-hidden flex flex-col">
        <!-- Background -->
        <div class="absolute inset-0">
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome"
               class="w-full h-full object-cover"
               :class="isDark ? 'opacity-25' : 'opacity-20'" />
          <!-- Gradient overlay -->
          <div class="absolute inset-0"
               :class="isDark
                 ? 'bg-gradient-to-br from-slate-950 via-cyan-950/60 to-slate-950'
                 : 'bg-gradient-to-br from-slate-50 via-cyan-50/60 to-slate-100'"/>
          <!-- Grid pattern -->
          <div class="absolute inset-0"
               :class="isDark ? 'opacity-[0.07]' : 'opacity-[0.05]'"
               style="background-image: linear-gradient(to right, cyan 1px, transparent 1px), linear-gradient(to bottom, cyan 1px, transparent 1px); background-size: 40px 40px;"></div>
          <!-- Corner glow -->
          <div class="absolute top-0 right-0 w-96 h-96 rounded-full blur-[120px] pointer-events-none opacity-30"
               style="background: radial-gradient(circle, rgba(6,182,212,0.4), transparent)"></div>
        </div>

        <!-- Nav overlay -->
        <div class="relative flex items-center justify-between px-6 py-5 z-10">
          <div class="flex items-center gap-3">
            <button @click="$router.back()"
              class="flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-mono tracking-wider transition"
              :class="isDark ? 'border-slate-700 text-slate-400 hover:border-cyan-500/50 hover:text-cyan-400 bg-slate-950/50' : 'border-slate-300 text-slate-500 hover:border-cyan-400 hover:text-cyan-600 bg-white/50'">
              ← BACK
            </button>
            <button @click="toggleDark"
              class="w-9 h-9 rounded-lg border flex items-center justify-center transition"
              :class="isDark ? 'border-slate-700 text-cyan-400 hover:border-cyan-500 bg-slate-950/50' : 'border-slate-300 text-cyan-600 hover:border-cyan-400 bg-white/50'">
              <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Hero content — centro -->
        <div class="relative flex-1 flex flex-col items-center justify-center px-6 py-16 z-10 text-center">
          <div v-if="loja.logo_url"
               class="w-24 h-24 mb-8 rounded-2xl overflow-hidden border-2 shadow-xl"
               :style="{ borderColor: 'var(--cor-primaria)', boxShadow: `0 0 40px var(--cor-primaria)40` }">
            <img :src="loja.logo_url" :alt="loja.nome" class="w-full h-full object-cover" />
          </div>

          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-mono tracking-[0.3em] uppercase mb-6"
               :style="{ borderColor: 'var(--cor-primaria)40', color: 'var(--cor-primaria)', backgroundColor: 'var(--cor-primaria)10' }">
            <span class="w-1.5 h-1.5 rounded-full animate-pulse"
                  :style="{ backgroundColor: 'var(--cor-primaria)' }"></span>
            {{ loja.categoria }}
          </div>

          <h1 class="font-black leading-none mb-4 tracking-tight"
              style="font-size: clamp(3.5rem, 10vw, 9rem)"
              :class="isDark ? '' : ''">
            <span class="bg-clip-text text-transparent"
                  :style="isDark
                    ? 'background-image: linear-gradient(135deg, #e2e8f0, #94a3b8, #67e8f9)'
                    : 'background-image: linear-gradient(135deg, #0f172a, #334155, #0e7490)'">
              {{ loja.nome }}
            </span>
          </h1>

          <p v-if="loja.descricao" class="text-base max-w-2xl leading-relaxed mb-10"
             :class="isDark ? 'text-slate-400' : 'text-slate-600'">
            {{ loja.descricao.substring(0, 140) }}{{ loja.descricao.length > 140 ? '…' : '' }}
          </p>

          <!-- HUD Stats -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl w-full">
            <div v-if="loja.rating_medio"
                 class="hud-card rounded-xl p-4 border text-center"
                 :class="isDark ? 'bg-slate-900/70 border-slate-700/50' : 'bg-white/70 border-slate-200'">
              <p class="text-2xl font-black"
                 :style="{ color: 'var(--cor-primaria)' }">{{ loja.rating_medio }}</p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-slate-500' : 'text-slate-400'">Rating</p>
            </div>
            <div v-if="loja.total_avaliacoes"
                 class="hud-card rounded-xl p-4 border text-center"
                 :class="isDark ? 'bg-slate-900/70 border-slate-700/50' : 'bg-white/70 border-slate-200'">
              <p class="text-2xl font-black"
                 :class="isDark ? 'text-slate-100' : 'text-slate-800'">{{ loja.total_avaliacoes }}</p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-slate-500' : 'text-slate-400'">Reviews</p>
            </div>
            <div v-if="loja.entrega_ativa"
                 class="hud-card rounded-xl p-4 border text-center col-span-2 md:col-span-1"
                 :class="isDark ? 'bg-slate-900/70 border-emerald-500/20' : 'bg-white/70 border-emerald-300/50'">
              <p class="text-2xl font-black text-emerald-400">ON</p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-slate-500' : 'text-slate-400'">Entrega</p>
            </div>
            <div class="hud-card rounded-xl p-4 border text-center"
                 :class="isDark ? 'bg-slate-900/70 border-slate-700/50' : 'bg-white/70 border-slate-200'">
              <p class="text-2xl font-black"
                 :class="isDark ? 'text-slate-100' : 'text-slate-800'">
                {{ (tiposExistentes.length + categoriasExistentes.length) || '—' }}
              </p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-slate-500' : 'text-slate-400'">Categorias</p>
            </div>
          </div>

          <!-- CTA -->
          <button @click="scrollToId('produtos')"
            class="mt-10 px-8 py-3.5 rounded-xl font-bold text-white tracking-wider transition-all hover:scale-105"
            :style="{ background: `linear-gradient(135deg, var(--cor-primaria), ${isDark ? '#1d4ed8' : '#0284c7'})`, boxShadow: `0 8px 30px var(--cor-primaria)40` }">
            Explorar Produtos ↓
          </button>
        </div>
      </section>

      <!-- ── LAYOUT PRINCIPAL — 3 colunas: sidebar filtros + conteúdo + sidebar info ── -->
      <div id="produtos" class="flex gap-0">

        <!-- LEFT SIDEBAR — categorias e filtros rápidos -->
        <aside class="hidden lg:flex flex-col sticky top-0 h-screen w-60 xl:w-64 flex-shrink-0 border-r overflow-y-auto"
               :class="isDark ? 'bg-slate-950 border-slate-800/50' : 'bg-slate-50 border-slate-200'">
          <div class="p-5">
            <!-- Store badge -->
            <div class="flex items-center gap-3 mb-6 p-3 rounded-xl border"
                 :class="isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'">
              <img v-if="loja.logo_url" :src="loja.logo_url" class="w-9 h-9 rounded-xl object-cover flex-shrink-0" />
              <div v-else class="w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center text-white text-sm font-black"
                   :style="{ background: 'var(--cor-primaria)' }">
                {{ loja.nome.charAt(0) }}
              </div>
              <div class="min-w-0">
                <p class="text-xs font-bold truncate" :class="isDark ? 'text-slate-200' : 'text-slate-800'">{{ loja.nome }}</p>
                <p class="text-[10px]" :style="{ color: 'var(--cor-primaria)' }">● Online</p>
              </div>
            </div>

            <p class="text-[10px] font-mono tracking-[0.3em] uppercase mb-3"
               :class="isDark ? 'text-slate-600' : 'text-slate-400'">// Navegação</p>

            <nav class="space-y-1">
              <button @click="scrollToId('destaques')"
                class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition group"
                :class="isDark ? 'text-cyan-400 hover:bg-slate-800' : 'text-cyan-600 hover:bg-slate-100'">
                <span class="w-5 h-5 rounded-lg flex items-center justify-center text-[10px]"
                      :style="{ background: 'var(--cor-primaria)20', color: 'var(--cor-primaria)' }">⚡</span>
                FEATURED
              </button>

              <template v-if="tiposExistentes.length">
                <p class="text-[10px] font-mono tracking-[0.3em] uppercase pt-4 pb-2 px-3"
                   :class="isDark ? 'text-slate-600' : 'text-slate-400'">// Tipos</p>
                <button v-for="tipo in tiposExistentes" :key="tipo.id"
                  @click="scrollToId('tipo-' + tipo.id)"
                  class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition capitalize"
                  :class="isDark ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'">
                  <span>{{ tipoIcon(tipo.nome) }}</span>
                  {{ tipo.nome }}
                </button>
              </template>

              <template v-if="categoriasExistentes.length">
                <p class="text-[10px] font-mono tracking-[0.3em] uppercase pt-4 pb-2 px-3"
                   :class="isDark ? 'text-slate-600' : 'text-slate-400'">// Categorias</p>
                <button v-for="cat in categoriasExistentes" :key="cat.id"
                  @click="scrollToId('cat-' + cat.id)"
                  class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition capitalize"
                  :class="isDark ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'">
                  <span>{{ cat.icone }}</span>
                  {{ cat.nome }}
                </button>
              </template>

              <p class="text-[10px] font-mono tracking-[0.3em] uppercase pt-4 pb-2 px-3"
                 :class="isDark ? 'text-slate-600' : 'text-slate-400'">// Mais</p>
              <button @click="scrollToId('catalogo')"
                class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition"
                :class="isDark ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'">
                <span class="w-5 h-5 rounded-lg flex items-center justify-center text-[10px]"
                      :class="isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-500'">⊞</span>
                ALL PRODUCTS
              </button>
              <button @click="scrollToId('avaliacoes')"
                class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition"
                :class="isDark ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'">
                <span class="w-5 h-5 rounded-lg flex items-center justify-center text-[10px]"
                      :class="isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-500'">★</span>
                REVIEWS
              </button>
            </nav>

            <!-- Specs da loja -->
            <div class="mt-6 border-t pt-5 space-y-2"
                 :class="isDark ? 'border-slate-800' : 'border-slate-200'">
              <p class="text-[10px] font-mono tracking-[0.3em] uppercase mb-3"
                 :class="isDark ? 'text-slate-600' : 'text-slate-400'">// Especificações</p>
              <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                   class="flex items-center justify-between py-1.5 border-b text-xs"
                   :class="isDark ? 'border-slate-800/50 text-slate-500' : 'border-slate-100 text-slate-400'">
                <span class="font-mono">{{ opcao.nome }}</span>
                <span class="font-bold" :style="{ color: 'var(--cor-primaria)' }">
                  {{ opcao.preco == 0 ? 'FREE' : formatPrice(opcao.preco) }}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <!-- MAIN CONTENT -->
        <main class="flex-1 min-w-0 pb-20">

          <!-- Mobile nav -->
          <div class="lg:hidden sticky top-0 z-20 border-b overflow-x-auto scrollbar-hide"
               :class="isDark ? 'bg-slate-950/95 border-slate-800 backdrop-blur-xl' : 'bg-slate-50/95 border-slate-200 backdrop-blur-xl'">
            <div class="flex gap-2 px-4 py-3 min-w-max">
              <button @click="scrollToId('destaques')"
                class="px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap text-white transition"
                :style="{ background: 'var(--cor-primaria)' }">
                ⚡ FEATURED
              </button>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap border transition"
                :class="isDark ? 'border-slate-700 text-slate-400 hover:border-cyan-500/50 hover:text-cyan-400' : 'border-slate-300 text-slate-500 hover:border-cyan-400 hover:text-cyan-600'">
                {{ cat.icone }} {{ cat.nome }}
              </button>
            </div>
          </div>

          <div class="px-6 md:px-10 pt-10">

            <!-- Destaques -->
            <section id="destaques" class="mb-16">
              <div class="flex items-center gap-4 mb-8">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center"
                     :style="{ background: `linear-gradient(135deg, var(--cor-primaria), #1d4ed8)` }">
                  <span class="text-white text-xs font-black">⚡</span>
                </div>
                <h2 class="text-2xl font-black tracking-tight"
                    :class="isDark ? 'text-slate-100' : 'text-slate-900'">Em Destaque</h2>
                <div class="flex-1 h-px bg-gradient-to-r from-current to-transparent opacity-20"
                     :class="isDark ? 'text-slate-400' : 'text-slate-500'"></div>
                <span class="text-[10px] font-mono tracking-[0.3em] uppercase"
                      :style="{ color: 'var(--cor-primaria)' }">// FEATURED</span>
              </div>
              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="230px"
                image-height="200px"
                card-height="320px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-300"
                :hover-border-class="'hover:border-cyan-500/50'"
                price-class="text-cyan-400 font-black"
                badge-class="bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg text-white font-bold"
                badge-text="HOT"
                :show-store-name="false"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- Por tipo -->
            <template v-if="tiposExistentes.length > 0">
              <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                       class="mb-16">
                <div class="flex items-center gap-4 mb-8">
                  <div class="w-8 h-8 rounded-xl border flex items-center justify-center text-lg"
                       :class="isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'">
                    {{ tipoIcon(tipo.nome) }}
                  </div>
                  <h2 class="text-2xl font-black capitalize tracking-tight"
                      :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ tipo.nome }}</h2>
                  <div class="flex-1 h-px bg-gradient-to-r from-current to-transparent opacity-20"
                       :class="isDark ? 'text-slate-400' : 'text-slate-500'"></div>
                </div>
                <ProductSlider
                  :title="tipo.nome"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }"
                  :isDark="isDark"
                  card-width="200px"
                  image-height="170px"
                  card-height="290px"
                  card-border-radius="rounded-2xl"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                  hover-border-class="hover:border-cyan-500/50"
                  price-class="text-cyan-400 font-bold"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- Por categoria -->
            <template v-if="categoriasExistentes.length > 0">
              <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                       class="mb-16">
                <div class="flex items-center gap-4 mb-8">
                  <div class="w-8 h-8 rounded-xl border flex items-center justify-center text-lg"
                       :class="isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'">
                    {{ cat.icone }}
                  </div>
                  <h2 class="text-2xl font-black capitalize tracking-tight"
                      :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ cat.nome }}</h2>
                  <div class="flex-1 h-px bg-gradient-to-r from-current to-transparent opacity-20"
                       :class="isDark ? 'text-slate-400' : 'text-slate-500'"></div>
                </div>
                <ProductSlider
                  :title="cat.nome"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :isDark="isDark"
                  card-width="200px"
                  image-height="170px"
                  card-height="290px"
                  card-border-radius="rounded-2xl"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                  hover-border-class="hover:border-cyan-500/50"
                  price-class="text-cyan-400 font-bold"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- Catálogo completo -->
            <section id="catalogo" class="mb-16">
              <div class="flex items-center gap-4 mb-8">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center text-white font-black text-xs"
                     :style="{ background: `linear-gradient(135deg, var(--cor-primaria), #1d4ed8)` }">⊞</div>
                <h2 class="text-2xl font-black tracking-tight"
                    :class="isDark ? 'text-slate-100' : 'text-slate-900'">Todos os Produtos</h2>
                <div class="flex-1 h-px bg-gradient-to-r from-current to-transparent opacity-20"
                     :class="isDark ? 'text-slate-400' : 'text-slate-500'"></div>
              </div>
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 xl:grid-cols-4"
                image-height="175px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                hover-border-class="hover:border-cyan-500/50"
                tab-border-radius="rounded-xl"
                :active-tab-class="'text-white font-bold shadow-lg shadow-cyan-500/20'"
                :inactive-tab-dark-class="'bg-slate-800 text-cyan-300/70 hover:text-cyan-200 border border-slate-700'"
                :inactive-tab-light-class="'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'"
                active-sub-tab-class="bg-cyan-500/20 text-cyan-400"
                input-border-radius="rounded-xl"
                input-focus-class="focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                filter-container-radius="rounded-2xl"
                product-name-hover-class="group-hover:text-cyan-400"
                price-class="text-cyan-400 font-bold"
                spinner-class="text-cyan-400"
                indicator-active-class="bg-cyan-500/20 text-cyan-400"
                clear-all-class="text-cyan-400 hover:text-cyan-300"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- Avaliações -->
            <section id="avaliacoes" class="mb-16">
              <div class="flex items-center gap-4 mb-8">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center text-white text-xs font-black"
                     :style="{ background: `linear-gradient(135deg, var(--cor-primaria), #1d4ed8)` }">★</div>
                <h2 class="text-2xl font-black tracking-tight"
                    :class="isDark ? 'text-slate-100' : 'text-slate-900'">Avaliações</h2>
                <div class="flex-1 h-px bg-gradient-to-r from-current to-transparent opacity-20"
                     :class="isDark ? 'text-slate-400' : 'text-slate-500'"></div>
              </div>
              <AvaliacaoLoja
                :loja-id="lojaId"
                :isDark="isDark"
                summary-border-radius="rounded-2xl"
                form-border-radius="rounded-2xl"
                review-card-border-radius="rounded-2xl"
                button-border-radius="rounded-xl"
                textarea-border-radius="rounded-xl"
                star-active-class="text-cyan-400"
                :star-inactive-class="isDark ? 'text-slate-700' : 'text-slate-300'"
                :progress-bar-class="'bg-gradient-to-r from-cyan-500 to-blue-600'"
                :submit-button-class="'text-white font-bold'"
                :own-review-border-class="isDark ? 'bg-slate-900 border border-cyan-500/30' : 'bg-white border border-cyan-200'"
                own-badge-class="bg-cyan-500/20 text-cyan-400"
                link-class="text-cyan-400 hover:text-cyan-300"
                @rating-updated="onRatingUpdated" />
            </section>

            <!-- Footer -->
            <footer class="border-t pb-8 pt-6"
                    :class="isDark ? 'border-slate-800' : 'border-slate-200'">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <p class="font-black text-sm bg-clip-text text-transparent"
                     :style="isDark
                       ? 'background-image: linear-gradient(to right, #94a3b8, #67e8f9)'
                       : 'background-image: linear-gradient(to right, #334155, #0e7490)'">
                    {{ loja.nome }}
                  </p>
                  <p class="text-xs font-mono mt-0.5"
                     :class="isDark ? 'text-slate-600' : 'text-slate-400'">
                    © {{ new Date().getFullYear() }} · All rights reserved
                  </p>
                </div>
                <div class="flex gap-4 text-xs font-mono">
                  <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-slate-500 hover:text-cyan-400' : 'text-slate-400 hover:text-cyan-600'">
                    RETURNS
                  </button>
                  <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-slate-500 hover:text-cyan-400' : 'text-slate-400 hover:text-cyan-600'">
                    TERMS
                  </button>
                  <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-slate-500 hover:text-cyan-400' : 'text-slate-400 hover:text-cyan-600'">
                    PRIVACY
                  </button>
                </div>
              </div>
            </footer>
          </div>
        </main>
      </div>

      <!-- Modal políticas -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-0 md:p-4 bg-black/80 backdrop-blur-md"
           @click.self="modalPolitica = null">
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto md:rounded-2xl border"
             :class="isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-100'">
            <h3 class="font-bold font-mono text-xs tracking-[0.3em] uppercase"
                :class="isDark ? 'text-slate-200' : 'text-slate-800'">
              // {{ modalPolitica === 'devolucao' ? 'RETURNS' : modalPolitica === 'termos' ? 'TERMS' : 'PRIVACY' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-lg border flex items-center justify-center transition"
              :class="isDark ? 'border-slate-700 text-slate-400 hover:border-cyan-500 hover:text-cyan-400' : 'border-slate-200 text-slate-500 hover:border-cyan-400 hover:text-cyan-600'">
              ×
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-slate-300' : 'text-slate-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao
             : modalPolitica === 'termos'    ? loja.termos_servico
             :                                 loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center font-mono"
         :class="isDark ? 'bg-slate-950' : 'bg-slate-50'">
      <p class="text-sm text-cyan-400 mb-4">[ ERROR 404 ] Store not found</p>
      <button @click="$router.back()" class="text-xs hover:underline" :style="{ color: 'var(--cor-primaria)' }">← BACK</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLojaData }   from '@/composables/useLojaData'
import ProductInfoCard   from '@/components/product/productInfoCard.vue'
import MultiCart         from '@/components/cart/multiCart.vue'
import ProductSlider     from '@/components/sliders/ProductSlider.vue'
import Profile           from '@/components/profile/UserProfile.vue'
import ProductCatalog    from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja     from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateTechStore',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#06b6d4',
      '--cor-secundaria': props.tema?.corSecundaria || '#0f172a',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }

    return { isDark, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }

@keyframes loading-bar {
  0%   { left: -30%; width: 30%; }
  50%  { left: 20%; width: 60%; }
  100% { left: 100%; width: 30%; }
}
.animate-loading-bar { animation: loading-bar 1.4s ease-in-out infinite; }

.nav-btn { transition: all 0.15s ease; }
.nav-btn:hover { transform: translateX(3px); }

.hud-card { transition: all 0.2s ease; }
.hud-card:hover { transform: translateY(-2px); }
</style>