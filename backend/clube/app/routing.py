from django.urls import re_path
from .consumers import NotificacaoConsumer

websocket_urlpatterns = [
    re_path(r"ws/notificacoes/$", NotificacaoConsumer.as_asgi()),
]
