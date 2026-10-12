<!-- TemplateRestauranteModerno.vue — Revamp
     Hero full-bleed com cartão de serviço · Sugestões do chef em bento
     A Carta: índice sticky + pratos agrupados por categoria (linhas com leader pontilhado)
     Tipografia: Fraunces (títulos) + Manrope (corpo)
     Acento configurável via --cor-primaria (default: #e4572e tomate)
-->
<template>
  <div
    class="rm-root"
    :class="isDark ? 'rm-dark' : 'rm-light'"
    :style="cssVars"
  >
    <ProductInfoCard
      :produto="selectedProduct"
      :loja="loja"
      :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)"
    />

    <MultiCart ref="cart" :isDark="isDark" />

    <Profile
      :data="user"
      :isDark="isDark"
      class="z-40"
      @log_out="logOut()"
    />

    <!-- Loading -->
    <div v-if="loading" class="rm-loading">
      <div class="rm-loading__plate">
        <span class="rm-loading__dot"></span>
      </div>
      <span class="rm-loading__text">A preparar a mesa…</span>
    </div>

    <template v-else-if="loja">
      <!-- ══════════════════════════════════════════
           TOP BAR
      ══════════════════════════════════════════ -->
      <header class="rm-bar" :class="{ 'rm-bar--solid': scrolled }">
        <div class="rm-bar__left">
          <button class="rm-icon-btn" @click="$router.back()" aria-label="Voltar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
          </button>

          <div class="rm-bar__brand">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" class="rm-bar__logo" />
            <span v-else class="rm-bar__logo rm-bar__logo--initial">{{ loja.nome.charAt(0) }}</span>
            <span class="rm-bar__name">{{ loja.nome }}</span>
          </div>
        </div>

        <nav class="rm-bar__links">
          <button v-if="totalDestaques" @click="scrollToId('rm-chef')">Chef</button>
          <button @click="scrollToId('rm-carta')">Carta</button>
          <button @click="scrollToId('rm-catalogo')">Catálogo</button>
          <button @click="scrollToId('rm-visite')">Visite-nos</button>
          <button @click="scrollToId('rm-avaliacoes')">Avaliações</button>
        </nav>

        <button class="rm-icon-btn rm-bar__theme" @click="toggleDark" aria-label="Alternar tema">
          <svg v-if="isDark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
      </header>

      <!-- ══════════════════════════════════════════
           HERO
      ══════════════════════════════════════════ -->
      <section class="rm-hero">
        <video
          v-if="isVideo(loja.banner_url)"
          :src="loja.banner_url" :poster="loja.banner_poster_url"
          class="rm-hero__media"
          v-video-visivel muted loop playsinline
        ></video>
        <img
          v-else-if="loja.banner_url"
          :src="loja.banner_url"
          :alt="loja.nome"
          class="rm-hero__media"
        />
        <div v-else class="rm-hero__media rm-hero__media--empty"></div>
        <div class="rm-hero__shade"></div>

        <div class="rm-hero__inner">
          <div class="rm-hero__copy">
            <div class="rm-hero__pills">
              <span class="rm-pill rm-pill--accent">{{ loja.categoria || 'Restaurante' }}</span>
              <span v-if="loja.localizacao" class="rm-pill">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ loja.localizacao }}
              </span>
            </div>

            <h1 class="rm-hero__title">{{ loja.nome }}</h1>
            <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />

            <p v-if="loja.descricao" class="rm-hero__desc">
              {{ truncate(loja.descricao, 170) }}
            </p>

            <div class="rm-hero__ctas">
              <button class="rm-btn rm-btn--accent" @click="scrollToId('rm-carta')">
                Ver a carta
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
              </button>
              <button v-if="totalDestaques" class="rm-btn rm-btn--glass" @click="scrollToId('rm-chef')">
                Sugestões do chef
              </button>
            </div>
          </div>

          <!-- Cartão de serviço -->
          <aside class="rm-service">
            <div class="rm-service__head">Serviço</div>

            <div class="rm-service__row">
              <span>Entrega</span>
              <span :class="loja.entrega_ativa ? 'rm-ok' : 'rm-off'">
                {{ loja.entrega_ativa ? (entregaDesde !== null ? 'desde ' + entregaDesde : 'Sim') : 'Indisponível' }}
              </span>
            </div>
            <div class="rm-service__row">
              <span>Take-away</span>
              <span :class="loja.levantamento_ativo ? 'rm-ok' : 'rm-off'">
                {{ loja.levantamento_ativo ? 'Sim' : 'Indisponível' }}
              </span>
            </div>
            <div class="rm-service__row">
              <span>Pratos na carta</span>
              <span>{{ totalProdutos ?? "—" }}</span>
            </div>

            <div class="rm-service__rating">
              <span class="rm-service__score">{{ ratingFormatted }}</span>
              <div>
                <div class="rm-stars">
                  <svg v-for="i in 5" :key="i" width="12" height="12" viewBox="0 0 24 24"
                       :class="i <= Math.round(loja.rating_medio || 0) ? 'rm-star--on' : 'rm-star--off'"
                       fill="currentColor"><path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2-6.2 3.2L7 14.2 2 9.3l6.9-1z"/></svg>
                </div>
                <span class="rm-service__reviews">{{ loja.total_avaliacoes || 0 }} avaliações</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <main>
        <!-- ══════════════════════════════════════════
             SUGESTÕES DO CHEF — bento
        ══════════════════════════════════════════ -->
        <section v-if="totalDestaques" id="rm-chef" class="rm-section">
          <div class="rm-wrap">
            <div class="rm-heading">
              <span class="rm-heading__eyebrow">Escolhas da casa</span>
              <h2 class="rm-heading__title">Sugestões do <em>chef</em></h2>
            </div>

            <!-- uma página: os 5 primeiros destaques -->
            <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="5" :lazy="false"
                               class="rm-bento" :class="'rm-bento--' + Math.min(totalDestaques, 5)" v-slot="l">
              <template v-if="l.carregando">
                <div v-for="n in Math.min(totalDestaques, 5)" :key="n" class="rm-dish rm-skel" :class="{ 'rm-dish--hero': n === 1 }"></div>
              </template>
              <article
                v-for="(p, i) in l.itens"
                :key="p.id"
                class="rm-dish"
                :class="{ 'rm-dish--hero': i === 0 }"
                @click="selectedProduct = p"
              >
                <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" class="rm-dish__img" muted loop v-video-visivel playsinline></video>
                <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" class="rm-dish__img" loading="lazy" />
                <div v-else class="rm-dish__img rm-dish__img--empty">{{ p.nome.charAt(0) }}</div>
                <div class="rm-dish__shade"></div>

                <div class="rm-dish__body">
                  <span v-if="i === 0" class="rm-dish__tag">Assinatura</span>
                  <h3 class="rm-dish__name">{{ p.nome }}</h3>
                  <p v-if="i === 0 && p.descricao" class="rm-dish__desc">{{ truncate(p.descricao, 110) }}</p>
                  <div class="rm-dish__foot">
                    <span class="rm-dish__price">{{ formatPrice(p.preco) }}</span>
                    <span class="rm-dish__add" aria-hidden="true">+</span>
                  </div>
                </div>
              </article>
            </ProdutosPaginados>
          </div>
        </section>

        <!-- ══════════════════════════════════════════
             A CARTA — cada grupo pede os seus pratos página a página
        ══════════════════════════════════════════ -->
        <section id="rm-carta" class="rm-section rm-section--carta">
          <div class="rm-wrap">
            <div class="rm-heading">
              <span class="rm-heading__eyebrow">Menu</span>
              <h2 class="rm-heading__title">A <em>carta</em></h2>
            </div>

            <!-- Chips de secção (sticky): tipos · categorias · catálogo -->
            <div v-if="grupos.length" class="rm-chips hide-scroll">
              <template v-for="(g, i) in grupos" :key="g.key">
                <span v-if="i === 0 || grupos[i - 1].seccao !== g.seccao" class="rm-chips__label">
                  {{ SECCOES[g.seccao] }}
                </span>
                <button
                  class="rm-chip"
                  :class="{ 'rm-chip--active': grupoActivo === g.key }"
                  @click="irParaGrupo(g.key)"
                >
                  {{ g.nome }}
                  <span class="rm-chip__count">{{ g.total }}</span>
                </button>
              </template>
              <span class="rm-chips__sep"></span>
              <button class="rm-chip rm-chip--outline" @click="scrollToId('rm-catalogo')">
                Catálogo completo →
              </button>
            </div>

            <div v-if="loading" class="rm-menu-skeleton">
              <div v-for="i in 6" :key="i" class="rm-skel"></div>
            </div>

            <div v-else-if="!grupos.length" class="rm-empty">
              <p>A carta ainda está a ser preparada.</p>
            </div>

            <div v-else class="rm-menu">
              <div
                v-for="(g, i) in grupos"
                :key="g.key"
                :id="'rm-grupo-' + g.key"
                class="rm-group"
              >
                <div v-if="i === 0 || grupos[i - 1].seccao !== g.seccao" class="rm-seccao">
                  <span>{{ SECCOES[g.seccao] }}</span>
                </div>

                <div class="rm-group__head">
                  <h3 class="rm-group__title">{{ g.nome }}</h3>
                  <span class="rm-group__line"></span>
                  <span class="rm-group__count">{{ g.total }} {{ g.total === 1 ? 'prato' : 'pratos' }}</span>
                </div>

                <ProdutosPaginados :params="g.params" :limit="LIMITE" v-slot="l">
                  <div class="rm-items">
                    <template v-if="l.carregando">
                      <div v-for="n in Math.min(g.total, LIMITE)" :key="n" class="rm-skel"></div>
                    </template>
                    <button
                      v-for="p in l.itens"
                      :key="p.id"
                      class="rm-item"
                      :class="{ 'rm-item--out': esgotado(p) }"
                      @click="selectedProduct = p"
                    >
                      <div class="rm-item__thumb">
                        <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                        <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                        <span v-else>{{ p.nome.charAt(0) }}</span>
                      </div>

                      <div class="rm-item__body">
                        <div class="rm-item__top">
                          <span class="rm-item__name">{{ p.nome }}</span>
                          <span class="rm-item__dots"></span>
                          <span class="rm-item__price">{{ formatPrice(p.preco) }}</span>
                          <BotaoFavorito tipo="produto" :id="p.id" elemento="span" variante="simples" :tamanho="30" :isDark="isDark" class="rm-item__fav" />
                        </div>
                        <p v-if="p.descricao" class="rm-item__desc">{{ p.descricao }}</p>
                        <div class="rm-item__tags">
                          <span v-if="esgotado(p)" class="rm-tag rm-tag--out">Esgotado</span>
                          <span v-if="p.destaque" class="rm-tag rm-tag--accent">Chef</span>
                          <span v-for="t in tagsProduto(p)" :key="t" class="rm-tag">{{ t }}</span>
                        </div>
                      </div>
                    </button>
                  </div>
                  <button v-if="l.temMais || l.aCarregarMais" class="rm-mais" :disabled="l.aCarregarMais" @click="l.carregarMais()">
                    {{ l.aCarregarMais ? 'A carregar…' : `Ver mais pratos (${l.total - l.itens.length})` }}
                  </button>
                </ProdutosPaginados>
              </div>
            </div>
          </div>
        </section>

        <!-- ══════════════════════════════════════════
             CATÁLOGO COMPLETO — pesquisa e filtros em todos os produtos
        ══════════════════════════════════════════ -->
        <section id="rm-catalogo" class="rm-section rm-section--catalogo">
          <div class="rm-wrap">
            <div class="rm-heading">
              <span class="rm-heading__eyebrow">Todos os produtos</span>
              <h2 class="rm-heading__title">Catálogo <em>completo</em></h2>
              <p class="rm-heading__sub">Pesquisa e filtra por tipo, categoria ou preço.</p>
            </div>

            <div class="rm-catalog">
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="200px"
                card-border-radius="rounded-3xl"
                skeleton-class="rounded-3xl"
                hover-effect="hover:-translate-y-1 hover:shadow-xl transition-all duration-300"
                hover-border-class=""
                filter-container-radius="rounded-3xl"
                input-border-radius="rounded-full"
                input-focus-class="rm-input-focus"
                tab-border-radius="rounded-full"
                active-tab-class="rm-cat-tab--active"
                inactive-tab-dark-class="rm-cat-tab"
                inactive-tab-light-class="rm-cat-tab"
                active-sub-tab-class="rm-cat-tab--active"
                inactive-sub-tab-dark-class="rm-cat-tab"
                inactive-sub-tab-light-class="rm-cat-tab"
                category-border-class="rm-cat-border"
                product-name-class="rm-cat-name"
                product-name-hover-class="group-hover:opacity-75"
                price-class="rm-cat-price"
                badge-text="Chef"
                badge-class="rm-cat-badge"
                indicator-active-class="rm-cat-indicator"
                clear-filter-class="rm-cat-clear"
                clear-all-class="rm-cat-clear-all"
                spinner-class="rm-cat-spinner"
                :show-stock="false"
                :show-category-badges="false"
                empty-text="Nenhum prato encontrado."
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- ══════════════════════════════════════════
             VISITE-NOS
        ══════════════════════════════════════════ -->
        <section id="rm-visite" class="rm-section rm-section--visite">
          <div class="rm-wrap rm-visite">
            <div class="rm-visite__quote">
              <span class="rm-heading__eyebrow">A nossa casa</span>
              <blockquote>
                “{{ loja.descricao || 'Cozinha honesta, ingredientes da época e uma mesa onde todos se sentem em casa.' }}”
              </blockquote>
              <div class="rm-visite__sign">— {{ loja.nome }}</div>
            </div>

            <div class="rm-visite__info">
              <div v-if="loja.localizacao" class="rm-info-block">
                <div class="rm-info-block__label">Onde estamos</div>
                <div class="rm-info-block__value">{{ loja.localizacao }}</div>
              </div>

              <div v-if="opcoesEntrega.length" class="rm-info-block">
                <div class="rm-info-block__label">Entregas</div>
                <div v-for="o in opcoesEntrega" :key="o.id" class="rm-info-row">
                  <span>{{ o.nome }}</span>
                  <span class="rm-info-row__val">{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</span>
                </div>
              </div>

              <div v-if="metodosPagamento.length" class="rm-info-block">
                <div class="rm-info-block__label">Pagamento</div>
                <div class="rm-pay">
                  <span v-for="m in metodosPagamento" :key="m.id" class="rm-pay__chip">
                    {{ m.tipo }}
                  </span>
                </div>
              </div>

              <button class="rm-btn rm-btn--accent rm-visite__cta" @click="scrollToId('rm-carta')">
                Fazer o meu pedido
              </button>
            </div>
          </div>
        </section>

        <!-- ══════════════════════════════════════════
             AVALIAÇÕES
        ══════════════════════════════════════════ -->
        <section id="rm-avaliacoes" class="rm-section">
          <div class="rm-wrap">
            <div class="rm-heading">
              <span class="rm-heading__eyebrow">Quem já provou</span>
              <h2 class="rm-heading__title">Avaliações</h2>
            </div>

            <AvaliacaoLoja
              :loja-id="lojaId"
              :isDark="isDark"
              summary-border-radius="rounded-3xl"
              form-border-radius="rounded-3xl"
              review-card-border-radius="rounded-2xl"
              button-border-radius="rounded-full"
              textarea-border-radius="rounded-2xl"
              :star-active-class="'rm-star--on'"
              :star-inactive-class="'rm-star--off'"
              progress-bar-class="rm-progress"
              :submit-button-class="'rm-btn rm-btn--accent w-full justify-center'"
              :review-card-class="'rm-review-card'"
              :own-review-border-class="'rm-review-own'"
              :load-more-button-class="'rm-btn rm-btn--ghost'"
              @rating-updated="onRatingUpdated"
            />
          </div>
        </section>
      </main>

      <!-- ══════════════════════════════════════════
           FOOTER
      ══════════════════════════════════════════ -->
      <footer class="rm-footer">
        <div class="rm-wrap">
          <div class="rm-footer__name">{{ loja.nome }}</div>
          <div class="rm-footer__row">
            <span class="rm-footer__copy">© {{ currentYear }} {{ loja.nome }}<template v-if="loja.localizacao"> · {{ loja.localizacao }}</template></span>
            <div class="rm-footer__links">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
            </div>
          </div>
        </div>
      </footer>

      <!-- Modal políticas -->
      <div v-if="modalPolitica" class="rm-modal-overlay" @click.self="modalPolitica = null">
        <div class="rm-modal">
          <div class="rm-modal__head">
            <h3>{{ tituloPolitica }}</h3>
            <button class="rm-icon-btn" @click="modalPolitica = null" aria-label="Fechar">×</button>
          </div>
          <div class="rm-modal__body">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="rm-notfound">
      <p>Restaurante não encontrado</p>
      <button class="rm-btn rm-btn--ghost" @click="$router.back()">← Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import ProdutosPaginados from '@/components/produtos/ProdutosPaginados.vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import Profile from '@/components/profile/UserProfile.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import BotaoFavorito from '@/components/favoritos/BotaoFavorito.vue'

// atributos que fazem sentido mostrar como etiqueta numa carta
const TAGS_ATRIBUTOS = ['calorias', 'picante', 'alergenos', 'volume', 'porcao', 'dose', 'vegetariano', 'vegan']

const SECCOES = { tipo: 'Por tipo', categoria: 'Por categoria', todos: 'Carta' }

const LIMITE = 6   // pratos por página em cada grupo

export default {
  name: 'TemplateRestauranteModerno',

  components: { ProductInfoCard, BotaoFavorito, MultiCart, Profile, AvaliacaoLoja, ProductCatalog, ProdutosPaginados },

  emits: ['toggle-dark'],

  props: {
    tema: { type: Object, default: () => ({}) },
  },

  setup (props, { emit }) {
    const lojaData = useLojaData()
    const isDark   = ref(props.tema?.darkMode !== false)
    const user     = ref(JSON.parse(localStorage.getItem('user') || '{}'))
    const currentYear = new Date().getFullYear()

    const grupoActivo     = ref(null)
    const scrolled        = ref(false)

    watch(() => props.tema?.darkMode, v => { if (v !== undefined) isDark.value = v !== false })

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#e4572e',
      '--cor-secundaria': props.tema?.corSecundaria || '#14110f',
    }))

    // Como no Clássico: primeiro "Por tipo", depois "Por categoria", pela ordem da loja.
    // Só metadados e contagens — cada grupo pede os pratos página a página.
    const grupos = lojaData.gruposProdutos

    const entregaDesde = computed(() => {
      const precos = lojaData.opcoesEntrega.value.map(o => Number(o.preco))
      if (!precos.length) return null
      const min = Math.min(...precos)
      return min === 0 ? 'grátis' : lojaData.formatPrice(min)
    })

    const ratingFormatted = computed(() => {
      const r = lojaData.loja.value?.rating_medio
      return r ? Number(r).toFixed(1) : '—'
    })

    const tituloPolitica = computed(() => ({
      devolucao: 'Devoluções', termos: 'Termos de serviço', privacidade: 'Privacidade',
    })[lojaData.modalPolitica.value] || '')

    const textoPolitica = computed(() => {
      const l = lojaData.loja.value
      if (!l) return ''
      return ({
        devolucao: l.politica_devolucao, termos: l.termos_servico, privacidade: l.politica_privacidade,
      })[lojaData.modalPolitica.value] || ''
    })

    // ── Helpers ───────────────────────────────────────────────────────
    function toggleDark () {
      isDark.value = !isDark.value
      emit('toggle-dark', isDark.value)
    }

    function isVideo (url) {
      return /\.(mp4|webm|mov|mkv)(\?|$)/i.test(url || '')
    }

    function truncate (txt, n) {
      if (!txt) return ''
      return txt.length > n ? txt.slice(0, n).trimEnd() + '…' : txt
    }

    function esgotado (p) {
      return p.stock && Number(p.stock.quantidade) <= 0
    }

    function tagsProduto (p) {
      const attrs = p.atributos_normalizados || {}
      const tags = []
      Object.entries(attrs).forEach(([k, vals]) => {
        if (!TAGS_ATRIBUTOS.includes(k.toLowerCase()) || !vals?.length) return
        const v = vals.join(', ')
        tags.push(k.toLowerCase() === 'calorias' && /^\d+$/.test(v) ? `${v} kcal` : v)
      })
      return tags.slice(0, 3)
    }

    function irParaGrupo (key) {
      grupoActivo.value = key
      lojaData.scrollToId('rm-grupo-' + key)
    }

    // ── Scroll: barra sólida + grupo activo ─────────────────────────
    let groupObserver = null

    function onScroll () {
      scrolled.value = window.scrollY > 60
    }

    function observarGrupos () {
      groupObserver?.disconnect()
      groupObserver = new IntersectionObserver(entries => {
        entries.forEach(e => {
          if (e.isIntersecting) grupoActivo.value = e.target.id.replace('rm-grupo-', '')
        })
      }, { rootMargin: '-30% 0px -60% 0px' })
      document.querySelectorAll('[id^="rm-grupo-"]').forEach(el => groupObserver.observe(el))
    }

    watch([grupos, lojaData.loading], async () => {
      await nextTick()
      observarGrupos()
    })

    onMounted(() => {
      window.addEventListener('scroll', onScroll, { passive: true })
      onScroll()
    })

    onUnmounted(() => {
      window.removeEventListener('scroll', onScroll)
      groupObserver?.disconnect()
    })

    return {
      ...lojaData,
      isDark, user, currentYear, cssVars,
      SECCOES,
      LIMITE, grupoActivo, scrolled,
      grupos, entregaDesde, ratingFormatted,
      tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, tagsProduto, irParaGrupo,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,800;1,9..144,400;1,9..144,600&family=Manrope:wght@400;500;600;700;800&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.rm-root {
  --accent: var(--cor-primaria, #e4572e);
  --font-display: 'Fraunces', Georgia, serif;
  --font-body: 'Manrope', system-ui, sans-serif;
  --radius: 22px;
  --bar-h: 68px;
  --bar-pad: 28px;

  /* carrinho · notificações · perfil centrados na barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--font-body);
  background: var(--bg);
  color: var(--fg);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .4s, color .4s;
}

.rm-dark {
  --bg: var(--cor-secundaria, #14110f);
  --bg2: color-mix(in srgb, var(--bg) 88%, #fff 12%);
  --bg3: color-mix(in srgb, var(--bg) 80%, #fff 20%);
  --fg: #f6f1ea;
  --fg2: rgba(246, 241, 234, .66);
  --fg3: rgba(246, 241, 234, .38);
  --line: rgba(246, 241, 234, .12);
}

.rm-light {
  --bg: #f7f2eb;
  --bg2: #fffdf9;
  --bg3: #efe7dc;
  --fg: #1d1915;
  --fg2: rgba(29, 25, 21, .68);
  --fg3: rgba(29, 25, 21, .42);
  --line: rgba(29, 25, 21, .12);
}

.rm-wrap {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 32px;
}

/* ── Loading ─────────────────────────────────────────────── */
.rm-loading {
  position: fixed; inset: 0; z-index: 50;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px;
  background: var(--bg);
}
.rm-loading__plate {
  width: 64px; height: 64px; border-radius: 50%;
  border: 2px solid var(--line);
  border-top-color: var(--accent);
  display: flex; align-items: center; justify-content: center;
  animation: rmSpin 1s linear infinite;
}
.rm-loading__dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); }
.rm-loading__text { font-family: var(--font-display); font-style: italic; color: var(--fg2); }
@keyframes rmSpin { to { transform: rotate(360deg); } }

/* ── Top bar ─────────────────────────────────────────────── */
.rm-bar {
  /* abaixo do botão do carrinho (z-30) e do perfil (z-40), acima dos chips (z-20) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h);
  display: flex; align-items: center; gap: 24px;
  /* espaço à direita para os botões flutuantes de carrinho/perfil */
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 20px) 0 var(--bar-pad);
  color: #fff;
  transition: background .3s, color .3s, box-shadow .3s;
}
.rm-bar--solid {
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(14px);
  color: var(--fg);
  box-shadow: 0 1px 0 var(--line);
}
.rm-bar__left { display: flex; align-items: center; gap: 14px; min-width: 0; }
.rm-bar__brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
.rm-bar__logo {
  width: 34px; height: 34px; border-radius: 50%; object-fit: cover; flex-shrink: 0;
}
.rm-bar__logo--initial {
  display: flex; align-items: center; justify-content: center;
  background: var(--accent); color: #fff;
  font-family: var(--font-display); font-weight: 800; font-size: 16px;
}
.rm-bar__name {
  font-family: var(--font-display); font-weight: 600; font-size: 18px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.rm-bar__links { display: flex; gap: 4px; margin-left: auto; }
.rm-bar__links button {
  padding: 8px 14px; border-radius: 999px;
  font-size: 13px; font-weight: 600; color: inherit; opacity: .8;
  background: none; border: none; cursor: pointer; transition: opacity .2s, background .2s;
}
.rm-bar__links button:hover { opacity: 1; background: color-mix(in srgb, currentColor 10%, transparent); }
.rm-bar__theme { flex-shrink: 0; }

.rm-icon-btn {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid color-mix(in srgb, currentColor 25%, transparent);
  background: color-mix(in srgb, currentColor 6%, transparent);
  color: inherit; cursor: pointer; font-size: 20px; line-height: 1;
  transition: background .2s;
}
.rm-icon-btn:hover { background: color-mix(in srgb, currentColor 14%, transparent); }

/* ── Hero ────────────────────────────────────────────────── */
.rm-hero {
  position: relative;
  min-height: 92vh;
  display: flex; align-items: flex-end;
  color: #fff;
  overflow: hidden;
}
.rm-hero__media { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.rm-hero__media--empty {
  background:
    radial-gradient(circle at 75% 30%, color-mix(in srgb, var(--accent) 55%, transparent), transparent 55%),
    radial-gradient(circle at 20% 80%, color-mix(in srgb, var(--accent) 25%, transparent), transparent 50%),
    #1a1512;
}
.rm-hero__shade {
  position: absolute; inset: 0;
  background:
    linear-gradient(to top, rgba(12,9,7,.92) 0%, rgba(12,9,7,.35) 45%, rgba(12,9,7,.25) 100%),
    linear-gradient(to right, rgba(12,9,7,.55), transparent 60%);
}
.rm-hero__inner {
  position: relative; z-index: 1;
  width: 100%; max-width: 1240px; margin: 0 auto;
  padding: 140px 32px 64px;
  display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 48px; align-items: end;
}
.rm-hero__pills { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 22px; }
.rm-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 999px;
  font-size: 12px; font-weight: 600; letter-spacing: .02em; text-transform: capitalize;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
  backdrop-filter: blur(8px);
}
.rm-pill--accent { background: var(--accent); border-color: transparent; }
.rm-hero__title {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(3.2rem, 8vw, 7.5rem);
  line-height: .92;
  letter-spacing: -.03em;
  margin: 0 0 22px;
  text-wrap: balance;
}
.rm-hero__desc {
  max-width: 560px; font-size: 16px; line-height: 1.65; color: rgba(255,255,255,.78);
  margin: 0 0 30px;
}
.rm-hero__ctas { display: flex; flex-wrap: wrap; gap: 12px; }

/* Service card */
.rm-service {
  background: rgba(20,16,13,.55);
  border: 1px solid rgba(255,255,255,.14);
  backdrop-filter: blur(18px);
  border-radius: var(--radius);
  padding: 22px;
}
.rm-service__head {
  font-size: 11px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase;
  color: rgba(255,255,255,.5); margin-bottom: 10px;
}
.rm-service__row {
  display: flex; justify-content: space-between; gap: 12px;
  padding: 11px 0; border-bottom: 1px solid rgba(255,255,255,.1);
  font-size: 14px; color: rgba(255,255,255,.75);
}
.rm-service__row span:last-child { font-weight: 700; color: #fff; text-align: right; }
.rm-ok { color: #fff !important; }
.rm-ok::before {
  content: ''; display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: #4ade80; margin-right: 7px; vertical-align: middle;
}
.rm-off { color: rgba(255,255,255,.45) !important; font-weight: 500 !important; }
.rm-service__rating { display: flex; align-items: center; gap: 14px; padding-top: 16px; }
.rm-service__score { font-family: var(--font-display); font-size: 44px; font-weight: 800; line-height: 1; }
.rm-service__reviews { font-size: 12px; color: rgba(255,255,255,.55); }
.rm-stars { display: flex; gap: 2px; margin-bottom: 4px; }

/* ── Buttons ─────────────────────────────────────────────── */
.rm-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 24px; border-radius: 999px;
  font-family: var(--font-body); font-size: 14px; font-weight: 700;
  border: 1px solid transparent; cursor: pointer;
  transition: transform .2s, opacity .2s, background .2s;
}
.rm-btn:hover { transform: translateY(-1px); }
.rm-btn--accent { background: var(--accent); color: #fff; }
.rm-btn--accent:hover { opacity: .9; }
.rm-btn--glass { background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.25); color: #fff; backdrop-filter: blur(8px); }
.rm-btn--ghost { background: transparent; border-color: var(--line); color: var(--fg); }

/* ── Sections ────────────────────────────────────────────── */
.rm-section { padding: 96px 0; scroll-margin-top: var(--bar-h); }
.rm-section + .rm-section { border-top: 1px solid var(--line); }
.rm-heading { margin-bottom: 40px; }
.rm-heading--row { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
.rm-heading__eyebrow {
  display: block; margin-bottom: 10px;
  font-size: 12px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase;
  color: var(--accent);
}
.rm-heading__title {
  font-family: var(--font-display); font-weight: 600;
  font-size: clamp(2.4rem, 5vw, 4rem); line-height: 1; letter-spacing: -.02em;
  margin: 0;
}
.rm-heading__title em { font-style: italic; font-weight: 400; color: var(--accent); }

/* ── Bento (chef) ────────────────────────────────────────── */
.rm-bento {
  display: grid; gap: 16px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: 240px;
}
.rm-bento--1 { grid-template-columns: 1fr; }
.rm-bento--1 .rm-dish--hero { grid-column: auto; }
.rm-bento--2 { grid-template-columns: 2fr 1fr; }
.rm-bento--2 .rm-dish--hero { grid-column: auto; }
.rm-bento--2 .rm-dish:not(.rm-dish--hero) { grid-row: span 2; }
.rm-bento--3 { grid-template-columns: 2fr 1fr; }
.rm-bento--3 .rm-dish--hero { grid-column: auto; }
.rm-dish--hero { grid-column: span 2; grid-row: span 2; }
.rm-bento--4 .rm-dish:last-child { grid-column: span 2; }

.rm-dish {
  position: relative; overflow: hidden; cursor: pointer;
  border-radius: var(--radius);
  background: var(--bg3);
  color: #fff;
  isolation: isolate;
}
.rm-dish__img {
  position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
  transition: transform .7s cubic-bezier(.2,.7,.2,1);
}
.rm-dish:hover .rm-dish__img { transform: scale(1.06); }
.rm-dish__img--empty {
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 80px; font-weight: 800;
  color: color-mix(in srgb, var(--accent) 60%, transparent);
  background: color-mix(in srgb, var(--accent) 14%, var(--bg3));
}
.rm-dish__shade {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(10,8,6,.85) 0%, rgba(10,8,6,.15) 55%, transparent 100%);
}
.rm-dish__body {
  position: absolute; left: 0; right: 0; bottom: 0; z-index: 1;
  padding: 18px 20px;
}
.rm-dish__tag {
  display: inline-block; margin-bottom: 10px;
  padding: 4px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  background: var(--accent);
}
.rm-dish__name {
  font-family: var(--font-display); font-weight: 600; font-size: 20px; line-height: 1.15;
  margin: 0 0 6px;
}
.rm-dish--hero .rm-dish__name { font-size: clamp(1.8rem, 3vw, 2.6rem); }
.rm-dish__desc { font-size: 14px; line-height: 1.55; color: rgba(255,255,255,.75); margin: 0 0 10px; max-width: 460px; }
.rm-dish__foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.rm-dish__price { font-weight: 800; font-size: 15px; }
.rm-dish__add {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: #fff; color: #111; font-size: 20px; font-weight: 600;
  transform: scale(.85); opacity: 0; transition: all .25s;
}
.rm-dish:hover .rm-dish__add { transform: scale(1); opacity: 1; }

/* ── Carta ───────────────────────────────────────────────── */
.rm-heading__sub { margin: 12px 0 0; font-size: 15px; color: var(--fg2); }

.rm-chips__label {
  flex-shrink: 0; align-self: center; padding: 0 4px 0 2px;
  font-size: 10px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase;
  color: var(--fg3);
}
.rm-chips__label:not(:first-child) { margin-left: 10px; }
.rm-chips__sep { flex-shrink: 0; width: 1px; margin: 4px 6px; background: var(--line); }
.rm-chip--outline { background: transparent; border-color: var(--accent); color: var(--accent); }
.rm-chip--outline:hover { background: var(--accent); color: #fff; }

.rm-seccao {
  display: flex; align-items: center; gap: 14px; margin: 8px 0 28px;
  font-size: 12px; font-weight: 800; letter-spacing: .18em; text-transform: uppercase;
  color: var(--accent);
}
.rm-seccao::after { content: ''; flex: 1; height: 2px; background: var(--accent); opacity: .25; }
.rm-group + .rm-group .rm-seccao { margin-top: 32px; }

.rm-chips {
  position: sticky; top: var(--bar-h); z-index: 20;
  display: flex; gap: 8px; overflow-x: auto;
  margin: 0 -32px 36px; padding: 12px 32px;
  background: color-mix(in srgb, var(--bg) 92%, transparent);
  backdrop-filter: blur(12px);
}
.rm-chip {
  display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0;
  padding: 9px 16px; border-radius: 999px;
  font-family: var(--font-body); font-size: 13px; font-weight: 600; text-transform: capitalize;
  background: var(--bg2); color: var(--fg2); border: 1px solid var(--line);
  cursor: pointer; transition: all .2s;
}
.rm-chip:hover { color: var(--fg); }
.rm-chip--active { background: var(--fg); color: var(--bg); border-color: var(--fg); }
.rm-chip__count {
  font-size: 11px; padding: 1px 7px; border-radius: 999px;
  background: color-mix(in srgb, currentColor 14%, transparent);
}

.rm-group { scroll-margin-top: 140px; margin-bottom: 56px; }
.rm-group:last-child { margin-bottom: 0; }
.rm-group__head { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
.rm-group__title {
  font-family: var(--font-display); font-weight: 600; font-style: italic;
  font-size: 28px; margin: 0; text-transform: capitalize; white-space: nowrap;
}
.rm-group__line { flex: 1; height: 1px; background: var(--line); }
.rm-group__count { font-size: 12px; color: var(--fg3); white-space: nowrap; }

.rm-items { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 40px; }
.rm-item {
  display: flex; gap: 18px; align-items: flex-start; text-align: left;
  padding: 16px; margin: 0 -16px; width: calc(100% + 32px);
  border-radius: 18px; background: none; border: none; color: inherit; cursor: pointer;
  font-family: inherit; transition: background .2s;
}
.rm-item:hover { background: var(--bg2); }
.rm-item--out { opacity: .5; }
.rm-item__thumb {
  width: 88px; height: 88px; border-radius: 16px; overflow: hidden; flex-shrink: 0;
  background: color-mix(in srgb, var(--accent) 12%, var(--bg3));
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 30px; font-weight: 800;
  color: color-mix(in srgb, var(--accent) 70%, transparent);
}
.rm-item__thumb img, .rm-item__thumb video { width: 100%; height: 100%; object-fit: cover; }
.rm-item__body { flex: 1; min-width: 0; }
.rm-item__top { display: flex; align-items: baseline; gap: 10px; }
.rm-item__name { font-weight: 700; font-size: 16px; line-height: 1.3; }
.rm-item__dots { flex: 1; min-width: 20px; border-bottom: 2px dotted var(--line); transform: translateY(-4px); }
.rm-item__price { font-family: var(--font-display); font-weight: 600; font-size: 17px; color: var(--accent); white-space: nowrap; }
.rm-item__fav { align-self: center; margin: -6px -6px -6px 0; }
.rm-item__desc {
  margin: 6px 0 0; font-size: 13.5px; line-height: 1.55; color: var(--fg2);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.rm-item__tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.rm-item__tags:empty { display: none; }
.rm-tag {
  padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 600;
  background: var(--bg3); color: var(--fg2);
}
.rm-tag--accent { background: color-mix(in srgb, var(--accent) 16%, transparent); color: var(--accent); }
.rm-tag--out { background: var(--fg); color: var(--bg); }

.rm-menu-skeleton { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 40px; }
.rm-skel { height: 104px; border-radius: 18px; background: var(--bg2); animation: rmPulse 1.4s ease-in-out infinite; }
.rm-dish.rm-skel { height: auto; min-height: 200px; cursor: default; }
.rm-mais {
  margin-top: 14px; padding: 10px 20px; border-radius: 999px; cursor: pointer;
  background: transparent; border: 2px solid var(--line); color: var(--fg);
  font-family: var(--font-body); font-size: 14px; font-weight: 700; transition: border-color .2s, color .2s;
}
.rm-mais:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.rm-mais:disabled { opacity: .6; cursor: default; }
@keyframes rmPulse { 50% { opacity: .5; } }
.rm-empty { padding: 60px 0; text-align: center; color: var(--fg3); font-family: var(--font-display); font-style: italic; font-size: 20px; }

/* ── Catálogo (ProductCatalog adaptado aos tokens do template) ── */
.rm-catalog :deep(.bg-zinc-900),
.rm-catalog :deep(.bg-white) { background: var(--bg2) !important; }
.rm-catalog :deep(.bg-zinc-800),
.rm-catalog :deep(.bg-gray-50),
.rm-catalog :deep(.bg-gray-100),
.rm-catalog :deep(.bg-zinc-700),
.rm-catalog :deep(.bg-gray-200) { background: var(--bg3) !important; }
.rm-catalog :deep(.border-zinc-800),
.rm-catalog :deep(.border-zinc-700),
.rm-catalog :deep(.border-gray-200),
.rm-catalog :deep(.border-gray-300) { border-color: var(--line) !important; }
.rm-catalog :deep(.text-zinc-100),
.rm-catalog :deep(.text-zinc-900) { color: var(--fg) !important; }
.rm-catalog :deep(input),
.rm-catalog :deep(select) { color: var(--fg) !important; font-family: var(--font-body); }
.rm-catalog :deep(input::placeholder) { color: var(--fg3) !important; }

.rm-catalog :deep(.rm-input-focus:focus),
.rm-catalog :deep(input:focus),
.rm-catalog :deep(select:focus) { border-color: var(--accent) !important; outline: none; }
.rm-catalog :deep(.rm-cat-tab) {
  background: var(--bg2); color: var(--fg2); border: 1px solid var(--line);
  font-weight: 600; text-transform: capitalize;
}
.rm-catalog :deep(.rm-cat-tab:hover) { color: var(--fg); }
.rm-catalog :deep(.rm-cat-tab--active) {
  background: var(--fg) !important; color: var(--bg) !important; border: 1px solid var(--fg);
  font-weight: 700; text-transform: capitalize;
}
.rm-catalog :deep(.rm-cat-border) { border-color: color-mix(in srgb, var(--accent) 40%, transparent) !important; }
.rm-catalog :deep(.rm-cat-name) { font-family: var(--font-body); font-weight: 700; }
.rm-catalog :deep(.rm-cat-price) { font-family: var(--font-display); font-weight: 600; color: var(--accent) !important; }
.rm-catalog :deep(.rm-cat-badge) {
  background: var(--accent) !important; color: #fff !important; border-radius: 999px !important;
  font-weight: 700; letter-spacing: .04em;
}
.rm-catalog :deep(.rm-cat-indicator) { background: color-mix(in srgb, var(--accent) 16%, transparent) !important; color: var(--accent) !important; }
.rm-catalog :deep(.rm-cat-clear) { background: color-mix(in srgb, var(--accent) 12%, transparent) !important; color: var(--accent) !important; }
.rm-catalog :deep(.rm-cat-clear-all) { color: var(--accent) !important; }
.rm-catalog :deep(.rm-cat-spinner) { color: var(--accent) !important; }

/* ── Visite-nos ──────────────────────────────────────────── */
.rm-section--visite { background: var(--bg2); }
.rm-visite { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 72px; align-items: start; }
.rm-visite__quote blockquote {
  margin: 0; font-family: var(--font-display); font-style: italic; font-weight: 400;
  font-size: clamp(1.6rem, 3vw, 2.4rem); line-height: 1.3; letter-spacing: -.01em;
}
.rm-visite__sign { margin-top: 22px; font-weight: 700; color: var(--fg2); }
.rm-visite__info { display: flex; flex-direction: column; gap: 28px; }
.rm-info-block__label {
  font-size: 11px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase;
  color: var(--fg3); margin-bottom: 10px;
}
.rm-info-block__value { font-size: 17px; font-weight: 600; }
.rm-info-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--line); font-size: 15px; }
.rm-info-row:last-child { border-bottom: none; }
.rm-info-row__val { font-weight: 700; color: var(--accent); }
.rm-pay { display: flex; flex-wrap: wrap; gap: 8px; }
.rm-pay__chip {
  padding: 7px 14px; border-radius: 999px; font-size: 13px; font-weight: 600; text-transform: capitalize;
  background: var(--bg); border: 1px solid var(--line);
}
.rm-visite__cta { align-self: flex-start; }

/* ── Reviews (classes passadas ao AvaliacaoLoja) ─────────── */
.rm-service .rm-star--off { color: rgba(255,255,255,.25) !important; }
:deep(.rm-star--on) { color: var(--accent) !important; }
:deep(.rm-star--off) { color: var(--line) !important; }
:deep(.rm-progress) { background: var(--accent) !important; }
:deep(.rm-review-card) { background: var(--bg2) !important; border: 1px solid var(--line) !important; }
:deep(.rm-review-own) { border: 1px solid var(--accent) !important; }
:deep(.rm-btn) {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 22px; border-radius: 999px; font-weight: 700; cursor: pointer;
}
:deep(.rm-btn--accent) { background: var(--accent) !important; color: #fff !important; }
:deep(.rm-btn--ghost) { background: transparent; border: 1px solid var(--line); color: var(--fg); }

/* ── Footer ──────────────────────────────────────────────── */
.rm-footer { padding: 72px 0 36px; border-top: 1px solid var(--line); }
.rm-footer__name {
  font-family: var(--font-display); font-weight: 800;
  font-size: clamp(3rem, 10vw, 8rem); line-height: .9; letter-spacing: -.04em;
  color: color-mix(in srgb, var(--fg) 12%, transparent);
  margin-bottom: 32px; word-break: break-word;
}
.rm-footer__row { display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; }
.rm-footer__copy { font-size: 13px; color: var(--fg3); }
.rm-footer__links { display: flex; gap: 22px; }
.rm-footer__links button {
  background: none; border: none; cursor: pointer; font-family: inherit;
  font-size: 13px; font-weight: 600; color: var(--fg2);
}
.rm-footer__links button:hover { color: var(--accent); }

/* ── Modal ───────────────────────────────────────────────── */
.rm-modal-overlay {
  position: fixed; inset: 0; z-index: 60;
  display: flex; align-items: center; justify-content: center; padding: 16px;
  background: rgba(0,0,0,.6); backdrop-filter: blur(6px);
}
.rm-modal {
  width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto;
  background: var(--bg); color: var(--fg);
  border: 1px solid var(--line); border-radius: var(--radius);
}
.rm-modal__head {
  position: sticky; top: 0; background: var(--bg);
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 22px; border-bottom: 1px solid var(--line);
}
.rm-modal__head h3 { margin: 0; font-family: var(--font-display); font-size: 22px; font-weight: 600; }
.rm-modal__body { padding: 22px; font-size: 14px; line-height: 1.7; color: var(--fg2); white-space: pre-wrap; }

.rm-notfound {
  min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px;
  font-family: var(--font-display); font-size: 28px;
}

.hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.hide-scroll::-webkit-scrollbar { display: none; }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .rm-bar__links { display: none; }
  .rm-bar__theme { margin-left: auto; }
  .rm-hero__inner { grid-template-columns: 1fr; gap: 28px; }
  .rm-service { max-width: 420px; }
  .rm-bento { grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: 220px; }
  .rm-bento--1 { grid-template-columns: 1fr; }
  .rm-items, .rm-menu-skeleton { grid-template-columns: 1fr; }
  .rm-visite { grid-template-columns: 1fr; gap: 40px; }
}

@media (max-width: 640px) {
  .rm-wrap { padding: 0 16px; }
  .rm-root { --bar-h: 60px; --bar-pad: 14px; }
  .rm-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 10px); gap: 10px; }
  .rm-bar__name { font-size: 15px; }
  .rm-hero { min-height: 88vh; }
  .rm-hero__inner { padding: 110px 16px 36px; }
  .rm-hero__desc { font-size: 14px; }
  .rm-service { padding: 16px; }
  .rm-service__score { font-size: 36px; }
  .rm-section { padding: 64px 0; }
  .rm-heading { margin-bottom: 28px; }
  .rm-chips { margin: 0 -16px 28px; padding: 10px 16px; }
  .rm-bento { grid-template-columns: 1fr 1fr; grid-auto-rows: 180px; gap: 10px; }
  .rm-bento--1, .rm-bento--2, .rm-bento--3 { grid-template-columns: 1fr 1fr; }
  .rm-bento--2 .rm-dish:not(.rm-dish--hero) { grid-row: auto; grid-column: span 2; }
  .rm-bento--3 .rm-dish--hero, .rm-bento--1 .rm-dish--hero { grid-column: span 2; }
  .rm-dish__body { padding: 14px; }
  .rm-dish__name { font-size: 16px; }
  .rm-dish__add { opacity: 1; transform: scale(.85); }
  .rm-item { padding: 12px; margin: 0 -12px; width: calc(100% + 24px); gap: 14px; }
  .rm-item__thumb { width: 72px; height: 72px; border-radius: 14px; }
  .rm-item__name { font-size: 15px; }
  .rm-item__dots { display: none; }
  .rm-item__top { justify-content: space-between; }
  .rm-group__title { font-size: 24px; }
  .rm-group__count { display: none; }
  .rm-footer { padding: 56px 0 28px; }
}
</style>
