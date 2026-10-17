// utils/demoLoja.js
// Loja de demonstração para o preview de templates no "Criar loja" (a loja ainda não existe).
// Abre-se em /loja/demo?preview=1&tpl=…&cat=…&nome=… e mostra o template verdadeiro com
// dados fictícios: um adapter do axios responde às chamadas à API sem tocar no backend.
//
// Query aceite: tpl, c1, c2, dark (tratados em views/loja/lojaPublica.vue) e
//   nome, desc, loc, cat (categoria da loja), logo, banner (blob URLs do formulário).
import { fas } from '@fortawesome/free-solid-svg-icons'
import api from '@/services/api'
import { chaveCategoria, chaveCategoriaProduto } from '@/utils/icones'

export const DEMO_ID = 'demo'

// ── Dados por tipo de negócio ──────────────────────────────────────────────
// produto: [nome, preço, tipo, categoria, ícone FA, destaque, descrição]
const CONJUNTOS = {
  comida: {
    descricao: 'Cozinha caseira com ingredientes frescos, feita na hora e entregue quente.',
    tipos: ['prato', 'bebida', 'sobremesa'],
    categorias: ['pratos do dia', 'grelhados', 'bebidas', 'doces'],
    produtos: [
      ['Bitoque da casa', 9.5, 'prato', 'pratos do dia', 'utensils', true, 'Bife do lombo, ovo estrelado, batata frita e salada.'],
      ['Cachupa rica', 8.9, 'prato', 'pratos do dia', 'bowl-food', true, 'Milho, feijão, carnes e legumes, cozinhados lentamente.'],
      ['Frango grelhado', 7.5, 'prato', 'grelhados', 'drumstick-bite', false, 'Meio frango no carvão com arroz e salada.'],
      ['Hambúrguer artesanal', 8.0, 'prato', 'grelhados', 'burger', true, 'Pão brioche, carne 180 g, queijo cheddar e cebola caramelizada.'],
      ['Pizza margherita', 9.0, 'prato', 'pratos do dia', 'pizza-slice', false, 'Molho de tomate, mozzarella fresca e manjericão.'],
      ['Peixe do dia', 11.5, 'prato', 'grelhados', 'fish', false, 'Grelhado com batata cozida e legumes salteados.'],
      ['Sumo natural', 2.5, 'bebida', 'bebidas', 'glass-water', false, 'Laranja, manga ou maracujá, espremido no momento.'],
      ['Café expresso', 1.0, 'bebida', 'bebidas', 'mug-hot', false, 'Lote da casa, torra média.'],
      ['Mousse de chocolate', 3.5, 'sobremesa', 'doces', 'ice-cream', true, 'Chocolate negro 70% e flor de sal.'],
      ['Bolo de bolacha', 3.0, 'sobremesa', 'doces', 'cake-candles', false, 'Receita da avó, servido fresco.'],
    ],
  },
  moda: {
    descricao: 'Peças intemporais e acessórios escolhidos a dedo para todos os dias.',
    tipos: ['roupa', 'calcado', 'acessorio'],
    categorias: ['mulher', 'homem', 'novidades', 'acessórios'],
    produtos: [
      ['Vestido de linho', 49.9, 'roupa', 'mulher', 'person-dress', true, 'Linho lavado, corte midi, ideal para dias quentes.'],
      ['Camisa oxford', 34.9, 'roupa', 'homem', 'shirt', true, 'Algodão oxford com gola abotoada.'],
      ['Casaco de ganga', 59.0, 'roupa', 'novidades', 'vest', false, 'Ganga resistente com acabamento vintage.'],
      ['T-shirt essencial', 14.9, 'roupa', 'homem', 'shirt', false, '100% algodão orgânico, várias cores.'],
      ['Ténis urbanos', 69.9, 'calcado', 'novidades', 'shoe-prints', true, 'Sola leve e confortável para o dia a dia.'],
      ['Sandálias de couro', 44.0, 'calcado', 'mulher', 'shoe-prints', false, 'Couro natural feito à mão.'],
      ['Mala tote', 39.9, 'acessorio', 'acessórios', 'bag-shopping', true, 'Espaçosa, em lona e pele.'],
      ['Óculos de sol', 29.9, 'acessorio', 'acessórios', 'glasses', false, 'Proteção UV400 e armação leve.'],
      ['Chapéu de palha', 19.9, 'acessorio', 'acessórios', 'hat-cowboy', false, 'Aba larga para os dias de praia.'],
      ['Relógio clássico', 89.0, 'acessorio', 'novidades', 'clock', false, 'Mostrador minimalista e bracelete em pele.'],
    ],
  },
  tech: {
    descricao: 'Tecnologia com garantia, aconselhamento honesto e assistência local.',
    tipos: ['telemovel', 'eletronico', 'acessorio'],
    categorias: ['smartphones', 'computadores', 'áudio', 'gaming'],
    produtos: [
      ['Smartphone Pro 128 GB', 649.0, 'telemovel', 'smartphones', 'mobile-screen', true, 'Ecrã OLED 6,1", câmara tripla e 5G.'],
      ['Smartphone Lite 64 GB', 229.0, 'telemovel', 'smartphones', 'mobile-screen-button', false, 'Bateria para dois dias e carregamento rápido.'],
      ['Portátil 14" Ultra', 899.0, 'eletronico', 'computadores', 'laptop', true, '16 GB RAM, SSD 512 GB, apenas 1,2 kg.'],
      ['Monitor 27" QHD', 279.0, 'eletronico', 'computadores', 'desktop', false, 'Painel IPS 75 Hz com cores calibradas.'],
      ['Auscultadores sem fios', 129.0, 'acessorio', 'áudio', 'headphones', true, 'Cancelamento de ruído e 30 h de bateria.'],
      ['Coluna Bluetooth', 59.0, 'acessorio', 'áudio', 'volume-high', false, 'Resistente à água, som 360°.'],
      ['Comando sem fios', 64.9, 'acessorio', 'gaming', 'gamepad', true, 'Compatível com PC e consolas.'],
      ['Teclado mecânico', 89.9, 'acessorio', 'gaming', 'keyboard', false, 'Switches táteis e retroiluminação RGB.'],
      ['Smartwatch', 149.0, 'eletronico', 'smartphones', 'clock', false, 'GPS, ritmo cardíaco e notificações.'],
      ['Carregador 65 W', 34.9, 'acessorio', 'smartphones', 'plug', false, 'USB-C, carrega portátil e telemóvel.'],
    ],
  },
  mercado: {
    descricao: 'Mercearia de bairro com frescos todos os dias e entrega à porta.',
    tipos: ['fruta', 'legume', 'mercearia'],
    categorias: ['frescos', 'padaria', 'bebidas', 'despensa'],
    produtos: [
      ['Banana da Madeira (kg)', 1.99, 'fruta', 'frescos', 'lemon', true, 'Pequena, doce e aromática.'],
      ['Maçã gala (kg)', 1.79, 'fruta', 'frescos', 'apple-whole', false, 'Estaladiça e sumarenta.'],
      ['Cenoura (kg)', 0.99, 'legume', 'frescos', 'carrot', false, 'Produção nacional.'],
      ['Cabaz de legumes', 12.5, 'legume', 'frescos', 'basket-shopping', true, 'Seleção semanal da época.'],
      ['Pão caseiro', 1.6, 'mercearia', 'padaria', 'bread-slice', true, 'Fermentação lenta, cozido em forno de lenha.'],
      ['Queijo fresco', 2.3, 'mercearia', 'despensa', 'cheese', false, 'Da ilha, feito diariamente.'],
      ['Ovos do campo (12)', 3.2, 'mercearia', 'despensa', 'egg', false, 'Galinhas criadas ao ar livre.'],
      ['Água mineral 6×1,5 L', 2.99, 'mercearia', 'bebidas', 'bottle-water', false, 'Pack económico.'],
      ['Café moído 250 g', 3.49, 'mercearia', 'despensa', 'mug-hot', false, 'Torra tradicional.'],
      ['Sumo de laranja 1 L', 1.89, 'mercearia', 'bebidas', 'glass-water', true, '100% sumo, sem açúcar adicionado.'],
    ],
  },
  beleza: {
    descricao: 'Cosmética cuidada, rituais de bem-estar e aconselhamento personalizado.',
    tipos: ['rosto', 'corpo', 'perfume'],
    categorias: ['cuidado do rosto', 'corpo', 'perfumes', 'kits'],
    produtos: [
      ['Sérum vitamina C', 24.9, 'rosto', 'cuidado do rosto', 'droplet', true, 'Ilumina e uniformiza o tom da pele.'],
      ['Creme hidratante', 18.5, 'rosto', 'cuidado do rosto', 'pump-soap', false, 'Ácido hialurónico, textura leve.'],
      ['Máscara de argila', 12.9, 'rosto', 'cuidado do rosto', 'spa', false, 'Purifica e reduz o brilho.'],
      ['Óleo corporal', 21.0, 'corpo', 'corpo', 'bottle-droplet', true, 'Óleos de argão e amêndoa doce.'],
      ['Esfoliante de café', 14.5, 'corpo', 'corpo', 'mug-hot', false, 'Ativa a circulação e suaviza.'],
      ['Eau de parfum 50 ml', 54.0, 'perfume', 'perfumes', 'spray-can-sparkles', true, 'Notas de flor de laranjeira e baunilha.'],
      ['Batom mate', 11.9, 'rosto', 'cuidado do rosto', 'wand-magic-sparkles', false, 'Longa duração, sem secar os lábios.'],
      ['Kit ritual relax', 39.0, 'corpo', 'kits', 'gift', true, 'Óleo, vela aromática e sais de banho.'],
      ['Vela aromática', 16.0, 'corpo', 'kits', 'fire', false, 'Cera de soja, 40 h de queima.'],
      ['Escova de bambu', 6.5, 'corpo', 'corpo', 'leaf', false, 'Cerdas suaves e cabo sustentável.'],
    ],
  },
  desporto: {
    descricao: 'Equipamento para treinar mais e melhor, do ginásio à montanha.',
    tipos: ['equipamento', 'roupa', 'calcado'],
    categorias: ['treino', 'corrida', 'futebol', 'outdoor'],
    produtos: [
      ['Bola de futebol pro', 34.9, 'equipamento', 'futebol', 'futbol', true, 'Tamanho 5, costura térmica.'],
      ['Sapatilhas de corrida', 89.9, 'calcado', 'corrida', 'person-running', true, 'Amortecimento reativo e malha respirável.'],
      ['Halteres 2×5 kg', 39.0, 'equipamento', 'treino', 'dumbbell', false, 'Revestimento antiderrapante.'],
      ['Tapete de yoga', 24.9, 'equipamento', 'treino', 'person-walking', false, '6 mm, com alça de transporte.'],
      ['Camisola técnica', 22.0, 'roupa', 'corrida', 'shirt', false, 'Tecido leve que seca rápido.'],
      ['Garrafa térmica 750 ml', 18.9, 'equipamento', 'outdoor', 'bottle-water', false, 'Mantém frio 24 h.'],
      ['Mochila de trilho 20 L', 49.9, 'equipamento', 'outdoor', 'mountain-sun', true, 'Leve, com sistema de hidratação.'],
      ['Bicicleta de estrada', 699.0, 'equipamento', 'outdoor', 'person-biking', true, 'Quadro em alumínio, 18 velocidades.'],
      ['Corda de saltar', 9.9, 'equipamento', 'treino', 'stopwatch', false, 'Rolamentos e cabo ajustável.'],
      ['Caneleiras', 14.9, 'equipamento', 'futebol', 'shield-halved', false, 'Proteção leve e anatómica.'],
    ],
  },
  casa: {
    descricao: 'Peças para tornar a casa mais bonita, prática e acolhedora.',
    tipos: ['decoracao', 'cozinha', 'jardim'],
    categorias: ['sala', 'cozinha', 'jardim', 'iluminação'],
    produtos: [
      ['Candeeiro de mesa', 45.0, 'decoracao', 'iluminação', 'lightbulb', true, 'Base em madeira e luz quente regulável.'],
      ['Almofada de linho', 19.9, 'decoracao', 'sala', 'couch', false, 'Capa removível, 45×45 cm.'],
      ['Manta de algodão', 34.0, 'decoracao', 'sala', 'rug', true, 'Tecida à mão, toque macio.'],
      ['Conjunto de canecas', 24.0, 'cozinha', 'cozinha', 'mug-saucer', false, 'Cerâmica artesanal, 4 unidades.'],
      ['Tábua de corte', 22.5, 'cozinha', 'cozinha', 'utensils', false, 'Madeira de oliveira.'],
      ['Panela de ferro', 79.0, 'cozinha', 'cozinha', 'kitchen-set', true, 'Distribui o calor por igual.'],
      ['Vaso de cerâmica', 16.9, 'jardim', 'jardim', 'seedling', false, 'Com furo de drenagem.'],
      ['Planta monstera', 29.0, 'jardim', 'jardim', 'leaf', true, 'Fácil de cuidar, ideal para interior.'],
      ['Regador de latão', 27.0, 'jardim', 'jardim', 'droplet', false, 'Capacidade de 1,5 L.'],
      ['Grinalda de luzes', 14.9, 'decoracao', 'iluminação', 'star', false, '5 m de luz LED quente.'],
    ],
  },
}

