from rest_framework import serializers
from ..models import ChatThread, ChatParticipant, ChatMessage
from app.Serializers.UtilizadorSerializer import UtilizadorSerializer   # existing

class ChatParticipantSerializer(serializers.ModelSerializer):
    user = UtilizadorSerializer(read_only=True)

    class Meta:
        model  = ChatParticipant
        fields = ('user', 'last_read')


class ChatThreadSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model  = ChatThread
        fields = ('id','thread_type','title','last_msg_at',
                  'participants','unread_count')

    def get_unread_count(self, obj):
        me = self.context['request'].user.utilizador
        try:
            p = obj.participants.get(user=me)
            return obj.messages.filter(created_at__gt=p.last_read).count()
        except ChatParticipant.DoesNotExist:
            return 0


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UtilizadorSerializer(read_only=True)

    class Meta:
        model  = ChatMessage
        fields = ('id','thread','sender','text','attachment',
                  'created_at','edited_at','deleted')
        read_only_fields = ('sender','created_at','edited_at','deleted')
