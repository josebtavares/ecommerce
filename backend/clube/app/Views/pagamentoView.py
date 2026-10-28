"""
Pagamentos das encomendas e regresso/avisos dos fornecedores (a lógica está em app/pagamentos).

POST /app/pagamento/iniciar/            { encomenda_id, metodo } → { estado: aprovado|pendente|redirecionar, redirecionar? }
POST /app/pagamento/regresso/           { fornecedor, ...o que o fornecedor pôs no endereço de regresso }
POST /app/pagamento/<fornecedor>/aviso/ webhook do fornecedor (sem utilizador: a autenticidade vem da assinatura)

Antigos, mantidos para quem tem o checkout aberto durante um deploy e para o webhook já configurado no
Flutterwave: pagamento/dinheiro/, pagamento/mbway/, pagamento/flutterwave/verificar/ e /webhook/.
"""
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from django_ratelimit.core import is_ratelimited

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..pagamentos import ErroPagamento, obter
from ..pagamentos import servico as pagamentos
from ..utils.encomendas import expirar_encomenda, MSG_EXPIROU, PRAZO_PAGAMENTO_MIN
from ..models import Encomenda, MetodoPagamento, Loja, UtilizadorLoja
from ..Serializers.PagamentoSerializer import MetodoPagamentoSerializer, PagamentoSerializer

log = logging.getLogger(__name__)

# o que uma loja pode ligar: os pagos online passam pelo fornecedor da plataforma (a loja não configura nada)
METODOS_LOJA = ('dinheiro', 'transferencia', 'cartao', 'mobile_money')


