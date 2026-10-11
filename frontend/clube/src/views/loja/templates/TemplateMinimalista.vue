<!-- TemplateMinimalista.vue — Revamp "galeria"
     Espaço em branco, uma só família tipográfica leve, peças apresentadas como obras:
     hero com banner emoldurado · índice numerado · selecção em galeria assimétrica ·
     filas por tipo e por categoria · catálogo completo · informação em texto.
     Sem ícones: controlos e informação em texto.
     Tipografia: Hanken Grotesk. Acento: --cor-primaria (detalhes). Fundo escuro: --cor-secundaria.
-->
<template>
  <div class="mn-root" :class="isDark ? 'mn-dark' : 'mn-light'" :style="cssVars">
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
    <div v-if="loading" class="mn-loading">
      <span class="mn-loading__linha"></span>
      <span class="mn-loading__texto">A carregar</span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="mn-bar" :class="{ 'mn-bar--solid': scrolled }">
        <button class="mn-link" @click="$router.back()">Voltar</button>
        <span class="mn-bar__sep" aria-hidden="true"></span>
        <button class="mn-link" @click="toggleDark">{{ isDark ? 'Claro' : 'Escuro' }}</button>
        <span class="mn-bar__nome" :class="{ 'mn-bar__nome--on': scrolled }">{{ loja.nome }}</span>
      </header>

      <!-- ══ HERO ══ -->
      <section class="mn-hero">
        <div class="mn-wrap mn-hero__grid">
          <div class="mn-hero__texto">
            <p class="mn-eyebrow">
              {{ loja.categoria || 'Loja' }}<template v-if="loja.localizacao"> · {{ loja.localizacao }}</template>
            </p>
            <h1 class="mn-hero__nome">{{ loja.nome }}</h1>
            <p v-if="loja.descricao" class="mn-hero__desc">{{ truncate(loja.descricao, 220) }}</p>

            <dl class="mn-meta">
              <div v-if="loja.rating_medio">
                <dt>Avaliação</dt>
                <dd>{{ rating }} <span class="mn-muted">/ 5 · {{ loja.total_avaliacoes || 0 }}</span></dd>
              </div>
              <div>
                <dt>Entrega</dt>
                <dd>{{ textoEntrega }}</dd>
              </div>
              <div>
                <dt>Peças</dt>
                <dd>{{ totalProdutos ?? '—' }}</dd>
              </div>
            </dl>

            <div class="mn-hero__ctas">
              <button v-if="totalDestaques" class="mn-cta" @click="scrollToId('mn-selecao')">Ver a selecção</button>
              <button class="mn-cta mn-cta--sec" @click="scrollToId('mn-catalogo')">Catálogo completo</button>
            </div>
          </div>

          <figure class="mn-hero__fig">
            <div class="mn-hero__moldura">
              <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" v-video-visivel muted loop playsinline></video>
              <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
              <div v-else class="mn-hero__vazio"><span>{{ iniciais }}</span></div>
            </div>
            <figcaption>Fig. 01 — {{ loja.nome }}</figcaption>
          </figure>
        </div>
      </section>

      <!-- ══ ÍNDICE ══ -->
      <nav class="mn-index" aria-label="Secções">
        <div class="mn-index__inner mn-hide-scroll">
          <button v-for="item in indice" :key="item.id"
                  class="mn-index__item" :class="{ 'mn-index__item--on': secaoActiva === item.id }"
                  @click="scrollToId(item.id)">
            <span class="mn-num">{{ item.num }}</span>{{ item.label }}
          </button>
        </div>
      </nav>

      <main>
        <!-- ══ SELECÇÃO (uma página de destaques) ══ -->
        <section v-if="totalDestaques" id="mn-selecao" class="mn-sec">
          <div class="mn-wrap">
            <header class="mn-sec__head">
              <span class="mn-num">{{ numDe('mn-selecao') }}</span>
              <h2 class="mn-sec__titulo">Selecção</h2>
              <span class="mn-sec__conta">{{ nSelecao }} {{ nSelecao === 1 ? 'peça' : 'peças' }}</span>
            </header>

            <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="5" :lazy="false"
                               class="mn-galeria" :class="'mn-galeria--' + nSelecao" v-slot="l">
              <template v-if="l.carregando">
                <div v-for="n in nSelecao" :key="n" class="mn-skel"></div>
              </template>
              <button v-for="(p, i) in l.itens" :key="p.id" class="mn-peca" :class="{ 'mn-peca--grande': i === 0 }"
                      @click="selectedProduct = p">
                <div class="mn-peca__img">
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted loop v-video-visivel playsinline></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="mn-peca__inicial">{{ p.nome.charAt(0) }}</span>
                  <span v-if="esgotado(p)" class="mn-etiqueta">Esgotado</span>
                </div>
                <div class="mn-peca__legenda">
                  <span class="mn-peca__nome">{{ p.nome }}</span>
                  <span class="mn-peca__preco">{{ precoDe(p) }}</span>
                </div>
                <p v-if="i === 0 && p.descricao" class="mn-peca__desc">{{ truncate(p.descricao, 120) }}</p>
              </button>
            </ProdutosPaginados>
          </div>
        </section>

        <!-- ══ POR TIPO / POR CATEGORIA (filas com scroll infinito horizontal) ══ -->
        <template v-for="(g, i) in grupos" :key="g.key">
          <div v-if="i === 0 || grupos[i - 1].seccao !== g.seccao" class="mn-wrap">
            <p class="mn-divisor">{{ SECCOES[g.seccao] }}</p>
          </div>
          <section :id="'mn-g-' + g.key" class="mn-sec mn-sec--fila">
            <div class="mn-wrap">
              <header class="mn-sec__head">
                <span class="mn-num">{{ numDe('mn-g-' + g.key) }}</span>
                <h2 class="mn-sec__titulo">{{ g.nome }}</h2>
                <span class="mn-sec__conta">{{ g.total }} {{ g.total === 1 ? 'peça' : 'peças' }}</span>
              </header>
            </div>
            <ProdutosPaginados :params="g.params" :limit="8" class="mn-fila mn-hide-scroll" v-slot="l">
              <template v-if="l.carregando">
                <div v-for="n in Math.min(g.total, 4)" :key="n" class="mn-skel"></div>
              </template>
              <button v-for="p in l.itens" :key="p.id" class="mn-peca mn-peca--fila" @click="selectedProduct = p">
                <div class="mn-peca__img">
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="mn-peca__inicial">{{ p.nome.charAt(0) }}</span>
                  <span v-if="esgotado(p)" class="mn-etiqueta">Esgotado</span>
                </div>
                <div class="mn-peca__legenda">
                  <span class="mn-peca__nome">{{ p.nome }}</span>
                  <span class="mn-peca__preco">{{ precoDe(p) }}</span>
                </div>
              </button>
              <FimDaLista v-if="l.temMais || l.aCarregarMais" class="mn-skel" :chave="l.itens.length" @visivel="l.carregarMais()" />
            </ProdutosPaginados>
          </section>
        </template>

        <!-- ══ CATÁLOGO ══ -->
        <section id="mn-catalogo" class="mn-sec">
          <div class="mn-wrap">
            <header class="mn-sec__head">
              <span class="mn-num">{{ numDe('mn-catalogo') }}</span>
              <h2 class="mn-sec__titulo">Catálogo</h2>
              <span class="mn-sec__conta">Pesquisa e filtra por tipo, categoria ou preço</span>
            </header>
            <div class="mn-catalogo">
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="280px"
                card-border-radius="rounded-none"
                skeleton-class="rounded-none"
                hover-effect="transition-opacity duration-300 hover:opacity-80"
                hover-border-class=""
                filter-container-radius="rounded-none"
                input-border-radius="rounded-none"
                input-focus-class="mn-input-focus"
                tab-border-radius="rounded-none"
                active-tab-class="mn-tab--on"
                inactive-tab-dark-class="mn-tab"
                inactive-tab-light-class="mn-tab"
                active-sub-tab-class="mn-tab--on"
                inactive-sub-tab-dark-class="mn-tab"
                inactive-sub-tab-light-class="mn-tab"
                category-border-class="mn-cat-borda"
                product-name-class="mn-cat-nome"
                product-name-hover-class=""
                price-class="mn-cat-preco"
                badge-text="Selecção"
                badge-class="mn-cat-badge"
                indicator-active-class="mn-cat-indicador"
                clear-filter-class="mn-cat-limpar"
                clear-all-class="mn-cat-limpar-tudo"
                spinner-class="mn-cat-spinner"
                :show-stock="false"
                :show-category-badges="false"
                empty-text="Nenhuma peça encontrada."
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- ══ INFORMAÇÃO ══ -->
        <section id="mn-info" class="mn-sec mn-sec--info">
          <div class="mn-wrap">
            <header class="mn-sec__head">
              <span class="mn-num">{{ numDe('mn-info') }}</span>
              <h2 class="mn-sec__titulo">Informação</h2>
            </header>
            <div class="mn-info">
              <div>
                <h3 class="mn-info__titulo">Sobre</h3>
                <p class="mn-info__texto">{{ loja.descricao || 'Uma selecção cuidada, sem excessos.' }}</p>
              </div>
              <div>
                <h3 class="mn-info__titulo">Entrega</h3>
                <p v-if="!opcoesEntrega.length" class="mn-info__texto">
                  {{ loja.levantamento_ativo ? 'Levantamento na loja.' : 'Consulta a loja.' }}
                </p>
                <dl v-else class="mn-linhas">
                  <div v-for="o in opcoesEntrega" :key="o.id">
                    <dt>{{ o.nome }}</dt>
                    <dd>{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</dd>
                  </div>
                  <div v-if="loja.levantamento_ativo"><dt>Levantamento na loja</dt><dd>Grátis</dd></div>
                </dl>
              </div>
              <div>
                <h3 class="mn-info__titulo">Pagamento</h3>
                <p class="mn-info__texto mn-capital">
                  {{ metodosPagamento.length ? metodosPagamento.map(m => m.tipo).join(' · ') : '—' }}
                </p>
                <template v-if="loja.localizacao">
                  <h3 class="mn-info__titulo mn-info__titulo--esp">Morada</h3>
                  <p class="mn-info__texto">{{ loja.localizacao }}</p>
                </template>
              </div>
            </div>
          </div>
        </section>

        <!-- ══ AVALIAÇÕES ══ -->
        <section id="mn-avaliacoes" class="mn-sec">
          <div class="mn-wrap">
            <header class="mn-sec__head">
              <span class="mn-num">{{ numDe('mn-avaliacoes') }}</span>
              <h2 class="mn-sec__titulo">Avaliações</h2>
            </header>
            <AvaliacaoLoja
              :loja-id="lojaId"
              :isDark="isDark"
              summary-border-radius="rounded-none"
              form-border-radius="rounded-none"
              review-card-border-radius="rounded-none"
              button-border-radius="rounded-none"
              textarea-border-radius="rounded-none"
              :star-active-class="'mn-estrela--on'"
              :star-inactive-class="'mn-estrela--off'"
              progress-bar-class="mn-barra"
              :submit-button-class="'mn-cta w-full justify-center'"
              :review-card-class="'mn-review'"
              :own-review-border-class="'mn-review--minha'"
              :load-more-button-class="'mn-cta mn-cta--sec'"
              @rating-updated="onRatingUpdated"
            />
          </div>
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="mn-footer">
        <div class="mn-wrap mn-footer__grid">
          <p class="mn-footer__nome">{{ loja.nome }}</p>
          <nav class="mn-footer__links">
            <button v-if="loja.politica_devolucao" class="mn-link" @click="modalPolitica = 'devolucao'">Devoluções</button>
            <button v-if="loja.termos_servico" class="mn-link" @click="modalPolitica = 'termos'">Termos</button>
            <button v-if="loja.politica_privacidade" class="mn-link" @click="modalPolitica = 'privacidade'">Privacidade</button>
          </nav>
          <p class="mn-footer__copy">© {{ ano }}</p>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="mn-modal" @click.self="modalPolitica = null">
        <div class="mn-modal__painel">
          <header class="mn-modal__head">
            <h3>{{ tituloPolitica }}</h3>
            <button class="mn-link" @click="modalPolitica = null">Fechar</button>
          </header>
          <div class="mn-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="mn-vazio">
      <p>Loja não encontrada.</p>
      <button class="mn-link" @click="$router.back()">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import ProdutosPaginados from '@/components/produtos/ProdutosPaginados.vue'
import FimDaLista from '@/components/produtos/FimDaLista.vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

const SECCOES = { tipo: 'Por tipo', categoria: 'Por categoria', todos: 'Peças' }

export default {
  name: 'TemplateMinimalista',

  components: { ProductInfoCard, MultiCart, Profile, ProductCatalog, AvaliacaoLoja, ProdutosPaginados, FimDaLista },

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
    const secaoActiva = ref('')

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#a0522d',
      '--cor-secundaria': props.tema?.corSecundaria || '#121212',
    }))

    // a Selecção mostra uma página com até 5 destaques
    const nSelecao = computed(() => Math.min(lojaData.totalDestaques.value, 5))

    // Por tipo, depois por categoria (ordem da loja). Sem nenhum dos dois → uma fila com tudo.
    // Só metadados e contagens — cada fila pede as peças página a página.
    const grupos = lojaData.gruposProdutos

    // Índice numerado (01, 02…) de todas as secções visíveis
    const indice = computed(() => {
      const itens = []
      if (nSelecao.value) itens.push({ id: 'mn-selecao', label: 'Selecção' })
      grupos.value.forEach(g => itens.push({ id: 'mn-g-' + g.key, label: g.nome }))
      itens.push({ id: 'mn-catalogo', label: 'Catálogo' })
      itens.push({ id: 'mn-info', label: 'Informação' })
      itens.push({ id: 'mn-avaliacoes', label: 'Avaliações' })
      return itens.map((it, i) => ({ ...it, num: String(i + 1).padStart(2, '0') }))
    })

    function numDe (id) {
      return indice.value.find(i => i.id === id)?.num || ''
    }

    // ── Texto ────────────────────────────────────────────────
    const rating = computed(() => {
      const r = lojaData.loja.value?.rating_medio
      return r ? Number(r).toFixed(1) : '—'
    })

    const textoEntrega = computed(() => {
      const precos = lojaData.opcoesEntrega.value.map(o => Number(o.preco))
      if (precos.length) {
        const min = Math.min(...precos)
        return min === 0 ? 'Grátis' : `Desde ${lojaData.formatPrice(min)}`
      }
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento' : '—'
    })

    const iniciais = computed(() =>
      (lojaData.loja.value?.nome || '').split(/\s+/).slice(0, 2).map(p => p.charAt(0)).join('').toUpperCase()
    )

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

    // com variações de preços diferentes → "desde"
    function precoDe (p) {
      const precos = (p.variantes || []).filter(v => v.quantidade > 0).map(v => Number(v.preco_efetivo))
      if (precos.length && Math.min(...precos) !== Math.max(...precos)) {
        return `desde ${lojaData.formatPrice(Math.min(...precos))}`
      }
      return lojaData.formatPrice(p.preco)
    }

    // ── Scroll: barra sólida + secção activa no índice ───────
    let observer = null
    function onScroll () { scrolled.value = window.scrollY > 80 }

    function observar () {
      observer?.disconnect()
      observer = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) secaoActiva.value = e.target.id })
      }, { rootMargin: '-35% 0px -60% 0px' })
      indice.value.forEach(i => {
        const el = document.getElementById(i.id)
        if (el) observer.observe(el)
      })
    }

    watch([indice, lojaData.loading], async () => {
      await nextTick()
      observar()
    })

    onMounted(() => {
      window.addEventListener('scroll', onScroll, { passive: true })
      onScroll()
    })

    onUnmounted(() => {
      window.removeEventListener('scroll', onScroll)
      observer?.disconnect()
    })

    return {
      ...lojaData,
      SECCOES,
      isDark, user, ano, cssVars,
      scrolled, secaoActiva, nSelecao,
      grupos, indice, numDe,
      rating, textoEntrega, iniciais, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, precoDe,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.mn-root {
  --acento: var(--cor-primaria, #a0522d);
  --fonte: 'Hanken Grotesk', system-ui, sans-serif;
  --bar-h: 68px;
  --bar-pad: 28px;
  /* carrinho · notificações · perfil alinhados com a barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--fonte);
  font-weight: 400;
  background: var(--bg);
  color: var(--fg);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .4s, color .4s;
}
.mn-light {
  --bg: #f4f2ee;
  --bg2: #ebe8e2;
  --fg: #161514;
  --fg2: #5f5b55;
  --fg3: #9a958c;
  --linha: rgba(22, 21, 20, .12);
}
.mn-dark {
  --bg: var(--cor-secundaria, #121212);
  --bg2: color-mix(in srgb, var(--bg) 90%, #fff 10%);
  --fg: #ecebe7;
  --fg2: #a7a39c;
  --fg3: #6f6b65;
  --linha: rgba(236, 235, 231, .12);
}

.mn-wrap { max-width: 1280px; margin: 0 auto; padding: 0 var(--bar-pad); }
.mn-muted { color: var(--fg3); }
.mn-capital { text-transform: capitalize; }
.mn-num {
  font-size: 11px; font-weight: 500; letter-spacing: .08em;
  color: var(--fg3); font-variant-numeric: tabular-nums;
}

/* links/controlos em texto */
.mn-link {
  background: none; border: none; padding: 0; cursor: pointer;
  font: inherit; font-size: 13px; color: inherit; letter-spacing: .02em;
  border-bottom: 1px solid transparent; transition: border-color .2s, color .2s;
}
.mn-link:hover { border-bottom-color: currentColor; }

/* ── Loading ─────────────────────────────────────────────── */
.mn-loading {
  position: fixed; inset: 0; z-index: 50; background: var(--bg);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px;
}
.mn-loading__linha { width: 120px; height: 1px; background: var(--linha); position: relative; overflow: hidden; }
.mn-loading__linha::after {
  content: ''; position: absolute; inset: 0; width: 40%; background: var(--fg);
  animation: mnLinha 1.1s ease-in-out infinite;
}
.mn-loading__texto { font-size: 12px; letter-spacing: .2em; text-transform: uppercase; color: var(--fg3); }
@keyframes mnLinha { from { transform: translateX(-100%); } to { transform: translateX(250%); } }

/* ── Barra ───────────────────────────────────────────────── */
.mn-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h);
  display: flex; align-items: center; gap: 16px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 20px) 0 var(--bar-pad);
  transition: background .3s, box-shadow .3s;
}
.mn-bar--solid { background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(10px); box-shadow: 0 1px 0 var(--linha); }
.mn-bar__sep { width: 1px; height: 14px; background: var(--linha); }
.mn-bar__nome {
  margin-left: auto; font-size: 14px; font-weight: 500; letter-spacing: .01em;
  opacity: 0; transform: translateY(4px); transition: opacity .3s, transform .3s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.mn-bar__nome--on { opacity: 1; transform: none; }

/* ── Hero ────────────────────────────────────────────────── */
.mn-hero { padding: calc(var(--bar-h) + 72px) 0 96px; }
.mn-hero__grid { display: grid; grid-template-columns: minmax(0, 7fr) minmax(0, 5fr); gap: 64px; align-items: end; }
.mn-eyebrow { font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: var(--fg2); margin: 0 0 28px; }
.mn-hero__nome {
  font-weight: 300; font-size: clamp(3rem, 8vw, 7.25rem);
  line-height: .95; letter-spacing: -.045em; margin: 0 0 32px; text-wrap: balance;
}
.mn-hero__desc { max-width: 520px; font-size: 17px; line-height: 1.7; color: var(--fg2); margin: 0 0 40px; font-weight: 300; }

.mn-meta { display: flex; flex-wrap: wrap; gap: 0; margin: 0 0 44px; border-top: 1px solid var(--linha); }
.mn-meta > div { padding: 16px 40px 0 0; margin-right: 40px; }
.mn-meta dt { font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: var(--fg3); margin-bottom: 6px; }
.mn-meta dd { margin: 0; font-size: 18px; font-weight: 400; }

.mn-hero__ctas { display: flex; flex-wrap: wrap; gap: 28px; align-items: center; }
.mn-cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 28px; background: var(--fg); color: var(--bg);
  border: 1px solid var(--fg); cursor: pointer;
  font: inherit; font-size: 13px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase;
  transition: background .25s, color .25s;
}
.mn-cta:hover { background: transparent; color: var(--fg); }
.mn-cta--sec { background: transparent; color: var(--fg); border-color: var(--linha); }
.mn-cta--sec:hover { border-color: var(--fg); }

