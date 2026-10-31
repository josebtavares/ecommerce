// O HTML de cada página para quem não corre JavaScript (WhatsApp, Facebook, Google).
// O index.html traz as etiquetas por defeito com o atributo data-seo; aqui são trocadas pelas da página.
// Os dados das lojas e produtos vêm do backend (app/utils/seo.py) — tudo o que vem de lá é escapado.

const DESCRICAO = 'Marketplace de Cabo Verde: descobre lojas locais, encomenda online e marca serviços na Bende.'
const IMAGEM = { url: '/og-bende.png', largura: 1200, altura: 630, tipo: 'image/png' }

// páginas institucionais (router.js → /:slug) e as de entrada no site
const PUBLICAS = {
  '/': 'Bende — Marketplace de Cabo Verde',
  '/ajuda': 'Ajuda — Bende',
  '/contacto': 'Contacto — Bende',
  '/faq': 'Perguntas frequentes — Bende',
  '/termos': 'Termos e condições — Bende',
  '/privacidade': 'Política de privacidade — Bende',
  '/devolucoes': 'Devoluções — Bende',
  '/entregas': 'Entregas — Bende',
}

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
const meta = (nome, valor) => `<meta name="${nome}" content="${esc(valor)}">`
const prop = (nome, valor) => `<meta property="${nome}" content="${esc(valor)}">`

function etiquetas (site, p) {
  const url = site + p.caminho
  const img = p.imagem ? { url: p.imagem, largura: 1200, altura: 630, tipo: 'image/jpeg' } : IMAGEM
  const linhas = [
    `<title>${esc(p.titulo)}</title>`,
    meta('description', p.descricao),
    p.indexar ? '' : meta('robots', 'noindex'),
    p.indexar ? `<link rel="canonical" href="${esc(url)}">` : '',
    prop('og:site_name', 'Bende'),
    prop('og:locale', 'pt_PT'),
    prop('og:type', p.tipo === 'produto' ? 'product' : 'website'),
    prop('og:title', p.titulo),
    prop('og:description', p.descricao),
    prop('og:url', url),
    prop('og:image', site + img.url),
    prop('og:image:type', img.tipo),
    prop('og:image:width', img.largura),
    prop('og:image:height', img.altura),
    prop('og:image:alt', p.nome || 'Bende'),
    meta('twitter:card', 'summary_large_image'),
  ]
  if (p.estruturados) {
    // dentro de <script>: "<" escapado para o texto de uma loja não fechar a etiqueta
    const json = JSON.stringify(p.estruturados).replace(/</g, '\\u003c')
    linhas.push(`<script type="application/ld+json">${json}</script>`)
  }
  return linhas.filter(Boolean).join('')
}

// troca o <title> e as etiquetas data-seo do index.html pelas desta página
function injetar (html, site, pagina) {
  return html
    .replace(/<title>[^<]*<\/title>/, '')
    .replace(/<(meta|link)\b[^>]*\bdata-seo\b[^>]*>/g, '')
    .replace('</head>', () => etiquetas(site, pagina) + '</head>')   // função: o "$" dos preços não é um padrão
}

// página sem dados próprios: institucional, ou privada/desconhecida (fica fora do Google)
function paginaFixa (caminho) {
  const c = caminho.replace(/\/+$/, '').toLowerCase() || '/'
  const destino = c === '/home' ? '/' : c
  const titulo = PUBLICAS[destino]
  return { tipo: 'site', titulo: titulo || 'Bende', descricao: DESCRICAO, caminho: destino,
           indexar: !!titulo }
}

function sitemap (site, dados) {
  const fixas = Object.keys(PUBLICAS).map(c => ({ loc: site + c }))
  const lojas = (dados.lojas || []).map(l => ({ loc: `${site}/loja/${l.id}`, lastmod: l.atualizado }))
  const produtos = (dados.produtos || []).map(p => ({ loc: `${site}/loja/${p.loja}?produto=${p.id}` }))
  const urls = [...fixas, ...lojas, ...produtos].map(u =>
    `<url><loc>${esc(u.loc)}</loc>${u.lastmod ? `<lastmod>${esc(u.lastmod)}</lastmod>` : ''}</url>`)
  return '<?xml version="1.0" encoding="UTF-8"?>\n' +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.join('')}</urlset>\n`
}

module.exports = { injetar, paginaFixa, sitemap }
