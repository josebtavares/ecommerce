<!-- TemplateRestauranteBistro.vue — Revamp "carta de bistrô"
     A loja como uma carta impressa: capa emoldurada com janela em arco ·
     ardósia com as sugestões do chef (escrita a giz) · carta em capítulos numerados
     com linhas pontilhadas entre prato e preço, organizada por tipo ou por categoria ·
     catálogo completo · informação em colunas · livro de visitas.
     Tipografia: Cormorant Garamond + Karla (+ Caveat na ardósia).
     Acento: --cor-primaria. Ardósia e fundo escuro: --cor-secundaria.
     Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="bs-root" :class="isDark ? 'bs-dark' : 'bs-light'" :style="cssVars">
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
    <div v-if="loading" class="bs-loading">
      <span class="bs-loading__nome">a preparar a carta…</span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="bs-bar" :class="{ 'bs-bar--papel': scrolled }">
        <button class="bs-circ" @click="$router.back()" aria-label="Voltar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="bs-circ" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="bs-bar__nome" :class="{ 'bs-bar__nome--on': scrolled }">{{ loja.nome }}</span>
      </header>

      <!-- ══ CAPA ══ -->
      <section class="bs-wrap bs-capa">
        <div class="bs-capa__moldura">
          <div class="bs-capa__texto">
            <p class="bs-versal">{{ loja.categoria || 'Bistrô' }}<template v-if="loja.localizacao"> · {{ loja.localizacao }}</template></p>
            <h1 class="bs-capa__nome">{{ loja.nome }}</h1>
            <div class="bs-orn" aria-hidden="true"><span></span><i></i><span></span></div>
            <p v-if="loja.descricao" class="bs-capa__desc">{{ truncate(loja.descricao, 220) }}</p>

            <div class="bs-capa__meta">
              <span v-if="loja.rating_medio" class="bs-capa__rating">
                <svg v-for="n in 5" :key="n" width="13" height="13" viewBox="0 0 20 20"
                     :fill="n <= Math.round(loja.rating_medio) ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.2">
                  <path d="M9.05 2.93c.3-.92 1.6-.92 1.9 0l1.07 3.29a1 1 0 0 0 .95.69h3.46c.97 0 1.37 1.24.59 1.81l-2.8 2.03a1 1 0 0 0-.36 1.12l1.07 3.3c.3.91-.76 1.68-1.54 1.11l-2.8-2.03a1 1 0 0 0-1.18 0l-2.8 2.03c-.78.57-1.84-.2-1.54-1.12l1.07-3.29a1 1 0 0 0-.36-1.12L2.98 8.72c-.78-.57-.38-1.81.59-1.81h3.46a1 1 0 0 0 .95-.69z"/>
                </svg>
                <em>{{ rating }} · {{ loja.total_avaliacoes || 0 }} avaliações</em>
              </span>
              <span>{{ textoEntrega }}</span>
            </div>

            <div class="bs-capa__ctas">
              <button class="bs-btn bs-btn--cheio" @click="scrollToId('bs-carta')">Ver a carta</button>
              <button class="bs-btn" @click="scrollToId('bs-catalogo')">Catálogo completo</button>
            </div>
          </div>

          <div class="bs-arco">
            <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" v-video-visivel muted loop playsinline></video>
            <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
            <div v-else class="bs-arco__vazio">{{ loja.nome.charAt(0) }}</div>
          </div>
        </div>
      </section>

      <main class="bs-wrap">
        <!-- ══ ARDÓSIA · SUGESTÕES DO CHEF (uma página de destaques) ══ -->
        <section v-if="totalDestaques" id="bs-sugestoes" class="bs-sec">
          <div class="bs-ardosia">
            <p class="bs-ardosia__titulo">Sugestões do chef</p>
            <p class="bs-ardosia__sub">hoje, na nossa ardósia</p>
            <ProdutosPaginados tag="ul" class="bs-ardosia__lista" :params="{ loja_id: lojaId, destaque: 'true' }"
                               :limit="8" :lazy="false" v-slot="l">
              <li v-for="p in l.itens" :key="p.id">
                <button class="bs-ardosia__item" @click="selectedProduct = p">
                  <span class="bs-ardosia__nome">{{ p.nome }}</span>
                  <span class="bs-pontos"></span>
                  <span class="bs-ardosia__preco">{{ precoDe(p) }}</span>
                </button>
                <p v-if="p.descricao" class="bs-ardosia__desc">{{ truncate(p.descricao, 80) }}</p>
              </li>
            </ProdutosPaginados>
          </div>
        </section>

        <!-- ══ A CARTA (cada capítulo pede os seus pratos página a página) ══ -->
        <section v-if="grupos.length" id="bs-carta" class="bs-sec">
          <header class="bs-titulo">
            <p class="bs-versal">A carta</p>
            <h2>{{ modos.find(m => m.key === modo)?.label }}</h2>
            <div v-if="modos.length > 1" class="bs-modo" role="tablist">
              <button v-for="m in modos" :key="m.key" role="tab" :aria-selected="modo === m.key"
                      :class="{ 'bs-modo--on': modo === m.key }" @click="modoEscolhido = m.key">
                {{ m.label }}
              </button>
            </div>
          </header>

          <nav v-if="capitulos.length > 1" class="bs-indice bs-hide-scroll">
            <button v-for="(c, i) in capitulos" :key="c.key" @click="scrollToId('bs-cap-' + c.key)">
              <span>{{ romano(i + 1) }}.</span> {{ c.nome }}
            </button>
          </nav>

          <article v-for="(c, i) in capitulos" :key="c.key" :id="'bs-cap-' + c.key" class="bs-capitulo">
            <header class="bs-capitulo__head">
              <span class="bs-capitulo__num">{{ romano(i + 1) }}</span>
              <h3>{{ c.nome }}</h3>
              <span class="bs-capitulo__n">{{ c.total }} {{ c.total === 1 ? 'opção' : 'opções' }}</span>
            </header>

            <ProdutosPaginados :params="c.params" :limit="LIMITE" v-slot="l">
              <div class="bs-pratos">
                <template v-if="l.carregando">
                  <div v-for="n in Math.min(c.total, LIMITE)" :key="n" class="bs-skel"></div>
                </template>
                <button v-for="p in l.itens" :key="p.id" class="bs-prato"
                        :class="{ 'bs-prato--esgotado': esgotado(p) }" @click="selectedProduct = p">
                  <span class="bs-prato__foto">
                    <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                    <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                    <span v-else>{{ p.nome.charAt(0) }}</span>
                  </span>
                  <span class="bs-prato__corpo">
                    <span class="bs-prato__linha">
                      <span class="bs-prato__nome">{{ p.nome }}</span>
                      <span class="bs-pontos"></span>
                      <span class="bs-prato__preco">{{ precoDe(p) }}</span>
                    </span>
                    <span v-if="p.descricao || esgotado(p)" class="bs-prato__desc">
                      <em v-if="esgotado(p)" class="bs-prato__tag">Esgotado</em>
                      {{ truncate(p.descricao, 100) }}
                    </span>
                  </span>
                </button>
              </div>

              <button v-if="l.temMais || l.aCarregarMais" class="bs-ver-todos" :disabled="l.aCarregarMais" @click="l.carregarMais()">
                {{ l.aCarregarMais ? 'A carregar…' : `Ver mais ${Math.min(LIMITE, l.total - l.itens.length)} de ${l.total - l.itens.length}` }}
              </button>
            </ProdutosPaginados>
          </article>
        </section>

        <!-- ══ CATÁLOGO ══ -->
        <section id="bs-catalogo" class="bs-sec">
          <header class="bs-titulo">
            <p class="bs-versal">Tudo o que servimos</p>
            <h2>Catálogo completo</h2>
          </header>
          <div class="bs-catalogo">
            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="200px"
              card-border-radius="rounded-sm"
              skeleton-class="rounded-sm"
              hover-effect="transition-transform duration-300 hover:-translate-y-0.5"
              hover-border-class=""
              filter-container-radius="rounded-sm"
              input-border-radius="rounded-sm"
              input-focus-class="bs-foco"
              tab-border-radius="rounded-full"
              active-tab-class="bs-tab--on"
              inactive-tab-dark-class="bs-tab"
              inactive-tab-light-class="bs-tab"
              active-sub-tab-class="bs-tab--on"
              inactive-sub-tab-dark-class="bs-tab"
              inactive-sub-tab-light-class="bs-tab"
              category-border-class="bs-cat-borda"
              product-name-class="bs-cat-nome"
              product-name-hover-class=""
              price-class="bs-cat-preco"
              badge-text="Sugestão"
              badge-class="bs-cat-badge"
              indicator-active-class="bs-cat-indicador"
              clear-filter-class="bs-cat-limpar"
              clear-all-class="bs-cat-limpar"
              spinner-class="bs-cat-spinner"
              :show-stock="false"
              :show-category-badges="false"
              empty-text="Nenhum prato encontrado."
              @product-click="selectedProduct = $event"
            />
          </div>
        </section>

        <!-- ══ INFORMAÇÃO ══ -->
        <section id="bs-info" class="bs-sec bs-info">
          <div class="bs-info__col">
            <p class="bs-versal">Entrega</p>
            <ul v-if="opcoesEntrega.length || loja.levantamento_ativo">
              <li v-for="o in opcoesEntrega" :key="o.id">
                <span>{{ o.nome }}</span><span class="bs-pontos"></span><b>{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</b>
              </li>
              <li v-if="loja.levantamento_ativo"><span>Levantamento</span><span class="bs-pontos"></span><b>Grátis</b></li>
            </ul>
            <p v-else>Fale connosco.</p>
          </div>
          <div class="bs-info__col">
            <p class="bs-versal">Pagamento</p>
            <p v-if="metodosPagamento.length" class="bs-info__metodos">
              <template v-for="(m, i) in metodosPagamento" :key="m.id">
                <span>{{ m.tipo }}</span><i v-if="i < metodosPagamento.length - 1"> · </i>
              </template>
            </p>
            <p v-else>—</p>
          </div>
          <div class="bs-info__col">
            <p class="bs-versal">Visite-nos</p>
            <p v-if="loja.localizacao" class="bs-info__morada">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              {{ loja.localizacao }}
            </p>
            <p v-else>Encomende online.</p>
          </div>
        </section>

        <!-- ══ LIVRO DE VISITAS ══ -->
        <section id="bs-avaliacoes" class="bs-sec">
          <header class="bs-titulo">
            <p class="bs-versal">Livro de visitas</p>
            <h2>Avaliações</h2>
          </header>
          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-sm"
            form-border-radius="rounded-sm"
            review-card-border-radius="rounded-sm"
            button-border-radius="rounded-full"
            textarea-border-radius="rounded-sm"
            :star-active-class="'bs-estrela--on'"
            :star-inactive-class="'bs-estrela--off'"
            progress-bar-class="bs-barra"
            :submit-button-class="'bs-btn bs-btn--cheio w-full justify-center'"
            :review-card-class="'bs-review'"
            :own-review-border-class="'bs-review--minha'"
            :load-more-button-class="'bs-btn'"
            @rating-updated="onRatingUpdated"
          />
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="bs-wrap bs-footer">
        <div class="bs-orn" aria-hidden="true"><span></span><i></i><span></span></div>
        <p class="bs-footer__nome">{{ loja.nome }}</p>
        <p v-if="loja.localizacao" class="bs-footer__morada">{{ loja.localizacao }}</p>
        <nav class="bs-footer__links">
          <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
          <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
          <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
        </nav>
        <p class="bs-footer__copy">© {{ ano }} {{ loja.nome }}</p>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="bs-modal" @click.self="modalPolitica = null">
        <div class="bs-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="bs-circ" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="bs-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="bs-vazio">
      <p>Loja não encontrada</p>
      <button class="bs-btn bs-btn--cheio" @click="$router.back()">Voltar</button>
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
import AvaliacaoLoja from '@/components/avaliacao/avaliacaoLoja.vue'

const LIMITE = 8

export default {
  name: 'TemplateRestauranteBistro',

  components: { ProductInfoCard, MultiCart, Profile, ProductCatalog, AvaliacaoLoja, ProdutosPaginados },

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
    const modoEscolhido = ref(null)

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#8c2f2b',
      '--cor-secundaria': props.tema?.corSecundaria || '#1e2a24',
    }))

    // ── Carta (só metadados; os pratos vêm página a página) ──
    const grupos = lojaData.gruposProdutos

    const modos = computed(() => [
      { key: 'tipo', label: 'Por tipo' },
      { key: 'categoria', label: 'Por categoria' },
      { key: 'todos', label: 'Todos os pratos' },
    ].filter(m => grupos.value.some(g => g.seccao === m.key)))

    // por tipo por defeito; se a loja não tem tipos, abre logo por categoria
    const modo = computed(() =>
      modos.value.some(m => m.key === modoEscolhido.value) ? modoEscolhido.value : modos.value[0]?.key)

    const capitulos = computed(() => grupos.value.filter(g => g.seccao === modo.value))

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
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento no local' : 'Consulte a entrega'
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

    function romano (n) {
      const tabela = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']]
      let out = ''
      for (const [v, s] of tabela) while (n >= v) { out += s; n -= v }
      return out
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
      scrolled,
      grupos, modos, modo, modoEscolhido, capitulos,
      rating, textoEntrega, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, romano, esgotado, precoDe,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Karla:wght@400;500;600;700&family=Caveat:wght@500;700&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.bs-root {
  --cor: var(--cor-primaria, #8c2f2b);
  --serif: 'Cormorant Garamond', Georgia, serif;
  --sans: 'Karla', system-ui, sans-serif;
  --giz: 'Caveat', 'Comic Sans MS', cursive;
  --bar-h: 68px;
  --bar-pad: 28px;
  /* carrinho · notificações · perfil alinhados com a barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--sans);
  background: var(--bg);
  color: var(--tinta);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .4s, color .4s;
}
.bs-light {
  --bg: #f6efe2;
  --papel: #fbf7ef;
  --tinta: #2a211b;
  --tinta2: #6f6256;
  --regra: rgba(42, 33, 27, .2);
  --ardosia: var(--cor-secundaria, #1e2a24);
  --acento: var(--cor);
}
.bs-dark {
  --bg: var(--cor-secundaria, #1e2a24);
  --papel: color-mix(in srgb, var(--bg) 90%, #fff 10%);
  --tinta: #f3eadb;
  --tinta2: #b9ad9c;
  --regra: rgba(243, 234, 219, .2);
  --ardosia: color-mix(in srgb, var(--bg) 70%, #000 30%);
  /* acento legível sobre fundo escuro */
  --acento: color-mix(in srgb, var(--cor) 65%, #fff 35%);
}

.bs-wrap { max-width: 1180px; margin: 0 auto; padding: 0 var(--bar-pad); }
.bs-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.bs-hide-scroll::-webkit-scrollbar { display: none; }

.bs-versal {
  margin: 0; font-family: var(--sans); font-size: 12px; font-weight: 700;
  letter-spacing: .22em; text-transform: uppercase; color: var(--acento);
}

/* Ornamento: dois traços com um losango (forma CSS) */
.bs-orn { display: flex; align-items: center; justify-content: center; gap: 12px; color: var(--acento); }
.bs-orn span { width: 56px; height: 1px; background: currentColor; opacity: .6; }
.bs-orn i { width: 7px; height: 7px; transform: rotate(45deg); border: 1px solid currentColor; }

/* Linha pontilhada entre nome e preço */
.bs-pontos { flex: 1; min-width: 16px; border-bottom: 1.5px dotted var(--regra); transform: translateY(-5px); }

/* ── Loading ─────────────────────────────────────────────── */
.bs-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; align-items: center; justify-content: center; }
.bs-loading__nome { font-family: var(--serif); font-style: italic; font-size: 26px; color: var(--tinta2); animation: bsRespira 1.4s ease-in-out infinite; }
@keyframes bsRespira { 50% { opacity: .4; } }

/* ── Barra ───────────────────────────────────────────────── */
.bs-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center; gap: 8px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 12px) 0 var(--bar-pad);
  border-bottom: 1px solid transparent;
  transition: background .3s, border-color .3s;
}
.bs-bar--papel { background: color-mix(in srgb, var(--bg) 94%, transparent); backdrop-filter: blur(8px); border-bottom-color: var(--regra); }
.bs-circ {
  width: 38px; height: 38px; flex-shrink: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--papel); color: var(--tinta); border: 1px solid var(--regra); cursor: pointer;
  transition: border-color .2s, color .2s;
}
.bs-circ:hover { border-color: var(--acento); color: var(--acento); }
.bs-bar__nome {
  margin-left: 8px; min-width: 0; font-family: var(--serif); font-style: italic; font-weight: 600; font-size: 22px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  opacity: 0; transform: translateY(4px); transition: opacity .3s, transform .3s;
}
.bs-bar__nome--on { opacity: 1; transform: none; }

