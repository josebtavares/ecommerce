<template>
  <div class="classico-root min-h-screen transition-colors duration-300"
       :class="isDark ? 'classico-fundo text-zinc-100' : 'bg-gray-50 text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <svg class="animate-spin h-10 w-10" style="color: var(--cor-primaria)"
           xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>

    <template v-else-if="loja">
      <!-- ── BARRA FIXA — transparente sobre o banner, sólida ao descer (ícones da direita: assets/loja-acoes.css) ── -->
      <header class="classico-bar" :class="{ 'classico-bar--solida': scrolled, 'classico-bar--clara': !isDark }">
        <button @click="$router.back()" aria-label="Voltar"
          class="w-9 h-9 rounded-full flex items-center justify-center transition backdrop-blur-sm flex-shrink-0"
          :class="scrolled && !isDark ? 'bg-gray-100 hover:bg-gray-200' : 'bg-black/50 hover:bg-black/70'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="scrolled && !isDark ? 'text-zinc-700' : 'text-white'"
               fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <!-- Toggle dark/light — ao lado do botão voltar -->
        <button @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'"
          class="w-9 h-9 rounded-full flex items-center justify-center transition backdrop-blur-sm flex-shrink-0"
          :class="isDark ? 'bg-black/50 hover:bg-black/70' : (scrolled ? 'bg-gray-100 hover:bg-gray-200' : 'bg-white/70 hover:bg-white/90')">
          <!-- Ícone sol (modo dark → carrega para light) -->
          <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Ícone lua (modo light → carrega para dark) -->
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-zinc-700" fill="currentColor" viewBox="0 0 24 24">
            <path d="M21.64 13.02A9 9 0 1 1 10.98 2.36 7 7 0 0 0 21.64 13.02Z" />
          </svg>
        </button>

        <!-- nome da loja: aparece quando o banner sai do ecrã -->
        <span class="classico-bar__nome" :class="{ 'classico-bar__nome--on': scrolled }">
          <img v-if="loja.logo_url" :src="loja.logo_url" alt="" class="w-7 h-7 rounded-lg object-cover flex-shrink-0" />
          <span class="truncate">{{ loja.nome }}</span>
        </span>
      </header>

      <!-- ── HERO ── -->
      <section class="relative h-[55vh] min-h-[360px] overflow-hidden">
        <video v-if="isVideo(loja.banner_url)"
          :src="loja.banner_url" :poster="loja.banner_poster_url"
          class="w-full h-full object-cover"
          v-video-visivel muted loop playsinline></video>
        <img v-else
          :src="loja.banner_url || defaultBanner"
          :alt="loja.nome" class="w-full h-full object-cover" />

            
        <div class="absolute inset-0 bg-gradient-to-t"
             :class="isDark ? 'classico-degrade' : 'from-gray-900/80 via-gray-900/30 to-transparent'"/>

        <div class="absolute bottom-0 left-0 p-8 flex items-end gap-5">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome"
               class="w-20 h-20 rounded-2xl object-cover border-2 border-white/20 shadow-xl flex-shrink-0" />
          <div v-else class="w-20 h-20 rounded-2xl flex items-center justify-center flex-shrink-0 border-2 border-white/20"
               :style="{ backgroundColor: 'var(--cor-primaria)' }">
            <span class="text-3xl font-bold text-white">{{ loja.nome.charAt(0) }}</span>
          </div>
          <div class="text-white">
            <span class="inline-block px-2 py-0.5 rounded-full text-white text-[10px] font-bold uppercase tracking-wider mb-2"
                  :style="{ backgroundColor: 'var(--cor-primaria)' }">
              {{ loja.categoria }}
            </span>
            <h1 class="text-3xl md:text-4xl font-extrabold text-white leading-tight">{{ loja.nome }}</h1>
            <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />
            <EstadoLoja :horario="loja.horario" :loja-id="lojaId" class="loja-estado" />
            <div class="flex items-center gap-4 mt-2 text-sm text-zinc-300 flex-wrap">
              <span v-if="loja.localizacao" class="inline-flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {{ loja.localizacao }}
              </span>
              <span v-if="loja.rating_medio" class="inline-flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {{ loja.rating_medio }}
                <span v-if="loja.total_avaliacoes" class="text-zinc-500">({{ loja.total_avaliacoes }})</span>
              </span>
              <span v-if="loja.entrega_ativa" class="inline-flex items-center gap-1 text-green-400">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                Entrega disponível
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- ── SIDEBAR + MAIN ── -->
      <div class="flex">
        <transition enter-active-class="transition duration-300" enter-from-class="-translate-x-full"
                    leave-active-class="transition duration-200" leave-to-class="-translate-x-full">
          <aside v-if="sidebarAberta"
                 class="fixed left-0 top-0 h-screen w-64 overflow-y-auto z-30 pt-6"
                 :class="isDark ? 'classico-painel border-r border-zinc-800' : 'bg-white border-r border-gray-200 shadow-xl'">
            <div class="flex items-center justify-between px-5 mb-5">
              <h3 class="text-sm font-bold" :class="isDark ? 'text-zinc-300' : 'text-zinc-700'">Navegar</h3>
              <button @click="sidebarAberta = false"
                class="w-7 h-7 rounded-lg flex items-center justify-center transition"
                :class="isDark ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-gray-100 hover:bg-gray-200'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'"
                     fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div v-if="tiposExistentes.length > 0" class="px-3 mb-5">
              <p class="text-[10px] font-bold uppercase tracking-wider px-2 mb-2"
                 :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Tipos</p>
              <button v-for="tipo in tiposExistentes" :key="tipo.id"
                @click="scrollToId('tipo-' + tipo.id); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100 hover:text-zinc-900'">
                <span class="capitalize">{{ tipo.nome }}</span>
              </button>
            </div>
            <div v-if="categoriasExistentes.length > 0" class="px-3 mb-5 border-t pt-4"
                 :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <p class="text-[10px] font-bold uppercase tracking-wider px-2 mb-2"
                 :class="isDark ? 'text-zinc-600' : 'text-zinc-400'">Categorias</p>
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100 hover:text-zinc-900'">
                <span class="capitalize">{{ cat.nome }}</span>
              </button>
            </div>
            <div class="px-3 border-t pt-4" :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <button @click="scrollToId(soServicos ? 'servicos' : 'catalogo'); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100'">{{ soServicos ? 'Serviços' : 'Catálogo completo' }}</button>
              <button @click="scrollToId('avaliacoes'); sidebarAberta = false"
                class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition text-left"
                :class="isDark ? 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100' : 'text-zinc-600 hover:bg-gray-100'">
                Avaliações
              </button>
            </div>
          </aside>
        </transition>
        <div v-if="sidebarAberta" class="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm"
             @click="sidebarAberta = false" />
        <button v-if="temSidebar" @click="sidebarAberta = !sidebarAberta"
          class="fixed bottom-6 left-6 z-30 w-12 h-12 rounded-xl flex items-center justify-center shadow-lg transition border"
          :class="isDark ? 'classico-painel classico-painel--hover border-zinc-700' : 'bg-white border-gray-200 hover:bg-gray-50 shadow-md'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5"
               :class="isDark ? 'text-zinc-300' : 'text-zinc-600'"
               fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <main class="flex-1 min-w-0">
          <div class="max-w-6xl mx-auto px-6 py-8">
            <!-- Info cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
              <div class="md:col-span-2 rounded-2xl p-5 border"
                   :class="isDark ? 'classico-painel border-zinc-800' : 'bg-white border-gray-200 shadow-sm'">
                <h2 class="text-sm font-bold uppercase tracking-wider mb-3"
                    :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Sobre a loja</h2>
                <p class="text-sm leading-relaxed" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
                  {{ loja.descricao || 'Sem descrição disponível.' }}
                </p>
                <div v-if="metodosPagamento.length > 0" class="mt-4 pt-4 border-t"
                     :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                  <p class="text-xs font-bold uppercase tracking-wider mb-2"
                     :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Pagamento aceite</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="m in metodosPagamento" :key="m.id"
                          class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs"
                          :class="isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-gray-100 text-zinc-600'">
                      {{ m.tipo }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="rounded-2xl p-5 border"
                   :class="isDark ? 'classico-painel border-zinc-800' : 'bg-white border-gray-200 shadow-sm'">
                <h2 class="text-sm font-bold uppercase tracking-wider mb-3"
                    :class="isDark ? 'text-zinc-400' : 'text-zinc-500'">Entrega</h2>
                <div v-if="opcoesEntrega.length === 0" class="text-sm"
                     :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Sem opções configuradas.</div>
                <div v-else class="space-y-2">
                  <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                       class="flex items-center justify-between py-2 border-b last:border-0"
                       :class="isDark ? 'border-zinc-800' : 'border-gray-100'">
                    <div>
                      <p class="text-sm font-medium" :class="isDark ? 'text-zinc-200' : 'text-zinc-700'">{{ opcao.nome }}</p>
                      <p v-if="opcao.tempo_estimado" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ opcao.tempo_estimado }}</p>
                    </div>
                    <span class="text-sm font-bold" :style="{ color: 'var(--cor-primaria)' }">
                      {{ opcao.preco == 0 ? 'Grátis' : formatPrice(opcao.preco) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sliders -->
            <ProductSlider title="Em Destaque"
              :params="{ loja_id: lojaId, destaque: true }" :isDark="isDark"
              @product-click="selectedProduct = $event" />

            <template v-if="tiposExistentes.length > 0">
              <div class="flex items-center gap-3 my-6">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                <span class="text-xs font-bold uppercase tracking-widest"
                      :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Por tipo</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
              </div>
              <div v-for="tipo in tiposExistentes" :key="'tipo-' + tipo.id" :id="'tipo-' + tipo.id">
                <ProductSlider :title="tipo.nome"
                  :params="{ loja_id: lojaId, tipo: tipo.nome }" :isDark="isDark"
                  @product-click="selectedProduct = $event" />
              </div>
            </template>

            <template v-if="categoriasExistentes.length > 0">
              <div class="flex items-center gap-3 my-6">
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
                <span class="text-xs font-bold uppercase tracking-widest"
                      :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">Por categoria</span>
                <div class="h-px flex-1" :class="isDark ? 'bg-zinc-800' : 'bg-gray-200'"></div>
              </div>
              <div v-for="cat in categoriasExistentes" :key="'cat-' + cat.id" :id="'cat-' + cat.id">
                <ProductSlider :title="cat.nome"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }" :isDark="isDark"
                  @product-click="selectedProduct = $event" />
              </div>
            </template>

            <!-- Serviços (marcações) -->
            <SeccaoServicos :loja-id="lojaId" :isDark="isDark" :cor="tema?.corPrimaria || '#dc2626'" class="mt-10" />

            <template v-if="!soServicos">
              <div id="catalogo" class="mt-10 mb-4">
                <h2 class="text-xl font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Catálogo completo</h2>
                <p class="text-sm mt-1" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">Filtra por tipo, categoria ou pesquisa</p>
              </div>
              <ProductCatalog :loja-id="lojaId" :isDark="isDark" @product-click="selectedProduct = $event" />
            </template>

            <div id="avaliacoes" class="mt-10">
              <h2 class="text-xl font-bold mb-5" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">Avaliações</h2>
              <AvaliacaoLoja :loja-id="lojaId" :isDark="isDark" @rating-updated="onRatingUpdated" />
            </div>

            <footer v-if="temFooter" class="mt-16 pt-8 border-t"
                    :class="isDark ? 'border-zinc-800' : 'border-gray-200'">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div>
                  <div class="flex items-center gap-3 mb-3">
                    <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-8 h-8 rounded-lg object-cover" />
                    <p class="font-bold" :class="isDark ? 'text-zinc-200' : 'text-zinc-800'">{{ loja.nome }}</p>
                  </div>
                  <p class="text-xs leading-relaxed" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ loja.descricao }}</p>
                </div>
                <div v-if="loja.politica_devolucao" class="space-y-2">
                  <button @click="modalPolitica = 'devolucao'"
                    class="text-sm font-semibold transition"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-500 hover:text-zinc-800'">
                    Política de devoluções
                  </button>
                  <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'"
                    class="block text-sm font-semibold transition"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-500 hover:text-zinc-800'">
                    Termos de serviço
                  </button>
                  <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'"
                    class="block text-sm font-semibold transition"
                    :class="isDark ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-500 hover:text-zinc-800'">
                    Política de privacidade
                  </button>
                </div>
              </div>
              <div class="text-center text-xs pt-4 border-t"
                   :class="isDark ? 'text-zinc-700 border-zinc-900' : 'text-zinc-400 border-gray-200'">
                © {{ new Date().getFullYear() }} {{ loja.nome }}
              </div>
            </footer>
          </div>
        </main>
      </div>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-2xl border w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'classico-painel border-zinc-800' : 'bg-white border-gray-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'classico-painel border-zinc-800' : 'bg-white border-gray-200'">
            <h3 class="text-base font-bold" :class="isDark ? 'text-zinc-100' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Política de devoluções'
               : modalPolitica === 'termos'    ? 'Termos de serviço'
               :                                 'Política de privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-full flex items-center justify-center transition"
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

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center text-center"
         :class="isDark ? 'classico-fundo' : 'bg-gray-50'">
      <p class="text-2xl font-bold" :class="isDark ? 'text-zinc-400' : 'text-zinc-600'">Loja não encontrada</p>
      <button @click="$router.back()" class="mt-2 text-sm" :style="{ color: 'var(--cor-primaria)' }">← Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useLojaData }   from '@/composables/useLojaData'
