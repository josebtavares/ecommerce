"""
Envio por transportadora (utils/envios.py) — fase 1. Correr: python manage.py test app.test_envios
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (Encomenda, Entrega, Loja, MetodoPagamento, Notificacao, OpcaoEntrega, Pagamento, Transportadora,
                     Utilizador, UtilizadorLoja)
from .utils import envios as E
from .utils import prontidao


def _conta(username, staff=False):
    user = User.objects.create_user(username=username, email=f'{username}@exemplo.cv', password='x-Teste-123!',
                                    is_staff=staff)
    user.date_joined = timezone.now() - timedelta(days=90)
    user.save(update_fields=['date_joined'])
    u = Utilizador.objects.create(user=user, telefone='+238 991 12 23', morada='Rua 1', pais='CV', concelho='PR',
                                  email_confirmado=True)
    if staff:
        u.role_admin = 'superadmin'
        u.save(update_fields=['role_admin'])
    return u


class BaseEnvios(TestCase):

    def setUp(self):
        self.dono = _conta('envdono')
        self.loja = Loja.objects.create(dono=self.dono, nome='Loja Envios', slug='loja-envios', categoria='moda',
                                        estado='ativa', entrega_ativa=True, concelho='SV')
        UtilizadorLoja.objects.get_or_create(loja=self.loja, utilizador=self.dono, defaults={'role': 'dono', 'ativo': True})
        self.dhl = Transportadora.objects.get(nome='DHL')
        self.opcao = OpcaoEntrega.objects.create(loja=self.loja, nome='Envio Santiago', preco=Decimal('500'),
                                                 tipo='envio', transportadora=self.dhl, ilhas=['Santiago'])
        self.cliente = _conta('envcliente')
        self.api = APIClient()
        self.api.force_authenticate(self.dono.user)

    def _encomenda(self, pago=True, metodo='cartao', opcao=None):
        enc = Encomenda.objects.create(comprador=self.cliente, loja=self.loja, valor_total=Decimal('1500'),
                                       tipo_entrega='entrega', status='pago' if pago else 'pendente',
                                       morada_entrega='Rua 1, Praia', concelho_entrega='PR',
                                       opcao_entrega=opcao or self.opcao)
        m, _ = MetodoPagamento.objects.get_or_create(loja=self.loja, tipo=metodo, defaults={'ativo': True})
        Pagamento.objects.create(encomenda=enc, metodo=m, valor=enc.valor_total,
                                 status='aprovado' if pago else 'pendente',
                                 referencia_transacao='TX1' if pago else 'dinheiro')
        return enc

    def _url(self, enc, sufixo=''):
        return f'/app/loja/{self.loja.id}/encomendas/{enc.id}/envio/{sufixo}'


class Envios(BaseEnvios):

    # ── enviar ───────────────────────────────────────────────────────────────
    def test_enviar_com_codigos(self):
        enc = self._encomenda()
        r = self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': '["ab 123", "AB 123", "cd9"]'},
                          format='multipart')
        self.assertEqual(r.status_code, 200, r.content[:300])
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'enviado')
        ent = enc.entrega
        self.assertEqual((ent.tipo, ent.status, ent.condutor_id), ('envio', 'a_caminho', None))
        self.assertEqual(ent.codigos, ['AB 123', 'CD9'])          # normalizados, sem repetidos
        self.assertEqual(ent.transportadora_nome, 'DHL')
        self.assertIn('tracking-id=AB%20123', r.data['envio']['codigos'][0]['link'])
        self.assertEqual(ent.historico_envio[-1]['acao'], 'enviado')
        n = Notificacao.objects.filter(utilizador=self.cliente, tipo='encomenda_enviada').latest('id')
        self.assertIn('AB 123', n.mensagem)

    def test_enviar_com_outra_transportadora(self):
        enc = self._encomenda()
        r = self.api.post(self._url(enc), {'transportadora_outra': 'Barco Interilhas', 'codigos': ['X1']}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.data['envio']['transportadora'], 'Barco Interilhas')
        self.assertEqual(r.data['envio']['codigos'][0]['link'], '')

    def test_enviar_exige_pago_antecipado(self):
        enc = self._encomenda(pago=False, metodo='dinheiro')
        Encomenda.objects.filter(pk=enc.pk).update(status='preparando')
        r = self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('já paga', r.data['detail'])
        self.assertFalse(Entrega.objects.filter(encomenda=enc).exists())

    def test_enviar_sem_codigo_ou_transportadora(self):
        enc = self._encomenda()
        r = self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['  ']}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.post(self._url(enc), {'codigos': ['A1']}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A' * 61]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_enviar_duas_vezes(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        r = self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A2']}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_outro_utilizador_nao_envia(self):
        enc = self._encomenda()
        api = APIClient()
        api.force_authenticate(self.cliente.user)
        r = api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        self.assertEqual(r.status_code, 403)

    # ── regras com os outros caminhos ────────────────────────────────────────
    def test_status_enviado_a_mao_e_condutor_recusados(self):
        enc = self._encomenda()
        r = self.api.patch(f'/app/loja/{self.loja.id}/encomendas/{enc.id}/status/', {'status': 'enviado'}, format='json')
        self.assertEqual(r.status_code, 400, r.content[:300])
        r = self.api.post(f'/app/loja/{self.loja.id}/encomendas/{enc.id}/entrega/criar/', {}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_nao_cancela_a_caminho_e_lista_de_entregas_sem_envios(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        r = self.api.patch(f'/app/loja/{self.loja.id}/encomendas/{enc.id}/status/', {'status': 'cancelado'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.get(f'/app/loja/{self.loja.id}/entrega/lista/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'] if 'count' in r.data else len(r.data['results']), 0)

    def test_concluir_fecha_o_envio(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        r = self.api.patch(f'/app/loja/{self.loja.id}/encomendas/{enc.id}/status/', {'status': 'concluido'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        enc.refresh_from_db()
        self.assertEqual((enc.status, enc.entrega.status), ('concluido', 'entregue'))
        self.assertIsNotNone(enc.data_conclusao)

    # ── corrigir / devolvida / reenviar ──────────────────────────────────────
    def test_corrigir_codigo(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        r = self.api.post(self._url(enc, 'corrigir/'), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        self.assertEqual(r.status_code, 400)          # nada mudou
        r = self.api.post(self._url(enc, 'corrigir/'), {'transportadora_id': self.dhl.id, 'codigos': ['B2']}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        ent = Entrega.objects.get(encomenda=enc)
        self.assertEqual(ent.codigos, ['B2'])
        self.assertEqual([h['acao'] for h in ent.historico_envio], ['enviado', 'corrigido'])

    def test_devolvida_reenviar_e_cancelar(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        r = self.api.post(self._url(enc, 'devolvida/'), {'nota': 'x'}, format='json')
        self.assertEqual(r.status_code, 400)          # nota curta
        r = self.api.post(self._url(enc, 'devolvida/'), {'nota': 'Morada não encontrada'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        enc.refresh_from_db()
        self.assertEqual((enc.status, enc.entrega.status), ('preparando', 'devolvida'))
        # reenvio: mesma entrega, novo código, sem novo pagamento
        r = self.api.post(self._url(enc), {'transportadora_outra': 'Correio local', 'codigos': ['Z9']}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        ent = Entrega.objects.get(encomenda=enc)
        self.assertEqual((ent.status, ent.codigos), ('a_caminho', ['Z9']))
        self.assertEqual([h['acao'] for h in ent.historico_envio], ['enviado', 'devolvido', 'reenviado'])
        self.assertEqual(Pagamento.objects.filter(encomenda=enc).count(), 1)
        # devolvida outra vez → agora já se pode cancelar
        self.api.post(self._url(enc, 'devolvida/'), {'nota': 'Recusada pelo cliente'}, format='json')
        r = self.api.patch(f'/app/loja/{self.loja.id}/encomendas/{enc.id}/status/', {'status': 'cancelado'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])

    # ── opções, loja, prontidão, admin ───────────────────────────────────────
    def test_opcao_envio_exige_transportadora_e_ilhas(self):
        base = f'/app/loja/{self.loja.id}/entrega/opcoes/criar/'
        r = self.api.post(base, {'nome': 'Envio', 'preco': 300, 'tipo': 'envio', 'ilhas': ['Sal']}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.post(base, {'nome': 'Envio', 'preco': 300, 'tipo': 'envio', 'transportadora_id': self.dhl.id},
                          format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.post(base, {'nome': 'Envio', 'preco': 300, 'tipo': 'envio', 'transportadora_id': self.dhl.id,
                                 'ilhas': ['Sal', 'Atlântida']}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.post(base, {'nome': 'Envio', 'preco': 300, 'tipo': 'envio', 'transportadora_id': self.dhl.id,
                                 'ilhas': ['Fogo', 'Sal', 'Sal']}, format='json')
        self.assertEqual(r.status_code, 201, r.content[:300])
        self.assertEqual(r.data['ilhas'], ['Sal', 'Fogo'])
        self.assertEqual(r.data['transportadora_nome'], 'DHL')

    def test_serve_ilha(self):
        local = OpcaoEntrega.objects.create(loja=self.loja, nome='Local', preco=Decimal('100'))
        self.assertTrue(E.serve_ilha(local, 'Sal'))
        self.assertTrue(E.serve_ilha(self.opcao, 'Santiago'))
        self.assertFalse(E.serve_ilha(self.opcao, 'Sal'))
        self.assertFalse(E.serve_ilha(self.opcao, ''))

    def test_prontidao_pede_concelho_com_envio(self):
        Loja.objects.filter(pk=self.loja.pk).update(concelho='')
        self.loja.refresh_from_db()
        req = {r['chave']: r['ok'] for r in prontidao.avaliar(self.loja)['requisitos']}
        self.assertIs(req.get('concelho'), False)
        self.assertIs(req.get('envio_pagamento'), False)         # só dinheiro (nenhum método) → o envio não serve
        MetodoPagamento.objects.create(loja=self.loja, tipo='cartao', ativo=True)
        req = {r['chave']: r['ok'] for r in prontidao.avaliar(self.loja)['requisitos']}
        self.assertIs(req.get('envio_pagamento'), True)
        self.opcao.ativa = False
        self.opcao.save()
        self.assertNotIn('concelho', [r['chave'] for r in prontidao.avaliar(self.loja)['requisitos']])

    def test_admin_transportadoras(self):
        admin = _conta('envadmin', staff=True)
        api = APIClient()
        api.force_authenticate(admin.user)
        r = api.post('/app/admin/transportadoras/', {'nome': 'Rápido CV', 'url_rastreio': 'http://x/{codigo}'},
                     format='json')
        self.assertEqual(r.status_code, 400)          # tem de ser https
        r = api.post('/app/admin/transportadoras/', {'nome': 'Rápido CV', 'url_rastreio': 'https://r.cv/t/{codigo}'},
                     format='json')
        self.assertEqual(r.status_code, 201, r.content[:300])
        r = api.patch(f'/app/admin/transportadoras/{r.data["id"]}/', {'ativa': False}, format='json')
        self.assertEqual(r.status_code, 200)
        nomes = [t['nome'] for t in self.api.get('/app/transportadoras/').data]
        self.assertNotIn('Rápido CV', nomes)
        self.assertIn('CTT', nomes)
        r = self.api.post('/app/admin/transportadoras/', {'nome': 'Y'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_cliente_ve_codigos_sem_historico(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        api = APIClient()
        api.force_authenticate(self.cliente.user)
        r = api.get(f'/app/encomenda/{enc.id}/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertTrue(r.data['e_envio'])
        self.assertEqual(r.data['envio']['codigos'][0]['codigo'], 'A1')
        self.assertNotIn('historico', r.data['envio'])


class EnviosCliente(BaseEnvios):
    """Fase 2: checkout por ilha, sem dinheiro no envio, "Recebi" / "Não recebi"."""

    def setUp(self):
        super().setUp()
        from .models import Inventario, Produto
        self.produto = Produto.objects.create(loja=self.loja, nome='Camisa', preco=Decimal('1000'))
        Inventario.objects.update_or_create(produto=self.produto, defaults={'loja': self.loja, 'quantidade': 50})
        self.local = OpcaoEntrega.objects.create(loja=self.loja, nome='Mindelo', preco=Decimal('100'), ilhas=['São Vicente'])
        MetodoPagamento.objects.get_or_create(loja=self.loja, tipo='dinheiro', defaults={'ativo': True})
        self.capi = APIClient()
        self.capi.force_authenticate(self.cliente.user)

    def _checkout(self, opcao, concelho, **extra):
        self.capi.post(f'/app/loja/{self.loja.id}/carrinho/adicionar/', {'produto_id': self.produto.id, 'quantidade': 1},
                       format='json')
        corpo = {'tipo_entrega': 'entrega', 'opcao_entrega_id': opcao.id, 'morada_entrega': 'Rua 1',
                 'aceita_termos': True, **({'concelho_entrega': concelho} if concelho is not None else {}), **extra}
        return self.capi.post(f'/app/loja/{self.loja.id}/encomenda/criar/', corpo, format='json')

    def test_checkout_exige_concelho_e_ilha_servida(self):
        r = self._checkout(self.opcao, None)
        self.assertEqual(r.status_code, 400)
        self.assertIn('concelho', r.data['detail'])
        r = self._checkout(self.opcao, 'SV')                   # envio só para Santiago
        self.assertEqual(r.status_code, 400)
        self.assertIn('São Vicente', r.data['detail'])
        r = self._checkout(self.local, 'PR')                   # local só em São Vicente
        self.assertEqual(r.status_code, 400)
        r = self._checkout(self.opcao, 'pr', metodo_pagamento='cartao')
        self.assertEqual(r.status_code, 201, r.content[:300])
        self.assertEqual(Encomenda.objects.get(id=r.data['id']).concelho_entrega, 'PR')

    def test_envio_sem_dinheiro_nem_hora(self):
        r = self._checkout(self.opcao, 'PR', metodo_pagamento='dinheiro')
        self.assertEqual(r.status_code, 400)
        self.assertIn('antecipado', r.data['detail'])
        r = self._checkout(self.opcao, 'PR', agendar_para='2030-01-01T10:00')
        self.assertEqual(r.status_code, 400)
        # mesmo que o browser não diga o método ao criar, o pagamento em dinheiro é recusado
        r = self._checkout(self.opcao, 'PR')
        self.assertEqual(r.status_code, 201, r.content[:300])
        r = self.capi.post('/app/pagamento/iniciar/', {'encomenda_id': r.data['id'], 'metodo': 'dinheiro'}, format='json')
        self.assertEqual(r.status_code, 400, r.content[:300])
        self.assertFalse(Pagamento.objects.filter(encomenda__comprador=self.cliente).exists())

    def test_local_aceita_dinheiro(self):
        r = self._checkout(self.local, 'SV', metodo_pagamento='dinheiro')
        self.assertEqual(r.status_code, 201, r.content[:300])

    def _enviada(self):
        enc = self._encomenda()
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        return enc

    def test_recebi(self):
        enc = self._encomenda()
        r = self.capi.post(f'/app/encomenda/{enc.id}/envio/recebi/')
        self.assertEqual(r.status_code, 400)                   # ainda não foi enviada
        self.api.post(self._url(enc), {'transportadora_id': self.dhl.id, 'codigos': ['A1']}, format='json')
        outro = APIClient()
        outro.force_authenticate(self.dono.user)
        self.assertEqual(outro.post(f'/app/encomenda/{enc.id}/envio/recebi/').status_code, 404)
        r = self.capi.post(f'/app/encomenda/{enc.id}/envio/recebi/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        enc.refresh_from_db()
        self.assertEqual((enc.status, enc.entrega.status), ('concluido', 'entregue'))
        self.assertIsNotNone(enc.data_conclusao)
        self.assertTrue(Notificacao.objects.filter(utilizador=self.dono, tipo='encomenda_concluida_loja').exists())
        self.assertEqual(self.capi.post(f'/app/encomenda/{enc.id}/envio/recebi/').status_code, 400)

    def test_nao_recebi(self):
        enc = self._enviada()
        r = self.capi.post(f'/app/encomenda/{enc.id}/envio/nao-recebi/', {'nota': 'Passaram 10 dias'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        ent = Entrega.objects.get(encomenda=enc)
        self.assertIsNotNone(ent.nao_recebido_em)
        n = Notificacao.objects.filter(utilizador=self.dono).latest('id')
        self.assertIn('não recebeu', n.titulo)
        self.assertIn('Passaram 10 dias', n.mensagem)
        self.assertEqual(self.capi.post(f'/app/encomenda/{enc.id}/envio/nao-recebi/').status_code, 400)
        r = self.api.get(f'/app/encomenda/{enc.id}/')
        self.assertIsNotNone(r.data['envio']['nao_recebido_em'])
        # a loja corrige o código → o aviso sai
        self.api.post(self._url(enc, 'corrigir/'), {'transportadora_id': self.dhl.id, 'codigos': ['A2']}, format='json')
        ent.refresh_from_db()
        self.assertIsNone(ent.nao_recebido_em)

    def test_afinal_recebi_depois_de_nao_recebi(self):
        enc = self._enviada()
        self.capi.post(f'/app/encomenda/{enc.id}/envio/nao-recebi/', {}, format='json')
        r = self.capi.post(f'/app/encomenda/{enc.id}/envio/recebi/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'concluido')
        # já concluída: "não recebi" deixa de fazer sentido
        self.assertEqual(self.capi.post(f'/app/encomenda/{enc.id}/envio/nao-recebi/').status_code, 400)
