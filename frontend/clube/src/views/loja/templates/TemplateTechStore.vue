<!-- TemplateTechStore.vue — Revamp "ficha técnica"
     A loja como uma ficha de especificações: hero com tabela de dados e banner num ecrã
     com marcas de corte · destaques num carrossel de cartões com specs (scroll infinito) ·
     explorador por tipo/categoria com vista Grelha ou Lista (linhas tipo tabela de specs) ·
     catálogo completo · serviço em tabela · avaliações.
     Produtos sempre paginados pelo servidor (ProdutosPaginados / FimDaLista).
     Tipografia: Geist + Geist Mono. Acento: --cor-primaria. Fundo escuro: --cor-secundaria.
     Sem emojis (ícones SVG funcionais apenas).
-->
<template>
  <div class="ts-root" :class="isDark ? 'ts-dark' : 'ts-light'" :style="cssVars">
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
    <div v-if="loading" class="ts-loading">
      <span class="ts-loading__barra"></span>
      <span class="ts-mono">a carregar</span>
    </div>

    <template v-else-if="loja">
      <!-- ══ BARRA ══ -->
      <header class="ts-bar" :class="{ 'ts-bar--solida': scrolled }">
        <button class="ts-quad" @click="$router.back()" aria-label="Voltar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="ts-quad" @click="toggleDark" :aria-label="isDark ? 'Modo claro' : 'Modo escuro'">
          <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="ts-bar__marca">
          <img v-if="loja.logo_url" :src="loja.logo_url" :alt="loja.nome" />
          <span v-else class="ts-bar__inicial">{{ loja.nome.charAt(0) }}</span>
          <span class="ts-bar__nome">{{ loja.nome }}</span>
        </span>
        <nav class="ts-bar__links">
          <button v-if="totalDestaques" @click="scrollToId('ts-destaques')">Destaques</button>
          <button v-if="grupos.length" @click="scrollToId('ts-explorar')">Explorar</button>
          <button @click="scrollToId(soServicos ? 'servicos' : 'ts-catalogo')">{{ soServicos ? 'Serviços' : 'Catálogo' }}</button>
          <button @click="scrollToId('ts-avaliacoes')">Avaliações</button>
        </nav>
      </header>

      <!-- ══ HERO ══ -->
      <section class="ts-hero">
        <div class="ts-wrap ts-hero__grid">
          <div class="ts-hero__texto">
            <p class="ts-eyebrow ts-mono">
              <span class="ts-ponto"></span>
              {{ loja.categoria || 'Tecnologia' }}<template v-if="loja.localizacao"> / {{ loja.localizacao }}</template>
            </p>
            <h1 class="ts-hero__nome">{{ loja.nome }}</h1>
            <BotaoFavorito tipo="loja" :id="lojaId" variante="pilula" :tamanho="28" class="loja-fav" />
            <EstadoLoja :horario="loja.horario" :loja-id="lojaId" class="loja-estado" />
            <p v-if="loja.descricao" class="ts-hero__desc">{{ truncate(loja.descricao, 190) }}</p>

            <dl class="ts-specs">
              <div>
                <dt class="ts-mono">Avaliação</dt>
                <dd>
                  {{ rating }}<small v-if="loja.rating_medio">/5</small>
                  <span class="ts-specs__nota">{{ loja.total_avaliacoes || 0 }} avaliações</span>
                </dd>
              </div>
              <div>
                <dt class="ts-mono">{{ soServicos ? 'Serviços' : 'Produtos' }}</dt>
                <dd>{{ soServicos ? totalServicos : (totalProdutos ?? '—') }}<span v-if="!soServicos" class="ts-specs__nota">{{ grupos.length }} {{ grupos.length === 1 ? 'secção' : 'secções' }}</span></dd>
              </div>
              <div>
                <dt class="ts-mono">Entrega</dt>
                <dd class="ts-specs__txt">{{ textoEntrega }}</dd>
              </div>
              <div>
                <dt class="ts-mono">Pagamento</dt>
                <dd class="ts-specs__txt">{{ metodosPagamento.length ? metodosPagamento.length + ' métodos' : '—' }}</dd>
              </div>
            </dl>

            <div class="ts-hero__ctas">
              <button class="ts-btn ts-btn--cor" @click="scrollToId(soServicos ? 'servicos' : grupos.length ? 'ts-explorar' : 'ts-catalogo')">
                {{ soServicos ? 'Ver serviços' : 'Explorar produtos' }}
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </button>
              <button v-if="!soServicos" class="ts-btn" @click="scrollToId('ts-catalogo')">Pesquisar no catálogo</button>
            </div>
          </div>

          <div class="ts-ecra">
            <span class="ts-ecra__marca ts-ecra__marca--a"></span>
            <span class="ts-ecra__marca ts-ecra__marca--b"></span>
            <span class="ts-ecra__marca ts-ecra__marca--c"></span>
            <span class="ts-ecra__marca ts-ecra__marca--d"></span>
            <div class="ts-ecra__vidro">
              <video v-if="isVideo(loja.banner_url)" :src="loja.banner_url" :poster="loja.banner_poster_url" v-video-visivel muted loop playsinline></video>
              <img v-else-if="loja.banner_url" :src="loja.banner_url" :alt="loja.nome" />
              <div v-else class="ts-ecra__vazio">{{ loja.nome.charAt(0) }}</div>
            </div>
          </div>
        </div>
      </section>

      <main class="ts-wrap">
        <!-- ══ DESTAQUES (carrossel com scroll infinito) ══ -->
        <section v-if="totalDestaques" id="ts-destaques" class="ts-sec">
          <header class="ts-sec__head">
            <div>
              <p class="ts-eyebrow ts-mono">01 · Seleção</p>
              <h2 class="ts-sec__titulo">Em destaque</h2>
            </div>
            <div class="ts-setas">
              <button class="ts-quad" @click="deslizar(-1)" aria-label="Anterior">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button class="ts-quad" @click="deslizar(1)" aria-label="Seguinte">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
              </button>
            </div>
          </header>

          <ProdutosPaginados :params="{ loja_id: lojaId, destaque: 'true' }" :limit="8" :lazy="false" v-slot="l">
            <div ref="carrossel" class="ts-carrossel ts-hide-scroll">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="ts-skel"></div>
              </template>
              <button v-for="p in l.itens" :key="p.id" class="ts-cartao" @click="selectedProduct = p">
                <span class="ts-cartao__img">
                  <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted loop v-video-visivel playsinline></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="ts-cartao__inicial">{{ p.nome.charAt(0) }}</span>
                  <span class="ts-badge ts-mono">Destaque</span>
                </span>
                <span class="ts-cartao__corpo">
                  <span class="ts-cartao__nome">{{ p.nome }}</span>
                  <span v-for="(v, k) in specs(p)" :key="k" class="ts-cartao__spec ts-mono"><i>{{ k }}</i>{{ v }}</span>
                  <span class="ts-cartao__pe">
                    <span class="ts-preco ts-mono">{{ precoDe(p) }}</span>
                    <span class="ts-estado ts-mono" :class="estado(p).classe">{{ estado(p).texto }}</span>
                  </span>
                </span>
              </button>
              <FimDaLista v-if="l.temMais || l.aCarregarMais" :chave="l.itens.length" @visivel="l.carregarMais()">
                <div class="ts-skel"></div>
              </FimDaLista>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ EXPLORAR (por tipo / por categoria; grelha ou lista) ══ -->
        <section v-if="grupos.length" id="ts-explorar" class="ts-sec">
          <header class="ts-sec__head">
            <div>
              <p class="ts-eyebrow ts-mono">{{ totalDestaques ? '02' : '01' }} · Navegar</p>
              <h2 class="ts-sec__titulo">Explorar</h2>
            </div>
            <div class="ts-controlos">
              <div v-if="modos.length > 1" class="ts-seg">
                <button v-for="m in modos" :key="m.key" :class="{ 'ts-on': modo === m.key }" @click="mudarModo(m.key)">{{ m.label }}</button>
              </div>
              <div class="ts-seg ts-seg--icones" role="group" aria-label="Vista">
                <button :class="{ 'ts-on': vista === 'grelha' }" @click="vista = 'grelha'" aria-label="Vista em grelha">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>
                </button>
                <button :class="{ 'ts-on': vista === 'lista' }" @click="vista = 'lista'" aria-label="Vista em lista">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
                </button>
              </div>
            </div>
          </header>

          <div class="ts-chips ts-hide-scroll">
            <button v-for="g in gruposDoModo" :key="g.key" class="ts-chip" :class="{ 'ts-on': grupoActivo?.key === g.key }"
                    @click="grupoKey = g.key">
              {{ g.nome }}<span class="ts-mono">{{ g.total }}</span>
            </button>
          </div>

          <ProdutosPaginados v-if="grupoActivo" :key="grupoActivo.key" :params="grupoActivo.params" :limit="LIMITE" :lazy="false" v-slot="l">
            <!-- Grelha -->
            <div v-if="vista === 'grelha'" class="ts-grelha">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="ts-skel"></div>
              </template>
              <button v-for="p in l.itens" :key="p.id" class="ts-cartao" @click="selectedProduct = p">
                <span class="ts-cartao__img">
                  <BotaoFavorito tipo="produto" :id="p.id" elemento="span" :tamanho="32" class="fav-card" />
                  <video v-if="isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :poster="p.ficheiro_poster_url" muted playsinline :preload="p.ficheiro_poster_url ? 'none' : 'metadata'"></video>
                  <img v-else-if="p.ficheiro_url" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else class="ts-cartao__inicial">{{ p.nome.charAt(0) }}</span>
                </span>
                <span class="ts-cartao__corpo">
                  <span class="ts-cartao__nome">{{ p.nome }}</span>
                  <span v-for="(v, k) in specs(p)" :key="k" class="ts-cartao__spec ts-mono"><i>{{ k }}</i>{{ v }}</span>
                  <span class="ts-cartao__pe">
                    <span class="ts-preco ts-mono">{{ precoDe(p) }}</span>
                    <span class="ts-estado ts-mono" :class="estado(p).classe">{{ estado(p).texto }}</span>
                  </span>
                </span>
              </button>
            </div>

            <!-- Lista (tabela de specs) -->
            <div v-else class="ts-lista">
              <template v-if="l.carregando">
                <div v-for="n in 4" :key="n" class="ts-skel ts-skel--linha"></div>
              </template>
              <button v-for="p in l.itens" :key="p.id" class="ts-linha" @click="selectedProduct = p">
                <span class="ts-linha__img">
                  <img v-if="p.ficheiro_url && !isVideo(p.ficheiro_url)" :src="p.ficheiro_url" :alt="p.nome" loading="lazy" />
                  <span v-else>{{ p.nome.charAt(0) }}</span>
                </span>
                <span class="ts-linha__info">
                  <span class="ts-linha__nome">{{ p.nome }}</span>
                  <span class="ts-linha__specs ts-mono">
                    <span v-for="(v, k) in specs(p, 4)" :key="k"><i>{{ k }}</i>{{ v }}</span>
                  </span>
                </span>
                <span class="ts-estado ts-mono" :class="estado(p).classe">{{ estado(p).texto }}</span>
                <span class="ts-preco ts-mono">{{ precoDe(p) }}</span>
                <svg class="ts-linha__seta" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
              </button>
            </div>

            <div v-if="l.temMais || l.aCarregarMais" class="ts-mais">
              <button class="ts-btn" :disabled="l.aCarregarMais" @click="l.carregarMais()">
                {{ l.aCarregarMais ? 'A carregar…' : 'Carregar mais' }}
                <span class="ts-mono ts-mais__n">{{ l.itens.length }}/{{ l.total }}</span>
              </button>
            </div>
          </ProdutosPaginados>
        </section>

        <!-- ══ SERVIÇOS ══ -->
        <SeccaoServicos :loja-id="lojaId" :isDark="isDark" :cor="tema?.corPrimaria || '#dc2626'" class="ts-sec" />

        <!-- ══ CATÁLOGO ══ -->
        <section v-if="!soServicos" id="ts-catalogo" class="ts-sec">
          <header class="ts-sec__head">
            <div>
              <p class="ts-eyebrow ts-mono">Pesquisa e filtros</p>
              <h2 class="ts-sec__titulo">Catálogo completo</h2>
            </div>
          </header>
          <div class="ts-catalogo">
            <ProductCatalog
              :loja-id="lojaId"
              :isDark="isDark"
              grid-class="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
              image-height="200px"
              card-border-radius="rounded-2xl"
              skeleton-class="rounded-2xl"
              hover-effect="transition-transform duration-300 hover:-translate-y-1"
              hover-border-class=""
              filter-container-radius="rounded-2xl"
              input-border-radius="rounded-xl"
              input-focus-class="ts-foco"
              tab-border-radius="rounded-lg"
              active-tab-class="ts-tab--on"
              inactive-tab-dark-class="ts-tab"
              inactive-tab-light-class="ts-tab"
              active-sub-tab-class="ts-tab--on"
              inactive-sub-tab-dark-class="ts-tab"
              inactive-sub-tab-light-class="ts-tab"
              category-border-class="ts-cat-borda"
              product-name-class="ts-cat-nome"
              product-name-hover-class=""
              price-class="ts-cat-preco"
              badge-text="Destaque"
              badge-class="ts-cat-badge"
              indicator-active-class="ts-cat-indicador"
              clear-filter-class="ts-cat-limpar"
              clear-all-class="ts-cat-limpar"
              spinner-class="ts-cat-spinner"
              :show-stock="true"
              :show-category-badges="false"
              empty-text="Nenhum produto encontrado."
              @product-click="selectedProduct = $event"
            />
          </div>
        </section>

        <!-- ══ SERVIÇO ══ -->
        <section id="ts-info" class="ts-sec">
          <header class="ts-sec__head">
            <div>
              <p class="ts-eyebrow ts-mono">Antes de encomendar</p>
              <h2 class="ts-sec__titulo">Serviço</h2>
            </div>
          </header>
          <div class="ts-servico">
            <div class="ts-servico__col">
              <p class="ts-servico__titulo ts-mono">Entrega</p>
              <ul v-if="opcoesEntrega.length || loja.levantamento_ativo">
                <li v-for="o in opcoesEntrega" :key="o.id">
                  <span>{{ o.nome }}</span><b class="ts-mono">{{ Number(o.preco) === 0 ? 'Grátis' : formatPrice(o.preco) }}</b>
                </li>
                <li v-if="loja.levantamento_ativo"><span>Levantamento na loja</span><b class="ts-mono">Grátis</b></li>
              </ul>
              <p v-else>Contacte a loja.</p>
            </div>
            <div class="ts-servico__col">
              <p class="ts-servico__titulo ts-mono">Pagamento</p>
              <div v-if="metodosPagamento.length" class="ts-servico__tags">
                <span v-for="m in metodosPagamento" :key="m.id" class="ts-mono">{{ m.nome }}</span>
              </div>
              <p v-else>—</p>
            </div>
            <div class="ts-servico__col">
              <p class="ts-servico__titulo ts-mono">Loja</p>
              <p v-if="loja.localizacao" class="ts-servico__morada">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ loja.localizacao }}
              </p>
              <p v-else>Loja online.</p>
            </div>
          </div>
        </section>

        <!-- ══ AVALIAÇÕES ══ -->
        <section id="ts-avaliacoes" class="ts-sec">
          <header class="ts-sec__head">
            <div>
              <p class="ts-eyebrow ts-mono">Clientes</p>
              <h2 class="ts-sec__titulo">Avaliações</h2>
            </div>
          </header>
          <AvaliacaoLoja
            :loja-id="lojaId"
            :isDark="isDark"
            summary-border-radius="rounded-2xl"
            form-border-radius="rounded-2xl"
            review-card-border-radius="rounded-2xl"
            button-border-radius="rounded-xl"
            textarea-border-radius="rounded-xl"
            :star-active-class="'ts-estrela--on'"
            :star-inactive-class="'ts-estrela--off'"
            progress-bar-class="ts-barra"
            :submit-button-class="'ts-btn ts-btn--cor w-full justify-center'"
            :review-card-class="'ts-review'"
            :own-review-border-class="'ts-review--minha'"
            :load-more-button-class="'ts-btn'"
            @rating-updated="onRatingUpdated"
          />
        </section>
      </main>

      <!-- ══ RODAPÉ ══ -->
      <footer class="ts-footer">
        <div class="ts-wrap ts-footer__grid">
          <div>
            <p class="ts-footer__nome">{{ loja.nome }}</p>
            <p class="ts-mono ts-footer__meta">{{ loja.categoria || 'Tecnologia' }}<template v-if="loja.localizacao"> / {{ loja.localizacao }}</template></p>
          </div>
          <nav class="ts-footer__links">
            <button v-if="loja.politica_devolucao" @click="modalPolitica = 'devolucao'">Devoluções</button>
            <button v-if="loja.termos_servico" @click="modalPolitica = 'termos'">Termos</button>
            <button v-if="loja.politica_privacidade" @click="modalPolitica = 'privacidade'">Privacidade</button>
          </nav>
          <p class="ts-mono ts-footer__copy">© {{ ano }} {{ loja.nome }}</p>
        </div>
      </footer>

      <!-- Políticas -->
      <div v-if="modalPolitica" class="ts-modal" @click.self="modalPolitica = null">
        <div class="ts-modal__painel">
          <header>
            <h3>{{ tituloPolitica }}</h3>
            <button class="ts-quad" @click="modalPolitica = null" aria-label="Fechar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </header>
          <div class="ts-modal__corpo">{{ textoPolitica }}</div>
        </div>
      </div>
    </template>

    <div v-else class="ts-vazio">
      <p>Loja não encontrada</p>
      <button class="ts-btn ts-btn--cor" @click="$router.back()">Voltar</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useLojaData } from '@/composables/useLojaData'