import ProductInfoCard   from '@/components/product/productInfoCard.vue'
import MultiCart         from '@/components/cart/multiCart.vue'
import ProductSlider     from '@/components/sliders/ProductSlider.vue'
import Profile           from '@/components/profile/UserProfile.vue'
import ProductCatalog    from '@/components/catalog/ProductCatalog.vue'
import SeccaoServicos from '@/components/servicos/loja/SeccaoServicos.vue'
import BotaoFavorito     from '@/components/favoritos/BotaoFavorito.vue'
import EstadoLoja from '@/components/horario/EstadoLoja.vue'
import AvaliacaoLoja     from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateClassico',
  components: { SeccaoServicos, BotaoFavorito, EstadoLoja, ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],

  props: {
    tema: { type: Object, default: () => ({ id: 'classico', corPrimaria: '#dc2626', corSecundaria: '#1c1c1e', darkMode: true }) }
  },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    watch(() => props.tema?.darkMode, v => { isDark.value = v !== false })
    const lojaData = useLojaData()
    const cssVars  = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#dc2626',
      '--cor-secundaria': props.tema?.corSecundaria || '#1c1c1e',
    }))
    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () {
      isDark.value = !isDark.value
      emit('toggle-dark', isDark.value)  // avisa o LojaPublica.vue para guardar no localStorage
    }

    function isVideo (url) {
      return /\.(mp4|webm|mov|mkv)$/i.test(url || '')
    }

    // barra fixa: fica sólida (e mostra o nome) depois de descer um pouco
    const scrolled = ref(false)
    function onScroll () { scrolled.value = window.scrollY > 80 }
    onMounted(() => { window.addEventListener('scroll', onScroll, { passive: true }); onScroll() })
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, cssVars, user, toggleDark, isVideo, scrolled, ...lojaData }
  }
}
</script>
<style scoped>
/* Mesma geometria do Restaurante Moderno: barra virtual de 68px / margem 28px
   (mobile 60px / 14px). Os ícones da direita (assets/loja-acoes.css) e os
   botões voltar + tema da esquerda ficam centrados na mesma linha. */
