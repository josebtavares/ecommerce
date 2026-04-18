// config/lojaTemplates.js
// Registo central de todos os templates disponíveis

export const TEMPLATES = [
  // ── GENÉRICOS ─────────────────────────────────────────────
  {
    id: 'classico',
    nome: 'Clássico',
    descricao: 'Layout limpo e equilibrado. Funciona para qualquer tipo de loja.',
    preview: '🏪',
    categorias: ['todos'],
    component: () => import('@/views/loja/templates/TemplateClassico.vue'),
  },
  {
    id: 'minimalista',
    nome: 'Minimalista',
    descricao: 'Espaçado, tipografia grande, ideal para marcas premium.',
    preview: '◻️',
    categorias: ['todos'],
    component: () => import('@/views/loja/templates/TemplateMinimalista.vue'),
  },
  {
    id: 'vibrante',
    nome: 'Vibrante',
    descricao: 'Cores fortes, cards grandes, muito visual. Ideal para produtos de impulso.',
    preview: '🎨',
    categorias: ['todos'],
    component: () => import('@/views/loja/templates/TemplateVibrante.vue'),
  },

  // ── RESTAURANTE ───────────────────────────────────────────
  {
    id: 'restaurante_moderno',
    nome: 'Restaurante Moderno',
    descricao: 'Hero escuro com foto de fundo, menu por categorias em tabs.',
    preview: '🍽️',
    categorias: ['restaurante'],
    component: () => import('@/views/loja/templates/TemplateRestauranteModerno.vue'),
  },
  {
    id: 'restaurante_bistro',
    nome: 'Bistrô',
    descricao: 'Tom quente, grid de pratos com fotos grandes, atmosfera acolhedora.',
    preview: '🥂',
    categorias: ['restaurante'],
    component: () => import('@/views/loja/templates/TemplateRestauranteBistro.vue'),
  },

  // ── MODA ──────────────────────────────────────────────────
  {
    id: 'moda_editorial',
    nome: 'Editorial',
    descricao: 'Full-bleed hero, grid assimétrico, focado na imagem do produto.',
    preview: '👗',
    categorias: ['moda'],
    component: () => import('@/views/loja/templates/TemplateModaEditorial.vue'),
  },
  {
    id: 'moda_boutique',
    nome: 'Boutique',
    descricao: 'Elegante, fundo claro opcional, produtos em destaque individual.',
    preview: '🛍️',
    categorias: ['moda'],
    component: () => import('@/views/loja/templates/TemplateModaBoutique.vue'),
  },

  // ── ELECTRÓNICA ───────────────────────────────────────────
  {
    id: 'tech_store',
    nome: 'Tech Store',
    descricao: 'Dark mode, specs em destaque, grid denso estilo loja de electrónica.',
    preview: '💻',
    categorias: ['tecnologia', 'eletronicos'],
    component: () => import('@/views/loja/templates/TemplateTechStore.vue'),
  },
]

// Devolve template por id, com fallback para 'classico'
export function getTemplate (templateId) {
  return TEMPLATES.find(t => t.id === templateId) || TEMPLATES.find(t => t.id === 'classico')
}

// Templates recomendados para uma categoria de loja
export function getTemplatesSugeridos (categoriaLoja) {
  const cat = categoriaLoja?.toLowerCase() || ''
  return TEMPLATES.filter(t =>
    t.categorias.includes('todos') || t.categorias.some(c => cat.includes(c))
  )
}