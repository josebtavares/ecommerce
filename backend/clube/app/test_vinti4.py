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
from .pagamentos.base import Cobranca, Confirmacao
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

    def test_erro_do_middleware_3ds_assinado_como_sucesso(self):
        """O middleware 3DS da SISP assina o messageType 6 com a fórmula de sucesso (resposta real, 2026-11-12)."""
        _, tx = self._iniciar()
        d = {'messageType': '6', 'merchantResp': 'C', 'merchantRespMerchantRef': tx.ref,
             'merchantRespMerchantSession': tx.sessao, 'merchantRespMessageID': 'S8zs59e0thSzZ3bBKDHC',
             'merchantRespErrorCode': '03', 'merchantRespErrorDetail': '', 'merchantRespCP': '', 'merchantRespTid': '',
             'merchantRespPan': '****', 'merchantRespPurchaseAmount': '1500', 'merchantRespTimeStamp': '2026-11-12 11:51:56',
             'merchantRespErrorDescription': 'There was an error while processing the operation',
             'merchantRespAdditionalErrorMessage': '', 'dcc': 'N'}
        d['resultFingerPrint'] = v4.fingerprint_sucesso(CHAVE, d)
        v4.processar_resposta(d)
        tx.refresh_from_db()
        self.assertEqual((tx.estado, tx.erro_codigo), ('falhada', '03'))
        # com outra chave continua a ser recusada
        _, tx2 = self._iniciar(referencia='fat-8-cartao-1')
        d2 = {**d, 'merchantRespMerchantRef': tx2.ref, 'merchantRespMerchantSession': tx2.sessao}
        d2['resultFingerPrint'] = v4.fingerprint_sucesso('outra-chave', d2)
        v4.processar_resposta(d2)
        tx2.refresh_from_db()
        self.assertEqual(tx2.estado, 'iniciada')

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


# ── fase 2: cobranças da Bendi (faturas de subscrição, comissões) pelo vinti4, vendas das lojas à parte ──

@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='simulado', PAGAMENTOS_FORNECEDOR_BENDI='vinti4')
class CobrancasBendi(TestCase):

    def setUp(self):
        self.u = _utilizador()

    def test_fornecedores_separados(self):
        from .pagamentos import ativo, ativo_bendi, bendi_cobra_a_serio, cobra_a_serio
        self.assertEqual(ativo().codigo, 'simulado')
        self.assertEqual(ativo_bendi().codigo, 'vinti4')
        self.assertFalse(cobra_a_serio())
        self.assertTrue(bendi_cobra_a_serio())
        with override_settings(PAGAMENTOS_FORNECEDOR_BENDI=''):
            self.assertEqual(ativo_bendi().codigo, 'simulado')       # por omissão, o mesmo das vendas

    def test_fatura_vai_ao_vinti4(self):
        from types import SimpleNamespace
        from .pagamentos import servico
        fatura = SimpleNamespace(id=31, estado='pendente', valor=Decimal('2500.00'), descricao='Plano Loja — 11/2026')
        inicio = servico.iniciar_fatura(fatura, self.u)
        self.assertEqual(inicio.estado, 'redirecionar')
        corpo = servico.para_frontend(inicio)
        self.assertEqual(corpo['redirecionar']['fornecedor'], 'vinti4')
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        self.assertIsNone(tx.loja_id)                    # credenciais da Bendi
        self.assertEqual(tx.pos_id, '90051')
        self.assertTrue(tx.referencia.startswith('fat-31-'))
        self.assertEqual(inicio.campos['amount'], '2500')

    def test_comissoes_vao_ao_vinti4(self):
        from datetime import date
        from types import SimpleNamespace
        from .pagamentos import servico
        c = SimpleNamespace(id=8, estado='pendente', valor=Decimal('730.40'), mes=date(2026, 10, 1),
                            loja=SimpleNamespace(nome='Loja X'))
        inicio = servico.iniciar_cobranca_comissoes(c, self.u)
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        self.assertTrue(tx.referencia.startswith('com-8-'))
        self.assertEqual(inicio.campos['amount'], '730')          # escudos inteiros (arredonda a metade para cima)

    def test_sem_dados_pede_os(self):
        from types import SimpleNamespace
        from .pagamentos import servico
        u = _utilizador('semdados', telefone='', concelho='')
        fatura = SimpleNamespace(id=32, estado='pendente', valor=Decimal('1000'), descricao='POS')
        with self.assertRaises(DadosClienteEmFalta) as ctx:
            servico.iniciar_fatura(fatura, u)
        corpo = servico.erro_para_frontend(ctx.exception)
        self.assertEqual(corpo['codigo'], 'dados_cliente')
        self.assertEqual(corpo['campos'], ['telefone', 'cidade'])
        self.assertFalse(TransacaoVinti4.objects.filter(referencia__startswith='fat-32-').exists())
        with self.assertRaises(ErroPagamento):                    # POS sem dono (nunca deve acontecer)
            servico.iniciar_fatura(fatura, None)


# ── fase 3: respostas guardadas, erros do comerciante (BT202108A), recibo, Admin → Pagamentos → Cartão ──

def _resposta_erro_comerciante(tx, chave=CHAVE):
    d = {'messageType': '6', 'merchantRespMerchantRef': tx.ref, 'merchantRespMerchantSession': tx.sessao,
         'merchantRespMessageID': 'MSG0000000000000003', 'merchantRespErrorCode': '1',
         'merchantRespErrorDescription': 'Erro nos dados', 'merchantRespErrorDetail': 'FingerPrint',
         'merchantRespTimeStamp': '2026-11-11 10:02:00',
         'merchantRespAdditionalErrorMessage': 'Dados do pedido inválidos. Corrigir e reenviar.'}
    d['resultFingerPrint'] = v4.fingerprint_erro(chave, d)
    return d


@override_settings(**CRED)
class Certificacao(TestCase):

    def setUp(self):
        self.u = _utilizador()
        self.f = obter('vinti4')

    def _iniciar(self, referencia='fat-7-cartao-1'):
        inicio = self.f.iniciar(Cobranca(referencia=referencia, valor=Decimal('1500'), descricao='Plano', pagador=self.u))
        return TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])

    def test_classificar_erros(self):
        self.assertTrue(v4.erro_do_comerciante('Dados do pedido inválidos. Corrigir e reenviar.'))
        self.assertTrue(v4.erro_do_comerciante('Falha na configuração.'))
        self.assertTrue(v4.erro_do_comerciante('Invalid order data. Fix and resend.'))
        self.assertFalse(v4.erro_do_comerciante('Saldo do cartão insuficiente'))
        self.assertFalse(v4.erro_do_comerciante('Código de autenticação errado. Favor tentar novamente'))
        self.assertFalse(v4.erro_do_comerciante(''))

    def test_erro_do_cliente_mostra_se_e_guarda(self):
        tx = self._iniciar()
        v4.processar_resposta(_resposta_erro(tx))
        tx.refresh_from_db()
        self.assertIn('Código de autenticação errado', tx.mensagem)
        self.assertEqual(len(tx.respostas), 1)
        self.assertEqual(tx.respostas[0]['origem'], 'resposta')
        self.assertEqual(tx.respostas[0]['campos']['merchantRespErrorCode'], '2')

    @mock.patch('app.Views.notificacaoView.notificar_admins')
    def test_erro_do_comerciante_avisa_a_bendi(self, notificar):
        tx = self._iniciar()
        v4.processar_resposta(_resposta_erro_comerciante(tx))
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'falhada')
        self.assertEqual(tx.mensagem, v4.MENSAGEM_ERRO_COMERCIANTE)
        self.assertTrue(tx.erro.startswith('[comerciante] Dados do pedido'))
        notificar.assert_called_once()
        self.assertEqual(notificar.call_args.kwargs['tipo'], 'pagamento_erro')

    def test_respostas_guardadas_ate_ao_limite(self):
        tx = self._iniciar()
        for _ in range(v4.MAX_RESPOSTAS + 3):
            v4.processar_resposta({'merchantRef': tx.ref, 'UserCancelled': 'true', 'x': 'y' * 1000})
        tx.refresh_from_db()
        self.assertEqual(len(tx.respostas), v4.MAX_RESPOSTAS)
        self.assertEqual(len(tx.respostas[-1]['campos']['x']), 400)

    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago'})
    def test_recibo_do_cartao(self, _confirmar):
        from types import SimpleNamespace
        from .utils import documentos
        tx = self._iniciar('fat-77-cartao-1')
        v4.processar_resposta(_resposta_sucesso(tx, dcc='Y', dccAmount='16.30', dccCurrency='USD', dccMarkup='3',
                                                dccRate='92.65882'))
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'paga')
        linhas = []

        class P:
            def seccao(self, t): linhas.append(('S', t))
            def linha(self, r, v, destaque=False): linhas.append((r, str(v)))
            def texto(self, t): linhas.append(('T', t))
        self.assertTrue(documentos._cartao_vinti4(P(), 'fat', 77))
        d = dict(l for l in linhas if l[0] not in ('S', 'T'))
        self.assertEqual(d['Referência do pagamento'], tx.ref)
        self.assertEqual(d['Nº da transação'], '1234-56')
        self.assertEqual(d['Cartão'], '************1112')
        self.assertEqual(d['Loja virtual'], 'https://exemplo.cv')
        self.assertEqual(d['[x] TOTAL'], '16.30 USD')
        self.assertIn(('T', 'Exchange rate provided by Banco de Cabo Verde.'), linhas)
        self.assertFalse(documentos._cartao_vinti4(P(), 'fat', 78))
        # o PDF inteiro gera-se
        f = SimpleNamespace(id=77, pos_id=None, alvo=SimpleNamespace(nome='Loja', nif=''), descricao='Plano',
                            periodo_inicio=timezone.now().date(), periodo_fim=timezone.now().date() + timedelta(days=30),
                            paga_em=timezone.now(), metodo='online', get_metodo_display=lambda: 'Online', valor=Decimal('1500'))
        with mock.patch('app.utils.subscricoes.nome_alvo', return_value='Loja'):
            self.assertTrue(documentos.pdf_comprovativo_subscricao(f).startswith(b'%PDF'))

    def test_admin_lista_e_ficha(self):
        tx = self._iniciar()
        v4.processar_resposta(_resposta_erro(tx))
        admin = _utilizador('adminv4')
        admin.user.is_staff = True
        admin.user.save(update_fields=['is_staff'])
        papel = next(r for r, perms in Utilizador.PERMISSOES_ADMIN.items() if 'gerir_pagamentos' in perms)
        admin.role_admin = papel
        admin.save(update_fields=['role_admin'])
        from rest_framework.test import APIClient
        api = APIClient()
        api.force_authenticate(admin.user)
        r = api.get('/app/admin/pagamentos/vinti4/', {'estado': 'falhada'})
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.assertEqual(r.json()['count'], 1)
        self.assertEqual(r.json()['results'][0]['tipo'], 'fatura')
        self.assertNotIn('respostas', r.json()['results'][0])
        r = api.get(f'/app/admin/pagamentos/vinti4/{tx.id}/')
        self.assertEqual(len(r.json()['respostas']), 1)
        self.assertEqual(r.json()['destino'], '')               # a fatura 7 não existe neste teste
        cliente = _utilizador('naoadmin')
        api.force_authenticate(cliente.user)
        self.assertEqual(api.get('/app/admin/pagamentos/vinti4/').status_code, 403)


