<!-- TemplateMinimalista — Tipografia extrema, espaço máximo, zero ornamentação -->
<template>
  <div class="min-h-screen transition-colors duration-700"
       :class="isDark ? 'bg-stone-950 text-stone-100' : 'bg-stone-50 text-stone-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <!-- ── NAV MINIMALISTA ── sticky, apenas o essencial -->
    <header class="fixed top-0 left-0 right-0 z-20 transition-all duration-500"
            :class="scrolled
              ? (isDark ? 'bg-stone-950/95 backdrop-blur-xl border-b border-stone-800/50' : 'bg-stone-50/95 backdrop-blur-xl border-b border-stone-200/80')
              : 'bg-transparent'">
      <div class="max-w-4xl mx-auto px-4 md:px-8 h-14 md:h-16 flex items-center justify-between relative">
        <!-- Esquerda: voltar + toggle tema lado a lado -->
        <div class="flex items-center gap-3">
          <button @click="$router.back()"
            class="text-xs tracking-[0.25em] uppercase transition-colors duration-300"
            :class="isDark ? 'text-stone-500 hover:text-stone-200' : 'text-stone-400 hover:text-stone-800'">
            ← Voltar
          </button>
          <button @click="toggleDark"
            class="w-7 h-7 rounded-full flex items-center justify-center transition-all duration-300 border"
            :class="isDark
              ? 'border-stone-700 text-stone-400 hover:border-stone-400 hover:text-stone-100 bg-stone-950/80'
              : 'border-stone-300 text-stone-500 hover:border-stone-600 hover:text-stone-900 bg-stone-50/80'">
            <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
        </div>

        <!-- Centro: nome ao scroll — absolute para não deslocar os lados -->
        <span v-if="scrolled && loja"
              class="absolute left-1/2 -translate-x-1/2 text-xs tracking-[0.3em] uppercase pointer-events-none"
              :class="isDark ? 'text-stone-400' : 'text-stone-600'">
          {{ loja.nome }}
        </span>

        <!-- Direita: vazio para equilibrar (Profile/Cart via componente global ficam aqui) -->
        <div class="w-16"></div>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="w-px h-20 animate-pulse" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO — tipografia enorme, imagem subtil como fundo ── -->
      <section class="relative min-h-screen flex flex-col justify-end overflow-hidden">
        <!-- Imagem de fundo com opacidade baixa -->
        <div class="absolute inset-0 overflow-hidden">
          <img v-if="loja.banner_url"
               :src="loja.banner_url"
               :alt="loja.nome"
               class="w-full h-full object-cover transition-transform duration-[8s] scale-105"
               :class="isDark ? 'opacity-15' : 'opacity-8'" />
          <!-- Gradiente para garantir legibilidade -->
          <div class="absolute inset-0"
               :class="isDark
                 ? 'bg-gradient-to-t from-stone-950 via-stone-950/80 to-stone-950/40'
                 : 'bg-gradient-to-t from-stone-50 via-stone-50/85 to-stone-50/50'"></div>
        </div>

        <!-- Linha decorativa vertical -->
        <div class="absolute left-8 top-1/4 bottom-1/4 w-px"
             :class="isDark ? 'bg-stone-800' : 'bg-stone-300'"></div>

        <!-- Conteúdo principal -->
        <div class="relative max-w-4xl mx-auto px-8 pb-20 pt-32 w-full">

          <!-- Categoria como label minúscula -->
          <p class="text-xs tracking-[0.4em] uppercase mb-8 transition-colors"
             :class="isDark ? 'text-stone-500' : 'text-stone-400'">
            {{ loja.categoria }}
            <span v-if="loja.localizacao" class="ml-4">· {{ loja.localizacao }}</span>
          </p>

          <!-- Nome enorme — o elemento dominante -->
          <h1 class="font-black leading-[0.85] tracking-tighter mb-12 break-words"
              :style="{ fontSize: 'clamp(3.5rem, 12vw, 10rem)' }"
              :class="isDark ? 'text-stone-100' : 'text-stone-900'">
            {{ loja.nome }}
          </h1>

          <!-- Descrição — font light, comprimento restrito -->
          <p v-if="loja.descricao"
             class="text-xl font-extralight leading-relaxed max-w-lg mb-12"
             :class="isDark ? 'text-stone-400' : 'text-stone-600'">
            {{ loja.descricao }}
          </p>

          <!-- Stats em linha -->
          <div class="flex items-center gap-12 mb-16">
            <div v-if="loja.rating_medio" class="flex flex-col">
              <span class="text-4xl font-black" :style="{ color: 'var(--cor-primaria)' }">
                {{ loja.rating_medio }}
              </span>
              <span class="text-[10px] tracking-[0.3em] uppercase mt-1"
                    :class="isDark ? 'text-stone-600' : 'text-stone-400'">
                Rating
              </span>
            </div>
            <div v-if="loja.total_avaliacoes" class="flex flex-col">
              <span class="text-4xl font-black"
                    :class="isDark ? 'text-stone-100' : 'text-stone-900'">
                {{ loja.total_avaliacoes }}
              </span>
              <span class="text-[10px] tracking-[0.3em] uppercase mt-1"
                    :class="isDark ? 'text-stone-600' : 'text-stone-400'">
                Reviews
              </span>
            </div>
            <div v-if="loja.entrega_ativa" class="flex flex-col">
              <span class="text-4xl font-black text-emerald-500">✓</span>
              <span class="text-[10px] tracking-[0.3em] uppercase mt-1"
                    :class="isDark ? 'text-stone-600' : 'text-stone-400'">
                Entrega
              </span>
            </div>
          </div>

          <!-- CTA único -->
          <button @click="scrollToId('colecao')"
            class="group flex items-center gap-4 text-sm tracking-[0.2em] uppercase transition-all duration-500"
            :class="isDark ? 'text-stone-300 hover:text-stone-100' : 'text-stone-700 hover:text-stone-900'">
            <span class="w-12 h-px transition-all duration-500 group-hover:w-20"
                  :style="{ backgroundColor: 'var(--cor-primaria)' }"></span>
            Ver coleção
          </button>
        </div>

        <!-- Scroll indicator -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3">
          <div class="w-px h-12 animate-pulse opacity-40"
               :class="isDark ? 'bg-stone-400' : 'bg-stone-600'"></div>
        </div>
      </section>

      <!-- ── MAIN ── -->
      <main>

        <!-- ── SOBRE — layout de duas colunas assimétricas ── -->
        <section id="colecao" class="border-t py-24"
                 :class="isDark ? 'border-stone-800' : 'border-stone-200'">
          <div class="max-w-4xl mx-auto px-8">
            <div class="grid grid-cols-1 md:grid-cols-12 gap-16 items-start">
              <!-- Label lateral -->
              <div class="md:col-span-3">
                <p class="text-[10px] tracking-[0.4em] uppercase sticky top-24"
                   :class="isDark ? 'text-stone-600' : 'text-stone-400'">
                  Sobre
                </p>
              </div>
              <!-- Conteúdo -->
              <div class="md:col-span-9">
                <p class="text-2xl font-extralight leading-relaxed mb-12"
                   :class="isDark ? 'text-stone-300' : 'text-stone-700'">
                  {{ loja.descricao || 'Uma loja construída em torno de um único princípio: qualidade sem compromissos.' }}
                </p>

                <!-- Info de entrega e pagamento — minimalista -->
                <div class="grid grid-cols-2 gap-8 pt-8 border-t"
                     :class="isDark ? 'border-stone-800' : 'border-stone-200'">
                  <div v-if="opcoesEntrega.length">
                    <p class="text-[10px] tracking-[0.3em] uppercase mb-4"
                       :class="isDark ? 'text-stone-600' : 'text-stone-400'">Envio</p>
                    <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="mb-3">
                      <p class="text-sm font-light"
                         :class="isDark ? 'text-stone-300' : 'text-stone-700'">{{ opcao.nome }}</p>
                      <p class="text-xs mt-0.5" :style="{ color: 'var(--cor-primaria)' }">
                        {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                        <span v-if="opcao.tempo_estimado" class="text-stone-500 ml-2">{{ opcao.tempo_estimado }}</span>
                      </p>
                    </div>
                  </div>
                  <div v-if="metodosPagamento.length">
                    <p class="text-[10px] tracking-[0.3em] uppercase mb-4"
                       :class="isDark ? 'text-stone-600' : 'text-stone-400'">Pagamento</p>
                    <div class="flex flex-wrap gap-2">
                      <span v-for="m in metodosPagamento" :key="m.id"
                            class="text-sm font-light"
                            :class="isDark ? 'text-stone-300' : 'text-stone-700'">
                        {{ m.tipo }}<span class="text-stone-600 ml-1">·</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ── DESTAQUES ── cards altos e estreitos -->
        <section class="border-t py-24 overflow-x-hidden"
                 :class="isDark ? 'border-stone-800' : 'border-stone-200'">
          <div class="max-w-4xl mx-auto px-4 mb-12">
            <div class="grid grid-cols-12 items-baseline gap-8">
              <p class="col-span-3 text-[10px] tracking-[0.4em] uppercase"
                 :class="isDark ? 'text-stone-600' : 'text-stone-400'">Destaques</p>
              <div class="col-span-9 h-px self-center"
                   :class="isDark ? 'bg-stone-800' : 'bg-stone-200'"></div>
            </div>
          </div>
          <div class="max-w-6xl mx-auto px-4">
            <ProductSlider
              title="Destaques" icon=""
              :params="{ loja_id: lojaId, destaque: true }"
              :isDark="isDark"
              card-width="160px"
              image-height="240px"
              card-height="340px"
              :limit="8"
              card-border-radius="rounded-none"
              hover-effect="hover:opacity-80 transition-opacity duration-500"
              hover-border-class=""
              title-size="text-base"
              title-class="font-extralight tracking-widest uppercase"
              product-name-size="text-base"
              product-name-class="font-light"
              product-name-hover-class="group-hover:opacity-60"
              price-size="text-sm"
              :price-class="isDark ? 'font-extralight text-stone-300' : 'font-extralight text-stone-700'"
              :show-store-name="false"
              :show-badges="false"
              :show-stock="false"
              @product-click="selectedProduct = $event" />
          </div>
        </section>

        <!-- ── POR TIPO ── cada tipo é uma secção com label lateral -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                   class="border-t py-24 overflow-x-hidden"
                   :class="isDark ? 'border-stone-800' : 'border-stone-200'">
            <div class="max-w-4xl mx-auto px-4 mb-6">
              <div class="grid grid-cols-12 items-baseline gap-8">
                <p class="col-span-3 text-[10px] tracking-[0.4em] uppercase"
                   :class="isDark ? 'text-stone-600' : 'text-stone-400'">{{ tipo.nome }}</p>
                <div class="col-span-9 h-px self-center"
                     :class="isDark ? 'bg-stone-800' : 'bg-stone-200'"></div>
              </div>
            </div>
            <div class="max-w-6xl mx-auto px-4">
              <ProductSlider
                :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark"
                card-width="155px"
                image-height="240px"
                card-height="340px"
              :limit="8"
                card-border-radius="rounded-none"
                hover-effect="hover:opacity-75 transition-opacity duration-500"
                hover-border-class=""
                product-name-class="font-light"
                product-name-hover-class="group-hover:opacity-60"
                price-class="font-extralight"
                :show-store-name="false"
                :show-badges="false"
                :show-stock="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- ── POR CATEGORIA ── -->
        <template v-if="categoriasExistentes.length > 0">
          <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                   class="border-t py-24 overflow-x-hidden"
                   :class="isDark ? 'border-stone-800' : 'border-stone-200'">
            <div class="max-w-4xl mx-auto px-4 mb-6">
              <div class="grid grid-cols-12 items-baseline gap-8">
                <p class="col-span-3 text-[10px] tracking-[0.4em] uppercase"
                   :class="isDark ? 'text-stone-600' : 'text-stone-400'">{{ cat.nome }}</p>
                <div class="col-span-9 h-px self-center"
                     :class="isDark ? 'bg-stone-800' : 'bg-stone-200'"></div>
              </div>
            </div>
            <div class="max-w-6xl mx-auto px-4">
              <ProductSlider
                :title="cat.nome" :icon="cat.icone"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark"
                card-width="155px"
                image-height="240px"
                card-height="340px"
              :limit="8"
                card-border-radius="rounded-none"
                hover-effect="hover:opacity-75 transition-opacity duration-500"
                hover-border-class=""
                product-name-class="font-light"
                product-name-hover-class="group-hover:opacity-60"
                price-class="font-extralight"
                :show-store-name="false"
                :show-badges="false"
                :show-stock="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- ── CATÁLOGO COMPLETO — grid 3 colunas, sem filtros visuais pesados ── -->
        <section id="catalogo" class="border-t py-24"
                 :class="isDark ? 'border-stone-800' : 'border-stone-200'">
          <div class="max-w-6xl mx-auto px-4">
            <div class="grid grid-cols-12 items-baseline gap-8 mb-12">
              <p class="col-span-3 text-[10px] tracking-[0.4em] uppercase"
                 :class="isDark ? 'text-stone-600' : 'text-stone-400'">Catálogo</p>
              <div class="col-span-9 h-px self-center"
                   :class="isDark ? 'bg-stone-800' : 'bg-stone-200'"></div>
            </div>

            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3"
              image-height="240px"
              card-height="320px"
              card-border-radius="rounded-none"
              hover-effect="hover:opacity-75 transition-opacity duration-500"
              hover-border-class=""
              tab-border-radius="rounded-none"
              :active-tab-class="isDark ? 'border-b-2 pb-2 text-stone-100' : 'border-b-2 pb-2 text-stone-900'"
              :inactive-tab-dark-class="'text-stone-500 hover:text-stone-300 pb-2'"
              :inactive-tab-light-class="'text-stone-400 hover:text-stone-700 pb-2'"
              :active-sub-tab-class="'underline underline-offset-4 text-current'"
              :inactive-sub-tab-dark-class="'text-stone-600 hover:text-stone-300'"
              :inactive-sub-tab-light-class="'text-stone-400 hover:text-stone-700'"
              category-border-class="border-l-0"
              input-border-radius="rounded-none"
              :input-focus-class="'focus:outline-none focus:border-b focus:border-current'"
              filter-container-radius="rounded-none"
              :product-name-hover-class="'group-hover:opacity-60'"
              product-name-class="font-light"
              :price-class="isDark ? 'font-extralight text-stone-300' : 'font-extralight text-stone-700'"
              spinner-class="text-current opacity-40"
              :clear-all-class="'underline underline-offset-4 text-stone-500 hover:text-stone-300'"
              :show-stock="false"
              :show-badges="false"
              :show-category-badges="false"
              @product-click="selectedProduct = $event" />
          </div>
        </section>

        <!-- ── AVALIAÇÕES — ultra-clean, sem cards ── -->
        <section id="avaliacoes" class="border-t py-24"
                 :class="isDark ? 'border-stone-800' : 'border-stone-200'">
          <div class="max-w-6xl mx-auto px-4">
            <div class="grid grid-cols-12 items-baseline gap-8 mb-16">
              <p class="col-span-3 text-[10px] tracking-[0.4em] uppercase"
                 :class="isDark ? 'text-stone-600' : 'text-stone-400'">Avaliações</p>
              <div class="col-span-9 h-px self-center"
                   :class="isDark ? 'bg-stone-800' : 'bg-stone-200'"></div>
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
              :star-inactive-class="isDark ? 'text-stone-800' : 'text-stone-200'"
              progress-bar-class="bg-current opacity-70"
              :submit-button-class="isDark ? 'bg-stone-100 text-stone-900 hover:bg-white' : 'bg-stone-900 text-white hover:bg-stone-700'"
              :own-review-border-class="isDark ? 'border-b border-stone-700' : 'border-b border-stone-300'"
              :own-badge-class="'text-[10px] tracking-widest uppercase opacity-60'"
              :review-card-class="isDark ? 'border-b border-stone-900 hover:border-stone-800 transition-colors' : 'border-b border-stone-100 hover:border-stone-200 transition-colors'"
              :load-more-button-class="'text-xs tracking-widest uppercase underline underline-offset-4 text-stone-500 hover:text-stone-300'"
              :link-class="'underline underline-offset-4'"
              :remaining-badge-class="isDark ? 'text-stone-600 normal-case' : 'text-stone-400 normal-case'"
              :delete-button-class="'text-stone-500 hover:text-stone-300 underline underline-offset-4'"
              @rating-updated="onRatingUpdated" />
          </div>
        </section>

        <!-- ── FOOTER ── mínimo absoluto -->
        <footer class="border-t py-16"
                :class="isDark ? 'border-stone-800' : 'border-stone-200'">
          <div class="max-w-4xl mx-auto px-8">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <p class="text-xs tracking-[0.3em] uppercase"
                   :class="isDark ? 'text-stone-600' : 'text-stone-400'">
                  {{ loja.nome }}
                </p>
                <p class="text-[10px] tracking-[0.2em] uppercase mt-1"
                   :class="isDark ? 'text-stone-700' : 'text-stone-300'">
                  © {{ new Date().getFullYear() }}
                </p>
              </div>
              <div class="flex flex-col items-end gap-3">
                <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                  class="text-[10px] tracking-[0.3em] uppercase transition-colors"
                  :class="isDark ? 'text-stone-600 hover:text-stone-300' : 'text-stone-400 hover:text-stone-700'">
                  Devoluções
                </button>
                <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                  class="text-[10px] tracking-[0.3em] uppercase transition-colors"
                  :class="isDark ? 'text-stone-600 hover:text-stone-300' : 'text-stone-400 hover:text-stone-700'">
                  Termos
                </button>
                <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                  class="text-[10px] tracking-[0.3em] uppercase transition-colors"
                  :class="isDark ? 'text-stone-600 hover:text-stone-300' : 'text-stone-400 hover:text-stone-700'">
                  Privacidade
                </button>
              </div>
            </div>
          </div>
        </footer>
      </main>

      <!-- Modal políticas — sem bordas, simples -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full max-w-2xl max-h-[70vh] overflow-y-auto transition-transform"
             :class="isDark ? 'bg-stone-950' : 'bg-stone-50'">
          <div class="flex items-center justify-between px-8 py-6 border-b sticky top-0"
               :class="isDark ? 'bg-stone-950 border-stone-800' : 'bg-stone-50 border-stone-200'">
            <p class="text-[10px] tracking-[0.4em] uppercase"
               :class="isDark ? 'text-stone-400' : 'text-stone-600'">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </p>
            <button @click="modalPolitica = null"
              class="text-[10px] tracking-widest uppercase transition-colors"
              :class="isDark ? 'text-stone-600 hover:text-stone-300' : 'text-stone-400 hover:text-stone-700'">
              Fechar
            </button>
          </div>
          <div class="px-8 py-8 text-sm font-light leading-loose whitespace-pre-wrap"
               :class="isDark ? 'text-stone-400' : 'text-stone-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao
             : modalPolitica === 'termos'    ? loja.termos_servico
             :                                 loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <!-- Loja não encontrada -->
    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-stone-950' : 'bg-stone-50'">
      <p class="text-xs tracking-[0.4em] uppercase mb-8"
         :class="isDark ? 'text-stone-600' : 'text-stone-400'">Loja não encontrada</p>
      <button @click="$router.back()"
        class="text-xs tracking-[0.3em] uppercase underline underline-offset-4 transition-colors"
        :class="isDark ? 'text-stone-500 hover:text-stone-200' : 'text-stone-400 hover:text-stone-800'">
        Voltar
      </button>
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
  name: 'TemplateMinimalista',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],

  props: {
    tema: { type: Object, default: () => ({}) }
  },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#78716c',  // stone-500 como default
      '--cor-secundaria': props.tema?.corSecundaria || '#fafaf9',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () {
      isDark.value = !isDark.value
      emit('toggle-dark', isDark.value)
    }

    function onScroll () { scrolled.value = window.scrollY > 60 }
    onMounted (() => window.addEventListener('scroll', onScroll, { passive: true }))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrolled, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>

<style scoped>
/* Transição suave ao fazer scroll no hero */
section img { will-change: transform; }
</style>