<!-- TemplateModaEditorial — Magazine de moda, layout editorial assimétrico, tipografia condensada bold -->
<template>
  <div class="min-h-screen transition-colors duration-500"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-zinc-50 text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-zinc-50'">
      <div class="text-center space-y-3">
        <div class="flex gap-1 justify-center">
          <div v-for="i in 5" :key="i" class="w-1 h-8 rounded-full animate-pulse"
               :style="{ backgroundColor: 'var(--cor-primaria)', animationDelay: i * 0.1 + 's' }"></div>
        </div>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO EDITORIAL — split assimétrico 60/40 ── -->
      <section class="relative min-h-screen grid grid-cols-1 lg:grid-cols-5">

        <!-- Coluna imagem — 3/5 -->
        <div class="relative lg:col-span-3 h-[60vh] lg:h-screen overflow-hidden">
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome"
               class="w-full h-full object-cover transition-transform duration-[10s] hover:scale-105" />
          <div class="absolute inset-0"
               :class="isDark ? 'bg-gradient-to-r from-transparent via-transparent to-zinc-950/60' : 'bg-gradient-to-r from-transparent via-transparent to-zinc-50/40'"/>

          <!-- Número editorial em diagonal -->
          <div class="absolute bottom-8 left-8 font-black text-white/10 select-none pointer-events-none"
               style="font-size: clamp(6rem, 15vw, 14rem); line-height: 1; letter-spacing: -0.05em">
            {{ new Date().getFullYear() }}
          </div>
        </div>

        <!-- Coluna texto — 2/5 -->
        <div class="relative lg:col-span-2 flex flex-col justify-between px-8 md:px-12 py-10 lg:py-16 min-h-[40vh] lg:min-h-screen"
             :class="isDark ? 'bg-zinc-950' : 'bg-zinc-50'">

          <!-- Topo: nav -->
          <div class="flex items-center justify-between">
            <button @click="$router.back()"
              class="text-xs tracking-[0.3em] uppercase transition-colors"
              :class="isDark ? 'text-zinc-500 hover:text-zinc-200' : 'text-zinc-400 hover:text-zinc-800'">
              ← Voltar
            </button>
            <button @click="toggleDark"
              class="w-8 h-8 rounded-full border flex items-center justify-center transition"
              :class="isDark ? 'border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200' : 'border-zinc-300 text-zinc-500 hover:border-zinc-500'">
              <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
          </div>

          <!-- Centro: título grande -->
          <div class="flex-1 flex flex-col justify-center py-8">
            <p class="text-xs tracking-[0.5em] uppercase mb-6"
               :style="{ color: 'var(--cor-primaria)' }">{{ loja.categoria }}</p>

            <h1 class="leading-none font-black tracking-tighter mb-6"
                style="font-size: clamp(2.8rem, 6vw, 5.5rem)">
              {{ loja.nome }}
            </h1>

            <p v-if="loja.descricao" class="text-sm leading-relaxed mb-8 max-w-xs"
               :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
              {{ loja.descricao.substring(0, 150) }}{{ loja.descricao.length > 150 ? '…' : '' }}
            </p>

            <!-- Line divider com ornamento -->
            <div class="flex items-center gap-4 mb-8">
              <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-200'"></div>
              <div class="w-2 h-2 rotate-45"
                   :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
              <div class="flex-1 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-200'"></div>
            </div>

            <!-- Stats compactos -->
            <div class="flex items-center gap-6 mb-8">
              <div v-if="loja.rating_medio">
                <span class="text-3xl font-black" :style="{ color: 'var(--cor-primaria)' }">{{ loja.rating_medio }}</span>
                <span class="text-xs ml-1" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">/ 5</span>
              </div>
              <div v-if="loja.localizacao" class="text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
                📍 {{ loja.localizacao }}
              </div>
            </div>

            <div class="flex gap-3 flex-wrap">
              <button @click="scrollToId('colecao')"
                class="px-6 py-3 font-bold text-sm tracking-wider text-white transition-all hover:scale-[1.02] hover:shadow-lg"
                :style="{ backgroundColor: 'var(--cor-primaria)' }">
                Ver Coleção
              </button>
              <button @click="scrollToId('catalogo')"
                class="px-6 py-3 font-bold text-sm tracking-wider border transition-all hover:scale-[1.02]"
                :class="isDark ? 'border-zinc-700 text-zinc-300 hover:bg-zinc-800' : 'border-zinc-300 text-zinc-700 hover:bg-zinc-100'">
                Catálogo
              </button>
            </div>
          </div>

          <!-- Fundo: info rápida -->
          <div class="border-t pt-5 grid grid-cols-2 gap-4"
               :class="isDark ? 'border-zinc-800' : 'border-zinc-200'">
            <div v-for="opcao in opcoesEntrega.slice(0, 2)" :key="opcao.id">
              <p class="text-[10px] tracking-[0.3em] uppercase"
                 :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">{{ opcao.nome }}</p>
              <p class="text-sm font-bold mt-0.5" :style="{ color: 'var(--cor-primaria)' }">
                {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- ── MAIN — layout com sidebar editorial ── -->
      <div id="colecao" class="flex">

        <!-- SIDEBAR editorial: índice de secções -->
        <aside class="hidden xl:flex flex-col sticky top-0 h-screen w-48 flex-shrink-0 border-r"
               :class="isDark ? 'bg-zinc-950 border-zinc-800/50' : 'bg-zinc-50 border-zinc-200'">
          <div class="flex-1 overflow-y-auto p-5">
            <!-- Issue number vertical -->
            <div class="mb-8 pb-4 border-b" :class="isDark ? 'border-zinc-800' : 'border-zinc-200'">
              <p class="text-[10px] tracking-[0.4em] uppercase" :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Índice</p>
            </div>

            <nav class="space-y-6">
              <div>
                <p class="text-[9px] tracking-[0.4em] uppercase mb-2"
                   :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">Colecções</p>
                <div class="space-y-2">
                  <button @click="scrollToId('destaques')"
                    class="block w-full text-left text-xs tracking-wider uppercase transition hover:pl-2"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-100' : 'text-zinc-500 hover:text-zinc-900'"
                    style="transition: padding 0.2s ease">
                    Destaques
                  </button>
                  <button v-for="tipo in tiposExistentes" :key="tipo.id"
                    @click="scrollToId('tipo-' + tipo.id)"
                    class="block w-full text-left text-xs tracking-wider uppercase capitalize transition hover:pl-2"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-100' : 'text-zinc-500 hover:text-zinc-900'"
                    style="transition: padding 0.2s ease">
                    {{ tipo.nome }}
                  </button>
                  <button v-for="cat in categoriasExistentes" :key="cat.id"
                    @click="scrollToId('cat-' + cat.id)"
                    class="block w-full text-left text-xs tracking-wider uppercase capitalize transition hover:pl-2"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-100' : 'text-zinc-500 hover:text-zinc-900'"
                    style="transition: padding 0.2s ease">
                    {{ cat.nome }}
                  </button>
                </div>
              </div>

              <div>
                <p class="text-[9px] tracking-[0.4em] uppercase mb-2"
                   :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">Mais</p>
                <div class="space-y-2">
                  <button @click="scrollToId('catalogo')"
                    class="block w-full text-left text-xs tracking-wider uppercase transition hover:pl-2"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-100' : 'text-zinc-500 hover:text-zinc-900'"
                    style="transition: padding 0.2s ease">
                    Catálogo
                  </button>
                  <button @click="scrollToId('avaliacoes')"
                    class="block w-full text-left text-xs tracking-wider uppercase transition hover:pl-2"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-100' : 'text-zinc-500 hover:text-zinc-900'"
                    style="transition: padding 0.2s ease">
                    Reviews
                  </button>
                </div>
              </div>
            </nav>
          </div>

          <!-- Pagamentos no fundo -->
          <div class="p-5 border-t" :class="isDark ? 'border-zinc-800/50' : 'border-zinc-200'">
            <p class="text-[9px] tracking-[0.3em] uppercase mb-3"
               :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">Pagamento</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="m in metodosPagamento" :key="m.id"
                    class="text-[9px] tracking-wider uppercase px-1.5 py-0.5 border rounded"
                    :class="isDark ? 'border-zinc-800 text-zinc-600' : 'border-zinc-200 text-zinc-400'">
                {{ m.tipo }}
              </span>
            </div>
          </div>
        </aside>

        <!-- CONTEÚDO PRINCIPAL -->
        <main class="flex-1 min-w-0 pb-20">

          <!-- Mobile: tabs -->
          <div class="xl:hidden sticky top-0 z-20 overflow-x-auto scrollbar-hide border-b"
               :class="isDark ? 'bg-zinc-950/95 border-zinc-800 backdrop-blur-xl' : 'bg-zinc-50/95 border-zinc-200 backdrop-blur-xl'">
            <div class="flex gap-0 min-w-max">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-5 py-4 text-xs tracking-[0.25em] uppercase border-r whitespace-nowrap transition"
                :class="isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900' : 'border-zinc-200 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100'">
                {{ cat.nome }}
              </button>
            </div>
          </div>

          <div class="px-6 md:px-12 pt-14">

            <!-- DESTAQUES — slider amplo -->
            <section id="destaques" class="mb-20">
              <div class="flex items-end justify-between mb-8">
                <div>
                  <p class="text-[10px] tracking-[0.5em] uppercase mb-2"
                     :style="{ color: 'var(--cor-primaria)' }">New Season</p>
                  <h2 class="text-4xl font-black tracking-tighter leading-none"
                      :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Destaques</h2>
                </div>
                <div class="hidden md:flex items-center gap-2">
                  <div class="w-12 h-px" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-300'"></div>
                  <div class="w-2 h-2 rotate-45 flex-shrink-0"
                       :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
                </div>
              </div>
              <ProductSlider
                title="Destaques"
                :params="{ loja_id: lojaId, destaque: true }"
                :isDark="isDark"
                card-width="240px"
                image-height="300px"
                card-height="400px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-2xl transition-all duration-500"
                hover-border-class=""
                product-name-class="font-bold tracking-wide uppercase text-sm"
                price-class="font-black text-base"
                :show-badges="true"
                badge-text="NEW"
                badge-class="bg-current rounded-none px-2 py-0.5 text-white text-[9px] font-black tracking-widest"
                :show-store-name="false"
                :show-stock="false"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- Por tipo — secções com divisor editorial -->
            <template v-if="tiposExistentes.length > 0">
              <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                       class="mb-20">
                <div class="flex items-end gap-6 mb-8">
                  <h2 class="text-4xl font-black tracking-tighter capitalize leading-none"
                      :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ tipo.nome }}</h2>
                  <span class="text-6xl font-black opacity-10 leading-none"
                        :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                    {{ String(idx + 1).padStart(2, '0') }}
                  </span>
                  <div class="flex-1 h-px self-center" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-200'"></div>
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
                  product-name-class="font-bold tracking-wide uppercase text-sm"
                  :show-store-name="false"
                  :show-stock="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- Por categoria -->
            <template v-if="categoriasExistentes.length > 0">
              <section v-for="(cat, idx) in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                       class="mb-20">
                <div class="flex items-end gap-6 mb-8">
                  <h2 class="text-4xl font-black tracking-tighter capitalize leading-none"
                      :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ cat.nome }}</h2>
                  <!-- <span class="text-lg">{{ cat.icone }}</span> -->
                  <span class="text-6xl font-black opacity-10 leading-none"
                        :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                    {{ String(tiposExistentes.length + idx + 1).padStart(2, '0') }}
                  </span>
                  <div class="flex-1 h-px self-center" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-200'"></div>
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
                  product-name-class="font-bold tracking-wide uppercase text-sm"
                  :show-store-name="false"
                  :show-stock="false"
                  @product-click="selectedProduct = $event" />
              </section>
            </template>

            <!-- CATÁLOGO — grid editorial -->
            <section id="catalogo" class="mb-20">
              <div class="flex items-end gap-6 mb-8">
                <h2 class="text-4xl font-black tracking-tighter leading-none"
                    :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Coleção Completa</h2>
                <div class="flex-1 h-px self-center" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-200'"></div>
              </div>
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="240px"
                card-border-radius="rounded-none"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-500"
                hover-border-class=""
                tab-border-radius="rounded-none"
                :active-tab-class="isDark ? 'border-b-2 pb-2 text-zinc-100 font-bold tracking-wider uppercase text-xs' : 'border-b-2 pb-2 text-zinc-900 font-bold tracking-wider uppercase text-xs'"
                :inactive-tab-dark-class="'text-zinc-500 hover:text-zinc-300 pb-2 tracking-wider uppercase text-xs'"
                :inactive-tab-light-class="'text-zinc-400 hover:text-zinc-700 pb-2 tracking-wider uppercase text-xs'"
                active-sub-tab-class="underline underline-offset-4 text-current text-xs tracking-wider uppercase"
                :inactive-sub-tab-dark-class="'text-zinc-600 hover:text-zinc-300 text-xs tracking-wider uppercase'"
                :inactive-sub-tab-light-class="'text-zinc-400 hover:text-zinc-700 text-xs tracking-wider uppercase'"
                category-border-class="border-l-0"
                input-border-radius="rounded-none"
                :input-focus-class="'focus:outline-none focus:border-b focus:border-current'"
                filter-container-radius="rounded-none"
                product-name-class="font-bold tracking-wider uppercase text-xs"
                product-name-hover-class="group-hover:opacity-60"
                price-class="font-black text-sm"
                :show-stock="false"
                :show-badges="false"
                :show-category-badges="false"
                spinner-class="text-current opacity-40"
                clear-all-class="underline underline-offset-4 text-xs tracking-widest uppercase"
                @product-click="selectedProduct = $event" />
            </section>

            <!-- AVALIAÇÕES -->
            <section id="avaliacoes" class="mb-20">
              <div class="flex items-end gap-6 mb-8">
                <h2 class="text-4xl font-black tracking-tighter leading-none"
                    :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Reviews</h2>
                <div class="flex-1 h-px self-center" :class="isDark ? 'bg-zinc-800' : 'bg-zinc-200'"></div>
              </div>
              <AvaliacaoLoja
                :loja-id="lojaId"
                :isDark="isDark"
                summary-border-radius="rounded-none"
                form-border-radius="rounded-none"
                review-card-border-radius="rounded-none"
                button-border-radius="rounded-none"
                textarea-border-radius="rounded-none"
                :star-active-class="'text-current opacity-90'"
                :star-inactive-class="isDark ? 'text-zinc-800' : 'text-zinc-200'"
                progress-bar-class="bg-current opacity-60"
                :submit-button-class="isDark ? 'bg-zinc-100 text-zinc-900 hover:bg-white font-bold tracking-wider uppercase text-xs' : 'bg-zinc-900 text-white hover:bg-zinc-700 font-bold tracking-wider uppercase text-xs'"
                :own-review-border-class="isDark ? 'border-b border-zinc-700' : 'border-b border-zinc-200'"
                :review-card-class="isDark ? 'border-b border-zinc-900' : 'border-b border-zinc-100'"
                load-more-button-class="text-xs tracking-widest uppercase underline underline-offset-4"
                link-class="underline underline-offset-4"
                @rating-updated="onRatingUpdated" />
            </section>

            <!-- FOOTER editorial -->
            <footer class="border-t py-10"
                    :class="isDark ? 'border-zinc-800' : 'border-zinc-200'">
              <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div>
                  <h3 class="text-2xl font-black tracking-tighter"
                      :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">{{ loja.nome }}</h3>
                  <p class="text-xs tracking-[0.3em] uppercase mt-1"
                     :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">© {{ new Date().getFullYear() }}</p>
                </div>
                <div class="flex gap-6 text-[10px] tracking-[0.3em] uppercase">
                  <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-zinc-600 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
                    Devoluções
                  </button>
                  <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-zinc-600 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
                    Termos
                  </button>
                  <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                    class="transition hover:underline underline-offset-4"
                    :class="isDark ? 'text-zinc-600 hover:text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'">
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
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto"
             :class="isDark ? 'bg-zinc-900 border-t border-zinc-800 md:border' : 'bg-white border-t border-zinc-200 md:border'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-100'">
            <h3 class="text-xs tracking-[0.35em] uppercase font-bold"
                :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded flex items-center justify-center transition border"
              :class="isDark ? 'border-zinc-800 hover:border-zinc-600 text-zinc-400' : 'border-zinc-200 hover:border-zinc-400 text-zinc-500'">
              ×
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
         :class="isDark ? 'bg-zinc-950' : 'bg-zinc-50'">
      <p class="text-4xl font-black tracking-tighter mb-6" :class="isDark ? 'text-zinc-700' : 'text-zinc-300'">404</p>
      <button @click="$router.back()" class="text-xs tracking-[0.3em] uppercase hover:underline"
              :style="{ color: 'var(--cor-primaria)' }">← Voltar</button>
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
      '--cor-primaria':   props.tema?.corPrimaria   || '#18181b',
      '--cor-secundaria': props.tema?.corSecundaria || '#f4f4f5',
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
</style>