.mn-hero__fig { margin: 0; }
.mn-hero__moldura {
  aspect-ratio: 4 / 5; background: var(--bg2); padding: 18px;
  box-shadow: inset 0 0 0 1px var(--linha);
}
.mn-hero__moldura img, .mn-hero__moldura video { width: 100%; height: 100%; object-fit: cover; display: block; }
.mn-hero__vazio {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  background: color-mix(in srgb, var(--acento) 14%, var(--bg));
  font-size: clamp(3rem, 8vw, 6rem); font-weight: 300; letter-spacing: -.04em; color: var(--acento);
}
.mn-hero__fig figcaption { margin-top: 12px; font-size: 12px; color: var(--fg3); letter-spacing: .02em; }

/* ── Índice ──────────────────────────────────────────────── */
.mn-index {
  position: sticky; top: var(--bar-h); z-index: 20;
  background: color-mix(in srgb, var(--bg) 94%, transparent); backdrop-filter: blur(10px);
  border-top: 1px solid var(--linha); border-bottom: 1px solid var(--linha);
}
.mn-index__inner { max-width: 1280px; margin: 0 auto; padding: 0 var(--bar-pad); display: flex; gap: 32px; overflow-x: auto; }
.mn-index__item {
  flex-shrink: 0; display: inline-flex; align-items: baseline; gap: 8px;
  padding: 16px 0; background: none; border: none; cursor: pointer;
  font: inherit; font-size: 13px; color: var(--fg2); text-transform: capitalize;
  border-bottom: 1px solid transparent; margin-bottom: -1px; transition: color .2s, border-color .2s;
}
.mn-index__item:hover { color: var(--fg); }
.mn-index__item--on { color: var(--fg); border-bottom-color: var(--acento); }

