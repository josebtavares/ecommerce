<!-- TemplateRestauranteModerno.vue — REDESENHADO
     Direção: fine-dining editorial. Serif + sans, paleta quente (charcoal + bone +
     cobre), hero split com "carta do chef", barra de info ambiente (horário/local/
     telefone), navegação por secções de menu (entradas/principais/sobremesas/...),
     cards editoriais com preço em "dot leader", reservas inline, reviews curadas.

     IMPORTANTE — gutter direito reservado ao chrome (NÃO MEXER):
       UserProfile  → top-2 md:top-6           right-[2.5vw]
       MultiCart    → top-2 md:top-[1.35rem]   right-[6rem] md:right-[calc(2.5vw+5.5rem)]
       NotificacaoSino → dentro do UserProfile
     Top bar e sticky nav só ocupam o lado esquerdo / centro com padding-right
     responsivo de ~18rem (desktop) / 8.5rem (mobile).
-->
<template>
  <div class="trm min-h-screen overflow-x-hidden transition-colors duration-500"
       :class="isDark ? 'trm--dark' : 'trm--light'"
       :style="cssVars">

    <ProductInfoCard :produto="selectedProduct" :loja="loja" :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)" />
    <MultiCart ref="cart" :isDark="isDark" />
    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <!-- Loader -->
    <div v-if="loading" class="fixed inset-0 z-50 flex flex-col items-center justify-center gap-6"
         :class="isDark ? 'bg-[var(--trm-bg-d)]' : 'bg-[var(--trm-bg-l)]'">
      <div class="trm-loader"></div>
      <p class="text-[10px] tracking-[0.5em] uppercase opacity-50">Reservando a mesa</p>
    </div>

    <template v-else-if="loja">

      <!-- ───── TOP BAR (esquerda apenas) ───── -->
      <header class="relative z-30 flex items-center justify-between px-6 md:px-10 pt-5 md:pt-7"
              style="padding-right: clamp(8.5rem, calc(2.5vw + 11rem), 19rem)">
        <div class="flex items-center gap-3">
          <button @click="$router.back()" class="trm-iconbtn" aria-label="Voltar">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"
                 stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <button @click="toggleDark" class="trm-iconbtn" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
            <span class="text-[12px] leading-none">{{ isDark ? '☀' : '☾' }}</span>
          </button>
        </div>

        <!-- Brand wordmark central (esquerda+centro) -->
        <div class="hidden md:flex items-center gap-3 select-none">
          <span class="trm-rule"></span>
          <span class="trm-monogram" :style="{ borderColor: 'var(--cor-primaria)', color: 'var(--cor-primaria)' }">
            {{ monograma }}
          </span>
          <span class="font-serif italic text-sm opacity-60">est. {{ anoFundacao }}</span>
        </div>
      </header>

      <!-- ───── HERO ───── -->
      <section class="relative px-6 md:px-10 pt-10 md:pt-14 pb-16 md:pb-24">
        <div class="grid grid-cols-12 gap-6 md:gap-12 items-center max-w-[1400px] mx-auto"
             style="min-height: clamp(560px, 80vh, 100vh)">

          <!-- Coluna texto editorial -->
          <div class="col-span-12 lg:col-span-6 order-2 lg:order-1">
            <div class="flex items-center gap-4 mb-7">
              <span class="trm-rule" style="width: 48px"></span>
              <span class="text-[10px] font-medium uppercase tracking-[0.45em] opacity-70">
                {{ loja.categoria || 'Restaurante' }} · {{ loja.localizacao ? loja.localizacao.split(',')[0] : 'Lisboa' }}
              </span>
            </div>

            <h1 class="trm-hero-title font-serif">
              <span v-for="(linha, i) in tituloLinhas" :key="i" class="block"
                    :class="i % 2 === 1 ? 'italic font-light' : 'font-normal'"
                    :style="i === 1 ? { color: 'var(--cor-primaria)' } : {}">
                {{ linha }}
              </span>
            </h1>

            <p v-if="loja.descricao" class="mt-8 max-w-lg text-base md:text-[17px] leading-[1.7] opacity-75">
              {{ loja.descricao.substring(0, 200) }}{{ loja.descricao.length > 200 ? '…' : '' }}
            </p>

            <!-- Assinatura "do chef" -->
            <div class="mt-8 flex items-center gap-3">
              <span class="trm-rule" style="width: 28px"></span>
              <span class="font-serif italic text-sm opacity-60">— uma palavra da casa</span>
            </div>

            <!-- CTAs -->
            <div class="mt-10 flex flex-wrap items-center gap-4">
              <button @click="scrollToId('menu')" class="trm-btn trm-btn--solid">
                <span>Ver Menu</span>
                <span class="trm-btn__arr">→</span>
              </button>
              <button @click="scrollToId('reservar')" class="trm-btn trm-btn--ghost">
                <span>Reservar Mesa</span>
              </button>
            </div>

            <!-- KPIs serenos -->
            <div class="mt-12 grid grid-cols-3 gap-6 max-w-md">
              <div class="trm-kpi">
                <p class="trm-kpi__num font-serif">{{ loja.rating_medio ? Number(loja.rating_medio).toFixed(1) : '—' }}</p>
                <p class="trm-kpi__lbl">Rating</p>
              </div>
              <div class="trm-kpi">
                <p class="trm-kpi__num font-serif">{{ loja.total_avaliacoes || 0 }}</p>
                <p class="trm-kpi__lbl">Reviews</p>
              </div>
              <div class="trm-kpi">
                <p class="trm-kpi__num font-serif">{{ anoFundacao }}</p>
                <p class="trm-kpi__lbl">Desde</p>
              </div>
            </div>
          </div>

          <!-- Coluna imagem ambiente -->
          <div class="col-span-12 lg:col-span-6 order-1 lg:order-2 relative">
            <div class="relative mx-auto w-full max-w-[560px]">
              <!-- frame principal -->
              <div class="trm-hero-frame">
                <video v-if="isVideo(loja.banner_url)"
                       :src="loja.banner_url" autoplay muted loop playsinline
                       class="w-full h-full object-cover"></video>
                <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome"
                     class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center"
                     :style="{ background: 'var(--cor-primaria)' }">
                  <span class="text-[140px] font-serif italic text-white/90 leading-none">{{ monograma }}</span>
                </div>

                <!-- vinheta sobreposta -->
                <div class="absolute inset-0 trm-vignette"></div>

                <!-- overlay info: hours -->
                <div class="absolute left-5 bottom-5 right-5 flex items-end justify-between gap-3">
                  <div>
                    <p class="text-[10px] tracking-[0.35em] uppercase text-white/60">Aberto agora</p>
                    <p class="font-serif text-white text-2xl mt-1">19:00 — 23:30</p>
                  </div>
                  <span class="trm-dot-pulse"></span>
                </div>
              </div>

              <!-- card flutuante: rating com talheres -->
              <div class="trm-floatcard">
                <div class="flex items-center gap-3">
                  <span class="font-serif text-3xl leading-none" style="color:var(--cor-primaria)">★</span>
                  <div>
                    <p class="font-serif text-2xl leading-none">
                      {{ loja.rating_medio ? Number(loja.rating_medio).toFixed(1) : '4.7' }}
                    </p>
                    <p class="text-[9px] tracking-[0.3em] uppercase opacity-60 mt-1">Excelente</p>
                  </div>
                </div>
                <div class="trm-rule mt-3 mb-3" style="width: 100%"></div>
                <p class="text-[10px] tracking-[0.25em] uppercase opacity-70">
                  Top 1% · {{ new Date().getFullYear() }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ───── INFO BAR (horário · morada · telefone) ───── -->
      <section class="trm-infobar">
        <div class="max-w-[1400px] mx-auto grid grid-cols-2 md:grid-cols-4 divide-x"
             :class="isDark ? 'divide-white/10' : 'divide-black/10'">
          <div class="trm-infobar__item">
            <span class="trm-infobar__lbl">Horário</span>
            <span class="trm-infobar__val font-serif">Ter — Dom · 19:00</span>
          </div>
          <div class="trm-infobar__item">
            <span class="trm-infobar__lbl">Morada</span>
            <span class="trm-infobar__val font-serif">
              {{ loja.localizacao || 'Rua das Flores, 12' }}
            </span>
          </div>
          <div class="trm-infobar__item">
            <span class="trm-infobar__lbl">Reservas</span>
            <span class="trm-infobar__val font-serif">+351 21 000 0000</span>
          </div>
          <div class="trm-infobar__item">
            <span class="trm-infobar__lbl">Dress code</span>
            <span class="trm-infobar__val font-serif italic">Smart casual</span>
          </div>
        </div>
      </section>

      <!-- ───── SECTION NAV (sticky) ───── -->
      <nav class="trm-sectionnav">
        <div class="trm-sectionnav__inner">
          <a v-for="s in secoes" :key="s.id" :href="`#${s.id}`"
             @click.prevent="scrollToId(s.id)" class="trm-sectionnav__link">
            <span class="trm-sectionnav__num font-serif italic">{{ s.num }}</span>
            <span>{{ s.label }}</span>
          </a>
        </div>
      </nav>

      <!-- ───── MAIN ───── -->
      <main class="px-6 md:px-10 pb-20">
        <div class="max-w-[1400px] mx-auto">

          <!-- PRATOS DE ASSINATURA -->
          <section id="assinatura" class="pt-20 md:pt-28">
            <div class="trm-secthead">
              <div>
                <span class="trm-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Carte du Chef</span>
                <h2 class="trm-secttitle font-serif">Pratos de Assinatura</h2>
                <p class="trm-sectdesc">Selecção do chef. Ingredientes da estação, acabamentos à mesa.</p>
              </div>
              <span class="trm-sectnum font-serif italic">i.</span>
            </div>
            <ProductSlider
              title="Assinatura"
              :params="{ loja_id: lojaId, destaque: true }"
              :isDark="isDark"
              card-width="280px"
              card-height="420px"
              image-height="280px"
              card-border-radius="rounded-[2px]"
              :card-class="'trm-card'"
              hover-effect="transition-all duration-500"
              :hover-border-class="'trm-card-hover'"
              :title-class="'!font-serif !text-2xl !italic !font-normal'"
              :product-name-class="'trm-prodname'"
              :price-class="'trm-price'"
              :badge-class="'trm-badge'"
              badge-text="CHEF"
              :show-store-name="false"
              @product-click="selectedProduct = $event" />
          </section>

          <!-- POR TIPO (entradas, pratos, etc.) -->
          <template v-if="tiposExistentes.length > 0">
            <section v-for="(tipo, idx) in tiposExistentes" :key="tipo.id" :id="'tipo-' + tipo.id"
                     class="pt-20 md:pt-28 trm-divider">
              <div class="trm-secthead">
                <div>
                  <span class="trm-eyebrow opacity-60">Curso · {{ romano(idx + 1) }}</span>
                  <h2 class="trm-secttitle font-serif trm-secttitle--md">
                    <span class="opacity-50 mr-2">{{ tipoIcon(tipo.nome) }}</span>{{ tipo.nome }}
                  </h2>
                </div>
                <span class="trm-sectnum font-serif italic">{{ romanoMin(idx + 2) }}</span>
              </div>
              <ProductSlider
                :title="tipo.nome"
                :params="{ loja_id: lojaId, tipo: tipo.nome }"
                :isDark="isDark"
                card-width="240px"
                card-height="380px"
                image-height="240px"
                card-border-radius="rounded-[2px]"
                :card-class="'trm-card'"
                hover-effect="transition-all duration-500"
                :hover-border-class="'trm-card-hover'"
                :product-name-class="'trm-prodname'"
                :price-class="'trm-price'"
                :show-store-name="false"
                @product-click="selectedProduct = $event" />
            </section>
          </template>

          <!-- CATEGORIAS — chips elegantes -->
          <template v-if="categoriasExistentes.length > 0">
            <section id="categorias" class="pt-20 md:pt-28 trm-divider">
              <div class="trm-secthead">
                <div>
                  <span class="trm-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Toda a Carta</span>
                  <h2 class="trm-secttitle font-serif">Por Categoria</h2>
                </div>
                <span class="trm-sectnum font-serif italic">{{ romanoMin(tiposExistentes.length + 2) }}</span>
              </div>

              <div class="flex flex-wrap gap-2 mb-12">
                <button v-for="cat in categoriasExistentes" :key="cat.id"
                        @click="scrollToId('cat-' + cat.id)" class="trm-chip">
                  <span class="opacity-70">{{ cat.icone }}</span>
                  <span>{{ cat.nome }}</span>
                </button>
              </div>

              <div v-for="cat in categoriasExistentes" :key="cat.id" :id="'cat-' + cat.id" class="mb-16">
                <div class="flex items-baseline gap-4 mb-6">
                  <h3 class="font-serif text-3xl md:text-4xl">{{ cat.nome }}</h3>
                  <span class="trm-rule flex-1"></span>
                  <span class="text-[10px] tracking-[0.3em] uppercase opacity-50">{{ cat.icone }}</span>
                </div>
                <ProductSlider
                  :title="cat.nome"
                  :params="{ loja_id: lojaId, categoria_id: cat.id }"
                  :isDark="isDark"
                  card-width="220px"
                  card-height="360px"
                  image-height="220px"
                  card-border-radius="rounded-[2px]"
                  :card-class="'trm-card'"
                  hover-effect="transition-all duration-500"
                  :hover-border-class="'trm-card-hover'"
                  :product-name-class="'trm-prodname'"
                  :price-class="'trm-price'"
                  :show-store-name="false"
                  @product-click="selectedProduct = $event" />
              </div>
            </section>
          </template>

          <!-- MENU COMPLETO (catálogo) -->
          <section id="menu" class="pt-20 md:pt-28 trm-divider">
            <div class="trm-secthead">
              <div>
                <span class="trm-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Menu Complet</span>
                <h2 class="trm-secttitle font-serif">A Carta</h2>
                <p class="trm-sectdesc">Pesquise, filtre e descubra.</p>
              </div>
              <span class="trm-sectnum font-serif italic">{{ romanoMin(tiposExistentes.length + 3) }}</span>
            </div>
            <ProductCatalog
              :loja-id="lojaId" :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="200px"
              card-border-radius="rounded-[2px]"
              :card-class="'trm-card'"
              hover-effect="transition-all duration-500"
              :hover-border-class="'trm-card-hover'"
              tab-border-radius="rounded-full"
              :active-tab-class="'trm-tab trm-tab--active'"
              :inactive-tab-dark-class="'trm-tab'"
              :inactive-tab-light-class="'trm-tab'"
              :active-sub-tab-class="'trm-subtab trm-subtab--active'"
              :inactive-sub-tab-dark-class="'trm-subtab'"
              :inactive-sub-tab-light-class="'trm-subtab'"
              input-border-radius="rounded-[2px]"
              filter-container-radius="rounded-[2px]"
              :filter-container-class="'trm-filterbox'"
              :product-name-hover-class="'group-hover:opacity-70'"
              :product-name-class="'trm-prodname'"
              :price-class="'trm-price'"
              :badge-class="'trm-badge'"
              badge-text="NOVO"
              :indicator-active-class="'trm-indicator'"
              :stock-active-class="'trm-stock-on'"
              :clear-filter-class="'trm-btn-tiny trm-btn-tiny--accent'"
              @product-click="selectedProduct = $event" />
          </section>



          <!-- AVALIAÇÕES -->
          <section id="avaliacoes" class="pt-20 md:pt-28 trm-divider">
            <div class="trm-secthead">
              <div>
                <span class="trm-eyebrow" :style="{ color: 'var(--cor-primaria)' }">Mesa Aberta</span>
                <h2 class="trm-secttitle font-serif">A palavra dos clientes</h2>
              </div>
              <span class="trm-sectnum font-serif italic">{{ romanoMin(tiposExistentes.length + 4) }}</span>
            </div>
            <AvaliacaoLoja
              :loja-id="lojaId" :isDark="isDark"
              summary-border-radius="rounded-[2px]"
              form-border-radius="rounded-[2px]"
              review-card-border-radius="rounded-[2px]"
              button-border-radius="rounded-[2px]"
              textarea-border-radius="rounded-[2px]"
              :star-active-class="'trm-star-on'"
              :star-inactive-class="isDark ? 'text-white/15' : 'text-black/15'"
              :submit-button-class="'trm-btn trm-btn--solid'"
              :own-review-border-class="'trm-review-own'"
              own-badge-class="trm-ownbadge"
              link-class="trm-link"
              :progress-bar-class="'trm-progress'"
              @rating-updated="onRatingUpdated" />
          </section>

          <!-- FOOTER -->
          <footer class="pt-24 md:pt-32 pb-12">
            <div class="text-center mb-12">
              <span class="trm-monogram trm-monogram--big font-serif"
                    :style="{ borderColor: 'var(--cor-primaria)', color: 'var(--cor-primaria)' }">
                {{ monograma }}
              </span>
              <h2 class="font-serif text-4xl md:text-6xl mt-6">{{ loja.nome }}</h2>
              <p class="font-serif italic opacity-60 mt-3">une expérience · since {{ anoFundacao }}</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 pt-10 border-t"
                 :class="isDark ? 'border-white/10' : 'border-black/10'">
              <div>
                <p class="trm-eyebrow opacity-60 mb-3">Visite-nos</p>
                <p class="font-serif text-lg">{{ loja.localizacao || 'Rua das Flores, 12 · Lisboa' }}</p>
                <p class="text-sm opacity-60 mt-1">Ter — Dom · 19:00 — 23:30</p>
              </div>
              <div>
                <p class="trm-eyebrow opacity-60 mb-3">Contactos</p>
                <p class="font-serif text-lg">+351 21 000 0000</p>
                <p class="text-sm opacity-60 mt-1">reservas&#64;{{ slugDominio }}.pt</p>
              </div>
              <div>
                <p class="trm-eyebrow opacity-60 mb-3">Políticas</p>
                <div class="flex flex-col gap-1.5 text-sm">
                  <button v-if="loja.termos_servico"     @click="modalPolitica = 'termos'"     class="trm-foot-link text-left">Termos de Serviço</button>
                  <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'" class="trm-foot-link text-left">Política de Privacidade</button>
                  <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'" class="trm-foot-link text-left">Devoluções</button>
                </div>
              </div>
            </div>

            <p class="text-center text-[10px] tracking-[0.45em] uppercase opacity-40 mt-12">
              © {{ new Date().getFullYear() }} · {{ loja.nome }} · Todos os direitos reservados
            </p>
          </footer>
        </div>
      </main>

      <!-- Modal políticas -->
      <div v-if="modalPolitica"
           class="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-0 md:p-4 bg-black/70 backdrop-blur-sm"
           @click.self="modalPolitica = null">
        <div class="w-full md:max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
             :class="isDark ? 'bg-[var(--trm-bg-d)] text-zinc-100' : 'bg-[var(--trm-bg-l)] text-zinc-900'">
          <div class="flex items-center justify-between px-6 py-4 border-b sticky top-0 backdrop-blur-md"
               :class="isDark ? 'bg-[var(--trm-bg-d)]/95 border-white/10' : 'bg-[var(--trm-bg-l)]/95 border-black/10'">
            <h3 class="font-serif text-xl">
              {{ modalPolitica === 'devolucao' ? 'Devoluções' : modalPolitica === 'termos' ? 'Termos' : 'Privacidade' }}
            </h3>
            <button @click="modalPolitica = null" class="trm-iconbtn">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"
                   stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="p-6 text-sm leading-[1.7] whitespace-pre-wrap opacity-80">
            {{ modalPolitica === 'devolucao' ? loja.politica_devolucao
             : modalPolitica === 'termos'    ? loja.termos_servico
             : loja.politica_privacidade }}
          </div>
        </div>
      </div>
    </template>

    <!-- 404 -->
    <div v-else-if="!loading" class="min-h-screen flex flex-col items-center justify-center"
         :class="isDark ? 'bg-[var(--trm-bg-d)] text-zinc-100' : 'bg-[var(--trm-bg-l)] text-zinc-900'">
      <p class="font-serif italic text-3xl mb-3 opacity-70">Mesa não encontrada</p>
      <button @click="$router.back()" class="trm-btn trm-btn--solid mt-4">Voltar</button>
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
  components: { ProductInfoCard, MultiCart, ProductSlider, Profile, ProductCatalog, AvaliacaoLoja },
  emits: ['toggle-dark'],
  props: { tema: { type: Object, default: () => ({}) } },

  setup (props, { emit }) {
    const isDark   = ref(props.tema?.darkMode !== false)
    const lojaData = useLojaData()

    const cssVars = computed(() => {
      const primaryColor = props.tema?.corPrimaria || '#b07b3f'
      const secondaryColor = props.tema?.corSecundaria || '#0f0d0a'
      return {
        '--cor-primaria':   primaryColor,
        '--cor-secundaria': secondaryColor,
        '--trm-bg-d':       isDark.value ? '#0f0d0a' : '#f7f3ec',
        '--trm-bg-l':       isDark.value ? '#0f0d0a' : '#f7f3ec',
      }
    })

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

    function toggleDark () { isDark.value = !isDark.value; emit('toggle-dark', isDark.value) }
    function isVideo (url) { return /\.(mp4|webm|mov|mkv)$/i.test(url || '') }

    function romano (n) {
      const map = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
      return map[n - 1] || String(n)
    }
    function romanoMin (n) {
      return (romano(n) || '').toLowerCase() + '.'
    }

    const secoes = [
      { id: 'assinatura', label: 'Assinatura', num: 'i.' },
      { id: 'categorias', label: 'Categorias', num: 'ii.' },
      { id: 'menu',       label: 'A Carta',    num: 'iii.' },
      { id: 'reservar',   label: 'Reservar',   num: 'iv.' },
      { id: 'avaliacoes', label: 'Reviews',    num: 'v.' },
    ]

    return { isDark, cssVars, user, toggleDark, isVideo, romano, romanoMin, secoes, ...lojaData }
  },

  computed: {
    monograma () {
      const partes = (this.loja?.nome || '').trim().split(/\s+/)
      if (partes.length === 1) return partes[0].charAt(0).toUpperCase()
      return (partes[0].charAt(0) + partes[partes.length - 1].charAt(0)).toUpperCase()
    },
    anoFundacao () {
      return this.loja?.criada_em ? new Date(this.loja.criada_em).getFullYear() : new Date().getFullYear() - 4
    },
    slugDominio () {
      return (this.loja?.nome || 'restaurante').toLowerCase().replace(/[^a-z0-9]+/g, '')
    },
    tituloLinhas () {
      const nome = (this.loja?.nome || '').trim()
      const partes = nome.split(/\s+/)
      if (partes.length === 1) return [nome]
      if (partes.length === 2) return [partes[0], partes[1]]
      const meio = Math.ceil(partes.length / 2)
      return [partes.slice(0, meio).join(' '), partes.slice(meio).join(' ')]
    },
  },
}
</script>

