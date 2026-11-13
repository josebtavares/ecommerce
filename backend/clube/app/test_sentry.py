"""Sentry (clube/sentry.py): liga só com SENTRY_DSN, e o que é enviado não leva dados sensíveis."""
import os
from unittest import mock

import sentry_sdk
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from sentry_sdk.transport import Transport

from clube import sentry as S


class _Guardar(Transport):
    """Em vez de enviar para o Sentry, guarda os eventos."""
    def __init__(self, options=None):
        super().__init__(options)
        self.eventos = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            ev = item.get_event() or item.get_transaction_event()
            if ev:
                self.eventos.append(ev)


def _ligar():
    t = _Guardar()
    real = sentry_sdk.init

    def init(**kw):
        kw['transport'] = t
        return real(**kw)

    with mock.patch.dict(os.environ, {'SENTRY_DSN': 'https://chave@o1.ingest.de.sentry.io/1', 'SENTRY_TRACES': '0'}), \
            mock.patch('sentry_sdk.init', init):
        assert S.iniciar(debug=True) is True
    return t


def _desligar():
    sentry_sdk.init(dsn=None)


class SentryLigaSoComDsn(TestCase):
    def test_sem_dsn_nao_liga(self):
        with mock.patch.dict(os.environ, {'SENTRY_DSN': ''}):
            self.assertFalse(S.iniciar(debug=True))

    def test_com_dsn_liga(self):
        t = _ligar()
        try:
            sentry_sdk.capture_message('ola')
            sentry_sdk.flush()
            self.assertEqual(len(t.eventos), 1)
            ev = t.eventos[0]
            self.assertEqual(ev['environment'], 'dev')
            self.assertEqual(ev['tags'].get('servico'), 'local')
        finally:
            _desligar()


class SentryNaoEnviaDadosSensiveis(TestCase):
    def tearDown(self):
        _desligar()

    def test_variaveis_locais_e_extras(self):
        t = _ligar()

        # os valores são montados em tempo de execução: o Sentry mostra as linhas do código (contexto), não os dados
        x = 'SEG' + 'REDO-'

        def falha():
            senha = x + '1'                                  # noqa: F841
            pos_aut_code = x + '2'                           # noqa: F841
            corpo = '{"posAuthCode":"%s3"}' % x              # noqa: F841 — texto: nenhum filtro por nome o apanha
            raise ValueError('falhou')

        with sentry_sdk.new_scope() as scope:
            scope.set_extra('dados', {'iban': x + '4', 'nib': x + '5', 'nome': 'visivel'})
            scope.set_context('pedido', {'senha': x + '6', 'chave': x + '7'})
            try:
                falha()
            except ValueError as e:
                sentry_sdk.capture_exception(e)
        sentry_sdk.flush()
        texto = repr(t.eventos)
        for i in range(1, 8):
            self.assertNotIn(f'SEGREDO-{i}', texto)
        self.assertIn('visivel', texto)
        frames = t.eventos[0]['exception']['values'][0]['stacktrace']['frames']
        self.assertTrue(frames and all('vars' not in f for f in frames))

    @override_settings(DEBUG_PROPAGATE_EXCEPTIONS=False)
    def test_pedido_sem_corpo_ip_nem_token(self):
        t = _ligar()
        u = User.objects.create_user('sentry_t', 'sentry_' + 't@x.cv', 'Pw-123456!')
        c = APIClient(HTTP_HOST='localhost', REMOTE_ADDR='203.0.113.9')
        c.force_authenticate(u)
        with mock.patch('app.Views.horarioView._exige_admin', side_effect=RuntimeError('rebentou')):
            c.raise_request_exception = False
            x = 'SEG' + 'REDO-'
            r = c.post('/app/admin/plataforma/sentry/', {'senha': x + '8', 'iban': x + '9'}, format='json',
                       HTTP_AUTHORIZATION='Bearer ' + x + '10', HTTP_COOKIE='sessionid=' + x + '11')
        self.assertEqual(r.status_code, 500)
        sentry_sdk.flush()
        self.assertTrue(t.eventos, 'o erro 500 tem de chegar ao Sentry')
        texto = repr(t.eventos)
        for s in ('SEGREDO-8', 'SEGREDO-9', 'SEGREDO-10', 'SEGREDO-11', '203.0.113.9', 'sentry_t@x.cv'):
            self.assertNotIn(s, texto)
        self.assertIn('/app/admin/plataforma/sentry/', texto)

    def test_emails_nas_mensagens(self):
        import logging
        t = _ligar()
        quem = 'cliente.' + 'teste@exemplo.cv'
        logging.getLogger('app.teste').warning('a preparar envio para %s', quem)     # breadcrumb
        logging.getLogger('app.teste').error('falhou o envio para %s', quem)        # evento
        try:
            raise ValueError(f'conta {quem} inválida')
        except ValueError as e:
            sentry_sdk.capture_exception(e)
        sentry_sdk.flush()
        self.assertEqual(len(t.eventos), 2)
        self.assertNotIn(quem, repr(t.eventos))
        self.assertIn('[email]', repr(t.eventos))

    def test_credenciais_vinti4_nao_mostram_a_chave(self):
        from app.pagamentos.vinti4 import Credenciais
        self.assertNotIn('SEGREDO', repr(Credenciais('90000586', 'SEG' + 'REDO')))

    def test_worker_reportar(self):
        from app.utils.erros import reportar
        t = _ligar()
        try:
            raise KeyError('ciclo')
        except KeyError as e:
            reportar(e)
        sentry_sdk.flush()
        self.assertEqual(len(t.eventos), 1)

    def test_reportar_sem_sentry_nao_parte(self):
        from app.utils.erros import reportar
        _desligar()
        reportar(ValueError('x'))      # sem exceção


class BotaoDeTesteDoAdmin(TestCase):
    def tearDown(self):
        _desligar()

    def test_so_admins(self):
        u = User.objects.create_user('nao_admin', 'na@x.cv', 'Pw-123456!')
        c = APIClient(HTTP_HOST='localhost'); c.force_authenticate(u)
        self.assertEqual(c.post('/app/admin/plataforma/sentry/').status_code, 403)

    def test_desligado_e_ligado(self):
        from app.models import Utilizador
        a = User.objects.create_superuser('adm_sentry', 'adm@x.cv', 'Pw-123456!')
        Utilizador.objects.create(user=a, role_admin='superadmin')
        c = APIClient(HTTP_HOST='localhost'); c.force_authenticate(a)
        with override_settings(SENTRY_LIGADO=False):
            self.assertEqual(c.post('/app/admin/plataforma/sentry/').json(), {'ligado': False, 'ambiente': None})
        t = _ligar()
        with override_settings(SENTRY_LIGADO=True):
            r = c.post('/app/admin/plataforma/sentry/').json()
        self.assertTrue(r['ligado'] and r['evento'])
        self.assertEqual(len(t.eventos), 1)
        self.assertEqual(t.eventos[0]['tags'].get('teste'), 'sim')
