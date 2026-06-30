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

const isPublic = (url) => PUBLIC_URLS.some(pub => url?.includes(pub));

// Aplica token JWT no cabeçalho Authorization (só em URLs privadas)
api.interceptors.request.use((config) => {
  if (!isPublic(config.url)) {
    const access = localStorage.getItem('access_token');
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

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const res = await axios.post(`${process.env.VUE_APP_URL_BASE}/api/token/refresh/`, {
          refresh: refreshToken
        });

        const newAccess = res.data.access_token || res.data.access;
        localStorage.setItem('access_token', newAccess);

        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return axios(originalRequest);
      } catch (refreshError) {
        console.error('Erro ao renovar token', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/Login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;