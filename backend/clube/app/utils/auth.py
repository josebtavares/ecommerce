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

MSG_BLOQUEADO = 'Demasiadas tentativas falhadas. Por segurança, tenta novamente dentro de 1 hora.'


def autenticar(request, identificador, password):
    """
    identificador: username ou email.
    Devolve (user, None, None) ou (None, mensagem, status_http).
    """
    ident = (identificador or '').strip()
    alvo = (User.objects.filter(username=ident).first()
            or User.objects.filter(email__iexact=ident).order_by('id').first())
    # sem conta: autentica na mesma com o texto dado, para o axes contar a tentativa
    username = alvo.username if alvo else ident

    user = authenticate(request, username=username, password=password)

    if getattr(request, 'axes_locked_out', False):
        return None, MSG_BLOQUEADO, 429
    if not user:
        return None, 'Credenciais inválidas.', 401

    reset(username=user.username)
    return user, None, None