.classico-root {
  --acoes-altura: 68px;
  --acoes-direita: 28px;
}

@media (max-width: 640px) {
  .classico-root {
    --acoes-altura: 60px;
    --acoes-direita: 14px;
  }
}

/* ── Cor secundária = fundo do modo escuro (painéis um pouco mais claros) ── */
.classico-fundo { background: var(--cor-secundaria, #1c1c1e); }
.classico-painel { background: color-mix(in srgb, var(--cor-secundaria, #1c1c1e) 92%, #fff 8%); }
.classico-painel--hover:hover { background: color-mix(in srgb, var(--cor-secundaria, #1c1c1e) 86%, #fff 14%); }
.classico-degrade {
  background-image: linear-gradient(to top, var(--cor-secundaria, #1c1c1e),
    color-mix(in srgb, var(--cor-secundaria, #1c1c1e) 50%, transparent), transparent) !important;
}

/* ── Barra fixa ──
   abaixo do carrinho (z-30) e do perfil (z-40); reserva à direita o espaço dos ícones */
.classico-bar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--acoes-altura);
  display: flex; align-items: center; gap: 10px;
  padding: 0 calc(var(--acoes-direita) + var(--acoes-espaco) + 16px) 0 var(--acoes-direita);
  color: #fff;
  transition: background-color .3s, box-shadow .3s;
}
.classico-bar--solida {
  background: color-mix(in srgb, var(--cor-secundaria, #1c1c1e) 90%, transparent);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .08);
}
.classico-bar--clara.classico-bar--solida {
  background: rgba(249, 250, 251, .92);
  box-shadow: 0 1px 0 rgba(0, 0, 0, .08);
  color: #18181b;
}
.classico-bar__nome {
  display: flex; align-items: center; gap: 8px; min-width: 0;
  margin-left: 6px; font-weight: 700; font-size: 15px;
  opacity: 0; transform: translateY(4px); pointer-events: none;
  transition: opacity .3s, transform .3s;
}
.classico-bar__nome--on { opacity: 1; transform: none; }

/* os saltos do menu lateral não ficam escondidos atrás da barra */
.classico-root [id] { scroll-margin-top: calc(var(--acoes-altura) + 12px); }
</style>
