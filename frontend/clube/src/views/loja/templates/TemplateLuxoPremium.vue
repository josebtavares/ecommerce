<!-- TemplateLuxoPremium.vue — Ultra-premium, ouro/preto absoluto, jóias e marcas de prestígio -->
<template>
  <div class="min-h-screen transition-colors duration-700"
       :class="isDark ? 'bg-[#030303] text-amber-50' : 'bg-[#faf9f7] text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center"
         :class="isDark ? 'bg-[#030303]' : 'bg-[#faf9f7]'">
      <div class="text-center space-y-4">
        <div class="w-16 h-px mx-auto animate-pulse" style="background:var(--cor-primaria)"></div>
        <p class="text-[9px] tracking-[0.5em] uppercase" style="color:var(--cor-primaria)">Un moment…</p>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HEADER ultra-fino ── -->
      <header class="fixed top-0 left-0 right-0 z-30 transition-all duration-700"
              :class="scrolled
                ? (isDark ? 'bg-[#030303]/98 backdrop-blur-xl border-b border-[#c9a84c]/10' : 'bg-[#faf9f7]/98 backdrop-blur-xl border-b border-[#c9a84c]/20')
                : 'bg-transparent'">
        <div class="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
          <button @click="$router.back()"
            class="text-[9px] tracking-[0.4em] uppercase transition-colors"
            :class="isDark ? 'text-[#c9a84c]/40 hover:text-[#c9a84c]' : 'text-[#c9a84c]/60 hover:text-[#8a6e28]'">
            ← Retour
          </button>

          <!-- Logo central ao scroll -->
          <div v-if="scrolled && loja" class="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
            <p class="text-[9px] tracking-[0.5em] uppercase" style="color:var(--cor-primaria)">{{ loja.nome }}</p>
          </div>

          <button @click="toggleDark"
            class="w-7 h-7 rounded-full border flex items-center justify-center transition"
            :class="isDark ? 'border-[#c9a84c]/20 text-[#c9a84c]/50 hover:border-[#c9a84c]/60' : 'border-[#c9a84c]/30 text-[#8a6e28] hover:border-[#c9a84c]'">
            <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
        </div>
      </header>

      <!-- ── HERO full-bleed minimalista ── -->
      <section class="relative min-h-screen flex flex-col justify-end overflow-hidden">
        <!-- Imagem de fundo com opacidade muito baixa -->
        <div class="absolute inset-0">
          <video v-if="isVideo(loja.banner_url)"
            :src="loja.banner_url"
            class="w-full h-full object-cover"
            :class="isDark ? 'opacity-20' : 'opacity-15'"
            autoplay muted loop playsinline></video>
          <img v-else
            :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
            :alt="loja.nome"
            class="w-full h-full object-cover"
            :class="isDark ? 'opacity-20' : 'opacity-15'" />
          <div class="absolute inset-0"
               :class="isDark
                 ? 'bg-gradient-to-t from-[#030303] via-[#030303]/70 to-[#030303]/30'
                 : 'bg-gradient-to-t from-[#faf9f7] via-[#faf9f7]/80 to-transparent'" />
          <!-- Glow de cor dourada subtil -->
          <div class="absolute inset-0 pointer-events-none" style="background:radial-gradient(ellipse at 50% 80%,rgba(201,168,76,0.06),transparent 70%)"></div>
        </div>

        <!-- Conteúdo principal centrado -->
        <div class="relative max-w-4xl mx-auto px-10 pb-24 pt-32 w-full text-center">
          <!-- Linha decorativa -->
          <div class="flex items-center gap-4 justify-center mb-10">
            <div class="h-px w-16" style="background:var(--cor-primaria);opacity:0.4"></div>
            <div class="w-1.5 h-1.5 rotate-45" style="background:var(--cor-primaria);opacity:0.6"></div>
            <div class="h-px w-16" style="background:var(--cor-primaria);opacity:0.4"></div>
          </div>

          <p class="text-[9px] tracking-[0.6em] uppercase mb-8"
             :class="isDark ? 'text-[#c9a84c]/50' : 'text-[#8a6e28]/60'">
            {{ loja.categoria }}<span v-if="loja.localizacao" class="ml-4 opacity-60">· {{ loja.localizacao }}</span>
          </p>

          <!-- Nome enorme, serif leve -->
          <h1 class="font-light tracking-tight leading-[0.9] mb-10"
              style="font-size:clamp(3.5rem,10vw,9rem);font-family:'Playfair Display',Georgia,serif;font-style:italic">
            <span :class="isDark ? 'text-amber-50' : 'text-zinc-900'">{{ loja.nome }}</span>
          </h1>

          <p v-if="loja.descricao"
             class="text-base font-light leading-relaxed max-w-lg mx-auto mb-12"
             :class="isDark ? 'text-amber-50/30' : 'text-zinc-500'">
            {{ loja.descricao }}
          </p>

          <!-- Linha decorativa fundo -->
          <div class="flex items-center gap-4 justify-center mb-12">
            <div class="h-px w-16" style="background:var(--cor-primaria);opacity:0.4"></div>
            <span class="text-[9px] tracking-[0.4em] uppercase" style="color:var(--cor-primaria);opacity:0.5">Collection</span>
            <div class="h-px w-16" style="background:var(--cor-primaria);opacity:0.4"></div>
          </div>

          <button @click="scrollToId('colecao')"
            class="inline-flex items-center gap-4 text-[9px] tracking-[0.4em] uppercase transition-all duration-500 group"
            :class="isDark ? 'text-[#c9a84c]/60 hover:text-[#c9a84c]' : 'text-[#8a6e28]/60 hover:text-[#8a6e28]'">
            <span class="h-px w-10 transition-all duration-500 group-hover:w-20" style="background:var(--cor-primaria)"></span>
            Découvrir
            <span class="h-px w-10 transition-all duration-500 group-hover:w-20" style="background:var(--cor-primaria)"></span>
          </button>
        </div>

        <!-- Stats bottom center -->
        <div class="absolute bottom-6 left-0 right-0 flex justify-center gap-20 pb-4">
          <div v-if="loja.rating_medio" class="text-center">
            <p class="text-2xl font-light" style="font-family:Georgia,serif;color:var(--cor-primaria)">{{ loja.rating_medio }}</p>
            <p class="text-[8px] tracking-[0.4em] uppercase mt-1" :class="isDark ? 'text-[#c9a84c]/25' : 'text-[#8a6e28]/40'">Rating</p>
          </div>
          <div v-if="loja.total_avaliacoes" class="text-center">
            <p class="text-2xl font-light" style="font-family:Georgia,serif" :class="isDark ? 'text-amber-50/60' : 'text-zinc-600'">{{ loja.total_avaliacoes }}</p>
            <p class="text-[8px] tracking-[0.4em] uppercase mt-1" :class="isDark ? 'text-[#c9a84c]/25' : 'text-[#8a6e28]/40'">Clientes</p>
          </div>
          <div v-if="loja.entrega_ativa" class="text-center">
            <p class="text-2xl font-light" style="font-family:Georgia,serif;color:var(--cor-primaria)">✦</p>
            <p class="text-[8px] tracking-[0.4em] uppercase mt-1" :class="isDark ? 'text-[#c9a84c]/25' : 'text-[#8a6e28]/40'">Exclusivo</p>
          </div>
        </div>
      </section>

      <!-- ── MAIN ── -->
      <main id="colecao">

        <!-- Sobre -->
        <section class="border-t py-24" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
          <div class="max-w-4xl mx-auto px-10">
            <div class="grid grid-cols-1 md:grid-cols-12 gap-16 items-start">
              <div class="md:col-span-3">
                <p class="text-[8px] tracking-[0.5em] uppercase sticky top-24"
                   :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Maison</p>
              </div>
              <div class="md:col-span-9">
                <p class="text-2xl font-light leading-relaxed" style="font-family:'Playfair Display',Georgia,serif;font-style:italic"
                   :class="isDark ? 'text-amber-50/50' : 'text-zinc-600'">
                  {{ loja.descricao || 'Uma maison construída sobre os alicerces da excelência, da raridade e do detalhe absoluto.' }}
                </p>
                <div class="grid grid-cols-2 gap-8 mt-10 pt-8 border-t" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
                  <div v-if="opcoesEntrega.length">
                    <p class="text-[8px] tracking-[0.4em] uppercase mb-4" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Livraison</p>
                    <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="mb-2">
                      <p class="text-sm font-light" :class="isDark ? 'text-amber-50/50' : 'text-zinc-600'">{{ opcao.nome }}</p>
                      <p class="text-xs mt-0.5" style="color:var(--cor-primaria)">
                        {{ opcao.preco == 0 ? 'Gratuit' : formatPrice(opcao.preco) }}
                        <span v-if="opcao.tempo_estimado" class="opacity-40 ml-2">{{ opcao.tempo_estimado }}</span>
                      </p>
                    </div>
                  </div>
                  <div v-if="metodosPagamento.length">
                    <p class="text-[8px] tracking-[0.4em] uppercase mb-4" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Paiement</p>
                    <div class="flex flex-wrap gap-1.5">
                      <span v-for="m in metodosPagamento" :key="m.id"
                            class="text-xs font-light px-2 py-1 rounded border"
                            :class="isDark ? 'border-[#c9a84c]/15 text-amber-50/30' : 'border-[#c9a84c]/25 text-zinc-500'">
                        {{ m.tipo }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Destaques -->
        <section class="border-t py-24" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
          <div class="max-w-4xl mx-auto px-10 mb-14">
            <div class="flex items-center gap-6">
              <p class="text-[8px] tracking-[0.5em] uppercase" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Collection</p>
              <div class="flex-1 h-px" :class="isDark ? 'bg-[#c9a84c]/8' : 'bg-[#c9a84c]/15'"></div>
            </div>
          </div>
          <div class="max-w-6xl mx-auto px-6">
            <ProductSlider
              title="Destaques"
              :params="{ loja_id: lojaId, destaque: true }"
              :isDark="isDark"
              card-width="200px"
              image-height="280px"
              card-height="380px"
              card-border-radius="rounded-none"
              hover-effect="hover:opacity-75 transition-opacity duration-700"
              hover-border-class=""
              product-name-class="font-light tracking-widest uppercase text-xs"
              :price-class="isDark ? 'font-light text-amber-50/50' : 'font-light text-zinc-500'"
              :show-store-name="false"
              :show-badges="false"
              :show-stock="false"
              @product-click="selectedProduct = $event" />
          </div>
        </section>

        <!-- Por tipo -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                   class="border-t py-24" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
            <div class="max-w-4xl mx-auto px-10 mb-14">
              <div class="flex items-center gap-6">
                <p class="text-[8px] tracking-[0.5em] uppercase capitalize" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">{{ tipo.nome }}</p>
                <div class="flex-1 h-px" :class="isDark ? 'bg-[#c9a84c]/8' : 'bg-[#c9a84c]/15'"></div>
              </div>
            </div>
            <div class="max-w-6xl mx-auto px-6">
              <ProductSlider
                :title="tipo.nome"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark"
                card-width="185px" image-height="260px" card-height="360px"
                card-border-radius="rounded-none"
                hover-effect="hover:opacity-70 transition-opacity duration-700"
                hover-border-class=""
                product-name-class="font-light tracking-wider uppercase text-xs"
                :show-store-name="false" :show-badges="false" :show-stock="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Por categoria -->
        <template v-if="categoriasExistentes.length > 0">
          <section v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id"
                   class="border-t py-24" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
            <div class="max-w-4xl mx-auto px-10 mb-14">
              <div class="flex items-center gap-6">
                <p class="text-[8px] tracking-[0.5em] uppercase capitalize" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">{{ cat.nome }}</p>
                <div class="flex-1 h-px" :class="isDark ? 'bg-[#c9a84c]/8' : 'bg-[#c9a84c]/15'"></div>
              </div>
            </div>
            <div class="max-w-6xl mx-auto px-6">
              <ProductSlider
                :title="cat.nome"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark"
                card-width="185px" image-height="260px" card-height="360px"
                card-border-radius="rounded-none"
                hover-effect="hover:opacity-70 transition-opacity duration-700"
                hover-border-class=""
                product-name-class="font-light tracking-wider uppercase text-xs"
                :show-store-name="false" :show-badges="false" :show-stock="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Catálogo -->
        <section id="catalogo" class="border-t py-24" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
          <div class="max-w-6xl mx-auto px-10">
            <div class="flex items-center gap-6 mb-14">
              <p class="text-[8px] tracking-[0.5em] uppercase" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Catalogue</p>
              <div class="flex-1 h-px" :class="isDark ? 'bg-[#c9a84c]/8' : 'bg-[#c9a84c]/15'"></div>
            </div>
            <ProductCatalog
              :loja-id="lojaId" :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3"
              image-height="260px"
              card-border-radius="rounded-none"
              hover-effect="hover:opacity-70 transition-opacity duration-700"
              hover-border-class=""
              tab-border-radius="rounded-none"
              :active-tab-class="isDark ? 'border-b pb-2 text-amber-50/80 font-light tracking-widest uppercase text-xs' : 'border-b pb-2 text-zinc-800 font-light tracking-widest uppercase text-xs'"
              :inactive-tab-dark-class="'text-amber-50/20 hover:text-amber-50/40 pb-2 tracking-widest uppercase text-xs font-light'"
              :inactive-tab-light-class="'text-zinc-400 hover:text-zinc-700 pb-2 tracking-widest uppercase text-xs font-light'"
              input-border-radius="rounded-none"
              filter-container-radius="rounded-none"
              product-name-class="font-light tracking-wider uppercase text-xs"
              :price-class="isDark ? 'font-light text-amber-50/50' : 'font-light text-zinc-500'"
              :show-stock="false" :show-badges="false" :show-category-badges="false"
              @product-click="selectedProduct = $event" />
          </div>
        </section>

        <!-- Avaliações -->
        <section id="avaliacoes" class="border-t py-24" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
          <div class="max-w-6xl mx-auto px-10">
            <div class="flex items-center gap-6 mb-14">
              <p class="text-[8px] tracking-[0.5em] uppercase" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Avis</p>
              <div class="flex-1 h-px" :class="isDark ? 'bg-[#c9a84c]/8' : 'bg-[#c9a84c]/15'"></div>
            </div>
            <AvaliacaoLoja
              :loja-id="lojaId" :isDark="isDark"
              summary-border-radius="rounded-none"
              form-border-radius="rounded-none"
              review-card-border-radius="rounded-none"
              button-border-radius="rounded-none"
              textarea-border-radius="rounded-none"
              :star-active-class="'text-[#c9a84c]'"
              :star-inactive-class="isDark ? 'text-[#c9a84c]/10' : 'text-[#c9a84c]/20'"
              :progress-bar-class="'bg-[#c9a84c]'"
              :submit-button-class="isDark ? 'bg-[#c9a84c]/10 border border-[#c9a84c]/30 text-[#c9a84c] hover:bg-[#c9a84c]/20 font-light tracking-widest uppercase text-xs' : 'bg-zinc-900 text-white font-light tracking-widest uppercase text-xs hover:bg-zinc-700'"
              :own-review-border-class="isDark ? 'border-b border-[#c9a84c]/15' : 'border-b border-[#c9a84c]/20'"
              :review-card-class="isDark ? 'border-b border-[#030303]' : 'border-b border-[#f0ece4]'"
              :load-more-button-class="'text-[9px] tracking-widest uppercase underline underline-offset-4 opacity-30 hover:opacity-60'"
              @rating-updated="onRatingUpdated" />
          </div>
        </section>

        <!-- Footer -->
        <footer class="border-t py-16" :class="isDark ? 'border-[#c9a84c]/8' : 'border-[#c9a84c]/15'">
          <div class="max-w-4xl mx-auto px-10 flex flex-col md:flex-row items-center justify-between gap-6">
            <div class="text-center md:text-left">
              <p class="text-[9px] tracking-[0.5em] uppercase" style="color:var(--cor-primaria);opacity:0.5">{{ loja.nome }}</p>
              <p class="text-[8px] tracking-[0.3em] uppercase mt-1" :class="isDark ? 'text-[#c9a84c]/15' : 'text-[#8a6e28]/20'">© {{ new Date().getFullYear() }}</p>
            </div>
            <div class="flex gap-8 text-[8px] tracking-[0.3em] uppercase">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="transition hover:opacity-80" :class="isDark ? 'text-[#c9a84c]/25 hover:text-[#c9a84c]/60' : 'text-[#8a6e28]/30 hover:text-[#8a6e28]/70'">Retours</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="transition hover:opacity-80" :class="isDark ? 'text-[#c9a84c]/25 hover:text-[#c9a84c]/60' : 'text-[#8a6e28]/30 hover:text-[#8a6e28]/70'">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="transition hover:opacity-80" :class="isDark ? 'text-[#c9a84c]/25 hover:text-[#c9a84c]/60' : 'text-[#8a6e28]/30 hover:text-[#8a6e28]/70'">Privacidade</button>
            </div>
          </div>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-[60] flex items-end justify-center bg-black/70 backdrop-blur-sm" @click.self="modalPolitica = null">
        <div class="w-full max-w-2xl max-h-[70vh] overflow-y-auto" :class="isDark ? 'bg-[#030303] border-t border-[#c9a84c]/10' : 'bg-[#faf9f7] border-t border-[#c9a84c]/20'">
          <div class="flex items-center justify-between px-8 py-5 border-b sticky top-0" :class="isDark ? 'bg-[#030303] border-[#c9a84c]/10' : 'bg-[#faf9f7] border-[#c9a84c]/15'">
            <p class="text-[8px] tracking-[0.5em] uppercase" :class="isDark ? 'text-[#c9a84c]/40' : 'text-[#8a6e28]/50'">
              {{ modalPolitica === 'devolucao' ? 'Retours' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </p>
            <button @click="modalPolitica = null" class="text-[9px] tracking-widest uppercase transition" :class="isDark ? 'text-[#c9a84c]/30 hover:text-[#c9a84c]/70' : 'text-[#8a6e28]/40 hover:text-[#8a6e28]/80'">Fechar</button>
          </div>
          <div class="px-8 py-8 text-sm font-light leading-loose whitespace-pre-wrap" :class="isDark ? 'text-amber-50/30' : 'text-zinc-500'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center" :class="isDark ? 'bg-[#030303]' : 'bg-[#faf9f7]'">
      <p class="text-[9px] tracking-[0.5em] uppercase mb-8" :class="isDark ? 'text-[#c9a84c]/30' : 'text-[#8a6e28]/40'">Maison introuvable</p>
      <button @click="$router.back()" class="text-[9px] tracking-[0.3em] uppercase underline underline-offset-4 transition" style="color:var(--cor-primaria);opacity:0.5">← Retour</button>
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
  name: 'TemplateLuxoPremium',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#c9a84c',
      '--cor-secundaria': props.tema?.corSecundaria || '#030303',
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
  },
}
</script>

<style scoped>
h1 { font-family: 'Playfair Display', Georgia, serif; }
</style>