/* ── Capa ────────────────────────────────────────────────── */
.bs-capa { padding-top: calc(var(--bar-h) + 8px); }
.bs-capa__moldura {
  position: relative; display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 48px; align-items: center;
  padding: 56px; background: var(--papel); border: 1px solid var(--regra);
}
.bs-capa__moldura::before {
  /* moldura dupla, como a capa de uma carta impressa */
  content: ''; position: absolute; inset: 8px; border: 1px solid var(--regra); pointer-events: none;
}
.bs-capa__texto { text-align: center; position: relative; }
.bs-capa__nome {
  margin: 16px 0 18px; font-family: var(--serif); font-style: italic; font-weight: 600;
  font-size: clamp(3rem, 7vw, 6rem); line-height: .95; letter-spacing: -.01em; text-wrap: balance;
}
.bs-capa__desc { margin: 20px auto 0; max-width: 460px; font-family: var(--serif); font-size: 21px; line-height: 1.5; color: var(--tinta2); }
.bs-capa__meta {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 22px; margin: 24px 0 30px;
  font-size: 14px; color: var(--tinta2);
}
.bs-capa__rating { display: inline-flex; align-items: center; gap: 2px; color: var(--acento); }
.bs-capa__rating em { margin-left: 6px; color: var(--tinta2); }
.bs-capa__ctas { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }

