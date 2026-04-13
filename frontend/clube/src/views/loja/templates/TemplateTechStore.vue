<!-- TemplateTechStore — Futurista, clean, tons de azul/ciano, estilo Apple/tech -->
<template>
  <div class="min-h-screen transition-colors duration-300"
       :class="isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" />
    <Profile :data="user" class="z-10" @log_out="logOut()" />

    <!-- Sticky nav tech style -->
    <nav class="fixed top-0 left-0 right-0 z-30 transition-all duration-300"
         :class="scrolled 
           ? (isDark ? 'bg-slate-950/80 backdrop-blur-xl border-b border-slate-800' : 'bg-white/80 backdrop-blur-xl border-b border-slate-200 shadow-sm') 
           : ''">
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <button @click="$router.back()"
          class="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
          :class="isDark ? 'bg-slate-800/80 hover:bg-slate-700' : 'bg-slate-100 hover:bg-slate-200'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="isDark ? 'text-slate-300' : 'text-slate-700'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <!-- Logo when scrolled -->
        <div v-if="scrolled && loja" class="flex items-center gap-3">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-8 h-8 rounded-lg object-cover" />
          <span class="font-semibold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ loja.nome }}</span>
        </div>

        <div class="flex items-center gap-3">
          <button @click="scrollToId('catalogo')"
            class="hidden md:flex px-4 py-2 rounded-xl text-sm font-medium transition-all"
            :class="isDark ? 'bg-slate-800 text-slate-300 hover:bg-slate-700' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'">
            Produtos
          </button>
          <button @click="toggleDark"
            class="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
            :class="isDark ? 'bg-slate-800/80 hover:bg-slate-700' : 'bg-slate-100 hover:bg-slate-200'">
            <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21.64 13.02A9 9 0 1 1 10.98 2.36 7 7 0 0 0 21.64 13.02Z" />
            </svg>
          </button>
        </div>
      </div>
    </nav>

    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="relative">
        <div class="w-16 h-16 border-4 border-cyan-500/30 rounded-full"></div>
        <div class="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-cyan-500 rounded-full animate-spin"></div>
      </div>
    </div>

    <template v-else-if="loja">
      <!-- HERO Tech - Gradient mesh background -->
      <section class="relative min-h-[80vh] overflow-hidden">
        <!-- Gradient background -->
        <div class="absolute inset-0" :class="isDark ? 'bg-slate-950' : 'bg-slate-100'">
          <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/20 via-transparent to-blue-600/20"></div>
          <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
          <div class="absolute bottom-1/4 left-1/4 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl"></div>
          <!-- Grid pattern -->
          <div class="absolute inset-0 opacity-[0.03]" 
               style="background-image: linear-gradient(rgba(0,0,0,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,.1) 1px, transparent 1px); background-size: 50px 50px;"></div>
        </div>

        <!-- Content -->
        <div class="relative max-w-7xl mx-auto px-6 pt-32 pb-20">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <!-- Left: Text content -->
            <div>
              <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
                   :class="isDark ? 'bg-cyan-500/10 border border-cyan-500/20' : 'bg-cyan-50 border border-cyan-200'">
                <span class="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                <span class="text-sm font-medium" :style="{ color: 'var(--cor-primaria)' }">{{ loja.categoria }}</span>
              </div>

              <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6"
                  :class="isDark ? 'text-white' : 'text-slate-900'">
                {{ loja.nome }}
              </h1>

              <p v-if="loja.descricao" class="text-lg leading-relaxed mb-8 max-w-lg"
                 :class="isDark ? 'text-slate-400' : 'text-slate-600'">
                {{ loja.descricao.substring(0, 180) }}{{ loja.descricao.length > 180 ? '...' : '' }}
              </p>

              <!-- Stats row -->
              <div class="flex items-center gap-8 mb-8">
                <div v-if="loja.rating_medio" class="flex items-center gap-2">
                  <div class="flex items-center gap-1 px-3 py-1.5 rounded-lg" :style="{ backgroundColor: 'var(--cor-primaria)' }">
                    <svg class="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                    <span class="font-bold text-white">{{ loja.rating_medio }}</span>
                  </div>
                  <span class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">{{ loja.total_avaliacoes }} reviews</span>
                </div>
                <div v-if="loja.entrega_ativa" class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                  <span class="text-sm font-medium text-emerald-500">Entrega Express</span>
                </div>
              </div>

              <!-- CTA buttons -->
              <div class="flex items-center gap-4">
                <button @click="scrollToId('catalogo')"
                  class="px-8 py-4 rounded-xl font-semibold text-white transition-all hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/20"
                  :style="{ backgroundColor: 'var(--cor-primaria)' }">
                  Explorar Produtos
                </button>
                <button @click="scrollToId('especificacoes')"
                  class="px-8 py-4 rounded-xl font-semibold transition-all border"
                  :class="isDark ? 'border-slate-700 text-slate-300 hover:bg-slate-800' : 'border-slate-300 text-slate-700 hover:bg-slate-100'">
                  Saber Mais
                </button>
              </div>
            </div>

            <!-- Right: Logo/Image showcase -->
            <div class="relative flex justify-center">
              <div class="relative">
                <!-- Glow effect -->
                <div class="absolute inset-0 blur-3xl opacity-50" :style="{ backgroundColor: 'var(--cor-primaria)' }"></div>
                <!-- Logo container -->
                <div class="relative w-64 h-64 md:w-80 md:h-80 rounded-3xl overflow-hidden border shadow-2xl"
                     :class="isDark ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-white'">
                  <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full flex items-center justify-center"
                       :style="{ backgroundColor: 'var(--cor-primaria)' }">
                    <span class="text-7xl font-bold text-white">{{ loja.nome.charAt(0) }}</span>
                  </div>
                </div>
                <!-- Floating badges -->
                <div class="absolute -top-4 -right-4 px-4 py-2 rounded-xl shadow-lg"
                     :class="isDark ? 'bg-slate-800' : 'bg-white'" v-if="loja.entrega_ativa">
                  <span class="text-sm font-medium" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Envio Gratis*</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Features bar -->
      <section class="border-y" :class="isDark ? 'border-slate-800 bg-slate-900/50' : 'border-slate-200 bg-white'">
        <div class="max-w-7xl mx-auto px-6 py-8">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                   :class="isDark ? 'bg-cyan-500/10' : 'bg-cyan-50'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :style="{ color: 'var(--cor-primaria)' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <p class="font-semibold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Garantia</p>
                <p class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">Produtos originais</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                   :class="isDark ? 'bg-cyan-500/10' : 'bg-cyan-50'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :style="{ color: 'var(--cor-primaria)' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p class="font-semibold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Entrega Rapida</p>
                <p class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">24-48h uteis</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                   :class="isDark ? 'bg-cyan-500/10' : 'bg-cyan-50'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :style="{ color: 'var(--cor-primaria)' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <p class="font-semibold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Pagamento Seguro</p>
                <p class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">SSL encriptado</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                   :class="isDark ? 'bg-cyan-500/10' : 'bg-cyan-50'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :style="{ color: 'var(--cor-primaria)' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div>
                <p class="font-semibold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Suporte Tech</p>
                <p class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">Ajuda especializada</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Main content -->
      <main class="max-w-7xl mx-auto px-6">
        
        <!-- Featured products -->
        <section class="py-16">
          <div class="flex items-center justify-between mb-8">
            <div>
              <p class="text-sm font-medium mb-1" :style="{ color: 'var(--cor-primaria)' }">NOVIDADES</p>
              <h2 class="text-3xl font-bold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Produtos em Destaque</h2>
            </div>
          </div>
          <ProductSlider title="Destaques" icon=""
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Products by Type -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="tipo in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id" class="py-12 border-t"
                   :class="isDark ? 'border-slate-800' : 'border-slate-200'">
            <div class="flex items-center justify-between mb-8">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                     :class="isDark ? 'bg-slate-800' : 'bg-slate-100'">
                  <span class="text-xl">{{ tipoIcon(tipo.nome) }}</span>
                </div>
                <h2 class="text-2xl font-bold capitalize" :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ tipo.nome }}</h2>
              </div>
            </div>
            <ProductSlider :title="tipo.nome" :icon="tipoIcon(tipo.nome)"
              :params="{ loja_id: lojaId, tipo: tipo.nome }"
              :isDark="isDark" :show-title="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Categories grid -->
        <template v-if="categoriasExistentes.length > 0">
          <section class="py-12 border-t" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
            <div class="mb-8">
              <p class="text-sm font-medium mb-1" :style="{ color: 'var(--cor-primaria)' }">CATEGORIAS</p>
              <h2 class="text-3xl font-bold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Explorar por Categoria</h2>
            </div>
            
            <!-- Category buttons -->
            <div class="flex flex-wrap gap-3 mb-10">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="px-5 py-3 rounded-xl font-medium transition-all flex items-center gap-2 border"
                :class="isDark ? 'border-slate-700 bg-slate-800/50 text-slate-300 hover:border-cyan-500 hover:bg-slate-800' : 'border-slate-200 bg-white text-slate-700 hover:border-cyan-500 hover:bg-slate-50'">
                {{ cat.icone }} {{ cat.nome }}
              </button>
            </div>

            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
              <div class="flex items-center gap-3 mb-6">
                <span class="text-2xl">{{ cat.icone }}</span>
                <h3 class="text-xl font-bold capitalize" :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ cat.nome }}</h3>
                <div class="flex-1 h-px" :class="isDark ? 'bg-slate-800' : 'bg-slate-200'"></div>
              </div>
              <ProductSlider :title="cat.nome" :icon="cat.icone"
                :params="{ loja_id: lojaId, categoria_id: cat.id }"
                :isDark="isDark" :show-title="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Full Catalog -->
        <section id="catalogo" class="py-16 border-t" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <div class="mb-8">
            <p class="text-sm font-medium mb-1" :style="{ color: 'var(--cor-primaria)' }">CATALOGO</p>
            <h2 class="text-3xl font-bold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Todos os Produtos</h2>
          </div>
          <ProductCatalog :loja-id="lojaId" :isDark="isDark" @product-click="selectedProduct = $event" />
        </section>

        <!-- Specifications / Info -->
        <section id="especificacoes" class="py-16 border-t" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- Delivery -->
            <div class="rounded-2xl p-6 border" :class="isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'">
              <h3 class="text-lg font-bold mb-4 flex items-center gap-2" :class="isDark ? 'text-slate-100' : 'text-slate-900'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :style="{ color: 'var(--cor-primaria)' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
                </svg>
                Opcoes de Envio
              </h3>
              <div v-if="opcoesEntrega.length === 0" class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">
                Sem opcoes configuradas.
              </div>
              <div v-else class="space-y-3">
                <div v-for="opcao in opcoesEntrega" :key="opcao.id"
                     class="flex items-center justify-between py-3 border-b last:border-0"
                     :class="isDark ? 'border-slate-800' : 'border-slate-100'">
                  <div>
                    <p class="font-medium" :class="isDark ? 'text-slate-200' : 'text-slate-700'">{{ opcao.nome }}</p>
                    <p v-if="opcao.tempo_estimado" class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">{{ opcao.tempo_estimado }}</p>
                  </div>
                  <span class="font-bold" :style="{ color: 'var(--cor-primaria)' }">
                    {{ opcao.preco == 0 ? 'Gratis' : formatPrice(opcao.preco) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Payment -->
            <div class="rounded-2xl p-6 border" :class="isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'">
              <h3 class="text-lg font-bold mb-4 flex items-center gap-2" :class="isDark ? 'text-slate-100' : 'text-slate-900'">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :style="{ color: 'var(--cor-primaria)' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                Metodos de Pagamento
              </h3>
              <div class="flex flex-wrap gap-2">
                <span v-for="m in metodosPagamento" :key="m.id"
                      class="px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2"
                      :class="isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-700'">
                  {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- Reviews -->
        <section id="avaliacoes" class="py-16 border-t" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <div class="mb-8">
            <p class="text-sm font-medium mb-1" :style="{ color: 'var(--cor-primaria)' }">FEEDBACK</p>
            <h2 class="text-3xl font-bold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Avaliacoes de Clientes</h2>
          </div>
          <AvaliacaoLoja :loja-id="lojaId" :isDark="isDark" @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer -->
        <footer class="py-12 border-t" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <div class="flex flex-col md:flex-row items-center justify-between gap-6">
            <div class="flex items-center gap-4">
              <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-12 h-12 rounded-xl object-cover" />
              <div>
                <p class="font-bold text-lg" :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ loja.nome }}</p>
                <p class="text-sm" :class="isDark ? 'text-slate-500' : 'text-slate-500'">{{ loja.categoria }}</p>
              </div>
            </div>
            <div class="flex gap-6 text-sm" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="hover:underline">Devolucoes</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="hover:underline">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="hover:underline">Privacidade</button>
            </div>
          </div>
          <p class="text-center text-xs mt-8" :class="isDark ? 'text-slate-600' : 'text-slate-400'">
            {{ new Date().getFullYear() }} {{ loja.nome }}. Tecnologia ao seu alcance.
          </p>
        </footer>
      </main>

      <!-- Modal politicas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="rounded-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-slate-900 border border-slate-800' : 'bg-white'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0"
               :class="isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-100'">
            <h3 class="font-bold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">
              {{ modalPolitica === 'devolucao' ? 'Politica de Devolucoes' : modalPolitica === 'termos' ? 'Termos de Servico' : 'Politica de Privacidade' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-8 h-8 rounded-lg flex items-center justify-center transition"
              :class="isDark ? 'bg-slate-800 hover:bg-slate-700' : 'bg-slate-100 hover:bg-slate-200'">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="isDark ? 'text-slate-400' : 'text-slate-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap"
               :class="isDark ? 'text-slate-300' : 'text-slate-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center">
      <p class="text-2xl font-bold mb-4" :class="isDark ? 'text-slate-400' : 'text-slate-600'">Loja nao encontrada</p>
      <button @click="$router.back()" class="text-sm hover:underline" :style="{ color: 'var(--cor-primaria)' }">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import ProductSlider from '@/components/sliders/ProductSlider.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateTechStore',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  props: { tema: { type: Object, default: () => ({}) } },

  setup(props) {
    const isDark = ref(props.tema?.darkMode !== false)
    const scrolled = ref(false)
    const lojaData = useLojaData()
    
    const cssVars = computed(() => ({
      '--cor-primaria': props.tema?.corPrimaria || '#06b6d4',
      '--cor-secundaria': props.tema?.corSecundaria || '#0f172a',
    }))
    
    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark() { isDark.value = !isDark.value }
    function onScroll() { scrolled.value = window.scrollY > 80 }
    
    onMounted(() => window.addEventListener('scroll', onScroll))
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return { isDark, scrolled, cssVars, user, toggleDark, ...lojaData }
  }
}
</script>
