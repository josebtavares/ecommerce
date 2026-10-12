import axios from 'axios';

const api = axios.create({
  baseURL: process.env.VUE_APP_URL_BASE
});

// URLs públicas — não enviam token nem fazem refresh
const PUBLIC_URLS = [
  '/app/utilizador/registar/',
  '/app/utilizador/login/',
  '/app/utilizador/recuperar_senha/',
  '/app/utilizador/recuperar_senha/confirmar/',
  '/app/utilizador/google/',          // URL do Google e callback
  '/app/utilizador/disponivel/',      // verificação de username/email nos formulários
  '/api/token/refresh/',

   // POS
  '/api/pos/login/',
  '/api/pos/register/',
];

// normaliza a barra inicial: 'app/utilizador/login/' também é público
const comBarra = (url) => '/' + String(url || '').replace(/^\/+/, '');
const isPublic = (url) => PUBLIC_URLS.some(pub => comBarra(url).includes(pub));

// ── Duas sessões independentes no mesmo browser ──────────────────────
// access_token/refresh_token/user → Bendi (loja, backoffice, admin)
// pos_access/pos_refresh/pos_user → POS (dono ou membro da equipa — o token diz qual)
// Entrar ou sair de uma nunca mexe na outra; podem até ser contas diferentes.
// Quem decide qual usar é a PÁGINA onde se está: em /pos/... todos os pedidos levam o
// token do POS (incluindo /app/loja/minhas/); no resto do site, o da Bendi
// (incluindo o admin da plataforma a chamar /api/pos/admin/...).
export const POS_ACCESS  = 'pos_access';
export const POS_REFRESH = 'pos_refresh';

const naPaginaPOS = () => window.location.pathname.toLowerCase().startsWith('/pos');

const payloadDe = (t) => JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));

// ── Migração de sessões de versões anteriores (corre uma vez por carregamento) ──
try {
  // 1) membro do POS com as chaves antigas
  const membroAntigo = localStorage.getItem('pos_membro_access');
  if (membroAntigo && !localStorage.getItem(POS_ACCESS)) {
    localStorage.setItem(POS_ACCESS, membroAntigo);
    const r = localStorage.getItem('pos_membro_refresh');
    if (r) localStorage.setItem(POS_REFRESH, r);
  }
  localStorage.removeItem('pos_membro_access');
  localStorage.removeItem('pos_membro_refresh');

  // 2) token de membro gravado no lugar do da Bendi (versão ainda mais antiga)
  const t = localStorage.getItem('access_token');
  if (t && payloadDe(t)?.tipo_sessao === 'membro') {
    if (!localStorage.getItem(POS_ACCESS)) {
      localStorage.setItem(POS_ACCESS, t);
      const r = localStorage.getItem('refresh_token');
      if (r) localStorage.setItem(POS_REFRESH, r);
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // 3) dono com o POS aberto quando a sessão era partilhada com a Bendi:
  //    o POS fica com uma cópia própria, para não ter de entrar outra vez
  if (naPaginaPOS() && !localStorage.getItem(POS_ACCESS)
      && localStorage.getItem('tipo_sessao') === 'principal' && localStorage.getItem('access_token')) {
    localStorage.setItem(POS_ACCESS, localStorage.getItem('access_token'));
    const r = localStorage.getItem('refresh_token');
    if (r) localStorage.setItem(POS_REFRESH, r);
  }
} catch { /* token ilegível — fica como está */ }

// Aplica token JWT no cabeçalho Authorization (só em URLs privadas)
api.interceptors.request.use((config) => {
  if (!isPublic(config.url)) {
    const access = localStorage.getItem(naPaginaPOS() ? POS_ACCESS : 'access_token');
    if (access) {
      config.headers.Authorization = `Bearer ${access}`;
    }
  }
  return config;
});

// Interceptor de resposta para renovar token automaticamente
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    const pos = naPaginaPOS();
    const [chaveAccess, chaveRefresh] = pos ? [POS_ACCESS, POS_REFRESH] : ['access_token', 'refresh_token'];

    // Não tenta refresh em URLs públicas ou se já tentou.
    // Visitante sem sessão (site sem login obrigatório): o 401 é só a resposta normal de um
    // endpoint privado — não há sessão para renovar nem razão para o mandar para o login.
    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry &&
      !isPublic(originalRequest.url) &&
      (localStorage.getItem(chaveAccess) || localStorage.getItem(chaveRefresh))
    ) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem(chaveRefresh);
        if (!refreshToken) throw new Error('No refresh token');

        const res = await axios.post(`${process.env.VUE_APP_URL_BASE}/api/token/refresh/`, {
          refresh: refreshToken
        });

        const newAccess = res.data.access_token || res.data.access;
        localStorage.setItem(chaveAccess, newAccess);

        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return axios(originalRequest);
      } catch (refreshError) {
        console.error('Erro ao renovar token', refreshError);
        localStorage.removeItem(chaveAccess);
        localStorage.removeItem(chaveRefresh);
        // só a sessão que expirou sai — a outra (Bendi ou POS) fica intacta
        if (pos) {
          localStorage.removeItem('pos_user');
          window.location.href = '/pos/login';
        } else {
          localStorage.removeItem('user');
          // volta à mesma página depois de entrar outra vez
          const aqui = window.location.pathname + window.location.search;
          window.location.href = '/Login?seguinte=' + encodeURIComponent(aqui);
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
