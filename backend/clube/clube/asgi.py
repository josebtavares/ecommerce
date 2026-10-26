"""
ASGI config for clube project.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clube.settings")
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
import app.routing

django_app = get_asgi_application()


class JwtAuthMiddleware:
    """
    Só actua em WebSockets — identifica o utilizador pelo bilhete de uso único (?bilhete=...)
    pedido antes em POST /api/ws/bilhete/ (Views/sessaoView.py). O JWT já não vai no endereço:
    ficava gravado nos logs do servidor e do proxy.
    Requests HTTP passam directamente sem interferência.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # ── só processa WebSockets ────────────────────────────
        if scope["type"] != "websocket":
            return await self.inner(scope, receive, send)

        from channels.db import database_sync_to_async
        from django.contrib.auth import get_user_model
        from django.core.cache import cache

        query   = parse_qs(scope.get("query_string", b"").decode())
        bilhete = query.get("bilhete", [None])[0]
        scope["user"] = AnonymousUser()

        if bilhete:
            try:
                chave = f"ws_bilhete:{bilhete}"
                uid   = await cache.aget(chave)
                # uso único: só quem consegue apagar o bilhete entra (dois pedidos ao mesmo tempo → um)
                if uid is not None and await cache.adelete(chave):
                    User = get_user_model()
                    user = await database_sync_to_async(User.objects.get)(id=uid)
                    from app.autenticacao import conta_ativa
                    if await database_sync_to_async(conta_ativa)(user):   # contas banidas/suspensas não ligam
                        scope["user"] = user
            except Exception:
                pass  # bilhete inválido → AnonymousUser

        return await self.inner(scope, receive, send)


application = ProtocolTypeRouter({
    "http": django_app,                          # HTTP — sem alterações
    "websocket": JwtAuthMiddleware(              # WebSocket — com JWT
        URLRouter(app.routing.websocket_urlpatterns)
    ),
})