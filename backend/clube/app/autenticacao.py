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


# Password mudada (perfil ou recuperação): as sessões abertas ANTES deixam de valer — quem tinha
# um token roubado perdia-o só quando expirasse (o refresh roda e renovava-se para sempre).
# Guarda-se a hora da troca enquanto um refresh antigo ainda podia ser usado.
# Membros da equipa do POS (sem User Django) têm a chave própria: 'membro:<id>'.
def _chave_desde(user_id):
    return f'jwt_desde:{user_id}'


def terminar_sessoes(user=None, membro_id=None):
    """Devolve o instante da troca: o iat do JWT é em segundos inteiros, por isso guarda-se a hora
    exata e um token do mesmo segundo (emitido antes) também cai. Os tokens entregues a quem fez a
    troca levam a marca 'troca' com esse instante (ver tokens_depois_da_troca)."""
    from django.core.cache import cache
    import time
    agora = time.time()
    chave = _chave_desde(f'membro:{membro_id}' if membro_id else user.pk)
    cache.set(chave, agora, int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()) + 60)
    return agora


def tokens_depois_da_troca(user, desde):
    """(access, refresh) para a própria resposta da troca. O iat não pode ir para o segundo seguinte
    (o JWT recusa tokens 'do futuro'): levam a marca da troca, que os deixa passar."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    refresh['troca'] = repr(desde)
    return str(refresh.access_token), str(refresh)   # o access copia a marca


def anterior_a_troca(user_id, token, membro_id=None):
    from django.core.cache import cache
    desde = cache.get(_chave_desde(f'membro:{membro_id}' if membro_id else user_id))
    if not desde or token.get('troca') == repr(desde):
        return False
    return token.get('iat', 0) < desde


def conta_ativa(user):
    """User activo e, se tiver perfil, com status 'ativo'."""
    if user is None or not user.is_active:
        return False
    from .models import Utilizador
    perfil = Utilizador.objects.filter(user_id=user.pk).values('status', 'suspenso_ate').first()
    if perfil is None or perfil['status'] == 'ativo':
        return True
    if perfil['status'] == 'suspenso' and perfil['suspenso_ate']:
        # a suspensão acabou: levanta-a já (e fica no histórico)
        from .utils.moderacao import levantar_expiradas
        return levantar_expiradas(Utilizador.objects.filter(user_id=user.pk)) > 0
    return False


class JWTContaAtiva(JWTAuthentication):
    def authenticate(self, request):
        from rest_framework.exceptions import PermissionDenied
        from .utils import ver_loja
        ver_loja.definir()      # nunca herda o modo de leitura de outro pedido
        resultado = super().authenticate(request)
        if resultado is None:
            return None
        user, token = resultado
        loja_id = token.get('ver_loja')
        if loja_id:
            # admin a ver o backoffice de uma loja (utils/ver_loja.py): só leitura, e só enquanto
            # continuar a ter a permissão
            from .models import Utilizador
            perfil = Utilizador.objects.filter(user_id=user.pk).first()
            if not user.is_staff or not perfil or not perfil.pode_admin('ver_backoffice_lojas'):
                raise InvalidToken('Sem permissão para ver lojas.')
            if request.method not in ver_loja.METODOS_LEITURA:
                raise PermissionDenied('Modo só de leitura — estás a ver esta loja como admin.')
            ver_loja.definir(loja_id, user.pk)
        return resultado

    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        if sessao_terminada(token):
            raise InvalidToken('Sessão terminada.')
        return token

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not conta_ativa(user):
            raise AuthenticationFailed(MSG_INATIVA, code='conta_inativa')
        if anterior_a_troca(user.pk, validated_token):
            raise InvalidToken('Sessão terminada.')
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
            if anterior_a_troca(None, refresh, membro_id=refresh.get('membro_id')):
                raise InvalidToken('Sessão terminada.')
            return super().validate(attrs)
        user = get_user_model().objects.filter(**{api_settings.USER_ID_FIELD: refresh.get(api_settings.USER_ID_CLAIM)}).first()
        if not conta_ativa(user):
            raise AuthenticationFailed(MSG_INATIVA, code='conta_inativa')
        if anterior_a_troca(user.pk, refresh):
            raise InvalidToken('Sessão terminada.')
        return super().validate(attrs)
