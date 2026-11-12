"""
Autenticação partilhada pelos logins da Bendi e do dono do POS.

Com django-axes, cada authenticate() falhado conta como tentativa falhada.
Por isso o username é resolvido ANTES (username ou email) e há uma só chamada:
um login por email bem-sucedido já não regista uma falha "fantasma".
O axes só limpa o contador no sinal user_logged_in (login de sessão), que o
fluxo JWT não dispara — limpamos explicitamente após sucesso.
"""
import hashlib
from functools import wraps

from axes.utils import reset
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django_ratelimit.core import get_usage, is_ratelimited
from rest_framework import status
from rest_framework.response import Response

from . import turnstile

MSG_BLOQUEADO = 'Demasiadas tentativas falhadas. Por segurança, tenta novamente dentro de 1 hora.'
MSG_IP = 'Demasiadas tentativas falhadas a partir desta ligação. Tenta novamente mais tarde.'

# O axes bloqueia uma conta num IP; quem experimenta muitas contas diferentes a partir do mesmo IP
# (listas de passwords roubadas) não era travado. Só as FALHAS contam: numa rede partilhada
# (dados móveis, escritório) quem acerta na password não gasta o limite dos outros.
LIMITES_IP = (('login_falhas_ip_m', '30/m'), ('login_falhas_ip_h', '150/h'))


# todos os pedidos de login (certos ou errados) a partir de uma ligação — o POS já tinha (10/min);
# o site leva mais folga porque muita gente partilha o IP dos dados móveis
LIMITES_PEDIDOS_IP = (('login_pedidos_ip_m', '20/m'), ('login_pedidos_ip_h', '300/h'))


def ip_excedeu_pedidos(request):
    excedeu = False
    for g, r in LIMITES_PEDIDOS_IP:
        excedeu = is_ratelimited(request=request, group=g, key='ip', rate=r, method='POST', increment=True) or excedeu
    return excedeu


def limite_login_ip(func):
    """Decorator das views de login do site: 429 quando a ligação passa os LIMITES_PEDIDOS_IP."""
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if ip_excedeu_pedidos(request):
            return Response({'detail': 'Demasiadas tentativas. Aguarda um momento antes de tentar novamente.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        return func(request, *args, **kwargs)
    return wrapped


def _ip_bloqueado(request):
    """Já gastou as falhas permitidas (o pedido seguinte é recusado mesmo com a password certa)."""
    for g, r in LIMITES_IP:
        uso = get_usage(request, group=g, key='ip', rate=r)
        if uso and uso['limit'] and uso['count'] >= uso['limit']:   # sem cache (Redis em baixo) não bloqueia
            return True
    return False


def _contar_falha(request):
    for g, r in LIMITES_IP:
        get_usage(request, group=g, key='ip', rate=r, increment=True)


# ── captcha adaptativo: quem acerta à primeira não vê nada; depois de algumas falhas (na conta ou na
#    ligação) o login pede o Turnstile ANTES de verificar a password — um bot deixa de poder experimentar
#    passwords sem resolver o desafio. Pedir o captcha numa conta alheia não a bloqueia (só pede o desafio).
#    Sem TURNSTILE_SECRET (ou sem cache) não se pede nada. ──
CAPTCHA_FALHAS_CONTA = 3     # por conta (username/email/username do membro), numa hora
CAPTCHA_FALHAS_IP = 10       # por ligação (dados móveis partilham IPs: mais folga), numa hora
MSG_CAPTCHA = 'Confirma que não és um robô para continuar.'


def _chave_conta(ident):
    return hashlib.sha256((ident or '').strip().lower().encode()).hexdigest()[:32]


def _usos_captcha(request, ident, incrementar=False):
    conta = _chave_conta(ident)
    return (
        get_usage(request, group='login_captcha_conta', key=lambda g, r: conta,
                  rate=f'{CAPTCHA_FALHAS_CONTA}/h', increment=incrementar),
        get_usage(request, group='login_captcha_ip', key='ip', rate=f'{CAPTCHA_FALHAS_IP}/h', increment=incrementar),
    )


def captcha_necessario(request, ident):
    if not turnstile.ativo():
        return False
    return any(u and u['count'] >= u['limit'] for u in _usos_captcha(request, ident))


def contar_falha_captcha(request, ident):
    _usos_captcha(request, ident, incrementar=True)


def captcha_em_falta(request, ident):
    """None se pode tentar a password; senão a mensagem (o login responde 400 com turnstile=True)."""
    if not captcha_necessario(request, ident):
        return None
    if not str(request.data.get('turnstile') or ''):
        return MSG_CAPTCHA
    return turnstile.verificar(request)


def corpo_erro(request, ident, erro):
    """Corpo da resposta de erro de um login: diz ao frontend se a próxima tentativa já precisa do captcha."""
    corpo = {'detail': erro}
    if captcha_necessario(request, ident):
        corpo['turnstile'] = True
    return corpo


def autenticar(request, identificador, password):
    """
    identificador: username ou email.
    Devolve (user, None, None) ou (None, mensagem, status_http).
    """
    if _ip_bloqueado(request):
        return None, MSG_IP, 429
    ident = (identificador or '').strip()
    falta = captcha_em_falta(request, ident)
    if falta:
        return None, falta, 400
    alvo = (User.objects.filter(username=ident).first()
            or User.objects.filter(email__iexact=ident).order_by('id').first())
    # sem conta: autentica na mesma com o texto dado, para o axes contar a tentativa
    username = alvo.username if alvo else ident

    user = authenticate(request, username=username, password=password)

    if getattr(request, 'axes_locked_out', False):
        return None, MSG_BLOQUEADO, 429
    if not user:
        _contar_falha(request)
        contar_falha_captcha(request, ident)
        return None, 'Credenciais inválidas.', 401

    reset(username=user.username)
    return user, None, None