<style scoped>
/* ════════════════════════════════════════════════════════════════
   TOKENS
   ════════════════════════════════════════════════════════════════ */
.trm { font-family: 'Inter', system-ui, sans-serif; }
.trm--dark  { background: var(--trm-bg-d); color: #ece6db; }
.trm--light { background: var(--trm-bg-l); color: #1a1714; }
.font-serif { font-family: 'Cormorant Garamond', 'Playfair Display', Georgia, serif; }

/* loader */
.trm-loader {
  width: 80px; height: 1px;
  background: color-mix(in oklab, var(--cor-primaria), transparent 70%);
  position: relative; overflow: hidden;
}
.trm-loader::after {
  content: ''; position: absolute; inset: 0; width: 30%;
  background: var(--cor-primaria);
  animation: trm-load 1.4s ease-in-out infinite;
}
@keyframes trm-load { 0%{ transform: translateX(-100%);} 100%{ transform: translateX(330%);} }

/* utils */
.trm-rule {
  display: inline-block; height: 1px;
  background: currentColor; opacity: .35;
  width: 32px;
}
.trm-monogram {
  display: inline-flex; align-items: center; justify-content: center;
  width: 36px; height: 36px;
  border: 1px solid var(--cor-primaria);
  border-radius: 50%;
  font-family: 'Cormorant Garamond', serif;
  font-style: italic; font-size: 18px;
  letter-spacing: -0.02em;
}
.trm-monogram--big {
  width: 84px; height: 84px;
  font-size: 38px;
}

/* iconbtn */
.trm-iconbtn {
  width: 38px; height: 38px;
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid currentColor; opacity: .55;
  transition: all .3s ease;
  background: transparent; color: currentColor;
}
.trm-iconbtn:hover {
  opacity: 1;
  border-color: var(--cor-primaria);
  color: var(--cor-primaria);
}

/* ════════════════════════════════════════════════════════════════
   HERO
   ════════════════════════════════════════════════════════════════ */
.trm-hero-title {
  font-size: clamp(3.4rem, 8.5vw, 7.4rem);
  line-height: .95;
  letter-spacing: -0.025em;
  font-weight: 400;
}

.trm-hero-frame {
  position: relative;
  aspect-ratio: 4 / 5;
  overflow: hidden;
  background: rgba(255,255,255,.04);
  box-shadow: 0 40px 80px -30px rgba(0,0,0,.55);
}
.trm--light .trm-hero-frame { background: rgba(0,0,0,.04); box-shadow: 0 40px 80px -30px rgba(60,40,20,.25); }

.trm-vignette {
  background:
    linear-gradient(180deg, transparent 55%, rgba(0,0,0,.7) 100%),
    radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,.35) 100%);
}

