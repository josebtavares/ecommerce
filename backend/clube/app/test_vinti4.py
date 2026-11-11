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