# ── fase 4: vendas das lojas com o contrato vinti4 de cada uma ──

CHAVE_LOJA = 'LojaChave12345'


def _loja(dono, estado='ativa', pos_id='90099', portal=None):
    from .models import AdesaoVinti4, Loja, UtilizadorLoja
    from .utils import vinti4 as adesoes
    loja = Loja.objects.create(dono=dono, nome=f'Loja {dono.user.username}', slug=f'loja-{dono.user.username}',
                               categoria='moda')
    UtilizadorLoja.objects.get_or_create(loja=loja, utilizador=dono, defaults={'role': 'dono', 'ativo': True})
    AdesaoVinti4.objects.create(loja=loja, estado=estado, pos_id=pos_id, merchant_id='M1',
                                chave_cifrada=adesoes.cifrar(CHAVE_LOJA),
                                portal_id=(portal or ('', ''))[0],
                                portal_password_cifrada=adesoes.cifrar(portal[1]) if portal else '')
    return loja


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4', PAGAMENTOS_FORNECEDOR_BENDI='vinti4')
class VendasDasLojas(TestCase):

    def setUp(self):
        self.dono = _utilizador('dono')
        self.cliente = _utilizador('compra')
        self.f = obter('vinti4')

    def test_credenciais_da_loja(self):
        loja = _loja(self.dono)
        inicio = self.f.iniciar(Cobranca(referencia='enc-5-cartao-1', valor=Decimal('2300'), descricao='Encomenda #5',
                                         pagador=self.cliente, loja=loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        self.assertEqual((tx.loja_id, tx.pos_id, inicio.campos['posID']), (loja.id, '90099', '90099'))
        # a assinatura é feita com a chave da loja, não com a da Bendi
        self.assertEqual(inicio.campos['FingerPrint'], v4.fingerprint_pedido(
            CHAVE_LOJA, inicio.campos['TimeStamp'], 2300, tx.ref, tx.sessao, '90099'))
        # e a resposta valida-se com a chave da loja
        with mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago'}):
            v4.processar_resposta(_resposta_sucesso(tx, chave=CHAVE_LOJA))
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'paga')

    def test_mesmo_pos_que_a_bendi(self):
        """A CV PRIME STORE (loja) e a Bendi usam o mesmo POS ID: cada transacção tem a sua referência."""
        loja = _loja(self.dono, pos_id=CRED['VINTI4_POS_ID'])
        a = self.f.iniciar(Cobranca(referencia='enc-6-cartao-1', valor=Decimal('500'), descricao='E', pagador=self.cliente, loja=loja))
        b = self.f.iniciar(Cobranca(referencia='fat-6-cartao-1', valor=Decimal('500'), descricao='F', pagador=self.dono))
        self.assertNotEqual(a.campos['merchantRef'], b.campos['merchantRef'])
        self.assertEqual(a.campos['posID'], b.campos['posID'])

    def test_sem_adesao_ou_suspensa_recusa(self):
        loja = _loja(self.dono, estado='suspensa')
        with self.assertRaises(ErroPagamento):
            self.f.iniciar(Cobranca(referencia='enc-7-cartao-1', valor=Decimal('500'), descricao='E', pagador=self.cliente, loja=loja))

    def test_em_testes_so_a_equipa(self):
        from .utils.banco import online_suspenso
        loja = _loja(self.dono, estado='teste')
        self.assertTrue(online_suspenso(loja))                    # o público não vê o cartão
        self.assertTrue(online_suspenso(loja, self.cliente))
        self.assertFalse(online_suspenso(loja, self.dono))        # a equipa experimenta
        loja.vinti4.estado = 'ativa'
        loja.vinti4.save(update_fields=['estado'])
        self.assertFalse(online_suspenso(loja))
        loja.vinti4.estado = 'por_validar'
        loja.vinti4.save(update_fields=['estado'])
        self.assertTrue(online_suspenso(loja, self.dono))
        with override_settings(PAGAMENTOS_FORNECEDOR='simulado'):
            self.assertFalse(online_suspenso(loja))               # simulado: nunca se aplica

    def test_reembolso_e_estorno_da_loja(self):
        with self.assertRaises(ErroPagamento) as e:
            self.f.reembolsar('v4_1-2', Decimal('100'))
        self.assertTrue(e.exception.estorno_loja)
        from types import SimpleNamespace
        from .utils import devolucoes as dev
        with mock.patch.object(dev, 'pagamento_de', return_value=SimpleNamespace(fornecedor='vinti4')):
            self.assertEqual(dev.como_devolve(None), 'cartao')
        with mock.patch.object(dev, 'pagamento_de', return_value=SimpleNamespace(fornecedor='simulado', metodo_id=None,
                                                                                  referencia_transacao='x')):
            self.assertEqual(dev.como_devolve(None), 'dinheiro')

    @mock.patch('app.pagamentos.vinti4.requests.post')
    def test_api_de_estado_com_o_portal_da_loja(self, post):
        loja = _loja(self.dono, portal=('portal-loja', 'segredo123'))
        inicio = self.f.iniciar(Cobranca(referencia='enc-8-cartao-1', valor=Decimal('900'), descricao='E', pagador=self.cliente, loja=loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        post.return_value.json.return_value = {'result': True, 'transactionSuccess': False}
        self.assertEqual(v4.consultar_estado(tx), 'nao_paga')
        kw = post.call_args.kwargs
        self.assertEqual(kw['auth'], ('portal-loja', 'segredo123'))
        self.assertEqual(kw['json']['posID'], '90099')
        self.assertEqual(kw['json']['posAuthCode'], CHAVE_LOJA)
        # sem portal: não pergunta
        loja2 = _loja(_utilizador('dono2'), pos_id='90100')
        inicio = self.f.iniciar(Cobranca(referencia='enc-9-cartao-1', valor=Decimal('900'), descricao='E', pagador=self.cliente, loja=loja2))
        post.reset_mock()
        self.assertIsNone(v4.consultar_estado(TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])))
        post.assert_not_called()

    def test_guardar_portal(self):
        from types import SimpleNamespace
        from .utils import vinti4 as adesoes
        loja = _loja(self.dono)
        pedido = SimpleNamespace(user=self.dono.user)
        _, erros = adesoes.guardar_portal(pedido, loja, 'tem espaço', 'x')
        self.assertIn('portal_id', erros)
        self.assertIn('portal_password', erros)
        a, erros = adesoes.guardar_portal(pedido, loja, 'P123', 'segredo-123')
        self.assertIsNone(erros)
        self.assertEqual(adesoes.portal(loja), ('P123', 'segredo-123'))
        self.assertNotIn('segredo', a.portal_password_cifrada)
        self.assertEqual(a.estado, 'ativa')                       # não volta a pedir validação
        adesoes.guardar_portal(pedido, loja, '', '')
        self.assertIsNone(adesoes.portal(loja))


# ── ficheiro de reconciliação VBVT (Plan Test 36–37) e "Perguntar à SISP" (39–41) ──

MID = '9000058'


def _vbvt(detalhes, data='20261112', seq=1, ant='00000000', seq_ant=0, mid=MID, trailer=None, versao='01', moeda='132'):
    linhas = [f'0VBVT{versao}{mid:0>15}{data}{seq:03d}{ant}{seq_ant:03d}{moeda}'] + list(detalhes)
    linhas.append(f'9{(len(detalhes) if trailer is None else trailer):08d}')
    return ('\r\n'.join(linhas) + '\r\n').encode('latin-1')


def _compra(ref, valor, rt='0', comissao=0, cp=987, tid=26, cartao='visa', pan='************3101'):
    return (f'1{ref:<20}{"MSG" + ref:<20}{rt}20261111153000{cp:04d}{tid:08d}{pan:<16}{int(valor * 100):013d}'
            f'{int(comissao * 100):013d}{cartao:<5}')


def _estorno(ref, original, valor, rt='0'):
    return (f'2{ref:<20}{"EST" + ref:<20}{rt}20261111160000{988:04d}{30:08d}{int(valor * 100):013d}'
            f'{"************3101":<16}{original:<20}{987:04d}{26:08d}{0:013d}{"visa":<5}')


def _admin_api(nome):
    admin = _utilizador(nome)
    admin.user.is_staff = True
    admin.user.save(update_fields=['is_staff'])
    admin.role_admin = next(r for r, perms in Utilizador.PERMISSOES_ADMIN.items() if 'gerir_pagamentos' in perms)
    admin.save(update_fields=['role_admin'])
    from rest_framework.test import APIClient
    api = APIClient()
    api.force_authenticate(admin.user)
    return api


@override_settings(**CRED, VINTI4_MERCHANT_ID=MID)
class ReconciliacaoVBVT(TestCase):

    def setUp(self):
        self.u = _utilizador()

    def _tx(self, estado='paga', valor=1500):
        inicio = obter('vinti4').iniciar(Cobranca(referencia='fat-7-cartao-1', valor=Decimal(valor), descricao='T',
                                                  pagador=self.u))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado=estado)
        tx.refresh_from_db()
        return tx

    def test_ler_e_reconciliar(self):
        from .pagamentos import vbvt
        ok, dif, so_sisp, so_ca, recusada = (self._tx(), self._tx(), self._tx('por_confirmar'), self._tx(),
                                             self._tx('falhada'))
        f = vbvt.processar(_vbvt([
            _compra(ok.ref, 1500, comissao=Decimal('22.50')), _compra(dif.ref, 1400), _compra(so_sisp.ref, 1500),
            _compra(so_ca.ref, 1500, rt='2'), _compra(recusada.ref, 1500, rt='2'), _compra('XNAOENOSSA', 900),
            _estorno('BEST000000001', ok.ref, 1500),
        ]), nome='VBVT_20261112.txt', utilizador=self.u.user)
        self.assertEqual(f.estado, 'aplicado', f.erros)
        res = {l['ref']: l['resultado'] for l in f.linhas if l['tipo'] == 'compra'}
        self.assertEqual(res, {ok.ref: 'ok', dif.ref: 'valor_diferente', so_sisp.ref: 'paga_so_na_sisp',
                               so_ca.ref: 'paga_so_ca', recusada.ref: 'recusada', 'XNAOENOSSA': 'desconhecida'})
        self.assertEqual(f.linhas[-1]['resultado'], 'estorno')
        self.assertEqual(f.resumo['problemas'], 4)
        self.assertEqual((f.resumo['total_compras'], f.resumo['total_estornos']), ('5300.00', '1500.00'))
        ok.refresh_from_db()
        so_sisp.refresh_from_db()
        self.assertIsNotNone(ok.reconciliada_em)
        self.assertIsNotNone(ok.estornada_em)
        self.assertEqual((ok.comissao_sisp, ok.tipo_cartao), (Decimal('22.50'), 'visa'))
        self.assertEqual(so_sisp.estado, 'por_confirmar')          # o ficheiro nunca dá nada como pago
        self.assertIsNone(so_sisp.reconciliada_em)
        self.assertIn('Diferenças', vbvt.relatorio(f))

    def test_sequencia(self):
        from .pagamentos import vbvt
        conteudo = _vbvt([], data='20261112', seq=1)
        self.assertEqual(vbvt.processar(conteudo).estado, 'aplicado')
        repetido = vbvt.processar(conteudo)
        self.assertEqual(repetido.estado, 'rejeitado')
        self.assertIn('já foi processado', repetido.erros[0]['erro'])
        # o seguinte certo
        self.assertEqual(vbvt.processar(_vbvt([], data='20261113', seq=1, ant='20261112', seq_ant=1)).estado, 'aplicado')
        # falta o de dia 14: rejeitado, a não ser que o admin o aceite assim
        salto = _vbvt([], data='20261115', seq=1, ant='20261114', seq_ant=1)
        f = vbvt.processar(salto)
        self.assertEqual(f.estado, 'rejeitado')
        self.assertIn('Sequência', f.erros[0]['erro'])
        f = vbvt.processar(salto, forcar=True)
        self.assertEqual((f.estado, f.forcado, len(f.avisos)), ('aplicado', True, 1))
        # mesma data e sequência com outro conteúdo
        f = vbvt.processar(_vbvt([_compra('BX', 10)], data='20261115', seq=1, ant='20261113', seq_ant=1))
        self.assertEqual(f.estado, 'rejeitado')

    def test_erros_de_estrutura(self):
        from .pagamentos import vbvt
        casos = {
            'trailer': _vbvt([_compra('BA', 10)], trailer=3),
            'numérico': _vbvt([_compra('BA', 10).replace('0987', '09X7')]),
            'VBVT': _vbvt([]).replace(b'VBVT', b'XXXX'),
            'Versão': _vbvt([], versao='02'),
            'Moeda': _vbvt([], moeda='978'),
            'desconhecido': _vbvt([], mid='111'),
            'Falta o trailer': _vbvt([]).rsplit(b'9', 1)[0],
        }
        for palavra, conteudo in casos.items():
            f = vbvt.processar(conteudo)
            self.assertEqual(f.estado, 'rejeitado', palavra)
            self.assertTrue(any(palavra.lower() in e['erro'].lower() for e in f.erros), (palavra, f.erros))
        self.assertFalse(TransacaoVinti4.objects.filter(reconciliada_em__isnull=False).exists())
        self.assertEqual(vbvt.processar(b'').erros[0]['erro'], 'O ficheiro está vazio.')

    def test_ficheiro_de_uma_loja(self):
        from .models import AdesaoVinti4
        from .pagamentos import vbvt
        loja = _loja(_utilizador('donovbvt'))
        AdesaoVinti4.objects.filter(loja=loja).update(merchant_id='000000000777')
        f = vbvt.processar(_vbvt([], mid='777'))
        self.assertEqual((f.estado, f.loja_id, f.merchant_id), ('aplicado', loja.id, '777'))

    def test_endpoints_vbvt(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        tx = self._tx()
        api = _admin_api('adminvbvt')
        r = api.post('/app/admin/pagamentos/vbvt/',
                     {'ficheiro': SimpleUploadedFile('VBVT.txt', _vbvt([_compra(tx.ref, 1500)]))}, format='multipart')
        self.assertEqual(r.status_code, 201, r.content[:300])
        self.assertEqual(r.json()['estado'], 'aplicado')
        self.assertIn('Confere: 1', r.json()['relatorio'])
        lista = api.get('/app/admin/pagamentos/vbvt/').json()
        self.assertEqual((lista['count'], lista['merchant_id_bendi']), (1, True))
        self.assertEqual(api.get(f'/app/admin/pagamentos/vbvt/{r.json()["id"]}/').status_code, 200)
        self.assertEqual(api.get('/app/admin/pagamentos/vinti4/', {'reconciliacao': 'falta'}).json()['count'], 0)
        api.force_authenticate(_utilizador('naoadminvbvt').user)
        self.assertEqual(api.get('/app/admin/pagamentos/vbvt/').status_code, 403)


@override_settings(**CRED)
class PerguntarASisp(TestCase):
    """Admin → "Perguntar à SISP" (Plan Test 39–41)."""

    def setUp(self):
        self.u = _utilizador()

    def _tx(self, minutos=9):
        self.n = getattr(self, 'n', 6) + 1          # uma fatura por transacção (só uma a decorrer de cada vez)
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'fat-{self.n}-cartao-1', valor=Decimal('1500'),
                                                  descricao='T', pagador=self.u))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(criada_em=timezone.now() - timedelta(minutes=minutos))
        return tx

    def test_sem_api(self):
        with self.assertRaises(ErroPagamento):
            v4.consultar_agora(self._tx().id)

    @override_settings(VINTI4_PORTAL_ID='1', VINTI4_PORTAL_PASSWORD='abc123')
    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago'})
    @mock.patch('app.pagamentos.vinti4.requests.post')
    def test_respostas(self, post, confirmar):
        def resposta(corpo):
            r = mock.Mock()
            r.json.return_value = corpo
            return r
        sucesso = {'result': True, 'msg': 'Consulta efetuado', 'transactionSuccess': True,
                   'transactionStatusDescription': 'C-SUCESSO'}
        erro = {'result': True, 'msg': 'Consulta efetuado', 'transactionSuccess': False,
                'transactionStatusDescription': 'E-ERRO'}
        login = {'result': False, 'msg': 'Portal ID ou Password errado', 'transactionSuccess': False,
                 'transactionStatusDescription': ''}
        # 39: login errado → nada muda, fica registado
        post.return_value = resposta(login)
        tx, resultado, corpo = v4.consultar_agora(self._tx().id)
        self.assertEqual((resultado, tx.estado, tx.respostas[-1]['campos']['msg']), (None, 'iniciada', login['msg']))
        # 41: não paga — há menos de 8 minutos não mexe; depois passa a sem resposta
        post.return_value = resposta(erro)
        nova = self._tx(minutos=2)
        self.assertEqual(v4.consultar_agora(nova.id)[0].estado, 'iniciada')
        self.assertEqual(v4.consultar_agora(tx.id)[0].estado, 'expirada')
        # 40: paga → aplica o pagamento uma vez; perguntar outra vez só regista
        post.return_value = resposta(sucesso)
        paga = self._tx()
        tx2, resultado, _ = v4.consultar_agora(paga.id)
        self.assertEqual((resultado, tx2.estado, tx2.confirmada_por), ('paga', 'paga', 'estado'))
        v4.consultar_agora(paga.id)
        self.assertEqual(confirmar.call_count, 1)
        self.assertEqual(len(TransacaoVinti4.objects.get(pk=paga.pk).respostas), 2)
        # endpoint
        api = _admin_api('adminconsulta')
        r = api.post(f'/app/admin/pagamentos/vinti4/{paga.id}/consultar/')
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.assertEqual((r.json()['resultado'], r.json()['transacao']['estado']), ('paga', 'paga'))
        api.force_authenticate(_utilizador('naoadmin2').user)
        self.assertEqual(api.post(f'/app/admin/pagamentos/vinti4/{paga.id}/consultar/').status_code, 403)


