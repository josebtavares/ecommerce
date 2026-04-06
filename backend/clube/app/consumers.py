# app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now

from .models import ChatThread, ChatParticipant, ChatMessage, Utilizador
from .Serializers.ChatSerializer import ChatMessageSerializer


# ═══════════════════════════════════════════════════════════════
class InboxConsumer(AsyncWebsocketConsumer):
    """
    Socket "global" de cada utilizador: recebe avisos de novas
    mensagens/threads para actualizar badge + toast no front-end.
    """

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.inbox_group = f"inbox_{user.id}"
        await self.channel_layer.group_add(self.inbox_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "inbox_group"):
            await self.channel_layer.group_discard(
                self.inbox_group, self.channel_name
            )

    async def inbox_message(self, event):
        await self.send(text_data=json.dumps(event))


# ═══════════════════════════════════════════════════════════════
class ThreadConsumer(AsyncWebsocketConsumer):
    """
    Um socket por janela de conversa.
    """

    async def connect(self):
        self.thread_id       = self.scope["url_route"]["kwargs"]["thread_id"]
        self.room_group_name = f"thread_{self.thread_id}"

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.room_group_name,
                                           self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        user = self.scope["user"]
        data = json.loads(text_data or "{}")
        text = (data.get("text") or "").strip()

        if not text and "attachment" not in data:
            return

        msg = await self._create_message(user, text)
        ser = await database_sync_to_async(ChatMessageSerializer)(msg)
        payload = {"type": "chat.message", "message": ser.data}
        await self.channel_layer.group_send(self.room_group_name, payload)

        other_ids = await self._other_auth_user_ids(msg)
        inbox_payload = {
            "type":    "inbox.message",
            "thread":  msg.thread_id,
            "message": ser.data,
        }
        for uid in other_ids:
            await self.channel_layer.group_send(f"inbox_{uid}", inbox_payload)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def _create_message(self, user, text):
        util   = user.utilizador
        thread = ChatThread.objects.get(pk=self.thread_id)
        msg = ChatMessage.objects.create(thread=thread, sender=util, text=text)
        thread.last_msg_at = msg.created_at
        thread.save(update_fields=["last_msg_at"])
        ChatParticipant.objects.filter(thread=thread, user=util)\
                               .update(last_read=msg.created_at)
        return msg

    @database_sync_to_async
    def _other_auth_user_ids(self, msg):
        return list(
            msg.thread
               .participants
               .exclude(user=msg.sender)
               .values_list("user__user__id", flat=True)
        )


# ═══════════════════════════════════════════════════════════════
# NOVO — Notificações em tempo real
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