.bs-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 13px 26px; border-radius: 999px;
  font-family: var(--sans); font-size: 14px; font-weight: 700; letter-spacing: .04em; cursor: pointer;
  background: transparent; color: var(--tinta); border: 1px solid var(--tinta);
  transition: background .2s, color .2s, border-color .2s;
}
.bs-btn:hover { border-color: var(--acento); color: var(--acento); }
.bs-btn--cheio { background: var(--cor); border-color: var(--cor); color: #fff; }
.bs-btn--cheio:hover { background: color-mix(in srgb, var(--cor) 85%, #000); color: #fff; border-color: transparent; }

.bs-arco {
  position: relative; aspect-ratio: 3 / 4; max-height: 560px; width: 100%;
  border-radius: 999px 999px 4px 4px; overflow: hidden; background: var(--bg);
  outline: 1px solid var(--regra); outline-offset: 8px;
}
.bs-arco img, .bs-arco video { width: 100%; height: 100%; object-fit: cover; display: block; }
.bs-arco__vazio { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-family: var(--serif); font-style: italic; font-size: 160px; color: var(--acento); }

/* ── Secções ─────────────────────────────────────────────── */
.bs-sec { padding-top: 88px; scroll-margin-top: calc(var(--bar-h) + 8px); }
.bs-titulo { text-align: center; margin-bottom: 36px; }
.bs-titulo h2 { margin: 10px 0 0; font-family: var(--serif); font-style: italic; font-weight: 600; font-size: clamp(2.4rem, 5vw, 3.6rem); line-height: 1; }

/* ── Ardósia ─────────────────────────────────────────────── */
.bs-ardosia {
  position: relative; max-width: 920px; margin: 0 auto; padding: 52px 56px 44px;
  background: var(--ardosia); color: #f4f1ea; border-radius: 6px;
  border: 12px solid #6b4e35;                 /* moldura em madeira */
  box-shadow: inset 0 0 80px rgba(0,0,0,.35), 0 20px 40px rgba(0,0,0,.18);
}
.bs-ardosia::before {
  /* pó de giz */
  content: ''; position: absolute; inset: 0; pointer-events: none; opacity: .5;
  background: radial-gradient(ellipse at 30% 20%, rgba(255,255,255,.07), transparent 60%),
              radial-gradient(ellipse at 80% 90%, rgba(255,255,255,.05), transparent 50%);
}
.bs-ardosia__titulo { margin: 0; text-align: center; font-family: var(--giz); font-weight: 700; font-size: 48px; line-height: 1; }
.bs-ardosia__sub { margin: 4px 0 28px; text-align: center; font-family: var(--giz); font-size: 22px; opacity: .65; }
.bs-ardosia__lista { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 48px; }
.bs-ardosia__item {
  width: 100%; display: flex; align-items: baseline; gap: 10px; padding: 0; background: none; border: none;
  color: inherit; cursor: pointer; text-align: left; font-family: var(--giz); font-size: 26px; line-height: 1.15;
}
.bs-ardosia__item .bs-pontos { border-bottom-color: rgba(244, 241, 234, .35); }
.bs-ardosia__item:hover .bs-ardosia__nome { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 4px; }
.bs-ardosia__preco { flex-shrink: 0; font-weight: 700; }
.bs-ardosia__desc { margin: 2px 0 0; font-family: var(--giz); font-size: 18px; opacity: .6; }

/* ── A carta ─────────────────────────────────────────────── */
.bs-modo { display: inline-flex; gap: 4px; margin-top: 22px; padding: 4px; border-radius: 999px; border: 1px solid var(--regra); }
.bs-modo button {
  padding: 8px 18px; border-radius: 999px; border: none; background: none; cursor: pointer;
  font-family: var(--sans); font-size: 13px; font-weight: 700; color: var(--tinta2);
}
.bs-modo .bs-modo--on { background: var(--tinta); color: var(--bg); }

.bs-indice {
  position: sticky; top: var(--bar-h); z-index: 20;
  display: flex; justify-content: center; gap: 4px 26px; overflow-x: auto;
  margin: 0 calc(-1 * var(--bar-pad)) 12px; padding: 12px var(--bar-pad);
  background: color-mix(in srgb, var(--bg) 94%, transparent); backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--regra);
}
.bs-indice button {
  flex-shrink: 0; background: none; border: none; cursor: pointer; padding: 2px 0;
  font-family: var(--serif); font-style: italic; font-size: 19px; font-weight: 600; color: var(--tinta2);
  white-space: nowrap; text-transform: capitalize; transition: color .2s;
}
.bs-indice button span { font-style: normal; color: var(--acento); margin-right: 2px; }
.bs-indice button:hover { color: var(--tinta); }

.bs-capitulo { padding-top: 48px; scroll-margin-top: calc(var(--bar-h) + 64px); }
.bs-capitulo__head { display: flex; align-items: baseline; gap: 16px; padding-bottom: 14px; margin-bottom: 8px; border-bottom: 1px solid var(--tinta); }
.bs-capitulo__num { font-family: var(--serif); font-weight: 700; font-size: 20px; color: var(--acento); min-width: 28px; }
.bs-capitulo__head h3 { margin: 0; flex: 1; font-family: var(--serif); font-style: italic; font-weight: 600; font-size: 34px; line-height: 1; text-transform: capitalize; }
.bs-capitulo__n { font-size: 13px; color: var(--tinta2); }

.bs-pratos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 56px; }
.bs-prato {
  display: flex; align-items: flex-start; gap: 16px; padding: 18px 0; text-align: left; width: 100%;
  background: none; border: none; border-bottom: 1px solid var(--regra); cursor: pointer; color: inherit; font: inherit;
}
.bs-prato__foto {
  flex-shrink: 0; width: 64px; height: 64px; border-radius: 50%; overflow: hidden; background: var(--papel);
  display: flex; align-items: center; justify-content: center; border: 1px solid var(--regra);
  font-family: var(--serif); font-style: italic; font-size: 28px; color: var(--acento);
  transition: transform .3s;
}
.bs-prato__foto img, .bs-prato__foto video { width: 100%; height: 100%; object-fit: cover; }
.bs-prato:hover .bs-prato__foto { transform: scale(1.06); }
.bs-prato__corpo { flex: 1; min-width: 0; padding-top: 6px; }
.bs-prato__linha { display: flex; align-items: baseline; gap: 10px; }
.bs-prato__nome { font-family: var(--serif); font-weight: 700; font-size: 22px; line-height: 1.15; transition: color .2s; }
.bs-prato:hover .bs-prato__nome { color: var(--acento); }
.bs-prato__preco { flex-shrink: 0; font-weight: 700; font-size: 15px; color: var(--acento); }
.bs-prato__desc { display: block; margin-top: 4px; font-size: 14px; line-height: 1.5; color: var(--tinta2); }
.bs-prato__tag { font-style: normal; font-weight: 700; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--acento); margin-right: 6px; }
.bs-prato--esgotado .bs-prato__foto, .bs-prato--esgotado .bs-prato__nome { opacity: .5; }

