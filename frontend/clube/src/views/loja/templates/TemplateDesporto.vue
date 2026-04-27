<!-- TemplateDesporto.vue — Dinâmico, diagonal, alta energia. Desporto e fitness. -->
<template>
  <div class="min-h-screen transition-colors duration-300 overflow-x-hidden"
       :class="isDark ? 'bg-[#0a0a0a] text-white' : 'bg-[#f5f5f5] text-zinc-900'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center font-mono"
         :class="isDark ? 'bg-[#0a0a0a]' : 'bg-[#f5f5f5]'">
      <div class="text-center space-y-3">
        <div class="relative w-10 h-10 mx-auto">
          <div class="absolute inset-0 rotate-45 animate-spin" :style="{ border: '2px solid var(--cor-primaria)', borderTopColor: 'transparent' }"></div>
        </div>
        <p class="text-xs tracking-[0.3em] uppercase" style="color:var(--cor-primaria)">Loading…</p>
      </div>
    </div>

    <template v-else-if="loja">

      <!-- ── HERO — diagonal split, alta energia ── -->
      <section class="relative min-h-screen overflow-hidden flex flex-col">

        <!-- Background imagem -->
        <div class="absolute inset-0">
          <img :src="loja.banner_url || `${backendUrl}/media/lojas/default_banner.jpg`"
               :alt="loja.nome"
               class="w-full h-full object-cover"
               :class="isDark ? 'opacity-30' : 'opacity-25'" />
          <div class="absolute inset-0"
               :class="isDark ? 'bg-[#0a0a0a]' : 'bg-[#f5f5f5]'"
               style="opacity:0.5"></div>
        </div>

        <!-- Forma diagonal direita (cor primária) -->
        <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div class="absolute top-0 right-0 h-full w-1/2"
               :style="{ background: 'var(--cor-primaria)', clipPath: 'polygon(30% 0, 100% 0, 100% 100%, 0% 100%)', opacity: isDark ? '0.9' : '0.85' }"></div>
          <!-- Linha diagonal decorativa -->
          <div class="absolute top-0 bottom-0 pointer-events-none"
               :style="{ left: 'calc(50% - 60px)', width: '2px', background: 'var(--cor-primaria)', transform: 'skewX(-8deg)', opacity: '0.3' }"></div>
        </div>

        <!-- Nav -->
        <div class="relative flex items-center justify-between px-6 py-5 z-10">
          <div class="flex items-center gap-3">
            <button @click="$router.back()"
              class="flex items-center gap-2 px-4 py-2 rounded border text-xs font-bold tracking-wider transition"
              :class="isDark ? 'border-white/20 text-white/60 hover:border-white/50 hover:text-white' : 'border-zinc-300 text-zinc-500 hover:border-zinc-500 hover:text-zinc-800'">
              ← BACK
            </button>
            <button @click="toggleDark"
              class="w-9 h-9 flex items-center justify-center rounded border transition text-xs font-bold"
              :class="isDark ? 'border-white/20 text-white/60 hover:border-white/40 hover:bg-white/5' : 'border-zinc-300 text-zinc-500 hover:border-zinc-500'">
              {{ isDark ? '☀' : '🌙' }}
            </button>
          </div>
        </div>

        <!-- Hero content -->
        <div class="relative flex-1 flex items-center z-10 px-6 md:px-12 pb-16">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center w-full max-w-7xl mx-auto">

            <!-- Texto esquerda -->
            <div>
              <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded mb-6 text-white text-xs font-black uppercase tracking-wider"
                   :style="{ background: 'var(--cor-primaria)' }">
                <div class="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                {{ loja.categoria }}
              </div>

              <h1 class="font-black uppercase leading-[0.88] tracking-tight mb-6"
                  style="font-size:clamp(3rem,8vw,7rem)">
                <span :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.nome.split(' ')[0] }}</span>
                <br>
                <span v-if="loja.nome.split(' ').length > 1"
                      :style="{ color: 'transparent', WebkitTextStroke: isDark ? '2px white' : '2px #1a1a1a' }">
                  {{ loja.nome.split(' ').slice(1).join(' ') }}
                </span>
              </h1>

              <p v-if="loja.descricao" class="text-base leading-relaxed mb-8 max-w-md"
                 :class="isDark ? 'text-white/50' : 'text-zinc-600'">
                {{ loja.descricao.substring(0, 160) }}{{ loja.descricao.length > 160 ? '…' : '' }}
              </p>

              <!-- Stats em linha -->
              <div class="flex items-center gap-8 mb-8">
                <div v-if="loja.rating_medio">
                  <p class="text-4xl font-black" style="color:var(--cor-primaria)">{{ loja.rating_medio }}</p>
                  <p class="text-[9px] uppercase tracking-widest mt-1" :class="isDark ? 'text-white/30' : 'text-zinc-400'">Rating</p>
                </div>
                <div v-if="loja.total_avaliacoes">
                  <p class="text-4xl font-black" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.total_avaliacoes }}</p>
                  <p class="text-[9px] uppercase tracking-widest mt-1" :class="isDark ? 'text-white/30' : 'text-zinc-400'">Reviews</p>
                </div>
                <div v-if="loja.entrega_ativa">
                  <p class="text-4xl font-black text-green-400">✓</p>
                  <p class="text-[9px] uppercase tracking-widest mt-1" :class="isDark ? 'text-white/30' : 'text-zinc-400'">Entrega</p>
                </div>
              </div>

              <div class="flex gap-3 flex-wrap">
                <button @click="scrollToId('produtos')"
                  class="px-8 py-4 font-black uppercase tracking-wider text-sm text-white transition-all hover:scale-105 hover:-rotate-1 rounded"
                  :style="{ background: 'var(--cor-primaria)', boxShadow: '4px 4px 0px rgba(0,0,0,0.3)' }">
                  Shop Now
                </button>
                <button @click="scrollToId('catalogo')"
                  class="px-8 py-4 font-black uppercase tracking-wider text-sm transition-all hover:scale-105 hover:rotate-1 rounded"
                  :class="isDark ? 'border-2 border-white text-white hover:bg-white hover:text-zinc-900' : 'border-2 border-zinc-900 text-zinc-900 hover:bg-zinc-900 hover:text-white'">
                  Catálogo
                </button>
              </div>
            </div>

            <!-- Logo / imagem direita sobre o fundo cor -->
            <div class="hidden lg:flex justify-end items-center pr-6">
              <div class="relative">
                <!-- Anel decorativo -->
                <div class="absolute -inset-4 rounded-2xl border-2 border-white/20 rotate-3"></div>
                <div class="relative w-72 h-72 rounded-2xl overflow-hidden -rotate-2 hover:rotate-0 transition-transform duration-500"
                     :class="isDark ? 'bg-zinc-800' : 'bg-white shadow-2xl'">
                  <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full flex items-center justify-center" :style="{ background: 'var(--cor-primaria)' }">
                    <span class="text-7xl font-black text-white">{{ loja.nome.charAt(0) }}</span>
                  </div>
                </div>
                <!-- Badge localização -->
                <div v-if="loja.localizacao"
                     class="absolute -bottom-4 -left-4 px-4 py-2 rounded text-xs font-black uppercase tracking-wider text-white"
                     :style="{ background: isDark ? '#18181b' : '#1a1a1a', border: '2px solid var(--cor-primaria)' }">
                  📍 {{ loja.localizacao }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Scroll indicator -->
        <div class="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 z-10">
          <div class="w-5 h-8 rounded-full border-2 flex items-start justify-center p-1"
               :class="isDark ? 'border-white/20' : 'border-zinc-300'">
            <div class="w-1 h-2 rounded-full animate-bounce" :style="{ background: 'var(--cor-primaria)' }"></div>
          </div>
        </div>
      </section>

      <!-- ── MARQUEE strip ── -->
      <div class="overflow-hidden py-3" :style="{ background: 'var(--cor-primaria)' }">
        <div class="flex items-center gap-8 animate-marquee whitespace-nowrap">
          <span v-for="n in 8" :key="n" class="text-white font-black uppercase tracking-wider text-sm flex items-center gap-8 flex-shrink-0">
            <span>Performance</span>
            <span class="w-2 h-2 bg-white rounded-full inline-block"></span>
            <span>{{ loja.nome }}</span>
            <span class="w-2 h-2 bg-white rounded-full inline-block"></span>
            <span>Shop Now</span>
            <span class="w-2 h-2 bg-white rounded-full inline-block"></span>
          </span>
        </div>
      </div>

      <!-- ── MAIN ── -->
      <main class="max-w-7xl mx-auto px-6 pb-20">

        <!-- Info entrega + pagamento -->
        <section class="py-14 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="rounded-2xl p-6 border-2"
               :class="isDark ? 'bg-[#111] border-zinc-800' : 'bg-white border-zinc-200'">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center text-xl text-white mb-4" :style="{ background: 'var(--cor-primaria)' }">🚚</div>
            <h3 class="text-lg font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">Envio</h3>
            <div v-if="!opcoesEntrega.length" class="text-sm" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">Sem opções configuradas.</div>
            <div v-else class="space-y-2">
              <div v-for="opcao in opcoesEntrega" :key="opcao.id" class="flex justify-between items-center py-2 border-b last:border-0"
                   :class="isDark ? 'border-zinc-800' : 'border-zinc-100'">
                <div>
                  <p class="text-sm font-bold" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ opcao.nome }}</p>
                  <p v-if="opcao.tempo_estimado" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">{{ opcao.tempo_estimado }}</p>
                </div>
                <span class="font-black text-sm" style="color:var(--cor-primaria)">{{ opcao.preco == 0 ? 'FREE' : formatPrice(opcao.preco) }}</span>
              </div>
            </div>
          </div>
          <div class="rounded-2xl p-6 border-2"
               :class="isDark ? 'bg-[#111] border-zinc-800' : 'bg-white border-zinc-200'">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center text-xl text-white mb-4" :style="{ background: 'var(--cor-primaria)' }">💳</div>
            <h3 class="text-lg font-black uppercase mb-4" :class="isDark ? 'text-white' : 'text-zinc-900'">Pagamento</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="m in metodosPagamento" :key="m.id"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold uppercase"
                    :class="isDark ? 'bg-zinc-800 text-white' : 'bg-zinc-100 text-zinc-800'">
                {{ metodoPagamentoIcon(m.tipo) }} {{ m.tipo }}
              </span>
            </div>
          </div>
        </section>

        <!-- Destaques -->
        <section id="produtos" class="pb-16">
          <div class="flex items-end justify-between mb-10">
            <div>
              <p class="text-xs font-black uppercase tracking-widest mb-2" style="color:var(--cor-primaria)">Hot Items</p>
              <h2 class="text-5xl font-black uppercase tracking-tight" :class="isDark ? 'text-white' : 'text-zinc-900'">Destaques</h2>
            </div>
            <span class="hidden md:block text-8xl font-black" :style="{ color: 'var(--cor-primaria)', opacity: '0.12' }">01</span>
          </div>
          <ProductSlider
            title="Destaques"
            :params="{ loja_id: lojaId, destaque: true }"
            :isDark="isDark"
            card-width="220px"
            image-height="200px"
            card-height="320px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:-translate-y-2 hover:shadow-2xl transition-all duration-300"
            :hover-border-class="isDark ? 'hover:border-orange-500/50' : 'hover:border-orange-400/60'"
            :price-class="'font-black text-lg'"
            badge-class="text-white font-black rounded"
            :style-badge="{ background: 'var(--cor-primaria)' }"
            badge-text="HOT"
            :show-store-name="false"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Por tipo -->
        <template v-if="tiposExistentes.length > 0">
          <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                   class="pb-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
            <div class="flex items-end justify-between my-10">
              <div class="flex items-center gap-5">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl text-white" :style="{ background: 'var(--cor-primaria)' }">{{ tipoIcon(tipo.nome) }}</div>
                <h2 class="text-4xl font-black uppercase tracking-tight" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ tipo.nome }}</h2>
              </div>
              <span class="hidden md:block text-7xl font-black opacity-10" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ String(idx + 2).padStart(2, '0') }}</span>
            </div>
            <ProductSlider
              :title="tipo.nome" :params="{ loja_id: lojaId, tipo: tipo.nome }" :isDark="isDark"
              card-width="200px" image-height="180px" card-height="290px"
              card-border-radius="rounded-2xl"
              hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
              :hover-border-class="isDark ? 'hover:border-orange-500/50' : 'hover:border-orange-400/50'"
              :show-store-name="false"
              @product-click="selectedProduct = $event" />
          </section>
        </template>

        <!-- Por categoria -->
        <template v-if="categoriasExistentes.length > 0">
          <section class="pb-16">
            <div class="flex items-end justify-between mb-10">
              <h2 class="text-4xl font-black uppercase tracking-tight" :class="isDark ? 'text-white' : 'text-zinc-900'">Categorias</h2>
            </div>
            <!-- Grid de categorias como nav buttons -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-12">
              <button v-for="cat in categoriasExistentes" :key="cat.id"
                @click="scrollToId('cat-' + cat.id)"
                class="p-5 rounded-xl font-black uppercase text-center transition-all hover:scale-105 border-2"
                :class="isDark ? 'bg-[#111] border-zinc-800 text-white hover:border-orange-500/50' : 'bg-white border-zinc-200 text-zinc-900 hover:border-orange-400/50'">
                <span class="text-3xl block mb-2">{{ cat.icone }}</span>
                <span class="text-xs tracking-wider">{{ cat.nome }}</span>
              </button>
            </div>
            <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-12">
              <div class="flex items-center gap-4 mb-6">
                <span class="text-2xl">{{ cat.icone }}</span>
                <h3 class="text-2xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ cat.nome }}</h3>
                <div class="flex-1 h-0.5" :style="{ background: 'var(--cor-primaria)', opacity: '0.3' }"></div>
              </div>
              <ProductSlider
                :title="cat.nome" :params="{ loja_id: lojaId, categoria_id: cat.id }" :isDark="isDark"
                card-width="200px" image-height="180px" card-height="290px"
                card-border-radius="rounded-2xl"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                :show-store-name="false"
                @product-click="selectedProduct = $event" />
            </div>
          </section>
        </template>

        <!-- Catálogo completo -->
        <section id="catalogo" class="pb-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-end justify-between my-10">
            <div>
              <p class="text-xs font-black uppercase tracking-widest mb-2" style="color:var(--cor-primaria)">Full Collection</p>
              <h2 class="text-5xl font-black uppercase tracking-tight" :class="isDark ? 'text-white' : 'text-zinc-900'">Catálogo</h2>
            </div>
          </div>
          <ProductCatalog
            :loja-id="lojaId" :isDark="isDark"
            grid-class="grid-cols-2 sm:grid-cols-3 xl:grid-cols-4"
            image-height="185px"
            card-border-radius="rounded-2xl"
            hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
            :hover-border-class="isDark ? 'hover:border-orange-500/50' : 'hover:border-orange-400/50'"
            tab-border-radius="rounded-xl"
            :active-tab-class="'text-white font-black uppercase tracking-wider text-xs shadow-lg'"
            :inactive-tab-dark-class="'bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-700 uppercase tracking-wider text-xs font-bold'"
            :inactive-tab-light-class="'bg-white text-zinc-500 hover:text-zinc-900 border border-zinc-200 uppercase tracking-wider text-xs font-bold'"
            input-border-radius="rounded-xl"
            filter-container-radius="rounded-2xl"
            :product-name-hover-class="'group-hover:opacity-70'"
            :price-class="'font-black'"
            @product-click="selectedProduct = $event" />
        </section>

        <!-- Avaliações -->
        <section id="avaliacoes" class="pb-16 border-t-4" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-end justify-between my-10">
            <div>
              <p class="text-xs font-black uppercase tracking-widest mb-2" style="color:var(--cor-primaria)">Community</p>
              <h2 class="text-5xl font-black uppercase tracking-tight" :class="isDark ? 'text-white' : 'text-zinc-900'">Reviews</h2>
            </div>
          </div>
          <AvaliacaoLoja
            :loja-id="lojaId" :isDark="isDark"
            summary-border-radius="rounded-2xl"
            form-border-radius="rounded-2xl"
            review-card-border-radius="rounded-2xl"
            button-border-radius="rounded-xl"
            textarea-border-radius="rounded-xl"
            :star-active-class="'text-orange-400'"
            :star-inactive-class="isDark ? 'text-zinc-700' : 'text-zinc-300'"
            :progress-bar-class="'bg-orange-400'"
            :submit-button-class="'text-white font-black uppercase tracking-wider text-xs'"
            :own-review-border-class="isDark ? 'bg-[#111] border border-orange-500/30' : 'bg-orange-50 border border-orange-200'"
            own-badge-class="bg-orange-500/20 text-orange-400 font-bold uppercase text-xs"
            link-class="text-orange-400 hover:text-orange-300 font-bold"
            @rating-updated="onRatingUpdated" />
        </section>

        <!-- Footer -->
        <footer class="border-t-4 py-14 text-center" :style="{ borderColor: 'var(--cor-primaria)' }">
          <div class="flex items-center justify-center gap-4 mb-6">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="w-14 h-14 rounded-xl object-cover" />
            <span class="text-3xl font-black uppercase" :class="isDark ? 'text-white' : 'text-zinc-900'">{{ loja.nome }}</span>
          </div>
          <div class="flex justify-center gap-8 text-xs font-black uppercase tracking-wider mb-6"
               :class="isDark ? 'text-zinc-500' : 'text-zinc-400'">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="hover:underline">Returns</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'" class="hover:underline">Terms</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="hover:underline">Privacy</button>
          </div>
          <p class="text-xs" :class="isDark ? 'text-zinc-700' : 'text-zinc-400'">© {{ new Date().getFullYear() }} {{ loja.nome }}. Keep Moving.</p>
        </footer>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" @click.self="modalPolitica = null">
        <div class="rounded-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl border-2"
             :class="isDark ? 'bg-[#111] border-zinc-800' : 'bg-white border-zinc-200'">
          <div class="flex items-center justify-between px-6 py-4 border-b-2 sticky top-0"
               :class="isDark ? 'bg-[#111] border-zinc-800' : 'bg-white border-zinc-200'">
            <h3 class="font-black uppercase tracking-wider text-sm" :class="isDark ? 'text-white' : 'text-zinc-900'">
              {{ modalPolitica === 'devolucao' ? 'Returns' : modalPolitica === 'termos' ? 'Terms' : 'Privacy' }}
            </h3>
            <button @click="modalPolitica = null"
              class="w-9 h-9 rounded-xl flex items-center justify-center font-black text-white"
              :style="{ background: 'var(--cor-primaria)' }">×</button>
          </div>
          <div class="p-6 text-sm leading-relaxed whitespace-pre-wrap" :class="isDark ? 'text-zinc-300' : 'text-zinc-600'">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao : modalPolitica === 'termos' ? loja.termos_servico : loja.politica_privacidade }}
          </div>
        </div>
      </div>

    </template>

    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-[#0a0a0a]' : 'bg-[#f5f5f5]'">
      <p class="text-4xl font-black mb-4" style="color:var(--cor-primaria)">404</p>
      <p class="text-lg font-bold uppercase mb-6" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">Loja não encontrada</p>
      <button @click="$router.back()" class="px-8 py-3 rounded-xl font-black uppercase text-white" :style="{ background: 'var(--cor-primaria)' }">Voltar</button>
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
  name: 'TemplateDesporto',
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#f97316',
      '--cor-secundaria': props.tema?.corSecundaria || '#0a0a0a',
    }))

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }

    return { isDark, cssVars, user, toggleDark, ...lojaData }
  },
}
</script>

<style scoped>
@keyframes marquee {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee { animation: marquee 20s linear infinite; }
</style>
