<!-- TemplateVibrante.vue — Revamp "pop"
     Blocos de cor arredondados, tipografia expressiva, energia sem ruído:
     barra em pílula · hero num bloco da cor primária com o banner como "autocolante" ·
     faixa animada · "Em alta" em cartões coloridos · tipos/categorias em pílulas que trocam
     a grelha · catálogo completo · informação em cartões de cor.
     Tipografia: Bricolage Grotesque. Acento: --cor-primaria. Fundo escuro: --cor-secundaria.
     Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="vb-root" :class="isDark ? 'vb-dark' : 'vb-light'" :style="cssVars">
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
    <div v-if="loading" class="vb-loading">
      <span v-for="i in 3" :key="i" class="vb-loading__bola" :style="{ animationDelay: (i * 0.12) + 's' }"></span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="vb-bar">
        <div class="vb-bar__pilula" :class="{ 'vb-bar__pilula--solida': scrolled }">
          <button class="vb-redondo" @click="$router.back()" aria-label="Voltar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <span class="vb-bar__marca">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" />
            <span v-else class="vb-bar__inicial">{{ loja.nome.charAt(0) }}</span>
            <span class="vb-bar__nome">{{ loja.nome }}</span>
          </span>
          <button class="vb-redondo" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
            <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
          </button>
        </div>
      </header>

      <!-- ══ HERO ══ -->
      <section class="vb-wrap vb-hero">
        <div class="vb-hero__bloco">
          <div class="vb-hero__texto">
            <p class="vb-hero__tag">{{ loja.categoria || 'Loja' }}</p>
            <h1 class="vb-hero__nome">{{ loja.nome }}</h1>
            <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />
            <EstadoLoja :horario="loja.horario" :loja-id="lojaId" class="loja-estado" />
            <p v-if="loja.descricao" class="vb-hero__desc">{{ truncate(loja.descricao, 180) }}</p>

            <div class="vb-chips">
              <span v-if="loja.rating_medio" class="vb-chip">
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path d="M9.05 2.93c.3-.92 1.6-.92 1.9 0l1.07 3.29a1 1 0 0 0 .95.69h3.46c.97 0 1.37 1.24.59 1.81l-2.8 2.03a1 1 0 0 0-.36 1.12l1.07 3.3c.3.91-.76 1.68-1.54 1.11l-2.8-2.03a1 1 0 0 0-1.18 0l-2.8 2.03c-.78.57-1.84-.2-1.54-1.12l1.07-3.29a1 1 0 0 0-.36-1.12L2.98 8.72c-.78-.57-.38-1.81.59-1.81h3.46a1 1 0 0 0 .95-.69z"/></svg>
                {{ rating }} · {{ loja.total_avaliacoes || 0 }} avaliações
              </span>
              <span v-if="loja.localizacao" class="vb-chip">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ loja.localizacao }}
              </span>
              <span class="vb-chip">{{ textoEntrega }}</span>
            </div>

            <div class="vb-hero__ctas">
              <button class="vb-btn vb-btn--branco" @click="scrollToId(totalDestaques ? 'vb-alta' : 'vb-catalogo')">
                {{ totalDestaques ? 'Ver o que está em alta' : 'Ver produtos' }}
              </button>
              <button class="vb-btn vb-btn--contorno" @click="scrollToId('vb-catalogo')">Catálogo</button>
            </div>
          </div>

          <div class="vb-hero__media">
            <div class="vb-autocolante">
              <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" v-video-visivel muted loop playsinline></video>
              <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
              <div v-else class="vb-autocolante__vazio">{{ loja.nome.charAt(0) }}</div>
            </div>
            <div class="vb-selo" aria-hidden="true">
              <span class="vb-selo__num">{{ totalProdutos ?? '—' }}</span>
              <span class="vb-selo__txt">produtos</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ══ FAIXA ══ -->
      <div class="vb-faixa" aria-hidden="true">
        <div class="vb-faixa__trilho">
          <template v-for="n in 2" :key="n">
            <span v-for="(t, i) in faixa" :key="n + '-' + i" class="vb-faixa__item">
              {{ t }}<span class="vb-faixa__ponto"></span>
            </span>
          </template>
        </div>
      </div>

      <main class="vb-wrap">
        <!-- ══ EM ALTA (uma página de destaques) ══ -->
        <section v-if="totalDestaques" id="vb-alta" class="vb-sec">
          <header class="vb-sec__head">
            <h2 class="vb-sec__titulo">Em alta</h2>
            <p class="vb-sec__sub">Os favoritos da casa</p>
          </header>
          <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="8" :lazy="false"
                             class="vb-grelha vb-grelha--alta" v-slot="l">
            <template v-if="l.carregando">
              <div v-for="n in 4" :key="n" class="vb-skel"></div>
            </template>
            <button v-for="(p, i) in l.itens" :key="p.id" class="vb-cartao" :class="'vb-cartao--t' + (i % 4)"
                    @click="selectedProduct = p">
              <div class="vb-cartao__img">
                <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted loop v-video-visivel playsinline></video>
                <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                <span v-else class="vb-cartao__inicial">{{ p.nome.charAt(0) }}</span>
                <span v-if="esgotado(p)" class="vb-cartao__esgotado">Esgotado</span>
              </div>
              <div class="vb-cartao__info">
                <span class="vb-cartao__nome">{{ p.nome }}</span>
                <span class="vb-cartao__preco">{{ precoDe(p) }}</span>
              </div>
            </button>
          </ProdutosPaginados>
        </section>

        <!-- ══ POR TIPO / POR CATEGORIA (pílulas que trocam a grelha; página a página) ══ -->
        <section v-if="grupos.length" id="vb-explorar" class="vb-sec">
          <header class="vb-sec__head">
            <h2 class="vb-sec__titulo">Explorar</h2>
            <p class="vb-sec__sub">Escolhe um tipo ou uma categoria</p>
          </header>

          <div v-for="sec in seccoesGrupos" :key="sec.key" class="vb-pilulas">
            <span class="vb-pilulas__label">{{ sec.label }}</span>
            <div class="vb-pilulas__lista vb-hide-scroll">
              <button v-for="g in sec.grupos" :key="g.key" class="vb-pilula"
                      :class="{ 'vb-pilula--on': grupoActivo?.key === g.key }"
                      @click="grupoKey = g.key">
                {{ g.nome }}<span class="vb-pilula__n">{{ g.total }}</span>
              </button>
            </div>
          </div>

          <ProdutosPaginados v-if="grupoActivo" :key="grupoActivo.key" :params="grupoActivo.params" class="vb-explorar__grelha"
                             :limit="12" :lazy="false" v-slot="l">
            <div class="vb-grelha">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="vb-skel"></div>
              </template>
              <button v-for="(p, i) in l.itens" :key="p.id" class="vb-cartao vb-cartao--simples"
                      :style="{ animationDelay: (i % 12) * 0.03 + 's' }" @click="selectedProduct = p">
                <div class="vb-cartao__img">
                  <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="vb-cartao__inicial">{{ p.nome.charAt(0) }}</span>
                  <span v-if="esgotado(p)" class="vb-cartao__esgotado">Esgotado</span>
                </div>
                <div class="vb-cartao__info">
                  <span class="vb-cartao__nome">{{ p.nome }}</span>
                  <span class="vb-cartao__preco">{{ precoDe(p) }}</span>
                </div>
              </button>
            </div>
            <div v-if="l.temMais || l.aCarregarMais" class="vb-mais">
              <button class="vb-btn vb-btn--suave" :disabled="l.aCarregarMais" @click="l.carregarMais()">
                {{ l.aCarregarMais ? 'A carregar…' : `Ver mais (${l.total - l.itens.length})` }}
              </button>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ CATÁLOGO ══ -->
        <section id="vb-catalogo" class="vb-sec">
          <header class="vb-sec__head">
            <h2 class="vb-sec__titulo">Catálogo</h2>
            <p class="vb-sec__sub">Pesquisa e filtra todos os produtos</p>
          </header>
          <div class="vb-catalogo">
            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="220px"
              card-border-radius="rounded-[28px]"
              skeleton-class="rounded-[28px]"
              hover-effect="transition-transform duration-300 hover:-translate-y-1"
              hover-border-class=""
              filter-container-radius="rounded-[28px]"
              input-border-radius="rounded-full"
              input-focus-class="vb-foco"
              tab-border-radius="rounded-full"
              active-tab-class="vb-tab--on"
              inactive-tab-dark-class="vb-tab"
              inactive-tab-light-class="vb-tab"
              active-sub-tab-class="vb-tab--on"
              inactive-sub-tab-dark-class="vb-tab"
              inactive-sub-tab-light-class="vb-tab"
              category-border-class="vb-cat-borda"
              product-name-class="vb-cat-nome"
              product-name-hover-class=""
              price-class="vb-cat-preco"
              badge-text="Em alta"
              badge-class="vb-cat-badge"
              indicator-active-class="vb-cat-indicador"
              clear-filter-class="vb-cat-limpar"
              clear-all-class="vb-cat-limpar-tudo"
              spinner-class="vb-cat-spinner"
              :show-stock="false"
              :show-category-badges="false"
              empty-text="Nenhum produto encontrado."
              @product-click="selectedProduct = $event"
            />
          </div>
        </section>

        <!-- ══ INFORMAÇÃO ══ -->
        <section id="vb-info" class="vb-sec vb-info">
          <div class="vb-info__cartao vb-info__cartao--a">
            <h3>Entrega</h3>
            <p v-if="!opcoesEntrega.length">{{ loja.levantamento_ativo ? 'Levantamento na loja.' : 'Fala com a loja.' }}</p>
            <ul v-else>
              <li v-for="o in opcoesEntrega" :key="o.id">
                <span>{{ o.nome }}</span><b>{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</b>
              </li>
              <li v-if="loja.levantamento_ativo"><span>Levantamento</span><b>Grátis</b></li>
            </ul>
          </div>
          <div class="vb-info__cartao vb-info__cartao--b">
            <h3>Pagamento</h3>
            <div class="vb-info__tags">
              <span v-for="m in metodosPagamento" :key="m.id">{{ m.tipo }}</span>
              <span v-if="!metodosPagamento.length">—</span>
            </div>
          </div>
          <div class="vb-info__cartao vb-info__cartao--c">
            <h3>Sobre</h3>
            <p>{{ loja.descricao || 'Uma loja com energia própria.' }}</p>
          </div>
        </section>

        <!-- ══ AVALIAÇÕES ══ -->
        <section id="vb-avaliacoes" class="vb-sec">
          <header class="vb-sec__head">
            <h2 class="vb-sec__titulo">Avaliações</h2>
            <p class="vb-sec__sub">O que dizem os clientes</p>
          </header>
          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-[28px]"
            form-border-radius="rounded-[28px]"
            review-card-border-radius="rounded-3xl"
            button-border-radius="rounded-full"
            textarea-border-radius="rounded-2xl"
            :star-active-class="'vb-estrela--on'"
            :star-inactive-class="'vb-estrela--off'"
            progress-bar-class="vb-barra"
            :submit-button-class="'vb-btn vb-btn--cor w-full justify-center'"
            :review-card-class="'vb-review'"
            :own-review-border-class="'vb-review--minha'"
            :load-more-button-class="'vb-btn vb-btn--suave'"
            @rating-updated="onRatingUpdated"
          />
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="vb-wrap vb-footer">
        <div class="vb-footer__bloco">
          <p class="vb-footer__nome">{{ loja.nome }}</p>
          <div class="vb-footer__linha">
            <nav class="vb-footer__links">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
            </nav>
            <span>© {{ ano }} {{ loja.nome }}</span>
          </div>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="vb-modal" @click.self="modalPolitica = null">
        <div class="vb-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="vb-redondo" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="vb-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="vb-vazio">
      <p>Loja não encontrada</p>
      <button class="vb-btn vb-btn--cor" @click="$router.back()">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import ProdutosPaginados from '@/components/produtos/ProdutosPaginados.vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import BotaoFavorito from '@/components/favoritos/BotaoFavorito.vue'
import EstadoLoja from '@/components/horario/EstadoLoja.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

export default {
  name: 'TemplateVibrante',

  components: { ProductInfoCard, BotaoFavorito, EstadoLoja, MultiCart, Profile, ProductCatalog, AvaliacaoLoja, ProdutosPaginados },

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
      '--cor-primaria':   props.tema?.corPrimaria   || '#ff4d2e',
      '--cor-secundaria': props.tema?.corSecundaria || '#111014',
    }))

    // ── Grupos (só metadados; os produtos vêm página a página) ──
    const grupos = lojaData.gruposProdutos

    const seccoesGrupos = computed(() => [
      { key: 'tipo', label: 'Por tipo' },
      { key: 'categoria', label: 'Por categoria' },
      { key: 'todos', label: 'Tudo' },
    ].map(s => ({ ...s, grupos: grupos.value.filter(g => g.seccao === s.key) })).filter(s => s.grupos.length))

    // o primeiro grupo fica escolhido por defeito
    const grupoKey = ref(null)
    const grupoActivo = computed(() => grupos.value.find(g => g.key === grupoKey.value) || grupos.value[0] || null)

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
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento na loja' : 'Consulta a entrega'
    })

    const faixa = computed(() => {
      const l = lojaData.loja.value
      if (!l) return []
      return [l.nome, l.categoria, textoEntrega.value, l.localizacao].filter(Boolean)
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

    function onScroll () { scrolled.value = window.scrollY > 40 }

    onMounted(() => {
      window.addEventListener('scroll', onScroll, { passive: true })
      onScroll()
    })
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return {
      ...lojaData,
      isDark, user, ano, cssVars,
      scrolled,
      grupos, seccoesGrupos, grupoKey, grupoActivo,
      rating, textoEntrega, faixa, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, precoDe,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,700;12..96,800&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.vb-root {
  --cor: var(--cor-primaria, #ff4d2e);
  --fonte: 'Bricolage Grotesque', system-ui, sans-serif;
  --raio: 32px;
  --bar-h: 68px;
  --bar-pad: 28px;
  /* carrinho · notificações · perfil alinhados com a barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--fonte);
  background: var(--bg);
  color: var(--fg);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .4s, color .4s;
}
.vb-light {
  --bg: #fff8ef;
  --bg2: #ffffff;
  --fg: #17130f;
  --fg2: #5d544b;
  --linha: rgba(23, 19, 15, .1);
  --tom-a: color-mix(in srgb, var(--cor) 16%, #fff);
  --tom-b: color-mix(in srgb, var(--cor) 30%, #fff8ef);
  --tom-c: color-mix(in srgb, var(--cor) 8%, #f1ece4);
  --tom-d: color-mix(in srgb, var(--cor) 45%, #fff);
}
.vb-dark {
  --bg: var(--cor-secundaria, #111014);
  --bg2: color-mix(in srgb, var(--bg) 88%, #fff 12%);
  --fg: #fbf6ef;
  --fg2: #b8b0a6;
  --linha: rgba(251, 246, 239, .12);
  --tom-a: color-mix(in srgb, var(--cor) 26%, var(--bg));
  --tom-b: color-mix(in srgb, var(--cor) 40%, var(--bg));
  --tom-c: color-mix(in srgb, var(--cor) 14%, var(--bg));
  --tom-d: color-mix(in srgb, var(--cor) 55%, var(--bg));
}

.vb-wrap { max-width: 1320px; margin: 0 auto; padding: 0 var(--bar-pad); }
.vb-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.vb-hide-scroll::-webkit-scrollbar { display: none; }

/* ── Loading ─────────────────────────────────────────────── */
.vb-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; align-items: center; justify-content: center; gap: 10px; }
.vb-loading__bola { width: 14px; height: 14px; border-radius: 50%; background: var(--cor); animation: vbSalto .7s ease-in-out infinite alternate; }
@keyframes vbSalto { from { transform: translateY(6px); opacity: .5; } to { transform: translateY(-6px); opacity: 1; } }

/* ── Barra (pílula flutuante) ────────────────────────────── */
.vb-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 16px) 0 var(--bar-pad);
  pointer-events: none;
}
.vb-bar__pilula {
  pointer-events: auto;
  display: flex; align-items: center; gap: 10px; padding: 5px;
  border-radius: 999px; background: color-mix(in srgb, var(--bg2) 70%, transparent);
  backdrop-filter: blur(12px); box-shadow: 0 0 0 1px var(--linha);
  transition: background .3s, box-shadow .3s; min-width: 0;
}
.vb-bar__pilula--solida { background: var(--bg2); box-shadow: 0 0 0 1px var(--linha), 0 10px 30px rgba(0,0,0,.08); }
.vb-redondo {
  width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg); color: var(--fg); border: none; cursor: pointer;
  transition: background .2s, transform .2s;
}
.vb-redondo:hover { background: var(--cor); color: #fff; transform: rotate(-8deg); }
.vb-bar__marca { display: flex; align-items: center; gap: 8px; min-width: 0; padding: 0 6px; }
.vb-bar__marca img, .vb-bar__inicial { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.vb-bar__inicial { display: flex; align-items: center; justify-content: center; background: var(--cor); color: #fff; font-weight: 800; font-size: 14px; }
.vb-bar__nome { font-weight: 700; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 220px; }

/* ── Hero ────────────────────────────────────────────────── */
.vb-hero { padding-top: calc(var(--bar-h) + 12px); padding-bottom: 28px; }
.vb-hero__bloco {
  position: relative; overflow: hidden;
  display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, .85fr); gap: 32px; align-items: center;
  padding: 56px; border-radius: 44px;
  background: var(--cor); color: #fff;
}
.vb-hero__bloco::before {
  /* círculo decorativo (forma, não ícone) */
  content: ''; position: absolute; width: 520px; height: 520px; border-radius: 50%;
  right: -160px; bottom: -220px; background: rgba(255,255,255,.12);
}
.vb-hero__texto { position: relative; z-index: 1; }
.vb-hero__tag {
  display: inline-block; margin: 0 0 18px; padding: 7px 14px; border-radius: 999px;
  background: rgba(255,255,255,.18); font-size: 13px; font-weight: 700; text-transform: capitalize;
}
.vb-hero__nome {
  margin: 0 0 18px; font-weight: 800; font-size: clamp(3rem, 8vw, 7rem);
  line-height: .88; letter-spacing: -.04em; text-wrap: balance;
}
.vb-hero__desc { margin: 0 0 24px; max-width: 520px; font-size: 18px; line-height: 1.55; opacity: .9; }
.vb-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }
.vb-chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 999px;
  background: rgba(0,0,0,.14); font-size: 14px; font-weight: 500;
}
.vb-hero__ctas { display: flex; flex-wrap: wrap; gap: 10px; }

.vb-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 15px 26px; border-radius: 999px;
  font: inherit; font-size: 15px; font-weight: 700; cursor: pointer; border: 2px solid transparent;
  transition: transform .2s, background .2s, color .2s;
}
.vb-btn:hover { transform: translateY(-2px) rotate(-1deg); }
.vb-btn--branco { background: #fff; color: var(--cor); }
.vb-btn--contorno { background: transparent; color: #fff; border-color: rgba(255,255,255,.6); }
.vb-btn--cor { background: var(--cor); color: #fff; }
.vb-btn--suave { background: var(--tom-a); color: var(--fg); }

.vb-hero__media { position: relative; z-index: 1; display: flex; justify-content: center; }
.vb-autocolante {
  width: min(100%, 400px); aspect-ratio: 4 / 5; border-radius: 28px; overflow: hidden;
  border: 8px solid #fff; transform: rotate(-4deg); box-shadow: 0 30px 60px rgba(0,0,0,.25);
  background: rgba(255,255,255,.2); transition: transform .5s cubic-bezier(.2,.8,.2,1);
}
.vb-autocolante:hover { transform: rotate(0deg) scale(1.02); }
.vb-autocolante img, .vb-autocolante video { width: 100%; height: 100%; object-fit: cover; display: block; }
.vb-autocolante__vazio { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 140px; font-weight: 800; }
.vb-selo {
  position: absolute; left: 4%; bottom: 6%; width: 112px; height: 112px; border-radius: 50%;
  background: var(--fg); color: var(--bg); transform: rotate(8deg);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  box-shadow: 0 14px 30px rgba(0,0,0,.25);
}
.vb-selo__num { font-size: 34px; font-weight: 800; line-height: 1; }
.vb-selo__txt { font-size: 12px; font-weight: 600; opacity: .75; }

/* ── Faixa animada ───────────────────────────────────────── */
.vb-faixa { overflow: hidden; padding: 14px 0; margin: 8px 0 0; background: var(--fg); color: var(--bg); transform: rotate(-1deg); }
.vb-faixa__trilho { display: flex; width: max-content; animation: vbFaixa 28s linear infinite; }
.vb-faixa__item { display: inline-flex; align-items: center; gap: 28px; padding-right: 28px; font-size: 22px; font-weight: 800; white-space: nowrap; text-transform: capitalize; }
.vb-faixa__ponto { width: 12px; height: 12px; border-radius: 50%; background: var(--cor); }
@keyframes vbFaixa { to { transform: translateX(-50%); } }

/* ── Secções ─────────────────────────────────────────────── */
.vb-sec { padding: 72px 0 0; scroll-margin-top: calc(var(--bar-h) + 12px); }
.vb-sec__head { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }
.vb-sec__titulo { margin: 0; font-weight: 800; font-size: clamp(2.2rem, 5vw, 3.75rem); letter-spacing: -.035em; line-height: 1; }
.vb-sec__sub { margin: 0; font-size: 16px; color: var(--fg2); }

/* ── Cartões ─────────────────────────────────────────────── */
.vb-grelha { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
.vb-cartao {
  display: flex; flex-direction: column; gap: 12px; padding: 12px; text-align: left;
  border-radius: var(--raio); border: none; cursor: pointer; color: var(--fg); font: inherit;
  background: var(--bg2); box-shadow: 0 0 0 1px var(--linha);
  transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s;
  animation: vbEntra .4s both;
}
.vb-cartao:hover { transform: translateY(-6px) rotate(-1.2deg); box-shadow: 0 0 0 1px var(--linha), 0 18px 40px rgba(0,0,0,.1); }
.vb-cartao--t0 { background: var(--tom-a); box-shadow: none; }
.vb-cartao--t1 { background: var(--tom-b); box-shadow: none; }
.vb-cartao--t2 { background: var(--tom-c); box-shadow: none; }
.vb-cartao--t3 { background: var(--tom-d); box-shadow: none; }
.vb-cartao__img { position: relative; aspect-ratio: 1; border-radius: calc(var(--raio) - 10px); overflow: hidden; background: color-mix(in srgb, var(--fg) 6%, transparent); }
.vb-cartao__img img, .vb-cartao__img video { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .5s; }
.vb-cartao:hover .vb-cartao__img img { transform: scale(1.05); }
.vb-cartao__inicial { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 64px; font-weight: 800; color: var(--cor); }
.vb-cartao__esgotado {
  position: absolute; left: 10px; top: 10px; padding: 5px 11px; border-radius: 999px;
  background: var(--fg); color: var(--bg); font-size: 12px; font-weight: 700;
}
.vb-cartao__info { display: flex; justify-content: space-between; align-items: flex-end; gap: 10px; padding: 0 6px 4px; }
.vb-cartao__nome { font-size: 16px; font-weight: 700; line-height: 1.2; }
.vb-cartao__preco {
  flex-shrink: 0; padding: 5px 11px; border-radius: 999px; background: var(--fg); color: var(--bg);
  font-size: 13px; font-weight: 700; white-space: nowrap;
}
@keyframes vbEntra { from { opacity: 0; transform: translateY(12px); } }

.vb-skel { aspect-ratio: 1; border-radius: var(--raio); background: var(--tom-c); animation: vbPulse 1.3s ease-in-out infinite; }
@keyframes vbPulse { 50% { opacity: .5; } }

/* ── Pílulas (explorar) ──────────────────────────────────── */
.vb-pilulas { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; min-width: 0; }
.vb-pilulas__label { flex-shrink: 0; width: 110px; font-size: 13px; font-weight: 700; color: var(--fg2); }
.vb-pilulas__lista { display: flex; gap: 8px; overflow-x: auto; min-width: 0; padding: 2px; }
.vb-pilula {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; padding: 11px 18px; border-radius: 999px;
  background: var(--bg2); color: var(--fg); border: none; box-shadow: 0 0 0 1px var(--linha);
  font: inherit; font-size: 15px; font-weight: 700; cursor: pointer; text-transform: capitalize;
  transition: background .2s, color .2s, transform .2s;
}
.vb-pilula:hover { transform: translateY(-1px); }
.vb-pilula--on { background: var(--cor); color: #fff; box-shadow: none; }
.vb-pilula__n { font-size: 12px; padding: 2px 8px; border-radius: 999px; background: color-mix(in srgb, currentColor 16%, transparent); }
.vb-explorar__grelha { margin-top: 28px; }
.vb-mais { display: flex; justify-content: center; margin-top: 24px; }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.vb-catalogo :deep(.bg-zinc-900), .vb-catalogo :deep(.bg-white) { background: var(--bg2) !important; }
.vb-catalogo :deep(.bg-zinc-800), .vb-catalogo :deep(.bg-gray-50), .vb-catalogo :deep(.bg-gray-100),
.vb-catalogo :deep(.bg-zinc-700), .vb-catalogo :deep(.bg-gray-200) { background: var(--tom-c) !important; }
.vb-catalogo :deep(.border-zinc-800), .vb-catalogo :deep(.border-zinc-700),
.vb-catalogo :deep(.border-gray-200), .vb-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.vb-catalogo :deep(.text-zinc-100), .vb-catalogo :deep(.text-zinc-900) { color: var(--fg) !important; }
.vb-catalogo :deep(input), .vb-catalogo :deep(select) { color: var(--fg) !important; font-family: var(--fonte); }
.vb-catalogo :deep(input:focus), .vb-catalogo :deep(select:focus) { border-color: var(--cor) !important; outline: none; }
.vb-catalogo :deep(.vb-tab) { background: var(--bg2); color: var(--fg); box-shadow: 0 0 0 1px var(--linha); font-weight: 700; text-transform: capitalize; }
.vb-catalogo :deep(.vb-tab--on) { background: var(--cor) !important; color: #fff !important; font-weight: 700; text-transform: capitalize; }
.vb-catalogo :deep(.vb-cat-borda) { border-color: color-mix(in srgb, var(--cor) 40%, transparent) !important; }
.vb-catalogo :deep(.vb-cat-nome) { font-family: var(--fonte); font-weight: 700; }
.vb-catalogo :deep(.vb-cat-preco) { color: var(--cor) !important; font-weight: 800; }
.vb-catalogo :deep(.vb-cat-badge) { background: var(--cor) !important; color: #fff !important; border-radius: 999px !important; font-weight: 700; }
.vb-catalogo :deep(.vb-cat-indicador) { background: var(--tom-a) !important; color: var(--fg) !important; }
.vb-catalogo :deep(.vb-cat-limpar), .vb-catalogo :deep(.vb-cat-limpar-tudo) { color: var(--cor) !important; }
.vb-catalogo :deep(.vb-cat-spinner) { color: var(--cor) !important; }

/* ── Informação ──────────────────────────────────────────── */
.vb-info { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.vb-info__cartao { padding: 28px; border-radius: var(--raio); }
.vb-info__cartao--a { background: var(--tom-a); }
.vb-info__cartao--b { background: var(--fg); color: var(--bg); }
.vb-info__cartao--c { background: var(--tom-b); }
.vb-info__cartao h3 { margin: 0 0 16px; font-size: 26px; font-weight: 800; letter-spacing: -.02em; }
.vb-info__cartao p { margin: 0; font-size: 16px; line-height: 1.6; }
.vb-info__cartao ul { list-style: none; margin: 0; padding: 0; }
.vb-info__cartao li { display: flex; justify-content: space-between; gap: 12px; padding: 9px 0; border-bottom: 1px solid var(--linha); font-size: 15px; }
.vb-info__cartao li:last-child { border-bottom: none; }
.vb-info__tags { display: flex; flex-wrap: wrap; gap: 8px; }
.vb-info__tags span { padding: 8px 14px; border-radius: 999px; background: color-mix(in srgb, var(--bg) 14%, transparent); font-size: 14px; font-weight: 700; text-transform: capitalize; }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.vb-estrela--on) { color: var(--cor) !important; }
:deep(.vb-estrela--off) { color: var(--linha) !important; }
:deep(.vb-barra) { background: var(--cor) !important; }
:deep(.vb-review) { background: var(--bg2) !important; border: 1px solid var(--linha) !important; }
:deep(.vb-review--minha) { border: 2px solid var(--cor) !important; }
:deep(.vb-btn) { display: inline-flex; padding: 14px 24px; border-radius: 999px; font-weight: 700; }
:deep(.vb-btn--cor) { background: var(--cor) !important; color: #fff !important; }
:deep(.vb-btn--suave) { background: var(--tom-a); color: var(--fg); }

/* ── Rodapé ──────────────────────────────────────────────── */
.vb-footer { padding-top: 80px; padding-bottom: 28px; }
.vb-footer__bloco { padding: 48px; border-radius: 44px; background: var(--fg); color: var(--bg); }
.vb-footer__nome { margin: 0 0 40px; font-size: clamp(2.6rem, 9vw, 7rem); font-weight: 800; letter-spacing: -.045em; line-height: .9; word-break: break-word; }
.vb-footer__linha { display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; font-size: 14px; opacity: .85; }
.vb-footer__links { display: flex; gap: 20px; flex-wrap: wrap; }
.vb-footer__links button { background: none; border: none; color: inherit; font: inherit; font-weight: 700; cursor: pointer; }
.vb-footer__links button:hover { color: var(--cor); }

/* ── Modal ───────────────────────────────────────────────── */
.vb-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.5); }
.vb-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--bg); color: var(--fg); border-radius: var(--raio); }
.vb-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 18px 22px; background: var(--bg); border-bottom: 1px solid var(--linha); }
.vb-modal__painel h3 { margin: 0; font-size: 22px; font-weight: 800; }
.vb-modal__corpo { padding: 22px; font-size: 15px; line-height: 1.7; color: var(--fg2); white-space: pre-wrap; }

.vb-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-size: 28px; font-weight: 800; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .vb-hero__bloco { grid-template-columns: minmax(0, 1fr); padding: 40px; }
  .vb-hero__media { justify-content: flex-start; }
  .vb-autocolante { width: min(100%, 320px); }
  .vb-grelha { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .vb-info { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 640px) {
  .vb-root { --bar-h: 60px; --bar-pad: 14px; --raio: 24px; }
  .vb-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .vb-bar__nome { max-width: 110px; font-size: 14px; }
  .vb-hero__bloco { padding: 28px 22px; border-radius: 32px; }
  .vb-hero__desc { font-size: 16px; }
  .vb-chip { font-size: 13px; padding: 7px 12px; }
  .vb-btn { padding: 13px 20px; font-size: 14px; }
  .vb-selo { width: 88px; height: 88px; }
  .vb-selo__num { font-size: 26px; }
  .vb-faixa__item { font-size: 18px; }
  .vb-sec { padding-top: 56px; }
  .vb-grelha { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .vb-cartao { padding: 8px; gap: 8px; }
  .vb-cartao__info { flex-direction: column; align-items: flex-start; gap: 6px; padding: 0 4px 4px; }
  .vb-cartao__nome { font-size: 14px; }
  .vb-pilulas { flex-direction: column; align-items: stretch; gap: 8px; }
  .vb-pilulas__label { width: auto; }
  .vb-footer__bloco { padding: 32px 24px; border-radius: 32px; }
}
</style>
