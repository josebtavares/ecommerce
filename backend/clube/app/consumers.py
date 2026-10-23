# app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

# O chat (caixas de mensagens) tem o consumer próprio em app/chat/consumers.py


# ═══════════════════════════════════════════════════════════════
# Notificações em tempo real
# ═══════════════════════════════════════════════════════════════
class NotificacaoConsumer(AsyncWebsocketConsumer):
    """
    Canal pessoal de notificações de cada utilizador.
    URL: ws/notificacoes/

    Ao conectar envia logo o contador de não lidas.
    Quando o backend chama notificar(), a notificação chega
    aqui em tempo real sem polling.
    """

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close(code=4001)
            return

        self.group_name = f"notif_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # envia contador de não lidas ao conectar
        count = await self._nao_lidas(user)
        await self.send(text_data=json.dumps({
            "type":      "contador",
            "nao_lidas": count,
        }))

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    # backend → browser: nova notificação
    async def notificacao_nova(self, event):
        await self.send(text_data=json.dumps({
            "type":        "nova",
            "notificacao": event["notificacao"],
            "nao_lidas":   event.get("nao_lidas", 0),
        }))

    # backend → browser: só actualiza o badge
    async def reembolso_atualizado(self, event):
        # pedido de reembolso mudou (mensagem, estado…): só ids — a página aberta vai buscar o resto
        await self.send(text_data=json.dumps({'type': 'reembolso', 'reembolso': event['reembolso']}))

    async def marcacao_atualizada(self, event):
        # marcação de serviços mudou (mensagem, proposta, estado…): só ids — a página aberta vai buscar o resto
        await self.send(text_data=json.dumps({'type': 'marcacao', 'marcacao': event['marcacao']}))

    async def notificacao_contador(self, event):
        await self.send(text_data=json.dumps({
            "type":      "contador",
            "nao_lidas": event["nao_lidas"],
        }))

    @database_sync_to_async
    def _nao_lidas(self, user):
        from .models import Notificacao
        try:
            return Notificacao.objects.filter(
                utilizador=user.utilizador, lida=False
            ).count()
        except Exception:
            return 0