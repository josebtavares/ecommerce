"""
O cliente não consegue mudar o que paga (inspect, pedidos feitos à mão). Correr: python manage.py test app.test_precos

O total de uma encomenda é sempre calculado no servidor a partir da base de dados (preço do produto/variante,
opção de entrega da loja); o valor que vai à SISP está assinado no FingerPrint; e na confirmação o valor pago tem de
bater com o guardado. Cada teste tenta uma forma de enganar e confirma que não serve.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Carrinho, Encomenda, Inventario, Loja, OpcaoEntrega, Produto, Utilizador, UtilizadorLoja
from .pagamentos import ErroPagamento
from .pagamentos import servico
from .pagamentos import vinti4 as v4
from .pagamentos.base import Confirmacao

PRECO = Decimal('1500.00')


def _conta(username):
    user = User.objects.create_user(username=username, email=f'{username}@exemplo.cv', password='x-Teste-123!')
    user.date_joined = timezone.now() - timedelta(days=90)
    user.save(update_fields=['date_joined'])
    return Utilizador.objects.create(user=user, telefone='+238 991 12 23', morada='Achada Santo António, Rua 1',
                                     pais='CV', concelho='PR', email_confirmado=True)


class PrecoNoServidor(TestCase):

    def setUp(self):
        self.dono = _conta('donoprecos')
        self.loja = Loja.objects.create(dono=self.dono, nome='Loja Preços', slug='loja-precos', categoria='moda',
                                        estado='ativa', entrega_ativa=True)
        UtilizadorLoja.objects.get_or_create(loja=self.loja, utilizador=self.dono, defaults={'role': 'dono', 'ativo': True})
        self.produto = Produto.objects.create(loja=self.loja, nome='Camisa', preco=PRECO)
        Inventario.objects.update_or_create(produto=self.produto, defaults={'loja': self.loja, 'quantidade': 50})
        self.entrega = OpcaoEntrega.objects.create(loja=self.loja, nome='Standard', preco=Decimal('200.00'))
        self.cliente = _conta('clienteprecos')
        self.api = APIClient()
        self.api.force_authenticate(self.cliente.user)

    def _adicionar(self, **extra):
        return self.api.post(f'/app/loja/{self.loja.id}/carrinho/adicionar/',
                             {'produto_id': self.produto.id, 'quantidade': 2, **extra}, format='json')

    def _encomendar(self, **extra):
        corpo = {'tipo_entrega': 'entrega', 'opcao_entrega_id': self.entrega.id, 'morada_entrega': 'Rua 1, Praia',
                 'aceita_termos': True, **extra}
        return self.api.post(f'/app/loja/{self.loja.id}/encomenda/criar/', corpo, format='json')

    def test_precos_mudados_no_pedido_sao_ignorados(self):
        # o carrinho ignora preços enviados pelo browser
        r = self._adicionar(preco='1.00', preco_unitario='1.00', valor='1.00', total='1.00')
        self.assertIn(r.status_code, (200, 201), r.content[:300])
        # a encomenda também: o total vem da base de dados (2 × 1500 + entrega 200)
        r = self._encomendar(valor_total='1.00', total='1.00', subtotal='1.00', custo_entrega='0', preco='1.00',
                             desconto='3000', itens=[{'produto_id': self.produto.id, 'preco': '1.00', 'quantidade': 2}])
        self.assertIn(r.status_code, (200, 201), r.content[:300])
        enc = Encomenda.objects.get(comprador=self.cliente)
        self.assertEqual(enc.valor_total, PRECO * 2 + Decimal('200.00'))
        self.assertEqual([(i.preco, i.quantidade) for i in enc.itens.all()], [(PRECO, 2)])

    def test_preco_mudado_depois_de_ir_para_o_carrinho(self):
        # o preço conta no momento de encomendar (a loja muda-o, o cliente não)
        self._adicionar()
        Produto.objects.filter(pk=self.produto.pk).update(preco=Decimal('1800.00'))
        self._encomendar()
        self.assertEqual(Encomenda.objects.get(comprador=self.cliente).valor_total, Decimal('3800.00'))

    def test_quantidades_negativas_ou_zero(self):
        for q in (0, -1, -5, '-3', 'abc', 2.5):
            r = self._adicionar(quantidade=q)
            self.assertEqual(r.status_code, 400, (q, r.content[:200]))
        self.assertFalse(Carrinho.objects.filter(utilizador=self.cliente, itens__isnull=False).exists())
        # um item já no carrinho: pôr quantidade negativa tira-o, nunca baixa o total
        self._adicionar()
        item = Carrinho.objects.get(utilizador=self.cliente, loja=self.loja).itens.get()
        self.api.patch(f'/app/loja/{self.loja.id}/carrinho/item/{item.id}/', {'quantidade': -4}, format='json')
        r = self._encomendar()
        if r.status_code in (200, 201):
            self.assertGreaterEqual(Encomenda.objects.get(comprador=self.cliente).valor_total, Decimal('0'))
            self.assertTrue(all(i.quantidade > 0 for i in Encomenda.objects.get(comprador=self.cliente).itens.all()))

    def test_entrega_de_outra_loja_ou_inativa(self):
        outra_loja = Loja.objects.create(dono=self.dono, nome='Outra', slug='outra-precos', categoria='moda', estado='ativa')
        gratis = OpcaoEntrega.objects.create(loja=outra_loja, nome='Grátis', preco=Decimal('0'))
        inativa = OpcaoEntrega.objects.create(loja=self.loja, nome='Velha', preco=Decimal('0'), ativa=False)
        self._adicionar()
        for opcao in (gratis.id, inativa.id, 999999):
            r = self._encomendar(opcao_entrega_id=opcao)
            self.assertEqual(r.status_code, 400, (opcao, r.content[:200]))
        self.assertFalse(Encomenda.objects.filter(comprador=self.cliente).exists())

    def test_valor_pago_diferente_nao_paga_a_encomenda(self):
        self._adicionar()
        self._encomendar()
        enc = Encomenda.objects.get(comprador=self.cliente)
        ref = servico.nova_referencia('enc', enc.id, 'cartao')
        menos = Confirmacao(sucesso=True, referencia=ref, transacao='v4_1-1', valor=Decimal('1.00'),
                            moeda=servico.valor_cobranca(enc.valor_total, 'vinti4')[1])
        with self.assertRaisesMessage(ErroPagamento, 'não corresponde'):
            servico.confirmar(v4.FORNECEDOR, menos)
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'pendente')


@override_settings(VINTI4_POS_ID='90051', VINTI4_POS_AUT_CODE='123456789A', API_BASE_URL='https://api.exemplo.cv',
                   VINTI4_URL='https://3dsteste.vinti4net.cv/3ds_middleware_php/public/3ds_init.php')
class FormularioDaSisp(TestCase):
    """O valor do formulário que o browser envia à SISP está assinado: mudá-lo estraga o FingerPrint."""

    def test_valor_alterado_no_formulario(self):
        from .pagamentos.base import Cobranca
        u = _conta('clientesisp')
        inicio = v4.FORNECEDOR.iniciar(Cobranca(referencia='fat-7-cartao-1', valor=Decimal('1500'), descricao='T',
                                                pagador=u))
        c = inicio.campos
        refazer = lambda montante: v4.fingerprint_pedido('123456789A', c['TimeStamp'], montante,     # noqa: E731
                                                         c['merchantRef'], c['merchantSession'], c['posID'])
        self.assertEqual(c['FingerPrint'], refazer(c['amount']))         # o que a SISP calcula com o valor certo
        self.assertNotEqual(c['FingerPrint'], refazer('1'))                # com o valor mudado já não bate
        # e sem a chave não se consegue fazer outro válido
        self.assertNotEqual(c['FingerPrint'], v4.fingerprint_pedido('', c['TimeStamp'], '1', c['merchantRef'],
                                                                     c['merchantSession'], c['posID']))
        self.assertNotIn('123456789A', str(c))                             # a chave nunca vai para o browser
