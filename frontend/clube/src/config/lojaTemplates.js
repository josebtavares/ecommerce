// config/lojaTemplates.js
// Registo central de todos os templates disponíveis.
// IDs mantêm underscore para compatibilidade com a BD existente.
// Exporta getTemplate() (API antiga) + TEMPLATE_COMPONENTS (API nova).

export const TEMPLATES = [
  // ── GENÉRICOS ─────────────────────────────────────────────────────────────
  {
    id: 'classico',
    nome: 'Clássico',
    descricao: 'Layout versátil com sidebar flutuante. Para qualquer tipo de negócio.',
    preview: '🏪',
    categorias: ['todos'],
    tag: 'Versátil',
    primaryDefault:    '#dc2626',
    secundariaDefault: '#1c1c1e',
    darkDefault: true,
  },
  {
    id: 'minimalista',
    nome: 'Minimalista',
    descricao: 'Tipografia extrema, espaço máximo. A marca fala sozinha.',
    preview: '◻️',
    categorias: ['todos', 'moda'],
    tag: 'Luxury',
    primaryDefault:    '#a8a29e',
    secundariaDefault: '#1c1917',
    darkDefault: true,
  },
  {
    id: 'vibrante',
    nome: 'Vibrante',
    descricao: 'Formas geométricas, texto outline, marquee animado. Energia pura.',
    preview: '🎨',
    categorias: ['todos', 'moda'],
    tag: 'Bold',
    primaryDefault:    '#f43f5e',
    secundariaDefault: '#09090b',
    darkDefault: true,
  },

  // ── RESTAURANTE ───────────────────────────────────────────────────────────
  {
    id: 'restaurante_moderno',
    nome: 'Restaurante Moderno',
    descricao: 'Hero cinematográfico com parallax, sidebar de categorias.',
    preview: '🍽️',
    categorias: ['restaurante'],
    tag: 'Food',
    primaryDefault:    '#e11d48',
    secundariaDefault: '#0f0f0f',
    darkDefault: true,
  },
  {
    id: 'restaurante_bistro',
    nome: 'Restaurante Bistro',
    descricao: 'Tipografia serif italiana, tons quentes, ornamentos. Estilo Parisiense.',
    preview: '🥂',
    categorias: ['restaurante'],
    tag: 'Food',
    primaryDefault:    '#d97706',
    secundariaDefault: '#1a1410',
    darkDefault: false,
  },

  // ── MODA ──────────────────────────────────────────────────────────────────
  {
    id: 'moda_editorial',
    nome: 'Moda Editorial',
    descricao: 'Hero full-bleed, grid com números editoriais. Estética de revista.',
    preview: '👗',
    categorias: ['moda'],
    tag: 'Editorial',
    primaryDefault:    '#e4e4e7',
    secundariaDefault: '#09090b',
    darkDefault: true,
  },
  {
    id: 'moda_boutique',
    nome: 'Moda Boutique',
    descricao: 'Serif elegante com tons dourados. Para boutiques e marcas premium.',
    preview: '🛍️',
    categorias: ['moda'],
    tag: 'Fashion',
    primaryDefault:    '#b8860b',
    secundariaDefault: '#0a0805',
    darkDefault: true,
  },

  // ── TECNOLOGIA ────────────────────────────────────────────────────────────
  {
    id: 'tech_store',
    nome: 'Tech Store',
    descricao: 'Dashboard tech com grid overlay, HUD de estatísticas e neon cyan.',
    preview: '💻',
    categorias: ['tecnologia', 'eletronicos'],
    tag: 'Tech',
    primaryDefault:    '#06b6d4',
    secundariaDefault: '#020617',
    darkDefault: true,
  },

  // ── NOVOS ─────────────────────────────────────────────────────────────────
  {
    id: 'natureza',
    nome: 'Natureza',
    descricao: 'Visual orgânico, tons verdes e terrosos. Para produtos naturais e bio.',
    preview: '🌿',
    categorias: ['todos', 'natureza'],
    tag: 'Nature',
    primaryDefault:    '#16a34a',
    secundariaDefault: '#051a0a',
    darkDefault: true,
  },
  {
    id: 'luxo_premium',
    nome: 'Luxo Premium',
    descricao: 'Ultra-minimalista, ouro e preto absoluto. Para jóias e marcas de prestígio.',
    preview: '✦',
    categorias: ['moda', 'luxo'],
    tag: 'Premium',
    primaryDefault:    '#c9a84c',
    secundariaDefault: '#030303',
    darkDefault: true,
  },
  {
    id: 'desporto',
    nome: 'Desporto',
    descricao: 'Diagonal, alta energia, marquee. Para equipamento desportivo e fitness.',
    preview: '⚡',
    categorias: ['desporto', 'todos'],
    tag: 'Sport',
    primaryDefault:    '#f97316',
    secundariaDefault: '#0a0a0a',
    darkDefault: true,
  },
]

// ── Mapa id → lazy loader ──────────────────────────────────────────────────
// Usado em LojaPublica.vue para carregar o componente certo dinamicamente.
export const TEMPLATE_COMPONENTS = {
  'classico':            () => import('@/views/loja/templates/TemplateClassico.vue'),
  'minimalista':         () => import('@/views/loja/templates/TemplateMinimalista.vue'),
  'vibrante':            () => import('@/views/loja/templates/TemplateVibrante.vue'),
  'restaurante_moderno': () => import('@/views/loja/templates/TemplateRestauranteModerno.vue'),
  'restaurante_bistro':  () => import('@/views/loja/templates/TemplateRestauranteBistro.vue'),
  'moda_editorial':      () => import('@/views/loja/templates/TemplateModaEditorial.vue'),
  'moda_boutique':       () => import('@/views/loja/templates/TemplateModaBoutique.vue'),
  'tech_store':          () => import('@/views/loja/templates/TemplateTechStore.vue'),
  'natureza':            () => import('@/views/loja/templates/TemplateNatureza.vue'),
  'luxo_premium':        () => import('@/views/loja/templates/TemplateLuxoPremium.vue'),
  'desporto':            () => import('@/views/loja/templates/TemplateDesporto.vue'),
}

// ── API de compatibilidade (usado em código legado) ────────────────────────

/** Devolve o objecto de template por id, com fallback para 'classico'. */
export function getTemplate (templateId) {
  const tpl = TEMPLATES.find(t => t.id === templateId)
  if (!tpl) return TEMPLATES.find(t => t.id === 'classico')
  // Expõe .component() para compatibilidade com o padrão antigo
  return {
    ...tpl,
    component: TEMPLATE_COMPONENTS[tpl.id] ?? TEMPLATE_COMPONENTS['classico'],
  }
}

/** Templates recomendados para uma categoria de loja. */
export function getTemplatesSugeridos (categoriaLoja) {
  const cat = categoriaLoja?.toLowerCase() || ''
  return TEMPLATES.filter(t =>
    t.categorias.includes('todos') || t.categorias.some(c => cat.includes(c))
  )
}

// Filtros para o BackofficeTemplates
export const CATEGORIAS_FILTRO = [
  { value: 'todos',       label: 'Genérico'    },
  { value: 'moda',        label: 'Moda'        },
  { value: 'luxo',        label: 'Luxo'        },
  { value: 'restaurante', label: 'Restauração' },
  { value: 'tecnologia',  label: 'Tecnologia'  },
  { value: 'desporto',    label: 'Desporto'    },
  { value: 'natureza',    label: 'Natureza'    },
]
