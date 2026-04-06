"""
ASGI config for clube project.
Inclui middleware JWT para autenticação via WebSocket.
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
    Lê o token JWT do query string (?token=...) e autentica o utilizador.
    O AuthMiddlewareStack padrão lê cookies — não funciona para WebSockets
    com JWT enviado pelo frontend Vue.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        from channels.db import database_sync_to_async
        from django.contrib.auth import get_user_model

        query     = parse_qs(scope.get("query_string", b"").decode())
        token_str = query.get("token", [None])[0]
        scope["user"] = AnonymousUser()

        if token_str:
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                token = AccessToken(token_str)
                uid   = token["user_id"]
                User  = get_user_model()
                scope["user"] = await database_sync_to_async(
                    User.objects.get
                )(id=uid)
            except Exception:
                pass  # token inválido → AnonymousUser

        return await self.inner(scope, receive, send)


application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(app.routing.websocket_urlpatterns)
    ),
})