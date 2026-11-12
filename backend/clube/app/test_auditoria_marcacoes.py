"""Auditoria das marcações (2026-11-12): preço que muda com o cartão a decorrer, receita com estorno por fazer,
tempo real das que expiram, referência do estorno opcional."""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from .models import TransacaoVinti4
from .pagamentos import obter
from .pagamentos import vinti4 as v4
from .pagamentos.base import Cobranca, Confirmacao
from .test_vinti4 import CRED, _loja, _marcacao, _utilizador


def _pendente(loja, cliente):
    m = _marcacao(loja, cliente, estado='pendente')
    m.expira_em = timezone.now() + timedelta(minutes=20)
    m.save(update_fields=['expira_em'])
    return m


def _iniciar_cartao(loja, cliente, m, valor='1200'):
    inicio = obter('vinti4').iniciar(Cobranca(referencia=f'mar-{m.id}-cartao-1', valor=Decimal(valor), descricao='M',
                                              pagador=cliente, loja=loja))
    return TransacaoVinti4.objects.get(ref=inicio.campos['merchantRef'])


def _confirmar(tx, valor):
    from .pagamentos import servico
    TransacaoVinti4.objects.filter(pk=tx.pk).update(estado='paga', tid='301', periodo='987')
    tx.refresh_from_db()
    conf = Confirmacao(sucesso=True, referencia=tx.referencia, transacao=tx.transacao, valor=Decimal(valor),
                       moeda=v4._moeda())
    return servico.confirmar(v4.FORNECEDOR, conf)


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class PrecoComCartaoADecorrer(TestCase):

    def setUp(self):
        self.dono, self.cliente = _utilizador('donopreco'), _utilizador('clipreco')
        self.loja = _loja(self.dono)

    def test_nao_se_muda_o_preco_com_o_cartao_a_decorrer(self):
        from .servicos import conversa
        m = _pendente(self.loja, self.cliente)
        _iniciar_cartao(self.loja, self.cliente, m)
        with self.assertRaises(conversa.ErroConversa):
            conversa.propor(m, Decimal('1000'), '', 'Dono')

    def test_aceitar_com_o_cartao_a_decorrer(self):
        from .servicos import conversa
        m = _pendente(self.loja, self.cliente)
        p = conversa.propor(m, Decimal('1000'), '', 'Dono')
        _iniciar_cartao(self.loja, self.cliente, m)
        with self.assertRaises(conversa.ErroConversa):
            conversa.responder(m, p.id, True, self.cliente)

    def test_valor_diferente_fica_registado_para_devolver(self):
        """Se mesmo assim o valor cobrado não bate, o dinheiro não se perde: fica por devolver na marcação."""
        from .servicos import marcacoes as ops
        from .servicos.models import Marcacao
        m = _pendente(self.loja, self.cliente)
        tx = _iniciar_cartao(self.loja, self.cliente, m)
        Marcacao.objects.filter(pk=m.pk).update(preco_indicado=Decimal('1000'))
        res = _confirmar(tx, '1200')
        self.assertEqual(res['estado'], 'reembolso')
        m.refresh_from_db()
        self.assertEqual((m.pago, m.valor_pago, m.reembolso_devido), (True, Decimal('1200'), Decimal('1200')))
        self.assertEqual(ops.por_reembolsar(m), Decimal('1200'))


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class ReceitaComEstornoPorFazer(TestCase):

    def test_cancelada_com_estorno_por_fazer_nao_e_receita(self):
        from .servicos import marcacoes as ops
        from .servicos.relatorios import _receita
        from .utils import faturas_vendas
        dono, cliente = _utilizador('donorec'), _utilizador('clirec')
        loja = _loja(dono)
        m = _pendente(loja, cliente)
        tx = _iniciar_cartao(loja, cliente, m)
        _confirmar(tx, '1200')
        m.refresh_from_db()
        self.assertTrue(m.pago)
        m = ops.cancelar(m, 'Dono', 'Doente')            # a loja cancela: devolve tudo (estorno no Portal)
        m.refresh_from_db()
        self.assertEqual(ops.por_reembolsar(m), Decimal('1200'))
        self.assertEqual(_receita(m), Decimal('0'))
        self.assertEqual(faturas_vendas.base('marcacoes').get(pk=m.pk).receita, Decimal('0'))
        self.assertFalse(faturas_vendas.base('marcacoes').filter(faturas_vendas.q_por_faturar('marcacoes'), pk=m.pk).exists())


