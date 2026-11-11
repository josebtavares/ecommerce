from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import logging

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from ..models import Notificacao
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

log = logging.getLogger(__name__)


def _data(n):
    """Data da notificação na hora de Cabo Verde (TIME_ZONE), como o sino a mostra."""
    return timezone.localtime(n.data_criacao).strftime('%d-%m-%Y %H:%M')


def _payload(n, loja=None):
    loja = loja if loja is not None else n.loja
    return {'id': n.id, 'tipo': n.tipo, 'titulo': n.titulo, 'mensagem': n.mensagem,
            'loja_id': loja.id if loja else None, 'loja_nome': loja.nome if loja else None,
            'link': n.link, 'lida': False, 'data_criacao': _data(n)}


def _empurrar(notificacoes, loja=None):
    """Manda pelo WebSocket (grupo notif_<user.id>) cada notificação acabada de gravar, com o contador de não
    lidas de cada pessoa. Quem não estiver ligado vê-as ao abrir o sino. Uma falha aqui nunca parte a acção."""
    if not notificacoes:
        return
    try:
        canal = get_channel_layer()
        ids = {n.utilizador_id for n in notificacoes}
        contas = dict(Notificacao.objects.filter(utilizador_id__in=ids, lida=False)
                      .values('utilizador_id').annotate(n=Count('id')).values_list('utilizador_id', 'n'))
        users = dict(type(notificacoes[0].utilizador).objects.filter(id__in=ids).values_list('id', 'user_id'))
        for n in notificacoes:
            if users.get(n.utilizador_id) is None:
                continue
            async_to_sync(canal.group_send)(f'notif_{users[n.utilizador_id]}', {
                'type': 'notificacao.nova', 'notificacao': _payload(n, loja), 'nao_lidas': contas.get(n.utilizador_id, 0)})
    except Exception:
        log.warning('notificações: envio em tempo real falhou', exc_info=True)


def _empurrar_depois(notificacoes, loja=None):
    # depois do commit: se a acção for desfeita, ninguém recebe um aviso de algo que não aconteceu
    transaction.on_commit(lambda: _empurrar(notificacoes, loja))

# ══════════════════════════════════════════════════════════════
# HELPERS — importa e usa em qualquer view
# ══════════════════════════════════════════════════════════════

# rótulo do botão do email, pelo início do link do aviso
BOTOES = (('/mensagens', 'Responder'), ('/minhas-marcacoes', 'Ver a marcação'), ('/perfil/reembolsos', 'Ver o pedido'),
          ('/perfil', 'Ver as minhas encomendas'), ('/encomendas/', 'Ver a encomenda'), ('/encomenda/', 'Ver a encomenda'),
          ('/loja/', 'Abrir o backoffice'), ('/pos/', 'Abrir o POS'), ('/admin', 'Abrir o admin'))


def notificar(utilizador, tipo, titulo, mensagem='', loja=None, link='', email=None, email_validade=None,
              email_chave=None):
    """Grava a notificação e, depois do commit, manda-a em tempo real (WebSocket) à pessoa.
    Se ela não estiver ligada, a notificação fica na BD e aparece quando abrir o sino.
    email=<prioridade> (utils/fila_emails: ESSENCIAL / IMPORTANTE / INFORMATIVO): também vai por email, pela fila,
    na mesma transacção. email_validade: timedelta depois do qual já não vale a pena enviar; email_chave: não repete."""
    notif = Notificacao.objects.create(utilizador=utilizador, tipo=tipo, titulo=titulo, mensagem=mensagem,
                                       loja=loja, link=link)
    _empurrar_depois([notif], loja)
    if email:
        _email(utilizador, tipo, titulo, mensagem, loja, link, email, email_validade, email_chave)
    return notif


def _email(utilizador, tipo, titulo, mensagem, loja, link, prioridade, validade, chave):
    """O aviso por email: saudação, o texto do aviso e um botão para a página. Só para contas activas com o email
    confirmado (as outras não recebem — evita emails devolvidos). Uma falha nunca parte a acção."""
    try:
        from django.conf import settings
        from ..utils import fila_emails
        from ..utils.email_html import saudacao
        user = utilizador.user
        if not user.email or not user.is_active or not utilizador.email_confirmado:
            return
        assunto = titulo if not loja or loja.nome in titulo else f'{titulo} — {loja.nome}'
        texto = f'{saudacao(user)}\n\n{mensagem or titulo}'
        botao = None
        if link.startswith('/'):
            rotulo = 'Responder' if '/mensagens?' in link else next(
                (r for prefixo, r in BOTOES if link.startswith(prefixo)), 'Abrir na Bendi')
            botao = (rotulo, settings.FRONTEND_BASE_URL.rstrip('/') + link)
        fila_emails.enfileirar(user.email, assunto, texto, tipo=f'aviso_{tipo}', prioridade=prioridade,
                               botao=botao, utilizador=utilizador, chave=chave, validade=validade)
    except Exception:
        log.warning('notificações: o email do aviso "%s" não ficou na fila', tipo, exc_info=True)


