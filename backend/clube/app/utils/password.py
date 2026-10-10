"""
Regras de password forte — as mesmas que o frontend mostra na checklist
(components/forms/PasswordForca.vue).
"""
import re

REGRAS = [
    (lambda p: len(p) >= 8,                   'mínimo 8 caracteres'),
    (lambda p: re.search(r'[A-Z]', p),        'uma letra maiúscula'),
    (lambda p: re.search(r'[a-z]', p),        'uma letra minúscula'),
    (lambda p: re.search(r'[0-9]', p),        'um número'),
    (lambda p: re.search(r'[^A-Za-z0-9]', p), 'um símbolo especial'),
]


def erros_password(password: str) -> list:
    """Devolve a lista de requisitos em falta (vazia = password válida)."""
    password = password or ''
    return [msg for regra, msg in REGRAS if not regra(password)]


def mensagem_password_fraca(password: str):
    """Mensagem pronta para a API, ou None se a password for válida."""
    falta = erros_password(password)
    if not falta:
        return None
    return 'A password precisa de: ' + ', '.join(falta) + '.'
