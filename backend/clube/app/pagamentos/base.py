"""
O que um fornecedor de pagamentos online (simulado, Flutterwave, SISP…) tem de saber fazer.

O resto da plataforma nunca fala com um fornecedor directamente: passa por pagamentos.servico, que
escolhe o fornecedor activo (settings.PAGAMENTOS_FORNECEDOR) e trata do que vem depois (encomenda paga,
marcação paga, fatura paga, reembolso pedido…). Juntar a SISP = escrever um Fornecedor novo.
"""
from dataclasses import dataclass, field
from decimal import Decimal


class ErroPagamento(Exception):
    """O fornecedor recusou ou não respondeu. A mensagem pode ser mostrada ao cliente."""


@dataclass
class Cobranca:
    referencia: str                 # a nossa (servico.nova_referencia): diz o que se paga — enc-12-cartao-…
    valor: Decimal                  # em CVE; o fornecedor converte se não aceitar escudos (dinheiro.valor_cobranca)
    descricao: str
    titulo: str = ''                # nome da loja / Bende, na página do fornecedor
    logo: str = ''
    cliente: dict = field(default_factory=dict)      # {email, nome, telefone}
    regresso: str = ''              # para onde o fornecedor manda o cliente depois de pagar


@dataclass
class Inicio:
    """
    aprovado     → pago já (transacao preenchida)
    redirecionar → o cliente vai à página do fornecedor: GET url, ou POST de um formulário (campos)
    """
    estado: str
    transacao: str = ''
    url: str = ''
    metodo_http: str = 'GET'
    campos: dict = field(default_factory=dict)


@dataclass
class Confirmacao:
    """O que o fornecedor diz de uma transacção (já verificada junto dele, nunca só o que o browser trouxe)."""
    sucesso: bool
    referencia: str                 # a nossa
    transacao: str                  # a dele (com prefixo: flw_123)
    valor: Decimal = Decimal('0')
    moeda: str = ''
    motivo: str = ''


class Fornecedor:
    codigo = ''
    nome = ''

    def iniciar(self, cobranca):
        """Cobranca → Inicio."""
        raise NotImplementedError

    def confirmar_regresso(self, dados):
        """Dados com que o cliente voltou (query da página de regresso) → Confirmacao, verificada no fornecedor."""
        raise ErroPagamento('Este fornecedor não usa página de regresso.')

    def ler_webhook(self, request):
        """Aviso do fornecedor → Confirmacao, None (evento que não interessa) ou ErroPagamento (assinatura inválida)."""
        raise ErroPagamento('Este fornecedor não envia avisos.')

    def reembolsar(self, transacao, valor, chave=''):
        """Devolve `valor` (CVE) da transacção → a referência do reembolso."""
        raise NotImplementedError
