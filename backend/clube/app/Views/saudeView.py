"""
GET /health/ — estado do serviço para o health check do Railway.

O Railway só passa o tráfego para um deploy novo quando isto responde 200, por isso um deploy
que não consegue falar com a base de dados ou com o Redis nunca substitui o que está a funcionar.
Sem autenticação e sem detalhes (não revela versões, hosts nem erros).
"""
import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

log = logging.getLogger(__name__)


@never_cache
@require_GET
def saude(request):
    falhas = []
    try:
        with connection.cursor() as c:
            c.execute('SELECT 1')
    except Exception:
        log.exception('health: base de dados indisponível')
        falhas.append('db')
    try:
        cache.set('health:ping', 1, 10)
        if cache.get('health:ping') != 1:
            raise RuntimeError('cache não devolveu o valor')
    except Exception:
        log.exception('health: Redis indisponível')
        falhas.append('cache')
    if falhas:
        return JsonResponse({'ok': False, 'falhas': falhas}, status=503)
    return JsonResponse({'ok': True})
