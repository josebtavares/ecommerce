from django.urls import re_path		
from .consumers import InboxConsumer, ThreadConsumer,NotificacaoConsumer		

websocket_urlpatterns = [
    re_path(r"ws/chat/inbox/$", InboxConsumer.as_asgi()),
    re_path(r"ws/chat/thread/(?P<thread_id>\d+)/$", ThreadConsumer.as_asgi()),
    re_path(r"ws/notificacoes/$", NotificacaoConsumer.as_asgi()),
    
]