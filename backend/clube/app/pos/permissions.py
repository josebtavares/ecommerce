"""
Permissões customizadas para o sistema POS.
Suporta dois tipos de autenticação:
1. Conta principal — JWT Django normal (tem user_id)
2. Membro de equipa — JWT com claims customizados (tem membro_id, pos_id)
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import UtilizadorPOS, ConfiguracaoPOS


# ═══════════════════════════════════════════════════════════════════
# OBJETO FAKE USER PARA MEMBROS DE EQUIPA
# ═══════════════════════════════════════════════════════════════════

class MembroUser:
    """
    Objeto que simula um 'user' para membros de equipa.
    Usado para que o DRF não rejeite o request.
    """
    def __init__(self, membro, pos):
        self.membro    = membro
        self.pos       = pos
        self.is_membro = True
        self.is_authenticated = True
        self.pk        = f'membro_{membro.id}'

    @property
    def id(self):
        return self.membro.id

    def __str__(self):
        return f'Membro: {self.membro.nome}'


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO DUAL — PRINCIPAL OU MEMBRO
# ═══════════════════════════════════════════════════════════════════

class POSAuthentication(BaseAuthentication):
    """
    Autenticação que aceita:
    - JWT normal (conta principal) → retorna (user, token)
    - JWT de membro (tipo_sessao='membro') → retorna (MembroUser, token)
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        token_str = auth_header.split(' ')[1]

        try:
            token = AccessToken(token_str)
        except (TokenError, InvalidToken):
            raise AuthenticationFailed('Token inválido ou expirado.')

        # ── Membro de equipa (tem tipo_sessao='membro') ──────────────
        if token.get('tipo_sessao') == 'membro':
            membro_id = token.get('membro_id')
            pos_id    = token.get('pos_id')

            if not membro_id or not pos_id:
                raise AuthenticationFailed('Token de membro inválido.')

            try:
                membro = UtilizadorPOS.objects.select_related('pos').get(
                    id=membro_id,
                    pos_id=pos_id,
                    ativo=True
                )
            except UtilizadorPOS.DoesNotExist:
                raise AuthenticationFailed('Membro não encontrado ou inativo.')

            user = MembroUser(membro=membro, pos=membro.pos)
            return (user, token)

        # ── Conta principal (JWT Django normal com user_id) ──────────
        user_id = token.get('user_id')

        if not user_id:
            raise AuthenticationFailed('Token não contém identificação de utilizador.')

        from django.contrib.auth.models import User
        try:
            user = User.objects.select_related('utilizador').get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('Utilizador não encontrado.')

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'


# ═══════════════════════════════════════════════════════════════════
# PERMISSÕES
# ═══════════════════════════════════════════════════════════════════

class IsPOSAuthenticated(BasePermission):
    """
    Permite acesso a qualquer utilizador autenticado via POSAuthentication
    (conta principal OU membro de equipa).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated
        )


class IsContaPrincipal(BasePermission):
    """
    Permite acesso apenas à conta principal (dono do POS).
    Bloqueia membros de equipa.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            not getattr(request.user, 'is_membro', False)
        )


# ═══════════════════════════════════════════════════════════════════
# HELPERS PARA AS VIEWS
# ═══════════════════════════════════════════════════════════════════

def get_utilizador_from_request(request):
    """
    Retorna o Utilizador Bendi do request (conta principal).
    Levanta AttributeError se for membro.
    """
    return request.user.utilizador


def get_membro_from_request(request):
    """
    Retorna o UtilizadorPOS do request (membro de equipa).
    Retorna None se for conta principal.
    """
    if getattr(request.user, 'is_membro', False):
        return request.user.membro
    return None


def is_membro(request):
    """Verifica se o request é de um membro de equipa."""
    return getattr(request.user, 'is_membro', False)