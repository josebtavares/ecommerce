"""
Unicidade de username e email das contas Bendi (User do Django).
Sem distinguir maiúsculas: "Ana" e "ana" são o mesmo username, tal como os emails —
o login procura o email sem maiúsculas, por isso dois iguais deixavam a conta ambígua.
Usado no registo da Bendi e do POS, no perfil, na criação de staff, no Google e na
verificação ao vivo dos formulários (utilizador_disponivel).
"""
import re

from django.contrib.auth.models import User

# o que o Django aceita num username (letras, números e @ . + - _)
USERNAME_RE = re.compile(r'^[\w.@+-]{3,150}$')


def username_em_uso(username, excluir=None):
    qs = User.objects.filter(username__iexact=(username or '').strip())
    if excluir is not None:
        qs = qs.exclude(pk=excluir.pk)
    return qs.exists()


def email_em_uso(email, excluir=None):
    qs = User.objects.filter(email__iexact=(email or '').strip())
    if excluir is not None:
        qs = qs.exclude(pk=excluir.pk)
    if qs.exists():
        return True
    from .eliminacao import email_bloqueado      # de uma conta banida já apagada
    return email_bloqueado(email)


def username_livre(base):
    """Primeiro username livre a partir de `base` (base, base1, base2…)."""
    base = re.sub(r'[^\w.@+-]', '', base or '')[:140] or 'utilizador'
    username, i = base, 1
    while username_em_uso(username):
        username = f'{base}{i}'
        i += 1
    return username


def sugerir_usernames(base, quantidade=3):
    """Alternativas livres para um username ocupado."""
    base = re.sub(r'[^\w.@+-]', '', base or '')[:140] or 'utilizador'
    sugestoes, i = [], 1
    while len(sugestoes) < quantidade and i < 1000:
        candidato = f'{base}{i}'
        if not username_em_uso(candidato):
            sugestoes.append(candidato)
        i += 1
    return sugestoes