@override_settings(**CRED, VINTI4_MERCHANT_ID=MID)
class TempoRealCartao(TestCase):
    """O admin vê as idas à SISP mudar sem recarregar; o cliente sem resposta fica à espera e a página volta a perguntar."""

    def setUp(self):
        self.u = _utilizador()

    def _tx(self):
        inicio = obter('vinti4').iniciar(Cobranca(referencia='fat-7-cartao-1', valor=Decimal('1500'), descricao='T',
                                                  pagador=self.u))
        return TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])

    def test_avisos_do_painel(self):
        from .pagamentos import vbvt
        with mock.patch('app.utils.tempo_real_painel.emitir') as emitir:
            tx = self._tx()
            self.assertEqual([c.args[0] for c in emitir.call_args_list], ['cartao'])        # criada
            emitir.reset_mock()
            tx.respostas = [{'x': 1}]
            tx.save(update_fields=['respostas'])                                              # só a resposta: não avisa
            emitir.assert_not_called()
            v4.processar_resposta({'merchantRef': tx.ref, 'merchantSession': tx.sessao, 'UserCancelled': 'true'})           # cancelada: avisa
            self.assertEqual([c.args[0] for c in emitir.call_args_list], ['cartao'])
            emitir.reset_mock()
            TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga')
            vbvt.processar(_vbvt([_compra(tx.ref, 1500), _compra('XOUTRA', 10)]))             # um aviso pelo ficheiro
            self.assertEqual([c.args[0] for c in emitir.call_args_list], ['vbvt'])

    def test_regresso_pendente(self):
        from rest_framework.test import APIClient
        tx = self._tx()
        api = APIClient()
        r = api.post('/app/pagamento/regresso/', {'fornecedor': 'vinti4', 'ref': tx.ref}, format='json')
        self.assertEqual((r.status_code, r.json().get('codigo')), (400, 'pendente'))
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='cancelada')
        r = api.post('/app/pagamento/regresso/', {'fornecedor': 'vinti4', 'ref': tx.ref}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertNotIn('codigo', r.json())


# ── backoffice da loja → Pagamentos (Views/lojaCartaoView.py) e o VBVT separado por comerciante ──

@override_settings(**CRED, VINTI4_MERCHANT_ID=MID, PAGAMENTOS_FORNECEDOR='vinti4', PAGAMENTOS_FORNECEDOR_BENDI='vinti4')
class PagamentosDaLoja(TestCase):

    def setUp(self):
        from rest_framework.test import APIClient
        from .models import AdesaoVinti4
        self.dono = _utilizador('donoa')
        self.loja = _loja(self.dono)
        self.outro = _utilizador('donob')
        self.outra = _loja(self.outro, pos_id='90077')
        AdesaoVinti4.objects.filter(loja=self.loja).update(merchant_id='9000101')
        AdesaoVinti4.objects.filter(loja=self.outra).update(merchant_id='9000202')
        self.cliente = _utilizador('comprador')
        self.f = obter('vinti4')
        self.api = APIClient()
        self.api.force_authenticate(self.dono.user)

    def _tx(self, loja=None, referencia='enc-5-cartao-1', estado='paga', valor=2300):
        inicio = self.f.iniciar(Cobranca(referencia=referencia, valor=Decimal(valor), descricao='Compra',
                                         pagador=self.cliente, loja=loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado=estado)
        tx.refresh_from_db()
        return tx

    def _url(self, resto='', loja=None):
        return f'/app/loja/{(loja or self.loja).id}/cartao/{resto}'

    def test_so_ve_as_suas(self):
        minha = self._tx(self.loja)
        self._tx(self.outra)
        self._tx(None, referencia='fat-7-cartao-1')                     # mensalidade da Bendi
        r = self.api.get(self._url())
        self.assertEqual(r.status_code, 200, r.content[:200])
        d = r.json()
        self.assertEqual([t['id'] for t in d['results']], [minha.id])
        self.assertNotIn('lojas', d)                                     # a lista de lojas é só do admin
        self.assertEqual(d['totais']['pagas'], 1)
        self.assertEqual(d['totais']['valor_pago'], '2300.00')
        self.assertTrue(d['contrato']['merchant_id'])
        # a ficha, o CSV e o "Perguntar à SISP" de outra loja dão 404 / 403
        alheia = TransacaoVinti4.objects.exclude(loja=self.loja).first()
        self.assertEqual(self.api.get(self._url(f'{alheia.id}/')).status_code, 404)
        self.assertEqual(self.api.post(self._url(f'{alheia.id}/consultar/')).status_code, 404)
        self.assertEqual(self.api.get(self._url(loja=self.outra)).status_code, 403)
        csv = self.api.get(self._url('csv/'))
        self.assertEqual(csv.status_code, 200)
        self.assertIn(minha.ref, csv.content.decode('utf-8'))
        self.assertNotIn(alheia.ref, csv.content.decode('utf-8'))
        ficha = self.api.get(self._url(f'{minha.id}/')).json()
        self.assertEqual(ficha['destino'], f'/loja/{self.loja.id}/backoffice/encomendas/5')

    def test_so_o_dono(self):
        from rest_framework.test import APIClient
        from .models import UtilizadorLoja
        gestor = _utilizador('gestora')
        UtilizadorLoja.objects.create(loja=self.loja, utilizador=gestor, role='gestor', ativo=True)
        api = APIClient()
        api.force_authenticate(gestor.user)
        self.assertEqual(api.get(self._url()).status_code, 403)
        self.assertEqual(api.get(self._url('vbvt/')).status_code, 403)

    def test_filtros_e_contagens(self):
        paga = self._tx(self.loja)
        self._tx(self.loja, estado='por_confirmar')
        self._tx(self.loja, referencia='mar-3-cartao-1', estado='falhada')
        d = self.api.get(self._url(), {'estado': 'paga'}).json()
        self.assertEqual([t['id'] for t in d['results']], [paga.id])
        # as contagens dos botões não dependem do estado escolhido
        self.assertEqual({e['valor']: e['n'] for e in d['estados']}['falhada'], 1)
        self.assertEqual(d['totais']['por_confirmar'], 1)
        self.assertEqual(self.api.get(self._url(), {'tipo': 'marcacao'}).json()['count'], 1)
        self.assertEqual(self.api.get(self._url(), {'reconciliacao': 'falta'}).json()['count'], 1)
        self.assertEqual(self.api.get(self._url(), {'reconciliacao': 'feita'}).json()['count'], 0)
        self.assertEqual(self.api.get(self._url(), {'q': paga.ref}).json()['count'], 1)
        hoje = timezone.localdate().isoformat()
        self.assertEqual(self.api.get(self._url(), {'de': hoje, 'ate': hoje}).json()['count'], 3)
        for mau in ({'estado': 'xpto'}, {'tipo': 'xpto'}, {'reconciliacao': 'x'}, {'de': '2026-13-01'},
                    {'de': '2026-11-10', 'ate': '2026-11-01'}):
            self.assertEqual(self.api.get(self._url(), mau).status_code, 400, mau)
        p = self.api.get(self._url(), {'limit': 2, 'offset': 2}).json()
        self.assertEqual((p['count'], len(p['results'])), (3, 1))

    def test_vbvt_so_do_contrato_da_loja(self):
        from .models import FicheiroVBVT
        minha = self._tx(self.loja)
        alheia = self._tx(self.outra)
        # o ficheiro de outro comerciante é recusado e fica registado na loja que o carregou, não na outra
        r = self.api.post(self._url('vbvt/'), {'ficheiro': _ficheiro(_vbvt([_compra(alheia.ref, 2300)], mid='9000202'))})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['estado'], 'rejeitado')
        self.assertIn('não é o do contrato vinti4 desta loja', r.json()['erros'][0]['erro'])
        alheia.refresh_from_db()
        self.assertIsNone(alheia.reconciliada_em)
        from rest_framework.test import APIClient
        api_b = APIClient()
        api_b.force_authenticate(self.outro.user)
        self.assertEqual(api_b.get(self._url('vbvt/', loja=self.outra)).json()['count'], 0)
        # o ficheiro dela é aplicado; uma linha com a referência de outra loja não lhe toca ("não é nossa")
        r = self.api.post(self._url('vbvt/'), {'ficheiro': _ficheiro(_vbvt([_compra(minha.ref, 2300, comissao=10),
                                                                            _compra(alheia.ref, 2300)], mid='9000101'))})
        d = r.json()
        self.assertEqual(d['estado'], 'aplicado', d['erros'])
        self.assertEqual([l['resultado'] for l in d['linhas']], ['ok', 'desconhecida'])
        minha.refresh_from_db()
        alheia.refresh_from_db()
        self.assertIsNotNone(minha.reconciliada_em)
        self.assertIsNone(alheia.reconciliada_em)
        lista = self.api.get(self._url('vbvt/')).json()
        self.assertEqual([f['estado'] for f in lista['results']], ['aplicado', 'rejeitado'])
        self.assertEqual(self.api.get(self._url('vbvt/'), {'estado': 'aplicado'}).json()['count'], 1)
        alheio = FicheiroVBVT.objects.create(nome='x', hash='h', merchant_id='9000202', estado='aplicado')
        self.assertEqual(self.api.get(self._url(f'vbvt/{alheio.id}/')).status_code, 404)
        # os totais já contam a comissão da SISP
        self.assertEqual(self.api.get(self._url()).json()['totais']['liquido'], '2290.00')

    def test_ficheiro_da_bendi_nao_toca_nas_lojas(self):
        from .pagamentos import vbvt
        da_loja = self._tx(self.loja)
        da_bendi = self._tx(None, referencia='fat-7-cartao-1')
        f = vbvt.processar(_vbvt([_compra(da_loja.ref, 2300), _compra(da_bendi.ref, 2300)]))     # Merchant ID da Bendi
        self.assertEqual([l['resultado'] for l in f.linhas], ['desconhecida', 'ok'])
        da_loja.refresh_from_db()
        self.assertIsNone(da_loja.reconciliada_em)

    def test_avisa_o_dono_e_os_admins(self):
        from .models import Notificacao
        from .models import EmailEnviado
        admin = _utilizador('adminpag')
        admin.user.is_staff = True
        admin.user.save(update_fields=['is_staff'])
        admin.role_admin = next(r for r, p in Utilizador.PERMISSOES_ADMIN.items() if 'gerir_pagamentos' in p)
        admin.email_confirmado = True
        admin.save(update_fields=['role_admin', 'email_confirmado'])
        Utilizador.objects.filter(pk=self.dono.pk).update(email_confirmado=True)
        nao_paga = self._tx(self.loja, estado='por_confirmar')
        with self.captureOnCommitCallbacks(execute=True):
            r = self.api.post(self._url('vbvt/'), {'ficheiro': _ficheiro(_vbvt([_compra(nao_paga.ref, 2300)], mid='9000101'))})
        self.assertEqual(r.json()['linhas'][0]['resultado'], 'paga_so_na_sisp')
        avisos = Notificacao.objects.filter(tipo='vinti4')
        self.assertEqual(set(avisos.values_list('utilizador_id', flat=True)), {self.dono.id, admin.id})
        self.assertEqual(avisos.get(utilizador=self.dono).link, f'/loja/{self.loja.id}/backoffice/pagamentos')
        self.assertEqual(EmailEnviado.objects.filter(tipo='aviso_vinti4').count(), 2)
        # um ficheiro sem diferenças de dinheiro não avisa
        Notificacao.objects.all().delete()
        ok = self._tx(self.loja)
        with self.captureOnCommitCallbacks(execute=True):
            self.api.post(self._url('vbvt/'), {'ficheiro': _ficheiro(_vbvt([_compra(ok.ref, 2300)], mid='9000101', data='20261113',
                                                                          ant='20261112', seq_ant=1))})
        self.assertFalse(Notificacao.objects.filter(tipo='vinti4').exists())

    def test_tempo_real_da_loja(self):
        with mock.patch('app.utils.tempo_real_listas.emitir') as emitir:
            tx = self._tx(self.loja)
            self.assertIn(mock.call('cartao', self.loja.id), emitir.call_args_list)
            emitir.reset_mock()
            tx.respostas = [{'x': 1}]
            tx.save(update_fields=['respostas'])                       # só a resposta guardada: não avisa
            self.assertNotIn(mock.call('cartao', self.loja.id), emitir.call_args_list)
            tx.estado = 'cancelada'
            tx.save(update_fields=['estado'])
            self.assertIn(mock.call('cartao', self.loja.id), emitir.call_args_list)

    def test_admin_filtra_por_loja(self):
        api = _admin_api('adminfiltro')
        self._tx(self.loja)
        self._tx(self.outra)
        d = api.get('/app/admin/pagamentos/vinti4/', {'loja_id': self.loja.id}).json()
        self.assertEqual(d['count'], 1)
        self.assertEqual({l['id'] for l in d['lojas']}, {self.loja.id, self.outra.id})
        self.assertEqual(api.get('/app/admin/pagamentos/vinti4/', {'loja_id': 'x'}).status_code, 400)
        self.assertEqual(api.get('/app/admin/pagamentos/vinti4/csv/').status_code, 200)
        self.assertEqual(api.get('/app/admin/pagamentos/vbvt/', {'dono': self.loja.id}).status_code, 200)


def _ficheiro(conteudo, nome='VBVT.txt'):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile(nome, conteudo, content_type='text/plain')


@override_settings(**CRED)
class UmPagamentoDeCadaVez(TestCase):
    """Com um pagamento com cartão ainda na página da SISP, não se começa outro para a mesma coisa."""

    def setUp(self):
        self.u = _utilizador()
        self.f = obter('vinti4')

    def _iniciar(self, ref='enc-12-cartao-1'):
        return self.f.iniciar(Cobranca(referencia=ref, valor=Decimal('1500'), descricao='T', pagador=self.u))

    def test_bloqueia_e_liberta(self):
        primeiro = TransacaoVinti4.objects.get(ref=self._iniciar().campos['merchantRef'])
        with self.assertRaisesMessage(ErroPagamento, 'Já há um pagamento com cartão a decorrer'):
            self._iniciar('enc-12-cartao-2')
        self._iniciar('enc-13-cartao-1')                    # outra encomenda: pode
        self._iniciar('mar-12-cartao-1')                    # uma marcação com o mesmo número: pode
        v4.processar_resposta({'merchantRef': primeiro.ref, 'merchantSession': primeiro.sessao, 'UserCancelled': 'true'})
        self._iniciar('enc-12-cartao-3')                    # cancelou na SISP: fica livre logo
        TransacaoVinti4.objects.filter(referencia__startswith='enc-12-').update(
            criada_em=timezone.now() - timedelta(minutes=9))
        self._iniciar('enc-12-cartao-4')                    # passaram os 8 minutos: fica livre


@override_settings(**CRED, VINTI4_MERCHANT_ID=MID)
class IdentificadorEstavel(TestCase):
    """Confirmada pela API de estado e depois reconciliada pelo VBVT: o regresso do cliente continua a reconhecer o
    mesmo pagamento (não vira um pagamento a dobrar com pedido de reembolso)."""

    def test_vbvt_nao_muda_a_transacao(self):
        from .pagamentos import vbvt
        u = _utilizador()
        inicio = obter('vinti4').iniciar(Cobranca(referencia='fat-7-cartao-1', valor=Decimal('1500'), descricao='T',
                                                  pagador=u))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga', confirmada_por='estado', efeito='pago')
        antes = TransacaoVinti4.objects.get(pk=tx.pk).transacao
        f = vbvt.processar(_vbvt([_compra(tx.ref, 1500, comissao=Decimal('10'))]))
        self.assertEqual(f.estado, 'aplicado', f.erros)
        tx.refresh_from_db()
        self.assertIsNotNone(tx.reconciliada_em)
        self.assertEqual(tx.transacao, antes)
        self.assertEqual(f.linhas[0]['transacao'], '987-26')            # o nº da SISP fica na linha do ficheiro


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4', PAGAMENTOS_FORNECEDOR_BENDI='vinti4')
class PagamentoTardioDaLoja(TestCase):
    """Cartão vinti4 da loja cobrado depois de a encomenda ser cancelada, ou a dobrar: o dinheiro está na conta da
    loja — é ela que faz o estorno (nunca o simulado), e a encomenda paga não é cancelada."""

    def setUp(self):
        from .models import Encomenda
        self.dono = _utilizador('donotardio')
        self.loja = _loja(self.dono)
        self.cliente = _utilizador('clientetardio')
        self.enc = Encomenda.objects.create(comprador=self.cliente, loja=self.loja, valor_total=Decimal('2300'))
        self.admin = _utilizador('admintardio')
        self.admin.user.is_staff = True
        self.admin.user.save(update_fields=['is_staff'])

    def _paga(self, n):
        from .pagamentos import servico
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'enc-{self.enc.id}-cartao-{n}', valor=Decimal('2300'),
                                                  descricao='E', pagador=self.cliente, loja=self.loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga', tid=str(100 + n), periodo='987')
        tx.refresh_from_db()
        conf = Confirmacao(sucesso=True, referencia=tx.referencia, transacao=tx.transacao, valor=Decimal('2300'),
                           moeda=v4._moeda())
        return servico.confirmar(v4.FORNECEDOR, conf), tx

    def test_cancelada_depois_paga(self):
        from .models import Reembolso
        from .utils import devolucoes
        self.enc.status = 'cancelado'
        self.enc.save(update_fields=['status'])
        res, tx = self._paga(1)
        self.assertEqual(res['estado'], 'reembolso')
        r = Reembolso.objects.get(encomenda=self.enc)
        from .models import MensagemReembolso
        self.assertIn('A loja vai devolver', MensagemReembolso.objects.filter(reembolso=r).first().texto)
        self.assertTrue(devolucoes._pagou_com_cartao_loja(self.enc))
        self._paga(1)                                           # o mesmo regresso outra vez: não repete o pedido
        self.assertEqual(Reembolso.objects.filter(encomenda=self.enc).count(), 1)
        devolucoes.admin_decidir(r, self.admin, 'reembolsar')
        r.refresh_from_db()
        # a loja devolve com estorno (manual), nunca "reembolsado" pelo simulado
        self.assertEqual((r.estado, r.metodo), ('a_devolver', 'manual'))

    def test_pago_a_dobrar_nao_cancela(self):
        from .models import Reembolso
        from .utils import devolucoes
        res, _ = self._paga(1)
        self.assertEqual(res['estado'], 'pago')
        res, segunda = self._paga(2)
        self.assertEqual(res['estado'], 'reembolso')
        r = Reembolso.objects.get(encomenda=self.enc, motivo='pagamento_tardio')
        self.assertIn(segunda.transacao, r.descricao)
        devolucoes.admin_decidir(r, self.admin, 'reembolsar')
        self.enc.refresh_from_db()
        r.refresh_from_db()
        self.assertEqual(self.enc.status, 'pago')               # a encomenda paga continua
        self.assertEqual((r.estado, r.metodo), ('a_devolver', 'manual'))


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class EncomendaEsperaPeloCartao(TestCase):
    """Passados os 30 minutos, uma encomenda com o cliente ainda na página da SISP não é cancelada."""

    def test_espera(self):
        from .models import Encomenda
        from .utils.encomendas import expirar_por_pagar
        dono, cliente = _utilizador('donoespera'), _utilizador('clienteespera')
        loja = _loja(dono)
        enc = Encomenda.objects.create(comprador=cliente, loja=loja, valor_total=Decimal('900'))
        Encomenda.objects.filter(pk=enc.pk).update(data_criacao=timezone.now() - timedelta(minutes=35))
        obter('vinti4').iniciar(Cobranca(referencia=f'enc-{enc.id}-cartao-1', valor=Decimal('900'), descricao='E',
                                         pagador=cliente, loja=loja))
        self.assertEqual(expirar_por_pagar(), 0)
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'pendente')
        # 8 minutos depois sem resposta: já cancela
        self.assertEqual(expirar_por_pagar(timezone.now() + timedelta(minutes=9)), 1)