/* ── Secções ─────────────────────────────────────────────── */
.mn-sec { padding: 96px 0; scroll-margin-top: calc(var(--bar-h) + 52px); }
.mn-sec--fila { padding: 56px 0; }
.mn-sec__head { display: flex; align-items: baseline; gap: 18px; margin-bottom: 40px; flex-wrap: wrap; }
.mn-sec__titulo { margin: 0; font-weight: 300; font-size: clamp(2rem, 4vw, 3.25rem); letter-spacing: -.03em; line-height: 1; text-transform: capitalize; }
.mn-sec__conta { margin-left: auto; font-size: 12px; color: var(--fg3); letter-spacing: .04em; }
.mn-divisor {
  margin: 48px 0 0; padding-top: 18px; border-top: 1px solid var(--linha);
  font-size: 11px; letter-spacing: .2em; text-transform: uppercase; color: var(--fg3);
}

/* ── Peças (galeria e filas) ─────────────────────────────── */
.mn-peca {
  display: flex; flex-direction: column; gap: 14px; text-align: left;
  background: none; border: none; padding: 0; cursor: pointer; color: inherit; font: inherit;
}
.mn-peca__img {
  position: relative; aspect-ratio: 4 / 5; background: var(--bg2); overflow: hidden;
}
.mn-peca__img img, .mn-peca__img video {
  width: 100%; height: 100%; object-fit: cover; display: block;
  transition: transform .8s cubic-bezier(.2, .7, .2, 1), opacity .3s;
}
.mn-peca:hover .mn-peca__img img, .mn-peca:hover .mn-peca__img video { transform: scale(1.03); }
.mn-peca__inicial {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 48px; font-weight: 300; color: var(--fg3);
}
.mn-etiqueta {
  position: absolute; left: 12px; top: 12px; padding: 5px 9px;
  background: var(--bg); color: var(--fg);
  font-size: 10px; letter-spacing: .14em; text-transform: uppercase;
}
.mn-peca__legenda { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; }
.mn-peca__nome { font-size: 14px; font-weight: 400; line-height: 1.35; }
.mn-peca__preco { font-size: 14px; color: var(--fg2); white-space: nowrap; font-variant-numeric: tabular-nums; }
.mn-peca__desc { margin: 0; font-size: 14px; line-height: 1.6; color: var(--fg2); font-weight: 300; max-width: 460px; }