// Loja genérica: um pouco de tudo
CONJUNTOS.geral = {
  descricao: 'Uma seleção de produtos de qualidade, com entrega rápida e apoio próximo.',
  tipos: ['geral', 'presente', 'acessorio'],
  categorias: ['novidades', 'mais vendidos', 'presentes'],
  produtos: [
    ['Caderno artesanal', 9.9, 'geral', 'novidades', 'book', true, 'Capa em pele e papel reciclado.'],
    ['Caneca personalizada', 12.0, 'presente', 'presentes', 'mug-hot', false, 'Cerâmica com o teu nome.'],
    ['Cabaz gourmet', 39.0, 'presente', 'presentes', 'gift', true, 'Doces, compotas e um vinho da ilha.'],
    ['Auscultadores', 49.0, 'acessorio', 'mais vendidos', 'headphones', true, 'Som limpo e confortáveis.'],
    ['Mochila urbana', 44.9, 'acessorio', 'mais vendidos', 'bag-shopping', false, 'Compartimento para portátil.'],
    ['Vela aromática', 16.0, 'presente', 'presentes', 'fire', false, 'Cera de soja, 40 h de queima.'],
    ['Puzzle 1000 peças', 19.9, 'geral', 'novidades', 'puzzle-piece', false, 'Paisagens de Cabo Verde.'],
    ['Garrafa térmica', 18.9, 'acessorio', 'mais vendidos', 'bottle-water', false, 'Mantém frio 24 h.'],
    ['Planta de interior', 22.0, 'geral', 'novidades', 'seedling', true, 'Vaso de cerâmica incluído.'],
    ['Conjunto de lápis', 7.5, 'geral', 'mais vendidos', 'palette', false, '24 cores, para todas as idades.'],
  ],
}

