"""
Tratamento de erros da API.

Muitas views fazem int(request.GET['offset']), filter(id=request.data['x']), etc. Com texto onde se
esperava um número rebentavam com erro 500 (a auditoria geral encontrou 26 endpoints assim).
Um valor mal formado é um erro do pedido, não do servidor: passa a 400.
A transacção da view já foi desfeita quando chega aqui (a excepção saiu do atomic).
"""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

log = logging.getLogger(__name__)


def tratar_excecao(exc, context):
    resposta = exception_handler(exc, context)
    if resposta is not None:
        return resposta
    if isinstance(exc, (ValueError, DjangoValidationError)):
        view = context.get('view')
        log.warning('Pedido inválido em %s: %r', getattr(view, '__class__', type(view)).__name__, exc, exc_info=exc)
        detalhe = 'Pedido inválido: há um valor com formato errado.'
        if isinstance(exc, DjangoValidationError) and exc.messages:
            detalhe = ' '.join(exc.messages)      # p.ex. "Tipo de ficheiro não permitido (.svg)…"
        return Response({'detail': detalhe}, status=status.HTTP_400_BAD_REQUEST)
    return None
