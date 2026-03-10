import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    Encomenda, Pagamento, MetodoPagamento,
    CartaoGuardado, UtilizadorLoja, Loja,
)
from ..Serializers.PagamentoSerializer import (
    CartaoGuardadoSerializer,
    MetodoPagamentoSerializer,
    PagamentoSerializer,
    PagarComCartaoSerializer,
    PagarComMBWaySerializer,
    PagarComDinheiroSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _get_ou_criar_stripe_customer(utilizador) -> str:
    """
    Devolve o stripe_customer_id existente ou cria um novo no Stripe.
    Guarda o ID no primeiro cartão do utilizador ou num campo auxiliar.
    """
    # verifica se já tem customer_id nalgum cartão
    cartao = CartaoGuardado.objects.filter(utilizador=utilizador).first()
    if cartao:
        return cartao.stripe_customer_id

    # cria novo customer no Stripe
    customer = stripe.Customer.create(
        email=utilizador.email,
        name=utilizador.nome,
        metadata={'utilizador_id': utilizador.id}
    )
    return customer.id


def _verificar_encomenda(request, encomenda_id):
    """Valida que a encomenda pertence ao utilizador e está pendente."""
    utilizador = request.user.utilizador
    encomenda  = get_object_or_404(Encomenda, id=encomenda_id)

    if encomenda.comprador != utilizador:
        return None, Response(
            {'detail': 'Sem permissão.'},
            status=status.HTTP_403_FORBIDDEN
        )
    if encomenda.status != 'pendente':
        return None, Response(
            {'detail': f'Encomenda já está: {encomenda.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return encomenda, None


def _registar_pagamento(encomenda, metodo, stripe_intent_id, valor):
    """Cria o registo de pagamento e actualiza o status da encomenda."""
    pagamento = Pagamento.objects.create(
        encomenda            = encomenda,
        metodo               = metodo,
        valor                = valor,
        status               = 'aprovado',
        referencia_transacao = stripe_intent_id,
    )
    encomenda.status = 'pago'
    encomenda.save(update_fields=['status'])
    return pagamento


# ══════════════════════════════════════════════════════════════
# CARTÕES GUARDADOS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cartao_list(request):
    """GET /app/pagamento/cartoes/ — lista cartões guardados do utilizador"""
    cartoes = CartaoGuardado.objects.filter(utilizador=request.user.utilizador)
    serializer = CartaoGuardadoSerializer(cartoes, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def cartao_remover(request, id):
    """
    DELETE /app/pagamento/cartoes/<id>/remover/
    Remove o cartão guardado localmente e no Stripe.
    """
    utilizador = request.user.utilizador
    cartao     = get_object_or_404(CartaoGuardado, id=id, utilizador=utilizador)

    try:
        stripe.PaymentMethod.detach(cartao.stripe_payment_id)
    except stripe.error.StripeError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    cartao.delete()
    return Response({'detail': 'Cartão removido.'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cartao_predefinir(request, id):
    """PATCH /app/pagamento/cartoes/<id>/predefinir/"""
    utilizador = request.user.utilizador
    cartao     = get_object_or_404(CartaoGuardado, id=id, utilizador=utilizador)
    cartao.predefinido = True
    cartao.save()  # o save() do modelo trata de desmarcar os outros
    return Response(CartaoGuardadoSerializer(cartao).data)


# ══════════════════════════════════════════════════════════════
# MÉTODOS DE PAGAMENTO DA LOJA
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metodos_loja(request, loja_id):
    """GET /app/loja/<loja_id>/pagamento/metodos/ — métodos activos da loja"""
    loja    = get_object_or_404(Loja, id=loja_id, ativa=True)
    metodos = MetodoPagamento.objects.filter(loja=loja, ativo=True)
    serializer = MetodoPagamentoSerializer(metodos, many=True)
    return Response(serializer.data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def metodo_gerir(request, loja_id, tipo):
    """
    POST   /app/loja/<loja_id>/pagamento/metodos/<tipo>/  → activa método
    DELETE /app/loja/<loja_id>/pagamento/metodos/<tipo>/  → desactiva método
    """
    loja = get_object_or_404(Loja, id=loja_id)

    try:
        membro = UtilizadorLoja.objects.get(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    if not membro.pode('gerir_metodos_pagamento'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    metodo, _ = MetodoPagamento.objects.get_or_create(loja=loja, tipo=tipo)

    if request.method == 'POST':
        metodo.ativo = True
        metodo.save()
        return Response(MetodoPagamentoSerializer(metodo).data)

    metodo.ativo = False
    metodo.save()
    return Response({'detail': f'Método {tipo} desactivado.'})


# ══════════════════════════════════════════════════════════════
# PAGAR COM CARTÃO (Stripe)
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_com_cartao(request):
    """
    POST /app/pagamento/cartao/
    Body:
      { encomenda_id, cartao_id }              ← cartão já guardado
      { encomenda_id, payment_method_id }      ← novo cartão via Stripe.js
      { encomenda_id, payment_method_id,
        guardar_cartao: true }                 ← novo cartão + guardar

    Fluxo:
      1) Frontend usa Stripe.js para tokenizar → devolve payment_method_id
      2) Envia payment_method_id para esta view
      3) View cria PaymentIntent no Stripe e confirma
      4) Se sucesso → regista pagamento + muda status encomenda
    """
    serializer = PagarComCartaoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data       = serializer.validated_data
    utilizador = request.user.utilizador

    # valida encomenda
    encomenda, erro = _verificar_encomenda(request, data['encomenda_id'])
    if erro:
        return erro

    # verifica que a loja aceita cartão
    metodo = MetodoPagamento.objects.filter(
        loja=encomenda.loja, tipo='cartao', ativo=True
    ).first()
    if not metodo:
        return Response(
            {'detail': 'Esta loja não aceita pagamento por cartão.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # ── obtém ou cria customer no Stripe ──────────────────
        customer_id = _get_ou_criar_stripe_customer(utilizador)

        # ── determina o payment_method a usar ─────────────────
        if data.get('cartao_id'):
            cartao = get_object_or_404(
                CartaoGuardado, id=data['cartao_id'], utilizador=utilizador
            )
            payment_method_id = cartao.stripe_payment_id
        else:
            payment_method_id = data['payment_method_id']
            # anexa o novo método ao customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )

        # ── cria e confirma o PaymentIntent ───────────────────
        valor_centimos = int(encomenda.valor_total * 100)  # Stripe usa centimos
        intent = stripe.PaymentIntent.create(
            amount         = valor_centimos,
            currency       = 'eur',
            customer       = customer_id,
            payment_method = payment_method_id,
            confirm        = True,
            metadata       = {
                'encomenda_id'  : encomenda.id,
                'utilizador_id' : utilizador.id,
            },
            # sem redirect para pagamentos de cartão simples
            return_url='http://localhost:8080/pagamento/sucesso',
        )

        if intent.status not in ('succeeded', 'processing'):
            return Response(
                {'detail': f'Pagamento não confirmado: {intent.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── guarda cartão se pedido ───────────────────────────
        if data.get('guardar_cartao') and not data.get('cartao_id'):
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            CartaoGuardado.objects.create(
                utilizador         = utilizador,
                stripe_customer_id = customer_id,
                stripe_payment_id  = payment_method_id,
                marca              = pm.card.brand,
                ultimos_4          = pm.card.last4,
                mes_expiracao      = pm.card.exp_month,
                ano_expiracao      = pm.card.exp_year,
                predefinido        = not CartaoGuardado.objects.filter(
                                         utilizador=utilizador
                                     ).exists(),
            )

        # ── regista pagamento ─────────────────────────────────
        pagamento = _registar_pagamento(
            encomenda, metodo, intent.id, encomenda.valor_total
        )

        return Response(
            PagamentoSerializer(pagamento).data,
            status=status.HTTP_200_OK
        )

    except stripe.error.CardError as e:
        return Response({'detail': e.user_message}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.StripeError as e:
        return Response({'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


# ══════════════════════════════════════════════════════════════
# PAGAR COM MBWAY
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_com_mbway(request):
    """
    POST /app/pagamento/mbway/
    Body: { encomenda_id, telemovel }

    Nota: MBWay real requer integração com SIBS/Stripe.
    Esta view cria o registo pendente — o webhook confirma depois.
    """
    serializer = PagarComMBWaySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data      = serializer.validated_data
    encomenda, erro = _verificar_encomenda(request, data['encomenda_id'])
    if erro:
        return erro

    metodo = MetodoPagamento.objects.filter(
        loja=encomenda.loja, tipo='mbway', ativo=True
    ).first()
    if not metodo:
        return Response(
            {'detail': 'Esta loja não aceita MBWay.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # cria pagamento pendente — webhook do SIBS confirmará
    pagamento = Pagamento.objects.create(
        encomenda = encomenda,
        metodo    = metodo,
        valor     = encomenda.valor_total,
        status    = 'pendente',
        referencia_transacao = f'mbway_{data["telemovel"]}',
    )

    return Response(
        {
            'detail'    : f'Pedido MBWay enviado para {data["telemovel"]}. Aguarda confirmação.',
            'pagamento' : PagamentoSerializer(pagamento).data,
        },
        status=status.HTTP_200_OK
    )


# ══════════════════════════════════════════════════════════════
# PAGAR NA ENTREGA (dinheiro / levantamento)
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_dinheiro(request):
    """
    POST /app/pagamento/dinheiro/
    Body: { encomenda_id }
    Regista pagamento em dinheiro — confirmado pelo staff na entrega/levantamento.
    """
    serializer = PagarComDinheiroSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    encomenda, erro = _verificar_encomenda(request, serializer.validated_data['encomenda_id'])
    if erro:
        return erro

    metodo = MetodoPagamento.objects.filter(
        loja=encomenda.loja, tipo='dinheiro', ativo=True
    ).first()
    if not metodo:
        return Response(
            {'detail': 'Esta loja não aceita pagamento em dinheiro.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    pagamento = Pagamento.objects.create(
        encomenda = encomenda,
        metodo    = metodo,
        valor     = encomenda.valor_total,
        status    = 'pendente',  # confirmado pelo staff na entrega
        referencia_transacao = 'dinheiro',
    )

    # muda para pago — será confirmado fisicamente
    encomenda.status = 'pago'
    encomenda.save(update_fields=['status'])

    return Response(PagamentoSerializer(pagamento).data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# STRIPE WEBHOOK  (confirmações assíncronas)
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
def stripe_webhook(request):
    """
    POST /app/pagamento/webhook/stripe/
    Recebe eventos do Stripe (ex: MBWay confirmado, pagamento falhado).
    Não requer autenticação — usa assinatura do Stripe.
    """
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return Response({'detail': 'Webhook inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    # ── payment_intent.succeeded ──────────────────────────────
    if event['type'] == 'payment_intent.succeeded':
        intent    = event['data']['object']
        intent_id = intent['id']

        pagamento = Pagamento.objects.filter(
            referencia_transacao=intent_id
        ).first()

        if pagamento and pagamento.status != 'aprovado':
            pagamento.status = 'aprovado'
            pagamento.save(update_fields=['status'])
            pagamento.encomenda.status = 'pago'
            pagamento.encomenda.save(update_fields=['status'])

    # ── payment_intent.payment_failed ─────────────────────────
    elif event['type'] == 'payment_intent.payment_failed':
        intent    = event['data']['object']
        intent_id = intent['id']

        pagamento = Pagamento.objects.filter(
            referencia_transacao=intent_id
        ).first()

        if pagamento:
            pagamento.status = 'falhado'
            pagamento.save(update_fields=['status'])

    return Response({'detail': 'ok'}, status=status.HTTP_200_OK)