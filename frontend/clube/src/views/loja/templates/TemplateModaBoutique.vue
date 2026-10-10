<!-- TemplateModaBoutique.vue — Revamp "boutique de ateliê"
     A loja como uma boutique: montra com o banner e o nome em versais ·
     novidades num carrossel de peças com etiquetas penduradas ·
     "o provador": lista lateral de tipos/categorias que troca a grelha ·
     catálogo completo · informação em cartões com costura · avaliações.
     Tipografia: Marcellus + Jost. Acento: --cor-primaria.
     Faixa de novidades e fundo escuro: --cor-secundaria.
     Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="bt-root" :class="isDark ? 'bt-dark' : 'bt-light'" :style="cssVars">
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
    <div v-if="loading" class="bt-loading">
      <span class="bt-loading__linha"></span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="bt-bar" :class="{ 'bt-bar--solida': scrolled }">
        <button class="bt-circ" @click="$router.back()" aria-label="Voltar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="bt-circ" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="bt-bar__marca">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" />
          <span v-else class="bt-monograma">{{ loja.nome.charAt(0) }}</span>
          <span class="bt-bar__nome">{{ loja.nome }}</span>
        </span>
      </header>

      <!-- ══ MONTRA ══ -->
      <section class="bt-wrap bt-montra">
        <div class="bt-montra__vidro">
          <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" autoplay muted loop playsinline></video>
          <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
          <div v-else class="bt-montra__vazio"></div>
          <div class="bt-montra__sombra"></div>

          <div class="bt-montra__texto">
            <p class="bt-montra__cat">{{ loja.categoria || 'Boutique' }}<template v-if="loja.localizacao"> · {{ loja.localizacao }}</template></p>
            <h1 class="bt-montra__nome">{{ loja.nome }}</h1>
            <div class="bt-montra__ctas">
              <button class="bt-btn bt-btn--claro" @click="scrollToId(totalDestaques ? 'bt-novidades' : 'bt-provador')">
                {{ totalDestaques ? 'Ver novidades' : 'Ver coleção' }}
              </button>
              <button class="bt-btn bt-btn--vidro" @click="scrollToId('bt-catalogo')">Catálogo</button>
            </div>
          </div>

          <div class="bt-etiqueta bt-etiqueta--grande" aria-hidden="true">
            <span class="bt-etiqueta__topo">Coleção</span>
            <span class="bt-etiqueta__valor">{{ totalProdutos ?? '—' }} peças</span>
          </div>
        </div>

        <div class="bt-montra__rodape">
          <p v-if="loja.descricao" class="bt-montra__desc">{{ truncate(loja.descricao, 200) }}</p>
          <div class="bt-montra__dados">
            <span v-if="loja.rating_medio">
              <svg width="13" height="13" viewBox="0 0 20 20" fill="currentColor"><path d="M9.05 2.93c.3-.92 1.6-.92 1.9 0l1.07 3.29a1 1 0 0 0 .95.69h3.46c.97 0 1.37 1.24.59 1.81l-2.8 2.03a1 1 0 0 0-.36 1.12l1.07 3.3c.3.91-.76 1.68-1.54 1.11l-2.8-2.03a1 1 0 0 0-1.18 0l-2.8 2.03c-.78.57-1.84-.2-1.54-1.12l1.07-3.29a1 1 0 0 0-.36-1.12L2.98 8.72c-.78-.57-.38-1.81.59-1.81h3.46a1 1 0 0 0 .95-.69z"/></svg>
              {{ rating }} <small>({{ loja.total_avaliacoes || 0 }})</small>
            </span>
            <span>{{ textoEntrega }}</span>
            <span v-if="metodosPagamento.length">{{ metodosPagamento.length }} formas de pagamento</span>
          </div>
        </div>
      </section>

      <!-- ══ FAIXA ══ -->
      <div v-if="faixa.length" class="bt-faixa">
        <div class="bt-wrap bt-faixa__lista bt-hide-scroll">
          <span v-for="t in faixa" :key="t">{{ t }}</span>
        </div>
      </div>

      <main class="bt-wrap">
        <!-- ══ NOVIDADES (carrossel com scroll infinito) ══ -->
        <section v-if="totalDestaques" id="bt-novidades" class="bt-sec">
          <header class="bt-titulo bt-titulo--linha">
            <div>
              <p class="bt-sobre">Acabadas de chegar</p>
              <h2>Novidades</h2>
            </div>
            <div class="bt-setas">
              <button class="bt-circ" @click="deslizar(-1)" aria-label="Anterior">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button class="bt-circ" @click="deslizar(1)" aria-label="Seguinte">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
              </button>
            </div>
          </header>

          <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="8" :lazy="false" v-slot="l">
            <div ref="carrossel" class="bt-carrossel bt-hide-scroll">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="bt-skel"></div>
              </template>
              <button v-for="p in l.itens" :key="p.id" class="bt-peca bt-peca--carrossel" @click="selectedProduct = p">
                <span class="bt-peca__foto">
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" muted loop autoplay playsinline></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="bt-peca__inicial">{{ p.nome.charAt(0) }}</span>
                  <span v-if="esgotado(p)" class="bt-peca__esgotado">Esgotado</span>
                  <span class="bt-etiqueta"><span class="bt-etiqueta__valor">{{ precoDe(p) }}</span></span>
                </span>
                <span class="bt-peca__nome">{{ p.nome }}</span>
                <span v-if="p.tipo?.nome" class="bt-peca__meta">{{ p.tipo.nome }}</span>
              </button>
              <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                <div class="bt-skel"></div>
              </FimDaLista>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ O PROVADOR (por tipo / por categoria; página a página) ══ -->
        <section v-if="grupos.length" id="bt-provador" class="bt-sec">
          <header class="bt-titulo">
            <p class="bt-sobre">A coleção</p>
            <h2>O provador</h2>
          </header>

          <div class="bt-provador">
            <aside class="bt-cabide">
              <div v-if="modos.length > 1" class="bt-cabide__modo">
                <button v-for="m in modos" :key="m.key" :class="{ 'bt-on': modo === m.key }" @click="mudarModo(m.key)">
                  {{ m.label }}
                </button>
              </div>
              <p v-else-if="modos.length" class="bt-cabide__label">{{ modos[0].label }}</p>

              <div class="bt-cabide__lista bt-hide-scroll">
                <button v-for="g in gruposDoModo" :key="g.key" class="bt-cabide__item"
                        :class="{ 'bt-on': grupoActivo?.key === g.key }" @click="grupoKey = g.key">
                  <span>{{ g.nome }}</span>
                  <small>{{ g.total }}</small>
                </button>
              </div>
            </aside>

            <div v-if="grupoActivo" class="bt-provador__grelha">
              <p class="bt-provador__titulo">
                {{ grupoActivo.nome }} <small>{{ grupoActivo.total }} {{ grupoActivo.total === 1 ? 'peça' : 'peças' }}</small>
              </p>
              <ProdutosPaginados :key="grupoActivo.key" :params="grupoActivo.params" :limit="LIMITE" :lazy="false" v-slot="l">
                <div class="bt-grelha">
                  <template v-if="l.carregando">
                    <div v-for="n in 6" :key="n" class="bt-skel"></div>
                  </template>
                  <button v-for="(p, i) in l.itens" :key="p.id" class="bt-peca"
                          :style="{ animationDelay: (i % LIMITE) * 0.035 + 's' }" @click="selectedProduct = p">
                    <span class="bt-peca__foto">
                      <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" muted playsinline preload="metadata"></video>
                      <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                      <span v-else class="bt-peca__inicial">{{ p.nome.charAt(0) }}</span>
                      <span v-if="esgotado(p)" class="bt-peca__esgotado">Esgotado</span>
                      <span class="bt-etiqueta"><span class="bt-etiqueta__valor">{{ precoDe(p) }}</span></span>
                    </span>
                    <span class="bt-peca__nome">{{ p.nome }}</span>
                    <span v-if="p.variantes?.length" class="bt-peca__meta">{{ p.variantes.length }} variantes</span>
                  </button>
                </div>
                <div v-if="l.temMais || l.aCarregarMais" class="bt-mais">
                  <button class="bt-btn" :disabled="l.aCarregarMais" @click="l.carregarMais()">
                    {{ l.aCarregarMais ? 'A carregar…' : `Ver mais peças (${l.total - l.itens.length})` }}
                  </button>
                </div>
              </ProdutosPaginados>
            </div>
          </div>
        </section>

        <!-- ══ CATÁLOGO ══ -->
        <section id="bt-catalogo" class="bt-sec">
          <header class="bt-titulo">
            <p class="bt-sobre">Todas as peças</p>
            <h2>Catálogo</h2>
          </header>
          <div class="bt-catalogo">
            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="280px"
              card-border-radius="rounded-2xl"
              skeleton-class="rounded-2xl"
              hover-effect="transition-transform duration-300 hover:-translate-y-1"
              hover-border-class=""
              filter-container-radius="rounded-2xl"
              input-border-radius="rounded-full"
              input-focus-class="bt-foco"
              tab-border-radius="rounded-full"
              active-tab-class="bt-tab--on"
              inactive-tab-dark-class="bt-tab"
              inactive-tab-light-class="bt-tab"
              active-sub-tab-class="bt-tab--on"
              inactive-sub-tab-dark-class="bt-tab"
              inactive-sub-tab-light-class="bt-tab"
              category-border-class="bt-cat-borda"
              product-name-class="bt-cat-nome"
              product-name-hover-class=""
              price-class="bt-cat-preco"
              badge-text="Novidade"
              badge-class="bt-cat-badge"
              indicator-active-class="bt-cat-indicador"
              clear-filter-class="bt-cat-limpar"
              clear-all-class="bt-cat-limpar"
              spinner-class="bt-cat-spinner"
              :show-stock="false"
              :show-category-badges="false"
              empty-text="Nenhuma peça encontrada."
              @product-click="selectedProduct = $event"
            />
          </div>
        </section>

        <!-- ══ A BOUTIQUE (informação) ══ -->
        <section id="bt-info" class="bt-sec">
          <header class="bt-titulo">
            <p class="bt-sobre">Antes de comprar</p>
            <h2>A boutique</h2>
          </header>
          <div class="bt-info">
            <div class="bt-costura">
              <p class="bt-costura__titulo">Entrega</p>
              <ul v-if="opcoesEntrega.length || loja.levantamento_ativo">
                <li v-for="o in opcoesEntrega" :key="o.id">
                  <span>{{ o.nome }}</span><b>{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</b>
                </li>
                <li v-if="loja.levantamento_ativo"><span>Levantamento na loja</span><b>Grátis</b></li>
              </ul>
              <p v-else>Contacte a boutique.</p>
            </div>
            <div class="bt-costura">
              <p class="bt-costura__titulo">Pagamento</p>
              <div v-if="metodosPagamento.length" class="bt-costura__tags">
                <span v-for="m in metodosPagamento" :key="m.id">{{ m.tipo }}</span>
              </div>
              <p v-else>—</p>
            </div>
            <div class="bt-costura">
              <p class="bt-costura__titulo">Onde estamos</p>
              <p v-if="loja.localizacao" class="bt-costura__morada">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ loja.localizacao }}
              </p>
              <p v-else>Boutique online.</p>
            </div>
          </div>
        </section>

        <!-- ══ AVALIAÇÕES ══ -->
        <section id="bt-avaliacoes" class="bt-sec">
          <header class="bt-titulo">
            <p class="bt-sobre">Quem já comprou</p>
            <h2>Avaliações</h2>
          </header>
          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-2xl"
            form-border-radius="rounded-2xl"
            review-card-border-radius="rounded-2xl"
            button-border-radius="rounded-full"
            textarea-border-radius="rounded-xl"
            :star-active-class="'bt-estrela--on'"
            :star-inactive-class="'bt-estrela--off'"
            progress-bar-class="bt-barra"
            :submit-button-class="'bt-btn bt-btn--cheio w-full justify-center'"
            :review-card-class="'bt-review'"
            :own-review-border-class="'bt-review--minha'"
            :load-more-button-class="'bt-btn'"
            @rating-updated="onRatingUpdated"
          />
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="bt-footer">
        <div class="bt-wrap bt-footer__inner">
          <span class="bt-monograma bt-monograma--grande">{{ loja.nome.charAt(0) }}</span>
          <p class="bt-footer__nome">{{ loja.nome }}</p>
          <nav class="bt-footer__links">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
          </nav>
          <p class="bt-footer__copy">© {{ ano }} {{ loja.nome }}<template v-if="loja.localizacao"> · {{ loja.localizacao }}</template></p>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="bt-modal" @click.self="modalPolitica = null">
        <div class="bt-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="bt-circ" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="bt-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="bt-vazio">
      <p>Loja não encontrada</p>
      <button class="bt-btn bt-btn--cheio" @click="$router.back()">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import ProdutosPaginados from '@/components/produtos/ProdutosPaginados.vue'
