// config/lojaTemplates.js
// Registo central de todos os templates disponíveis.
// IDs mantêm underscore para compatibilidade com a BD existente.
// Exporta getTemplate() (API antiga) + TEMPLATE_COMPONENTS (API nova).

export const TEMPLATES = [
  // ── GENÉRICOS ─────────────────────────────────────────────────────────────
  {
    id: 'classico',
    usaCorSecundaria: true,   // fundo do modo escuro
    nome: 'Clássico',
    descricao: 'Layout versátil com sidebar flutuante. Para qualquer tipo de negócio.',
    categorias: ['todos'],
    tag: 'Versátil',
    primaryDefault:    '#dc2626',
    secundariaDefault: '#1c1c1e',
    darkDefault: true,
  },
  {
    id: 'minimalista',
    nome: 'Minimalista',
    usaCorSecundaria: true,   // fundo do modo escuro
    descricao: 'Galeria: muito espaço, tipografia leve, peças com legenda. Sem ruído visual.',
    categorias: ['todos', 'moda'],
    tag: 'Luxury',
    primaryDefault:    '#a0522d',
    secundariaDefault: '#121212',
    darkDefault: false,
  },
  {
    id: 'vibrante',
    usaCorSecundaria: true,   // fundo do modo escuro
    nome: 'Vibrante',
    descricao: 'Pop: blocos de cor arredondados, tipografia expressiva, cartões coloridos. Energia sem ruído.',
    categorias: ['todos', 'moda'],
    tag: 'Bold',
    primaryDefault:    '#ff4d2e',
    secundariaDefault: '#111014',
    darkDefault: false,
  },

  // ── RESTAURANTE ───────────────────────────────────────────────────────────
  {
    id: 'restaurante_moderno',
    usaCorSecundaria: true,   // fundo do modo escuro
    nome: 'Restaurante Moderno',
    descricao: 'Hero com cartão de serviço, sugestões do chef em bento e carta com índice e pesquisa.',
    categorias: ['restaurante'],
    tag: 'Food',
    primaryDefault:    '#e4572e',
    secundariaDefault: '#14110f',
    darkDefault: true,
  },
  {
    id: 'restaurante_bistro',
    nome: 'Restaurante Bistro',
    usaCorSecundaria: true,   // ardósia e fundo do modo escuro
    descricao: 'Carta de bistrô: capa emoldurada, ardósia com sugestões do chef, pratos com linhas pontilhadas.',
    categorias: ['restaurante'],
    tag: 'Food',
    primaryDefault:    '#8c2f2b',
    secundariaDefault: '#1e2a24',
    darkDefault: false,
  },

  // ── MODA ──────────────────────────────────────────────────────────────────
  {
    id: 'moda_editorial',
    usaCorSecundaria: true,   // fundo do modo escuro
    nome: 'Moda Editorial',
    descricao: 'Hero full-bleed, grid com números editoriais. Estética de revista.',
    categorias: ['moda'],
    tag: 'Editorial',
    primaryDefault:    '#e4e4e7',
    secundariaDefault: '#09090b',
    darkDefault: true,
  },
  {
    id: 'moda_boutique',
    nome: 'Moda Boutique',
    usaCorSecundaria: true,   // faixa, rodapé e fundo do modo escuro
    descricao: 'Boutique de ateliê: montra, etiquetas penduradas, provador por tipo e categoria.',
    categorias: ['moda'],
    tag: 'Fashion',
    primaryDefault:    '#b4637a',
    secundariaDefault: '#1f1a1d',
    darkDefault: false,
  },

  // ── TECNOLOGIA ────────────────────────────────────────────────────────────
  {
    id: 'tech_store',
    nome: 'Tech Store',
    usaCorSecundaria: true,   // fundo do modo escuro
    descricao: 'Ficha técnica: specs em tabela, cartões com especificações, vista em grelha ou lista.',
    categorias: ['tecnologia', 'eletronicos'],
    tag: 'Tech',
    primaryDefault:    '#3d7bff',
    secundariaDefault: '#0b0f17',
    darkDefault: true,
  },

  // ── NOVOS ─────────────────────────────────────────────────────────────────
  {
    id: 'natureza',
    nome: 'Natureza',
    usaCorSecundaria: true,   // fundo do modo escuro
    descricao: 'Mercado da horta: formas orgânicas, bancas com etiquetas kraft, selo da época.',
    categorias: ['todos', 'natureza'],
    tag: 'Nature',
    primaryDefault:    '#4f7d3a',
    secundariaDefault: '#1b261d',
    darkDefault: false,
  },
  {
    id: 'luxo_premium',
    nome: 'Luxo Premium',
    usaCorSecundaria: true,   // fundo do modo escuro
    descricao: 'Maison: hero com moldura e monograma, vitrine de uma peça sob foco de luz, coleções.',
    categorias: ['moda', 'luxo'],
    tag: 'Premium',
    primaryDefault:    '#b8975a',
    secundariaDefault: '#0e0d0c',
    darkDefault: true,
  },
  {
    id: 'desporto',
    nome: 'Desporto',
    usaCorSecundaria: true,   // fundo do modo escuro
    descricao: 'Pista: itálico expandido, placar, top com números de camisola, modalidades em pistas.',
    categorias: ['desporto', 'todos'],
    tag: 'Sport',
    primaryDefault:    '#c6f432',
    secundariaDefault: '#101114',
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
