<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-stone-50 text-zinc-900'">

    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="log_out()" />
    <ProductInfoCard :produto="selectedProduct" :loja="selectedLoja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <PaginaInfoModal :slug="paginaAberta" :isDark="isDark" @close="paginaAberta = null" />

    <!-- Botão toggle dark/light — canto superior esquerdo, ao lado do hamburger -->
    <div class="fixed top-2 md:top-4 left-16 z-30 flex items-center gap-2">
      <button @click="isDark = !isDark"
        class="w-9 h-9 rounded-xl flex items-center justify-center border transition shadow-md"
        :class="isDark
          ? 'bg-zinc-900 border-zinc-700 text-yellow-400 hover:border-zinc-500'
          : 'bg-white border-stone-300 text-zinc-600 hover:border-stone-400 shadow-sm'">
        <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>
    </div>

    <div class="flex overflow-x-hidden">

      <!-- ═══ SIDEBAR TOGGLE ═══ -->
      <button @click="sidebarAberta = !sidebarAberta"
        class="fixed top-2 md:top-4 left-4 z-30 w-9 h-9 rounded-xl flex items-center justify-center border transition shadow-md"
        :class="isDark
          ? 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
          : 'bg-white border-stone-300 hover:bg-stone-100 shadow-sm'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
             :class="isDark ? 'text-zinc-300' : 'text-zinc-600'"
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- ═══ OVERLAY ═══ -->
      <transition enter-active-class="transition duration-200" enter-from-class="opacity-0"
                  leave-active-class="transition duration-150" leave-to-class="opacity-0">
        <div v-if="sidebarAberta" class="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm"
             @click="sidebarAberta = false" />
      </transition>

      <!-- ═══ SIDEBAR ═══ -->
      <transition enter-active-class="transition duration-300" enter-from-class="-translate-x-full"
                  leave-active-class="transition duration-200" leave-to-class="-translate-x-full">
        <aside v-if="sidebarAberta"
               class="fixed left-0 top-0 h-screen w-64 overflow-y-auto z-30 border-r"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200 shadow-xl'">
          <div class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-base font-bold flex items-center gap-2"
                  :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                Categorias
              </h2>
              <button @click="sidebarAberta = false"
                class="w-7 h-7 rounded-lg flex items-center justify-center transition"
                :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-stone-100 hover:bg-stone-200'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
                     :class="isDark ? 'text-zinc-400' : 'text-zinc-500'"
                     fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div v-if="loadingHome" class="space-y-2">
              <div v-for="n in 5" :key="n" class="h-10 rounded-lg animate-pulse"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-100'"></div>
            </div>

            <ul v-else class="space-y-1">
              <li v-for="cat in categoriasExistentes" :key="cat.value"
                  @click="selectCategoria(cat)"
                  :class="['px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 text-sm',
                           selectedCategoria === cat.value
                             ? 'bg-red-600 text-white'
                             : isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-stone-100 hover:text-zinc-900']">
                <font-awesome-icon :icon="['fas', cat.icon]" class="w-4 h-4 flex-shrink-0" fixed-width />
                {{ cat.label }}
              </li>

              <li @click="clearCategoria"
                  :class="['px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 mt-4 border border-dashed text-sm',
                           !selectedCategoria
                             ? 'border-red-500 text-red-500'
                             : isDark ? 'border-zinc-700 text-zinc-500 hover:border-zinc-600 hover:text-zinc-400' : 'border-stone-300 text-zinc-400 hover:border-stone-400']">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                Ver Todas
              </li>

              <div class="border-t my-3" :class="isDark ? 'border-zinc-800' : 'border-stone-200'"></div>

              <li @click="scrollToSection('produtos')"
                  class="px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 text-sm"
                  :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-stone-100 hover:text-zinc-900'">
                <font-awesome-icon :icon="['fas', 'box']" class="w-4 h-4 flex-shrink-0" fixed-width />
                Produtos
              </li>
              <li @click="scrollToSection('catalogo')"
                  class="px-4 py-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 text-sm"
                  :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-stone-100 hover:text-zinc-900'">
                <font-awesome-icon :icon="['fas', 'store']" class="w-4 h-4 flex-shrink-0" fixed-width />
                Explorar Lojas
              </li>
            </ul>
          </div>

          <!-- Lojas da categoria -->
          <div v-if="selectedCategoria && storesByCategory.length > 0"
               class="p-6 border-t"
               :class="isDark ? 'border-zinc-800' : 'border-stone-200'">
            <h3 class="text-xs font-bold uppercase tracking-wider mb-3"
                :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
              Lojas em {{ selectedCategoriaLabel }}
            </h3>
            <ul class="space-y-2">
              <li v-for="store in storesByCategory" :key="store.id"
                  @click="goToStore(store.id)"
                  class="flex items-center gap-3 p-2 rounded-xl cursor-pointer transition"
                  :class="isDark ? 'hover:bg-zinc-800' : 'hover:bg-stone-100'">
                <img v-if="store.logo_url" :src="store.logo_url" :alt="store.nome"
                     class="w-9 h-9 rounded-lg object-cover flex-shrink-0" />
                <div v-else class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                     :class="isDark ? 'bg-zinc-700' : 'bg-stone-200'">
                  <span class="text-xs font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ store.nome.charAt(0) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium truncate" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ store.nome }}</p>
                  <p class="text-xs truncate" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ store.localizacao }}</p>
                </div>
              </li>
            </ul>
          </div>
        </aside>
      </transition>

      <!-- ═══ MAIN ═══ -->
      <main class="flex-1 overflow-x-hidden">

        <!-- ── PRÉ-VISUALIZAÇÃO (admin → Página inicial) ── -->
        <div v-if="preview || previewErro" class="sticky top-0 z-20 px-4 py-2 text-center text-xs font-semibold"
             :class="previewErro ? 'bg-red-600 text-white' : 'bg-amber-400 text-zinc-900'">
          {{ previewErro || 'Pré-visualização do rascunho: os visitantes ainda vêem a home publicada.' }}
        </div>

        <!-- ── SECÇÕES (montadas no admin → /app/home/) ── -->
        <div v-if="loadingHome" class="py-10 px-6 md:px-12 space-y-10">
          <div class="h-[50vh] rounded-2xl animate-pulse" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
          <div v-for="n in 3" :key="n">
            <div class="h-5 w-40 rounded animate-pulse mb-4"
                 :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
            <div class="flex gap-4">
              <div v-for="m in 4" :key="m" class="w-64 h-48 rounded-2xl animate-pulse flex-shrink-0"
                   :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
            </div>
          </div>
        </div>

        <template v-for="sec in seccoes" :key="sec.id">

          <!-- Hero -->
          <section v-if="sec.tipo === 'hero'" class="relative overflow-hidden">
            <swiper :ref="el => { if (el) heroRefs[sec.id] = el }" :pagination="heroPagination" :modules="modules"
                    :autoplay="{ delay: 3500, disableOnInteraction: false }"
                    :speed="800" effect="slide" class="md:h-[90vh] h-[70vh]"
                    @mouseenter="pararHero(sec.id)" @mouseleave="retomarHero(sec.id)">
              <swiper-slide v-for="(slide, i) in sec.slides" :key="i"
                @click="abrirSlide(slide)" class="cursor-pointer">
                <div class="relative h-full w-full">
                  <template v-if="slide.tipo === 'loja'">
                    <video v-if="isVideo(slide.loja.banner_url)"
                      :src="slide.loja.banner_url" :poster="slide.loja.banner_poster_url"
                      class="w-full h-full object-cover"
                      v-video-visivel muted loop playsinline></video>
                    <img v-else
                      :src="slide.loja.banner_url || bannerPadrao"
                      :alt="slide.loja.nome"
                      class="w-full h-full object-cover" />
                  </template>
                  <img v-else-if="slide.tipo === 'produto'"
                    :src="slide.produto.ficheiro_poster_url || slide.produto.ficheiro_url || produtoPadrao"
                    :alt="slide.produto.nome" class="w-full h-full object-cover" />
                  <img v-else-if="slide.imagem_url" :src="slide.imagem_url" :alt="slide.titulo" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full bg-gradient-to-br from-red-700 via-zinc-900 to-zinc-950"></div>
                  <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-transparent"></div>
                  <div class="absolute inset-0 bg-gradient-to-r from-zinc-950/80 to-transparent"></div>
                  <div class="absolute bottom-0 left-0 p-8 md:p-12 max-w-2xl">
                    <span v-if="slide.tipo !== 'banner' || slide.titulo"
                      class="inline-block px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-full mb-4 uppercase tracking-wider">
                      {{ etiquetaSlide(sec, slide) }}
                    </span>
                    <h1 class="text-4xl md:text-6xl font-bold text-white mb-3 leading-tight">
                      {{ slide.titulo || slide.loja?.nome || slide.produto?.nome }}
                    </h1>
                    <p class="text-base text-zinc-300 mb-4 line-clamp-2">
                      {{ slide.texto || slide.loja?.descricao || slide.produto?.descricao }}
                    </p>
                    <div v-if="slide.tipo === 'loja'" class="flex items-center gap-4 text-zinc-400 text-sm flex-wrap mb-5">
                      <span v-if="slide.loja.localizacao" class="flex items-center gap-1.5">
                        <font-awesome-icon :icon="['fas', 'location-dot']" /> {{ slide.loja.localizacao }}
                      </span>
                      <span class="flex items-center gap-1.5 capitalize">
                        <font-awesome-icon :icon="['fas', iconeCategoria(null, slide.loja.categoria)]" /> {{ slide.loja.categoria }}
                      </span>
                      <span v-if="slide.loja.rating_medio" class="flex items-center gap-1">
                        <svg class="h-4 w-4 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                        {{ slide.loja.rating_medio }}
                      </span>
                    </div>
                    <div v-else-if="slide.tipo === 'produto'" class="flex items-center gap-4 text-zinc-300 text-sm flex-wrap mb-5">
                      <span class="text-xl font-bold text-white">{{ $dinheiro(slide.produto.preco) }}</span>
                      <span v-if="slide.produto.loja" class="flex items-center gap-1.5">
                        <font-awesome-icon :icon="['fas', 'store']" /> {{ slide.produto.loja.nome }}
                      </span>
                    </div>
                    <button v-if="slide.tipo !== 'banner' || slide.link"
                      class="px-6 py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl transition flex items-center gap-2">
                      {{ slide.tipo === 'loja' ? 'Visitar Loja' : slide.tipo === 'produto' ? 'Ver Produto' : 'Saber mais' }}
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </button>
                  </div>
                </div>
              </swiper-slide>
            </swiper>
          </section>

          <!-- Cabeçalho / divisor -->
          <section v-else-if="sec.tipo === 'cabecalho'"
                   :ref="el => { if (el && sec.parametros.ancora) sectionRefs[sec.parametros.ancora] = el }"
                   class="pt-10 pb-2 px-6 md:px-12 border-t"
                   :class="isDark ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-stone-200'">
            <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ sec.titulo }}</h2>
            <p v-if="sec.subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ sec.subtitulo }}</p>
          </section>

          <!-- Grupos: um slider por categoria / tipo -->
          <template v-else-if="sec.grupos">
            <section v-if="sec.titulo" class="py-4 px-6 md:px-12">
              <div v-if="sec.parametros.estilo_titulo === 'divisor'" class="flex items-center gap-3 mb-2">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
                <span class="text-xs font-bold uppercase tracking-widest"
                      :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ sec.titulo }}</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'"></div>
              </div>
              <template v-else>
                <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ sec.titulo }}</h2>
                <p v-if="sec.subtitulo" class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ sec.subtitulo }}</p>
              </template>
            </section>
            <section v-for="(g, gi) in sec.grupos" :key="sec.id + '-' + g.chave"
                     :ref="el => { if (el && sec.conteudo === 'lojas') sectionRefs[g.chave] = el }"
                     :class="sec.conteudo === 'lojas'
                       ? ['py-8 px-6 md:px-12', gi % 2 !== 0 ? (isDark ? 'bg-zinc-900/40' : 'bg-stone-100/60') : '']
                       : ['py-4 px-6 md:px-12', isDark ? 'bg-zinc-900/50' : 'bg-white']">
              <StoreSlider v-if="sec.conteudo === 'lojas'" :title="g.titulo" :icon="iconeCategoria(null, g.chave)"
                :inicial="g.pagina" :endpoint="endpointSeccao(sec.id)" :params="{ grupo: g.chave }"
                :isDark="isDark" @store-click="goToStore($event.id)" />
              <ProductSlider v-else :title="g.titulo"
                :inicial="g.pagina" :endpoint="endpointSeccao(sec.id)" :params="{ grupo: g.chave }"
                :isDark="isDark" @product-click="openProduct($event)" />
            </section>
          </template>

          <!-- Lojas -->
          <section v-else-if="sec.tipo === 'lojas'" class="py-8 px-6 md:px-12">
            <p v-if="sec.subtitulo" class="-mb-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">{{ sec.subtitulo }}</p>
            <StoreSlider :title="sec.titulo || 'Lojas'"
              :inicial="sec.pagina" :endpoint="endpointSeccao(sec.id)"
              :isDark="isDark" @store-click="goToStore($event.id)" />
          </section>

          <!-- Produtos -->
          <section v-else-if="sec.tipo === 'produtos'" data-produtos class="py-4 px-6 md:px-12"
                   :class="isDark ? 'bg-zinc-900/50' : 'bg-white'">
            <ProductSlider :title="sec.titulo || 'Produtos'"
              :inicial="sec.pagina" :endpoint="endpointSeccao(sec.id)"
              :isDark="isDark" @product-click="openProduct($event)" />
          </section>

          <!-- Loja em destaque -->
          <section v-else-if="sec.tipo === 'loja_destaque'" class="py-8 px-6 md:px-12">
            <HomeLojaDestaque :loja="sec.loja" :produtos="sec.produtos" :titulo="sec.titulo" :subtitulo="sec.subtitulo"
              :isDark="isDark" @store-click="goToStore($event.id)" @product-click="openProduct($event)" />
          </section>

          <!-- Categorias -->
          <section v-else-if="sec.tipo === 'categorias'" class="py-8 px-6 md:px-12">
            <HomeCategorias :categorias="sec.categorias" :titulo="sec.titulo" :subtitulo="sec.subtitulo"
              :isDark="isDark" @escolher="filtrarCatalogo" />
          </section>

          <!-- Serviços (marcações) -->
          <section v-else-if="sec.tipo === 'servicos'" class="py-8 px-6 md:px-12" data-teste="home-servicos">
            <HomeServicos :titulo="sec.titulo" :subtitulo="sec.subtitulo" :servicos="sec.servicos" :isDark="isDark" />
          </section>

          <!-- Banners -->
          <section v-else-if="sec.tipo === 'banner'" class="py-8 px-6 md:px-12">
            <HomeBanners :banners="sec.banners" :titulo="sec.titulo" :subtitulo="sec.subtitulo"
              :isDark="isDark" @abrir="abrirLink" />
          </section>
        </template>

        <!-- ── CATÁLOGO COMPLETO ── -->
        <section :ref="el => { if (el) sectionRefs['catalogo'] = el }"
                 class="py-12 px-6 md:px-12 border-t"
                 :class="isDark ? 'border-zinc-800 bg-zinc-900/20' : 'border-stone-200 bg-stone-50'">
          <div class="mb-8 flex flex-wrap items-end gap-4">
            <div class="flex-1 min-w-[220px]">
              <h2 class="text-2xl md:text-3xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ abaCatalogo === 'servicos' ? 'Explorar Serviços' : 'Explorar Lojas' }}</h2>
              <p class="mt-1 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                {{ abaCatalogo === 'servicos' ? 'Cortes, tratamentos, tatuagens… marca a tua hora' : 'Pesquisa e filtra todas as lojas da plataforma' }}</p>
            </div>
            <div class="flex gap-1 rounded-xl p-1" :class="isDark ? 'bg-zinc-800' : 'bg-stone-200'" role="tablist" aria-label="Lojas ou serviços">
              <button v-for="a in [{ k: 'lojas', t: 'Lojas' }, { k: 'servicos', t: 'Serviços' }]" :key="a.k" type="button" role="tab"
                :aria-selected="abaCatalogo === a.k" @click="abaCatalogo = a.k" :data-teste="`catalogo-${a.k}`"
                :class="['px-4 py-1.5 rounded-lg text-sm font-semibold', abaCatalogo === a.k ? 'bg-red-600 text-white' : (isDark ? 'text-zinc-400' : 'text-zinc-600')]">{{ a.t }}</button>
            </div>
          </div>
          <StoreCatalog v-show="abaCatalogo === 'lojas'" ref="catalogo" :isDark="isDark" @store-click="goToStore($event.id)" />
          <ServicoCatalog v-if="abaCatalogo === 'servicos'" :isDark="isDark" />
        </section>

        <!-- ── FOOTER ── -->
        <footer class="border-t py-12 px-6 md:px-12"
                :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-stone-200'">
          <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <!-- logo here -->
              <img :src="isDark ? logoLight : logoDefault" alt="Logo" class="w-32 h-32 object-contain mb-3" />
              <!-- <h3 class="text-lg font-bold mb-3" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Bendi</h3> -->
              <p class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">A melhor plataforma para descobrir lojas e produtos incríveis.</p>
            </div>
            <div>
              <h4 class="text-xs font-semibold uppercase tracking-wider mb-4"
                  :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">Explorar</h4>
              <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                <li @click="scrollToSection('catalogo')" class="hover:text-red-500 cursor-pointer transition">Todas as Lojas</li>
                <li @click="scrollToSection('produtos')" class="hover:text-red-500 cursor-pointer transition">Produtos</li>
              </ul>
            </div>
            <div v-for="sec in seccoesRodape" :key="sec.key">
              <h4 class="text-xs font-semibold uppercase tracking-wider mb-4"
                  :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">{{ sec.label }}</h4>
              <ul class="space-y-2 text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">
                <li v-for="p in sec.paginas" :key="p.slug">
                  <button @click="paginaAberta = p.slug"
                    class="hover:text-red-500 transition text-left">{{ p.titulo }}</button>
                </li>
              </ul>
            </div>
          </div>
          <div class="max-w-7xl mx-auto mt-8 pt-8 border-t text-center text-sm"
               :class="isDark ? 'border-zinc-800 text-zinc-500' : 'border-stone-200 text-zinc-400'">
            © {{ new Date().getFullYear() }} Marketplace. Todos os direitos reservados.
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script>
import { Navigation, Pagination, Autoplay } from 'swiper/modules'
import { Swiper, SwiperSlide } from 'swiper/vue'
import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/effect-fade'