// chave da categoria da plataforma (utils/icones.js) → conjunto de dados
const POR_CATEGORIA = {
  comida: 'comida', cafe: 'comida', bebidas: 'comida',
  roupa: 'moda', joias: 'moda',
  tech: 'tech', auto: 'tech', servicos: 'tech', musica: 'tech',
  mercado: 'mercado',
  beleza: 'beleza', saude: 'beleza',
  desporto: 'desporto',
  casa: 'casa', jardim: 'casa', animais: 'casa', bebe: 'casa', brinquedo: 'casa',
}

const PALETAS = [
  ['#f97316', '#be123c'], ['#0ea5e9', '#4338ca'], ['#10b981', '#0f766e'], ['#a855f7', '#6d28d9'],
  ['#f59e0b', '#c2410c'], ['#ec4899', '#9d174d'], ['#14b8a6', '#155e75'], ['#64748b', '#1e293b'],
  ['#84cc16', '#3f6212'], ['#ef4444', '#7f1d1d'],
]

const AVALIACOES = [
  ['marta.s', 5, 'Tudo impecável, chegou antes do previsto. Recomendo!'],
  ['joao_p', 5, 'Ótimo atendimento e qualidade acima do esperado.'],
  ['ana.lopes', 4, 'Gostei muito, voltarei a comprar.'],
]