def _verificar_encomenda(request, encomenda_id):
    """
    A encomenda do comprador, por pagar e bloqueada (as views de pagamento são atómicas: o worker
    que cancela as expiradas não lhe mexe enquanto o pagamento decorre).
    """
    utilizador = request.user.utilizador
    if not str(encomenda_id or '').isdigit():
        return None, Response({'detail': 'Encomenda inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    encomenda  = get_object_or_404(Encomenda.objects.select_for_update(of=('self',)).select_related('loja'),
                                   id=encomenda_id)
    if encomenda.comprador != utilizador:
        return None, Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
    if expirar_encomenda(encomenda):
        return None, Response({'detail': MSG_EXPIROU.format(min=PRAZO_PAGAMENTO_MIN), 'codigo': 'encomenda_expirada'},
                              status=status.HTTP_400_BAD_REQUEST)
    if encomenda.status != 'pendente':
        return None, Response({'detail': f'Encomenda ja esta: {encomenda.status}'}, status=status.HTTP_400_BAD_REQUEST)
    if not encomenda.loja.ativa:
        return None, Response({'detail': 'Esta loja não está a aceitar pagamentos de momento.'},
                              status=status.HTTP_400_BAD_REQUEST)
    return encomenda, None


# ══════════════════════════════════════════════════════════════
# METODOS DE PAGAMENTO DA LOJA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metodos_loja(request, loja_id):
    loja    = get_object_or_404(Loja, id=loja_id, ativa=True)
    metodos = MetodoPagamento.objects.filter(loja=loja, ativo=True)
    return Response(MetodoPagamentoSerializer(metodos, many=True).data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def metodo_gerir(request, loja_id, tipo):
    loja = get_object_or_404(Loja, id=loja_id)
    membro = UtilizadorLoja.obter_membro(loja, request.user.utilizador)
    if not membro or not membro.pode('gerir_metodos_pagamento'):
        return Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'POST':
        # os antigos (flutterwave, mbway, stripe, paypal) só se desligam
        if tipo not in METODOS_LOJA:
            return Response({'detail': 'Método de pagamento inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        metodo, _ = MetodoPagamento.objects.get_or_create(loja=loja, tipo=tipo)
        metodo.ativo = True
        metodo.save()
        return Response(MetodoPagamentoSerializer(metodo).data)
    metodo = get_object_or_404(MetodoPagamento, loja=loja, tipo=tipo)
    metodo.ativo = False
    metodo.save()
    return Response({'detail': f'Metodo {tipo} desactivado.'})


# ══════════════════════════════════════════════════════════════
# PAGAR UMA ENCOMENDA
# ══════════════════════════════════════════════════════════════

def _dados(request):
    return request.data if isinstance(request.data, dict) else {}


def _iniciar(request, tipo_metodo):
    encomenda, erro = _verificar_encomenda(request, _dados(request).get('encomenda_id'))
    if erro:
        return erro
    try:
        inicio = pagamentos.iniciar_encomenda(encomenda, tipo_metodo, request.user.utilizador)
    except ErroPagamento as e:
        transaction.set_rollback(True)
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    pagamento = getattr(encomenda, 'pagamento', None) if inicio.estado != 'redirecionar' else None
    return Response(pagamentos.para_frontend(inicio, encomenda_id=encomenda.id,
                                    pagamento=PagamentoSerializer(pagamento).data if pagamento else None))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagamento_iniciar(request):
    return _iniciar(request, str(_dados(request).get('metodo') or ''))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_dinheiro(request):
    """Antigo: o checkout mandava por aqui o dinheiro e os métodos simulados ({ metodo })."""
    return _iniciar(request, str(_dados(request).get('metodo') or 'dinheiro'))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_com_mbway(request):
    """Antigo (MBWay simulado)."""
    return _iniciar(request, 'mbway')


# ══════════════════════════════════════════════════════════════
# REGRESSO DO CLIENTE E AVISOS DO FORNECEDOR
# ══════════════════════════════════════════════════════════════

def _confirmar(f, ler):
    try:
        conf = ler()
        if conf is None:                       # evento que não interessa (aviso)
            return Response({'detail': 'ok'})
        resultado = pagamentos.confirmar(f, conf)
    except ErroPagamento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    if resultado['estado'] == 'reembolso':
        return Response({**resultado, 'codigo': 'reembolso',
                         'detail': 'O pagamento chegou depois de já não poder ser aceite. '
                                   'Vais ser reembolsado — a equipa já foi avisada.'},
                        status=status.HTTP_409_CONFLICT)
    return Response(resultado)


# o regresso não exige sessão: só confirma o que o fornecedor diz que foi pago (verificado na API dele),
# e o cliente pode voltar noutra sessão (ex.: o POS, ou depois de a sessão expirar na página do banco)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def pagamento_regresso(request):
    dados = _dados(request)
    return _regresso(request, dados.get('fornecedor'))


def _regresso(request, fornecedor):
    # cada regresso pergunta ao fornecedor: limita quem tenta à sorte
    if is_ratelimited(request=request, group='pag_regresso', key='ip', rate='30/m', method='POST', increment=True):
        return Response({'detail': 'Demasiados pedidos. Espera um minuto.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    try:
        f = obter(fornecedor)
    except ErroPagamento as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return _confirmar(f, lambda: f.confirmar_regresso(_dados(request)))


def _aviso(request, fornecedor):
    try:
        f = obter(fornecedor)
    except ErroPagamento as e:
        return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
    resp = _confirmar(f, lambda: f.ler_webhook(request))
    if resp.status_code == status.HTTP_409_CONFLICT:       # para o fornecedor o aviso foi recebido
        return Response({'detail': 'ok'})
    if resp.status_code >= 400:
        log.warning('aviso de pagamento recusado (%s): %s', fornecedor, resp.data.get('detail'))
    return resp


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def pagamento_aviso(request, fornecedor):
    return _aviso(request, fornecedor)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def flutterwave_webhook(request):
    """Antigo endereço do webhook (o configurado no painel do Flutterwave)."""
    return _aviso(request, 'flutterwave')


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def verificar_pagamento_flutterwave(request):
    """Antigo: { transaction_id, tx_ref }."""
    return _regresso(request, 'flutterwave')
