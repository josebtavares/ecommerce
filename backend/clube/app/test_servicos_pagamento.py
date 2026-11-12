"""Pagamento das marcações igual ao das encomendas: termos aceites, regra geral do pagamento, e a marcação não
expira com um pagamento com cartão a decorrer na página da SISP."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import TransacaoVinti4
from .pagamentos import obter
from .pagamentos.base import Cobranca
from .test_vinti4 import CRED, _loja, _marcacao, _utilizador


@override_settings(**CRED, PAGAMENTOS_FORNECEDOR='vinti4')
class NaoExpiraComCartaoADecorrer(TestCase):

    def _pendente_vencida(self):
        dono, cliente = _utilizador('donoexp'), _utilizador('cliexp')
        loja = _loja(dono)
        m = _marcacao(loja, cliente, estado='pendente')
        m.expira_em = timezone.now() - timedelta(minutes=1)
        m.save(update_fields=['expira_em'])
        return loja, cliente, m

    def _cartao(self, loja, cliente, m, ha_minutos):
        inicio = obter('vinti4').iniciar(Cobranca(referencia=f'mar-{m.id}-cartao-1', valor=Decimal('1200'),
                                                  descricao='M', pagador=cliente, loja=loja))
        TransacaoVinti4.objects.filter(ref=inicio.campos['merchantRef']).update(
            criada_em=timezone.now() - timedelta(minutes=ha_minutos))

    def test_espera_pela_sisp(self):
        from .servicos import marcacoes as ops
        loja, cliente, m = self._pendente_vencida()
        self._cartao(loja, cliente, m, 2)
        self.assertEqual(ops.expirar_vencidas(pk=m.pk), 0)
        m.refresh_from_db()
        self.assertEqual(m.estado, 'pendente')

    def test_passados_os_8_minutos_expira(self):
        from .servicos import marcacoes as ops
        loja, cliente, m = self._pendente_vencida()
        self._cartao(loja, cliente, m, 9)
        self.assertEqual(ops.expirar_vencidas(pk=m.pk), 1)

    def test_o_cartao_de_outra_marcacao_nao_conta(self):
        from .servicos import marcacoes as ops
        loja, cliente, m = self._pendente_vencida()
        outra = _marcacao(loja, cliente, estado='pendente')
        self._cartao(loja, cliente, outra, 1)
        self.assertEqual(ops.expirar_vencidas(pk=m.pk), 1)


class RegraGeralDoPagamento(TestCase):

    def setUp(self):
        from .servicos.models import ConfigServicos
        self.dono = _utilizador('donoregra')
        self.loja = _loja(self.dono)
        ConfigServicos.objects.get_or_create(loja=self.loja, defaults={'ativo': True})
        self.api = APIClient()
        self.api.force_authenticate(self.dono.user)

    def test_aplicar_a_todos_e_servico_novo(self):
        from .servicos.models import Servico
        a = Servico.objects.create(loja=self.loja, nome='A', duracao_min=30, preco=Decimal('500'), pagamento='ambos')
        b = Servico.objects.create(loja=self.loja, nome='B', duracao_min=30, preco=Decimal('500'), pagamento='local')
        url = f'/app/loja/{self.loja.id}/servicos/config/'
        r = self.api.patch(url, {'pagamento_padrao': 'antecipado'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.json()['config']['pagamento_padrao'], 'antecipado')
        a.refresh_from_db()
        self.assertEqual(a.pagamento, 'ambos')               # sem "aplicar a todos" os existentes ficam
        r = self.api.patch(url, {'pagamento_padrao': 'antecipado', 'aplicar_pagamento_a_todos': True}, format='json')
        self.assertEqual(r.json()['servicos_alterados'], 2)
        self.assertEqual(set(Servico.objects.filter(id__in=(a.id, b.id)).values_list('pagamento', flat=True)), {'antecipado'})
        self.assertEqual(self.api.patch(url, {'pagamento_padrao': 'x'}, format='json').status_code, 400)
        # um serviço novo sem escolha fica com a regra geral
        r = self.api.post(f'/app/loja/{self.loja.id}/servicos/catalogo/',
                          {'nome': 'Novo', 'duracao_min': 30, 'preco': '700'}, format='json')
        self.assertEqual(r.status_code, 201, r.content[:300])
        self.assertEqual(r.json()['pagamento'], 'antecipado')


@override_settings(PAGAMENTOS_FORNECEDOR='simulado')
class TermosNasMarcacoes(TestCase):

    def setUp(self):
        self.dono, self.cliente = _utilizador('donotermos'), _utilizador('clitermos')
        self.cliente.email_confirmado = True
        self.cliente.save(update_fields=['email_confirmado'])
        self.loja = _loja(self.dono)
        self.api = APIClient()
        self.api.force_authenticate(self.cliente.user)

    def test_marcar_sem_aceitar_os_termos(self):
        r = self.api.post(f'/app/lojas/{self.loja.id}/servicos/marcar/', {'servico_id': 1}, format='json')
        self.assertEqual((r.status_code, r.json().get('codigo')), (400, 'termos'))

    def test_pagar_uma_antiga_pede_os_termos(self):
        m = _marcacao(self.loja, self.cliente, estado='pendente')
        m.expira_em = timezone.now() + timedelta(minutes=20)
        m.save(update_fields=['expira_em'])
        url = f'/app/marcacoes/{m.id}/acao/'
        r = self.api.post(url, {'acao': 'pagar'}, format='json')
        self.assertEqual((r.status_code, r.json().get('codigo')), (400, 'termos'))
        r = self.api.post(url, {'acao': 'pagar', 'aceita_termos': True}, format='json')
        self.assertNotEqual(r.json().get('codigo'), 'termos')       # passou dos termos (a loja de teste não tem o módulo)
        m.refresh_from_db()
        self.assertIsNotNone(m.termos_aceites_em)
        r = self.api.get(f'/app/marcacoes/{m.id}/')
        self.assertTrue(r.json()['termos_aceites'])