import Profile         from '@/components/profile/UserProfile.vue'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart       from '@/components/cart/multiCart.vue'
import StoreSlider     from '@/components/sliders/StoreSlider.vue'
import ProductSlider   from '@/components/sliders/ProductSlider.vue'
import StoreCatalog    from '@/components/catalog/StoreCatalog.vue'
import ServicoCatalog  from '@/components/catalog/ServicoCatalog.vue'
import HomeServicos    from '@/components/home/HomeServicos.vue'
import PaginaInfoModal from '@/components/paginas/PaginaInfoModal.vue'
import HomeLojaDestaque from '@/components/home/HomeLojaDestaque.vue'
import HomeCategorias from '@/components/home/HomeCategorias.vue'
import HomeBanners from '@/components/home/HomeBanners.vue'
import logoDefault from '@/assets/img/login/logo_final_4k.png'
import logoLight from '@/assets/img/login/logo_final_4k_light.png'
import api from '@/services/api'
import { DEFAULT_BANNER, DEFAULT_PRODUTO } from '@/services/media'
import { iconeCategoria } from '@/utils/icones'

export default {
  name: 'AppHome',
  components: { Swiper, SwiperSlide, Profile, ProductInfoCard, MultiCart, StoreSlider, ProductSlider, StoreCatalog, PaginaInfoModal,
    ServicoCatalog, HomeServicos,
                HomeLojaDestaque, HomeCategorias, HomeBanners },

  data () {
    return {
      isDark: true,   // dark por defeito — pode ser lido de localStorage se quiseres
      seccoes: [],              // secções da home (admin → /app/home/)
      abaCatalogo: 'lojas',     // pesquisa: lojas ou serviços
      categoriasExistentes: [],
      loadingHome: true,
      heroRefs: {},
      preview: false,           // ?preview=1 → rascunho do admin
      previewErro: '',
      bannerPadrao: DEFAULT_BANNER,
      produtoPadrao: DEFAULT_PRODUTO,
      selectedProduct: null,
      selectedLoja: null,
      selectedCategoria: null,
      storesByCategory: [],
      sidebarAberta: false,
      user: {},
      sectionRefs: {},
      logoDefault,
      logoLight,
      paginasRodape: [],
      paginaAberta: null,
    }
  },

  computed: {
    // Colunas "Suporte" e "Legal" do rodapé — só páginas activas no admin
    seccoesRodape () {
      return [
        { key: 'suporte', label: 'Suporte' },
        { key: 'legal',   label: 'Legal' },
      ]
        .map(s => ({ ...s, paginas: this.paginasRodape.filter(p => p.seccao === s.key).sort((a, b) => a.ordem - b.ordem) }))
        .filter(s => s.paginas.length)
    },

    selectedCategoriaLabel () {
      return this.categoriasExistentes.find(c => c.value === this.selectedCategoria)?.label || ''
    },
  },

  async created () {
    const user = localStorage.getItem('user')
    this.user = user ? JSON.parse(user) : {}
    // Persistir preferência de tema
    const savedDark = localStorage.getItem('home_dark_mode')
    if (savedDark !== null) this.isDark = savedDark === 'true'

    await Promise.all([
      this.fetchHome(),
      this.fetchPaginasRodape(),
    ])
  },

  watch: {
    isDark (val) {
      localStorage.setItem('home_dark_mode', String(val))
    }
  },

  methods: {
    goToStore (id) { this.sidebarAberta = false; this.$router.push(`/loja/${id}`) },

    async fetchPaginasRodape () {
      try {
        const { data } = await api.get('/app/paginas/')
        this.paginasRodape = data || []
      } catch (e) { this.paginasRodape = [] }
    },
    openProduct (produto) { this.selectedProduct = produto; this.selectedLoja = produto.loja },
    iconeCategoria,

    scrollToSection (key) {
      // sem cabeçalho "produtos" no layout publicado, vai para a primeira secção de produtos
      const el = this.sectionRefs[key] || (key === 'produtos' ? this.$el.querySelector?.('[data-produtos]') : null)
      if (el) { el.scrollIntoView({ behavior: 'smooth' }); this.sidebarAberta = false }
    },

    async selectCategoria (cat) {
      this.selectedCategoria = cat.value
      await this.fetchStoresByCategory(cat.value)
      // sem slider dessa categoria no layout publicado, filtra o catálogo
      if (this.sectionRefs[cat.value]) this.scrollToSection(cat.value)
      else this.filtrarCatalogo(cat.value)
    },

    clearCategoria () { this.selectedCategoria = null; this.storesByCategory = [] },

    async fetchStoresByCategory (categoria) {
      try {
        const { data } = await api.get(`/app/loja/?categoria=${encodeURIComponent(categoria)}&limit=10`)
        this.storesByCategory = data.results || data
      } catch (e) { console.error(e) }
    },

    pararHero  (id) { this.heroRefs[id]?.swiper?.autoplay.stop() },
    retomarHero (id) { this.heroRefs[id]?.swiper?.autoplay.start() },

    abrirSlide (slide) {
      if (slide.tipo === 'loja') this.goToStore(slide.id)
      else if (slide.tipo === 'produto' && slide.produto) this.openProduct(slide.produto)
      else if (slide.link) this.abrirLink(slide.link)
    },

    // links dos banners (o admin só aceita "/caminho" ou http(s))
    abrirLink (link) {
      if (/^https?:\/\//i.test(link)) window.open(link, '_blank', 'noopener')
      else if (link.startsWith('/') && !link.startsWith('//')) this.$router.push(link)
    },

    // grelha de categorias → catálogo filtrado
    filtrarCatalogo (categoria) {
      this.$refs.catalogo?.selectCategoria(categoria)
      this.scrollToSection('catalogo')
    },

    etiquetaSlide (sec, slide) {
      if (slide.tipo === 'produto') return 'Produto em destaque'
      if (slide.tipo === 'banner') return 'Novidade'
      return { novas: 'Nova Loja', populares: 'Popular', mais_vendidas: 'Mais vendida', mais_favoritas: 'Favorita', abertas: 'Aberta agora' }[sec.criterio] || 'Em destaque'
    },

    endpointSeccao (id) {
      return this.preview ? `/app/admin/home/preview/seccao/${id}/` : `/app/home/seccao/${id}/`
    },

    async fetchHome () {
      this.preview = this.$route.query.preview === '1'
      try {
        let data
        if (this.preview) {
          try {
            ({ data } = await api.get('/app/admin/home/preview/'))
          } catch (e) {
            this.previewErro = 'Sem permissão para pré-visualizar: estás a ver a home publicada.'
            this.preview = false
          }
        }
        if (!data) ({ data } = await api.get('/app/home/'))
        this.seccoes = data.seccoes || []
        this.categoriasExistentes = (data.categorias_lojas || []).map(c => ({
          value: c.valor, label: c.nome, icon: iconeCategoria(null, c.valor),
        }))
      } catch (e) { console.error(e) }
      finally { this.loadingHome = false }
    },

    log_out () {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      this.user = {}
      this.$router.push('/login')
    },
    isVideo (url) {
      return /\.(mp4|webm|mov|mkv)$/i.test(url || '')
    },
  },

  setup () {
    return {
      heroPagination: { clickable: true },
      modules: [Navigation, Pagination, Autoplay],
    }
  },
}
</script>

<style scoped>
.swiper {
  --swiper-pagination-bullet-inactive-color: rgba(255,255,255,0.4);
  --swiper-pagination-color: #dc2626;
  --swiper-pagination-bullet-size: 10px;
  --swiper-pagination-bullet-horizontal-gap: 6px;
}
.swiper-pagination { bottom: 30px !important; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>