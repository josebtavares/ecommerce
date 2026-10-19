"""
Calendário das entregas (backoffice → Entregas → Calendário).

Cada encomenda aparece no dia/hora em que está agendada (agendada_para) ou, se não tem
agendamento ("o mais cedo possível"), no dia em que foi feita. Canceladas não aparecem.
- dono/gestor (gerir_entregas): todas as encomendas da loja
- condutor: só as entregas atribuídas a ele (sem ficha de condutor → nenhuma)
"""
from collections import Counter
from datetime import date, datetime, time, timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, Encomenda, Condutor
from ..utils import horarios
from .lojaView import _exige_permissao

MAX_DIAS = 400
MAX_ITENS = 2000


def _data(txt):
    try:
        return date.fromisoformat(str(txt))
    except (TypeError, ValueError):
        return None


def encomendas_visiveis(loja, membro):
    """Encomendas que este membro pode ver no calendário."""
    qs = Encomenda.objects.filter(loja=loja).exclude(status='cancelado')
    if membro.role == 'condutor':
        condutor = Condutor.objects.filter(loja=loja, utilizador=membro.utilizador).first()
        if not condutor:
            return qs.none()
        qs = qs.filter(entrega__condutor=condutor)      # o que lhe está atribuído (como na lista)
    return qs


def _a_pagar(e):
    try:
        p = e.pagamento
    except Exception:
        return None
    return str(p.valor) if p.status == 'pendente' else None


def _item(e, tz):
    quando = (e.agendada_para or e.data_criacao).astimezone(tz)
    try:
        entrega = e.entrega            # OneToOne: não existe enquanto não há condutor atribuído
    except Encomenda.entrega.RelatedObjectDoesNotExist:
        entrega = None
    cond = entrega.condutor if entrega else None
    return {
        'encomenda_id':   e.id,
        'data':           quando.date().isoformat(),
        'hora':           quando.strftime('%H:%M'),
        'agendada':       e.agendada_para is not None,
        'origem':         (e.agendamento_origem or 'abertura') if e.agendada_para else '',
        'tipo_entrega':   e.tipo_entrega,
        'status':         e.status,
        'valor_total':    str(e.valor_total),
        'valor_a_pagar':  _a_pagar(e),        # dinheiro na entrega: o que o condutor cobra (sem os esgotados)
        'cliente':        e.comprador.nome or e.comprador.user.username,
        'telefone':       e.comprador.telefone or '',
        'morada':         e.morada_entrega,
        'notas':          e.notas,
        'itens':          ', '.join(f'{i.quantidade}× {i.produto.nome if i.produto else "Produto removido"}'
                                    for i in e.itens.all()),
        'entrega': {
            'status':        entrega.status,
            'condutor_id':   cond.id if cond else None,
            'condutor_nome': (cond.utilizador.nome or cond.utilizador.user.username) if cond else '',
        } if entrega else None,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def entrega_calendario(request, loja_id):
    """
    GET /app/loja/<loja_id>/entrega/calendario/?inicio=2026-10-01&fim=2026-10-31
        &tipo=entrega|levantamento   (opcional)
        &agendadas=1                 (só as agendadas)
        &resumo=1                    (só o número por dia — vista do ano)
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro

    inicio, fim = _data(request.GET.get('inicio')), _data(request.GET.get('fim'))
    if not inicio or not fim or fim < inicio:
        return Response({'detail': 'Indica inicio e fim (AAAA-MM-DD).'}, status=status.HTTP_400_BAD_REQUEST)
    if (fim - inicio).days > MAX_DIAS:
        return Response({'detail': f'No máximo {MAX_DIAS} dias de cada vez.'}, status=status.HTTP_400_BAD_REQUEST)

    tz = horarios.fuso()
    de = datetime.combine(inicio, time(0), tzinfo=tz)
    ate = datetime.combine(fim + timedelta(days=1), time(0), tzinfo=tz)
    qs = encomendas_visiveis(loja, membro).filter(
        Q(agendada_para__gte=de, agendada_para__lt=ate) |
        Q(agendada_para__isnull=True, data_criacao__gte=de, data_criacao__lt=ate))

    tipo = request.GET.get('tipo')
    if tipo in ('entrega', 'levantamento'):
        qs = qs.filter(tipo_entrega=tipo)
    if request.GET.get('agendadas') in ('1', 'true'):
        qs = qs.filter(agendada_para__isnull=False)

    base = {'hoje': horarios.agora().date().isoformat(), 'fuso': str(tz)}
    if request.GET.get('resumo') in ('1', 'true'):
        dias = Counter((e['agendada_para'] or e['data_criacao']).astimezone(tz).date().isoformat()
                       for e in qs.values('agendada_para', 'data_criacao'))
        return Response({**base, 'dias': dict(dias)})

    qs = qs.select_related('comprador__user', 'entrega__condutor__utilizador__user').prefetch_related('itens__produto')
    lista = [_item(e, tz) for e in qs[:MAX_ITENS + 1]]
    lista.sort(key=lambda x: (x['data'], x['hora'], x['encomenda_id']))
    return Response({**base, 'itens': lista[:MAX_ITENS], 'truncado': len(lista) > MAX_ITENS})
