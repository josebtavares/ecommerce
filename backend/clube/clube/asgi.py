"""
ASGI config for clube project.
"""

import os
import django

# 1) settings — tem de ser absolutamente primeiro
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clube.settings")

# 2) inicializa o Django completamente (regista todas as apps)
django.setup()

# 3) só agora é seguro importar modelos, consumers, routing
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import app.routing

django_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(app.routing.websocket_urlpatterns)
        ),
    }
)