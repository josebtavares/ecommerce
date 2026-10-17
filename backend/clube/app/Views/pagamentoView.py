import os

import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..Views.notificacaoView import notificar_staff, notificar_admins
from ..utils.encomendas import expirar_encomenda, MSG_EXPIROU, PRAZO_PAGAMENTO_MIN
from decimal import Decimal
from ..models import (
    Encomenda, Pagamento, MetodoPagamento,
    CartaoGuardado, UtilizadorLoja, Loja, Carrinho, Comissao,
)

import requests as flw_requests
import hashlib
import hmac

from ..Serializers.PagamentoSerializer import (
    CartaoGuardadoSerializer,
    MetodoPagamentoSerializer,
    PagamentoSerializer,
    PagarComCartaoSerializer,
    PagarComMBWaySerializer,
    PagarComDinheiroSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

FLW_SECRET_KEY    = os.environ.get('FLW_SECRET_KEY', '')
FLW_PUBLIC_KEY    = os.environ.get('FLW_PUBLIC_KEY', '')
FLW_SECRET_HASH   = os.environ.get('FLW_SECRET_HASH', '')
FLW_BASE_URL      = 'https://api.flutterwave.com/v3'
PLATAFORMA_SUBACCOUNT = os.environ.get('FLW_PLATAFORMA_SUBACCOUNT', '')
 
def _flw_headers():
    return {
        'Authorization': f'Bearer {FLW_SECRET_KEY}',
        'Content-Type':  'application/json',
    }
 


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _get_ou_criar_stripe_customer(utilizador) -> str:
    cartao = CartaoGuardado.objects.filter(utilizador=utilizador).first()
    if cartao:
        return cartao.stripe_customer_id
    customer = stripe.Customer.create(
        email=utilizador.email,
        name=utilizador.nome,
        metadata={'utilizador_id': utilizador.id}
    )
    return customer.id


def _verificar_encomenda(request, encomenda_id, prazo=True):
    """
    A encomenda do comprador, por pagar e bloqueada (as views de pagamento são atómicas: o worker
    que cancela as expiradas não lhe mexe enquanto o pagamento decorre).
    prazo=False (regresso do Flutterwave): o dinheiro já foi cobrado — aceita-se mesmo fora do prazo
    se a encomenda ainda não foi cancelada.
    """
    utilizador = request.user.utilizador
    encomenda  = get_object_or_404(Encomenda.objects.select_for_update(of=('self',)).select_related('loja'),
                                   id=encomenda_id)
    if encomenda.comprador != utilizador:
        return None, Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
    if prazo and expirar_encomenda(encomenda):
        return None, Response({'detail': MSG_EXPIROU.format(min=PRAZO_PAGAMENTO_MIN), 'codigo': 'encomenda_expirada'},
                              status=status.HTTP_400_BAD_REQUEST)
    if encomenda.status != 'pendente':
        return None, Response({'detail': f'Encomenda ja esta: {encomenda.status}'}, status=status.HTTP_400_BAD_REQUEST)
    if not encomenda.loja.ativa:
        return None, Response({'detail': 'Esta loja não está a aceitar pagamentos de momento.'},
                              status=status.HTTP_400_BAD_REQUEST)
    return encomenda, None


def _limpar_carrinho(encomenda):
    """Limpa o carrinho do comprador para a loja, apos pagamento confirmado."""
    try:
        carrinho = Carrinho.objects.get(utilizador=encomenda.comprador, loja=encomenda.loja)
        carrinho.itens.all().delete()
    except Carrinho.DoesNotExist:
        pass


def _registar_pagamento_aprovado(encomenda, metodo, referencia, valor):
    """
    Cria pagamento com status=aprovado, muda encomenda para pago,
    regista comissao e limpa carrinho.
    Usado para cartao e mbway (pagamento digital confirmado).
    """
    pagamento = Pagamento.objects.create(
        encomenda=encomenda,
        metodo=metodo,
        valor=valor,
        status='aprovado',
        referencia_transacao=referencia,
    )
    encomenda.status = 'pago'
    encomenda.save(update_fields=['status'])

    # regista comissao imediatamente
    Comissao.registar(encomenda)
    
    # calcula valor da comissao para a mensagem
    _perc = encomenda.percentagem_comissao_aplicavel     # 0 se a loja estava em subscrição
    _com  = (encomenda.valor_total * _perc / 100).quantize(Decimal('0.01'))
    _liq  = encomenda.valor_total - _com
 
    # notifica dono/gestor — pagamento confirmado
    notificar_staff(
        loja=encomenda.loja,
        roles=['dono', 'gestor'],
        tipo='pagamento_aprovado',
        titulo=f'Pagamento confirmado — Encomenda #{encomenda.id}',
        mensagem=f'€{encomenda.valor_total} recebido via {referencia}. Receita líquida: €{_liq}.',
        link=f'/loja/{encomenda.loja_id}/backoffice',
    )
 
    # notifica admins — comissão registada (as lojas em subscrição não pagam comissão)
    if _com:
        notificar_admins(
            tipo='comissao_recebida',
            titulo=f'Comissão registada — {encomenda.loja.nome}',
            mensagem=f'Encomenda #{encomenda.id} · Total: €{encomenda.valor_total} · Comissão ({_perc}%): €{_com}.',
            loja=encomenda.loja,
            link='/admin',
        )

    # limpa carrinho
    _limpar_carrinho(encomenda)
    return pagamento


# ══════════════════════════════════════════════════════════════
# CARTOES GUARDADOS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cartao_list(request):
    cartoes = CartaoGuardado.objects.filter(utilizador=request.user.utilizador)
    return Response(CartaoGuardadoSerializer(cartoes, many=True).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def cartao_remover(request, id):
    utilizador = request.user.utilizador
    cartao     = get_object_or_404(CartaoGuardado, id=id, utilizador=utilizador)
    try:
        stripe.PaymentMethod.detach(cartao.stripe_payment_id)
    except stripe.error.StripeError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    cartao.delete()
    return Response({'detail': 'Cartao removido.'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cartao_predefinir(request, id):
    utilizador = request.user.utilizador
    cartao     = get_object_or_404(CartaoGuardado, id=id, utilizador=utilizador)
    cartao.predefinido = True
    cartao.save()
    return Response(CartaoGuardadoSerializer(cartao).data)


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
    try:
        membro = UtilizadorLoja.objects.get(loja=loja, utilizador=request.user.utilizador, ativo=True)
    except UtilizadorLoja.DoesNotExist:
        return Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
    if not membro.pode('gerir_metodos_pagamento'):
        return Response({'detail': 'Sem permissao.'}, status=status.HTTP_403_FORBIDDEN)
    metodo, _ = MetodoPagamento.objects.get_or_create(loja=loja, tipo=tipo)
    if request.method == 'POST':
        metodo.ativo = True
        metodo.save()
        return Response(MetodoPagamentoSerializer(metodo).data)
    metodo.ativo = False
    metodo.save()
    return Response({'detail': f'Metodo {tipo} desactivado.'})


# ══════════════════════════════════════════════════════════════
# PAGAR COM CARTAO (Stripe)
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_com_cartao(request):
    serializer = PagarComCartaoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data       = serializer.validated_data
    utilizador = request.user.utilizador
    encomenda, erro = _verificar_encomenda(request, data['encomenda_id'])
    if erro: return erro
    metodo = MetodoPagamento.objects.filter(loja=encomenda.loja, tipo='cartao', ativo=True).first()
    if not metodo:
        return Response({'detail': 'Esta loja nao aceita pagamento por cartao.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        customer_id = _get_ou_criar_stripe_customer(utilizador)
        if data.get('cartao_id'):
            cartao = get_object_or_404(CartaoGuardado, id=data['cartao_id'], utilizador=utilizador)
            payment_method_id = cartao.stripe_payment_id
        else:
            payment_method_id = data['payment_method_id']
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        valor_centimos = int(encomenda.valor_total * 100)
        intent = stripe.PaymentIntent.create(
            amount=valor_centimos, currency='eur', customer=customer_id,
            payment_method=payment_method_id, confirm=True,
            metadata={'encomenda_id': encomenda.id, 'utilizador_id': utilizador.id},
            return_url='http://localhost:8080/pagamento/sucesso',
        )
        if intent.status not in ('succeeded', 'processing'):
            return Response({'detail': f'Pagamento nao confirmado: {intent.status}'}, status=status.HTTP_400_BAD_REQUEST)
        if data.get('guardar_cartao') and not data.get('cartao_id'):
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            CartaoGuardado.objects.create(
                utilizador=utilizador, stripe_customer_id=customer_id,
                stripe_payment_id=payment_method_id, marca=pm.card.brand,
                ultimos_4=pm.card.last4, mes_expiracao=pm.card.exp_month,
                ano_expiracao=pm.card.exp_year,
                predefinido=not CartaoGuardado.objects.filter(utilizador=utilizador).exists(),
            )
        # cartao confirmado digitalmente → aprovado imediatamente + comissao
        pagamento = _registar_pagamento_aprovado(encomenda, metodo, intent.id, encomenda.valor_total)
        return Response(PagamentoSerializer(pagamento).data, status=status.HTTP_200_OK)
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
    serializer = PagarComMBWaySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data      = serializer.validated_data
    encomenda, erro = _verificar_encomenda(request, data['encomenda_id'])
    if erro: return erro
    metodo = MetodoPagamento.objects.filter(loja=encomenda.loja, tipo='mbway', ativo=True).first()
    if not metodo:
        return Response({'detail': 'Esta loja nao aceita MBWay.'}, status=status.HTTP_400_BAD_REQUEST)

    # MBWay simulado — trata como aprovado imediatamente (em producao seria async via webhook)
    pagamento = _registar_pagamento_aprovado(
        encomenda, metodo,
        f'mbway_{data["telemovel"]}',
        encomenda.valor_total
    )
    return Response(
        {'detail': f'Pagamento MBWay confirmado para {data["telemovel"]}.',
         'pagamento': PagamentoSerializer(pagamento).data},
        status=status.HTTP_200_OK
    )


# ══════════════════════════════════════════════════════════════
# PAGAR NA ENTREGA (dinheiro)
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pagar_dinheiro(request):
    """
    Dinheiro → pagamento PENDENTE (confirmado fisicamente na entrega).
    A comissao so e registada quando a encomenda for marcada como concluida.
    """
    serializer = PagarComDinheiroSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    encomenda, erro = _verificar_encomenda(request, serializer.validated_data['encomenda_id'])
    if erro: return erro
    # o checkout também manda por aqui (simulado) cartão, transferência e mobile money: antes procurava
    # sempre o método "dinheiro" e uma loja que só aceitasse, p.ex., transferência recusava o pagamento
    tipo = request.data.get('metodo') or 'dinheiro'
    if tipo not in ('dinheiro', 'cartao', 'transferencia', 'mobile_money'):
        return Response({'detail': 'Método de pagamento inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    metodo = MetodoPagamento.objects.filter(loja=encomenda.loja, tipo=tipo, ativo=True).first()
    if not metodo:
        return Response({'detail': 'Esta loja não aceita este método de pagamento.'}, status=status.HTTP_400_BAD_REQUEST)

    # dinheiro → pagamento pendente, encomenda pendente ate entrega fisica
    pagamento = Pagamento.objects.create(
        encomenda=encomenda,
        metodo=metodo,
        valor=encomenda.valor_total,
        status='pendente',          # ← pendente ate staff confirmar
        referencia_transacao='dinheiro',
    )
    encomenda.status = 'pago'       # encomenda aceite, aguarda entrega
    encomenda.save(update_fields=['status'])

    # NAO regista comissao ainda — so quando concluido
    # NAO limpa carrinho ainda — so quando concluido
    _limpar_carrinho(encomenda)     # limpa o carrinho (encomenda ja foi criada)

    return Response(PagamentoSerializer(pagamento).data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# STRIPE WEBHOOK
# ══════════════════════════════════════════════════════════════

# chamado pelo Stripe (sem utilizador): a autenticidade vem da assinatura
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return Response({'detail': 'Webhook invalido.'}, status=status.HTTP_400_BAD_REQUEST)

    if event['type'] == 'payment_intent.succeeded':
        intent    = event['data']['object']
        pagamento = Pagamento.objects.filter(referencia_transacao=intent['id']).first()
        if pagamento and pagamento.status != 'aprovado':
            pagamento.status = 'aprovado'
            pagamento.save(update_fields=['status'])
            pagamento.encomenda.status = 'pago'
            pagamento.encomenda.save(update_fields=['status'])
            Comissao.registar(pagamento.encomenda)
            _limpar_carrinho(pagamento.encomenda)

    elif event['type'] == 'payment_intent.payment_failed':
        intent    = event['data']['object']
        pagamento = Pagamento.objects.filter(referencia_transacao=intent['id']).first()
        if pagamento:
            pagamento.status = 'falhado'
            pagamento.save(update_fields=['status'])

    return Response({'detail': 'ok'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def iniciar_pagamento_flutterwave(request):
    """
    POST /app/pagamento/flutterwave/iniciar/
    Body: { encomenda_id }
    """
    encomenda_id = request.data.get('encomenda_id')
    encomenda, erro = _verificar_encomenda(request, encomenda_id)
    if erro:
        return erro
 
    loja = encomenda.loja
 
    # só verifica se flutterwave está activo — subaccount é opcional para testes
    metodo = MetodoPagamento.objects.filter(
        loja=loja, tipo='flutterwave', ativo=True
    ).first()
    if not metodo:
        return Response(
            {'detail': 'Flutterwave não está activo nesta loja.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    utilizador  = request.user.utilizador
    valor_total = float(encomenda.valor_total)
 
    # calcular comissão (0 se a encomenda foi feita com a loja em subscrição → sem divisão)
    percentagem_comissao = float(encomenda.percentagem_comissao_aplicavel)
    valor_comissao = round(valor_total * percentagem_comissao / 100, 2)
 
    # payload base
    payload = {
        'tx_ref':       f'enc_{encomenda.id}_{encomenda.data_criacao.strftime("%Y%m%d%H%M%S")}',
        'amount':       valor_total,
        'currency':     MOEDA_FLW,  # mudar para CVE quando tiveres conta em escudos
        'redirect_url': f'{os.environ.get("FRONTEND_BASE_URL", "")}/pagamento/callback',
        'customer': {
            'email':       utilizador.email,
            'name':        utilizador.nome,
            'phonenumber': utilizador.telefone or '',
        },
        'meta': {
            'encomenda_id': encomenda.id,
            'loja_id':      loja.id,
        },
        'customizations': {
            'title':       loja.nome,
            'description': f'Encomenda #{encomenda.id}',
            'logo':        loja.logo.url if loja.logo else '',
        },
    }
 
    # split só se ambos os subaccounts estiverem configurados
    if loja.flutterwave_subaccount_id and PLATAFORMA_SUBACCOUNT:
        payload['subaccounts'] = [
            {
                'id':                      PLATAFORMA_SUBACCOUNT,
                'transaction_charge_type': 'flat',
                'transaction_charge':      valor_comissao,
            }
        ]
 
    # chamar API Flutterwave
    resp = flw_requests.post(
        f'{FLW_BASE_URL}/payments',
        json=payload,
        headers=_flw_headers(),
        timeout=15,
    )
 
    if resp.status_code != 200 or resp.json().get('status') != 'success':
        return Response(
            {'detail': 'Erro ao criar pagamento no Flutterwave.', 'flw_error': resp.json()},
            status=status.HTTP_502_BAD_GATEWAY
        )
 
    link = resp.json()['data']['link']
    return Response({'payment_url': link, 'tx_ref': payload['tx_ref']})
 
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def verificar_pagamento_flutterwave(request):
    """
    POST /app/pagamento/flutterwave/verificar/
    Body: { transaction_id, tx_ref }
 
    Chamado pelo frontend após o utilizador regressar do Flutterwave.
    Verifica o pagamento na API e confirma a encomenda.
    """
    transaction_id = request.data.get('transaction_id')
    tx_ref         = request.data.get('tx_ref')
 
    if not transaction_id:
        return Response({'detail': 'transaction_id em falta.'}, status=status.HTTP_400_BAD_REQUEST)
 
    # extrair encomenda_id do tx_ref (formato: enc_<id>_<timestamp>)
    try:
        encomenda_id = int(tx_ref.split('_')[1])
    except (IndexError, ValueError):
        return Response({'detail': 'tx_ref inválido.'}, status=status.HTTP_400_BAD_REQUEST)
 
    cancelada = Encomenda.objects.filter(id=encomenda_id, comprador=request.user.utilizador,
                                         status='cancelado').select_related('loja').first()
    if cancelada is None:
        encomenda, erro = _verificar_encomenda(request, encomenda_id, prazo=False)
        if erro:
            return erro
    else:
        encomenda = cancelada
 
    # verificar na API do Flutterwave
    resp = flw_requests.get(
        f'{FLW_BASE_URL}/transactions/{transaction_id}/verify',
        headers=_flw_headers(),
        timeout=15,
    )
 
    if resp.status_code != 200:
        return Response({'detail': 'Erro ao verificar pagamento.'}, status=status.HTTP_502_BAD_GATEWAY)
 
    flw_data = resp.json().get('data', {})
 
    # validar valor e moeda
    valor_esperado = float(encomenda.valor_total)
    valor_pago     = float(flw_data.get('amount', 0))
    moeda_paga     = flw_data.get('currency', '')
    flw_status     = flw_data.get('status', '')
 
    if flw_status != 'successful':
        return Response(
            {'detail': f'Pagamento não confirmado: {flw_status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    if abs(valor_pago - valor_esperado) > 0.01:
        return Response(
            {'detail': f'Valor incorreto. Esperado: {valor_esperado}, Pago: {valor_pago}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # a transacção tem de ser DESTA encomenda e ainda não usada. Antes bastava um transaction_id
    # verdadeiro com o mesmo valor: um pagamento antigo de 5 € "pagava" qualquer outra encomenda de 5 €.
    erro_tx = _transacao_flw_invalida(flw_data, encomenda, transaction_id)
    if erro_tx:
        return Response({'detail': erro_tx}, status=status.HTTP_400_BAD_REQUEST)

    # cobrado, mas a encomenda já tinha sido cancelada (expirou / a loja fechou) → reembolso
    if cancelada is not None:
        _pedir_reembolso(encomenda, f'flw_{transaction_id}')
        return Response({'detail': 'O pagamento chegou depois de a encomenda ter sido cancelada. '
                                   'Vais ser reembolsado — a equipa já foi avisada.', 'codigo': 'reembolso'},
                        status=status.HTTP_409_CONFLICT)

    # pagamento confirmado — registar
    metodo = MetodoPagamento.objects.filter(
        loja=encomenda.loja, tipo='flutterwave', ativo=True
    ).first()
 
    pagamento = _registar_pagamento_aprovado(
        encomenda, metodo,
        f'flw_{transaction_id}',
        encomenda.valor_total,
    )
 
    return Response(PagamentoSerializer(pagamento).data, status=status.HTTP_200_OK)
 
 
MOEDA_FLW = 'EUR'   # a mesma do iniciar_pagamento_flutterwave


def _transacao_flw_invalida(flw_data, encomenda, transaction_id):
    """Motivo para recusar a transacção do Flutterwave, ou None se pertence a esta encomenda."""
    tx_ref = str(flw_data.get('tx_ref') or '')
    if not tx_ref.startswith(f'enc_{encomenda.id}_'):
        return 'Esta transacção não pertence a esta encomenda.'
    if flw_data.get('currency') != MOEDA_FLW:
        return 'Moeda do pagamento inválida.'
    if Pagamento.objects.filter(referencia_transacao=f'flw_{transaction_id}').exclude(encomenda=encomenda).exists():
        return 'Esta transacção já foi usada noutra encomenda.'
    return None


def _pedir_reembolso(encomenda, referencia):
    """Avisa os admins (uma vez por encomenda — o webhook e o regresso do cliente podem chegar os dois)."""
    from ..models import Notificacao
    titulo = f'Reembolso necessário — Encomenda #{encomenda.id}'
    if Notificacao.objects.filter(tipo='pagamento_reembolsar', titulo=titulo).exists():
        return
    notificar_admins(
        tipo='pagamento_reembolsar',
        titulo=titulo,
        mensagem=f'O Flutterwave confirmou €{encomenda.valor_total} (tx {referencia}) '
                 f'para uma encomenda cancelada da loja {encomenda.loja.nome}. Reembolsa o cliente.',
        loja=encomenda.loja,
        link='/admin',
    )


# chamado pelo Flutterwave (sem utilizador): a autenticidade vem do verif-hash
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def flutterwave_webhook(request):
    """
    POST /app/pagamento/flutterwave/webhook/
    Webhook do Flutterwave — confirmação assíncrona de pagamento.
    """
    # verificar assinatura
    signature = request.META.get('HTTP_VERIF_HASH', '')
    # sem hash configurado não há forma de validar → recusa (antes aceitava pedidos sem assinatura)
    if not FLW_SECRET_HASH or not hmac.compare_digest(signature, FLW_SECRET_HASH):
        return Response({'detail': 'Assinatura inválida.'}, status=status.HTTP_400_BAD_REQUEST)
 
    data       = request.data
    flw_status = data.get('data', {}).get('status', '')
    tx_ref     = data.get('data', {}).get('tx_ref', '')
 
    if data.get('event') != 'charge.completed' or flw_status != 'successful':
        return Response({'detail': 'ok'})
 
    # extrair encomenda_id
    try:
        encomenda_id = int(tx_ref.split('_')[1])
        encomenda = Encomenda.objects.get(id=encomenda_id)
    except (IndexError, ValueError, Encomenda.DoesNotExist):
        return Response({'detail': 'Encomenda não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
 
    # cobrança confirmada para uma encomenda já cancelada (ex.: a loja fechou enquanto o
    # cliente estava na página do Flutterwave) → o dinheiro entrou, é preciso reembolsar à mão
    if encomenda.status == 'cancelado':
        _pedir_reembolso(encomenda, f'flw_{data.get("data", {}).get("id", "")}')
        return Response({'detail': 'ok'})

    # evitar duplicados
    if encomenda.status != 'pendente':
        return Response({'detail': 'ok'})
 
    metodo = MetodoPagamento.objects.filter(
        loja=encomenda.loja, tipo='flutterwave', ativo=True
    ).first()
 
    transaction_id = data.get('data', {}).get('id', '')
    # mesmo assinado, só confirma se o valor, a moeda e a transacção batem com esta encomenda
    try:
        valor_pago = float(data.get('data', {}).get('amount', 0))
    except (TypeError, ValueError):
        valor_pago = 0
    if (abs(valor_pago - float(encomenda.valor_total)) > 0.01
            or _transacao_flw_invalida(data.get('data', {}), encomenda, transaction_id)):
        return Response({'detail': 'Pagamento não corresponde à encomenda.'}, status=status.HTTP_400_BAD_REQUEST)

    _registar_pagamento_aprovado(
        encomenda, metodo,
        f'flw_{transaction_id}',
        encomenda.valor_total,
    )
 
    return Response({'detail': 'ok'})