"""
Tempo real do chat (WebSocket /ws/chat/).

Cada utilizador ligado está no grupo `chat_u<user id>`. Os eventos levam só identificadores
(conversa, mensagem, caixa) — o browser vai buscar o conteúdo à API, que volta a verificar o acesso.
Assim um evento nunca entrega texto a quem não o pode ler.

Eventos: mensagem_nova · mensagem_apagada · lida · a_escrever · conversa_atualizada
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from app.models import Utilizador, UtilizadorLoja, Entrega
from .models import Caixa, Conversa


def grupo(user_id):
    return f'chat_u{user_id}'


def _agentes_suporte():
    roles = [r for r, perms in Utilizador.PERMISSOES_ADMIN.items() if 'atender_suporte' in perms]
    return Utilizador.objects.filter(user__is_staff=True, role_admin__in=roles, status='ativo') \
        .values_list('user_id', flat=True)


def destinatarios(conversa):
    """ids (auth.User) de quem pode ler esta conversa neste momento — as mesmas regras de regras.py."""
    membros = UtilizadorLoja.objects.filter(loja_id=conversa.loja_id, ativo=True).select_related('utilizador')
    if conversa.tipo == Conversa.EQUIPA_GRUPO:
        return {m.utilizador.user_id for m in membros}

    ids = set()
    ativos_na_loja = {m.utilizador_id for m in membros}
    for p in conversa.participantes.select_related('caixa__utilizador'):
        cx = p.caixa
        if cx.tipo == Caixa.PESSOAL:
            if conversa.tipo == Conversa.EQUIPA_DIRETA and cx.utilizador_id not in ativos_na_loja:
                continue
            ids.add(cx.utilizador.user_id)
        elif cx.tipo == Caixa.LOJA:
            for m in UtilizadorLoja.objects.filter(loja_id=cx.loja_id, ativo=True).select_related('utilizador'):
                if m.atende_chat:
                    ids.add(m.utilizador.user_id)
            if conversa.encomenda_id:
                ent = Entrega.objects.filter(encomenda_id=conversa.encomenda_id, condutor__ativo=True,
                                             condutor__loja_id=cx.loja_id).select_related('condutor__utilizador').first()
                if ent and ent.condutor:
                    ids.add(ent.condutor.utilizador.user_id)
        else:
            ids.update(_agentes_suporte())
    return ids


def emitir(conversa, evento, excluir_user_id=None):
    """Envia o evento a quem pode ler a conversa (depois do commit — nunca anuncia o que foi desfeito)."""
    def _enviar():
        layer = get_channel_layer()
        if layer is None:
            return
        for uid in destinatarios(conversa):
            if uid == excluir_user_id:
                continue
            try:
                async_to_sync(layer.group_send)(grupo(uid), {'type': 'chat.evento', 'evento': evento})
            except Exception:
                pass      # Redis em baixo não pode estragar o envio da mensagem
    transaction.on_commit(_enviar)
