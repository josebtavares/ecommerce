// utils/icones.js
// Ícones em vez de emojis. Usa o Font Awesome (solid), já registado globalmente em main.js:
//   <font-awesome-icon :icon="['fas', iconeCategoria(cat.icon, cat.nome)]" />
//
// As categorias da plataforma guardam no campo `icon` (max 10 caracteres) uma CHAVE curta
// desta lista — ex.: 'roupa'. Valores antigos (emojis) e nomes de categoria ('moda',
// 'restaurante'…) também são reconhecidos, para não ser preciso migrar dados.

export const ICONES_CATEGORIA = [
  { chave: 'loja',      icone: 'store',                       label: 'Loja' },
  { chave: 'comida',    icone: 'utensils',                    label: 'Restauração' },
  { chave: 'cafe',      icone: 'mug-hot',                     label: 'Café' },
  { chave: 'bebidas',   icone: 'wine-glass',                  label: 'Bebidas' },
  { chave: 'mercado',   icone: 'basket-shopping',             label: 'Supermercado' },
  { chave: 'roupa',     icone: 'shirt',                       label: 'Moda' },
  { chave: 'joias',     icone: 'gem',                         label: 'Joalharia' },
  { chave: 'beleza',    icone: 'spa',                         label: 'Beleza' },
  { chave: 'saude',     icone: 'prescription-bottle-medical', label: 'Farmácia' },
  { chave: 'tech',      icone: 'laptop',                      label: 'Tecnologia' },
  { chave: 'desporto',  icone: 'futbol',                      label: 'Desporto' },
  { chave: 'livros',    icone: 'book',                        label: 'Livraria' },
  { chave: 'casa',      icone: 'couch',                       label: 'Casa' },
  { chave: 'jardim',    icone: 'seedling',                    label: 'Jardim' },
  { chave: 'animais',   icone: 'paw',                         label: 'Animais' },
  { chave: 'bebe',      icone: 'baby',                        label: 'Bebé' },
  { chave: 'brinquedo', icone: 'puzzle-piece',                label: 'Brinquedos' },
  { chave: 'musica',    icone: 'music',                       label: 'Música' },
  { chave: 'arte',      icone: 'palette',                     label: 'Arte' },
  { chave: 'auto',      icone: 'car',                         label: 'Automóvel' },
  { chave: 'servicos',  icone: 'screwdriver-wrench',          label: 'Serviços' },
  { chave: 'presentes', icone: 'gift',                        label: 'Presentes' },
]

const POR_CHAVE = Object.fromEntries(ICONES_CATEGORIA.map(i => [i.chave, i.icone]))

// emojis que já estejam gravados na base de dados
const POR_EMOJI = {
  '🏪': 'loja', '🏬': 'loja', '🛍️': 'loja', '🛍': 'loja',
  '🍔': 'comida', '🍽️': 'comida', '🍽': 'comida', '🍕': 'comida', '🥗': 'comida',
  '☕': 'cafe', '🥤': 'bebidas', '🍷': 'bebidas', '🍺': 'bebidas',
  '🛒': 'mercado', '🍎': 'mercado', '🥦': 'mercado',
  '👗': 'roupa', '👕': 'roupa', '👟': 'roupa', '👜': 'roupa',
  '💎': 'joias', '💍': 'joias', '💄': 'beleza', '💅': 'beleza',
  '💊': 'saude', '🏥': 'saude',
  '📱': 'tech', '💻': 'tech', '🖥️': 'tech', '🎧': 'tech',
  '⚽': 'desporto', '🏀': 'desporto', '🏋️': 'desporto',
  '📚': 'livros', '📖': 'livros',
  '🏠': 'casa', '🛋️': 'casa', '🌿': 'jardim', '🌱': 'jardim', '🌸': 'jardim',
  '🐶': 'animais', '🐾': 'animais', '👶': 'bebe', '🧸': 'brinquedo',
  '🎵': 'musica', '🎨': 'arte', '🚗': 'auto', '🔧': 'servicos', '🎁': 'presentes',
}

// nomes de categoria (sem acentos, minúsculas)
const POR_NOME = {
  loja: 'loja', outros: 'loja', geral: 'loja',
  restaurante: 'comida', restaurantes: 'comida', restauracao: 'comida', comida: 'comida', 'take-away': 'comida',
  cafe: 'cafe', pastelaria: 'cafe', padaria: 'cafe', bebidas: 'bebidas', bar: 'bebidas',
  supermercado: 'mercado', mercearia: 'mercado', mercado: 'mercado', alimentacao: 'mercado',
  moda: 'roupa', roupa: 'roupa', vestuario: 'roupa', calcado: 'roupa',
  joalharia: 'joias', joias: 'joias', beleza: 'beleza', cosmetica: 'beleza',
  farmacia: 'saude', saude: 'saude',
  tecnologia: 'tech', eletronica: 'tech', informatica: 'tech',
  desporto: 'desporto', fitness: 'desporto',
  livraria: 'livros', livros: 'livros', papelaria: 'livros',
  casa: 'casa', 'casa e jardim': 'casa', decoracao: 'casa', jardim: 'jardim', natureza: 'jardim',
  animais: 'animais', bebe: 'bebe', brinquedos: 'brinquedo',
  musica: 'musica', arte: 'arte', automovel: 'auto', servicos: 'servicos', presentes: 'presentes',
}