.trm-dot-pulse {
  width: 10px; height: 10px; border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 0 4px rgba(74,222,128,.2);
  animation: trm-pulse 2s ease-in-out infinite;
}
@keyframes trm-pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(74,222,128,.18); }
  50%      { box-shadow: 0 0 0 8px rgba(74,222,128,.05); }
}

.trm-floatcard {
  position: absolute;
  bottom: -32px; left: -32px;
  background: var(--trm-bg-d);
  color: #ece6db;
  padding: 18px 22px;
  min-width: 200px;
  border: 1px solid color-mix(in oklab, var(--cor-primaria), transparent 60%);
  box-shadow: 0 30px 50px -20px rgba(0,0,0,.5);
}
.trm--light .trm-floatcard {
  background: #fff;
  color: #1a1714;
  border-color: color-mix(in oklab, var(--cor-primaria), transparent 70%);
  box-shadow: 0 30px 50px -20px rgba(60,40,20,.25);
}

/* KPIs */
.trm-kpi { padding-top: 14px; border-top: 1px solid; border-color: currentColor; opacity: 1; }
.trm-kpi__num {
  font-size: clamp(2.2rem, 4vw, 2.8rem);
  font-weight: 400;
  line-height: 1;
  color: var(--cor-primaria);
}
.trm-kpi__lbl {
  font-size: 9px; letter-spacing: .35em;
  text-transform: uppercase;
  opacity: .55;
  margin-top: 6px;
}
.trm-kpi { border-color: color-mix(in oklab, currentColor, transparent 80%); }