.mn-galeria { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 56px 32px; align-items: start; }
.mn-galeria .mn-peca--grande { grid-column: span 2; grid-row: span 2; }
.mn-galeria .mn-peca--grande .mn-peca__img { aspect-ratio: 5 / 6; }
.mn-galeria .mn-peca:not(.mn-peca--grande):nth-child(odd) { margin-top: 48px; }
.mn-galeria--1 { grid-template-columns: minmax(0, 1fr); max-width: 720px; }
.mn-galeria--1 .mn-peca--grande, .mn-galeria--2 .mn-peca--grande { grid-row: auto; }
.mn-galeria--2 .mn-peca--grande { grid-column: span 2; }

.mn-fila {
  display: flex; gap: 28px; overflow-x: auto; scroll-snap-type: x mandatory;
  padding: 0 var(--bar-pad) 8px;
  max-width: 1280px; margin: 0 auto;
}
.mn-peca--fila { flex: 0 0 240px; scroll-snap-align: start; }

.mn-skel-fila { display: flex; gap: 28px; padding-top: 56px; }
.mn-skel { flex: 0 0 240px; aspect-ratio: 4 / 5; background: var(--bg2); animation: mnPulse 1.4s ease-in-out infinite; }
@keyframes mnPulse { 50% { opacity: .5; } }

