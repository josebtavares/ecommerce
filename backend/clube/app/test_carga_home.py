"""Teste de carga 2026-11-14: lista de lojas sem N+1 nas avaliações, nomes das categorias numa consulta e home
que não é montada por todos ao mesmo tempo quando a cache expira (utils/home.py)."""
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from app.models import AvaliacaoLoja, Categoria, Loja, Utilizador
from app.utils import home as H


def _conta(nome):
    u = User.objects.create_user(nome, f'{nome}@x.invalid', 'x-Teste-123!')
    return Utilizador.objects.create(user=u, email_confirmado=True)


class ListaDeLojasSemN1(TestCase):
    def setUp(self):
        cache.clear()
        self.dono = _conta('donocarga')
        self.clientes = [_conta(f'cli{i}') for i in range(3)]

    def _lojas(self, n, inicio=0):
        for i in range(inicio, inicio + n):
            loja = Loja.objects.create(dono=self.dono, nome=f'Loja {i}', slug=f'loja-carga-{i}', categoria='moda',
                                       estado='ativa', ativa=True)
            for j, c in enumerate(self.clientes):
                AvaliacaoLoja.objects.create(utilizador=c, loja=loja, pontuacao=j + 3, oculta=(j == 2))

    def _pedir(self):
        with CaptureQueriesContext(connection) as q:
            r = APIClient().get('/app/loja/?limit=50&offset=0')
        self.assertEqual(r.status_code, 200)
        return r.data['results'], len(q.captured_queries)

    def test_consultas_nao_crescem_com_o_numero_de_lojas(self):
        self._lojas(2)
        _, poucas = self._pedir()
        self._lojas(8, inicio=2)
        cache.clear()
        lojas, muitas = self._pedir()
        self.assertEqual(len(lojas), 10)
        self.assertEqual(poucas, muitas)

    def test_media_e_total_so_das_visiveis(self):
        self._lojas(1)
        loja = self._pedir()[0][0]
        self.assertEqual(loja['total_avaliacoes'], 2)      # a oculta (5★) não conta
        self.assertEqual(loja['rating_medio'], 3.5)        # (3 + 4) / 2

    def test_loja_sem_avaliacoes(self):
        Loja.objects.create(dono=self.dono, nome='Nova', slug='nova-carga', categoria='moda', estado='ativa', ativa=True)
        loja = self._pedir()[0][0]
        self.assertEqual((loja['rating_medio'], loja['total_avaliacoes']), (None, 0))


class NomesDasCategorias(TestCase):
    def setUp(self):
        cache.clear()
        Categoria.objects.create(nome='Beleza & Bem-estar')

    def test_uma_consulta_para_varias(self):
        with CaptureQueriesContext(connection) as q:
            nomes = [H.rotulo_categoria(v) for v in ('beleza & bem-estar', 'BELEZA & BEM-ESTAR', 'moda', 'xpto', '')]
        self.assertEqual(nomes, ['Beleza & Bem-estar', 'Beleza & Bem-estar', 'Moda', 'Xpto', ''])
        self.assertEqual(len(q.captured_queries), 1)


class HomeSemCorrida(TestCase):
    def setUp(self):
        cache.clear()
        self.pedido = mock.Mock()
        self.pedido.build_absolute_uri.return_value = 'https://e-bendi.cv/'
        self.publicada = mock.patch.object(H, 'publicada', return_value=(7, []))
        self.publicada.start()
        self.addCleanup(self.publicada.stop)

    def test_fresca_nao_volta_a_montar(self):
        with mock.patch.object(H, 'montar', return_value={'v': 1}) as m:
            H.home(self.pedido); H.home(self.pedido)
        self.assertEqual(m.call_count, 1)

    def test_expirada_um_monta_os_outros_recebem_a_anterior(self):
        with mock.patch.object(H, 'montar', return_value={'v': 1}):
            H.home(self.pedido)
        with mock.patch('app.utils.home.time.time', return_value=10 ** 12):      # passou muito tempo
            cache.add('home:v2:7:https://e-bendi.cv/:a_montar', 1, 30)          # outro pedido já está a montar
            with mock.patch.object(H, 'montar', return_value={'v': 2}) as m:
                self.assertEqual(H.home(self.pedido), {'v': 1})
            m.assert_not_called()
            cache.delete('home:v2:7:https://e-bendi.cv/:a_montar')
            with mock.patch.object(H, 'montar', return_value={'v': 2}) as m:
                self.assertEqual(H.home(self.pedido), {'v': 2})                    # este monta a nova
            m.assert_called_once()

    def test_erro_ao_montar_liberta_a_tranca(self):
        with mock.patch.object(H, 'montar', side_effect=RuntimeError('bd')):
            with self.assertRaises(RuntimeError):
                H.home(self.pedido)
        self.assertIsNone(cache.get('home:v2:7:https://e-bendi.cv/:a_montar'))
