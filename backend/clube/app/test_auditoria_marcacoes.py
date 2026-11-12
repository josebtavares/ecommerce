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
