from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Notificacao
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# ══════════════════════════════════════════════════════════════
# HELPERS — importa e usa em qualquer view
# ══════════════════════════════════════════════════════════════

def notificar(utilizador, tipo, titulo, mensagem='', loja=None, link=''):
    """
    1. Grava a notificação na BD (como antes)
    2. Envia em tempo real via WebSocket ao utilizador
       Se ele não estiver ligado, a notificação fica na BD
       e é carregada quando abrir o sino.
    """
    
    
 
    # ── 1. gravar na BD ──────────────────────────────────────
    notif = Notificacao.objects.create(
        utilizador = utilizador,
        tipo       = tipo,
        titulo     = titulo,
        mensagem   = mensagem,
        loja       = loja,
        link       = link,
    )
 
    # ── 2. contar não lidas ───────────────────────────────────
    nao_lidas = Notificacao.objects.filter(
        utilizador=utilizador, lida=False
    ).count()
 
    # ── 3. enviar via WebSocket ───────────────────────────────
    try:
        channel_layer = get_channel_layer()
        group_name    = f"notif_{utilizador.user.id}"
 
        async_to_sync(channel_layer.group_send)(group_name, {
            "type": "notificacao.nova",      # → chama notificacao_nova() no consumer
            "notificacao": {
                "id":          notif.id,
                "tipo":        notif.tipo,
                "titulo":      notif.titulo,
                "mensagem":    notif.mensagem,
                "loja_id":     loja.id   if loja else None,
                "loja_nome":   loja.nome if loja else None,
                "link":        notif.link,
                "lida":        False,
                "data_criacao": notif.data_criacao.strftime('%d-%m-%Y %H:%M'),
            },
            "nao_lidas": nao_lidas,
        })
    except Exception:
        pass  # falha silenciosa — notificação já está na BD
 
    return notif


def notificar_staff(loja, roles, tipo, titulo, mensagem='', link='', excluir=None):
    """Notifica todos os membros activos da loja com os roles indicados."""
    try:
        from ..models import UtilizadorLoja
        membros = UtilizadorLoja.objects.filter(
            loja=loja, role__in=roles, ativo=True
        ).select_related('utilizador')

        notificacoes = []
        for membro in membros:
            if excluir and membro.utilizador == excluir:
                continue
            notificacoes.append(Notificacao(
                utilizador=membro.utilizador,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                loja=loja,
                link=link,
            ))
        if notificacoes:
            Notificacao.objects.bulk_create(notificacoes)
    except Exception:
        pass


def notificar_admins(tipo, titulo, mensagem='', loja=None, link=''):
    """Notifica todos os admins do site (is_staff=True)."""
    try:
        from ..models import Utilizador
        admins = Utilizador.objects.filter(user__is_staff=True)
        notificacoes = [
            Notificacao(
                utilizador=admin,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                loja=loja,
                link=link,
            )
            for admin in admins
        ]
        if notificacoes:
            Notificacao.objects.bulk_create(notificacoes)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notificacao_list(request):
    """GET /app/notificacoes/?loja_id=&lida=&offset=0&limit=20"""
    utilizador = request.user.utilizador
    qs = Notificacao.objects.filter(utilizador=utilizador)

    loja_id = request.GET.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    lida = request.GET.get('lida')
    if lida == 'true':
        qs = qs.filter(lida=True)
    elif lida == 'false':
        qs = qs.filter(lida=False)

    nao_lidas = Notificacao.objects.filter(utilizador=utilizador, lida=False).count()

    offset = int(request.GET.get('offset', 0))
    limit  = int(request.GET.get('limit', 20))
    total  = qs.count()
    items  = qs[offset:offset + limit]

    results = [
        {
            'id':           n.id,
            'tipo':         n.tipo,
            'titulo':       n.titulo,
            'mensagem':     n.mensagem,
            'loja_id':      n.loja_id,
            'loja_nome':    n.loja.nome if n.loja else None,
            'link':         n.link,
            'lida':         n.lida,
            'data_criacao': n.data_criacao.strftime('%d-%m-%Y %H:%M'),
        }
        for n in items
    ]

    return Response({
        'count':       total,
        'nao_lidas':   nao_lidas,
        'next_offset': offset + limit if offset + limit < total else None,
        'results':     results,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def notificacao_marcar_lida(request, notificacao_id):
    """PATCH /app/notificacoes/<id>/lida/"""
    utilizador = request.user.utilizador
    notif = get_object_or_404(Notificacao, id=notificacao_id, utilizador=utilizador)
    notif.lida = True
    notif.save(update_fields=['lida'])
    return Response({'id': notif.id, 'lida': True})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def notificacao_marcar_todas_lidas(request):
    """PATCH /app/notificacoes/todas-lidas/"""
    utilizador = request.user.utilizador
    qs = Notificacao.objects.filter(utilizador=utilizador, lida=False)
    loja_id = request.data.get('loja_id')
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    count = qs.update(lida=True)
    return Response({'marcadas': count})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def notificacao_apagar(request, notificacao_id):
    """DELETE /app/notificacoes/<id>/apagar/"""
    utilizador = request.user.utilizador
    notif = get_object_or_404(Notificacao, id=notificacao_id, utilizador=utilizador)
    notif.delete()
    return Response({'detail': 'Notificação apagada.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notificacao_contador(request):
    """GET /app/notificacoes/contador/"""
    utilizador = request.user.utilizador
    count = Notificacao.objects.filter(utilizador=utilizador, lida=False).count()
    return Response({'nao_lidas': count})