# ── auditoria 2: cancelamento com sessão, assinaturas inválidas, por confirmar sem Portal, encomenda nova com o
#    cartão a decorrer, marcação paga tarde e a ficha do cartão ligada ao reembolso ──

@override_settings(**CRED)
class CancelamentoComSessao(TestCase):
    """O cancelamento da SISP não leva FingerPrint: só vale com o merchantSession certo (que nunca anda nos
    endereços do site); a sessão também não fica à vista nas respostas guardadas."""

    def test_sem_a_sessao_nao_cancela(self):
        from .models import RegistoTransacao
        u = _utilizador()
        tx = TransacaoVinti4.objects.get(ref=obter('vinti4').iniciar(Cobranca(
            referencia='fat-7-cartao-1', valor=Decimal('1500'), descricao='T', pagador=u)).campos['merchantRef'])
        for falso in ({}, {'merchantSession': 'SERRADA0000000'}):
            v4.processar_resposta({'merchantRef': tx.ref, 'UserCancelled': 'true', **falso})
            tx.refresh_from_db()
            self.assertEqual(tx.estado, 'iniciada')
        self.assertEqual(RegistoTransacao.objects.filter(evento='cartao_cancelamento_invalido', objeto_id=tx.id).count(), 2)
        v4.processar_resposta({'merchantRef': tx.ref, 'merchantSession': tx.sessao, 'UserCancelled': 'true'})
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'cancelada')
        self.assertNotIn(tx.sessao, str(tx.respostas))