/* ── Catálogo (ProductCatalog no tom do template) ── */
.mn-catalogo :deep(.bg-zinc-900), .mn-catalogo :deep(.bg-white) { background: transparent !important; }
.mn-catalogo :deep(.bg-zinc-800), .mn-catalogo :deep(.bg-gray-50), .mn-catalogo :deep(.bg-gray-100),
.mn-catalogo :deep(.bg-zinc-700), .mn-catalogo :deep(.bg-gray-200) { background: var(--bg2) !important; }
.mn-catalogo :deep(.border-zinc-800), .mn-catalogo :deep(.border-zinc-700),
.mn-catalogo :deep(.border-gray-200), .mn-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.mn-catalogo :deep(.shadow-sm), .mn-catalogo :deep(.shadow-xl), .mn-catalogo :deep(.shadow-lg) { box-shadow: none !important; }
.mn-catalogo :deep(.text-zinc-100), .mn-catalogo :deep(.text-zinc-900) { color: var(--fg) !important; }
.mn-catalogo :deep(input), .mn-catalogo :deep(select) { color: var(--fg) !important; font-family: var(--fonte); }
.mn-catalogo :deep(input::placeholder) { color: var(--fg3) !important; }
.mn-catalogo :deep(input:focus), .mn-catalogo :deep(select:focus) { border-color: var(--fg) !important; outline: none; }
.mn-catalogo :deep(.mn-tab) {
  background: transparent; color: var(--fg2); border: 1px solid var(--linha);
  font-size: 12px; letter-spacing: .04em; text-transform: capitalize;
}
.mn-catalogo :deep(.mn-tab:hover) { color: var(--fg); border-color: var(--fg3); }
.mn-catalogo :deep(.mn-tab--on) {
  background: var(--fg) !important; color: var(--bg) !important; border: 1px solid var(--fg);
  font-size: 12px; letter-spacing: .04em; text-transform: capitalize;
}
.mn-catalogo :deep(.mn-cat-borda) { border-color: var(--linha) !important; }
.mn-catalogo :deep(.mn-cat-nome) { font-family: var(--fonte); font-weight: 400; }
.mn-catalogo :deep(.mn-cat-preco) { color: var(--fg2) !important; font-weight: 400; }
.mn-catalogo :deep(.mn-cat-badge) {
  background: var(--bg) !important; color: var(--fg) !important; border-radius: 0 !important;
  font-size: 10px; letter-spacing: .14em; text-transform: uppercase;
}
.mn-catalogo :deep(.mn-cat-indicador) { background: var(--bg2) !important; color: var(--fg) !important; }
.mn-catalogo :deep(.mn-cat-limpar), .mn-catalogo :deep(.mn-cat-limpar-tudo) { color: var(--acento) !important; background: transparent !important; }
.mn-catalogo :deep(.mn-cat-spinner) { color: var(--fg3) !important; }