import { formatarAtributos } from '@/utils/atributos'
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

const LIMITE = 12

export default {
  name: 'TemplateTechStore',

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
    const carrossel = ref(null)
    const modoEscolhido = ref(null)
    const grupoKey = ref(null)
    const vista = ref('grelha')

    const cssVars = computed(() => ({
      '--cor-primaria':   props.tema?.corPrimaria   || '#3d7bff',
      '--cor-secundaria': props.tema?.corSecundaria || '#0b0f17',
    }))

    // ── Explorar (só metadados; os produtos vêm página a página) ──
    const grupos = lojaData.gruposProdutos

    const modos = computed(() => [
      { key: 'tipo', label: 'Por tipo' },
      { key: 'categoria', label: 'Por categoria' },
      { key: 'todos', label: 'Todos' },
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

    // especificações do produto (atributos), já em texto legível
    function specs (p, limite = 2) {
      return formatarAtributos(p.atributos_normalizados || p.atributos, limite)
    }

    function estado (p) {
      if (!p.stock) return { texto: '', classe: 'ts-estado--vazio' }
      const q = Number(p.stock.quantidade)
      if (q <= 0) return { texto: 'Esgotado', classe: 'ts-estado--off' }
      if (q <= 5) return { texto: 'Últimas unidades', classe: 'ts-estado--pouco' }
      return { texto: 'Em stock', classe: 'ts-estado--on' }
    }

    function precoDe (p) {
      const precos = (p.variantes || []).filter(v => v.quantidade > 0).map(v => Number(v.preco_efetivo))
      if (precos.length && Math.min(...precos) !== Math.max(...precos)) {
        return `desde ${lojaData.formatPrice(Math.min(...precos))}`
      }
      return lojaData.formatPrice(p.preco)
    }

    function onScroll () { scrolled.value = window.scrollY > 30 }

    onMounted(() => {
      window.addEventListener('scroll', onScroll, { passive: true })
      onScroll()
    })
    onUnmounted(() => window.removeEventListener('scroll', onScroll))

    return {
      ...lojaData,
      LIMITE,
      isDark, user, ano, cssVars, scrolled, carrossel, vista,
      grupos, modos, modo, gruposDoModo, grupoKey, grupoActivo, mudarModo, deslizar,
      rating, textoEntrega, tituloPolitica, textoPolitica,
      toggleDark, isVideo, truncate, specs, estado, precoDe,
    }
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

/* ── Tokens ──────────────────────────────────────────────── */
.ts-root {
  --cor: var(--cor-primaria, #3d7bff);
  --sans: 'Geist', system-ui, sans-serif;
  --mono: 'Geist Mono', ui-monospace, monospace;
  --raio: 16px;
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
.ts-dark {
  --bg: var(--cor-secundaria, #0b0f17);
  --painel: color-mix(in srgb, var(--bg) 92%, #fff 8%);
  --painel2: color-mix(in srgb, var(--bg) 85%, #fff 15%);
  --fg: #eef2f8;
  --fg2: #8e98aa;
  --linha: rgba(238, 242, 248, .1);
  --grelha: rgba(238, 242, 248, .045);
  --acento: color-mix(in srgb, var(--cor) 80%, #fff 20%);
}
.ts-light {
  --bg: #f4f6f9;
  --painel: #ffffff;
  --painel2: #eef1f5;
  --fg: #0e1420;
  --fg2: #5d6778;
  --linha: rgba(14, 20, 32, .1);
  --grelha: rgba(14, 20, 32, .05);
  --acento: var(--cor);
}

.ts-wrap { max-width: 1320px; margin: 0 auto; padding: 0 var(--bar-pad); }
.ts-mono { font-family: var(--mono); }
.ts-hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
.ts-hide-scroll::-webkit-scrollbar { display: none; }

/* ── Loading ─────────────────────────────────────────────── */
.ts-loading { position: fixed; inset: 0; z-index: 50; background: var(--bg); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: var(--fg2); font-size: 12px; text-transform: uppercase; letter-spacing: .14em; }
.ts-loading__barra { width: 140px; height: 2px; background: var(--linha); position: relative; overflow: hidden; border-radius: 2px; }
.ts-loading__barra::after { content: ''; position: absolute; inset: 0; width: 35%; background: var(--acento); animation: tsCorre 1s ease-in-out infinite; }
@keyframes tsCorre { from { transform: translateX(-100%); } to { transform: translateX(300%); } }

/* ── Barra ───────────────────────────────────────────────── */
.ts-bar {
  /* abaixo do carrinho (z-30) e do perfil (z-40) */
  position: fixed; top: 0; left: 0; right: 0; z-index: 25;
  height: var(--bar-h); display: flex; align-items: center; gap: 8px;
  padding: 0 calc(var(--bar-pad) + var(--acoes-espaco) + 16px) 0 var(--bar-pad);
  border-bottom: 1px solid transparent; transition: background .3s, border-color .3s;
}
.ts-bar--solida { background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(12px); border-bottom-color: var(--linha); }
.ts-quad {
  width: 36px; height: 36px; flex-shrink: 0; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: var(--painel); color: var(--fg); border: 1px solid var(--linha); cursor: pointer;
  transition: border-color .2s, color .2s;
}
.ts-quad:hover { border-color: var(--acento); color: var(--acento); }
.ts-bar__marca { display: flex; align-items: center; gap: 10px; min-width: 0; margin-left: 8px; }
.ts-bar__marca img, .ts-bar__inicial { width: 28px; height: 28px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.ts-bar__inicial { display: flex; align-items: center; justify-content: center; background: var(--cor); color: #fff; font-weight: 700; font-size: 14px; }
.ts-bar__nome { font-weight: 600; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ts-bar__links { display: flex; gap: 2px; margin-left: auto; }
.ts-bar__links button {
  padding: 8px 12px; border-radius: 8px; border: none; background: none; cursor: pointer;
  font: inherit; font-size: 14px; font-weight: 500; color: var(--fg2); transition: color .2s, background .2s;
}
.ts-bar__links button:hover { color: var(--fg); background: var(--painel); }

/* ── Hero ────────────────────────────────────────────────── */
.ts-hero {
  position: relative; padding: calc(var(--bar-h) + 48px) 0 72px; border-bottom: 1px solid var(--linha);
  background-image:
    linear-gradient(var(--grelha) 1px, transparent 1px),
    linear-gradient(90deg, var(--grelha) 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: center top;
}
.ts-hero::after {
  /* brilho suave da cor primária */
  content: ''; position: absolute; right: 8%; top: 20%; width: 480px; height: 480px; border-radius: 50%;
  background: var(--cor); opacity: .14; filter: blur(110px); pointer-events: none;
}
.ts-hero__grid { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 56px; align-items: center; }
.ts-eyebrow { display: inline-flex; align-items: center; gap: 8px; margin: 0; font-size: 12px; font-weight: 500; letter-spacing: .08em; text-transform: uppercase; color: var(--fg2); }
.ts-ponto { width: 7px; height: 7px; border-radius: 50%; background: var(--acento); box-shadow: 0 0 0 4px color-mix(in srgb, var(--cor) 22%, transparent); }
.ts-hero__nome { margin: 18px 0 16px; font-weight: 700; font-size: clamp(2.6rem, 6vw, 5rem); line-height: .98; letter-spacing: -.04em; text-wrap: balance; }
.ts-hero__desc { margin: 0 0 28px; max-width: 520px; font-size: 17px; line-height: 1.6; color: var(--fg2); }

.ts-specs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 0 0 28px; border: 1px solid var(--linha); border-radius: var(--raio); overflow: hidden; background: var(--painel); }
.ts-specs > div { padding: 14px 18px; border-bottom: 1px solid var(--linha); }
.ts-specs > div:nth-child(odd) { border-right: 1px solid var(--linha); }
.ts-specs > div:nth-last-child(-n+2) { border-bottom: none; }
.ts-specs dt { font-size: 11px; letter-spacing: .1em; text-transform: uppercase; color: var(--fg2); margin-bottom: 6px; }
.ts-specs dd { margin: 0; font-size: 26px; font-weight: 600; letter-spacing: -.02em; line-height: 1.1; }
.ts-specs dd small { font-size: 14px; color: var(--fg2); font-weight: 500; }
.ts-specs__nota { display: block; margin-top: 2px; font-size: 12px; font-weight: 400; color: var(--fg2); letter-spacing: 0; }
.ts-specs__txt { font-size: 17px !important; font-weight: 500 !important; }
.ts-hero__ctas { display: flex; flex-wrap: wrap; gap: 10px; }

.ts-btn {
  display: inline-flex; align-items: center; gap: 10px; padding: 13px 20px; border-radius: 12px;
  font: inherit; font-size: 14px; font-weight: 600; cursor: pointer;
  background: var(--painel); color: var(--fg); border: 1px solid var(--linha);
  transition: border-color .2s, transform .2s, background .2s;
}
.ts-btn:hover:not(:disabled) { border-color: var(--acento); transform: translateY(-1px); }
.ts-btn:disabled { opacity: .6; cursor: default; }
.ts-btn--cor { background: var(--cor); border-color: var(--cor); color: #fff; }
.ts-btn--cor:hover:not(:disabled) { background: color-mix(in srgb, var(--cor) 88%, #fff); }

.ts-ecra { position: relative; padding: 18px; }
.ts-ecra__vidro {
  position: relative; aspect-ratio: 4 / 3; border-radius: 20px; overflow: hidden;
  background: var(--painel); border: 1px solid var(--linha);
  box-shadow: 0 40px 80px -30px rgba(0,0,0,.45);
}
.ts-ecra__vidro img, .ts-ecra__vidro video { width: 100%; height: 100%; object-fit: cover; display: block; }
.ts-ecra__vazio { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 140px; font-weight: 700; color: var(--acento); }
/* marcas de corte nos cantos */
.ts-ecra__marca { position: absolute; width: 18px; height: 18px; border-color: var(--acento); border-style: solid; border-width: 0; }
.ts-ecra__marca--a { top: 0; left: 0; border-top-width: 2px; border-left-width: 2px; }
.ts-ecra__marca--b { top: 0; right: 0; border-top-width: 2px; border-right-width: 2px; }
.ts-ecra__marca--c { bottom: 0; left: 0; border-bottom-width: 2px; border-left-width: 2px; }
.ts-ecra__marca--d { bottom: 0; right: 0; border-bottom-width: 2px; border-right-width: 2px; }

/* ── Secções ─────────────────────────────────────────────── */
.ts-sec { padding-top: 80px; scroll-margin-top: calc(var(--bar-h) + 8px); }
.ts-sec__head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
.ts-sec__titulo { margin: 8px 0 0; font-weight: 700; font-size: clamp(1.8rem, 3.6vw, 2.6rem); letter-spacing: -.035em; line-height: 1; }
.ts-setas { display: flex; gap: 8px; }

/* ── Cartões ─────────────────────────────────────────────── */
.ts-cartao {
  display: flex; flex-direction: column; min-width: 0; padding: 0; text-align: left;
  border-radius: var(--raio); overflow: hidden; cursor: pointer; color: var(--fg); font: inherit;
  background: var(--painel); border: 1px solid var(--linha);
  transition: border-color .25s, transform .25s;
}
.ts-cartao:hover { border-color: color-mix(in srgb, var(--acento) 60%, transparent); transform: translateY(-3px); }
.ts-cartao__img { position: relative; display: block; aspect-ratio: 1; background: var(--painel2); }
.ts-cartao__img img, .ts-cartao__img video { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .5s; }
.ts-cartao:hover .ts-cartao__img img { transform: scale(1.04); }
.ts-cartao__inicial { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 56px; font-weight: 700; color: var(--acento); }
.ts-badge {
  position: absolute; left: 10px; top: 10px; padding: 4px 8px; border-radius: 6px;
  background: var(--cor); color: #fff; font-size: 10px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
}
.ts-cartao__corpo { display: flex; flex-direction: column; gap: 4px; padding: 14px 14px 12px; flex: 1; }
.ts-cartao__nome { font-size: 15px; font-weight: 600; line-height: 1.3; margin-bottom: 2px; }
.ts-cartao__spec { font-size: 11.5px; color: var(--fg2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ts-cartao__spec i, .ts-linha__specs i { font-style: normal; text-transform: capitalize; opacity: .7; margin-right: 6px; }
.ts-cartao__pe { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-top: auto; padding-top: 10px; border-top: 1px dashed var(--linha); }
.ts-preco { font-size: 15px; font-weight: 600; color: var(--fg); white-space: nowrap; }
.ts-estado { font-size: 10.5px; letter-spacing: .04em; white-space: nowrap; display: inline-flex; align-items: center; gap: 5px; }
.ts-estado::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.ts-estado--on { color: #22a06b; }
.ts-estado--pouco { color: #d98b0b; }
.ts-estado--off { color: var(--fg2); }
.ts-estado--vazio::before { display: none; }

.ts-carrossel {
  display: grid; grid-auto-flow: column; grid-auto-columns: calc((100% - 3 * 16px) / 4); gap: 16px;
  overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 4px;
}
.ts-carrossel > * { scroll-snap-align: start; }
.ts-skel { aspect-ratio: 3 / 4; border-radius: var(--raio); background: var(--painel); border: 1px solid var(--linha); animation: tsPulso 1.3s ease-in-out infinite; }
.ts-skel--linha { aspect-ratio: auto; height: 84px; }
@keyframes tsPulso { 50% { opacity: .5; } }

/* ── Explorar ────────────────────────────────────────────── */
.ts-controlos { display: flex; gap: 8px; flex-wrap: wrap; }
.ts-seg { display: inline-flex; gap: 2px; padding: 3px; border-radius: 11px; background: var(--painel); border: 1px solid var(--linha); }
.ts-seg button {
  padding: 7px 12px; border-radius: 8px; border: none; background: none; cursor: pointer;
  font: inherit; font-size: 13px; font-weight: 500; color: var(--fg2); display: inline-flex; align-items: center;
}
.ts-seg .ts-on { background: var(--painel2); color: var(--fg); box-shadow: 0 1px 2px rgba(0,0,0,.15); }
.ts-seg--icones button { padding: 7px 9px; }

.ts-chips { display: flex; gap: 8px; overflow-x: auto; padding: 2px 0 20px; }
.ts-chip {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; padding: 9px 14px; border-radius: 10px;
  background: transparent; border: 1px solid var(--linha); color: var(--fg2); cursor: pointer;
  font: inherit; font-size: 14px; font-weight: 500; text-transform: capitalize; transition: color .2s, border-color .2s, background .2s;
}
.ts-chip span { font-size: 11px; opacity: .7; }
.ts-chip:hover { color: var(--fg); }
.ts-chip.ts-on { color: var(--fg); border-color: var(--acento); background: color-mix(in srgb, var(--cor) 12%, transparent); }

.ts-grelha { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }

.ts-lista { display: flex; flex-direction: column; border: 1px solid var(--linha); border-radius: var(--raio); overflow: hidden; background: var(--painel); }
.ts-lista .ts-skel--linha { border-radius: 0; border: none; border-bottom: 1px solid var(--linha); }
.ts-linha {
  display: grid; grid-template-columns: 56px minmax(0, 1fr) 130px 120px 16px; align-items: center; gap: 18px;
  padding: 12px 18px; text-align: left; background: none; border: none; border-bottom: 1px solid var(--linha);
  cursor: pointer; color: inherit; font: inherit; transition: background .2s;
}
.ts-linha:last-child { border-bottom: none; }
.ts-linha:hover { background: var(--painel2); }
.ts-linha__img { width: 56px; height: 56px; border-radius: 10px; overflow: hidden; background: var(--painel2); display: flex; align-items: center; justify-content: center; font-weight: 700; color: var(--acento); }
.ts-linha__img img { width: 100%; height: 100%; object-fit: cover; }
.ts-linha__info { min-width: 0; }
.ts-linha__nome { display: block; font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ts-linha__specs { display: flex; flex-wrap: wrap; gap: 2px 16px; margin-top: 4px; font-size: 11.5px; color: var(--fg2); }
.ts-linha .ts-preco { text-align: right; }
.ts-linha__seta { color: var(--fg2); }

.ts-mais { display: flex; justify-content: center; margin-top: 24px; }
.ts-mais__n { font-size: 12px; color: var(--fg2); }

/* ── Catálogo (ProductCatalog no tom do template) ───────── */
.ts-catalogo :deep(.bg-zinc-900), .ts-catalogo :deep(.bg-white) { background: var(--painel) !important; }
.ts-catalogo :deep(.bg-zinc-800), .ts-catalogo :deep(.bg-gray-50), .ts-catalogo :deep(.bg-gray-100),
.ts-catalogo :deep(.bg-zinc-700), .ts-catalogo :deep(.bg-gray-200) { background: var(--painel2) !important; }
.ts-catalogo :deep(.border-zinc-800), .ts-catalogo :deep(.border-zinc-700),
.ts-catalogo :deep(.border-gray-200), .ts-catalogo :deep(.border-gray-300) { border-color: var(--linha) !important; }
.ts-catalogo :deep(.text-zinc-100), .ts-catalogo :deep(.text-zinc-900) { color: var(--fg) !important; }
.ts-catalogo :deep(input), .ts-catalogo :deep(select) { color: var(--fg) !important; font-family: var(--sans); }
.ts-catalogo :deep(input:focus), .ts-catalogo :deep(select:focus) { border-color: var(--acento) !important; outline: none; }
.ts-catalogo :deep(.ts-tab) { background: transparent; color: var(--fg2); border: 1px solid var(--linha); font-weight: 500; text-transform: capitalize; }
.ts-catalogo :deep(.ts-tab--on) { background: color-mix(in srgb, var(--cor) 14%, transparent) !important; color: var(--fg) !important; border: 1px solid var(--acento) !important; font-weight: 500; text-transform: capitalize; }
.ts-catalogo :deep(.ts-cat-borda) { border-color: var(--linha) !important; }
.ts-catalogo :deep(.ts-cat-nome) { font-weight: 600; }
.ts-catalogo :deep(.ts-cat-preco) { color: var(--fg) !important; font-family: var(--mono); font-weight: 600; }
.ts-catalogo :deep(.ts-cat-badge) { background: var(--cor) !important; color: #fff !important; border-radius: 6px !important; font-family: var(--mono); letter-spacing: .06em; }
.ts-catalogo :deep(.ts-cat-indicador) { background: var(--painel2) !important; color: var(--fg) !important; }
.ts-catalogo :deep(.ts-cat-limpar) { color: var(--acento) !important; }
.ts-catalogo :deep(.ts-cat-spinner) { color: var(--acento) !important; }

/* ── Serviço ─────────────────────────────────────────────── */
.ts-servico { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--linha); border-radius: var(--raio); overflow: hidden; background: var(--painel); }
.ts-servico__col { padding: 24px; }
.ts-servico__col + .ts-servico__col { border-left: 1px solid var(--linha); }
.ts-servico__titulo { margin: 0 0 14px; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--acento); }
.ts-servico p { margin: 0; font-size: 15px; line-height: 1.6; color: var(--fg2); }
.ts-servico ul { list-style: none; margin: 0; padding: 0; }
.ts-servico li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 14px; border-bottom: 1px dashed var(--linha); }
.ts-servico li:last-child { border-bottom: none; }
.ts-servico li b { font-weight: 500; }
.ts-servico__tags { display: flex; flex-wrap: wrap; gap: 6px; }
.ts-servico__tags span { padding: 6px 10px; border-radius: 8px; background: var(--painel2); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
.ts-servico__morada { display: flex; gap: 8px; align-items: flex-start; }
.ts-servico__morada svg { flex-shrink: 0; margin-top: 4px; color: var(--acento); }

/* ── Avaliações ──────────────────────────────────────────── */
:deep(.ts-estrela--on) { color: var(--acento) !important; }
:deep(.ts-estrela--off) { color: var(--linha) !important; }
:deep(.ts-barra) { background: var(--acento) !important; }
:deep(.ts-review) { background: var(--painel) !important; border: 1px solid var(--linha) !important; }
:deep(.ts-review--minha) { border: 1px solid var(--acento) !important; }
:deep(.ts-btn) { display: inline-flex; padding: 12px 20px; border-radius: 12px; font-weight: 600; border: 1px solid var(--linha); }
:deep(.ts-btn--cor) { background: var(--cor) !important; border-color: var(--cor) !important; color: #fff !important; }

/* ── Rodapé ──────────────────────────────────────────────── */
.ts-footer { margin-top: 96px; padding: 36px 0; border-top: 1px solid var(--linha); }
.ts-footer__grid { display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; }
.ts-footer__nome { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -.02em; }
.ts-footer__meta { margin: 4px 0 0; font-size: 12px; color: var(--fg2); text-transform: uppercase; letter-spacing: .06em; }
.ts-footer__links { display: flex; gap: 4px; flex-wrap: wrap; }
.ts-footer__links button { padding: 8px 12px; border-radius: 8px; border: none; background: none; cursor: pointer; font: inherit; font-size: 14px; color: var(--fg2); }
.ts-footer__links button:hover { color: var(--fg); background: var(--painel); }
.ts-footer__copy { margin: 0; font-size: 12px; color: var(--fg2); }

/* ── Modal ───────────────────────────────────────────────── */
.ts-modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.55); }
.ts-modal__painel { width: 100%; max-width: 560px; max-height: 80vh; overflow-y: auto; background: var(--painel); color: var(--fg); border: 1px solid var(--linha); border-radius: var(--raio); }
.ts-modal__painel header { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: var(--painel); border-bottom: 1px solid var(--linha); }
.ts-modal__painel h3 { margin: 0; font-size: 18px; font-weight: 600; }
.ts-modal__corpo { padding: 20px; font-size: 14px; line-height: 1.7; color: var(--fg2); white-space: pre-wrap; }

.ts-vazio { min-height: 100vh; display: flex; flex-direction: column; gap: 16px; align-items: center; justify-content: center; font-size: 24px; font-weight: 600; }

/* ── Responsivo ──────────────────────────────────────────── */
@media (max-width: 1100px) {
  .ts-bar__links { display: none; }
}

@media (max-width: 1024px) {
  .ts-hero__grid { grid-template-columns: minmax(0, 1fr); gap: 32px; }
  .ts-ecra { order: -1; max-width: 560px; }
  .ts-carrossel { grid-auto-columns: calc((100% - 2 * 16px) / 3); }
  .ts-grelha { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .ts-servico { grid-template-columns: minmax(0, 1fr); }
  .ts-servico__col + .ts-servico__col { border-left: none; border-top: 1px solid var(--linha); }
}

@media (max-width: 640px) {
  .ts-root { --bar-h: 60px; --bar-pad: 14px; --raio: 14px; }
  .ts-bar { padding-right: calc(var(--bar-pad) + var(--acoes-espaco) + 8px); }
  .ts-quad { width: 34px; height: 34px; }
  .ts-bar__marca img, .ts-bar__inicial { display: none; }
  .ts-bar__nome { font-size: 14px; }
  .ts-hero { padding: calc(var(--bar-h) + 20px) 0 48px; }
  .ts-ecra { padding: 12px; }
  .ts-hero__desc { font-size: 16px; }
  .ts-specs dd { font-size: 22px; }
  .ts-specs > div { padding: 12px 14px; }
  .ts-sec { padding-top: 60px; }
  .ts-carrossel { grid-auto-columns: 70%; gap: 12px; }
  .ts-grelha { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .ts-cartao__corpo { padding: 10px; }
  .ts-cartao__nome { font-size: 14px; }
  .ts-cartao__pe { flex-direction: column; align-items: flex-start; gap: 4px; }
  .ts-linha { grid-template-columns: 48px minmax(0, 1fr) auto; gap: 12px; padding: 10px 12px; }
  .ts-linha__img { width: 48px; height: 48px; }
  .ts-linha .ts-estado, .ts-linha__seta { display: none; }
  .ts-controlos { width: 100%; justify-content: space-between; }
}
</style>
