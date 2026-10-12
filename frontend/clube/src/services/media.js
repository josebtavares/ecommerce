// Onde vivem os ficheiros media (uploads, vídeos do site):
//   dev  → backend Django em /media/
//   prod → Cloudflare R2 (VUE_APP_MEDIA_URL definido no serviço do frontend no Railway)
const base = process.env.VUE_APP_MEDIA_URL || `${process.env.VUE_APP_URL_BASE || 'http://localhost:8000'}/media/`;

export const MEDIA_URL = base.endsWith('/') ? base : `${base}/`;

export const mediaUrl = (caminho) => MEDIA_URL + String(caminho).replace(/^\/+/, '');

// Imagens por defeito vêm com o próprio frontend (public/img/defaults) —
// funcionam em qualquer ambiente, sem depender do /media/ nem do R2
const publico = (ficheiro) => `${process.env.BASE_URL || '/'}img/defaults/${ficheiro}`;

export const DEFAULT_UTILIZADOR = publico('utilizador.png');
export const DEFAULT_PRODUTO    = publico('produto.svg');
export const DEFAULT_BANNER     = publico('banner.svg');