def notificar_staff(loja, roles, tipo, titulo, mensagem='', link='', excluir=None, email=None, email_roles=None,
                    email_validade=None, email_chave=None, sino=True):
    """Notifica todos os membros activos da loja com os roles indicados.
    email=<prioridade>: também por email aos membros com os roles de email_roles (por omissão os mesmos de roles).
    sino=False: só o email (o aviso no sino já foi dado antes)."""
    try:
        from ..models import UtilizadorLoja
        membros = [m for m in UtilizadorLoja.objects.filter(loja=loja, role__in=roles, ativo=True)
                   .select_related('utilizador__user') if not (excluir and m.utilizador == excluir)]
        notificacoes = [Notificacao(utilizador=m.utilizador, tipo=tipo, titulo=titulo, mensagem=mensagem, loja=loja,
                                    link=link) for m in membros]
        if notificacoes and sino:
            _empurrar_depois(Notificacao.objects.bulk_create(notificacoes), loja)
        if email:
            vistos = set()
            for m in membros:
                if m.role in (email_roles or roles) and m.utilizador_id not in vistos:
                    vistos.add(m.utilizador_id)
                    _email(m.utilizador, tipo, titulo, mensagem, loja, link, email, email_validade,
                           f'{email_chave}:{m.utilizador_id}' if email_chave else None)
    except Exception:
        log.warning('notificações: notificar_staff falhou', exc_info=True)


# Quem recebe cada aviso da plataforma (Utilizador.PERMISSOES_ADMIN): só quem trata do assunto.
PERMISSAO_AVISO = {
    'comissao_recebida':    'gerir_pagamentos',
    'pagamento_reembolsar': 'gerir_pagamentos',
    'pagamento_erro': 'gerir_pagamentos',
    'cobranca_comissoes':   'gerir_pagamentos',
    'dados_bancarios':      'gerir_pagamentos',
    'vinti4':               'gerir_pagamentos',
    'reembolso_disputa':    'gerir_devolucoes',
    'reembolso_atualizado': 'gerir_devolucoes',
    'loja_pendente':        'gerir_lojas',
    'loja_fechada':         'gerir_lojas',
    'documento_loja':       'verificar_documentos',
    'subscricao_fatura':    'gerir_subscricoes',
    'subscricao_paga':      'gerir_subscricoes',
    'emails':               'gerir_plataforma',
}


def admins_com(permissao):
    """Contas de admin activas com esta permissão (None = todas as contas de admin activas)."""
    from ..models import Utilizador
    admins = Utilizador.objects.filter(user__is_staff=True, user__is_active=True).select_related('user')
    if permissao:
        admins = admins.filter(role_admin__in=[r for r, perms in Utilizador.PERMISSOES_ADMIN.items() if permissao in perms])
    return [a for a in admins if a.is_active]       # um admin suspenso ou banido não recebe avisos


def notificar_admins(tipo, titulo, mensagem='', loja=None, link='', permissao=None, email=None, email_chave=None):
    """Notifica os admins do site que tratam deste assunto: permissao (ou PERMISSAO_AVISO[tipo]).
    email=<prioridade>: também por email (só para o que pede uma acção — não gastar o limite)."""
    try:
        admins = admins_com(permissao or PERMISSAO_AVISO.get(tipo))
        notificacoes = [Notificacao(utilizador=a, tipo=tipo, titulo=titulo, mensagem=mensagem, loja=loja, link=link)
                        for a in admins]
        if notificacoes:
            _empurrar_depois(Notificacao.objects.bulk_create(notificacoes), loja)
        if email:
            for a in admins:
                _email(a, tipo, titulo, mensagem, loja, link, email, None,
                       f'{email_chave}:{a.id}' if email_chave else None)
    except Exception:
        log.warning('notificações: notificar_admins falhou', exc_info=True)


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
            'data_criacao': _data(n),
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