// ── Imagens geradas (SVG): gradiente + ícone, sem pedidos externos ─────────
const ICONES_FA = Object.fromEntries(Object.values(fas).map(i => [i.iconName, i.icon]))

function iconeSvg (nome, cx, cy, tamanho, opacidade) {
  const def = ICONES_FA[nome] || ICONES_FA.box
  const [w, h, , , path] = def
  const d = Array.isArray(path) ? path.join(' ') : path
  const s = tamanho / Math.max(w, h)
  return `<g transform='translate(${cx - (w * s) / 2} ${cy - (h * s) / 2}) scale(${s})' fill='#fff' fill-opacity='${opacidade}'><path d='${d}'/></g>`
}

function svgUrl (svg) {
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg)
}

function imagemProduto (icone, [c1, c2]) {
  return svgUrl(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 600'>` +
    `<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='${c1}'/><stop offset='1' stop-color='${c2}'/></linearGradient></defs>` +
    `<rect width='600' height='600' fill='url(#g)'/>` +
    `<circle cx='490' cy='110' r='170' fill='#fff' fill-opacity='.08'/><circle cx='80' cy='530' r='130' fill='#fff' fill-opacity='.06'/>` +
    iconeSvg(icone, 300, 300, 230, 0.92) +
    `</svg>`
  )
}

