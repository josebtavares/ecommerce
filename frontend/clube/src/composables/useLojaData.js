// composables/useLojaData.js
// Toda a lógica de fetch da loja — partilhada por todos os templates
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

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
  const selectedProduct    = ref(null)
  const sidebarAberta      = ref(false)
  const modalPolitica      = ref(null)

  // ── Computed ──────────────────────────────────────────────
  const temSidebar = computed(() =>
    (tiposExistentes.value.length + categoriasExistentes.value.length) >= 3
  )

  const temFooter = computed(() =>
    loja.value?.politica_devolucao ||
    loja.value?.termos_servico ||
    loja.value?.politica_privacidade ||
    metodosPagamento.value.length > 0
  )

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
      metodosPagamento.value = (data.results || data).filter(m => m.ativo)
    } catch (e) { console.error(e) }
  }

  async function fetchTiposExistentes (id) {
    try {
      const { data } = await api.get('/app/produto/', { params: { loja_id: id, limit: 200 } })
      const map = {}
      ;(data.results || data).forEach(p => {
        if (p.tipo && !map[p.tipo.id]) map[p.tipo.id] = p.tipo
      })
      tiposExistentes.value = Object.values(map)
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
    return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(val || 0)
  }

  function tipoIcon (tipo) {
    const icons = {
      prato: '🍽️', comida: '🍔', bebida: '🥤', sobremesa: '🍰',
      roupa: '👗', calcado: '👟', acessorio: '👜',
      eletronico: '📱', telemovel: '📱', tablet: '💻',
      fruta: '🍎', legume: '🥦', carne: '🥩',
      livro: '📚', manga: '📖', revista: '📰',
    }
    return icons[tipo?.toLowerCase()] || '📦'
  }

  function metodoPagamentoIcon (tipo) {
    const map = { cartao: '💳', dinheiro: '💵', mbway: '📱', paypal: '🅿️', stripe: '💳' }
    return map[tipo] || '💰'
  }

  function scrollToId (id) {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function onRatingUpdated ({ media }) {
    if (loja.value && media !== undefined) loja.value.rating_medio = media
  }

  function logOut () {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    router.push({ name: 'Login' })
  }

  onMounted(() => loadAll())

  return {
    // state
    loading, loja, opcoesEntrega, metodosPagamento,
    tiposExistentes, categoriasExistentes,
    selectedProduct, sidebarAberta, modalPolitica,
    // computed
    temSidebar, temFooter, cssVars, lojaId,
    // helpers
    backendUrl, formatPrice, tipoIcon, metodoPagamentoIcon,
    scrollToId, onRatingUpdated, logOut,
    // reload
    loadAll,
  }
}