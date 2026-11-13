"""A página inicial é "/": botões da landing com /Home passam a "/" (ao gravar e ao mostrar)."""
from django.test import SimpleTestCase

from app.utils import landing as L


class BotoesDaPaginaInicial(SimpleTestCase):
    def test_inicio(self):
        for antigo in ('/Home', '/home', '/HOME/', '/Home/'):
            self.assertEqual(L._inicio(antigo), '/')
        for outro in ('/', '/homes', '/loja/criar', '#entrar', 'https://x.cv/Home', None):
            self.assertEqual(L._inicio(outro), outro)

    def test_botoes_gravados(self):
        r = L._botoes_inicio({'tipo': 'hero', 'botao': {'texto': 'Ir', 'link': '/Home'}, 'botao2': {'texto': 'C', 'link': '#criar-conta'},
                              'itens': [{'titulo': 'a', 'botao': {'texto': 'b', 'link': '/home'}}, 'x'], 'titulo': 'T'})
        self.assertEqual(r['botao']['link'], '/')
        self.assertEqual(r['botao2']['link'], '#criar-conta')
        self.assertEqual(r['itens'][0]['botao']['link'], '/')
        self.assertEqual(r['itens'][1], 'x')
        self.assertEqual(r['titulo'], 'T')

    def test_validar_grava_barra(self):
        self.assertEqual(L._valor(('botao',), {'texto': 'Ir', 'link': '/Home'}, 'botao', set())['link'], '/')