function escurecer (hex, f = 0.45) {
  const n = parseInt(String(hex).replace('#', ''), 16)
  if (Number.isNaN(n)) return '#111111'
  const c = [16, 8, 0].map(sh => Math.round(((n >> sh) & 255) * f))
  return '#' + c.map(v => v.toString(16).padStart(2, '0')).join('')
}

function imagemBanner (cor, icones) {
  const c2 = escurecer(cor)
  // ícones espalhados pela largura: os templates recortam o banner de formas diferentes (faixa larga ou caixa)
  const decor = [...new Set(icones)].slice(0, 6).map((ic, i) =>
    iconeSvg(ic, 260 + i * 220, i % 2 ? 380 : 220, 120, 0.13)).join('')
  return svgUrl(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 600' preserveAspectRatio='xMidYMid slice'>` +
    `<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='${cor}'/><stop offset='1' stop-color='${c2}'/></linearGradient></defs>` +
    `<rect width='1600' height='600' fill='url(#g)'/>` +
    `<circle cx='1350' cy='80' r='320' fill='#fff' fill-opacity='.07'/><circle cx='180' cy='620' r='260' fill='#000' fill-opacity='.12'/>` +
    decor + `</svg>`
  )
}

// ── Construção da loja a partir da query ───────────────────────────────────
function lerQuery () {
  const q = new URLSearchParams(window.location.search)
  const cor = v => (/^[0-9a-f]{6}$/i.test(v || '') ? '#' + v : null)
  return {
    nome:   (q.get('nome') || '').trim() || 'A tua loja',
    desc:   (q.get('desc') || '').trim(),
    loc:    (q.get('loc') || '').trim() || 'Praia, Cabo Verde',
    cat:    (q.get('cat') || '').trim(),
    logo:   q.get('logo') || null,
    banner: q.get('banner') || null,
    tpl:    q.get('tpl') || 'classico',
    c1:     cor(q.get('c1')) || '#dc2626',
    c2:     cor(q.get('c2')) || '#1c1c1e',
    dark:   q.get('dark') !== '0',
  }
}

