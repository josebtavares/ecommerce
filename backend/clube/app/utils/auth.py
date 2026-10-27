"""
Autenticação partilhada pelos logins da Bendi e do dono do POS.

Com django-axes, cada authenticate() falhado conta como tentativa falhada.
Por isso o username é resolvido ANTES (username ou email) e há uma só chamada:
um login por email bem-sucedido já não regista uma falha "fantasma".
O axes só limpa o contador no sinal user_logged_in (login de sessão), que o
fluxo JWT não dispara — limpamos explicitamente após sucesso.
"""
from axes.utils import reset
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django_ratelimit.core import get_usage

MSG_BLOQUEADO = 'Demasiadas tentativas falhadas. Por segurança, tenta novamente dentro de 1 hora.'
MSG_IP = 'Demasiadas tentativas falhadas a partir desta ligação. Tenta novamente mais tarde.'

# O axes bloqueia uma conta num IP; quem experimenta muitas contas diferentes a partir do mesmo IP
# (listas de passwords roubadas) não era travado. Só as FALHAS contam: numa rede partilhada
# (dados móveis, escritório) quem acerta na password não gasta o limite dos outros.
LIMITES_IP = (('login_falhas_ip_m', '30/m'), ('login_falhas_ip_h', '150/h'))


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


def autenticar(request, identificador, password):
    """
    identificador: username ou email.
    Devolve (user, None, None) ou (None, mensagem, status_http).
    """
    if _ip_bloqueado(request):
        return None, MSG_IP, 429
    ident = (identificador or '').strip()
    alvo = (User.objects.filter(username=ident).first()
            or User.objects.filter(email__iexact=ident).order_by('id').first())
    # sem conta: autentica na mesma com o texto dado, para o axes contar a tentativa
    username = alvo.username if alvo else ident

    user = authenticate(request, username=username, password=password)

    if getattr(request, 'axes_locked_out', False):
        return None, MSG_BLOQUEADO, 429
    if not user:
        _contar_falha(request)
        return None, 'Credenciais inválidas.', 401

    reset(username=user.username)
    return user, None, None
