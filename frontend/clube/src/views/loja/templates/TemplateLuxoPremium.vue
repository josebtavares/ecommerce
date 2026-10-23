<!-- TemplateLuxoPremium.vue — Revamp "maison"
     Silêncio e luz: hero de ecrã inteiro com moldura fina e monograma ·
     a vitrine — uma peça de cada vez sob um foco de luz, com navegação 01 / N ·
     coleções por tipo/categoria numa fila de vitrines com scroll infinito ·
     catálogo completo · concierge em três colunas · testemunhos.
     Produtos sempre paginados pelo servidor (ProdutosPaginados / FimDaLista).
     Tipografia: Bodoni Moda + Montserrat. Acento (dourado): --cor-primaria.
     Fundo escuro: --cor-secundaria. Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="lx-root" :class="isDark ? 'lx-dark' : 'lx-light'" :style="cssVars">
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
    <div v-if="loading" class="lx-loading">
      <span class="lx-loading__linha"></span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="lx-bar" :class="{ 'lx-bar--solida': scrolled }">
        <button class="lx-circ" @click="$router.back()" aria-label="Voltar">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="lx-circ" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <svg v-if="isDark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="lx-bar__nome" :class="{ 'lx-bar__nome--on': scrolled }">{{ loja.nome }}</span>
      </header>

      <!-- ══ HERO ══ -->
      <section class="lx-hero">
        <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" class="lx-hero__media" v-video-visivel muted loop playsinline></video>
        <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" class="lx-hero__media" />
        <div class="lx-hero__veu"></div>
        <div class="lx-hero__moldura"></div>

        <div class="lx-hero__centro">
          <span class="lx-monograma">
            <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" />
            <template v-else>{{ loja.nome.charAt(0) }}</template>
          </span>
          <p class="lx-versal">{{ loja.categoria || 'Maison' }}<template v-if="loja.localizacao"> — {{ loja.localizacao }}</template></p>
          <h1 class="lx-hero__nome">{{ loja.nome }}</h1>
          <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />
          <EstadoLoja :horario="loja.horario" :loja-id="lojaId" class="loja-estado" />
          <p v-if="loja.descricao" class="lx-hero__desc">{{ truncate(loja.descricao, 160) }}</p>
          <div class="lx-hero__ctas">
            <button class="lx-btn lx-btn--ouro" @click="scrollToId(totalDestaques ? 'lx-vitrine' : 'lx-colecoes')">
              {{ totalDestaques ? 'Descobrir a vitrine' : 'Ver as coleções' }}
            </button>
            <button class="lx-btn lx-btn--fino" @click="scrollToId('lx-catalogo')">Catálogo</button>
          </div>
        </div>

        <button class="lx-hero__desce" @click="scrollToId(totalDestaques ? 'lx-vitrine' : 'lx-colecoes')" aria-label="Descer">
          <span></span>
        </button>
      </section>

      <!-- ══ DADOS ══ -->
      <div class="lx-dados">
        <div class="lx-wrap lx-dados__linha">
          <span v-if="loja.rating_medio"><em>{{ rating }}</em> avaliação · {{ loja.total_avaliacoes || 0 }}</span>
          <span><em>{{ totalProdutos ?? '—' }}</em> peças</span>
          <span>{{ textoEntrega }}</span>
        </div>
      </div>

      <main>
        <!-- ══ A VITRINE (uma peça de cada vez; páginas de 8) ══ -->
        <section v-if="totalDestaques" id="lx-vitrine" class="lx-sec">
          <div class="lx-wrap">
            <header class="lx-titulo">
              <p class="lx-versal">A vitrine</p>
              <h2>Peças em destaque</h2>
            </header>

            <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="8" :lazy="false" v-slot="l">
              <div v-if="l.carregando" class="lx-vitrine lx-vitrine--vazia"><div class="lx-foco lx-skel"></div></div>

              <div v-else-if="l.itens.length" class="lx-vitrine">
                <Transition name="lx-troca" mode="out-in">
                  <div :key="atual(l).id" class="lx-vitrine__peca">
                    <button class="lx-foco" @click="selectedProduct = atual(l)">
                      <BotaoFavorito tipo="produto" :id="atual(l).id" elemento="span" :tamanho="32" class="fav-card" />
                      <video v-if="isVideo(atual(l).ficheiro_url)" :src="atual(l).ficheiro_url" :poster="atual(l).ficheiro_poster_url" muted loop v-video-visivel playsinline></video>
                      <img v-else-if="atual(l).ficheiro_url" :src="atual(l).ficheiro_url" :alt="atual(l).nome" />
                      <span v-else class="lx-foco__inicial">{{ atual(l).nome.charAt(0) }}</span>
                    </button>
                    <div class="lx-vitrine__info">
                      <p class="lx-versal">Nº {{ String(posicao(l) + 1).padStart(2, '0') }}</p>
                      <h3 class="lx-vitrine__nome">{{ atual(l).nome }}</h3>
                      <p v-if="atual(l).descricao" class="lx-vitrine__desc">{{ truncate(atual(l).descricao, 220) }}</p>
                      <p class="lx-vitrine__preco">{{ precoDe(atual(l)) }}</p>
                      <p v-if="esgotado(atual(l))" class="lx-vitrine__esgotado">Esgotado</p>
                      <button class="lx-btn lx-btn--ouro" @click="selectedProduct = atual(l)">Descobrir</button>
                    </div>
                  </div>
                </Transition>

                <div class="lx-vitrine__nav">
                  <button class="lx-circ" @click="mover(l, -1)" aria-label="Peça anterior">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
                  </button>
                  <span class="lx-vitrine__conta">
                    {{ String(posicao(l) + 1).padStart(2, '0') }}
                    <i class="lx-vitrine__barra"><b :style="{ width: ((posicao(l) + 1) / (l.total || 1) * 100) + '%' }"></b></i>
                    {{ String(l.total || 0).padStart(2, '0') }}
                  </span>
                  <button class="lx-circ" @click="mover(l, 1)" aria-label="Peça seguinte">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
                  </button>
                </div>
              </div>
            </ProdutosPaginados>
          </div>
        </section>

        <!-- ══ COLEÇÕES (por tipo / por categoria; fila com scroll infinito) ══ -->
        <section v-if="grupos.length" id="lx-colecoes" class="lx-sec">
          <div class="lx-wrap">
            <header class="lx-titulo">
              <p class="lx-versal">As coleções</p>
              <h2>{{ grupoActivo?.nome }}</h2>
              <p v-if="grupoActivo" class="lx-titulo__n">{{ grupoActivo.total }} {{ grupoActivo.total === 1 ? 'peça' : 'peças' }}</p>
            </header>

            <div v-if="modos.length > 1" class="lx-modos">
              <button v-for="m in modos" :key="m.key" :class="{ 'lx-on': modo === m.key }" @click="mudarModo(m.key)">{{ m.label }}</button>
            </div>

            <nav class="lx-colecoes">
              <button v-for="g in gruposDoModo" :key="g.key" :class="{ 'lx-on': grupoActivo?.key === g.key }" @click="grupoKey = g.key">
                {{ g.nome }}<sup>{{ g.total }}</sup>
              </button>
            </nav>
          </div>

          <ProdutosPaginados v-if="grupoActivo" :key="grupoActivo.key" :params="grupoActivo.params" :limit="8" :lazy="false" v-slot="l">
            <div class="lx-fila-wrap">
              <div ref="fila" class="lx-fila lx-hide-scroll">
                <template v-if="l.carregando">
                  <div v-for="n in 4" :key="n" class="lx-skel lx-skel--peca"></div>
                </template>
                <button v-for="(p, i) in l.itens" :key="p.id" class="lx-peca" @click="selectedProduct = p">
                  <span class="lx-peca__foco">
                    <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                    <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                    <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                    <span v-else class="lx-foco__inicial">{{ p.nome.charAt(0) }}</span>
                    <span v-if="esgotado(p)" class="lx-peca__esgotado">Esgotado</span>
                  </span>
                  <span class="lx-peca__num">{{ String(i + 1).padStart(2, '0') }}</span>
                  <span class="lx-peca__nome">{{ p.nome }}</span>
                  <span class="lx-peca__preco">{{ precoDe(p) }}</span>
                </button>
                <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                  <div class="lx-skel lx-skel--peca"></div>
                </FimDaLista>
              </div>
              <div class="lx-wrap lx-fila__nav">
                <button class="lx-circ" @click="deslizar(-1)" aria-label="Anterior">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
                </button>
                <button class="lx-circ" @click="deslizar(1)" aria-label="Seguinte">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
                </button>
              </div>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ SERVIÇOS ══ -->
        <SeccaoServicos :loja-id="lojaId" :isDark="isDark" :cor="tema?.corPrimaria || '#dc2626'" class="lx-sec" contido />

        <!-- ══ CATÁLOGO ══ -->
        <section id="lx-catalogo" class="lx-sec">
          <div class="lx-wrap">
            <header class="lx-titulo">
              <p class="lx-versal">Todas as peças</p>
              <h2>Catálogo</h2>
            </header>
            <div class="lx-catalogo">
              <ProductCatalog
                :loja-id="lojaId"
                :isDark="isDark"
                grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                image-height="260px"
                card-border-radius="rounded-none"
                skeleton-class="rounded-none"
                hover-effect="transition-opacity duration-300 hover:opacity-90"
                hover-border-class=""
                filter-container-radius="rounded-none"
                input-border-radius="rounded-none"
                input-focus-class="lx-foco-input"
                tab-border-radius="rounded-none"
                active-tab-class="lx-tab--on"
                inactive-tab-dark-class="lx-tab"
                inactive-tab-light-class="lx-tab"
                active-sub-tab-class="lx-tab--on"
                inactive-sub-tab-dark-class="lx-tab"
                inactive-sub-tab-light-class="lx-tab"
                category-border-class="lx-cat-borda"
                product-name-class="lx-cat-nome"
                product-name-hover-class=""
                price-class="lx-cat-preco"
                badge-text="Vitrine"
                badge-class="lx-cat-badge"
                indicator-active-class="lx-cat-indicador"
                clear-filter-class="lx-cat-limpar"
                clear-all-class="lx-cat-limpar"
                spinner-class="lx-cat-spinner"
                :show-stock="false"
                :show-category-badges="false"
                empty-text="Nenhuma peça encontrada."
                @product-click="selectedProduct = $event"
              />
            </div>
          </div>
        </section>

        <!-- ══ CONCIERGE ══ -->
        <section id="lx-info" class="lx-sec">
          <div class="lx-wrap">
            <header class="lx-titulo">
              <p class="lx-versal">Ao seu serviço</p>
              <h2>Concierge</h2>
            </header>
            <div class="lx-concierge">
              <div>
                <span class="lx-concierge__num">I</span>
                <p class="lx-versal">Entrega</p>
                <ul v-if="opcoesEntrega.length || loja.levantamento_ativo">
                  <li v-for="o in opcoesEntrega" :key="o.id">
                    <span>{{ o.nome }}</span><span>{{ Number(o.preco) === 0 ? 'Oferta' : formatPrice(o.preco) }}</span>
                  </li>
                  <li v-if="loja.levantamento_ativo"><span>Levantamento na maison</span><span>Oferta</span></li>
                </ul>
                <p v-else>Sob consulta.</p>
              </div>
              <div>
                <span class="lx-concierge__num">II</span>
                <p class="lx-versal">Pagamento</p>
                <p v-if="metodosPagamento.length" class="lx-concierge__metodos">{{ metodosPagamento.map(m => m.tipo).join(' · ') }}</p>
                <p v-else>—</p>
              </div>
              <div>
                <span class="lx-concierge__num">III</span>
                <p class="lx-versal">A maison</p>
                <p>{{ loja.localizacao || 'Exclusivamente online.' }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- ══ TESTEMUNHOS ══ -->
        <section id="lx-avaliacoes" class="lx-sec">
          <div class="lx-wrap">
            <header class="lx-titulo">
              <p class="lx-versal">Testemunhos</p>
              <h2>Avaliações</h2>
            </header>
            <AvaliacaoLoja
              :loja-id="lojaId"
              :isDark="isDark"
              summary-border-radius="rounded-none"
              form-border-radius="rounded-none"
              review-card-border-radius="rounded-none"
              button-border-radius="rounded-none"
              textarea-border-radius="rounded-none"
              :star-active-class="'lx-estrela--on'"
              :star-inactive-class="'lx-estrela--off'"
              progress-bar-class="lx-barra"
              :submit-button-class="'lx-btn lx-btn--ouro w-full justify-center'"
              :review-card-class="'lx-review'"
              :own-review-border-class="'lx-review--minha'"
              :load-more-button-class="'lx-btn lx-btn--fino'"
              @rating-updated="onRatingUpdated"
            />
          </div>
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="lx-footer">
        <div class="lx-wrap lx-footer__inner">
          <span class="lx-monograma lx-monograma--pequeno">{{ loja.nome.charAt(0) }}</span>
          <p class="lx-footer__nome">{{ loja.nome }}</p>
          <nav class="lx-footer__links">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
          </nav>
          <p class="lx-footer__copy">© {{ ano }} {{ loja.nome }}<template v-if="loja.localizacao"> — {{ loja.localizacao }}</template></p>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="lx-modal" @click.self="modalPolitica = null">
        <div class="lx-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="lx-circ" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="lx-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="lx-vazio">
      <p>Loja não encontrada</p>
      <button class="lx-btn lx-btn--ouro" @click="$router.back()">Voltar</button>
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

export default {
  name: 'TemplateLuxoPremium',

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
    const fila = ref(null)
    const vitrineIdx = ref(0)
    const modoEscolhido = ref(null)
    const grupoKey = ref(null)

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#b8975a',
      '--cor-secundaria': props.tema?.corSecundaria || '#0e0d0c',
    }))

    // ── Vitrine: uma peça de cada vez; pede a página seguinte ao chegar ao fim ──
    function posicao (l) { return Math.min(vitrineIdx.value, Math.max(l.itens.length - 1, 0)) }
    function atual (l) { return l.itens[posicao(l)] }

    function mover (l, dir) {
      const n = l.itens.length
      if (!n) return
      let i = posicao(l) + dir
      if (i >= n) {
        if (l.temMais || l.aCarregarMais) { l.carregarMais(); i = n }   // mostra-a assim que chegar
        else i = 0
      }
      if (i < 0) i = (l.temMais || l.aCarregarMais) ? 0 : n - 1
      vitrineIdx.value = i
    }

    // ── Coleções (só metadados; as peças vêm página a página) ──
    const grupos = lojaData.gruposProdutos

    const modos = computed(() => [
      { key: 'tipo', label: 'Por tipo' },
      { key: 'categoria', label: 'Por categoria' },
      { key: 'todos', label: 'Todas' },
    ].filter(m => grupos.value.some(g => g.seccao === m.key)))

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
      const el = fila.value
      if (el) el.scrollBy({ left: dir * el.clientWidth * 0.75, behavior: 'smooth' })
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
        return min === 0 ? 'Entrega oferecida' : `Entrega desde ${lojaData.formatPrice(min)}`
      }
      return lojaData.loja.value?.levantamento_ativo ? 'Levantamento na maison' : 'Entrega sob consulta'
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

    function onScroll () { scrolled.value = window.scrollY > window.innerHeight * 0.6 }

    onMounted(() => {
      window.addEventListener('scroll', onScroll, { passive: true })
      onScroll()
    })
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return {
      ...lojaData,
      isDark, user, ano, cssVars, scrolled, fila,
      posicao, atual, mover,
      grupos, modos, modo, gruposDoModo, grupoKey, grupoActivo, mudarModo, deslizar,
      rating, textoEntrega, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, esgotado, precoDe,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;1,6..96,400&family=Montserrat:wght@300;400;500&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.lx-root {
  --ouro: var(--cor-primaria, #b8975a);
  --serif: 'Bodoni Moda', Didot, Georgia, serif;
  --sans: 'Montserrat', system-ui, sans-serif;
  --bar-h: 68px;
  --bar-pad: 28px;
  /* carrinho · notificações · perfil alinhados com a barra (assets/loja-acoes.css) */
  --acoes-altura: var(--bar-h);
  --acoes-direita: var(--bar-pad);

  font-family: var(--sans);
  font-weight: 300;
  background: var(--bg);
  color: var(--fg);
  min-height: 100vh;
  overflow-x: hidden;
  transition: background .5s, color .5s;
}
.lx-dark {
  --bg: var(--cor-secundaria, #0e0d0c);
  --painel: color-mix(in srgb, var(--bg) 92%, #fff 8%);
  --fg: #f1ece3;
  --fg2: #9d968a;
  --linha: rgba(241, 236, 227, .12);
  --foco: radial-gradient(ellipse at 50% 38%, color-mix(in srgb, var(--ouro) 22%, transparent), transparent 62%);
}
.lx-light {
  --bg: #f7f4ee;
  --painel: #fffdf9;
  --fg: #1a1714;
  --fg2: #7d7568;
  --linha: rgba(26, 23, 20, .12);
  --foco: radial-gradient(ellipse at 50% 38%, #ffffff, transparent 65%);
}

.lx-wrap { max-width: 1240px; margin: 0 auto; padding: 0 var(--bar-pad); }
.lx-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.lx-hide-scroll::-webkit-scrollbar { display: none; }
.lx-versal { margin: 0; font-size: 11px; font-weight: 500; letter-spacing: .36em; text-transform: uppercase; color: var(--ouro); }

/* ── Loading ─────────────────────────────────────────────── */
.lx-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; align-items: center; justify-content: center; }
.lx-loading__linha { width: 1px; height: 64px; background: var(--ouro); animation: lxCresce 1.2s ease-in-out infinite alternate; transform-origin: top; }
@keyframes lxCresce { from { transform: scaleY(.1); opacity: .3; } to { transform: scaleY(1); opacity: 1; } }

/* ── Barra ───────────────────────────────────────────────── */
.lx-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center; gap: 8px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 12px) 0 var(--bar-pad);
  color: #f1ece3; transition: background .4s, color .4s, border-color .4s;
  border-bottom: 1px solid transparent;
}
.lx-bar--solida { background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(10px); color: var(--fg); border-bottom-color: var(--linha); }
.lx-circ {
  width: 38px; height: 38px; flex-shrink: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: transparent; color: inherit; border: 1px solid currentColor; cursor: pointer;
  opacity: .85; transition: opacity .2s, color .2s, border-color .2s;
}
.lx-circ:hover { opacity: 1; color: var(--ouro); border-color: var(--ouro); }
.lx-bar__nome {
  margin-left: 10px; min-width: 0; font-family: var(--serif); font-size: 18px; letter-spacing: .12em; text-transform: uppercase;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; opacity: 0; transition: opacity .4s;
}
.lx-bar__nome--on { opacity: 1; }

/* ── Hero ────────────────────────────────────────────────── */
.lx-hero {
  position: relative; min-height: 100vh; min-height: 100svh; display: flex; align-items: center; justify-content: center;
  overflow: hidden; background: #0e0d0c; color: #f1ece3;
}
.lx-hero__media { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; animation: lxZoom 22s ease-out both; }
@keyframes lxZoom { from { transform: scale(1.08); } to { transform: scale(1); } }
.lx-hero__veu { position: absolute; inset: 0; background: radial-gradient(ellipse at center, rgba(10,9,8,.45), rgba(10,9,8,.85)); }
.lx-hero__moldura { position: absolute; inset: calc(var(--bar-h) + 6px) 28px 28px; border: 1px solid color-mix(in srgb, var(--ouro) 45%, transparent); pointer-events: none; }
.lx-hero__centro { position: relative; z-index: 1; text-align: center; padding: calc(var(--bar-h) + 40px) 32px 80px; max-width: 900px; }
.lx-monograma {
  display: inline-flex; align-items: center; justify-content: center; width: 78px; height: 78px; margin-bottom: 26px;
  border-radius: 50%; border: 1px solid var(--ouro); color: var(--ouro); overflow: hidden;
  font-family: var(--serif); font-size: 34px; font-style: italic;
}
.lx-monograma img { width: 100%; height: 100%; object-fit: cover; }
.lx-monograma--pequeno { width: 52px; height: 52px; font-size: 22px; margin-bottom: 18px; }
.lx-hero__nome { margin: 22px 0 22px; font-family: var(--serif); font-weight: 400; font-size: clamp(3rem, 9vw, 7.5rem); line-height: .95; letter-spacing: .02em; text-wrap: balance; }
.lx-hero__desc { margin: 0 auto 36px; max-width: 540px; font-size: 16px; line-height: 1.8; color: rgba(241, 236, 227, .78); }
.lx-hero__ctas { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; }
.lx-hero__desce { position: absolute; left: 50%; bottom: 44px; transform: translateX(-50%); z-index: 1; width: 24px; height: 52px; background: none; border: none; cursor: pointer; }
.lx-hero__desce span { display: block; width: 1px; height: 100%; margin: 0 auto; background: linear-gradient(var(--ouro), transparent); animation: lxDesce 2s ease-in-out infinite; }
@keyframes lxDesce { 0% { transform: scaleY(0); transform-origin: top; } 50% { transform: scaleY(1); transform-origin: top; } 51% { transform-origin: bottom; } 100% { transform: scaleY(0); transform-origin: bottom; } }

.lx-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 15px 30px;
  font: inherit; font-size: 11px; font-weight: 500; letter-spacing: .3em; text-transform: uppercase;
  cursor: pointer; border: 1px solid var(--ouro); background: transparent; color: inherit; border-radius: 0;
  transition: background .3s, color .3s;
}
.lx-btn--ouro { background: var(--ouro); color: #0e0d0c; }
.lx-btn--ouro:hover { background: transparent; color: var(--ouro); }
.lx-btn--fino:hover { background: var(--ouro); color: #0e0d0c; }

/* ── Dados ───────────────────────────────────────────────── */
.lx-dados { border-bottom: 1px solid var(--linha); }
.lx-dados__linha { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px 48px; padding-top: 22px; padding-bottom: 22px; font-size: 12px; letter-spacing: .16em; text-transform: uppercase; color: var(--fg2); }
.lx-dados__linha em { font-family: var(--serif); font-style: italic; font-size: 20px; letter-spacing: 0; text-transform: none; color: var(--fg); margin-right: 4px; }

/* ── Secções ─────────────────────────────────────────────── */
.lx-sec { padding-top: 112px; scroll-margin-top: var(--bar-h); }
.lx-titulo { text-align: center; margin-bottom: 48px; }
.lx-titulo h2 { margin: 16px 0 0; font-family: var(--serif); font-weight: 400; font-size: clamp(2.2rem, 4.6vw, 3.6rem); line-height: 1.05; text-transform: capitalize; }
.lx-titulo__n { margin: 10px 0 0; font-size: 12px; letter-spacing: .2em; text-transform: uppercase; color: var(--fg2); }

/* ── Vitrine ─────────────────────────────────────────────── */
.lx-vitrine { position: relative; }
.lx-vitrine__peca { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 64px; align-items: center; }
.lx-foco {
  position: relative; display: flex; align-items: center; justify-content: center; width: 100%; aspect-ratio: 1;
  padding: 10%; border: 1px solid var(--linha); background: var(--foco), var(--painel); cursor: pointer;
}
.lx-foco img, .lx-foco video { width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 30px 40px rgba(0,0,0,.35)); transition: transform .8s cubic-bezier(.2,.8,.2,1); }
.lx-foco:hover img { transform: scale(1.04); }
.lx-foco__inicial { font-family: var(--serif); font-style: italic; font-size: 120px; color: var(--ouro); }
.lx-vitrine__info { max-width: 420px; }
.lx-vitrine__nome { margin: 18px 0 18px; font-family: var(--serif); font-weight: 400; font-size: clamp(2rem, 3.6vw, 3rem); line-height: 1.1; }
.lx-vitrine__desc { margin: 0 0 24px; font-size: 15px; line-height: 1.85; color: var(--fg2); }
.lx-vitrine__preco { margin: 0 0 28px; font-family: var(--serif); font-size: 26px; font-style: italic; color: var(--ouro); }
.lx-vitrine__esgotado { margin: -18px 0 22px; font-size: 11px; letter-spacing: .3em; text-transform: uppercase; color: var(--fg2); }
.lx-vitrine__nav { display: flex; align-items: center; justify-content: center; gap: 22px; margin-top: 40px; color: var(--fg); }
.lx-vitrine__conta { display: inline-flex; align-items: center; gap: 14px; font-family: var(--serif); font-size: 15px; letter-spacing: .1em; }
.lx-vitrine__barra { display: inline-block; width: 120px; height: 1px; background: var(--linha); position: relative; }
.lx-vitrine__barra b { position: absolute; left: 0; top: 0; bottom: 0; background: var(--ouro); transition: width .5s; }
.lx-vitrine--vazia { max-width: 560px; }
.lx-troca-enter-active, .lx-troca-leave-active { transition: opacity .45s, transform .45s; }
.lx-troca-enter-from { opacity: 0; transform: translateX(16px); }
.lx-troca-leave-to { opacity: 0; transform: translateX(-16px); }

.lx-skel { background: var(--painel); border: 1px solid var(--linha); animation: lxPulso 1.6s ease-in-out infinite; }
.lx-skel--peca { aspect-ratio: 3 / 4; }
@keyframes lxPulso { 50% { opacity: .45; } }

/* ── Coleções ────────────────────────────────────────────── */
.lx-modos { display: flex; justify-content: center; gap: 28px; margin: -24px 0 22px; }
.lx-modos button { background: none; border: none; cursor: pointer; font: inherit; font-size: 11px; font-weight: 500; letter-spacing: .3em; text-transform: uppercase; color: var(--fg2); padding: 4px 0; border-bottom: 1px solid transparent; }
.lx-modos .lx-on { color: var(--ouro); border-bottom-color: var(--ouro); }
.lx-colecoes { display: flex; justify-content: center; flex-wrap: wrap; gap: 6px 30px; margin-bottom: 48px; }
.lx-colecoes button {
  background: none; border: none; cursor: pointer; padding: 4px 0; color: var(--fg2);
  font-family: var(--serif); font-size: 24px; text-transform: capitalize; transition: color .3s;
}
.lx-colecoes button sup { font-family: var(--sans); font-size: 10px; margin-left: 4px; letter-spacing: .1em; }
.lx-colecoes button:hover { color: var(--fg); }
.lx-colecoes .lx-on { color: var(--fg); font-style: italic; }

.lx-fila {
  display: grid; grid-auto-flow: column; grid-auto-columns: 300px; gap: 28px;
  overflow-x: auto; scroll-snap-type: x mandatory;
  padding: 0 max(var(--bar-pad), calc((100vw - 1240px) / 2 + var(--bar-pad)));
  scroll-padding: 0 max(var(--bar-pad), calc((100vw - 1240px) / 2 + var(--bar-pad)));
}
.lx-fila > * { scroll-snap-align: start; }
.lx-fila__nav { display: flex; justify-content: flex-end; gap: 10px; margin-top: 28px; color: var(--fg); }
.lx-peca { display: flex; flex-direction: column; text-align: left; padding: 0; min-width: 0; background: none; border: none; cursor: pointer; color: inherit; font: inherit; }
.lx-peca__foco {
  position: relative; display: flex; align-items: center; justify-content: center; aspect-ratio: 3 / 4; padding: 12%;
  border: 1px solid var(--linha); background: var(--foco), var(--painel); margin-bottom: 18px; transition: border-color .4s;
}
.lx-peca:hover .lx-peca__foco { border-color: color-mix(in srgb, var(--ouro) 60%, transparent); }
.lx-peca__foco img, .lx-peca__foco video { width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 20px 26px rgba(0,0,0,.3)); transition: transform .8s cubic-bezier(.2,.8,.2,1); }
.lx-peca:hover .lx-peca__foco img { transform: scale(1.05); }
.lx-peca__foco .lx-foco__inicial { font-size: 72px; }
.lx-peca__esgotado { position: absolute; left: 0; right: 0; bottom: 14px; text-align: center; font-size: 10px; letter-spacing: .3em; text-transform: uppercase; color: var(--fg2); }
.lx-peca__num { font-family: var(--serif); font-style: italic; font-size: 13px; color: var(--ouro); }
.lx-peca__nome { margin: 6px 0 8px; font-family: var(--serif); font-size: 20px; line-height: 1.25; }
.lx-peca__preco { font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: var(--fg2); }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.lx-catalogo :deep(.bg-zinc-900), .lx-catalogo :deep(.bg-white) { background: var(--painel) !important; }
.lx-catalogo :deep(.bg-zinc-800), .lx-catalogo :deep(.bg-gray-50), .lx-catalogo :deep(.bg-gray-100),
.lx-catalogo :deep(.bg-zinc-700), .lx-catalogo :deep(.bg-gray-200) { background: var(--bg) !important; }
.lx-catalogo :deep(.border-zinc-800), .lx-catalogo :deep(.border-zinc-700),
.lx-catalogo :deep(.border-gray-200), .lx-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.lx-catalogo :deep(.text-zinc-100), .lx-catalogo :deep(.text-zinc-900) { color: var(--fg) !important; }
.lx-catalogo :deep(input), .lx-catalogo :deep(select) { color: var(--fg) !important; font-family: var(--sans); }
.lx-catalogo :deep(input:focus), .lx-catalogo :deep(select:focus) { border-color: var(--ouro) !important; outline: none; }
.lx-catalogo :deep(.lx-tab) { background: transparent; color: var(--fg2); border: 1px solid var(--linha); font-size: 11px; letter-spacing: .2em; text-transform: uppercase; }
.lx-catalogo :deep(.lx-tab--on) { background: var(--ouro) !important; color: #0e0d0c !important; border: 1px solid var(--ouro) !important; font-size: 11px; letter-spacing: .2em; text-transform: uppercase; }
.lx-catalogo :deep(.lx-cat-borda) { border-color: var(--linha) !important; }
.lx-catalogo :deep(.lx-cat-nome) { font-family: var(--serif); font-size: 17px; font-weight: 400; }
.lx-catalogo :deep(.lx-cat-preco) { color: var(--ouro) !important; font-family: var(--serif); font-style: italic; font-weight: 400; }
.lx-catalogo :deep(.lx-cat-badge) { background: var(--ouro) !important; color: #0e0d0c !important; border-radius: 0 !important; letter-spacing: .2em; text-transform: uppercase; }
.lx-catalogo :deep(.lx-cat-indicador) { background: var(--bg) !important; color: var(--fg) !important; }
.lx-catalogo :deep(.lx-cat-limpar) { color: var(--ouro) !important; }
.lx-catalogo :deep(.lx-cat-spinner) { color: var(--ouro) !important; }

/* ── Concierge ───────────────────────────────────────────── */
.lx-concierge { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--linha); border-bottom: 1px solid var(--linha); }
.lx-concierge > div { padding: 40px 36px; text-align: center; }
.lx-concierge > div + div { border-left: 1px solid var(--linha); }
.lx-concierge__num { display: block; margin-bottom: 14px; font-family: var(--serif); font-style: italic; font-size: 26px; color: var(--ouro); }
.lx-concierge .lx-versal { margin-bottom: 16px; color: var(--fg2); }
.lx-concierge p { margin: 0; font-family: var(--serif); font-size: 18px; line-height: 1.6; }
.lx-concierge ul { list-style: none; margin: 0; padding: 0; }
.lx-concierge li { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; font-family: var(--serif); font-size: 17px; }
.lx-concierge li span:last-child { font-style: italic; color: var(--ouro); }
.lx-concierge__metodos { text-transform: capitalize; }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.lx-estrela--on) { color: var(--ouro) !important; }
:deep(.lx-estrela--off) { color: var(--linha) !important; }
:deep(.lx-barra) { background: var(--ouro) !important; }
:deep(.lx-review) { background: var(--painel) !important; border: 1px solid var(--linha) !important; }
:deep(.lx-review--minha) { border: 1px solid var(--ouro) !important; }
:deep(.lx-btn) { display: inline-flex; padding: 14px 26px; border: 1px solid var(--ouro); font-size: 11px; letter-spacing: .26em; text-transform: uppercase; font-weight: 500; }
:deep(.lx-btn--ouro) { background: var(--ouro) !important; color: #0e0d0c !important; }

/* ── Rodapé ──────────────────────────────────────────────── */
.lx-footer { margin-top: 128px; padding: 72px 0 40px; border-top: 1px solid var(--linha); }
.lx-footer__inner { text-align: center; }
.lx-footer__nome { margin: 0; font-family: var(--serif); font-size: clamp(1.8rem, 4vw, 2.8rem); letter-spacing: .14em; text-transform: uppercase; }
.lx-footer__links { display: flex; justify-content: center; flex-wrap: wrap; gap: 8px 32px; margin: 30px 0 22px; }
.lx-footer__links button { background: none; border: none; cursor: pointer; color: var(--fg2); font: inherit; font-size: 11px; font-weight: 500; letter-spacing: .28em; text-transform: uppercase; }
.lx-footer__links button:hover { color: var(--ouro); }
.lx-footer__copy { margin: 0; font-size: 12px; letter-spacing: .08em; color: var(--fg2); }

/* ── Modal ───────────────────────────────────────────────── */
.lx-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.6); }
.lx-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--bg); color: var(--fg); border: 1px solid var(--linha); }
.lx-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 18px 22px; background: var(--bg); border-bottom: 1px solid var(--linha); }
.lx-modal__painel h3 { margin: 0; font-family: var(--serif); font-size: 24px; font-weight: 400; }
.lx-modal__corpo { padding: 22px; font-size: 14px; line-height: 1.85; color: var(--fg2); white-space: pre-wrap; }