/* ── Informação ──────────────────────────────────────────── */
.mn-sec--info { background: var(--bg2); }
.mn-info { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 48px; }
.mn-info__titulo { margin: 0 0 14px; font-size: 11px; font-weight: 500; letter-spacing: .18em; text-transform: uppercase; color: var(--fg3); }
.mn-info__titulo--esp { margin-top: 32px; }
.mn-info__texto { margin: 0; font-size: 16px; line-height: 1.7; font-weight: 300; }
.mn-linhas { margin: 0; }
.mn-linhas > div { display: flex; justify-content: space-between; gap: 16px; padding: 10px 0; border-bottom: 1px solid var(--linha); font-size: 15px; }
.mn-linhas dt { font-weight: 300; }
.mn-linhas dd { margin: 0; color: var(--fg2); }

/* ── Avaliações (classes passadas ao AvaliacaoLoja) ─────── */
:deep(.mn-estrela--on) { color: var(--fg) !important; }
:deep(.mn-estrela--off) { color: var(--linha) !important; }
:deep(.mn-barra) { background: var(--fg) !important; }
:deep(.mn-review) { background: transparent !important; border-bottom: 1px solid var(--linha) !important; }
:deep(.mn-review--minha) { border: 1px solid var(--fg3) !important; }
:deep(.mn-cta) {
  display: inline-flex; padding: 14px 28px; background: var(--fg); color: var(--bg);
  border: 1px solid var(--fg); font-size: 13px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase;
}
:deep(.mn-cta--sec) { background: transparent; color: var(--fg); border-color: var(--linha); }