let cache = { chave: null, loja: null }

function construir () {
  const q = lerQuery()
  const chave = JSON.stringify(q)
  if (cache.chave === chave) return cache.loja

  const conjuntoId = POR_CATEGORIA[chaveCategoria(null, q.cat)] || 'geral'
  const dados = CONJUNTOS[conjuntoId]

  const tipos = dados.tipos.map((nome, i) => ({
    id: i + 1, nome, descricao: '', atributos_schema: [], is_global: true, ativo: true,
  }))
  const categorias = dados.categorias.map((nome, i) => ({
    id: i + 1, nome, icone: chaveCategoriaProduto('', nome), ativo: true, ordem: i,
  }))

  const loja = {
    id: DEMO_ID,
    nome: q.nome,
    descricao: q.desc || dados.descricao,
    categoria: q.cat || 'Loja',
    localizacao: q.loc,
    logo_url: q.logo,
    banner_url: q.banner || imagemBanner(q.c1, dados.produtos.map(p => p[4])),
    cor_primaria: q.c1,
    cor_secundaria: q.c2,
    template_id: q.tpl,
    dark_mode: q.dark,
    layout_produtos: 'grid',
    entrega_ativa: true,
    levantamento_ativo: true,
    rating_medio: 4.8,
    total_avaliacoes: 127,
    politica_devolucao: 'Aceitamos devoluções até 14 dias após a entrega, com o produto em perfeito estado.',
    termos_servico: '',
    politica_privacidade: '',
  }
  const lojaMini = { id: DEMO_ID, nome: loja.nome, categoria: loja.categoria, logo_url: loja.logo_url }

  const n = dados.produtos.length
  const produtos = dados.produtos.map(([nome, preco, tipoNome, catNome, icone, destaque, descricao], i) => {
    // os preços da lista estão em euros: passam a escudos, arredondados a 50$00
    const precoTxt = (Math.round(preco * 110.265 / 50) * 50).toFixed(2)
    const cat = categorias.find(c => c.nome === catNome)
    return {
      id: n - i,   // a API ordena por -id: o primeiro da lista aparece primeiro
      loja: lojaMini,
      tipo: tipos.find(t => t.nome === tipoNome),
      nome, descricao, sku: '',
      preco: precoTxt,
      ficheiro_url: imagemProduto(icone, PALETAS[i % PALETAS.length]),
      imagens: [],
      atributos: {}, atributos_normalizados: {}, atributos_em_falta: [],
      stock: { quantidade: 24, preco_custo: '0.00', preco_venda: precoTxt },
      stock_por_variante: false, atributos_variante: [], variantes: [], variantes_pendentes: false,
      destaque: !!destaque, ativo: true,
      data_criacao: new Date(Date.now() - i * 86400000).toISOString(),
      categorias: cat ? [{ id: cat.id, nome: cat.nome, icone: cat.icone }] : [],
    }
  })

  const contar = filtro => produtos.filter(filtro).length
  tipos.forEach(t => { t.total_produtos = contar(p => p.tipo.id === t.id) })
  categorias.forEach(c => { c.total_produtos = contar(p => p.categorias.some(x => x.id === c.id)) })

  cache = { chave, loja: { loja, tipos, categorias, produtos } }
  return cache.loja
}

