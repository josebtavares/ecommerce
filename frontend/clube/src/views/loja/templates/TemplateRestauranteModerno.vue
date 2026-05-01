<!-- TemplateRestauranteModerno — Editorial escuro, sidebar de categorias, cards cinematográficos -->
<template>
  <div class="min-h-screen transition-colors duration-500 font-sans"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-100 text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <!-- Loading -->
    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-stone-100'">
      <div class="flex flex-col items-center gap-4">
        <div class="w-12 h-1 relative overflow-hidden">
          <div class="absolute inset-0 animate-slide-loading" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
        </div>
        <p class="text-xs tracking-[0.4em] uppercase" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">A carregar</p>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO ── Full-bleed, parallax, texto diagonal grande -->
      <section class="relative h-screen overflow-hidden" ref="heroRef">
        <div class="absolute inset-0 scale-110 hero-parallax"
             :style="{ transform: `translateY(${scrollY * 0.3}px) scale(1.1)` }">
          <video v-if="isVideo(loja.banner_url)"
            :src="loja.banner_url"
            class="w-full h-full object-cover"
            autoplay muted loop playsinline></video>
          <img v-else
            :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
            :alt="loja.nome" class="w-full h-full object-cover" />
        </div>
        <!-- Overlay gradiente duplo — vignette + bottom fade -->
        <div class="absolute inset-0"
             :class="isDark
               ? 'bg-[radial-gradient(ellipse_at_center,transparent_30%,rgba(9,9,11,0.7)_100%)]'
               : 'bg-[radial-gradient(ellipse_at_center,transparent_20%,rgba(28,25,23,0.6)_100%)]'"/>
        <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent"
             style="height: 100%"/>

        <!-- Nav overlay -->
        <div class="absolute top-0 left-0 right-0 flex items-center justify-between px-6 py-5 z-10">
          <button @click="$router.back()"
            class="flex items-center gap-2 text-xs tracking-[0.25em] uppercase text-white/70 hover:text-white transition group">
            <span class="w-6 h-px bg-white/50 group-hover:w-10 group-hover:bg-white transition-all duration-300"></span>
            Voltar
          </button>
          <button @click="toggleDark"
            class="w-9 h-9 rounded-full border flex items-center justify-center transition"
            :class="isDark ? 'border-white/20 text-white/60 hover:border-white/50 hover:text-white' : 'border-white/30 text-white hover:border-white'">
            <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
        </div>

        <!-- Hero content — bottom left, tipografia grande e condensada -->
        <div class="absolute bottom-0 left-0 right-0 p-8 md:p-14">
          <div class="flex items-end justify-between max-w-6xl mx-auto">
            <div class="flex-1">
              <!-- Categoria pill -->
              <div class="flex items-center gap-3 mb-5">
                <div class="w-8 h-px" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
                <span class="text-xs tracking-[0.35em] uppercase text-white/60">{{ loja.categoria }}</span>
              </div>
              <h1 class="hero-title text-white leading-none mb-4"
                  style="font-size: clamp(3rem, 9vw, 8rem); font-weight: 900; letter-spacing: -0.03em; line-height: 0.9">
                {{ loja.nome }}
              </h1>
              <p v-if="loja.descricao" class="text-white/60 text-base max-w-xl leading-relaxed mt-4">
                {{ loja.descricao.substring(0, 120) }}{{ loja.descricao.length > 120 ? '…' : '' }}
              </p>
            </div>
            <!-- Stats à direita no desktop -->
            <div class="hidden md:flex flex-col items-end gap-6 ml-8 pb-2">
              <div v-if="loja.rating_medio" class="text-right">
                <p class="text-5xl font-black text-white">{{ loja.rating_medio }}</p>
                <p class="text-xs tracking-[0.3em] uppercase text-white/40 mt-1">/ 5 estrelas</p>
              </div>
              <div v-if="loja.localizacao" class="text-right">
                <p class="text-sm text-white/60">📍 {{ loja.localizacao }}</p>
              </div>
            </div>
          </div>
          <!-- Scroll hint -->
          <div class="flex items-center gap-3 mt-8 max-w-6xl mx-auto">
            <div class="w-5 h-5 rounded-full border border-white/30 flex items-center justify-center animate-bounce">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            <span class="text-xs tracking-[0.3em] uppercase text-white/40">Scroll para explorar</span>
          </div>
        </div>
      </section>

      <!-- ── LAYOUT PRINCIPAL — sidebar + conteúdo ── -->
      <div class="flex min-h-screen" id="conteudo">

        <!-- SIDEBAR fixa — categorias + navegação -->
        <aside class="hidden lg:flex flex-col sticky top-0 h-screen w-64 xl:w-72 flex-shrink-0 border-r overflow-hidden"
               :class="isDark ? 'bg-zinc-950 border-zinc-800/60' : 'bg-stone-100 border-stone-300/60'">

          <!-- Logo + info da loja -->
          <div class="p-6 border-b" :class="isDark ? 'border-zinc-800/60' : 'border-stone-300/60'">
            <div class="flex items-center gap-3 mb-4">
              <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
                   class="w-10 h-10 rounded-xl object-cover" />
              <div v-else class="w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-black"
                   :style="{ backgroundColor: 'var(--cor-primaria)' }">
                {{ loja.nome.charAt(0) }}
              </div>
              <div class="min-w-0">
                <p class="font-bold text-sm truncate" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ loja.nome }}</p>
                <p class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ loja.categoria }}</p>
              </div>
            </div>
            <!-- Rating bar -->
            <div v-if="loja.rating_medio" class="flex items-center gap-2">
              <div class="flex-1 h-1 rounded-full overflow-hidden"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-300'">
                <div class="h-full rounded-full transition-all duration-1000"
                     :style="{ width: (loja.rating_medio / 5 * 100) + '%', backgroundColor: 'var(--cor-primaria)' }"></div>
              </div>
              <span class="text-xs font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ loja.rating_medio }}</span>
            </div>
          </div>

          <!-- Navegação por secção -->
          <nav class="flex-1 overflow-y-auto p-4 space-y-1">
            <p class="text-[10px] tracking-[0.35em] uppercase px-3 pt-3 pb-2"
               :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Menu</p>

            <button @click="scrollToId('destaques')"
              class="sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all text-left group"
              :class="isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-stone-200 text-zinc-500 hover:text-zinc-900'">
              <span class="w-6 h-6 rounded-lg flex items-center justify-center text-[11px]"
                    :style="{ backgroundColor: 'var(--cor-primaria)20', color: 'var(--cor-primaria)' }">✦</span>
              Destaques
            </button>

            <template v-if="tiposExistentes.length">
              <p class="text-[10px] tracking-[0.35em] uppercase px-3 pt-5 pb-2"
                 :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Por tipo</p>
              <button v-for="tipo in tiposExistentes" :key="tipo.id"
                @click="scrollToId('tipo-' + tipo.id)"
                class="sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all text-left"
                :class="isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-stone-200 text-zinc-500 hover:text-zinc-900'">
                <span class="text-base">{{ tipoIcon(tipo.nome) }}</span>
                <span class="capitalize">{{ tipo.nome }}</span>
              </button>
            </template>

            <template v-if="categoriasExistentes.length">
              <p class="text-[10px] tracking-[0.35em] uppercase px-3 pt-5 pb-2"
                 :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Categorias</p>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all text-left"
                :class="isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-stone-200 text-zinc-500 hover:text-zinc-900'">
                <span class="text-base">{{ cat.icone }}</span>
                <span class="capitalize">{{ cat.nome }}</span>
              </button>
            </template>

            <p class="text-[10px] tracking-[0.35em] uppercase px-3 pt-5 pb-2"
               :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Mais</p>
            <button @click="scrollToId('catalogo')"
              class="sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all text-left"
              :class="isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-stone-200 text-zinc-500 hover:text-zinc-900'">
              <span class="w-6 h-6 rounded-lg flex items-center justify-center text-[11px]"
                    :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-stone-200 text-zinc-500'">⊞</span>
              Catálogo completo
            </button>
            <button @click="scrollToId('avaliacoes')"
              class="sidebar-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all text-left"
              :class="isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-stone-200 text-zinc-500 hover:text-zinc-900'">
              <span class="w-6 h-6 rounded-lg flex items-center justify-center text-[11px]"
                    :class="isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-stone-200 text-zinc-500'">★</span>
              Avaliações
            </button>
          </nav>

          <!-- Entrega + pagamento no fundo da sidebar -->
          <div class="p-4 border-t space-y-3" :class="isDark ? 'border-zinc-800/60' : 'border-stone-300/60'">
            <div v-if="opcoesEntrega.length">
              <p class="text-[10px] tracking-[0.3em] uppercase mb-2"
                 :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Entrega</p>
              <div v-for="opcao in opcoesEntrega.slice(0, 2)" :key="opcao.id"
                   class="flex items-center justify-between text-xs py-1">
                <span :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">{{ opcao.nome }}</span>
                <span class="font-semibold" :style="{ color: 'var(--cor-primaria)' }">
                  {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <!-- CONTEÚDO PRINCIPAL -->
        <main class="flex-1 min-w-0 pb-20">

          <!-- Mobile: barra de categorias sticky horizontal -->
          <div class="lg:hidden sticky top-0 z-20 border-b overflow-x-auto scrollbar-hide"
               :class="isDark ? 'bg-zinc-950/95 border-zinc-800 backdrop-blur-xl' : 'bg-stone-100/95 border-stone-300 backdrop-blur-xl'">
            <div class="flex gap-1 px-4 py-3 min-w-max">
              <button @click="scrollToId('destaques')"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition"
                :style="{ backgroundColor: 'var(--cor-primaria)', color: 'white' }">
                ✦ Destaques
              </button>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-500 hover:bg-stone-200'">
                {{ cat.icone }} {{ cat.nome }}
              </button>
            </div>
          </div>

          <div class="px-6 md:px-10 pt-12">

            <!-- DESTAQUES — grid misto: 1 card grande + vários pequenos -->
            <section id="destaques" class="mb-16">
              <div class="flex items-baseline gap-4 mb-8">
                <h2 class="text-3xl font-black tracking-tight"
                    :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Em Destaque</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-stone-300'"></div>
                <span class="text-xs tracking-[0.25em] uppercase"
                      :style="{ color: 'var(--cor-primaria)' }">Today's picks</span>
              </div>
              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="220px"
                image-height="280px"
                card-height="380px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-300"
                :hover-border-class="'hover:border-[var(--cor-primaria)]/60'"
                :price-class="'font-black text-lg'"
                :show-store-name="false"
                :show-badges="true"
                badge-text="★"
                badge-class="bg-[var(--cor-primaria)] rounded-lg text-white font-black"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- POR TIPO — secções com divisor estilizado -->
            <template v-if="tiposExistentes.length > 0">
              <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                       class="mb-16">
                <div class="flex items-center gap-4 mb-8">
                  <div class="w-10 h-10 rounded-2xl flex items-center justify-center text-xl"
                       :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'">
                    {{ tipoIcon(tipo.nome) }}
                  </div>
                  <div>
                    <h2 class="text-2xl font-black capitalize tracking-tight"
                        :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ tipo.nome }}</h2>
                    <div class="h-0.5 w-12 mt-1 rounded" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
                  </div>
                  <div class="flex-1 h-px ml-2" :class="isDark ? 'bg-zinc-800/60' : 'bg-stone-300/60'"></div>
                </div>
                <ProductSlider
                  :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }"
                  :isDark="isDark"
                  card-width="190px"
                  image-height="220px"
                  card-height="320px"
                  card-border-radius="rounded-2xl"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- POR CATEGORIA -->
            <template v-if="categoriasExistentes.length > 0">
              <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                       class="mb-16">
                <div class="flex items-center gap-4 mb-8">
                  <div class="w-10 h-10 rounded-2xl flex items-center justify-center text-xl"
                       :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'">
                    {{ cat.icone }}
                  </div>
                  <div>
                    <h2 class="text-2xl font-black capitalize tracking-tight"
                        :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ cat.nome }}</h2>
                    <div class="h-0.5 w-12 mt-1 rounded" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
                  </div>
                  <div class="flex-1 h-px ml-2" :class="isDark ? 'bg-zinc-800/60' : 'bg-stone-300/60'"></div>
                </div>
                <ProductSlider
                  :title="cat.nome" :icon="cat.icone"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :isDark="isDark"
                  card-width="190px"
                  image-height="220px"
                  card-height="320px"
                  card-border-radius="rounded-2xl"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- CATÁLOGO — com filtros integrados -->
            <section id="catalogo" class="mb-16">
              <div class="flex items-baseline gap-4 mb-8">
                <h2 class="text-3xl font-black tracking-tight"
                    :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Menu Completo</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-stone-300'"></div>
              </div>
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 xl:grid-cols-4"
                image-height="180px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                :hover-border-class="'hover:border-[var(--cor-primaria)]/40'"
                tab-border-radius="rounded-xl"
                :active-tab-class="'text-white font-bold shadow-lg'"
                :inactive-tab-dark-class="'bg-zinc-800/80 text-zinc-400 hover:text-zinc-200'"
                :inactive-tab-light-class="'bg-stone-200 text-zinc-600 hover:text-zinc-900'"
                input-border-radius="rounded-xl"
                filter-container-radius="rounded-2xl"
                :product-name-hover-class="'group-hover:opacity-80'"
                :price-class="'font-black'"
                spinner-class="text-current opacity-50"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- AVALIAÇÕES -->
            <section id="avaliacoes" class="mb-16">
              <div class="flex items-baseline gap-4 mb-8">
                <h2 class="text-3xl font-black tracking-tight"
                    :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">O que dizem</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-stone-300'"></div>
              </div>
              <AvaliacaoLoja
                :loja-id="lojaId"
                :isDark="isDark"
                summary-border-radius="rounded-2xl"
                form-border-radius="rounded-2xl"
                review-card-border-radius="rounded-2xl"
                button-border-radius="rounded-xl"
                textarea-border-radius="rounded-xl"
                :star-active-class="'text-yellow-400'"
                :star-inactive-class="isDark ? 'text-zinc-700' : 'text-stone-300'"
                :submit-button-class="'text-white font-bold'"
                :own-review-border-class="isDark ? 'bg-zinc-900 border border-zinc-700' : 'bg-stone-200 border border-stone-300'"
                @rating-updated="onRatingUpdated" />
            </section>

            <!-- FOOTER inline -->
            <footer class="border-t pb-8 pt-8"
                    :class="isDark ? 'border-zinc-800' : 'border-stone-300'">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                  <img v-if="loja.logo_url" :src="loja.logo_url" class="w-8 h-8 rounded-lg object-cover" />
                  <div>
                    <p class="font-bold text-sm" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ loja.nome }}</p>
                    <p class="text-xs" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">© {{ new Date().getFullYear() }}</p>
                  </div>
                </div>
                <div class="flex flex-wrap gap-4 text-xs">
                  <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
                    Devoluções
                  </button>
                  <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
                    Termos
                  </button>
                  <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
                    Privacidade
                  </button>
                </div>
              </div>
            </footer>
          </div>
        </main>
      </div>

      <!-- Modal políticas -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-0 md:p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl md:rounded-2xl"
             :class="isDark ? 'bg-zinc-900 border border-zinc-800' : 'bg-white border border-stone-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
            <h3 class="font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-full flex items-center justify-center transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-stone-100 hover:bg-stone-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                   fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao
             : modalPolitica === 'termos'    ? loja.termos_servico
             :                                 loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-stone-100'">
      <p class="text-2xl font-black mb-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Loja não encontrada</p>
      <button @click="$router.back()" class="text-sm hover:underline" :style="{ color: 'var(--cor-primaria)' }">← Voltar</button>
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
  name: 'TemplateRestauranteModerno',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const scrollY  = ref(0)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#e11d48',
      '--cor-secundaria': props.tema?.corSecundaria || '#0f0f0f',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }
    function onScroll ()   { scrollY.value = window.scrollY }

    function isVideo (url) {
      return /\.(mp4|webm|mov|mkv)$/i.test(url || '')
    }

    onMounted (() => window.addEventListener('scroll', onScroll, { passive: true }))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrollY, cssVars, user, toggleDark, isVideo, ...lojaData }
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }

@keyframes slide-loading {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}
.animate-slide-loading { animation: slide-loading 1.2s ease-in-out infinite; }

.sidebar-item { transition: all 0.15s ease; }
.sidebar-item:hover { transform: translateX(2px); }
</style>