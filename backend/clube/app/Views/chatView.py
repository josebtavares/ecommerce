# chat/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils.timezone import now

from ..models import ChatThread, ChatParticipant, ChatMessage, Utilizador
from ..Serializers.ChatSerializer import ChatThreadSerializer, ChatMessageSerializer

# (caso use o User padrão em algum ponto)
from django.contrib.auth.models import User


class ThreadViewSet(viewsets.ModelViewSet):
    """
    /api/chat/threads/               – list / create
    /api/chat/threads/<id>/          – retrieve / update / delete
    /api/chat/threads/<id>/messages/ – list & send messages  (action abaixo)
    """
    serializer_class   = ChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    # ───────────────────────────────────────────────────────────
    # apenas threads em que o utilizador participa
    def get_queryset(self):
        me = self.request.user.utilizador              # FK para Utilizador
        return ChatThread.objects.filter(participants__user=me)

    # ───────────────────────────────────────────────────────────
    def perform_create(self, serializer):
        thread = serializer.save()

        me   = self.request.user.utilizador
        dest = Utilizador.objects.get(pk=self.request.data['destinatario_id'])

        # adiciona participantes
        ChatParticipant.objects.get_or_create(thread=thread, user=me)
        ChatParticipant.objects.get_or_create(thread=thread, user=dest)

    # ───────────────────────────────────────────────────────────
    # /threads/<id>/messages/
    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        thread = self.get_object()                     # 404 se não pertencer
        me     = request.user.utilizador

        # -------- GET : lista de mensagens ----------
        if request.method == 'GET':
            qs  = thread.messages.order_by('created_at')
            ser = ChatMessageSerializer(qs, many=True, context={'request': request})
            return Response(ser.data)

        # -------- POST : enviar mensagem ------------
        text = request.data.get('text', '').strip()
        if not text and 'attachment' not in request.data:
            return Response({'detail': 'Mensagem vazia'},
                            status=status.HTTP_400_BAD_REQUEST)

        msg = ChatMessage.objects.create(
            thread     = thread,
            sender     = me,
            text       = text,
            attachment = request.data.get('attachment')      # opcional
        )

        # actualiza “última actividade” da thread
        thread.last_msg_at = msg.created_at
        thread.save(update_fields=['last_msg_at'])

        # cursor de leitura do remetente
        ChatParticipant.objects.filter(thread=thread, user=me)\
                               .update(last_read=msg.created_at)

        # realtime push
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()

        # 1) envia para o grupo da própria thread (chat aberto)
        async_to_sync(layer.group_send)(
            f"thread_{thread.id}",
            {
                "type":    "chat.message",
                "message": ChatMessageSerializer(msg).data
            }
        )

        # 2) ───── NOVO ───── notifica as inbox dos OUTROS participantes
        inbox_payload = {
            "type":   "inbox.message",                 # método do InboxConsumer
            "thread": thread.id,
            "message": ChatMessageSerializer(msg).data,
        }

        for part in thread.participants.exclude(user=me):
            # cada participante → grupo global “inbox_<auth_user_id>”
            async_to_sync(layer.group_send)(
                f"inbox_{part.user.user.id}",          # django.contrib.auth user id
                inbox_payload
            )
        # ─────────────────────────────────────────────

        return Response(ChatMessageSerializer(msg).data,
                        status=status.HTTP_201_CREATED)

    # /threads/<id>/mark-read/
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        thread = self.get_object()
        me     = request.user.utilizador

        ChatParticipant.objects.filter(thread=thread, user=me)\
                               .update(last_read=now())
        return Response({"status": "ok"})
