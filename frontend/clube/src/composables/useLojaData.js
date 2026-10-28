import { formatarDinheiro } from '@/utils/dinheiro'
// composables/useLojaData.js
// Toda a lógica de fetch da loja — partilhada por todos os templates
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { terminarSessao } from '@/services/api'
import { iconeTipoProduto, iconePagamento } from '@/utils/icones'
import { DEFAULT_BANNER } from '@/services/media'

const NOMES_PAGAMENTO = {
  cartao: 'Cartão', dinheiro: 'Dinheiro', mbway: 'MB WAY', paypal: 'PayPal', stripe: 'Stripe',
  flutterwave: 'Flutterwave', transferencia: 'Transferência',
}

export function useLojaData () {
  const route  = useRoute()
  const router = useRouter()

  // ── Estado ────────────────────────────────────────────────
  const loading            = ref(true)
  const loja               = ref(null)
  const opcoesEntrega      = ref([])
  const metodosPagamento   = ref([])
  const tiposExistentes    = ref([])
  const categoriasExistentes = ref([])  // CategoriaLoja objects
  const totalProdutos      = ref(null)  // produtos activos da loja
  const totalDestaques     = ref(0)     // produtos activos em destaque
  const selectedProduct    = ref(null)
  const sidebarAberta      = ref(false)
  const modalPolitica      = ref(null)

  // ── Computed ──────────────────────────────────────────────
  const temSidebar = computed(() =>
    (tiposExistentes.value.length + categoriasExistentes.value.length) >= 3
  )

  // loja só de serviços: sem produtos activos e a aceitar marcações — os templates escondem o catálogo
  // de produtos (vazio) e os atalhos para ele apontam para os serviços
  const soServicos = computed(() => totalProdutos.value === 0 && !!loja.value?.tem_servicos)
  const totalServicos = computed(() => loja.value?.total_servicos || 0)

  // o rodapé da loja leva sempre o "Vendido por" (LojaRodapeInfo)
  const temFooter = computed(() => !!loja.value)

  // Secções "Por tipo" e "Por categoria" — só metadados e contagens; cada template pede
  // os produtos de cada grupo página a página (components/produtos/ProdutosPaginados.vue).
  // Sem tipos nem categorias, um único grupo com todos os produtos.
  const gruposProdutos = computed(() => {
    const id = lojaId.value
    const lista = [
      ...tiposExistentes.value
        .filter(t => t.total_produtos > 0)
        .map(t => ({ key: 't' + t.id, seccao: 'tipo', nome: t.nome, total: t.total_produtos, params: { loja_id: id, tipo_id: t.id } })),
      ...categoriasExistentes.value
        .filter(c => c.total_produtos > 0)
        .map(c => ({ key: 'c' + c.id, seccao: 'categoria', nome: c.nome, total: c.total_produtos, params: { loja_id: id, categoria_id: c.id } })),
    ]
    if (!lista.length && totalProdutos.value) {
      lista.push({ key: 'todos', seccao: 'todos', nome: 'Todos os produtos', total: totalProdutos.value, params: { loja_id: id } })
    }
    return lista
  })

  // CSS variables dinâmicas baseadas nas cores da loja
  const cssVars = computed(() => {
    if (!loja.value) return {}
    return {
      '--cor-primaria':    loja.value.cor_primaria   || '#dc2626',
      '--cor-secundaria':  loja.value.cor_secundaria || '#1c1c1e',
    }
  })

  // ── Fetch ──────────────────────────────────────────────────
  const lojaId = computed(() => route.params.id)

  async function fetchLoja (id) {
    try {
      const { data } = await api.get(`/app/loja/${id}/`)
      loja.value = data
    } catch (e) { console.error(e) }
  }

  async function fetchOpcoesEntrega (id) {
    try {
      const { data } = await api.get(`/app/loja/${id}/entrega/opcoes/`)
      opcoesEntrega.value = data.results || data
    } catch (e) { console.error(e) }
  }

  async function fetchMetodosPagamento (id) {
    try {
      const { data } = await api.get(`/app/loja/${id}/pagamento/metodos/`)
      // nome para mostrar ("Cartão", "Transferência"…); o tipo fica para os ícones
      metodosPagamento.value = (data.results || data).filter(m => m.ativo).map(m => ({ ...m, nome: NOMES_PAGAMENTO[m.tipo] || m.tipo }))
    } catch (e) { console.error(e) }
  }

  async function fetchTiposExistentes (id) {
    try {
      // só tipos + contagens — não descarrega produtos
      const { data } = await api.get(`/app/loja/${id}/produtos/tipos/`)
      tiposExistentes.value = data.tipos || []
      totalProdutos.value = data.total ?? null
      totalDestaques.value = data.destaques || 0
    } catch (e) { console.error(e) }
  }

  async function fetchCategoriasExistentes (id) {
    try {
      const { data } = await api.get(`/app/loja/${id}/categorias/`)
      categoriasExistentes.value = data
    } catch (e) { console.error(e) }
  }

  async function loadAll () {
    loading.value = true
    const id = lojaId.value
    await Promise.all([
      fetchLoja(id),
      fetchOpcoesEntrega(id),
      fetchMetodosPagamento(id),
      fetchTiposExistentes(id),
      fetchCategoriasExistentes(id),
    ])
    loading.value = false
  }

  // ── Helpers ────────────────────────────────────────────────
  const backendUrl = process.env.VUE_APP_URL_BASE || 'http://localhost:8000'

  function formatPrice (val) {
    return formatarDinheiro(val || 0)
  }

  const tipoIcon = iconeTipoProduto

  const metodoPagamentoIcon = iconePagamento

  function scrollToId (id) {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function onRatingUpdated ({ media }) {
    if (loja.value && media !== undefined) loja.value.rating_medio = media
  }

  function logOut () {
    terminarSessao('access_token', 'refresh_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    router.push({ name: 'Login' })
  }

  // /loja/<id>?produto=<id> abre logo o produto (vindo dos favoritos do perfil)
  async function abrirProdutoDoLink () {
    const pid = route.query.produto
    if (!/^\d+$/.test(String(pid ?? ''))) return
    const resto = { ...route.query }
    delete resto.produto
    router.replace({ query: resto })
    try {
      const { data } = await api.get(`/app/produto/${pid}/`)
      if (String(data.loja?.id) === String(lojaId.value)) selectedProduct.value = data
    } catch { /* produto indisponível — fica a página da loja */ }
  }

  watch(() => route.query.produto, abrirProdutoDoLink)

  onMounted(() => { loadAll(); abrirProdutoDoLink() })

  return {
    // state
    loading, loja, opcoesEntrega, metodosPagamento,
    tiposExistentes, categoriasExistentes, totalProdutos, totalDestaques,
    selectedProduct, sidebarAberta, modalPolitica,
    // computed
    temSidebar, temFooter, soServicos, totalServicos, cssVars, lojaId, gruposProdutos,
    // helpers
    backendUrl, defaultBanner: DEFAULT_BANNER, formatPrice, tipoIcon, metodoPagamentoIcon,
    scrollToId, onRatingUpdated, logOut,
    // reload
    loadAll,
  }
}