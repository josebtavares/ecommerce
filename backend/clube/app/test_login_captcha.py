"""Captcha adaptativo nos logins (utils/auth.py): só depois de falhas, antes de verificar a password."""
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Utilizador

CACHE_LOCAL = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'login-captcha'}}


def _cloudflare(ok):
    resp = mock.Mock()
    resp.json.return_value = {'success': ok}
    return mock.patch('app.utils.turnstile.requests.post', return_value=resp)


@override_settings(CACHES=CACHE_LOCAL, TURNSTILE_SECRET='segredo-teste')
class CaptchaNoLogin(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('ana_captcha', 'ana_captcha@exemplo.cv', 'Senha-certa-123')
        Utilizador.objects.create(user=self.user)
        self.api = APIClient()

    def tearDown(self):
        cache.clear()

    def _login(self, password, url='/app/utilizador/login/', ident='ana_captcha', **extra):
        return self.api.post(url, {'username': ident, 'password': password, **extra}, format='json')

    def test_a_primeira_nao_pede(self):
        r = self._login('Senha-certa-123')
        self.assertEqual(r.status_code, 200, r.content[:200])

    def test_depois_de_falhas_pede_antes_da_password(self):
        for i in range(3):
            r = self._login('errada')
            self.assertEqual(r.status_code, 401)
        self.assertTrue(r.json().get('turnstile'))      # a 3.ª falha já avisa o frontend
        # sem captcha: nem a password certa entra (e não conta como falha no axes)
        r = self._login('Senha-certa-123')
        self.assertEqual((r.status_code, r.json().get('turnstile')), (400, True))
        with _cloudflare(False):
            self.assertEqual(self._login('Senha-certa-123', turnstile='x').status_code, 400)
        with _cloudflare(True):
            r = self._login('Senha-certa-123', turnstile='bom')
        self.assertEqual(r.status_code, 200, r.content[:200])

    def test_por_email_conta_a_mesma_conta(self):
        for _ in range(3):
            self._login('errada', ident='ANA_captcha@exemplo.cv')
        self.assertEqual(self._login('Senha-certa-123', ident='ana_captcha@exemplo.cv').status_code, 400)

    def test_api_token_tambem(self):
        for _ in range(3):
            r = self._login('errada', url='/api/token/')
        self.assertEqual(r.status_code, 401)
        self.assertIs(r.json().get('turnstile'), True)
        r = self._login('Senha-certa-123', url='/api/token/')
        self.assertEqual((r.status_code, r.json().get('turnstile')), (400, True))
        with _cloudflare(True):
            self.assertEqual(self._login('Senha-certa-123', url='/api/token/', turnstile='bom').status_code, 200)

    def test_pos_dono(self):
        for _ in range(3):
            self.api.post('/api/pos/login/', {'email': 'ana_captcha@exemplo.cv', 'password': 'errada'}, format='json')
        r = self.api.post('/api/pos/login/', {'email': 'ana_captcha@exemplo.cv', 'password': 'Senha-certa-123'}, format='json')
        self.assertEqual((r.status_code, r.json().get('turnstile')), (400, True))

    def test_pos_membro(self):
        for _ in range(3):
            r = self.api.post('/api/pos/login/membro/', {'username': 'joana', 'password': 'errada'}, format='json')
        self.assertEqual(r.status_code, 401)
        self.assertTrue(r.json().get('turnstile'))
        r = self.api.post('/api/pos/login/membro/', {'username': 'joana', 'password': 'errada'}, format='json')
        self.assertEqual(r.status_code, 400)

    @override_settings(TURNSTILE_SECRET='')
    def test_sem_chave_nunca_pede(self):
        for _ in range(4):
            r = self._login('errada')
        self.assertNotIn('turnstile', r.json())

    def test_limite_de_pedidos_por_ip(self):
        from .utils import auth
        with mock.patch.object(auth, 'LIMITES_PEDIDOS_IP', (('login_pedidos_ip_m', '2/m'),)):
            self.assertEqual(self._login('Senha-certa-123').status_code, 200)
            self.assertEqual(self._login('Senha-certa-123').status_code, 200)
            self.assertEqual(self._login('Senha-certa-123').status_code, 429)
            self.assertEqual(self._login('Senha-certa-123', url='/api/token/').status_code, 429)
