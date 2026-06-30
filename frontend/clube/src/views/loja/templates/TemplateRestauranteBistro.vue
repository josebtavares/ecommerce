<!-- TemplateRestauranteBistro — Estilo menu de bistro parisiense, tipografia serif, tons quentes, layout de duas colunas -->
<template>
  <div class="min-h-screen transition-colors duration-500"
       :class="isDark ? 'bg-[#1a1410] text-amber-50' : 'bg-[#fdf6ec] text-stone-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-[#1a1410]' : 'bg-[#fdf6ec]'">
      <div class="text-center">
        <div class="w-16 h-16 mx-auto mb-4 border-2 border-amber-600/30 rounded-full flex items-center justify-center">
          <div class="w-8 h-8 border-2 border-t-transparent border-amber-600 rounded-full animate-spin"></div>
        </div>
        <p class="font-serif text-sm italic" :class="isDark ? 'text-amber-600/60' : 'text-amber-800/60'">
          Un moment…
        </p>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HEADER bistro — topo fixo com moldura decorativa ── -->
      <header class="fixed top-0 left-0 right-0 z-30 transition-all duration-500"
              :class="scrolled
                ? (isDark ? 'bg-[#1a1410]/95 backdrop-blur-xl shadow-lg shadow-black/30' : 'bg-[#fdf6ec]/95 backdrop-blur-xl shadow-md shadow-amber-900/10')
                : 'bg-transparent'">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <!-- Esquerda: voltar + toggle -->
          <div class="flex items-center gap-3">
            <button @click="$router.back()"
              class="text-xs tracking-[0.3em] uppercase transition-colors font-medium"
              :class="isDark ? 'text-amber-600/70 hover:text-amber-400' : 'text-amber-900/60 hover:text-amber-900'">
              ← Voltar
            </button>
            <button @click="toggleDark"
              class="w-7 h-7 rounded-full border flex items-center justify-center transition"
              :class="isDark ? 'border-amber-800 text-amber-500 hover:border-amber-600' : 'border-amber-300 text-amber-700 hover:border-amber-600'">
              <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
          </div>

          <!-- Centro: nome ao scroll -->
          <span v-if="scrolled && loja"
                class="absolute left-1/2 -translate-x-1/2 font-serif italic text-lg pointer-events-none"
                :class="isDark ? 'text-amber-200' : 'text-amber-900'">
            {{ loja.nome }}
          </span>

          <div class="w-24"></div>
        </div>
      </header>

      <!-- ── HERO bistro — layout dividido, imagem + texto em colunas ── -->
      <section class="pt-16 min-h-screen grid grid-cols-1 lg:grid-cols-2">
        <!-- Coluna esquerda: imagem full-height -->
        <div class="relative h-[50vh] lg:h-screen lg:sticky lg:top-0 overflow-hidden">
          <video v-if="isVideo(loja.banner_url)"
            :src="loja.banner_url"
            class="w-full h-full object-cover"
            autoplay muted loop playsinline></video>
          <img v-else
            :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
            :alt="loja.nome" class="w-full h-full object-cover" />
          <!-- Moldura decorativa sobre a imagem -->
          <div class="absolute inset-4 border pointer-events-none opacity-50"
               :class="isDark ? 'border-amber-600/40' : 'border-amber-900/30'"></div>
          <!-- Canto decorativo -->
          <div class="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 pointer-events-none"
               :class="isDark ? 'border-amber-500' : 'border-amber-800'"></div>
          <div class="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 pointer-events-none"
               :class="isDark ? 'border-amber-500' : 'border-amber-800'"></div>

          <div v-if="loja.entrega_ativa"
               class="absolute bottom-8 left-1/2 -translate-x-1/2 px-4 py-2 backdrop-blur-md rounded-full border text-xs font-medium whitespace-nowrap"
               :class="isDark ? 'bg-emerald-900/60 border-emerald-500/30 text-emerald-300' : 'bg-emerald-100/80 border-emerald-400/30 text-emerald-800'">
            ✓ Entrega disponível
          </div>
        </div>

        <!-- Coluna direita: texto + info -->
        <div class="flex flex-col justify-center px-8 md:px-16 py-16 lg:py-24 lg:min-h-screen">
          <!-- Ornamento decorativo topo -->
          <div class="flex items-center gap-3 mb-8">
            <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/40' : 'bg-amber-300/60'"></div>
            <span class="text-amber-600 text-lg">✦</span>
            <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/40' : 'bg-amber-300/60'"></div>
          </div>

          <p class="text-xs tracking-[0.4em] uppercase mb-4"
             :class="isDark ? 'text-amber-600/70' : 'text-amber-700/70'">
            {{ loja.categoria }}
            <span v-if="loja.localizacao" class="ml-3">· {{ loja.localizacao }}</span>
          </p>

          <h1 class="font-serif leading-tight mb-6"
              style="font-size: clamp(3rem, 7vw, 6rem); font-weight: 400; font-style: italic;"
              :class="isDark ? 'text-amber-50' : 'text-stone-900'">
            {{ loja.nome }}
          </h1>

          <p v-if="loja.descricao" class="text-base leading-relaxed mb-10 max-w-md"
             :class="isDark ? 'text-amber-200/60' : 'text-stone-600'">
            {{ loja.descricao }}
          </p>

          <!-- Stats em grid 3x1 -->
          <div class="grid grid-cols-3 gap-4 mb-10 border-y py-6"
               :class="isDark ? 'border-amber-800/30' : 'border-amber-200'">
            <div v-if="loja.rating_medio" class="text-center">
              <p class="font-serif text-3xl italic"
                 :class="isDark ? 'text-amber-300' : 'text-amber-700'">{{ loja.rating_medio }}</p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-amber-700' : 'text-amber-600/70'">Avaliação</p>
            </div>
            <div v-if="loja.total_avaliacoes" class="text-center border-x"
                 :class="isDark ? 'border-amber-800/30' : 'border-amber-200'">
              <p class="font-serif text-3xl italic"
                 :class="isDark ? 'text-amber-300' : 'text-amber-700'">{{ loja.total_avaliacoes }}</p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-amber-700' : 'text-amber-600/70'">Reviews</p>
            </div>
            <div v-if="opcoesEntrega.length" class="text-center">
              <p class="font-serif text-3xl italic"
                 :class="isDark ? 'text-amber-300' : 'text-amber-700'">
                {{ opcoesEntrega.find(o => o.preco == 0) ? '0€' : formatPrice(opcoesEntrega[0]?.preco) }}
              </p>
              <p class="text-[10px] tracking-[0.3em] uppercase mt-1"
                 :class="isDark ? 'text-amber-700' : 'text-amber-600/70'">Entrega</p>
            </div>
          </div>

          <!-- CTAs -->
          <div class="flex flex-wrap gap-4">
            <button @click="scrollToId('menu')"
              class="px-8 py-3 font-serif italic text-white text-base transition-all hover:scale-[1.02] hover:shadow-lg"
              :style="{ backgroundColor: 'var(--cor-primaria)' }">
              Ver o Menu →
            </button>
            <button @click="scrollToId('avaliacoes')"
              class="px-8 py-3 font-serif italic text-base border transition-all hover:scale-[1.02]"
              :class="isDark ? 'border-amber-700 text-amber-300 hover:bg-amber-900/30' : 'border-amber-400 text-amber-800 hover:bg-amber-100'">
              ★ Avaliações
            </button>
          </div>

          <!-- Ornamento decorativo fundo -->
          <div class="flex items-center gap-3 mt-12">
            <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/40' : 'bg-amber-300/60'"></div>
            <span class="text-amber-600 text-sm">◆ ◆ ◆</span>
            <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/40' : 'bg-amber-300/60'"></div>
          </div>
        </div>
      </section>

      <!-- ── MENU PRINCIPAL — layout de duas colunas com sidebar ── -->
      <div id="menu" class="flex">

        <!-- Mini sidebar do menu (desktop) -->
        <aside class="hidden xl:block sticky top-0 h-screen w-56 flex-shrink-0 border-r"
               :class="isDark ? 'bg-[#1a1410] border-amber-900/30' : 'bg-[#fdf6ec] border-amber-200'">
          <div class="p-6">
            <div class="flex items-center gap-2 mb-6">
              <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
              <span class="font-serif italic text-sm" :class="isDark ? 'text-amber-600' : 'text-amber-700'">Menu</span>
              <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
            </div>

            <nav class="space-y-1">
              <button @click="scrollToId('destaques')"
                class="w-full text-left px-3 py-2 text-sm font-medium rounded-lg transition"
                :class="isDark ? 'text-amber-400 hover:bg-amber-900/30' : 'text-amber-800 hover:bg-amber-100'"
                :style="{ fontFamily: 'Georgia, serif', fontStyle: 'italic' }">
                ✦ Destaques
              </button>
              <button v-for="tipo in tiposExistentes" :key="tipo.id"
                @click="scrollToId('tipo-' + tipo.id)"
                class="w-full text-left px-3 py-2 text-sm rounded-lg transition capitalize"
                :class="isDark ? 'text-amber-300/70 hover:bg-amber-900/30 hover:text-amber-200' : 'text-amber-800/70 hover:bg-amber-100 hover:text-amber-900'"
                :style="{ fontFamily: 'Georgia, serif' }">
                {{ tipoIcon(tipo.nome) }} {{ tipo.nome }}
              </button>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="w-full text-left px-3 py-2 text-sm rounded-lg transition capitalize"
                :class="isDark ? 'text-amber-300/70 hover:bg-amber-900/30 hover:text-amber-200' : 'text-amber-800/70 hover:bg-amber-100 hover:text-amber-900'"
                :style="{ fontFamily: 'Georgia, serif' }">
                {{ cat.icone }} {{ cat.nome }}
              </button>
            </nav>

            <div class="mt-8 border-t pt-6"
                 :class="isDark ? 'border-amber-900/30' : 'border-amber-200'">
              <div v-for="m in metodosPagamento.slice(0, 3)" :key="m.id"
                   class="flex items-center gap-2 py-1 text-xs"
                   :class="isDark ? 'text-amber-700' : 'text-amber-600'">
                <span>{{ metodoPagamentoIcon(m.tipo) }}</span>
                <span>{{ m.tipo }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- Conteúdo principal do menu -->
        <main class="flex-1 min-w-0 pb-20">

          <!-- Mobile: tabs horizontais -->
          <div class="xl:hidden sticky top-0 z-20 overflow-x-auto scrollbar-hide border-b"
               :class="isDark ? 'bg-[#1a1410]/95 border-amber-900/30 backdrop-blur-xl' : 'bg-[#fdf6ec]/95 border-amber-200 backdrop-blur-xl'">
            <div class="flex gap-2 px-4 py-3 min-w-max">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-4 py-1.5 rounded-full text-xs font-medium whitespace-nowrap border transition"
                :class="isDark ? 'border-amber-800/50 text-amber-400 hover:bg-amber-900/40' : 'border-amber-300 text-amber-800 hover:bg-amber-100'"
                :style="{ fontFamily: 'Georgia, serif', fontStyle: 'italic' }">
                {{ cat.icone }} {{ cat.nome }}
              </button>
            </div>
          </div>

          <div class="px-6 md:px-12 pt-12">

            <!-- Destaques -->
            <section id="destaques" class="mb-16">
              <div class="flex items-center gap-4 mb-8">
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                <h2 class="font-serif italic text-2xl px-4"
                    :class="isDark ? 'text-amber-200' : 'text-stone-800'">✦ Destaques da Casa</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
              </div>
              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="210px"
                image-height="260px"
                card-height="360px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-300"
                hover-border-class="hover:border-amber-500/40"
                price-class="text-amber-600 font-bold"
                badge-class="bg-amber-600 rounded-lg text-white font-bold"
                badge-text="Chef"
                :show-store-name="false"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- Por tipo -->
            <template v-if="tiposExistentes.length > 0">
              <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                       class="mb-16">
                <div class="flex items-center gap-4 mb-8">
                  <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                  <h2 class="font-serif italic text-2xl capitalize px-4"
                      :class="isDark ? 'text-amber-200' : 'text-stone-800'">
                    {{ tipoIcon(tipo.nome) }} {{ tipo.nome }}
                  </h2>
                  <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                </div>
                <ProductSlider
                  :title="tipo.nome"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }"
                  :isDark="isDark"
                  card-width="185px"
                  image-height="220px"
                  card-height="320px"
                  card-border-radius="rounded-2xl"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                  hover-border-class="hover:border-amber-500/40"
                  price-class="text-amber-600 font-bold"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- Por categoria -->
            <template v-if="categoriasExistentes.length > 0">
              <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                       class="mb-16">
                <div class="flex items-center gap-4 mb-8">
                  <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                  <h2 class="font-serif italic text-2xl capitalize px-4"
                      :class="isDark ? 'text-amber-200' : 'text-stone-800'">
                    {{ cat.icone }} {{ cat.nome }}
                  </h2>
                  <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                </div>
                <ProductSlider
                  :title="cat.nome"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :isDark="isDark"
                  card-width="185px"
                  image-height="220px"
                  card-height="320px"
                  card-border-radius="rounded-2xl"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                  hover-border-class="hover:border-amber-500/40"
                  price-class="text-amber-600 font-bold"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- Menu completo / catálogo -->
            <section id="catalogo" class="mb-16">
              <div class="flex items-center gap-4 mb-8">
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                <h2 class="font-serif italic text-2xl px-4"
                    :class="isDark ? 'text-amber-200' : 'text-stone-800'">◆ Menu Completo</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
              </div>
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4"
                image-height="180px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                hover-border-class="hover:border-amber-500/40"
                tab-border-radius="rounded-full"
                active-tab-class="bg-amber-600 text-white"
                :inactive-tab-dark-class="'bg-[#2a1f14] text-amber-400/80 hover:text-amber-200 border border-amber-900/40'"
                :inactive-tab-light-class="'bg-amber-100 text-amber-800 hover:text-amber-900 border border-amber-200'"
                active-sub-tab-class="bg-amber-600/80 text-white"
                input-border-radius="rounded-xl"
                input-focus-class="focus:border-amber-500"
                filter-container-radius="rounded-2xl"
                product-name-hover-class="group-hover:text-amber-500"
                price-class="text-amber-600 font-bold"
                spinner-class="text-amber-600"
                indicator-active-class="bg-amber-600/20 text-amber-500"
                clear-all-class="text-amber-500 hover:text-amber-400"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- Avaliações -->
            <section id="avaliacoes" class="mb-16">
              <div class="flex items-center gap-4 mb-8">
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                <h2 class="font-serif italic text-2xl px-4"
                    :class="isDark ? 'text-amber-200' : 'text-stone-800'">★ Avaliações</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
              </div>
              <AvaliacaoLoja
                :loja-id="lojaId"
                :isDark="isDark"
                summary-border-radius="rounded-2xl"
                form-border-radius="rounded-2xl"
                review-card-border-radius="rounded-2xl"
                button-border-radius="rounded-xl"
                textarea-border-radius="rounded-xl"
                star-active-class="text-amber-500"
                :star-inactive-class="isDark ? 'text-amber-900/50' : 'text-amber-200'"
                progress-bar-class="bg-amber-500"
                submit-button-class="bg-amber-600 hover:bg-amber-500 text-white"
                :own-review-border-class="isDark ? 'bg-[#241a0f] border border-amber-700/40' : 'bg-amber-50 border border-amber-200'"
                own-badge-class="bg-amber-600/20 text-amber-500"
                link-class="text-amber-500 hover:text-amber-400"
                @rating-updated="onRatingUpdated" />
            </section>

            <!-- Footer -->
            <footer class="border-t py-10 text-center"
                    :class="isDark ? 'border-amber-900/30' : 'border-amber-200'">
              <div class="flex items-center gap-4 justify-center mb-6">
                <div class="flex-1 h-px max-w-20" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
                <span class="font-serif italic text-lg" :class="isDark ? 'text-amber-400' : 'text-amber-700'">{{ loja.nome }}</span>
                <div class="flex-1 h-px max-w-20" :class="isDark ? 'bg-amber-800/30' : 'bg-amber-200'"></div>
              </div>
              <div class="flex justify-center gap-6 text-xs"
                   :class="isDark ? 'text-amber-800' : 'text-amber-500'">
                <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                  class="hover:underline">Devoluções</button>
                <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                  class="hover:underline">Termos</button>
                <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                  class="hover:underline">Privacidade</button>
              </div>
              <p class="text-xs mt-4" :class="isDark ? 'text-amber-900/60' : 'text-amber-400/60'">
                © {{ new Date().getFullYear() }} {{ loja.nome }}
              </p>
            </footer>
          </div>
        </main>
      </div>

      <!-- Modal políticas -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-0 md:p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl md:rounded-2xl"
             :class="isDark ? 'bg-[#211811] border border-amber-900/30' : 'bg-[#fdf6ec] border border-amber-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-[#211811] border-amber-900/30' : 'bg-[#fdf6ec] border-amber-200'">
            <h3 class="font-serif italic" :class="isDark ? 'text-amber-200' : 'text-stone-800'">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-full flex items-center justify-center transition"
              :class="isDark ? 'bg-amber-900/30 hover:bg-amber-900/50 text-amber-400' : 'bg-amber-100 hover:bg-amber-200 text-amber-700'">
              ×
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-amber-200/70' : 'text-stone-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao
             : modalPolitica === 'termos'    ? loja.termos_servico
             :                                 loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-[#1a1410]' : 'bg-[#fdf6ec]'">
      <p class="font-serif italic text-2xl mb-4" :class="isDark ? 'text-amber-400' : 'text-amber-800'">Bistro não encontrado</p>
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
  name: 'TemplateRestauranteBistro',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#d97706',
      '--cor-secundaria': props.tema?.corSecundaria || '#292524',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }
    function onScroll ()   { scrolled.value = window.scrollY > 80 }

    function isVideo (url) {
      return /\.(mp4|webm|mov|mkv)$/i.test(url || '')
    }

    onMounted (() => window.addEventListener('scroll', onScroll, { passive: true }))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrolled, cssVars, user, toggleDark, isVideo, ...lojaData }
  }
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>