function normalizar (txt) {
  return String(txt || '').normalize('NFD').replace(/[̀-ͯ]/g, '').trim().toLowerCase()
}

/** Nome do ícone Font Awesome para uma categoria (chave, emoji antigo ou nome). */
export function iconeCategoria (valor, nome) {
  const v = String(valor || '').trim()
  if (POR_CHAVE[v]) return POR_CHAVE[v]
  if (POR_EMOJI[v]) return POR_CHAVE[POR_EMOJI[v]]
  const chave = POR_NOME[normalizar(nome)] || POR_NOME[normalizar(v)]
  return chave ? POR_CHAVE[chave] : 'store'
}

/** Chave da lista para um valor antigo (emoji/nome) — usada ao editar no admin. */
export function chaveCategoria (valor, nome) {
  const v = String(valor || '').trim()
  if (POR_CHAVE[v]) return v
  return POR_EMOJI[v] || POR_NOME[normalizar(nome)] || 'loja'
}

/** Ícone para um método de pagamento. */
export function iconePagamento (tipo) {
  return ({
    dinheiro: 'money-bill-wave', mbway: 'mobile-screen-button', cartao: 'credit-card',
    paypal: 'wallet', stripe: 'credit-card', transferencia: 'building-columns',
    multibanco: 'building-columns', flutterwave: 'earth-africa', mobile_money: 'mobile-screen',
  })[String(tipo || '').toLowerCase()] || 'wallet'
}

// ── Categorias de produtos (criadas por cada loja no backoffice) ─────────────
// Mesmo princípio: o campo `icone` (max 10) guarda uma chave desta lista.
export const ICONES_CATEGORIA_PRODUTO = [
  { chave: 'pasta',     icone: 'folder-open',     label: 'Geral' },
  { chave: 'etiqueta',  icone: 'tag',             label: 'Etiqueta' },
  { chave: 'promo',     icone: 'percent',         label: 'Promoções' },
  { chave: 'novidade',  icone: 'star',            label: 'Novidades' },
  { chave: 'popular',   icone: 'fire',            label: 'Populares' },
  { chave: 'homem',     icone: 'person',          label: 'Homem' },
  { chave: 'mulher',    icone: 'person-dress',    label: 'Mulher' },
  { chave: 'crianca',   icone: 'child',           label: 'Criança' },
  { chave: 'roupa',     icone: 'shirt',           label: 'Roupa' },
  { chave: 'calcado',   icone: 'shoe-prints',     label: 'Calçado' },
  { chave: 'acessorio', icone: 'glasses',         label: 'Acessórios' },
  { chave: 'joias',     icone: 'gem',             label: 'Joias' },
  { chave: 'beleza',    icone: 'spa',             label: 'Beleza' },
  { chave: 'hamburger', icone: 'burger',          label: 'Hambúrgueres' },
  { chave: 'pizza',     icone: 'pizza-slice',     label: 'Pizzas' },
  { chave: 'carne',     icone: 'drumstick-bite',  label: 'Carne' },
  { chave: 'peixe',     icone: 'fish',            label: 'Peixe' },
  { chave: 'legumes',   icone: 'carrot',          label: 'Legumes' },
  { chave: 'fruta',     icone: 'apple-whole',     label: 'Fruta' },
  { chave: 'padaria',   icone: 'bread-slice',     label: 'Padaria' },
  { chave: 'doces',     icone: 'cake-candles',    label: 'Doces' },
  { chave: 'gelados',   icone: 'ice-cream',       label: 'Gelados' },
  { chave: 'cafe',      icone: 'mug-hot',         label: 'Café' },
  { chave: 'bebidas',   icone: 'wine-glass',      label: 'Bebidas' },
  { chave: 'agua',      icone: 'bottle-water',    label: 'Águas' },
  { chave: 'tech',      icone: 'laptop',          label: 'Informática' },
  { chave: 'telemovel', icone: 'mobile-screen',   label: 'Telemóveis' },
  { chave: 'audio',     icone: 'headphones',      label: 'Áudio' },
  { chave: 'jogos',     icone: 'gamepad',         label: 'Jogos' },
  { chave: 'casa',      icone: 'couch',           label: 'Casa' },
  { chave: 'jardim',    icone: 'seedling',        label: 'Jardim' },
  { chave: 'animais',   icone: 'paw',             label: 'Animais' },
  { chave: 'bebe',      icone: 'baby',            label: 'Bebé' },
  { chave: 'livros',    icone: 'book',            label: 'Livros' },
  { chave: 'presentes', icone: 'gift',            label: 'Presentes' },
  { chave: 'saude',     icone: 'heart',           label: 'Saúde' },
]

const PRODUTO_POR_CHAVE = Object.fromEntries(ICONES_CATEGORIA_PRODUTO.map(i => [i.chave, i.icone]))