@override_settings(**CRED)
class AssinaturaInvalida(TestCase):
    """Uma resposta (de sucesso ou de erro) com o resultFingerPrint errado fica no registo e avisa os admins."""

    def test_erro_com_assinatura_errada(self):
        from .models import RegistoTransacao
        u = _utilizador()
        tx = TransacaoVinti4.objects.get(ref=obter('vinti4').iniciar(Cobranca(
            referencia='fat-7-cartao-1', valor=Decimal('1500'), descricao='T', pagador=u)).campos['merchantRef'])
        with mock.patch('app.Views.notificacaoView.notificar_admins') as notificar:
            v4.processar_resposta(_resposta_erro(tx, chave='OUTRACHAVE'))
            v4.processar_resposta(_resposta_sucesso(tx, chave='OUTRACHAVE'))
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'iniciada')
        self.assertEqual(RegistoTransacao.objects.filter(evento='cartao_assinatura_invalida', objeto_id=tx.id).count(), 2)
        self.assertEqual(notificar.call_args.kwargs['tipo'], 'pagamento_erro')
        self.assertIn('assinatura inválida', notificar.call_args.kwargs['titulo'])


@override_settings(**CRED)
class PorConfirmarSemPortal(TestCase):
    """Sem Portal configurado as voltas do worker não gastam consultas; depois das 12, continua devagar."""

    def _tx(self):
        u = _utilizador()
        tx = TransacaoVinti4.objects.get(ref=obter('vinti4').iniciar(Cobranca(
            referencia='fat-7-cartao-1', valor=Decimal('1500'), descricao='T', pagador=u)).campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(criada_em=timezone.now() - timedelta(minutes=9))
        return tx

    def test_sem_portal_nao_conta(self):
        tx = self._tx()
        v4.rever_sem_resposta()
        for _ in range(3):
            TransacaoVinti4.objects.filter(pk=tx.pk).update(consultada_em=timezone.now() - timedelta(minutes=11))
            v4.rever_sem_resposta()
        tx.refresh_from_db()
        self.assertEqual((tx.estado, tx.consultas), ('por_confirmar', 0))

    @override_settings(VINTI4_PORTAL_ID='1', VINTI4_PORTAL_PASSWORD='abc123')
    @mock.patch('app.pagamentos.servico.confirmar', return_value={'estado': 'pago'})
    @mock.patch('app.pagamentos.vinti4.requests.post')
    def test_depois_das_12_continua_devagar(self, post, _confirmar):
        tx = self._tx()
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='por_confirmar', consultas=v4.CONSULTAS_MAX,
                                                        consultada_em=timezone.now() - timedelta(hours=1))
        post.return_value.json.return_value = {'result': True, 'transactionSuccess': True}
        v4.rever_sem_resposta()
        post.assert_not_called()                         # 1 hora: ainda não
        TransacaoVinti4.objects.filter(pk=tx.pk).update(consultada_em=timezone.now() - timedelta(hours=7))
        v4.rever_sem_resposta()
        tx.refresh_from_db()
        self.assertEqual(tx.estado, 'paga')
        # mais de 30 dias: só à mão ("Perguntar à SISP")
        post.reset_mock()
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='por_confirmar', consultada_em=None,
                                                        criada_em=timezone.now() - timedelta(days=31))
        v4.rever_sem_resposta()
        post.assert_not_called()


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class NovaEncomendaComCartaoADecorrer(TestCase):
    """O cliente a pagar na SISP uma encomenda por pagar: uma nova encomenda na mesma loja não a cancela."""

    def test_minutos(self):
        from .models import Encomenda
        from .utils.encomendas import minutos_cartao_a_decorrer
        dono, cliente = _utilizador('dononova'), _utilizador('clientenova')
        loja = _loja(dono)
        enc = Encomenda.objects.create(comprador=cliente, loja=loja, valor_total=Decimal('900'))
        self.assertEqual(minutos_cartao_a_decorrer(cliente, loja), 0)
        obter('vinti4').iniciar(Cobranca(referencia=f'enc-{enc.id}-cartao-1', valor=Decimal('900'), descricao='E',
                                         pagador=cliente, loja=loja))
        self.assertEqual(minutos_cartao_a_decorrer(cliente, loja), 8)
        outra = _loja(_utilizador('donooutra'), pos_id='90088')
        self.assertEqual(minutos_cartao_a_decorrer(cliente, outra), 0)          # noutra loja: pode
        self.assertEqual(minutos_cartao_a_decorrer(cliente, loja, timezone.now() + timedelta(minutes=9)), 0)


