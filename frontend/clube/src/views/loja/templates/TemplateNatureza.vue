<!-- TemplateNatureza.vue — Revamp "mercado da horta"
     Orgânico e calmo: banner em forma orgânica com selo circular a rodar ·
     "Da época" num carrossel (scroll infinito) · "Bancas" por tipo e por categoria —
     cada banca tem uma placa e uma fila horizontal com scroll infinito, como o ProductSlider ·
     etiquetas de papel kraft · catálogo completo · informação em cartões-folha · avaliações.
     Produtos sempre paginados pelo servidor (ProdutosPaginados / FimDaLista).
     Tipografia: Young Serif + Figtree. Acento: --cor-primaria. Fundo escuro: --cor-secundaria.
     Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="nt-root" :class="isDark ? 'nt-dark' : 'nt-light'" :style="cssVars">
    <ProductInfoCard
      :produto="selectedProduct"
      :loja="loja"
      :isDark="isDark"
      @close="selectedProduct = null"
      @added-to-cart="({ loja }) => $refs.cart.openForLoja(loja)"
    />

    <MultiCart ref="cart" :isDark="isDark" />

    <Profile :data="user" :isDark="isDark" class="z-40" @log_out="logOut()" />

    <!-- Loading -->
    <div v-if="loading" class="nt-loading">
      <span class="nt-loading__semente"></span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="nt-bar" :class="{ 'nt-bar--solida': scrolled }">
        <button class="nt-redondo" @click="$router.back()" aria-label="Voltar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="nt-redondo" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="nt-bar__nome" :class="{ 'nt-bar__nome--on': scrolled }">{{ loja.nome }}</span>
      </header>

      <!-- ══ HERO ══ -->
      <section class="nt-wrap nt-hero">
        <div class="nt-hero__texto">
          <p class="nt-etiqueta">{{ loja.categoria || 'Produtos naturais' }}</p>
          <h1 class="nt-hero__nome">{{ loja.nome }}</h1>
          <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />
          <EstadoLoja :horario="loja.horario" :loja-id="lojaId" class="loja-estado" />
          <p v-if="loja.descricao" class="nt-hero__desc">{{ truncate(loja.descricao, 200) }}</p>

          <ul class="nt-hero__dados">
            <li v-if="loja.rating_medio">
              <svg width="15" height="15" viewBox="0 0 20 20" fill="currentColor"><path d="M9.05 2.93c.3-.92 1.6-.92 1.9 0l1.07 3.29a1 1 0 0 0 .95.69h3.46c.97 0 1.37 1.24.59 1.81l-2.8 2.03a1 1 0 0 0-.36 1.12l1.07 3.3c.3.91-.76 1.68-1.54 1.11l-2.8-2.03a1 1 0 0 0-1.18 0l-2.8 2.03c-.78.57-1.84-.2-1.54-1.12l1.07-3.29a1 1 0 0 0-.36-1.12L2.98 8.72c-.78-.57-.38-1.81.59-1.81h3.46a1 1 0 0 0 .95-.69z"/></svg>
              <span><b>{{ rating }}</b> · {{ loja.total_avaliacoes || 0 }} avaliações</span>
            </li>
            <li>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/></svg>
              <span>{{ textoEntrega }}</span>
            </li>
            <li v-if="loja.localizacao">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              <span>{{ loja.localizacao }}</span>
            </li>
          </ul>

          <div class="nt-hero__ctas">
            <button class="nt-btn nt-btn--cheio" @click="scrollToId(soServicos ? 'servicos' : totalDestaques ? 'nt-epoca' : 'nt-bancas')">
              {{ soServicos ? 'Ver serviços' : totalDestaques ? 'Ver o que é da época' : 'Ver produtos' }}
            </button>
            <button v-if="!soServicos" class="nt-btn" @click="scrollToId('nt-catalogo')">Catálogo</button>
          </div>
        </div>

        <div class="nt-hero__media">
          <div class="nt-forma">
            <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" v-video-visivel="'destaque'" muted loop playsinline></video>
            <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
            <div v-else class="nt-forma__vazio">{{ loja.nome.charAt(0) }}</div>
          </div>
          <svg class="nt-selo" viewBox="0 0 120 120" aria-hidden="true">
            <defs>
              <path id="nt-circulo" d="M60,60 m-44,0 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0" />
            </defs>
            <circle cx="60" cy="60" r="58" class="nt-selo__fundo" />
            <text class="nt-selo__texto">
              <textPath href="#nt-circulo" textLength="272" lengthAdjust="spacing">{{ textoSelo }}</textPath>
            </text>
            <text x="60" y="66" text-anchor="middle" class="nt-selo__num">{{ soServicos ? totalServicos : (totalProdutos ?? '') }}</text>
          </svg>
        </div>
      </section>

      <main class="nt-wrap">
        <!-- ══ DA ÉPOCA (destaques, scroll infinito) ══ -->
        <section v-if="totalDestaques" id="nt-epoca" class="nt-sec">
          <header class="nt-sec__head">
            <div>
              <p class="nt-etiqueta">Escolhidos a dedo</p>
              <h2 class="nt-sec__titulo">Da época</h2>
            </div>
            <div class="nt-setas">
              <button class="nt-redondo" @click="deslizar($event, -1)" aria-label="Anterior">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button class="nt-redondo" @click="deslizar($event, 1)" aria-label="Seguinte">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
              </button>
            </div>
          </header>

          <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="8" :lazy="false" v-slot="l">
            <div class="nt-fila nt-fila--epoca nt-hide-scroll">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="nt-skel nt-skel--grande"></div>
              </template>
              <button v-for="p in l.itens" :key="p.id" class="nt-cesto nt-cesto--grande" @click="selectedProduct = p">
                <span class="nt-cesto__foto">
                  <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="$miniatura(p.ficheiro_poster_url)" muted loop v-video-visivel="'cartao'" playsinline></video>
                  <img v-img v-else-if="p.ficheiro_url" :src="$miniatura(p.ficheiro_url)" :alt="p.nome" loading="lazy" />
                  <span v-else class="nt-cesto__inicial">{{ p.nome.charAt(0) }}</span>
                  <span v-if="esgotado(p)" class="nt-cesto__esgotado">Esgotado</span>
                </span>
                <span class="nt-kraft">
                  <span class="nt-kraft__nome">{{ p.nome }}</span>
                  <span class="nt-kraft__preco">{{ precoDe(p) }}</span>
                </span>
                <span v-if="p.descricao" class="nt-cesto__desc">{{ truncate(p.descricao, 90) }}</span>
              </button>
              <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                <div class="nt-skel nt-skel--grande"></div>
              </FimDaLista>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ BANCAS (por tipo / por categoria; filas com scroll infinito) ══ -->
        <section v-if="grupos.length" id="nt-bancas" class="nt-sec">
          <header class="nt-sec__head">
            <div>
              <p class="nt-etiqueta">Percorra o mercado</p>
              <h2 class="nt-sec__titulo">As bancas</h2>
            </div>
          </header>

          <nav class="nt-indice nt-hide-scroll">
            <button v-for="g in grupos" :key="g.key" @click="scrollToId('nt-g-' + g.key)">{{ g.nome }}</button>
          </nav>

          <template v-for="(g, i) in grupos" :key="g.key">
            <p v-if="i === 0 || grupos[i - 1].seccao !== g.seccao" class="nt-divisor">
              <span>{{ SECCOES[g.seccao] }}</span>
            </p>

            <div :id="'nt-g-' + g.key" class="nt-banca">
              <div class="nt-placa" :class="'nt-placa--' + (i % 3)">
                <span class="nt-placa__seccao">{{ SECCOES[g.seccao] }}</span>
                <h3 class="nt-placa__nome">{{ g.nome }}</h3>
                <span class="nt-placa__n">{{ g.total }} {{ g.total === 1 ? 'produto' : 'produtos' }}</span>
                <div class="nt-placa__setas">
                  <button class="nt-redondo nt-redondo--placa" @click="deslizar($event, -1)" aria-label="Anterior">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
                  </button>
                  <button class="nt-redondo nt-redondo--placa" @click="deslizar($event, 1)" aria-label="Seguinte">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
                  </button>
                </div>
              </div>

              <ProdutosPaginados :params="g.params" :limit="8" class="nt-banca__lista" v-slot="l">
                <div class="nt-fila nt-hide-scroll">
                  <template v-if="l.carregando">
                    <div v-for="n in Math.min(g.total, 4)" :key="n" class="nt-skel"></div>
                  </template>
                  <button v-for="p in l.itens" :key="p.id" class="nt-cesto" @click="selectedProduct = p">
                    <span class="nt-cesto__foto">
                      <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                      <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="$miniatura(p.ficheiro_poster_url)" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                      <img v-img v-else-if="p.ficheiro_url" :src="$miniatura(p.ficheiro_url)" :alt="p.nome" loading="lazy" />
                      <span v-else class="nt-cesto__inicial">{{ p.nome.charAt(0) }}</span>
                      <span v-if="esgotado(p)" class="nt-cesto__esgotado">Esgotado</span>
                    </span>
                    <span class="nt-kraft">
                      <span class="nt-kraft__nome">{{ p.nome }}</span>
                      <span class="nt-kraft__preco">{{ precoDe(p) }}</span>
                    </span>
                  </button>
                  <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                    <div class="nt-skel"></div>
                  </FimDaLista>
                </div>
              </ProdutosPaginados>
            </div>
          </template>
        </section>

        <!-- ══ SERVIÇOS ══ -->
        <SeccaoServicos :loja-id="lojaId" :isDark="isDark" :cor="tema?.corPrimaria || '#dc2626'" class="nt-sec" />

        <!-- ══ CATÁLOGO ══ -->
        <section v-if="!soServicos" id="nt-catalogo" class="nt-sec">
          <header class="nt-sec__head">
            <div>
              <p class="nt-etiqueta">Pesquisa e filtros</p>
              <h2 class="nt-sec__titulo">Catálogo completo</h2>
            </div>
          </header>
          <div class="nt-catalogo">
            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="210px"
              card-border-radius="rounded-3xl"
              skeleton-class="rounded-3xl"
              hover-effect="transition-transform duration-300 hover:-translate-y-1"
              hover-border-class=""
              filter-container-radius="rounded-3xl"
              input-border-radius="rounded-full"
              input-focus-class="nt-foco"
              tab-border-radius="rounded-full"
              active-tab-class="nt-tab--on"
              inactive-tab-dark-class="nt-tab"
              inactive-tab-light-class="nt-tab"
              active-sub-tab-class="nt-tab--on"
              inactive-sub-tab-dark-class="nt-tab"
              inactive-sub-tab-light-class="nt-tab"
              category-border-class="nt-cat-borda"
              product-name-class="nt-cat-nome"
              product-name-hover-class=""
              price-class="nt-cat-preco"
              badge-text="Da época"
              badge-class="nt-cat-badge"
              indicator-active-class="nt-cat-indicador"
              clear-filter-class="nt-cat-limpar"
              clear-all-class="nt-cat-limpar"
              spinner-class="nt-cat-spinner"
              :show-stock="false"
              :show-category-badges="false"
              empty-text="Nenhum produto encontrado."
              @product-click="selectedProduct = $event"
            />
          </div>
        </section>

        <!-- ══ INFORMAÇÃO ══ -->
        <section id="nt-info" class="nt-sec">
          <header class="nt-sec__head">
            <div>
              <p class="nt-etiqueta">Do campo à sua porta</p>
              <h2 class="nt-sec__titulo">Como funciona</h2>
            </div>
          </header>
          <div class="nt-info">
            <div class="nt-folha">
              <p class="nt-folha__titulo">Entrega</p>
              <ul v-if="opcoesEntrega.length || loja.levantamento_ativo">
                <li v-for="o in opcoesEntrega" :key="o.id">
                  <span>{{ o.nome }}</span><b>{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</b>
                </li>
                <li v-if="loja.levantamento_ativo"><span>Levantamento</span><b>Grátis</b></li>
              </ul>
              <p v-else>Fale connosco.</p>
            </div>
            <div class="nt-folha nt-folha--b">
              <p class="nt-folha__titulo">Pagamento</p>
              <div v-if="metodosPagamento.length" class="nt-folha__tags">
                <span v-for="m in metodosPagamento" :key="m.id">{{ m.nome }}</span>
              </div>
              <p v-else>—</p>
            </div>
            <div class="nt-folha nt-folha--c">
              <p class="nt-folha__titulo">Onde estamos</p>
              <p v-if="loja.localizacao">{{ loja.localizacao }}</p>
              <p v-else>Loja online.</p>
            </div>
          </div>
        </section>

        <!-- ══ AVALIAÇÕES ══ -->
        <section id="nt-avaliacoes" class="nt-sec">
          <header class="nt-sec__head">
            <div>
              <p class="nt-etiqueta">Quem já provou</p>
              <h2 class="nt-sec__titulo">Avaliações</h2>
            </div>
          </header>
          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-3xl"
            form-border-radius="rounded-3xl"
            review-card-border-radius="rounded-3xl"
            button-border-radius="rounded-full"
            textarea-border-radius="rounded-2xl"
            :star-active-class="'nt-estrela--on'"
            :star-inactive-class="'nt-estrela--off'"
            progress-bar-class="nt-barra"
            :submit-button-class="'nt-btn nt-btn--cheio w-full justify-center'"
            :review-card-class="'nt-review'"
            :own-review-border-class="'nt-review--minha'"
            :load-more-button-class="'nt-btn'"
            @rating-updated="onRatingUpdated"
          />
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="nt-footer">
        <div class="nt-wrap nt-footer__inner">
          <p class="nt-footer__nome">{{ loja.nome }}</p>
          <p v-if="loja.localizacao" class="nt-footer__morada">{{ loja.localizacao }}</p>
          <nav class="nt-footer__links">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
          </nav>
          <p class="nt-footer__copy">© {{ ano }} {{ loja.nome }}</p>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="nt-modal" @click.self="modalPolitica = null">
        <div class="nt-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="nt-redondo" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="nt-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="nt-vazio">
      <p>Loja não encontrada</p>
      <button class="nt-btn nt-btn--cheio" @click="$router.back()">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import SeccaoServicos from '@/components/servicos/loja/SeccaoServicos.vue'
import BotaoFavorito from '@/components/favoritos/BotaoFavorito.vue'
import EstadoLoja from '@/components/horario/EstadoLoja.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'
import ProdutosPaginados from '@/components/produtos/ProdutosPaginados.vue'
import FimDaLista from '@/components/produtos/FimDaLista.vue'

const SECCOES = { tipo: 'Por tipo', categoria: 'Por categoria', todos: 'Tudo' }

export default {
  name: 'TemplateNatureza',

  components: { SeccaoServicos, ProductInfoCard, BotaoFavorito, EstadoLoja, MultiCart, Profile, ProductCatalog, AvaliacaoLoja, ProdutosPaginados, FimDaLista },

  emits: ['toggle-dark'],

  props: {
    tema: { type: Object, default: () => ({}) },
  },

  setup (props, { emit }) {
    const lojaData = useLojaData()
    const isDark = ref(props.tema?.darkMode === true)
    watch(() => props.tema?.darkMode, v => { if (v !== undefined) isDark.value = v === true })

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
    const ano = new Date().getFullYear()
    const scrolled = ref(false)

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#4f7d3a',
      '--cor-secundaria': props.tema?.corSecundaria || '#1b261d',
    }))

    // Bancas: por tipo, depois por categoria — só metadados; cada fila pede página a página
    const grupos = lojaData.gruposProdutos

    // ── Texto ────────────────────────────────────────────────
    const rating = computed(() => {
      const r = lojaData.loja.value?.rating_medio
      return r ? Number(r).toFixed(1) : '—'
    })

    const textoEntrega = computed(() => {
      const precos = lojaData.opcoesEntrega.value.map(o => Number(o.preco))
      if (precos.length) {
        const min = Math.min(...precos)
        return min === 0 ? 'Entrega grátis' : `Entrega desde ${lojaData.formatPrice(min)}`
      }
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento no local' : 'Consulte a entrega'
    })

    // texto que corre à volta do selo
    const textoSelo = computed(() => {
      const l = lojaData.loja.value
      const partes = ['fresco', l?.localizacao || 'local', 'da época']
      return partes.join(' · ').toLowerCase() + ' · '
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

    // ── Helpers ──────────────────────────────────────────────
    function toggleDark () {
      isDark.value = !isDark.value
      emit('toggle-dark', isDark.value)
    }

    function isVideo (url) { return /\.(mp4|webm|mov|mkv)(\?|$)/i.test(url || '') }

    function truncate (txt, n) {
      if (!txt) return ''
      return txt.length > n ? txt.slice(0, n).trimEnd() + '…' : txt
    }

    function esgotado (p) { return !!p.stock && Number(p.stock.quantidade) <= 0 }

    function precoDe (p) {
      const precos = (p.variantes || []).filter(v => v.quantidade > 0).map(v => Number(v.preco_efetivo))
      if (precos.length && Math.min(...precos) !== Math.max(...precos)) {
        return `desde ${lojaData.formatPrice(Math.min(...precos))}`
      }
      return lojaData.formatPrice(p.preco)
    }

    // setas: deslizam a fila da mesma secção/banca
    function deslizar (evento, dir) {
      const fila = evento.currentTarget.closest('.nt-sec, .nt-banca')?.querySelector('.nt-fila')
      if (fila) fila.scrollBy({ left: dir * fila.clientWidth * 0.8, behavior: 'smooth' })
    }

    function onScroll () { scrolled.value = window.scrollY > 40 }

    onMounted(() => {
      window.addEventListener('scroll', onScroll, { passive: true })
      onScroll()
    })
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return {
      ...lojaData,
      SECCOES,
      isDark, user, ano, cssVars, scrolled,
      grupos,
      rating, textoEntrega, textoSelo, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, precoDe, deslizar,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Young+Serif&family=Figtree:wght@400;500;600;700&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.nt-root {
  --cor: var(--cor-primaria, #4f7d3a);
  --serif: 'Young Serif', Georgia, serif;
  --sans: 'Figtree', system-ui, sans-serif;
  --raio: 28px;
  --bar-h: 68px;
  --bar-pad: 28px;
  /* carrinho · notificações · perfil alinhados com a barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--sans);
  background: var(--bg);
  color: var(--fg);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .4s, color .4s;
}
.nt-light {
  --bg: #f5f1e6;
  --papel: #fffdf7;
  --fg: #23291f;
  --fg2: #66705c;
  --linha: rgba(35, 41, 31, .12);
  --kraft: #e3cfa8;
  --kraft-fg: #4a3a1e;
  --tom-a: color-mix(in srgb, var(--cor) 16%, #f5f1e6);
  --tom-b: color-mix(in srgb, #c98a3c 22%, #f5f1e6);
  --tom-c: color-mix(in srgb, var(--cor) 32%, #f5f1e6);
  --acento: var(--cor);
}
.nt-dark {
  --bg: var(--cor-secundaria, #1b261d);
  --papel: color-mix(in srgb, var(--bg) 88%, #fff 12%);
  --fg: #eef0e6;
  --fg2: #a9b29d;
  --linha: rgba(238, 240, 230, .12);
  --kraft: #b89c6c;
  --kraft-fg: #2b2213;
  --tom-a: color-mix(in srgb, var(--cor) 22%, var(--bg));
  --tom-b: color-mix(in srgb, #c98a3c 22%, var(--bg));
  --tom-c: color-mix(in srgb, var(--cor) 36%, var(--bg));
  /* acento legível sobre fundo escuro */
  --acento: color-mix(in srgb, var(--cor) 60%, #fff 40%);
}

.nt-wrap { max-width: 1280px; margin: 0 auto; padding: 0 var(--bar-pad); }
.nt-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.nt-hide-scroll::-webkit-scrollbar { display: none; }

.nt-etiqueta { margin: 0; font-size: 13px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--acento); }

/* ── Loading ─────────────────────────────────────────────── */
.nt-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; align-items: center; justify-content: center; }
.nt-loading__semente { width: 22px; height: 34px; border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%; background: var(--cor); animation: ntBrota 1.1s ease-in-out infinite alternate; }
@keyframes ntBrota { from { transform: scale(.7) rotate(-12deg); opacity: .5; } to { transform: scale(1) rotate(12deg); opacity: 1; } }

/* ── Barra ───────────────────────────────────────────────── */
.nt-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center; gap: 8px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 12px) 0 var(--bar-pad);
  transition: background .3s, box-shadow .3s;
}
.nt-bar--solida { background: color-mix(in srgb, var(--bg) 90%, transparent); backdrop-filter: blur(10px); box-shadow: 0 1px 0 var(--linha); }
.nt-redondo {
  width: 38px; height: 38px; flex-shrink: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--papel); color: var(--fg); border: 1px solid var(--linha); cursor: pointer;
  transition: background .2s, color .2s, border-color .2s;
}
.nt-redondo:hover { background: var(--cor); border-color: var(--cor); color: #fff; }
.nt-bar__nome {
  margin-left: 8px; min-width: 0; font-family: var(--serif); font-size: 19px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  opacity: 0; transform: translateY(4px); transition: opacity .3s, transform .3s;
}
.nt-bar__nome--on { opacity: 1; transform: none; }

/* ── Hero ────────────────────────────────────────────────── */
.nt-hero {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 56px; align-items: center;
  padding-top: calc(var(--bar-h) + 32px); padding-bottom: 24px;
}
.nt-hero__nome { margin: 16px 0 20px; font-family: var(--serif); font-weight: 400; font-size: clamp(2.8rem, 6.5vw, 5.6rem); line-height: 1; letter-spacing: -.02em; text-wrap: balance; }
.nt-hero__desc { margin: 0 0 26px; max-width: 500px; font-size: 18px; line-height: 1.65; color: var(--fg2); }
.nt-hero__dados { list-style: none; margin: 0 0 30px; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.nt-hero__dados li { display: flex; align-items: center; gap: 10px; font-size: 15px; }
.nt-hero__dados svg { flex-shrink: 0; color: var(--acento); }
.nt-hero__ctas { display: flex; flex-wrap: wrap; gap: 10px; }

.nt-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 14px 24px; border-radius: 999px;
  font: inherit; font-size: 15px; font-weight: 600; cursor: pointer;
  background: transparent; color: var(--fg); border: 1.5px solid var(--fg);
  transition: background .2s, color .2s, border-color .2s, transform .2s;
}
.nt-btn:hover { transform: translateY(-1px); border-color: var(--acento); color: var(--acento); }
.nt-btn--cheio { background: var(--cor); border-color: var(--cor); color: #fff; }
.nt-btn--cheio:hover { color: #fff; background: color-mix(in srgb, var(--cor) 85%, #000); border-color: transparent; }

.nt-hero__media { position: relative; }
.nt-forma {
  aspect-ratio: 1; width: 100%; overflow: hidden; background: var(--tom-a);
  border-radius: 58% 42% 52% 48% / 46% 54% 46% 54%;     /* forma orgânica */
  animation: ntRespira 14s ease-in-out infinite alternate;
}
@keyframes ntRespira {
  to { border-radius: 44% 56% 42% 58% / 56% 44% 58% 42%; }
}
.nt-forma img, .nt-forma video { width: 100%; height: 100%; object-fit: cover; display: block; }
.nt-forma__vazio { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-family: var(--serif); font-size: 160px; color: var(--acento); }
.nt-selo { position: absolute; left: -2%; bottom: 4%; width: 132px; height: 132px; }
.nt-selo__fundo { fill: var(--papel); stroke: var(--linha); }
.nt-selo__texto { fill: var(--fg); font-family: var(--sans); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
.nt-selo__texto { transform-origin: 60px 60px; transform-box: view-box; animation: ntRoda 24s linear infinite; }
.nt-selo__num { fill: var(--acento); font-family: var(--serif); font-size: 22px; }
@keyframes ntRoda { to { transform: rotate(360deg); } }

/* ── Secções ─────────────────────────────────────────────── */
.nt-sec { padding-top: 88px; scroll-margin-top: calc(var(--bar-h) + 8px); }
.nt-sec__head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }
.nt-sec__titulo { margin: 8px 0 0; font-family: var(--serif); font-weight: 400; font-size: clamp(2.2rem, 4.5vw, 3.4rem); line-height: 1; }
.nt-setas { display: flex; gap: 8px; }

/* ── Filas e cestos ──────────────────────────────────────── */
.nt-fila {
  display: grid; grid-auto-flow: column; grid-auto-columns: 220px; gap: 18px;
  overflow-x: auto; scroll-snap-type: x mandatory; padding: 4px 2px 8px;
}
.nt-fila > * { scroll-snap-align: start; }
.nt-fila--epoca { grid-auto-columns: calc((100% - 3 * 18px) / 4); }

.nt-cesto {
  display: flex; flex-direction: column; gap: 10px; padding: 0; min-width: 0; text-align: left;
  background: none; border: none; cursor: pointer; color: inherit; font: inherit;
}
.nt-cesto__foto {
  position: relative; display: block; aspect-ratio: 1; border-radius: var(--raio); overflow: hidden; background: var(--tom-a);
  transition: border-radius .5s cubic-bezier(.2,.8,.2,1);
}
.nt-cesto--grande .nt-cesto__foto { aspect-ratio: 4 / 5; }
.nt-cesto:hover .nt-cesto__foto { border-radius: 46% 54% 40% 60% / 40% 44% 56% 60%; }
.nt-cesto__foto img, .nt-cesto__foto video { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .6s; }
.nt-cesto:hover .nt-cesto__foto img { transform: scale(1.05); }
.nt-cesto__inicial { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-family: var(--serif); font-size: 64px; color: var(--acento); }
.nt-cesto__esgotado {
  position: absolute; left: 12px; top: 12px; padding: 5px 12px; border-radius: 999px;
  background: var(--papel); color: var(--fg); font-size: 12px; font-weight: 600;
}
.nt-cesto__desc { padding: 0 4px; font-size: 14px; line-height: 1.5; color: var(--fg2); }

/* etiqueta de papel kraft com picotado */
.nt-kraft {
  position: relative; display: flex; justify-content: space-between; align-items: baseline; gap: 10px;
  padding: 10px 14px; border-radius: 6px 6px 14px 14px;
  background: var(--kraft); color: var(--kraft-fg);
  border-top: 2px dashed color-mix(in srgb, var(--kraft-fg) 25%, transparent);
  transform: rotate(-.6deg);
}
.nt-cesto:nth-child(even) .nt-kraft { transform: rotate(.6deg); }
.nt-kraft__nome { font-weight: 600; font-size: 15px; line-height: 1.25; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nt-kraft__preco { flex-shrink: 0; font-family: var(--serif); font-size: 16px; }

.nt-skel { aspect-ratio: 1; border-radius: var(--raio); background: var(--tom-a); animation: ntPulso 1.3s ease-in-out infinite; }
.nt-skel--grande { aspect-ratio: 4 / 5; }
@keyframes ntPulso { 50% { opacity: .5; } }

/* ── Bancas ──────────────────────────────────────────────── */
.nt-indice { display: flex; gap: 8px; overflow-x: auto; margin-bottom: 8px; padding: 2px; }
.nt-indice button {
  flex-shrink: 0; padding: 9px 16px; border-radius: 999px; border: 1px solid var(--linha); background: var(--papel);
  color: var(--fg); cursor: pointer; font: inherit; font-size: 14px; font-weight: 500; text-transform: capitalize;
  transition: border-color .2s, color .2s;
}
.nt-indice button:hover { border-color: var(--acento); color: var(--acento); }

.nt-divisor { display: flex; align-items: center; gap: 14px; margin: 40px 0 0; font-size: 13px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--fg2); }
.nt-divisor::before, .nt-divisor::after { content: ''; flex: 1; height: 1px; background: var(--linha); }
.nt-divisor::before { max-width: 28px; }

.nt-banca {
  display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 18px; align-items: stretch;
  margin-top: 24px; scroll-margin-top: calc(var(--bar-h) + 16px);
}
.nt-placa {
  display: flex; flex-direction: column; padding: 24px 22px; border-radius: var(--raio);
  background: var(--tom-a); min-height: 220px;
}
.nt-placa--1 { background: var(--tom-b); }
.nt-placa--2 { background: var(--tom-c); }
.nt-placa__seccao { font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--fg2); }
.nt-placa__nome { margin: 10px 0 6px; font-family: var(--serif); font-weight: 400; font-size: 30px; line-height: 1.05; text-transform: capitalize; word-break: break-word; }
.nt-placa__n { font-size: 14px; color: var(--fg2); }
.nt-placa__setas { display: flex; gap: 6px; margin-top: auto; padding-top: 18px; }
.nt-redondo--placa { width: 34px; height: 34px; background: color-mix(in srgb, var(--papel) 70%, transparent); }
.nt-banca__lista { min-width: 0; }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.nt-catalogo :deep(.bg-zinc-900), .nt-catalogo :deep(.bg-white) { background: var(--papel) !important; }
.nt-catalogo :deep(.bg-zinc-800), .nt-catalogo :deep(.bg-gray-50), .nt-catalogo :deep(.bg-gray-100),
.nt-catalogo :deep(.bg-zinc-700), .nt-catalogo :deep(.bg-gray-200) { background: var(--tom-a) !important; }
.nt-catalogo :deep(.border-zinc-800), .nt-catalogo :deep(.border-zinc-700),
.nt-catalogo :deep(.border-gray-200), .nt-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.nt-catalogo :deep(.text-zinc-100), .nt-catalogo :deep(.text-zinc-900) { color: var(--fg) !important; }
.nt-catalogo :deep(input), .nt-catalogo :deep(select) { color: var(--fg) !important; font-family: var(--sans); }
.nt-catalogo :deep(input:focus), .nt-catalogo :deep(select:focus) { border-color: var(--acento) !important; outline: none; }
.nt-catalogo :deep(.nt-tab) { background: var(--papel); color: var(--fg); border: 1px solid var(--linha); font-weight: 500; text-transform: capitalize; }
.nt-catalogo :deep(.nt-tab--on) { background: var(--cor) !important; color: #fff !important; font-weight: 600; text-transform: capitalize; }
.nt-catalogo :deep(.nt-cat-borda) { border-color: var(--linha) !important; }
.nt-catalogo :deep(.nt-cat-nome) { font-weight: 600; }
.nt-catalogo :deep(.nt-cat-preco) { color: var(--acento) !important; font-family: var(--serif); }
.nt-catalogo :deep(.nt-cat-badge) { background: var(--kraft) !important; color: var(--kraft-fg) !important; border-radius: 999px !important; font-weight: 600; }
.nt-catalogo :deep(.nt-cat-indicador) { background: var(--tom-a) !important; color: var(--fg) !important; }
.nt-catalogo :deep(.nt-cat-limpar) { color: var(--acento) !important; }
.nt-catalogo :deep(.nt-cat-spinner) { color: var(--acento) !important; }

/* ── Informação (cartões-folha) ─────────────────────────── */
.nt-info { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.nt-folha { padding: 30px 28px; background: var(--tom-a); border-radius: 48px 8px 48px 8px; }
.nt-folha--b { background: var(--tom-b); border-radius: 8px 48px 8px 48px; }
.nt-folha--c { background: var(--tom-c); }
.nt-folha__titulo { margin: 0 0 14px !important; font-family: var(--serif); font-size: 24px; color: var(--fg) !important; }
.nt-folha p { margin: 0; font-size: 16px; line-height: 1.6; color: var(--fg2); }
.nt-folha ul { list-style: none; margin: 0; padding: 0; }
.nt-folha li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 15px; border-bottom: 1px solid var(--linha); }
.nt-folha li:last-child { border-bottom: none; }
.nt-folha li b { font-weight: 600; color: var(--acento); }
.nt-folha__tags { display: flex; flex-wrap: wrap; gap: 8px; }
.nt-folha__tags span { padding: 7px 14px; border-radius: 999px; background: var(--papel); font-size: 14px; font-weight: 500; text-transform: capitalize; }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.nt-estrela--on) { color: var(--acento) !important; }
:deep(.nt-estrela--off) { color: var(--linha) !important; }
:deep(.nt-barra) { background: var(--acento) !important; }
:deep(.nt-review) { background: var(--papel) !important; border: 1px solid var(--linha) !important; }
:deep(.nt-review--minha) { border: 1.5px solid var(--acento) !important; }
:deep(.nt-btn) { display: inline-flex; padding: 12px 22px; border-radius: 999px; font-weight: 600; border: 1.5px solid var(--fg); }
:deep(.nt-btn--cheio) { background: var(--cor) !important; border-color: var(--cor) !important; color: #fff !important; }

/* ── Rodapé ──────────────────────────────────────────────── */
.nt-footer {
  margin-top: 110px; padding: 72px 0 36px; background: var(--tom-c);
  border-radius: 50% 50% 0 0 / 60px 60px 0 0;            /* topo em colina */
}
.nt-footer__inner { text-align: center; }
.nt-footer__nome { margin: 0; font-family: var(--serif); font-size: clamp(2.2rem, 6vw, 4rem); line-height: 1; }
.nt-footer__morada { margin: 10px 0 0; color: var(--fg2); }
.nt-footer__links { display: flex; justify-content: center; flex-wrap: wrap; gap: 8px 22px; margin: 26px 0 16px; }
.nt-footer__links button { background: none; border: none; cursor: pointer; color: var(--fg); font: inherit; font-size: 14px; font-weight: 600; }
.nt-footer__links button:hover { color: var(--acento); }
.nt-footer__copy { margin: 0; font-size: 13px; color: var(--fg2); }

/* ── Modal ───────────────────────────────────────────────── */
.nt-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.5); }
.nt-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--papel); color: var(--fg); border-radius: var(--raio); }
.nt-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 18px 22px; background: var(--papel); border-bottom: 1px solid var(--linha); }
.nt-modal__painel h3 { margin: 0; font-family: var(--serif); font-size: 24px; font-weight: 400; }
.nt-modal__corpo { padding: 22px; font-size: 15px; line-height: 1.7; color: var(--fg2); white-space: pre-wrap; }

