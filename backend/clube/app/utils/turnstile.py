"""
Cloudflare Turnstile ("não sou um robô") no registo, no registo do POS e na recuperação da password.

O frontend mostra o widget com VUE_APP_TURNSTILE_SITE_KEY e manda a resposta no campo `turnstile`;
aqui confirma-se com a Cloudflare usando TURNSTILE_SECRET. Sem TURNSTILE_SECRET (ainda não configurado)
não se verifica nada — para poder fazer o deploy antes de as chaves existirem.
Dev: chaves de teste da Cloudflare (1x00000000000000000000AA / 1x0000000000000000000000000000000AA passam sempre).
"""
import logging

import requests
from django.conf import settings

log = logging.getLogger(__name__)

URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def ativo():
    return bool(getattr(settings, 'TURNSTILE_SECRET', ''))


def verificar(request):
    """None se passou; senão a mensagem para mostrar."""
    if not ativo():
        return None
    token = str(request.data.get('turnstile') or '')
    if not token:
        return 'Confirma que não és um robô.'
    try:
        r = requests.post(URL, data={'secret': settings.TURNSTILE_SECRET, 'response': token[:2048]}, timeout=8)
        ok = r.json().get('success') is True
    except (requests.RequestException, ValueError):
        log.exception('turnstile: a Cloudflare não respondeu')
        return 'Não foi possível confirmar que não és um robô. Tenta outra vez.'
    return None if ok else 'A verificação anti-robô falhou ou expirou. Tenta outra vez.'


def armadilha(request):
    """Campo escondido `website`: uma pessoa não o vê nem preenche; muitos bots preenchem tudo."""
    return bool(str(request.data.get('website') or '').strip())