def _marcacao(loja, cliente, estado='expirada', pago=False):
    from .servicos.models import ConfigServicos, Marcacao, Profissional, Servico
    ConfigServicos.objects.get_or_create(loja=loja, defaults={'ativo': True})
    prof = Profissional.objects.create(loja=loja, nome='Ana')
    serv = Servico.objects.create(loja=loja, nome='Corte', duracao_min=30, preco=Decimal('1200'), pagamento='antecipado')
    inicio = timezone.now() + timedelta(days=2)
    return Marcacao.objects.create(loja=loja, servico=serv, profissional=prof, cliente=cliente, servico_nome='Corte',
                                   duracao_min=30, inicio=inicio, fim=inicio + timedelta(minutes=30),
                                   ocupado_ate=inicio + timedelta(minutes=30), estado=estado,
                                   preco_indicado=Decimal('1200'), pagamento='antecipado', pago=pago)


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class MarcacaoPagaTarde(TestCase):
    """Cartão da loja cobrado numa marcação que já não podia ser paga: fica na marcação como reembolso por concluir
    (a loja faz o estorno e marca "Estorno feito"), o cliente e a loja são avisados, a ficha do cartão mostra-o."""

    def setUp(self):
        self.dono = _utilizador('donomar')
        self.loja = _loja(self.dono)
        self.cliente = _utilizador('clientemar')

    def _paga(self, m, n=1):
        from .pagamentos import servico
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'mar-{m.id}-cartao-{n}', valor=Decimal('1200'),
                                                  descricao='M', pagador=self.cliente, loja=self.loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga', tid=str(200 + n), periodo='987',
                                                        efeito='reembolso')
        tx.refresh_from_db()
        conf = Confirmacao(sucesso=True, referencia=tx.referencia, transacao=tx.transacao, valor=Decimal('1200'),
                           moeda=v4._moeda())
        return servico.confirmar(v4.FORNECEDOR, conf), tx

    def test_expirada_depois_paga(self):
        from .models import Notificacao
        from .pagamentos import cartao_listas
        from .servicos import marcacoes as ops
        from .servicos.models import MensagemMarcacao
        m = _marcacao(self.loja, self.cliente)
        res, tx = self._paga(m)
        self.assertEqual(res['estado'], 'reembolso')
        m.refresh_from_db()
        self.assertEqual((m.pago, m.valor_pago, m.reembolso_devido, m.pagamento_referencia),
                         (True, Decimal('1200'), Decimal('1200'), tx.transacao))
        self.assertEqual(ops.por_reembolsar(m), Decimal('1200'))
        self.assertTrue(MensagemMarcacao.objects.filter(marcacao=m, texto__contains='Vai ser devolvido').exists())
        self.assertTrue(Notificacao.objects.filter(utilizador=self.cliente, titulo='Reembolso a caminho').exists())
        self.assertTrue(Notificacao.objects.filter(utilizador=self.dono, titulo='Faz o estorno no cartão').exists())
        self._paga(m)                                    # o mesmo pagamento outra vez: nada muda
        m.refresh_from_db()
        self.assertEqual(m.reembolso_devido, Decimal('1200'))
        ficha = cartao_listas.item(tx, completo=True, destino_loja=lambda t, i: '')
        self.assertEqual([(r['estado'], r['valor']) for r in ficha['reembolsos']], [('por_reembolsar', '1.200$00')])
        ops.estorno_feito(m, 'EST-123')
        m.refresh_from_db()
        self.assertEqual(ops.por_reembolsar(m), Decimal('0'))
        ficha = cartao_listas.item(tx, completo=True)
        self.assertEqual(ficha['reembolsos'][0]['estado'], 'reembolsado')

    def test_a_dobrar(self):
        from .servicos import marcacoes as ops
        m = _marcacao(self.loja, self.cliente, estado='confirmada', pago=True)
        primeira = 'v4_987-101'
        from .servicos.models import Marcacao
        Marcacao.objects.filter(pk=m.pk).update(valor_pago=Decimal('1200'), pagamento_fornecedor='vinti4',
                                                pagamento_referencia=primeira)
        res, segunda = self._paga(m, 2)
        self.assertEqual(res['estado'], 'reembolso')
        m.refresh_from_db()
        self.assertEqual((m.valor_pago, m.reembolso_devido, m.pagamento_referencia),
                         (Decimal('2400'), Decimal('1200'), primeira))
        self.assertNotEqual(segunda.transacao, primeira)
        self.assertEqual(ops.por_reembolsar(m), Decimal('1200'))


