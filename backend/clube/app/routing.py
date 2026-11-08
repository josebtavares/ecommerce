from django.urls import re_path
from .consumers import NotificacaoConsumer
from .chat.consumers import ChatConsumer
from .pos.consumers import POSConsumer

websocket_urlpatterns = [
    re_path(r"ws/notificacoes/$", NotificacaoConsumer.as_asgi()),
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),
    re_path(r"ws/pos/$", POSConsumer.as_asgi()),           # POS: dono e equipa (bilhete próprio)
]