/* ── Rodapé ──────────────────────────────────────────────── */
.mn-footer { padding: 64px 0 40px; border-top: 1px solid var(--linha); }
.mn-footer__grid { display: flex; align-items: baseline; gap: 32px; flex-wrap: wrap; }
.mn-footer__nome { margin: 0; font-size: 20px; font-weight: 300; letter-spacing: -.02em; }
.mn-footer__links { display: flex; gap: 24px; flex-wrap: wrap; color: var(--fg2); }
.mn-footer__copy { margin: 0 0 0 auto; font-size: 12px; color: var(--fg3); }

/* ── Modal ───────────────────────────────────────────────── */
.mn-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.45); }
.mn-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--bg); color: var(--fg); }
.mn-modal__head { position: sticky; top: 0; background: var(--bg); display: flex; justify-content: space-between; align-items: baseline; padding: 20px 24px; border-bottom: 1px solid var(--linha); }
.mn-modal__head h3 { margin: 0; font-size: 18px; font-weight: 400; }
.mn-modal__corpo { padding: 24px; font-size: 14px; line-height: 1.75; color: var(--fg2); white-space: pre-wrap; font-weight: 300; }

.mn-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-size: 22px; font-weight: 300; }

.mn-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.mn-hide-scroll::-webkit-scrollbar { display: none; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 960px) {
  .mn-hero__grid { grid-template-columns: minmax(0, 1fr); gap: 48px; }
  .mn-hero__fig { max-width: 480px; }
  .mn-galeria { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 40px 20px; }
  .mn-galeria .mn-peca--grande { grid-column: span 2; grid-row: auto; }
  .mn-galeria .mn-peca:not(.mn-peca--grande):nth-child(odd) { margin-top: 0; }
  .mn-info { grid-template-columns: minmax(0, 1fr); gap: 40px; }
}

@media (max-width: 640px) {
  .mn-root { --bar-h: 60px; --bar-pad: 14px; }
  .mn-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 10px); gap: 12px; }
  .mn-bar__nome { display: none; }
  .mn-hero { padding: calc(var(--bar-h) + 40px) 0 64px; }
  .mn-hero__desc { font-size: 15px; }
  .mn-meta > div { margin-right: 24px; padding-right: 0; }
  .mn-meta dd { font-size: 16px; }
  .mn-sec { padding: 64px 0; }
  .mn-sec--fila { padding: 40px 0; }
  .mn-sec__head { margin-bottom: 28px; gap: 12px; }
  .mn-sec__conta { margin-left: 0; width: 100%; }
  .mn-galeria { gap: 32px 14px; }
  .mn-peca--fila, .mn-skel { flex-basis: 180px; }
  .mn-fila { gap: 16px; }
  .mn-footer__copy { margin-left: 0; }
}
</style>
