"""
Autenticação JWT que respeita o estado da conta.

Banir/suspender um utilizador (Admin → Utilizadores) muda Utilizador.status, mas o simplejwt só
olha para User.is_active — e a renovação do token nem isso: quem já tinha sessão aberta continuava
a usar o site (o token renova-se sozinho). Aqui cada pedido, cada renovação e o WebSocket do chat
recusam contas que não estão activas.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings

MSG_INATIVA = 'A tua conta não está activa. Contacta o suporte.'


# Access de uma sessão terminada (logout): fica no Redis até expirar sozinho.
def _chave_fim(token):
    return f'jwt_fim:{token.get(api_settings.JTI_CLAIM)}'


def terminar_access(token):
    from django.core.cache import cache
    import time
    restante = int(token.get('exp', 0) - time.time())
    if restante > 0:
        cache.set(_chave_fim(token), 1, restante + 5)


def sessao_terminada(token):
    from django.core.cache import cache
    return bool(cache.get(_chave_fim(token)))


def conta_ativa(user):
    """User activo e, se tiver perfil, com status 'ativo'."""
    if user is None or not user.is_active:
        return False
    from .models import Utilizador
    estado = Utilizador.objects.filter(user_id=user.pk).values_list('status', flat=True).first()
    return estado in (None, 'ativo')


class JWTContaAtiva(JWTAuthentication):
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        if sessao_terminada(token):
            raise InvalidToken('Sessão terminada.')
        return token

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not conta_ativa(user):
            raise AuthenticationFailed(MSG_INATIVA, code='conta_inativa')
        return user


class RefreshContaAtiva(TokenRefreshSerializer):
    """A renovação do token também verifica a conta (o original não olha para o utilizador)."""

    def validate(self, attrs):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            refresh = self.token_class(attrs['refresh'])
        except TokenError as e:
            raise InvalidToken(e.args[0])
        if refresh.get('tipo_sessao') == 'membro':
            # sessão de um membro da equipa do POS: não tem User Django (o token não leva user_id).
            # Sem isto o POS desligava os empregados ao fim de 30 min (o access expira e não renovava).
            from .pos.models import UtilizadorPOS
            if not UtilizadorPOS.objects.filter(id=refresh.get('membro_id'), pos_id=refresh.get('pos_id'),
                                                ativo=True, pos__suspenso=False).exists():
                raise AuthenticationFailed('Membro não encontrado ou inativo.', code='conta_inativa')
            return super().validate(attrs)
        user = get_user_model().objects.filter(**{api_settings.USER_ID_FIELD: refresh.get(api_settings.USER_ID_CLAIM)}).first()
        if not conta_ativa(user):
            raise AuthenticationFailed(MSG_INATIVA, code='conta_inativa')
        return super().validate(attrs)