.nt-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-family: var(--serif); font-size: 28px; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .nt-hero { grid-template-columns: minmax(0, 1fr); gap: 32px; }
  .nt-hero__media { order: -1; max-width: 460px; width: 100%; margin: 0 auto; }
  .nt-fila--epoca { grid-auto-columns: calc((100% - 2 * 18px) / 3); }
  .nt-info { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 760px) {
  .nt-banca { grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .nt-placa { min-height: 0; flex-direction: row; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; padding: 18px 20px; }
  .nt-placa__seccao { width: 100%; }
  .nt-placa__nome { margin: 0; font-size: 24px; }
  .nt-placa__setas { display: none; }
}

@media (max-width: 640px) {
  .nt-root { --bar-h: 60px; --bar-pad: 14px; --raio: 22px; }
  .nt-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .nt-redondo { width: 34px; height: 34px; }
  .nt-bar__nome { font-size: 17px; }
  .nt-hero { padding-top: calc(var(--bar-h) + 12px); }
  .nt-hero__desc { font-size: 16px; }
  .nt-selo { width: 104px; height: 104px; }
  .nt-sec { padding-top: 64px; }
  .nt-fila { grid-auto-columns: 46%; gap: 12px; }
  .nt-fila--epoca { grid-auto-columns: 70%; }
  .nt-kraft { flex-direction: column; gap: 2px; padding: 8px 12px; }
  .nt-kraft__nome { font-size: 14px; white-space: normal; }
  .nt-folha { padding: 26px 22px; }
}
</style>
