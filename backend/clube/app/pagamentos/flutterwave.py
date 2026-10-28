"""
Flutterwave (Standard): página de pagamento alojada, regresso com ?transaction_id=&tx_ref=, aviso por webhook.
O dinheiro entra na conta da plataforma (sem divisão por subconta — as lojas só dão os dados bancários).
Cada confirmação é verificada na API (GET /transactions/<id>/verify), mesmo a do webhook assinado.
"""
import hmac
import os
from decimal import Decimal

import requests

from ..utils.dinheiro import valor_cobranca
from .base import Confirmacao, ErroPagamento, Fornecedor, Inicio

BASE = 'https://api.flutterwave.com/v3'


def _headers():
    return {'Authorization': f'Bearer {os.environ.get("FLW_SECRET_KEY", "")}', 'Content-Type': 'application/json'}


class Flutterwave(Fornecedor):
    codigo = 'flutterwave'
    nome = 'Flutterwave'

    def _pedido(self, metodo, caminho, **kw):
        try:
            resp = requests.request(metodo, BASE + caminho, headers=_headers(), timeout=15, **kw)
            corpo = resp.json()
        except (requests.RequestException, ValueError):
            raise ErroPagamento('O serviço de pagamentos não respondeu. Tenta outra vez daqui a pouco.')
        if resp.status_code != 200 or corpo.get('status') != 'success':
            raise ErroPagamento('O serviço de pagamentos recusou o pedido.')
        return corpo.get('data') or {}

    def iniciar(self, cobranca):
        valor, moeda = valor_cobranca(cobranca.valor, self.codigo)
        dados = self._pedido('POST', '/payments', json={
            'tx_ref': cobranca.referencia,
            'amount': float(valor),
            'currency': moeda,
            'redirect_url': cobranca.regresso,
            'customer': {'email': cobranca.cliente.get('email', ''), 'name': cobranca.cliente.get('nome', ''),
                         'phonenumber': cobranca.cliente.get('telefone', '')},
            'customizations': {'title': cobranca.titulo, 'description': cobranca.descricao, 'logo': cobranca.logo},
        })
        return Inicio('redirecionar', url=dados.get('link', ''))

    def _verificar(self, transaction_id):
        if not str(transaction_id or '').isdigit():
            raise ErroPagamento('Transacção inválida.')
        d = self._pedido('GET', f'/transactions/{transaction_id}/verify')
        try:
            valor = Decimal(str(d.get('amount', 0)))
        except Exception:
            valor = Decimal('0')
        return Confirmacao(sucesso=d.get('status') == 'successful', referencia=str(d.get('tx_ref') or ''),
                           transacao=f'flw_{d.get("id", transaction_id)}', valor=valor,
                           moeda=str(d.get('currency') or ''), motivo=str(d.get('status') or ''))

    def confirmar_regresso(self, dados):
        if dados.get('status') == 'cancelled':
            return Confirmacao(sucesso=False, referencia=str(dados.get('tx_ref') or ''), transacao='',
                               motivo='cancelado')
        return self._verificar(dados.get('transaction_id'))

    def ler_webhook(self, request):
        segredo = os.environ.get('FLW_SECRET_HASH', '')
        # sem hash configurado não há forma de validar → recusa
        if not segredo or not hmac.compare_digest(request.META.get('HTTP_VERIF_HASH', ''), segredo):
            raise ErroPagamento('Assinatura inválida.')
        corpo = request.data if isinstance(request.data, dict) else {}
        dados = corpo.get('data') if isinstance(corpo.get('data'), dict) else {}
        if corpo.get('event') != 'charge.completed':
            return None
        return self._verificar(dados.get('id'))

    def reembolsar(self, transacao, valor, chave=''):
        valor_flw, _ = valor_cobranca(valor, self.codigo)
        d = self._pedido('POST', f'/transactions/{transacao.removeprefix("flw_")}/refund',
                         json={'amount': float(valor_flw)})
        return f'flw_refund_{d.get("id", "")}'