.bs-ver-todos {
  display: block; margin: 20px auto 0; background: none; border: none; cursor: pointer;
  font-family: var(--serif); font-style: italic; font-size: 19px; font-weight: 600; color: var(--acento);
  text-decoration: underline; text-underline-offset: 5px; text-decoration-thickness: 1px;
}

.bs-skel { height: 64px; margin: 18px 0; border-bottom: 1px solid var(--regra); background: linear-gradient(90deg, var(--papel), transparent); animation: bsRespira 1.3s ease-in-out infinite; }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.bs-catalogo :deep(.bg-zinc-900), .bs-catalogo :deep(.bg-white) { background: var(--papel) !important; }
.bs-catalogo :deep(.bg-zinc-800), .bs-catalogo :deep(.bg-gray-50), .bs-catalogo :deep(.bg-gray-100),
.bs-catalogo :deep(.bg-zinc-700), .bs-catalogo :deep(.bg-gray-200) { background: var(--bg) !important; }
.bs-catalogo :deep(.border-zinc-800), .bs-catalogo :deep(.border-zinc-700),
.bs-catalogo :deep(.border-gray-200), .bs-catalogo :deep(.border-gray-300) { border-color: var(--regra) !important; }
.bs-catalogo :deep(.text-zinc-100), .bs-catalogo :deep(.text-zinc-900) { color: var(--tinta) !important; }
.bs-catalogo :deep(input), .bs-catalogo :deep(select) { color: var(--tinta) !important; font-family: var(--sans); }
.bs-catalogo :deep(input:focus), .bs-catalogo :deep(select:focus) { border-color: var(--acento) !important; outline: none; }
.bs-catalogo :deep(.bs-tab) { background: transparent; color: var(--tinta2); border: 1px solid var(--regra); font-weight: 700; text-transform: capitalize; }
.bs-catalogo :deep(.bs-tab--on) { background: var(--tinta) !important; color: var(--bg) !important; font-weight: 700; text-transform: capitalize; }
.bs-catalogo :deep(.bs-cat-borda) { border-color: var(--regra) !important; }
.bs-catalogo :deep(.bs-cat-nome) { font-family: var(--serif); font-size: 19px; font-weight: 700; }
.bs-catalogo :deep(.bs-cat-preco) { color: var(--acento) !important; font-weight: 700; }
.bs-catalogo :deep(.bs-cat-badge) { background: var(--cor) !important; color: #fff !important; border-radius: 999px !important; font-weight: 700; }
.bs-catalogo :deep(.bs-cat-indicador) { background: var(--papel) !important; color: var(--tinta) !important; }
.bs-catalogo :deep(.bs-cat-limpar) { color: var(--acento) !important; }
.bs-catalogo :deep(.bs-cat-spinner) { color: var(--acento) !important; }

/* ── Informação ──────────────────────────────────────────── */
.bs-info { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--tinta); border-bottom: 1px solid var(--tinta); padding-top: 0; margin-top: 88px; }
.bs-info__col { padding: 32px 32px 36px; }
.bs-info__col + .bs-info__col { border-left: 1px solid var(--regra); }
.bs-info__col .bs-versal { margin-bottom: 16px; }
.bs-info__col p { margin: 0; font-family: var(--serif); font-size: 20px; line-height: 1.5; }
.bs-info__col ul { list-style: none; margin: 0; padding: 0; }
.bs-info__col li { display: flex; align-items: baseline; gap: 8px; padding: 5px 0; font-family: var(--serif); font-size: 20px; }
.bs-info__col li b { font-family: var(--sans); font-size: 14px; color: var(--acento); }
.bs-info__metodos span { text-transform: capitalize; }
.bs-info__metodos i { font-style: normal; color: var(--acento); }
.bs-info__morada { display: flex; gap: 8px; align-items: flex-start; }
.bs-info__morada svg { flex-shrink: 0; margin-top: 6px; color: var(--acento); }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.bs-estrela--on) { color: var(--acento) !important; }
:deep(.bs-estrela--off) { color: var(--regra) !important; }
:deep(.bs-barra) { background: var(--acento) !important; }
:deep(.bs-review) { background: var(--papel) !important; border: 1px solid var(--regra) !important; }
:deep(.bs-review--minha) { border: 1px solid var(--acento) !important; }
:deep(.bs-btn) { display: inline-flex; padding: 12px 24px; border-radius: 999px; font-weight: 700; border: 1px solid var(--tinta); }
:deep(.bs-btn--cheio) { background: var(--cor) !important; border-color: var(--cor) !important; color: #fff !important; }

/* ── Rodapé ──────────────────────────────────────────────── */
.bs-footer { padding-top: 96px; padding-bottom: 40px; text-align: center; }
.bs-footer__nome { margin: 18px 0 6px; font-family: var(--serif); font-style: italic; font-weight: 600; font-size: clamp(2.4rem, 6vw, 4rem); line-height: 1; }
.bs-footer__morada { margin: 0; color: var(--tinta2); }
.bs-footer__links { display: flex; justify-content: center; flex-wrap: wrap; gap: 8px 24px; margin: 28px 0 16px; }
.bs-footer__links button { background: none; border: none; cursor: pointer; font: inherit; font-size: 13px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--tinta2); }
.bs-footer__links button:hover { color: var(--acento); }
.bs-footer__copy { margin: 0; font-size: 13px; color: var(--tinta2); }

