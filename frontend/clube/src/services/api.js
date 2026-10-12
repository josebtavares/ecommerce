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
  '/api/token/refresh/',

   // POS
  '/api/pos/login/',
  '/api/pos/register/',
];

// normaliza a barra inicial: 'app/utilizador/login/' também é público
const comBarra = (url) => '/' + String(url || '').replace(/^\/+/, '');
const isPublic = (url) => PUBLIC_URLS.some(pub => comBarra(url).includes(pub));

// ── Duas sessões independentes no mesmo browser ──────────────────────
// access_token/refresh_token → conta Bendi (loja, admin, e o POS quando entra o dono)
// pos_membro_access/refresh   → membro da equipa do POS (só serve para /api/pos/)
// Antes o membro gravava por cima do access_token e a loja deixava de funcionar.
export const MEMBRO_ACCESS  = 'pos_membro_access';
export const MEMBRO_REFRESH = 'pos_membro_refresh';

const ePOS = (url) => comBarra(url).startsWith('/api/pos/');
const usaSessaoMembro = (url) => ePOS(url) && !!localStorage.getItem(MEMBRO_ACCESS);

// browsers que ficaram com o token de membro no lugar do da Bendi (versão antiga):
// muda-o para as chaves do membro, para a loja voltar a funcionar sem limpar nada à mão
try {
  const t = localStorage.getItem('access_token');
  const payload = t && JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
  if (payload?.tipo_sessao === 'membro') {
    localStorage.setItem(MEMBRO_ACCESS, t);
    const r = localStorage.getItem('refresh_token');
    if (r) localStorage.setItem(MEMBRO_REFRESH, r);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
} catch { /* token ilegível — fica como está */ }

// Aplica token JWT no cabeçalho Authorization (só em URLs privadas)
api.interceptors.request.use((config) => {
  if (!isPublic(config.url)) {
    const access = localStorage.getItem(usaSessaoMembro(config.url) ? MEMBRO_ACCESS : 'access_token');
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

    // Não tenta refresh em URLs públicas ou se já tentou
    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry &&
      !isPublic(originalRequest.url)
    ) {
      originalRequest._retry = true;
      const membro = usaSessaoMembro(originalRequest.url);
      const [chaveAccess, chaveRefresh] = membro ? [MEMBRO_ACCESS, MEMBRO_REFRESH] : ['access_token', 'refresh_token'];

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
        // a sessão expirada é só a que falhou — a outra (Bendi ou membro do POS) fica intacta
        if (membro) {
          window.location.href = '/pos/login';
        } else {
          localStorage.removeItem('user');
          window.location.href = '/Login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;