@override_settings(**CRED)
class FichaComReembolso(TestCase):
    """A ficha do cartão de uma encomenda mostra o pedido de reembolso dela, com o caminho certo (loja/admin)."""

    def test_pedido_na_ficha(self):
        from .models import Encomenda
        from .pagamentos import cartao_listas
        dono, cliente = _utilizador('donoficha'), _utilizador('clienteficha')
        loja = _loja(dono)
        enc = Encomenda.objects.create(comprador=cliente, loja=loja, valor_total=Decimal('2300'), status='cancelado')
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'enc-{enc.id}-cartao-1', valor=Decimal('2300'),
                                                  descricao='E', pagador=cliente, loja=loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga', tid='301', periodo='987', efeito='reembolso')
        tx.refresh_from_db()
        from .utils.devolucoes import pago_depois_de_cancelada
        from .models import Notificacao
        with mock.patch('app.utils.tempo_real_listas.emitir') as emitir:
            r = pago_depois_de_cancelada(enc, Decimal('2300'), tx.transacao, cartao_loja=True)
        self.assertIn(('cartao', loja.id), [c.args for c in emitir.call_args_list])
        self.assertTrue(Notificacao.objects.filter(utilizador=dono, titulo__startswith='Pagamento com cartão a devolver').exists())
        loja_ficha = cartao_listas.item(tx, completo=True, destino_loja=lambda t, i: '')
        self.assertEqual(loja_ficha['reembolsos'][0]['link'], f'/loja/{loja.id}/backoffice/devolucoes/{r.id}')
        self.assertEqual(loja_ficha['reembolsos'][0]['estado'], 'em_disputa')
        self.assertEqual(cartao_listas.item(tx, completo=True)['reembolsos'][0]['link'], f'/admin/devolucoes/{r.id}')


# ── reembolsos com cartão: a loja indica como devolveu (estorno com referência / outra forma com prova) e o VBVT,
#    se a loja o carregar, confirma o estorno (reforço opcional) ──

def _png():
    import io
    from PIL import Image
    from django.core.files.uploadedfile import SimpleUploadedFile
    b = io.BytesIO()
    Image.new('RGB', (4, 4), (200, 10, 10)).save(b, 'PNG')
    return SimpleUploadedFile('prova.png', b.getvalue(), content_type='image/png')


