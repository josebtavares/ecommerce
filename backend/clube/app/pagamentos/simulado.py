"""Fornecedor simulado (o activo até haver contrato com a SISP): aprova logo, não cobra nada."""
from .base import Fornecedor, Inicio


class Simulado(Fornecedor):
    codigo = 'simulado'
    nome = 'Pagamento simulado'

    def iniciar(self, cobranca):
        return Inicio('aprovado', transacao=f'SIM-{cobranca.referencia}')

    def reembolsar(self, transacao, valor, chave=''):
        return f'simulado_{chave}' if chave else 'simulado'