/* ════════════════════════════════════════════════════════════════
   BUTTONS
   ════════════════════════════════════════════════════════════════ */
.trm-btn {
  display: inline-flex; align-items: center; gap: 12px;
  padding: 14px 26px;
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .25em;
  transition: all .35s ease;
  cursor: pointer;
  border: 1px solid transparent;
  white-space: nowrap;
  background: transparent;
}
.trm-btn--solid {
  background: var(--cor-primaria);
  color: #fff;
  border-color: var(--cor-primaria);
}
.trm-btn--solid:hover {
  background: transparent;
  color: var(--cor-primaria);
}
.trm-btn--ghost {
  border-color: currentColor;
  opacity: .75;
}
.trm-btn--ghost:hover {
  opacity: 1;
  background: currentColor;
  color: var(--trm-bg-d);
}
.trm--light .trm-btn--ghost:hover { color: var(--trm-bg-l); }
.trm-btn--reverse {
  background: #fff;
  color: var(--cor-primaria);
  border-color: #fff;
}
.trm-btn--reverse:hover { background: transparent; color: #fff; }
.trm-btn__arr { transition: transform .35s ease; }
.trm-btn:hover .trm-btn__arr { transform: translateX(4px); }

/* ════════════════════════════════════════════════════════════════
   INFO BAR
   ════════════════════════════════════════════════════════════════ */
.trm-infobar {
  border-top: 1px solid;
  border-bottom: 1px solid;
  border-color: color-mix(in oklab, currentColor, transparent 85%);
  padding: 0 24px;
}
.trm-infobar__item {
  padding: 18px 24px;
  display: flex; flex-direction: column; gap: 4px;
}
.trm-infobar__lbl {
  font-size: 9px; letter-spacing: .4em;
  text-transform: uppercase;
  opacity: .55;
}
.trm-infobar__val {
  font-size: 16px;
  letter-spacing: -0.005em;
}

/* ════════════════════════════════════════════════════════════════
   SECTION NAV (sticky)
   ════════════════════════════════════════════════════════════════ */
.trm-sectionnav {
  position: sticky; top: 0; z-index: 20;
  padding: 12px 18rem 12px 24px;
  backdrop-filter: blur(18px);
  background: color-mix(in oklab, var(--trm-bg-d) 75%, transparent);
  border-bottom: 1px solid color-mix(in oklab, currentColor, transparent 90%);
}
.trm--light .trm-sectionnav {
  background: color-mix(in oklab, var(--trm-bg-l) 80%, transparent);
}
@media (max-width: 768px) {
  .trm-sectionnav { padding-right: 8.5rem; padding-left: 16px; }
}
.trm-sectionnav__inner {
  display: flex; gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}
.trm-sectionnav__inner::-webkit-scrollbar { display: none; }
.trm-sectionnav__link {
  display: inline-flex; align-items: baseline; gap: 8px;
  padding: 8px 16px;
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .22em;
  white-space: nowrap;
  transition: all .25s ease;
  opacity: .55;
  cursor: pointer;
  position: relative;
}
.trm-sectionnav__link::after {
  content: ''; position: absolute;
  left: 50%; bottom: 2px;
  width: 0; height: 1px;
  background: var(--cor-primaria);
  transition: all .3s ease;
}
.trm-sectionnav__link:hover {
  opacity: 1;
  color: var(--cor-primaria);
}
.trm-sectionnav__link:hover::after {
  width: calc(100% - 32px);
  left: 16px;
}
.trm-sectionnav__num {
  font-size: 12px;
  opacity: .7;
}

/* ════════════════════════════════════════════════════════════════
   SECTION HEADERS
   ════════════════════════════════════════════════════════════════ */
.trm-divider {
  border-top: 1px solid color-mix(in oklab, currentColor, transparent 88%);
}
.trm-secthead {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 24px;
  margin: 60px 0 44px;
  padding-top: 8px;
}
.trm-eyebrow {
  display: inline-block;
  font-size: 10px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .4em;
  margin-bottom: 14px;
}
.trm-secttitle {
  font-size: clamp(2.6rem, 5.5vw, 4.4rem);
  font-weight: 400; line-height: 1;
  letter-spacing: -0.025em;
}
.trm-secttitle--md {
  font-size: clamp(1.9rem, 3.6vw, 2.8rem);
}
.trm-sectdesc {
  margin-top: 14px;
  font-style: italic;
  font-family: 'Cormorant Garamond', serif;
  font-size: 17px;
  opacity: .65;
  max-width: 520px;
}
.trm-sectnum {
  display: none;
  font-size: clamp(2.6rem, 4.5vw, 3.8rem);
  opacity: .25;
  color: var(--cor-primaria);
  white-space: nowrap;
}
@media (min-width: 768px) { .trm-sectnum { display: block; } }

/* chips */
.trm-chip {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 18px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px; font-style: italic;
  border: 1px solid color-mix(in oklab, currentColor, transparent 70%);
  border-radius: 999px;
  transition: all .3s ease;
  background: transparent;
  cursor: pointer;
  color: currentColor;
}
.trm-chip:hover {
  background: var(--cor-primaria);
  color: #fff;
  border-color: var(--cor-primaria);
}

/* ════════════════════════════════════════════════════════════════
   CARDS (passados via classe a ProductSlider/Catalog)
   ════════════════════════════════════════════════════════════════ */
:deep(.trm-card) {
  border: 1px solid color-mix(in oklab, currentColor, transparent 88%) !important;
  background: transparent !important;
  transition: all .5s ease !important;
}
:deep(.trm-card-hover):hover {
  border-color: var(--cor-primaria) !important;
  background: color-mix(in oklab, var(--cor-primaria), transparent 96%) !important;
  transform: translateY(-3px);
}
:deep(.trm-prodname) {
  font-family: 'Cormorant Garamond', 'Playfair Display', Georgia, serif !important;
  font-size: 19px !important;
  font-weight: 400 !important;
  letter-spacing: -0.005em !important;
  line-height: 1.25 !important;
}
:deep(.trm-price) {
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 20px !important;
  font-weight: 500 !important;
  font-style: italic !important;
  color: var(--cor-primaria) !important;
  letter-spacing: -0.01em !important;
}
:deep(.trm-badge) {
  background: transparent !important;
  border: 1px solid var(--cor-primaria) !important;
  color: var(--cor-primaria) !important;
  font-weight: 500 !important;
  font-size: 9px !important;
  letter-spacing: .25em !important;
  padding: 3px 8px !important;
  border-radius: 0 !important;
}

/* ════════════════════════════════════════════════════════════════
   BLOCKS (reservar / take-away)
   ════════════════════════════════════════════════════════════════ */
.trm-card-block {
  border: 1px solid color-mix(in oklab, currentColor, transparent 88%);
  padding: 36px 32px;
  position: relative;
  overflow: hidden;
}
.trm-card-block__bg {
  position: absolute;
  inset: auto -120px -120px auto;
  width: 360px; height: 360px;
  border-radius: 50%;
  background: rgba(255,255,255,.06);
  pointer-events: none;
}

.trm-input-on-accent {
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.2);
  padding: 12px 14px;
  font-size: 13px;
  color: #fff;
  outline: none;
  font-family: inherit;
  transition: all .25s;
  border-radius: 0;
}
.trm-input-on-accent::placeholder { color: rgba(255,255,255,.5); }
.trm-input-on-accent:focus {
  background: rgba(255,255,255,.15);
  border-color: rgba(255,255,255,.5);
}
.trm-input-on-accent option { color: #1a1714; }

/* dot leader (preço estilo carta) */
.trm-dotleader {
  flex: 1; min-width: 30px; align-self: flex-end;
  margin-bottom: 6px;
  background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
  background-size: 6px 6px;
  background-repeat: repeat-x;
  background-position: 0 50%;
  height: 6px;
  opacity: .35;
}

.trm-paychip {
  padding: 7px 14px;
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .2em;
  border: 1px solid color-mix(in oklab, currentColor, transparent 75%);
  opacity: .8;
}

/* ════════════════════════════════════════════════════════════════
   CATALOG TABS
   ════════════════════════════════════════════════════════════════ */
:deep(.trm-tab) {
  background: transparent !important;
  border: 1px solid color-mix(in oklab, currentColor, transparent 75%) !important;
  color: currentColor !important;
  opacity: .65 !important;
  text-transform: uppercase;
  font-weight: 500 !important;
  font-size: 10.5px !important;
  letter-spacing: .25em !important;
  padding: 9px 18px !important;
  transition: all .3s ease !important;
}
:deep(.trm-tab:hover) { opacity: 1 !important; }
:deep(.trm-tab--active) {
  background: var(--cor-primaria) !important;
  color: #fff !important;
  border-color: var(--cor-primaria) !important;
  opacity: 1 !important;
}
:deep(.trm-subtab) {
  background: transparent !important;
  color: currentColor !important;
  opacity: .55 !important;
  font-weight: 500 !important;
  font-size: 10px !important;
  text-transform: uppercase;
  letter-spacing: .2em !important;
}
:deep(.trm-subtab--active) {
  color: var(--cor-primaria) !important;
  opacity: 1 !important;
  font-style: italic;
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 14px !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}
:deep(.trm-filterbox) {
  border: 1px solid color-mix(in oklab, currentColor, transparent 85%) !important;
  background: transparent !important;
}
:deep(.trm-indicator) {
  background: var(--cor-primaria) !important;
  color: #fff !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: .2em !important;
  border-radius: 0 !important;
}
:deep(.trm-stock-on) {
  border: 1px solid var(--cor-primaria) !important;
  color: var(--cor-primaria) !important;
  background: transparent !important;
}
:deep(.trm-btn-tiny--accent) {
  color: var(--cor-primaria) !important;
  background: transparent !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* reviews */
:deep(.trm-star-on) { color: var(--cor-primaria) !important; }
:deep(.trm-progress) { background: var(--cor-primaria) !important; }
:deep(.trm-review-own) {
  border: 1px solid var(--cor-primaria) !important;
  background: color-mix(in oklab, var(--cor-primaria), transparent 95%) !important;
}
:deep(.trm-ownbadge) {
  background: var(--cor-primaria) !important;
  color: #fff !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: .2em !important;
  font-size: 9px !important;
}
:deep(.trm-link) {
  color: var(--cor-primaria) !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* footer */
.trm-foot-link {
  display: inline-block;
  transition: color .25s ease;
  font-size: 14px;
  cursor: pointer;
  background: transparent;
  border: 0;
  color: currentColor;
  opacity: .75;
}
.trm-foot-link:hover { color: var(--cor-primaria); opacity: 1; }
</style>
