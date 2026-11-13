"""Criação da loja: contactos, políticas, dados bancários (sem password) e o que falta para publicar."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import DadosBancarios, Loja, Utilizador

IBAN = 'CV64 0003 0000 4547 0691 1017 6'


class CriarLoja(TestCase):

    def setUp(self):
        user = User.objects.create_user(username='novadona', email='novadona@exemplo.cv', password='x-Teste-123!')
        user.date_joined = timezone.now() - timedelta(days=90)
        user.save(update_fields=['date_joined'])
        self.u = Utilizador.objects.create(user=user, telefone='+238 991 12 23', morada='Rua 1', pais='CV', concelho='PR',
                                           email_confirmado=True, verificado=True)
        self.api = APIClient()
        self.api.force_authenticate(user)

    def _criar(self, **extra):
        dados = {'nome': 'Loja Nova', 'descricao': 'Uma loja', 'categoria': 'moda', 'concelho': 'PR',
                 'localizacao': 'Plateau', 'template_id': 'classico', 'modelo_cobranca': 'comissao',
                 'entrega_ativa': 'false', 'levantamento_ativo': 'true', 'nif': '123456789',
                 'regime_fiscal': 'particular', 'declaracao_fiscal': 'true', 'metodos_pagamento': ['dinheiro']}
        dados.update(extra)
        return self.api.post('/app/loja/criar/', dados, format='multipart')

    def test_contactos_politicas_e_prontidao(self):
        r = self._criar(contacto_telefone='+238 900 00 00', politica_devolucao='Até 14 dias.', prazo_devolucao_dias=7)
        self.assertEqual(r.status_code, 201, r.content[:400])
        loja = Loja.objects.get(id=r.data['id'])
        self.assertEqual((loja.contacto_telefone, loja.politica_devolucao, loja.prazo_devolucao_dias),
                         ('+238 900 00 00', 'Até 14 dias.', 7))
        req = {x['chave']: x['ok'] for x in r.data['prontidao']['requisitos']}
        self.assertTrue(req['contacto'] and req['devolucoes'] and req['nif'] and req['localizacao'])
        self.assertFalse(req['produto'])                       # falta o primeiro produto

    def test_banco_na_criacao_sem_password(self):
        r = self._criar(metodos_pagamento=['dinheiro', 'transferencia'], banco='Banco Comercial do Atlântico (BCA)',
                        nib=IBAN, titular='Nova Dona')
        self.assertEqual(r.status_code, 201, r.content[:400])
        d = DadosBancarios.objects.get(loja_id=r.data['id'])
        self.assertEqual((d.nib, d.titular), ('000300004547069110176', 'Nova Dona'))
        req = {x['chave']: x['ok'] for x in r.data['prontidao']['requisitos']}
        self.assertTrue(req['banco'])

    def test_banco_invalido_nao_cria_a_loja(self):
        r = self._criar(metodos_pagamento=['transferencia'], banco='Banco Comercial do Atlântico (BCA)',
                        nib='123', titular='Nova Dona')
        self.assertEqual(r.status_code, 400)
        self.assertIn('nib', r.data)
        self.assertFalse(Loja.objects.filter(dono=self.u).exists())

    def test_sem_banco_continua_a_funcionar(self):
        r = self._criar(metodos_pagamento=['transferencia'])
        self.assertEqual(r.status_code, 201, r.content[:400])
        self.assertFalse(DadosBancarios.objects.filter(loja_id=r.data['id']).exists())
        req = {x['chave']: x['ok'] for x in r.data['prontidao']['requisitos']}
        self.assertFalse(req['banco'])

    def test_lista_de_bancos(self):
        r = self.api.get('/app/bancos/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Banco Comercial do Atlântico (BCA)', r.data)
        self.assertEqual(APIClient().get('/app/bancos/').status_code, 401)