@override_settings(PAGAMENTOS_FORNECEDOR='simulado')
class TempoRealDasExpiradas(TestCase):

    def test_expirar_avisa_as_paginas(self):
        from .servicos import marcacoes as ops
        dono, cliente = _utilizador('donoexpt'), _utilizador('cliexpt')
        loja = _loja(dono)
        m = _marcacao(loja, cliente, estado='pendente')
        m.expira_em = timezone.now() - timedelta(minutes=1)
        m.save(update_fields=['expira_em'])
        with mock.patch('app.servicos.tempo_real.emitir') as emitir, self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(ops.expirar_vencidas(pk=m.pk), 1)
        emitir.assert_any_call(m.pk)


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class EstornoSemReferencia(TestCase):

    def test_referencia_opcional_como_nas_encomendas(self):
        from .servicos import marcacoes as ops
        dono, cliente = _utilizador('donoest'), _utilizador('cliest')
        loja = _loja(dono)
        m = _pendente(loja, cliente)
        tx = _iniciar_cartao(loja, cliente, m)
        _confirmar(tx, '1200')
        m.refresh_from_db()
        m = ops.cancelar(m, 'Dono', 'Fechado')
        ops.estorno_feito(m, '')
        m.refresh_from_db()
        self.assertEqual(ops.por_reembolsar(m), Decimal('0'))
        with self.assertRaises(ops.ErroMarcacao):
            ops.estorno_feito(m, '')                        # já não há nada por devolver


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class DevolvidoDeOutraForma(TestCase):
    """Cartão vinti4: a loja devolve de outra forma com prova; o cliente confirma, diz que não recebeu, ou o prazo fecha."""

    def setUp(self):
        from rest_framework.test import APIClient
        from .servicos import marcacoes as ops
        self.dono, self.cliente = _utilizador('donooutra'), _utilizador('clioutra')
        self.loja = _loja(self.dono)
        m = _pendente(self.loja, self.cliente)
        _confirmar(_iniciar_cartao(self.loja, self.cliente, m), '1200')
        self.m = ops.cancelar(m, 'Dono', 'Doente')
        self.ops = ops
        self.loja_api, self.cli_api = APIClient(), APIClient()
        self.loja_api.force_authenticate(self.dono.user)
        self.cli_api.force_authenticate(self.cliente.user)
        self.url_loja = f'/app/loja/{self.loja.id}/servicos/marcacoes/{self.m.id}/acao/'
        self.url_cli = f'/app/marcacoes/{self.m.id}/acao/'

    def _devolver(self, **extra):
        from .test_vinti4 import _png
        dados = {'acao': 'devolvido_outra_forma', 'nota': 'Em dinheiro ao balcão', 'fotos': [_png()], **extra}
        return self.loja_api.post(self.url_loja, dados, format='multipart')

    def test_prova_obrigatoria(self):
        r = self.loja_api.post(self.url_loja, {'acao': 'devolvido_outra_forma', 'nota': 'Em dinheiro'}, format='multipart')
        self.assertEqual(r.status_code, 400)
        self.assertIn('prova', r.json()['detail'])
        r = self._devolver(nota='x')
        self.assertEqual(r.status_code, 400)

    def test_cliente_confirma(self):
        from .servicos.models import FotoMarcacao
        r = self._devolver()
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertIsNotNone(r.json()['reembolso_por_concluir']['outra_forma'])
        self.assertEqual(FotoMarcacao.objects.filter(marcacao=self.m).count(), 1)
        self.assertEqual(self._devolver().status_code, 400)                       # não se declara duas vezes
        self.assertEqual(self.loja_api.post(self.url_loja, {'acao': 'estorno_feito'}, format='json').status_code, 400)
        r = self.cli_api.get(f'/app/marcacoes/{self.m.id}/')
        self.assertEqual(r.json()['reembolso_por_concluir']['outra_forma']['nota'], 'Em dinheiro ao balcão')
        r = self.cli_api.post(self.url_cli, {'acao': 'devolucao_recebida'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.m.refresh_from_db()
        self.assertEqual((self.ops.por_reembolsar(self.m), self.m.valor_reembolsado, self.m.devolucao_outra_prazo),
                         (Decimal('0'), Decimal('1200'), None))

    def test_cliente_nao_recebeu(self):
        self._devolver()
        with mock.patch('app.Views.notificacaoView.notificar_admins') as admins:
            r = self.cli_api.post(self.url_cli, {'acao': 'devolucao_nao_recebida', 'texto': 'Não me deram nada'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.m.refresh_from_db()
        self.assertEqual(self.ops.por_reembolsar(self.m), Decimal('1200'))
        self.assertIsNotNone(self.m.devolucao_nao_recebida_em)
        self.assertEqual(admins.call_args.kwargs['titulo'], f'Devolução não recebida — Marcação #{self.m.id}')
        self.assertEqual(self._devolver().status_code, 200)                       # a loja pode tentar outra vez

    def test_prazo_acaba_fica_confirmado(self):
        from .servicos import ciclo
        from .servicos.models import Marcacao
        self._devolver()
        Marcacao.objects.filter(pk=self.m.pk).update(devolucao_outra_prazo=timezone.now() - timedelta(minutes=1))
        self.assertEqual(ciclo.processar()['devolucoes_confirmadas'], 1)
        self.m.refresh_from_db()
        self.assertEqual(self.ops.por_reembolsar(self.m), Decimal('0'))

    def test_outro_cliente_nao_confirma(self):
        from rest_framework.test import APIClient
        self._devolver()
        outro = APIClient()
        outro.force_authenticate(_utilizador('intruso').user)
        self.assertEqual(outro.post(self.url_cli, {'acao': 'devolucao_recebida'}, format='json').status_code, 404)


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class ConcluirPorPagarOnline(TestCase):

    def setUp(self):
        from rest_framework.test import APIClient
        self.dono, self.cliente = _utilizador('donoconc'), _utilizador('cliconc')
        self.loja = _loja(self.dono)
        self.m = _pendente(self.loja, self.cliente)
        from .servicos.models import Marcacao
        agora = timezone.now()
        Marcacao.objects.filter(pk=self.m.pk).update(inicio=agora - timedelta(minutes=5), fim=agora + timedelta(minutes=25),
                                                     ocupado_ate=agora + timedelta(minutes=25))
        self.api = APIClient()
        self.api.force_authenticate(self.dono.user)
        self.url = f'/app/loja/{self.loja.id}/servicos/marcacoes/{self.m.id}/acao/'

    def test_pede_confirmacao_e_fica_no_local(self):
        r = self.api.post(self.url, {'acao': 'concluir'}, format='json')
        self.assertEqual((r.status_code, r.json().get('codigo')), (400, 'pago_no_local'))
        r = self.api.post(self.url, {'acao': 'concluir', 'pago_no_local': True}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.m.refresh_from_db()
        self.assertEqual((self.m.estado, self.m.pagamento, self.m.pago), ('concluida', 'local', False))

    def test_com_o_cartao_a_decorrer_espera(self):
        _iniciar_cartao(self.loja, self.cliente, self.m)
        r = self.api.post(self.url, {'acao': 'concluir', 'pago_no_local': True}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('cartão', r.json()['detail'])