import FimDaLista from '@/components/produtos/FimDaLista.vue'
import { useLojaData } from '@/composables/useLojaData'
import ProductInfoCard from '@/components/product/productInfoCard.vue'
import MultiCart from '@/components/cart/multiCart.vue'
import Profile from '@/components/profile/UserProfile.vue'
import ProductCatalog from '@/components/catalog/ProductCatalog.vue'
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

const LIMITE = 9

export default {
  name: 'TemplateModaBoutique',

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
    const carrossel = ref(null)
    const modoEscolhido = ref(null)
    const grupoKey = ref(null)

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#b4637a',
      '--cor-secundaria': props.tema?.corSecundaria || '#1f1a1d',
    }))

    // ── Provador (só metadados; as peças vêm página a página) ──
    const grupos = lojaData.gruposProdutos

    const modos = computed(() => [
      { key: 'tipo', label: 'Por tipo' },
      { key: 'categoria', label: 'Por categoria' },
      { key: 'todos', label: 'Todas as peças' },
    ].filter(m => grupos.value.some(g => g.seccao === m.key)))

    // modo e grupo escolhidos, ou o primeiro disponível
    const modo = computed(() =>
      modos.value.some(m => m.key === modoEscolhido.value) ? modoEscolhido.value : modos.value[0]?.key)

    const gruposDoModo = computed(() => grupos.value.filter(g => g.seccao === modo.value))

    const grupoActivo = computed(() =>
      gruposDoModo.value.find(g => g.key === grupoKey.value) || gruposDoModo.value[0] || null)

    function mudarModo (m) {
      modoEscolhido.value = m
      grupoKey.value = null
    }

    function deslizar (dir) {
      const el = carrossel.value
      if (el) el.scrollBy({ left: dir * el.clientWidth * 0.8, behavior: 'smooth' })
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
        return min === 0 ? 'Entrega gratuita' : `Entrega desde ${lojaData.formatPrice(min)}`
      }
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento na loja' : 'Consulte a entrega'
    })

    // faixa com as categorias da loja (ou dados da loja, se não houver)
    const faixa = computed(() => {
      const cats = lojaData.categoriasExistentes.value.map(c => c.nome)
      if (cats.length) return cats.slice(0, 10)
      const l = lojaData.loja.value
      return l ? [textoEntrega.value, l.localizacao].filter(Boolean) : []
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
      LIMITE,
      isDark, user, ano, cssVars,
      scrolled, carrossel,
      grupos, modos, modo, gruposDoModo, grupoKey, grupoActivo,
      mudarModo, deslizar,
      rating, textoEntrega, faixa, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, precoDe,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.bt-root {
  --cor: var(--cor-primaria, #b4637a);
  --display: 'Marcellus', Georgia, serif;
  --sans: 'Jost', system-ui, sans-serif;
  --raio: 20px;
  --bar-h: 68px;
  --bar-pad: 28px;
  /* carrinho · notificações · perfil alinhados com a barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--sans);
  font-weight: 400;
  background: var(--bg);
  color: var(--tinta);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .4s, color .4s;
}
.bt-light {
  --bg: #faf5f2;
  --papel: #ffffff;
  --tinta: #2b2326;
  --tinta2: #7b6d70;
  --linha: rgba(43, 35, 38, .12);
  --suave: color-mix(in srgb, var(--cor) 9%, #faf5f2);
  --faixa: var(--cor-secundaria, #1f1a1d);
  --acento: var(--cor);
}
.bt-dark {
  --bg: var(--cor-secundaria, #1f1a1d);
  --papel: color-mix(in srgb, var(--bg) 90%, #fff 10%);
  --tinta: #f6eef0;
  --tinta2: #b7a9ad;
  --linha: rgba(246, 238, 240, .13);
  --suave: color-mix(in srgb, var(--cor) 14%, var(--bg));
  --faixa: color-mix(in srgb, var(--cor) 30%, var(--bg));
  /* acento legível sobre fundo escuro */
  --acento: color-mix(in srgb, var(--cor) 70%, #fff 30%);
}

.bt-wrap { max-width: 1320px; margin: 0 auto; padding: 0 var(--bar-pad); }
.bt-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.bt-hide-scroll::-webkit-scrollbar { display: none; }

/* ── Loading ─────────────────────────────────────────────── */
.bt-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; align-items: center; justify-content: center; }
.bt-loading__linha { width: 120px; height: 1px; background: var(--linha); position: relative; overflow: hidden; }
.bt-loading__linha::after { content: ''; position: absolute; inset: 0; width: 40%; background: var(--acento); animation: btCorre 1.1s ease-in-out infinite; }
@keyframes btCorre { from { transform: translateX(-100%); } to { transform: translateX(260%); } }

/* ── Barra ───────────────────────────────────────────────── */
.bt-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center; gap: 8px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 12px) 0 var(--bar-pad);
  transition: background .3s, box-shadow .3s;
}
.bt-bar--solida { background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(10px); box-shadow: 0 1px 0 var(--linha); }
.bt-circ {
  width: 38px; height: 38px; flex-shrink: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--papel); color: var(--tinta); border: 1px solid var(--linha); cursor: pointer;
  transition: background .2s, color .2s, border-color .2s;
}
.bt-circ:hover { background: var(--tinta); color: var(--bg); border-color: var(--tinta); }
.bt-bar__marca { display: flex; align-items: center; gap: 10px; min-width: 0; margin-left: 8px; }
.bt-bar__marca img { width: 30px; height: 30px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.bt-bar__nome {
  font-family: var(--display); font-size: 17px; letter-spacing: .14em; text-transform: uppercase;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bt-monograma {
  width: 30px; height: 30px; flex-shrink: 0; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--acento); color: var(--acento); font-family: var(--display); font-size: 15px;
}
.bt-monograma--grande { width: 64px; height: 64px; font-size: 30px; margin: 0 auto; }

/* ── Montra ──────────────────────────────────────────────── */
.bt-montra { padding-top: var(--bar-h); }
.bt-montra__vidro {
  position: relative; height: min(78vh, 720px); min-height: 460px; border-radius: 28px; overflow: hidden;
  background: var(--suave);
}
.bt-montra__vidro > img, .bt-montra__vidro > video { width: 100%; height: 100%; object-fit: cover; display: block; }
.bt-montra__vazio { width: 100%; height: 100%; background: linear-gradient(140deg, var(--suave), color-mix(in srgb, var(--cor) 45%, var(--bg))); }
.bt-montra__sombra { position: absolute; inset: 0; background: linear-gradient(to top, rgba(20, 14, 16, .72), rgba(20, 14, 16, .1) 55%, transparent); }
.bt-montra__texto { position: absolute; left: 48px; right: 48px; bottom: 44px; color: #fff; }
.bt-montra__cat { margin: 0 0 14px; font-size: 13px; font-weight: 500; letter-spacing: .28em; text-transform: uppercase; opacity: .85; }
.bt-montra__nome {
  margin: 0 0 26px; font-family: var(--display); font-weight: 400; font-size: clamp(2.8rem, 8vw, 7.5rem);
  line-height: .95; letter-spacing: .04em; text-transform: uppercase; text-wrap: balance;
}
.bt-montra__ctas { display: flex; flex-wrap: wrap; gap: 10px; }
.bt-montra__rodape { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px 48px; flex-wrap: wrap; padding: 28px 4px 0; }
.bt-montra__desc { margin: 0; max-width: 620px; font-size: 18px; font-weight: 300; line-height: 1.6; color: var(--tinta2); }
.bt-montra__dados { display: flex; flex-wrap: wrap; gap: 8px; }
.bt-montra__dados span {
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 999px;
  border: 1px solid var(--linha); font-size: 13px; font-weight: 500;
}
.bt-montra__dados svg { color: var(--acento); }
.bt-montra__dados small { color: var(--tinta2); }

.bt-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 13px 26px; border-radius: 999px;
  font-family: var(--sans); font-size: 13px; font-weight: 500; letter-spacing: .16em; text-transform: uppercase;
  cursor: pointer; background: transparent; color: var(--tinta); border: 1px solid var(--tinta);
  transition: background .25s, color .25s, border-color .25s;
}
.bt-btn:hover { background: var(--tinta); color: var(--bg); }
.bt-btn--claro { background: #fff; color: #2b2326; border-color: #fff; }
.bt-btn--claro:hover { background: var(--cor); border-color: var(--cor); color: #fff; }
.bt-btn--vidro { color: #fff; border-color: rgba(255,255,255,.6); backdrop-filter: blur(6px); }
.bt-btn--vidro:hover { background: #fff; color: #2b2326; }
.bt-btn--cheio { background: var(--cor); border-color: var(--cor); color: #fff; }

/* ── Etiqueta pendurada (forma CSS) ──────────────────────── */
.bt-etiqueta {
  position: absolute; top: 14px; right: 14px; z-index: 1;
  display: flex; flex-direction: column; align-items: flex-start;
  padding: 7px 12px 7px 20px; background: var(--papel); color: var(--tinta);
  clip-path: polygon(10px 0, 100% 0, 100% 100%, 10px 100%, 0 50%);
  transform: rotate(5deg); transform-origin: left center;
  box-shadow: 0 6px 16px rgba(0,0,0,.12);
  transition: transform .4s cubic-bezier(.2,.8,.2,1);
}
.bt-etiqueta::before {
  /* furo da etiqueta */
  content: ''; position: absolute; left: 8px; top: 50%; width: 5px; height: 5px; margin-top: -2.5px;
  border-radius: 50%; background: var(--bg); box-shadow: inset 0 0 0 1px var(--linha);
}
.bt-etiqueta__topo { font-size: 10px; font-weight: 500; letter-spacing: .2em; text-transform: uppercase; color: var(--tinta2); }
.bt-etiqueta__valor { font-family: var(--display); font-size: 15px; white-space: nowrap; }
.bt-etiqueta--grande { top: 32px; right: 36px; padding: 12px 20px 12px 28px; transform: rotate(-6deg); }
.bt-etiqueta--grande::before { left: 11px; width: 7px; height: 7px; margin-top: -3.5px; }
.bt-etiqueta--grande .bt-etiqueta__valor { font-size: 24px; }

/* ── Faixa ───────────────────────────────────────────────── */
.bt-faixa { margin-top: 40px; background: var(--faixa); color: #f6eef0; }
.bt-faixa__lista { display: flex; justify-content: safe center; gap: 0; overflow-x: auto; padding-top: 16px; padding-bottom: 16px; }
.bt-faixa__lista span {
  flex-shrink: 0; font-family: var(--display); font-size: 15px; letter-spacing: .2em; text-transform: uppercase; white-space: nowrap;
}
.bt-faixa__lista span + span::before { content: ''; display: inline-block; width: 5px; height: 5px; margin: 0 22px 3px; border-radius: 50%; background: var(--cor); }

/* ── Secções ─────────────────────────────────────────────── */
.bt-sec { padding-top: 96px; scroll-margin-top: calc(var(--bar-h) + 8px); }
.bt-titulo { margin-bottom: 36px; text-align: center; }
.bt-titulo h2 { margin: 8px 0 0; font-family: var(--display); font-weight: 400; font-size: clamp(2.2rem, 4.5vw, 3.4rem); line-height: 1; letter-spacing: .03em; }
.bt-titulo--linha { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; text-align: left; }
.bt-sobre { margin: 0; font-size: 12px; font-weight: 500; letter-spacing: .28em; text-transform: uppercase; color: var(--acento); }
.bt-setas { display: flex; gap: 8px; }

/* ── Peças ───────────────────────────────────────────────── */
.bt-peca {
  display: flex; flex-direction: column; gap: 4px; padding: 0; text-align: left; min-width: 0;
  background: none; border: none; cursor: pointer; color: inherit; font: inherit;
  animation: btEntra .5s both;
}
@keyframes btEntra { from { opacity: 0; transform: translateY(10px); } }
.bt-peca__foto {
  position: relative; display: block; aspect-ratio: 3 / 4; margin-bottom: 10px;
  border-radius: var(--raio); overflow: hidden; background: var(--suave);
}
.bt-peca__foto img, .bt-peca__foto video { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .7s cubic-bezier(.2,.8,.2,1); }
.bt-peca:hover .bt-peca__foto img, .bt-peca:hover .bt-peca__foto video { transform: scale(1.05); }
.bt-peca:hover .bt-etiqueta { transform: rotate(-3deg); }
.bt-peca__inicial { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-family: var(--display); font-size: 64px; color: var(--acento); }
.bt-peca__esgotado {
  position: absolute; left: 0; right: 0; bottom: 0; padding: 9px; text-align: center;
  background: color-mix(in srgb, var(--bg) 85%, transparent); backdrop-filter: blur(4px);
  font-size: 11px; font-weight: 500; letter-spacing: .24em; text-transform: uppercase;
}
.bt-peca__nome { font-size: 13px; font-weight: 500; letter-spacing: .14em; text-transform: uppercase; line-height: 1.4; }
.bt-peca__meta { font-size: 13px; color: var(--tinta2); text-transform: capitalize; }

.bt-carrossel {
  display: grid; grid-auto-flow: column; grid-auto-columns: calc((100% - 3 * 20px) / 4); gap: 20px;
  overflow-x: auto; scroll-snap-type: x mandatory; scroll-padding: 0;
}
.bt-peca--carrossel { scroll-snap-align: start; }

/* ── O provador ──────────────────────────────────────────── */
.bt-provador { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 48px; align-items: start; }
.bt-cabide { position: sticky; top: calc(var(--bar-h) + 16px); }
.bt-cabide__modo { display: flex; gap: 4px; padding: 4px; margin-bottom: 18px; border-radius: 999px; border: 1px solid var(--linha); }
.bt-cabide__modo button {
  flex: 1; padding: 8px 6px; border-radius: 999px; border: none; background: none; cursor: pointer;
  font: inherit; font-size: 12px; font-weight: 500; color: var(--tinta2); white-space: nowrap;
}
.bt-cabide__modo .bt-on { background: var(--tinta); color: var(--bg); }
.bt-cabide__label { margin: 0 0 14px; font-size: 12px; font-weight: 500; letter-spacing: .24em; text-transform: uppercase; color: var(--tinta2); }
.bt-cabide__lista { display: flex; flex-direction: column; }
.bt-cabide__item {
  position: relative; display: flex; justify-content: space-between; align-items: baseline; gap: 10px;
  padding: 12px 0 12px 18px; background: none; border: none; border-bottom: 1px solid var(--linha);
  cursor: pointer; text-align: left; color: var(--tinta2); font-family: var(--display); font-size: 19px;
  text-transform: capitalize; transition: color .2s, padding .3s;
}
.bt-cabide__item::before {
  /* o "gancho" do cabide marca o grupo escolhido */
  content: ''; position: absolute; left: 0; top: 50%; width: 8px; height: 8px; margin-top: -4px;
  border-radius: 50%; border: 1px solid var(--linha); transition: background .2s, border-color .2s;
}
.bt-cabide__item small { font-family: var(--sans); font-size: 12px; }
.bt-cabide__item:hover { color: var(--tinta); }
.bt-cabide__item.bt-on { color: var(--tinta); padding-left: 24px; }
.bt-cabide__item.bt-on::before { background: var(--acento); border-color: var(--acento); }

.bt-provador__titulo { margin: 0 0 22px; font-family: var(--display); font-size: 30px; text-transform: capitalize; }
.bt-provador__titulo small { margin-left: 8px; font-family: var(--sans); font-size: 13px; color: var(--tinta2); text-transform: none; }
.bt-grelha { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 36px 22px; }
.bt-skel { aspect-ratio: 3 / 4; border-radius: var(--raio); background: var(--suave); animation: btPulso 1.3s ease-in-out infinite; }
@keyframes btPulso { 50% { opacity: .5; } }
.bt-mais { display: flex; justify-content: center; margin-top: 36px; }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.bt-catalogo :deep(.bg-zinc-900), .bt-catalogo :deep(.bg-white) { background: var(--papel) !important; }
.bt-catalogo :deep(.bg-zinc-800), .bt-catalogo :deep(.bg-gray-50), .bt-catalogo :deep(.bg-gray-100),
.bt-catalogo :deep(.bg-zinc-700), .bt-catalogo :deep(.bg-gray-200) { background: var(--suave) !important; }
.bt-catalogo :deep(.border-zinc-800), .bt-catalogo :deep(.border-zinc-700),
.bt-catalogo :deep(.border-gray-200), .bt-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.bt-catalogo :deep(.text-zinc-100), .bt-catalogo :deep(.text-zinc-900) { color: var(--tinta) !important; }
.bt-catalogo :deep(input), .bt-catalogo :deep(select) { color: var(--tinta) !important; font-family: var(--sans); }
.bt-catalogo :deep(input:focus), .bt-catalogo :deep(select:focus) { border-color: var(--acento) !important; outline: none; }
.bt-catalogo :deep(.bt-tab) { background: transparent; color: var(--tinta2); border: 1px solid var(--linha); font-weight: 500; text-transform: capitalize; }
.bt-catalogo :deep(.bt-tab--on) { background: var(--tinta) !important; color: var(--bg) !important; font-weight: 500; text-transform: capitalize; }
.bt-catalogo :deep(.bt-cat-borda) { border-color: var(--linha) !important; }
.bt-catalogo :deep(.bt-cat-nome) { font-family: var(--sans); font-size: 13px; font-weight: 500; letter-spacing: .12em; text-transform: uppercase; }
.bt-catalogo :deep(.bt-cat-preco) { color: var(--acento) !important; font-family: var(--display); font-size: 16px; }
.bt-catalogo :deep(.bt-cat-badge) { background: var(--cor) !important; color: #fff !important; border-radius: 999px !important; letter-spacing: .1em; }
.bt-catalogo :deep(.bt-cat-indicador) { background: var(--suave) !important; color: var(--tinta) !important; }
.bt-catalogo :deep(.bt-cat-limpar) { color: var(--acento) !important; }
.bt-catalogo :deep(.bt-cat-spinner) { color: var(--acento) !important; }

/* ── A boutique (cartões com costura) ───────────────────── */
.bt-info { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.bt-costura { position: relative; padding: 34px 30px; border-radius: var(--raio); background: var(--suave); }
.bt-costura::before {
  /* pesponto */
  content: ''; position: absolute; inset: 8px; border-radius: calc(var(--raio) - 6px);
  border: 1.5px dashed color-mix(in srgb, var(--acento) 45%, transparent); pointer-events: none;
}
.bt-costura__titulo { margin: 0 0 16px; font-family: var(--display); font-size: 26px; }
.bt-costura p { margin: 0; font-size: 16px; line-height: 1.6; color: var(--tinta2); }
.bt-costura ul { list-style: none; margin: 0; padding: 0; }
.bt-costura li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 15px; border-bottom: 1px solid var(--linha); }
.bt-costura li:last-child { border-bottom: none; }
.bt-costura li b { font-weight: 500; color: var(--acento); }
.bt-costura__tags { display: flex; flex-wrap: wrap; gap: 8px; }
.bt-costura__tags span { padding: 7px 14px; border-radius: 999px; background: var(--papel); font-size: 13px; font-weight: 500; text-transform: capitalize; }
.bt-costura__morada { display: flex; gap: 8px; align-items: flex-start; }
.bt-costura__morada svg { flex-shrink: 0; margin-top: 4px; color: var(--acento); }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.bt-estrela--on) { color: var(--acento) !important; }
:deep(.bt-estrela--off) { color: var(--linha) !important; }
:deep(.bt-barra) { background: var(--acento) !important; }
:deep(.bt-review) { background: var(--papel) !important; border: 1px solid var(--linha) !important; }
:deep(.bt-review--minha) { border: 1px solid var(--acento) !important; }
:deep(.bt-btn) { display: inline-flex; padding: 12px 24px; border-radius: 999px; font-weight: 500; letter-spacing: .14em; text-transform: uppercase; font-size: 13px; border: 1px solid var(--tinta); }
:deep(.bt-btn--cheio) { background: var(--cor) !important; border-color: var(--cor) !important; color: #fff !important; }

/* ── Rodapé ──────────────────────────────────────────────── */
.bt-footer { margin-top: 110px; padding: 64px 0 36px; background: var(--faixa); color: #f6eef0; }
.bt-footer .bt-monograma { border-color: rgba(246, 238, 240, .5); color: #f6eef0; }
.bt-footer__inner { text-align: center; }
.bt-footer__nome { margin: 20px 0 0; font-family: var(--display); font-size: clamp(2rem, 5vw, 3.2rem); letter-spacing: .16em; text-transform: uppercase; }
.bt-footer__links { display: flex; justify-content: center; flex-wrap: wrap; gap: 8px 28px; margin: 28px 0 18px; }
.bt-footer__links button { background: none; border: none; cursor: pointer; color: inherit; font: inherit; font-size: 12px; font-weight: 500; letter-spacing: .22em; text-transform: uppercase; opacity: .8; }
.bt-footer__links button:hover { opacity: 1; text-decoration: underline; text-underline-offset: 5px; }
.bt-footer__copy { margin: 0; font-size: 13px; opacity: .6; }

/* ── Modal ───────────────────────────────────────────────── */
.bt-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.5); }
.bt-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--papel); color: var(--tinta); border-radius: var(--raio); }
.bt-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 18px 22px; background: var(--papel); border-bottom: 1px solid var(--linha); }
.bt-modal__painel h3 { margin: 0; font-family: var(--display); font-size: 24px; font-weight: 400; }
.bt-modal__corpo { padding: 22px; font-size: 15px; line-height: 1.7; color: var(--tinta2); white-space: pre-wrap; }

.bt-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-family: var(--display); font-size: 28px; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .bt-carrossel { grid-auto-columns: calc((100% - 2 * 20px) / 3); }
  .bt-provador { grid-template-columns: minmax(0, 1fr); gap: 24px; }
  .bt-cabide { position: static; }
  .bt-cabide__modo { max-width: 320px; }
  .bt-cabide__lista { flex-direction: row; gap: 8px; overflow-x: auto; }
  .bt-cabide__item {
    flex-shrink: 0; padding: 9px 16px; border: 1px solid var(--linha); border-radius: 999px; font-size: 16px; white-space: nowrap;
  }
  .bt-cabide__item::before { display: none; }
  .bt-cabide__item.bt-on { padding-left: 16px; background: var(--tinta); color: var(--bg); border-color: var(--tinta); }
  .bt-info { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 640px) {
  .bt-root { --bar-h: 60px; --bar-pad: 14px; --raio: 16px; }
  .bt-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .bt-circ { width: 34px; height: 34px; }
  .bt-bar__nome { font-size: 14px; letter-spacing: .1em; }
  .bt-bar__marca img, .bt-bar .bt-monograma { display: none; }
  .bt-montra__vidro { height: 72vh; min-height: 420px; border-radius: 20px; }
  .bt-montra__texto { left: 22px; right: 22px; bottom: 26px; }
  .bt-etiqueta--grande { top: 18px; right: 18px; padding: 9px 14px 9px 24px; }
  .bt-etiqueta--grande .bt-etiqueta__valor { font-size: 18px; }
  .bt-montra__desc { font-size: 16px; }
  .bt-faixa__lista { justify-content: flex-start; }
  .bt-sec { padding-top: 72px; }
  .bt-titulo--linha { align-items: center; }
  .bt-carrossel { grid-auto-columns: 70%; gap: 14px; }
  .bt-grelha { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 26px 12px; }
  .bt-etiqueta { top: 10px; right: 10px; padding: 5px 9px 5px 17px; }
  .bt-etiqueta__valor { font-size: 13px; }
  .bt-peca__nome { font-size: 12px; letter-spacing: .1em; }
  .bt-costura { padding: 28px 24px; }
}
</style>