/* ── Modal ───────────────────────────────────────────────── */
.bs-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.5); }
.bs-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--papel); color: var(--tinta); border: 1px solid var(--regra); }
.bs-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 18px 22px; background: var(--papel); border-bottom: 1px solid var(--regra); }
.bs-modal__painel h3 { margin: 0; font-family: var(--serif); font-style: italic; font-size: 28px; font-weight: 600; }
.bs-modal__corpo { padding: 22px; font-size: 15px; line-height: 1.7; color: var(--tinta2); white-space: pre-wrap; }

.bs-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-family: var(--serif); font-style: italic; font-size: 32px; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .bs-capa__moldura { grid-template-columns: minmax(0, 1fr); padding: 44px 36px; gap: 36px; }
  .bs-arco { order: -1; max-width: 360px; margin: 0 auto; aspect-ratio: 4 / 5; }
  .bs-pratos { grid-template-columns: minmax(0, 1fr); }
  .bs-info { grid-template-columns: minmax(0, 1fr); }
  .bs-info__col + .bs-info__col { border-left: none; border-top: 1px solid var(--regra); }
  .bs-indice { justify-content: flex-start; }
}

@media (max-width: 640px) {
  .bs-root { --bar-h: 60px; --bar-pad: 14px; }
  .bs-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .bs-bar__nome { font-size: 19px; }
  .bs-circ { width: 34px; height: 34px; }
  .bs-capa__moldura { padding: 32px 20px; }
  .bs-arco { max-width: 260px; }
  .bs-capa__desc { font-size: 18px; }
  .bs-sec { padding-top: 64px; }
  .bs-ardosia { padding: 36px 22px 30px; border-width: 8px; }
  .bs-ardosia__titulo { font-size: 38px; }
  .bs-ardosia__lista { grid-template-columns: minmax(0, 1fr); }
  .bs-ardosia__item { font-size: 23px; }
  .bs-capitulo__head h3 { font-size: 28px; }
  .bs-prato { gap: 12px; padding: 14px 0; }
  .bs-prato__foto { width: 52px; height: 52px; }
  .bs-prato__nome { font-size: 19px; }
  .bs-indice button { font-size: 17px; }
  .bs-info__col { padding: 26px 4px; }
}
</style>
