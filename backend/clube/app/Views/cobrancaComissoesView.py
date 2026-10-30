"""
Cobrança mensal das comissões (utils/cobranca_comissoes.py).

  GET  /app/loja/<loja_id>/comissoes/cobrancas/                       → resumo (ver_subscricao)
  POST /app/loja/<loja_id>/comissoes/cobrancas/<id>/pagar/            → pagamento online à Bende (pagar_subscricao)
  GET  /app/admin/comissoes/cobrancas/?estado=pendente|paga|anulada|atraso&loja_id=   (gerir_pagamentos)
  POST /app/admin/comissoes/cobrancas/<id>/  { acao: pagar, metodo, referencia?, notas? } | { acao: anular, motivo }
  POST /app/admin/comissoes/cobrancas/emitir/  { loja_id? } → emite já as que faltam do mês anterior
"""
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import CobrancaComissoes, Loja
from ..pagamentos import ErroPagamento
from ..pagamentos import servico as pagamentos
from ..utils import cobranca_comissoes as cc
from .adminView import _exige_admin
from .lojaView import _exige_permissao


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detail': msg}, status=codigo)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_cobrancas(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'ver_subscricao')
    if erro:
        return erro
    return Response({**cc.resumo_loja(loja), 'pode_pagar': bool(membro and membro.pode('pagar_subscricao'))})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_cobranca_pagar(request, loja_id, cobranca_id):
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'pagar_subscricao')
    if erro:
        return erro
    c = get_object_or_404(CobrancaComissoes.objects.select_related('loja'), id=cobranca_id, loja=loja)
    try:
        inicio = pagamentos.iniciar_cobranca_comissoes(c, request.user.utilizador)
    except (cc.ErroCobranca, ErroPagamento) as e:
        return _erro(str(e))
    if inicio.estado == 'redirecionar':
        return Response(pagamentos.para_frontend(inicio))
    return Response({**cc.resumo_loja(loja), 'pode_pagar': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_cobrancas(request):
    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro:
        return erro
    qs = CobrancaComissoes.objects.select_related('loja')
    estado = request.GET.get('estado')
    hoje = cc._hoje()
    if estado == 'atraso':
        qs = qs.filter(estado='pendente', vencimento__lt=hoje)
    elif estado in ('pendente', 'paga', 'anulada'):
        qs = qs.filter(estado=estado)
    loja_id = request.GET.get('loja_id')
    if loja_id and str(loja_id).isdigit():
        qs = qs.filter(loja_id=int(loja_id))
    pend = CobrancaComissoes.objects.filter(estado='pendente')
    return Response({
        'resultados': [cc.payload(c, hoje) for c in qs[:300]],
        'total_por_pagar': f"{pend.aggregate(t=Sum('valor'))['t'] or 0:.2f}",
        'total_em_atraso': f"{pend.filter(vencimento__lt=hoje).aggregate(t=Sum('valor'))['t'] or 0:.2f}",
        'n_em_atraso': pend.filter(vencimento__lt=hoje).count(),
        'metodos': [{'valor': m, 'nome': dict(CobrancaComissoes.METODOS)[m]} for m in cc.METODOS_ADMIN],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_cobranca(request, cobranca_id):
    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro:
        return erro
    c = get_object_or_404(CobrancaComissoes.objects.select_related('loja'), id=cobranca_id)
    acao = request.data.get('acao')
    try:
        if acao == 'pagar':
            metodo = request.data.get('metodo')
            if metodo not in cc.METODOS_ADMIN:
                return _erro('Escolhe como foi pago.')
            notas = str(request.data.get('notas') or '').strip()
            if metodo == 'oferta' and len(notas) < 5:
                return _erro('Escreve porque é perdoada.')
            c = cc.pagar(c, metodo, referencia=str(request.data.get('referencia') or '').strip(), notas=notas, por=request.user)
        elif acao == 'anular':
            c = cc.anular(c, request.data.get('motivo'), por=request.user)
        else:
            return _erro('Acção inválida.')
    except cc.ErroCobranca as e:
        return _erro(str(e))
    return Response(cc.payload(c))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_cobrancas_emitir(request):
    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro:
        return erro
    loja_id = request.data.get('loja_id')
    if loja_id:
        loja = get_object_or_404(Loja, id=loja_id)
        c = cc.emitir(loja)
        return Response({'emitidas': int(bool(c))})
    return Response({'emitidas': cc.emitir_todas()})
