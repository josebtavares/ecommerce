<!-- TemplateModaEditorial.vue — REMODELADO
     Distinto do Minimalista: grid editorial de REVISTA com colunas variáveis,
     números de secção grandes, tipografia condensada + sans-serif em contraste,
     hero full-bleed com texto sobre imagem (não split).
-->
<template>
  <div class="min-h-screen transition-colors duration-500"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-zinc-100 text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-zinc-100'">
      <div class="flex gap-1 justify-center">
        <div v-for="i in 5" :key="i" class="w-0.5 h-8 rounded-full animate-pulse"
             :style="{ background: 'var(--cor-primaria)', animationDelay: (i * 0.12) + 's' }"></div>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO full-bleed — imagem + overlay + texto em diagonal ── -->
      <section class="relative h-screen overflow-hidden">
        <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
             :alt="loja.nome"
             class="absolute inset-0 w-full h-full object-cover transition-transform duration-[12s] scale-105" />

        <!-- Overlay escuro em gradiente diagonal -->
        <div class="absolute inset-0"
             :class="isDark
               ? 'bg-gradient-to-br from-zinc-950/90 via-zinc-950/60 to-transparent'
               : 'bg-gradient-to-br from-zinc-900/80 via-zinc-900/50 to-transparent'" />
        <div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent" />

        <!-- Nav -->
        <div class="absolute top-0 left-0 right-0 flex items-center justify-between px-8 py-6 z-10">
          <button @click="$router.back()"
            class="text-[9px] tracking-[0.4em] uppercase font-bold transition-colors"
            :class="isDark ? 'text-zinc-400 hover:text-white' : 'text-white/70 hover:text-white'">
            ← Voltar
          </button>
          <button @click="toggleDark"
            class="w-8 h-8 rounded-full border flex items-center justify-center transition"
            :class="isDark ? 'border-zinc-700 text-zinc-400 hover:border-zinc-400 hover:text-white' : 'border-white/30 text-white hover:border-white'">
            <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
        </div>

        <!-- Número editorial gigante no canto -->
        <div class="absolute bottom-24 right-8 font-black text-white pointer-events-none select-none leading-none"
             style="font-size:clamp(8rem,20vw,18rem);opacity:0.05;letter-spacing:-0.06em">
          {{ new Date().getFullYear() }}
        </div>

        <!-- Conteúdo textual no canto inferior esquerdo -->
        <div class="absolute bottom-0 left-0 right-0 px-8 md:px-14 pb-14 z-10">
          <!-- Issue label -->
          <div class="flex items-center gap-3 mb-5">
            <div class="h-px w-10" style="background:var(--cor-primaria)"></div>
            <span class="text-[9px] tracking-[0.5em] uppercase font-bold text-white/50">
              {{ loja.categoria }} · {{ loja.localizacao || 'Editorial' }}
            </span>
          </div>

          <h1 class="text-white font-black tracking-tighter leading-[0.88] mb-5"
              style="font-size:clamp(3.5rem,10vw,9rem)">
            {{ loja.nome }}
          </h1>

          <div class="flex items-end justify-between flex-wrap gap-6">
            <div>
              <p v-if="loja.descricao" class="text-sm font-light text-white/50 max-w-lg leading-relaxed mb-6">
                {{ loja.descricao.substring(0, 130) }}{{ loja.descricao.length > 130 ? '…' : '' }}
              </p>
              <div class="flex gap-3">
                <button @click="scrollToId('colecao')"
                  class="px-7 py-3 font-bold text-sm tracking-wider uppercase text-white transition-all hover:scale-[1.02]"
                  :style="{ background: 'var(--cor-primaria)' }">
                  Ver Coleção →
                </button>
                <button @click="scrollToId('catalogo')"
                  class="px-7 py-3 font-bold text-sm tracking-wider uppercase border text-white border-white/25 transition-all hover:bg-white/10">
                  Catálogo
                </button>
              </div>
            </div>

            <!-- Stats coluna direita -->
            <div class="flex gap-8 pb-1">
              <div v-if="loja.rating_medio" class="text-right">
                <p class="text-5xl font-black text-white leading-none">{{ loja.rating_medio }}</p>
                <p class="text-[8px] tracking-[0.35em] uppercase text-white/30 mt-1.5">Rating</p>
              </div>
              <div v-if="loja.total_avaliacoes" class="text-right">
                <p class="text-5xl font-black text-white leading-none">{{ loja.total_avaliacoes }}</p>
                <p class="text-[8px] tracking-[0.35em] uppercase text-white/30 mt-1.5">Reviews</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── ÍNDICE / NAVEGAÇÃO horizontal ── -->
      <nav class="border-b overflow-x-auto scrollbar-hide"
           :class="isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-100 border-zinc-300'">
        <div class="flex min-w-max">
          <button @click="scrollToId('colecao')"
            class="px-5 py-4 text-[9px] tracking-[0.35em] uppercase font-bold border-r transition whitespace-nowrap"
            :class="isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900' : 'border-zinc-300 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'">
            Destaques
          </button>
          <button v-for="tipo in tiposExistentes" :key="tipo.id"
            @click="scrollToId('tipo-' + tipo.id)"
            class="px-5 py-4 text-[9px] tracking-[0.35em] uppercase font-bold border-r transition capitalize whitespace-nowrap"
            :class="isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900' : 'border-zinc-300 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'">
            {{ tipo.nome }}
          </button>
          <button v-for="cat in categoriasExistentes" :key="cat.id"
            @click="scrollToId('cat-' + cat.id)"
            class="px-5 py-4 text-[9px] tracking-[0.35em] uppercase font-bold border-r transition capitalize whitespace-nowrap"
            :class="isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900' : 'border-zinc-300 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'">
            {{ cat.nome }}
          </button>
          <button @click="scrollToId('catalogo')"
            class="px-5 py-4 text-[9px] tracking-[0.35em] uppercase font-bold border-r transition whitespace-nowrap"
            :class="isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900' : 'border-zinc-300 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'">
            Catálogo
          </button>
          <button @click="scrollToId('avaliacoes')"
            class="px-5 py-4 text-[9px] tracking-[0.35em] uppercase font-bold transition whitespace-nowrap"
            :class="isDark ? 'text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'">
            Reviews
          </button>
        </div>
      </nav>

      <!-- ── MAIN ── -->
      <main>

        <!-- Sobre — layout grid editorial assimétrico -->
        <section class="border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
          <div class="grid grid-cols-1 md:grid-cols-12">
            <!-- Número de secção lateral -->
            <div class="hidden md:flex md:col-span-2 items-start justify-center pt-10 border-r"
                 :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
              <span class="font-black text-5xl" :style="{ color: 'var(--cor-primaria)', opacity: '0.3' }">00</span>
            </div>
            <!-- Conteúdo -->
            <div class="md:col-span-10 px-8 md:px-12 py-12 grid grid-cols-1 md:grid-cols-2 gap-10">
              <div>
                <p class="text-[9px] tracking-[0.5em] uppercase font-bold mb-5" style="color:var(--cor-primaria)">About</p>
                <p class="text-2xl font-light leading-relaxed" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">
                  {{ loja.descricao || 'Curadoria editorial de peças que definem a temporada.' }}
                </p>
              </div>
              <div class="space-y-6">
                <div v-if="opcoesEntrega.length">
                  <p class="text-[9px] tracking-[0.4em] uppercase font-bold mb-4" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Envio</p>
                  <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="flex justify-between items-center py-2.5 border-b last:border-0"
                       :class="isDark ? 'border-zinc-800' : 'border-zinc-200'">
                    <span class="text-sm" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">{{ opcao.nome }}</span>
                    <span class="text-sm font-bold" style="color:var(--cor-primaria)">{{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}</span>
                  </div>
                </div>
                <div v-if="metodosPagamento.length">
                  <p class="text-[9px] tracking-[0.4em] uppercase font-bold mb-3" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Pagamento</p>
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="m in metodosPagamento" :key="m.id"
                          class="px-2.5 py-1 rounded text-xs font-bold uppercase"
                          :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-200 text-zinc-700'">{{ m.tipo }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Destaques -->
        <section id="colecao" class="border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
          <div class="grid grid-cols-1 md:grid-cols-12">
            <div class="hidden md:flex md:col-span-2 items-start justify-center pt-10 border-r"
                 :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
              <span class="font-black text-5xl" :style="{ color: 'var(--cor-primaria)', opacity: '0.3' }">01</span>
            </div>
            <div class="md:col-span-10 px-8 md:px-12 pt-10 pb-14">
              <div class="flex items-end gap-5 mb-10">
                <div>
                  <p class="text-[9px] tracking-[0.5em] uppercase font-bold mb-2" style="color:var(--cor-primaria)">New Season</p>
                  <h2 class="text-4xl font-black tracking-tight leading-none" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Destaques</h2>
                </div>
                <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-300'"></div>
              </div>
              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="230px"
                image-height="290px"
                card-height="395px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-2xl transition-all duration-500"
                hover-border-class=""
                product-name-class="font-bold tracking-wide uppercase text-xs"
                :price-class="isDark ? 'font-black text-sm' : 'font-black text-sm text-zinc-800'"
                badge-text="NEW"
                badge-class="rounded-none px-2 py-0.5 text-white text-[9px] font-black tracking-widest"
                :show-store-name="false"
                :show-stock="false"
                @product-click="selectedProduct = $event" />
            </div>
          </div>
        </section>

        <!-- Por tipo -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                   class="border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
            <div class="grid grid-cols-1 md:grid-cols-12">
              <div class="hidden md:flex md:col-span-2 items-start justify-center pt-10 border-r"
                   :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
                <span class="font-black text-5xl" :style="{ color: 'var(--cor-primaria)', opacity: '0.3' }">
                  {{ String(idx + 2).padStart(2, '0') }}
                </span>
              </div>
              <div class="md:col-span-10 px-8 md:px-12 pt-10 pb-14">
                <div class="flex items-end gap-5 mb-10">
                  <h2 class="text-4xl font-black tracking-tight capitalize leading-none" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ tipo.nome }}</h2>
                  <span class="text-6xl font-black opacity-10 leading-none" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                    {{ tipoIcon(tipo.nome) }}
                  </span>
                  <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-300'"></div>
                </div>
                <ProductSlider
                  :title="tipo.nome"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }"
                  :isDark="isDark"
                  card-width="200px"
                  image-height="260px"
                  card-height="360px"
                  card-border-radius="rounded-none"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                  hover-border-class=""
                  product-name-class="font-bold tracking-wide uppercase text-xs"
                  :show-store-name="false"
                  :show-stock="false"
                  @product-click="selectedProduct = $event" />
              </div>
            </div>
          </section>
        </template>

        <!-- Por categoria -->
        <template v-if="categoriasExistentes.length > 0">
          <section v-for="(cat, idx) in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                   class="border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
            <div class="grid grid-cols-1 md:grid-cols-12">
              <div class="hidden md:flex md:col-span-2 items-start justify-center pt-10 border-r"
                   :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
                <span class="font-black text-5xl" :style="{ color: 'var(--cor-primaria)', opacity: '0.3' }">
                  {{ String(tiposExistentes.length + idx + 2).padStart(2, '0') }}
                </span>
              </div>
              <div class="md:col-span-10 px-8 md:px-12 pt-10 pb-14">
                <div class="flex items-end gap-5 mb-10">
                  <h2 class="text-4xl font-black tracking-tight capitalize leading-none" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ cat.nome }}</h2>
                  <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-300'"></div>
                </div>
                <ProductSlider
                  :title="cat.nome"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :isDark="isDark"
                  card-width="200px"
                  image-height="260px"
                  card-height="360px"
                  card-border-radius="rounded-none"
                  hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                  hover-border-class=""
                  product-name-class="font-bold tracking-wide uppercase text-xs"
                  :show-store-name="false"
                  :show-stock="false"
                  @product-click="selectedProduct = $event" />
              </div>
            </div>
          </section>
        </template>

        <!-- Catálogo completo -->
        <section id="catalogo" class="border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
          <div class="grid grid-cols-1 md:grid-cols-12">
            <div class="hidden md:flex md:col-span-2 items-start justify-center pt-10 border-r"
                 :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
              <span class="font-black text-4xl" :class="isDark ? 'text-zinc-700' : 'text-zinc-400'" style="writing-mode:vertical-rl;text-orientation:mixed;letter-spacing:0.2em">CATALOG</span>
            </div>
            <div class="md:col-span-10 px-8 md:px-12 pt-10 pb-14">
              <div class="flex items-end gap-5 mb-10">
                <h2 class="text-4xl font-black tracking-tight leading-none" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Coleção Completa</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-300'"></div>
              </div>
              <ProductCatalog
                :loja-id="lojaId" :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="240px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                tab-border-radius="rounded-none"
                :active-tab-class="isDark ? 'border-b-2 pb-2 text-zinc-100 font-bold tracking-wider uppercase text-xs' : 'border-b-2 pb-2 text-zinc-900 font-bold tracking-wider uppercase text-xs'"
                :inactive-tab-dark-class="'text-zinc-500 hover:text-zinc-300 pb-2 tracking-wider uppercase text-xs'"
                :inactive-tab-light-class="'text-zinc-400 hover:text-zinc-700 pb-2 tracking-wider uppercase text-xs'"
                input-border-radius="rounded-none"
                filter-container-radius="rounded-none"
                product-name-class="font-bold tracking-wider uppercase text-xs"
                product-name-hover-class="group-hover:opacity-60"
                :price-class="'font-black text-sm'"
                :show-stock="false"
                :show-badges="false"
                :show-category-badges="false"
                @product-click="selectedProduct = $event" />
            </div>
          </div>
        </section>

        <!-- Avaliações -->
        <section id="avaliacoes" class="border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
          <div class="grid grid-cols-1 md:grid-cols-12">
            <div class="hidden md:flex md:col-span-2 items-start justify-center pt-10 border-r"
                 :class="isDark ? 'border-zinc-800' : 'border-zinc-300'">
              <span class="font-black text-4xl" :class="isDark ? 'text-zinc-700' : 'text-zinc-400'" style="writing-mode:vertical-rl;text-orientation:mixed;letter-spacing:0.2em">REVIEWS</span>
            </div>
            <div class="md:col-span-10 px-8 md:px-12 pt-10 pb-14">
              <div class="flex items-end gap-5 mb-10">
                <h2 class="text-4xl font-black tracking-tight leading-none" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Reviews</h2>
                <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-300'"></div>
              </div>
              <AvaliacaoLoja
                :loja-id="lojaId" :isDark="isDark"
                summary-border-radius="rounded-none"
                form-border-radius="rounded-none"
                review-card-border-radius="rounded-none"
                button-border-radius="rounded-none"
                textarea-border-radius="rounded-none"
                :star-active-class="'text-current opacity-90'"
                :star-inactive-class="isDark ? 'text-zinc-800' : 'text-zinc-200'"
                progress-bar-class="bg-current opacity-60"
                :submit-button-class="isDark ? 'bg-zinc-100 text-zinc-900 hover:bg-white font-bold tracking-wider uppercase text-xs' : 'bg-zinc-900 text-white hover:bg-zinc-700 font-bold tracking-wider uppercase text-xs'"
                :review-card-class="isDark ? 'border-b border-zinc-900' : 'border-b border-zinc-200'"
                @rating-updated="onRatingUpdated" />
            </div>
          </div>
        </section>

        <!-- Footer -->
        <footer class="px-8 md:px-14 py-12">
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <h3 class="text-2xl font-black tracking-tight" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ loja.nome }}</h3>
              <p class="text-[9px] tracking-[0.3em] uppercase mt-1" :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">© {{ new Date().getFullYear() }}</p>
            </div>
            <div class="flex gap-7 text-[9px] tracking-[0.3em] uppercase font-bold">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                class="transition hover:underline underline-offset-4"
                :class="isDark ? 'text-zinc-600 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">Devoluções</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                class="transition hover:underline underline-offset-4"
                :class="isDark ? 'text-zinc-600 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                class="transition hover:underline underline-offset-4"
                :class="isDark ? 'text-zinc-600 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">Privacidade</button>
            </div>
          </div>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-0 md:p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto"
             :class="isDark ? 'bg-zinc-900 border-t md:border border-zinc-800' : 'bg-white border-t md:border border-zinc-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-100'">
            <h3 class="text-[9px] tracking-[0.4em] uppercase font-bold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 flex items-center justify-center border transition"
              :class="isDark ? 'border-zinc-800 hover:border-zinc-600 text-zinc-400' : 'border-zinc-200 hover:border-zinc-400 text-zinc-500'">×</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-zinc-100'">
      <p class="text-5xl font-black tracking-tighter mb-6" :class="isDark ? 'text-zinc-800' : 'text-zinc-200'">404</p>
      <button @click="$router.back()" class="text-[9px] tracking-[0.3em] uppercase hover:underline" style="color:var(--cor-primaria)">← Voltar</button>
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
  name: 'TemplateModaEditorial',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#e4e4e7',
      '--cor-secundaria': props.tema?.corSecundaria || '#09090b',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }

    return { isDark, cssVars, user, toggleDark, ...lojaData }
  },
}
</script>

<style scoped>
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }
</style>
