"""
Pagamentos online — uma só porta para todos os fornecedores.

  base.py         o contrato de um fornecedor (iniciar, confirmar regresso/aviso, reembolsar)
  simulado.py     o activo enquanto não houver contrato (aprova logo, não cobra)
  flutterwave.py  página alojada do Flutterwave
  servico.py      o que acontece a seguir: encomenda/marcação/fatura paga, reembolsos

O fornecedor é da PLATAFORMA (settings.PAGAMENTOS_FORNECEDOR), nunca da loja: a loja só escolhe que
métodos aceita (cartão, mobile money…) e dá os dados bancários.
"""
from django.conf import settings

from .base import Cobranca, Confirmacao, ErroPagamento, Fornecedor, Inicio
from .flutterwave import Flutterwave
from .simulado import Simulado

__all__ = ['Cobranca', 'Confirmacao', 'ErroPagamento', 'Fornecedor', 'Inicio', 'FORNECEDORES', 'obter', 'ativo', 'cobra_a_serio']

FORNECEDORES = {f.codigo: f for f in (Simulado(), Flutterwave())}


def obter(codigo):
    f = FORNECEDORES.get(codigo) if isinstance(codigo, str) else None
    if not f:
        raise ErroPagamento('Fornecedor de pagamentos desconhecido.')
    return f


def ativo():
    return obter(getattr(settings, 'PAGAMENTOS_FORNECEDOR', 'simulado'))


def cobra_a_serio():
    """O fornecedor activo cobra dinheiro real (não é o simulado)."""
    return ativo().codigo != 'simulado'