@override_settings(**CRED, VINTI4_MERCHANT_ID=MID, PAGAMENTOS_FORNECEDOR='vinti4')
class DevolucaoComCartao(TestCase):

    def setUp(self):
        from rest_framework.test import APIClient
        from .models import AdesaoVinti4, Encomenda, Pagamento
        from .utils import devolucoes
        self.dono = _utilizador('donodev')
        self.loja = _loja(self.dono)
        AdesaoVinti4.objects.filter(loja=self.loja).update(merchant_id='9000101')
        self.cliente = _utilizador('clientedev')
        self.enc = Encomenda.objects.create(comprador=self.cliente, loja=self.loja, valor_total=Decimal('2300'),
                                            status='pago')
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'enc-{self.enc.id}-cartao-1', valor=Decimal('2300'),
                                                  descricao='E', pagador=self.cliente, loja=self.loja))
        self.tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=self.tx.pk).update(estado='paga', tid='77', periodo='987', efeito='pago')
        self.tx.refresh_from_db()
        Pagamento.objects.create(encomenda=self.enc, valor=Decimal('2300'), status='aprovado', fornecedor='vinti4',
                                 referencia_transacao=self.tx.transacao)
        self.r = devolucoes.ao_cancelar_pela_loja(self.enc, self.dono)
        self.r.refresh_from_db()
        self.api = APIClient()
        self.api.force_authenticate(self.dono.user)

    def _acao(self, dados, multipart=False):
        return self.api.post(f'/app/loja/{self.loja.id}/reembolsos/{self.r.id}/acao/', {'acao': 'dinheiro_entregue', **dados},
                             format='multipart' if multipart else 'json')

    def test_estorno_sem_referencia(self):
        """A referência é opcional: sem ela o estorno fica marcado na mesma (o cliente confirma ou diz que não recebeu)."""
        r = self._acao({})
        self.assertEqual(r.status_code, 200, r.content[:300])
        d = r.json()
        self.assertEqual((d['devolvido_como'], d['referencia_devolucao']), ('estorno', ''))
        self.assertTrue(d['entregue_em'])

    def test_estorno_com_referencia(self):
        self.assertEqual((self.r.estado, self.r.metodo), ('a_devolver', 'manual'))
        self.assertEqual(self._acao({'como': 'estorno', 'referencia': 'AB'}).status_code, 400)      # demasiado curta
        r = self._acao({'como': 'estorno', 'referencia': 'EST-998877'})
        self.assertEqual(r.status_code, 200, r.content[:300])
        d = r.json()
        self.assertEqual((d['devolvido_como'], d['referencia_devolucao']), ('estorno', 'EST-998877'))
        self.assertTrue(d['entregue_em'])
        # o cliente vê a referência e confirma
        from rest_framework.test import APIClient
        api = APIClient()
        api.force_authenticate(self.cliente.user)
        self.assertEqual(api.get(f'/app/reembolsos/{self.r.id}/').json()['referencia_devolucao'], 'EST-998877')

    def test_outra_forma_pede_prova(self):
        self.assertEqual(self._acao({'como': 'outro', 'nota': 'Transferência BCA'}).status_code, 400)       # sem foto
        self.assertEqual(self._acao({'como': 'outro', 'fotos': _png()}, multipart=True).status_code, 400)  # sem nota
        r = self._acao({'como': 'outro', 'nota': 'Transferência BCA para a conta do cliente', 'fotos': _png()},
                       multipart=True)
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.r.refresh_from_db()
        self.assertEqual((self.r.devolvido_como, self.r.fotos.count()), ('outro', 1))
        self.assertEqual(self.r.fotos.first().mensagem.papel, 'loja')

    def test_vbvt_confirma_e_fecha(self):
        from .models import Notificacao
        from .pagamentos import vbvt
        self._acao({'como': 'estorno', 'referencia': 'EST-1'})
        f = vbvt.processar(_vbvt([_estorno('BEST000000009', self.tx.ref, 2300)], mid='9000101'), loja=self.loja)
        self.assertEqual(f.estado, 'aplicado', f.erros)
        self.r.refresh_from_db()
        self.tx.refresh_from_db()
        self.assertEqual(self.tx.valor_estornado, Decimal('2300'))
        self.assertEqual(self.r.estado, 'reembolsado')
        self.assertIsNotNone(self.r.confirmado_sisp_em)
        self.assertTrue(Notificacao.objects.filter(utilizador=self.cliente, titulo__startswith='Reembolso confirmado').exists())
        from .pagamentos import cartao_listas
        self.assertTrue(cartao_listas.item(self.tx, completo=True)['reembolsos'][0]['confirmado_sisp'])

    def test_sem_marcar_tambem_fecha(self):
        """A loja esqueceu-se de marcar, mas carregou o VBVT: o estorno da SISP chega."""
        from .pagamentos import vbvt
        with mock.patch('app.utils.tempo_real_listas.emitir') as emitir,                 mock.patch('app.utils.devolucoes._enviar') as enviar:
            with self.captureOnCommitCallbacks(execute=True):
                vbvt.processar(_vbvt([_estorno('BEST000000009', self.tx.ref, 2300)], mid='9000101'), loja=self.loja)
        self.r.refresh_from_db()
        self.assertEqual((self.r.estado, self.r.devolvido_como), ('reembolsado', 'estorno'))
        self.assertTrue(self.r.referencia.startswith('SISP 988-'), self.r.referencia)   # a referência vem da SISP
        # tempo real: a ficha do cartão (backoffice → Pagamentos) e o pedido (cliente, loja, Bendi)
        self.assertIn(('cartao', self.loja.id), [c.args for c in emitir.call_args_list])
        self.assertTrue(any(c.args[0].id == self.r.id for c in enviar.call_args_list))

    def test_estorno_parcial_nao_chega(self):
        from .pagamentos import vbvt
        vbvt.processar(_vbvt([_estorno('BEST000000009', self.tx.ref, 1000)], mid='9000101'), loja=self.loja)
        self.r.refresh_from_db()
        self.assertEqual(self.r.estado, 'a_devolver')
        self.assertIsNone(self.r.confirmado_sisp_em)
        # o resto no ficheiro do dia seguinte: a soma chega
        vbvt.processar(_vbvt([_estorno('BEST000000010', self.tx.ref, 1300)], mid='9000101', data='20261113',
                             ant='20261112', seq_ant=1), loja=self.loja)
        self.r.refresh_from_db()
        self.assertEqual(self.r.estado, 'reembolsado')

    def test_sem_vbvt_nada_muda(self):
        """O VBVT é opcional: sem ele, a loja marca, o cliente confirma — como sempre."""
        from .utils import devolucoes
        self._acao({'como': 'estorno', 'referencia': 'EST-1'})
        self.r.refresh_from_db()
        devolucoes.cliente_recebi(self.r, self.cliente)
        self.r.refresh_from_db()
        self.assertEqual(self.r.estado, 'reembolsado')
        self.assertIsNone(self.r.confirmado_sisp_em)

    def test_avisa_estorno_que_nao_aparece(self):
        from .models import Notificacao, Reembolso
        from .pagamentos import vbvt
        self._acao({'como': 'estorno', 'referencia': 'EST-1'})
        Reembolso.objects.filter(pk=self.r.pk).update(entregue_em=timezone.now() - timedelta(days=10))
        # um ficheiro de dias depois sem o estorno → avisa (uma vez)
        outra = self._compra_qualquer()
        for data, ant, seq in (('20261112', '00000000', 0), ('20261113', '20261112', 1)):
            vbvt.processar(_vbvt([_compra(outra.ref, 500)], mid='9000101', data=data, ant=ant, seq_ant=seq), loja=self.loja)
        avisos = Notificacao.objects.filter(titulo__startswith=f'Estorno não aparece no VBVT — Encomenda #{self.enc.id}')
        self.assertEqual(set(avisos.values_list('utilizador_id', flat=True)), {self.dono.id})

    def _compra_qualquer(self):
        inicio = obter('vinti4').iniciar(Cobranca(referencia='mar-999-cartao-1', valor=Decimal('500'), descricao='X',
                                                  pagador=self.cliente, loja=self.loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga')
        return tx


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class MarcacaoEstornoNoVBVT(TestCase):

    def test_vbvt_conclui_o_estorno_da_marcacao(self):
        from .models import AdesaoVinti4
        from .pagamentos import vbvt
        from .servicos import marcacoes as ops
        dono, cliente = _utilizador('donomv'), _utilizador('clientemv')
        loja = _loja(dono)
        AdesaoVinti4.objects.filter(loja=loja).update(merchant_id='9000101')
        m = _marcacao(loja, cliente)
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'mar-{m.id}-cartao-1', valor=Decimal('1200'),
                                                  descricao='M', pagador=cliente, loja=loja))
        tx = TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])
        TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga', tid='55', periodo='987', efeito='reembolso')
        tx.refresh_from_db()
        ops.pago_sem_efeito(m, 'vinti4', tx.transacao, Decimal('1200'), 'expirou')
        m.refresh_from_db()
        self.assertEqual(ops.por_reembolsar(m), Decimal('1200'))
        vbvt.processar(_vbvt([_estorno('BEST000000011', tx.ref, 1200)], mid='9000101'), loja=loja)
        m.refresh_from_db()
        self.assertEqual(ops.por_reembolsar(m), Decimal('0'))
        self.assertEqual(m.valor_reembolsado, Decimal('1200'))