// ── Respostas da "API" ─────────────────────────────────────────────────────
function listarProdutos (params = {}) {
  const { produtos } = construir()
  let lista = produtos.slice()
  const num = v => (v === undefined || v === null || v === '' ? null : Number(v))

  if (params.tipo_id)      lista = lista.filter(p => p.tipo.id === Number(params.tipo_id))
  if (params.tipo)         lista = lista.filter(p => p.tipo.nome === String(params.tipo).toLowerCase())
  if (params.categoria_id) lista = lista.filter(p => p.categorias.some(c => c.id === Number(params.categoria_id)))
  if (String(params.destaque) === 'true') lista = lista.filter(p => p.destaque)
  if (params.q) {
    const q = String(params.q).toLowerCase()
    lista = lista.filter(p => p.nome.toLowerCase().includes(q) || p.descricao.toLowerCase().includes(q))
  }
  if (num(params.preco_min) !== null) lista = lista.filter(p => Number(p.preco) >= num(params.preco_min))
  if (num(params.preco_max) !== null) lista = lista.filter(p => Number(p.preco) <= num(params.preco_max))

  const ord = params.ordering
  if (ord === 'preco')               lista.sort((a, b) => a.preco - b.preco)
  else if (ord === '-preco')         lista.sort((a, b) => b.preco - a.preco)
  else if (ord === '-data_criacao')  lista.sort((a, b) => b.data_criacao.localeCompare(a.data_criacao))
  else                               lista.sort((a, b) => b.id - a.id)

  const limit  = num(params.limit) || 20
  const offset = num(params.offset) || 0
  const results = lista.slice(offset, offset + limit)
  const fim = offset + results.length
  return { count: lista.length, next_offset: fim < lista.length ? fim : null, results }
}

function responder (metodo, caminho, params) {
  const base = `/app/loja/${DEMO_ID}/`
  if (metodo !== 'get') return {}   // carrinho, avaliações… no demo não fazem nada

  if (caminho === '/app/produto/') return listarProdutos(params)
  if (caminho === '/app/carrinho/') return []

  if (caminho.startsWith(base)) {
    const { loja, tipos, categorias, produtos } = construir()
    switch (caminho.slice(base.length)) {
      case '':                     return loja
      case 'entrega/opcoes/':      return [
        { id: 1, nome: 'Standard', preco: '250.00', tempo_estimado: '24 h', area_cobertura: '', ativa: true },
        { id: 2, nome: 'Expresso', preco: '500.00', tempo_estimado: '2 h', area_cobertura: '', ativa: true },
      ]
      case 'pagamento/metodos/':   return ['dinheiro', 'cartao', 'mbway'].map((tipo, i) => ({ id: i + 1, tipo, ativo: true }))
      case 'produtos/tipos/':      return {
        total: produtos.length,
        destaques: produtos.filter(p => p.destaque).length,
        tipos: tipos.map(({ id, nome, total_produtos }) => ({ id, nome, total_produtos })),
      }
      case 'categorias/':          return categorias
      case 'avaliacoes/':          return {
        count: AVALIACOES.length, next_offset: null,
        results: AVALIACOES.map(([u, p, c], i) => ({
          id: i + 1, utilizador_username: u, utilizador_foto: null, pontuacao: p, comentario: c,
          data_criacao: new Date(Date.now() - (i + 2) * 86400000 * 3).toISOString(), oculta: false,
        })),
      }
      case 'avaliacoes/pode-avaliar/': return { pode_avaliar: false, encomenda_id: null, avaliacoes_restantes: 0 }
      case 'carrinho/':            return { id: null, itens: [] }
    }
  }
  return { count: 0, next_offset: null, results: [] }
}

function caminhoDe (url) {
  try { return new URL(url, 'http://x').pathname } catch { return url }
}

function demoAdapter (config) {
  const data = responder((config.method || 'get').toLowerCase(), caminhoDe(config.url), config.params || {})
  return Promise.resolve({ data, status: 200, statusText: 'OK', headers: {}, config, request: {} })
}

export function emModoDemo () {
  return window.location.pathname.replace(/\/$/, '') === `/loja/${DEMO_ID}`
}

let ativo = false
/** Liga o modo demo: enquanto a página for /loja/demo, todos os pedidos do `api` são simulados. */
export function ativarLojaDemo () {
  if (ativo) return
  ativo = true
  api.interceptors.request.use(config => {
    if (emModoDemo()) config.adapter = demoAdapter
    return config
  })
}