.lx-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 18px; align-items: center; justify-content: center; font-family: var(--serif); font-size: 28px; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .lx-vitrine__peca { grid-template-columns: minmax(0, 1fr); gap: 32px; }
  .lx-foco { max-width: 560px; margin: 0 auto; }
  .lx-vitrine__info { max-width: none; text-align: center; }
  .lx-concierge { grid-template-columns: minmax(0, 1fr); }
  .lx-concierge > div + div { border-left: none; border-top: 1px solid var(--linha); }
}

@media (max-width: 640px) {
  .lx-root { --bar-h: 60px; --bar-pad: 14px; }
  .lx-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .lx-circ { width: 34px; height: 34px; }
  .lx-bar__nome { font-size: 15px; letter-spacing: .08em; }
  .lx-hero__moldura { inset: calc(var(--bar-h) + 4px) 12px 12px; }
  .lx-hero__centro { padding: calc(var(--bar-h) + 28px) 22px 72px; }
  .lx-monograma { width: 64px; height: 64px; font-size: 28px; }
  .lx-hero__desc { font-size: 15px; }
  .lx-btn { padding: 14px 22px; letter-spacing: .24em; }
  .lx-dados__linha { gap: 8px 22px; font-size: 11px; }
  .lx-sec { padding-top: 80px; }
  .lx-titulo { margin-bottom: 36px; }
  .lx-colecoes { gap: 4px 20px; margin-bottom: 32px; }
  .lx-colecoes button { font-size: 20px; }
  .lx-fila { grid-auto-columns: 68%; gap: 16px; }
  .lx-peca__nome { font-size: 17px; }
  .lx-concierge > div { padding: 30px 12px; }
}
</style>
