<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-gray-50 text-zinc-900'"
       :style="cssVars">

    <!-- Product Info Card Modal -->
    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    
    <!-- Multi Cart (fixed top-right, respects UserProfile position) -->
    <MultiCart ref="cart" :isDark="isDark" />
    
    <!-- User Profile with Notification Bell (fixed top-right) -->
    <Profile :data="user" :isDark="isDark" class="z-10" @log_out="logOut()" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-screen">
      <svg class="animate-spin h-10 w-10" style="color: var(--cor-primaria)"
           xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>

    <template v-else-if="loja">
      
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!-- HERO SECTION - Full viewport cinematic style                        -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <section class="relative h-screen min-h-[600px] overflow-hidden">
        <!-- Background Media -->
        <video v-if="isVideo(loja.banner_url)"
          :src="loja.banner_url"
          class="absolute inset-0 w-full h-full object-cover"
          autoplay muted loop playsinline></video>
        <img v-else
          :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
          :alt="loja.nome" 
          class="absolute inset-0 w-full h-full object-cover" />

        <!-- Cinematic Overlays -->
        <div class="absolute inset-0" 
             :class="isDark 
               ? 'bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-zinc-950/30' 
               : 'bg-gradient-to-t from-black/20 via-transparent to-transparent'"></div>
        <div class="absolute inset-0"
             :class="isDark
               ? 'bg-[radial-gradient(ellipse_at_center,transparent_30%,rgba(9,9,11,0.8)_100%)]'
               : 'bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(0,0,0,0.3)_100%)]'"></div>

        <!-- Navigation Bar - positioned to avoid UserProfile/NotificacaoSino/MultiCart -->
        <nav class="absolute top-0 left-0 right-0 z-10">
          <div class="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
            <!-- Left side: Back button + Dark mode toggle -->
            <div class="flex items-center gap-3">
              <button @click="$router.back()"
                class="flex items-center gap-2 px-3 py-2 rounded-lg backdrop-blur-sm transition-all group"
                :class="isDark 
                  ? 'bg-white/5 hover:bg-white/10 text-white/60 hover:text-white' 
                  : 'bg-black/5 hover:bg-black/10 text-black/60 hover:text-black'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span class="text-sm font-medium hidden sm:inline">Voltar</span>
              </button>
              
              <button @click="toggleDark"
                class="w-9 h-9 rounded-lg backdrop-blur-sm flex items-center justify-center transition-all"
                :class="isDark 
                  ? 'bg-white/5 hover:bg-white/10' 
                  : 'bg-black/5 hover:bg-black/10'">
                <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-700" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M21.64 13.02A9 9 0 1 1 10.98 2.36 7 7 0 0 0 21.64 13.02Z" />
                </svg>
              </button>
            </div>

            <!-- Center: Logo/Name (hidden on small screens to not interfere with right icons) -->
            <div class="hidden md:flex items-center gap-3 absolute left-1/2 -translate-x-1/2">
              <div class="h-px w-8" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
              <span class="text-xs font-bold tracking-[0.3em] uppercase"
                    :class="isDark ? 'text-white/40' : 'text-black/40'">
                {{ loja.categoria }}
              </span>
              <div class="h-px w-8" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
            </div>

            <!-- Right side: Empty space for UserProfile/NotificacaoSino/MultiCart (they're fixed positioned) -->
            <div class="w-32"></div>
          </div>
        </nav>

        <!-- Hero Content -->
        <div class="absolute bottom-0 left-0 right-0 pb-16 px-6 md:px-12">
          <div class="max-w-7xl mx-auto">
            <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
              
              <!-- Left: Restaurant Info -->
              <div class="max-w-2xl">
                <!-- Category Tag -->
                <div class="flex items-center gap-3 mb-4">
                  <div class="h-px w-10" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
                  <span class="text-xs font-bold tracking-[0.25em] uppercase"
                        :class="isDark ? 'text-white/40' : 'text-black/50'">
                    {{ loja.categoria }}
                  </span>
                </div>

                <!-- Restaurant Name -->
                <h1 class="text-5xl md:text-7xl font-black tracking-tight leading-[0.9] mb-4"
                    :class="isDark ? 'text-white' : 'text-zinc-900'">
                  {{ loja.nome }}
                </h1>

                <!-- Description -->
                <p class="text-base md:text-lg leading-relaxed mb-6 max-w-lg"
                   :class="isDark ? 'text-white/50' : 'text-zinc-600'">
                  {{ loja.descricao || 'Descubra uma experiência gastronómica única.' }}
                </p>

                <!-- CTA Buttons -->
                <div class="flex flex-wrap gap-3">
                  <button @click="scrollToId('catalogo')"
                    class="px-6 py-3 font-bold text-sm uppercase tracking-wider transition-all hover:-translate-y-0.5 shadow-lg"
                    :style="{ 
                      backgroundColor: 'var(--cor-primaria)', 
                      color: '#fff',
                      boxShadow: `0 10px 30px -10px var(--cor-primaria)`
                    }">
                    Ver Menu
                  </button>
                  <button @click="scrollToId('avaliacoes')"
                    class="px-6 py-3 font-bold text-sm uppercase tracking-wider border transition-all hover:-translate-y-0.5"
                    :class="isDark 
                      ? 'border-white/25 text-white/70 hover:border-white/50 hover:text-white' 
                      : 'border-black/25 text-black/70 hover:border-black/50 hover:text-black'">
                    ★ Reviews
                  </button>
                </div>
              </div>

              <!-- Right: Stats -->
              <div class="flex gap-8 md:gap-12">
                <div class="text-right" v-if="loja.rating_medio">
                  <p class="text-4xl md:text-5xl font-black" :class="isDark ? 'text-white' : 'text-zinc-900'">
                    {{ loja.rating_medio }}
                  </p>
                  <p class="text-xs font-medium tracking-widest uppercase"
                     :class="isDark ? 'text-white/25' : 'text-zinc-400'">
                    / 5 stars
                  </p>
                </div>
                <div class="text-right" v-if="loja.total_avaliacoes">
                  <p class="text-4xl md:text-5xl font-black" :class="isDark ? 'text-white' : 'text-zinc-900'">
                    {{ loja.total_avaliacoes }}
                  </p>
                  <p class="text-xs font-medium tracking-widest uppercase"
                     :class="isDark ? 'text-white/25' : 'text-zinc-400'">
                    Reviews
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Scroll Indicator -->
        <div class="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce">
          <span class="text-[10px] font-bold tracking-widest uppercase"
                :class="isDark ? 'text-white/30' : 'text-black/30'">Scroll</span>
          <svg class="w-4 h-4" :class="isDark ? 'text-white/30' : 'text-black/30'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!-- MAIN CONTENT                                                        -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <main class="relative z-10">
        <div class="max-w-7xl mx-auto px-6 py-16">
          
          <!-- Info Section -->
          <section class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-20">
            <!-- About -->
            <div class="lg:col-span-2 p-8 rounded-none border-l-2 transition-colors"
                 :class="isDark ? 'bg-zinc-900/50 border-l-red-500' : 'bg-white border-l-red-500 shadow-sm'"
                 :style="{ borderLeftColor: 'var(--cor-primaria)' }">
              <h2 class="text-xs font-bold uppercase tracking-[0.25em] mb-4"
                  :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Sobre Nós</h2>
              <p class="text-base leading-relaxed"
                 :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
                {{ loja.descricao || 'Sem descrição disponível.' }}
              </p>
              
              <!-- Payment Methods -->
              <div v-if="metodosPagamento.length > 0" class="mt-6 pt-6 border-t"
                   :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                <p class="text-xs font-bold uppercase tracking-widest mb-3"
                   :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Métodos de Pagamento</p>
                <div class="flex flex-wrap gap-2">
                  <span v-for="m in metodosPagamento" :key="m.id"
                        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium"
                        :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-gray-100 text-zinc-600'">
                    {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Delivery Info -->
            <div class="p-8 rounded-none border-t-2 transition-colors"
                 :class="isDark ? 'bg-zinc-900/50' : 'bg-white shadow-sm'"
                 :style="{ borderTopColor: 'var(--cor-primaria)' }">
              <h2 class="text-xs font-bold uppercase tracking-[0.25em] mb-4"
                  :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Entrega</h2>
              
              <div v-if="opcoesEntrega.length === 0" class="text-sm"
                   :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
                Sem opções configuradas.
              </div>
              
              <div v-else class="space-y-4">
                <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                     class="flex items-center justify-between py-3 border-b last:border-0"
                     :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                  <div>
                    <p class="text-sm font-semibold" :class="isDark ? 'text-zinc-200' : 'text-zinc-700'">
                      {{ opcao.nome }}
                    </p>
                    <p v-if="opcao.tempo_estimado" class="text-xs"
                       :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
                      {{ opcao.tempo_estimado }}
                    </p>
                  </div>
                  <span class="text-sm font-bold" :style="{ color: 'var(--cor-primaria)' }">
                    {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                  </span>
                </div>
              </div>

              <!-- Location -->
              <div v-if="loja.localizacao" class="mt-6 pt-4 border-t"
                   :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                <p class="text-xs font-bold uppercase tracking-widest mb-2"
                   :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Localização</p>
                <p class="text-sm" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
                  📍 {{ loja.localizacao }}
                </p>
              </div>
            </div>
          </section>

          <!-- Product Sliders -->
          <section class="mb-20">
            <!-- Featured Products -->
            <ProductSlider 
              title="Em Destaque" 
              icon="⭐"
              :params="{ loja_id: lojaId, destaque: true }" 
              :isDark="isDark"
              cardBorderRadius="rounded-none"
              hoverEffect="hover:-translate-y-1 hover:shadow-2xl"
              :hoverBorderClass="isDark ? 'hover:border-zinc-600' : 'hover:border-zinc-300'"
              productNameHoverClass="group-hover:text-current"
              :priceClass="'font-bold'"
              :priceStyle="{ color: 'var(--cor-primaria)' }"
              @product-click="selectedProduct = $event" 
            />

            <!-- By Type -->
            <template v-if="tiposExistentes.length > 0">
              <div class="flex items-center gap-4 my-10">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                <span class="text-xs font-bold uppercase tracking-[0.3em]"
                      :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Por Tipo</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
              </div>
              <div v-for="tipo in tiposExistentes" :key="'tipo-' + tipo.id" :id="'tipo-' + tipo.id">
                <ProductSlider 
                  :title="tipo.nome" 
                  :icon="tipoIcon(tipo.nome)"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }" 
                  :isDark="isDark"
                  cardBorderRadius="rounded-none"
                  @product-click="selectedProduct = $event" 
                />
              </div>
            </template>

            <!-- By Category -->
            <template v-if="categoriasExistentes.length > 0">
              <div class="flex items-center gap-4 my-10">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                <span class="text-xs font-bold uppercase tracking-[0.3em]"
                      :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Por Categoria</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
              </div>
              <div v-for="cat in categoriasExistentes" :key="'cat-' + cat.id" :id="'cat-' + cat.id">
                <ProductSlider 
                  :title="cat.nome" 
                  :icon="cat.icone || '📂'"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }" 
                  :isDark="isDark"
                  cardBorderRadius="rounded-none"
                  @product-click="selectedProduct = $event" 
                />
              </div>
            </template>
          </section>

          <!-- Full Catalog -->
          <section id="catalogo" class="mb-20">
            <div class="mb-8">
              <h2 class="text-3xl font-black tracking-tight"
                  :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                Menu Completo
              </h2>
              <p class="text-sm mt-2" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
                Explore todos os nossos pratos e bebidas
              </p>
            </div>
            
            <ProductCatalog 
              :loja-id="lojaId" 
              :isDark="isDark"
              cardBorderRadius="rounded-none"
              filterContainerRadius="rounded-none"
              tabBorderRadius="rounded-none"
              inputBorderRadius="rounded-none"
              skeletonClass="rounded-none"
              :activeTabClass="'text-white'"
              :activeTabStyle="{ backgroundColor: 'var(--cor-primaria)' }"
              hoverEffect="hover:-translate-y-1 hover:shadow-2xl"
              :hoverBorderClass="isDark ? 'hover:border-zinc-600' : 'hover:border-zinc-300'"
              :priceClass="'font-bold'"
              productNameHoverClass="group-hover:text-current"
              @product-click="selectedProduct = $event" 
            />
          </section>

          <!-- Reviews Section -->
          <section id="avaliacoes" class="mb-20">
            <div class="mb-8">
              <h2 class="text-3xl font-black tracking-tight"
                  :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
                Avaliações
              </h2>
              <p class="text-sm mt-2" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
                O que os nossos clientes dizem
              </p>
            </div>
            
            <AvaliacaoLoja 
              :loja-id="lojaId" 
              :isDark="isDark"
              summaryBorderRadius="rounded-none"
              formBorderRadius="rounded-none"
              textareaBorderRadius="rounded-none"
              buttonBorderRadius="rounded-none"
              reviewCardBorderRadius="rounded-none"
              skeletonClass="rounded-none"
              :starActiveClass="'text-amber-400'"
              progressBarClass="bg-amber-400"
              :submitButtonClass="'text-white hover:opacity-90'"
              :submitButtonStyle="{ backgroundColor: 'var(--cor-primaria)' }"
              :ownReviewBorderClass="isDark 
                ? 'bg-zinc-900 border-l-4' 
                : 'bg-white border-l-4'"
              :ownReviewBorderStyle="{ borderLeftColor: 'var(--cor-primaria)' }"
              @rating-updated="onRatingUpdated" 
            />
          </section>

        </div>

        <!-- Footer -->
        <footer v-if="temFooter" class="border-t"
                :class="isDark ? 'border-zinc-800 bg-zinc-900/50' : 'border-gray-200 bg-white'">
          <div class="max-w-7xl mx-auto px-6 py-16">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
              <!-- Brand -->
              <div>
                <div class="flex items-center gap-4 mb-4">
                  <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" 
                       class="w-12 h-12 object-cover" />
                  <div v-else class="w-12 h-12 flex items-center justify-center text-lg font-black text-white"
                       :style="{ backgroundColor: 'var(--cor-primaria)' }">
                    {{ loja.nome.charAt(0) }}
                  </div>
                  <div>
                    <p class="font-bold text-lg" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">
                      {{ loja.nome }}
                    </p>
                    <p class="text-xs uppercase tracking-widest"
                       :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">
                      {{ loja.categoria }}
                    </p>
                  </div>
                </div>
                <p class="text-sm leading-relaxed"
                   :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">
                  {{ loja.descricao }}
                </p>
              </div>

              <!-- Policies -->
              <div v-if="loja.politica_devolucao || loja.termos_servico || loja.politica_privacidade" 
                   class="space-y-3">
                <p class="text-xs font-bold uppercase tracking-widest mb-4"
                   :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Informações</p>
                <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'"
                  class="block text-sm font-medium transition"
                  :class="isDark ? 'text-zinc-400 hover:text-white' : 'text-zinc-500 hover:text-zinc-800'">
                  Política de Devoluções
                </button>
                <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                  class="block text-sm font-medium transition"
                  :class="isDark ? 'text-zinc-400 hover:text-white' : 'text-zinc-500 hover:text-zinc-800'">
                  Termos de Serviço
                </button>
                <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                  class="block text-sm font-medium transition"
                  :class="isDark ? 'text-zinc-400 hover:text-white' : 'text-zinc-500 hover:text-zinc-800'">
                  Política de Privacidade
                </button>
              </div>

              <!-- Contact -->
              <div v-if="loja.localizacao">
                <p class="text-xs font-bold uppercase tracking-widest mb-4"
                   :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Localização</p>
                <p class="text-sm" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
                  {{ loja.localizacao }}
                </p>
              </div>
            </div>

            <!-- Copyright -->
            <div class="text-center text-xs pt-8 border-t"
                 :class="isDark ? 'text-zinc-700 border-zinc-800' : 'text-zinc-400 border-gray-200'">
              © {{ new Date().getFullYear() }} {{ loja.nome }}. Todos os direitos reservados.
            </div>
          </div>
        </footer>
      </main>

      <!-- Policy Modal -->
      <div v-if="modalPolitica" 
           class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-zinc-900 border border-zinc-800' : 'bg-white border border-gray-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-gray-200'">
            <h3 class="text-base font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Política de Devoluções'
               : modalPolitica === 'termos'    ? 'Termos de Serviço'
               :                                 'Política de Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 flex items-center justify-center transition"
              :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4"
                   :class="isDark ? 'text-zinc-400' : 'text-zinc-600'"
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

    <!-- Not Found State -->
    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center text-center"
         :class="isDark ? 'bg-zinc-950' : 'bg-gray-50'">
      <p class="text-2xl font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">
        Restaurante não encontrado
      </p>
      <button @click="$router.back()" class="mt-3 text-sm font-medium"
              :style="{ color: 'var(--cor-primaria)' }">
        ← Voltar
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useLojaData }   from '@/composables/useLojaData'
import ProductInfoCard   from '@/components/product/productInfoCard.vue'
import MultiCart         from '@/components/cart/multiCart.vue'
import ProductSlider     from '@/components/sliders/ProductSlider.vue'
import Profile           from '@/components/profile/UserProfile.vue'
import ProductCatalog    from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja     from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateRestauranteModerno',

  components: {
    ProductInfoCard,
    MultiCart,
    ProductSlider,
    Profile,
    ProductCatalog,
    AvaliacaoLoja,
  },

  props: {
    tema: {
      type: Object,
      default: () => ({
        id: 'restaurante_moderno',
        corPrimaria: '#dc2626',
        corSecundaria: '#1c1c1e',
        darkMode: true,
      }),
    },
  },

  emits: ['toggle-dark'],

  setup (props, { emit }) {
    const selectedProduct = ref(null)
    const modalPolitica   = ref(null)

    const {
      loja, loading, lojaId, user,
      tiposExistentes, categoriasExistentes,
      metodosPagamento, opcoesEntrega,
      backendUrl,
      logOut,
    } = useLojaData()

    const isDark = computed(() => props.tema?.darkMode ?? true)

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#dc2626',
      '--cor-secundaria': props.tema?.corSecundaria || '#1c1c1e',
    }))

    const temFooter = computed(() => {
      return loja.value?.descricao || 
             loja.value?.politica_devolucao || 
             loja.value?.termos_servico ||
             loja.value?.politica_privacidade
    })

    function toggleDark () {
      emit('toggle-dark', !isDark.value)
    }

    function scrollToId (id) {
      const el = document.getElementById(id)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }

    function formatPrice (val) {
      return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
    }

    function isVideo (url) {
      if (!url) return false
      return /\.(mp4|webm|ogg)$/i.test(url)
    }

    function tipoIcon (nome) {
      const map = {
        'bebidas': '🍹', 'drinks': '🍹',
        'entradas': '🥗', 'starters': '🥗',
        'pratos': '🍽️', 'mains': '🍽️', 'principais': '🍽️',
        'sobremesas': '🍰', 'desserts': '🍰',
        'snacks': '🍿',
        'pizzas': '🍕', 'pizza': '🍕',
        'burgers': '🍔', 'hambúrgueres': '🍔',
        'sushi': '🍣',
        'vegetariano': '🥬', 'vegan': '🌱',
        'café': '☕', 'coffee': '☕',
      }
      const key = nome?.toLowerCase() || ''
      return map[key] || '📂'
    }

    function metodoPagamentoIcon (tipo) {
      const map = {
        'multibanco': '💳', 'mbway': '📱', 'paypal': '🅿️',
        'dinheiro': '💵', 'cash': '💵', 'cartão': '💳', 'card': '💳',
        'transferência': '🏦', 'transfer': '🏦',
      }
      const key = tipo?.toLowerCase() || ''
      return map[key] || '💰'
    }

    function onRatingUpdated (data) {
      if (loja.value && data.media) {
        loja.value.rating_medio = parseFloat(data.media.toFixed(1))
      }
    }

    return {
      // Data
      selectedProduct,
      modalPolitica,
      loja,
      loading,
      lojaId,
      user,
      tiposExistentes,
      categoriasExistentes,
      metodosPagamento,
      opcoesEntrega,
      backendUrl,
      
      // Computed
      isDark,
      cssVars,
      temFooter,
      
      // Methods
      toggleDark,
      scrollToId,
      formatPrice,
      isVideo,
      tipoIcon,
      metodoPagamentoIcon,
      logOut,
      onRatingUpdated,
    }
  },
}
</script>

<style scoped>
/* Custom scrollbar for dark mode */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #27272a;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #3f3f46;
}
</style>