const PRODUTO_POR_EMOJI = {
  '📂': 'pasta', '📁': 'pasta', '🏷️': 'etiqueta', '🏷': 'etiqueta', '💸': 'promo', '🔖': 'etiqueta',
  '⭐': 'novidade', '✨': 'novidade', '🆕': 'novidade', '🔥': 'popular',
  '👨': 'homem', '🧔': 'homem', '👩': 'mulher', '👧': 'crianca', '🧒': 'crianca', '👦': 'crianca',
  '👕': 'roupa', '👗': 'roupa', '👔': 'roupa', '👟': 'calcado', '👠': 'calcado', '👞': 'calcado',
  '👜': 'acessorio', '🕶️': 'acessorio', '⌚': 'acessorio', '💎': 'joias', '💍': 'joias',
  '💄': 'beleza', '💅': 'beleza', '🍔': 'hamburger', '🍕': 'pizza', '🍗': 'carne', '🥩': 'carne',
  '🐟': 'peixe', '🍣': 'peixe', '🥕': 'legumes', '🥦': 'legumes', '🥗': 'legumes', '🍎': 'fruta',
  '🍞': 'padaria', '🥐': 'padaria', '🍰': 'doces', '🎂': 'doces', '🍫': 'doces', '🍦': 'gelados',
  '☕': 'cafe', '🍷': 'bebidas', '🍺': 'bebidas', '🥤': 'bebidas', '🍹': 'bebidas', '💧': 'agua',
  '💻': 'tech', '🖥️': 'tech', '📱': 'telemovel', '🎧': 'audio', '🎮': 'jogos',
  '🏠': 'casa', '🛋️': 'casa', '🌱': 'jardim', '🌿': 'jardim', '🐶': 'animais', '🐾': 'animais',
  '👶': 'bebe', '📚': 'livros', '📖': 'livros', '🎁': 'presentes', '💊': 'saude', '❤️': 'saude',
}

const PRODUTO_POR_NOME = {
  geral: 'pasta', outros: 'pasta', promocao: 'promo', promocoes: 'promo', saldos: 'promo', desconto: 'promo',
  novidades: 'novidade', novo: 'novidade', destaques: 'novidade', populares: 'popular', 'mais vendidos': 'popular',
  homem: 'homem', mulher: 'mulher', senhora: 'mulher', crianca: 'crianca', criancas: 'crianca', infantil: 'crianca',
  roupa: 'roupa', vestuario: 'roupa', calcado: 'calcado', sapatos: 'calcado', acessorios: 'acessorio',
  joias: 'joias', joalharia: 'joias', beleza: 'beleza', cosmetica: 'beleza',
  hamburgueres: 'hamburger', burgers: 'hamburger', pizzas: 'pizza', pizza: 'pizza', carne: 'carne', carnes: 'carne',
  peixe: 'peixe', marisco: 'peixe', legumes: 'legumes', saladas: 'legumes', fruta: 'fruta', frutas: 'fruta',
  padaria: 'padaria', pao: 'padaria', doces: 'doces', sobremesas: 'doces', pastelaria: 'doces', gelados: 'gelados',
  cafe: 'cafe', cafes: 'cafe', bebidas: 'bebidas', vinhos: 'bebidas', cervejas: 'bebidas', aguas: 'agua',
  informatica: 'tech', computadores: 'tech', telemoveis: 'telemovel', audio: 'audio', jogos: 'jogos',
  casa: 'casa', decoracao: 'casa', jardim: 'jardim', animais: 'animais', bebe: 'bebe',
  livros: 'livros', presentes: 'presentes', saude: 'saude',
}

/** Ícone Font Awesome para uma categoria de produtos da loja (chave, emoji antigo ou nome). */
export function iconeCategoriaProduto (valor, nome) {
  return PRODUTO_POR_CHAVE[chaveCategoriaProduto(valor, nome)]
}

/** Chave da lista para uma categoria de produtos (converte emojis antigos / sugere pelo nome). */
export function chaveCategoriaProduto (valor, nome) {
  const v = String(valor || '').trim()
  if (PRODUTO_POR_CHAVE[v]) return v
  if (PRODUTO_POR_EMOJI[v]) return PRODUTO_POR_EMOJI[v]
  return PRODUTO_POR_NOME[normalizar(nome)] || 'pasta'
}

/** Ícone para um tipo de produto (nome livre: 'prato', 'roupa', 'telemovel'…). */
export function iconeTipoProduto (tipo) {
  return ({
    prato: 'utensils', comida: 'burger', bebida: 'wine-glass', sobremesa: 'cake-candles',
    roupa: 'shirt', calcado: 'shoe-prints', acessorio: 'glasses',
    eletronico: 'plug', telemovel: 'mobile-screen', tablet: 'tablet-screen-button',
    fruta: 'apple-whole', legume: 'carrot', carne: 'drumstick-bite',
    livro: 'book', manga: 'book-open', revista: 'newspaper',
  })[normalizar(tipo)] || 'box'
}
