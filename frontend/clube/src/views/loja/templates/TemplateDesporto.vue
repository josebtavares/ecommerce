<!-- TemplateDesporto.vue — Revamp "pista"
     Velocidade sem ruído: hero com riscas diagonais, nome em itálico expandido e banner
     num paralelogramo · placar com os números da loja · "Top da época" com números de
     camisola (scroll infinito) · modalidades por tipo/categoria em pistas numeradas,
     cada uma com scroll infinito horizontal · catálogo completo · balneário (informação) · avaliações.
     Produtos sempre paginados pelo servidor (ProdutosPaginados / FimDaLista).
     Tipografia: Archivo (eixo de largura). Acento: --cor-primaria (texto sobre ele calculado
     por contraste). Fundo escuro: --cor-secundaria. Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="dp-root" :class="isDark ? 'dp-dark' : 'dp-light'" :style="cssVars">
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
    <div v-if="loading" class="dp-loading">
      <span v-for="i in 3" :key="i" class="dp-loading__risca" :style="{ animationDelay: (i * 0.1) + 's' }"></span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="dp-bar" :class="{ 'dp-bar--solida': scrolled }">
        <button class="dp-quad" @click="$router.back()" aria-label="Voltar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="dp-quad" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="dp-bar__nome">{{ loja.nome }}</span>
      </header>

      <!-- ══ HERO ══ -->
      <section class="dp-hero">
        <div class="dp-hero__riscas" aria-hidden="true"><span></span><span></span><span></span></div>
        <div class="dp-wrap dp-hero__grid">
          <div class="dp-hero__texto">
            <p class="dp-tag">{{ loja.categoria || 'Desporto' }}</p>
            <h1 class="dp-hero__nome">{{ loja.nome }}</h1>
            <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />
            <EstadoLoja :horario="loja.horario" :loja-id="lojaId" class="loja-estado" />
            <p v-if="loja.descricao" class="dp-hero__desc">{{ truncate(loja.descricao, 170) }}</p>
            <div class="dp-hero__ctas">
              <button class="dp-btn dp-btn--cor" @click="scrollToId(soServicos ? 'servicos' : totalDestaques ? 'dp-top' : 'dp-pistas')">
                {{ soServicos ? 'Ver serviços' : totalDestaques ? 'Ver o top' : 'Ver produtos' }}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </button>
              <button v-if="!soServicos" class="dp-btn" @click="scrollToId('dp-catalogo')">Catálogo</button>
            </div>
          </div>

          <div class="dp-hero__media">
            <div class="dp-paralelo">
              <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" v-video-visivel muted loop playsinline></video>
              <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
              <div v-else class="dp-paralelo__vazio">{{ loja.nome.charAt(0) }}</div>
            </div>
          </div>
        </div>

        <!-- Placar -->
        <div class="dp-wrap">
          <dl class="dp-placar">
            <div>
              <dt>Avaliação</dt>
              <dd>{{ rating }}<small v-if="loja.rating_medio">/5</small></dd>
            </div>
            <div>
              <dt>{{ soServicos ? 'Serviços' : 'Produtos' }}</dt>
              <dd>{{ soServicos ? totalServicos : (totalProdutos ?? '—') }}</dd>
            </div>
            <div>
              <dt>Modalidades</dt>
              <dd>{{ grupos.length }}</dd>
            </div>
            <div>
              <dt>Entrega</dt>
              <dd class="dp-placar__txt">{{ textoEntrega }}</dd>
            </div>
          </dl>
        </div>
      </section>

      <main class="dp-wrap">
        <!-- ══ TOP DA ÉPOCA (destaques; scroll infinito) ══ -->
        <section v-if="totalDestaques" id="dp-top" class="dp-sec">
          <header class="dp-sec__head">
            <h2 class="dp-sec__titulo">Top da época</h2>
            <div class="dp-setas">
              <button class="dp-quad" @click="deslizar($event, -1)" aria-label="Anterior">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button class="dp-quad" @click="deslizar($event, 1)" aria-label="Seguinte">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
              </button>
            </div>
          </header>

          <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="8" :lazy="false" v-slot="l">
            <div class="dp-fila dp-fila--top dp-hide-scroll">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="dp-skel"></div>
              </template>
              <button v-for="(p, i) in l.itens" :key="p.id" class="dp-cartao dp-cartao--top" @click="selectedProduct = p">
                <span class="dp-camisola" aria-hidden="true">{{ String(i + 1).padStart(2, '0') }}</span>
                <span class="dp-cartao__img">
                  <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted loop v-video-visivel playsinline></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="dp-cartao__inicial">{{ p.nome.charAt(0) }}</span>
                  <span v-if="esgotado(p)" class="dp-cartao__esgotado">Esgotado</span>
                </span>
                <span class="dp-cartao__nome">{{ p.nome }}</span>
                <span class="dp-preco">{{ precoDe(p) }}</span>
              </button>
              <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                <div class="dp-skel"></div>
              </FimDaLista>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ MODALIDADES (pistas por tipo / categoria; scroll infinito) ══ -->
        <section v-if="grupos.length" id="dp-pistas" class="dp-sec">
          <header class="dp-sec__head">
            <h2 class="dp-sec__titulo">Modalidades</h2>
            <nav class="dp-saltos dp-hide-scroll">
              <button v-for="(g, i) in grupos" :key="g.key" @click="scrollToId('dp-g-' + g.key)">
                <b>{{ i + 1 }}</b>{{ g.nome }}
              </button>
            </nav>
          </header>

          <template v-for="(g, i) in grupos" :key="g.key">
            <p v-if="i === 0 || grupos[i - 1].seccao !== g.seccao" class="dp-divisor">{{ SECCOES[g.seccao] }}</p>

            <div :id="'dp-g-' + g.key" class="dp-pista">
              <header class="dp-pista__head">
                <span class="dp-pista__num">{{ i + 1 }}</span>
                <h3 class="dp-pista__nome">{{ g.nome }}</h3>
                <span class="dp-pista__n">{{ g.total }} {{ g.total === 1 ? 'produto' : 'produtos' }}</span>
                <span class="dp-pista__setas">
                  <button class="dp-quad dp-quad--peq" @click="deslizar($event, -1)" aria-label="Anterior">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
                  </button>
                  <button class="dp-quad dp-quad--peq" @click="deslizar($event, 1)" aria-label="Seguinte">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
                  </button>
                </span>
              </header>

              <ProdutosPaginados :params="g.params" :limit="8" v-slot="l">
                <div class="dp-fila dp-hide-scroll">
                  <template v-if="l.carregando">
                    <div v-for="n in Math.min(g.total, 5)" :key="n" class="dp-skel"></div>
                  </template>
                  <button v-for="p in l.itens" :key="p.id" class="dp-cartao" @click="selectedProduct = p">
                    <span class="dp-cartao__img">
                      <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                      <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                      <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                      <span v-else class="dp-cartao__inicial">{{ p.nome.charAt(0) }}</span>
                      <span v-if="esgotado(p)" class="dp-cartao__esgotado">Esgotado</span>
                    </span>
                    <span class="dp-cartao__nome">{{ p.nome }}</span>
                    <span class="dp-preco">{{ precoDe(p) }}</span>
                  </button>
                  <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                    <div class="dp-skel"></div>
                  </FimDaLista>
                </div>
              </ProdutosPaginados>
            </div>
          </template>
        </section>

        <!-- ══ SERVIÇOS ══ -->
        <SeccaoServicos :loja-id="lojaId" :isDark="isDark" :cor="tema?.corPrimaria || '#dc2626'" class="dp-sec" />

        <!-- ══ CATÁLOGO ══ -->
        <section v-if="!soServicos" id="dp-catalogo" class="dp-sec">
          <header class="dp-sec__head">
            <h2 class="dp-sec__titulo">Catálogo</h2>
          </header>
          <div class="dp-catalogo">
            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="220px"
              card-border-radius="rounded-md"
              skeleton-class="rounded-md"
              hover-effect="transition-transform duration-200 hover:-translate-y-1"
              hover-border-class=""
              filter-container-radius="rounded-md"
              input-border-radius="rounded-md"
              input-focus-class="dp-foco"
              tab-border-radius="rounded-md"
              active-tab-class="dp-tab--on"
              inactive-tab-dark-class="dp-tab"
              inactive-tab-light-class="dp-tab"
              active-sub-tab-class="dp-tab--on"
              inactive-sub-tab-dark-class="dp-tab"
              inactive-sub-tab-light-class="dp-tab"
              category-border-class="dp-cat-borda"
              product-name-class="dp-cat-nome"
              product-name-hover-class=""
              price-class="dp-cat-preco"
              badge-text="Top"
              badge-class="dp-cat-badge"
              indicator-active-class="dp-cat-indicador"
              clear-filter-class="dp-cat-limpar"
              clear-all-class="dp-cat-limpar"
              spinner-class="dp-cat-spinner"
              :show-stock="false"
              :show-category-badges="false"
              empty-text="Nenhum produto encontrado."
              @product-click="selectedProduct = $event"
            />
          </div>
        </section>

        <!-- ══ BALNEÁRIO (informação) ══ -->
        <section id="dp-info" class="dp-sec">
          <header class="dp-sec__head">
            <h2 class="dp-sec__titulo">Balneário</h2>
          </header>
          <div class="dp-info">
            <div class="dp-info__bloco">
              <p class="dp-info__titulo">Entrega</p>
              <ul v-if="opcoesEntrega.length || loja.levantamento_ativo">
                <li v-for="o in opcoesEntrega" :key="o.id">
                  <span>{{ o.nome }}</span><b>{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</b>
                </li>
                <li v-if="loja.levantamento_ativo"><span>Levantamento</span><b>Grátis</b></li>
              </ul>
              <p v-else>Fala com a loja.</p>
            </div>
            <div class="dp-info__bloco dp-info__bloco--cor">
              <p class="dp-info__titulo">Pagamento</p>
              <div v-if="metodosPagamento.length" class="dp-info__tags">
                <span v-for="m in metodosPagamento" :key="m.id">{{ m.nome }}</span>
              </div>
              <p v-else>—</p>
            </div>
            <div class="dp-info__bloco">
              <p class="dp-info__titulo">Loja</p>
              <p v-if="loja.localizacao" class="dp-info__morada">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ loja.localizacao }}
              </p>
              <p v-else>Loja online.</p>
            </div>
          </div>
        </section>

        <!-- ══ AVALIAÇÕES ══ -->
        <section id="dp-avaliacoes" class="dp-sec">
          <header class="dp-sec__head">
            <h2 class="dp-sec__titulo">Avaliações</h2>
          </header>
          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-md"
            form-border-radius="rounded-md"
            review-card-border-radius="rounded-md"
            button-border-radius="rounded-md"
            textarea-border-radius="rounded-md"
            :star-active-class="'dp-estrela--on'"
            :star-inactive-class="'dp-estrela--off'"
            progress-bar-class="dp-barra"
            :submit-button-class="'dp-btn dp-btn--cor w-full justify-center'"
            :review-card-class="'dp-review'"
            :own-review-border-class="'dp-review--minha'"
            :load-more-button-class="'dp-btn'"
            @rating-updated="onRatingUpdated"
          />
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="dp-footer">
        <div class="dp-footer__riscas" aria-hidden="true"></div>
        <div class="dp-wrap dp-footer__inner">
          <p class="dp-footer__nome">{{ loja.nome }}</p>
          <div class="dp-footer__linha">
            <nav class="dp-footer__links">
              <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
              <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
              <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
            </nav>
            <span>© {{ ano }} {{ loja.nome }}</span>
          </div>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="dp-modal" @click.self="modalPolitica = null">
        <div class="dp-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="dp-quad" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="dp-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="dp-vazio">
      <p>Loja não encontrada</p>
      <button class="dp-btn dp-btn--cor" @click="$router.back()">Voltar</button>
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

