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
// WebSockets no mesmo servidor da API (http→ws, https→wss): evita o VUE_APP_WS_URL
// ficar a apontar para outro sítio (aconteceu na dev — o tempo real caía para polling).
export function urlWebSocket (caminho) {
  const base = process.env.VUE_APP_URL_BASE || 'http://localhost:8000';
  return base.replace(/^http/, 'ws').replace(/\/+$/, '') + '/ws/' + caminho.replace(/^\/+/, '');
}

// O JWT não vai no endereço do WebSocket (ficava nos logs): pede-se antes um bilhete de uso
// único (60 s). Sem bilhete (rede, sessão caída) liga sem ele — o servidor recusa e quem chama
// segue o caminho normal de religar.
export async function urlWebSocketComBilhete (caminho) {
  try {
    const { data } = await api.post('/api/ws/bilhete/');
    return urlWebSocket(`${caminho}?bilhete=${encodeURIComponent(data.bilhete)}`);
  } catch {
    return urlWebSocket(caminho);
  }
}

// Sair a sério: o servidor põe o refresh na lista negra e o access deixa de valer já
// (Views/sessaoView.py). Lê as chaves antes de quem chama as apagar; não se espera pela resposta.
export function terminarSessao (chaveAccess, chaveRefresh) {
  const access = localStorage.getItem(chaveAccess);
  const refresh = localStorage.getItem(chaveRefresh);
  if (!access && !refresh) return;
  axios.post(`${process.env.VUE_APP_URL_BASE}/api/token/logout/`, { refresh },
    access ? { headers: { Authorization: `Bearer ${access}` } } : {}).catch(() => {});
}

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

// ── Admin a ver o backoffice de uma loja (só leitura — backend utils/ver_loja.py) ──
// O Admin abre /loja/<id>/backoffice#ver_admin=<token> noutro separador. O token fica só nesse
// separador (sessionStorage), sai logo do endereço e vai nos pedidos feitos a partir do backoffice
// dessa loja. Não se renova: quando expira, abre-se outra vez a partir do Admin.
const VER_ADMIN = 'ver_admin';
export const EVENTO_VER_ADMIN_EXPIROU = 'ver-admin-expirou';
const lojaDoBackoffice = () => (window.location.pathname.match(/^\/loja\/(\d+)\/backoffice/i) || [])[1];

export function capturarVerAdmin () {
  try {
    const m = window.location.hash.match(/ver_admin=([^&]+)/);
    const loja = lojaDoBackoffice();
    if (!m) return;
    if (loja) sessionStorage.setItem(VER_ADMIN, JSON.stringify({ loja, token: decodeURIComponent(m[1]) }));
    history.replaceState(history.state, '', window.location.pathname + window.location.search);
  } catch { /* sessionStorage bloqueado: abre como um utilizador normal (sem acesso) */ }
}
capturarVerAdmin();

// token de leitura desta loja, ou null
export function verAdmin (lojaId) {
  try {
    const v = JSON.parse(sessionStorage.getItem(VER_ADMIN) || 'null');
    return v && String(v.loja) === String(lojaId) ? v.token : null;
  } catch { return null; }
}

// a sessão do próprio admin (sino, tempo real) continua com o token normal
const DO_PROPRIO_ADMIN = ['/app/notificacoes/', '/api/ws/bilhete/'];

// Aplica token JWT no cabeçalho Authorization (só em URLs privadas)
api.interceptors.request.use((config) => {
  const loja = !naPaginaPOS() && lojaDoBackoffice();
  const ver = loja && !DO_PROPRIO_ADMIN.some(u => comBarra(config.url).includes(u)) && verAdmin(loja);
  if (ver) {
    config.headers.Authorization = `Bearer ${ver}`;
    config._verAdmin = true;
    return config;
  }
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

    // modo de leitura do admin: sem refresh — o separador mostra que a sessão de leitura terminou
    if (originalRequest?._verAdmin && error.response?.status === 401) {
      try { sessionStorage.removeItem(VER_ADMIN); } catch { /* */ }
      window.dispatchEvent(new Event(EVENTO_VER_ADMIN_EXPIROU));
      return Promise.reject(error);
    }

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
