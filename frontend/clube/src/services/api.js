import axios from 'axios';

const api = axios.create({
  baseURL: process.env.VUE_APP_URL_BASE
});

// Aplica token JWT no cabeçalho Authorization
api.interceptors.request.use((config) => {
  const access = localStorage.getItem('access_token');
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// Interceptor de resposta para renovar token automaticamente
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        // Requisição para obter novo access token
        const res = await axios.post(`${process.env.VUE_APP_URL_BASE}/api/token/refresh/`, {
          refresh: refreshToken
        });

        const newAccess = res.data.access;

        localStorage.setItem('access_token', newAccess);

        // Atualiza o header da requisição original e repete
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return axios(originalRequest);
      } catch (refreshError) {
        console.error('Erro ao renovar token', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        // Opcional: redirecionar para login
        window.location.href = '/Login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;