// texto preto ou branco sobre a cor primária, conforme a luminância
function textoSobre (hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || '')
  if (!m) return '#ffffff'
  const n = parseInt(m[1], 16)
  const canal = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }
  const lum = 0.2126 * canal(n >> 16) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255)
  return lum > 0.4 ? '#0c0d0f' : '#ffffff'
}

export default {
  name: 'TemplateDesporto',

  components: { SeccaoServicos, ProductInfoCard, BotaoFavorito, EstadoLoja, MultiCart, Profile, ProductCatalog, AvaliacaoLoja, ProdutosPaginados, FimDaLista },

  emits: ['toggle-dark'],

  props: {
    tema: { type: Object, default: () => ({}) },
  },

  setup (props, { emit }) {
    const lojaData = useLojaData()
    const isDark = ref(props.tema?.darkMode !== false)
    watch(() => props.tema?.darkMode, v => { if (v !== undefined) isDark.value = v !== false })

    const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
    const ano = new Date().getFullYear()
    const scrolled = ref(false)

    const cssVars = computed(() => {
      const cor = props.tema?.corPrimaria || '#c6f432'
      return {
        '--cor-primaria':   cor,
        '--cor-secundaria': props.tema?.corSecundaria || '#101114',
        '--cor-texto':      textoSobre(cor),
      }
    })

    // Modalidades: por tipo, depois por categoria — só metadados; cada pista pede página a página
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
        return min === 0 ? 'Grátis' : `Desde ${lojaData.formatPrice(min)}`
      }
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento' : 'Consultar'
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

    // setas: deslizam a fila da mesma secção/pista
    function deslizar (evento, dir) {
      const fila = evento.currentTarget.closest('.dp-pista, .dp-sec')?.querySelector('.dp-fila')
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
      rating, textoEntrega, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, precoDe, deslizar,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,400..900;1,62..125,400..900&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.dp-root {
  --cor: var(--cor-primaria, #c6f432);
  --sobre-cor: var(--cor-texto, #0c0d0f);
  --fonte: 'Archivo', system-ui, sans-serif;
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
.dp-dark {
  --bg: var(--cor-secundaria, #101114);
  --painel: color-mix(in srgb, var(--bg) 90%, #fff 10%);
  --painel2: color-mix(in srgb, var(--bg) 82%, #fff 18%);
  --fg: #f4f5f7;
  --fg2: #9aa0aa;
  --linha: rgba(244, 245, 247, .1);
  --acento: var(--cor);
}
.dp-light {
  --bg: #f1f2f4;
  --painel: #ffffff;
  --painel2: #e6e8ec;
  --fg: #0c0d0f;
  --fg2: #5c626d;
  --linha: rgba(12, 13, 15, .1);
  /* cores claras (ex.: lima) ficam ilegíveis como texto sobre fundo claro */
  --acento: color-mix(in srgb, var(--cor) 55%, #000 45%);
}

.dp-wrap { max-width: 1320px; margin: 0 auto; padding: 0 var(--bar-pad); }
.dp-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.dp-hide-scroll::-webkit-scrollbar { display: none; }

/* ── Loading ─────────────────────────────────────────────── */
.dp-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; align-items: center; justify-content: center; gap: 8px; }
.dp-loading__risca { width: 10px; height: 44px; background: var(--cor); transform: skewX(-18deg); animation: dpRisca .8s ease-in-out infinite alternate; }
@keyframes dpRisca { from { opacity: .25; transform: skewX(-18deg) scaleY(.6); } to { opacity: 1; transform: skewX(-18deg) scaleY(1); } }

/* ── Barra ───────────────────────────────────────────────── */
.dp-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center; gap: 8px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 12px) 0 var(--bar-pad);
  transition: background .3s, box-shadow .3s;
}
.dp-bar--solida { background: color-mix(in srgb, var(--bg) 90%, transparent); backdrop-filter: blur(10px); box-shadow: 0 1px 0 var(--linha); }
.dp-quad {
  width: 38px; height: 38px; flex-shrink: 0; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  background: var(--painel); color: var(--fg); border: 1px solid var(--linha); cursor: pointer;
  transition: background .15s, color .15s, border-color .15s;
}
.dp-quad:hover { background: var(--cor); border-color: var(--cor); color: var(--sobre-cor); }
.dp-quad--peq { width: 32px; height: 32px; }
.dp-bar__nome {
  margin-left: 8px; min-width: 0; font-weight: 900; font-style: italic; font-stretch: 120%; font-size: 17px;
  text-transform: uppercase; letter-spacing: -.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* ── Hero ────────────────────────────────────────────────── */
.dp-hero { position: relative; overflow: hidden; padding: calc(var(--bar-h) + 40px) 0 0; }
.dp-hero__riscas { position: absolute; top: 0; bottom: 0; right: -10%; width: 60%; display: flex; gap: 22px; transform: skewX(-18deg); pointer-events: none; }
.dp-hero__riscas span { flex: 1; background: var(--cor); opacity: .1; }
.dp-hero__riscas span:nth-child(2) { opacity: .18; flex: .5; }
.dp-hero__riscas span:nth-child(3) { opacity: .06; flex: .3; }
.dp-hero__grid { position: relative; display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 40px; align-items: center; }
.dp-tag {
  display: inline-block; margin: 0; padding: 6px 14px; background: var(--cor); color: var(--sobre-cor);
  font-size: 13px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; transform: skewX(-12deg);
}
.dp-hero__nome {
  margin: 22px 0 18px; font-weight: 900; font-style: italic; font-stretch: 125%;
  font-size: clamp(2.8rem, 7.5vw, 6.6rem); line-height: .88; letter-spacing: -.03em; text-transform: uppercase; text-wrap: balance;
  overflow-wrap: anywhere;
}
.dp-hero__desc { margin: 0 0 28px; max-width: 520px; font-size: 18px; line-height: 1.55; color: var(--fg2); }
.dp-hero__ctas { display: flex; flex-wrap: wrap; gap: 10px; }

.dp-btn {
  display: inline-flex; align-items: center; gap: 10px; padding: 15px 24px; border-radius: 6px;
  font: inherit; font-size: 15px; font-weight: 800; font-stretch: 110%; text-transform: uppercase; letter-spacing: .02em;
  cursor: pointer; background: transparent; color: var(--fg); border: 2px solid var(--fg);
  transition: transform .15s, background .15s, color .15s, border-color .15s;
}
.dp-btn:hover { transform: translateY(-2px); }
.dp-btn--cor { background: var(--cor); border-color: var(--cor); color: var(--sobre-cor); }
.dp-btn--cor svg { transition: transform .2s; }
.dp-btn--cor:hover svg { transform: translateX(4px); }

.dp-hero__media { position: relative; }
.dp-paralelo {
  aspect-ratio: 5 / 4; overflow: hidden; background: var(--painel);
  clip-path: polygon(14% 0, 100% 0, 86% 100%, 0 100%);
}
.dp-paralelo img, .dp-paralelo video { width: 100%; height: 100%; object-fit: cover; display: block; }
.dp-paralelo__vazio { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 160px; font-weight: 900; font-style: italic; color: var(--acento); }

/* placar */
.dp-placar {
  position: relative; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 48px 0 0;
  background: var(--painel); border: 1px solid var(--linha); border-radius: 8px; overflow: hidden;
}
.dp-placar > div { padding: 18px 22px; }
.dp-placar > div + div { border-left: 1px solid var(--linha); }
.dp-placar dt { font-size: 12px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--fg2); }
.dp-placar dd { margin: 6px 0 0; font-weight: 900; font-style: italic; font-stretch: 115%; font-size: 36px; line-height: 1; font-variant-numeric: tabular-nums; color: var(--acento); }
.dp-placar dd small { font-size: 16px; color: var(--fg2); }
.dp-placar__txt { font-size: 22px !important; color: var(--fg) !important; }

/* ── Secções ─────────────────────────────────────────────── */
.dp-sec { padding-top: 80px; scroll-margin-top: calc(var(--bar-h) + 8px); }
.dp-sec__head { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
.dp-sec__titulo {
  margin: 0; font-weight: 900; font-style: italic; font-stretch: 125%; text-transform: uppercase;
  font-size: clamp(2rem, 4.6vw, 3.4rem); line-height: 1; letter-spacing: -.02em;
}
.dp-setas { display: flex; gap: 8px; }

/* ── Cartões e filas ─────────────────────────────────────── */
.dp-fila {
  display: grid; grid-auto-flow: column; grid-auto-columns: 230px; gap: 16px;
  overflow-x: auto; scroll-snap-type: x mandatory; padding: 4px 2px 8px;
}
.dp-fila > * { scroll-snap-align: start; }
.dp-fila--top { grid-auto-columns: 280px; }
.dp-cartao {
  position: relative; display: flex; flex-direction: column; gap: 8px; padding: 0; min-width: 0; text-align: left;
  background: none; border: none; cursor: pointer; color: inherit; font: inherit;
}
.dp-cartao__img {
  position: relative; display: block; aspect-ratio: 1; border-radius: 8px; overflow: hidden; background: var(--painel);
  border: 1px solid var(--linha); transition: border-color .2s;
}
.dp-cartao:hover .dp-cartao__img { border-color: var(--cor); }
.dp-cartao__img img, .dp-cartao__img video { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .4s; }
.dp-cartao:hover .dp-cartao__img img { transform: scale(1.06); }
.dp-cartao__inicial { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 64px; font-weight: 900; font-style: italic; color: var(--acento); }
.dp-cartao__esgotado {
  position: absolute; left: 0; right: 0; bottom: 0; padding: 7px; text-align: center;
  background: var(--fg); color: var(--bg); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .08em;
}
.dp-cartao__nome { font-size: 15px; font-weight: 700; line-height: 1.25; }
.dp-preco {
  align-self: flex-start; padding: 4px 10px; background: var(--cor); color: var(--sobre-cor);
  font-weight: 900; font-style: italic; font-size: 15px; transform: skewX(-12deg); white-space: nowrap;
}

/* número de camisola */
.dp-cartao--top { padding-top: 10px; }
.dp-camisola {
  position: absolute; top: -6px; left: 10px; z-index: 1; pointer-events: none;
  font-weight: 900; font-style: italic; font-stretch: 125%; font-size: 64px; line-height: 1;
  color: transparent; -webkit-text-stroke: 2px var(--cor); text-shadow: 0 2px 10px rgba(0,0,0,.25);
}

.dp-skel { aspect-ratio: 1; border-radius: 8px; background: var(--painel); animation: dpPulso 1.2s ease-in-out infinite; }
@keyframes dpPulso { 50% { opacity: .5; } }

/* ── Pistas ──────────────────────────────────────────────── */
.dp-saltos { display: flex; gap: 6px; overflow-x: auto; max-width: 100%; }
.dp-saltos button {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px;
  background: var(--painel); border: 1px solid var(--linha); color: var(--fg); cursor: pointer;
  font: inherit; font-size: 13px; font-weight: 700; text-transform: capitalize; transition: border-color .15s;
}
.dp-saltos button b { font-style: italic; font-weight: 900; color: var(--acento); }
.dp-saltos button:hover { border-color: var(--cor); }

.dp-divisor { margin: 36px 0 0; font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--fg2); }
.dp-pista { position: relative; margin-top: 18px; padding: 20px 0 6px 20px; border-left: 4px solid var(--cor); scroll-margin-top: calc(var(--bar-h) + 16px); }
.dp-pista + .dp-pista, .dp-divisor + .dp-pista { border-top: 1px dashed var(--linha); }
.dp-pista__head { display: flex; align-items: baseline; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.dp-pista__num { font-weight: 900; font-style: italic; font-stretch: 125%; font-size: 40px; line-height: .8; color: var(--acento); font-variant-numeric: tabular-nums; }
.dp-pista__nome { margin: 0; font-weight: 900; font-style: italic; font-stretch: 115%; font-size: 26px; text-transform: uppercase; letter-spacing: -.01em; }
.dp-pista__n { font-size: 13px; font-weight: 600; color: var(--fg2); }
.dp-pista__setas { display: flex; gap: 6px; margin-left: auto; align-self: center; }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.dp-catalogo :deep(.bg-zinc-900), .dp-catalogo :deep(.bg-white) { background: var(--painel) !important; }
.dp-catalogo :deep(.bg-zinc-800), .dp-catalogo :deep(.bg-gray-50), .dp-catalogo :deep(.bg-gray-100),
.dp-catalogo :deep(.bg-zinc-700), .dp-catalogo :deep(.bg-gray-200) { background: var(--painel2) !important; }
.dp-catalogo :deep(.border-zinc-800), .dp-catalogo :deep(.border-zinc-700),
.dp-catalogo :deep(.border-gray-200), .dp-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.dp-catalogo :deep(.text-zinc-100), .dp-catalogo :deep(.text-zinc-900) { color: var(--fg) !important; }
.dp-catalogo :deep(input), .dp-catalogo :deep(select) { color: var(--fg) !important; font-family: var(--fonte); }
.dp-catalogo :deep(input:focus), .dp-catalogo :deep(select:focus) { border-color: var(--cor) !important; outline: none; }
.dp-catalogo :deep(.dp-tab) { background: var(--painel); color: var(--fg); border: 1px solid var(--linha); font-weight: 700; text-transform: uppercase; }
.dp-catalogo :deep(.dp-tab--on) { background: var(--cor) !important; color: var(--sobre-cor) !important; font-weight: 800; text-transform: uppercase; }
.dp-catalogo :deep(.dp-cat-borda) { border-color: var(--linha) !important; }
.dp-catalogo :deep(.dp-cat-nome) { font-weight: 700; }
.dp-catalogo :deep(.dp-cat-preco) { color: var(--acento) !important; font-weight: 900; font-style: italic; }
.dp-catalogo :deep(.dp-cat-badge) { background: var(--cor) !important; color: var(--sobre-cor) !important; border-radius: 4px !important; font-weight: 800; text-transform: uppercase; }
.dp-catalogo :deep(.dp-cat-indicador) { background: var(--painel2) !important; color: var(--fg) !important; }
.dp-catalogo :deep(.dp-cat-limpar) { color: var(--acento) !important; }
.dp-catalogo :deep(.dp-cat-spinner) { color: var(--acento) !important; }

/* ── Balneário ───────────────────────────────────────────── */
.dp-info { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.dp-info__bloco { padding: 26px; border-radius: 8px; background: var(--painel); border: 1px solid var(--linha); }
.dp-info__bloco--cor { background: var(--cor); border-color: var(--cor); color: var(--sobre-cor); }
.dp-info__titulo { margin: 0 0 14px !important; font-weight: 900; font-style: italic; font-stretch: 120%; font-size: 24px; text-transform: uppercase; }
.dp-info__bloco p { margin: 0; font-size: 15px; line-height: 1.6; }
.dp-info__bloco ul { list-style: none; margin: 0; padding: 0; }
.dp-info__bloco li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 15px; border-bottom: 1px solid var(--linha); }
.dp-info__bloco li:last-child { border-bottom: none; }
.dp-info__bloco li b { font-weight: 800; color: var(--acento); }
.dp-info__tags { display: flex; flex-wrap: wrap; gap: 8px; }
.dp-info__tags span { padding: 7px 12px; border-radius: 4px; background: rgba(0,0,0,.12); font-size: 13px; font-weight: 800; text-transform: uppercase; }
.dp-info__morada { display: flex; gap: 8px; align-items: flex-start; }
.dp-info__morada svg { flex-shrink: 0; margin-top: 3px; color: var(--acento); }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.dp-estrela--on) { color: var(--acento) !important; }
:deep(.dp-estrela--off) { color: var(--linha) !important; }
:deep(.dp-barra) { background: var(--cor) !important; }
:deep(.dp-review) { background: var(--painel) !important; border: 1px solid var(--linha) !important; }
:deep(.dp-review--minha) { border: 2px solid var(--cor) !important; }
:deep(.dp-btn) { display: inline-flex; padding: 13px 22px; border-radius: 6px; font-weight: 800; text-transform: uppercase; border: 2px solid var(--fg); }
:deep(.dp-btn--cor) { background: var(--cor) !important; border-color: var(--cor) !important; color: var(--sobre-cor) !important; }

/* ── Rodapé ──────────────────────────────────────────────── */
.dp-footer { position: relative; margin-top: 100px; padding: 56px 0 30px; background: var(--painel); overflow: hidden; }
.dp-footer__riscas { position: absolute; top: 0; left: 0; right: 0; height: 8px; background: repeating-linear-gradient(-60deg, var(--cor) 0 14px, transparent 14px 28px); }
.dp-footer__nome { margin: 0 0 30px; font-weight: 900; font-style: italic; font-stretch: 125%; font-size: clamp(2.4rem, 8vw, 6rem); line-height: .9; text-transform: uppercase; letter-spacing: -.03em; overflow-wrap: anywhere; }
.dp-footer__linha { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; font-size: 13px; color: var(--fg2); }
.dp-footer__links { display: flex; gap: 20px; flex-wrap: wrap; }
.dp-footer__links button { background: none; border: none; cursor: pointer; color: var(--fg); font: inherit; font-weight: 800; text-transform: uppercase; letter-spacing: .04em; }
.dp-footer__links button:hover { color: var(--acento); }

/* ── Modal ───────────────────────────────────────────────── */
.dp-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.55); }
.dp-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--painel); color: var(--fg); border-radius: 8px; border-top: 4px solid var(--cor); }
.dp-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: var(--painel); border-bottom: 1px solid var(--linha); }
.dp-modal__painel h3 { margin: 0; font-weight: 900; font-style: italic; font-size: 22px; text-transform: uppercase; }
.dp-modal__corpo { padding: 20px; font-size: 15px; line-height: 1.7; color: var(--fg2); white-space: pre-wrap; }

.dp-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-weight: 900; font-style: italic; font-size: 28px; text-transform: uppercase; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .dp-hero__grid { grid-template-columns: minmax(0, 1fr); gap: 28px; }
  .dp-hero__media { order: -1; max-width: 560px; }
  .dp-placar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dp-placar > div:nth-child(3) { border-left: none; }
  .dp-placar > div:nth-child(n+3) { border-top: 1px solid var(--linha); }
  .dp-info { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 640px) {
  .dp-root { --bar-h: 60px; --bar-pad: 14px; }
  .dp-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .dp-quad { width: 34px; height: 34px; }
  .dp-bar__nome { font-size: 15px; }
  .dp-hero { padding-top: calc(var(--bar-h) + 16px); }
  .dp-hero__desc { font-size: 16px; }
  .dp-btn { padding: 13px 18px; font-size: 14px; }
  .dp-placar { margin-top: 32px; }
  .dp-placar > div { padding: 14px 16px; }
  .dp-placar dd { font-size: 28px; }
  .dp-placar__txt { font-size: 18px !important; }
  .dp-sec { padding-top: 60px; }
  .dp-fila { grid-auto-columns: 46%; gap: 12px; }
  .dp-fila--top { grid-auto-columns: 66%; }
  .dp-camisola { font-size: 48px; }
  .dp-pista { padding-left: 14px; }
  .dp-pista__num { font-size: 32px; }
  .dp-pista__nome { font-size: 21px; }
  .dp-pista__setas { display: none; }
}
</style>
