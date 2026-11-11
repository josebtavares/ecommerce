"""
vinti4 / SISP (pagamentos/vinti4.py). Correr: python manage.py test app.test_vinti4

As assinaturas são verificadas contra os exemplos oficiais da SISP (Pagamento Web — Especificação do Protocolo
de Segurança, 2.4.2). As credenciais de teste são as dos exemplos de código públicos da SISP (posID 90051).
"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import TransacaoVinti4, Utilizador
from .pagamentos import ErroPagamento, obter
from .pagamentos import vinti4 as v4
from .pagamentos.base import Cobranca
from .pagamentos.servico import DadosClienteEmFalta

CHAVE = '123456789A'
CRED = dict(VINTI4_POS_ID='90051', VINTI4_POS_AUT_CODE=CHAVE, VINTI4_PORTAL_ID='', VINTI4_PORTAL_PASSWORD='',
            VINTI4_URL='https://3dsteste.vinti4net.cv/3ds_middleware_php/public/3ds_init.php',
            API_BASE_URL='https://api.exemplo.cv', FRONTEND_BASE_URL='https://exemplo.cv')


class AssinaturasOficiais(TestCase):
    """Os três exemplos da especificação de segurança."""

    def test_chave(self):
        self.assertTrue(v4._sha512_b64('ttqRdOzmGvCSpuag').startswith('Db9k/Mqg6dLNrdKseAdLTm7p6201'))
        self.assertEqual(v4._sha512_b64('123456789A'),
                         'TrmzQzqPgdgicNXUMMKu8p+rtbSoqZDkXeHBZVeZdkyY/BhPZKArQpCJAP4GsPaJbviDg51P8iYlyohDjNr52w==')

    def test_resposta_sucesso(self):
        d = {'messageType': '8', 'merchantRespCP': '987', 'merchantRespTid': '26',
             'merchantRespMerchantRef': 'R20200517133227', 'merchantRespMerchantSession': 'S20200517133227',
             'merchantRespPurchaseAmount': '1000.00', 'merchantRespMessageID': 'J38HvwHPPn22P1se0OxJ',
             'merchantRespPan': '************3335', 'merchantResp': 'C', 'merchantRespErrorCode': '',
             'merchantRespTimeStamp': '2020-05-17 13:30:48', 'merchantRespReferenceNumber': '',
             'merchantRespEntityCode': '', 'merchantRespClientReceipt': '', 'merchantRespReloadCode': '',
             'merchantRespAdditionalErrorMessage': ''}
        self.assertEqual(v4.fingerprint_sucesso('ttqRdOzmGvCSpuag', d),
                         'URCdX5Y4D4YW1afIdlbdRMx+FDAt//jdvFJreGUZC98n2xepsGcAlgrWUPQj4n+lcWS04Dm9kNGY4G1N82pPeQ==')
        # zeros à esquerda no período e no tid não mudam a assinatura
        self.assertEqual(v4.fingerprint_sucesso('ttqRdOzmGvCSpuag', {**d, 'merchantRespCP': '0000987',
                                                                      'merchantRespTid': '00000026'}),
                         v4.fingerprint_sucesso('ttqRdOzmGvCSpuag', d))

    def test_resposta_erro(self):
        d = {'messageType': '6', 'merchantRespMerchantRef': 'R20200517185116',
             'merchantRespMerchantSession': 'S20200517185116', 'merchantRespMessageID': '15CJ2GtDCOy5578q64a1',
             'merchantRespErrorCode': '2', 'merchantRespErrorDescription': 'A autenticacao 3D Secure falhou.',
             'merchantRespErrorDetail': 'VEREnrollRes', 'merchantRespTimeStamp': '2020-05-17 18:51:41',
             'merchantRespAdditionalErrorMessage': 'PASSWORD ERRADO. FAVOR TENTAR NOVAMENTE.'}
        self.assertEqual(v4.fingerprint_erro('ttqRdOzmGvCSpuag', d),
                         'AYpWZLwKhnwXtfDAW4l15D9oM3fVtJOwZkKt89djbAZP+L2FW/hPuHeyMQQVmX16xvmoSzRptSNcM5AGy0Y93w==')

    def test_auxiliares(self):
        self.assertEqual(v4._milesimos('5432.98'), '5432980')
        self.assertEqual(v4._milesimos('500'), '500000')
        self.assertEqual(v4._long('00100'), '100')
        self.assertEqual(v4._long(''), '')
        self.assertEqual(v4.montante(Decimal('1250.50')), 1251)
        self.assertEqual(v4.montante(Decimal('1250.49')), 1250)


def _utilizador(username='cliente', pais='CV', concelho='PR', cidade='', telefone='+238 991 12 23',
                morada='Achada Santo António, Rua 1', dias=90):
    user = User.objects.create_user(username=username, email=f'{username}@exemplo.cv', password='x-Teste-123!')
    user.date_joined = timezone.now() - timedelta(days=dias)
    user.save(update_fields=['date_joined'])
    return Utilizador.objects.create(user=user, telefone=telefone, morada=morada, pais=pais, concelho=concelho,
                                     cidade=cidade)


def _resposta_sucesso(tx, chave=CHAVE, **mudar):
    d = {'messageType': '8', 'merchantRespCP': '1234', 'merchantRespTid': '00000056',
         'merchantRespMerchantRef': tx.ref, 'merchantRespMerchantSession': tx.sessao,
         'merchantRespPurchaseAmount': f'{tx.montante}.00', 'merchantRespMessageID': 'MSG0000000000000001',
         'merchantRespPan': '************1112', 'merchantResp': 'C', 'merchantRespTimeStamp': '2026-11-11 10:00:00',
         'merchantRespReferenceNumber': '', 'merchantRespEntityCode': '', 'merchantRespClientReceipt': '',
         'merchantRespAdditionalErrorMessage': '', 'merchantRespReloadCode': '', 'languageMessages': 'pt',
         'resultFingerPrintVersion': '1'}
    d.update(mudar)
    d['resultFingerPrint'] = v4.fingerprint_sucesso(chave, d)
    return d


def _resposta_erro(tx, chave=CHAVE):
    d = {'messageType': '6', 'merchantRespMerchantRef': tx.ref, 'merchantRespMerchantSession': tx.sessao,
         'merchantRespMessageID': 'MSG0000000000000002', 'merchantRespErrorCode': '2',
         'merchantRespErrorDescription': 'A autenticacao 3D Secure falhou.', 'merchantRespErrorDetail': 'OTP',
         'merchantRespTimeStamp': '2026-11-11 10:01:00',
         'merchantRespAdditionalErrorMessage': 'Código de autenticação errado. Favor tentar novamente'}
    d['resultFingerPrint'] = v4.fingerprint_erro(chave, d)
    return d


@override_settings(**CRED)
class Fluxo(TestCase):

    def setUp(self):
        self.u = _utilizador()
        self.f = obter('vinti4')

    def _iniciar(self, valor='1500.00', referencia='fat-7-cartao-1'):
        inicio = self.f.iniciar(Cobranca(referencia=referencia, valor=Decimal(valor), descricao='Teste',
                                         pagador=self.u))
        return inicio, TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])

    def test_dados_3ds(self):
        d = v4.dados_3ds(self.u)
        self.assertEqual((d['billAddrCountry'], d['billAddrState'], d['billAddrCity']), ('132', 'PR', 'Praia'))
        self.assertEqual(d['billAddrPostCode'], '0000')
        self.assertEqual(d['billAddrLine2'], d['billAddrLine1'])
        self.assertEqual(d['mobilePhone'], {'cc': '238', 'subscriber': '9911223'})
        self.assertEqual(d['acctInfo']['chAccAgeInd'], '05')
        self.assertEqual(d['acctInfo']['suspiciousAccActivity'], '01')
        fora = _utilizador('emigrante', pais='PT', concelho='', cidade='Lisboa', telefone='912345678', dias=10)
        d = v4.dados_3ds(fora)
        self.assertEqual((d['billAddrCountry'], d['billAddrCity']), ('620', 'Lisboa'))
        self.assertNotIn('billAddrState', d)
        self.assertEqual(d['mobilePhone']['cc'], '351')
        self.assertEqual(d['acctInfo']['chAccAgeInd'], '03')

    def test_iniciar(self):
        inicio, tx = self._iniciar('1250.50')
        c = inicio.campos
        self.assertEqual(inicio.estado, 'redirecionar')
        self.assertEqual(inicio.metodo_http, 'POST')
        self.assertTrue(inicio.url.startswith(CRED['VINTI4_URL'] + '?FingerPrint='))
        self.assertEqual((c['amount'], c['currency'], c['transactionCode'], c['is3DSec']), ('1251', '132', '1', '1'))
        self.assertLessEqual(len(c['merchantRef']), 15)
        self.assertLessEqual(len(c['merchantSession']), 15)
        self.assertEqual(c['urlMerchantResponse'], 'https://api.exemplo.cv/app/pagamento/vinti4/resposta/')
        self.assertEqual(c['FingerPrint'], v4.fingerprint_pedido(CHAVE, c['TimeStamp'], 1251, c['merchantRef'],
                                                                 c['merchantSession'], '90051'))
        self.assertNotIn(CHAVE, str(c) + inicio.url)                 # a chave nunca sai do servidor
        self.assertEqual((tx.estado, tx.montante, tx.valor, tx.loja_id), ('iniciada', 1251, Decimal('1250.50'), None))

    def test_iniciar_recusa(self):
        with self.assertRaises(ErroPagamento):
            self._iniciar('1.00')
        self.u.concelho = ''
        self.u.save()
        with self.assertRaises(DadosClienteEmFalta) as e:
            self._iniciar()
        self.assertEqual(e.exception.campos, ['cidade'])
        with override_settings(VINTI4_POS_ID=''):
            self.u.concelho = 'SV'
            self.u.save()
            with self.assertRaises(ErroPagamento):
                self._iniciar()
        self.assertEqual(TransacaoVinti4.objects.count(), 0)

    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago', 'tipo': 'fatura', 'id': 7,
                                                                   'destino': '/x'})
    def test_sucesso(self, confirmar):
        _, tx = self._iniciar()
        self.assertEqual(v4.processar_resposta(_resposta_sucesso(tx)).pk, tx.pk)
        tx.refresh_from_db()
        self.assertEqual((tx.estado, tx.efeito, tx.periodo, tx.tid, tx.pan), ('paga', 'pago', '1234', '56', '************1112'))
        conf = confirmar.call_args[0][1]
        self.assertEqual((conf.referencia, conf.transacao, conf.valor, conf.moeda),
                         ('fat-7-cartao-1', 'v4_1234-56', Decimal('1500.00'), 'CVE'))
        v4.processar_resposta(_resposta_sucesso(tx))               # a mesma resposta outra vez
        self.assertEqual(confirmar.call_count, 1)
        c = self.f.confirmar_regresso({'ref': tx.ref})
        self.assertTrue(c.sucesso)
        self.assertEqual(c.transacao, 'v4_1234-56')

    @mock.patch('app.pagamentos.servico.confirmar')
    def test_assinatura_falsa_nao_muda_nada(self, confirmar):
        _, tx = self._iniciar()
        d = _resposta_sucesso(tx)
        d['merchantRespPurchaseAmount'] = '1.00'                     # alterado depois de assinado
        v4.processar_resposta(d)
        v4.processar_resposta(_resposta_sucesso(tx, chave='outra-chave'))
        v4.processar_resposta(_resposta_erro(tx, chave='outra-chave'))
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'iniciada')
        confirmar.assert_not_called()

    @mock.patch('app.pagamentos.servico.confirmar', side_effect=ErroPagamento('O valor pago não corresponde à fatura.'))
    def test_valor_diferente(self, confirmar):
        _, tx = self._iniciar()
        v4.processar_resposta(_resposta_sucesso(tx, merchantRespPurchaseAmount='999.00'))
        tx.refresh_from_db()
        self.assertEqual((tx.estado, tx.efeito), ('paga', 'erro'))
        self.assertEqual(confirmar.call_args[0][1].valor, Decimal('999'))
        with self.assertRaises(ErroPagamento):
            self.f.confirmar_regresso({'ref': tx.ref})

    @mock.patch('app.pagamentos.servico.confirmar')
    def test_merchant_resp_nao_c(self, confirmar):
        _, tx = self._iniciar()
        v4.processar_resposta(_resposta_sucesso(tx, merchantResp=''))
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'falhada')
        confirmar.assert_not_called()

    def test_erro(self):
        _, tx = self._iniciar()
        v4.processar_resposta(_resposta_erro(tx))
        tx.refresh_from_db()
        self.assertEqual((tx.estado, tx.erro_codigo), ('falhada', '2'))
        self.assertIn('Código de autenticação errado', tx.mensagem)
        with self.assertRaises(ErroPagamento) as e:
            self.f.confirmar_regresso({'ref': tx.ref})
        self.assertIn('Código de autenticação errado', str(e.exception))
        self.assertEqual(e.exception.destino_ref, 'fat-7-cartao-1')

    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago'})
    def test_cancelar_e_sucesso_depois(self, confirmar):
        _, tx = self._iniciar()
        v4.processar_resposta({'merchantRef': tx.ref, 'merchantSession': tx.sessao, 'UserCancelled': 'true'})
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'cancelada')
        v4.processar_resposta(_resposta_sucesso(tx))             # o dinheiro foi cobrado: vale
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'paga')
        v4.processar_resposta({'merchantRef': tx.ref, 'userCancelled': 'true'})    # não desfaz um pagamento
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'paga')

    def test_ref_desconhecido(self):
        self.assertIsNone(v4.processar_resposta({'merchantRespMerchantRef': 'BNAOEXISTE00000', 'messageType': '8'}))
        with self.assertRaises(ErroPagamento):
            self.f.confirmar_regresso({'ref': 'BNAOEXISTE00000'})

    def test_reembolsar(self):
        with self.assertRaises(ErroPagamento):
            self.f.reembolsar('v4_1-2', Decimal('10'))


@override_settings(**CRED)
class SemResposta(TestCase):
    """Plan Test 38–41: 8 minutos sem resposta → API de estado."""

    def setUp(self):
        self.u = _utilizador()

    def _tx(self, minutos=9, referencia='fat-7-cartao-1'):
        inicio = obter('vinti4').iniciar(Cobranca(referencia=referencia, valor=Decimal('1500'), descricao='T',
                                                  pagador=self.u))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(criada_em=timezone.now() - timedelta(minutes=minutos))
        return tx

    def test_sem_api_fica_por_confirmar(self):
        velha, nova = self._tx(9), self._tx(2)
        self.assertEqual(v4.rever_sem_resposta(), 1)
        velha.refresh_from_db()
        nova.refresh_from_db()
        self.assertEqual((velha.estado, nova.estado), ('por_confirmar', 'iniciada'))

    @override_settings(VINTI4_PORTAL_ID='1', VINTI4_PORTAL_PASSWORD='abc123')
    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago'})
    @mock.patch('app.pagamentos.vinti4.requests.post')
    def test_api(self, post, confirmar):
        paga, nao, recusa = self._tx(), self._tx(), self._tx()
        respostas = {
            paga.ref: {'result': True, 'msg': 'Consulta efetuado', 'transactionSuccess': True,
                       'transactionStatusDescription': 'C-SUCESSO'},
            nao.ref: {'result': True, 'msg': 'Consulta efetuado', 'transactionSuccess': False,
                      'transactionStatusDescription': 'E-ERRO'},
            recusa.ref: {'result': False, 'msg': 'Portal ID ou Password errado', 'transactionSuccess': False,
                         'transactionStatusDescription': ''},
        }

        def responder(url, auth, timeout, json):
            self.assertEqual(auth, ('1', 'abc123'))
            self.assertEqual((json['posID'], json['posAuthCode']), ('90051', CHAVE))
            r = mock.Mock()
            r.json.return_value = respostas[json['merchantRef']]
            return r
        post.side_effect = responder
        v4.rever_sem_resposta()
        for tx in (paga, nao, recusa):
            tx.refresh_from_db()
        self.assertEqual((paga.estado, paga.confirmada_por, paga.efeito), ('paga', 'estado', 'pago'))
        self.assertEqual(nao.estado, 'expirada')
        self.assertEqual(recusa.estado, 'por_confirmar')
        self.assertEqual(confirmar.call_count, 1)
        # a por confirmar volta a ser perguntada passados 10 minutos, até 12 vezes
        TransacaoVinti4.objects.filter(pk=recusa.pk).update(consultada_em=timezone.now() - timedelta(minutes=11))
        respostas[recusa.ref] = respostas[paga.ref]
        v4.rever_sem_resposta()
        recusa.refresh_from_db()
        self.assertEqual(recusa.estado, 'paga')


@override_settings(**CRED)
class Endpoints(TestCase):

    def setUp(self):
        self.u = _utilizador()

    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago', 'tipo': 'fatura', 'id': 7,
                                                                   'destino': '/loja/1/backoffice/subscricao'})
    def test_resposta_e_regresso(self, confirmar):
        inicio = obter('vinti4').iniciar(Cobranca(referencia='fat-7-cartao-1', valor=Decimal('1500'),
                                                  descricao='T', pagador=self.u))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        r = self.client.post('/app/pagamento/vinti4/resposta/', _resposta_sucesso(tx))      # form, sem CSRF
        self.assertEqual(r.status_code, 303)
        self.assertEqual(r['Location'], f'https://exemplo.cv/pagamento/callback?fornecedor=vinti4&ref={tx.ref}')
        r = self.client.post('/app/pagamento/regresso/', {'fornecedor': 'vinti4', 'ref': tx.ref},
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['destino'], '/loja/1/backoffice/subscricao')
        self.assertEqual(self.client.get('/app/pagamento/vinti4/resposta/').status_code, 405)

    def test_regresso_falhado_traz_caminho(self):
        tx = TransacaoVinti4.objects.create(ref='BTESTE00000001X', sessao='S1', referencia='enc-55-cartao-1',
                                            pos_id='90051', valor=Decimal('100'), montante=100, estado='cancelada')
        r = self.client.post('/app/pagamento/regresso/', {'fornecedor': 'vinti4', 'ref': tx.ref},
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual((r.json()['tipo'], r.json()['destino']), ('encomenda', '/encomendas/55'))


class Perfil(TestCase):

    def test_password_alterada(self):
        u = _utilizador()
        self.assertIsNone(u.password_alterada_em)
        u.user.last_login = timezone.now()
        u.user.save(update_fields=['last_login'])
        u.refresh_from_db()
        self.assertIsNone(u.password_alterada_em)
        u.user.set_password('Outra-Password-9')
        u.user.save()
        u.refresh_from_db()
        self.assertIsNotNone(u.password_alterada_em)

    def test_campos_morada(self):
        from .Serializers.UtilizadorSerializer import UtilizadorSerializer
        u = _utilizador()
        s = UtilizadorSerializer(u, data={'pais': 'cv', 'concelho': 'sv', 'codigo_postal': ' 7600 '}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        u.refresh_from_db()
        self.assertEqual((u.pais, u.concelho, u.codigo_postal), ('CV', 'SV', '7600'))
        s = UtilizadorSerializer(u, data={'pais': 'PT', 'cidade': '  Lisboa ', 'concelho': 'SV'}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        u.refresh_from_db()
        self.assertEqual((u.pais, u.concelho, u.cidade), ('PT', '', 'Lisboa'))
        self.assertFalse(UtilizadorSerializer(u, data={'concelho': 'XX'}, partial=True).is_valid())
        self.assertFalse(UtilizadorSerializer(u, data={'pais': 'ZZ'}, partial=True).is_valid())
        self.assertFalse(UtilizadorSerializer(u, data={'codigo_postal': '<script>'}, partial=True).is_valid())
